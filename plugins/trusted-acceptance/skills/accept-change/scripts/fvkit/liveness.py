"""Liveness (leads-to / eventually / infinitely-often) under weak and strong fairness.

TLA+ semantics: every state may stutter forever unless fairness forbids it. A property
P ~> Q is violated iff some reachable P∧¬Q state can continue along ¬Q states into a fair
cycle (a strongly connected set where every weak-fairness action is disabled somewhere or
taken, and every strong-fairness action is never enabled or taken). Strong fairness uses
the Emerson–Lei refinement: drop states where the starved action is enabled and recurse.
The counterexample is a lasso: prefix from an initial state, then a cycle (or a stutter).
"""
from collections import deque

from .expr import truth
from .values import ckey


def _constraints(model, g):
    out = []
    for f in model.fairness:
        if not f["per_params"]:
            out.append((f["kind"], (lambda l, a=f["action"]: l[0] == a), f["action"]))
            continue
        labels = {}
        for en in g.enabled:
            for l in en:
                if l[0] == f["action"]:
                    labels[ckey(l)] = l
        for key in sorted(labels):
            out.append((f["kind"], (lambda l, k=key: ckey(l) == k), labels[key]))
    return out


def _sccs(nodes, g):
    index, low, on, stack, out, counter = {}, {}, set(), [], [], 0
    for root in sorted(nodes):
        if root in index:
            continue
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on.add(root)
        work = [(root, iter([t for _, t in g.edges[root]]))]
        while work:
            v, it = work[-1]
            pushed = False
            for w in it:
                if w not in nodes:
                    continue
                if w not in index:
                    index[w] = low[w] = counter
                    counter += 1
                    stack.append(w)
                    on.add(w)
                    work.append((w, iter([t for _, t in g.edges[w]])))
                    pushed = True
                    break
                if w in on:
                    low[v] = min(low[v], index[w])
            if pushed:
                continue
            work.pop()
            if work:
                u = work[-1][0]
                low[u] = min(low[u], low[v])
            if low[v] == index[v]:
                comp = []
                while True:
                    w = stack.pop()
                    on.discard(w)
                    comp.append(w)
                    if w == v:
                        break
                out.append(sorted(comp))
    return out


def _fair_components(nodes, g, constraints):
    """All fair strongly connected sets inside `nodes` (every state may stutter)."""
    out = []
    for comp in _sccs(nodes, g):
        out.extend(_check_scc(comp, g, constraints))
    return out


def _check_scc(comp, g, constraints):
    members = set(comp)
    internal = [(u, l, t) for u in comp for l, t in g.edges[u] if t in members]
    for kind, match, _ in constraints:
        if any(match(l) for _, l, _ in internal):
            continue
        enabled = [s for s in comp if any(match(l) for l in g.enabled[s])]
        if kind == "weak":
            if len(enabled) == len(comp):
                return []  # enabled everywhere, never taken: no sub-cycle can be fair either
        elif enabled:
            return _fair_components(members - set(enabled), g, constraints)
    return [comp]


def _bfs(g, start, targets, allowed):
    """Shortest labelled path inside `allowed` from start to any target (start itself counts)."""
    if start in targets:
        return start, []
    prev = {start: None}
    q = deque([start])
    while q:
        v = q.popleft()
        for l, t in g.edges[v]:
            if t in allowed and t not in prev:
                prev[t] = (v, l)
                if t in targets:
                    labels, cur = [], t
                    while prev[cur] is not None:
                        labels.append(prev[cur][1])
                        cur = prev[cur][0]
                    return t, list(reversed(labels))
                q.append(t)
    return None, None


def check_liveness(sem, g, inst, model):
    consts = model.constants
    n = len(g.states)
    prop = inst.prop

    def holds(expr, sid):
        return truth(expr(inst.env(consts, g.obs[sid])), expr.source)

    if inst.kind == "leads_to":
        p = [holds(prop.from_, s) for s in range(n)]
        q = [holds(prop.to, s) for s in range(n)]
    elif inst.kind == "eventually":
        init = set(g.initial)
        p = [s in init for s in range(n)]
        q = [holds(prop.expr, s) for s in range(n)]
    else:
        p = [True] * n
        q = [holds(prop.expr, s) for s in range(n)]
    seeds = [s for s in range(n) if p[s] and not q[s]]
    if not seeds:
        return {"status": "PASS", "vacuous": inst.kind == "leads_to" and not any(p), "fairness_used": model.fairness}
    order = sorted(seeds, key=lambda s: (g.depth[s], s))
    region, parent, cost = set(order), {s: None for s in order}, {s: g.depth[s] for s in order}
    dq = deque(order)
    while dq:
        v = dq.popleft()
        for l, t in g.edges[v]:
            if not q[t] and t not in region:
                region.add(t)
                parent[t] = (v, l)
                cost[t] = cost[v] + 1
                dq.append(t)
    constraints = _constraints(model, g)
    comps = _fair_components(region, g, constraints)
    if not comps:
        return {"status": "PASS", "vacuous": False, "fairness_used": model.fairness}
    owner = {s: c for c in comps for s in c}
    entry = min(owner, key=lambda s: (cost[s], s))
    comp = owner[entry]
    members = set(comp)
    labels, cur = [], entry
    while parent[cur] is not None:
        labels.append(parent[cur][1])
        cur = parent[cur][0]
    seed, prefix = cur, list(reversed(labels))
    internal = [(u, l, t) for u in comp for l, t in g.edges[u] if t in members]
    waypoints = []
    for kind, match, _ in constraints:
        disabled = [s for s in comp if not any(match(l) for l in g.enabled[s])]
        taken = [(u, l, t) for u, l, t in internal if match(l)]
        if kind == "weak" and disabled:
            waypoints.append(("state", disabled[0]))
        elif kind == "strong" and len(disabled) == len(comp):
            continue
        elif taken:
            waypoints.append(("edge", taken[0]))
    cycle, cur = [], entry
    for kind, w in waypoints:
        target = {w} if kind == "state" else {w[0]}
        cur, path = _bfs(g, cur, target, members)
        cycle += path
        if kind == "edge":
            cycle.append(w[1])
            cur = w[2]
    if cycle or cur != entry:
        cur, path = _bfs(g, cur, {entry}, members)
        cycle += path
    return {"status": "FAIL", "vacuous": False, "fairness_used": model.fairness,
            "counterexample": {"kind": "lasso", "seed": seed, "prefix_labels": prefix, "cycle_labels": cycle,
                               "stutter": not cycle}}
