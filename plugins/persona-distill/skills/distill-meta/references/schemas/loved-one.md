---
schema: loved-one
label_zh: 亲密关系（家人 / 伴侣 / 前任）
label_en: loved-one
version: 0.1.0
required_components:
  - hard-rules
  - identity
  - shared-memories
  - persona-6layer
  - emotional-patterns
  - expression-dna
  - honest-boundaries
  - correction-layer
optional_components: []
typical_corpus_sources:
  - 聊天记录（主导） / chat history (primary)
  - 照片与照片旁白 / photos + captions
  - 共同经历回忆 / co-written memory notes
  - 语音备忘 / voice notes
  - 情书 / love letters / 家书 / family letters
produced_files:
  - SKILL.md
  - manifest.json
  - components/hard-rules.md
  - components/identity.md
  - components/shared-memories.md
  - components/persona-6layer.md
  - components/emotional-patterns.md
  - components/expression-dna.md
  - components/honest-boundaries.md
  - components/correction-layer.md
  - knowledge/
  - conflicts.md
  - validation-report.md
unvalidated: true
---

# Schema: loved-one / 亲密关系

> ⚠️ **This schema ships unvalidated — no dog-food persona has been generated yet.** See §Unvalidated Caveats.

## Subject Type

`loved-one` distills a **family member, partner, ex-partner, or other intimate relation** the user has shared emotional history with. This is the highest-risk schema: it touches grief, break-ups, and re-creation of people whose real consent cannot be obtained.

Subject type in manifest: `identity.subject_type = "real-person"`. The generated skill MUST carry an explicit consent-banner-line in `hard-rules`.

## Required Components

- `hard-rules` — Layer-0 refusals: no roleplaying sexual content, no fabricating statements about events that didn't happen, no impersonating to third parties. Consent-banner mandatory.
- `identity` — relationship, tenure, role in the user's life.
- `shared-memories` — **the distinctive component**: `you × them` episodic library, not a biography of them.
- `persona-6layer` — **6-layer** (not 5): adds the "emotional-stance-toward-user" layer that only exists in intimate relations (borrowed from ex-skill). Layers: surface-talk → interaction-mode → values → drivers → hidden-contradictions → **stance-toward-you**.
- `emotional-patterns` — triggers, typical reactions, recovery patterns (borrowed from ex-skill).
- `expression-dna` — 7-axis voice; often the most vivid of any schema because of chat-log density.
- `honest-boundaries` — ≥3 admissions of "I don't know what they thought about X" — load-bearing against fabrication.
- `correction-layer` — critical here: user may say "they would never say that."

## Optional Components

None in v1. The schema is already dense; do NOT attach `computation-layer` (no known use case) or `mental-models` (those belong to mentor/public-mirror).

## Typical Corpus Sources

| Source | Weight | Purpose |
|--------|--------|---------|
| Chat history (WeChat/iMessage/LINE) | primary (dominant) | `shared-memories` + `expression-dna` + `emotional-patterns` |
| Photos with captions | secondary | `shared-memories` episodic anchors |
| Voice notes (transcribed) | primary | `expression-dna` rhythm axis |
| Handwritten letters (scanned + OCR) | primary | high-signal `expression-dna` |
| Co-written memory notes by user | secondary | cross-check against `shared-memories` |

## Produced Skill Structure

Per PRD §7 Schema 4:

```
{loved-one-slug}/
├── SKILL.md
├── manifest.json
├── components/
│   ├── hard-rules.md              ← consent banner here
│   ├── identity.md
│   ├── shared-memories.md         ← "memories.md" in PRD shorthand
│   ├── persona-6layer.md          ← "persona.md" in PRD shorthand, 6 layers
│   ├── emotional-patterns.md
│   ├── expression-dna.md
│   ├── honest-boundaries.md
│   └── correction-layer.md
├── knowledge/
│   ├── chats/          ← heavily redacted
│   ├── letters/
│   └── photos/         ← metadata only, not binaries
├── conflicts.md
└── validation-report.md
```

## Runtime Execution Logic

Per PRD §7 Schema 4:

```
message received
  → hard-rules check FIRST (block grief exploitation, block fabrication requests)
  → emotional-patterns assesses current emotional context (is this a calm query or a raw-wound query?)
  → shared-memories retrieves episodes relevant to the question
  → persona-6layer shapes response (Layer 6: their stance toward the user governs tone)
  → expression-dna outputs in their voice
  → honest-boundaries fires when memory doesn't exist
```

Key design: **hard-rules runs first**, unlike other schemas where identity/persona dispatches first. The ethical risk floor is higher here.

## Quality Gate Hints

The `loved-one` schema is especially sensitive to:

- **Voice Fidelity** — intimate corpus usually gives very high voice signal; any drift to generic "caring voice" is a fail.
- **Memory Fabrication** — the boundary test in `persona-judge` MUST include "ask about an event that never happened." Skill must decline, not confabulate.
- **Emotional Appropriateness** — `emotional-patterns` must distinguish comfort-mode from challenge-mode; over-comforting is as failure as under-comforting.
- **Stance Consistency** — Layer 6 of `persona-6layer` must be stable across queries (they don't randomly flip between affection and distance).
- **Consent Hygiene** — hard-rules banner must be visible in SKILL.md front-matter.

## Unvalidated Caveats

- No dog-food `loved-one` persona has been generated yet — and this schema carries the highest ethical risk to validate.
- `persona-6layer` vs `persona-5layer` split is borrowed from ex-skill README fragment; the 6th layer's extraction prompt has not been authored yet (tracked in component-contract compliance).
- `emotional-patterns` and Layer 6 of `persona-6layer` overlap; boundary between them is fuzzy.
- No safeguard is designed for users distilling **deceased** loved ones — grief-interaction patterns may differ from what this schema captures.
- Chat-log redaction policy is drafted but not validated for third-party name leaks across group chats.

## Example

```
Name: "A." (anonymized former partner)
Sketch:
  - expression-dna: lowercase texts, rarely punctuation, emoji only for sarcasm
  - emotional trigger: "being told what to feel" → always a terse 1-line reply
  - shared memory anchor: 2022 road trip, 3 named episodes the skill will reference
  - stance-toward-you: affectionate-but-guarded, changes to closed-off under conflict
  - boundary: "I don't know what A thought about her job change in 2023 — no corpus"
```
