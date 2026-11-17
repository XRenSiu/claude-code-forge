"""Explicit-state model checker (breadth-first, deterministic).

What a result may claim is encoded in it:
- PASS          complete exploration of the declared constants; every property decided.
- BOUNDED_PASS  no violation in the explored part; `exhaustive_depth` says which behaviour
                lengths were covered completely. Liveness and witnesses stay UNKNOWN.
- FAIL          at least one property, model invariant or deadlock check has a counterexample
                (shortest by construction for safety; a lasso for liveness).
- INCOMPLETE    nothing could be concluded (e.g. the time budget ran out at depth 0).
A bounded or incomplete run is never reported as PASS.
"""
import time

from .expr import Budget, BudgetExceeded, set_budget, truth
from .liveness import check_liveness
from .semantics import Semantics, invert, label_json
from .spec import LIVENESS_KINDS
from .values import FMap, FvError, ckey, require, show

DEFAULT_MAX_STATES = 200000


class Instance:
    """A property with its forall variables bound."""

    def __init__(self, prop, binding):
        self.prop, self.binding = prop, binding
        self.kind = prop.kind
        suffix = ",".join("%s=%s" % (k, show(v)) for k, v in binding)
        self.id = prop.id + ("[" + suffix + "]" if suffix else "")

    def env(self, consts, obs):
        e = dict(consts)
        e.update(obs)
        e.update(self.binding)
        return e


def instances(contract, consts):
    from .expr import _items
    out = []
    for prop in contract.properties:
        bindings = [()]
        for name, dom in prop.forall:
            nxt = []
            for b in bindings:
                env = dict(consts)
                env.update(b)
                for v in _items(dom(env)):
                    nxt.append(b + ((name, v),))
            bindings = nxt
        out.extend(Instance(prop, b) for b in bindings)
    return out


def _pre_post(obs):
    return FMap(obs.items())


class Graph:
    """Explored state graph (states in BFS order)."""

    def __init__(self):
        self.states, self.index, self.parent, self.depth, self.obs = [], {}, [], [], []
        self.edges, self.enabled, self.initial = [], [], []

    def add(self, state, obs, parent, depth, keep_edges):
        sid = len(self.states)
        self.states.append(state)
        self.index[ckey(state)] = sid
        self.parent.append(parent)
        self.depth.append(depth)
        self.obs.append(obs)
        if keep_edges:
            self.edges.append([])
            self.enabled.append(frozenset())
        return sid


