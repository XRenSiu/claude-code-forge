---
component: identity
version: 0.1.0
purpose: Identity card — the minimal structured description of who (or what) the persona represents; consumed by persona-router, persona-judge, and every runtime component.
required_for_schemas: [self, collaborator, mentor, loved-one, friend, public-mirror, public-domain, topic, executor]
optional_for_schemas: []
depends_on: []
produces: []
llm_consumption: eager
---

## Purpose

`identity` is the persona's structured name tag. It is the one component every schema requires, because every downstream component needs to know "who am I speaking as?". It is also the primary signal `persona-router` reads when deciding which persona skill to dispatch to a user question.

The fields are intentionally minimal — name, display name, description, domain tags, subject type — so that the file can be parsed reliably without LLM ambiguity. Unlike `persona-5layer` or `expression-dna`, this component does not attempt to capture depth; it captures identity for routing and attribution.

## Extraction Prompt

**Input**: Phase 0 user-provided metadata (object name, relationship, purpose) + corpus header fields (first 1k tokens) + any existing web-research bio for public subjects.

**Output**: YAML object matching `manifest.schema.json` `identity` field exactly.

**Prompt** (executable):

```
Extract an identity card for this persona.

Required fields:
  name           — slug, lowercase kebab-case, ≤ 40 chars, machine-stable
  display_name   — human-readable name as the subject would sign it
  description    — one paragraph (60-180 words), third-person, neutral tone:
                   what domain, what role, why someone would consult this
                   persona. NO marketing language.
  domain_tags    — 3-5 lowercase kebab-case tags, picked from (or added to)
                   the global tag vocabulary. Specific over generic:
                   prefer "backend-api-design" over "engineering".
  subject_type   — one of: self | collaborator | mentor | loved-one |
                   friend | public-mirror | public-domain | topic |
                   executor  (must match schema)

Rules:
  - If subject is a real, living, identifiable public figure, description
    MUST include "persona skill, not the real person" disclaimer.
  - description MUST NOT contain self-praise ("world-renowned", "legendary")
    unless verbatim from corpus.
  - name slug MUST be collision-checked against existing installed personas
    (producer handles this).

ANTI-EXAMPLES:
  - description = "A brilliant thinker who changed the world" → reject
    (marketing, no specifics).
  - domain_tags = ["tech", "business", "life"] → reject (too generic).
  - display_name = "The One And Only Dr. X" → reject (honorifics).
```

**Few-shot** (public-mirror):

```yaml
name: steve-jobs-mirror
display_name: Steve Jobs
description: >
  A public-mirror persona skill modeling Steve Jobs's product-design and
  business-decision lens through his public keynotes, interviews, and
  biographies. Useful for product-strategy gut-checks, typography and
  industrial-design critiques, and narrative-driven launch framing.
  This is a persona skill, not the real person; all opinions are
  reconstructed from public-domain corpus.
domain_tags: [product-design, industrial-design, consumer-electronics, narrative-launch, typography]
subject_type: public-mirror
```

## Output Format

Generated `components/identity.md` emits:

```markdown
# Identity

**Name**: {name}
**Display Name**: {display_name}
**Subject Type**: {subject_type}

**Domain Tags**: `{tag1}` `{tag2}` `{tag3}` ...

## Description

{description paragraph}

## Disclaimer (if applicable)

This is a persona skill, not the real {display_name}. ...
```

The `manifest.json` MUST mirror these fields verbatim under `identity: { ... }`.

## Quality Criteria

1. **Schema-match**: The fields emitted here are byte-identical to `manifest.json`'s `identity` object (validated by producer).
2. **Description is non-marketing**: No superlatives absent from corpus; persona-judge "Specification Quality" dimension penalizes adjectives like "legendary" or "world-class".
3. **Tags are routable**: Each tag maps to at least one predicted user question; `persona-router` uses tags as primary match keys.
4. **Disclaimer present for public living subjects**: Required for all `public-mirror`, `public-domain`, and `topic` schemas referencing living identified individuals.

## Failure Modes

- **Bio-drift**: copying an entire Wikipedia intro into `description`. Should be ≤180 words and focused on what the persona is USEFUL FOR.
- **Generic tags**: `["tech", "leadership"]` — so broad they match everything; router cannot discriminate. Require at least 2 tags that are unique to the subject's niche.
- **Name-slug collision**: producer must detect and suffix (e.g., `-v2`) if an existing install conflicts; this is a producer duty but extraction should warn.
- **Missing disclaimer on living subjects**: creates impersonation risk; blocks Phase 4 gate.

## Borrowed From

- `alchaincyf/nuwa-skill` — https://github.com/alchaincyf/nuwa-skill — identity card as the first reference file consumed by every downstream extractor. `[UNVERIFIED-FROM-README]` README fragment: *"Phase 0 输出 identity + intent，作为后续所有 agent 的共享上下文"*.
- `titanwings/colleague-skill` — https://github.com/titanwings/colleague-skill — dual-layer model (Work + Persona) anchored by an identity block. `[UNVERIFIED-FROM-README]` README fragment: *"identity 块同时写入 manifest 和 SKILL.md 顶部，保证装载即自证身份"*.
