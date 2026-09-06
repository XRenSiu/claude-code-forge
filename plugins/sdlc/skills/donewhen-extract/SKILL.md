---
name: donewhen-extract
description: |
  Use when a Run's 本次验收-class acceptance conditions are MISSING or DEGENERATE — when "what
  *this specific execution* must achieve to count as done" lives only as a fuzzy Issue
  sentence, and the engine, left alone, fills a boilerplate `done_when` that cannot be
  falsified ("信号诉求被兑现"). donewhen-extract turns one Issue/Run intent into a set of
  STRUCTURED, falsifiable `done_when` predicates (Given/When/Then), each with numeric
  thresholds instead of adjectives, each happy path paired with an unhappy one, and exits
  on a contradiction-check + coverage-check. It is the TASK-LEVEL mirror of invariant-extract:
  invariant-extract recovers a Territory's 常驻不变量 (every Run must hold); this recovers one Run's
  本次验收 (this Run must achieve). Triggers: "抽 done_when" / "提取验收条件" / "任务级规约" /
  "本次验收" / "把 Issue 变成可证伪验收信号" / "为这次任务立法" / "donewhen-extract" /
  "draft the done_when for this issue". Do NOT use for: a Territory's resident invariants
  (that is invariant-extract), compiling done_when into tests/rubric (that is spec-compile),
  or proving the compiled ruler is correct (that is calibrate).
argument-hint: "<issue id / signal id / intent text> [--template <contract_template_id>] [--auto]"
version: 0.2.0
user-invocable: true
# imported into sdlc 2026-09-05 from qanat/.claude/skills; body kept, sdlc wiring added (see 接线 / 术语映射)
---

# donewhen-extract

Recover one Run's **本次验收 acceptance conditions** — the `done_when` predicates *this specific
execution* must achieve to be judged done, distinct from a Territory's 常驻不变量 resident invariants
(every Run must always hold). This skill describes the world those predicates live in, the
criteria that separate a falsifiable one from boilerplate, the primitive that makes the
Given/When/Then shape mechanical, and the gates a draft must clear before a Contract is signed.
**It prescribes no step order — the engine sequences the work; what follows are the gaps to
fill and the gates that must hold, in any order.**

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

## The gap (why the engine can't just paraphrase the Issue)

A composite of three atoms: **Judgment** (what counts as a falsifiable 本次验收), **Capability**
(the adjective→threshold rewrite + the happy/unhappy pairing + the exit contradiction/coverage
checks), **Control** (done_when rides a Contract template — a gate asset only a human signs, R002).

The load-bearing reason this is not free:

> **An Issue states a *wish*, not an *acceptance test*.** "把审核做对" / "让接口更快" describe
> intent; they are not falsifiable. A naive "paraphrase the Issue into done_when" pass emits
> unfalsifiable boilerplate — `done_when: ["信号诉求被兑现"]` — which any output passes and
> no gate can ever fail. That is the exact pathology dos.yaml 0.1.13 was legislated against
> (done_when 退化成不可证伪套话).

Deletion test: remove this skill and ask the engine to "write the done_when for this Issue."
It produces an adjective soup with no numeric thresholds, all happy and no unhappy paths, and
no check that the clauses don't contradict each other or leave a scenario uncovered — i.e. a
green-by-construction contract. The gap is the *judgment* that makes each clause falsifiable,
plus the exit that proves the set is consistent and complete enough.

## The world

- **本次验收 vs 常驻不变量 (KAOS).** 本次验收 = Achieve, "this Run attains it" (`P⇒本次验收Q`) — that is `done_when`.
  常驻不变量 = Maintain/Avoid, "always holds, every Run" (`常驻不变量(P→Q)`) — that is an invariant, *not* this
  skill's output. A clause that must survive a future, unrelated Run is misfiled: it is 常驻不变量, **hand
  it to invariant-extract** (it is not garbage, it is the wrong layer). See `references/given-when-then.md`.
