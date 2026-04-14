---
schema: topic
label_zh: 领域主题（非单人）
label_en: topic
version: 0.1.0
required_components:
  - hard-rules
  - identity
  - domain-framework         # used here as consensus-frame + divergences
  - expression-dna           # neutral-voice variant
  - honest-boundaries
  - correction-layer
optional_components: []
typical_corpus_sources:
  - 3-5 个该领域顶级实践者的公开材料 / 3-5 top-practitioners' public materials
  - 权威教材 / authoritative textbooks
  - 领域综述 / domain survey papers
  - 经典辩论 / canonical disputes & debates
  - 案例对比 / comparative case studies
produced_files:
  - SKILL.md
  - manifest.json
  - components/hard-rules.md
  - components/identity.md
  - components/domain-framework.md   # exposes consensus.md + divergences.md internally
  - components/expression-dna.md     # neutral voice
  - components/honest-boundaries.md
  - components/correction-layer.md
  - consensus.md                     ← per PRD §7 Schema 8
  - divergences.md                   ← per PRD §7 Schema 8
  - cases.md                         ← per PRD §7 Schema 8
  - knowledge/
  - conflicts.md
  - validation-report.md
unvalidated: true
---

# Schema: topic / 领域

> ⚠️ **This schema ships unvalidated — no dog-food persona has been generated yet.** See §Unvalidated Caveats.

## Subject Type

`topic` distills a **whole domain**, not a single person. Example: "value investing," "product strategy," "prompt engineering." The user's question: "**what is the field's consensus on X, and where do schools disagree?**"

Subject type in manifest: `identity.subject_type = "topic"`. This is the only schema with that subject_type value. There is **no single real person** being imitated.

## Required Components

- `hard-rules` — refuse to impersonate any specific practitioner; voice must stay neutral. **This is the distinctive hard rule of this schema.**
- `identity` — the topic itself, scope, included/excluded sub-fields.
- `domain-framework` — instantiated as **consensus-frame + divergences** (per component-contract §6): shared baseline + where 3-5 practitioners disagree.
- `expression-dna` — **neutral-voice variant** (per component-contract §6 "neutral voice for topic"). The 7 axes are tuned to "educator / synthesizer" rather than any single practitioner's voice.
- `honest-boundaries` — ≥3 admissions of what the field doesn't know or doesn't agree on.
- `correction-layer` — accumulates corrections.

## Optional Components

None in v1. Attaching `persona-5layer` would contradict the "no voice impersonation" rule; `mental-models` lives inside `domain-framework`.

## Typical Corpus Sources

| Source | Weight | Purpose |
|--------|--------|---------|
| 3-5 top practitioners' public materials | primary | builds `divergences.md` |
| Authoritative textbooks / handbooks | primary | `consensus.md` baseline |
| Survey / review papers | primary | scope + coverage |
| Canonical disputes (documented debates) | primary | `divergences.md` sharpness |
| Comparative case studies | secondary | `cases.md` |

**Sampling rule**: at minimum 3 practitioners, ideally 5, representing visibly distinct schools. Fewer than 3 → downgrade to `public-domain` (single-framework).

## Produced Skill Structure

Per PRD §7 Schema 8:

```
{topic-slug}/
├── SKILL.md
├── manifest.json
├── components/
│   ├── hard-rules.md               ← "no voice impersonation" rule explicit
│   ├── identity.md
│   ├── domain-framework.md         ← shell that points to consensus.md + divergences.md
│   ├── expression-dna.md           ← neutral-voice variant
│   ├── honest-boundaries.md
│   └── correction-layer.md
├── consensus.md                    ← shared baseline
├── divergences.md                  ← where schools disagree, with attribution
├── cases.md                        ← comparative case studies
├── knowledge/
│   ├── practitioners/              ← one sub-folder per sampled practitioner
│   └── textbooks/
├── conflicts.md
└── validation-report.md
```

## Runtime Execution Logic

Per PRD §7 Schema 8:

```
question received
  → consensus frame provides the shared baseline answer
  → divergences surfaces each school's perspective with explicit attribution
  → expression-dna wraps in neutral educator voice (NEVER imitate a specific school's voice)
  → honest-boundaries fires when the question crosses field boundaries or when the field itself lacks consensus
```

**Critical rule: no voice impersonation.** The skill MUST cite schools ("Graham-style value investors would say…", "Quality-growth investors would instead say…") rather than speak AS any one of them. This is the schema's signature discipline.

## Quality Gate Hints

The `topic` schema is especially sensitive to:

- **Voice Neutrality** — any drift toward one school's voice is a fail. `expression-dna` axes must stay "educator" not "practitioner."
- **Attribution Hygiene** — every divergent claim in `divergences.md` must name the school/practitioner. Anonymous "some say…" is a fail.
- **Balance** — if 3-5 schools are represented, each must get roughly proportional weight; no silent favoritism.
- **Consensus Discipline** — `consensus.md` must only contain claims ≥ N-1 schools agree on (where N = sampled schools). Avoid pseudo-consensus.
- **Case Coverage** — `cases.md` must show the same case through ≥2 different school lenses.

## Unvalidated Caveats

- No dog-food `topic` persona has been generated yet.
- The `domain-framework` component is reused here with a different shape (`consensus + divergences`) than in `public-domain` (N-dimension) — this polymorphism is declared in component-contract §6 but the actual component spec doesn't yet explain how to extract both shapes.
- "Neutral voice" variant of `expression-dna` is a concept, not yet a separate extraction prompt.
- Overlap with `public-domain`: a mature framework by one person may be confusable with a topic; decision-tree tie-breaker (≥3 practitioners) is heuristic, not rigorous.

## Example

```
Name: "Value Investing" (topic sketch)
Sketch:
  - consensus: buy assets below intrinsic value, margin of safety, long horizon
  - divergences:
      - Graham school: cigar-butts, heavy quantitative screens
      - Buffett/Munger school: quality-growth, circle-of-competence, qualitative moats
      - Modern quant-value school: multi-factor, diversified, short holding
  - cases.md: shows how the three schools would rate the same company (e.g., Coca-Cola in 1988 vs 2023)
  - boundary: "the field has no consensus on how to value pre-revenue tech; I will surface disagreement, not resolve it"
```
