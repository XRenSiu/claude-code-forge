"""Trace conformance: does a behaviour recorded from the REAL implementation fit the model?

An implementation (test harness, instrumented service, replayed log) writes JSON Lines:

    {"kind": "fv-trace", "schema_version": 1, "model": "<model id>"}        optional header
    {"init": true, "observed": {...}}                                       optional first event
    {"action": "buy", "params": {"u": "alice"}, "observed": {...}}          a step that happened
    {"action": "buy", "params": {"u": "bob"}, "rejected": true, "observed": {...}}  refused step

`observed` may name any subset of the contract observables. Matching keeps the set of
model states consistent with everything seen so far (partial observation, nondeterminism);
`hidden_steps` allows unobserved internal steps between events. A refused step must be
disabled in the model and leave the observables unchanged. Fully observed events are also
monitored directly against the contract's invariants and transition properties.
"""
import json
from pathlib import Path

from .checker import Instance, instances
from .expr import truth
from .semantics import Semantics, label_json
from .values import FMap, FvError, ckey, from_json, require, show

MAX_EVENTS = 100000
MAX_TRACE_BYTES = 64 * 1024 * 1024


def load_trace(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), "trace is not a regular file: %s" % path)
    require(path.stat().st_size <= MAX_TRACE_BYTES, "trace larger than 64 MiB: %s" % path)
    return parse_trace(path.read_bytes(), str(path))


