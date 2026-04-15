---
name: component-contract
description: Authoritative interface contract for the 19 shared components used across 9 persona schemas
version: 1.1.0
---

# Component Contract

> All 19 shared components (`hard-rules`, `identity`, `expression-dna`, `persona-5layer`, `persona-6layer`, `self-memory`, `work-capability`, `shared-memories`, `emotional-patterns`, `mental-models`, `decision-heuristics`, `thought-genealogy`, `internal-tensions`, `honest-boundaries`, `domain-framework`, `computation-layer`, `interpretation-layer`, `correction-layer`, `execution-profile`) MUST conform to this contract. Schema writers consume components by slug; any component file violating this contract blocks the Phase 4 quality gate.

## 1. File Naming

- Component definition (inside `distill-meta/references/components/`): `<slug>.md` where slug is lowercase kebab-case.
- Generated component in produced persona skill (inside `{persona-skill}/components/`): same filename.

## 2. Required YAML Frontmatter

Every component file MUST start with:

```yaml
---
component: <slug>                    # must match filename
version: <semver>                    # component definition version
purpose: <one-line string>           # what this component carries
required_for_schemas: [<schema>...]  # which of 9 schemas MUST include it
optional_for_schemas: [<schema>...]  # which MAY include it
depends_on: [<slug>...]              # other components this reads at runtime (if any)
produces: [<slug>...]                # other components this populates (if any)
llm_consumption: eager | progressive # eager = always loaded; progressive = loaded on demand
---
```

## 3. Required H2 Sections (in order)

Every component definition file MUST have, in this order:

1. `## Purpose` — why this component exists. 1-2 paragraphs.
2. `## Extraction Prompt` — the prompt used during Phase 2 to extract this component from corpus. Include input schema, output schema, few-shot examples, anti-examples.
3. `## Output Format` — the structure the generated component file takes when emitted into a persona skill (headings, required fields, allowed variability).
4. `## Quality Criteria` — observable properties used by persona-judge to score this component. At least 3 criteria.
5. `## Failure Modes` — known failure patterns for this extraction (what bad output looks like). Helps density-classifier distinguish REMOVE vs DILUTE content.
6. `## Borrowed From` — citation to any reference library (nuwa-skill / colleague-skill / ex-skill / etc.). If this component is re-derived from a README fragment, state `[UNVERIFIED-FROM-README]` and quote the fragment.

Optional H2 sections:

- `## Examples` — 1-3 worked examples of the component as emitted in a real persona skill.
- `## Interaction Notes` — how this component interacts with other components at skill runtime.

## 4. Generated-File Discipline

When a component is emitted into a produced persona skill (under `components/`), it MUST:

- Keep the frontmatter block (adjust `produced_for` to the persona's manifest fingerprint).
- Drop the `Extraction Prompt` / `Failure Modes` / `Borrowed From` sections (these are for generation-time, not runtime).
- Keep `Purpose` / `Output Format` (now as concrete content) / any `Examples`.
- Stay **self-contained** — no cross-references to `distill-meta`. Borrow-copy, don't link.

## 5. Versioning

- Bump component `version` (SemVer) in `distill-meta/references/components/` when changing the Extraction Prompt or Output Format.
- Producer records resolved `component_versions` in the persona skill's `manifest.json`.
- Consumer (persona-judge) validates that the manifest's component versions are declared in distill-meta's current component library — unknown versions emit a WARN in validation-report.

## 6. Slug Reservations

The 19 reserved component slugs:

| Slug | Schemas it is required for |
|------|-----------------------------|
| `hard-rules` | all persona schemas (schema 1-8), optional for executor |
| `identity` | all 9 |
| `expression-dna` | all persona schemas (1-8); "neutral voice" variant for topic |
| `persona-5layer` | self, collaborator, friend, mentor (base), public-domain (optional) |
| `persona-6layer` | loved-one only |
| `self-memory` | self only |
| `work-capability` | collaborator, mentor |
| `shared-memories` | loved-one, friend (lightweight) |
| `emotional-patterns` | loved-one |
| `mental-models` | public-mirror, mentor |
| `decision-heuristics` | public-mirror, mentor |
| `thought-genealogy` | public-mirror |
| `internal-tensions` | public-mirror, mentor (optional) |
| `honest-boundaries` | all 9 |
| `domain-framework` | public-domain, topic (as `consensus-frame + divergences`) |
| `computation-layer` | executor (required), any schema (optional attachment) |
| `interpretation-layer` | executor |
| `correction-layer` | all persona schemas |
| `execution-profile` | optional for persona schemas 1-7 (public-mirror, mentor recommended); not applicable to topic / executor |

No third-party or plugin-added components in v1.

## 7. Anti-Contract (explicit NO)

Components MUST NOT:

- Execute arbitrary shell commands in their Extraction Prompts.
- Depend on non-stdlib Python unless they are `computation-layer` and the host schema declares `computation_python_packages` in manifest.
- Reference files outside the persona skill's own root at runtime.
- Include user corpus verbatim without redaction (see `distill-collector/references/redaction-policy.md`).

## 8. Change Log

- 1.0.0 — Initial contract.
- 1.1.0 — Added `execution-profile` component (19th slug). Optional for persona schemas 1-7; drives Phase 3.7 CDM-based execution-layer extraction. Additive change — existing schemas unaffected.