def check(model, max_states=None, max_depth=None, time_seconds=None, symmetry=True, keep_graph=False,
          stop_on_first=False, only=None):
    """Run the checker. `only` restricts contract properties to these ids (for mutants)."""
    started = time.monotonic()
    bounds = model.bounds
    max_states = max_states or bounds.get("max_states") or DEFAULT_MAX_STATES
    max_depth = max_depth if max_depth is not None else bounds.get("max_depth")
    time_seconds = time_seconds if time_seconds is not None else bounds.get("time_seconds")
    require(type(max_states) is int and 1 <= max_states <= 5000000, "max_states must be 1..5000000")
    require(max_depth is None or (type(max_depth) is int and max_depth >= 0), "max_depth must be a natural number")
    budget = Budget(time_seconds)
    set_budget(budget)
    contract = model.contract
    insts = [i for i in instances(contract, model.constants) if only is None or i.prop.id in only]
    liveness = [i for i in insts if i.kind in LIVENESS_KINDS]
    use_symmetry = bool(symmetry and model.symmetry)
    notes = []
    if use_symmetry:
        members = set()
        for name in model.symmetry:
            members |= set(model.constants[name])
        literals = set()
        for p in contract.properties:
            for e in p.exprs() + [d for _, d in p.forall]:
                literals |= e.constants()
        require(not (literals & members), "contract properties name symmetric values %s; disable symmetry" % sorted(literals & members))
        if liveness:
            notes.append("symmetry reduction disabled: it is unsound for liveness")
            use_symmetry = False
    sem = Semantics(model, symmetry=use_symmetry)
    keep_edges = keep_graph or bool(liveness)
    g = Graph()
    invariants = [i for i in insts if i.kind == "invariant"]
    transitions = [i for i in insts if i.kind == "transition"]
    witnesses = [i for i in insts if i.kind == "reachable"]
    status = {i.id: {"id": i.id, "property": i.prop.id, "kind": i.kind, "origin": "contract", "status": None,
                     "counterexample": None} for i in insts}
    model_inv = {k: {"id": k, "property": k, "kind": "invariant", "origin": "model", "status": None, "counterexample": None}
                 for k, _ in model.model_invariants}
    found_witness, violated_state, violated_edge = {}, {}, {}
    deadlock = None
    truncated, refused_depth, unexpanded_depth = [], None, None
    error = None
    i = 0

    def visit_state(sid, env):
        obs = g.obs[sid]
        for inst in invariants:
            if inst.id not in violated_state and not truth(inst.prop.expr(inst.env(model.constants, obs)), inst.prop.expr.source):
                violated_state[inst.id] = sid
        for k, expr in model.model_invariants:
            if k not in violated_state and not truth(expr(env), expr.source):
                violated_state[k] = sid
        for inst in witnesses:
            if inst.id not in found_witness and truth(inst.prop.expr(inst.env(model.constants, obs)), inst.prop.expr.source):
                found_witness[inst.id] = sid

    try:
        for state in sem.initial_states(max_states):
            canon, _ = sem.canon(state)
            if ckey(canon) in g.index:
                continue
            require(len(g.states) < max_states, "max_states smaller than the number of initial states")
            env = sem.env(canon)
            sid = g.add(canon, sem.observe(env), None, 0, keep_edges)
            g.initial.append(sid)
            visit_state(sid, env)
        while i < len(g.states):
            if stop_on_first and any(k in status for k in list(violated_state) + list(violated_edge)):
                truncated.append("stopped at first violation")
                unexpanded_depth = g.depth[i] if unexpanded_depth is None else min(unexpanded_depth, g.depth[i])
                break
            if budget.expired():
                truncated.append("time budget exhausted")
                unexpanded_depth = g.depth[i]
                break
            sid, state = i, g.states[i]
            i += 1
            env = sem.env(state)
            at_limit = max_depth is not None and g.depth[sid] >= max_depth
            succ = list(sem.successors(state, env, count=not at_limit))
            if not succ:
                if model.deadlock == "check" and deadlock is None and (
                        model.terminal is None or not truth(model.terminal(env), model.terminal.source)):
                    deadlock = sid
                continue
            if at_limit:
                if any(ckey(sem.canon(t)[0]) not in g.index for _, t in succ):
                    if "max_depth reached" not in truncated:
                        truncated.append("max_depth reached")
                    unexpanded_depth = g.depth[sid] if unexpanded_depth is None else min(unexpanded_depth, g.depth[sid])
                continue
            enabled = set()
            pre_obs = g.obs[sid]
            for label, nxt in succ:
                if ckey(nxt) == ckey(state):
                    continue  # stuttering step
                enabled.add(label)
                canon, _ = sem.canon(nxt)
                key = ckey(canon)
                tid = g.index.get(key)
                if tid is None:
                    if len(g.states) >= max_states:
                        if "max_states reached" not in truncated:
                            truncated.append("max_states reached")
                        refused_depth = g.depth[sid] + 1 if refused_depth is None else min(refused_depth, g.depth[sid] + 1)
                        continue
                    nenv = sem.env(canon)
                    tid = g.add(canon, sem.observe(nenv), (sid, label), g.depth[sid] + 1, keep_edges)
                    visit_state(tid, nenv)
                if transitions:
                    post_obs = g.obs[tid] if canon is nxt or not sem.perms else sem.observe(sem.env(nxt))
                    for inst in transitions:
                        if inst.id in violated_edge:
                            continue
                        env2 = inst.env(model.constants, {})
                        env2["pre"], env2["post"] = _pre_post(pre_obs), _pre_post(post_obs)
                        if not truth(inst.prop.expr(env2), inst.prop.expr.source):
                            violated_edge[inst.id] = (sid, label)
                if keep_edges:
                    g.edges[sid].append((label, tid))
            if keep_edges:
                g.enabled[sid] = frozenset(enabled)
    except BudgetExceeded:
        truncated.append("time budget exhausted")
        unexpanded_depth = g.depth[max(i - 1, 0)] if g.depth else -1
    except FvError as e:
        error = str(e)

    complete = not truncated and error is None
    depth_reached = max(g.depth) if g.depth else 0
    if complete:
        exhaustive_depth = depth_reached
    else:
        # Every behaviour of length <= exhaustive_depth was explored and checked.
        cands = [d for d in (None if refused_depth is None else refused_depth - 1, unexpanded_depth) if d is not None]
        exhaustive_depth = min(cands) if cands else -1

    trace = Tracer(sem, g)
    for inst_id, sid in violated_state.items():
        rec = status.get(inst_id) or model_inv[inst_id]
        rec["status"] = "FAIL"
        rec["counterexample"] = {"kind": "state", "steps": trace.path(sid)}
    for inst_id, (sid, label) in violated_edge.items():
        rec = status[inst_id]
        rec["status"] = "FAIL"
        rec["counterexample"] = {"kind": "transition", "steps": trace.path(sid, extra=label)}
    for inst in witnesses:
        rec = status[inst.id]
        if inst.id in found_witness:
            rec["status"] = "PASS"
            rec["witness"] = {"kind": "state", "steps": trace.path(found_witness[inst.id])}
        else:
            rec["status"] = "FAIL" if complete else "UNKNOWN"
            rec["reason"] = "not reachable in the complete state space" if complete else "not found within the explored bound"
    for inst in invariants + transitions:
        if status[inst.id]["status"] is None:
            status[inst.id]["status"] = "PASS" if complete else "UNKNOWN"
    for k in model_inv:
        if model_inv[k]["status"] is None:
            model_inv[k]["status"] = "PASS" if complete else "UNKNOWN"
    if liveness:
        if complete and not error:
            for inst in liveness:
                res = check_liveness(sem, g, inst, model)
                ce = res.pop("counterexample", None)
                if ce is not None:
                    steps = trace.path(ce["seed"], tail=ce["prefix_labels"] + ce["cycle_labels"])
                    k = len(steps) - len(ce["cycle_labels"])
                    res["counterexample"] = {"kind": "lasso", "prefix": steps[:k], "cycle": steps[k:],
                                             "loop_to_step": k - 1, "stutter": ce["stutter"]}
                status[inst.id].update(res)
        else:
            for inst in liveness:
                status[inst.id].update(status="UNKNOWN", reason="liveness needs a complete state graph")
    dead = {"status": "PASS" if deadlock is None else "FAIL", "checked": model.deadlock == "check", "counterexample": None}
    if deadlock is not None:
        dead["counterexample"] = {"kind": "deadlock", "steps": trace.path(deadlock)}
    elif not complete and model.deadlock == "check":
        dead["status"] = "UNKNOWN"
    props = list(status.values()) + list(model_inv.values())
    failed = [p for p in props if p["status"] == "FAIL"] or ([dead] if dead["status"] == "FAIL" else [])
    if error:
        verdict = "ERROR"
    elif failed or dead["status"] == "FAIL":
        verdict = "FAIL"
    elif complete:
        verdict = "PASS"
    elif exhaustive_depth >= 0:
        verdict = "BOUNDED_PASS"
    else:
        verdict = "INCOMPLETE"
    dead_actions = sorted(a for a, c in sem.coverage.items() if c["state_changing"] == 0)
    return {
        "verdict": verdict,
        "error": error,
        "complete": complete,
        "truncation": truncated,
        "exhaustive_depth": exhaustive_depth,
        "stats": {"states": len(g.states), "initial_states": len(g.initial),
                  "transitions": sum(c["fired"] for c in sem.coverage.values()),
                  "depth": depth_reached, "millis": int((time.monotonic() - started) * 1000)},
        "settings": {"max_states": max_states, "max_depth": max_depth, "time_seconds": time_seconds,
                     "symmetry": use_symmetry, "stop_on_first": stop_on_first, "only": sorted(only) if only else None},
        "constants": {k: show(v) for k, v in sorted(model.constants.items())},
        "fairness": model.fairness,
        "properties": props,
        "deadlock": dead,
        "coverage": {"actions": sem.coverage, "dead_actions": dead_actions},
        "notes": notes,
    }, (g if keep_graph else None), sem


