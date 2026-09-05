---
name: calibrate
description: |
  Use BEFORE a compiled standard (an eval_case set or a rubric_version from spec-compile) is
  allowed to go live as a gate — to prove the RULER ITSELF is correct, not just that it is
  green. calibrate is the META-GATE ("标准的标准"): it does not judge the artifact, it judges
  the thing that judges the artifact. Two mirrors, one principle (永远不要相信一把没校准的尺子):
  ① eval_case → MUTATION SCORE (inject mutants — PIT/Stryker/mutmut/cosmic-ray; every mutant a
  failing eval_case can't kill is a gate gap); ② rubric → AGREEMENT (run it on reference
  solutions with known verdicts; drop rubric sets that disagree — CDRRM; hard line Krippendorff
  α ≥ 0.80). Plus the two non-negotiables: a HOLDOUT slice the executor never sees, and G2
  evaluator/executor ISOLATION (R001). A standard that fails any of the four is FORBIDDEN to go
  live. Triggers: "校准" / "标准的标准" / "mutation score" / "agreement / α" / "证明 eval_case 承重" /
  "证明 rubric 对" / "元闸门" / "calibrate" / "prove this ruler is load-bearing". Do NOT use for:
  writing specs (invariant-extract / donewhen-extract), compiling specs into standards
  (spec-compile — it produces the ruler, calibrate certifies it), or the runtime post-supersede
  calibration QUESTION (that is the `calibration.resolved` event — a SIGNAL into this skill, not it).
argument-hint: "<standard ref: eval_case set id | rubric_version id> [--mirror mutation|agreement] [--auto]"
version: 0.1.0
user-invocable: true
# imported into sdlc 2026-09-05 from qanat/.claude/skills; body kept, sdlc wiring added (see 接线 / 术语映射)
---

# calibrate

Prove that a compiled standard — an `eval_case` set or a `rubric_version` — is **load-bearing,
not decorative**, before it is allowed to gate anything. This is the **meta-gate**: the only
gate that judges *the thing that judges the output*. This skill describes the two mirrors that
certify a ruler, the two non-negotiables (holdout + isolation) that make the certification real,
and the meta-gate verdict that decides whether a standard may go live. **It prescribes no step
order — the engine sequences the work; what follows are the gaps to fill and the gates that must
hold, in any order.**

## 术语映射（在 sdlc 里怎么读这份文件）

本 skill 引自 qanat 仓库，正文保留其领域词汇；在 sdlc 里按下表读：

| 原文 | sdlc 里的对应物 |
|---|---|
| Territory（领地） | 一个 bounded context / 模块：`dos.yaml` 的 `bounded_contexts.current_context`；issue 的 `Depends on DOS` 所属上下文 |
| Run（一次执行） | 一次 issue → PR 的交付，即 `.sdlc/<slug>/` 一个 slug |
| Contract / Contract 模板 | `done_when.yaml`（v2，以 AC 为单位）；模板 = 同类需求复用的 AC 骨架 |
| R001（评估者与执行者隔离） | sdlc 的信息隔离：实现子 agent 看不到评审判据；验收在独立会话 |
| R002（闸门资产只能人签） | sdlc 的 **G2**（判据冻结 `lock_done_when.py sign --by <人>`）与 **G3**（例外复核） |
| 变更提案 / G2 签字（sdlc） / change proposal / G2 signing (sdlc) / NEEDS_HUMAN | `assets/change_proposal.md` 变更提案 + G2/G3 人签；账本 `ledger.md` 记 propose |
| `verify_g1` / `review_g2`（qanat 的机器闸 / 评审闸） | sdlc L7 的 **A 档机械验收** / **C 档判断验收**——注意与 sdlc 的 G1（世界裁决）、G2（判据冻结）**不是同一对门** |
| MemoryAsset（eval_case / rubric_version / failure_memory） | 归档目录 `specs/<slug>/` 里的测试集 / 评判 rubric；failure_memory = `ledger.md` 的 fail 行 + `escape-defects.md` |
| daemon / 运行时 | 本地测试与 CI；`/sdlc` 的 acceptance 阶段 |
| `calibration.resolved` 事件 | G3 记录里"标准不清"的改判（`g3_record.md`） |

## The gap (why a green test report is not a calibrated ruler)

