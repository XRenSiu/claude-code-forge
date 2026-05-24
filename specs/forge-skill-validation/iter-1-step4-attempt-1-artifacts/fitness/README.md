# Fitness rubrics — channel-mention-notifications

This directory holds the soft-criteria gates from `done_when.yaml.fitness:`.

Both criteria in `done_when.yaml` use `judge: persona-judge`, so both
emit `.rubric.md` files consumed by the **manual fresh-Claude-session
workflow** (see the rubric files for the exact steps). There is no
packaged auto-runner today — the `persona-judge` skill that ships in
`persona-distill` evaluates distilled-persona skills, not arbitrary
artifacts.

## Files

| File | Source criterion (excerpt) | Threshold |
|---|---|---|
| `oncall_engineer_edge_case_prediction.rubric.md` | on-call engineer can predict 10 edge cases from `spec.md` alone | ≥ 8/10 |
| `glossary_partition_agreement.rubric.md` | two reviewers partition 20 cases the same way using the glossary | ≥ 8/10 |

## How to consume

1. **Programmatic files** — there are none in this batch (both criteria are
   persona-judge).
2. **Rubric files** — open a fresh Claude session, paste the rubric, paste the
   artifact (`spec.md`), follow the "How to run" block in the file.
3. **Manual checklists** — there are none in this batch.

## Hard warning

A naively-written rubric *hurts* judge accuracy (research: JudgeBench, GPT-4o
accuracy 55.6% → 42.9% with bad rubric). Both rubrics here use concrete
anchors per sub-dimension and force evidence citations. If you find yourself
asking the judge for "an overall impression", you are NOT using the rubric;
stop and re-read the structured sub-dimensions.

## When a rubric repeatedly fails

If a criterion comes in below 8/10 across multiple iterations despite
implementer fixes:

- Re-examine the rubric anchors — are they crisp enough?
- If the rubric is solid, the artifact (`spec.md`) is the issue —
  escalate to a human; do not loop forever.
- If the rubric itself is mushy, push the criterion back to `acceptance-spec`
  for refinement — this is a form of spec drift.

The `spec_drift_threshold.max_fix_loops_before_escalation: 3` field in
`done_when.yaml` is the relevant hint (ratchet does not auto-read it; see
INTEGRATION.md if chained).
