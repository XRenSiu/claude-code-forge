---
name: invariant-extract
description: |
  Use when a Territory's □-class resident invariants are MISSING — when "what this
  block must always hold, on every Run" lives only in people's heads or in scars
  from past failures, not as written, traceable, verifiable rules. invariant-extract
  recovers them by ABDUCTION from the Territory's failure memory (the load-bearing
  channel — a violation is the most reliable signal an invariant exists) and by
  DEDUCTION from its code execution points. It is the symmetric counterpart of
  dos-extract (which deductively reverse-engineers a system's constitution + ontology
  from a static repo); this one abductively recovers ONE Territory's resident
  invariants from the failures it paid for. Triggers: "抽不变量" / "提取不变量" /
  "责任级不变量" / "□ 不变量" / "从失败里总结规则" / "把失败变成不变量" /
  "为这块领地立常驻法" / "invariant-extract" / "harden this territory's invariants".
  Do NOT use for: binding / claim-resolution (orthogonal, human-set), ontology /
  boundary (that is dos-extract), or task-level done_when (that is acceptance-spec).
argument-hint: "<territory id or name> [--cross-territory] [--auto]"
version: 0.3.1
user-invocable: true
# imported into AI-DLC 2026-09-05 from looper v0.2.0; body kept, AI-DLC wiring added (see 接线 / 术语映射)
---

# invariant-extract

Recover a Territory's **□ resident invariants** — the rules every Run under it must
hold, distinct from a single Run's `done_when` (◊). This skill describes the world
those invariants live in, the criteria that tell a real one from a fake, the primitives
that make extraction mechanical where it can be, and the gates a candidate must clear
before it lands. **It does not prescribe a step order — the engine sequences the work;
what follows are the gaps to fill and the gates that must hold, in any order.**

## 术语映射（在 AI-DLC 里怎么读这份文件）

本 skill 引自 qanat 仓库，正文保留其领域词汇；在 AI-DLC 里按下表读。**Territory 与 Run 两行是承重的**：
按字面读 dos.yaml 的 `Run`（一次 issue → PR 的交付）会把"这个插件自己被改"的那些失败全部投影为 ∅，
溯因通道当场掏空。

| 原文 | AI-DLC 里的对应物 |
|---|---|
| Territory（领地） | 一块有单一责任的区域：一个 `dos.yaml` 的 `bounded_contexts.current_context`，或一个插件 / 一个环 / 一个 skill 族。**"插件即领地"是合法读法**——它有 name、有 kpi、有 scope |
| Territory.name / kpi | 该区域的一句话责任 + 它的直接度量。插件领地：`README` 的一句话定位 + 它守的东西（每步产物可检或被人签的门挡住） |
| Run（一次执行） | **该领地的任一次被调用**，不只是交付。对插件领地有两类：① 交付 Run = `.aidlc/<slug>/` 一个 slug；② dogfood Run = 用这套 skill 改这套 skill 自己的一次。□ 要活得过**两类**，这是 `--cross-territory` 之外最容易漏的宽度 |
| 失败记忆 failure.memory | 见下面「接线」的清单：`ledger.md` 的 `fail` / `deviation` 行、`escape-defects.md`、G3 记录、dogfood 的 `skill-issues.md`。**不含** `gate.json` 的 `fix_list`（那是登记的缺口，见下） |
| obstacle_ref | 上面任一条的稳定 id：`ledger:fail#3`、trace 事件 id（`ev-0005`）、`skill-issues.md` 的 `I-nn`、逃逸缺陷编号 |
| R001 / R002 / R00x | **dos.yaml `rules` 段的 id**（AI-DLC：R001 单生产者、R002 单契约 schema …）。qanat 原文里 R001=评估者隔离、R002=闸门资产只能人签，**在本插件里不要这样读**——那两条在 AI-DLC 是「信息隔离」与「G2/G3 人签」，不是编号 |
| 立法收件箱 / 立法者签字 | `assets/change_proposal.md` 变更提案 → **G2**（`lock_done_when.py sign`）；账本 `ledger.md` 记 propose |
| MemoryAsset | 归档目录 `specs/<slug>/` 里的测试集 / rubric；failure_memory 见上 |
| daemon / 运行时 | 本地测试与 CI；`/ai-dlc` 的 acceptance 阶段 |

## The gap (why the engine can't just read them off the code)

