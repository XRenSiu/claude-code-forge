"""Portable product/calibration evidence verifier (standard library only).

Canonical source: trusted-acceptance. The byte-identical copy in AI-DLC keeps
both installed plugins self-contained. Integrity is not protected provenance.
"""
import hashlib
import json
import math
import os
import re
import subprocess
from pathlib import Path

MAX_BYTES = 8 * 1024 * 1024
DIGEST = re.compile(r"sha256:[a-f0-9]{64}\Z")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def digest(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode())


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def load(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= MAX_BYTES, "invalid evidence file")
    return json.loads(path.read_text(), object_pairs_hook=_pairs,
                      parse_constant=lambda _: require(False, "non-finite number"))


def artifact(root, record):
    require(isinstance(record, dict), "missing artifact descriptor")
    name = record.get("path")
    require(isinstance(name, str) and name and "\\" not in name and "\0" not in name, "invalid artifact path")
    parts = Path(name).parts
    require(not Path(name).is_absolute() and ".." not in parts, "artifact escapes evidence root")
    cursor = Path(root)
    for part in parts:
        cursor = cursor / part
        require(not cursor.is_symlink(), "artifact symlink")
    require(cursor.is_file() and cursor.stat().st_size <= MAX_BYTES, "artifact missing or too large")
    data = cursor.read_bytes()
    require(type(record.get("size_bytes")) is int and len(data) == record["size_bytes"] and sha(data) == record.get("digest"), "artifact integrity mismatch")
    return cursor


def entry_from_index(index, feature_id, entry_id):
    require(index.get("schema_version") == 1, "unsupported feature index")
    matches = [(f, e) for f in index.get("features", []) for e in f.get("entries", [])
               if f.get("id") == feature_id and e.get("id") == entry_id]
    require(len(matches) == 1, "unknown or duplicate feature entry")
    return matches[0][1]


