"""Seeded random simulation. Finds bugs fast; proves nothing (evidence level E1).

A violation found here is a real counterexample of the model (replayable). "No violation"
only means the sampled paths were fine, so the verdict is NO_VIOLATION_SAMPLED, never PASS.
"""
import random

from .checker import instances
from .expr import Budget, set_budget, truth
from .semantics import Semantics, label_json
from .values import FMap, ckey, require


def simulate(model, seed=1, runs=100, depth=50, time_seconds=None):
    require(all(type(x) is int for x in (seed, runs, depth)) and 0 < runs <= 100000 and 0 < depth <= 10000, "invalid simulation bounds")
    set_budget(Budget(time_seconds))
    sem = Semantics(model, symmetry=False)
    rng = random.Random(seed)
    insts = [i for i in instances(model.contract, model.constants) if i.kind in ("invariant", "transition")]
    inits = sorted(sem.initial_states(10000), key=ckey)
    steps_total = 0
    for run in range(runs):
        state = inits[rng.randrange(len(inits))]
        env = sem.env(state)
        obs = sem.observe(env)
        trail = [{"step": 0, "action": None, "state": sem.state_json(state), "observed": sem.obs_json(obs)}]
        for n in range(depth + 1):
            for inst in insts:
                if inst.kind == "invariant" and not truth(inst.prop.expr(inst.env(model.constants, obs)), inst.prop.expr.source):
                    return _fail(inst.id, trail, seed, run, steps_total)
            if n == depth:
                break
            options = sorted(sem.successors(state, env, count=False), key=lambda x: ckey(x[0]))
            if not options:
                break
            label, nxt = options[rng.randrange(len(options))]
            nenv = sem.env(nxt)
            nobs = sem.observe(nenv)
            for inst in insts:
                if inst.kind == "transition":
                    e = inst.env(model.constants, {})
                    e["pre"], e["post"] = FMap(obs.items()), FMap(nobs.items())
                    if not truth(inst.prop.expr(e), inst.prop.expr.source):
                        trail.append({"step": len(trail), "action": label_json(label), "state": sem.state_json(nxt), "observed": sem.obs_json(nobs)})
                        return _fail(inst.id, trail, seed, run, steps_total)
            state, env, obs = nxt, nenv, nobs
            steps_total += 1
            trail.append({"step": len(trail), "action": label_json(label), "state": sem.state_json(state), "observed": sem.obs_json(obs)})
    return {"verdict": "NO_VIOLATION_SAMPLED", "seed": seed, "runs": runs, "depth": depth, "steps": steps_total, "violation": None}


def _fail(pid, trail, seed, run, steps):
    return {"verdict": "FAIL", "seed": seed, "run": run, "steps": steps,
            "violation": {"property": pid, "counterexample": {"kind": "state", "steps": trail}}}