A composite of three atoms: **Judgment** (what counts as a real □), **Control** (the
propose-and-sign gate, role separation), **Capability** (the mechanical scan + the exit
verifier). The Knowledge it needs (KAOS, Model Spec) it routes to, below.

The load-bearing reason this is not free:

> **A piece of code that correctly maintains an invariant, and one that merely hasn't
> violated it yet, look identical.** Correct code is *silent* about its invariants — it
> just doesn't break them. So the most reliable signal that an invariant exists is a
> **violation**: the moment it actually broke.

Deletion test: remove this skill and ask the engine to "list this Territory's resident
invariants" from the code — it will pattern-match guard clauses (deduction only) and
miss every invariant that was learned from a failure, because that knowledge is not in
the code, it is in `failure.memory`. The gap is real; it is the abductive channel.

## The world

- **□ vs ◊ (KAOS).** □ = Maintain/Avoid, "always holds", every Run (`□(P→Q)`, `□(P→¬Q)`).
  ◊ = Achieve, "this Run attains it" (`P⇒◊Q`) — that is `done_when`, not an invariant.
- **Two channels, both real, never merged.** *Deduction* scans code execution points →
  invariants the code already declares (cheap, high-precision). *Abduction* negates a
  failure → the invariant the code paid for (expensive, high-value; the moat). See
  `references/abduction.md`.
- **Purpose is the lens, not an input.** A bare failure does not self-interpret — what
  "counts as a failure" is defined relative to *what this Territory maintains*. Purpose
  (= `Territory.name` + `Territory.kpi` + `dos.scope`) projects a failure onto the
  aspect this block owns (correctness / latency / cost / safety / reversibility), and
  `kpi` is that aspect's direct carrier. Two axes, orthogonal: **purpose picks the
  aspect (dimension), Occam picks the scope (width).** See `references/abduction.md`.
- **Altitude.** Constitution (R00x, system-wide) ⊃ responsibility (this Territory's
  invariants, where this skill works) ⊃ task (`done_when`). A candidate that holds under
  *every* Territory's purpose is constitution, not territory-level (see cross-territory).
- **Division of labor (no whole-card generator).** dos-extract → ontology / boundary /
  system constitution. **invariant-extract → the □ column (here).** acceptance-spec →
  `done_when`. Binding / autonomy / ownership → human-set when the Territory is established.
  There is no
  monolithic "territory-spec"; assembling the card is the engine's job, not a skill.

## What counts as a correct invariant (the criteria — declared, not sequenced)

These are the Judgment fences. They hold whenever a candidate is evaluated, in any order.

- **Survives the □/◊ test.** Ask: *can this rule survive a future, unrelated Run of this
  Territory?* Asked **relative to this Territory's purpose**. Survives → □, keep. Only
  holds relative to one task's goal → ◊, **hand to the `done_when` generator** (it is
  not garbage, it is misfiled). Adjudication bias: **rather demote than wrongly promote**
  — a missed invariant is re-caught by the next failure; a ◊ wrongly promoted to □
  strangles the whole block. Full test + the layer-probe: `references/survival-test.md`.
- **Narrowest rule on the right aspect.** A failure's negation is underdetermined — a
  whole family of rules would prevent it, spread on two axes. Project by purpose first
  (drop the failure if it projects to ∅ under this purpose), then take the *narrowest*
  rule covering the obstacle. A narrowest rule on the wrong aspect is still wrong.
- **Has provenance, or it does not enter.** Every carded invariant points to a code
  execution point (deduction) or a real failure (abduction). **No provenance, no entry.**
  This is the line between a recovered rule and an LLM inventing plausible-sounding ones.
- **Strength-classified.** "Can a task legally violate it?" No → **hard** (root, mostly
  prohibitions). Yes → **overridable default** (carries an authority level; Model Spec
  chain of command). What can be legally violated is *not* a hard □ — keep it out of the
  hard column.

## Primitives (the mechanical share — `scripts/`, `assets/`)

- **The card is a named-field structure** (`assets/invariant_card.yaml`): every invariant
  fills named slots (statement / strength / aspect / channel / provenance / on_violation),
  so a value cannot silently land in the wrong field. Emit the card; do not hand-format prose.
- **The deductive scan** is documented ripgrep patterns + (optionally) dos-extract's
  `scripts/inventory.py`; it surfaces execution points (`assert`, guard, schema/DB
  constraint, permission check, throw branch, timeout/retry/idempotency key). Patterns:
  `references/abduction.md`. (Engine-runnable; not welded into a sequence.)