def parse_trace(data, path="trace"):
    require(len(data) <= MAX_TRACE_BYTES, "trace larger than 64 MiB: %s" % path)
    header, events = None, []
    for n, line in enumerate(data.decode("utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line, parse_constant=lambda c: (_ for _ in ()).throw(ValueError("non-finite")))
        except ValueError as error:
            raise FvError("%s:%d: invalid JSON (%s)" % (path, n, error)) from None
        require(isinstance(obj, dict), "%s:%d: each line must be an object" % (path, n))
        if obj.get("kind") == "fv-trace":
            require(header is None and not events, "%s:%d: header must be the first line" % (path, n))
            header = obj
            continue
        unknown = set(obj) - {"init", "action", "params", "observed", "rejected", "note", "at"}
        require(not unknown, "%s:%d: unknown fields %s" % (path, n, sorted(unknown)))
        require(isinstance(obj.get("observed", {}), dict), "%s:%d: observed must be an object" % (path, n))
        require(obj.get("init") or obj.get("action") or obj.get("observed"), "%s:%d: empty event" % (path, n))
        obj["_line"] = n
        events.append(obj)
        require(len(events) <= MAX_EVENTS, "trace has more than %d events" % MAX_EVENTS)
    require(events, "trace has no events: %s" % path)
    return header, events


def _normalise(contract, observed, where):
    out = {}
    for k, v in observed.items():
        require(k in contract.observables, "%s: unknown observable %r" % (where, k))
        try:
            out[k] = from_json(v, contract.observables[k]["type"])
        except FvError as error:
            raise FvError("%s: observable %s: %s" % (where, k, error)) from None
    return out


def _matches(obs, observed):
    return all(ckey(obs[k]) == ckey(v) for k, v in observed.items())


def _monitor(model, insts, observed, previous, where, violations):
    full = set(observed) == set(model.contract.observables)
    if not full:
        return
    for inst in insts:
        if inst.kind == "invariant":
            if not truth(inst.prop.expr(inst.env(model.constants, observed)), inst.prop.expr.source):
                violations.append({"property": inst.id, "at": where, "observed": {k: show(v) for k, v in observed.items()}})
        elif inst.kind == "transition" and previous is not None:
            env = inst.env(model.constants, {})
            env["pre"], env["post"] = FMap(previous.items()), FMap(observed.items())
            if not truth(inst.prop.expr(env), inst.prop.expr.source):
                violations.append({"property": inst.id, "at": where})


def check_trace(model, events, hidden_steps=0, max_candidates=10000, label="trace"):
    require(type(hidden_steps) is int and 0 <= hidden_steps <= 8, "hidden_steps must be 0..8")
    sem = Semantics(model, symmetry=False)
    contract = model.contract
    insts = [i for i in instances(contract, model.constants) if i.kind in ("invariant", "transition")]
    cands = {}
    for s in sem.initial_states(max_candidates):
        cands[ckey(s)] = s
    violations, previous_full = [], None
    start = 0
    if events[0].get("init"):
        observed = _normalise(contract, events[0].get("observed", {}), "%s:%d" % (label, events[0]["_line"]))
        cands = {k: s for k, s in cands.items() if _matches(sem.observe(sem.env(s)), observed)}
        _monitor(model, insts, observed, None, "line %d" % events[0]["_line"], violations)
        previous_full = observed if set(observed) == set(contract.observables) else None
        if not cands:
            return _result("NONCONFORMANT", events, 0, sem, {}, observed, "no initial state matches the first observation", violations)
        start = 1
    for idx in range(start, len(events)):
        ev = events[idx]
        where = "%s:%d" % (label, ev["_line"])
        observed = _normalise(contract, ev.get("observed", {}), where)
        params = ev.get("params")
        require(params is None or isinstance(params, dict), where + ": params must be an object")
        frontier = dict(cands)
        layer = dict(cands)
        for _ in range(hidden_steps):
            nxt = {}
            for s in layer.values():
                for _, t in sem.successors(s, sem.env(s), count=False):
                    k = ckey(t)
                    if k not in frontier:
                        frontier[k] = nxt[k] = t
            layer = nxt
            require(len(frontier) <= max_candidates * 10, where + ": too many hidden-step candidates")
        new = {}
        for s in frontier.values():
            env = sem.env(s)
            if ev.get("rejected"):
                require(ev.get("action"), where + ": a rejected event must name its action")
                action = sem.action(ev["action"])
                enabled = False
                for b in sem.bindings(action, env):
                    if params is not None and label_json((action.name, b))["params"] != params:
                        continue
                    if sem.apply(action, b, s, env) is not None:
                        enabled = True
                        break
                if not enabled and _matches(sem.observe(env), observed):
                    new[ckey(s)] = s
                continue
            for lbl, t in sem.successors(s, env, count=False):
                if ev.get("action") and lbl[0] != ev["action"]:
                    continue
                if params is not None and label_json(lbl)["params"] != params:
                    continue
                if _matches(sem.observe(sem.env(t)), observed):
                    new[ckey(t)] = t
        _monitor(model, insts, observed, previous_full, "line %d" % ev["_line"], violations)
        previous_full = observed if set(observed) == set(contract.observables) else None
        if not new:
            return _result("NONCONFORMANT", events, idx, sem, frontier, observed,
                           "no model step from any consistent state explains this event", violations, ev)
        if len(new) > max_candidates:
            return _result("INCOMPLETE", events, idx, sem, {}, observed, "candidate set exceeds max_candidates", violations, ev)
        cands = new
    verdict = "NONCONFORMANT" if violations else "CONFORMS"
    out = _result(verdict, events, None, sem, {}, None, None, violations)
    out["final_candidates"] = len(cands)
    return out


def _result(verdict, events, failed_at, sem, frontier, observed, reason, violations, event=None):
    out = {"verdict": verdict, "events": len(events), "failed_at_event": failed_at,
           "failed_at_line": None if failed_at is None else events[failed_at]["_line"],
           "reason": reason, "property_violations": violations}
    if reason and verdict != "CONFORMS":
        expected = []
        for s in list(frontier.values())[:5]:
            env = sem.env(s)
            options = []
            for lbl, t in sem.successors(s, env, count=False):
                options.append({"action": label_json(lbl), "observed": sem.obs_json(sem.observe(sem.env(t)))})
                if len(options) >= 6:
                    break
            expected.append({"state": sem.state_json(s), "observed": sem.obs_json(sem.observe(env)), "possible_next": options})
        out["diagnostic"] = {"event": {k: v for k, v in (event or {}).items() if k != "_line"},
                             "observed": {k: show(v) for k, v in (observed or {}).items()},
                             "consistent_model_states": expected}
    return out


def check_files(model, paths, hidden_steps=0, max_candidates=10000):
    from .values import sha_bytes
    results = []
    for p in paths:
        header, events = load_trace(p)
        if header and header.get("model"):
            require(header["model"] == model.id, "%s was recorded for model %s, not %s" % (p, header["model"], model.id))
        r = check_trace(model, events, hidden_steps, max_candidates, label=Path(p).name)
        r["trace"] = {"path": str(p), "digest": sha_bytes(Path(p).read_bytes()), "header": header}
        results.append(r)
    verdict = "CONFORMS" if results and all(r["verdict"] == "CONFORMS" for r in results) else \
        "NONCONFORMANT" if any(r["verdict"] == "NONCONFORMANT" for r in results) else "INCOMPLETE"
    return {"verdict": verdict, "traces": results}


__all__ = ["load_trace", "check_trace", "check_files", "Instance"]
