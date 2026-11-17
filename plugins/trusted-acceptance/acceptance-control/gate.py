#!/usr/bin/env python3
"""Reference decision core. CLI output is ALWAYS advisory, never a signed pass.

Production callers must obtain policy, current task, complete attempt ledger and
collector identity from protected stores, not from the candidate or this JSON CLI.
This program neither runs candidate code nor publishes GitHub checks.
"""

import argparse
import hashlib
import json
import os
import stat
import sys
import time
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/accept-change/scripts"))
from protocol import (ATTEMPT, BINDING, BOOL, CONTRACT, DIGEST, ID, NATURAL, POSITIVE, TEXT,
                      ProtocolError, array, decode, digest, enum, load, obj, require,
                      unique_records, validate, validate_contract)

POLICY = obj(
    schema_version=enum(1), policy_id=ID, project_id=ID, contract_digest=DIGEST,
    approval_ref=ID, check_bundle_digest=DIGEST, adapter_digest=DIGEST,
    stage=enum("acceptance", "merge", "release"),
    baseline_check_ids=array(ID, 0, True),
    catalog=array(obj(id=ID, source_ref=TEXT, evidence_types=array(ID, 1, True)), 1),
)
CURRENT = obj(
    schema_version=enum(1), run_id=ID, collector_id=ID, request_digest=DIGEST,
    binding=BINDING, task_status=enum("active", "cancelled", "superseded"),
    authorization_expires_at=POSITIVE,
    budget=obj(max_code_repairs=NATURAL, code_repairs=NATURAL,
               max_environment_retries=NATURAL, environment_retries=NATURAL,
               max_cost_microunits=NATURAL, cost_microunits=NATURAL,
               deadline_at=POSITIVE),
    attempt_manifest=array(obj(attempt_id=ID, digest=DIGEST), 1),
)
RUN = obj(schema_version=enum(1), run_id=ID, collector_id=ID,
          request_digest=DIGEST, attempts=array(ATTEMPT, 1))
CASE = obj(contract=CONTRACT, policy=POLICY, current=CURRENT, run=RUN)
# Policy v2 = v1 + pinned formal-verification requirements. The approved policy, not the
# candidate, names the model/contract digests and the minimum evidence level; the gate then
# re-validates every fv-receipt (and, with rerun, re-executes it from the raw files).
FORMAL_REQUIREMENT = obj(
    check_id=ID, min_level=enum("E2", "E3", "E4"), model_digest=DIGEST, contract_digest=DIGEST,
    properties_digest=DIGEST,
    pass_verdicts=array(enum("PASS", "QUALIFIED", "CONFORMS", "SATISFIED"), 1, True),
    rerun=BOOL,
)
POLICY_V2 = obj(**dict(POLICY["properties"], schema_version=enum(2), formal=array(FORMAL_REQUIREMENT, 1)))
CASE_V2 = obj(contract=CONTRACT, policy=POLICY_V2, current=CURRENT, run=RUN)
FORMAL_TYPES = ("fv-receipt", "fv-model", "fv-contract", "fv-trace")
MAX_FORMAL_DOCUMENT = 8 * 1024 * 1024
MAX_EVIDENCE_BYTES = 64 * 1024 * 1024
MAX_TOTAL_EVIDENCE_BYTES = 256 * 1024 * 1024