A composite of three atoms: **Judgment** (what counts as a calibrated standard), **Capability**
(run mutation testing / compute an agreement matrix / carve a holdout), and **Control** (the
meta-gate seam — non-compliant forbids activation).

The load-bearing reason this is not free:

> **A standard that passes and a standard that bites look identical from a green report.** An
> eval_case suite can be all-green and kill zero injected faults; a rubric can score 100% and
> disagree wildly with the reference verdicts. Asked to "ship this gate", the engine reads the
> green report and ships — trusting a ruler nobody measured. That is the exact pathology the
> reward-hacking literature names: when the only signal is "tests pass", any model saturates the
> visible set while real compliance slides underneath (SpecBench).

Deletion test: remove this skill and ask the engine to "put this eval_case / rubric into the
gate." It activates the standard on "tests pass" alone — mutation score uncomputed, agreement
unmeasured, no holdout carved, isolation unverified. The green report decorates; it does not gate.
The gap is the *meta-gate*: the mirrors + thresholds + holdout + isolation that turn a decoration
into something that actually bites.

## The world

- **The first principle (HTML §01⑤).** **永远不要相信一把没校准的尺子。** Responsibility-level uses
  reference solutions to calibrate the rubric; task-level uses mutants to calibrate eval_case — the
  two命门 are the same thing seen in two mirrors. calibrate is where `eval_case` / `rubric_version`
  cross from decoration to load-bearing.
- **Two mirrors, one principle.** ① `eval_case → mutation score`: inject mutants, every one a failing
  eval_case can't kill marks a gate gap (`references/mutation-mirror.md`). ② `rubric → agreement`:
  run it on reference solutions with known verdicts, drop the inconsistent rubric sets, hard line
  Krippendorff α ≥ 0.80 (`references/agreement-mirror.md`).
- **Two non-negotiables (HTML §05 ☐3, ☐4).** A **holdout** slice of the golden set the executor
  never sees, run only at gate time; and **G2 isolation** — evaluator physically separated from
  executor (R001). Mutation testing is itself an adversarial stress-test *of the evaluator*. See
  `references/holdout-and-isolation.md`.
- **Not the runtime calibration QUESTION.** The codebase already has a `calibration.resolved` event
  — the post-supersede question a human answers (`evaluator_fault` vs `standard_unclear`). That is a
  **runtime signal INTO this skill**, not this skill: an accumulation of `standard_unclear` answers
  is exactly the trigger that a standard needs re-calibration here. calibrate is the *offline
  meta-gate*; the runtime question is one of its compounding inputs.
- **Altitude.** spec-compile produces the ruler (`calibration_pending: true`). calibrate flips that
  pending to a meta-gate verdict. Only then may the sign seam (R002, for rubric) / activation let the
  standard gate real Runs.

## What counts as a calibrated standard (the four 不可破 jud据 — declared, not sequenced)

These are the meta-gate fences (HTML §05). All four hold before a standard goes live, in any order.

- **☐1 eval_case kills the mutants — mutation score meets threshold.** Feed the step-① bad samples +
  auto-injected small faults; **every un-killed mutant is a gate gap**, logged, not swallowed. Below
  threshold = the eval_case is decoration, *not* the agent being weak. (镜面①)
- **☐2 rubric reproduces the reference verdicts — agreement α ≥ 0.80.** Run the rubric on known
  good/bad samples, measure consistency with the human-labeled verdicts. 0% or wildly variable = the
  gate is wrong, *not* the agent. (镜面②; `config.evaluator_exam.min_agreement` = 0.8 is this line.)
- **☐3 there is a holdout the executor never sees.** Part of the golden regression set is run **only
  at gate time**, invisible to the executor — else any model saturates the visible set while real
  compliance slides (SpecBench, measured).
- **☐4 G2 evaluator is isolated from the executor.** Unless the evaluating apparatus is fully
  separated from the evaluated entity, there is no evaluation (Berkeley RDI). Isolation is the
  precondition for evaluation to exist, not fastidiousness.

A standard failing ANY of the four is **forbidden to go live** — that is the meta-gate's whole job.

## Primitives (the mechanical share — `scripts/`, `assets/`)

