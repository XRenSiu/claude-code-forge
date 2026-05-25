# Integration with adjacent skills & tools (v1.0.0)

`done-when-pipeline` v1.0.0 covers Steps 1-6 of the source design doc internally — the nine skills in this plugin form a complete topology, and no hand-off to an external skill is required to run the pipeline end-to-end. This file documents the *optional* integrations: legacy fall-backs, implementation-side helpers, cross-vendor evaluators, and what deliberately stays separate.

Rewritten on 2026-05-25 alongside the v1.0.0 release (which extracted the 6 standalone review skills and retired the fitness layer). The previous v0.3.x version of this file documented hand-offs that no longer exist as separate steps — those sections have been removed.

> **Quickstart is in [`README.md`](README.md). End-to-end reference is in [`docs/pipeline-flow.md`](docs/pipeline-flow.md).** This file is *only* about boundaries with things outside this plugin.

---

## Pipeline boundaries (v1.0.0)

```
Step 1-3  →  /acceptance-spec          (this plugin)
Step  4   →  /test-suite-generator     (this plugin)
Step  5   →  user-chosen impl agent    (fresh session, REQUIRED)
Step 5-6  →  /acceptance-fleet         (this plugin) — orchestrator
                ├─ dispatches the 6 review skills (this plugin)
                └─ /meta-judge synthesizes               (this plugin)
```

Everything in the pipeline lives inside this plugin. The only place where you *must* leave the plugin is the implementation phase (Step 5): the impl agent must run in a fresh session that cannot see the review skills' prompts. Use any agent (Claude Code subagent, Cursor, Aider, a human) — see "Optional: forge-teams as implementer" below.

---

## Optional integration 1 — Cross-vendor evaluators (Codex CLI / Gemini CLI)

`/acceptance-fleet` S0 detects available evaluator runtimes and picks the highest isolation level it can reach. If `which codex` or `which gemini` succeeds, the fleet runs in **strong** isolation: cross-vendor agents take the two slots where same-vendor blind spots hurt most.

| Skill slot | Cross-vendor when available | Why this slot |
|---|---|---|
| `/code-reviewer --focus=security --adversarial` | Codex or Gemini | Adversarial review is where Claude-reviewing-Claude sycophancy hurts most. |
| `/spec-gaming-detector` | Codex or Gemini | Gaming detection requires an adversarial stance that benefits from architectural diversity. |

Per the Milvus benchmark (referenced in `skills/acceptance-fleet/references/evaluation-isolation-levels.md`): Claude + one other vendor catches ~91% of bugs that a 5-vendor ensemble catches — cross-vendor is the cost-effective sweet spot.

**Installation:** outside this plugin's scope. Install `codex` and/or `gemini` per their vendor docs and verify they are on `PATH`. If neither is available, `/acceptance-fleet` falls back to **medium** isolation (mixed Claude sizes) and logs a warning. If even medium cannot be guaranteed (single-session-only environment), the fleet refuses to run — see `skills/acceptance-fleet/references/evaluation-isolation-levels.md`.

---

## Optional integration 2 — `forge-teams` as implementer

For large features where adversarial review *at implementation time* is worthwhile, wrap the impl phase with `forge-teams`. This is orthogonal to `/acceptance-fleet`: forge-teams structures the inner-loop multi-agent collaboration during implementation; `/acceptance-fleet` then evaluates the result independently. Neither side reads the other's prompts.

```
# Step 5 (impl) — fresh session
[any forge-teams workflow on src/ guided by specs/<feature>/]

# Step 5-6 (review) — separate session, isolation enforced
/acceptance-fleet specs/<feature>/
```

The two-session boundary is the critical anti-gaming guarantee. Most features don't need forge-teams during impl — a plain impl agent + `/acceptance-fleet` review is faster and cheaper.

---

## Optional integration 3 — Legacy `/ratchet` (alternative to `/acceptance-fleet`)

`/ratchet` is the pre-v0.3 hand-off path. It's lighter (single-stream subagent loop, no parallel fleet), and acceptable when:

