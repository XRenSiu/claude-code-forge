#!/usr/bin/env python3
"""pick_evaluators.py — 把「强烈建议跨供应商」变成一次可检查的分配 + 一条留痕。

缺口：spec-gaming-detector 与 code-reviewer 的正文都写着「强烈建议跨供应商评估」，
但没有声明哪些供应商可用、没有脚本决定这一轮谁审、也没有一处记录这轮是不是跨供应商审的。
只写在正文里的建议，在真实运行里等于不存在。

本脚本读 assets/evaluators.yaml，探测每个供应商是否真的可用（命令存在即可用，不猜），
按同源盲区排名把非本家供应商分给最需要的槽，产出 evaluator-assignment.yaml。
分不到就**留痕**（same_vendor_caveat），不是静默降级——`/meta-judge` 读这个字段给同源发现降权。

用法：
  pick_evaluators.py [--implementer-vendor claude] [--out evaluator-assignment.yaml]
                     [--evaluators <yaml>] [--json]

退出码：0 = 出了分配（无论是否跨供应商）· 2 = 配置读不了。
**不因为"只有本家可用"而失败**：那是环境的事实，不是这次运行的错误；它只是必须被记下来。
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("pick_evaluators.py needs PyYAML\n"); sys.exit(2)

HERE = os.path.dirname(os.path.abspath(__file__))


def available(probe):
    try:
        return subprocess.run(probe, shell=True, capture_output=True, timeout=10).returncode == 0
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--implementer-vendor", default="claude")
    ap.add_argument("--evaluators", default=os.path.join(HERE, "..", "assets", "evaluators.yaml"))
    ap.add_argument("--out", default="evaluator-assignment.yaml")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        cfg = yaml.safe_load(open(a.evaluators, encoding="utf-8")) or {}
    except OSError as e:
        sys.stderr.write(f"pick_evaluators: {e}\n"); return 2

    vendors = cfg.get("vendors") or []
    probed = [{"id": v["id"], "available": available(v.get("probe", "false")), "note": v.get("note", "")}
              for v in vendors]
    others = [v["id"] for v in probed if v["available"] and v["id"] != a.implementer_vendor]
    cap = int(cfg.get("max_slots_per_vendor", 3))
    slots = sorted(cfg.get("slots") or [], key=lambda s: s.get("blind_spot_rank", 99))

    used, assignment, caveats = {}, [], []
    for s in slots:
        pick, cross = a.implementer_vendor, False
        for v in others:
            if used.get(v, 0) < cap:
                pick, cross = v, True
                used[v] = used.get(v, 0) + 1
                break
        row = {"skill": s["skill"], "vendor": pick, "cross_vendor": cross,
               "blind_spot_rank": s.get("blind_spot_rank"), "why": s.get("why", "")}
        if not cross:
            row["same_vendor_caveat"] = (
                f"与实现者同为 {a.implementer_vendor}：同源盲区未被覆盖"
                + ("（该供应商的槽位已用满）" if others else "（环境里没有别的供应商可用）"))
            caveats.append(row["same_vendor_caveat"])
        assignment.append(row)

    res = {"implementer_vendor": a.implementer_vendor, "vendors_probed": probed,
           "cross_vendor_slots": sum(1 for r in assignment if r["cross_vendor"]),
           "total_slots": len(assignment), "assignment": assignment,
           "same_vendor_caveats": len(caveats),
           "note": ("同源的槽不是失败，是必须被记下来的事实。/meta-judge 对 same_vendor_caveat "
                    "的发现降权；一次全同源的验收不该被读成和跨供应商验收一样强。")}
    open(a.out, "w", encoding="utf-8").write(yaml.safe_dump(res, allow_unicode=True, sort_keys=False, width=100))
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(f"pick_evaluators · 跨供应商 {res['cross_vendor_slots']}/{res['total_slots']} 个槽 · "
              f"实现者 = {a.implementer_vendor}")
        for r in assignment:
            mark = "跨" if r["cross_vendor"] else "同"
            print(f"  [{mark}] rank{r['blind_spot_rank']} {r['skill']:24} → {r['vendor']}")
        for v in probed:
            print(f"      {v['id']:8} {'可用' if v['available'] else '不可用'}  {v['note']}")
        print(f"  → {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
