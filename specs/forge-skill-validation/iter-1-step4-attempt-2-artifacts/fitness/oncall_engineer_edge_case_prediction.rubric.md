# Fitness criterion: an independent on-call engineer can read spec.md alone and correctly predict, for ten hand-crafted edge-case mention scenarios (non-member, self, edit-add, delete-before-open, in-thread non-participant, DND active, DND end with backlog, broadcast under DND, role mention, custom keyword), whether a notification fires and on which surfaces — without asking clarifying questions

**Source REQ(s):** REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007
**Judge:** `persona-judge` — v1 contract token; runner today is the manual fresh-Claude-session workflow described under "How to run".
**Threshold:** `>= 8/10` (verbatim from `done_when.yaml.fitness[0].score_threshold`)

> **WARNING TO THE JUDGING AGENT:**
> Research (JudgeBench, 2024) shows naively-written rubrics drop judge
> accuracy from **55.6% to 42.9%** — worse than no rubric. Use the structured
> sub-dimensions below verbatim. Do not collapse them into "overall
> impression". Cite a passage from `spec.md` (REQ number + line/quote) for
> every score.

## How to run this rubric

No packaged auto-runner exists today (the existing `persona-judge` skill in
`persona-distill` is scoped to distilled-persona quality gates, not arbitrary
artifacts). Run manually:

1. Open a fresh Claude session, separate from the implementer's context.
2. Paste this rubric file.
3. Paste in (or provide the path to) `spec.md`.
4. Use the **ten scenarios** below as the test set. For each, the judge
   produces (a) predicted behavior, (b) the REQ-IDs in `spec.md` that drove
   the prediction. Score per the sub-dimensions.
5. Aggregate. Compare to threshold. Record pass/fail in your dev log.

A general-purpose `fitness-judge` runner that automates this is potential
future work in this plugin; the `judge:` token stays `persona-judge`
regardless.

## Inputs

The judge examines:

- `specs/forge-skill-validation/iter-1-step3-attempt-2-artifacts/spec.md`
  — the EARS spec, including the glossary.

The judge does **not** read `done_when.yaml`, the test files, or any
implementation source code — the whole point is "can a fresh on-call
engineer predict behavior from the spec alone".

## Audience archetype

**Audience archetype: on-call platform engineer**

- 5+ years operating multi-tenant chat / messaging / collaboration
  infrastructure.
- Reads spec docs once-through, then forms predictions; will silently move
  on if confused (does not file clarifying questions during a page).
- Cares about: precise scope boundaries, explicit treatment of edge cases,
  unambiguous mapping from event → surface set, and no implicit ordering
  assumptions.
- Is comfortable reading EARS-style sentences but will not "guess" what
  WHEN/IF/WHILE means if the spec is ambiguous about, e.g., broadcast
  under DND.

## The ten scenarios (apply each to the spec)

For each scenario, the judge predicts:
- whether a notification fires (yes / no),
- on which of the four surfaces (push / in-app banner / sound / unread
  badge),
- which REQ(s) in `spec.md` ground the prediction.

| # | Scenario | Expected (from spec) |
|---|---|---|
| 1 | A user mentions `@OtherUser` in a top-level channel; OtherUser is a member, not in DND. | fires; all four surfaces (REQ-001). |
| 2 | A user mentions `@OtherUser` in a channel OtherUser is **not** a member of. | no notification; no error to mentioner (REQ-003). |
| 3 | A user mentions themselves (`@self`) in a channel. | no notification (REQ-004). |
| 4 | A user edits a message originally mentioning only `@A` to also mention `@B`. B was not previously mentioned. | fresh mention dispatched to B only (REQ-005). |
| 5 | A user deletes their `@OtherUser` message before OtherUser opens any notification. | in-app banner retracted; push & unread badge unchanged (REQ-006). |
| 6 | In a thread, a user mentions `@C` who has **never** posted in that thread. | silently skipped (REQ-001 thread-scope constraint). |
| 7 | While `@A` is in DND (manual toggle on), a user mentions `@A`. | push / banner / sound silenced; unread badge & count still increment (REQ-002 + glossary `silence`). |
| 8 | `@A` exits DND with 5 mentions accumulated during DND. | no retroactive push / banner / sound; pre-existing unread badge & count remain (REQ-007). |
| 9 | A user posts `@channel` in a channel where `@B` has DND on. | B's push / banner / sound silenced; B's badge increments (REQ-002 extension — broadcast does not override DND). |
| 10 | A user mentions `@role:engineers` in a channel where the role expands to {A, B}; A is a member, B is not. | A gets full surface set; B is silently skipped (REQ-001 + REQ-003 composition). |

