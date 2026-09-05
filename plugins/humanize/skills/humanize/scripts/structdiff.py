#!/usr/bin/env python3
"""structdiff.py — "只改表述、不动骨架"的机械闸门（--keep-structure 的编译态）。

humanize 的判据默认会把列表展开成段、删标题、去加粗——那是给方案 / ADR / 备忘录用的。
报告、README、参考文档的骨架是读者扫读的入口，改写只许动散文段里的句子。本脚本抽取两份 markdown 的
结构骨架并比对：

  硬（差异 = fail）：标题的层级序列（文字可改，层级 / 数量 / 顺序不可）、列表块的数量与每块的项数（有序 / 无序不可互换）、
                     表格的数量与每张的行列数、代码块的数量与内容（逐字）、块的先后顺序（段落连续段折叠成一个 P，所以拆并段落合法）。
  软（差异 = warn）：标题文字改动、加粗总数变化超过 30%、某段落连续段的段数变化超过一倍。

用法：
  python3 structdiff.py <source.md> <rewrite.md> [--json]

退出码：0 = pass / warn，1 = fail（骨架被动了），2 = IO 或用法错误。
骨架改动只能由人做：脚本没有 --allow；要动结构就别开 --keep-structure。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys

HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
UL = re.compile(r"^(\s*)[-*+•]\s+")
OL = re.compile(r"^(\s*)\d+[.)、]\s+")
TABLE = re.compile(r"^\s*\|")
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")
HR = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$")
QUOTE = re.compile(r"^\s*>")
BOLD = re.compile(r"\*\*[^*\n]+\*\*")


def skeleton(text: str):
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        try:
            lines = lines[lines.index("---", 1) + 1:]
        except ValueError:
            pass
    blocks = []          # (kind, payload)
    i, n = 0, len(lines)
    bold_total = 0
    while i < n:
        ln = lines[i]
        if FENCE.match(ln):
            mark = FENCE.match(ln).group(1)
            body = []
            i += 1
            while i < n and not lines[i].startswith(mark):
                body.append(lines[i]); i += 1
            i += 1
            blocks.append(("FENCE", hashlib.sha1("\n".join(body).encode()).hexdigest()[:10]))
            continue
        if not ln.strip():
            i += 1; continue
        if HR.match(ln):
            blocks.append(("HR", None)); i += 1; continue
        m = HEADING.match(ln)
        if m:
            blocks.append(("H", (len(m.group(1)), m.group(2)))); i += 1; continue
        if TABLE.match(ln):
            rows, cols = 0, 0
            while i < n and TABLE.match(lines[i]):
                if not TABLE_SEP.match(lines[i]):
                    rows += 1
                    cols = max(cols, len([c for c in lines[i].strip().strip("|").split("|")]))
                bold_total += len(BOLD.findall(lines[i])); i += 1
            blocks.append(("TABLE", (rows, cols))); continue
        if UL.match(ln) or OL.match(ln):
            ordered = bool(OL.match(ln)); items, top = 0, 0
            base = len((UL.match(ln) or OL.match(ln)).group(1))
            while i < n and lines[i].strip():
                mm = UL.match(lines[i]) or OL.match(lines[i])
                if mm:
                    items += 1
                    if len(mm.group(1)) <= base:
                        top += 1
                bold_total += len(BOLD.findall(lines[i])); i += 1
            blocks.append(("OL" if ordered else "UL", (top, items))); continue
        if QUOTE.match(ln):
            while i < n and QUOTE.match(lines[i]):
                bold_total += len(BOLD.findall(lines[i])); i += 1
            blocks.append(("QUOTE", None)); continue
        # 段落：连续非空行
        while i < n and lines[i].strip() and not (HEADING.match(lines[i]) or TABLE.match(lines[i]) or UL.match(lines[i]) or OL.match(lines[i]) or FENCE.match(lines[i]) or QUOTE.match(lines[i]) or HR.match(lines[i])):
            bold_total += len(BOLD.findall(lines[i])); i += 1
        blocks.append(("P", None))
    # 折叠连续 P 为一个 P 段落串，记段数
    folded = []
    for kind, payload in blocks:
        if kind == "P" and folded and folded[-1][0] == "P":
            folded[-1] = ("P", folded[-1][1] + 1)
        else:
            folded.append((kind, 1 if kind == "P" else payload))
    return folded, bold_total


def hard_key(block):
    kind, payload = block
    if kind == "H":
        return ("H", payload[0])
    if kind == "P":
        return ("P",)
    return (kind, payload)


def render_block(block):
    kind, payload = block
    if kind == "H":
        return f"H{payload[0]}「{payload[1][:18]}」"
    if kind == "P":
        return f"P×{payload}"
    if kind in ("UL", "OL"):
        return f"{kind}({payload[0]}/{payload[1]})"
    if kind == "TABLE":
        return f"TABLE({payload[0]}×{payload[1]})"
    if kind == "FENCE":
        return f"FENCE#{payload}"
    return kind


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source"); ap.add_argument("rewrite"); ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    try:
        a_txt = open(args.source, encoding="utf-8").read()
        b_txt = open(args.rewrite, encoding="utf-8").read()
    except OSError as e:
        print(f"ERROR: {e}", file=sys.stderr); return 2
    a, a_bold = skeleton(a_txt)
    b, b_bold = skeleton(b_txt)
    hard_a, hard_b = [hard_key(x) for x in a], [hard_key(x) for x in b]
    problems, warns = [], []
    if hard_a != hard_b:
        # 定位第一处分歧
        k = next((j for j in range(min(len(a), len(b))) if hard_a[j] != hard_b[j]), min(len(a), len(b)))
        ctx_a = " ".join(render_block(x) for x in a[max(0, k - 2): k + 2]) or "（末尾）"
        ctx_b = " ".join(render_block(x) for x in b[max(0, k - 2): k + 2]) or "（末尾）"
        problems.append(f"骨架在第 {k + 1} 块开始不一致：源「{ctx_a}」 → 改写「{ctx_b}」")
        counts = lambda s, kind: sum(1 for x in s if x[0] == kind)
        for kind, label in (("H", "标题"), ("UL", "无序列表块"), ("OL", "有序列表块"), ("TABLE", "表格"), ("FENCE", "代码块")):
            if counts(a, kind) != counts(b, kind):
                problems.append(f"{label}数量 {counts(a, kind)} → {counts(b, kind)}")
        items = lambda s: sum(x[1][1] for x in s if x[0] in ("UL", "OL"))
        if items(a) != items(b):
            problems.append(f"列表项总数 {items(a)} → {items(b)}")
    # 软：标题文字、加粗、段数
    ha = [x[1][1] for x in a if x[0] == "H"]; hb = [x[1][1] for x in b if x[0] == "H"]
    if len(ha) == len(hb):
        changed = [(x, y) for x, y in zip(ha, hb) if x.strip() != y.strip()]
        if changed:
            warns.append(f"{len(changed)} 个标题文字改了（层级未动）：" + "；".join(f"「{x[:14]}」→「{y[:14]}」" for x, y in changed[:3]))
    if a_bold and abs(b_bold - a_bold) > 0.3 * a_bold:
        warns.append(f"加粗数量 {a_bold} → {b_bold}（变化超过 30%）")
    pa = [x[1] for x in a if x[0] == "P"]; pb = [x[1] for x in b if x[0] == "P"]
    if len(pa) == len(pb):
        for j, (x, y) in enumerate(zip(pa, pb)):
            if y > 2 * x or x > 2 * y:
                warns.append(f"第 {j + 1} 个段落串的段数 {x} → {y}（拆并超过一倍，看一眼是不是内容被重组了）")
    verdict = "fail" if problems else ("warn" if warns else "pass")
    result = {"verdict": verdict, "problems": problems, "warnings": warns,
              "source": [render_block(x) for x in a], "rewrite": [render_block(x) for x in b],
              "bold": {"source": a_bold, "rewrite": b_bold}}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"structdiff · verdict = {verdict.upper()} · 源 {len(a)} 块 / 改写 {len(b)} 块 · 加粗 {a_bold} → {b_bold}")
        for p in problems:
            print(f"  FAIL  {p}")
        for w in warns:
            print(f"  WARN  {w}")
        if problems:
            print("\n骨架被动了。--keep-structure 下改写只许动散文段里的句子；要重组结构就去掉这个开关，并在报告里写明。")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
