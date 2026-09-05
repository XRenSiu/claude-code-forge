---
name: spec-compile
description: |
  Use when a spec (a 常驻不变量 invariant R00x from invariant-extract, OR a 本次验收 done_when clause from
  donewhen-extract) needs to become an ENFORCEABLE STANDARD that a gate can run — and the
  engine, left alone, dumps everything into one bucket (a few happy-path example tests + a
  free-form LLM-judge rubric), leaving structure unchecked, behavior under-covered, and
  judgment un-compiled. spec-compile is ONE compiler with THREE production lines, routed by
  DECIDABILITY not by level: ① structural → fitness function (G1); ② behavioral → eval_case
  (G1: example / property-PBT / metamorphic); ③ residual judgment → a judge PROGRAM (G2:
  per-dimension binary+evidence rubric compiled to an executable, retiring the LLM-judge).
  The iron law it encodes: push every clause as far DOWN the ladder as it will go — static
  before tests, tests before model, and even "let the model judge" compiles to a program
  (PAJAMA). Triggers: "编译规约" / "spec 编译" / "把 done_when/不变量编译成测试" /
  "生成 eval_case" / "生成 fitness function" / "把 rubric 编译成程序" / "spec-compile" /
  "compile this spec into a gate standard". Do NOT use for: writing the spec itself
  (invariant-extract / donewhen-extract), or proving the compiled ruler is load-bearing
  (that is calibrate — spec-compile produces the ruler, calibrate certifies it).
argument-hint: "<spec ref: R00x id | done_when card | contract id> [--line structural|behavioral|judgment] [--auto]"
version: 0.1.0
user-invocable: true
---

# spec-compile

Compile any spec — a 常驻不变量 invariant or a 本次验收 `done_when` clause — into a **standard a gate can
run**. One compiler, three production lines, **routed by decidability, not by level**. This
skill describes the decidability ladder the routing rides on, what each line emits, the
disciplines that keep each line load-bearing, and the exit that proves a clause was pushed as
far down as it could go. **It prescribes no step order — the engine sequences the work; what
follows are the gaps to fill and the gates that must hold, in any order.**

## The gap (why "write some tests" is not a compiler)

A composite of three atoms: **Judgment** (which line a clause belongs on — its decidability),
**Capability** (the three emitters: fitness-fn config, eval_case battery, judge program), and
**Knowledge** (the disciplines: Assured 3-filter, ACH mutation-guided generation, PBT sub-layer,
PAJAMA program form).

The load-bearing reason this is not free:

> **The decidability ladder is the whole product, and the engine skips it.** Asked to "make
> this spec testable", the engine writes a handful of happy-path example tests and a paragraph
> telling an LLM to "judge whether it's good." It never asks *can this be decided statically?*
> (cheaper, total) and never *compiles the judgment into a program* (it leaves the model in the
> loop). The result: structure unchecked, behavior gamed through the gaps between examples, and
> a G2 that is an unconstrained LLM — the exact reward-hacking surface dos.yaml R001 exists for.

Deletion test: remove this skill and ask the engine to "turn this done_when into a gate." It
emits example tests only (no property/metamorphic backstop), routes a statically-decidable rule
to an LLM-judge ("能静态判却让模型判"), and writes the rubric as free-form prose. The gap is the
*decidability routing* + the per-line disciplines that make each emitted standard actually bite.

## The world — the decidability ladder (the first principle)

> **能静态判就别跑,能跑测试判就别让模型判,能让模型判就别让人判 —— 而 PAJAMA 把"让模型判"也编译成了程序。**

Every clause is pushed as far DOWN this ladder as it will go. The line is chosen by *how the
clause is decidable*, not by whether it came from a 常驻不变量 invariant or a 本次验收 done_when:

- **① Structural — fitness function (→ G1).** Decidable by reading the artifact statically,
  no execution. Tools: `ArchUnit / dependency-cruiser / ts-arch / OPA-Conftest / Semgrep`.
  Mostly the responsibility-level main road (常驻不变量 invariants about shape/dependency/forbidden-API).
  Discipline: **principle before tool** (pick the check from the rule, not because a tool exists)
  + **tolerance ratchet** (thresholds only tighten — hand to `ratchet`). See `references/decidability-ladder.md`.
- **② Behavioral — eval_case (→ G1).** Decidable by running the artifact against inputs. Tools:
  `Vitest / Playwright / pytest`. Mostly the task-level main road (本次验收 done_when). **Three types,
  not one**: example / **property (the PBT sub-layer — Hypothesis · fast-check)** / metamorphic
  (when there is no oracle). The compiler = **Assured LLMSE three filters** (compiles / passes
  stably / catches a new fault — fails any filter, discard) + **ACH mutation-guided generation**
  (from "which fault class do I fear" → a mutant family → assertions proven to kill them). See
  `references/behavioral-line.md`.
