#!/usr/bin/env python3
"""score.py — 汇总三个 arm 的隐藏集得分，并在样本不够时**拒绝下结论**。

这个脚本存在的理由，一半是算分，一半是不让人（包括写它的人）拿一次运行去宣称插件有效。
`MIN_TASKS` 与 `NOISE_BAND` 是编译进来的：样本不够或差距落在带内，verdict 就是
`insufficient_sample` / `within_noise`，不是"sdlc 更好"。

用法：
  score.py --workdir DIR [--out baseline.md] [--json]

退出码：0 = 出了报告（无论结论是什么）· 2 = 没有任何 result.json。
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import statistics
import sys
import time

ARMS = ("bare", "claudemd", "sdlc")
MIN_TASKS = 5      # 少于这么多个任务，不许下"哪个 arm 更好"的结论
NOISE_BAND = 0.15  # 平均分差落在带内 = 没有差别


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workdir", required=True); ap.add_argument("--out", default="baseline.md")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    results = []
    for p in sorted(glob.glob(os.path.join(a.workdir, "*", "result.json"))):
        try:
            results.append(json.load(open(p, encoding="utf-8")))
        except Exception:
            pass
    if not results:
        sys.stderr.write(f"{a.workdir} 下没有 result.json —— 先 run.py collect\n"); return 2

    by_arm = {arm: [r for r in results if r["arm"] == arm] for arm in ARMS}
    tasks = sorted({r["task"] for r in results})
    summary = {}
    for arm, rs in by_arm.items():
        if not rs:
            summary[arm] = None; continue
        checks = [r["check_ratio"] for r in rs if r.get("check_ratio") is not None]
        slots = [(r["slots_addressed"] / r["slots_total"]) for r in rs if r.get("slots_total")]
        summary[arm] = {"tasks": len(rs),
                        "check_mean": round(statistics.mean(checks), 3) if checks else None,
                        "slot_mean": round(statistics.mean(slots), 3) if slots else None}

    have = [arm for arm in ARMS if summary.get(arm)]
    n_tasks = len(tasks)
    if n_tasks < MIN_TASKS:
        verdict = "insufficient_sample"
        verdict_note = (f"只跑了 {n_tasks} 个任务，下限是 {MIN_TASKS}。这份数据能证明**跑通了**，"
                        "不能证明任何一个 arm 更好。谁拿它说'sdlc 有效'，谁就重犯了这个插件自己批评的错。")
    elif len(have) < 2:
        verdict = "insufficient_arms"; verdict_note = "少于两个 arm 有数据。"
    else:
        best = max(have, key=lambda x: summary[x]["check_mean"] or 0)
        worst = min(have, key=lambda x: summary[x]["check_mean"] or 0)
        gap = (summary[best]["check_mean"] or 0) - (summary[worst]["check_mean"] or 0)
        if gap <= NOISE_BAND:
            verdict = "within_noise"
            verdict_note = f"最好与最差相差 {gap:.2f}，噪声带是 {NOISE_BAND}。差别没有超出噪声。"
        else:
            verdict = f"{best}_leads"
            verdict_note = f"{best} 比 {worst} 高 {gap:.2f}，超过噪声带 {NOISE_BAND}。"

    lines = [f"# 行为层基线 · {time.strftime('%Y-%m-%d')}", "",
             f"**verdict: `{verdict}`** — {verdict_note}", "",
             f"任务 {n_tasks} 个（{', '.join(tasks)}）· arm {len(have)} 个 · 判定门槛 ≥{MIN_TASKS} 任务、差距 >{NOISE_BAND}", "",
             "| arm | 任务数 | 隐藏集均分 | 欠定槽处理率 |", "|---|---|---|---|"]
    for arm in ARMS:
        s = summary.get(arm)
        lines.append(f"| {arm} | {s['tasks']} | {s['check_mean']} | {s['slot_mean']} |" if s else f"| {arm} | 0 | — | — |")
    lines += ["", "## 逐条", "", "| 任务 | arm | 隐藏集 | 欠定槽 | 失败的检查 |", "|---|---|---|---|---|"]
    for r in sorted(results, key=lambda x: (x["task"], x["arm"])):
        failed = ", ".join(c["id"] for c in r["checks"] if not c["passed"]) or "—"
        lines.append(f"| {r['task']} | {r['arm']} | {r['check_score']}/{r['check_total']} | "
                     f"{r['slots_addressed']}/{r['slots_total']} | {failed} |")
    lines += ["", "## 这份数据不能回答什么", "",
              "- 不能回答「sdlc 值不值得用」：任务是本仓库自己出的，出题人与被测者同源。",
              "- 不能回答「哪个 arm 写的代码更好看」：隐藏集只判行为，不判品味。",
              "- 不能外推到别的仓库：fixture 是纯 Python 小仓库，没有构建系统、没有并发、没有历史包袱。", ""]
    open(a.out, "w", encoding="utf-8").write("\n".join(lines))
    res = {"verdict": verdict, "note": verdict_note, "tasks": n_tasks, "summary": summary, "out": a.out}
    print(json.dumps(res, ensure_ascii=False, indent=2) if a.json else "\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
