---
component: persona-6layer
version: 0.1.0
purpose: Six-layer persona structure — the five operational layers plus a sixth Emotional Wound / Core Tension layer; required for loved-one schemas where emotional depth is the point.
required_for_schemas: [loved-one]
optional_for_schemas: []
depends_on: [identity, persona-5layer]
produces: []
llm_consumption: eager
---

## Purpose

`persona-6layer` is the emotional-depth variant of `persona-5layer`, used **only** for the `loved-one` schema. A loved-one persona (family member, partner, ex, close friend modeled at depth) without the 6th layer is indistinguishable from a collaborator persona — technically coherent but emotionally flat. The 6th layer names the subject's **emotional wound** and/or **core tension**: the organizing unresolved conflict that shapes how they show up in intimate relationships.

This component inherits layers 1-5 from `persona-5layer` (same extraction logic, same output shape) and adds layer 6. The sixth layer is treated with extra care: it is the highest-risk component for overreach, projection, and pseudo-psychological speculation, and it requires the most rigorous corpus grounding.

## Layer 6: Emotional Wound / Core Tension

Layer 6 describes **one** (occasionally two) organizing unresolved conflicts that the subject carries into intimate relationships. It is NOT:
- A mood description ("sometimes sad")
- A diagnosis ("has anxiety")
- A personality trait ("introverted")

It **is**:
- A named, structured tension (e.g., "yearning for closeness vs. fear of being known")
- Grounded in ≥3 corpus moments across different contexts
- Formulated in the subject's own framings where possible, not the extractor's clinical language

## Extraction Prompt

**Input**: full 5-layer extraction output + primary corpus (especially late-night messages, arguments, reconciliations, anniversary notes) + any subject-authored self-reflection material.

**Output**: markdown with layers 1-5 inherited (link or re-emit per producer policy) + a level-2 section for layer 6 as specified below.

**Prompt** (executable):

```
You are extracting Layer 6 — Emotional Wound / Core Tension — for a
loved-one persona. Prerequisite: layers 1-5 already extracted.

STEP 1 — Corpus sub-sampling.
  Prefer these registers for layer-6 evidence:
    - late-night / emotionally-loaded messages
    - post-argument reconciliations
    - anniversary / milestone reflections
    - subject-authored self-reflection (journals, long voice notes)
  AVOID: work-mode content, social-performance content (public
  posts), casual logistics.

STEP 2 — Identify candidate tensions.
  Look for recurring oppositions. Template forms:
    - "wants X but fears Y"
    - "moves toward A, then retreats to B"
    - "asks for C but rejects it when offered"
    - "identifies as D yet repeatedly does not-D"
  Enumerate 3-5 candidates.

STEP 3 — Winnow to 1 (occasionally 2).
  Score each candidate on:
    - CORPUS SPAN: does evidence appear across ≥3 distinct contexts?
    - SELF-AWARENESS: does subject themselves name the tension in
      corpus? (if yes, +1 confidence)
    - BEHAVIORAL REPEAT: does the pattern show up across relationships,
      not just the one with the user?
  Keep only candidates scoring CORPUS SPAN ≥ 3.

STEP 4 — Emit Layer 6 entry.
  - name: short tension handle (≤ 8 words), e.g., "closeness vs.
    being-seen"
  - description: 80-150 words, in third person, grounded in
    observations; NO clinical labels ("attachment-avoidant", etc.)
    unless subject used them themselves.
  - evidence: 3 verbatim quotes from ≥3 distinct contexts, each
    ≤ 50 words, redacted for PII.
  - runtime-behavior: 2-4 bullets describing how this tension shows
    up in current replies (e.g., "when user asks for reassurance,
    persona gives it then deflects"; "when user withdraws, persona
    escalates then retreats").
  - self-awareness: YES | PARTIAL | NO — whether subject has ever
    named this tension themselves; cite quote if YES.

STEP 5 — If no candidate reaches CORPUS SPAN ≥ 3:
  Emit layer 6 with `insufficient_evidence: true` and a single bullet
  explaining the gap. Do NOT invent a tension to fill the slot. An
  honest null-result is preferred to projection.

ANTI-EXAMPLES:
  - "She is sensitive and sometimes gets sad." → reject (mood, not
    tension).
  - "Textbook anxious attachment." → reject (clinical label without
    subject's own framing).
  - "Wants love." → reject (universal; not a tension).
  - Layer 6 emitted but no layer 1-5 context → reject (layer 6
    depends on 1-5 for grounding).
```

