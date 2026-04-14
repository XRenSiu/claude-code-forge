---
schema: executor
label_zh: 规则体系（八字 / 奇门 / 塔罗 / 法条引擎）
label_en: executor
version: 0.1.0
required_components:
  - hard-rules
  - identity
  - computation-layer
  - interpretation-layer
  - expression-dna            # voice-of-practice variant
optional_components:
  - correction-layer
typical_corpus_sources:
  - 领域经典典籍 / classical canonical texts
  - 规则表 / rule tables (干支 / 五行 / 卦象 / 法条)
  - 案例解读 / interpretive case collections
  - 流派手册 / school-specific handbooks
  - 开源实现 / open-source rule engines (if any)
produced_files:
  - SKILL.md
  - manifest.json
  - components/hard-rules.md
  - components/identity.md
  - components/computation-layer.md
  - components/interpretation-layer.md
  - components/expression-dna.md
  - references/                  ← rule tables (pure data)
  - tools/                       ← Python scripts (stdlib + declared packages only)
  - knowledge/
  - conflicts.md
  - validation-report.md
unvalidated: true
---

# Schema: executor / 规则体系

> ⚠️ **This schema ships unvalidated — no dog-food persona has been generated yet.** See §Unvalidated Caveats.

## Subject Type

`executor` is the **only non-persona schema**. Subject is a **rule-system** (Bazi / Qimen / Tarot / chess openings / legal-clause engines). The output is deterministic computation wrapped in a stylized interpretation voice. It is NOT a person; it does not claim consciousness or opinion.

Subject type in manifest: `identity.subject_type = "rule-system"`. `hard-rules` is marked optional in the component-contract for this schema but in practice v1 still emits it (legal disclaimers).

## Required Components

- `hard-rules` — disclaimers: not medical/legal/financial advice; results are computation outputs, not predictions of reality.
- `identity` — the rule system, its classical school, scope.
- `computation-layer` — **the defining component**: pure Python (stdlib, or declared packages in manifest's `computation_python_packages`) that takes input → outputs deterministic tokens/tables. The skill's correctness is traceable to this code. Per component-contract §7.
- `interpretation-layer` — maps computation tokens → natural-language readings, grounded in canonical texts. Each reading cites its source rule.
- `expression-dna` — **voice-of-practice variant**: the style of a traditional practitioner (solemn, measured, archaic terminology), not a person's personal voice.

## Optional Components

- `correction-layer` — the only optional component that makes sense here; accumulates user corrections when the interpretation-layer's tone or sourcing is off. No other component attaches cleanly.

Notably, `persona-5layer`/`mental-models`/`emotional-patterns` MUST NOT attach — they assume a person, not a rule system.

## Typical Corpus Sources

| Source | Weight | Purpose |
|--------|--------|---------|
| Classical canonical texts | primary | rule tables + authoritative interpretations |
| Rule tables | primary | `computation-layer` data tables |
| Case collections | primary | `interpretation-layer` worked examples |
| School-specific handbooks | secondary | variant rules, disclosed in `conflicts.md` |
| Open-source rule engines | secondary | cross-validate `computation-layer` |

## Produced Skill Structure

Per PRD §7 Schema 9:

```
{executor-slug}/
├── SKILL.md
├── manifest.json                  ← declares computation_python_packages if any
├── components/
│   ├── hard-rules.md              ← disclaimers
│   ├── identity.md
│   ├── computation-layer.md       ← describes inputs/outputs/algorithm
│   ├── interpretation-layer.md    ← mapping rules + citation discipline
│   └── expression-dna.md          ← voice-of-practice
├── references/                    ← rule tables (干支表 / 五行生克表 / 卦象表 等，纯数据)
│   ├── table-*.md
│   └── ...
├── tools/                         ← Python scripts
│   ├── compute.py                 ← the executor
│   └── ...
├── knowledge/
│   └── canonical-texts/
├── conflicts.md                   ← school-variant rules preserved
└── validation-report.md
```

Unique to this schema: `references/` carries **pure data tables**, `tools/` carries **actual Python code**. Other schemas have neither at the skill root.

## Runtime Execution Logic

Per PRD §7 Schema 9 — **computation-first flow** (unique among the 9 schemas):

```
input received (e.g., 生辰八字 / tarot spread / case facts)
  → computation-layer runs deterministic Python against rule tables
    → outputs structured tokens (e.g., {year_pillar: "甲子", ...})
  → interpretation-layer maps tokens → natural-language reading (with source citations)
  → expression-dna wraps in voice-of-practice (not personal voice)
  → hard-rules appends disclaimers before output
```

Key difference from all other schemas: **computation runs FIRST, voice runs LAST**, and there is no "persona layer" making judgement calls. Determinism is the contract.

## Quality Gate Hints

The `executor` schema is especially sensitive to:

- **Computational Correctness** — the same input must produce the same output every run. `persona-judge` must include a reproducibility test.
- **Citation Discipline** — every interpretation claim in `interpretation-layer` must cite a canonical text / rule table; uncited interpretations are DILUTE/REMOVE candidates.
- **Voice Discipline (voice-of-practice)** — must sound like the tradition, not a random mystical-AI voice. Over-dramatic output is a fail.
- **Disclaimer Hygiene** — `hard-rules` must appear in every user-facing output, not just SKILL.md front matter.
- **No Persona Leakage** — the skill must NOT drift into "I think…" style; it operates in "the chart shows…" mode.

## Unvalidated Caveats

- No dog-food `executor` persona has been generated yet.
- `computation-layer` as a **Python module** (rather than rule-table walk encoded in prompts) is borrowed from bazi-skill's README fragment — its packaging story (how the persona skill ships executable Python across Claude Code environments) is not specified here; component-contract §7 just forbids arbitrary shell and requires declared packages.
- The `voice-of-practice` variant of `expression-dna` is a concept, not a separate extraction prompt.
- Cross-school rule divergences (e.g., classical-vs-modern Bazi variants) are captured in `conflicts.md` but the runtime selection logic isn't specified — v1 skills will likely just pick one school arbitrarily.
- Interaction with `computation-layer` attached to a persona schema (PRD §2.4 Example C) is not yet specified from the executor side.

## Example

```
Name: "Classical Bazi Reader" (executor sketch)
Sketch:
  - input: birth datetime (solar) + location
  - computation-layer: solar→ganzhi conversion, pillar-derivation, five-elements scoring
    outputs: {year:甲子, month:丙寅, day:戊申, hour:壬子, elements:{wood:3,fire:1,...}}
  - interpretation-layer: cites 《子平真诠》 + 《滴天髓》 when mapping pillars → readings
  - voice-of-practice: "命主身弱，…宜补火而避水" — measured, archaic
  - disclaimer: "this is a classical chart reading, not life advice; consult professionals for decisions"
```
