#!/usr/bin/env python3
"""verify_coldread.py — cold-read.yaml 的形状检查 + 判决重算 + 轮数封顶。

cold-reader agent 的判决规则写在 agents/cold-reader.md 里，是声明式的：agent 可能算错、可能心软。
本脚本把那五条规则编译掉：读 cold-read.yaml，按同一套规则重算 verdict，与 agent 写的比对。
不一致 = 这一轮冷读无效，重开一个干净上下文再读一次；不是"以脚本为准继续"。

用法：
  python3 verify_coldread.py <cold-read.yaml> [--round N] [--json]

退出码：0 = 形状合法且判决一致；1 = 形状缺件 / 判决不一致 / round > 2；2 = IO 或用法错误。
--round N：本轮是第几轮冷读。N > 2 直接 exit 1（SKILL.md「绝不第 3 轮」在这里变成机械的）。

判决规则（与 agents/cold-reader.md 逐条对应，改一边必须改另一边）：
  needs_revision 当且仅当任一成立：
    R1 one_sentence 为空（读者答不出"这份文档要我做什么/相信什么"）；
    R2 lost_at 非空的段落 ≥ 2，或任一段 got == "no_claim"；
    R3 new_first 为真的段落占比 > 1/3；
    R4 flags 含 decision_buried 且 genre ∈ {proposal, design, adr, memo, report}；
    R5 told_not_shown 命中总数 ≥ 5 且 genre ∈ {proposal, design, adr, postmortem, report}。
"""

from __future__ import annotations

import argparse
import json
import sys

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None

REQUIRED_TOP = ["doc", "reader", "genre", "verdict", "paragraphs"]
REQUIRED_PARA = ["n", "expected", "got", "lost_at", "told_not_shown", "new_first", "list_replaces_argument", "hedged_claim"]
DECISION_GENRES = {"proposal", "design", "adr", "memo", "report"}
SHOWN_GENRES = {"proposal", "design", "adr", "postmortem", "report"}


def load(path: str):
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json") or yaml is None:
        return json.loads(text)
    return yaml.safe_load(text)


def recompute(d: dict):
    """返回 (verdict, fired_rules, stats)。"""
    paras = d.get("paragraphs") or []
    one = d.get("one_sentence")
    lost = sum(1 for p in paras if p.get("lost_at") not in (None, "", "null"))
    no_claim = sum(1 for p in paras if str(p.get("got", "")).strip() == "no_claim")
    new_first = sum(1 for p in paras if p.get("new_first") is True)
    tns = sum(len(p.get("told_not_shown") or []) for p in paras)
    genre = str(d.get("genre", "other"))
    flags = set(d.get("flags") or [])
    fired = []
    if one in (None, "", "null"):
        fired.append("R1_no_one_sentence")
    if lost >= 2 or no_claim >= 1:
        fired.append("R2_lost_or_no_claim")
    if paras and new_first / len(paras) > 1 / 3:
        fired.append("R3_new_first_ratio")
    if "decision_buried" in flags and genre in DECISION_GENRES:
        fired.append("R4_decision_buried")
    if tns >= 5 and genre in SHOWN_GENRES:
        fired.append("R5_told_not_shown")
    verdict = "needs_revision" if fired else "pass"
    stats = {"paragraphs": len(paras), "lost_at": lost, "no_claim": no_claim, "new_first": new_first,
             "told_not_shown": tns, "genre": genre}
    return verdict, fired, stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path")
    ap.add_argument("--round", type=int, default=1, help="本轮是第几轮冷读；> 2 直接拒")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if yaml is None and not args.path.endswith(".json"):
        print("ERROR: 没有 pyyaml；请 pip install pyyaml，或让 cold-reader 输出 .json", file=sys.stderr)
        return 2
    try:
        d = load(args.path)
    except (OSError, ValueError) as e:  # yaml.YAMLError 是 ValueError 的子类之外，单独接
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except Exception as e:  # yaml.YAMLError
        print(f"ERROR: 解析失败 {e}", file=sys.stderr)
        return 2
    if not isinstance(d, dict):
        print("ERROR: 顶层不是映射", file=sys.stderr)
        return 2

    problems = []
    if args.round > 2:
        problems.append(f"round={args.round}：cold-reader 封顶 2 轮，第 3 轮禁止——照常交付并附「两轮未过」清单")
    for k in REQUIRED_TOP:
        if k not in d:
            problems.append(f"缺顶层字段 {k}")
    paras = d.get("paragraphs") or []
    if not isinstance(paras, list) or not paras:
        problems.append("paragraphs 为空——没有逐段轨迹的冷读不算冷读")
    for i, p in enumerate(paras if isinstance(paras, list) else []):
        if not isinstance(p, dict):
            problems.append(f"paragraphs[{i}] 不是映射")
            continue
        for k in REQUIRED_PARA:
            if k not in p:
                problems.append(f"paragraphs[{i}] 缺字段 {k}")
        for k in ("new_first", "list_replaces_argument", "hedged_claim"):
            if k in p and not isinstance(p[k], bool):
                problems.append(f"paragraphs[{i}].{k} 必须是布尔")
    if d.get("contamination"):
        problems.append(f"contamination 非空：{d['contamination']}——调用方误传了作者意图材料，本轮读者不干净")

    verdict_claimed = d.get("verdict")
    verdict_calc, fired, stats = recompute(d) if isinstance(paras, list) else ("needs_revision", ["invalid"], {})
    if verdict_claimed not in ("pass", "needs_revision"):
        problems.append(f"verdict 必须是 pass | needs_revision，得到 {verdict_claimed!r}")
    elif verdict_claimed != verdict_calc:
        problems.append(f"判决不一致：agent 写 {verdict_claimed}，按规则重算是 {verdict_calc}（触发 {fired or '无'}）——本轮作废，重开干净上下文再读")
    if verdict_calc == "needs_revision" and not d.get("worst_three"):
        problems.append("needs_revision 但 worst_three 为空——没有修改优先级的打回是无效打回")

    result = {"path": args.path, "round": args.round, "verdict_claimed": verdict_claimed, "verdict_recomputed": verdict_calc,
              "fired_rules": fired, "stats": stats, "problems": problems, "ok": not problems}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"verify_coldread · round {args.round} · agent={verdict_claimed} recomputed={verdict_calc} · {'OK' if not problems else 'REJECT'}")
        print(f"  段落 {stats.get('paragraphs', 0)} · lost_at {stats.get('lost_at', 0)} · no_claim {stats.get('no_claim', 0)} · "
              f"new_first {stats.get('new_first', 0)} · told_not_shown {stats.get('told_not_shown', 0)} · 触发 {', '.join(fired) or '无'}")
        for pr in problems:
            print(f"  REJECT  {pr}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
