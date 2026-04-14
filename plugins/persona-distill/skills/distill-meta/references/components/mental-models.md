---
component: mental-models
version: 0.1.0
purpose: 3-7 persona-specific mental models, each validated by the nuwa-skill triple-validation protocol (formulation + 3 independent corpus citations + 1 counter-example).
required_for_schemas: [public-mirror, mentor]
optional_for_schemas: []
depends_on: [identity]
produces: []
llm_consumption: eager
---

## Purpose

A mental model is not a named framework the persona happens to know — it is a reusable pattern of reasoning the persona visibly applies across unrelated topics. `mental-models` captures 3-7 such patterns in the persona's *own framing*, each defended with triple validation so that the produced skill doesn't parrot generic phrases like "first-principles thinking" without the persona-specific variant.

For `public-mirror` these are the levers a questioner can pull to ask "how would X think about Y?". For `mentor` they are the abstractions behind the heuristics emitted in `decision-heuristics`.

## Extraction Prompt

**Input**: Persona corpus — books, talks, long-form interviews, tweets, letters. For mentor schema, one-on-one transcripts. Redacted if private.

**Procedure** (LLM executes), per `references/extraction/triple-validation.md`:

1. Scan corpus for candidate mental models: reasoning moves the persona applies to ≥3 different topics.
2. For each candidate, attempt triple validation:
   - **Formulation**: one paragraph, using the persona's own vocabulary where possible. Must name the model and state its mechanism in ≤80 words.
   - **Three citations from distinct sources**: three independent corpus items (different book, different interview, different year), each containing the model in action. Not three quotes from the same chapter.
   - **One counter-example**: a case in the corpus where the persona *declined* to apply the model, or where applying it led the persona to revise. Counter-examples defend against overfitting.
3. If any leg of the triple fails, drop the candidate or escalate to Phase 2.5 iterative deepening.
4. Cap at 7 models total; prefer fewer-and-validated over more-and-thin.

**Output schema per model**:

```yaml
- model_id: mm-NN
  name: <persona's own label if available, else distilled>
  formulation: <one paragraph ≤80 words>
  citations:
    - source: <book / talk / tweet / transcript>
      year: <YYYY>
      passage: "<short quote or locator>"
    - source: ...
    - source: ...
  counter_example:
    source: <where persona declined or revised>
    note: <what the counter-example teaches>
```

**Anti-example**: `name: "First Principles Thinking", formulation: "breaking problems to fundamentals"` — generic framework, no persona-specific framing, citations missing.

## Output Format

The generated `mental-models.md` in the produced skill contains:

1. **Frontmatter** with `produced_for` fingerprint.
2. **`## Models`** — one H3 per model, body includes formulation paragraph, three citations as a nested list, and the counter-example.
3. **`## Applicability Map`** — a table pairing each model with 2-3 question types it fits (helps runtime routing).
4. **`## Out-of-Scope Notes`** — 1-3 explicit statements of where these models stop working, linked to `honest-boundaries`.

## Quality Criteria

1. **Triple validation integrity** — every model has exactly 3 citations from distinct sources and exactly 1 counter-example; persona-judge counts these.
2. **Persona-specific framing** — every model uses at least one phrase lifted from the corpus; generic framework names alone fail.
3. **Cross-topic applicability** — citations span ≥2 distinct subject domains, demonstrating the model is a reasoning pattern not a topic claim.
4. **Counter-example substance** — counter-example is a real corpus instance, not a hypothetical "this wouldn't work if…". Grep-checkable via `source`.
5. **Ceiling discipline** — total count ∈ [3, 7]; violations are auto-flagged.

## Failure Modes

- **Generic-framework padding**: models named "first-principles", "second-order effects", "inversion" with no persona-specific variant. Density-classifier flags as DILUTE; the frameworks are famous, but the *persona's use* of them needs distillation.
- **Mono-source citations**: three citations all from the same book chapter or interview. Fails triple validation; REMOVE unless extended corpus can supply two more distinct sources.
- **Missing counter-example**: extractor skipped the counter-example because "no contradictions found". This almost always means insufficient corpus scan; escalate to Phase 2.5.
- **Topic-as-model confusion**: a recurring *subject* (e.g., "the importance of energy markets") mis-emitted as a mental model. Test: can it be applied outside its topic? If no, REMOVE.
- **Overcounting**: 10+ models emitted because extractor didn't compress. Each additional model past 7 dilutes the others' retrievability; REMOVE the lowest-confidence ones.

## Borrowed From

- `alchaincyf/nuwa-skill` — https://github.com/alchaincyf/nuwa-skill [UNVERIFIED-FROM-README]
  > Quoted from PRD §6: *"认知 OS 架构、三重验证、七轴 DNA、6 agent 并行、质量验证"* — triple validation is the load-bearing protocol we inherit here. See `references/extraction/triple-validation.md` for the canonical 3-citation + 1-counter-example procedure.
- Golden samples (Tier 3, PRD §10): `steve-jobs-skill` https://github.com/alchaincyf/steve-jobs-skill and `munger-skill` https://github.com/alchaincyf/munger-skill [UNVERIFIED-FROM-README] — used as target-density exemplars; 6 mental models each with full triple validation.

## Examples

```markdown
### Model mm-03: "The product is the argument"

Formulation: When asked to justify a decision, the persona consistently reframes the question as "what will the shipped product itself prove?" — postponing verbal justification until the artifact can carry it. This is not demo-driven culture in the generic sense; the persona specifically refuses written memos as the locus of persuasion.

Citations:
  - 2018 biography, ch. 7, "memo rejected, prototype accepted"
  - 2021 podcast transcript at 34:12
  - 2015 all-hands, leaked transcript

Counter-example:
  - 2019 regulatory filing: persona did write a 40-page memo. Note: counter-example reveals the model's boundary — regulators aren't audiences the product can argue to.
```
