#!/usr/bin/env bash
# 交叉核对的孪生：让工具**悄悄丢掉一族**（程序仍然合法，只是不再走冒号式），
# 独立计数就该和它对不上，退 1。
#
# 两个坑都踩过，都写在这里：
#  - 变异必须先证明落地，否则"探针没发射"和"发射了没发现"长得一样；
#  - 变异体必须还能跑。把正则分支整段删掉会让组引用失效、程序崩溃，
#    那时交叉核对退 2（读不到输出），看起来像"抓到了"，其实什么都没测。
set -u
RA="$1"; CROSS="$2"
T="$(cd "$(mktemp -d)" && pwd -P)"
cp -R "$RA"/. "$T"/ 2>/dev/null || exit 9
python3 - "$T/check_anchors.py" <<'PY' || exit 9
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
needle = ('                elif m.group("ca") is not None:\n'
          '                    style, a, dash, b = "colon", int(m.group("ca")), '
          'm.group("cd"), m.group("cb")\n')
if s.count(needle) != 1:
    sys.stderr.write("twin: colon arm not found — mutation did NOT land\n")
    sys.exit(9)
drop = ('                elif m.group("ca") is not None:\n'
        '                    return m.group(0)\n')
open(p, "w", encoding="utf-8").write(s.replace(needle, drop))
PY
python3 "$T/check_anchors.py" --audit "$T/audit.yaml" --lock "$T/anchors.lock" verify >/dev/null 2>&1
rc=$?
if [ "$rc" -gt 1 ]; then echo "twin: 变异体自身跑不起来 (exit $rc)" >&2; exit 9; fi
python3 "$CROSS" "$T/audit.yaml" "$T/check_anchors.py" >/dev/null 2>&1
