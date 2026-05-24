# Fitness rubric guide

> **Bad rubrics actively hurt LLM-judge accuracy.**
> Published evidence: on JudgeBench, naively-generated rubrics dropped GPT-4o's
> accuracy from **55.6% (no rubric) to 42.9% (bad rubric)** — 13 points worse than nothing.
> A rubric that you "just wrote" is more likely in the second bucket than the first.

That is why this skill puts fitness rubrics at the bottom of the priority order. Reach for them only when there is genuinely no programmatic alternative.

When you do have to write one, follow the rules below.

---

## Honest scope note (please read first)

Schema v1 (Appendix C of `done-when-pipeline.md`) sets the `judge:` enum to `persona-judge | programmatic | manual`. The token `persona-judge` is the LLM-as-judge path in the contract.

There is an important real-world caveat here: the `persona-judge` skill that exists today in the `persona-distill` plugin was built to evaluate **distilled persona skills** (e.g. `steve-jobs-mirror`) — it expects a persona-skill root directory as input and emits a 12-dimension validation report on that skill. It **cannot** be pointed at arbitrary artifacts (README, code, API reference) and asked to score them against a custom rubric.

So the rubric files this skill produces are **not auto-consumed by the existing `persona-judge` skill today**. They are designed for the "Claude-with-rubric inline" pattern documented below — a fresh Claude session driven manually by the developer. A dedicated `fitness-judge` runner (or a generalised mode of `persona-judge`) that automates this is a natural follow-up, but it does not exist yet — do not let your generated output imply otherwise.

The `judge:` value in `done_when.yaml` still stays `persona-judge` (that is the v1 contract token); only the **runner** is currently manual.

---

## When a fitness rubric is the right tool

Use a rubric **only** for criteria like:

- "Could an independent engineer use this API given only the README, without follow-up questions?" (Claude approximates "fresh engineer")
- "Does the help-center article read clearly to a non-technical user?" (Claude approximates "lay reader")
- "Does the generated UI feel consistent with the rest of the product?" (genuinely subjective; cannot be mechanically checked)

Do **not** use a rubric for things like:

- "Code runs without errors." — that's a programmatic check (run it).
- "Function returns within 200ms." — that's a programmatic check (time it).
- "Test coverage ≥ 80%." — programmatic.
- "API response matches schema." — programmatic (JSON schema validator).

If the criterion can be checked programmatically *at all*, push it back to `behavior:` in `done_when.yaml`, not `fitness:`.

---

## Rubric design rules

### 1. Concrete anchors, not vague scales

**Bad:**
```
Rate documentation clarity 1-10.
```

**Good:**
```
Rate documentation clarity:
  10 — A new engineer can read once and start using; every concept is defined before use; every example runs as-is.
   7 — Mostly clear but contains 1-2 paragraphs where the reader has to re-read; one example needs trivial adjustment to run.
   4 — Reader must hunt for prerequisites scattered across sections; examples partially work.
   1 — Reader cannot proceed without consulting external sources; examples don't run.
```

Every score must have a concrete anchor describing what *that score means in terms a different judge would converge on*.

### 2. Split into 3-7 sub-dimensions, then aggregate

A single "overall quality 1-10" is essentially random. Decompose:

```
For "README usability":
  - completeness  (1-10, anchors below)
  - accuracy      (1-10, anchors below)
  - runnable_examples (1-10, anchors below)
  - tone_appropriate_for_audience (1-10, anchors below)

Aggregate: weighted mean (completeness × 0.3 + accuracy × 0.3 + runnable × 0.3 + tone × 0.1)
```

Sub-dimensions are easier for the judge to anchor on. The aggregation is mechanical.

### 3. Force the judge to cite evidence

Every score the judge produces must reference a specific section / line / paragraph of the artifact. "I gave it a 7 because the second example uses `subscription.cancel()` but the API reference says `subscription.terminate()`" is a citation; "I gave it a 7 because it feels okay" is not.

### 4. Two-pass review

If a first scoring lands within ±0.5 of threshold, run the judge a second time on the revised artifact and require the score to *not* decrease before declaring pass. This catches the regression case where addressing one weakness opens another.

