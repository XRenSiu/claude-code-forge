---
schema: public-domain
label_zh: 领域专家（给方法论）
label_en: public-domain
version: 0.1.0
required_components:
  - hard-rules
  - identity
  - domain-framework
  - expression-dna
  - honest-boundaries
  - correction-layer
optional_components:
  - mental-models
  - computation-layer
  - persona-5layer
typical_corpus_sources:
  - 该领域的公开方法论 / published methodologies
  - 教材 / textbooks
  - 手册 / practitioner handbooks
  - 案例研究 / case studies
  - 经典论文 / seminal papers
produced_files:
  - SKILL.md
  - manifest.json
  - components/hard-rules.md
  - components/identity.md
  - components/domain-framework.md
  - components/expression-dna.md
  - components/honest-boundaries.md
  - components/correction-layer.md
  - knowledge/
  - cases.md                  ← per PRD §7 Schema 7
  - conflicts.md
  - validation-report.md
unvalidated: true
---

# Schema: public-domain / 领域专家

> ⚠️ **This schema ships unvalidated — no dog-food persona has been generated yet.** See §Unvalidated Caveats.

## Subject Type

`public-domain` distills a **public figure for their methodology**, not their thinking perspective. The user's goal: "**I want to use their framework to solve a problem**" — not "what would they say?" but "**given their method, what's the answer?**"

Subject type in manifest: `identity.subject_type = "real-person"` or `"composite"` (when the framework is the synthesized method of several practitioners credited to one). Distinct from `public-mirror` (perspective) and `topic` (multi-practitioner consensus).

## Required Components

- `hard-rules` — refuse predictions outside the framework's domain; refuse to claim methodology certainty it doesn't have.
- `identity` — the person + the one-line framework they are being distilled for.
- `domain-framework` — **the distinctive component**: an N-dimensional methodology (e.g., midas-skill's "six-dimension wealth"). Each dimension gets its own processing logic. See `components/domain-framework.md`.
- `expression-dna` — 7-axis voice, though typically weighted lighter than `public-mirror` (methodology > voice here).
- `honest-boundaries` — ≥3 "this framework does not apply to X" admissions.
- `correction-layer` — accumulates corrections.

## Optional Components

- `mental-models` — attach when the framework leans on named cognitive models (e.g., Kahneman's System 1/2). Optional because `domain-framework` often already embeds them.
- `computation-layer` — attach when the framework has quantitative steps (DCF for Buffett-style valuation, CHA2DS2-VASc for a cardiologist). Per PRD §2.4.
- `persona-5layer` — attach when voice matters for delivery (the practitioner has a signature teaching style).

## Typical Corpus Sources

| Source | Weight | Purpose |
|--------|--------|---------|
| Published methodology book / handbook | primary | `domain-framework` spine |
| Case studies (by them or credible others) | primary | `cases.md` |
| Teaching talks / MOOC transcripts | secondary | dimension definitions |
| Seminal papers | primary | framework origins |
| Contemporary reviews/critiques | tertiary | `honest-boundaries` |

## Produced Skill Structure

Per PRD §7 Schema 7:

```
{domain-expert-slug}/
├── SKILL.md
├── manifest.json
├── components/
│   ├── hard-rules.md
│   ├── identity.md
│   ├── domain-framework.md       ← N dimensions as subsections
│   ├── expression-dna.md
│   ├── honest-boundaries.md
│   └── correction-layer.md
│   # optional: mental-models.md, computation-layer.md, persona-5layer.md
├── knowledge/
│   ├── methodology/
│   └── cases/
├── cases.md                      ← worked examples per PRD §7 Schema 7
├── conflicts.md
└── validation-report.md
```

The `N-dimension` structure of `domain-framework.md` is the schema's signature — e.g., 6 H2 sections in a Buffett-style financial persona, 4 H2 sections in a "how to write a product PRD" persona.

## Runtime Execution Logic

Per PRD §7 Schema 7:

```
question received
  → domain-framework locates which dimension(s) the question belongs to
  → the dimension's own framework processes the question
  → (optional) mental-models or computation-layer enrich the processing
  → expression-dna shapes output voice (lighter weight than public-mirror)
  → honest-boundaries fires when question is outside all dimensions
```

Key design: **the framework owns the reasoning**, voice is a skin on top. This is the opposite of `public-mirror` where voice and perspective are the payload.

## Quality Gate Hints

The `public-domain` schema is especially sensitive to:

- **Framework Completeness** — every dimension declared in `domain-framework.md` must have processing logic; no empty sections.
- **Cross-dimension Interaction** — when a question spans 2+ dimensions, the skill must integrate, not pick one arbitrarily.
- **Case Grounding** — `cases.md` must provide ≥3 worked examples per major dimension.
- **Out-of-domain Honesty** — boundary test: ask a question completely outside the framework; must refuse, not stretch.
- **Quantitative Integrity** — if `computation-layer` attached, numbers must be computed not guessed.

## Unvalidated Caveats

- No dog-food `public-domain` persona has been generated yet.
- The "N-dimension" approach is borrowed from midas-skill README fragment; the extraction prompt for defining the N dimensions from corpus has not been implemented.
- Overlap with `mental-models` (when attached) is under-specified.
- `cases.md` as a separate top-level file (vs. subfolder of `knowledge/`) is inherited from PRD §7 but inconsistent with other schemas' structure — flagged as a spec ambiguity.

## Example

```
Name: "Buffett" (public-domain sketch for value investing)
Sketch:
  - dimension 1: circle-of-competence — does this business fit my expertise?
  - dimension 2: moat analysis — what protects this from competition?
  - dimension 3: management quality — signal of character over charisma
  - dimension 4: intrinsic value — DCF with conservative assumptions (computation-layer attached)
  - boundary: "I will not opine on tech platforms I don't use; not my circle"
```
