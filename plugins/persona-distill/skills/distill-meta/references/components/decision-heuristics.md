---
component: decision-heuristics
version: 0.1.0
purpose: 5-10 IF-THEN rules distilled from decisions the persona actually made, each citing a source case and a confidence level, for use by public-mirror and mentor schemas at runtime.
required_for_schemas: [public-mirror, mentor]
optional_for_schemas: []
depends_on: [identity, mental-models]
produces: []
llm_consumption: eager
---

## Purpose

Mental models explain *how the persona thinks*; decision heuristics encode *what the persona does under pressure*. The two are distinct: a model without a heuristic is a lecture, a heuristic without a model is a superstition. Together, they let the runtime answer "given constraints X, what would the persona actually pick?" with a traceable rule rather than a generative guess.

This component is where persona-distill's density discipline bites hardest: shallow rules ("IF problem is hard THEN think harder") are the most common failure mode and must be filtered aggressively.

## Extraction Prompt

**Input**: Persona's decision corpus — letters, memos, interview passages where the persona narrates a specific choice, biographical reconstructions of named decisions. For `mentor`, one-on-one transcripts where the persona advises a specific call.

**Procedure** (LLM executes):

1. Enumerate **named decisions**: events where the persona chose A over B with stated stakes. Candidate threshold: ≥2 corpus references to the same decision.
2. For each named decision, attempt to recover the implicit rule the persona applied.
3. Rewrite the rule as `IF <condition> THEN <action>`. The condition must be observable (not "IF important"), the action must be executable (not "think carefully").
4. Record the **source case** (the named decision the rule came from) and a **confidence** (high = rule appears in ≥3 decisions; medium = ≥2; low = 1 but strongly articulated).
5. Apply the dilution filter: any rule that reduces to "正确废话" / platitude under paraphrase is REMOVED, regardless of source.
6. Cap total at 10; prefer 5-7 validated over 10 thin.

**Output schema per heuristic**:

```yaml
- rule_id: dh-NN
  if: <observable condition>
  then: <executable action>
  source_case: <named decision>
  supporting_cases: [<named decision>, ...]
  confidence: high | medium | low
  linked_model: <mental-models id>   # optional cross-ref
```

**Anti-examples (REMOVE)**:
- `IF problem is hard THEN think more carefully` — tautological.
- `IF facing difficulty THEN persist` — platitude.
- `IF people disagree THEN listen to all sides` — not persona-specific.

## Output Format

The generated `decision-framework.md` in the produced skill contains:

1. **Frontmatter** with `produced_for` fingerprint.
2. **`## Heuristics`** — ordered by confidence descending; each rule rendered as a block with IF / THEN / source / supporting / confidence / linked model.
3. **`## Conflicts`** — known cases where two heuristics fire on the same input; persona's historical tiebreaker noted.
4. **`## Not Heuristics`** — 2-3 explicit non-rules: things users commonly assume the persona does but the corpus doesn't support. Feeds `honest-boundaries`.

## Quality Criteria

1. **Count discipline** — total ∈ [5, 10].
2. **Observability of condition** — every `if` can be evaluated by the runtime without additional interpretation; grep for vague predicates ("important", "right", "hard") as a smoke test.
3. **Executability of action** — every `then` names a specific move the runtime or user can take.
4. **Source-case traceability** — every rule names a real decision from the corpus; rules with fabricated or unnamed sources are rejected.
5. **Non-triviality** — at least 60% of heuristics are ones a non-persona-expert would not have guessed; tested by asking persona-judge to predict rules before reading them.

## Failure Modes

- **正确废话 / platitudes**: rules that would apply to any reasonable actor. Density-classifier flags DILUTE or REMOVE depending on severity. Common culprits: "listen before speaking", "measure twice cut once", "focus on fundamentals".
- **Condition vagueness**: `IF the situation is risky` — unevaluable. Rewrite from source case or drop.
- **Action abstraction**: `THEN proceed with care` — not executable. Rewrite to the concrete move the persona made.
- **Over-specification**: `IF Tuesday AND quarterly review AND team > 12` — a single case pretending to be a rule. Demote to a case study; not a heuristic.
- **Model collapse**: heuristic restates a mental model without adding a rule. Merge with `mental-models` instead of double-counting.
- **Confidence inflation**: marking every rule `high`; persona-judge checks the distribution and penalizes unrealistic uniformity.

## Borrowed From

- `alchaincyf/nuwa-skill` — https://github.com/alchaincyf/nuwa-skill [UNVERIFIED-FROM-README]
  > Quoted from PRD §6: *"认知 OS 架构、三重验证、七轴 DNA"* — nuwa's Phase-2 extraction treats decision rules as first-class alongside mental models; we inherit the structural separation and the 5-10 count guidance.
- `leilei926524-tech/anti-distill` — https://github.com/leilei926524-tech/anti-distill [UNVERIFIED-FROM-README]
  > Quoted from PRD §6: *"4 级密度分类器（SAFE/DILUTE/REMOVE/MASK）、稀释策略"* — we reuse the 4-level classifier to aggressively cull platitudinous rules. We do not adopt the dilution strategy itself (anti-distill is adversarial; we're constructive).

## Examples

```yaml
- rule_id: dh-02
  if: a new hire in month 1 ships something that breaks a prod invariant
  then: debrief with them same day; keep them on the project; do not add review gates
  source_case: "2017 payments outage, engineer E"
  supporting_cases: ["2019 onboarding cohort L", "2022 contractor onboarding"]
  confidence: high
  linked_model: mm-04
```