- **done_when is a structured Contract field, never prose.** dos.yaml `Contract.done_when` is an
  array of items `{id, statement, ears_type?, verify?, based_on?}`: `id` is a stable REQ-ID
  (stable within the template, inherited by instances, so G2 and failure_memory can track *per
  clause* across Runs); `statement` is the falsifiable EARS sentence; `ears_type ∈
  ubiquitous|event|state|unwanted|optional`; `verify ∈ command|checklist|rubric` is the per-clause
  verification intent; `based_on` points at the MemoryAsset that motivated the clause (复利溯源).
  Emit items, not a paragraph.
- **The Issue is the seed, the Territory's purpose is the lens.** A bare Issue does not
  self-bound — what "done" means is defined relative to *what this Territory owns* (`Territory.name`
  + `Territory.kpi` + the contract template). Project the intent onto the aspect this Run delivers
  (correctness / latency / cost / safety), and the kpi is that aspect's threshold source.
- **Altitude.** Constitution (R00x) ⊃ responsibility (常驻不变量 invariants) ⊃ **task (`done_when`, where
  this skill works)**. A predicate that holds for *every* Run of this Territory is not done_when —
  it is a resident invariant; do not smuggle it onto the done_when card.
- **Division of labor.** invariant-extract → the 常驻不变量 column. **donewhen-extract → the 本次验收 done_when
  (here).** spec-compile → done_when ↓ into eval_case / fitness fn / rubric. calibrate → proves
  those compiled rulers are load-bearing. This skill stops at the SPEC; it does not compile it.

## What counts as a correct done_when clause (the criteria — declared, not sequenced)

These are the Judgment fences. They hold whenever a clause is evaluated, in any order. The three
HTML disciplines are the load-bearing three; full procedures in `references/given-when-then.md`.

- **Falsifiable, or it does not enter — adjectives become numeric thresholds.** "更快" → "p95 < 200ms";
  "稳定" → "在 1000 次并发下 0 报错"; "大部分" → a number. **A clause you cannot point an instrument
  at is boilerplate, not an acceptance condition.** Every surviving clause must name a value a gate
  can read. This is the line between a recovered 本次验收 and an LLM inventing plausible-sounding wishes.
- **Every happy path carries an unhappy twin, and the twin stands alone.** A `given` that states only
  the difference forces the reader to inherit the rest from its sibling, so a checker handed just the
  twin cannot tell what was removed — restate the happy `given`, then write the difference.
  `validate_done_when_v2.py` rejects a twin whose `given` does not cover its pair's (dogfood I-55).
- **Every happy path carries an unhappy twin.** A clause that only says what should succeed leaves
  the failure semantics undefined — exactly the seam an agent games (pass the example, ignore the
  edge). For each `WHEN <happy> THE SYSTEM SHALL <succeed>`, draft the paired
  `WHEN <unhappy/边界/恶意输入> THE SYSTEM SHALL <reject/降级/报错>` (`ears_type: unwanted`).
  Adjudication bias: **rather over-specify the unhappy path than leave it implicit.**
- **Given/When/Then shape, EARS surface.** Each clause is `WHEN/WHILE/IF <condition> THE SYSTEM
  SHALL <observable outcome>`. Given = precondition/context, When = trigger, Then = the falsifiable
  outcome. The shape is mechanical (`assets/done_when_card.yaml`); the *content* is the judgment.
- **Has provenance when it comes from a scar.** A clause distilled from a `failure_memory` entry
  carries `based_on` pointing at it — the compounding anchor (a failure → a new clause → a regression
  guard). Greenfield clauses (from the Issue alone) need no based_on, but are flagged for review.

## Primitives (the mechanical share — `scripts/`, `assets/`)

- **The card is a named-field structure** (`assets/done_when_card.yaml`): every clause fills named
  slots (id / statement / ears_type / given / when / then / threshold / paired_with / verify /
  based_on / disposition), so an adjective cannot silently land where a threshold belongs and a
  happy clause cannot land without its unhappy twin recorded. Emit the card; do not hand-format prose.
