#!/usr/bin/env python3
"""verify_agent_map.py — 仓库地图的机械预门；`--probe` 真跑一遍里面的命令。

缺口：卡给实现者卡 + AC 子集 + 红基线 + 约束，**没给**测试怎么跑、构建怎么起、目录谁管、
哪里不能碰。AI-DLC 有意不做 rules/ 与 hooks（怕注入每个会话），结果这部分知识回到了每个人
自己的 CLAUDE.md——正是"不同人给的上下文不一样"这个差异的来源。

但 2607.27250 那份 288 次运行的对照实验说得很清楚：把仓库知识堆进上下文**不提高正确率**。
所以这份地图不是"把 README 塞给 agent"，它只装四样一个无上下文的实现者必须问、而卡里没有的东西，
且每一样都要能被核对：

  - 命令必须真能跑（`--probe` 执行并记退出码）——跑不通的命令比没有命令更糟
  - 陷阱必须有来路（ledger / issue / commit）——没有来路的条目是想出来的，不是仓库里的
  - 占位符不算填写

用法：
  verify_agent_map.py <agent-map.md> [--repo .] [--probe] [--timeout 120] [--json]

退出码：0 = 过（可带 flag）· 1 = 拒 · 2 = IO / 用法错误。
`--probe` 不加时，命令这一节只检形状不检可执行性，输出里写明 probed=false ——
一份没被 probe 过的地图，它的命令是声明不是事实。
"""
from __future__ import annotations

import argparse
import json
import re
import os
import subprocess
import sys
import time

SECTIONS = ["跑起来", "目录职责", "禁区", "已知陷阱"]
PLACEHOLDER = re.compile(r"<[^>\n]{0,40}>|TODO|待补|FIXME", re.I)


def unfilled(text):
    """占位符检测：反引号里的 `plugins/<name>/…` 是路径模式，不是没填完。"""
    return bool(PLACEHOLDER.search(re.sub(r"`[^`]*`", "", text)))
PROV = re.compile(r"(ledger:|issue:#?\d+|commit:[0-9a-f]{7,}|pr:#?\d+|file:)", re.I)
CODE = re.compile(r"`([^`]+)`")


