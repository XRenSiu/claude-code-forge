# done-when-pipeline

Turn fuzzy natural-language requirements into **machine-verifiable completion contracts** that an independent agent can mechanically check — no human in the loop at verification time.

## Why this exists

Making an AI agent autonomously finish a task is not bottlenecked by "making it code." It is bottlenecked by **telling it when it is done**. The completion criteria must be:

- **Mechanically verifiable** — no human subjective check
- **Independently verifiable** — the agent that builds and the agent that judges are different sessions
- **Reward-hacking resistant** — passing the form must require passing the substance
- **Traceable** — every check ties back to a stated requirement

This plugin gives you the two skills that produce that contract.

## Pipeline

```
NL requirement
   │
   ▼
acceptance-spec ───────►  specs/<feature>/
   (Steps 1-3)              proposal.md
   clarify loop, 3          spec.md           (EARS, REQ-IDs)
   question types,          tasks.md
   2-3 rounds max           done_when.yaml    (the contract)
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
ratchet  ─── consumes done_when.yaml as the kill/restart/done oracle (Step 5-6)
   spec-drift bailout: PBT failing >=3 rounds escalates back to clarify
```

## Two skills

| Skill | Trigger | What it produces |
|---|---|---|
| `/acceptance-spec` | `"spec this requirement"` / `"draft EARS"` / `"done_when for X"` / `"clarify this feature"` | `specs/<feature>/` (4 files) |
| `/test-suite-generator` | `"generate tests for spec X"` / `"derive test suite"` / `"build verification battery"` | `tests/<feature>/` (6 batches) |

Each skill enters its first phase by reading the requirement / spec, then walks a strict sub-step sequence — they do not improvise the structure.

## Design philosophy

1. **Verifiable beats judgeable.** PBT > LLM-as-judge whenever both work. LLM judge is the layer of last resort, used only for things genuinely outside mechanical reach (doc clarity, agent usability, intent alignment).
2. **Pay human time only where it cannot be replaced.** That is exactly *one* step: ambiguity removal. Everything else is delegated to LLM-for-semantic-work or to traditional tools for combinatorial-work.
3. **Anti-reward-hacking is mandatory, not optional.** A done_when that only checks coverage ≥ 80% incentivizes `assert True`. Mutation testing closes that loop; PBT closes the "agent memorized the test cases" loop.
4. **Spec drift is a first-class failure mode.** If PBT keeps finding counterexamples after multiple fix attempts, the spec is the bug. Bailout to the clarify loop, do not pile on more code patches.
5. **Borrow formats, not CLIs.** EARS, OpenSpec's file conventions, the AWS Kiro EARS→PBT idea — borrowed as ideas, not as dependencies.

## Integration with existing claude-code-forge assets

| Existing | Role here |
|---|---|
| `ratchet` | Step 5-6 main controller. Consumes `done_when.yaml` as its acceptance contract; runs the master/subagent kill-and-restart loop; receives the spec-drift escalation signal from PBT. |
| `forge-teams` | Optional implementation team during Step 5 if the work is large enough to warrant adversarial review. |
| (no packaged fitness-judge skill exists yet) | Step 4-F rubric files are consumed manually by a fresh Claude session — see `INTEGRATION.md` and `skills/test-suite-generator/references/fitness-rubric-guide.md` for the workflow. The `persona-judge` skill from `persona-distill` was originally listed here in error; it evaluates persona-skill quality, not arbitrary artifacts. |

## What this plugin does **not** do

- It does not run tests. (That's Step 5 — pytest, vitest, Playwright, mutmut.)
- It does not implement the feature. (Hand the spec to your implementer of choice.)
- It does not bundle Hypothesis / fast-check / testcontainers. (Those are tool stacks the generated tests *use*; install them in the target project.)
- It does not replace OpenSpec or GitHub Spec Kit. It re-uses their *ideas* without dragging in their CLIs.

## Where to start

```
/acceptance-spec  "users can cancel their subscription but keep access until end of paid period"
```

Then once the 4 files are written:

```
/test-suite-generator  specs/subscription-cancellation/
```

Then hand `specs/subscription-cancellation/done_when.yaml` to `/ratchet` as the acceptance contract for the implementation loop.

## Version

0.1.0 — initial release, covers Steps 1-4 of the pipeline. Step 5 (execution) and Step 6 (loop) hand off **manually** to `ratchet` (a chained `/ratchet` invocation whose Goal/Criteria/Scope the user translates from our outputs). Fitness rubrics are scored **manually** by a fresh Claude session per the rubric file's how-to-run block. See `INTEGRATION.md` for the honest scope of each hand-off — there is no automated structural integration today; a wrapper skill that would automate these is potential future work.
