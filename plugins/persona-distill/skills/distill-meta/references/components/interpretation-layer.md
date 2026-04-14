---
component: interpretation-layer
version: 0.1.0
purpose: Converts the structured output of computation-layer back into natural-language explanation in the persona's voice, routed through expression-dna so the answer sounds like the subject rather than a JSON dump.
required_for_schemas: [executor]
optional_for_schemas: []
depends_on: [expression-dna, computation-layer]
produces: []
llm_consumption: progressive
---

## Purpose

`interpretation-layer` closes the loop on the executor architecture. `computation-layer` returns a structured object — four-pillars, RSI values, drug-interaction flags, whatever — and without this component the persona's final answer would either (a) spit raw JSON at the user or (b) ask the LLM to improvise, re-opening the hallucination surface the computation was meant to close.

The component is a **template-mapping + variability-axes spec**: for each field the computation emits, one or more candidate interpretation phrases are declared, with variability axes (register, confidence-hedge, length, metaphor-density) that `expression-dna` then steers. The output is not a fixed template that reads like a fortune cookie; it is a *grammar* of phrasings that the voice layer selects from and inflects. This component is required only for the `executor` schema, because only `executor` schemas are structurally guaranteed to have a `computation-layer` to interpret.

## Extraction Prompt

**Input**: the `computation-layer` output schema (from the same persona) plus corpus of the domain expert's typical phrasings when explaining each field to a non-specialist.

**Output**: YAML block mapping each `computation_field` to an array of `interpretation_phrase` templates, with variability axes annotated.

**Prompt** (executable on corpus):

```
You are extracting the interpretation-layer for an executor persona.

STEP 1 — Load the computation-layer output schema. For every field in
  it (recursively), you must produce an interpretation entry.

STEP 2 — For each field, mine the corpus for 3-5 phrasings the subject
  uses when explaining this field (or its domain-equivalent) to a
  non-specialist. If fewer than 3 exist, mark the field
  `under_sourced: true` and use corpus-adjacent approximations.

STEP 3 — For each phrasing, annotate variability axes (values the
  runtime may pick among, steered by expression-dna):
    - register: [casual, formal, lecture]
    - confidence_hedge: [certain, probable, speculative]
    - length: [short, medium, long]
    - metaphor_density: [none, low, high]

STEP 4 — For fields where the computation returns a categorical enum,
  ensure every enum value has at least one interpretation phrase.

ANTI-EXAMPLES (reject):
  - A single template string per field (no variability) — produces
    robotic output.
  - Phrasings that leak the raw field name or JSON key into prose
    ("your four_pillars is …").
  - Interpretation that re-computes (adds new numbers not in the
    computation output) — that is hallucination, not interpretation.
```

**Few-shot example** (executor: bazi-style persona, interpreting the `day_master` field):

```yaml
- computation_field: "day_master"
  under_sourced: false
  phrases:
    - template: "你的日主是 {value}，{value_trait}"
      axes: { register: formal, confidence_hedge: certain, length: short, metaphor_density: none }
    - template: "用一句话讲，你这个人的底子偏 {value_trait} — 像 {metaphor}"
      axes: { register: casual, confidence_hedge: certain, length: medium, metaphor_density: high }
    - template: "日主 {value} 这件事不必看得太重，它只是给一个起点，不是结论"
      axes: { register: lecture, confidence_hedge: probable, length: medium, metaphor_density: low }
```

## Output Format

Generated `components/interpretation-layer.md` emits:

```markdown
# Interpretation Layer

> Converts computation-layer output → natural language in the subject's voice.
> Variability axes are selected at runtime by expression-dna.

## Field: {computation_field}
- **Under-sourced**: true | false
- **Phrases**:
  1. template: "..." — axes: { register, confidence_hedge, length, metaphor_density }
  2. template: "..." — axes: { ... }
  3. ...

## Runtime Selection Rule
Given a request, expression-dna resolves target axes → pick the phrase
whose axes match best (simple L1 distance over ordinal axes).
```

Required per field: `under_sourced` flag, ≥3 phrases (≥1 if `under_sourced: true` and flagged in validation-report).

Allowed variability: axes vocabulary may be extended per persona (e.g., add `humor_level`) but must remain a closed enumeration.

## Quality Criteria

1. **Coverage**: every field in `computation-layer.output_schema` has an interpretation entry (including enum values).
2. **Variability**: ≥3 phrases per non-under-sourced field; ≤1 allowed only with `under_sourced: true` flag.
3. **No re-computation**: interpretation templates reference only values present in the computation output — never introduce new numbers.
4. **Voice delegation**: final inflection is the responsibility of `expression-dna`; this component provides the material, not the tone.
5. **Enum completeness**: every categorical enum value has at least one phrase — prevents silent fallback to "unknown".

## Failure Modes

- **Templated robotic output**: one template per field, no axes, no variability — the whole point of routing through `expression-dna` is defeated; reads like a weather bulletin.
- **Leaking raw keys**: "your four_pillars field shows…" — JSON key names surfacing in prose indicates the producer skipped interpretation.
- **Re-computation inside templates**: adding "(roughly 3.5x baseline)" when `3.5x` is not in the computation output — hallucination masquerading as interpretation.
- **Missing enum values**: categorical output has 10 enum values but only 6 have phrases; the other 4 fall through to a fallback that breaks voice.
- **Duplicate axes with no meaningful variance**: 3 phrases that are axis-identical — fails the variability criterion.
- **Axes unknown to `expression-dna`**: using an axis like `sassiness` that `expression-dna` cannot resolve; runtime selection degrades to random.

## Borrowed From

- `jinchenma94/bazi-skill` — https://github.com/jinchenma94/bazi-skill — original source of the "Agent 解读层" half of the computation/interpretation split. `[UNVERIFIED-FROM-README]` README fragment per PRD §5 Tier 4: *"Python 计算层 + Agent 解读层分离"*.
- `gaoxin492/bazi-skill` — https://github.com/gaoxin492/bazi-skill — parallel lineage with the same split. `[UNVERIFIED-FROM-README]`.
- Variability-axes formulation is re-derived from the nuwa-skill seven-axis DNA pattern (applied here at the phrase level rather than the persona level); see `expression-dna` for the axis vocabulary this component consumes.