- **③ Judgment — a judge PROGRAM (→ G2).** The residual *after lines ① and ② have drained every
  bit of determinism*. Not a free-form LLM-judge: an **analytic per-dimension rubric** (binary +
  evidence-bound, RRD) → in its terminal form **PAJAMA-compiled into an executable program**, so
  the LLM-judge retires. See `references/judgment-line.md`.

Altitude rule: a clause that line ① could decide must NOT sit on line ② or ③; a clause line ②
could decide must NOT sit on ③. Routing *up* the ladder when a lower line was available is the
load-bearing defect — it leaves cheap, total determinism on the table and widens the gameable surface.

## What counts as correct compilation (the criteria — declared, not sequenced)

These are the Judgment fences. They hold whenever a routed clause is evaluated, in any order.

- **Pushed as far down as it goes.** Each clause carries its decidability verdict and the line it
  landed on; a clause on a higher line than its decidability allows is a **reject** (the keyline
  violated). The exit re-derives this, it is not taken on faith.
- **Behavioral standards are not example-only.** An eval_case battery with only examples and no
  property/metamorphic backstop is a reject (HTML §01①: 例子之间的缝就是 agent 钻空子的地方),
  unless a documented "no property applies here, why" is recorded. Examples pin points; properties
  pin the spaces between.
