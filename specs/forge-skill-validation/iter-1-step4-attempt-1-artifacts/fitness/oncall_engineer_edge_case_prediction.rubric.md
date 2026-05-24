# Fitness criterion: an independent on-call engineer can read spec.md alone and correctly predict, for ten hand-crafted edge-case mention scenarios (non-member, self, edit-add, delete-before-open, in-thread non-participant, DND active, DND end with backlog, broadcast under DND, role mention, custom keyword), whether a notification fires and on which surfaces — without asking clarifying questions

**Source REQ(s):** REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007
**Judge:** persona-judge (manual workflow — see "How to run" below)
**Threshold:** >= 8/10

> **WARNING TO THE JUDGING AGENT:**
> Research (JudgeBench) shows naively-written rubrics drop judge accuracy
> from 55.6% (no rubric) to 42.9% (bad rubric) — 13 points worse than nothing.
> Use the structured sub-dimensions below verbatim. Do not collapse them
> into "overall impression". Cite a specific REQ ID and a passage from
> spec.md for every score.

## How to run this rubric (no packaged automation today)

The `persona-judge` token from `done_when.yaml` is the v1 contract token
(per Appendix C of `done-when-pipeline.md`). However, the `persona-judge`
skill that exists today in the `persona-distill` plugin was built to
evaluate distilled persona skills, not arbitrary artifacts. There is no
packaged general-purpose runner for arbitrary-artifact persona judging
in this marketplace yet. So:

1. Open a **fresh Claude session** (separate from any implementer context).
2. Paste this rubric file in full.
3. Provide the path or contents of `spec.md`.
4. For each of the 10 scenarios listed below in **Inputs**, ask Claude
   (acting as the persona) to predict: (a) does any surface fire? (b) which
   surfaces? Claude must answer using **only** `spec.md` — no clarifying
   questions are allowed.
5. Score per the sub-dimensions, citing the REQ each prediction was derived from.
6. Apply aggregation and the pass rule.
7. Record the verdict in your dev log.

A future `fitness-judge` runner could automate steps 1-5 — none exists yet.

## Inputs

The judge examines:
- `specs/forge-skill-validation/iter-1-step3-attempt-2-artifacts/spec.md`
  — the only allowed reference text. The judge is NOT allowed to read
  `done_when.yaml`, `proposal.md`, or any source code.

The judge must predict (fire? / which surfaces?) for each of these
10 scenarios — these are the scenarios in the criterion text:

1. **non-member** — User X is @-mentioned in a channel they are not a member of.
2. **self** — Member M is the author and @-mentions themselves.
3. **edit-add** — A previously-sent message is edited to add @-mention of new member N.
4. **delete-before-open** — Member M is mentioned, message is deleted before M opens the banner.
5. **in-thread non-participant** — Member M is @-mentioned in a thread M has never posted in.
6. **DND active (manual toggle)** — Member M has manual DND on; gets @-mentioned in a channel they belong to.
7. **DND end with backlog** — M was in DND, accumulated 3 silenced mentions; DND turns off — what (if anything) fires?
8. **broadcast under DND** — Channel does `@channel`; M is in DND.
9. **role mention** — `@dev-team` is mentioned; M is a member of @dev-team and of the channel.
10. **custom keyword** — Someone says "deploy" and M has a custom-keyword subscription to "deploy" — out of scope per glossary.

## Audience archetype

**On-call engineer who has just been paged about notifications.**
- 5+ years backend engineering experience; familiar with chat systems but new to this product.
- Reads the spec once-through (≤10 minutes), then must act on it under time pressure.
- Will not ping the spec author with clarifying questions — there is no spec author at 3am.
- Cares about: precision on edge cases, internal consistency, clear "in scope" / "out of scope" boundaries, glossary clarity.
- Treats ambiguity as a defect that makes the spec unusable for triage.

## Rubric

### Sub-dimension 1: prediction accuracy (weight 0.40)

For each of the 10 scenarios, can the engineer arrive at the correct answer using
only `spec.md`? "Correct" = matches the contract (which the judge does not see,
so this dimension is implicitly measured by the next two).

