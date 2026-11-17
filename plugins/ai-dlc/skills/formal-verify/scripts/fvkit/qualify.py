"""Model qualification (the machine half of the design gate) and implementation conformance.

QUALIFIED requires, all at once:
  - the checker really ran to completion on the declared scope (or, if the policy allows
    `bounded`, every behaviour up to `min_depth` was explored) and found no violation;
  - every `reachable` witness was reached and no leads-to property is vacuous;
  - every action of the model fires somewhere (no dead actions);
  - at least one declared mutant exists and every required mutant is KILLED by one of
    the properties it names (proof that the rules can see the defects they are for).
CONFORMS requires: a FRESH source map, every given trace conforming to the SAME model,
and (optionally) the recorded counterexamples replayed as refused behaviours.
"""
from .checker import check
from .mutate import run_mutants
from .values import require


def qualify(model, settings=None):
    settings = dict(settings or {})
    allow_bounded = settings.pop("allow_bounded", False)
    min_depth = settings.pop("min_depth", None)
    auto = settings.pop("auto_mutants", False)
    check_settings = {k: settings.get(k) for k in ("max_states", "max_depth", "time_seconds", "symmetry") if settings.get(k) is not None}
    result, _, _ = check(model, **check_settings)
    reasons = []
    v = result["verdict"]
    if v == "ERROR":
        reasons.append("model does not evaluate: %s" % result["error"])
    elif v == "FAIL":
        failed = [p["id"] for p in result["properties"] if p["status"] == "FAIL"]
        if result["deadlock"]["status"] == "FAIL":
            failed.append("deadlock")
        reasons.append("counterexamples found: %s (triage them; do not weaken the contract)" % failed)
    elif v == "BOUNDED_PASS":
        if not allow_bounded:
            reasons.append("exploration was bounded (exhaustive to depth %d); the policy requires a complete run" % result["exhaustive_depth"])
        elif min_depth is not None and result["exhaustive_depth"] < min_depth:
            reasons.append("bounded exploration reached depth %d < required %d" % (result["exhaustive_depth"], min_depth))
    elif v == "INCOMPLETE":
        reasons.append("nothing was explored exhaustively")
    for p in result["properties"]:
        if p.get("vacuous"):
            reasons.append("%s is vacuous: its from-condition is never reachable" % p["id"])
        if p["kind"] == "reachable" and p["status"] != "PASS":
            reasons.append("witness %s not reached" % p["id"])
    if result["coverage"]["dead_actions"] and v in ("PASS", "BOUNDED_PASS"):
        if result["complete"]:
            reasons.append("dead actions (never change state): %s" % result["coverage"]["dead_actions"])
    mut = run_mutants(model, auto=auto, settings=check_settings)
    if not mut["declared"]:
        reasons.append("no declared mutant: show that at least one deliberate design defect is caught")
    for r in mut["declared"]:
        if r["required"] and r["status"] != "KILLED":
            reasons.append("required mutant %s %s (%s)" % (r["id"], r["status"], r.get("reason") or "expected %s" % r["expect_killed_by"]))
    verdict = "QUALIFIED" if not reasons else "NOT_QUALIFIED"
    return {"verdict": verdict, "result": {"check": result, "mutants": mut, "reasons": reasons},
            "settings": dict(check_settings, allow_bounded=allow_bounded, min_depth=min_depth, auto_mutants=auto)}


def conform(model, source_map_result, trace_result, replays=None):
    reasons = []
    if source_map_result is None:
        reasons.append("no source map: model actions are not tied to code")
    elif source_map_result["status"] != "FRESH":
        sm = source_map_result
        detail = sm["issues"] + sm["stale"] + (["drifted: %s" % sm["drifted_files"]] if sm["drifted_files"] else [])
        reasons.append("source map is %s: %s" % (sm["status"], "; ".join(detail)))
    require(trace_result is not None, "conformance needs at least one implementation trace")
    if not trace_result["traces"]:
        reasons.append("no implementation traces")
    for t in trace_result["traces"]:
        if t["verdict"] != "CONFORMS":
            reasons.append("trace %s is %s at line %s: %s" % (t["trace"]["path"], t["verdict"], t.get("failed_at_line"), t.get("reason")))
        for v in t["property_violations"]:
            reasons.append("trace %s violates %s at %s" % (t["trace"]["path"], v["property"], v["at"]))
    for rid in replays or []:
        if not any((t["trace"].get("header") or {}).get("vector") == rid and t["verdict"] == "CONFORMS" for t in trace_result["traces"]):
            reasons.append("counterexample regression %s has no conforming trace" % rid)
    return {"verdict": "CONFORMS" if not reasons else "NONCONFORMANT", "reasons": reasons}
