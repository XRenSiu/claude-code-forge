"""Receipts: what ran, on which exact inputs, with what result, and what it may claim.

Evidence levels (never merged into one word "verified"):
  E0 static review      lint / reading            may claim: reviewed           not: correct
  E1 simulation         random walks, quint run   may claim: sampled paths ok   not: all paths ok
  E2 model check        fvkit check, TLC, Apalache may claim: this model/bound/assumptions has
                        no violating path          not: the production code is bug-free
  E3 implementation     trace conformance, MBT    may claim: the real code passed these checks
                                                   not: every input/execution is proven
  E4 code-level proof   (external: Lean/Kani/…)   may claim: property proven for covered code
                                                   not: unmodelled services/environment are safe
A receipt is integrity evidence. It does not authenticate who ran it; protected execution
and signing stay with the control service.
"""
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import VERSION
from .values import FvError, digest, require, sha_bytes

LEVELS = ("E0", "E1", "E2", "E3", "E4")
CLAIMS = {
    "E0": ("static review of the documents was completed", "the design or code is correct"),
    "E1": ("the sampled behaviours showed no violation", "all possible behaviours are free of violations"),
    "E2": ("for this model, these constants/bounds and these assumptions no behaviour violates the checked properties",
           "the production implementation is free of defects"),
    "E3": ("the real implementation passed these specific, recorded checks against the model",
           "all inputs and all real executions are proven correct"),
    "E4": ("under the stated assumptions the covered code satisfies the property (machine-checked proof)",
           "unmodelled services, environment and the whole system are reliable"),
}
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z")
COMMANDS = ("lint", "check", "simulate", "mutate", "qualify", "trace", "conform", "source-map", "diff-contract",
            "external", "ci", "gen-tests")


def engine_identity():
    here = Path(__file__).resolve().parent
    files = sorted(p for p in here.glob("*.py"))
    return {"name": "fvkit", "version": VERSION,
            "digest": digest([[p.name, sha_bytes(p.read_bytes())] for p in files])}


def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def level_at_least(level, minimum):
    return LEVELS.index(level) >= LEVELS.index(minimum)


def make(command, inputs, settings, result, verdict, level, started):
    require(command in COMMANDS and level in LEVELS, "internal: bad receipt kind")
    may, may_not = CLAIMS[level]
    return {"schema_version": 1, "kind": "fv-receipt", "command": command, "invocation_id": str(uuid.uuid4()),
            "authority": "local_advisory", "engine": engine_identity(), "inputs": inputs, "settings": settings,
            "result": result, "verdict": verdict, "evidence_level": level,
            "claims": {"may_claim": may if verdict in ("PASS", "BOUNDED_PASS", "QUALIFIED", "CONFORMS", "FRESH", "NOT_WEAKENED", "SATISFIED") else None,
                       "may_not_claim": may_not},
            "started_at": started, "finished_at": now()}