Score 1-10 anchors:
- **10** — All 10 scenarios are derivable from a single REQ + glossary; no scenario forces the engineer to combine three or more REQs in a non-obvious way; no scenario forces a guess.
- **7** — 8-9 scenarios are derivable cleanly; 1-2 require chaining 2 REQs but the chain is signposted (e.g. the spec explicitly says "REQ-005 applies REQ-001 …").
- **4** — 5-7 scenarios are derivable; the rest require guesses or merge-conflict-style cross-references.
- **1** — Half or more scenarios force a guess. The engineer would have to ask the spec author or read code.

Cite for every scenario: which REQ(s) / glossary entries the prediction came from.

### Sub-dimension 2: surface-set determinism (weight 0.25)

For "fires? which surfaces?" questions, is the spec precise about which of
(push, in-app banner, sound, unread badge, unread count) fire?

Score 1-10 anchors:
- **10** — Every "fires" / "silenced" / "retracted" / "no-op" outcome maps to an enumerated, named surface set. The glossary defines `silence` and `deliver` with the exact surface lists.
- **7** — The general case is enumerated; one edge case (e.g. unread count vs unread badge) is implicit but inferrable.
- **4** — The engineer can tell IF a surface fires but not exactly WHICH ones; has to guess between (push, banner) vs. (push, banner, sound).
- **1** — "Notifies the user" appears without specifying surfaces; engineer must look at code.

Cite at least one passage that defines `silence` and at least one that defines `deliver`.

### Sub-dimension 3: in-scope / out-of-scope clarity (weight 0.20)

For scenario 10 (custom-keyword) and similar "is this even in scope?" questions,
does the spec make scope decisive?

Score 1-10 anchors:
- **10** — Custom keywords, 1:1 DMs, group DMs, OS-level DND, retroactive resurfacing — all explicitly named as out of scope in `Non-goals` or glossary. The engineer is never left wondering "does this case apply?".
- **7** — Most scope boundaries are explicit; one boundary (e.g. group DMs) is only implied via "team chat channel" definition.
- **4** — Several "is this in scope?" questions require inference from the glossary; engineer might draw the line in the wrong place.
- **1** — Scope is left implicit; engineer would guess differently from the spec author.

Cite the glossary entries (or `Non-goals`/`Constraint` clauses) that establish scope for each edge case.

### Sub-dimension 4: cross-REQ chaining cost (weight 0.15)

Some scenarios (edit-add, DND-end-with-backlog) require chaining 2-3 REQs.
Is the chaining explicit (e.g. "REQ-005 applies REQ-001 to the newly-mentioned member"),
or does the engineer have to infer it?

Score 1-10 anchors:
- **10** — Every multi-REQ scenario has an explicit pointer in the spec (e.g. "and where applicable REQ-002 / REQ-003").
- **7** — Chaining is explicit in 2-3 places; 1-2 chains are left implicit but flow naturally.
- **4** — Chaining is only implicit; the engineer must hold all 7 REQs in their head simultaneously.
- **1** — No cross-references; the spec reads like 7 standalone REQs that don't interact.

Cite the cross-references in spec.md (e.g. REQ-005's "AND SHALL apply REQ-001 …").

## Aggregation

Final score = (accuracy × 0.40) + (surface_determinism × 0.25) + (scope_clarity × 0.20) + (chaining × 0.15)

Express as `X.X / 10` (one decimal).

## Pass/fail

Pass if:
- final score >= 8.0/10, AND
- no sub-dimension scored below 5.

The second clause prevents one strong dimension from masking a glaring weakness
(e.g. a beautifully-precise surface set still does not help an engineer who
can't tell which REQ applies).

## Re-run policy

If first scoring lands within ±0.5 of threshold, run the rubric a second time
on the revised `spec.md` and require the score to NOT decrease before declaring
pass. This catches the regression case where addressing one weakness opens another.

## Note on persona-judge runner availability

`judge: persona-judge` is the v1 contract token (Appendix C). The existing
`persona-judge` skill in `persona-distill` is scoped to distilled-persona
quality gates and **cannot** be pointed at this rubric today. Use the
manual fresh-Claude-session workflow described in "How to run" until a
general-purpose runner ships.