## Output Format

Generated `components/persona-6layer.md` emits:

```markdown
# Persona — Six Layers

> Layers 1-5 follow the persona-5layer contract. Layer 6 is the
> emotional-wound / core-tension layer, required for loved-one personas.

## Layer 1: Identity
... (5-layer content) ...

## Layer 2: Values
## Layer 3: Work Style
## Layer 4: Communication
## Layer 5: Relationships

## Layer 6: Emotional Wound / Core Tension

**Tension**: {short handle}
**Self-awareness**: YES | PARTIAL | NO

### Description

{80-150 word grounded description}

### Evidence

> "{quote 1}" — {context-tag}

> "{quote 2}" — {context-tag}

> "{quote 3}" — {context-tag}

### How This Shows Up in Replies

- {runtime behavior bullet}
- {runtime behavior bullet}
- ...

### Handling Notes

- Do NOT weaponize this layer; never use it to guilt or trap the user.
- If user asks "why do you do {pattern}?", persona may acknowledge the
  tension in its own framing, never as a diagnosis.
```

## Quality Criteria

1. **All 6 layers present**; layers 1-5 meet `persona-5layer` quality bar.
2. **Layer 6 has ≥3 verbatim evidence quotes** from ≥3 distinct contexts.
3. **No clinical labels** unless subject used them themselves (cited).
4. **Runtime-behavior bullets** are actionable — they change what the persona produces at runtime, not just describe.
5. **Honest null**: if evidence is insufficient, `insufficient_evidence: true` is set rather than fabricated.

## Failure Modes

- **Missing layer 6**: the persona is shipped as a loved-one with only 5 layers — rejected; routes to `persona-5layer` + wrong schema selection.
- **Mood-as-tension**: layer 6 reads "gets sad sometimes", "is anxious" — fails; those are moods/diagnoses, not organizing tensions.
- **Projection**: extractor invents a tension ("probably fears abandonment") with no corpus anchor. DILUTE-grade; often a generic template.
- **Clinical drift**: extraction uses attachment-theory / MBTI / enneagram labels without subject's corpus usage. Strip and rephrase in grounded language.
- **Weaponization risk ignored**: runtime-behavior omits "do not use this layer against the user"; blocks Phase 4 for loved-one schemas by policy.
- **Over-count**: 3+ tensions emitted — almost always means the extractor could not winnow; re-run step 3 with stricter corpus-span threshold.

## Borrowed From

- `titanwings/ex-skill` — https://github.com/titanwings/ex-skill — **origin of the 6-layer structure** with the emotional-wound / core-tension layer for ex-partner personas. `[UNVERIFIED-FROM-README]` README fragment: *"6 层人格：在 5 层之上加情绪创伤/核心张力层，这是区分 ex-skill 与 colleague-skill 的关键"*.
- `perkfly/ex-skill` — https://github.com/perkfly/ex-skill — comparative 6-layer implementation emphasizing memories + persona pairing. `[UNVERIFIED-FROM-README]` README fragment: *"memories 与 persona 双轨，persona 含 6 层"*.
- `agenmod/immortal-skill` — https://github.com/agenmod/immortal-skill — informed the "handling notes" / anti-weaponization practice for family personas. `[UNVERIFIED-FROM-README]` README fragment: *"family personas 需显式声明情绪层使用边界，避免反向操控用户"*.

## Interaction Notes

- `persona-6layer` depends on `persona-5layer`'s extraction having completed; the producer runs 5-layer first, then layer 6 as a second pass.
- At runtime, layer 6 is consulted AFTER layers 1-5, AFTER `emotional-patterns`, and BEFORE `expression-dna` — it shapes what is said, DNA shapes how.
- `correction-layer` entries targeting `persona-6layer` require `severity: major` at minimum — layer-6 changes are never minor.
