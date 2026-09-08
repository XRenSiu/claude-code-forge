#!/usr/bin/env python3
"""verify_sizing.py — 体量网格的 lint：让 sizing.yaml 与 aidlc_state.py 互相断言。

缺口：v0.11.1 之前 `sizing.yaml` 的 S 档声明 `exempt: [acceptance-fleet, plan-cards]`，
而 `aidlc_state.py` 只实现了其中一项（`advance pr` 免掉整体验收）。plan-cards 那一半从来
没有生效过——数据承诺了一条轻量路径，引擎没兑现，而**没有任何东西会发现这件事**。
`graph.yaml` 有 `graph check` 让声明与 ORDER 互相断言，`loops.yaml` 有 `verify_loop.py`，
只有体量网格是一份没人核的散文。这个脚本补上那一格。

它检的是「数据说的」与「代码做的」是不是同一件事，不是「网格定得对不对」——
分档定得对不对由下一次逃逸缺陷回答（/retro 按档分桶），不由 lint 回答。

用法：
  verify_sizing.py [sizing.yaml] [--json]

退出码：
  0 = 网格自洽，且与 aidlc_state.py 的 ORDER / prereqs 一致
  1 = 有不一致（每条给出它对应的那类生产失败）
  2 = 用法 / IO 错误（文件读不到、YAML 解析失败、pyyaml 缺席）
      注意这里**没有 exit 3**：网格是本仓库自带的资产，不是用户可能没配的外部分析器。
      读不到它是错误，不是「未求值」。

七条 lint（每条对应一种它防住的失败）：
  L1 网格里的每个阶段名都在 ORDER 里
      —— 防「网格写了一个不存在的阶段名，永远不会命中，看起来配了其实没配」。
  L2 never_skippable ⊆ ORDER，且三道门与不可逆动作都在里面
      —— 防「广度旋钮把门拧掉」。三道门只能人签（不变量 6）是这条的上位法。
  L3 没有任何一档跳过 never_skippable 里的阶段
      —— 防 L2 的表填对了但某一档偷偷绕过它。
  L4 每条 skip 都有非空的 why
      —— 防「没有理由的跳过」。复盘时无法质疑的豁免也就无法被撤销。
  L5 默认档（rules 里 when 为空的那条兜底规则所指向的档）一个阶段也不跳
      —— **极性检查**：漏填得到的必须是较严的路径。一个靠遗漏就能打开的门不是门。
  L6 每条规则的 `needs` 与它的 `when` 一致（when 里引用的每个可数量都要在 needs 里）
      —— 这条让「早定档给不出 S」从注释变成可证的性质：S 的唯一入口需要 files，
         而 intake / issue 阶段没有 diff，所以 needs 里有 files 的规则早期不会命中。
  L7 每一档剩下的阶段构成一条 next_allowed 真的会放行的路径
      —— 这是「数据与代码互相断言」那一条：直接 import aidlc_state 的 next_allowed，
         用一个假 state 把整条路走一遍。网格声明的路径如果引擎走不通，这里就红。

为什么是 import 而不是重实现：一个自己写的第二份 next_allowed 迟早与真的那份分叉，
而分叉出来的那份会说「网格没问题」。同一个函数才叫互相断言（`graph check` 同源）。
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    import yaml
except ImportError:
    sys.stderr.write("verify_sizing.py needs PyYAML: pip install pyyaml\n")
    sys.exit(2)

import aidlc_state as S  # noqa: E402  (ORDER / next_allowed / effective_skips 的唯一来源)

# when: 里可以出现的可数量 → 它对应的 needs 名字
QUANTITY_KEYS = {
    "files_min": "files", "files_max": "files",
    "acs_min": "acs", "acs_max": "acs",
    "human_acs_min": "human_acs", "human_acs_max": "human_acs",
}
# 这些阶段无论 sizing.yaml 怎么写都必须在 never_skippable 里（L2）
MUST_BE_NEVER_SKIPPABLE = ["g2", "g3", "issue", "contract", "implement", "pr", "review", "merge"]


def check(doc):
    problems = []
    order = list(S.ORDER)
    never = set(((doc.get("never_skippable") or {}).get("stages")) or [])
    grid = doc.get("stages") or {}
    tiers = doc.get("tiers") or {}
    rules = doc.get("rules") or []

    # L1 / L4 —— 网格里的阶段名与理由
    for tier, conf in grid.items():
        for row in (conf or {}).get("skip") or []:
            st = row.get("stage")
            if st not in order:
                problems.append(f"L1 {tier}: `{st}` is not a stage in ORDER {order} — a grid entry that can "
                                "never match looks configured but is not")
            if not (row.get("why") or "").strip():
                problems.append(f"L4 {tier}/{st}: skip without a `why` — an exemption nobody can question "
                                "is an exemption nobody can withdraw")

    # L2 —— never_skippable 的形状
    for st in sorted(never):
        if st not in order:
            problems.append(f"L2 never_skippable lists `{st}`, not a stage in ORDER")
    for st in MUST_BE_NEVER_SKIPPABLE:
        if st not in never:
            problems.append(f"L2 `{st}` must be in never_skippable — the three human gates and the "
                            "irreversible actions are not what a breadth knob is allowed to turn off "
                            "(invariant 6: 三道门只能人签)")

    # L3 —— 没有一档绕过它
    for tier, conf in grid.items():
        for row in (conf or {}).get("skip") or []:
            if row.get("stage") in never:
                problems.append(f"L3 {tier} skips `{row['stage']}`, which is never_skippable")

    # L5 —— 极性：兜底档一个阶段也不跳
    fallback = next((r for r in rules if not (r.get("when") or {})), None)
    if not fallback:
        problems.append("L5 no fallback rule (one with an empty `when:`) — a rule set that can fail to match "
                        "leaves the tier undefined, and an undefined tier is decided by whoever reads it last")
    else:
        ft = fallback.get("tier")
        if ((grid.get(ft) or {}).get("skip")):
            problems.append(f"L5 fallback tier `{ft}` skips {[r.get('stage') for r in grid[ft]['skip']]} — "
                            "the tier you get by omission must be the STRICTER path, never the looser one")

    # L6 —— needs 与 when 一致
    for r in rules:
        w, needs = r.get("when") or {}, set(r.get("needs") or [])
        want = {QUANTITY_KEYS[k] for k in w if k in QUANTITY_KEYS}
        unknown = set(w) - set(QUANTITY_KEYS) - {"track"}
        if unknown:
            problems.append(f"L6 {r.get('id')}: unknown `when` key(s) {sorted(unknown)}")
        if want - needs:
            problems.append(f"L6 {r.get('id')}: `when` reads {sorted(want)} but `needs` declares {sorted(needs)} "
                            f"— missing {sorted(want - needs)}. `needs` is what makes 「早定档给不出 S」 provable "
                            "instead of a comment")
        if needs - want:
            problems.append(f"L6 {r.get('id')}: `needs` declares {sorted(needs - want)} that `when` never reads")
        if r.get("tier") and r["tier"] not in tiers:
            problems.append(f"L6 {r.get('id')}: tier `{r['tier']}` has no entry under `tiers:`")

    # L7 —— 每一档的剩余路径 next_allowed 真的放行
    for tier in tiers:
        skips = {row["stage"]: row.get("why", "") for row in ((grid.get(tier) or {}).get("skip") or [])
                 if row.get("stage") in order and row.get("stage") not in never}
        path = [s for s in order if s not in skips]
        st = {"stage": path[0], "gates": {"g3": {"required": True}},
              "intake": {"size": tier, "size_source": "derived"}}
        for nxt in path[1:]:
            if not S.next_allowed(st, nxt, skips):
                problems.append(f"L7 {tier}: next_allowed refuses {st['stage']} → {nxt} even though the grid "
                                f"skips {sorted(skips)} — the data declares a path the engine will not walk")
                break
            st["stage"] = nxt
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sizing", nargs="?", default=os.path.join(HERE, "..", "assets", "sizing.yaml"))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        with open(a.sizing, encoding="utf-8") as fh:
            doc = yaml.safe_load(fh) or {}
    except OSError as e:
        sys.stderr.write(f"verify_sizing: {e}\n")
        sys.exit(2)
    except yaml.YAMLError as e:
        sys.stderr.write(f"verify_sizing: YAML parse error: {e}\n")
        sys.exit(2)
    problems = check(doc)
    if a.json:
        print(json.dumps({"ok": not problems, "sizing": a.sizing, "problems": problems},
                         ensure_ascii=False, indent=2))
    else:
        print(f"verify_sizing: {a.sizing}")
        for p in problems:
            print(f"  ✗ {p}")
        if not problems:
            tiers = list((doc.get("tiers") or {}))
            print(f"  ✓ 7 checks pass · tiers={tiers} · "
                  f"never_skippable={len(((doc.get('never_skippable') or {}).get('stages')) or [])} stages")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
