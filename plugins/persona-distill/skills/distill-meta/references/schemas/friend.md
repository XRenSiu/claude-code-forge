---
schema: friend
label_zh: 朋友
label_en: friend
version: 0.1.0
required_components:
  - hard-rules
  - identity
  - shared-memories
  - persona-5layer
  - expression-dna
  - honest-boundaries
  - correction-layer
optional_components:
  - computation-layer
typical_corpus_sources:
  - 聊天记录（日常） / casual chat history
  - 群聊片段 / group chat fragments
  - 朋友圈互动 / social-feed reactions & comments
  - 共同活动回忆 / hangout recaps
produced_files:
  - SKILL.md
  - manifest.json
  - components/hard-rules.md
  - components/identity.md
  - components/shared-memories.md
  - components/persona-5layer.md
  - components/expression-dna.md
  - components/honest-boundaries.md
  - components/correction-layer.md
  - knowledge/
  - conflicts.md
  - validation-report.md
unvalidated: true
---

# Schema: friend / 朋友

> ⚠️ **This schema ships unvalidated — no dog-food persona has been generated yet.** See §Unvalidated Caveats.

## Subject Type

`friend` is the **lightweight sibling of `loved-one`**: a peer-level, non-romantic, non-family intimate connection. The user wants a "what would my friend X say here?" voice — casual feedback, gossip takes, hangout suggestions — not therapy, not work advice.

Subject type in manifest: `identity.subject_type = "real-person"`. Distinct from `loved-one` in three ways: **5 layers not 6**, **lightweight shared-memories**, **no emotional-patterns** component.

## Required Components

- `hard-rules` — refuse fabricating statements about third parties (common-friend gossip trap); consent banner lighter than `loved-one` but present.
- `identity` — friendship context, tenure, shared circles.
- `shared-memories` — **lightweight variant**: fewer episodes, more recurring-in-jokes / running references. See [shared-memories.md component doc] for the "lightweight" flag.
- `persona-5layer` — standard 5 layers (surface → interaction → values → drivers → contradictions).
- `expression-dna` — 7-axis voice; typically the highest-signal component for casual friends.
- `honest-boundaries` — ≥3 admissions; often "I don't know their work life" or "I don't know their family."
- `correction-layer` — user corrections accumulate.

## Optional Components

- `computation-layer` — rare (friend who always runs split calculators, DM travel planner scripts, etc.). Attach only with explicit use case.

## Typical Corpus Sources

| Source | Weight | Purpose |
|--------|--------|---------|
| 1-on-1 casual chat logs | primary | voice + in-jokes |
| Group chat fragments (friend as participant) | primary | interaction-style layer |
| Social-feed comments by the friend | secondary | voice cross-check |
| User-written hangout recaps | secondary | `shared-memories` anchors |

Corpus volume will typically be **smaller** than `loved-one` — the schema is tuned for that. If corpus is very rich, consider upgrading to `loved-one` (see decision-tree tie-breakers).

## Produced Skill Structure

Per PRD §7 Schema 5:

```
{friend-slug}/
├── SKILL.md
├── manifest.json
├── components/
│   ├── hard-rules.md
│   ├── identity.md
│   ├── shared-memories.md        ← lightweight variant
│   ├── persona-5layer.md
│   ├── expression-dna.md
│   ├── honest-boundaries.md
│   └── correction-layer.md
├── knowledge/
│   └── chats/
├── conflicts.md
└── validation-report.md
```

## Runtime Execution Logic

```
message received
  → hard-rules check (third-party gossip guard)
  → persona-5layer decides mode (banter? serious-friend-advice? logistics?)
  → shared-memories surfaces relevant in-joke or past reference (optional at runtime)
  → expression-dna shapes voice
  → honest-boundaries fires on domains outside the friendship's scope
```

Key design vs `loved-one`: **no `emotional-patterns` gate in front**. Friends are assumed to operate in banter-default, not emotional-assessment-default. If the real friend does emotional-assessment often, consider upgrading to `loved-one` schema.

## Quality Gate Hints

The `friend` schema is especially sensitive to:

- **Voice Fidelity** — casual voice collapses to generic quickly; slang/meme usage must be specific to this friend.
- **In-joke Authenticity** — `shared-memories` must surface recurring references (nicknames, running gags), not just events.
- **Third-party Silence** — the skill should refuse to speak as/about common friends without evidence (hard-rules).
- **Scope Honesty** — friends rarely know the user's work/family deeply; honest-boundaries must reflect that.

## Unvalidated Caveats

- No dog-food `friend` persona has been generated yet.
- The "lightweight `shared-memories`" variant is not yet specified in `components/shared-memories.md` — it's a conceptual flag pending implementation.
- The boundary between `friend` and `loved-one` will feel arbitrary on real corpus; expect user complaints that the decision tree mislabels.
- No heuristic yet distinguishes "close friend" from "acquaintance" — may warrant a 10th schema in v2.

## Example

```
Name: "J." (anonymized college friend)
Sketch:
  - expression-dna: memes > words; one-word replies; always lowercases
  - shared-memory anchors: the 2019 Tokyo trip, the "that pizza place" running joke
  - interaction-style: roasts first, then actually helpful
  - value-layer: hates self-seriousness, rewards honesty about failure
  - boundary: "I don't know what J thinks about your job — we don't talk work"
```
