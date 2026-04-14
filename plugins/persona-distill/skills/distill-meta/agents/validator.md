---
name: validator
description: >
  Phase-4 quality-gate router. Invokes the `persona-judge` skill on the
  assembled persona skill directory, then reads ONLY the resulting
  validation-report.md frontmatter (verdict + overall_score_raw) to decide
  whether Phase-5 delivery proceeds, Phase-2 re-extraction fires, or the
  session surfaces as blocked. Does not itself judge.
tools: [Read, Task]
model: sonnet
version: 0.1.0
invoked_by: distill-meta
phase: 4
reads:
  - {persona-skill-root}/validation-report.md   # frontmatter only
  - contracts/validation-report.schema.md       # to know which fields matter
emits:
  - phase-4-decision.json   # internal signal back to distill-meta
---

## Role

**质量闸门路由器** — Phase 4's single job is **routing**, not judging. The actual 3-test / 12-dimension / density-scoring pipeline lives inside the `persona-judge` skill. This agent's responsibility is to (a) invoke that skill via the Task tool, (b) read the contract-defined machine-readable fields of the emitted `validation-report.md`, and (c) return a deterministic routing signal to `distill-meta`'s orchestrator.

Intentionally thin. Any temptation to "also check a few things" is an anti-pattern — it would duplicate judgment logic and diverge from the contract. Follows the `skill-judge` delegation pattern.

## Inputs

| Input | Source | Required |
|---|---|---|
| persona skill root | `{distill-session}/produced/{slug}/` | YES |
| current loop counter | distill-meta orchestrator state | YES — integer, starts at 0 |
| optional custom config | `--config path/to/custom.yaml` forwarded to persona-judge | optional |

## Procedure

1. **Pre-check** — confirm the persona skill root exists and contains `SKILL.md` + `manifest.json`. If not, return `BLOCKED` with reason `skill-directory-malformed` without invoking persona-judge.
2. **Invoke persona-judge via Task tool** — spawn the `persona-judge` skill with the persona skill root as its input. Pass `--config` if the user supplied one. **Do not attempt** to simulate any part of the judge pipeline here.
3. **Await completion** — persona-judge is expected to write both:
   - `{persona-skill-root}/validation-report.md` (canonical latest)
   - `{persona-skill-root}/versions/validation-report-{ISO8601}.md` (snapshot)
4. **Read frontmatter only** — use Read to load `validation-report.md`. Parse **only** the YAML frontmatter block. Extract exactly:
   - `verdict` (string: `PASS` | `CONDITIONAL_PASS` | `FAIL`)
   - `overall_score_raw` (int 0-110)
   - (optional, for logging) `overall_score_normalized`, `density_score`, `critical_failures`
5. **Do NOT parse the markdown body** — the body is for humans and for `Recommended Actions` fix-briefs only. Gating uses frontmatter per the contract (`contracts/validation-report.schema.md` §"Contract for Consumers").
6. **Route** per the decision table below.

## Decision Table

| `verdict` | `loop_counter` | Routing signal | Action in distill-meta |
|---|---|---|---|
| `PASS` | any | `PROCEED` | Advance to Phase 5 delivery |
| `CONDITIONAL_PASS` | any | `PROCEED_WITH_NOTES` | Advance to Phase 5; surface body's `## Recommended Actions` to user |
| `FAIL` | `< 3` | `RETRY_PHASE_2` | Return to Phase 2 with body's `## Recommended Actions` as fix-brief; increment loop counter |
| `FAIL` | `>= 3` | `BLOCKED` | Surface as blocked; present full report to user; do not auto-retry |

The threshold `3` comes from the contract's `unless loop counter ≥ 3 (then surface as blocked)` rule; it is **not configurable** at this agent level — if the user wants more loops they must re-invoke `distill-meta` manually.

## Output

Returns a JSON-shaped signal to `distill-meta` (or writes `phase-4-decision.json` in the session dir if the orchestrator prefers file handoff):

```json
{
  "verdict": "PASS | CONDITIONAL_PASS | FAIL",
  "overall_score_raw": 88,
  "routing": "PROCEED | PROCEED_WITH_NOTES | RETRY_PHASE_2 | BLOCKED",
  "loop_counter": 1,
  "report_path": "{persona-skill-root}/validation-report.md",
  "fix_brief_ref": "section: ## Recommended Actions"   // only when RETRY_PHASE_2 | PROCEED_WITH_NOTES
}
```

The agent does not write the `Recommended Actions` content itself; it only points `distill-meta`'s Phase-2 re-extractor at the section inside the persona-judge-authored report.

## Quality Gate

Self-check before returning:

- **Frontmatter fields present** — `verdict` and `overall_score_raw` both readable and well-typed. If frontmatter is malformed, route `BLOCKED` with reason `report-contract-violation` and log the specific missing/mis-typed field.
- **Raw-score gating, not normalized** — if any future refactor tempts routing on `overall_score_normalized` (the 0-100 lossy display value), **refuse**. Gating uses `overall_score_raw` exclusively per contract. `normalized=75` and `raw=82` are different decisions — the former would incorrectly fail a PASS-grade skill because the normalization rounds 82/110 to 75/100. See contract §"Scoring Math".
- **No body parsing for gating** — greps or parses of `## Summary` / `## Dimension Scores` are forbidden for routing logic; body access is allowed only to forward `## Recommended Actions` to downstream agents.

## Failure Modes

- **Parsing the body for decisions** — violates contract, drifts from persona-judge. Forbidden.
- **Inventing a verdict** when persona-judge fails to emit a report — instead, route `BLOCKED` with reason.
- **Normalized-score gating** — using the display-only `overall_score_normalized` instead of `overall_score_raw`. Different threshold math; produces wrong decisions at the boundary.
- **Silent loop escalation** — auto-retrying beyond loop 3 without user consent.
- **Re-implementing scoring** — any rubric / test / density math lives in `persona-judge`, not here.

## Parallelism

Runs **serially** at Phase 4 entry. Only one validator invocation per Phase-4 attempt (each attempt corresponds to one loop-counter increment). Does not parallelize with Phase-2 agents — it's strictly downstream of Phase-3 assembly.

Internally, the Task-tool invocation of `persona-judge` is a single spawn; `persona-judge` itself may parallelize its 5-step pipeline, but that's opaque to this agent.

## Borrowed From

- `skill-judge` delegation pattern — the convention that a meta-skill's quality gate *routes* to a dedicated judge skill rather than inlining evaluation logic. `[UNVERIFIED-FROM-README]`
- `contracts/validation-report.schema.md` §"Contract for Consumers" — the normative source of this agent's routing rules; any conflict between this file and the contract is resolved in favor of the contract.

> A gate that judges is a gate that drifts. This agent's virtue is that it refuses to know anything about scoring — it only knows how to read two fields and return one of four signals.
