#!/usr/bin/env python3
"""factdiff.py — 改写前后"事实不变"的机械闸门。

改写只许动表达，不许动事实。本脚本抽取两份文本里的可核对锚点并比对：
数字（含单位/百分比/版本号）、日期、代码标识（反引号）、URL、路径、大写专名/缩写、
中文专名候选（书名号、引号内短语）、以及**确定性词**（Belem et al. 2026：LLM 改写在最多 75% 的
输出中扭曲了确定性，多数是往上扭）。

用法：
  python3 factdiff.py <source.md> <rewrite.md> [--json] [--allow-drop "<锚点>" ...]

退出码：0 = pass（无事实增删；确定性变化只 warn），1 = fail（有锚点被删除或新增），2 = 用法错误。
比对前做排版归一：数字内部的空格与千分位逗号不算差异（"1.4 s" = "1.4s"，"1,000" = "1000"）；
句末的句号不会吞掉单位（"10GB." 仍是 "10GB"）；x.y.z 或 v 前缀才算版本号，"1.4" 是数字。
--allow-drop 用于显式放行"确实该删"的锚点（例如原文里错误的数字），放行必须由人给出。
"""

from __future__ import annotations

import argparse
import json
import re
import sys

NUMBER = re.compile(r"(?<![A-Za-z_/\-])(?<!\d\.)\d+(?:[.,]\d+)*\s?(?:%|ms|s|min|h|d|GB|MB|KB|TB|QPS|RPS|TPS|rps|qps|x|倍|万|亿|个|次|条|台|人|天|周|月|年|行|毫秒|秒|分钟|小时)?(?![A-Za-z_/\-]|\.\d)")
DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}\s?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s\d{1,2}\b|\d{1,2}月\d{1,2}日|\d{4}年\d{1,2}月")
CODE = re.compile(r"`([^`\n]+)`")
URL = re.compile(r"https?://[^\s)>\]]+")
PATH = re.compile(r"(?<![\w`])(?:[A-Za-z_][\w\-]*/)+[\w\-.]+")
PROPER = re.compile(r"\b(?:[A-Z][a-z]+(?:[A-Z][a-z]+)+|[A-Z]{2,}[A-Za-z0-9]*|[A-Z][a-z]{2,}(?=\s|[,.;:!?)]|$))\b")
ZH_QUOTED = re.compile(r"[《「『“]([^》」』”]{1,20})[》」』”]")
VERSION = re.compile(r"\bv\d+\.\d+(?:\.\d+)?\b|\b\d+\.\d+\.\d+\b")

CERTAINTY_UP = re.compile(r"\b(will|always|never|definitely|certainly|clearly|proven|guarantees?|ensures?)\b|一定|必然|肯定|确保|保证|显然|毫无疑问|从不|总是", re.IGNORECASE)
CERTAINTY_DOWN = re.compile(r"\b(may|might|could|possibly|perhaps|likely|probably|seems?|appears?|arguably|somewhat)\b|可能|或许|也许|大概|似乎|应该|估计|一定程度上", re.IGNORECASE)

# 英文常见句首词与通用词，不算专名
STOP_PROPER = {
    "The", "This", "That", "These", "Those", "We", "Our", "It", "In", "On", "At", "For", "If", "As", "So", "But", "And",
    "When", "Then", "There", "Here", "What", "Why", "How", "Who", "Which", "After", "Before", "Because", "While",
    "Twice", "Once", "Both", "Each", "Every", "Nobody", "Everyone", "Standard", "Ordering", "Rollback", "Rollout",
    "Flag", "Idempotency", "Put", "Checkout", "Migrating", "Proposal", "Introduction", "Current", "Proposed", "Key",
    "Benefits", "Risks", "Conclusion", "Background", "Goals", "Design", "Summary", "Overview", "Solution", "Risk",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Yes", "No", "Not", "First",
    "Second", "Third", "Finally", "However", "Overall", "Ultimately", "Additionally", "Moreover", "Furthermore",
    "I", "A", "An", "Of", "To", "By", "With", "From", "Into", "Over", "Under", "Also", "Just", "Even", "Only",
    # 单位缩写跟着数字走（NUMBER 层已经计入），不算专名
    "GB", "MB", "KB", "TB", "QPS", "RPS", "TPS", "MS",
}


def strip_code_blocks(text: str) -> str:
    return re.sub(r"(```|~~~).*?\1", "", text, flags=re.S)


