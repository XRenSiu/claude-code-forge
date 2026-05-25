# done-when-pipeline

Turn fuzzy natural-language requirements into **machine-verifiable completion contracts** that an independent agent can mechanically check — no human in the loop at verification time.

## Why this exists

Making an AI agent autonomously finish a task is not bottlenecked by "making it code." It is bottlenecked by **telling it when it is done**. The completion criteria must be:

- **Mechanically verifiable** — no human subjective check
- **Independently verifiable** — the agent that builds and the agent that judges are different sessions
- **Reward-hacking resistant** — passing the form must require passing the substance
- **Traceable** — every check ties back to a stated requirement

This plugin gives you the three skills that produce, exercise, and verify that contract.

## Pipeline

```
NL requirement
   │
   ▼
acceptance-spec ───────►  specs/<feature>/
   (Steps 1-3)              proposal.md
   clarify loop, 3          spec.md           (EARS, REQ-IDs)
   question types,          tasks.md
   2-3 rounds max,          done_when.yaml    (the strict v1 contract)
   + S2.5 spec-self-        spec-robustness.md (anti-gaming companion —
   adversarial pass                            closed/surfaced/accepted
                                               gaming vectors per 6 RHD patterns)
   │
   ▼
test-suite-generator ──►  tests/<feature>/
   (Step 4)                  existence.sh     (4-A: ripgrep/AST)
   EARS → 6 batches          unit/             (4-B: example + PBT)
   batch-by-batch,           integration/      (4-C: + testcontainers)
   not all-at-once           e2e/              (4-D: Playwright)
                             mutation.config   (4-E: mutmut / Stryker)
                             fitness.rubric    (4-F: manual fresh-Claude-session workflow)
   │
   ▼
[implement in src/ using your agent of choice — must run in a fresh session that
 cannot see the evaluator prompts; same-session impl+eval is gaming substrate]
   │
   ▼
acceptance-fleet ──────►  ratchet-log/iteration-NNN/
   (Steps 5-6,               fleet-outputs/    (8 evaluator outputs, parallel)
   RECOMMENDED path)         rebuttals/        (S2 — 4-Eyes Principle)
                             meta-judge-output.yaml (synthesis, no re-review)
   7-role fleet + spec-      <state-report>.md (fix-prompt / spec-drift / gaming-risk / needs-human)
   gaming-detector,         four-state ratchet: DONE | FIX | SPEC_DRIFT | GAMING_RISK | NEEDS_HUMAN
   meta-judge synthesis,    cross-vendor evaluators preferred (Codex / Gemini break the
   four-state ratchet       Claude-reviewing-Claude sycophancy loop); medium isolation minimum
   │
   ▼
(OR legacy: /ratchet — user hands done_when.yaml to /ratchet as the acceptance contract,
 single-stream subagent loop, no gaming detection, no four-state ratchet. Acceptable
 for small features; INTEGRATION.md documents the translation.)
```

## Three skills

| Skill | Trigger | What it produces |
|---|---|---|
| `/acceptance-spec` | `"spec this requirement"` / `"draft EARS"` / `"done_when for X"` / `"clarify this feature"` | `specs/<feature>/` (5 files) |
| `/test-suite-generator` | `"generate tests for spec X"` / `"derive test suite"` / `"build verification battery"` | `tests/<feature>/` (6 batches) |
| `/acceptance-fleet` | `"verify this implementation"` / `"run acceptance fleet"` / `"fleet review"` | `ratchet-log/iteration-NNN/` (8 evaluator outputs + meta-judge verdict + state-specific report per iteration) |

Each skill enters its first phase by reading its inputs, then walks a strict sub-step sequence — they do not improvise the structure.

## Design philosophy

