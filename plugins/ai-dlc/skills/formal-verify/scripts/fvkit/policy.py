"""Risk-based verification policy, change impact and contract approvals.

`verification/policy.yaml` maps code paths to modules, modules to risk classes, and risk
classes to the evidence each change must carry. Which modules a change touches is computed
from git, not declared by the author: an omitted module is not a skipped check.
"""
import json
from pathlib import Path

from .sourcemap import changed_files, glob_match
from .spec import _keys, load_document
from .values import require

LEVELS = ("E0", "E1", "E2", "E3", "E4")
DEFAULT_RISKS = {
    "concurrency": {"min_level": "E3", "tier": "core"},
    "consistency": {"min_level": "E3", "tier": "core"},
    "permission": {"min_level": "E3", "tier": "core"},
    "retry": {"min_level": "E3", "tier": "core"},
    "pure": {"min_level": "E1", "tier": "fast"},
    "ui": {"min_level": "E0", "tier": "fast"},
    "low": {"min_level": "E0", "tier": "none"},
}
DEFAULT_TIERS = {
    "fast": {"max_states": 20000, "time_seconds": 120, "mutants": False, "auto_mutants": False, "allow_bounded": True},
    "core": {"max_states": 500000, "time_seconds": 900, "mutants": True, "auto_mutants": False, "allow_bounded": False},
    "deep": {"max_states": 5000000, "time_seconds": 3600, "mutants": True, "auto_mutants": True, "allow_bounded": False},
}
MODULE_KEYS = ["id", "risk", "paths"]
MODULE_OPTIONAL = ["contract", "model", "source_map", "traces", "trace_command", "vectors", "approvals", "min_depth", "notes", "owners",
                   "entrance", "rules_divergence", "rules_review", "model_divergence", "calibration",
                   "rules_intake", "rules_review_triage", "model_review", "modeling_brief", "defect_ledger", "brief_coverage"]


def load_policy(path):
    doc = load_document(path)
    _keys(doc, ["schema_version", "kind", "modules"], ["risk_classes", "tiers", "unclassified", "notes", "upstream"], "policy")
    require(doc["schema_version"] == 1 and doc["kind"] == "fv-policy", "unsupported policy (schema_version 1, kind fv-policy)")
    risks = dict(DEFAULT_RISKS)
    risks.update(doc.get("risk_classes") or {})
    tiers = dict(DEFAULT_TIERS)
    for name, spec in (doc.get("tiers") or {}).items():
        merged = dict(DEFAULT_TIERS.get(name, DEFAULT_TIERS["core"]))
        merged.update(spec)
        tiers[name] = merged
    for name, spec in risks.items():
        _keys(spec, ["min_level", "tier"], ["note"], "risk class " + name)
        require(spec["min_level"] in LEVELS and (spec["tier"] in tiers or spec["tier"] == "none"), "risk class %s: bad level or tier" % name)
    ids = set()
    for m in doc["modules"]:
        _keys(m, MODULE_KEYS, MODULE_OPTIONAL, "module")
        require(m["id"] not in ids, "duplicate module %s" % m["id"])
        ids.add(m["id"])
        require(m["risk"] in risks, "module %s: unknown risk class %s" % (m["id"], m["risk"]))
        require(m.get("entrance", "spec-first") in ("spec-first", "code-first"), "module %s: entrance must be spec-first|code-first" % m["id"])
        require(isinstance(m["paths"], list) and m["paths"], "module %s: paths must be a nonempty list" % m["id"])
        level = risks[m["risk"]]["min_level"]
        if LEVELS.index(level) >= 2:
            require(m.get("contract") and m.get("model"), "module %s (%s) needs a contract and a model" % (m["id"], level))
            need = ["rules_intake", "rules_divergence", "rules_review", "model_divergence", "model_review"]
            require(all(m.get(k) for k in need),
                    "module %s (%s): AI-generated rules and model need their evidence (%s)" % (m["id"], level, ", ".join(need)))
            if m.get("entrance") == "code-first":
                require(m.get("calibration"), "module %s: code-first needs the as-is model's calibration receipt" % m["id"])
                require(m.get("modeling_brief") and m.get("defect_ledger") and m.get("brief_coverage"),
                        "module %s: code-first needs the Specula modeling brief, defect ledger and brief coverage" % m["id"])
        if LEVELS.index(level) >= 3:
            require(m.get("source_map") and (m.get("traces") or m.get("trace_command")),
                    "module %s (%s) needs a source map and implementation traces" % (m["id"], level))
    require(doc.get("unclassified", "review") in ("review", "ignore"), "unclassified must be review|ignore")
    return {"doc": doc, "risks": risks, "tiers": tiers, "modules": doc["modules"], "unclassified": doc.get("unclassified", "review"),
            "upstream": doc.get("upstream")}


def module_files(m):
    return [m[k] for k in ("contract", "model", "source_map") if m.get(k)]


def impact(policy, root, base):
    root = Path(root)
    changed = changed_files(root, base)
    out, claimed = [], set()
    for m in policy["modules"]:
        hits = [f for f in changed if any(glob_match(f, p) for p in m["paths"])]
        formal = [f for f in changed if f in module_files(m) or (m.get("source_map") and f == str(Path(m["source_map"]).with_suffix("")) + ".lock.json")]
        claimed |= set(hits) | set(formal)
        if hits or formal:
            risk = policy["risks"][m["risk"]]
            out.append({"id": m["id"], "risk": m["risk"], "min_level": risk["min_level"], "tier": risk["tier"],
                        "code_changes": hits, "formal_changes": formal,
                        "contract_changed": bool(m.get("contract") and m["contract"] in changed),
                        "model_changed": bool(m.get("model") and m["model"] in changed)})
    unclassified = [f for f in changed if f not in claimed]
    return {"base": base, "changed": changed, "modules": out, "unclassified": unclassified,
            "unclassified_policy": policy["unclassified"]}


def approved(approvals_path, contract_digest):
    """An explicit approval record for exactly this contract digest (append-only JSONL)."""
    p = Path(approvals_path)
    if not p.is_file():
        return None
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("contract_digest") == contract_digest and rec.get("approved_by") and rec.get("signer_kind") in ("human", "delegated_agent"):
            if rec["signer_kind"] == "delegated_agent" and not rec.get("authorization"):
                continue
            return rec
    return None


def approve(approvals_path, contract, by, reason, signer_kind="human", authorization=None, previous=None):
    from .receipt import now
    require(by and reason, "an approval needs --by and --reason")
    require(signer_kind in ("human", "delegated_agent"), "signer kind must be human|delegated_agent")
    require(signer_kind == "human" or authorization, "a delegated approval must quote the human authorization")
    rec = {"contract_id": contract.id, "contract_version": contract.version, "contract_digest": contract.digest,
           "properties_digest": contract.properties_digest, "approved_by": by, "signer_kind": signer_kind,
           "authorization": authorization, "reason": reason, "previous_digest": previous, "at": now()}
    p = Path(approvals_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
    return rec
