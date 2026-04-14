---
name: validation-report-schema
description: Contract for persona-judge output consumed by distill-meta Phase-4 gate
version: 1.0.0
---

# validation-report.md — Schema Contract

> This document defines the authoritative contract for `validation-report.md` files emitted by **persona-judge** and read by **distill-meta** (Phase 4 quality gate). Any format change here is a breaking change to both skills.

## File Location

Generated report lives at `{persona-skill-root}/validation-report.md`. Successive evaluations append to `{persona-skill-root}/versions/validation-report-{ISO8601}.md` and the latest is mirrored to the canonical path.

## Required Structure

The file MUST have two top-level sections in this order:

1. **YAML frontmatter** — machine-readable. Required fields enumerated below.
2. **Markdown body** — human-readable. Required H2 sections enumerated below.

### 1. Frontmatter (required)

```yaml
---
persona_skill: <string>              # slug of the skill evaluated
persona_skill_version: <semver>      # version of skill at time of eval
persona_judge_version: <semver>      # version of persona-judge that ran this eval
evaluated_at: <ISO 8601 datetime>
overall_score_raw: <int 0-110>       # sum of 12 dimensions
overall_score_normalized: <int 0-100> # round(raw * 100 / 110)
pass_threshold_raw: 82               # default; configurable via config.yaml
verdict: PASS | FAIL | CONDITIONAL_PASS
density_score: <number 0-10>
critical_failures: <int>             # count of dims scoring 0
dimensions:
  known_test: <int 0-10>
  edge_test: <int 0-10>
  voice_test: <int 0-10>
  knowledge_delta: <int 0-10>
  mindset_transfer: <int 0-10>
  anti_pattern_specificity: <int 0-10>
  specification_quality: <int 0-5>
  structure: <int 0-5>
  density: <int 0-10>
  internal_tensions: <int 0-10>
  honest_boundaries: <int 0-10>
  primary_source_ratio: <int 0-10>
---
```

### 2. Body — required H2 sections (in this order)

- `## Summary` — 1-3 sentences: verdict + top concern.
- `## Dimension Scores` — a markdown table with columns `| Dimension | Score | Max | Notes |`. Exactly 12 rows, one per dimension, in the same order as the frontmatter `dimensions` object.
- `## Strengths` — markdown bulleted list, ≥1 bullet.
- `## Weaknesses` — markdown bulleted list, ≥0 bullets.
- `## Recommended Actions` — numbered list, ≥0 items. Each item MUST state the target file path and the change.
- `## Test Evidence` — verbatim outputs from Known/Edge/Voice tests. Optional but recommended.

## Contract for Consumers (distill-meta Phase 4 gate)

distill-meta MUST read `overall_score_raw` and `verdict` from frontmatter. It MUST NOT parse the markdown body for gating decisions. Gating rules:

- `verdict: PASS` → proceed to Phase 5 (delivery).
- `verdict: CONDITIONAL_PASS` → proceed but surface `Recommended Actions` to user.
- `verdict: FAIL` → return to Phase 2 with `Recommended Actions` as the fix-brief, unless loop counter ≥ 3 (then surface as blocked).

## Scoring Math

Raw score ∈ [0, 110]:
- 10-point dimensions × 10 = 100
- 5-point dimensions × 2 = 10

Default pass threshold: **82 / 110**. Normalization to /100 is lossy and only for display.

A dimension scoring **0** is a critical failure. Two or more critical failures forces `verdict: FAIL` regardless of total.

`density_score < 3.0` forces `verdict: FAIL` regardless of total.

## Example

```markdown
---
persona_skill: steve-jobs-mirror
persona_skill_version: 0.2.0
persona_judge_version: 0.1.0
evaluated_at: 2026-04-14T10:00:00Z
overall_score_raw: 90
overall_score_normalized: 82
pass_threshold_raw: 82
verdict: PASS
density_score: 6.8
critical_failures: 0
dimensions:
  known_test: 9
  edge_test: 8
  voice_test: 9
  knowledge_delta: 8
  mindset_transfer: 8
  anti_pattern_specificity: 8
  specification_quality: 4
  structure: 4
  density: 7
  internal_tensions: 9
  honest_boundaries: 8
  primary_source_ratio: 8
---

## Summary
PASS at 82/100. Strongest on voice and known-test reproduction; weakest on density (still some "正确废话" in decision-heuristics §3).

## Dimension Scores
| Dimension | Score | Max | Notes |
| --- | --- | --- | --- |
| Known Test | 9 | 10 | 3/3 close reproductions |
| Edge Test | 8 | 10 | Uncertainty expressed well |
| ... | | | |

## Strengths
- Voice test: 9/10 blind identification
- Internal tensions: 3 well-documented pairs

## Weaknesses
- Decision-heuristic #3 too generic ("focus on users") — reads as 正确废话

## Recommended Actions
1. Rewrite `components/decision-heuristics.md` heuristic #3 with specific 1984-Macintosh case
2. Add primary-source citations for heuristic #5 in `knowledge/articles/`
```
