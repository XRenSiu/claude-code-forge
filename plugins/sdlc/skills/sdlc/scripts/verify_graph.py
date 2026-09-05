#!/usr/bin/env python3
"""
verify_graph.py — lint the sdlc execution graph (assets/graph.yaml) against the failure modes graph
engineering names as "contract failures, not topology failures".

Usage:
  verify_graph.py [GRAPH.yaml] [--loops LOOPS.yaml] [--stages "intake,track,..."] [--json]

Exit 0 = pass (warnings allowed) · 1 = REJECT · 2 = usage/IO error.

The five compiled checks (REJECT):
  1. bounded writes    — every skill/agent node has a non-empty `writes` list and none of its entries is a bare
                         `**` / `*` / `/` / `.` (an unbounded write scope is a node without identity)
  2. every cycle owned — remove `loop_back` edges; the remainder must be a DAG. Every loop_back edge must name
                         `loop: <id>` that exists in loops.yaml and whose entry has `stop.budget` and a non-null
                         `stop.success` (an unbounded cycle with an unmeasurable pass condition)
  3. visibility ≠ order — an edge from an evaluator-role node into an implementer-role node (or a stage whose
                         handled_by contains an implementer) may only `carries` items from
                         `carries_allowed_to_implementer` (fix_prompt / accepted_claim), never findings /
                         verdicts / confidence / evaluator identity / hidden sets
  4. human resume      — every `kind: human` node declares a non-empty `resume_binding` (unsafe human resume
                         binding to the wrong run / stale checkpoint)
  5. fan_in merge      — every `fan_in` edge declares `merge` (concurrent writes without a merge rule)
Plus structural: edge endpoints exist; node ids unique; `stages` list matches the sequential stage chain;
each stage node's handled_by ids exist. Warnings: nodes with no edges; loops.yaml ids no edge references.
"""
import argparse
import json
import sys

FORBIDDEN_CARRY_TOKENS = ("finding", "verdict", "confidence", "evaluator", "hidden", "spec-robustness", "prompt")


def load_yaml(path):
    try:
        import yaml
    except ImportError:
        sys.stderr.write("verify_graph: PyYAML required (pip install pyyaml)\n"); sys.exit(2)
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except OSError as e:
        sys.stderr.write(f"verify_graph: cannot read {path}: {e}\n"); sys.exit(2)


def as_list(x):
    if x is None:
        return []
    return list(x) if isinstance(x, (list, tuple)) else [x]


def edge_pairs(e):
    for f in as_list(e.get("from")):
        for t in as_list(e.get("to")):
            yield f, t


def sccs(nodes, edges):
    """Tarjan; return components of size > 1 plus self-loops — the actual cycle members."""
    out = {n: [] for n in nodes}
    for f, t in edges:
        if f in out and t in out:
            out[f].append(t)
    index, low, on, stack, comps = {}, {}, set(), [], []
    counter = [0]

    def strong(v):
        index[v] = low[v] = counter[0]; counter[0] += 1
        stack.append(v); on.add(v)
        for w in out[v]:
            if w not in index:
                strong(w); low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop(); on.discard(w); comp.append(w)
                if w == v:
                    break
            if len(comp) > 1 or any(x == v for x in out[v]):
                comps.append(sorted(comp))
    sys.setrecursionlimit(max(10000, sys.getrecursionlimit()))
    for n in nodes:
        if n not in index:
            strong(n)
    return comps


