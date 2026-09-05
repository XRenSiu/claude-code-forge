#!/usr/bin/env python3
"""
trace.py — query the decision trace (.sdlc/<slug>/trace.jsonl): typed edges between lifecycle events.

The ledger (ledger.md) stays the human-readable, append-only record. trace.jsonl is its machine-readable
sidecar written by sdlc_state.py: one event per line, each with `refs: [{type, target}]` where type is one of
the closed edge set. The edge type IS the knowledge — an untyped "related to" cannot answer "why did AC-003
change" or "what does changing it break".

Edge types (closed). An append-only log can only point backwards, so every edge is written from the later
event / the new thing towards the earlier event / the old thing:
  caused_by             effect event     → cause event            (reflow → fail; failure_report → reflow; escape → AC change)
  decided_by            change / verdict → record or human        (gate record, routing rule, signer)
  supersedes            new version      → old version            (done_when.yaml#AC-003@v2 → @v1; card v2 → v1)
  implements            commit / card    → card / AC / REQ / PSL  (commit → CARD-03 → AC-003-a → REQ-003)
  references            event            → evidence artifact      (failure output, diff, report file)
  depends_on            card / AC        → card / AC
  rejected_alternative  decision         → the alternative not taken

Usage:
  trace.py why    <target> [--trace PATH | --root .sdlc --slug S] [--depth 10]   # backwards: what caused / decided it
  trace.py impact <target> [...]                                                 # forwards: what implements / depends on it
  trace.py render [--since ISO] [...]                                            # mermaid flowchart to stdout
  trace.py lint   [--routing routing.yaml] [--base DIR] [...]                    # edge types ∈ closed set; targets resolvable

Exit 0 ok · 1 lint reject / target not found · 2 usage/IO.
"""
import argparse
import json
import os
import re
import sys

EDGE_TYPES = {"caused_by", "decided_by", "supersedes", "implements", "references", "depends_on", "rejected_alternative"}
ANCHOR_RE = re.compile(r"^(CARD-\d+|AC-[\w-]+|REQ-[\w-]+|PSL-[\w-]+|DOS-[\w-]+|ev-\d+|routing\.R\d+|human:[\w.@-]+|github:[\w/#-]+)$")


def die(msg, code=2):
    sys.stderr.write(f"trace: {msg}\n"); sys.exit(code)


def locate(a):
    if a.trace:
        return a.trace
    root = a.root or ".sdlc"
    slug = a.slug
    if not slug:
        if not os.path.isdir(root):
            die(f"no {root}/ — pass --trace PATH")
        runs = [d for d in os.listdir(root) if os.path.isfile(os.path.join(root, d, "trace.jsonl"))]
        if len(runs) != 1:
            die(f"--slug required (runs with trace.jsonl under {root}: {sorted(runs)})")
        slug = runs[0]
    return os.path.join(root, slug, "trace.jsonl")


def load(path):
    if not os.path.isfile(path):
        die(f"trace not found: {path}")
    evs = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                evs.append(json.loads(line))
            except json.JSONDecodeError as e:
                die(f"{path}:{i}: bad json: {e}")
    return evs


def index(evs):
    byid = {e.get("id"): e for e in evs}
    out, inc = {}, {}  # out[id] = [(type,target)], inc[target] = [(type, source_id)]
    for e in evs:
        for r in e.get("refs") or []:
            out.setdefault(e["id"], []).append((r.get("type"), r.get("target")))
            inc.setdefault(r.get("target"), []).append((r.get("type"), e["id"]))
    return byid, out, inc


def anchor(t):
    """done_when.yaml#AC-003-a@v1 → AC-003-a ; cards/CARD-03.yaml → CARD-03 ; ev-0009 → ev-0009"""
    t = str(t)
    a = t.split("#")[-1].split("@")[0]
    base = os.path.basename(a)
    m = re.match(r"^(CARD-\d+|AC-[\w-]+|REQ-[\w-]+|PSL-[\w-]+|DOS-[\w-]+)", base)
    return m.group(1) if m else a


def matches(t, target):
    t = str(t)
    return t == target or anchor(t) == target or anchor(t).startswith(target + "-") or t.split("@")[0] == target