### 5. Name the **audience archetype**, not a fictitious persona

The earlier draft of this guide referenced persona names like `integration-engineer-persona`, `non-technical-end-user-persona`, `oncall-sre-persona` and suggested loading them from the `persona-distill` library. None of those personas exist in `persona-distill` — they were invented during drafting. Do not write rubric files that depend on a persona-distill library you cannot point at.

Instead, describe the **audience archetype inline**, in the rubric file itself, in 3-5 lines. Examples:

```markdown
**Audience archetype: integration engineer**
- 5+ years writing API clients in some language.
- Reads docs once-through, then runs an example.
- Will not file an issue if confused; will silently move on.
- Cares about: completeness of error-response examples, idempotency clarity, auth flow precision.
```

```markdown
**Audience archetype: non-technical end user**
- Does not know JSON, does not know what a status code is.
- Expects plain-English instructions in task-oriented sections ("how do I cancel").
- Cares about: clarity of consequences (will I lose data?), reassurance on common worries.
```

This is *self-contained* — Claude reading the rubric file has everything it needs in front of it, no external library required.

---

## The "Claude-with-rubric inline" pattern

Since there is no packaged automation today, the rubric file is consumed by a *human-driven, manually-initiated* Claude session:

1. The user opens a fresh Claude session (or starts a new conversation thread). This isolates the judge from the implementer's context.
2. The user pastes the rubric file in.
3. The user provides paths (or contents) of the artifacts to be scored.
4. Claude scores per the structured sub-dimensions, citing evidence.
5. The user reads the score, decides pass/fail per threshold.

The rubric file should explicitly call out this expected workflow at the top, so a human dropping into it cold knows what to do.

A future `fitness-judge` skill could automate steps 1-4. None exists yet.

---

## Template for a `fitness/<criterion>.rubric.md` file

```markdown
# Fitness criterion: <one-line description>

**Source REQ(s):** <REQ-IDs from done_when.yaml>
**Judge:** persona-judge (see ../README.md for the manual workflow; v1 contract token, runner is currently manual)
**Threshold:** <e.g. ">= 8.0/10">

> **WARNING TO THE JUDGING AGENT:**
> Research shows naively-written rubrics *hurt* judgment accuracy compared to
> no rubric at all (JudgeBench: 55.6% → 42.9%). Follow the structured
> sub-dimensions below; do not collapse them into "overall impression".
> Cite passages for every score.

## How to run this rubric

This file is consumed by a fresh Claude session (no implementer context).
The human invokes it as:
> "Open this rubric, read these artifact paths, produce a score per the rubric. Cite evidence."

## Inputs

The judge examines:
- `<path/to/README.md>`
- `<path/to/api-reference>`
- `<other relevant artifacts>`

## Audience archetype

<3-5 lines describing who the judge should simulate. Self-contained — no
reference to any external persona library.>

## Rubric

### Sub-dimension 1: <name>  (weight: 0.3)

Score 1-10 with these anchors:
- **10** — <very concrete>
- **7** — <concrete>
- **4** — <concrete>
- **1** — <concrete>

The judge must cite at least one passage from the inputs supporting the score.

### Sub-dimension 2: <name>  (weight: 0.3)
...

### Sub-dimension N: <name>  (weight: ...)
...

## Aggregation

Final score = Σ (sub-dimension_score × weight)

## Pass/fail

Pass if final score >= threshold AND no sub-dimension scored below 5.

The second clause prevents one strong dimension from masking a glaring weakness.
```

---

## When fitness rubrics fail

If a fitness criterion repeatedly comes in below threshold despite implementer fixes:

- Re-examine the rubric. Are the anchors crisp? Is the audience archetype tight?
- If the rubric is solid, the issue is the artifact — escalate to the human, do not loop forever.
- If the rubric is mushy, this is **also** a kind of spec drift — the criterion was too soft to begin with. Push it back to acceptance-spec for refinement.

The `spec_drift_threshold` field in `done_when.yaml` applies here too — as a hint to the user, not as auto-enforcement (see INTEGRATION.md).
