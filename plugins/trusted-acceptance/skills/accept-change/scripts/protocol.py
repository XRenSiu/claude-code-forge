"""Strict, bounded protocol for acceptance clients and the reference gate.

Parsing and hashes provide integrity checks, never authentication or approval.
Only the Python standard library is required (Python 3.9+).
"""

import hashlib
import json
import re
from pathlib import Path

MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_ITEMS = 2000
ID = {"type": "string", "pattern": r"[A-Za-z0-9][A-Za-z0-9._:@+\-]{0,127}"}
TEXT = {"type": "string", "min": 1, "max": 8192}
DIGEST = {"type": "string", "pattern": r"sha256:[0-9a-f]{64}"}
SHA = {"type": "string", "pattern": r"(?:[0-9a-f]{40}|[0-9a-f]{64})"}
POSITIVE = {"type": "integer", "min": 1}
NATURAL = {"type": "integer", "min": 0}
BOOL = {"type": "boolean"}


def enum(*values):
    return {"enum": list(values)}


def array(items, minimum=0, unique=False):
    return {"type": "array", "items": items, "min": minimum, "unique": unique}


def obj(**properties):
    return {"type": "object", "properties": properties}


BINDING = obj(
    project_id=ID, task_id=ID, task_revision=POSITIVE, candidate_sha=SHA,
    artifact_digest=DIGEST, contract_digest=DIGEST, check_bundle_digest=DIGEST,
    adapter_digest=DIGEST, environment_digest=DIGEST,
    stage=enum("acceptance", "merge", "release"),
)
REQUEST = obj(schema_version=enum(1), idempotency_key=ID, binding=BINDING)
CRITERION = obj(
    id=ID, source_ref=TEXT, given=TEXT, when=TEXT, expected=TEXT,
    required=BOOL, check_id=ID, evidence_types=array(ID, 1, True),
    scope=TEXT, method=TEXT,
)
CONTRACT = obj(
    schema_version=enum(1), project_id=ID, task_id=ID, task_revision=POSITIVE,
    contract_id=ID, request_ref=TEXT, product_rules_ref=TEXT,
    criteria=array(CRITERION, 1), required_check_ids=array(ID, 1, True),
    unresolved_questions=array(TEXT), approval_ref=ID,
)
CHECK = obj(
    id=ID, status=enum("pass", "fail", "skip", "not_run", "unknown", "timeout", "error"),
    requirement_ids=array(ID, 0, True),
    failure_type=enum("none", "implementation", "environment", "checker", "unknown"),
    expected=TEXT, observed=TEXT,
    reproduction_ref={"type": "string", "max": 8192},
    evidence_refs=array(ID, 0, True),
)
EVIDENCE = obj(
    id=ID, check_id=ID, type=ID, path=TEXT, digest=DIGEST, size_bytes=POSITIVE,
)
FINDING = obj(id=ID, blocking=BOOL, resolved=BOOL, summary=TEXT, evidence_refs=array(ID, 0, True))
ATTEMPT = obj(
    attempt_id=ID, sequence=POSITIVE, binding=BINDING,
    checks=array(CHECK), evidence=array(EVIDENCE), findings=array(FINDING),
    unverified=array(TEXT),
)
DECISIONS = (
    "accepted_for_stage", "needs_repair", "needs_review", "blocked",
    "infrastructure_blocked", "checker_blocked", "obsolete",
)
RESULT = obj(
    schema_version=enum(1), run_id=ID, request_digest=DIGEST, binding=BINDING,
    state=enum("queued", "running", "complete"),
    verification_decision=enum("pending", *DECISIONS),
    delivery_authorization=enum("not_granted"),
    checks=array(CHECK), evidence=array(EVIDENCE), findings=array(FINDING),
    unverified=array(TEXT), reasons=array(TEXT),
)
CONFIG = obj(
    schema_version=enum(1), endpoint=TEXT,
    token_env={"type": "string", "pattern": r"[A-Z][A-Z0-9_]{0,127}"},
    timeout_seconds={"type": "integer", "min": 1, "max": 60},
)


class ProtocolError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ProtocolError(message)


