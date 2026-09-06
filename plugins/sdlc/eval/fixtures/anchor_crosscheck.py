#!/usr/bin/env python3
"""独立于 check_anchors.py 再数一遍 audit.yaml 里的行引用，与它自报的「走到 N」对账。

为什么单独一个文件：这条核对的全部价值在于**不共用实现**。写进 check_anchors.py 里，
它就和被核对的对象共享同一套正则与同一套排除规则，一起错就一起看不见——
锚点识别面已经连栽四次，每一次都是"我认得的那部分全绿"。

隔离预审在 PR #3 的四轮里每一轮都手工跑这个交叉核对，并且正是它反复抓住这一族；
手工的东西下一轮就会忘，所以固化成 smoke 期望（预审 round-4 的建议）。

用法: anchor_crosscheck.py <audit.yaml> <check_anchors.py>
退出 0 = 两边数一致；1 = 不一致（报差额）；2 = 用法/读取错误。
"""
import re
import subprocess
import sys

# 与 check_anchors.py 里的 SCAN **无关**的一套写法：这里只问"像不像一处行引用"。
HASH = re.compile(r"#L\d+")
COLON = re.compile(r"[A-Za-z0-9_./<>*-]+\.(?:py|sh|yaml|json|md):\d+(?![\d/])")
DOS_VALUE = re.compile(r"\bdos_anchors:\s*\[([^\]]*)\]")


def main():
    if len(sys.argv) != 3:
        sys.stderr.write(__doc__)
        return 2
    audit, tool = sys.argv[1], sys.argv[2]
    try:
        lines = open(audit, encoding="utf-8").read().splitlines()
    except OSError as exc:
        sys.stderr.write(f"crosscheck: cannot read {audit}: {exc}\n")
        return 2

    expected = 0
    for line in lines:
        spans = [m.span(1) for m in DOS_VALUE.finditer(line)]
        def outside(m):
            return not any(a <= m.start() < b for a, b in spans)
        expected += sum(1 for m in HASH.finditer(line) if outside(m))
        expected += sum(1 for m in COLON.finditer(line) if outside(m))

    r = subprocess.run(["python3", tool, "--audit", audit, "verify"],
                       capture_output=True, text=True)
    m = re.search(r"走到 (\d+) 个行号锚点", r.stdout)
    if not m:
        sys.stderr.write("crosscheck: check_anchors.py 没有报出「走到 N」这一行\n"
                         f"--- stdout ---\n{r.stdout[-800:]}\n")
        return 2
    walked = int(m.group(1))
    if walked == expected:
        print(f"crosscheck: 两边各数各的，都是 {walked} 处行引用")
        return 0
    sys.stderr.write(
        f"crosscheck: 独立计数 {expected} ≠ 工具自报 {walked}（差 {expected - walked}）。\n"
        "差额的方向说明问题在哪：独立计数更大 = 有一种写法工具不认得；\n"
        "工具更大 = 它把不是引用的东西当成了引用。\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
