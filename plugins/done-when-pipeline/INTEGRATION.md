# Integration with existing claude-code-forge skills

The done-when-pipeline plugin covers Steps 1-6 of the source design doc as of v0.3.0. Step 5 (execution / fleet evaluation) and Step 6 (four-state ratchet + closed-loop iteration) are owned by the new `/acceptance-fleet` skill in this plugin; the legacy hand-off to the standalone `/ratchet` skill remains supported as a lighter path. This file documents both paths and what each adjacent skill does and does not do for us.

This file was rewritten on 2026-05-24 after the round-1 self-validation pass found that the previous version overclaimed the integrations (see `specs/done-when-skills/_skill-issues.md` ISSUE-002 and ISSUE-003), and again on 2026-05-25 to reflect the new `acceptance-fleet` skill landing as the recommended Step 5-6 path.

---

## Pipeline boundaries (honest version)

```
Step 1-3  →  /acceptance-spec               (this plugin) — 5-file output incl. spec-robustness.md
Step  4   →  /test-suite-generator          (this plugin)
Step 5-6  →  /acceptance-fleet              (this plugin — RECOMMENDED) — 7-role fleet + meta-judge + 4-state ratchet
   OR     →  /ratchet                       (external — LEGACY) — single-stream subagent loop, manual hand-off
Step 4-F  →  fitness rubrics are inputs to an inline Claude-with-rubric pattern
              (no packaged "fitness judge" skill exists yet; see below)
```

The boundaries that look like automation but aren't (still true under v0.3):
- `/ratchet` does **not** parse our `done_when.yaml`. It builds its own `ratchet.md` + `evaluate.sh` from a NL goal. (Use `/acceptance-fleet` if you want direct YAML consumption.)
- `persona-judge` does **not** consume our fitness rubric files. It's a quality gate for distilled persona skills, not a general-purpose LLM-as-judge.

---

## Handoff: test-suite-generator → acceptance-fleet (recommended, automated)

This is the v0.3.0 path. After `test-suite-generator` writes `tests/<feature>/`, the user invokes `/acceptance-fleet specs/<feature>/`. No translation step — the skill reads `done_when.yaml`, `spec-robustness.md`, `spec.md`, and the generated tests directly.

```
/acceptance-fleet specs/subscription-cancellation/
```

What runs internally (per iteration):

1. **S0 Bootstrap** — checks inputs, detects available evaluator runtimes, picks isolation level (weak / medium / strong / extreme — see `skills/acceptance-fleet/references/evaluation-isolation-levels.md`).
2. **S1 Fleet spawn** — 8 evaluators in parallel: `test-runner`, `existence-checker`, `requirement-tracer`, `design-reviewer`, `adversarial-reviewer` (cross-vendor preferred — Codex or Gemini), `edge-case-hunter`, `e2e-explorer`, `spec-gaming-detector`. Each runs independently; no inter-agent communication.
3. **S2 Rebuttal pass** — every finding gets challenged once by a different evaluator (4-Eyes Principle). Successfully rebutted findings are dropped.
4. **S3 Meta-judge** — single Opus session synthesizes the surviving findings: dedupe by `file:line + root_cause`, weight by source diversity (multi-vendor agreement = boost), check thresholds, classify state. Does NOT re-review code.
5. **S4 Ratchet decision** — one of four states: `DONE` (success, exit), `FIX` (emit fix-prompt for next iteration), `SPEC_DRIFT` (PBT counterexamples consistent with REQ text recurring — return to /acceptance-spec, do NOT patch code), `GAMING_RISK` (gaming_risk_score ≥ 7 from spec-gaming-detector — return to /acceptance-spec for contract hardening, do NOT patch code). A fifth escape `NEEDS_HUMAN` surfaces if meta-judge cannot decide.
6. **S5 Persist** — writes a complete `ratchet-log/iteration-NNN/` trace: per-role outputs, rebuttals, meta-judge output, state-specific report, full input checksums. Required for debugging, training-data reuse, and audit.

### Why this path (vs. legacy /ratchet)

- **Direct YAML consumption** — no manual translation step.
- **Spec-gaming-detector runs every iteration** — catches assertion weakening and dead-code padding that single-stream `/ratchet` would miss.
- **Cross-vendor adversarial review** — the Claude-reviewing-Claude sycophancy loop is broken when Codex/Gemini takes the adversarial-reviewer slot.
- **Four-state ratchet, not two** — `SPEC_DRIFT` and `GAMING_RISK` are first-class outcomes that route to /acceptance-spec instead of looping FIX endlessly.
- **Full audit trail** — `ratchet-log/` is the substrate for debugging and (eventually) RLHF/DPO training data.