- the feature is small enough that the multi-agent overhead isn't worth it
- the environment cannot install Codex / Gemini *and* cannot host parallel sub-agents
- you explicitly want a two-state (continue / stop) loop instead of the four-state ratchet

What you lose vs. `/acceptance-fleet`:

| Capability | `/acceptance-fleet` (v1.0.0) | `/ratchet` |
|---|---|---|
| `done_when.yaml` direct consumption | yes | no — you translate manually |
| Parallel review fleet | yes (6 skills) | no (single subagent) |
| Per-iteration gaming detection | yes | no |
| Per-iteration drift detection | yes | no |
| Four-state ratchet (`SPEC_DRIFT` / `GAMING_RISK` escapes) | yes | no — only continue / stop |
| `ratchet-log/iteration-NNN/` audit trail | yes | partial (own format) |
| Cross-vendor adversarial review | yes | no |

### How to translate `done_when.yaml` into a `/ratchet` invocation

`/ratchet` builds its own contract from a natural-language goal — it does not parse `done_when.yaml`. The mechanical translation:

```
/ratchet
  Goal: Implement the feature in specs/<feature>/spec.md.

  Criteria (P0, all must pass):
    - bash tests/<feature>/existence.sh exits 0
    - pytest tests/<feature>/unit/ -x passes all tests
    - pytest tests/<feature>/integration/ passes all tests
    - playwright test tests/<feature>/e2e/ passes
    - bash tests/<feature>/mutation.sh exits 0   # mutation_kill_rate ≥ threshold

  Scope:
    CAN modify:    src/
    CANNOT modify: specs/, tests/    # frozen — these are the contract

  done_when:
    success:     all P0 criteria pass
    convergence: 3 consecutive rounds with no new test passing
    budget:      max 15 rounds        # heuristic; tune per feature
```

| `/ratchet` field | Value | Source from `done_when.yaml` |
|---|---|---|
| `success` | "all P0 criteria pass" | One line per existence script + behavior layer + mutation threshold. |
| `convergence` | "3 rounds with no improvement" | Numerically equals `spec_drift_threshold.max_fix_loops_before_escalation` (default `3`). Semantically not identical — `escalate` is a user-prompt action; `convergence` just stops the loop. After ratchet stops, you (not ratchet) decide whether to return to `/acceptance-spec` (spec is wrong) or re-invoke `/ratchet` with more budget (code is wrong). |
| `budget` | 15 (heuristic) | Not a contract field. Typical small features converge in 5-8 rounds; 2× headroom + buffer ≈ 15. Tune up for large features. Setting `budget == convergence` makes the loop stop the first time the convergence guard trips — usually too aggressive. |

### After `/ratchet` stops with failing tests — decide which side is wrong

Apply this rule once per stop event (not in a loop):

- **If the failing test's evidence is consistent with the literal REQ text** — i.e. the REQ as written, taken at face value, would produce a misbehaving impl — then the **spec is wrong**. Return to `/acceptance-spec`, narrow the offending REQ, re-run `/test-suite-generator`, then `/ratchet` again.
- **If the evidence contradicts the REQ text** — the REQ says X, the impl does not-X — then the **code is wrong**. Re-invoke `/ratchet` with more budget, optionally a stronger implementer.

Edge cases:
- **PBT failure with no shrunk counterexample** (e.g. `RuleBasedStateMachine` failed inside an `@rule`): treat as code-wrong by default — the impl raised under a legal operation sequence the REQ permits.
- **`mutation_kill_rate` failing but example/PBT tests passing**: code-wrong (the impl is too loose). Re-invoke `/ratchet` with the focused goal "raise mutation kill rate to ≥ threshold without changing test names or thresholds".
- **e2e failing while integration passes**: usually code-wrong at the UI/wiring layer.

This is the manual analogue of what `/acceptance-fleet` does automatically via the `SPEC_DRIFT` / `FIX` state decoding.

---

## What does NOT integrate (kept separate on purpose)

