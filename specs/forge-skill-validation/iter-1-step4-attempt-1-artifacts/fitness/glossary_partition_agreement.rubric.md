# Fitness criterion: the glossary in spec.md defines `@`-mention, team chat channel, deliver, DND, silence, and thread participation precisely enough that two independent reviewers produce the same partition of "in scope" vs "out of scope" mention scenarios from a shared list of 20 cases

**Source REQ(s):** REQ-001, REQ-002, REQ-003 (scope-of-membership), spec.md Glossary
**Judge:** persona-judge (manual workflow — see "How to run" below)
**Threshold:** >= 8/10

> **WARNING TO THE JUDGING AGENT:**
> Research (JudgeBench) shows naively-written rubrics drop judge accuracy
> from 55.6% (no rubric) to 42.9% (bad rubric) — 13 points worse than nothing.
> Use the structured sub-dimensions below verbatim. Do not collapse them
> into "overall impression". For every score, cite the glossary term being
> tested and a passage in `spec.md`'s Glossary section.

## How to run this rubric (no packaged automation today)

The `persona-judge` token from `done_when.yaml` is the v1 contract token
(per Appendix C of `done-when-pipeline.md`). There is no packaged
general-purpose runner for arbitrary-artifact persona judging in this
marketplace yet (the existing `persona-judge` in `persona-distill` is
scoped to persona-skill gates). So:

1. Open **two separate fresh Claude sessions** ("Reviewer A" and "Reviewer B").
2. To each, paste this rubric AND the contents of `spec.md`.
3. Ask each reviewer to classify each of the 20 scenarios in **Inputs** as
   either `in scope` or `out of scope`, citing the glossary term that
   carried the decision.
4. Open a third fresh session ("Judge"). Paste both reviewers' classifications
   plus this rubric and ask the judge to score per the sub-dimensions.
5. The agreement rate between Reviewer A and Reviewer B is the load-bearing signal.

A future `fitness-judge` runner could automate steps 1-4 — none exists yet.

## Inputs

The reviewers examine:
- `specs/forge-skill-validation/iter-1-step3-attempt-2-artifacts/spec.md`
  — Glossary section is the primary source; REQs are reference.

The reviewers must classify these **20 scenarios** as in-scope / out-of-scope:

1. Member is `@`-mentioned by name in a top-level channel they are in.
2. Member is `@`-mentioned by name in a thread they have posted in.
3. Member is `@`-mentioned by name in a thread they have NEVER posted in.
4. Member is `@`-mentioned in a top-level channel they are not a member of.
5. Member is `@here`-mentioned in a channel they are in.
6. Member is `@everyone`-mentioned in a channel they are in.
7. Member is `@channel`-mentioned in a channel they are in but currently offline.
8. Member is mentioned via a custom-keyword subscription on the word "deploy".
9. Member is the author and `@`-mentions themselves.
10. Member receives `@`-mention in a 1:1 DM with another member.
11. Member receives `@`-mention in a group DM (3+ members, no channel).
12. Member's OS has system-wide DND on; gets a channel `@`-mention.
13. Member has manual DND toggle on; gets a channel `@`-mention.
14. Member's scheduled DND window is currently active.
15. Member has muted the specific channel; gets `@`-mentioned there.
16. Member's role `@dev-team` is mentioned; member is in the role and channel.
17. Member's role is mentioned but member is not in the channel.
18. Editing a message to add a new `@`-mention.
19. Deleting a message that previously contained an `@`-mention.
20. DND deactivates while there is a backlog of silenced mentions.

## Audience archetype

**Two independent reviewers, each acting in isolation.**
- Each is a senior engineer or technical PM who reads specs for a living.
- Each is fluent in EARS conventions and glossary-driven definitions.
- Neither has prior context on this product; only spec.md is available.
- Each cares about: glossary precision, the line between "covered by this spec" vs "covered by another spec", and ambiguity in scope language.

The two reviewers must NOT communicate; they classify in parallel, then their
outputs are compared.

## Rubric

