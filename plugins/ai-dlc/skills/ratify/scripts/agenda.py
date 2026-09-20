#!/usr/bin/env python3
"""
agenda.py — the ritual's mechanical half: what is still open on a lockable artefact, and writing a
human's ruling back into it.

Why a script and not the engine's prose: the engine that just drafted the card is the worst reader of
"what did I leave open" — it remembers the parts it found interesting. The list has to come from the
file, every time, unfiltered (same reason `aidlc_state.py notes --for-gate` exists). And a ruling typed
back by hand loses who ruled and when; here it is stamped.

Usage:
  agenda.py <card.yaml> [--json]                      # print the open items, numbered, with evidence
  agenda.py <card.yaml> --rule <n|id> --resolution "…" --by "<human>"   # record one ruling, stamped
  agenda.py <card.yaml> --check                        # exit 0 when nothing is open, 1 otherwise

Exit: 0 ok / nothing open · 1 items still open (for --check) · 2 usage / IO.

What counts as open (same set `verify_card.py --ready-to-sign` rejects on, read from the same file):
  - `conflicts_for_legislation[]` without a `resolution`
  - a carded entry with `confidence: low` and no `resolution_note`
  - a carded entry whose `survival_test` is not `pass`
A ruling is a decision, not a deferral: `--resolution` may not be empty, and "待定 / TBD / 再说" is
refused — deferring is legitimate, but then the item belongs in open_questions with an owner, not in a
signature.
"""
import argparse
import datetime as _dt
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("agenda.py needs PyYAML\n"); sys.exit(2)

DEFERRAL = re.compile(r"^\s*(待定|待议|再说|回头|tbd|todo|later|pending|不确定)\b", re.I)


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except (OSError, yaml.YAMLError) as e:
        sys.stderr.write(f"agenda: cannot read {path}: {e}\n"); sys.exit(2)


def open_items(card):
    """→ [{id, kind, what, evidence, where}] — read from the file, never from memory."""
    out = []
    for i, c in enumerate(card.get("conflicts_for_legislation") or []):
        c = c or {}
        if str(c.get("resolution") or "").strip():
            continue
        out.append({
            "id": f"C{i + 1}",
            "kind": "conflict",
            "what": "两条不能同真，要人裁：规则改写 / 降级，还是现状是 bug",
            "evidence": {"a": c.get("a"), "b": c.get("b"), "note": c.get("note")},
            "where": f"conflicts_for_legislation[{i}]",
        })
    for col in ("hard_invariants", "overridable_defaults"):
        for i, e in enumerate(card.get(col) or []):
            e = e or {}
            eid = e.get("id", f"{col}[{i}]")
            if e.get("confidence") == "low" and not str(e.get("resolution_note") or "").strip():
                out.append({"id": eid, "kind": "low_confidence",
                            "what": "置信度低：skill 自己说这条需要人看过才能落地",
                            "evidence": {"statement": e.get("statement"), "provenance": e.get("provenance")},
                            "where": f"{col}[{i}].resolution_note"})
            if e.get("survival_test") != "pass":
                out.append({"id": eid, "kind": "survival",
                            "what": f"存活测试是 {e.get('survival_test')!r}，不是 pass：没活过 □/◊ 的候选不能冻成法",
                            "evidence": {"statement": e.get("statement")},
                            "where": f"{col}[{i}].survival_test"})
    return out


def find_item(card, key):
    items = open_items(card)
    for n, it in enumerate(items, 1):
        if key == it["id"] or key == str(n):
            return it
    sys.stderr.write(f"agenda: no open item {key!r}; open now: {[i['id'] for i in items] or '（无）'}\n")
    sys.exit(2)