def rows(md, section):
    """取某一节下的表格行（去表头与分隔行）。"""
    m = re.search(rf"^##\s*{re.escape(section)}\s*$(.*?)(?=^##\s|\Z)", md, re.M | re.S)
    if not m:
        return None
    out = []
    for line in m.group(1).splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c or "") for c in cells):
            continue
        if cells and cells[0] in ("用途", "路径", "症状"):
            continue
        out.append(cells)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path"); ap.add_argument("--repo", default=".")
    ap.add_argument("--probe", action="store_true", help="逐条执行「跑起来」里的命令并记退出码")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        md = open(a.path, encoding="utf-8").read()
    except OSError as e:
        sys.stderr.write(f"verify_agent_map: {e}\n"); return 2

    rejects, flags, probes = [], [], []
    for sec in SECTIONS:
        if rows(md, sec) is None:
            rejects.append(f"缺 `## {sec}` 一节")
    if rejects:
        print("\n".join("REJECT  " + r for r in rejects)); return 1

    # ---- 跑起来 ----
    cmd_rows = rows(md, "跑起来") or []
    if not cmd_rows:
        rejects.append("「跑起来」一节没有任何行——实现者第一件事就是跑测试")
    named = set()
    for r in cmd_rows:
        purpose = r[0] if r else ""
        cell = r[1] if len(r) > 1 else ""
        named.add(purpose)
        if cell.strip() in ("无", "none", "N/A"):
            continue
        m = CODE.search(cell)
        if not m:
            rejects.append(f"「{purpose}」的命令没有用反引号写成可复制的命令（写 `无` 也行，留空不行）")
            continue
        cmd = m.group(1).strip()
        if cmd in ("无", "none", "N/A", "-", "—"):
            continue
        if unfilled(cmd):
            rejects.append(f"「{purpose}」的命令还是占位符：{cmd}")
            continue
        if a.probe and os.environ.get("AGENT_MAP_NO_RECURSE") and re.search(
                re.escape(os.environ["AGENT_MAP_NO_RECURSE"]), cmd):
            # 真实仓库的地图里「全套测试」往往就是本套件自己。挂在 smoke 里 probe 它会自我调用，
            # 一次跑成无限套娃（2026-09-06 实测卡死）。跳过它并**记录**——跳过的命令不算证过。
            probes.append({"purpose": purpose, "cmd": cmd, "exit": "skipped(recursive)",
                           "want": None, "seconds": 0.0, "ok": True})
            flags.append(f"「{purpose}」的命令会重入本套件，本次未 probe：`{cmd}`"
                         "——它的可执行性要在套件之外单独证（README 的 agent-map 一节）")
            continue
        if a.probe:
            t0 = time.time()
            try:
                p = subprocess.run(cmd, shell=True, cwd=a.repo, capture_output=True,
                                   text=True, timeout=a.timeout)
                code, tail = p.returncode, (p.stderr or p.stdout or "").strip().splitlines()[-1:]
            except subprocess.TimeoutExpired:
                code, tail = "timeout", [f"> {a.timeout}s"]
            except OSError as e:
                code, tail = "error", [str(e)]
            dt = round(time.time() - t0, 1)
            expect = (r[2] if len(r) > 2 else "").strip()
            m2 = re.search(r"exit\s*(\d+)", expect)
            want = int(m2.group(1)) if m2 else 0      # 期望列没写清楚 = 期望 0，不是"期望失败"
            ok = (code == want)
            probes.append({"purpose": purpose, "cmd": cmd, "exit": code, "want": want,
                           "seconds": dt, "ok": ok})
            if not ok:
                rejects.append(f"「{purpose}」跑不通：`{cmd}` → exit {code}，期望 {want}（{'; '.join(tail)[:120]}）"
                               "——跑不通的命令比没有命令更糟，实现者会照着它试三次再去猜")
    for must in ("全套测试",):
        if not any(must in n for n in named):
            rejects.append(f"「跑起来」缺一行 {must}——红-绿是实现者的唯一自证手段")

    # ---- 目录职责 / 禁区 ----
    for sec in ("目录职责", "禁区"):
        rs = rows(md, sec) or []
        if not rs:
            rejects.append(f"「{sec}」一节为空")
        for r in rs:
            joined = " | ".join(r)
            if unfilled(joined):
                rejects.append(f"「{sec}」还有占位符：{joined[:70]}")

    # ---- 已知陷阱：必须有来路 ----
    traps = rows(md, "已知陷阱") or []
    for r in traps:
        joined = " | ".join(r)
        if unfilled(joined):
            rejects.append(f"「已知陷阱」还有占位符：{joined[:70]}")
            continue
        if not PROV.search(joined):
            rejects.append(f"「已知陷阱」这条没有来路（ledger: / issue:#N / commit:sha / file:）：{r[0][:50]}"
                           "——没有来路的陷阱是想出来的，不是这个仓库里的")
    if not traps:
        flags.append("「已知陷阱」为空——可以（新仓库还没踩过坑），但 /retro 每次应该往这里加一条")

    res = {"path": a.path, "probed": bool(a.probe), "probes": probes,
           "sections": SECTIONS, "rejects": rejects, "flags": flags,
           "verdict": "reject" if rejects else "pass"}
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(f"verify_agent_map · verdict = {res['verdict'].upper()} · probed={res['probed']} · "
              f"命令 {len(probes)} 条实跑")
        for p_ in probes:
            print(f"  {'ok  ' if p_['ok'] else 'FAIL'}  {p_['purpose']}: `{p_['cmd']}` → exit {p_['exit']} "
                  f"(期望 {p_['want']}, {p_['seconds']}s)")
        for r in rejects:
            print(f"  REJECT  {r}")
        for f in flags:
            print(f"  flag    {f}")
        if not a.probe and not rejects:
            print("  注意：没有 --probe，这份地图里的命令是**声明**不是事实。交给实现者之前 probe 一次。")
    return 1 if rejects else 0


if __name__ == "__main__":
    sys.exit(main())