### When /acceptance-fleet refuses to run

- Missing inputs (`spec.md`, `done_when.yaml`, `tests/<feature>/`).
- Cannot guarantee at least **medium** isolation (single-session-only environment). Reason: implementation agents seeing evaluator prompts = gaming substrate. See `skills/acceptance-fleet/references/evaluation-isolation-levels.md`.
- `done_when.yaml` schema violation (v1 strict — does not attempt to repair).

Missing `spec-robustness.md` does NOT cause refusal — it produces a warning and the spec-gaming-detector runs in maximum suspicion mode. (Recommended: re-run `/acceptance-spec` to produce it; the S2.5 phase is what gives `/acceptance-fleet` its targeted hunting hints.)

### Cost expectation

~$0.75 per iteration with prompt caching. Typical feature converges in 2-4 iterations under the four-state machine (since spec-drift and gaming-risk escape FIX-loop thrashing). Budget ~$2-3 per feature acceptance. Cross-vendor evaluators cost more per call but catch more per iteration; net cost usually lower.

---

## Handoff: test-suite-generator → ratchet (legacy, manual)

After `test-suite-generator` writes `tests/<feature>/`, the user can chain to `/ratchet`. This is a manual handoff — the user phrases the ratchet goal so ratchet's own Step 1-3 (goal clarification + criteria design + ratchet.md generation) can derive its own internal contract from our artifacts.

Recommended invocation:

```
/ratchet
  Goal: Implement the feature in specs/<feature>/spec.md.

  Criteria (P0, all must pass):
    - bash tests/<feature>/existence.sh exits 0
    - pytest tests/<feature>/unit/ -x passes all tests
    - pytest tests/<feature>/integration/ passes all tests
    - playwright test tests/<feature>/e2e/ passes
    - bash tests/<feature>/mutation.sh exits 0   # mutation_kill_rate >= 0.70

  Scope:
    CAN modify:    src/ (or whichever implementation paths the spec implies)
    CANNOT modify: specs/, tests/    # frozen — these are the contract

  done_when:
    success:     all P0 criteria pass
    convergence: 3 consecutive rounds with no new test passing
    budget:      max 15 rounds        # default heuristic, see "Translation
                                      # parameters" below — tune per feature
```

### Translation parameters — where the numbers come from

The values in the `done_when:` block above are not magic constants; each is derivable from `done_when.yaml` or a documented default:

| Ratchet field | Value | Source |
|---|---|---|
| `success` | "all P0 criteria pass" | The criteria list above is the **mechanical reading** of `done_when.yaml`: 1 line per existence script + 1 line per behavior layer + 1 line per mutation threshold. fitness criteria are *not* in this list — they're consumed manually per their how-to-run block (see §"Handoff to fitness-judge" below). |
| `convergence` | "3 consecutive rounds with no new test passing" | Numerically equals `spec_drift_threshold.max_fix_loops_before_escalation` (default `3`). **Semantic caveat**: `max_fix_loops_before_escalation` literally means "after this many fix loops without progress, escalate to the user to judge spec-vs-code"; ratchet's `convergence` means "after this many stalled rounds, stop the loop". The numbers map cleanly, but `escalate` is a user-prompt action and `convergence` is just a stop action — *they are not strictly equivalent*, and after ratchet stops you (not ratchet) decide whether to come back to `/acceptance-spec` (spec is wrong) or re-invoke `/ratchet` with more budget (code is wrong). See "How to decide: spec wrong vs code wrong" below. |
| `budget` | 15 | **A practical heuristic, not a contract field.** Comes from: typical small-feature implementations converge in 5-8 rounds; a 2x headroom plus a single bailout buffer = ~15. Tune up for large features (multi-module / many integration paths) or down for trivial single-function changes. Setting `budget == convergence` (e.g. both 3) makes the loop stop the first time the convergence guard trips, which is usually too aggressive. There is no design-doc number for `budget`; pick a value that lets `convergence` trigger normally before `budget` does. |

What happens then:
1. Ratchet's own Step 1-3 runs: it reads the goal/criteria/scope above, writes `<experiment-dir>/ratchet.md` + `<experiment-dir>/evaluate.sh` (which is effectively a wrapper around our test commands).
2. Ratchet's Step 4 starts the master/subagent loop. The subagent implements code; master runs `evaluate.sh`; kill-and-restart on stall.
3. Ratchet's Step 5 wraps up when its own `done_when` triggers.

