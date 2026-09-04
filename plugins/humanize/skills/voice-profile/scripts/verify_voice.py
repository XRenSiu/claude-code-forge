#!/usr/bin/env python3
"""verify_voice.py — 声音档案（voice.md）的机械出口。

检产物不检过程。reject 的是让档案不可执行的缺陷：
  - 缺必需节（读者与场合 / 节奏数据 / 句子习惯 / 忌口表 / 正例）；
  - 节奏数据表里仍是模板占位（<…>）或没有数字；
  - 句子习惯条目没有原文引用（「…」或 "…" 或 > 引用块）；
  - 忌口表条目没有"换成"列；
  - 正例少于 3 段；
  - 出现人格形容词（温暖/严谨/犀利/幽默/warm/rigorous/witty…）——不可核对；
  - 超过 150 行。
flag：正例主题疑似重复（标题相同）；confidence 缺失。

用法：python3 verify_voice.py <voice.md> [--json]
退出码：0 pass（可带 flag），1 reject。
"""

from __future__ import annotations

import argparse
import json
import re
import sys

REQUIRED = [
    ("读者与场合", r"读者与场合|Audience"),
    ("节奏数据", r"节奏数据|Rhythm"),
    ("句子习惯", r"句子习惯|Sentence habits"),
    ("忌口表", r"忌口表|Avoid|Never say"),
    ("正例", r"正例|Positive examples"),
]
PERSONALITY = re.compile(r"温暖|严谨|犀利|幽默|睿智|真诚|亲切|沉稳|理性|感性|\bwarm\b|\brigorous\b|\bwitty\b|\bthoughtful\b|\bsincere\b|\bpassionate\b|\bcharismatic\b", re.IGNORECASE)
QUOTE = re.compile(r"「[^」]{4,}」|“[^”]{4,}”|\"[^\"]{8,}\"|^\s*>\s*\S")
PLACEHOLDER = re.compile(r"<[^>]{1,40}>|…")


def sections(lines):
    out, cur = {}, None
    for i, l in enumerate(lines):
        m = re.match(r"^\s{0,3}#{1,6}\s+(.*)", l)
        if m:
            cur = m.group(1).strip()
            out[cur] = []
        elif cur is not None:
            out[cur].append((i + 1, l))
    return out


def find(secs, pattern):
    rx = re.compile(pattern, re.IGNORECASE)
    return [(t, b) for t, b in secs.items() if rx.search(t)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    try:
        lines = open(args.path, encoding="utf-8").read().splitlines()
    except OSError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    rejects, flags = [], []
    secs = sections(lines)

    for name, pat in REQUIRED:
        if not find(secs, pat):
            rejects.append(f"缺必需节「{name}」")

    if len(lines) > 150:
        rejects.append(f"{len(lines)} 行 > 150：这是风格论文，不是工具")

    rhythm = find(secs, r"节奏数据|Rhythm")
    if rhythm:
        body = "\n".join(l for _, l in rhythm[0][1])
        if PLACEHOLDER.search(body) or not re.search(r"\d", body):
            rejects.append("节奏数据仍是模板占位或没有数字——必须来自 humanlint --json")

    habits = find(secs, r"句子习惯|Sentence habits")
    if habits:
        items = [l for _, l in habits[0][1] if re.match(r"^\s*[-*]\s+", l)]
        bad = [l for l in items if not QUOTE.search(l)]
        if items and bad:
            rejects.append(f"{len(bad)}/{len(items)} 条句子习惯没有原文引用：{bad[0].strip()[:40]}")
        if not items:
            rejects.append("句子习惯节没有条目")

    avoid = find(secs, r"忌口表|Avoid|Never say")
    if avoid:
        rows = [l for _, l in avoid[0][1] if l.strip().startswith("|") and not re.match(r"^\s*\|\s*-", l) and "不用" not in l and "换成" not in l]
        bad = [r for r in rows if len([c for c in r.split("|")[1:-1] if c.strip()]) < 2 or PLACEHOLDER.search(r)]
        if not rows:
            rejects.append("忌口表为空")
        elif bad:
            rejects.append(f"{len(bad)} 条忌口没有替换或仍是占位：{bad[0].strip()[:40]}")

    pos = find(secs, r"正例|Positive examples")
    if pos:
        # 正例的子标题（### 1. 主题）
        titles = [t for t in secs if re.match(r"^\d+\.\s*", t)]
        quotes = sum(1 for t in titles for _, l in secs[t] if l.strip().startswith(">"))
        if len(titles) < 3 or quotes < 3:
            rejects.append(f"正例只有 {len(titles)} 段（引用 {quotes}）< 3")
        topics = [re.sub(r"^\d+\.\s*", "", t).split("（")[0].strip() for t in titles]
        if len(set(topics)) < len(topics):
            flags.append("正例主题重复——同一主题只取一篇")

    full = "\n".join(lines)
    ph = PERSONALITY.findall(full)
    if ph:
        rejects.append(f"出现人格形容词 {sorted(set(ph))[:5]}——不可核对，改成写法")
    if not re.search(r"confidence:\s*(high|medium|low)", full, re.IGNORECASE):
        flags.append("缺 confidence 标注")

    result = {"verdict": "reject" if rejects else ("flag" if flags else "pass"), "rejects": rejects, "flags": flags, "lines": len(lines)}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"verify_voice · {len(lines)} 行 · verdict = {result['verdict'].upper()}")
        for r in rejects:
            print(f"  REJECT  {r}")
        for f in flags:
            print(f"  FLAG    {f}")
    return 1 if rejects else 0


if __name__ == "__main__":
    sys.exit(main())