The 11th scenario "custom keyword" in the criterion text is intentionally
**out of scope** per the glossary (`@`-mention excludes custom-keyword
subscriptions). A correct prediction is "spec excludes this".

## Rubric

### Sub-dimension 1: predictive accuracy (weight 0.40)

How many of the 10 scenarios did the engineer-archetype predict correctly
(both fire/no-fire AND the correct surface set)?

Score 1-10 with these anchors:
- **10** — 10/10 scenarios correct, citing the right REQ-ID for each.
- **8**  — 9/10 correct.
- **6**  — 7-8/10 correct.
- **4**  — 5-6/10 correct.
- **2**  — 3-4/10 correct.
- **1**  — ≤ 2/10 correct.

The judge must cite the REQ-ID and a verbatim sentence from `spec.md` for
each prediction.

### Sub-dimension 2: REQ→scenario traceability (weight 0.20)

For each predicted answer, did the engineer cite a specific REQ in
`spec.md` (not "I just inferred") that grounds the prediction?

- **10** — every prediction has a REQ-ID + a verbatim quote.
- **7**  — REQ-IDs present for ≥ 8/10 scenarios; quotes for ≥ 5.
- **4**  — REQ-IDs present for ≤ 6/10 scenarios; few or no quotes.
- **1**  — predictions made "from intuition" with no REQ citation.

### Sub-dimension 3: confidence calibration (weight 0.20)

Where the spec is ambiguous, did the engineer flag the ambiguity (rather
than confabulate an answer)? Where the spec is unambiguous, did they
answer with confidence?

- **10** — flags all genuinely ambiguous cases; answers all unambiguous
            cases with confidence.
- **7**  — one over-confidence or one false-flag.
- **4**  — confuses ambiguous and unambiguous cases multiple times.
- **1**  — uniformly confident or uniformly hedging across all cases.

The judge must cite which scenarios were flagged and why.

### Sub-dimension 4: no-questions-needed proxy (weight 0.20)

In the role-play, did the engineer succeed in predicting all 10 scenarios
**without asking clarifying questions** of the spec author? The criterion
text says "without asking clarifying questions" — this dimension measures
that directly.

- **10** — engineer produces all 10 predictions without requesting any
            clarification.
- **7**  — engineer notes uncertainty inline but still produces all 10
            predictions; does not block on questions.
- **4**  — engineer blocks on 1-2 clarifications before predicting.
- **1**  — engineer blocks on > 2 clarifications, or refuses to predict
            multiple scenarios without more spec.

## Aggregation

Final score = 0.40 × accuracy + 0.20 × traceability + 0.20 × calibration
            + 0.20 × no-questions-needed
            (each on the 1-10 scale)

## Pass/fail

Pass if:
- final score ≥ **8.0**
- AND no sub-dimension scored below **5**.

The second clause prevents a strong accuracy score from masking a weak
calibration / traceability score (which would defeat the criterion's
"can the engineer use the spec alone" intent).

## Re-run policy

If first scoring lands within ±0.5 of threshold (i.e. 7.5–8.5), the spec
author revises the spec and the rubric is run a second time. The score
on the second run must **not decrease** before declaring pass — this
catches the regression case where addressing one weakness opens another.