What ratchet does NOT do (despite earlier wording in this file):
- It does not parse our `done_when.yaml` directly.
- It does not honor a `spec_drift_threshold.max_fix_loops_before_escalation` field from our YAML.
- It does not automatically escalate "PBT failures look like spec bugs, not code bugs" back to the user — that escalation logic is not in ratchet today.

---

## "Spec drift" guidance (not auto-honored)

Our `done_when.yaml` carries a `spec_drift_threshold:` block. Per the v1 schema, it has **exactly one** sub-field (see `skills/acceptance-spec/SKILL.md` § "Hard rules for v1 字面" and `references/done-when-schema.yaml`):

```yaml
spec_drift_threshold:
  max_fix_loops_before_escalation: 3
```

Do not add `applies_to:` or any other key — strict v1 parsers will reject it. The threshold applies uniformly to *any* test failure category that keeps repeating across fix loops (PBT, mutation, e2e); v1 does not let you scope it per-category.

**This block is guidance for the human composing the `/ratchet` invocation**, not a contract field anything reads automatically. Concretely, when chaining to ratchet, translate it as:

- Set ratchet's `convergence` to `max_fix_loops_before_escalation` (here: 3 rounds with no improvement → stop).
- After ratchet stops, the user (not the loop) decides whether the failure means "spec is wrong, go back to /acceptance-spec" or "code is wrong, re-invoke /ratchet with more budget".

If you want auto-escalation, that needs to be built either (a) as a wrapper skill around ratchet that reads our `spec_drift_threshold:` and post-processes ratchet's exit, or (b) as a modification inside ratchet itself. Neither exists yet; do not promise the user this behavior.

(The source design doc §8.4 describes auto-escalation as a desirable property; we explicitly mark it as future work.)

### How to decide: spec wrong vs code wrong

After ratchet's `convergence` triggers a stop with PBTs still failing, the user (not the loop) decides which side of the contract is broken. Use this rule:

- **If the PBT's shrunk counterexample is *consistent* with the literal text of the REQ that produced the test** — i.e. the REQ as written, taken at face value, would also produce a misbehaving implementation — then the **spec is wrong**. Return to `/acceptance-spec`, re-open the relevant REQ, and run a focused clarify pass to narrow it. Once `done_when.yaml` is updated, re-run `/test-suite-generator` (the existing tests for that REQ get regenerated), then re-invoke `/ratchet`.
- **If the counterexample contradicts the REQ's text** — i.e. the REQ says X, the shrunk input demonstrates the impl does not-X — then the **code is wrong**. Re-invoke `/ratchet` with more budget (e.g. `budget: max 25 rounds`) and possibly a stronger implementer (`--implementer-team forge-teams` if not already used). Do not change the spec.

Edge cases:
- **PBT fails with no shrunk counterexample available** (e.g. `RuleBasedStateMachine` failed in a `@rule` not an `@invariant`): treat as code-wrong by default — the impl raised under a legal operation sequence the REQ permits.
- **mutation_kill_rate failing** but example/PBT tests passing: this is **code-wrong** (the test suite is fine but the impl is too loose). Re-invoke `/ratchet` with a focused goal "raise mutation kill rate to ≥ 70% without changing test names or thresholds".
- **e2e tests failing** while integration tests pass: usually **code-wrong** at the UI/wiring layer. Re-invoke `/ratchet`. Spec is rarely wrong if the integration layer agrees with it.

This rule is a *judgment heuristic*, not a contract field. Apply it once per stop event; do not loop on it.

---

## Handoff: test-suite-generator → fitness-judge (4-F) — **what actually exists**

The source design doc §6.7 and §11.2 list `persona-judge` as the Step 4-F judge. After investigation (round 1 of self-validation), this is a category error: the `persona-judge` skill in `plugins/persona-distill/` evaluates the **quality of persona-distillation skills** (input contract: "a persona skill root directory"; output: a 12-dimension validation report). It is not a general-purpose LLM-as-judge that can score arbitrary artifacts against a custom rubric.

So Step 4-F as designed has no packaged consumer in this marketplace today. **What you actually do:**

- For criteria with `judge: programmatic` — write a small script that returns pass/fail. This is the strongly preferred path; reach for it whenever possible.
- For criteria with `judge: llm-rubric` — the rubric file is intended to be loaded by a fresh Claude session (no implementer context) which reads the rubric + the artifacts + emits a score. The user invokes this manually: open a clean session, paste the rubric file, paste the artifact paths, ask Claude to score per the rubric's sub-dimensions. This is documented in `skills/test-suite-generator/references/fitness-rubric-guide.md` as the "Claude-with-rubric inline" pattern.
- For criteria with `judge: manual` — a human runs the checklist.

