# Fitness criterion: the glossary in spec.md defines `@`-mention, team chat channel, deliver, DND, silence, and thread participation precisely enough that two independent reviewers produce the same partition of "in scope" vs "out of scope" mention scenarios from a shared list of 20 cases

**Source REQ(s):** REQ-001, REQ-002, REQ-003, REQ-005, REQ-006 (glossary terms span the spec)
**Judge:** `persona-judge` — v1 contract token; runner today is the manual fresh-Claude-session workflow described under "How to run".
**Threshold:** `>= 8/10` (verbatim from `done_when.yaml.fitness[1].score_threshold`)

> **WARNING TO THE JUDGING AGENT:**
> Research (JudgeBench, 2024) shows naively-written rubrics drop judge
> accuracy from **55.6% to 42.9%** — worse than no rubric. Use the structured
> sub-dimensions below verbatim. Do not collapse them into "overall
> impression". Cite a passage from the glossary section of `spec.md` for
> every score.

## How to run this rubric

No packaged auto-runner exists today. Run manually:

1. Open **two** fresh Claude sessions (different conversation threads),
   playing the role of Reviewer A and Reviewer B.
2. In each session independently, paste the rubric file and the glossary
   section of `spec.md`.
3. Ask each reviewer to partition the 20 cases below into "in scope" /
   "out of scope" for the mention-notification system, using only the
   glossary text.
4. In a third session, the **judge**, compare the two partitions and score
   per the sub-dimensions.

The judge does **not** read the EARS REQs themselves, only the
**glossary** — the criterion is about glossary precision, not REQ
completeness.

## Inputs

The judge examines:

- `specs/forge-skill-validation/iter-1-step3-attempt-2-artifacts/spec.md`,
  but only the section starting at `## Glossary`.
- The two Reviewer A / Reviewer B partition outputs.

## Audience archetype

**Audience archetype: senior product / spec reviewer**

- 5+ years owning specs for cross-cutting platform features.
- Treats the glossary as the contract — if a term is fuzzy, scope is
  fuzzy.
- Cares about: precise inclusion/exclusion clauses, no implicit
  precedence (which definition wins when terms overlap), term
  consistency across the spec.
- Will NOT use REQ text to clarify a glossary entry — the glossary must
  stand alone.

## The 20 partition cases (Reviewers A and B each score independently)

| # | Case | Hint at correct answer (judge keeps hidden until reviewers submit) |
|---|---|---|
| 1 | `@OtherUser` in a top-level channel | IN — individual mention in team chat channel |
| 2 | `@OtherUser` in a 1:1 DM | OUT — DM excluded from "team chat channel" |
| 3 | `@OtherUser` in a group DM | OUT — group DM excluded |
| 4 | `@here` in a top-level channel | IN — broadcast mention is `@`-mention |
| 5 | `@channel` in a top-level channel | IN |
| 6 | `@everyone` in a top-level channel | IN |
| 7 | `@role:engineers` in a channel | IN — role/group mention is `@`-mention |
| 8 | "important" custom keyword subscription | OUT — explicitly excluded from `@`-mention |
| 9 | `@OtherUser` in a thread, OtherUser has posted in the thread | IN |
| 10 | `@OtherUser` in a thread, OtherUser has never posted in the thread | OUT (silent skip — but is the *case* in scope? Per glossary it's "in scope", silently-skipped behavior is the REQ's job) — **trap case** |
| 11 | A mention in an archived channel | not addressed by glossary → **ambiguous** |
| 12 | Mention via API (no UI involved) | not addressed by glossary → **ambiguous** |
| 13 | `@OtherUser` while OtherUser is OS-DND but not app-DND | OUT of DND glossary (OS-level explicitly excluded) |
| 14 | `@OtherUser` while OtherUser has manually toggled DND | IN of DND glossary |
| 15 | `@OtherUser` while current time is inside their scheduled DND window | IN of DND glossary |
| 16 | `@OtherUser` while their per-channel mute for the mention's channel is on | IN of DND glossary |
| 17 | Delivery via the in-app banner only (push, sound, badge failed) | IN of "deliver" — success = ≥ 1 surface |
| 18 | Delivery via no surface (all four failed) | OUT — not delivered |
| 19 | A mention sent to a member who has not yet "participated in" the thread but is a member of the parent channel | OUT of thread-participation eligibility (per the term "thread participation: having sent at least one message") |
| 20 | A mention edited in (REQ-005) — is the edit-added mention "an `@`-mention" by the glossary? | IN — the glossary definition does not depend on whether the mention was original or edit-added |

Cases 11 and 12 are intentionally **not addressed** by the glossary —
the correct reviewer behavior is to flag them as ambiguous, not to
invent a partition.

## Rubric

### Sub-dimension 1: partition agreement (weight 0.50)

Of the 20 cases, on how many do Reviewer A and Reviewer B agree
(in / out / ambiguous)?

Score 1-10 with these anchors:
- **10** — 20/20 agreement.
- **8**  — 18-19/20 agreement.
- **6**  — 16-17/20 agreement.
- **4**  — 14-15/20 agreement.
- **2**  — 12-13/20 agreement.
- **1**  — ≤ 11/20 agreement.

The judge must cite the disagreement cases and the glossary phrase each
reviewer relied on.

### Sub-dimension 2: ambiguity flagging (weight 0.20)

Did both reviewers flag cases 11 and 12 (and any other genuinely
glossary-ambiguous case) as ambiguous, rather than confabulating an
answer?

- **10** — both reviewers flagged 11, 12, and no false-flags on
            unambiguous cases.
- **7**  — one reviewer confabulated on 11 or 12 (gave a partition
            answer); the other flagged.
- **4**  — both reviewers confabulated on 11 or 12.
- **1**  — both reviewers confabulated AND introduced false flags on
            clearly-defined cases.

### Sub-dimension 3: term-by-term coverage (weight 0.20)

The criterion text names six specific terms: `@`-mention, team chat
channel, deliver, DND, silence, thread participation. Does the glossary
define each precisely enough to drive a non-trivial partition?

- **10** — every term has a definition that resolves at least one of
            the 20 cases unambiguously.
- **7**  — 4-5 of the 6 terms do; 1-2 are too vague to resolve any
            case.
- **4**  — 3 or fewer terms are usable.
- **1**  — glossary is decorative; reviewers cannot cite it for any
            partition.

### Sub-dimension 4: no precedence ambiguity (weight 0.10)

When two glossary terms overlap on a case (e.g. case 16 invokes both
"team chat channel" and "DND"), does the glossary make the precedence
clear?

- **10** — every overlap is resolved by the glossary text itself.
- **7**  — at most one overlap requires reviewer inference.
- **4**  — multiple overlaps require inference; reviewers diverge as
            a result.
- **1**  — overlaps dominate; the glossary is internally unclear.

## Aggregation

Final score = 0.50 × partition_agreement + 0.20 × ambiguity_flagging
            + 0.20 × term_coverage + 0.10 × no_precedence_ambiguity
            (each on the 1-10 scale)

## Pass/fail

Pass if:
- final score ≥ **8.0**
- AND no sub-dimension scored below **5**.

## Re-run policy

If first scoring lands within ±0.5 of threshold, the spec author revises
the glossary. The rubric is then run a second time with new fresh
sessions (the original reviewers' answers are not re-used). The score
must not decrease on the second run before declaring pass.