1. **Verifiable beats judgeable.** PBT > LLM-as-judge whenever both work. LLM judge is the layer of last resort, used only for things genuinely outside mechanical reach (doc clarity, agent usability, intent alignment).
2. **Pay human time only where it cannot be replaced.** That is exactly *one* step: ambiguity removal. Everything else is delegated to LLM-for-semantic-work or to traditional tools for combinatorial-work.
3. **Anti-reward-hacking is mandatory, not optional.** A done_when that only checks coverage ≥ 80% incentivizes `assert True`. Mutation testing closes that loop; PBT closes the "agent memorized the test cases" loop.
4. **Spec drift is a first-class failure mode.** If PBT keeps finding counterexamples after multiple fix attempts, the spec is the bug. Bailout to the clarify loop, do not pile on more code patches.
5. **Borrow formats, not CLIs.** EARS, OpenSpec's file conventions, the AWS Kiro EARS→PBT idea — borrowed as ideas, not as dependencies.

## Integration with existing claude-code-forge assets

| Existing | Role here |
|---|---|
| `ratchet` | **Legacy** Step 5-6 controller. Now an alternative to `/acceptance-fleet`. The user manually translates `done_when.yaml` into a `/ratchet` invocation (Goal / Criteria / Scope / done_when block); ratchet does not parse our YAML directly. No gaming detection, no four-state ratchet, no full audit log. Acceptable for small features or environments without cross-vendor evaluators. See `INTEGRATION.md` "Handoff: test-suite-generator → ratchet (legacy)" for the recipe. |
| `forge-teams` | Optional implementation team during the impl phase. Particularly useful for the adversarial-review-at-impl-time pattern; runs orthogonally to `/acceptance-fleet`'s adversarial-reviewer evaluator. |
| Codex CLI / Gemini CLI | Cross-vendor evaluators consumed by `/acceptance-fleet` for the adversarial-reviewer and spec-gaming-detector roles. The Milvus benchmark (MD §1.4) showed Claude + Gemini cover 91% of the bugs a 5-vendor ensemble finds — cross-vendor is the cost-effective sweet spot. If neither is available, `/acceptance-fleet` falls back to medium isolation (mixed Claude sizes) with a logged warning. |
| (no packaged fitness-judge skill exists yet) | Step 4-F rubric files are consumed manually by a fresh Claude session — see `INTEGRATION.md` and `skills/test-suite-generator/references/fitness-rubric-guide.md` for the workflow. `/acceptance-fleet` covers behavior/correctness layers; fitness-judge remains orthogonal future work. The `persona-judge` skill from `persona-distill` was originally listed here in error; it evaluates persona-skill quality, not arbitrary artifacts. |

## What this plugin does **not** do

- It does not implement the feature. (Hand the spec to your implementer of choice — must run in a fresh session that cannot see acceptance-fleet's evaluator prompts.)
- It does not bundle Hypothesis / fast-check / testcontainers. (Those are tool stacks the generated tests *use*; install them in the target project.)
- It does not bundle Codex CLI or Gemini CLI. (`/acceptance-fleet` detects them at S0; install them yourself for cross-vendor evaluation.)
- It does not replace OpenSpec or GitHub Spec Kit. It re-uses their *ideas* without dragging in their CLIs.

## Where to start

```
/acceptance-spec  "users can cancel their subscription but keep access until end of paid period"
```

Then once the 5 files are written:

```
/test-suite-generator  specs/subscription-cancellation/
```

Implement the feature (in a fresh session — do not let the impl agent see the next step's prompts), then:

```
/acceptance-fleet  specs/subscription-cancellation/
```

This runs the full Step 5-6 loop with automatic four-state ratchet feedback.

## Version

0.3.0 — adds `/acceptance-fleet` skill landing Steps 5-6 as a packaged multi-agent acceptance loop; bumps `/acceptance-spec` to v0.3.0 adding the S2.5 spec-self-adversarial pass and the fifth output file `spec-robustness.md`. The legacy hand-off to standalone `/ratchet` remains supported.

History:
- 0.2.0 — three-role validation pass; surfaced 17 P0 issues and hardened the skill source.
- 0.1.0 — initial release, covered Steps 1-4 only; Step 5-6 was manual hand-off to `/ratchet`.

See `INTEGRATION.md` for the honest scope of every hand-off.