- **Each eval_case passes the three filters.** It compiles, it passes stably on a correct artifact,
  and it catches at least one injected fault (the ACH/mutation tie-in — proven, not assumed; the
  proof that it bites is calibrate's mutation-score mirror, but the *generation* aims for it here).
- **Each G2 dimension is binary + evidence-bound, and compiles to a program.** A rubric dimension
  that reads "is the code high quality?" is not a dimension; "does function F have a test asserting
  behavior B, cited at file:line?" is. Free-form LLM-judge prose left un-compiled is a reject —
  PAJAMA form or it does not land on G2.
- **Fitness functions are principle-first, ratchet-only.** The check traces to the rule it enforces
  (not to a tool's feature list), and its threshold is monotone-tightening (ratchet), never loosened.

## Primitives (the mechanical share — `scripts/`, `assets/`)

- **The manifest is a named-field structure** (`assets/compile_manifest.yaml`): every source clause
  fills named slots (spec_ref / decidability / line / emitted_standard / type / filters_passed /
  gate / calibration_pending), so a clause cannot be silently routed up the ladder and an
  example-only battery cannot hide a missing property backstop.
- **The routing scan** is documented patterns for reading a clause's decidability (shape/dependency
  predicate → ①; input→output predicate → ②; "a human would have to weigh…" residual → ③) and the
  tool-selection table per line. Patterns: `references/decidability-ladder.md`.

## The exit — mechanical pre-gate, then the real guarantee

`scripts/verify_compile.py <manifest.yaml> [--dos dos.yaml]` is the **mechanical pre-gate** — it
checks the *product* (the routing), not mere well-formedness. It rejects on:

- any clause whose `decidability` is `structural` but `line` is `behavioral|judgment` (or
  `behavioral` routed to `judgment`) → **reject** (routed up the ladder — keyline violated);
- any `line: behavioral` standard of `type: example` with no sibling of `type: property|metamorphic`
  and no recorded `examples_only_justification` → **reject** (例子-only seam);
- any `line: judgment` dimension not marked `binary: true` with an `evidence_ref`, or left as
  `free_form` → **reject** (un-compiled LLM-judge);
- every emitted standard names its `gate` (g1 for ①②, g2 for ③) consistent with its line;
- every standard carries `calibration_pending: true` until calibrate has gated it (a standard is
  drafted here, certified there — it is not load-bearing on emission).

The semantic half — is this *really* the narrowest fitness function for the rule? does the property
capture the right invariant of the behavior? is the G2 dimension's evidence binding sufficient? — is
a judge call against the criteria above; `verify_compile.py` marks those `needs_semantic_review`, it
does not rubber-stamp them. The **certified guarantee** is that judge call + calibrate's two mirrors
(mutation score for ②, agreement for ③) + the human-sign seam on rubric (R002). The script lowers
mis-routing frequency; calibrate is what proves the ruler bites.

## Gates and the seam (Control — concrete and non-skippable)

The engine runs the compilation; these gates do not move:

- **Compiled ≠ certified — the calibrate seam.** spec-compile DRAFTS standards; an eval_case set or
  a rubric_version is **not load-bearing until `calibrate` gates it** (mutation score for ②,
  agreement α≥0.80 for ③). Every emitted standard is `calibration_pending` until then. Shipping a
  standard straight to a gate without calibrate is the headline anti-pattern (a green report that
  decorates, not gates).
- **Rubric is a gate asset — human signs (R002).** A G2 `rubric_version` (MemoryAsset) lands only by
  human signature. spec-compile emits it as a proposal to the legislation inbox.
- **G2 is isolated (R001).** The judge program runs in a process/session independent of the executor,
  read-only on the executor's worktree, input = artifact + rubric only; cross-vendor when the
  Territory sets it. spec-compile must not emit a G2 standard that reads the executor's context.
- **`done_when` for the compilation itself.** Done when: every source clause has a decidability verdict
  and a line; ① emits fitness-fn configs, ② emits an eval_case battery (not example-only), ③ emits a
  PAJAMA-shaped rubric program; `verify_compile.py` passes; everything is marked `calibration_pending`
  and routed to its gate. Iteration is the engine's.
- **Schema (landed).** Outputs land on existing dos objects: ①② → `verify_g1` commands +
  `MemoryAsset:eval_case`; ③ → `MemoryAsset:rubric_version` (+ `Verdict.review_rubric_ref`). No new
  object; spec-compile drafts these and hands them to calibrate + the sign seam.

## High-risk — never do (non-waivable)

- **Never route a clause up the ladder.** Statically-decidable → line ①, never ②/③; behaviorally-
  decidable → line ②, never ③. Leaving cheap determinism on the table is the keyline violation.
- **Never use a false decidability label to dodge a gate.** The down-route is only honest if the
  decidability verdict is TRUE; mislabeling a judgment clause as `structural` to skip G2 is the
  inverse of routing up — same gaming, opposite direction. (The script trusts the label; a false
  one is caught only by the `needs_semantic_review` judge call, so the honesty is on you.)
- **Never ship an example-only behavioral battery.** Add the property/metamorphic backstop, or record
  why none applies — the gaps between examples are the gaming surface.
- **Never leave a G2 dimension as free-form LLM-judge prose.** Compile to per-dimension binary +
  evidence-bound program (PAJAMA), or it does not land on G2.
- **Never treat a compiled standard as load-bearing before calibrate.** `calibration_pending` until
  mutation score / agreement gates it. A standard certifies at C, not at B.
- **Never emit a G2 standard that reads the executor's session/context** (R001 isolation).
- **Never pick the check tool-first.** Principle before tool; the fitness function traces to the rule,
  not to ArchUnit's feature list. And thresholds only ratchet tighter, never loosen.

## Ratchet and compounding (evolution behind a gate)

- **Ratchet.** Fitness-function tolerances and eval_case batteries only tighten: each new fault class
  (from `failure_memory`) adds a property or a mutant the battery must now kill, and `ratchet` pulls
  the tolerance knob one notch tighter — monotone, never loosened. spec-compile re-compiles the
  affected line; calibrate re-certifies it.
- **Mutation-guided growth (ACH).** "Which fault class do I fear next?" → a mutant family → new
  assertions proven to kill them → the battery grows exactly where the next failure would have hit.

## Out of scope

- **Writing the spec** — `invariant-extract` (常驻不变量) / `donewhen-extract` (本次验收). spec-compile consumes their
  output; it does not author rules.
- **Certifying the ruler** — `calibrate`. spec-compile produces the eval_case/rubric; calibrate proves
  they bite (mutation score / agreement / holdout). Compiled is not certified.
- **Running the gate** — that is the daemon's `verify_g1` / `review_g2` runtime. spec-compile produces
  the standard the runtime runs.

## References

- `references/decidability-ladder.md` — the three lines, routing by decidability, the keyline (push
  down), altitude violations, the per-line tool table, principle-before-tool + tolerance ratchet.
- `references/behavioral-line.md` — eval_case three types (example / property-PBT / metamorphic), the
  Assured LLMSE three filters, ACH mutation-guided generation.
- `references/judgment-line.md` — analytic per-dimension rubric (binary + evidence-bound, RRD) →
  PAJAMA executable program; how the LLM-judge retires; the R001 isolation requirement on G2.
- `references/anti_patterns.md` — the mis-routing failure modes, example-only batteries, un-compiled
  rubrics, the calibrate seam, the boundary reminders.
- `assets/compile_manifest.yaml` — the named-field routing output.
- `assets/decisions_template.md` — the per-clause routing audit-trail shape.

## Exit gate for this skill itself

Verify with skillwise `evaluate-skill`. A read is not the verdict (an unguided judge is ~46% on
"which skill is better"). Scaffold tier: static structural read + one smoke run compiling a real
spec (a 常驻不变量 + a 本次验收) across the three lines. Production tier: with/without `delta_exist` on held-out specs
(does the skill route down the ladder more, and emit non-example-only batteries, vs the engine alone?)
— until such a set exists this honestly sits at `static_only`.