def mentions(evs, target):
    """Events whose id == target or whose refs target it (exact, or by anchor: file#ANCHOR@version)."""
    hits = []
    for e in evs:
        if e.get("id") == target or e.get("card") == target or e.get("sha") == target:
            hits.append(e); continue
        if any(matches(r.get("target", ""), target) for r in e.get("refs") or []):
            hits.append(e)
    return hits


def fmt(e):
    bits = [e.get("id", "?"), e.get("kind", "?")]
    for k in ("signal", "layer", "decision", "by"):
        if e.get(k):
            bits.append(f"{k}={e[k]}")
    if e.get("note"):
        bits.append(f"“{str(e['note'])[:60]}”")
    return " · ".join(bits)


def cmd_why(a, evs):
    byid, out, inc = index(evs)
    hits = mentions(evs, a.target)
    if not hits:
        print(json.dumps({"target": a.target, "found": False}, ensure_ascii=False)); sys.exit(1)
    lines = [f"why {a.target}: {len(hits)} event(s) touch it"]
    seen = set()

    def back(eid, depth, indent):
        """Follow caused_by outwards: this event ← its cause ← its cause's cause …"""
        if depth > a.depth or eid in seen:
            return
        seen.add(eid)
        e = byid.get(eid)
        if not e:
            lines.append(f"{'  ' * indent}← {eid} (not in trace)"); return
        lines.append(f"{'  ' * indent}← {fmt(e)}")
        for t, tgt in out.get(eid, []):
            if t in ("decided_by", "references", "rejected_alternative", "supersedes"):
                lines.append(f"{'  ' * (indent + 1)}[{t}] {tgt}")
        for t, tgt in out.get(eid, []):
            if t == "caused_by":
                back(tgt, depth + 1, indent + 1)

    for h in hits:
        seen.clear()
        lines.append(f"• {fmt(h)}")
        for t, tgt in out.get(h["id"], []):
            if t != "caused_by":
                lines.append(f"    [{t}] {tgt}")
        for t, tgt in out.get(h["id"], []):
            if t == "caused_by":
                back(tgt, 1, 2)
        caused = [fmt(byid.get(src, {"id": src})) for t, src in inc.get(h["id"], []) if t == "caused_by"]
        for c in caused:
            lines.append(f"    → caused: {c}")
    print("\n".join(lines))


def cmd_impact(a, evs):
    byid, out, inc = index(evs)
    lines = [f"impact of {a.target}:"]
    seen = set()

    def fwd(target, depth, indent):
        if depth > a.depth:
            return
        for t, src in inc.get(target, []):
            if t in ("implements", "depends_on", "supersedes", "caused_by") and src not in seen:
                seen.add(src)
                e = byid.get(src, {})
                lines.append(f"{'  ' * indent}→ [{t}] {fmt(e)}")
                # what this event itself is (a commit / card) — others may implement it
                for k in ("sha", "card"):
                    if e.get(k):
                        fwd(e[k], depth + 1, indent + 1)
                fwd(src, depth + 1, indent + 1)
    # anchors that resolve to the target (AC-003 → AC-003-a; done_when.yaml#AC-003-a@v1 → AC-003-a)
    keys = {k for k in inc if matches(k, a.target)}
    for k in sorted(keys, key=str):
        fwd(k, 0, 1)
    if len(lines) == 1:
        lines.append("  (nothing implements / depends on it in this trace)")
    print("\n".join(lines))


def cmd_render(a, evs):
    if a.since:
        evs = [e for e in evs if str(e.get("at", "")) >= a.since]
    lines = ["flowchart LR"]
    ids = {e["id"] for e in evs}
    for e in evs:
        label = f"{e['id']}<br/>{e.get('kind','')}" + (f"<br/>{e['signal']}" if e.get("signal") else "")
        shape = ("{{%s}}" % label) if e.get("kind") == "gate" else ("[%s]" % label)
        lines.append(f"  {e['id'].replace('-', '_')}{shape}")
    ext = set()
    for e in evs:
        for r in e.get("refs") or []:
            t = str(r.get("target"))
            tid = t if t in ids else re.sub(r"[^A-Za-z0-9_]", "_", t)
            if t not in ids and tid not in ext:
                ext.add(tid); lines.append(f"  {tid}([{t}])")
            lines.append(f"  {e['id'].replace('-', '_')} -- {r.get('type')} --> {tid.replace('-', '_')}")
    print("\n".join(lines))