def current_project_binding(root, feature_id, entry_id, node='node'):
    """Measure current Git source without running candidate scripts (local gate only)."""
    root = Path(root).resolve()
    index = load(root / '.harness/features.json')
    entry = entry_from_index(index, feature_id, entry_id)
    names = subprocess.run(['git', '-C', str(root), 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
                           check=True, capture_output=True, timeout=15).stdout
    require(len(names) <= MAX_BYTES, 'current candidate listing too large')
    paths = sorted(set(names.decode().split('\0')) - {''}, key=lambda p: p.encode('utf-16-be'))
    require(len(paths) <= 100000, 'current candidate scan incomplete')
    entries = []
    for name in paths:
        path = root / name
        require(root in path.resolve().parents or path.is_symlink(), 'candidate path escapes root')
        if path.is_symlink(): entries.append([name, 'symlink', os.readlink(path)])
        elif path.is_file(): entries.append([name, path.stat().st_mode & 0o777, sha(path.read_bytes())[7:]])
        elif not path.exists(): entries.append([name, 'deleted'])
        else: raise ValueError('candidate submodule/directory is not a complete snapshot')
    def files(paths):
        values = []
        for name in sorted(set(paths)):
            path = (root / name).resolve()
            require(root in path.parents, 'checker or fixture escapes project')
            values.append([name, path.read_bytes().decode('utf-8')])
        return digest(values)
    environment = json.loads(subprocess.run([node, '-p', 'JSON.stringify({node:process.versions.node,platform:process.platform,arch:process.arch})'],
                                           check=True, capture_output=True, text=True, timeout=15).stdout)
    environment['node_args'] = entry['node_args']
    return {'feature_id': feature_id, 'entry_id': entry_id, 'check_id': entry['check_id'],
            'feature_index_digest': digest(index), 'candidate_digest': digest(entries),
            'checker_digest': files([entry['driver'], *entry['checker_files']]),
            'fixture_digest': files(entry['fixture_files']), 'environment_digest': digest(environment)}


def validate_product(path, expected_claims=None, expected_binding=None):
    report = load(path)
    require(report.get("schema_version") == 1 and report.get("evidence_kind") == "product-observation"
            and report.get("authority") == "project-self-check", "unsupported product receipt")
    binding = report.get("binding", {})
    for key in ("candidate_digest", "checker_digest", "fixture_digest", "feature_index_digest", "environment_digest"):
        require(isinstance(binding.get(key), str) and DIGEST.fullmatch(binding[key]), "missing product binding: " + key)
    for key in ("feature_id", "entry_id", "check_id"):
        require(isinstance(binding.get(key), str) and binding[key], "missing product identity")
    for key, value in (expected_binding or {}).items():
        require(binding.get(key) == value, "product binding mismatch: " + key)
    require(report.get("candidate_unchanged") is True, "product candidate changed")
    phases = report.get("phases", [])
    require([p.get("name") for p in phases] == ["launch", "doctor", "drive", "observe", "cleanup"]
            and all(p.get("status") == "PASS" for p in phases), "product lifecycle incomplete")
    evidence = report.get("evidence", [])
    evidence_ids = [e.get("id") for e in evidence]
    require(evidence_ids and all(isinstance(i, str) and i for i in evidence_ids)
            and len(set(evidence_ids)) == len(evidence_ids), "missing or duplicate raw evidence")
    for item in evidence:
        artifact(Path(path).parent, item)
    claims = report.get("claims", [])
    ids = [c.get("id") for c in claims]
    require(ids and all(isinstance(i, str) and i for i in ids) and len(set(ids)) == len(ids), "missing or duplicate product claims")
    if expected_claims is not None:
        require(len(ids) == len(expected_claims) and set(ids) == set(expected_claims), "product claim coverage mismatch")
    for claim in claims:
        require(claim.get("status") in ("PASS", "FAIL"), "unevaluated product claim")
        require(all(isinstance(claim.get(k), str) and claim[k].strip() for k in ("expected", "actual")), "missing observation")
        refs = claim.get("evidence_refs")
        require(isinstance(refs, list) and refs and set(refs) <= set(evidence_ids), "claim lacks raw evidence")
    status = "PASS" if all(c["status"] == "PASS" for c in claims) else "FAIL"
    require(report.get("status") == status, "product summary contradicts observations")
    return report


def validate_calibration(path, expected_plan=None, expected_index=None):
    root = Path(path).parent
    report = load(path)
    require(report.get("schema_version") == 1 and report.get("evidence_kind") == "checker-calibration"
            and report.get("authority") == "local_advisory", "unsupported calibration receipt")
    plan = load(artifact(root, report.get("plan")))
    require(plan.get("schema_version") == 1 and plan.get("mutations"), "empty calibration plan")
    if expected_plan is not None:
        require(plan == expected_plan, "calibration plan changed")
    mutations = plan["mutations"]
    ids = [m["id"] for m in mutations]
    required = plan.get("required_faults", [])
    require(len(set(ids)) == len(ids) and required and len(set(required)) == len(required)
            and set(required) <= set(ids) and report.get("required_faults") == required, "missing required faults")
    cases = report.get("cases", [])
    require([c.get("id") for c in cases] == ["baseline", *ids, "recovery"], "missing, duplicated or reordered calibration attempts")
    baseline = validate_product(artifact(root, cases[0].get("receipt")))
    binding = baseline["binding"]
    claims = [c["id"] for c in baseline["claims"]]
    require(binding["candidate_digest"] == report.get("source_digest") and binding["feature_id"] == plan.get("feature_id")
            and binding["entry_id"] == plan.get("entry_id"), "calibration subject mismatch")
    if expected_index is not None:
        entry = entry_from_index(expected_index, plan["feature_id"], plan["entry_id"])
        require(binding["feature_index_digest"] == digest(expected_index) and set(claims) == set(entry["claims"])
                and binding["check_id"] == entry["check_id"], "feature index binding mismatch")
        protected = {entry["driver"], *entry["checker_files"], *entry["fixture_files"]}
        require(all(isinstance(m['path'], str) and all(p not in ('', '.', '..') for p in m['path'].split('/')) and not Path(m['path']).is_absolute() for m in mutations), 'noncanonical fault path')
        require(not any(m["path"] in protected or m["path"].startswith(".harness/") or m['path'] == 'scripts/project-product.mjs' for m in mutations), "fault edits its own checker or fixture")
    shared = {k: v for k, v in binding.items() if k != "candidate_digest"}
    killed = 0
    for i, case in enumerate(cases):
        artifact(root, case.get("stdout")); artifact(root, case.get("stderr"))
        result = validate_product(artifact(root, case.get("receipt")), claims, shared)
        if i in (0, len(cases) - 1):
            require(case.get("kind") == "positive" and case.get("status") == "PASS" and case.get("exit_code") == 0
                    and result["status"] == "PASS" and result["binding"]["candidate_digest"] == report["source_digest"], "positive control failed or changed")
        else:
            mutation = mutations[i - 1]
            observed = case.get("mutation", {})
            require(case.get("kind") == "mutant" and all(observed.get(k) == v for k, v in mutation.items()), "fault differs from plan")
            patch = load(artifact(root, observed.get("patch")))
            require(patch.get("path") == mutation["path"] and patch["before"].count(mutation["before"]) == 1
                    and patch["after"] == patch["before"].replace(mutation["before"], mutation["after"], 1)
                    and patch["before"] != patch["after"], "invalid fault injection")
            require(sha(patch["before"].encode()) == observed.get("before_digest")
                    and sha(patch["after"].encode()) == observed.get("after_digest"), "fault preimage/postimage mismatch")
            require(result["binding"]["candidate_digest"] != binding["candidate_digest"], "fault reused the good candidate")
            failed = any(c["id"] == mutation["claim_id"] and c["status"] == "FAIL" for c in result["claims"])
            require(case.get("status") == "KILLED" and case.get("exit_code") == 1 and result["status"] == "FAIL" and failed,
                    "fault was not caught by its intended business assertion: " + mutation["id"])
            killed += 1
    require(type(report.get("total_mutants")) is int and report["total_mutants"] == len(mutations)
            and type(report.get("killed")) is int and report["killed"] == killed, "calibration counts disagree with attempts")
    score = report.get("mutation_score")
    require(type(score) in (int, float) and math.isfinite(score) and score == killed / len(mutations)
            and report.get("status") == "PASS", "calibration score or verdict disagrees with evidence")
    return {"authority": "local_advisory", "status": "PASS", "total_mutants": len(mutations), "killed": killed,
            "mutation_score": score, "binding": binding, "required_faults": required,
            "limitations": ["Evidence integrity does not authenticate the collector", "Holdout secrecy and protected execution remain separate requirements"]}
