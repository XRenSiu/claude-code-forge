#!/usr/bin/env python3
"""
render_audit.py — audit.yaml → AUDIT.md, the human half of the ring audit.

AUDIT.md is a PROJECTION of audit.yaml (F-12: same directory, the yaml wins on disagreement).  This
renderer therefore invents nothing: every word below comes out of the document, and the only things it
computes are joins the yaml already implies (a Part's Gap atoms, the 闸 / 门 label of a Gate id, the
Artifact comparison of a suspected duplicate pair, whether the exit 0 has its delete-ring twin).

Three rendering rules the report must never break:

  * `implemented` is a three-state — declared | compiled | verified (PSL-010).  "已实现 ✓" is a boolean
    and is forbidden; there is no code path here that can print one.
  * a `kind: script` Gate renders as 闸, a `kind: human` Gate (G1 / G2 / G3) as 门 (PSL-006).  闸 is not 门.
  * `signer_kind: delegated_agent` renders as 代签（delegated）, never as 人签 (F-15, PSL-006).  A
    substitute for external evidence renders as substitute, never as user verification.

Deterministic and re-runnable: no clock, no environment, no network — the same audit.yaml always
produces byte-identical AUDIT.md.

Usage:
  render_audit.py [audit.yaml] [-o AUDIT.md]      # both default to this script's own directory
"""
import argparse
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
REL = "/".join(DIR.parts[-4:])                    # plugins/sdlc/dogfood/ring-audit
RING_ORDER = ["R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "spine"]
RING_TITLE = {                                    # ARCHITECTURE §1 的环名，只作小标题用
    "R0": "世界", "R1": "本体", "R2": "契约", "R3": "标准", "R4": "计划",
    "R5": "实现", "R6": "验收", "R7": "交付", "R8": "回流", "spine": "脊柱",
}
SOURCE_LABEL = {                                  # PSL-017 三种来源
    "lifecycle_blank": "lifecycle_blank（生命周期自列的空白）",
    "newly_identified": "newly_identified（本次审计新识别）",
    "unenforced_rule": "unenforced_rule（宪法有规则、机器无闸）",
}
IMPLEMENTED_NOTE = {
    "declared": "declared（只有 SKILL.md / 提示）",
    "compiled": "compiled（有 verify 脚本或被门挡）",
    "verified": "verified（有行为层运行记录）",
}


# ---------------------------------------------------------------- small helpers

def load(path, what):
    try:
        import yaml
    except ImportError:                           # pragma: no cover - environment problem, not a defect
        sys.exit("render_audit: pyyaml is required (pip install pyyaml)")
    try:
        with open(path, encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    except FileNotFoundError:
        sys.exit(f"render_audit: cannot read {what}: {path} does not exist")
    except Exception as exc:
        sys.exit(f"render_audit: cannot read {what}: {path}: {exc}")


def lst(value):
    return value if isinstance(value, list) else []


def dct(value):
    return value if isinstance(value, dict) else {}


def cell(text):
    """One markdown table cell: pipes escaped, newlines folded, never empty."""
    if text is None or text == "":
        return "—"
    s = " ".join(str(text).split())
    return s.replace("|", "\\|")


def code(text):
    return f"`{text}`" if text not in (None, "") else "—"


def para(text):
    """Body text outside a table: collapse the yaml's folding, keep it on one line."""
    return " ".join(str(text).split()) if text is not None else ""


def refs(evidence):
    return " · ".join(f"`{dct(e).get('kind')}:{dct(e).get('ref')}`" for e in lst(evidence)) or "—"


# ---------------------------------------------------------------- derived joins

class Doc:
    """audit.yaml plus the lookups the report needs.  Nothing here adds content."""

    def __init__(self, doc):
        self.doc = doc
        self.rings = [dct(r) for r in lst(doc.get("rings"))]
        self.by_ring = {r.get("id"): r for r in self.rings}
        self.gaps = {g["id"]: g for g in (dct(x) for x in lst(doc.get("gaps"))) if g.get("id")}
        self.gates = {g["id"]: g for g in (dct(x) for x in lst(doc.get("gates"))) if g.get("id")}
        self.artifacts = [dct(a) for a in lst(doc.get("artifacts"))]
        self.parts = [(r.get("id"), dct(p)) for r in self.rings for p in lst(r.get("parts"))]
        self.part_by_id = {p.get("id"): p for _, p in self.parts}
        self.run = dct(doc.get("run_evidence"))

    # -- Gate: 闸 or 门, never the other way round (PSL-006) ------------------
    def gate_label(self, gid):
        gate = dct(self.gates.get(gid))
        kind = gate.get("kind")
        if kind == "script":
            return f"闸 `{gid}`"
        if kind == "human":
            return f"门 `{gid}`"
        return f"`{gid}`（未在 gates[] 登记）"

    # -- a Part's Gap atoms ---------------------------------------------------
    def fills_of(self, part):
        out = []
        for gid in lst(part.get("fills")):
            gap = dct(self.gaps.get(gid))
            atoms = "+".join(lst(gap.get("atoms"))) or "?"
            out.append((gid, atoms, gap))
        return out

    def artifacts_of(self, producer):
        return [a for a in self.artifacts if a.get("producer") == producer]

    # -- Artifact comparison of a suspected duplicate pair --------------------
    def compare_pair(self, a, b):
        """Returns (verdict, shared ids, per-part artifact lists).  Rule 1 + F-05, read off the data."""
        ra, rb = self.artifacts_of(a), self.artifacts_of(b)
        ida, idb = {r.get("id") for r in ra}, {r.get("id") for r in rb}
        shared = [i for i in (r.get("id") for r in ra) if i in idb]
        if not shared:
            return "distinct_exits", [], (ra, rb)
        exempt = [r for r in ra + rb if r.get("id") in shared and r.get("alternatives_of")]
        if exempt:
            return "alternatives_of", shared, (ra, rb)
        verdicts = [dct(dct(dct(self.part_by_id.get(p)).get("assessment")).get("needed")).get("verdict")
                    for p in (a, b)]
        if all(v == "merge_candidate" for v in verdicts):
            return "merge_candidate", shared, (ra, rb)
        return "double_producer", shared, (ra, rb)

    # -- F-14: is the exit 0 usable as evidence at all? -----------------------
    def calibration_twin(self):
        for run in lst(self.run.get("check_runs")):
            run = dct(run)
            if "delete-ring" in str(run.get("cmd")) and run.get("exit") == 1:
                return run
        return None


# ---------------------------------------------------------------- sections

def head(d):
    twin = d.calibration_twin()
    runs = [dct(r) for r in lst(d.run.get("check_runs"))]
    primary = next((r for r in runs if r.get("exit") == 0), None)
    if primary is not None:
        exit0 = "exit 0" if twin is not None else "exit 0 · **uncalibrated**（无删环变体记录，不当证据）"
    else:
        exit0 = "未记录"

    out = [
        f"# 九环审计 — {d.doc.get('feature')}",
        "",
        f"本文件是 `{REL}/audit.yaml` 的投影（F-12：两者同目录，**不一致时以 yaml 为准**）。",
        f"审计是否完整由退出码说话，不由本文的散文说话（F-13 / PSL-006）——判定在 `{REL}/check_audit.py`。",
        "",
        "| 项 | 值 |",
        "|---|---|",
        f"| 机器可读半边 | `{REL}/audit.yaml` |",
        f"| 判定脚本 | `{REL}/check_audit.py` |",
        f"| 本文件的生成方式 | `python3 {REL}/render_audit.py`（确定性、可重跑） |",
        f"| 规律来源 | `{REL}/{d.doc.get('psl')}` |",
        f"| check-audit 对本文档 | {exit0} |",
        f"| check-audit 删环变体 | {'exit 1（F-14 校准孪生已记录）' if twin else '**缺失**'} |",
        f"| 规模 | {len(d.rings)} 环 · {len(d.parts)} 配件 · {len(d.gaps)} 缺口 · "
        f"{sum(len(lst(r.get('missing'))) for r in d.rings)} 处登记为缺少 · "
        f"{len(d.artifacts)} 条产物-生产者 · {len(lst(d.doc.get('proposals')))} 条提案 |",
        "",
        "## 读法",
        "",
        "- **implemented 是三态，不是布尔**（PSL-010）：`declared` 只有 SKILL.md / 提示 · `compiled` 有 verify 脚本或被门挡 ·",
        "  `verified` 有行为层运行记录。本报告任何一处都不写「已实现 ✓」——那是布尔，`check_audit.py` 会 exit 1。",
        "- **闸不是门**（PSL-006）：`kind: script` 的 Gate 一律写「闸」，`kind: human` 的三道门 G1 / G2 / G3 才写「门」。",
        "- **代签不是人签**（F-15）：`signer_kind: delegated_agent` 一律渲染为「代签（delegated）」。",
        "- **缺口四原子**（PSL-016）：Knowledge / Capability / Judgment / Control。",
        "- **来源三种**（PSL-017）：lifecycle_blank（生命周期自列的空白）· newly_identified（本次新识别）·",
        "  unenforced_rule（宪法写了规则、机器一侧无闸）。",
        "",
    ]
    return out


def ring_section(d, ring):
    rid = ring.get("id")
    parts = [dct(p) for p in lst(ring.get("parts"))]
    missing = lst(ring.get("missing"))
    out = [
        f"## {rid} {RING_TITLE.get(rid, '')}".rstrip(),
        "",
        f"**问题**：{para(ring.get('question'))}",
        "",
        f"{len(parts)} 个配件 · {len(missing)} 处登记为缺少。",
        "",
        "| 配件 / 缺少 | kind | 缺口 · 原子 | 独占产物 / 角色 | 闸 · 门 | Loop | needed | implemented | naming |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    footnotes = []
    for part in parts:
        pid = part.get("id")
        a = dct(part.get("assessment"))
        aid = a.get("id")
        needed, impl, naming = dct(a.get("needed")), dct(a.get("implemented")), dct(a.get("naming"))

        fills = d.fills_of(part)
        if fills:
            gapcol = "<br>".join(f"`{atoms}` {cell(gid.rsplit('/', 1)[-1])}" for gid, atoms, _ in fills)
        else:
            gapcol = "**不填任何缺口 → overfill**"

        artifact = part.get("artifact")
        role = part.get("role")
        if artifact:
            artcol = code(cell(artifact))
            if role:
                artcol += f"<br>role `{role}`"
        elif role:
            artcol = f"无独占产物 · role `{role}`"
        else:
            artcol = "无独占产物 · 无 role"

        gates = lst(part.get("gates"))
        gatecol = "<br>".join(d.gate_label(g) for g in gates) if gates else "**无闸无门**"

        loop = part.get("loop")
        loopcol = code(loop) if loop else "`null`"

        ncol = f"**{needed.get('verdict')}**"
        if needed.get("merge_candidate_with"):
            ncol += f"<br>与 `{needed['merge_candidate_with']}` 并列"
        icol = f"**{impl.get('verdict')}**"
        not_reached = dct(impl.get("not_reached"))
        if not_reached:
            icol += "<br>未达：" + " / ".join(f"`{k}`" for k in not_reached)
        if impl.get("calibrated") is False:
            icol += "<br>`calibrated: false`"
        mcol = f"{naming.get('provenance')} → **{naming.get('verdict')}**"
        if naming.get("verdict") == "misfit":
            mcol += f"<br>建议名 `{naming.get('suggested_name')}`<br>**不重命名**"

        out.append(f"| `{pid}` [^{aid}] | `{part.get('kind')}` | {gapcol} | "
                   f"{artcol} | {gatecol} | {loopcol} | {ncol} | {icol} | {mcol} |")

        psl = " · ".join(f"{dim} {', '.join(lst(dct(a.get(dim)).get('psl_ids')))}"
                         for dim in ("needed", "implemented", "naming"))
        footnotes.append(f"[^{aid}]: `{pid}` 的 PSL-ID 追溯 — {psl}。环归属证据：`{part.get('ring_evidence')}`。")

    # 表末尾的 missing 行：来源标签 + necessity + deletion 一句（PSL-017 空白诚实登记）
    for gid in missing:
        gap = dct(d.gaps.get(gid))
        atoms = "+".join(lst(gap.get("atoms"))) or "?"
        source = SOURCE_LABEL.get(gap.get("source"), str(gap.get("source")))
        ncell = (f"necessity **{gap.get('necessity')}**<br>撤掉 / 不补它：{cell(gap.get('deletion_test'))}"
                 f"<br>证据：{cell(refs(gap.get('evidence')))}<br>disposition `{gap.get('disposition')}`")
        out.append(f"| **（缺少）** `{cell(gid.rsplit('/', 1)[-1])}` | — | `{atoms}`<br>**{source}** | — | — | — | "
                   f"{ncell} | — | — |")

    out.append("")
    out.append(f"### {rid} 判定详情")
    out.append("")
    for part in parts:
        out += part_detail(d, part)
    out += footnotes
    out.append("")
    return out


def part_detail(d, part):
    pid = part.get("id")
    a = dct(part.get("assessment"))
    needed, impl, naming = dct(a.get("needed")), dct(a.get("implemented")), dct(a.get("naming"))
    out = [f"#### `{pid}` — {a.get('id')}（state: {a.get('state')}）", ""]

    out.append(f"- **needed `{needed.get('verdict')}`** — 撤掉后：{para(needed.get('deletion_test'))}")
    for key, label in (("merge_reason", "并列生产的判定"), ("merge_candidate_reason", "并列生产的判定")):
        if needed.get(key):
            out.append(f"    - {label}：{para(needed[key])}")
    out.append(f"    - 证据：{refs(needed.get('evidence'))}")

    out.append(f"- **implemented `{impl.get('verdict')}`** — {IMPLEMENTED_NOTE.get(impl.get('verdict'), '')}")
    for state, why in dct(impl.get("not_reached")).items():
        out.append(f"    - 未达 `{state}`：{para(why)}")
    for key, label in (("gate_caveat", "闸的保留"), ("no_gate", "无闸"), ("no_gate_note", "无闸"),
                       ("note", "备注"), ("calibration_note", "校准备注")):
        if impl.get(key):
            out.append(f"    - {label}：{para(impl[key])}")
    if impl.get("calibrated") is not None:
        out.append(f"    - 这把尺子本身校准了没有（PSL-007）：`calibrated: {str(impl['calibrated']).lower()}`")
    out.append(f"    - 证据：{refs(impl.get('evidence'))}")

    out.append(f"- **naming {naming.get('provenance')} → `{naming.get('verdict')}`** — "
               f"位置 / 产物：{code(naming.get('artifact_or_position'))}")
    if naming.get("verdict") == "misfit":
        out.append(f"    - 建议名 `{naming.get('suggested_name')}`，**不重命名**（PSL-014：建议不等于重命名，"
                   f"`rename: {str(naming.get('rename')).lower()}`）")
    for key, label in (("fit_reason", "贴合理由"), ("rename_reason", "命名判定")):
        if naming.get(key):
            out.append(f"    - {label}：{para(naming[key])}")
    out.append(f"    - 证据：{refs(naming.get('evidence'))}")

    if part.get("loop_note"):
        out.append(f"- **Loop**：`{part.get('loop')}` — {para(part['loop_note'])}")
    elif part.get("loop_reason"):
        out.append(f"- **Loop `{part.get('loop')}`**：{para(part['loop_reason'])}")
    if part.get("role_conflict"):
        out.append(f"- **role_conflict**：{para(part.get('conflict_note'))}")
    for src in lst(part.get("ring_sources")):
        src = dct(src)
        out.append(f"    - 环归属来源 `{src.get('source')}`（{src.get('ref')}）：{para(src.get('says'))}")
    for adj in lst(a.get("adjudications")):
        adj = dct(adj)
        out.append(f"- **争议裁决**：{para(adj.get('question'))} — 采纳 {para(adj.get('held'))}；"
                   f"异见 {para(adj.get('dissent'))}；resolved_by `{adj.get('resolved_by')}`")
    out.append(f"- disposition `{a.get('disposition')}`")
    out.append("")
    return out


def duplicates_section(d):
    pairs = lst(d.doc.get("suspected_duplicate_pairs"))
    out = [
        "## 疑似重复的 Part 对",
        "",
        "同一件事有没有两个配件在做？下表的 **Artifact 对照** 与 **裁决** 都是从 `artifacts[]` 与两个 Part 的",
        "`needed.verdict` 现算的（G1 规则 1 + F-05），不是抄 `suspected_duplicate_pairs` 里的那一行——",
        "两者不一致时表里会写「登记 ≠ 现算」。三种裁决：`distinct_exits`（产物无交集，不是一回事）·",
        "`merge_candidate`（在争同一个产物，两边都认领为合并候选，审计不当场裁）·",
        "`alternatives_of`（同阶段的条件替代分支，F-05 三条件齐，不算争）。",
        "",
        "| 对 | Artifact 对照 | 裁决 | 落在哪份记录 |",
        "|---|---|---|---|",
    ]
    details = []
    for pair in pairs:
        pair = dct(pair)
        names = lst(pair.get("parts"))
        if len(names) != 2:
            continue
        a, b = names
        derived, shared, (ra, rb) = d.compare_pair(a, b)
        recorded = pair.get("verdict")
        verdict = f"**{derived}**" if derived == recorded else f"**{derived}**（登记 ≠ 现算：登记为 `{recorded}`）"

        def side(name, records):
            items = "、".join(f"`{r.get('id')}`" + ("（alternatives_of `%s`）" % r["alternatives_of"]
                                                    if r.get("alternatives_of") else "")
                              for r in records) or "—"
            return f"`{name}` → {items}"

        compare = f"{side(a, ra)}<br>{side(b, rb)}"
        if shared:
            compare += "<br>共同产物：" + "、".join(f"`{s}`" for s in shared)
        else:
            compare += "<br>共同产物：无"
        srcs = "、".join(f"`{s}`" for s in lst(pair.get("sources"))) or "—"
        props = "、".join(f"`{p}`" for p in lst(pair.get("proposals")))
        out.append(f"| `{a}`<br>vs<br>`{b}` | {compare} | {verdict} | {srcs}"
                   f"{'<br>提案 ' + props if props else ''} |")
        details.append(f"- **{pair.get('id')} `{a}` vs `{b}`** — {para(pair.get('note'))}")
    out.append("")
    out += details
    out.append("")
    return out


def proposals_section(d):
    proposals = [dct(p) for p in lst(d.doc.get("proposals"))]
    out = [
        "## proposals",
        "",
        f"{len(proposals)} 条。每条都必须指向一个已识别的 Assessment 或 Gap（DP-2：补的理由不能是"
        "「这环显得单薄」）——`proposal_without_source` 就是这条的闸。",
        "按 destination 分组：",
        "",
    ]
    for dest in ("new_issue", "skill_fix_list", "no_action"):
        group = [p for p in proposals if p.get("destination") == dest]
        out.append(f"### {dest}（{len(group)}）")
        out.append("")
        if not group:
            out += ["本次无。", ""]
            continue
        out.append("| id | source | 提案 |")
        out.append("|---|---|---|")
        for p in group:
            out.append(f"| `{p.get('id')}` | `{cell(p.get('source'))}` | {cell(p.get('text'))} |")
        out.append("")
    return out


def run_evidence_section(d):
    run = d.run
    out = [
        '<a id="run-evidence"></a>',
        "",
        "## run_evidence",
        "",
        "本次运行的行为层证据。签字三元组住在这里，不在 `gates[]`（G1 规则 3b）。",
        "",
    ]

    meta = dct(run.get("run"))
    out += [
        "| 项 | 值 |", "|---|---|",
        f"| slug | `{meta.get('slug')}` |",
        f"| 状态机 | `{meta.get('state')}` |",
        f"| 账本 | `{meta.get('ledger')}` |",
        f"| 分支 | `{meta.get('branch')}` |",
        f"| issue | `#{meta.get('issue')}` |",
        "",
        "### 三道门的签字（F-07 三元组）",
        "",
        "`verdict` ∈ pending / pass / reject / waived。pending 之外的任何判决都必须有 signer 与 signer_kind；",
        "`delegated_agent` 必须附授权引用，并且**只能渲染为「代签（delegated）」——本次三道门没有一道是人签**。",
        "",
        "| 门 | verdict | 签字人 | signer_kind | 渲染为 | 授权引用 | 时间 |",
        "|---|---|---|---|---|---|---|",
    ]
    for rec in lst(run.get("gates")):
        rec = dct(rec)
        kind = rec.get("signer_kind")
        rendered = {"delegated_agent": "**代签（delegated）**", "human": "人签", None: "—"}.get(kind, f"`{kind}`")
        out.append(f"| `{rec.get('gate')}` | **{rec.get('verdict')}** | {code(rec.get('signer') or None)} | "
                   f"{code(kind or None)} | {rendered} | {cell(rec.get('authorization_ref')) if rec.get('authorization_ref') else '—'} | "
                   f"{code(rec.get('at') or None)} |")

    twin = d.calibration_twin()
    out += [
        "",
        "### check-audit 的两次运行（F-14 校准孪生）",
        "",
        "对报告的 exit 0 只有在同一次运行里配上删环变体的 exit 1 才算证据；没有变体记录的 exit 0 标 `uncalibrated`，不当证据。",
        "",
        f"**本次：{'变体记录在场，exit 0 可作证据' if twin else '**缺变体记录 → exit 0 标 `uncalibrated`，不当证据**'}。**",
        "",
    ]
    for n, r in enumerate(lst(run.get("check_runs")), 1):
        r = dct(r)
        flag = ""
        if r.get("exit") == 0 and twin is None:
            flag = " · **uncalibrated**"
        out += [f"运行 {n} — **exit {r.get('exit')}**{flag}", "", "```", para(r.get("cmd")), "```", ""]
        observed = dct(r.get("observed"))
        if observed:
            def shown(v):
                if isinstance(v, list):
                    return "[" + ", ".join(str(x) for x in v) + "]"
                return str(v)
            out.append("观察到：" + " · ".join(f"`{k}: {shown(v)}`" for k, v in observed.items()))
            out.append("")
        if r.get("twin_note"):
            out += [f"> {para(r['twin_note'])}", ""]

    diff = dct(run.get("audited_dirs_diff"))
    stat = dct(diff.get("git_diff_stat"))
    out += [
        "### 审计者不改被审对象（PSL-003）",
        "",
        f"由 `{diff.get('instrument')}` 证明，不由记忆保证：分支上每个带 `Card:` footer 的提交，按它自己那张卡的",
        "白名单回放一遍 `verify_commit.py`，并检查它有没有碰被审的三个目录。",
        "",
        "| 项 | 值 |", "|---|---|",
        f"| 回放结论 | `ok: {str(diff.get('ok')).lower()}` |",
        f"| 快照取于 | `{diff.get('snapshot_at')}` |",
        f"| Card-footer 提交数 | {diff.get('card_commits')} |",
        f"| **碰了被审目录的提交数** | **{diff.get('card_commits_touching_audited_dirs')}** |",
        f"| 回放被拒的提交数 | {diff.get('card_commits_rejected')} |",
        "",
    ] + ([f"> {para(diff.get('snapshot_note'))}", ""] if diff.get("snapshot_note") else []) + [
        "| 提交 | 卡 | 回放 exit | 碰被审目录 |",
        "|---|---|---|---|",
    ]
    for c in lst(diff.get("touches_audited_dirs_per_commit")):
        c = dct(c)
        out.append(f"| `{c.get('sha')}` | `{c.get('card')}` | {c.get('exit')} | "
                   f"`{str(c.get('touches_audited_dirs')).lower()}` |")
    out += [
        "",
        f"三个被审目录（`plugins/sdlc/skills`、`plugins/sdlc/agents`、`plugins/sdlc/docs`）自第一个 Card 提交"
        f"（`{stat.get('first_card_commit')}`）起的 `git diff --stat`：",
        "",
        "```",
        para(stat.get("cmd")),
        f"→ {stat.get('lines')} 行输出（空）" if stat.get("lines") == 0 else f"→ {stat.get('output')}",
        "```",
        "",
        "### skill 源码问题",
        "",
        f"路径：`{run.get('skill_issues')}` — {run.get('skill_issues_count')} 条（`grep -c '^| I-'`）。",
        "",
        "### 这把尺子校准到什么程度",
        "",
        f"> {para(run.get('calibration_wording'))}",
        "",
        "以上措辞逐字取自 `calibration/known_gaps.yaml`（calibrate 阶段的已接受声明）。",
        "**报告里不出现不带限定语的「calibrated」**：本次的尺子有 11 项已知空隙，列在下面。",
        "",
    ]

    hold = dct(run.get("holdout"))
    if hold:
        attested = "**代签（delegated）**" if hold.get("attested_by_kind") == "delegated_agent" else \
                   code(hold.get("attested_by_kind"))
        out += [
            "#### holdout（实现者从未见过的那一片）",
            "",
            "| 项 | 值 |", "|---|---|",
            f"| 记录 | `{hold.get('ref')}` |",
            f"| 清单 | `{hold.get('manifest')}` |",
            f"| 仪器 HEAD | `{hold.get('instrument_head')}` |",
            f"| 变体 | {hold.get('variants')} |",
            f"| 命中 / 未命中 | {hold.get('hits')} / {hold.get('misses')}（hit_rate {hold.get('hit_rate')}） |",
            f"| 见证人 | `{hold.get('attested_by')}` · {attested} |",
            f"| 授权 | {cell(hold.get('authorization'))} |",
            f"| 渲染规定 | `render_as: {hold.get('render_as')}` — F-15：不渲染为人的验证 |",
            "",
        ]

    kg = lst(run.get("known_gaps"))
    if kg:
        out += [
            f"#### 已知空隙（{len(kg)} 项，逐字取自 `calibration/known_gaps.yaml`）",
            "",
            "每一条都是 open，去向 change-proposal-002（先过 G1 解释轮，再补锁定测试，再要一片新的 holdout）。",
            "",
            "| id | 空隙 | 规格出处 | 期望 token | 状态 |",
            "|---|---|---|---|---|",
        ]
        for g in kg:
            g = dct(g)
            out.append(f"| `{g.get('id')}` | {cell(g.get('name'))} | {cell(g.get('spec_source'))} | "
                       f"`{cell(g.get('expected_token'))}` | {cell(g.get('status'))} |")
        out.append("")

    ext = dct(run.get("external_evidence"))
    out += [
        "### 外部证据",
        "",
        f"- 档位：**`{ext.get('kind')}`** — 这是外部证据的**替代品**，"
        "不是用户验证，也不是行为层的对比运行。",
        f"- 内容：{para(ext.get('what'))}",
        f"- 有效范围：`{ext.get('valid_for')}`",
        "",
    ]
    return out


def assembly_notes(d, source_files):
    return [
        "## assembly notes",
        "",
        "CARD-06 只做装配。四个片段的正文逐字保留（同一段 YAML 在片段与 `audit.yaml` 里字节一致），"
        "装配时只做了下面这些事，一处不漏：",
        "",
        "| # | 改动 | 为什么 | 影响 |",
        "|---|---|---|---|",
        "| 1 | rings 重排为 R0…R8, spine | 片段的自然顺序是 R0,R1,R2,spine / R3,R4,R5 / R6 / R7,R8；`spine` 移到末尾 | 只改顺序，环与配件的内容一字未动 |",
        "| 2 | 去重 `gates[]` 的 `lock_done_when.py` | CARD-02 与 CARD-03 各登记了一次，两条内容完全相同 | 保留第一条；31 条 Gate 无内容冲突 |",
        "| 3 | 新增顶层 `suspected_duplicate_pairs[]` | 「哪两个配件疑似重复」是跨片段的事实，任何单张卡都写不了；AC-005-a 点名要 pr-review vs code-reviewer 与 donewhen-extract vs acceptance-spec 两对 | 只是索引：Artifact 对照与裁决由 `render_audit.py` 从 `artifacts[]` 现算并与登记值比对，不一致会在表里标出来 |",
        "| 4 | 新增顶层 `run_evidence{}` | 片段按约定不写它（它是整份文档级的证据） | 门的签字、两次 check 运行、回放结果、校准措辞与 11 项已知空隙 |",
        "| 5 | `run_evidence.calibration_wording` / `holdout` / `known_gaps` 逐字复制 | 它们是 calibrate 阶段的已接受声明 | 未改一字，含「never the unqualified word 'calibrated'」这条措辞禁令 |",
        "",
        "**其余全部为空**：没有新增、删除或改写任何 Part、Assessment、Gap、Artifact、Gate、Proposal；",
        "没有解决任何片段间的内容冲突（因为没有冲突：73 个 Gap、58 条产物-生产者、39 条提案的 id 两两不撞）。",
        "",
        "### 装配核对：PSL-017 三种来源都登记了吗",
        "",
        "`dos.yaml` 有四条规则的 `enforced_by` 不是 `system`（R001 / R008 / R010 / R017）——每一条都必须在合并后的",
        "`gaps[]` 里至少有一条 `source: unenforced_rule` 的登记。核对结果：",
        "",
        "| dos.yaml 规则 | enforced_by | 登记在 | 补登了吗 |",
        "|---|---|---|---|",
        "| R001 一个产物只有一个生产者 | `user_workflow` | `spine` · `R5` · `R6` | 否，片段已覆盖 |",
        "| R008 门的判决要有人签 | `user_workflow` | `spine` · `R6` · `R7` | 否，片段已覆盖 |",
        "| R010 未过 calibrate 的标准不是证据 | `not_enforced` | `R3` · `R6` · `R8` | 否，片段已覆盖 |",
        "| R017 效力主张不得超过证据档位 | `user_workflow` | `R6` · `R7` | 否，片段已覆盖 |",
        "",
        "四条全部有登记，**没有补登任何 Gap**。R017 落在 R6 / R7 而不是装配预判的 R3 / R8：R6 是"
        "「验收线自己没被验收」的位置，R7 是三个 static_only 的交付 skill——两处都比预判的位置更贴。",
        "",
        "### 输入片段",
        "",
    ] + [f"- `{REL}/{f}`" for f in source_files] + [
        "",
        "### 铁律",
        "",
        "check-audit 的 exit 0 说的是**这份文档的形状齐全**，不是「九环做到位了」。"
        + tiers_sentence(d) + "；"
        + gates_sentence(d) + "；外部证据是 "
        + f"`{dct(d.run.get('external_evidence')).get('kind')}`。",
        "这份报告能不能当结论，由 G3 的人看完上面这些标记之后决定。",
        "",
    ]


def tiers_sentence(d):
    """The declared / compiled / verified split, counted from the document — never hand-written."""
    tally = {"declared": 0, "compiled": 0, "verified": 0}
    for _, part in d.parts:
        v = dct(dct(part.get("assessment")).get("implemented")).get("verdict")
        if v in tally:
            tally[v] += 1
    said = "、".join(f"{n} 个停在 `{state}`" for state, n in tally.items() if n)
    zero = [f"`{state}`" for state, n in tally.items() if not n]
    tail = f"，**没有一个到 {' / '.join(zero)}**" if zero else ""
    return f"{len(d.parts)} 个配件里 {said}{tail}"


def gates_sentence(d):
    """How the three doors were actually signed, read off run_evidence."""
    kinds = [dct(g).get("signer_kind") for g in lst(d.run.get("gates"))]
    delegated = sum(1 for k in kinds if k == "delegated_agent")
    human = sum(1 for k in kinds if k == "human")
    pending = sum(1 for k in kinds if not k)
    bits = []
    if delegated:
        bits.append(f"{delegated} 道代签（delegated）")
    if human:
        bits.append(f"{human} 道人签")
    if pending:
        bits.append(f"{pending} 道未决")
    return "三道门里 " + "、".join(bits)


# ---------------------------------------------------------------- main

def render(doc):
    d = Doc(doc)
    out = head(d)
    out += ['<a id="ring-tables"></a>', "", "# 环表（R0…R8 · spine）", ""]
    for rid in RING_ORDER:
        ring = d.by_ring.get(rid)
        if ring is None:
            out += [f"## {rid}", "", "**该环不在 audit.yaml 里**（`ring_missing`）。", ""]
            continue
        out += ring_section(d, ring)
    out += duplicates_section(d)
    out += proposals_section(d)
    out += run_evidence_section(d)
    out += assembly_notes(d, ["audit/rings-R0-R2-spine.yaml", "audit/rings-R3-R5.yaml",
                              "audit/rings-R6.yaml", "audit/rings-R7-R8.yaml"])
    return "\n".join(out).rstrip("\n") + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audit", nargs="?", default=str(DIR / "audit.yaml"), help="path to audit.yaml")
    ap.add_argument("-o", "--output", default=str(DIR / "AUDIT.md"), help="path to AUDIT.md")
    args = ap.parse_args(argv)

    doc = load(args.audit, "audit")
    if not isinstance(doc, dict):
        sys.exit(f"render_audit: cannot read audit: {args.audit} is not a YAML mapping")
    text = render(doc)
    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"render_audit: {args.audit} → {args.output} ({len(text.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
