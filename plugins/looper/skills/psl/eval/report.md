# psl — evaluation marker

**gate_pass: `static_only`** · tier: production · evaluated_layers: `[structural]` · date: 2026-07-06

> **What this is (and is not).** This is a persistent record of a *structural* (Tier-1) review
> done by **2 independent, information-isolated judges emulating** skillwise's ruler
> (`docs/THEORY.md` + `psl-skill-spec.md` 行为契约) plus a fresh round-2 confirmer (4-eyes).
> It is **NOT** a run of the installed `evaluate-skill` skill, and **NOT** an official skillwise
> certification. The machine-readable verdict is `gate.json` beside this file. Per THEORY.md §7,
> an unguided judge reading skill text is ~46% accurate — everything here that speaks about
> *runtime behavior* is an L1 prediction, not an L2 verdict.

## Verdict

- **Tier-1 (structural): PASS** — round-1 blocking closed, hardening applied, regression green.
- **Tier-2 (effect delta / T1–T5): NOT RUN** → `static_only`. Spec §6's T1–T5 are L2-native
  (they require a live `/psl` run with a user in the loop; the Skill registry only picks up
  looper v0.2.0 in a fresh session). A static read must not impersonate that result.

## How it was reached (2 rounds, measure-after-change)

1. **Round 1** (2 information-isolated judges, one instructed to refute):
   - judge A: **pass**, 0 blocking, 5 non-blocking (declarative-only delivery gate; per-line
     arrow check false-positive; prose-pipeline blind spot; dangling eval/ refs; annotation nit).
   - judge B: **fail**, 1 blocking — SKILL.md's own exit-gate section referenced
     `eval/gate.json` + `eval/report.md` **before they existed** (an honesty wound in the exact
     section that vouches for honesty). Plus 5 adversarial script probes: unordered-list
     pipeline and 阶段一/二/三 both passed 0-flag; six-layer empty shell passed; vacuous-arrow
     acceptance passes by design (declared judge share); EXAMPLE.md fails the gate if run
     directly (footgun).
2. **Fixes applied** (same day): these files created; `verify_psl.py` hardened —
   `阶段N`/`phase N` → reject, ≥3 sequence words (首先/然后/接着/最后…) in Workflow → flag,
   per-layer empty-shell → reject (raw-line check so a pure-mermaid State Machine doesn't
   false-positive), Acceptance arrow check aggregated per **entry** (multi-line entries no
   longer falsely rejected); SKILL.md anti-pipeline criterion reworded beyond literal Step-N;
   EXAMPLE.md "not itself a PSL, don't gate it directly" note; stray `.impeccable/` removed;
   `[γ→人]` annotation unified.
3. **Regression** (author-run): legal PSL from EXAMPLE.md **PASS 0-flag**; multi-line
   acceptance probe **PASS** (round-1 false positive closed); planted-defect sample 5 REJECTs;
   adv-unordered-pipeline **FLAG**; adv-阶段N **3 REJECTs**; adv-empty-shell **7 REJECTs**.
4. **Round 2** (1 fresh confirmer, 4-eyes): see `gate.json.provenance.round2` for the verdict.

## Known, honestly-declared residuals

- The **delivery gate is declarative** ("交付前必须跑 verify_psl.py") — not compiled into a
  hook. Highest-ROI remaining hardening; in `fix_list`.
- The script's rejects are **lexical**; a semantically disguised pipeline can still pass with
  only a flag. This is inside the skill's declared scope (脚本只降机械缺陷频率；语义半边判给
  judge 与人) — umbrella honesty holds, mesh could always be finer.
- **Vacuous arrows** (`搜索 → 结果`) pass the arrow check; the skill never claims
  arrow-presence ⇒ judgeable. Judge share, declared.

## T1–T5 (spec §6) — pending behavioral run

| # | 用例 | 通过条件（行为） | 状态 |
|---|---|---|---|
| T1 | 体验性需求、无物料（"按时间搜索记忆"） | 主动问承重槽（带推荐答案）；Domain Model 含朴素表没有的实体；Acceptance 全行为可判 | pending L2 |
| T2 | 确定性需求（CSV 导出 6 列） | 判定 PRD 领域，明说过填，不虚构世界 | pending L2（双轨判据已编码于正文，行为未证） |
| T3 | 带物料 | 从物料抽世界事实，不重复问 | pending L2 |
| T4 | 用户答"不知道/直接写" | 该槽 → Open Question，仍交付完整 PSL，无默认值 | pending L2 |
| T5 | 反惯性 | 产出 PSL 的 Workflow 层无步骤 | pending L2（静态半已编译：verify_psl.py reject/flag；EXAMPLE 内嵌 PSL 过门 0-flag） |

## To upgrade `static_only` → certified `pass`

New session (so `/psl` is registered under looper v0.2.0), run T1–T5 live: T1 with a real
back-and-forth, T2 verbatim, T3 with a real legacy doc, T4 by answering "不知道", T5 on every
produced artifact via `verify_psl.py`. Assert on the produced PSL (not the wording), require
the with-skill run to clear conditions the without-skill run fails (`delta_exist > 0`), zero
repeated regressions. Then update `gate.json`.
