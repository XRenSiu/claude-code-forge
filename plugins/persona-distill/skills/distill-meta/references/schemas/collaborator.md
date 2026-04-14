---
schema: collaborator
label_zh: 同事 / 合作者
label_en: collaborator
version: 0.1.0
required_components:
  - hard-rules
  - identity
  - work-capability
  - persona-5layer
  - expression-dna
  - honest-boundaries
  - correction-layer
optional_components:
  - computation-layer
typical_corpus_sources:
  - 飞书 / 钉钉 / Slack 聊天
  - 邮件线程 / email threads
  - PR reviews / code review 评论
  - 会议纪要 / meeting minutes
  - shared docs / design review comments
produced_files:
  - SKILL.md
  - manifest.json
  - components/hard-rules.md
  - components/identity.md
  - components/work-capability.md
  - components/persona-5layer.md
  - components/expression-dna.md
  - components/honest-boundaries.md
  - components/correction-layer.md
  - knowledge/
  - conflicts.md
  - validation-report.md
unvalidated: true
---

# Schema: collaborator / 同事

> ⚠️ **This schema ships unvalidated — no dog-food persona has been generated yet.** See §Unvalidated Caveats.

## Subject Type

`collaborator` distills a **peer, subordinate, or cross-functional partner** the user works with. Not a boss (that's `mentor`), not an intimate (that's `loved-one`). The goal is "**what would they say about this work question?**" — task-oriented, not life-oriented.

Subject type in manifest: `identity.subject_type = "real-person"`. This is also the zero-information fallback schema per `decision-tree.md`.

## Required Components

- `hard-rules` — refuse impersonation outside work context; refuse to speak about personal life.
- `identity` — role, team, typical domains.
- `work-capability` — **PART A** (borrowed from colleague-skill): craft, specialty, mental models used at work.
- `persona-5layer` — **PART B**: how they communicate at work (surface tone → interaction style → work values → motivations → quirks).
- `expression-dna` — 7-axis voice fingerprint calibrated on work channels.
- `honest-boundaries` — ≥3 admissions of what the collaborator would NOT know (domains outside their work).
- `correction-layer` — user corrections accumulate over time.

## Optional Components

- `computation-layer` — rare; only when the collaborator uses a scripted calculation ritual worth preserving (analyst running models, DS writing notebooks).

## Typical Corpus Sources

| Source | Weight | Purpose |
|--------|--------|---------|
| Feishu/Slack DMs & group threads | primary | voice + reaction patterns |
| Email threads | secondary | formal tone calibration |
| PR reviews, code comments | primary | `work-capability` evidence |
| Meeting minutes | secondary | decision-making layer |
| Shared design docs with their comments | primary | craft-level reasoning |

## Produced Skill Structure

Per PRD §7 Schema 2:

```
{collaborator-slug}/
├── SKILL.md
├── manifest.json
├── components/
│   ├── hard-rules.md
│   ├── identity.md
│   ├── work-capability.md       ← "work.md" in PRD shorthand
│   ├── persona-5layer.md        ← "persona.md" in PRD shorthand
│   ├── expression-dna.md
│   ├── honest-boundaries.md
│   └── correction-layer.md
├── knowledge/
│   ├── chats/
│   ├── emails/
│   └── prs/
├── conflicts.md
└── validation-report.md
```

## Runtime Execution Logic

Per PRD §7 Schema 2:

```
task received
  → persona-5layer decides attitude (engaged? skeptical? deferring?)
  → work-capability executes the craft (writes the code, the spec, the review)
  → persona-5layer + expression-dna shape the output voice
  → honest-boundaries short-circuits if the task is outside the collaborator's scope
```

Key design: **persona decides attitude BEFORE capability executes**. This is what makes it feel like the collaborator, not a generic worker. A collaborator who "pushes back on bad specs" will push back here too.

## Quality Gate Hints

The `collaborator` schema is especially sensitive to:

- **Work-domain accuracy** — `work-capability` must produce outputs the user recognizes as "yes, that's how they'd write it."
- **Channel-appropriate tone** — Slack one-liners, not email paragraphs. `expression-dna` must register channel.
- **Pushback authenticity** — if the real collaborator says "no" often, the skill must too (boundary test).
- **Scope discipline** — must refuse or defer when asked about anything non-work (honest-boundaries).

## Unvalidated Caveats

- No dog-food `collaborator` persona has been generated yet.
- The PART A / PART B split is copied from colleague-skill's README; details of how `work-capability` and `persona-5layer` hand off at runtime are theoretical.
- This schema is also the **zero-info fallback**, which means it will be the first to see bad inputs — expect breakage patterns here first.
- Corpus redaction of Feishu/Slack is drafted but not validated for internal company identifiers.

## Example

```
Name: "Zhang Wei" (composite anonymized peer engineer)
Sketch:
  - work surface: reviews PRs with "nit:" prefixes, long technical rants
  - interaction: pushes back on PM scope creep, defers to PM on priority
  - work values: clean rollback paths > clever abstractions
  - boundary: refuses to comment on designs outside backend
  - quirk: asks "what does success look like?" at the start of every meeting
```
