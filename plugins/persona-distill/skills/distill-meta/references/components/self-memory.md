---
component: self-memory
version: 0.1.0
purpose: First-person dated memory bank anchoring the `self` schema in lived experience — decisions, emotional peaks, and relationship shifts extracted from the user's own corpus.
required_for_schemas: [self]
optional_for_schemas: []
depends_on: [identity]
produces: []
llm_consumption: progressive
---

## Purpose

`self-memory` is the autobiographical substrate of a `self` persona skill. Where `persona-5layer` encodes *how* the user reacts and `expression-dna` encodes *how* the user speaks, `self-memory` encodes *what actually happened* — the anchor points a self-reconstructed agent can cite when asked "why do you handle X this way?"

Without this component, a `self` skill collapses into stylized self-description. With it, the skill can ground reactions in concrete, dated episodes and resist hallucinated personal history.

## Extraction Prompt

**Input**: User's chat history (WeChat / QQ / iMessage export), journals, decision records, social-media posts — already redacted by `distill-collector`.

**Procedure** (LLM executes):

1. Walk the corpus chronologically. For each window of ~200 messages, ask:
   - Is there a **decision point** (user changed plan, committed, refused)?
   - Is there an **emotional peak** (first-person language intensity > baseline)?
   - Is there a **relationship shift** (new person introduced, existing relationship renegotiated, a relationship ended)?
2. For every positive hit, emit one memory entry in the schema below.
3. Never fabricate a date — if the corpus item is undated, write `date: unknown` and keep only if the event is causally linked to a dated entry.
4. Redact third-party names to `friend_A`, `colleague_B`, `family_01` etc., reusing the same alias across entries.

**Output schema per entry**:

```yaml
- date: YYYY-MM-DD | unknown
  event: <one-sentence first-person description>
  emotional_valence: [-5..+5]       # -5 crisis, 0 neutral, +5 peak joy
  who_else_involved: [<alias>...]
  causal_link: <optional: prior entry id this explains>
  corpus_citation: <opaque source id from collector>
```

**Few-shot positive**: `date: 2022-03-14, event: "Quit consulting job after 4-hour argument with friend_A about my own autonomy", emotional_valence: -3, who_else_involved: [friend_A], causal_link: mem-031`.

**Anti-example**: `event: "Had a bad day", emotional_valence: -2` — no specificity, no participants, no causal hook.

## Output Format

The generated `self-memory.md` file inside the produced persona skill contains:

1. **Frontmatter** — carrying `produced_for: <manifest fingerprint>`, and the component metadata (minus extraction-only fields).
2. **`## Timeline`** — memories in chronological order, grouped by year. Each entry uses the YAML schema above rendered as a compact bullet.
3. **`## Themes`** — 3-7 recurring motifs the extractor surfaced (e.g., *"retreats from conflict by travelling"*), each with pointers to 2+ entries.
4. **`## Open Threads`** — events whose significance the corpus hints at but does not resolve (flagged for `correction-layer` follow-up).

Target volume: 30-80 entries for a year of dense chat corpus; denser is not automatically better (see Failure Modes).

## Quality Criteria

1. **Citation density** — ≥90% of entries carry a non-empty `corpus_citation`.
2. **Emotional range** — valence distribution is not bimodal collapse; std dev ≥ 1.5 across the set.
3. **Causal coverage** — ≥30% of entries carry a `causal_link`, meaning the corpus narrates a chain, not just disconnected moments.
4. **Participant diversity** — ≥3 distinct `who_else_involved` aliases across the full timeline.
5. **Anonymization integrity** — persona-judge spot-checks 10 entries; zero raw PII should remain.

## Failure Modes

- **Diary-without-markers**: entries read like a diary (one event per day) but none carry emotional valence or causal links. Downstream layers can't *use* the memory for reasoning — it becomes decorative. Density-classifier flags as DILUTE.
- **Melodramatic compression**: every entry is valence ±4/±5. Indicates the extractor is over-weighting emotionally loaded corpus windows and ignoring the everyday. REMOVE the most extreme third and resample.
- **Orphan entries**: 80%+ of entries have no `causal_link` and no shared `who_else_involved`. Indicates the corpus is too thin or the extractor failed to thread episodes. Surface to `correction-layer` as an open question.
- **Pseudo-first-person**: entries written in third person ("The user quit...") or summarized ("During that period, several decisions...") — violates the first-person contract and breaks runtime voice consistency.

## Borrowed From

- `notdog1998/yourself-skill` — https://github.com/notdog1998/yourself-skill [UNVERIFIED-FROM-README]
  > Quoted from PRD §6: *"自我蒸馏的双层（self + persona）、WeChat/QQ parser"* — we adopt the self-layer memory component and the chat parser expectations; we do not adopt the specific two-layer runtime flow (we decompose into `self-memory` + `persona-5layer` + `expression-dna`).

## Examples

```yaml
- date: 2023-07-02
  event: "Told family_01 I wouldn't come home for the holiday; sat with the silence for three days."
  emotional_valence: -2
  who_else_involved: [family_01]
  causal_link: mem-014
  corpus_citation: wechat-2023-07-02-evening
```

```yaml
- date: 2024-11-18
  event: "Shipped the side-project I'd kept secret for 8 months; friend_A was the first to see it."
  emotional_valence: +4
  who_else_involved: [friend_A]
  causal_link: null
  corpus_citation: imessage-2024-11-18-morning
```
