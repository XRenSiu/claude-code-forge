#!/usr/bin/env python3
"""verify_techdoc.py — 技术文档"产物序"的机械预门（L0）。

检产物不检过程。它检查成品是否呈现资深工程师方案的形状（references/skeleton.md 十动作），
不检查方案本身对不对（那是评审的活）。

reject（退出码 1）：
  - 第一段没有任何具体锚点（数字/日期/标识符/专名）——套路化开头；
  - 前 3 段里找不到决定句（我们会/我建议/我们把/We will/I propose/I recommend/Decision）——结论埋没；
  - 方案/设计体裁缺"没选 X 因为…"的替代方案否决（没选/不选/未选/放弃/Alternatives/Rejected/rather than X because）；
  - 缺未决问题/开放问题/下一步/回滚 中的至少一项（结尾是复述而非新信息）；
  - 结尾段以 总之/综上/In conclusion/Overall 开头。
flag（needs_review，不拦）：
  - 没有非目标/不做什么；风险没有兜底词（兜底/回滚/降级/fallback/owner/负责人）；
  - 正文 bullet 行占比 > 45%；每段都没有数字；出现"本节将/本文将/In this section/This document aims"。

用法：python3 verify_techdoc.py <doc.md> [--genre proposal|design|adr|postmortem|memo|readme] [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys

CONCRETE = re.compile(r"`[^`]+`|\d+(?:[.,]\d+)*\s?(?:%|ms|s|min|h|GB|MB|QPS|rps|qps|x|倍|万|亿|个|次|条|台|人|天|周|月|年|行|秒|分钟|小时)?|\b[A-Z][a-zA-Z]+(?:[A-Z][a-zA-Z]+)+\b|\b[A-Z]{2,}\b|\d{1,2}月\d{1,2}日|上周|昨天|前天|本周")
DECISION = re.compile(r"我们会|我们将|我建议|我们建议|我打算|我们决定|我们把|我想把|我们要|我提议|决定[:：]|结论[:：]|\bWe will\b|\bWe'll\b|\bI propose\b|\bI recommend\b|\bWe recommend\b|\bI want to\b|\bWe are going to\b|\bDecision[:：]|\bWe decided\b|\bWe chose\b", re.IGNORECASE)
ALTERNATIVE = re.compile(r"没有?选|不选|未选|没采用|不采用|放弃了?|否决|替代方案|备选|另一个方案|也可以用.{0,20}但|\bAlternatives?\b|\bRejected\b|\bAbandoned\b|\binstead of\b|\bwould also work,? but\b|\bI didn'?t (choose|pick|go with)\b|\bwe didn'?t (choose|pick|go with)\b|\bnot (proposing|choosing)\b", re.IGNORECASE)
OPEN_END = re.compile(r"未决|没想清楚|不确定|开放问题|Open questions?|待定|下一步|排期|回滚|Rollback|Rollout|灰度|unsure|what I'?m not sure|TBD", re.IGNORECASE)
NONGOAL = re.compile(r"非目标|不做|不在范围|不包括|不打算|只做|先只|先不|暂不|不动|不碰|这次不|Non-?goals?|out of scope|not (proposing|touching|going to)|only (this|the) one|leave .{0,20} alone", re.IGNORECASE)
FALLBACK = re.compile(r"兜底|回滚|降级|绕过|开关|fallback|rollback|kill ?switch|feature flag|owner|负责人|on-?call", re.IGNORECASE)
CLOSER = re.compile(r"^\s*(总之|综上|综上所述|总而言之|总的来说|让我们|In conclusion|In summary|To summarize|Overall|Ultimately)", re.IGNORECASE)
NARRATION = re.compile(r"本节将|本文将|本文旨在|本方案旨在|接下来我们|In this (section|document)|This (document|section|proposal) (aims|will|explores)|Let'?s (dive|explore)", re.IGNORECASE)
HEDGE_GENERIC = re.compile(r"一定的风险|一定的挑战|相应的措施|完善的应对|certain risks|some challenges|appropriate measures|comprehensive testing", re.IGNORECASE)
BULLET = re.compile(r"^\s*(?:[-*+•]|\d+[.)、])\s+")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+")
FENCE = re.compile(r"^\s*(```|~~~)")

REQUIRED_ALT = {"proposal", "design", "adr", "memo"}
REQUIRED_DECISION = {"proposal", "design", "adr", "memo"}


def paragraphs(text: str):
    """散文段落列表（跳过代码块、标题、表格；bullet 块整体算一段）。"""
    paras, buf, in_fence, in_list = [], [], False, False
    for line in text.splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence or HEADING.match(line) or line.strip().startswith("|"):
            if buf:
                paras.append(" ".join(buf)); buf = []
            in_list = False
            continue
        if not line.strip():
            if buf:
                paras.append(" ".join(buf)); buf = []
            in_list = False
            continue
        if BULLET.match(line):
            if buf and not in_list:
                paras.append(" ".join(buf)); buf = []
            in_list = True
        buf.append(line.strip())
    if buf:
        paras.append(" ".join(buf))
    return paras


def guess_genre(text: str) -> str:
    t = text[:600]
    if re.search(r"复盘|postmortem|incident|故障回顾|时间线", t, re.I):
        return "postmortem"
    if re.search(r"\bADR\b|Decision Record|决策记录", t, re.I):
        return "adr"
    if re.search(r"设计文档|Design Doc|详细设计", t, re.I):
        return "design"
    if re.search(r"README|安装|Getting started", t, re.I):
        return "readme"
    return "proposal"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path")
    ap.add_argument("--genre", default="auto", choices=["auto", "proposal", "design", "adr", "postmortem", "memo", "readme"])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    try:
        text = open(args.path, encoding="utf-8").read()
    except OSError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    genre = guess_genre(text) if args.genre == "auto" else args.genre
    body = re.sub(r"^---.*?---\s*", "", text, count=1, flags=re.S)
    paras = paragraphs(body)
    rejects, flags = [], []

    if not paras:
        print("REJECT: 没有正文段落")
        return 1

    first = paras[0]
    if not CONCRETE.search(first):
        rejects.append(f"第一段没有任何具体锚点（数字/日期/标识符/专名）——套路化开头：「{first[:40]}…」")

    head = " ".join(paras[:3])
    if genre in REQUIRED_DECISION and not DECISION.search(head):
        rejects.append("前 3 段里没有决定句（我们会/我建议/We will/I propose…）——结论埋没或不存在")

    if genre in REQUIRED_ALT and not ALTERNATIVE.search(body):
        rejects.append("找不到被否决的替代方案（没选 X 因为…/Alternatives/instead of…）——读者无法判断你是选了还是只是想到了")

    if not OPEN_END.search(body):
        rejects.append("没有未决问题/下一步/回滚/排期——结尾是复述而不是新信息")

    last = paras[-1]
    if CLOSER.match(last):
        rejects.append(f"结尾段是总结式：「{last[:30]}…」——删掉，或换成下一步/未决点")

    if genre in {"proposal", "design"} and not NONGOAL.search(body):
        flags.append("没有非目标/不做什么——范围边界不明")
    if genre in {"proposal", "design", "adr"} and re.search(r"风险|Risk", body) and not FALLBACK.search(body):
        flags.append("提到了风险但没有兜底/回滚/负责人")
    lines = [l for l in body.splitlines() if l.strip() and not HEADING.match(l) and not l.strip().startswith("|")]
    bl = sum(1 for l in lines if BULLET.match(l))
    if lines and bl / len(lines) > 0.45:
        flags.append(f"bullet 行占正文 {bl / len(lines):.0%}——论证被列表替代")
    if NARRATION.search(body):
        flags.append("出现叙述文档自身的句子（本节将/本文旨在/In this section…）")
    if HEDGE_GENERIC.search(body):
        flags.append("出现通用风险套话（一定的风险/相应的措施/certain risks/comprehensive testing）——风险没有具体化")
    no_num = [i + 1 for i, p in enumerate(paras) if not CONCRETE.search(p) and len(p) > 60]
    if len(paras) >= 4 and len(no_num) >= max(2, len(paras) // 2):
        flags.append(f"{len(no_num)}/{len(paras)} 段没有任何具体锚点：第 {no_num[:6]} 段")

    result = {"genre": genre, "paragraphs": len(paras), "verdict": "reject" if rejects else ("flag" if flags else "pass"),
              "rejects": rejects, "flags": flags}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"verify_techdoc · genre={genre} · {len(paras)} 段 · verdict = {result['verdict'].upper()}")
        for r in rejects:
            print(f"  REJECT  {r}")
        for f in flags:
            print(f"  FLAG    {f}")
        if not rejects and not flags:
            print("  形状齐全。方案对不对，脚本不判。")
    return 1 if rejects else 0


if __name__ == "__main__":
    sys.exit(main())