- **`bespoke-design-system`** — visual / aesthetic design system. Behavioral requirements (`done_when` contracts) and visual taste are different problems. If the feature has visual requirements, generate a separate `bespoke-design-system` artifact and reference it from `proposal.md`. Do not encode visual taste in `done_when.yaml`.
- **`persona-distill` / `persona-judge`** — these evaluate the *quality of persona-distillation skills*, not arbitrary artifacts. They are not a general-purpose LLM-as-judge and have no role in this pipeline. The pre-v1.0 design briefly imagined `persona-judge` as the "fitness rubric" judge for Step 4-F; that whole layer was retired in v1.0.0 (see next bullet).
- **The retired `fitness:` layer** — `done_when.yaml` v1.0+ schema is `existence + behavior + rules`; there is no `fitness:` block. Per HTML v2 §3.5 (fitness-check dissolution), ~90% of what was previously written as `fitness:` rubrics is re-expressible as programmatic checks (existence / unit / integration / e2e / mutation), and the genuinely-unautomatable ~10% routes to `/pm-reviewer`'s `requires_human_verification` verdict. Both `/test-suite-generator` and `/acceptance-fleet` schema validators reject legacy `fitness:` blocks; re-run `/acceptance-spec` v1.0+ to regenerate the contract.
- **OpenSpec / GitHub Spec Kit CLIs** — file-format ideas borrowed (proposal/spec/tasks layout, clarify-question style); their CLIs are deliberately not integrated.

---

## Full lifecycle (v1.0.0 — recommended path)

```
1.  /acceptance-spec  "users can cancel their subscription but keep access until end of paid period"
       → specs/subscription-cancellation/
           ├── proposal.md
           ├── spec.md               (EARS, stable REQ-IDs)
           ├── tasks.md
           ├── done_when.yaml        (existence + behavior + rules)
           └── spec-robustness.md    (S2.5 anti-gaming companion)

2.  /test-suite-generator  specs/subscription-cancellation/
       → tests/subscription-cancellation/
           ├── existence.sh
           ├── unit/                 (example + PBT)
           ├── integration/          (testcontainers, no mocks)
           ├── e2e/                  (Playwright/Cypress)
           └── mutation.config       (mutmut/Stryker)

3.  [implement in src/ using any agent in a FRESH SESSION;
     impl agent MUST NOT see /acceptance-fleet's review prompts —
     this is the core anti-gaming guarantee]

4.  /acceptance-fleet  specs/subscription-cancellation/
       → ratchet-log/iteration-001/
       → final_state: DONE | FIX | SPEC_DRIFT | GAMING_RISK | NEEDS_HUMAN

5.  Route by state:
       DONE          → ship it
       FIX           → feed ratchet-log/iteration-001/fix-prompt.md
                       to a fresh impl session, then GOTO 4
       SPEC_DRIFT    → GOTO 1 with the offending REQs as a narrow brief
       GAMING_RISK   → GOTO 1 to close the surfaced vectors in spec-robustness.md
       NEEDS_HUMAN   → answer the surfaced questions; /acceptance-fleet resumes
```

Per-iteration cost with prompt caching: ~$0.84. Typical feature converges in 2-4 iterations: ~$2-4 per feature acceptance. See `skills/acceptance-fleet/SKILL.md` § "Cost expectation (per iteration)" for the per-skill breakdown.

## Legacy lifecycle (pre-v0.3.0, `/ratchet` path)

```
1.  /acceptance-spec  "..."
2.  /test-suite-generator  specs/<feature>/
3.  /ratchet  <paste Goal + Criteria + Scope + done_when block per
              "How to translate done_when.yaml into a /ratchet invocation" §>
4.  After /ratchet stops, apply the "spec wrong vs code wrong" rule
    in the same § to decide whether to re-invoke /ratchet or return to /acceptance-spec.
```

Acceptable for small features or environments without the v1.0 stack installed. For anything non-trivial, the v1.0 path catches more bugs per dollar (more parallelism + per-iteration drift/gaming detection + four-state escape from FIX-loop thrashing).