def norm_number(s: str) -> str:
    """'1.4 s' == '1.4s'，'1,000' == '1000'，'5 万' == '5万'：空格与千分位是排版，不是事实。"""
    s = re.sub(r"\s+", "", s.strip())
    return re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", s)


def anchors(text: str):
    t = strip_code_blocks(text)
    out = {}
    out["number"] = set(norm_number(m.group(0)) for m in NUMBER.finditer(t))
    out["date"] = set(DATE.findall(t))
    out["code"] = set(CODE.findall(t))
    out["url"] = set(URL.findall(t))
    out["path"] = set(p for p in PATH.findall(t) if not p.startswith("http") and "/" in p and len(p) > 3)
    out["version"] = set(VERSION.findall(t))
    props = set()
    lower_words = set(re.findall(r"(?<![A-Za-z])[a-z]{2,}(?![A-Za-z])", t))
    for m in PROPER.finditer(t):
        w = m.group(0)
        if w in STOP_PROPER or len(w) < 2:
            continue
        # 同一篇里还以小写出现过的词（Two / two, Rollout / rollout）是句首大写，不是专名
        if w.lower() in lower_words:
            continue
        props.add(w)
    out["proper"] = props
    out["zh_quoted"] = set(ZH_QUOTED.findall(t))
    # x.y.z 形态的版本号不重复计入数字
    out["number"] = {n for n in out["number"] if n not in out["version"]}
    return out


def certainty(text: str):
    t = strip_code_blocks(text)
    return len(CERTAINTY_UP.findall(t)), len(CERTAINTY_DOWN.findall(t))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("rewrite")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--allow-drop", nargs="*", default=[], help="人工放行的可删除锚点")
    ap.add_argument("--allow-add", nargs="*", default=[], help="人工放行的可新增锚点（如来源已给的补充数据）")
    args = ap.parse_args()
    try:
        src = open(args.source, encoding="utf-8").read()
        new = open(args.rewrite, encoding="utf-8").read()
    except OSError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    a, b = anchors(src), anchors(new)
    allow_drop, allow_add = set(args.allow_drop), set(args.allow_add)
    dropped, added = {}, {}
    # 专名层噪声大，只报 warn；数字/日期/代码/URL/路径/版本 是硬锚点
    hard = ["number", "date", "code", "url", "path", "version"]
    soft = ["proper", "zh_quoted"]
    for k in hard + soft:
        d = sorted(x for x in a[k] - b[k] if x not in allow_drop)
        n = sorted(x for x in b[k] - a[k] if x not in allow_add)
        if d:
            dropped[k] = d
        if n:
            added[k] = n
    up_a, down_a = certainty(src)
    up_b, down_b = certainty(new)

    hard_fail = any(k in dropped for k in hard) or any(k in added for k in hard)
    soft_warn = any(k in dropped for k in soft) or any(k in added for k in soft)
    cert_warn = (up_b - up_a) >= 3 or (down_b - down_a) >= 3 or (up_a and up_b > 2 * up_a) or (down_a and down_b > 2 * down_a)

    verdict = "fail" if hard_fail else ("warn" if (soft_warn or cert_warn) else "pass")
    result = {
        "verdict": verdict,
        "dropped": dropped, "added": added,
        "certainty": {"source": {"up": up_a, "down": down_a}, "rewrite": {"up": up_b, "down": down_b}, "warn": cert_warn},
        "counts": {k: {"source": len(a[k]), "rewrite": len(b[k])} for k in hard + soft},
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"factdiff · verdict = {verdict.upper()}")
        for k in hard + soft:
            tag = "hard" if k in hard else "soft"
            line = f"  [{tag}] {k:<10} source {len(a[k]):>3} → rewrite {len(b[k]):>3}"
            if k in dropped:
                line += f"   DROPPED: {', '.join(dropped[k][:8])}"
            if k in added:
                line += f"   ADDED: {', '.join(added[k][:8])}"
            print(line)
        print(f"  certainty  up {up_a}→{up_b}  down {down_a}→{down_b}" + ("   WARN: 确定性被整体上调/下调，逐句核对" if cert_warn else ""))
        if hard_fail:
            print("\n硬锚点有增删：改写引入或丢失了数字/日期/标识符/URL/路径。逐条核对，确认该删的用 --allow-drop 放行，确认原文本来就有的用 --allow-add 放行；否则回滚该处改写。")
        elif verdict == "warn":
            print("\n软锚点或确定性有变化：通常是专名改写（如'订单服务'→'orders-api'）或对冲词增减，人工看一眼。")
    return 1 if hard_fail else 0


if __name__ == "__main__":
    sys.exit(main())
