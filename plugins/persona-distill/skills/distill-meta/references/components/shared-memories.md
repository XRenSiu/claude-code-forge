---
component: shared-memories
version: 0.1.0
purpose: Dated memories shared between the user and the target persona, stored in first-person-plural voice ("we/us") so the produced skill can reference a joint history rather than simulate one side.
required_for_schemas: [loved-one, friend]
optional_for_schemas: []
depends_on: [identity]
produces: []
llm_consumption: progressive
---

## Purpose

Where `self-memory` is autobiographical ("I did X"), `shared-memories` is *relational* ("we did X"). The component exists so a `loved-one` or `friend` persona skill can speak about a shared past without either (a) hallucinating events or (b) collapsing the relationship to the user's private perspective.

Pronoun discipline is load-bearing: the component is useless if entries default to "you said…" or "I remember when I…". Every retained entry must legitimately take *we/us* as its grammatical subject.

## Extraction Prompt

**Input**: Two-party chat history between user and target (WeChat / iMessage / SMS / email threads), optionally augmented with photo captions or shared documents — all redacted by `distill-collector`.

**Procedure** (LLM executes):

1. For each dated conversation window, identify **joint events**: events both parties reference, events they planned together, moments where the two-party chat itself is the event (long goodnights, fights, reconciliations).
2. Reject any window where only one side speaks meaningfully — those belong in `self-memory`, not here.
3. For `loved-one` schema, emit 50+ entries when corpus permits; for `friend` schema, emit 10-30 entries (lightweight variant — friendships don't need the same archival density as intimate relationships).
4. Rewrite each entry with *we/us* as subject. If an entry cannot be rewritten naturally in first-person plural, drop it.
5. Include at least one direct quote (2-15 words) per entry, drawn from either party, redacted of third-party PII.

**Output schema per entry**:

```yaml
- date: YYYY-MM-DD | unknown
  event: <first-person-plural sentence using "we" or "us">
  setting: <location / channel / occasion>
  quoted_fragment: "<short quote from corpus>"
  quoted_by: user | target
  emotional_valence: [-5..+5]       # joint, not the user's alone
  corpus_citation: <opaque source id>
```

**Anti-example**: `event: "I told them about my promotion"` — single-sided, does not belong in shared-memories.

## Output Format

The generated `memories.md` inside the produced skill contains:

1. **Frontmatter** with `produced_for` fingerprint.
2. **`## Timeline`** — entries by year then month; entries rendered as bullets with the YAML fields visible.
3. **`## Recurring Places / Rituals`** — 2-5 locations or patterns that appear in ≥3 entries.
4. **`## Unfinished`** — entries referencing unresolved events (promises, plans, arguments that never closed) — these feed into `correction-layer` and `emotional-patterns` (for `loved-one`).

Friend-schema variant omits `## Unfinished` by default.

## Quality Criteria

1. **Pronoun compliance** — 100% of entries have *we/us/our* as subject or primary object. Grep-testable.
2. **Dual-voice coverage** — across all entries, `quoted_by` is split at least 30/70 between user and target; neither side dominates.
3. **Temporal spread** — entries cover ≥60% of the months available in the corpus; no bunching in a single crisis window.
4. **Specificity floor** — each `setting` is concrete (named place / named occasion), not generic ("at home", "during chat").
5. **Redaction parity** — third-party names aliased consistently with `self-memory` (shared alias registry).

## Failure Modes

- **Monologue smuggling**: entries read as "we talked about how I was feeling" — user's inner state narrated through a plural pronoun. Flag DILUTE; rewrite or drop.
- **Greatest-hits bias**: only anniversaries / fights / breakups survive. Loses texture of mundane co-presence that makes the persona feel real.
- **Quote drought**: `quoted_fragment` is often empty or reused across entries. Skill will sound invented at runtime.
- **Inflation for loved-one**: padding to reach 50+ by duplicating low-information entries; density-classifier catches this as DILUTE.
- **Starvation for friend**: dropping below 10 entries because the corpus is short — better to emit a honest-boundaries note than to fabricate.

## Borrowed From

- `titanwings/ex-skill` — https://github.com/titanwings/ex-skill [UNVERIFIED-FROM-README]
  > Quoted from PRD §6: *"6 层人格、memories + persona、星盘/MBTI/依恋集成"* — we take the `memories` component and its pairing with the persona layer; we do not take astrology / MBTI integration.
- `perkfly/ex-skill` — https://github.com/perkfly/ex-skill [UNVERIFIED-FROM-README]
  > Quoted from PRD §6: *"memories + persona 5 层 + iMessage/SMS"* — confirms the memories component is schema-independent of the layer count, letting us reuse it for both `loved-one` (6-layer) and `friend` (5-layer).

## Examples

```yaml
- date: 2022-06-11
  event: "We spent the whole train ride back arguing about whether to move cities; neither of us slept."
  setting: G7 high-speed train, 22:00-06:00
  quoted_fragment: "if we don't decide by Sunday we're deciding by default"
  quoted_by: target
  emotional_valence: -3
  corpus_citation: wechat-2022-06-11-overnight
```
