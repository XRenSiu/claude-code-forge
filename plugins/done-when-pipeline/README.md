# done-when-pipeline (v1.0)

Turn fuzzy natural-language requirements into **machine-verifiable completion contracts** that independent agents can mechanically check — no human in the loop at verification time.

## Why this exists

Making an AI agent autonomously finish a task is not bottlenecked by "making it code." It is bottlenecked by **telling it when it is done**. The completion criteria must be:

- **Mechanically verifiable** — no human subjective check
- **Independently verifiable** — the agent that builds and the agents that judge are different sessions (and ideally different vendors)
- **Reward-hacking resistant** — passing the form must require passing the substance
- **Traceable** — every check ties back to a stated requirement

This plugin gives you nine skills in a two-layer topology that produce, exercise, and verify that contract.

> **Want the full end-to-end flow with skill topology + four-state ratchet diagram?** See [`docs/pipeline-flow.md`](docs/pipeline-flow.md). This README is the quickstart; pipeline-flow.md is the reference.

## v1.0 architecture: 9 skills, 2 layers

```
Layer 1 — Standalone skills (each user-invocable, no required dependencies on done_when.yaml)
─────────────────────────────────────────────────────────────────────────────────────────────

Contract producers:
  /acceptance-spec ─────────►  specs/<feature>/spec.md + done_when.yaml + spec-robustness.md
                                (NL → EARS; existence+behavior+rules schema; S2.5 anti-gaming pass)

  /test-suite-generator ────►  tests/<feature>/  (existence/unit/integration/e2e/mutation;
                                5 sub-steps, batch-by-batch)

Independent review skills (any subset usable; each works on any spec+code pair):
  /code-reviewer ───────────►  diff → findings (focus: security/logic/perf/style/all)
  /qa-reviewer ─────────────►  test execution + maintenance-vs-genuine classification → qa-report
  /pm-reviewer ─────────────►  Agent-as-Judge per-REQ compliance (4-state TicketCompliance verdict)
  /spec-drift-detector ─────►  spec vs code factual divergence (3 types: timing/behavior/contract)
  /spec-gaming-detector ────►  6 RHD patterns + diff mode → gaming_risk_score + spec_robustness_gaps
  /meta-judge ──────────────►  synthesize findings → PASS / BLOCK_MERGE / NEEDS_HUMAN

Layer 2 — Orchestrator (consumes Layer 1)
─────────────────────────────────────────

  /acceptance-fleet ────────►  ratchet-log/iteration-NNN/
                                (dispatches the 6 review skills in parallel against an impl,
                                 hands findings to /meta-judge, decodes the verdict into
                                 four-state ratchet: DONE / FIX / SPEC_DRIFT / GAMING_RISK)
```

Key property of the topology: **the 6 review skills do not know `done_when.yaml` exists**. Each works on any spec format (EARS / Jira / PRD / issue / PR description). `/acceptance-fleet` is just one of their consumers; you can also call `/code-reviewer` on any PR, or `/spec-drift-detector` on any aging codebase, with no connection to the rest of the pipeline.

## Quick start

### Full pipeline (Steps 1-6)

```
# Step 1-3: clarify + write contract
/acceptance-spec  "users can cancel their subscription but keep access until end of paid period"

# Step 4: derive test pyramid
/test-suite-generator  specs/subscription-cancellation/

# Implement in src/ — must be a fresh session (impl agent never sees evaluator prompts)

# Step 5-6: orchestrated review + ratchet
/acceptance-fleet  specs/subscription-cancellation/
```

### Standalone review (any review skill, on any code)

```
# Review a PR for security issues, adversarial mode, cross-vendor
/code-reviewer  HEAD~3..HEAD  --focus=security --adversarial

# Verify a Jira ticket against the implementation
/pm-reviewer  jira-export.md  src/

# Audit doc-code consistency on a legacy codebase
/spec-drift-detector  docs/  src/

# Synthesize multiple review outputs into one decision
/meta-judge  ./review-outputs/  --rules=./team-policy.yaml
```

## Migrating from v0.x

If you used the `0.3.x` line:

| v0.x | v1.0+ |
|---|---|
| 3 skills (`acceptance-spec`, `test-suite-generator`, `acceptance-fleet`) | **9 skills** (the 3 originals + 6 newly-standalone review skills) |
| `acceptance-fleet` had 7 evaluator roles + meta-judge embedded internally | `acceptance-fleet` is pure orchestrator; the 7 roles are now 6 standalone skills + `/meta-judge` |
| `done_when.yaml` had `existence + behavior + fitness` layers | `done_when.yaml` has **`existence + behavior + rules`** (`fitness:` retired per HTML v2 §3.5; truly-unautomatable cases route to `/pm-reviewer`'s `requires_human_verification` verdict) |
| `test-suite-generator` had sub-steps 4-A through 4-F | **4-A through 4-E only**; 4-F (fitness rubric) retired |
| Legacy `done_when.yaml` with `fitness:` block | rejected by both `/test-suite-generator` and `/acceptance-fleet` schema validators; re-generate via `/acceptance-spec` v1.0+ |

`ratchet-log/` directory layout is unchanged — old logs remain readable.

## Design philosophy

1. **Verifiable beats judgeable.** Per HTML v2 §3 principle I (and §3.5 corollary): most claims that *feel* like they need an LLM judge can be re-designed as programmatic checks. The genuinely-unautomatable ~10% are honestly handled by `/pm-reviewer`'s `requires_human_verification` verdict, not faked as an LLM rubric score.
2. **Independence-by-default.** Each review skill is independently invocable. "In some context I frequently use this" ≠ "this skill should live in that context." `/spec-gaming-detector` is useful in the done_when pipeline AND for general AI-coding gaming audits AND for KPI gaming reviews — so it's a standalone skill, not a fleet phase.
3. **Multi-agent debate amplifies bias.** *Judging with Many Minds* (Dartmouth/Yale 2025) showed debate frameworks amplify position / verbosity / CoT / bandwagon bias after round 1. `/meta-judge` is the non-debating synthesizer that replaces the bias-amplifying alternative.
4. **Model diversity > evaluator count.** Per the Milvus benchmark: Claude + Gemini found 91% of bugs a 5-vendor ensemble found. Cross-vendor (Codex / Gemini CLI) is the cost-effective sweet spot. `/code-reviewer --adversarial` and `/spec-gaming-detector` are the two slots where it matters most — `/acceptance-fleet` allocates cross-vendor there if available.
5. **Spec drift is a first-class failure mode.** If PBT keeps finding counterexamples or `/spec-drift-detector` reports recurring divergence, the spec is the bug. `/acceptance-fleet` escalates to `SPEC_DRIFT` state and hands back to `/acceptance-spec` instead of piling on more code patches.
6. **Anti-reward-hacking is mandatory.** `/spec-gaming-detector` runs every iteration; gaming_risk_score >= 7 triggers `GAMING_RISK` state which hands back to `/acceptance-spec` for contract hardening. The contract author gets a `spec_robustness_gaps:` block with concrete fixes.

## Integration with existing claude-code-forge assets

| Existing | Role here |
|---|---|
| `/ratchet` | Legacy alternative to `/acceptance-fleet`. No gaming detection, no four-state ratchet. Acceptable for small features or environments without the v1.0 skill set installed. See `INTEGRATION.md`. |
| `forge-teams` | Optional implementation team during the impl phase. Runs orthogonally to `/acceptance-fleet`'s review skills. |
| Codex CLI / Gemini CLI | Cross-vendor evaluators consumed by `/acceptance-fleet` for adversarial code review and gaming detection. If neither is available, falls back to medium isolation (mixed Claude sizes) with a logged warning. |

## What this plugin does **not** do

- It does not implement the feature. (Hand the spec to your implementer of choice — must run in a fresh session that cannot see the review skills' prompts.)
- It does not bundle Hypothesis / fast-check / testcontainers. (Those are tool stacks the generated tests *use*; install them in the target project.)
- It does not bundle Codex CLI or Gemini CLI. (`/acceptance-fleet` detects them at S0; install them yourself for cross-vendor evaluation.)
- It does not replace OpenSpec or GitHub Spec Kit. It re-uses their *ideas* without dragging in their CLIs.

## Version

**1.0.0** (BREAKING) — major architectural refactor per HTML v2 design:
- Extracted 6 standalone review skills from the monolithic `/acceptance-fleet`: `/code-reviewer`, `/qa-reviewer`, `/pm-reviewer`, `/spec-drift-detector`, `/spec-gaming-detector`, `/meta-judge`. Each user-invocable on its own.
- `/acceptance-fleet` refactored to pure orchestrator (dispatches the 6, decodes meta-judge verdict into 4-state ratchet, persists trace).
- Retired the `fitness:` layer in `done_when.yaml` per HTML v2 §3.5; the schema now has `existence + behavior + rules`. Truly-unautomatable cases route to `/pm-reviewer`'s `requires_human_verification` verdict.
- Retired sub-step 4-F (fitness rubric) in `/test-suite-generator`. The skill now has 5 sub-steps (4-A through 4-E).
- Plugin description rewrites + new keywords for the 6 standalone skills.

History:
- 0.3.x — three-role validation pass; landed `/acceptance-fleet` v0.1 as monolithic 7-role fleet.
- 0.2.0 — three-role validation pass; surfaced 17 P0 issues and hardened the skill source.
- 0.1.0 — initial release, covered Steps 1-4 only; Step 5-6 was manual hand-off to `/ratchet`.

See `INTEGRATION.md` for hand-off recipes and `docs/pipeline-flow.md` for the full reference.
