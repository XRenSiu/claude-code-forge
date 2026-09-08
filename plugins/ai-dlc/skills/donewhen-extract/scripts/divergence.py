#!/usr/bin/env python3
"""divergence.py — 把"这个需求写清楚了没有"从自评变成可核对的信号。

缺口：TASK 轨判断需求模不模糊，靠的是引擎自己说"这里我不确定"。而 Ambig-SWE（ICLR 2026）
测到的第一条结论就是：**模型分不清一个任务是写清楚了还是没写清楚**。DOS 词表闭包是目前唯一
的客观触发，它只抓得到"名词不在本体里"这一种模糊。

`psl-derive` 已经有对的机制——同一份 PSL 隔离推导 N 次，分歧集就是 G1 的议程——但只给了 PSL 轨。
本脚本把它搬到契约层：对同一个 issue **隔离**生成 2–3 份 done_when 草案（不同会话，互相看不见），
落到 N 份文件，然后由脚本比。**分歧处就是必须澄清的槽**：N 个读者读同一句需求读出了不同的判据，
那句需求就是欠定的，与谁更聪明无关。

用法：
  divergence.py <draft1.yaml> <draft2.yaml> [draft3.yaml ...] [--out divergence.yaml]
                [--max-divergence 0.20] [--json]

退出码：0 = 分歧在阈值内（可以进 G2）· 1 = 必须澄清 · 2 = 用法 / IO 错误。

比什么（AC 跨草案的对齐靠内容，不靠 id——各草案的 id 本来就不一样）：
  锚 = (req, ears_type, 归一化 observe)
  - only_in_some   某个锚只出现在部分草案里 → 这条判据是不是必要的，没有共识
  - expect_differs 同一个锚，expect 的形状不同 → "对"的样子没有共识
  - threshold_differs 同一个键的数值不同 → 阈值来源不明（最常见的编数字现场）
  - kind_differs   同一个锚，一份判 mechanical 一份判 human → 谁来裁决没有共识
  - twin_asymmetry 某份给了 unhappy 孪生，别份没给 → 失败语义没有共识
每条分歧都带一句 `question`：要问用户的那句话。分歧集不是报告，是议程。
"""
from __future__ import annotations

import argparse
import json
import re
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("divergence.py needs PyYAML\n"); sys.exit(2)

NUM = re.compile(r"-?\d+(?:\.\d+)?")


def norm_observe(s):
    return re.sub(r"\s+", "", str(s or "")).lower().rstrip("/")


def anchor(ac):
    return (str(ac.get("req") or ""), str(ac.get("ears_type") or ""), norm_observe(ac.get("observe")))


