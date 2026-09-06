#!/usr/bin/env python3
"""
reconcile_dos.py — turn the X1 as-is ↔ to-be reconciliation into a machine-readable product.

X1 compares the AS-IS ontology (this skill's `dos.yaml`, reverse-engineered from the repo)
with the TO-BE ontology (`/psl-derive`'s `dos-proposal.yaml`, derived from the world). Until
now the comparison lived only as a prose table in the G1 record, so nothing downstream could
consume it: cards written in the to-be vocabulary (`Ring`, `Part`, `Gap`, `Assessment`) do not
close over an as-is DOS keyed `Node` / `WorkUnit` / `Event`, and the operator has to point
`lint_cards --dos` at a hand-picked proposal file (dogfood 2026-09-05, I-49).

This emits `dos-reconciled.yaml`: the as-is DOS — still the ontology the code implements —
with each mapped to-be name folded in as a `synonyms:` entry, so ONE closure source accepts
both vocabularies. `dos_closure.py` resolves synonyms, so `/issue --dos` and
`lint_cards --dos` accept it with no further wiring.

Usage:
    reconcile_dos.py --as-is dos.yaml --to-be derived/dos-proposal.yaml \\
                     --output dos-reconciled.yaml \\
                     [--map "Ring=Node,Part=WorkUnit"] [--map-file map.yaml] \\
                     [--allow-unmapped]

    --map / --map-file entries read `to_be = as_is`: the LEFT name is the to-be object,
    the RIGHT one the as-is object it means. Same-name objects are matched automatically.
    --map-file is YAML: `objects: {Ring: Node}` (and optionally `rules: {R020: R014}`).

Exit 0 = reconciled, output written.
Exit 1 = the reconciliation is incomplete: some to-be object has no as-is counterpart, or a
         rule id means two different things in the two files. Both are human judgments, not
         defaults — the report names them. `--allow-unmapped` writes the file anyway and
         records the unmapped names in `open_questions`, so the gap stays visible.
Exit 2 = usage / IO error.

What it never does: invent a mapping. An unmapped to-be object is a decision the reconciler
owes a human, and silently adding it to the as-is DOS would assert the repo implements a
concept it does not.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("reconcile_dos.py needs PyYAML: pip install pyyaml\n")
    sys.exit(2)


def load(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def objects_of(dos):
    raw = dos.get("objects") or {}
    if isinstance(raw, dict):
        return {str(k): (v if isinstance(v, dict) else {}) for k, v in raw.items()}
    return {str(o.get("name")): o for o in raw if isinstance(o, dict) and o.get("name")}


def rules_of(dos):
    out = {}
    for r in (dos.get("rules") or []):
        if isinstance(r, dict) and r.get("id"):
            out[str(r["id"]).strip()] = str(r.get("statement") or "").strip()
    return out


def parse_map(pairs_arg, map_file):
    obj_map, rule_map = {}, {}
    for chunk in (pairs_arg or "").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "=" not in chunk:
            sys.stderr.write(f"reconcile_dos: --map needs to_be=as_is, got {chunk!r}\n")
            sys.exit(2)
        left, right = chunk.split("=", 1)
        obj_map[left.strip()] = right.strip()
    if map_file:
        data = load(map_file)
        for k, v in (data.get("objects") or {}).items():
            obj_map[str(k)] = str(v)
        for k, v in (data.get("rules") or {}).items():
            rule_map[str(k)] = str(v)
    return obj_map, rule_map


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--as-is", required=True, help="dos.yaml — the ontology the repo implements")
    ap.add_argument("--to-be", required=True, help="dos-proposal.yaml — the ontology the world implies")
    ap.add_argument("--output", type=Path, help="write the reconciled DOS here")
    ap.add_argument("--map", default="", help="comma-separated to_be=as_is object pairs")
    ap.add_argument("--map-file", help="YAML {objects: {to_be: as_is}, rules: {to_be: as_is}}")
    ap.add_argument("--allow-unmapped", action="store_true",
                    help="write the output even though to-be objects are unmapped")
    a = ap.parse_args()

    try:
        as_is, to_be = load(a.as_is), load(a.to_be)
    except Exception as e:
        sys.stderr.write(f"reconcile_dos: cannot read input: {e}\n")
        return 2

    obj_map, rule_map = parse_map(a.map, a.map_file)
    ai_objs, tb_objs = objects_of(as_is), objects_of(to_be)
    ai_rules, tb_rules = rules_of(as_is), rules_of(to_be)

    identical, renamed, unmapped_to_be, bad_target = [], [], [], []
    for name in tb_objs:
        if name in obj_map:
            target = obj_map[name]
            if target not in ai_objs:
                bad_target.append(f"{name} -> {target}: `{target}` is not an object in {a.as_is}")
            else:
                renamed.append({"to_be": name, "as_is": target})
        elif name in ai_objs:
            identical.append(name)
        else:
            unmapped_to_be.append(name)
    as_is_only = sorted(set(ai_objs) - set(tb_objs) - {v for v in obj_map.values()})

    # rules: same id, different statement = the id means two things
    rule_conflicts = []
    for rid, stmt in tb_rules.items():
        if rid in ai_rules and stmt and ai_rules[rid] and stmt != ai_rules[rid]:
            rule_conflicts.append({"id": rid, "as_is": ai_rules[rid][:120], "to_be": stmt[:120]})
    rule_renames = [{"to_be": k, "as_is": v} for k, v in rule_map.items()]

    # ---- build the reconciled DOS ----
    out = copy.deepcopy(as_is)
    out_objs = objects_of(out)
    for pair in renamed:
        body = out_objs[pair["as_is"]]
        syns = list(body.get("synonyms") or [])
        for s in [pair["to_be"]] + list((tb_objs[pair["to_be"]] or {}).get("synonyms") or []):
            if s and s not in syns and s != pair["as_is"]:
                syns.append(s)
        body["synonyms"] = syns
    if isinstance(out.get("objects"), dict):
        out["objects"] = out_objs
    for pair in rule_renames:
        for r in (out.get("rules") or []):
            if isinstance(r, dict) and str(r.get("id")) == pair["as_is"]:
                al = list(r.get("aliases") or [])
                if pair["to_be"] not in al:
                    al.append(pair["to_be"])
                r["aliases"] = al

    out["reconciliation"] = {
        "as_is_source": str(a.as_is),
        "to_be_source": str(a.to_be),
        "identical": sorted(identical),
        "renamed": renamed,
        "as_is_only": as_is_only,
        "unmapped_to_be": sorted(unmapped_to_be),
        "rule_aliases": rule_renames,
        "rule_conflicts": rule_conflicts,
        "note": ("Each `renamed` pair folded the to-be name into the as-is object's `synonyms:`, "
                 "so one closure source accepts both vocabularies. `unmapped_to_be` and "
                 "`rule_conflicts` are unresolved human judgments, not defaults."),
    }
    if unmapped_to_be or rule_conflicts:
        oq = out.get("open_questions")
        if not isinstance(oq, list):
            oq = []
        n = len(oq)
        for i, name in enumerate(sorted(unmapped_to_be), start=1):
            oq.append({
                "id": f"QX{n + i:03d}",
                "question": f"to-be object `{name}` has no as-is counterpart: is it unimplemented, "
                            f"or does it already exist under another name?",
                "raised_by": "reconcile_dos.py",
                "owner": "", "deadline": "",
                "impact_if_unresolved": "cards written in the to-be vocabulary fail DOS closure",
            })
        for c in rule_conflicts:
            oq.append({
                "id": f"QX-{c['id']}",
                "question": f"rule id {c['id']} states different things in the two ontologies — "
                            f"renumber one or reconcile the statement",
                "raised_by": "reconcile_dos.py",
                "owner": "", "deadline": "",
                "impact_if_unresolved": "an invariant id closes against the wrong rule",
            })
        out["open_questions"] = oq

    incomplete = bool(unmapped_to_be or rule_conflicts or bad_target)
    report = {
        "as_is": str(a.as_is), "to_be": str(a.to_be),
        "identical": sorted(identical),
        "renamed": renamed,
        "as_is_only": as_is_only,
        "unmapped_to_be": sorted(unmapped_to_be),
        "bad_map_targets": bad_target,
        "rule_conflicts": rule_conflicts,
        "output": str(a.output) if a.output else None,
        "verdict": "RECONCILED" if not incomplete else "INCOMPLETE",
    }

    written = False
    if a.output and (not incomplete or a.allow_unmapped) and not bad_target:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(
            yaml.safe_dump(out, allow_unicode=True, sort_keys=False, width=100),
            encoding="utf-8")
        written = True
    report["written"] = written
    if incomplete and not written:
        report["why_not_written"] = (
            "reconciliation incomplete — resolve the names above (or pass --allow-unmapped "
            "to write the file with the gaps recorded in open_questions)")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if bad_target:
        return 2
    return 1 if incomplete else 0


if __name__ == "__main__":
    sys.exit(main())