class Tracer:
    """Rebuild a concrete behaviour from BFS parent pointers (undoing symmetry renaming)."""

    def __init__(self, sem, graph):
        self.sem, self.g = sem, graph

    def chain(self, sid):
        out = []
        while sid is not None:
            p = self.g.parent[sid]
            out.append((sid, p[1] if p else None))
            sid = p[0] if p else None
        return list(reversed(out))

    def path(self, sid, extra=None, tail=None):
        sem = self.sem
        links = self.chain(sid)
        concrete = self.g.states[links[0][0]]
        perm = sem.canon(concrete)[1]
        steps = [self._step(0, None, concrete)]
        for n, (_target, label) in enumerate(links[1:], start=1):
            real = sem.map_label(label, invert(perm))
            concrete = sem.step(concrete, real)
            perm = sem.canon(concrete)[1]
            steps.append(self._step(n, real, concrete))
        if extra is not None:
            real = sem.map_label(extra, invert(perm))
            concrete = sem.step(concrete, real)
            steps.append(self._step(len(steps), real, concrete))
        for label in tail or []:
            concrete = sem.step(concrete, label)
            steps.append(self._step(len(steps), label, concrete))
        return steps

    def _step(self, n, label, state):
        env = self.sem.env(state)
        return {"step": n, "action": label_json(label) if label else None,
                "state": self.sem.state_json(state), "observed": self.sem.obs_json(self.sem.observe(env))}


def replay(model, steps, symmetry=False):
    """Validate that a recorded behaviour is a real behaviour of `model`.

    Returns the list of concrete states. Raises FvError naming the first impossible step.
    """
    sem = Semantics(model, symmetry=False)
    require(isinstance(steps, list) and steps and isinstance(steps[0], dict), "empty behaviour")
    first = steps[0]
    match = [s for s in sem.initial_states(10 ** 6) if sem.state_json(s) == first.get("state")]
    require(match, "step 0 is not an initial state of model %s" % model.id)
    state = match[0]
    states = [state]
    for n, step in enumerate(steps[1:], start=1):
        act = step.get("action")
        require(isinstance(act, dict), "step %d has no action" % n)
        action = sem.action(act["name"])
        env = sem.env(state)
        wanted = act.get("params") or {}
        chosen = None
        for b in sem.bindings(action, env):
            if label_json((act["name"], b))["params"] == wanted:
                chosen = b
                break
        require(chosen is not None, "step %d: no parameters of %s match %s" % (n, act["name"], show_json(wanted)))
        state = sem.step(state, (act["name"], chosen))
        require(sem.state_json(state) == step.get("state"), "step %d: recorded state differs from the model's successor" % n)
        states.append(state)
    return sem, states


def show_json(v):
    import json
    return json.dumps(v, ensure_ascii=False, sort_keys=True)
