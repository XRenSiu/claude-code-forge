#!/usr/bin/env python3
"""Run a real local HTTP fixture and collect evidence; never a production verdict."""

import argparse
import hashlib
import json
import os
import selectors
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "skills/accept-change/scripts"))
sys.path.insert(0, str(PLUGIN / "acceptance-control"))
from protocol import digest
from gate import evaluate


def contract_fixture():
    return {
        "schema_version": 1, "project_id": "synthetic-sharing", "task_id": "SHARE-123",
        "task_revision": 1, "contract_id": "revoke-contract@1",
        "request_ref": "synthetic-request@1", "product_rules_ref": "synthetic-sharing-policy@1",
        "criteria": [{
            "id": "AC-REVOKE", "source_ref": "synthetic-sharing-policy@1#new-read",
            "given": "An anonymous visitor can read a synthetic shared document",
            "when": "The fixture owner revokes sharing and receives success",
            "expected": "A new anonymous read returns 403 or 404 without the document body",
            "required": True, "check_id": "revoke-new-read", "evidence_types": ["request-response"],
            "scope": "Local HTTP fixture; no CDN, member access or offline cache",
            "method": "Observe independent HTTP reads before and after the owner revokes access",
        }],
        "required_check_ids": ["revoke-new-read"], "unresolved_questions": [],
        "approval_ref": "synthetic-policy-decision-1",
    }


def refresh_manifest(case):
    case["current"]["attempt_manifest"] = [
        {"attempt_id": a["attempt_id"], "digest": digest(a)} for a in case["run"]["attempts"]
    ]


def make_case(evidence_root, passed=True, transcript=None, variant="good"):
    """All identities and approval records here are explicit synthetic fixtures."""
    root = Path(evidence_root)
    root.mkdir(parents=True, exist_ok=True)
    contract = contract_fixture()
    bundle_digest = digest({"observer_source": Path(__file__).read_text()})
    adapter_digest = digest({"recipe": "demo-http-v1", "identities": ["owner", "anonymous"]})
    binding = {
        "project_id": contract["project_id"], "task_id": contract["task_id"], "task_revision": 1,
        "candidate_sha": hashlib.sha1(("synthetic-candidate:" + variant).encode()).hexdigest(),
        "artifact_digest": digest({"source": (PLUGIN / "evaluations/demo_service.py").read_text(), "variant": variant}),
        "contract_digest": digest(contract), "check_bundle_digest": bundle_digest,
        "adapter_digest": adapter_digest,
        "environment_digest": digest({"transport": "loopback-http", "fixture": "synthetic-document", "variant": variant}),
        "stage": "acceptance",
    }
    request = {"schema_version": 1, "idempotency_key": "synthetic-request-1", "binding": binding}
    policy = {
        "schema_version": 1, "policy_id": "synthetic-policy@1", "project_id": binding["project_id"],
        "contract_digest": digest(contract), "approval_ref": contract["approval_ref"],
        "check_bundle_digest": bundle_digest, "adapter_digest": adapter_digest, "stage": "acceptance",
        "baseline_check_ids": ["service-ready"],
        "catalog": [{"id": i, "source_ref": "synthetic-project-policy@1", "evidence_types": ["request-response"]}
                    for i in ("service-ready", "revoke-new-read")],
    }
    observations = transcript if transcript is not None else [{"synthetic_unit_fixture": True, "passed": passed}]
    evidence = []
    for name in ("service-ready", "revoke-new-read"):
        data = json.dumps(observations[:1] if name == "service-ready" else observations, indent=2).encode()
        filename = name + ".json"
        (root / filename).write_bytes(data)
        evidence.append({"id": "ev-" + name, "check_id": name, "type": "request-response",
                         "path": filename, "digest": "sha256:" + hashlib.sha256(data).hexdigest(), "size_bytes": len(data)})
    checks = [{
        "id": name, "status": "fail" if name == "revoke-new-read" and not passed else "pass",
        "requirement_ids": ["AC-REVOKE"] if name == "revoke-new-read" else [],
        "failure_type": "implementation" if name == "revoke-new-read" and not passed else "none",
        "expected": "No body on new read after revoke" if name == "revoke-new-read" else "Initial read succeeds",
        "observed": "Body still readable" if name == "revoke-new-read" and not passed else "Assertion satisfied",
        "reproduction_ref": "synthetic-fixture#revoke-then-read" if not passed else "",
        "evidence_refs": ["ev-" + name],
    } for name in ("service-ready", "revoke-new-read")]
    attempt = {"attempt_id": "attempt-1", "sequence": 1, "binding": binding,
               "checks": checks, "evidence": evidence, "findings": [], "unverified": []}
    now = int(time.time())
    case = {"contract": contract, "policy": policy, "current": {
        "schema_version": 1, "run_id": "synthetic-run-1", "collector_id": "synthetic-observer",
        "request_digest": digest(request), "binding": binding, "task_status": "active",
        "authorization_expires_at": now + 3600,
        "budget": {"max_code_repairs": 2, "code_repairs": 0, "max_environment_retries": 1,
                   "environment_retries": 0, "max_cost_microunits": 1000000, "cost_microunits": 0,
                   "deadline_at": now + 3600}, "attempt_manifest": [],
    }, "run": {"schema_version": 1, "run_id": "synthetic-run-1", "collector_id": "synthetic-observer",
               "request_digest": digest(request), "attempts": [attempt]}}
    refresh_manifest(case)
    return case, request


def observe(base):
    transcript = []

    def fetch(path, method="GET", owner=False):
        headers = {"X-Fixture-Owner": "synthetic-owner"} if owner else {}
        request = urllib.request.Request(base + path, method=method, headers=headers)
        # This synthetic loopback probe bypasses environment proxy settings.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            response = opener.open(request, timeout=5)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            status, body = response.status, response.read(8193).decode("utf-8")
        transcript.append({"method": method, "path": path, "identity": "owner" if owner else "anonymous",
                           "status": status, "body": body})
        return status, body

    before = fetch("/document")
    revoked = fetch("/revoke", "POST", True)
    after = fetch("/document")
    if before != (200, "synthetic document body") or revoked[0] != 200:
        raise RuntimeError("fixture preconditions failed; not a valid business failure")
    passed = after[0] in (403, 404) and "synthetic document body" not in after[1]
    return passed, transcript


def run_demo(out, variant):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    environment = {"PATH": os.environ.get("PATH", ""), "PYTHONIOENCODING": "utf-8"}
    process = subprocess.Popen([sys.executable, str(PLUGIN / "evaluations/demo_service.py"), variant],
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, env=environment)
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            if not selector.select(5):
                raise RuntimeError("fixture startup timed out")
        port = int(process.stdout.readline().strip())
        passed, transcript = observe(f"http://127.0.0.1:{port}")
        case, request = make_case(out / "evidence", passed, transcript, variant)
        result = evaluate(case, out / "evidence")
        for name, content in (("case.json", case), ("request.json", request), ("decision.json", result)):
            (out / name).write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n")
        return result
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        process.stdout.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="new directory; will not overwrite a previous run")
    parser.add_argument("--variant", choices=("good", "good-alternative", "ui-only"), default="good")
    args = parser.parse_args()
    result = run_demo(args.out, args.variant)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["verification_decision"] == "eligible" else 2)
