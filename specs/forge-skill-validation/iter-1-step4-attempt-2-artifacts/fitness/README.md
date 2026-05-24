# Fitness criteria (channel-mention-notifications)

Two `judge: persona-judge` rubrics live here, derived from
`done_when.yaml.fitness:`. Per schema v1 (Appendix C of
`done-when-pipeline.md`), `persona-judge` is the LLM-as-judge contract
token. **The runner today is manual** — see "How to run" in each rubric
file.

## Files

| File | Criterion (verbatim from done_when.yaml) | Threshold |
|---|---|---|
| `oncall_engineer_edge_case_prediction.rubric.md` | An independent on-call engineer can read `spec.md` alone and correctly predict, for ten hand-crafted edge-case mention scenarios, whether a notification fires and on which surfaces — without asking clarifying questions. | `>= 8/10` |
| `glossary_partition_agreement.rubric.md` | The glossary in `spec.md` defines `@`-mention, team chat channel, deliver, DND, silence, and thread participation precisely enough that two independent reviewers produce the same partition of "in scope" vs "out of scope" mention scenarios from a shared list of 20 cases. | `>= 8/10` |

## How rubric files are consumed (today)

There is **no packaged auto-runner** for arbitrary-artifact persona
judging in this marketplace. The `persona-judge` skill in
`persona-distill` was built for evaluating distilled persona skills, not
this kind of spec-clarity check. So:

1. Open a fresh Claude session (separate from any implementer context).
2. Paste the rubric file in.
3. Provide the artifact paths (`spec.md`, etc.) listed in the rubric's
   "Inputs" section.
4. Ask Claude to score per the sub-dimensions, citing evidence.
5. Compare aggregated score to threshold; record pass/fail.

The contract token `persona-judge` stays in `done_when.yaml` regardless
of whether automation lands — it is the v1 schema token.

## Why no `judge: programmatic` entries

Both criteria above are about **comprehension** — whether a fresh reader
can correctly predict system behavior, and whether two independent
readers agree on the partition. Comprehension cannot be checked by
running a script; it inherently needs a judging agent. This is precisely
the narrow band where rubric-based judging is the right tool.

## Why no `judge: manual` entries

Both criteria are evaluable by a sufficiently-skilled judging agent
given the right rubric. No tacit human-only judgment is involved.

## Why no `judge: llm-rubric` entries

`llm-rubric` is a legacy value from earlier drafts of this skill. Schema
v1 (Appendix C) uses `persona-judge` as the LLM-as-judge token. The
generator rejects `llm-rubric` and asks the user to regenerate the
contract via `/acceptance-spec`.
