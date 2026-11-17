#!/usr/bin/env python3
"""Bounded client. No shell execution, local pass issuer, or delivery credentials."""

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from protocol import (CONFIG, ID, MAX_JSON_BYTES, REQUEST, ProtocolError, canonical,
                      decode, load, require, validate, validate_contract, validate_result)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProtocolError("control endpoint redirect refused")


def endpoint_config(path):
    config = load(path)
    validate(config, CONFIG)
    parts = urllib.parse.urlsplit(config["endpoint"])
    require(parts.scheme == "https" and bool(parts.hostname), "control endpoint must use HTTPS")
    require(not (parts.username or parts.password or parts.query or parts.fragment),
            "endpoint must not contain credentials, query, or fragment")
    require(not any(c.isspace() or ord(c) < 32 for c in config["endpoint"]), "invalid endpoint")
    token = os.environ.get(config["token_env"], "")
    require(bool(token) and not any(c.isspace() or ord(c) < 32 for c in token),
            "missing or invalid control API token environment variable")
    return config, token


def exchange(config, token, method, suffix, body=None, key=None):
    headers = {"Authorization": "Bearer " + token, "Accept": "application/json"}
    if key:
        headers["Idempotency-Key"] = key
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(config["endpoint"].rstrip("/") + suffix,
                                     data=canonical(body) if body is not None else None,
                                     headers=headers, method=method)
    opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    try:
        with opener.open(request, timeout=config["timeout_seconds"]) as response:
            require(response.status in (200, 201, 202), "unexpected control HTTP status")
            require(response.headers.get_content_type() == "application/json", "expected JSON response")
            return decode(response.read(MAX_JSON_BYTES + 1))
    except urllib.error.HTTPError as error:
        # Do not print remote HTML, request bodies, URLs or credentials.
        raise ProtocolError(f"control HTTP {error.code}; no automatic retry") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ProtocolError("control endpoint unavailable; retain request/key before retrying") from None


def write_new(path, payload):
    """Never silently replace a receipt/history file."""
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if path:
        with Path(path).open("x", encoding="utf-8") as stream:
            stream.write(text)
    else:
        print(text, end="")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    evidence = sub.add_parser("validate-calibration", help="verify local raw calibration evidence; never issue formal acceptance")
    evidence.add_argument("file")
    evidence.add_argument("--plan", required=True, help="reviewed calibration plan")
    evidence.add_argument("--features", required=True, help="reviewed feature index")
    formal = sub.add_parser("validate-formal", help="re-verify an fvkit receipt (model check / qualification / conformance); never issue formal acceptance")
    formal.add_argument("file")
    formal.add_argument("--model", help="the approved fv-model; required for counterexample replay and --rerun")
    formal.add_argument("--contract", help="the approved fv-contract (defaults to the model's reference)")
    formal.add_argument("--rerun", action="store_true", help="re-execute the check/qualification/trace check and compare")
    formal.add_argument("--min-level", choices=["E0", "E1", "E2", "E3", "E4"])
    formal.add_argument("--expect", action="append", help="acceptable verdicts, e.g. QUALIFIED or CONFORMS")
    formal.add_argument("--trace", action="append", default=[], help="raw implementation trace for re-checking a conformance receipt")
    for name in ("validate-request", "validate-contract"):
        cmd = sub.add_parser(name)
        cmd.add_argument("file")
    for name in ("submit", "get-result"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--request", required=True)
        cmd.add_argument("--config", required=True, help="operator-owned config; never a candidate-provided file")
        cmd.add_argument("--output", help="new JSON file; existing files are never overwritten")
        if name == "get-result":
            cmd.add_argument("--run-id", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate-formal":
            from fvkit.receipt import load as load_receipt, validate as validate_receipt
            from fvkit.spec import load_contract, load_model
            from fvkit.values import FvError, sha_bytes
            try:
                contract = load_contract(args.contract) if args.contract else None
                model = load_model(args.model, contract=contract) if args.model else None
                traces = {sha_bytes(Path(t).read_bytes()): Path(t).read_bytes() for t in args.trace}
                result = validate_receipt(load_receipt(args.file), model=model, contract=contract or (model and model.contract),
                                          rerun=args.rerun, min_level=args.min_level, expect_verdicts=args.expect,
                                          base_dir=str(Path(args.file).resolve().parent), traces=traces)
            except FvError as error:
                raise ProtocolError("formal evidence rejected: " + str(error)) from None
            print(json.dumps(result, ensure_ascii=False))
            return 0
        if args.command == "validate-calibration":
            from verification_evidence import validate_calibration
            print(json.dumps(validate_calibration(args.file, load(args.plan), load(args.features)), ensure_ascii=False))
            return 0
        if args.command in ("validate-request", "validate-contract"):
            document = load(args.file)
            if args.command == "validate-contract":
                validate_contract(document)
            else:
                validate(document, REQUEST)
            print(json.dumps({"valid": True, "authority": "syntax_only"}))
            return 0
        request = load(args.request)
        validate(request, REQUEST)
        config, token = endpoint_config(args.config)
        run_id = getattr(args, "run_id", None)
        if run_id is not None:
            validate(run_id, ID)
        # Reserve no remote work when a known existing local output cannot be written.
        if args.output:
            require(not Path(args.output).exists(), "output already exists; choose a new receipt path")
        if args.command == "submit":
            result = exchange(config, token, "POST", "/runs", request, request["idempotency_key"])
        else:
            result = exchange(config, token, "GET", "/runs/" + urllib.parse.quote(run_id, safe=""))
        validate_result(result, request, run_id)
        write_new(args.output, result)
        if result["state"] != "complete":
            return 3
        return 0 if result["verification_decision"] == "accepted_for_stage" else 2
    except (ProtocolError, OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print("acceptance: " + str(error), file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