A dedicated "fitness-judge" skill that automates the `llm-rubric` case is a natural follow-up. It would: (a) take a rubric file + an artifact set, (b) start an isolated Claude subagent with no implementer context, (c) emit a structured score. None of that is built yet; do not let the README, SKILL.md, or generated test files imply it exists.

The earlier version of this file claimed `persona-judge` filled this role and named three personas (`integration-engineer-persona`, `non-technical-end-user-persona`, `oncall-sre-persona`) as defaults. **Those personas do not exist in `persona-distill`** — they were invented during the original drafting. All references have been removed in this round.

---

## Optional: forge-teams as implementer (Step 5)

For large features where adversarial review at implementation time is worthwhile, the user can wrap ratchet's subagent with `forge-teams`. This is also a manual handoff — neither side reads our YAML.

```
/ratchet   ... --implementer-team forge-teams
```

The done_when.yaml continues to drive the *goal/criteria* you hand to ratchet; forge-teams structures the inner-loop multi-agent collaboration the subagent uses. Most features don't need this — plain ratchet is faster and lighter.

---

## What does NOT integrate (kept separate on purpose)

- **bespoke-design-system** — for visual / aesthetic design. Behavioral requirements (done_when contracts) and visual design are different problems. If the spec has visual requirements, generate a separate `bespoke-design-system` artifact and reference it from `proposal.md` — do not encode visual taste in `done_when.yaml`.
- **persona-distill / persona-judge** — see above; the persona-distill ecosystem is for distilling person-or-rule-system personas, and `persona-judge` evaluates *those* skills' quality. It is not a fitness judge for our pipeline.
- **OpenSpec / GitHub Spec Kit CLIs** — file formats borrowed (proposal/spec/tasks; clarify question style); CLIs deliberately not integrated.

---

## Cheat-sheet for the full lifecycle (v0.3.0 — recommended path)

```
1.  /acceptance-spec  "users can cancel their subscription but keep access until end of paid period"
       → specs/subscription-cancellation/
           ├── proposal.md
           ├── spec.md           (EARS, REQ-IDs)
           ├── tasks.md
           ├── done_when.yaml    (v1 strict contract)
           └── spec-robustness.md  (S2.5 — anti-gaming companion)

2.  /test-suite-generator  specs/subscription-cancellation/
       → tests/subscription-cancellation/{existence.sh, unit/, integration/, e2e/, mutation.sh, fitness/}

3.  [implement in src/ using any agent; CRITICAL — implementation agent must NOT have
     visibility into /acceptance-fleet's evaluator prompts; use a fresh session]

4.  /acceptance-fleet  specs/subscription-cancellation/
       → ratchet-log/iteration-001/
       → state_decision: FIX | DONE | SPEC_DRIFT | GAMING_RISK | NEEDS_HUMAN

5.  If FIX     → feed ratchet-log/iteration-001/fix-prompt.md to fresh impl session, then GOTO 4
    If DONE    → done, ship it
    If SPEC_DRIFT  → GOTO 1 with the offending REQs as the narrow brief
    If GAMING_RISK → GOTO 1 to close the surfaced vectors in spec-robustness.md

6.  For each `judge: persona-judge` or `judge: manual` fitness criterion in done_when.yaml:
    consume per the rubric file's how-to-run block (no packaged auto-runner — see
    fitness-rubric-guide.md). These are orthogonal to /acceptance-fleet which runs
    the behavior/correctness layers.
```

## Cheat-sheet for the legacy lifecycle (pre-v0.3.0, /ratchet path)

```
1.  /acceptance-spec  "..."
2.  /test-suite-generator  specs/<feature>/
3.  /ratchet  <paste Goal + Criteria + Scope + done_when block per "Handoff: test-suite-generator → ratchet" §>
4.  For fitness criteria, the same manual workflow as path-A step 6.
```

The legacy path is acceptable for small features where the multi-agent overhead isn't worth it, or in environments where cross-vendor evaluators aren't available. For anything non-trivial, the v0.3.0 path catches more bugs per dollar (per the cost comparison in `skills/acceptance-fleet/SKILL.md` § "Cost expectation").

User effort under the v0.3.0 path is concentrated in step 1 (the clarify loop) + step 3 (implementing) + reviewing the iteration state if it lands NEEDS_HUMAN. Acceptance-fleet itself is fully automated.