## The exit — mechanical pre-gate, then the real guarantee

`scripts/verify_card.py <card.yaml> [--dos dos.yaml]` is the **mechanical pre-gate** — and it
checks the *product*, not mere well-formedness: it rejects auto-installed hard invariants
(they land only behind the human-signed G2 gate), entries with no provenance, and ◊ candidates
smuggled onto the card. Run it before
anything lands. It rejects on:

- every entry has provenance (execution_point or obstacle_ref) — else **reject**;
- strength ∈ {hard, overridable}; hard entries are `disposition: propose` (never auto-carded);
- `confidence: low` ⇒ `disposition: propose` **in either column** (`references/abduction.md` §5);
- aspect present; statement non-empty (EARS *shape* is a judge call — flagged, not mechanically rejected);
- `altitude`, where present, is `territory` — the constitutional suspicion is recorded once, in
  `constitution_promotion_suspects`, not twice (see the ruling in `references/survival-test.md` §2.5);
- no entry duplicates an existing `dos.yaml` R00x id (dedup, not re-legislate); a **re-wording** of
  one is flagged by statement similarity, since exact-match dedup catches nothing a paraphrase evades;
- `channel_2_input.failure_memory_count > 0` carries `sources` — a bare integer is unfalsifiable;
- every `registered_gaps` entry declares `destination ∈ {done_when, issue, backlog}`;
- flags any entry lacking `survival_test: pass` for the human/judge's semantic call.

The report prints `projected_out_obstacles` / `deduped_against_constitution` /
`constitution_promotion_suspects` / `conflicts_for_legislation` counts, so a card that skipped
the abductive channel does not print the same shape as one that worked it.

The semantic half (does it truly survive □/◊ under purpose? is it the narrowest rule on
the right aspect?) is a judge call against the same criteria above — `verify_card.py`
marks those entries `needs_semantic_review`, it does not rubber-stamp them. The **certified
guarantee** is that judge call + the human-sign seam + (production) `delta_exist` on held-out
Territories — `static_only` until such a set exists. The script lowers defect frequency; it
is not the whole exit.

## Gates and the seam (Control — concrete and non-skippable)

The engine runs the extraction; these gates do not move:

- **Propose, don't install — the seam.** The human checkpoint sits at the judgment →
  legislation boundary. **Hard invariants and broad/high-risk abductions are PROPOSE-only**
  (`NEEDS_HUMAN` → legislation inbox); they enter `Territory.invariants` only after a human
  signs — in AI-DLC that signature is **G2**, on a `change_proposal.md`. The skill is a drafting
  clerk, not a legislator.
- **`done_when` for the extraction.** Extraction is done when: the Territory is bound and
  its purpose pulled; both channels have been worked (or the dry channel is explicitly
  recorded, not faked); every surviving candidate has provenance, a □/◊ verdict, and a
  strength; `verify_card.py` passes; conflicts and R00x-dedup are recorded. Iteration to
  get there is the engine's.
- **Schema (landed, dos 0.1.14).** `Territory.invariants` exists. The skill writes
  candidates there (hard = proposed, human-signed). The 三件套 (guards /
  `invariant.proposed·signed` projection / UI sign-off) ships in implementation PRs;
  until then candidates live in the workspace and on the legislation inbox.

## High-risk — never do (non-waivable)

- **Never auto-install a hard invariant.** Hard □ enters only by human signature at G2.
- **Never card a candidate without provenance.** No execution point and no real failure → out.
- **Never promote to R00x inside a single-Territory run.** Cross-territory evidence + a
  legislator do that; a single run can only *flag* a purpose-independent suspect.
- **Never put a ◊ on the invariant card.** It goes to the `done_when` generator.
- **Never re-legislate what is already R00x.** Dedup against `dos.yaml.rules`.
- **Never over-generalize an abduction beyond its obstacle.** Narrowest rule, bound to
  the failure that revealed it.
- **Never write `Territory.invariants` directly for a hard invariant.** Direct writes
  bypass the signing seam; emit a proposal.

## Ratchet and cross-territory (evolution behind a gate)

- **Ratchet.** Each new `failure.memory` entry is a fresh abductive input; each carded
  invariant also becomes a **golden regression case** that gates future cards / rubric
  versions. One failure → invariant + regression guard = the compounding step.
