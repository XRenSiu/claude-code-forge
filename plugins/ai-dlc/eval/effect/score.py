#!/usr/bin/env python3
"""score.py — 汇总三个 arm 的隐藏集得分，并在样本不够时**拒绝下结论**。

这个脚本存在的理由，一半是算分，一半是不让人（包括写它的人）拿一次运行去宣称插件有效。
`MIN_TASKS` 与 `NOISE_BAND` 是编译进来的：样本不够或差距落在带内，verdict 就是
`insufficient_sample` / `within_noise`，不是"AI-DLC 更好"。

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

ARMS = ("bare", "claudemd", "aidlc")
MIN_TASKS = 5      # 少于这么多个任务，不许下"哪个 arm 更好"的结论
NOISE_BAND = 0.15  # 平均分差落在带内 = 没有差别


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workdir", required=True, action="append",
                    help="可给多次：一次跑不完的题分在几个工作区里，基线要合起来算")
    ap.add_argument("--out", default="baseline.md")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    results = []
    # 评分产物在 .score-<task>-<arm>/ 里（点开头，glob 的 * 不匹配它）；旧布局的 */result.json 也认
    # 只读评分副本。arm 目录里若有 result.json，那是旧布局留下的污染物，不是数据源。
    paths = sorted(p for w in a.workdir for p in glob.glob(os.path.join(w, ".score-*", "result.json")))
    for p in paths:
        try:
            results.append(json.load(open(p, encoding="utf-8")))
        except Exception:
            pass
    if not results:
        sys.stderr.write(f"{a.workdir} 下没有 result.json —— 先 run.py collect\n"); return 2
    # 同一个 (task, arm) 出现多次时，先看**题目修订号**再看收分时间。
    # 题改过之后旧修订版的分不能和新的比（E-08：T06/T10 的 revision 1 隐藏集在测接口命名）。
    latest, superseded = {}, []
    for r in results:
        k = (r["task"], r["arm"])
        cur = latest.get(k)
        newer = cur is None or (r.get("task_revision", 1), r.get("collected_at", "")) > (
            cur.get("task_revision", 1), cur.get("collected_at", ""))
        if newer:
            if cur is not None:
                superseded.append(cur)
            latest[k] = r
        else:
            superseded.append(r)
    results = list(latest.values())
    # 被污染的结果不计入，但**留在报告里**：账本只增不删，作废的那次也要看得见。
    contaminated = [r for r in results if r.get("contaminated")]
    results = [r for r in results if not r.get("contaminated")]
    if not results:
        sys.stderr.write("所有结果都被标为污染 —— 重跑，别拿它们算分\n"); return 2

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

    def judge(metric, label):
        """两个维度各判各的。只报隐藏集会把唯一分开的信号藏起来——
        2026-09-06 第二轮：隐藏集 0.94/0.94/1.00 落在带内，欠定槽 0.5/0.6/1.0 远超。
        把两者合成一个数，等于用一个不动的维度稀释掉一个动了的维度。"""
        if n_tasks < MIN_TASKS:
            return "insufficient_sample", (
                f"只跑了 {n_tasks} 个任务，下限是 {MIN_TASKS}。这份数据能证明**跑通了**，"
                "不能证明任何一个 arm 更好。")
        if len(have) < 2:
            return "insufficient_arms", "少于两个 arm 有数据。"
        vals = {x: (summary[x][metric] or 0) for x in have}
        best, worst = max(vals, key=vals.get), min(vals, key=vals.get)
        gap = vals[best] - vals[worst]
        if gap <= NOISE_BAND:
            return "within_noise", f"{label}：最好与最差相差 {gap:.2f}，噪声带 {NOISE_BAND}，没有超出噪声。"
        return f"{best}_leads", f"{label}：{best} 比 {worst} 高 {gap:.2f}，超过噪声带 {NOISE_BAND}。"

    v_check, n_check = judge("check_mean", "隐藏集（做对了没有）")
    v_slot, n_slot = judge("slot_mean", "欠定槽（没写清楚的地方写下来了没有）")
    verdict = f"checks={v_check} · slots={v_slot}"
    verdict_note = n_check + " " + n_slot

    lines = [f"# 行为层基线 · {time.strftime('%Y-%m-%d')}", "",
             f"**verdict: `{verdict}`**", "",
             f"- 隐藏集：{n_check}", f"- 欠定槽：{n_slot}", "",
             f"任务 {n_tasks} 个（{', '.join(tasks)}）· arm {len(have)} 个 · 判定门槛 ≥{MIN_TASKS} 任务、差距 >{NOISE_BAND}", "",
             f"轨道：TASK {sum(1 for t in tasks if t <= 'T05')} 道 · PSL {sum(1 for t in tasks if t > 'T05')} 道", "",
             "| arm | 任务数 | 隐藏集均分 | 欠定槽处理率 |", "|---|---|---|---|"]
    for arm in ARMS:
        s = summary.get(arm)
        lines.append(f"| {arm} | {s['tasks']} | {s['check_mean']} | {s['slot_mean']} |" if s else f"| {arm} | 0 | — | — |")
    lines += ["", "## 逐条", "", "| 任务 | arm | 隐藏集 | 欠定槽 | 失败的检查 |", "|---|---|---|---|---|"]
    for r in sorted(results, key=lambda x: (x["task"], x["arm"])):
        failed = ", ".join(c["id"] for c in r["checks"] if not c["passed"]) or "—"
        lines.append(f"| {r['task']} | {r['arm']} | {r['check_score']}/{r['check_total']} | "
                     f"{r['slots_addressed']}/{r['slots_total']} | {failed} |")
    if superseded:
        lines_sup = sorted({f"{r['task']}/{r['arm']} rev{r.get('task_revision', 1)}" for r in superseded})
    if contaminated:
        lines += ["", "## 作废（不计入上表）", "",
                  "| 任务 | arm | 为什么作废 |", "|---|---|---|"]
        lines += [f"| {r['task']} | {r['arm']} | 收分产物出现在 arm 的工作区里，隐藏集可能被它跑过 |"
                  for r in contaminated]
    if superseded:
        lines += ["", "## 被更高修订版取代（留档，不计入上表）", "",
                  "题目改过之后，旧修订版跑出来的分不能和新的比。", "",
                  "- " + " · ".join(lines_sup)]
    lines += ["", "## 这份数据不能回答什么", "",
              "- 不能回答「AI-DLC 值不值得用」：任务是本仓库自己出的，出题人与被测者同源。",
              "- 不能回答「哪个 arm 写的代码更好看」：隐藏集只判行为，不判品味。",
              "- 不能外推到别的仓库：fixture 是纯 Python 小仓库，没有构建系统、没有并发、没有历史包袱。", ""]
    open(a.out, "w", encoding="utf-8").write("\n".join(lines))
    res = {"verdict": verdict, "verdict_checks": v_check, "verdict_slots": v_slot,
           "note": verdict_note, "tasks": n_tasks, "summary": summary, "out": a.out}
    print(json.dumps(res, ensure_ascii=False, indent=2) if a.json else "\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
