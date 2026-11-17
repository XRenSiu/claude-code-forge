"""Negative-sensitivity evidence: deliberately broken designs must be caught.

Declared mutants (in the model's `mutants:` list) are reviewed design defects with the
properties expected to catch them; each must be KILLED by one of those properties, not by
a load error, a deadlock or an unrelated rule. Auto mutants (drop a guard, drop one guard
conjunct, skip one update) measure how much of the model the contract actually constrains;
survivors are reported, never silently counted as kills.
"""
import ast
import copy

from .checker import check
from .spec import MUTATION_OPS, model_from_doc
from .values import FvError, require


def apply_edits(doc, edits):
    doc = copy.deepcopy(doc)
    require(isinstance(edits, list) and edits, "a mutant needs a nonempty edits list")
    for i, edit in enumerate(edits):
        require(isinstance(edit, dict) and edit.get("op") in MUTATION_OPS, "edit %d: op must be one of %s" % (i, MUTATION_OPS))
        op = edit["op"]
        actions = doc["actions"]
        if op in ("set_guard", "set_update", "drop_update", "drop_action"):
            require(edit.get("action") in actions, "edit %d: unknown action %r" % (i, edit.get("action")))
        if op == "set_guard":
            actions[edit["action"]]["guard"] = edit["expr"]
        elif op == "set_update":
            actions[edit["action"]].setdefault("update", {})[edit["var"]] = edit["expr"]
        elif op == "drop_update":
            upd = actions[edit["action"]].get("update") or {}
            require(edit.get("var") in upd, "edit %d: action does not update %r" % (i, edit.get("var")))
            del upd[edit["var"]]
        elif op == "drop_action":
            del actions[edit["action"]]
            require(actions, "edit %d: cannot drop the last action" % i)
            doc["fairness"] = [f for f in doc.get("fairness") or [] if f["action"] != edit["action"]]
        elif op == "add_action":
            require(edit.get("action") not in actions, "edit %d: action already exists" % i)
            actions[edit["action"]] = edit["spec"]
        elif op == "set_init":
            require(edit.get("var") in doc["variables"], "edit %d: unknown variable" % i)
            doc["variables"][edit["var"]] = {"init": edit["expr"]}
        elif op == "drop_fairness":
            doc["fairness"] = [f for f in doc.get("fairness") or [] if f["action"] != edit["action"]]
        elif op == "set_observable":
            require(edit.get("observable") in (doc.get("observables") or {}), "edit %d: unknown observable" % i)
            doc["observables"][edit["observable"]] = edit["expr"]
        elif op == "set_constant":
            require(edit.get("name") in (doc.get("constants") or {}), "edit %d: unknown constant" % i)
            doc["constants"][edit["name"]] = edit["value"]
    doc.pop("mutants", None)
    return doc


def _conjuncts(source):
    tree = ast.parse(source.strip(), mode="eval").body
    if isinstance(tree, ast.BoolOp) and isinstance(tree.op, ast.And):
        return [ast.unparse(v) for v in tree.values]
    return [source.strip()]


def auto_mutants(doc):
    out = []
    for name in sorted(doc["actions"]):
        spec = doc["actions"][name]
        guard = spec.get("guard")
        if guard:
            out.append({"id": "auto:%s:guard=True" % name, "edits": [{"op": "set_guard", "action": name, "expr": "True"}]})
            parts = _conjuncts(guard)
            if len(parts) > 1:
                for k in range(len(parts)):
                    rest = " and ".join("(%s)" % p for j, p in enumerate(parts) if j != k)
                    out.append({"id": "auto:%s:drop-conjunct-%d" % (name, k), "dropped": parts[k],
                                "edits": [{"op": "set_guard", "action": name, "expr": rest}]})
        for var in sorted(spec.get("update") or {}):
            out.append({"id": "auto:%s:skip-update-%s" % (name, var), "edits": [{"op": "drop_update", "action": name, "var": var}]})
    return out