- **The intent scan** is documented patterns for harvesting candidate conditions from the Issue +
  its `failure_memory` (last-N for this template/Territory) + the contract template's prior done_when.
  Patterns: `references/given-when-then.md`. (Engine-runnable; not welded into a sequence.)

## The exit — mechanical pre-gate, then the real guarantee

`scripts/verify_done_when.py <card.yaml> [--dos dos.yaml]` is the **mechanical pre-gate** — and it
checks the *product*, not mere well-formedness. It rejects on:

- any `statement` containing a banned vague quantifier with no numeric threshold recorded
  (`快/慢/稳定/大部分/尽快/合理/友好/…` → **reject** unless a `threshold` field pins it);
- any clause of `ears_type: event|state` with **no paired unhappy clause** (`paired_with` empty) →
  **reject** (every happy needs an unhappy twin);
- `id` present, stable-shaped (REQ-ID / DW-NNN), and unique within the card;
- `statement` non-empty and EARS-shaped *enough* to carry a SHALL (EARS *grammar niceties* are a
  judge call — flagged, not mechanically rejected);
- **contradiction check**: no two clauses assert opposite outcomes on the same trigger (a cheap
  pairwise scan; the SMT-grade check is a judge/tool call — flagged);
- **coverage check**: every `ears_type: event` trigger has at least one unwanted-path sibling, and
  any Territory `kpi` aspect with zero clauses is flagged as an uncovered scenario.

The semantic half — is this *really* the narrowest falsifiable condition for this Run? does the
threshold reflect the kpi, not a number pulled from air? does the unhappy twin cover the *right*
edge? — is a judge call against the criteria above; `verify_done_when.py` marks those clauses
`needs_semantic_review`, it does not rubber-stamp them. The **certified guarantee** is that judge
call + the Contract-sign seam + (production) `delta_exist` on held-out Issues — `static_only` until
such a set exists. The script lowers boilerplate frequency; it is not the whole exit.

## Gates and the seam (Control — concrete and non-skippable)

The engine runs the extraction; these gates do not move:

- **Draft, don't sign — the seam.** done_when rides a **Contract template, a gate asset only a
  human signs (R002)**. This skill is a drafting clerk: it emits the done_when card as a Contract
  draft. The Contract goes live only when signed — by a human, or auto-signed for `risk_class ∈
  config.auto_sign_risk_classes` (default `low`). **High-risk or template-changing done_when is
  PROPOSE-only** (`NEEDS_HUMAN` → change proposal / G2 signing (sdlc)). The skill never auto-signs a contract.
- **Generation-side, trusted-side.** done_when is produced **pre-Run, on the trusted side** (the
  Goodhart fix from dos 0.1.13): the executor never writes its own acceptance criteria. Drafting
  here, before execution, is what keeps the contract honest.
- **`done_when` for the extraction itself.** The extraction is done when: the Issue is bound to a
  Territory and its purpose pulled; every surviving clause is falsifiable (threshold or instrument
  named), happy-paired-with-unhappy, EARS-shaped, and carries `based_on` if from a scar;
  `verify_done_when.py` passes; the contradiction + coverage checks are recorded; 本次验收/常驻不变量 misfiles are
  handed to invariant-extract. Iteration to get there is the engine's.
- **Schema (landed).** `Contract.done_when` exists (structured items, stable REQ-IDs). The skill
  writes a Contract draft; the contract.drafted/signed 三件套 (guards / projection / sign-off UI)
  already ships in the daemon. Until signed, the draft lives in the workspace + change proposal / G2 signing (sdlc).

## High-risk — never do (non-waivable)

- **Never emit an unfalsifiable clause.** No threshold and no instrument → out (or rewritten). A
  clause that cannot fail is not an acceptance condition.
- **Never leave a happy path without its unhappy twin.** The undefined failure semantics is the
  gaming seam.
