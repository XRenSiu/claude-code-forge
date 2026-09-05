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
version: 0.2.0
user-invocable: true
---

# invariant-extract

Recover a Territory's **□ resident invariants** — the rules every Run under it must
hold, distinct from a single Run's `done_when` (◊). This skill describes the world
those invariants live in, the criteria that tell a real one from a fake, the primitives
that make extraction mechanical where it can be, and the gates a candidate must clear
before it lands. **It does not prescribe a step order — the engine sequences the work;
what follows are the gaps to fill and the gates that must hold, in any order.**

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
  `done_when`. Binding / autonomy / ownership → human-set at 设立 (R002). There is no
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
(R002), entries with no provenance, and ◊ candidates smuggled onto the card. Run it before
anything lands. It rejects on:

- every entry has provenance (execution_point or obstacle_ref) — else **reject**;
- strength ∈ {hard, overridable}; hard entries are `disposition: propose` (never auto-carded);
- aspect present; statement non-empty (EARS *shape* is a judge call — flagged, not mechanically rejected);
- no entry duplicates an existing `dos.yaml` R00x id (dedup, not re-legislate);
- flags any entry lacking `survival_test: pass` for the human/judge's semantic call.

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
  signs (R002 — gate assets only humans sign). The skill is a drafting clerk, not a legislator.
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

- **Never auto-install a hard invariant.** Hard □ enters only by human signature (R002).
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

## Exit gate for this skill itself

Verify with skillwise `evaluate-skill`. Reading it is not the verdict (an unguided judge
is ~46% on "which skill is better"). Scaffold tier: static structural read + one smoke run
on a Territory with real `failure.memory`. Production tier: with/without `delta_exist` on a
held-out set of Territories — until such a set exists this honestly sits at `static_only`.
