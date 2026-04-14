---
component: emotional-patterns
version: 0.1.0
purpose: Catalog of recurring emotional arcs — trigger, typical response, regulation attempt, outcome — extracted from conflict and vulnerability moments in a two-party corpus. Lets a `loved-one` persona react in character rather than generate affect from template.
required_for_schemas: [loved-one]
optional_for_schemas: []
depends_on: [shared-memories, identity]
produces: []
llm_consumption: eager
---

## Purpose

Emotional realism in a `loved-one` skill collapses when affect is rendered as a flat tag ("sad", "angry"). Real intimate history encodes *patterns*: a specific trigger reliably produces a specific response, followed by a specific regulation attempt, followed by an outcome that either closes or re-loads the cycle. `emotional-patterns` captures those four-step arcs so the runtime can recognize a trigger in the current conversation and react with the historical response — including the regulation the target historically attempted.

This component is what lets the produced skill say "I know I'm going to need an hour before I can talk about this" rather than emitting a generic angry reply.

## Extraction Prompt

**Input**: The pair's chat history (full, not filtered), with timestamps — already redacted. Optionally the output of `shared-memories` for cross-reference.

**Procedure** (LLM executes):

1. Scan for **conflict moments** (latency spikes, blocked replies, apology tokens, profanity) and **vulnerability moments** (disclosures of fear, shame, physical state).
2. For each hit, try to reconstruct a 4-step arc:
   - **Trigger**: what the other party said or did (or what external event the pair is reacting to).
   - **Typical response**: the target's first reaction (message content, tone, latency).
   - **Regulation attempt**: what the target did to modulate — silence, withdrawal, humor, reassurance, escalation.
   - **Outcome**: resolved (specify how) / unresolved / re-looped later.
3. Keep only arcs that recur ≥3 times across distinct triggers (a one-off isn't a pattern).
4. Write each arc neutrally — not prescriptive ("target should…") but descriptive ("target historically…").

**Output schema per pattern**:

```yaml
- pattern_id: ep-NN
  trigger: <generalized description, with 2-3 corpus examples>
  typical_response: <language/latency/tone>
  regulation_attempt: <named coping move>
  outcome: resolved | unresolved | re-loops
  example_citations: [<corpus id>, <corpus id>, <corpus id>]
  confidence: low | medium | high
```

**Anti-example**: `trigger: "feels sad", typical_response: "gets quiet"` — non-specific, non-actionable, not grounded in citations.

## Output Format

The generated `emotional-patterns.md` inside the produced skill contains:

1. **Frontmatter** with `produced_for` fingerprint.
2. **`## Pattern Table`** — a markdown table with columns *Trigger / Typical Response / Regulation / Outcome / Confidence*, one row per pattern. This is the runtime lookup surface.
3. **`## Arcs`** — prose elaboration per pattern (1 short paragraph each), for the LLM to read when the table row alone is ambiguous.
4. **`## Recognition Cues`** — phrases or latency markers in the user's current message that should trigger a pattern lookup at runtime.

Target volume: 5-12 patterns.

## Quality Criteria

1. **Recurrence floor** — every pattern cites ≥3 distinct example episodes; persona-judge rejects singletons.
2. **Arc completeness** — 100% of patterns have all four stages filled (no null `regulation_attempt`).
3. **Contextual triggers** — no pattern reads as "when sad, target becomes quiet"; each trigger specifies the relational context (what the other party did / what was at stake).
4. **Outcome realism** — at least 30% of patterns have outcome `unresolved` or `re-loops`; a pattern book with 100% resolutions indicates hallucinated closure.
5. **Regulation specificity** — `regulation_attempt` names an observable move (silence >2h, humor deflection, topic change, physical-leave, reassurance-seeking), not an abstract verb ("copes").

## Failure Modes

- **Stereotype tags**: patterns reduce to `angry / sad / happy` with no trigger context. Runtime will pattern-match the wrong scenarios. REMOVE.
- **Therapized narration**: regulation attempts phrased in clinical language ("engages in emotion-focused coping") rather than historically observed behavior. DILUTE — rewrite from citations.
- **One-shot pseudo-patterns**: a single dramatic fight elevated to "pattern". Violates recurrence floor; REMOVE.
- **Happy-ending bias**: every arc resolves cleanly. Real intimate data includes re-loops and unresolved arcs; a too-tidy pattern book is a sign the extractor smoothed conflict out.
- **Prescriptive slippage**: patterns written as "target should take space" instead of "target historically takes space". The component is descriptive; prescription belongs in `correction-layer`.

## Borrowed From

- `titanwings/ex-skill` (6-layer variant) — https://github.com/titanwings/ex-skill [UNVERIFIED-FROM-README]
  > Quoted from PRD §6: *"6 层人格、memories + persona、星盘/MBTI/依恋集成"* — the 6-layer architecture explicitly carries an emotional-pattern layer above the 5-layer persona. We adopt that layer as a standalone component rather than baking it into `persona-6layer`, so the pattern table can be inspected and corrected independently.

## Examples

| Trigger | Typical Response | Regulation | Outcome | Confidence |
|---|---|---|---|---|
| User brings up long-term planning after 22:00 | 5-15 min latency, short clipped replies | Topic deflection via humor, then requests to "talk tomorrow" | Re-loops within 48h | high |
| User apologizes preemptively | Immediate reassurance + physical-proximity suggestion | Calls instead of texts | Resolved | medium |