def is_dag(nodes, edges):
    comps = sccs(nodes, edges)
    return (True, []) if not comps else (False, comps)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("graph", nargs="?", default=None)
    ap.add_argument("--loops"); ap.add_argument("--stages"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    gpath = a.graph or os.path.join(here, "..", "assets", "graph.yaml")
    lpath = a.loops or os.path.join(os.path.dirname(os.path.abspath(gpath)), "loops.yaml")
    g = load_yaml(gpath)
    loops = {l.get("id"): l for l in (load_yaml(lpath).get("loops") or [])} if os.path.isfile(lpath) else {}

    rejects, warns = [], []
    nodes = g.get("nodes") or []
    edges = g.get("edges") or []
    ids = [n.get("id") for n in nodes]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        rejects.append(f"duplicate node ids: {dup}")
    byid = {n.get("id"): n for n in nodes}
    allowed_carry = set(g.get("carries_allowed_to_implementer") or ["fix_prompt", "accepted_claim"])

    # structural: endpoints + handled_by exist
    for i, e in enumerate(edges):
        for f, t in edge_pairs(e):
            for end in (f, t):
                if end not in byid:
                    rejects.append(f"edge #{i} endpoint not a node: {end}")
        if e.get("type") not in ("sequential", "conditional", "fan_out", "fan_in", "loop_back", "interrupt", "handoff"):
            rejects.append(f"edge #{i} has unknown type {e.get('type')!r}")
    for n in nodes:
        if n.get("kind") == "stage":
            for h in as_list(n.get("handled_by")):
                if h not in byid:
                    rejects.append(f"stage {n['id']} handled_by unknown node {h}")

    # 1. bounded writes
    for n in nodes:
        if n.get("kind") in ("skill", "agent"):
            w = as_list(n.get("writes"))
            if not w:
                rejects.append(f"[1 bounded writes] {n['id']}: writes empty — a node without a write scope has no identity")
            for x in w:
                if str(x).strip() in ("**", "*", "/", ".", "**/*"):
                    rejects.append(f"[1 bounded writes] {n['id']}: unbounded write scope {x!r}")

    # 2. every cycle owned
    non_loop = [(f, t) for e in edges if e.get("type") != "loop_back" for f, t in edge_pairs(e)]
    ok, cyc = is_dag(list(byid), non_loop)
    if not ok:
        for comp in cyc:
            rejects.append(f"[2 every cycle owned] cycle without a loop_back edge (unbounded, no loop contract): {comp} — type the closing edge loop_back and name its loop")
    for i, e in enumerate(edges):
        if e.get("type") != "loop_back":
            continue
        lid = e.get("loop")
        if not lid:
            rejects.append(f"[2 every cycle owned] loop_back edge #{i} ({e.get('from')}→{e.get('to')}) has no loop: <id>")
            continue
        if lid not in loops:
            rejects.append(f"[2 every cycle owned] loop_back edge #{i} names loop {lid!r} not in loops.yaml")
            continue
        stop = loops[lid].get("stop") or {}
        if not stop.get("budget"):
            rejects.append(f"[2 every cycle owned] loop {lid}: stop.budget missing — unbounded cycle")
        if stop.get("success") in (None, ""):
            rejects.append(f"[2 every cycle owned] loop {lid}: stop.success null — unmeasurable pass condition")

    # 3. visibility ≠ execution order
    def roles_of(nid):
        n = byid.get(nid) or {}
        if n.get("kind") == "stage":
            return {(byid.get(h) or {}).get("role") for h in as_list(n.get("handled_by"))}
        return {n.get("role")}
    for i, e in enumerate(edges):
        for f, t in edge_pairs(e):
            if "evaluator" in roles_of(f) and "implementer" in roles_of(t):
                carries = as_list(e.get("carries"))
                bad = [c for c in carries if c not in allowed_carry]
                if bad:
                    rejects.append(f"[3 visibility≠order] evaluator {f} → implementer {t} carries {bad}; allowed: {sorted(allowed_carry)}")
                if not carries:
                    warns.append(f"[3 visibility≠order] evaluator {f} → implementer {t} declares no carries — say what crosses (fix_prompt?)")
            for c in as_list(e.get("carries")):
                if "implementer" in roles_of(t) and any(tok in str(c).lower() for tok in FORBIDDEN_CARRY_TOKENS) and c not in allowed_carry:
                    rejects.append(f"[3 visibility≠order] edge #{i} carries {c!r} into implementer {t}")

    # 4. human resume binding
    for n in nodes:
        if n.get("kind") == "human" and not as_list(n.get("resume_binding")):
            rejects.append(f"[4 human resume] {n['id']}: resume_binding empty — a human checkpoint must say which state fields it binds to")

    # 5. fan_in merge
    for i, e in enumerate(edges):
        if e.get("type") == "fan_in" and not e.get("merge"):
            rejects.append(f"[5 fan_in merge] edge #{i} → {e.get('to')} has no merge rule")

    # stages chain vs declared list
    stages = list(g.get("stages") or [])
    if a.stages:
        want = [s.strip() for s in a.stages.split(",") if s.strip()]
        if want != stages:
            rejects.append(f"stages list differs from --stages: graph={stages} expected={want}")
    seq = {f: t for e in edges if e.get("type") == "sequential" for f, t in edge_pairs(e)
           if f.startswith("stage.") and t.startswith("stage.")}
    chain, cur = [], f"stage.{stages[0]}" if stages else None
    while cur:
        chain.append(cur.split(".", 1)[1])
        cur = seq.get(cur)
    if stages and chain != stages:
        rejects.append(f"sequential stage chain {chain} ≠ stages {stages}")
    for s in stages:
        if f"stage.{s}" not in byid:
            rejects.append(f"stage {s} listed but node stage.{s} missing")

    # warnings
    touched = {x for e in edges for pair in edge_pairs(e) for x in pair}
    for n in nodes:
        if n.get("id") not in touched and n.get("kind") != "stage":
            warns.append(f"node {n['id']} has no edges")
    used_loops = {e.get("loop") for e in edges if e.get("type") == "loop_back"}
    for lid in loops:
        if lid not in used_loops:
            warns.append(f"loops.yaml#{lid} is referenced by no loop_back edge")

    out = {"verdict": "REJECT" if rejects else "PASS", "graph": gpath, "nodes": len(nodes), "edges": len(edges),
           "loops_referenced": sorted(l for l in used_loops if l), "rejects": rejects, "warnings": warns}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(1 if rejects else 0)


if __name__ == "__main__":
    main()