def _failed(result):
    return {p["property"] for p in result["properties"] if p["status"] == "FAIL" and p["origin"] == "contract"}


def run_mutant(doc, contract, mutant, settings):
    """A mutant only needs its first violation: stop early, and only on the rules it targets."""
    record = {"id": mutant["id"], "description": mutant.get("description"), "edits": mutant["edits"]}
    expected = list(mutant.get("expect_killed_by") or [])
    record["expect_killed_by"] = expected
    s = dict(settings, stop_on_first=True)
    try:
        mmodel = model_from_doc(apply_edits(doc, mutant["edits"]), contract)
        if expected:
            result, _, _ = check(mmodel, only=set(expected), **s)
            hit = sorted(_failed(result) & set(expected))
            if not hit and result["complete"] and result["verdict"] != "ERROR":
                result, _, _ = check(mmodel, **s)   # classify: caught by another rule, or survived
        else:
            result, _, _ = check(mmodel, **s)
            hit = sorted(_failed(result))
    except FvError as error:
        record.update(status="ERROR", reason="mutant does not load or evaluate: %s" % error)
        return record
    failed = sorted(_failed(result))
    record.update(failed_properties=failed, mutant_verdict=result["verdict"], deadlock=result["deadlock"]["status"])
    if result["verdict"] == "ERROR":
        record.update(status="ERROR", reason=result["error"])
    elif hit:
        record.update(status="KILLED", killed_by=hit)
    elif expected and (failed or result["deadlock"]["status"] == "FAIL"):
        record.update(status="KILLED_BY_OTHER", reason="caught only by %s, not by the expected %s" % (failed or ["deadlock"], expected))
    elif result["complete"]:
        record.update(status="SURVIVED")
    else:
        record.update(status="UNKNOWN", reason="mutant exploration truncated (%s)" % ", ".join(result["truncation"]))
    return record


AUTO_MAX_STATES = 50000


def run_mutants(model, auto=False, settings=None, only_ids=None):
    settings = dict(settings or {})
    settings.pop("keep_graph", None)
    doc = model.doc
    declared = []
    ids = set()
    for i, m in enumerate(model.mutants):
        require(isinstance(m, dict) and isinstance(m.get("id"), str) and m["id"], "mutants[%d] needs an id" % i)
        require(m["id"] not in ids, "duplicate mutant id %s" % m["id"])
        ids.add(m["id"])
        unknown = set(m.get("expect_killed_by") or []) - {p.id for p in model.contract.properties}
        require(not unknown, "mutant %s expects unknown properties %s" % (m["id"], sorted(unknown)))
        require(m.get("expect_killed_by"), "mutant %s must name the properties expected to catch it" % m["id"])
        if only_ids is None or m["id"] in only_ids:
            declared.append(m)
    results = [run_mutant(doc, model.contract, m, settings) for m in declared]
    for m, r in zip(declared, results):
        r["required"] = bool(m.get("required", True))
    out = {"declared": results,
           "declared_summary": {"total": len(results), "killed": sum(r["status"] == "KILLED" for r in results),
                                "required_survivors": [r["id"] for r in results if r["required"] and r["status"] != "KILLED"]}}
    if auto:
        auto_settings = dict(settings)
        auto_settings["max_states"] = min(settings.get("max_states") or AUTO_MAX_STATES, AUTO_MAX_STATES)
        autos = [run_mutant(doc, model.contract, m, auto_settings) for m in auto_mutants(doc)]
        for a, spec in zip(autos, auto_mutants(doc)):
            if spec.get("dropped"):
                a["dropped_conjunct"] = spec["dropped"]
        killed = sum(r["status"] == "KILLED" for r in autos)
        out["auto"] = autos
        out["auto_summary"] = {"total": len(autos), "killed": killed,
                               "score_permille": (killed * 1000 // len(autos)) if autos else None,
                               "survivors": [r["id"] for r in autos if r["status"] != "KILLED"]}
    return out
