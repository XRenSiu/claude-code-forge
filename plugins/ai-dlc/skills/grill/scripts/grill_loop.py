#!/usr/bin/env python3
"""grill_loop.py — 需求对齐环的机械部分：待定清单 · 来路核对 · 四键停机。

缺口（为什么不是一句 prompt）：让 Agent 自己 grill 自己、直到"它认为对齐了"再停——这个停机判据
不可信（Ambig-SWE：模型分不清一个任务写清楚了没有）。本脚本把停机从自评换成三样可核对的东西：

  1. **待定清单**（pending.yaml）——从 PSL 的 Open Questions（seam）、psl-derive 的分歧表（D-n）与
     「PSL 欠定」条目机械抽出来。它是"形状"数出来的槽，不是 Agent 临时想到的问题。
  2. **来路核对**——每一条只能以三种方式离开清单：`resolve --from materials`（必须给能在物料树里
     找到的文件，找不到 = 拒）、`resolve --from human --by <人>`、`defer --why`（机器找过、找不到，
     留给人）。`--from default` 被硬拒：默认值糊上的槽比空着的槽更危险。
  3. **四键停机**（check）——success：open=0 ∧ needs_human=0 ∧ 分歧率 ≤ max ∧ 本轮 resolve 都已重推；
     convergence：open 数连续 N 轮不降（plateau）；budget：轮数上限；impossible：分歧率 > 0.5
     （PSL 约束太弱，回 /psl 补 Mental Model / Domain Model，不许多数表决糊过去）。

用法：
  grill_loop.py pending <PSL.md> [--derived DIR] [--out DIR] [--material-root DIR]... [--json]
  grill_loop.py resolve <DIR> <ITEM> --from materials --provenance "<file> [§N]" --answer "…" [--material-root DIR]...
  grill_loop.py resolve <DIR> <ITEM> --from human --by <人> --answer "…"
  grill_loop.py defer   <DIR> <ITEM> --why "…"
  grill_loop.py check   <DIR> [--derived DIR] [--max-divergence 0.20] [--max-rounds 4] [--plateau 2] [--record] [--json]

退出码：
  pending / resolve / defer   0 ok · 1 reject · 2 用法 / IO
  check                       0 converged（机器与人的份额都做完，可进 G1 签字）
                              10 human（open=0，剩余项全部 needs_human：机器份额做完，把清单交人）
                              20 continue（还有 open 项，或本轮有 resolve 尚未重推：回 /psl 补槽 → /psl-derive 重推 → pending）
                              1 stop（impossible / budget / plateau：升级到人，不再自动转）
                              2 用法 / IO

pending 可重复运行：同一条槽（按来源 + 归一化文本对齐）保留已有的状态与答案；divergence.md 内容变了
即视为新一轮（round +1）。resolve 记下 `resolved_in_round`；check 发现本轮有 resolve 而没有新一轮推导
时判 continue（reason=rederive）——"拿答案重推一次"是环的一部分，不是可选项。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import sys

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

OPEN_Q_RE = re.compile(r"open\s*questions?|开放问题|未决", re.I)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)")
BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.、)])\s+(.*)")
D_ROW_RE = re.compile(r"^\|\s*(D-\d+)\s*\|")
WHY_RE = re.compile(r"[（(]\s*(?:承重|why|为什么(?:需要人来定)?)\s*[:：]?\s*([^)）]*)[)）]", re.I)
LOAD_BEARING_RE = re.compile(r"承重|load[-\s]?bearing", re.I)
USER_ELICIT_RE = re.compile(r"\[elicit\s*[:：]\s*(?:用户|user)\b", re.I)
MATERIAL_EXT = (".md", ".markdown", ".yaml", ".yml", ".json", ".py", ".sh", ".txt", ".toml", ".cfg", ".ts", ".js")
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
STATUSES = ("open", "resolved_materials", "resolved_human", "needs_human", "dropped_from_source")


def die(msg, code=2):
    sys.stderr.write(f"grill_loop: {msg}\n")
    sys.exit(code)


def need_yaml():
    if yaml is None:
        die("PyYAML required (pip install pyyaml)")


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        die(f"cannot read {path}: {e}")


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def now():
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def norm(text):
    return re.sub(r"\s+", "", text or "").lower()


def ledger_append(out_dir, kind, text):
    p = os.path.join(out_dir, "grill-ledger.md")
    new = not os.path.isfile(p)
    with open(p, "a", encoding="utf-8") as f:
        if new:
            f.write("# grill ledger — 只增不删\n\n")
        f.write(f"- {now()} `{kind}` {text}\n")


# ---------------------------------------------------------------- extraction ----------

def sections(lines):
    """[(title, level, start, end)]，跳过 fenced block 里的标题。"""
    heads, fence = [], False
    for i, line in enumerate(lines):
        if re.match(r"^\s*(```|~~~)", line):
            fence = not fence
            continue
        if fence:
            continue
        m = HEADING_RE.match(line)
        if m:
            heads.append((m.group(2).strip(), len(m.group(1)), i))
    out = []
    for idx, (t, lv, s) in enumerate(heads):
        e = len(lines)
        for t2, lv2, s2 in heads[idx + 1:]:
            if lv2 <= lv:
                e = s2
                break
        out.append((t, lv, s, e))
    return out


def open_questions(psl_text):
    """PSL 的 Open Questions 条目（顶层 bullet，续行合并）。"""
    lines = psl_text.splitlines()
    sec = next((s for s in sections(lines) if OPEN_Q_RE.search(s[0])), None)
    if not sec:
        return None
    items, cur, fence = [], None, False
    for line in lines[sec[2] + 1:sec[3]]:
        if re.match(r"^\s*(```|~~~)", line):
            fence = not fence
            continue
        if fence:
            continue
        m = BULLET_RE.match(line)
        if m and not line.startswith(("  ", "\t")):
            if cur:
                items.append(cur)
            cur = m.group(1).strip()
        elif cur and line.strip():
            cur += " " + line.strip()
        elif cur:
            items.append(cur)
            cur = None
    if cur:
        items.append(cur)
    return items


def divergence_rows(dv_text):
    rows = []
    for line in dv_text.splitlines():
        m = D_ROW_RE.match(line)
        if not m:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append({"id": m.group(1), "cells": cells})
    return rows


def divergence_meta(dv_text):
    n = re.search(r"^\s*n\s*:\s*(\d+)", dv_text, re.M)
    k = re.search(r"^\s*consistent_decisions\s*:\s*(\d+)", dv_text, re.M)
    rows = divergence_rows(dv_text)
    n = int(n.group(1)) if n else None
    k = int(k.group(1)) if k else None
    rate = None
    if n and n > 1 and k is not None and (len(rows) + k) > 0:
        rate = round(len(rows) / (len(rows) + k), 3)
    return {"n": n, "consistent_decisions": k, "rows": len(rows), "rate": rate}


def underdetermined(dv_text):
    m = re.search(r"^##\s*PSL\s*欠定.*?$(.*?)(?=^##|\Z)", dv_text, re.S | re.M)
    if not m:
        return []
    out = []
    for line in m.group(1).splitlines():
        b = BULLET_RE.match(line)
        if b and not b.group(1).startswith("<"):
            out.append(b.group(1).strip())
    return out


def why_of(text):
    m = WHY_RE.search(text)
    return m.group(1).strip() if m else ""


def build_items(psl_text, dv_text):
    items, flags = [], []
    oq = open_questions(psl_text)
    if oq is None:
        flags.append("PSL 没有 Open Questions 节——verify_psl.py 会拒；清单只能从分歧集抽")
        oq = []
    for t in oq:
        items.append({"source": "open_question", "text": t, "why_human": why_of(t),
                      "load_bearing": bool(LOAD_BEARING_RE.search(t))})
    if dv_text:
        for r in divergence_rows(dv_text):
            c = r["cells"]
            if len(c) < 7:
                flags.append(f"{r['id']}: 分歧行不足 7 格（verify_derived.py 会拒），议程读不到")
            point = c[1] if len(c) > 1 else r["id"]
            agenda = c[6] if len(c) > 6 else ""
            items.append({"source": "divergence", "text": f"{point} — v: {' / '.join(c[2:5]) if len(c) > 4 else '?'}",
                          "why_human": agenda, "load_bearing": True, "divergence_id": r["id"],
                          "refs": c[5] if len(c) > 5 else ""})
        for u in underdetermined(dv_text):
            hint = re.search(r"建议\s*[:：]?\s*(.+)$", u)
            items.append({"source": "underdetermined", "text": u,
                          "why_human": why_of(u) or (hint.group(1).strip() if hint else ""), "load_bearing": True})
    for it in items:
        if not it["why_human"]:
            flags.append(f"{it['source']} 「{it['text'][:40]}」没有写为什么需要人来定——交给人之前补上（否则人不知道该裁什么）")
    return items, flags


# ---------------------------------------------------------------- materials -----------

def find_material(name, roots, cap=20000):
    """在物料树里找 <name>（basename 或相对路径）。返回命中路径或 None。"""
    name = name.strip().strip("`")
    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        cand = os.path.join(root, name)
        if os.path.isfile(cand):
            return cand
    base = os.path.basename(name).lower()
    n = 0
    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        for dp, dns, fns in os.walk(root):
            dns[:] = [d for d in dns if d not in SKIP_DIRS and not d.startswith(".")]
            for fn in fns:
                n += 1
                if n > cap:
                    return None
                if fn.lower() == base and fn.lower().endswith(MATERIAL_EXT):
                    return os.path.join(dp, fn)
    return None


def provenance_file(prov):
    """`<file> §N` / `<file>#3` / `file:line` → file token。"""
    tok = re.split(r"\s+|§|#", prov.strip())[0]
    return tok.split(":")[0] if re.search(r"\.[A-Za-z]{1,6}:\d+$", tok) else tok


# ---------------------------------------------------------------- state ---------------

def load_pending(out_dir):
    need_yaml()
    p = os.path.join(out_dir, "pending.yaml")
    if not os.path.isfile(p):
        die(f"no pending.yaml in {out_dir} — run `pending` first")
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_pending(out_dir, doc):
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "pending.yaml")
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        yaml.safe_dump(doc, f, allow_unicode=True, sort_keys=False)
    os.replace(tmp, p)


def find_item(doc, item_id):
    for it in doc.get("items") or []:
        if it.get("id") == item_id:
            return it
    die(f"no item {item_id} in pending.yaml (ids: {[i.get('id') for i in doc.get('items') or []]})", 1)


# ---------------------------------------------------------------- commands ------------

def cmd_pending(a):
    need_yaml()
    psl_text = read(a.psl)
    dv_path = os.path.join(a.derived, "divergence.md") if a.derived else None
    dv_text = read(dv_path) if dv_path and os.path.isfile(dv_path) else ""
    if a.derived and not dv_text:
        die(f"{a.derived} has no divergence.md — run /psl-derive first (or omit --derived)", 1)
    items, flags = build_items(psl_text, dv_text)
    out_dir = a.out or "grill"
    prev = None
    ppath = os.path.join(out_dir, "pending.yaml")
    if os.path.isfile(ppath):
        with open(ppath, encoding="utf-8") as f:
            prev = yaml.safe_load(f) or {}
    dv_sha = sha(dv_text) if dv_text else None
    round_no = 1
    if prev:
        round_no = int(prev.get("round") or 1)
        if dv_sha and prev.get("divergence_sha") and dv_sha != prev.get("divergence_sha"):
            round_no += 1
    prev_items = {(i.get("source"), norm(i.get("text"))): i for i in (prev or {}).get("items") or []}
    counters = {"open_question": 0, "divergence": 0, "underdetermined": 0}
    prefix = {"open_question": "Q", "divergence": "D", "underdetermined": "U"}
    merged, seen = [], set()
    for it in items:
        key = (it["source"], norm(it["text"]))
        seen.add(key)
        old = prev_items.get(key)
        counters[it["source"]] += 1
        rec = dict(old) if old else {}
        rec.update({k: v for k, v in it.items()})
        rec.setdefault("id", f"{prefix[it['source']]}-{counters[it['source']]}")
        rec.setdefault("status", "open")
        rec.setdefault("answer", None)
        rec.setdefault("provenance", None)
        rec.setdefault("by", None)
        merged.append(rec)
    for key, old in prev_items.items():
        if key in seen:
            continue
        rec = dict(old)
        if rec.get("status") == "open":
            rec["status"] = "dropped_from_source"
            rec["note"] = f"round {round_no}: 来源里已不存在（PSL / divergence.md 改了）——不是 resolved，只是没人再问它"
        merged.append(rec)
    doc = {"version": 1, "psl": os.path.abspath(a.psl), "derived": os.path.abspath(a.derived) if a.derived else None,
           "round": round_no, "divergence_sha": dv_sha, "divergence": divergence_meta(dv_text) if dv_text else None,
           "generated_at": now(), "flags": flags, "items": merged}
    save_pending(out_dir, doc)
    ledger_append(out_dir, "pending", f"round={round_no} items={len(merged)} open={sum(1 for i in merged if i['status']=='open')} flags={len(flags)}")
    summary = {"ok": True, "out": ppath, "round": round_no, "items": len(merged),
               "open": sum(1 for i in merged if i["status"] == "open"), "flags": flags,
               "divergence": doc["divergence"]}
    print(json.dumps(summary, ensure_ascii=False, indent=2) if a.json else
          f"pending.yaml written: {ppath}\nround={round_no} items={len(merged)} open={summary['open']}" +
          ("".join(f"\nFLAG: {f}" for f in flags)))
    return 0


def cmd_resolve(a):
    doc = load_pending(a.dir)
    it = find_item(doc, a.item)
    if a.frm == "default":
        die(f"{a.item}: `--from default` is not a way out — a slot filled with a default looks full and is not. "
            f"Use --from materials (with a checkable provenance) or leave it to a human (defer)", 1)
    if not a.answer:
        die("--answer required", 2)
    if a.frm == "materials":
        if not a.provenance:
            die("--from materials requires --provenance \"<file> [§N]\"", 2)
        roots = a.material_root or [os.path.dirname(doc.get("psl") or "") or ".", os.getcwd()]
        fname = provenance_file(a.provenance)
        hit = find_material(fname, roots)
        if not hit:
            die(f"{a.item}: provenance `{a.provenance}` — file `{fname}` not found under {roots}. "
                f"A provenance nobody can open is a default fill with a citation-shaped hat", 1)
        it.update({"status": "resolved_materials", "answer": a.answer, "provenance": a.provenance,
                   "provenance_path": hit, "by": None, "resolved_in_round": doc.get("round"), "resolved_at": now()})
    elif a.frm == "human":
        if not a.by:
            die("--from human requires --by <人>", 2)
        it.update({"status": "resolved_human", "answer": a.answer, "provenance": None, "by": a.by,
                   "resolved_in_round": doc.get("round"), "resolved_at": now()})
    else:
        die(f"unknown --from {a.frm!r}", 2)
    save_pending(a.dir, doc)
    ledger_append(a.dir, "resolve", f"{a.item} from={a.frm} prov={a.provenance or '-'} by={a.by or '-'}: {a.answer[:80]}")
    print(json.dumps({"ok": True, "item": a.item, "status": it["status"], "round": doc.get("round")}, ensure_ascii=False))
    return 0


def cmd_defer(a):
    doc = load_pending(a.dir)
    it = find_item(doc, a.item)
    if not a.why:
        die("--why required: say what the machine looked for and why it is a human's call", 2)
    it.update({"status": "needs_human", "why_human": a.why if not it.get("why_human") else f"{it['why_human']} ｜ {a.why}",
               "deferred_in_round": doc.get("round")})
    save_pending(a.dir, doc)
    ledger_append(a.dir, "defer", f"{a.item}: {a.why[:100]}")
    print(json.dumps({"ok": True, "item": a.item, "status": "needs_human"}, ensure_ascii=False))
    return 0


def cmd_check(a):
    doc = load_pending(a.dir)
    items = doc.get("items") or []
    round_no = int(doc.get("round") or 1)
    dv_text = ""
    derived = a.derived or doc.get("derived")
    if derived and os.path.isfile(os.path.join(derived, "divergence.md")):
        dv_text = read(os.path.join(derived, "divergence.md"))
    meta = divergence_meta(dv_text) if dv_text else (doc.get("divergence") or {"n": None, "rows": 0, "rate": None})
    rate = meta.get("rate")
    cnt = {s: sum(1 for i in items if i.get("status") == s) for s in STATUSES}
    unrederived = [i["id"] for i in items if i.get("status") in ("resolved_materials", "resolved_human")
                   and i.get("resolved_in_round") == round_no]
    stale_sha = bool(dv_text) and doc.get("divergence_sha") and sha(dv_text) != doc.get("divergence_sha")

    # rounds.jsonl：plateau 的记忆
    hist = []
    rpath = os.path.join(a.dir, "rounds.jsonl")
    if os.path.isfile(rpath):
        with open(rpath, encoding="utf-8") as f:
            hist = [json.loads(l) for l in f if l.strip()]
    if a.record:
        rec = {"round": round_no, "at": now(), "open": cnt["open"], "needs_human": cnt["needs_human"],
               "resolved": cnt["resolved_materials"] + cnt["resolved_human"], "divergence_rate": rate}
        if not hist or hist[-1].get("round") != round_no:
            hist.append(rec)
            with open(rpath, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        else:
            hist[-1] = rec

    verdict, stop_key, reasons = None, None, []
    if rate is not None and rate > 0.5:
        verdict, stop_key = "impossible", "impossible"
        reasons.append(f"divergence rate {rate} > 0.5 — PSL 约束太弱；回 /psl 补 Mental Model / Domain Model，不用多数表决糊过去")
    elif round_no > a.max_rounds:
        verdict, stop_key = "budget", "budget"
        reasons.append(f"round {round_no} > max_rounds {a.max_rounds}")
    elif cnt["open"] > 0 and len(hist) >= a.plateau and all(h.get("open") == cnt["open"] for h in hist[-a.plateau:]) \
            and len({h.get("round") for h in hist[-a.plateau:]}) >= a.plateau:
        verdict, stop_key = "plateau", "convergence"
        reasons.append(f"open={cnt['open']} unchanged across the last {a.plateau} rounds — the machine is not finding provenance; hand the list over")
    elif stale_sha:
        verdict = "continue"
        reasons.append("divergence.md changed since pending.yaml was built — run `pending` again (new round)")
    elif cnt["open"] > 0:
        verdict = "continue"
        reasons.append(f"{cnt['open']} open item(s): try materials (resolve --from materials) or defer --why")
    elif unrederived:
        verdict = "continue"
        reasons.append(f"resolved in this round but not re-derived yet: {unrederived} — patch the PSL, run /psl-derive round {round_no + 1}, then `pending`")
    elif cnt["needs_human"] > 0:
        verdict = "human"
        reasons.append(f"{cnt['needs_human']} item(s) need a human — hand over pending.yaml (only these), not the whole PSL")
    else:
        if rate is not None and rate > a.max_divergence:
            verdict = "continue"
            reasons.append(f"all items closed but divergence rate {rate} > {a.max_divergence} — the last derivation still disagrees; re-derive")
        else:
            verdict, stop_key = "converged", "success"
            reasons.append("open=0 ∧ needs_human=0 ∧ 本轮无未重推的 resolve" + (f" ∧ divergence {rate} ≤ {a.max_divergence}" if rate is not None else " (n=1：未做分歧检验，声明在案)"))
    if meta.get("n") == 1:
        reasons.append("divergence.md n: 1 — 未做分歧检验；success 只覆盖清单，不覆盖分歧率")
    out = {"verdict": verdict, "stop_key": stop_key, "round": round_no, "counts": cnt, "divergence": meta,
           "unrederived": unrederived, "reasons": reasons,
           "next": {"converged": "G1: sign form-draft; pending.yaml + grill-ledger.md go into g1-record.md",
                    "human": "hand pending.yaml (needs_human rows) to the human; then resolve --from human, patch PSL, re-derive",
                    "continue": "keep the machine phase going", "impossible": "escalate to world layer (/psl)",
                    "budget": "escalate: write the failure report, hand over", "plateau": "escalate: hand the open items over as needs_human"}[verdict]}
    code = {"converged": 0, "human": 10, "continue": 20}.get(verdict, 1)
    if a.record:
        ledger_append(a.dir, "check", f"round={round_no} verdict={verdict} open={cnt['open']} needs_human={cnt['needs_human']} rate={rate}")
    print(json.dumps(out, ensure_ascii=False, indent=2) if a.json else
          f"verdict={verdict} (exit {code}) round={round_no} open={cnt['open']} needs_human={cnt['needs_human']} "
          f"resolved={cnt['resolved_materials'] + cnt['resolved_human']} rate={rate}\n" + "\n".join(f"- {r}" for r in reasons) + f"\nnext: {out['next']}")
    return code


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pending", help="从 PSL Open Questions + divergence.md 抽待定清单")
    p.add_argument("psl"); p.add_argument("--derived"); p.add_argument("--out")
    p.add_argument("--material-root", action="append", default=[]); p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_pending)
    p = sub.add_parser("resolve", help="以可核对的来路关闭一条槽")
    p.add_argument("dir"); p.add_argument("item"); p.add_argument("--from", dest="frm", required=True)
    p.add_argument("--provenance"); p.add_argument("--answer"); p.add_argument("--by")
    p.add_argument("--material-root", action="append", default=[])
    p.set_defaults(fn=cmd_resolve)
    p = sub.add_parser("defer", help="机器找过、找不到：留给人")
    p.add_argument("dir"); p.add_argument("item"); p.add_argument("--why")
    p.set_defaults(fn=cmd_defer)
    p = sub.add_parser("check", help="四键停机裁决")
    p.add_argument("dir"); p.add_argument("--derived"); p.add_argument("--max-divergence", type=float, default=0.20)
    p.add_argument("--max-rounds", type=int, default=4); p.add_argument("--plateau", type=int, default=2)
    p.add_argument("--record", action="store_true", help="把本轮计数写进 rounds.jsonl（plateau 的记忆）")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_check)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