def validate(value, schema, path="$"):
    """Validate our small explicit schema vocabulary; all properties required.

    Unknown properties are errors, including purported auth/approval overrides.
    This is deliberately not advertised as a general JSON Schema engine.
    """
    if "enum" in schema:
        require(any(type(value) is type(v) and value == v for v in schema["enum"]),
                f"{path}: invalid enum value")
        return
    kind = schema["type"]
    cls = {"object": dict, "array": list, "string": str, "integer": int, "boolean": bool}[kind]
    require(type(value) is cls, f"{path}: expected {kind}")
    if kind == "object":
        props = schema["properties"]
        require(value.keys() == props.keys(), f"{path}: missing or unknown fields")
        for key, child in props.items():
            validate(value[key], child, f"{path}.{key}")
    elif kind == "array":
        require(schema["min"] <= len(value) <= MAX_ITEMS, f"{path}: invalid array length")
        for index, item in enumerate(value):
            validate(item, schema["items"], f"{path}[{index}]")
        if schema["unique"]:
            require(len({canonical(item) for item in value}) == len(value), f"{path}: duplicate items")
    elif kind == "string":
        require(schema.get("min", 0) <= len(value) <= schema.get("max", 8192),
                f"{path}: invalid text length")
        require(schema.get("min", 0) == 0 or bool(value.strip()), f"{path}: blank text")
        if "pattern" in schema:
            require(re.fullmatch(schema["pattern"], value) is not None, f"{path}: invalid format")
    elif kind == "integer":
        require(schema.get("min", 0) <= value <= schema.get("max", 2**53 - 1),
                f"{path}: integer outside range")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value):
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def unique_records(records, key):
    require(len({row[key] for row in records}) == len(records), f"duplicate {key}")


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON object key")
        result[key] = value
    return result


def decode(data):
    require(len(data) <= MAX_JSON_BYTES, "JSON exceeds 2 MiB limit")
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_pairs,
                          parse_constant=lambda _: require(False, "non-finite JSON number"))
    except (UnicodeError, ValueError, RecursionError) as error:
        raise ProtocolError("invalid JSON: " + str(error)[:160]) from error


def load(path):
    with Path(path).open("rb") as stream:
        return decode(stream.read(MAX_JSON_BYTES + 1))


def validate_contract(contract):
    validate(contract, CONTRACT)
    unique_records(contract["criteria"], "id")
    required = set(contract["required_check_ids"])
    for item in contract["criteria"]:
        if item["required"]:
            require(item["check_id"] in required, "required criterion missing from required_check_ids")


def validate_result(result, request, run_id=None):
    validate(result, RESULT)
    validate(request, REQUEST)
    require(result["request_digest"] == digest(request), "response request digest mismatch")
    require(result["binding"] == request["binding"], "response binding mismatch")
    if run_id is not None:
        require(result["run_id"] == run_id, "response run ID mismatch")
    complete = result["state"] == "complete"
    require(complete == (result["verification_decision"] != "pending"), "inconsistent result state")
    unique_records(result["checks"], "id")
    unique_records(result["evidence"], "id")
    unique_records(result["findings"], "id")
    evidence = {e["id"]: e for e in result["evidence"]}
    for check in result["checks"]:
        require(set(check["evidence_refs"]) <= evidence.keys(), "response evidence reference missing")
        require(all(evidence[ref]["check_id"] == check["id"] for ref in check["evidence_refs"]),
                "response evidence belongs to another check")
    for finding in result["findings"]:
        require(set(finding["evidence_refs"]) <= evidence.keys(), "response finding evidence missing")
    if result["verification_decision"] == "accepted_for_stage":
        require(bool(result["checks"]), "empty accepted result")
        require(all(c["status"] == "pass" and c["failure_type"] == "none" for c in result["checks"]),
                "accepted result contains non-pass checks")
        require(all(c["evidence_refs"] for c in result["checks"]), "accepted result lacks check evidence")
        require(not result["unverified"], "accepted result contains unverified scope")
        require(not any(f["blocking"] and not f["resolved"] for f in result["findings"]),
                "accepted result contains blocking findings")
        # This is only a client consistency check; the server resolves the full checklist.