- **The report is a named-field structure** (`assets/calibration_report.yaml`): the standard under
  test fills named slots (standard_ref / kind / mutation_score / surviving_mutants / agreement_alpha /
  holdout_ref / isolation_attested / verdict), so a missing mutation score can't hide and surviving
  mutants can't be swallowed. Emit the report; do not hand-wave "looks calibrated."
- **The mutation harness** is the documented tool table (PIT·JVM / Stryker·TS / mutmut·cosmic-ray·Py)
  + the rule that each `failure_memory` bad sample enrolls as a natural mutant. The **agreement
  harness** is the reference-solution set + the Krippendorff α computation. Patterns:
  `references/mutation-mirror.md`, `references/agreement-mirror.md`. (Engine-runnable; not welded.)

## The exit — the meta-gate (mechanical thresholds, then the real guarantee)

`scripts/verify_calibration.py <calibration_report.yaml> [--min-mutation 0.7] [--min-alpha 0.8]` is
the **meta-gate enforcement** — it checks the *standard's right to go live*, not mere well-formedness.
It rejects (forbids activation) on:

- `kind: eval_case` with `mutation_score` absent or `< min-mutation` → **reject** (☐1);
- `kind: rubric` with `agreement_alpha` absent or `< min-alpha` (default 0.80) → **reject** (☐2);
- `surviving_mutants` non-empty but not each logged as a gate gap → **reject** (no silent caps);
- `holdout_ref` empty **or** `holdout_unexposed_confirmed` false → **reject** (☐3: no holdout — or a
  leaked one — certifies nothing);
- `isolation_attested` not true → **reject** (☐4: no isolation, no evaluation);
- thresholds loosened below the standing hard lines → **reject** (the lines only ratchet tighter).

The semantic half — is the mutant family the *right* one (does it cover the fault class actually
feared)? are the reference solutions representative, not cherry-picked? is the holdout genuinely
unseen? — is a judge call against the four jud据; `verify_calibration.py` marks those
`needs_semantic_review`, it does not rubber-stamp them. The **certified guarantee** is the meta-gate
verdict + the human-sign seam (R002, for rubric) + that the holdout was truly held out. The script
enforces the thresholds; the judgment confirms the mirrors were aimed correctly.

## Gates and the seam (Control — concrete and non-skippable)

The engine runs the calibration; these gates do not move:

- **The meta-gate is the seam.** calibrate does not judge a Run's output — it judges the standard.
  Its verdict (`pass` / `fail`) is the **gate on the gate**: a standard may go live only on `pass`.
  A `fail` blocks activation and routes the gaps (surviving mutants / inconsistent rubric dims) back
  to spec-compile to re-compile, and to the spec authors to tighten.
- **Rubric is a gate asset — human signs (R002).** calibrate produces the *evidence* (agreement α)
  that makes the signature defensible; the activation still goes through the human sign seam. The
  meta-gate verdict does not bypass R002 — it is its precondition.
- **Holdout discipline is non-skippable.** The held-out slice is never injected into any executor
  prompt, never used as a few-shot, never shown at compile time. It is run *only* when the meta-gate
  or the live G1 runs. Leaking it silently turns the whole certification into theater.
- **`done_when` for the calibration itself.** Done when: each standard under test has its mirror run
  (mutation score for eval_case, agreement for rubric), surviving mutants logged as gate gaps, a
  holdout carved and attested unseen, isolation attested; `verify_calibration.py` passes; the
  meta-gate verdict is recorded and (on pass) handed to the sign/activation seam.
- **Schema (landed, dos 0.1.15).** The standards are existing dos objects (`MemoryAsset:eval_case` /
  `rubric_version`). calibrate records its result on the **landed** `MemoryAsset.calibration` field
  (status / mutation_score / agreement_alpha / holdout_ref / isolation_attested) — see the dos.yaml
  0.1.15 amendment + decisions.md §十二. Field-name map: the dos field `agreement_alpha` is the
  `calibration_report.yaml`'s `agreement.krippendorff_alpha` (same number, the Krippendorff α). A
  standard with `status != calibrated` may not be relied on as a load-bearing gate.

## High-risk — never do (non-waivable)

- **Never let an uncalibrated standard go live.** 永远不要相信一把没校准的尺子 — no mutation score / no
  agreement / no holdout / no isolation ⇒ forbidden, full stop.
- **Never compute the score on data the executor can see.** The holdout must be genuinely unseen; a
  leaked holdout certifies nothing.