def write(path, receipt):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:  # receipts are never overwritten
        stream.write(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return str(path)


def load(path):
    from .spec import load_document
    doc = load_document(path)
    require(isinstance(doc, dict) and doc.get("kind") == "fv-receipt", "not an fv-receipt: %s" % path)
    return doc


# ---- validation ---------------------------------------------------------------------------
REQUIRED = ("schema_version", "kind", "command", "invocation_id", "authority", "engine", "inputs", "settings",
            "result", "verdict", "evidence_level", "claims", "started_at", "finished_at")
CHECK_VERDICTS = ("PASS", "BOUNDED_PASS", "FAIL", "INCOMPLETE", "ERROR")


def _shape(r):
    missing = [k for k in REQUIRED if k not in r]
    require(not missing, "receipt is missing %s" % missing)
    unknown = set(r) - set(REQUIRED)
    require(not unknown, "receipt has unknown fields %s" % sorted(unknown))
    require(r["schema_version"] == 1 and r["kind"] == "fv-receipt", "unsupported receipt")
    require(r["authority"] == "local_advisory", "an fvkit receipt is always local_advisory")
    require(isinstance(r["invocation_id"], str) and UUID.fullmatch(r["invocation_id"]), "missing invocation identity")
    require(r["command"] in COMMANDS and r["evidence_level"] in LEVELS, "unknown command or evidence level")
    eng = r["engine"]
    require(isinstance(eng, dict) and isinstance(eng.get("digest"), str), "missing engine identity")


def _check_verdict(result):
    props = result["properties"]
    failed = any(p["status"] == "FAIL" for p in props) or result["deadlock"]["status"] == "FAIL"
    if result.get("error"):
        return "ERROR"
    if failed:
        return "FAIL"
    if result["complete"]:
        require(all(p["status"] == "PASS" for p in props), "complete run with undecided properties")
        return "PASS"
    return "BOUNDED_PASS" if result["exhaustive_depth"] >= 0 else "INCOMPLETE"


def _replay_check(model, result):
    """Every counterexample and witness in a check result must be a real model behaviour."""
    from .checker import Instance, replay
    from .expr import truth
    props = {p.id: p for p in model.contract.properties}
    for rec in result["properties"]:
        ce = rec.get("counterexample") or rec.get("witness")
        if not ce:
            continue
        if ce["kind"] == "lasso":
            sem, states = replay(model, ce["prefix"] + ce["cycle"])
            k = ce["loop_to_step"]
            require(0 <= k < len(states), "%s: lasso loop index out of range" % rec["id"])
            if ce["cycle"]:
                require(states[-1] == states[k] or sem.state_json(states[-1]) == sem.state_json(states[k]),
                        "%s: lasso cycle does not return to its loop state" % rec["id"])
            else:
                require(ce["stutter"], "%s: lasso without a cycle must be a stutter" % rec["id"])
            continue
        sem, states = replay(model, ce["steps"])
        if rec["origin"] != "contract":
            continue
        prop = props[rec["property"]]
        binding = _binding_from_id(rec["id"], prop, model)
        inst = Instance(prop, binding)
        last = sem.observe(sem.env(states[-1]))
        if ce["kind"] == "state":
            value = truth(prop.expr(inst.env(model.constants, last)), prop.expr.source)
            want = rec["kind"] == "reachable"
            require(value is want, "%s: recorded %s does not %s the property at its last state" %
                    (rec["id"], "witness" if want else "counterexample", "satisfy" if want else "violate"))
        elif ce["kind"] == "transition":
            from .values import FMap
            pre = sem.observe(sem.env(states[-2]))
            env = inst.env(model.constants, {})
            env["pre"], env["post"] = FMap(pre.items()), FMap(last.items())
            require(truth(prop.expr(env), prop.expr.source) is False, "%s: recorded transition does not violate the property" % rec["id"])


def _binding_from_id(iid, prop, model):
    from .checker import instances
    for inst in instances(model.contract, model.constants):
        if inst.id == iid:
            return inst.binding
    raise FvError("receipt names an unknown property instance %s" % iid)


def _same_result(a, b, path="result"):
    """Deterministic fields of two check results must agree (timing excluded)."""
    def strip(x):
        if isinstance(x, dict):
            return {k: strip(v) for k, v in x.items() if k not in ("millis",)}
        if isinstance(x, list):
            return [strip(v) for v in x]
        return x
    require(strip(a) == strip(b), "re-execution differs from the recorded %s" % path)


def validate(r, model=None, contract=None, rerun=False, min_level=None, expect_verdicts=None, base_dir=None, traces=None,
             allow_paths=True):
    """Re-verify a receipt. Raises FvError; returns a summary dict on success.

    `traces` maps a trace digest to its bytes; with --rerun a conformance receipt is then
    re-decided from those raw traces instead of being believed. A protected gate passes
    allow_paths=False: paths written inside a receipt are candidate-controlled and are
    never opened there — only evidence-store bytes count.
    """
    _shape(r)
    if min_level is not None:
        require(level_at_least(r["evidence_level"], min_level), "evidence level %s is below the required %s" % (r["evidence_level"], min_level))
    if expect_verdicts is not None:
        require(r["verdict"] in expect_verdicts, "receipt verdict %s is not one of %s" % (r["verdict"], expect_verdicts))
    inputs = r["inputs"]
    if contract is not None:
        c = inputs.get("contract") or {}
        require(c.get("digest") == contract.digest and c.get("properties_digest") == contract.properties_digest,
                "receipt was produced for a different contract")
    if model is not None:
        require((inputs.get("model") or {}).get("digest") == model.digest, "receipt was produced for a different model")
    cmd = r["command"]
    if cmd == "check":
        require(r["verdict"] in CHECK_VERDICTS and r["verdict"] == _check_verdict(r["result"]), "check verdict contradicts its results")
        require(r["evidence_level"] == "E2", "a model check is E2 evidence")
        if model is not None:
            _replay_check(model, r["result"])
    elif cmd == "qualify":
        res = r["result"]
        require(r["verdict"] == ("QUALIFIED" if not res["reasons"] else "NOT_QUALIFIED"), "qualification verdict contradicts its reasons")
        require(res["check"]["verdict"] == _check_verdict(res["check"]), "nested check verdict contradicts its results")
        if model is not None:
            _replay_check(model, res["check"])
    elif cmd == "simulate":
        require(r["evidence_level"] == "E1" and r["verdict"] in ("NO_VIOLATION_SAMPLED", "FAIL"), "a simulation is E1 and never PASS")
    elif cmd == "conform":
        res = r["result"]
        require(r["evidence_level"] == "E3", "conformance is E3 evidence")
        from .qualify import conform
        again = conform(model, res["source_map"], res["traces"], res.get("replays"))
        require(again["verdict"] == r["verdict"] and again["reasons"] == res["reasons"],
                "conformance verdict contradicts its source map / trace results")
        require(isinstance(res.get("source"), dict) and "head" in res["source"], "conformance receipt lacks its source binding")
    elif cmd == "trace":
        require(r["evidence_level"] == "E3", "trace conformance is E3 evidence")
        require(r["verdict"] == r["result"]["verdict"], "trace verdict contradicts its results")
    elif cmd == "external":
        from .external import reparse
        reparse(r, base_dir)
    if rerun:
        require(model is not None, "--rerun needs the model and contract")
        require(r["engine"]["digest"] == engine_identity()["digest"],
                "receipt was produced by a different fvkit build; rerun with the current engine instead of validating")
        if cmd == "check":
            from .checker import check
            s = r["settings"]
            again, _, _ = check(model, max_states=s["max_states"], max_depth=s["max_depth"], time_seconds=s["time_seconds"],
                                symmetry=s["symmetry"], stop_on_first=s["stop_on_first"], only=set(s["only"]) if s["only"] else None)
            require(r["result"]["stats"]["states"] == again["stats"]["states"], "re-execution explored a different state count")
            _same_result(r["result"], again)
        elif cmd == "qualify":
            from .qualify import qualify
            again = qualify(model, r["settings"])
            require(again["verdict"] == r["verdict"] and again["result"]["reasons"] == r["result"]["reasons"],
                    "re-qualification disagrees with the receipt")
            _same_result(r["result"]["check"], again["result"]["check"], "qualification check")
            mutant_view = lambda res: [(m["id"], m["status"], m.get("killed_by")) for m in res["declared"]]  # noqa: E731
            require(mutant_view(r["result"]["mutants"]) == mutant_view(again["result"]["mutants"]),
                    "re-execution of the mutants differs from the receipt")
        elif cmd in ("conform", "trace"):
            from .trace import check_trace, parse_trace
            listed = r["result"]["traces"]["traces"] if cmd == "conform" else r["result"]["traces"]
            require(listed, "receipt lists no traces to re-check")
            for t in listed:
                data = (traces or {}).get(t["trace"]["digest"])
                recorded = Path(t["trace"]["path"])
                candidates = ([recorded] + ([Path(base_dir) / recorded, Path(base_dir) / recorded.name] if base_dir else [])) if allow_paths else []
                for p in candidates if data is None else []:
                    if p.is_file() and sha_bytes(p.read_bytes()) == t["trace"]["digest"]:
                        data = p.read_bytes()
                        break
                require(data is not None and sha_bytes(data) == t["trace"]["digest"], "raw trace %s is not available for re-checking" % t["trace"]["path"])
                header, events = parse_trace(data, t["trace"]["path"])
                again = check_trace(model, events, r["settings"].get("hidden_steps", 0), label=Path(t["trace"]["path"]).name)
                require(again["verdict"] == t["verdict"], "re-checking %s gives %s, receipt says %s" % (t["trace"]["path"], again["verdict"], t["verdict"]))
    return {"valid": True, "command": cmd, "verdict": r["verdict"], "evidence_level": r["evidence_level"],
            "invocation_id": r["invocation_id"], "authority": "local_advisory", "reexecuted": bool(rerun)}
