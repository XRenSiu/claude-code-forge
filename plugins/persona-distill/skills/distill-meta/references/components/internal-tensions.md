---
component: internal-tensions
version: 0.1.0
purpose: ≥2 unresolved internal contradictions — pairs of genuine statements the persona has made that conflict — preserved as tensions the persona actively holds rather than smoothed into a consistent avatar.
required_for_schemas: [public-mirror]
optional_for_schemas: [mentor]
depends_on: [identity, mental-models]
produces: []
llm_consumption: eager
---

## Purpose

The single biggest failure of persona skills is flattening: the produced skill becomes a consistent, agreeable, legible version of the original and loses the fault lines that made the original interesting. `internal-tensions` is the explicit counter-measure. It stores unresolved contradictions so that the runtime can refuse to smooth them — when a user pushes on a known tension, the skill must hold both sides, not pick one.

A tension presented as *resolved* (with a synthesis) defeats the entire purpose of this component. If the extractor found a synthesis, that's a mental model, not a tension.

## Extraction Prompt

**Input**: Persona's corpus across years. Longer time-spans are better; tensions often emerge when statements from different decades are juxtaposed.

**Procedure** (LLM executes):

1. Enumerate **strong claims**: passages where the persona makes a clear normative or predictive statement.
2. Cluster claims by topic.
3. Within each topic cluster, search for **genuine contradictions**: two claims that cannot both be true under a reasonable reading, both of which the persona has asserted.
4. For each contradiction, check whether the persona *later synthesized* the two. If synthesized, remove from this component (the synthesis belongs in `mental-models`).
5. Keep only tensions the persona continues to hold — tensions they move between depending on context, or tensions they acknowledge but refuse to resolve.
6. Require ≥2 such tensions; target 2-5.
7. For each tension, describe **how they hold both** — the contextual pattern under which side A is voiced vs side B.

**Output schema per tension**:

```yaml
- tension_id: it-NN
  topic: <short phrase>
  statement_a:
    claim: "<direct quote or tight paraphrase>"
    source: <corpus item>
    year: <YYYY>
  statement_b:
    claim: "<direct quote or tight paraphrase>"
    source: <corpus item>
    year: <YYYY>
  context_pattern: <when A surfaces vs when B surfaces>
  refusal_to_resolve: <evidence that persona resists synthesis, or `implicit`>
```

**Anti-example**: `statement_a: "hard work matters", statement_b: "luck matters", context_pattern: "both can be true"` — not a genuine contradiction, trivially reconciled; REMOVE.

## Output Format

The generated `internal-tensions.md` in the produced skill contains:

1. **Frontmatter** with `produced_for` fingerprint.
2. **`## Tensions`** — one H3 per tension, each displaying the two claims side-by-side (not synthesized) followed by the context pattern.
3. **`## Runtime Directive`** — a short prose block instructing the runtime: "when a user's question touches topic X, voice both sides. Do not collapse." Literal instruction, deliberately blunt.
4. **`## Tensions Excluded`** — optional: candidates the extractor considered but rejected (with reason), so persona-judge can audit filter decisions.

## Quality Criteria

1. **Unresolved integrity** — 0% of tensions are accompanied by a synthesis statement; persona-judge greps for "reconciled", "actually both", "turned out to be" as smoke signals.
2. **Claim directness** — both statements are direct quotes or tight paraphrases sourced to specific corpus items; no paraphrase chains.
3. **Temporal or contextual split** — `context_pattern` names observable conditions (time of life, audience, stakes); empty `context_pattern` is a REMOVE.
4. **Count floor** — ≥2 tensions; persona-mirror schemas fall below the floor only if persona-judge also flags "insufficient corpus for tension extraction".
5. **Non-triviality** — a reviewer cannot collapse the pair under charitable reading; tested by asking persona-judge to attempt reconciliation.

## Failure Modes

- **Resolved-tension smuggling**: the extractor writes "these look contradictory but actually the persona means…" — defeats the component. REMOVE and re-extract with stricter resolution-detector.
- **Trivial oppositions**: "sometimes bold, sometimes cautious" — context-dependent behavior, not a tension. Tensions require *claims*, not *moods*.
- **Single-source pseudo-tension**: both statements drawn from the same interview, possibly rhetorical hedging. Require cross-source pairs (different year or different venue).
- **Over-synthesis in `context_pattern`**: the pattern field subtly reconciles the two statements ("A in youth, B in maturity — same truth, different lens"). The pattern should describe *when each surfaces*, not argue they're the same.
- **Namedropped tensions**: importing tensions from biographical commentary rather than the persona's own words. Only primary-source contradictions count.

## Borrowed From

- `alchaincyf/nuwa-skill` — https://github.com/alchaincyf/nuwa-skill [UNVERIFIED-FROM-README]
  > Quoted from PRD §6: *"认知 OS 架构、三重验证、七轴 DNA、6 agent 并行、质量验证"* — nuwa explicitly includes an "internal contradictions" extraction as a load-bearing layer of the public-mirror blueprint. We treat it as required for public-mirror (not optional) because empirical nuwa outputs demonstrate it is the single most common missing piece when a skill feels flattened.
- Golden sample: `taleb-skill` https://github.com/alchaincyf/taleb-skill [UNVERIFIED-FROM-README] — target density exemplar (multiple publicly-held tensions around risk, scholarship, professional bodies).

## Examples

```markdown
### Tension it-01: The role of formal education

Statement A (1997 commencement address): "the four years I spent here were the foundation of everything I've built since."

Statement B (2011 podcast): "if I could redo my twenties I'd skip the degree and spend the tuition on five years of mistakes."

Context pattern: A surfaces when addressing students or institutions directly; B surfaces in reflective interviews with entrepreneurs.

Refusal to resolve: in a 2018 Q&A, persona was asked directly to reconcile and replied "both are true; stop asking me to pick."
```