- **Never let the evaluator share the executor's context/model** (R001) — including reusing the
  executor's session for the agreement run. Isolation is the precondition, not a nicety.
- **Never loosen the hard lines.** α ≥ 0.80 and the mutation-score threshold only ratchet tighter.
  Lowering a line to pass a standard is gaming the meta-gate.
- **Never treat "tests pass" as the gate.** Green ≠ load-bearing; only the mutation/agreement mirrors
  make a standard bite.
- **Never swallow a surviving mutant.** Each un-killed mutant is a logged gate gap that becomes the
  next eval_case to write — silent truncation reads as "covered" when it isn't (no silent caps).

## Ratchet and compounding (evolution behind a gate)

- **Ratchet.** Each gate gap (surviving mutant / rubric disagreement) becomes a new golden case that
  the *next* version of the standard must close; the golden set only grows, the thresholds only
  tighten. One miss → one new mutant + one new case = the compounding step. Both
  `rubric_version` (agreement) and `eval_case_version` (mutation score) are gated together at upgrade.
- **The runtime loop closes here.** A live `calibration.resolved = standard_unclear` (a human改判 said
  the *standard*, not the evaluator, was unclear) is a fresh seed: it enrolls the disputed sample into
  the golden set and re-triggers calibrate on the affected standard — the failure-back-to-legislation
  edge (HTML §04⑨) made concrete.

## Out of scope

- **Writing specs** — `invariant-extract` / `donewhen-extract`. calibrate certifies rulers, not rules.
- **Compiling specs into standards** — `spec-compile`. It produces the eval_case/rubric;
  calibrate proves they bite. Compiled is not certified.
- **The runtime post-supersede question** — the `calibration.resolved` event (a signal into this
  skill). calibrate is the offline meta-gate; the event is one of its inputs.
- **Running the live gate** — the daemon's `verify_g1` / `review_g2`. calibrate decides whether a
  standard is *allowed* into that runtime.

## References

- `references/mutation-mirror.md` — 镜面①: eval_case → mutation score; the tool table (PIT / Stryker /
  mutmut / cosmic-ray); failure.memory bad samples as natural mutants; surviving mutant = gate gap.
- `references/agreement-mirror.md` — 镜面②: rubric → agreement matrix; reference solutions; CDRRM drop
  rule; Krippendorff α ≥ 0.80; the tie to `evaluator_exam` + the `calibration.resolved` runtime signal.
- `references/holdout-and-isolation.md` — the golden regression set, the holdout the executor never
  sees, G2 physical isolation (R001), and the four 不可破 jud据 as one checklist.
- `references/anti_patterns.md` — the decoration-as-gate failure modes, the leaked-holdout trap, the
  loosened-threshold trap, the boundary reminders.
- `assets/calibration_report.yaml` — the named-field meta-gate report.
- `assets/decisions_template.md` — the per-standard calibration audit-trail shape.

## 接线（在 sdlc 里的位置）

- **标准的标准**：`/spec-compile` 产出的 eval_case 集与 rubric 在进入 L7 验收（A 档 / C 档）前必须过本门；
  未过的标准不能在 PR 的 Verification 段当证据，`meets_done_when` 不得引用它。
  报告路径记入 `sdlc_state.py set contract.calibration_report=…`。
- **holdout = 隐藏变体集**：参考文档 L5 的"隐藏集只含冻结 AC 的变体、放在实现 agent 不可读的环境"就是 ☐3；
  隐藏集失败路由 `sdlc_state.py fail --signal hidden_variant_fail`（任务层）。
- **☐4 隔离** = sdlc 的实现者 / 评审者信息隔离（`/pr-review` 输出不直接喂实现子 agent；跨供应商可用则用）。
- **运行时改判**：G3 记录里人把某次失败改判为"标准不清"→ 该样本入黄金集、重触发本 skill（`g3_record.md`）。

## Exit gate for this skill itself

Verify with skillwise `evaluate-skill`. A read is not the verdict (an unguided judge is ~46% on
"which skill is better"). Scaffold tier: static structural read + one smoke run computing a mutation
score on a real eval_case set and an agreement α on a real rubric. Production tier: with/without
`delta_exist` on held-out standards (does the skill catch decorative rulers the engine would have
shipped?) — until such a set exists this honestly sits at `static_only`.
