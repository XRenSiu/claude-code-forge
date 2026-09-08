#!/usr/bin/env python3
"""
verify_loop.py — lint the unified loop contracts (assets/loops.yaml).

Usage:
  verify_loop.py [LOOPS.yaml] [--routing ROUTING.yaml] [--json]

Exit 0 = pass (warnings allowed) · 1 = REJECT · 2 = usage/IO error.

Compiled checks (REJECT):
  - generator ≠ verifier            (self-verification is the anti-pattern every source names)
  - stop has all four keys explicit (success · convergence · budget · impossible; null allowed but present)
  - stop.success non-null           (a loop whose pass condition is unmeasurable never stops for the right reason)
  - budget.ref resolves             (`routing:<dotted>` must exist in routing.yaml for both tracks when <track> is
                                     used; `literal` must carry at least one numeric bound)
  - closed sets                     (level / timescale / trigger)
  - memory paths inside the archive / state layout
  - ids unique; escalate_to ∈ layers ∪ {human}
Warnings: fresh_context false without a note; convergence all-null on an agent/verification loop.
"""
import argparse
import json
import os
import re
import sys

LEVELS = {"agent", "verification", "event", "hill_climbing"}
TIMESCALES = {"minutes", "hours", "days"}
TRIGGERS = {"turn_end", "event", "interval", "cron", "after", "manual"}
LAYERS = {"card", "plan", "task", "ontology", "world", "human"}
MEMORY_PREFIXES = (".aidlc/", "specs/", "ratchet-log/", "cards/", "tests/", "tune/", "retro/")
MEMORY_FILES = ("state.json", "ledger.md", "trace.jsonl", "learnings.md", "dead-ends.md", "results.tsv")


def load_yaml(path):
    try:
        import yaml
    except ImportError:
        sys.stderr.write("verify_loop: PyYAML required (pip install pyyaml)\n"); sys.exit(2)
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except OSError as e:
        sys.stderr.write(f"verify_loop: cannot read {path}: {e}\n"); sys.exit(2)


def resolve(routing, dotted):
    cur = routing
    for k in dotted.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return False, None
        cur = cur[k]
    return True, cur


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("loops", nargs="?"); ap.add_argument("--routing"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    lpath = a.loops or os.path.join(here, "..", "assets", "loops.yaml")
    rpath = a.routing or os.path.join(os.path.dirname(os.path.abspath(lpath)), "routing.yaml")
    doc = load_yaml(lpath)
    routing = load_yaml(rpath) if os.path.isfile(rpath) else {}
    loops = doc.get("loops") or []
    rejects, warns = [], []
    ids = [l.get("id") for l in loops]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        rejects.append(f"duplicate loop ids: {dup}")
    if not loops:
        rejects.append("no loops declared")

    for l in loops:
        lid = l.get("id", "<no id>")
        gen, ver = l.get("generator"), l.get("verifier")
        if not gen or not ver:
            rejects.append(f"{lid}: generator and verifier both required")
        elif str(gen) == str(ver):
            rejects.append(f"{lid}: generator == verifier ({gen}) — self-verification; the verifier must be a different node")
        if l.get("level") not in LEVELS:
            rejects.append(f"{lid}: level {l.get('level')!r} ∉ {sorted(LEVELS)}")
        if l.get("timescale") not in TIMESCALES:
            rejects.append(f"{lid}: timescale {l.get('timescale')!r} ∉ {sorted(TIMESCALES)}")
        if l.get("trigger") not in TRIGGERS:
            rejects.append(f"{lid}: trigger {l.get('trigger')!r} ∉ {sorted(TRIGGERS)}")
        if l.get("escalate_to") not in LAYERS:
            rejects.append(f"{lid}: escalate_to {l.get('escalate_to')!r} ∉ {sorted(LAYERS)}")
        stop = l.get("stop")
        if not isinstance(stop, dict):
            rejects.append(f"{lid}: stop must be a mapping with success/convergence/budget/impossible")
            continue
        for k in ("success", "convergence", "budget", "impossible"):
            if k not in stop:
                rejects.append(f"{lid}: stop.{k} missing — declare it explicitly (null is allowed, absence is not)")
        if stop.get("success") in (None, ""):
            rejects.append(f"{lid}: stop.success is null — unmeasurable pass condition")
        b = stop.get("budget")
        if isinstance(b, dict):
            ref = str(b.get("ref", ""))
            if ref.startswith("routing:"):
                dotted = ref.split(":", 1)[1]
                targets = [dotted.replace("<track>", t) for t in ("psl", "task")] if "<track>" in dotted else [dotted]
                for t in targets:
                    ok, val = resolve(routing, t)
                    if not ok:
                        rejects.append(f"{lid}: budget.ref {ref} → {t} not found in {os.path.basename(rpath)}")
            elif ref == "literal":
                nums = [v for k, v in b.items() if k not in ("ref", "note", "source") and isinstance(v, (int, float))]
                if not nums:
                    rejects.append(f"{lid}: budget.ref literal but no numeric bound given")
            else:
                rejects.append(f"{lid}: budget.ref must be routing:<dotted> or literal (got {ref!r})")
        elif b is not None:
            rejects.append(f"{lid}: stop.budget must be a mapping or null")
        conv = stop.get("convergence")
        if l.get("level") in ("agent", "verification") and isinstance(conv, dict) and all(v in (None, "") for v in conv.values()):
            warns.append(f"{lid}: convergence all null on a {l.get('level')} loop — how do you tell no-progress from slow progress?")
        imp = stop.get("impossible")
        if isinstance(imp, dict) and isinstance(imp.get("reporters"), str) and imp["reporters"].startswith("routing:"):
            ok, _ = resolve(routing, imp["reporters"].split(":", 1)[1])
            if not ok:
                rejects.append(f"{lid}: impossible.reporters {imp['reporters']} not found in routing.yaml")
        for m in l.get("memory") or []:
            ms = str(m)
            base = ms.split("#")[0]
            if not (base.startswith(MEMORY_PREFIXES) or base in MEMORY_FILES or os.path.basename(base) in MEMORY_FILES):
                rejects.append(f"{lid}: memory {ms!r} outside the archive/state layout ({MEMORY_PREFIXES + MEMORY_FILES})")
        if not l.get("memory"):
            rejects.append(f"{lid}: memory empty — the model forgets everything between runs; memory has to be on disk")
        if l.get("fresh_context") is False and "note" not in l:
            warns.append(f"{lid}: fresh_context false — fine for a session-bound loop, but say so in a note")

    out = {"verdict": "REJECT" if rejects else "PASS", "loops": ids, "rejects": rejects, "warnings": warns}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(1 if rejects else 0)


if __name__ == "__main__":
    main()