def file_digest(root, relative, expected_size, keep=False):
    """Read only regular files beneath a protected evidence root, without symlinks.

    openat/O_NOFOLLOW also prevents path-swap escapes while opening components.
    The protected collector owns the files; hash agreement is not provenance.
    With keep=True the verified bytes are returned too (formal documents only, size-capped).
    """
    path = PurePosixPath(relative)
    require(not path.is_absolute() and bool(path.parts) and ".." not in path.parts,
            "unsafe evidence path")
    require(str(path) == relative and "\\" not in relative, "non-canonical evidence path")
    require(0 < expected_size <= MAX_EVIDENCE_BYTES, "evidence size outside limit")
    require(hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_DIRECTORY"),
            "secure evidence file opening unsupported on this platform")
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        descriptor = os.open(path.parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        with os.fdopen(descriptor, "rb") as stream:
            info = os.fstat(stream.fileno())
            require(stat.S_ISREG(info.st_mode), "evidence must be a regular file")
            require(info.st_size == expected_size, "evidence size mismatch")
            hasher = hashlib.sha256()
            total = 0
            kept = []
            require(not keep or expected_size <= MAX_FORMAL_DOCUMENT, "formal evidence document too large")
            while True:
                chunk = stream.read(min(1024 * 1024, expected_size + 1 - total))
                if not chunk:
                    break
                total += len(chunk)
                require(total <= expected_size, "evidence changed during read")
                hasher.update(chunk)
                if keep:
                    kept.append(chunk)
            require(total == expected_size, "evidence changed during read")
            if keep:
                return "sha256:" + hasher.hexdigest(), b"".join(kept)
            return "sha256:" + hasher.hexdigest()
    finally:
        os.close(directory)


def outcome(decision, *reasons):
    return {"schema_version": 1, "authority": "local_advisory",
            "verification_decision": decision, "reasons": list(reasons),
            "delivery_authorization": "not_granted"}


def evaluate(case, evidence_root, now=None):
    """Fail closed on malformed records; only a fully supported run is eligible.

    'eligible' is deliberately different from the remote 'accepted_for_stage'.
    now is injectable for deterministic tests; the CLI uses its own system clock.
    """
    try:
        return _evaluate(case, evidence_root, int(time.time()) if now is None else now)
    except (ProtocolError, OSError, ValueError, RecursionError) as error:
        return outcome("blocked", str(error))


def formal_documents(evidence_root, records):
    """Verified bytes of formal evidence records, keyed by record id."""
    out = {}
    for record in records:
        found, data = file_digest(evidence_root, record["path"], record["size_bytes"], keep=True)
        require(found == record["digest"], "evidence content digest mismatch")
        out[record["id"]] = data
    return out


def check_formal(policy, attempt, binding, evidence_root):
    """Fail closed unless every pinned formal requirement is supported by valid fv evidence."""
    from fvkit.receipt import level_at_least, validate as validate_receipt
    from fvkit.spec import Contract, Model, parse_document
    from fvkit.values import FvError, sha_bytes
    checks = {c["id"]: c for c in attempt["checks"]}
    for requirement in policy["formal"]:
        check = checks[requirement["check_id"]]
        if check["status"] not in ("pass", "fail"):
            continue  # skip/unknown/error is already blocking; formal evidence cannot change that
        records = [e for e in attempt["evidence"] if e["check_id"] == check["id"] and e["id"] in check["evidence_refs"]]
        docs = formal_documents(evidence_root, [e for e in records if e["type"] in FORMAL_TYPES])
        by_type = {t: [e for e in records if e["type"] == t] for t in FORMAL_TYPES}
        require(by_type["fv-receipt"], "formal check %s carries no fv-receipt evidence" % check["id"])
        model = contract = None
        try:
            if requirement["rerun"]:
                require(len(by_type["fv-model"]) == 1 and len(by_type["fv-contract"]) == 1,
                        "re-execution needs exactly one fv-model and one fv-contract record for " + check["id"])
                c_rec, m_rec = by_type["fv-contract"][0], by_type["fv-model"][0]
                contract = Contract(parse_document(docs[c_rec["id"]], PurePosixPath(c_rec["path"]).suffix, c_rec["path"]))
                model = Model(parse_document(docs[m_rec["id"]], PurePosixPath(m_rec["path"]).suffix, m_rec["path"]), None, contract)
                require(model.digest == requirement["model_digest"] and contract.digest == requirement["contract_digest"]
                        and contract.properties_digest == requirement["properties_digest"],
                        "formal model/contract evidence differs from the approved policy")
            traces = {sha_bytes(docs[e["id"]]): docs[e["id"]] for e in by_type["fv-trace"]}
            satisfied = False
            for rec in by_type["fv-receipt"]:
                receipt = decode(docs[rec["id"]])
                inputs = receipt.get("inputs") or {}
                require((inputs.get("model") or {}).get("digest") == requirement["model_digest"]
                        and (inputs.get("contract") or {}).get("digest") == requirement["contract_digest"]
                        and (inputs.get("contract") or {}).get("properties_digest") == requirement["properties_digest"],
                        "fv-receipt %s was produced for a model/contract the policy did not approve" % rec["id"])
                validate_receipt(receipt, model=model, contract=contract, rerun=requirement["rerun"], traces=traces, allow_paths=False)
                if receipt["command"] == "conform":
                    require(receipt["result"]["source"].get("head") == binding["candidate_sha"],
                            "implementation evidence %s belongs to another candidate" % rec["id"])
                positive = receipt["verdict"] in requirement["pass_verdicts"]
                if check["status"] == "fail":
                    continue
                require(positive or receipt["verdict"] in ("PASS", "QUALIFIED", "CONFORMS", "SATISFIED"),
                        "formal evidence %s says %s; it cannot support a pass" % (rec["id"], receipt["verdict"]))
                satisfied = satisfied or (positive and level_at_least(receipt["evidence_level"], requirement["min_level"]))
            if check["status"] == "pass":
                require(satisfied, "no fv-receipt at %s or above with an approved verdict supports %s" % (requirement["min_level"], check["id"]))
            else:
                require(not all(decode(docs[r["id"]])["verdict"] in requirement["pass_verdicts"] for r in by_type["fv-receipt"]),
                        "formal evidence for %s is all positive, yet the check failed" % check["id"])
        except FvError as error:
            raise ProtocolError("formal evidence for %s: %s" % (check["id"], error)) from None


def _evaluate(case, evidence_root, now):
    formal = isinstance(case, dict) and isinstance(case.get("policy"), dict) and case["policy"].get("schema_version") == 2
    validate(case, CASE_V2 if formal else CASE)
    contract, policy, current, run = (case[key] for key in ("contract", "policy", "current", "run"))
    validate_contract(contract)
    binding = current["binding"]
    require(binding["contract_digest"] == policy["contract_digest"] == digest(contract), "contract digest mismatch")
    require(contract["approval_ref"] == policy["approval_ref"], "approval record mismatch")
    for key in ("project_id", "task_id", "task_revision"):
        require(binding[key] == contract[key], "contract task identity mismatch")
    for key in ("project_id", "check_bundle_digest", "adapter_digest", "stage"):
        require(binding[key] == policy[key], "policy binding mismatch: " + key)
    for key in ("run_id", "collector_id", "request_digest"):
        require(run[key] == current[key], "control run identity mismatch: " + key)
    if current["task_status"] != "active":
        return outcome("obsolete", "task cancelled or superseded; archive only")
    if current["authorization_expires_at"] <= now:
        return outcome("blocked", "stage authorization expired")
    budget = current["budget"]
    if budget["deadline_at"] <= now or any(budget[used] > budget[limit] for used, limit in (
        ("code_repairs", "max_code_repairs"), ("environment_retries", "max_environment_retries"),
        ("cost_microunits", "max_cost_microunits"),
    )):
        return outcome("blocked", "cumulative task budget exhausted")
    require(not contract["unresolved_questions"], "unresolved contract questions")

    unique_records(policy["catalog"], "id")
    catalog = {c["id"]: c for c in policy["catalog"]}
    expected = set(policy["baseline_check_ids"]) | set(contract["required_check_ids"])
    require(bool(expected) and expected <= catalog.keys(), "required check absent from approved catalog")
    criteria = {c["id"]: c for c in contract["criteria"]}
    required_criteria = {key: set() for key in expected}
    evidence_types = {key: set(catalog[key]["evidence_types"]) for key in expected}
    for item in criteria.values():
        if item["required"]:
            required_criteria[item["check_id"]].add(item["id"])
            evidence_types[item["check_id"]].update(item["evidence_types"])

    attempts = run["attempts"]
    unique_records(attempts, "attempt_id")
    unique_records(current["attempt_manifest"], "attempt_id")
    require(current["attempt_manifest"] == [
        {"attempt_id": a["attempt_id"], "digest": digest(a)} for a in attempts
    ], "attempt history missing, reordered or modified")
    require([a["sequence"] for a in attempts] == list(range(1, len(attempts) + 1)), "attempt sequence gap")
    require(attempts[-1]["binding"] == binding, "latest attempt does not match current candidate/environment")
    current_attempts = []
    total_bytes = 0
    for attempt in attempts:
        require(attempt["binding"]["project_id"] == binding["project_id"] and
                attempt["binding"]["task_id"] == binding["task_id"] and
                attempt["binding"]["task_revision"] <= binding["task_revision"], "foreign attempt in task history")
        unique_records(attempt["checks"], "id")
        unique_records(attempt["evidence"], "id")
        unique_records(attempt["findings"], "id")
        # Older candidates remain in the trusted manifest. Their evidence retention
        # is managed separately; they do not veto a repaired candidate's full run.
        if attempt["binding"] != binding:
            continue
        current_attempts.append(attempt)
        checks = {c["id"]: c for c in attempt["checks"]}
        require(set(checks) == expected, "missing or unexpected required checks")
        evidence = {e["id"]: e for e in attempt["evidence"]}
        referenced = set()
        for check_id, check in checks.items():
            refs = set(check["requirement_ids"])
            require(required_criteria[check_id] <= refs <= criteria.keys(), "requirement coverage mismatch")
            require(all(criteria[r]["check_id"] == check_id for r in refs), "requirement assigned to wrong check")
            require(set(check["evidence_refs"]) <= evidence.keys(), "missing referenced evidence")
            observed_types = set()
            for ref in check["evidence_refs"]:
                record = evidence[ref]
                require(record["check_id"] == check_id, "evidence assigned to wrong check")
                observed_types.add(record["type"])
                referenced.add(ref)
            if check["status"] in ("pass", "fail"):
                require(evidence_types[check_id] <= observed_types, "required evidence type missing")
            if check["status"] == "pass":
                require(check["failure_type"] == "none", "pass has a failure type")
            if check["status"] in ("fail", "error"):
                require(check["failure_type"] != "none", "failure has no classification")
            if check["status"] == "fail" and check["failure_type"] == "implementation":
                require(bool(check["reproduction_ref"].strip()), "implementation failure has no reproduction")
        for finding in attempt["findings"]:
            require(set(finding["evidence_refs"]) <= evidence.keys(), "finding evidence missing")
            referenced.update(finding["evidence_refs"])
        require(referenced == evidence.keys(), "unbound evidence record")
        for record in evidence.values():
            total_bytes += record["size_bytes"]
            require(total_bytes <= MAX_TOTAL_EVIDENCE_BYTES, "aggregate evidence size limit exceeded")
            require(file_digest(evidence_root, record["path"], record["size_bytes"]) == record["digest"],
                    "evidence content digest mismatch")

    latest = current_attempts[-1]
    checks = latest["checks"]
    if formal:
        require({f["check_id"] for f in policy["formal"]} <= expected, "formal requirement names a check outside the required set")
        check_formal(policy, latest, binding, evidence_root)
    if any(c["failure_type"] == "environment" for c in checks):
        return outcome("infrastructure_blocked", "environment or fixture failure; do not request code repair")
    if any(c["failure_type"] == "checker" for c in checks):
        return outcome("checker_blocked", "checker maintenance requires a new approved bundle")
    if latest["unverified"] or any(c["status"] in ("skip", "not_run", "unknown", "timeout", "error") for c in checks):
        return outcome("blocked", "required scope not verified")
    if any(c["status"] == "fail" and c["failure_type"] != "implementation" for c in checks):
        return outcome("blocked", "failure is not diagnosed")
    if any(c["status"] == "fail" for c in checks):
        return outcome("needs_repair", "reproducible implementation failure; return evidence to harness")
    if any(f["blocking"] and not f["resolved"] for a in current_attempts for f in a["findings"]):
        return outcome("needs_review", "unresolved blocking finding in same-binding history")
    if any(a["unverified"] or any(c["status"] != "pass" for c in a["checks"]) for a in current_attempts[:-1]):
        return outcome("needs_review", "same candidate and conditions previously failed or were unverified")
    require(all(c["status"] == "pass" for c in checks), "no complete valid pass")
    return outcome("eligible", "all required checks and evidence are consistent; protected publisher still required")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, help="local fixture or protected-store export")
    parser.add_argument("--evidence-root", required=True)
    args = parser.parse_args()
    try:
        result = evaluate(load(args.case), args.evidence_root)
    except (ProtocolError, OSError) as error:
        result = outcome("blocked", str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["verification_decision"] == "eligible" else 2


if __name__ == "__main__":
    sys.exit(main())