- **Never auto-sign a Contract.** done_when lands only by signature (human, or risk-class auto-sign);
  the skill drafts, the seam signs (R002).
- **Never put a 常驻不变量 invariant on the done_when card.** A predicate that must hold on *every* Run goes
  to invariant-extract, not here.
- **Never let the executor's session draft its own done_when.** Generation is pre-Run, trusted-side
  (the Goodhart wall). 
- **Never copy a number from air.** A threshold must trace to the Territory kpi, an SLO, or a real
  failure — else flag it `needs_semantic_review`, do not pretend it is grounded.

## Ratchet and compounding (evolution behind a gate)

- **Ratchet.** Each `failure_memory` entry under this template (a clause that kept failing) is a
  fresh seed: it becomes a *new* done_when clause (`based_on` that memory) **and** a regression case
  that gates future contract versions. One failure → tighter done_when + a guard = the compounding
  step (dos behavior: template_refine_after_failures). The skill drafts the tightening; R002 signs it.
- **Per-clause tracking.** The stable REQ-ID is the compounding anchor: G2's `Verdict.reasons`
  reference clauses by REQ-ID, and failure_memory accumulates per REQ-ID, so "which clause this Run
  keeps tripping on" is mechanical, not a re-read.

## Out of scope

- **Territory resident invariants (常驻不变量)** — `invariant-extract`. 本次验收 candidates that must hold every Run
  are handed to it.
- **Compiling done_when into eval_case / fitness fn / rubric** — `spec-compile`. This skill produces
  the SPEC; spec-compile turns it into the STANDARD that enters a gate.
- **Proving the compiled ruler is load-bearing** — `calibrate`. done_when is the input to the ruler,
  not the proof the ruler works.
- **Ontology / boundary / ubiquitous language** — `dos-extract`. This skill *consumes* its output.

## References

- `references/given-when-then.md` — the 本次验收/常驻不变量 test, the Given/When/Then + EARS grammar, the three
  disciplines (adjective→threshold, happy/unhappy pairing, exit checks), the intent-scan patterns.
- `references/contradiction-coverage.md` — the exit's two checks: pairwise contradiction (SMT-style,
  borrowed from Kiro) and scenario coverage (fallback: OpenSpec strict missing-scenario probe).
- `references/anti_patterns.md` — the boilerplate failure modes, the provenance rule, the boundary
  reminders (don't become invariant-extract / spec-compile).
- `assets/done_when_card.yaml` — the named-field output card.
- `assets/decisions_template.md` — the per-clause audit-trail shape.

## 接线（在 sdlc 里的位置）

- **L3 契约起草者**：`/issue` 已把 AC 写成 v2 形状；本 skill 把它收紧成可签的 `done_when.yaml`（阈值溯源、
  happy/unhappy 配对、矛盾与覆盖两检），没有 done-when-pipeline 的 `/acceptance-spec` 时它就是契约产出者。
  产物路径记入 `sdlc_state.py set contract.done_when=… contract.source=donewhen-extract`。
- **G2 之前**：卡是草案；`lock_done_when.py sign` 之后才冻结。改动走变更提案。
- **常驻不变量候选 → `/invariant-extract`**（本插件）；编译成测试 / 评判程序 → `/spec-compile`；证明尺子承重 → `/calibrate`。
- **失败记忆的来源**：`.sdlc/<slug>/ledger.md` 的 `fail` 行与 `escape-defects.md`；`based_on` 引它们的行。

## Exit gate for this skill itself

Verify with skillwise `evaluate-skill`. A read is not the verdict (an unguided judge is ~46% on
"which skill is better"). Scaffold tier: static structural read + one smoke run on a real Issue with
`failure_memory`. Production tier: with/without `delta_exist` on a held-out set of Issues (does the
skill produce more falsifiable, better-paired done_when than the engine alone?) — until such a set
exists this honestly sits at `static_only`.