- **`--cross-territory`.** Single-territory runs can only *suspect* a candidate is
  purpose-independent. This pass collects ≥2 Territories' suspects + carded □, tests each
  against *all* known Territories' purposes, corroborates by recurrence, dedups, and emits
  a **batch legislation proposal** to promote the truly purpose-independent ones to R00x.
  Still propose-only; promotion is a human signature. Output template:
  `assets/cross_territory_promotion_template.md`.

## Out of scope

- **Binding / claim-resolution** — the binding column; orthogonal (a signal can feed many
  Territories or none — no unique winner). Purpose-projection here *resembles* it but is
  non-exclusive. Does not block this skill.
- **Ontology / boundary / ubiquitous language** — `dos-extract`. This skill *consumes* its
  output (`dos.yaml`), does not redo it.
- **Task `done_when` / rubric** — `acceptance-spec` / `done-when-pipeline`. ◊ candidates are
  handed to them.

## References

- `references/abduction.md` — the abductive move (project → negate → narrow), the two
  orthogonal axes, the over-generalization guard, the deductive-scan patterns.
- `references/survival-test.md` — the □/◊ survival test + the constitution/territory/task
  layer-probe + strength classification (the load-bearing judgment).
- `references/anti_patterns.md` — the three self-built failure modes, the provenance rule,
  the honest framing of the abductive use of KAOS's obstacle model.
- `assets/invariant_card.yaml` — the named-field output card.
- `assets/cross_territory_promotion_template.md` — the `--cross-territory` batch proposal.

## 接线（在 AI-DLC 里的位置）

- **X1 的常驻不变量**：消费 `/dos-extract` 的 `dos.yaml`；抽出的 □ 不变量卡（`verify_card.py` 过门）交
  `/spec-compile` 编成 fitness fn / property 测试；硬不变量 propose-only，签字走 G2（`change_proposal.md`）。
- **失败记忆的来源**，按本插件实测的产出量排（dogfood 2026-09-05）：
  1. `<plugin>/dogfood/**/skill-issues.md` —— 自审跑出来的缺陷清单，本次最厚的一源；
  2. `.aidlc/<slug>/ledger.md` 的 **`deviation` 行** + `trace.jsonl` 对应事件 —— "为了往下走，我破了自己的规矩"
     是溯因的富矿，而 `fail` 行在一次顺利的运行里可能一条都没有；
  3. `.aidlc/<slug>/ledger.md` 的 `fail` 行；
  4. `escape-defects.md` / G3 记录 —— 逃逸缺陷是最可靠的"有不变量存在"信号（R12 路由：人归因后回到本体层再抽一次）。
- **登记的缺口不是违反**：`eval/gate.json` 的 `fix_list`（本插件 52 条里绝大多数是"L2 从未跑过"这类登记）
  说的是**还没做**，不是**做错了**。取反一件没做过的事得不到 □，只得到一句"应该去做"——那是 ◊。
  这些进卡的 `registered_gaps`，`destination: done_when|issue|backlog` 必填，**不喂 hard_invariants**。
- **通道二输入要可核对**：`channel_2_input` 写 `sources`（每源 ref / entries / kind）与 `snapshot_at`。
  失败记忆在一次运行里会长（本次 `skill-issues.md` 从 6 行涨到 16 行），只写一个整数，别人重跑对不上。
- **◊ 候选**（本次验收）→ `/donewhen-extract`（本插件），不是 acceptance-spec 专属。
- **卡写在哪**：项目目录的 `invariants/`（`docs/invariants/` 也认），**提交进 git**——常驻不变量是
  这个仓库的法，不是这一次运行的产物；放进 `.aidlc/`（per-run 运行时状态）等于每个人各自维护一份。
- **谁写状态**：`world.invariants` 不用手记——`aidlc_state.py init` 用
  `../ai-dlc/scripts/repo_assets.py` 在项目目录里发现 `invariants/` 并写进 `world.*`，
  `repo` / `doctor` 报它在不在、进没进 git。执行本 skill 的实现者写白名单只覆盖 `invariants/`，
  `.aidlc/` 不在其中；让实现者写状态既会撞白名单执行器，也会让"谁记的"这件事失去单一来源。

## Exit gate for this skill itself

Verify with skillwise `evaluate-skill`. Reading it is not the verdict (an unguided judge
is ~46% on "which skill is better"). Scaffold tier: static structural read + one smoke run
on a Territory with real `failure.memory`. Production tier: with/without `delta_exist` on a
held-out set of Territories — until such a set exists this honestly sits at `static_only`.