FILE_LIKE = re.compile(r"^[\w./-]+\.(md|ya?ml|json|lock|tsv|txt|patch|py|sh|ts|tsx|js)$")


def graph_node_ids(path):
    try:
        import yaml
        with open(path, encoding="utf-8") as f:
            g = yaml.safe_load(f) or {}
        return {n.get("id") for n in g.get("nodes") or []} | {str(n.get("id")).split(".", 1)[-1] for n in g.get("nodes") or []}
    except Exception:
        return set()


def cmd_lint(a, evs, path):
    rejects, warns = [], []
    here = os.path.dirname(os.path.abspath(__file__))
    nodes = graph_node_ids(a.graph or os.path.join(here, "..", "assets", "graph.yaml"))
    ids = [e.get("id") for e in evs]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        rejects.append(f"duplicate event ids: {dup}")
    idset = set(ids)
    routing_rules = set()
    if a.routing and os.path.isfile(a.routing):
        try:
            import yaml
            routing_rules = {r.get("id") for r in (yaml.safe_load(open(a.routing, encoding="utf-8")) or {}).get("rules", [])}
        except Exception:
            pass
    base = a.base or os.path.dirname(os.path.abspath(path))
    for e in evs:
        if not e.get("id") or not e.get("kind") or not e.get("at"):
            rejects.append(f"event missing id/kind/at: {e}")
        for r in e.get("refs") or []:
            t = r.get("type"); tgt = str(r.get("target", ""))
            if t not in EDGE_TYPES:
                rejects.append(f"{e.get('id')}: edge type {t!r} ∉ {sorted(EDGE_TYPES)}")
            if not tgt:
                rejects.append(f"{e.get('id')}: ref without target"); continue
            core = tgt.split("#")[0].split("@")[0]
            if core.startswith("ev-"):
                if core not in idset:
                    rejects.append(f"{e.get('id')}: dangling event target {tgt!r}")
                continue
            if core.startswith("routing."):
                if routing_rules and core.split(".", 1)[1] not in routing_rules:
                    rejects.append(f"{e.get('id')}: unknown routing rule {tgt!r}")
                continue
            if ANCHOR_RE.match(core) or ANCHOR_RE.match(anchor(tgt)) or core in nodes or core.startswith(("human:", "github:", "git:")):
                continue
            if os.path.exists(os.path.join(base, core)) or os.path.exists(core):
                continue
            if FILE_LIKE.match(core):
                warns.append(f"{e.get('id')}: artifact {tgt!r} not found under {base} (archives need not copy every artifact)")
                continue
            rejects.append(f"{e.get('id')}: dangling target {tgt!r} (not an event id, contract anchor, routing rule, graph node, or existing path)")
    out = {"verdict": "REJECT" if rejects else "PASS", "events": len(evs), "rejects": rejects, "warnings": warns}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(1 if rejects else 0)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--trace"); common.add_argument("--root", default=".sdlc"); common.add_argument("--slug")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("why", parents=[common]); s.add_argument("target"); s.add_argument("--depth", type=int, default=10)
    s = sub.add_parser("impact", parents=[common]); s.add_argument("target"); s.add_argument("--depth", type=int, default=10)
    s = sub.add_parser("render", parents=[common]); s.add_argument("--since")
    s = sub.add_parser("lint", parents=[common]); s.add_argument("--routing"); s.add_argument("--base"); s.add_argument("--graph")
    a = p.parse_args()
    path = locate(a)
    evs = load(path)
    if a.cmd == "why":
        cmd_why(a, evs)
    elif a.cmd == "impact":
        cmd_impact(a, evs)
    elif a.cmd == "render":
        cmd_render(a, evs)
    else:
        cmd_lint(a, evs, path)


if __name__ == "__main__":
    main()