def flatten(d, prefix=""):
    """expect / given 摊平成 {点路径: 值}，好逐键比。"""
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(flatten(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(d, list):
        for i, v in enumerate(d):
            out.update(flatten(v, f"{prefix}[{i}]"))
    else:
        out[prefix] = d
    return out


def numbers(v):
    return NUM.findall(str(v))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("drafts", nargs="+")
    ap.add_argument("--out", default="divergence.yaml")
    ap.add_argument("--max-divergence", type=float, default=0.20,
                    help="分歧锚 / 锚总数 的上限；超过就必须澄清（缺省 0.20）")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if len(a.drafts) < 2:
        sys.stderr.write("divergence.py 需要至少 2 份独立草案——一份草案没有分歧可言，"
                         "那正是现在这条流水线的问题\n")
        return 2
    docs = []
    for p in a.drafts:
        try:
            docs.append(yaml.safe_load(open(p, encoding="utf-8")) or {})
        except Exception as e:
            sys.stderr.write(f"divergence: {p}: {e}\n")
            return 2
    n = len(docs)
    # 锚 → {草案序号: AC}
    index = {}
    for i, d in enumerate(docs):
        for ac in (d.get("acceptance") or []):
            if isinstance(ac, dict):
                index.setdefault(anchor(ac), {})[i] = ac
    divergent, agreed = [], []

    for anc, per in sorted(index.items()):
        req, ears, obs = anc
        where = sorted(per)
        label = f"{req or '(no req)'} · {ears or '(no ears_type)'} · {obs or '(no observe)'}"
        if len(per) < n:
            divergent.append({
                "kind": "only_in_some", "anchor": label, "present_in": [i + 1 for i in where],
                "missing_in": [i + 1 for i in range(n) if i not in per],
                "detail": f"{len(per)}/{n} 份草案写了这条判据",
                "question": f"「{obs or req}」这条要不要进验收？{len(per)} 个读者写了它，{n - len(per)} 个没写——"
                            "需求原文没说清它算不算这次的范围。",
            })
            continue
        acs = [per[i] for i in where]
        kinds = {str(x.get("kind")) for x in acs}
        if len(kinds) > 1:
            divergent.append({
                "kind": "kind_differs", "anchor": label, "values": sorted(kinds),
                "detail": "同一条判据，有的草案判机器可判、有的判需要人裁决",
                "question": f"「{obs or req}」这条谁来裁决？判 mechanical 就得给可读的观察边界，"
                            "判 human 就得指定裁决人并走 G3——两者的成本和路径都不同。",
            })
        exps = [flatten(x.get("expect") or {}) for x in acs]
        keys = set().union(*[set(e) for e in exps]) if exps else set()
        for k in sorted(keys):
            vals = [e.get(k, "(缺)") for e in exps]
            if len({json.dumps(v, ensure_ascii=False, sort_keys=True) for v in vals}) == 1:
                continue
            nums = [numbers(v) for v in vals]
            if any(nums) and all(nums):
                divergent.append({
                    "kind": "threshold_differs", "anchor": label, "key": k,
                    "values": [str(v) for v in vals],
                    "detail": "同一个键，各草案给了不同的数",
                    "question": f"「{obs or req}」的 {k} 到底是多少？各写了 {', '.join(str(v) for v in vals)}——"
                                "阈值必须有来源（用户给的 / SLO / 一次真实故障），三个不同的数说明现在一个来源都没有。",
                })
            else:
                divergent.append({
                    "kind": "expect_differs", "anchor": label, "key": k,
                    "values": [str(v) for v in vals],
                    "detail": "同一条判据，「对」的样子不一致",
                    "question": f"「{obs or req}」成功时应该观察到什么？各草案给的是 {', '.join(str(v) for v in vals)}。",
                })
        if ears in ("event", "state"):
            twins = [bool(x.get("paired_with")) for x in acs]
            if len(set(twins)) > 1:
                divergent.append({
                    "kind": "twin_asymmetry", "anchor": label,
                    "detail": f"{sum(twins)}/{n} 份草案给了 unhappy 孪生",
                    "question": f"「{obs or req}」失败时系统该怎么办（拒绝 / 降级 / 报错）？"
                                "需求原文只写了成功路径，失败语义正是被钻的缝。",
                })
        if not any(d0["anchor"] == label for d0 in divergent):
            agreed.append(label)

    anchors_total = len(index)
    div_anchors = len({d0["anchor"] for d0 in divergent})
    ratio = (div_anchors / anchors_total) if anchors_total else 0.0
    verdict = "must_clarify" if (ratio > a.max_divergence or not anchors_total) else "pass"
    res = {
        "drafts": a.drafts, "n": n,
        "anchors_total": anchors_total, "anchors_divergent": div_anchors,
        "divergence_ratio": round(ratio, 3), "max_divergence": a.max_divergence,
        "verdict": verdict,
        "agreed": agreed,
        "divergent": divergent,
        "note": ("分歧集是 G2 之前的议程，不是报告。每条 question 都要么被用户回答、"
                 "要么进假设台账带风险签字——不许由写契约的人自己拍板。"),
    }
    if not anchors_total:
        res["note"] = "N 份草案里一条 AC 都没有——这不是没有分歧，是契约还没开始写。"
    open(a.out, "w", encoding="utf-8").write(yaml.safe_dump(res, allow_unicode=True, sort_keys=False, width=100))
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(f"divergence · verdict = {verdict.upper()} · {n} 份草案 · 锚 {anchors_total} · "
              f"分歧 {div_anchors}（{ratio:.0%} vs 上限 {a.max_divergence:.0%}）")
        for d0 in divergent[:15]:
            print(f"  [{d0['kind']}] {d0['anchor']}")
            print(f"      问：{d0['question']}")
        print(f"  → {a.out}")
    return 1 if verdict == "must_clarify" else 0


if __name__ == "__main__":
    sys.exit(main())
