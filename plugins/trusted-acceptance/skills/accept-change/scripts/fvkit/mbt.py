"""Model-based test vectors: the model tells the real implementation what to try and expect.

Strategies:
- transitions      one shortest behaviour per reachable action instance (transition coverage)
- counterexamples  replay a recorded bad behaviour (e.g. the old design's counterexample)
                   against the CURRENT model: steps the fixed design refuses become
                   `enabled: false` expectations, so the regression test proves the refusal
- random           seeded random walks (reproducible; sampling, never a proof)

A harness reads the vectors, drives the system, and records a trace (see trace.py); the
trace is then checked against the same model. That closes model -> code -> model.
"""
import random

from .checker import check
from .semantics import Semantics, label_json, label_str
from .values import FvError, ckey, require


def _vector(sem, vid, origin, init, labels):
    state = init
    steps = []
    for lbl in labels:
        env = sem.env(state)
        action = sem.action(lbl[0])
        allowed = any(ckey(b) == ckey(lbl[1]) for b in sem.bindings(action, env))
        nxt = sem.apply(action, lbl[1], state, env) if allowed else None
        if nxt is None:
            steps.append({"action": label_json(lbl), "enabled": False, "expect": sem.obs_json(sem.observe(env))})
        else:
            state = nxt
            steps.append({"action": label_json(lbl), "enabled": True, "expect": sem.obs_json(sem.observe(sem.env(state)))})
    return {"id": vid, "origin": origin, "initial": sem.obs_json(sem.observe(sem.env(init))), "steps": steps}


def transition_vectors(model, max_states=None):
    result, g, sem = check(model, max_states=max_states, symmetry=False, keep_graph=True)
    require(result["verdict"] != "ERROR", "model does not evaluate: %s" % result["error"])
    best = {}
    for sid, edges in enumerate(g.edges):
        for lbl, _ in edges:
            k = ckey(lbl)
            if k not in best or g.depth[sid] < g.depth[best[k][0]]:
                best[k] = (sid, lbl)
    vectors = []
    for k in sorted(best):
        sid, lbl = best[k]
        chain = []
        cur = sid
        while g.parent[cur] is not None:
            chain.append(g.parent[cur][1])
            cur = g.parent[cur][0]
        labels = list(reversed(chain)) + [lbl]
        vectors.append(_vector(sem, "cover:" + label_str(lbl), "transition_coverage", g.states[cur], labels))
    return vectors, result


def _labels_from_steps(sem, steps):
    out = []
    for n, step in enumerate(steps[1:], start=1):
        act = step.get("action")
        require(isinstance(act, dict) and act.get("name"), "step %d has no action" % n)
        action = sem.action(act["name"])
        params = act.get("params") or {}
        require(set(params) == {p for p, _ in action.params}, "step %d: parameters %s do not match action %s" % (n, sorted(params), act["name"]))
        from .values import from_json
        out.append((act["name"], tuple((p, from_json(params[p])) for p, _ in action.params)))
    return out


def replay_vector(model, vid, steps, origin="counterexample_replay"):
    """Re-express a recorded behaviour (possibly from another model) as expectations of this model."""
    sem = Semantics(model, symmetry=False)
    inits = sem.initial_states(1000)
    first = (steps[0] or {}).get("observed")
    match = [s for s in inits if first is None or sem.obs_json(sem.observe(sem.env(s))) == first]
    require(match, "%s: no initial state of %s matches the recorded start" % (vid, model.id))
    return _vector(sem, vid, origin, match[0], _labels_from_steps(sem, steps))


def random_vectors(model, seed=1, count=8, length=12):
    require(all(type(x) is int for x in (seed, count, length)) and 0 < count <= 1000 and 0 < length <= 1000, "invalid random walk bounds")
    sem = Semantics(model, symmetry=False)
    rng = random.Random(seed)
    inits = sorted(sem.initial_states(1000), key=ckey)
    vectors = []
    for n in range(count):
        state = inits[rng.randrange(len(inits))]
        init, labels = state, []
        for _ in range(length):
            options = sorted(((lbl, t) for lbl, t in sem.successors(state, sem.env(state), count=False)), key=lambda x: ckey(x[0]))
            if not options:
                break
            lbl, state = options[rng.randrange(len(options))]
            labels.append(lbl)
        vectors.append(_vector(sem, "random:%d:%d" % (seed, n), "random_walk", init, labels))
    return vectors


def build(model, strategies, counterexamples=(), seed=1, count=8, length=12, max_states=None):
    vectors, notes = [], []
    for strategy in strategies:
        if strategy == "transitions":
            vs, result = transition_vectors(model, max_states)
            if not result["complete"]:
                notes.append("transition coverage computed on a truncated state space")
            vectors += vs
        elif strategy == "counterexamples":
            for cid, steps in counterexamples:
                vectors.append(replay_vector(model, "replay:" + cid, steps))
        elif strategy == "random":
            vectors += random_vectors(model, seed, count, length)
        else:
            raise FvError("unknown strategy " + strategy)
    ids = [v["id"] for v in vectors]
    require(len(set(ids)) == len(ids), "duplicate vector ids")
    return {"schema_version": 1, "kind": "fv-test-vectors", "model": model.identity(), "contract": model.contract.identity(),
            "strategies": list(strategies), "seed": seed if "random" in strategies else None,
            "vectors": vectors, "notes": notes}