### Sub-dimension 1: reviewer-pair agreement rate (weight 0.50)

For each of the 20 scenarios, do Reviewer A and Reviewer B produce the
same in-scope/out-of-scope label?

Score 1-10 anchors:
- **10** — 19-20 out of 20 agree. The 0-1 disagreement, if any, is on a genuinely novel boundary the spec author would also flag.
- **8** — 17-18 out of 20 agree.
- **6** — 14-16 out of 20 agree.
- **4** — 10-13 out of 20 agree (the glossary is leaky on majority of cases).
- **1** — Fewer than 10 agree. Glossary is unreliable.

Report: exact count of agreed labels, list each disagreement, and which glossary
term each reviewer cited.

### Sub-dimension 2: glossary term sufficiency (weight 0.25)

For each scenario, can the reviewer point to a single glossary term that
decides the case (rather than chaining 2+ glossary terms + an EARS REQ)?

Score 1-10 anchors:
- **10** — Every scenario is decided by a single glossary term, named verbatim in `spec.md`.
- **7** — 16-19 scenarios decided by a single glossary term; 1-4 require a glossary term + a REQ reference.
- **4** — Half the scenarios force the reviewer to chain glossary + REQ + Non-goals inference.
- **1** — The glossary is decorative; the REQs do all the work; the reviewer rarely cites the glossary.

Cite: for each scenario, the single (or multiple) glossary terms each reviewer used.

### Sub-dimension 3: out-of-scope completeness (weight 0.15)

Are the out-of-scope cases (1:1 DM, group DM, custom keyword, OS-level DND, role
mention of non-member) ALL named explicitly in the spec?

Score 1-10 anchors:
- **10** — All 5 explicit-out-of-scope cases are named verbatim either in `Non-goals` (proposal.md) or `Glossary` exclusions.
- **7** — 3-4 of 5 are named explicitly; the others are inferable from a glossary exclusion phrase ("Excludes 1:1 DMs and group DMs").
- **4** — Only 1-2 are explicit; the rest force inference.
- **1** — Out-of-scope is unnamed; reviewers will draw the line in different places.

Cite the exact passages.

### Sub-dimension 4: dual-form definitions for DND-arm union (weight 0.10)

The DND glossary entry defines DND as a union of three conditions (manual toggle,
schedule window, channel mute). Are scenarios 12-15 (each testing one arm)
unambiguously classifiable?

Score 1-10 anchors:
- **10** — Each of the three arms is named with the exact condition; scenario 12 (OS-level DND) is explicitly excluded; scenarios 13-15 each map to one arm.
- **7** — Three arms are present but one boundary is sloppy (e.g. "scheduled window" without saying inclusive/exclusive endpoints).
- **4** — DND is defined as a single condition without enumerating arms; scenarios 13-15 are ambiguous.
- **1** — DND is undefined or vaguely defined; scenarios 13-15 will produce reviewer disagreement.

Cite the DND glossary entry text.

## Aggregation

Final score = (agreement_rate × 0.50) + (glossary_sufficiency × 0.25) + (oos_completeness × 0.15) + (dnd_arms × 0.10)

Express as `X.X / 10` (one decimal).

## Pass/fail

Pass if:
- final score >= 8.0/10, AND
- no sub-dimension scored below 5, AND
- sub-dimension 1 (reviewer-pair agreement) achieved ≥ 17/20 raw agreement count
  (this is the load-bearing measurement of the criterion).

## Re-run policy

If first scoring lands within ±0.5 of threshold, run the rubric a second time
on the revised `spec.md` with two NEW reviewer sessions (do not reuse the
same Claude conversations) and require the score to NOT decrease before
declaring pass.

## Note on persona-judge runner availability

`judge: persona-judge` is the v1 contract token (Appendix C). The existing
`persona-judge` skill in `persona-distill` is scoped to distilled-persona
quality gates and **cannot** be pointed at this rubric today. Use the
manual three-fresh-sessions workflow described in "How to run" until a
general-purpose runner ships.