def apply_ruling(path, card, item, resolution, by):
    """Write the ruling in place, as TEXT.

    Not a yaml round-trip: `safe_dump` would drop every comment in the file, and an invariant card's
    comments carry "these are proposals, a human signature is what makes them law". Losing that while
    recording a ruling would be a bad trade, so the key is inserted into the entry's own block.
    """
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
    text = f"{stamp} {by}：{resolution}"
    col, idx = item["where"].split("[", 1)
    idx = int(idx.split("]")[0])
    key = {"conflict": "resolution", "low_confidence": "resolution_note"}.get(item["kind"])
    if not key:
        sys.stderr.write("agenda: a failed survival test is not closed by a ruling — rerun the □/◊ test, "
                         "then either fix the entry or drop it\n")
        sys.exit(2)
    section = "conflicts_for_legislation" if item["kind"] == "conflict" else col
    lines = open(path, encoding="utf-8").read().splitlines(keepends=True)
    start = next((i for i, l in enumerate(lines) if re.match(rf"^{re.escape(section)}\s*:", l)), None)
    if start is None:
        sys.stderr.write(f"agenda: section {section} not found in {path}\n"); sys.exit(2)
    # the section's list items: lines whose indent is the section's first "- " indent
    item_indent, seen, begin, end = None, -1, None, None
    for i in range(start + 1, len(lines) + 1):
        line = lines[i] if i < len(lines) else ""
        stripped = line.strip()
        if i < len(lines) and (not stripped or stripped.startswith("#")):
            continue
        indent = len(line) - len(line.lstrip()) if i < len(lines) else 0
        is_item = i < len(lines) and stripped.startswith("- ")
        if item_indent is None and is_item:
            item_indent = indent
        if i >= len(lines) or (indent == 0 and stripped and not is_item):        # section ended
            if begin is not None:
                end = i
            break
        if is_item and indent == item_indent:
            seen += 1
            if seen == idx:
                begin = i
            elif begin is not None and end is None:
                end = i
                break
    if begin is None:
        sys.stderr.write(f"agenda: could not locate {section}[{idx}] in {path} — edit it by hand\n"); sys.exit(2)
    end = end if end is not None else len(lines)
    while end > begin and not lines[end - 1].strip():
        end -= 1
    pad = " " * (item_indent + 2)
    quoted = text.replace('"', "'")
    lines.insert(end, f'{pad}{key}: "{quoted}"\n')
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.writelines(lines)
    if not (yaml.safe_load(open(tmp, encoding="utf-8")) or {}).get(section, [{}])[idx].get(key):
        sys.stderr.write("agenda: the write-back did not land where it should — file left untouched\n")
        os.remove(tmp); sys.exit(2)
    os.replace(tmp, path)
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("card")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--rule", help="item id or its number in the printed agenda")
    ap.add_argument("--resolution")
    ap.add_argument("--by", help="the human who ruled — never an agent name")
    a = ap.parse_args()
    card = load(a.card)

    if a.rule:
        if not a.resolution or not a.resolution.strip():
            sys.stderr.write("agenda: --resolution is required and may not be empty\n"); sys.exit(2)
        if DEFERRAL.match(a.resolution):
            sys.stderr.write("agenda: that is a deferral, not a ruling. Deferring is fine — move the item to "
                             "open_questions with an owner and a deadline; it cannot ride along into a signature\n")
            sys.exit(2)
        if not a.by or not a.by.strip():
            sys.stderr.write("agenda: --by is required: a ruling without a name is not a ruling\n"); sys.exit(2)
        item = find_item(card, a.rule)
        text = apply_ruling(a.card, card, item, a.resolution.strip(), a.by.strip())
        left = open_items(load(a.card))
        print(json.dumps({"ok": True, "ruled": item["id"], "recorded": text,
                          "still_open": [i["id"] for i in left]}, ensure_ascii=False, indent=2))
        return

    items = open_items(card)
    if a.check:
        if items:
            sys.stderr.write(f"agenda: {len(items)} item(s) still open: {[i['id'] for i in items]}\n")
            sys.exit(1)
        return
    if a.json:
        print(json.dumps({"card": a.card, "open": len(items), "items": items}, ensure_ascii=False, indent=2))
        return
    if not items:
        print("议程为空：这张卡没有未决项。")
        return
    print(f"这张卡还有 {len(items)} 项要你裁：\n")
    for n, it in enumerate(items, 1):
        print(f"{n}. [{it['id']}·{it['kind']}] {it['what']}")
        for k, v in (it["evidence"] or {}).items():
            if v:
                print(f"     {k}: {str(v)[:300]}")
        print(f"     写回：{it['where']}\n")


if __name__ == "__main__":
    main()
