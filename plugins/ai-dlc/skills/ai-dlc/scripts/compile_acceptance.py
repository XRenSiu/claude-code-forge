#!/usr/bin/env python3
"""Compile explicit AC/check mappings into a reviewable acceptance proposal.

No expected behavior is inferred from implementation. This is not an approval
issuer. Unmapped obligations and human ACs remain visible and block submission.
"""
import argparse
import json
import sys
from pathlib import Path

from verification import (VerificationError, digest, file_digest, read_json,
                          require, write_new)

HEADER = ("project_id", "task_id", "task_revision", "contract_id", "request_ref", "product_rules_ref")
CRITERION = ("id", "source_ref", "given", "when", "expected", "check_id", "evidence_types", "scope", "method")


def obligations(document):
    out = set()
    for key in (document.get("behavior", {}).get("thresholds") or {}):
        out.add("threshold:" + key)
    for key in (document.get("constraints") or {}):
        if key == "structure":
            out.update("structure:" + k for k in document["constraints"][key])
        else:
            out.add("constraint:" + key)
    for index, _ in enumerate(document.get("rules") or []):
        out.add("rule:" + str(index))
    return out


def compile_proposal(done_when, mapping):
    with open(done_when, encoding="utf-8") as stream:
        text = stream.read()
    try:
        document = json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml
        except ImportError:
            raise VerificationError("PyYAML is required for YAML contracts; use the project's Python or install with python3 -m pip install PyYAML. JSON contracts are also supported.") from None
        try:
            document = yaml.safe_load(text)
        except yaml.YAMLError:
            raise VerificationError("invalid done_when YAML") from None
    require(isinstance(document, dict) and document.get("schema") == 2, "done_when schema 2 required")
    require(isinstance(mapping, dict) and mapping.get("schema_version") == 1, "mapping schema 1 required")
    require(set(mapping) <= {"schema_version", "criteria", "feature_index", *HEADER}, "unknown mapping fields")
    feature_index = None
    feature_entries = {}
    if mapping.get("feature_index"):
        index_path = (Path(done_when).resolve().parent / mapping["feature_index"]).resolve()
        feature_index = read_json(index_path)
        require(feature_index.get("schema_version") == 1, "unsupported feature index")
        for feature in feature_index.get("features", []):
            for entry in feature.get("entries", []):
                key = feature["id"] + "/" + entry["id"]
                require(key not in feature_entries, "duplicate feature entry")
                feature_entries[key] = entry
        require(feature_entries, "empty feature index")
    for key in HEADER:
        require(key in mapping, "mapping missing " + key)
        require(type(mapping[key]) is int and mapping[key] > 0 if key == "task_revision" else isinstance(mapping[key], str) and mapping[key].strip(), "invalid mapping " + key)
    acs = document.get("acceptance")
    require(isinstance(acs, list) and acs and all(isinstance(a, dict) and isinstance(a.get("id"), str) for a in acs), "explicit ACs required")
    ac_by_id = {a["id"]: a for a in acs}
    require(len(ac_by_id) == len(acs), "duplicate AC ids")
    require(all(a.get("kind") in ("mechanical", "human") for a in acs), "unsupported AC kind")
    required_obligations = obligations(document)
    entries = mapping.get("criteria")
    require(isinstance(entries, list), "criteria mapping required")
    criteria, coverage, covered_ac, covered_obligations = [], [], set(), set()
    for item in entries:
        required_keys = {*CRITERION, "ac_ids", "local_check_ids", "obligations"}
        require(isinstance(item, dict) and required_keys <= set(item) <= required_keys | {"feature_entries"}, "criterion mapping has missing or unknown fields")
        refs = item.get("feature_entries", [])
        require(isinstance(refs, list) and all(isinstance(ref, str) for ref in refs) and len(set(refs)) == len(refs), "invalid feature references")
        for ref in refs:
            require(ref in feature_entries, "unknown feature entry: " + str(ref))
            require(feature_entries[ref]["check_id"] in item["local_check_ids"], "feature entry is not covered by local_check_ids")
        for key in CRITERION:
            if key == "evidence_types":
                require(isinstance(item[key], list) and item[key] and all(isinstance(x, str) and x.strip() for x in item[key]), "evidence_types required")
            else:
                require(isinstance(item[key], str) and item[key].strip(), "criterion missing " + key)
        for key in ("ac_ids", "local_check_ids", "obligations"):
            require(isinstance(item[key], list) and all(isinstance(x, str) and x for x in item[key]) and len(set(item[key])) == len(item[key]), "invalid " + key)
        require(item["ac_ids"] or item["obligations"], "criterion must cover an AC or an approved obligation")
        require(set(item["ac_ids"]) <= set(ac_by_id), "mapping references an unknown AC")
        require(set(item["obligations"]) <= required_obligations, "mapping references an unknown obligation")
        criteria.append({**{key: item[key] for key in CRITERION}, "required": True})
        coverage.append({key: item[key] for key in ("id", "ac_ids", "local_check_ids", "check_id", "obligations")})
        if refs:
            coverage[-1]["feature_entries"] = refs
        covered_ac.update(item["ac_ids"])
        covered_obligations.update(item["obligations"])
    require(len({x["id"] for x in criteria}) == len(criteria), "duplicate criterion ids")
    unresolved = ["No trusted check for AC " + key for key in sorted(set(ac_by_id) - covered_ac)]
    unresolved += ["No trusted check for " + key for key in sorted(required_obligations - covered_obligations)]
    unresolved += ["Human attestation is not supported by protocol v1: " + ac["id"] for ac in acs if ac.get("kind") == "human"]
    contract = {"schema_version": 1, **{key: mapping[key] for key in HEADER}, "criteria": criteria,
                "required_check_ids": sorted({item["check_id"] for item in criteria}), "unresolved_questions": unresolved}
    # approval_ref is deliberately absent: only the approval workflow can supply it.
    result = {"schema_version": 1, "authority": "proposal_only", "source_digest": file_digest(done_when),
            "mapping_digest": digest(mapping), "mapping": mapping, "coverage": coverage,
            "required_obligations": sorted(required_obligations), "contract": contract,
            "ready_for_approval": bool(criteria) and not unresolved}
    if feature_index is not None:
        result["feature_index_digest"] = digest(feature_index)
        result["unmapped_feature_entries"] = sorted(set(feature_entries) - {ref for c in coverage for ref in c.get("feature_entries", [])})
    return result


def validate_proposal(proposal, done_when, approved_contract):
    require(isinstance(proposal, dict) and proposal.get("authority") == "proposal_only", "compiled proposal required")
    rebuilt = compile_proposal(done_when, proposal["mapping"])
    require(proposal == rebuilt, "proposal/source/mapping changed; compile and review again")
    require(rebuilt["ready_for_approval"], "unresolved ACs/obligations or human attestation capability")
    expected = dict(approved_contract)
    approval = expected.pop("approval_ref", None)
    require(isinstance(approval, str) and approval, "approved contract needs an approval_ref verified by the service")
    require(expected == rebuilt["contract"], "approved contract differs from the reviewed proposal")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--done-when", required=True)
    parser.add_argument("--mapping", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        proposal = compile_proposal(args.done_when, read_json(args.mapping))
        write_new(args.out, proposal)
        print("proposal_only: " + ("ready for approval" if proposal["ready_for_approval"] else "unresolved checks; see contract.unresolved_questions"))
        return 0 if proposal["ready_for_approval"] else 1
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("compile_acceptance: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
