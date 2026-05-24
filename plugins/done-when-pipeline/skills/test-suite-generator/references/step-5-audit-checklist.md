# Step 5 audit checklist — for reviewers, not for this skill to execute

This skill (test-suite-generator) **ends at Step 4**. It does not run tests, does not aggregate evaluation results, and does not judge "done". Those are Step 5 actions executed by `/ratchet` and its `evaluate.sh`.

This file exists for the human (or auditor agent) doing a Step 5 review of artifacts emitted by Steps 1-4 to use as a checklist. It is **not** a runtime contract — nothing here changes what this skill outputs. It exists because the Step 5 audit in iter-1 surfaced multiple "Worker did not cross-check against §7.4 schema" findings; codifying the checklist here lets the next reviewer not re-derive it from the design doc.

---

## §7.4 evaluation_result schema — 10-field checklist

The source design doc §7.4 defines an evaluation_result with exactly these top-level fields. When a reviewer is auditing whether the Step 4 artifacts let Step 5 produce a complete `evaluation_result`, walk each field:

| # | Field | Where the signal comes from (in our pipeline) | Check |
|---|---|---|---|
| 1 | `feature` | `done_when.yaml.feature` (top-level) | Verify the YAML has it and it matches the directory slug. |
| 2 | `timestamp` | Set by ratchet's `evaluate.sh` at run time. | Not our skill's responsibility; verify ratchet's evaluator emits it. |
| 3 | `existence.status` + `existence.checks_passed` | `existence.sh` exit code + line count | The fail-fast `existence.sh` (4-A) exits 0 (= all pass) or 1 (= first failure). For per-check counts, evaluator parses `✓ <label>` / `✗ FAIL: <label>` lines. |
| 4 | `unit_tests.example_based.passed` + `unit_tests.property_based.passed` + `total_inputs_tested` | `pytest` (or vitest) exit code + JUnit XML | `passed` ← framework exit. `total_inputs_tested` for PBT ← Hypothesis statistics output (run with `--hypothesis-show-statistics`) or fast-check's run report. **If your evaluator does not pass that flag, this field cannot be populated.** Flag this to the user. |
| 5 | `integration_tests.example_based.passed` + `integration_tests.property_based.passed` + `minimal_counterexample` | Same as unit, plus Hypothesis prints the shrunk example on failure | `minimal_counterexample` ← parse pytest stderr for `Falsifying example: ...` block, or capture via `--hypothesis-seed` re-runs. Our skill does **not** require landing the counterexample to disk; if the evaluator wants structured access, it should set `HYPOTHESIS_DATABASE` to a stable path and read it. |
| 6 | `e2e_tests.passed` | Playwright/Cypress exit code | Same. |
| 7 | `mutation_testing.mutants_killed` + `kill_rate` + `surviving_mutants` | `mutation.sh` exit code + tool DB | `mutants_killed` / `kill_rate` ← mutation.sh prints them. `surviving_mutants: [{file, line, mutation}]` ← evaluator runs `mutmut results` (or `stryker mutator output`) to dump the survivors. **Our `mutation.sh` does not auto-export this list**; evaluator must call the per-tool results command. Document this in the manifest. |
| 8 | `fitness.<criterion>: score` | Manually scored per the rubric's "How to run" block | Not auto. Reviewer collates scores into the result. |
| 9 | `overall_status` | Computed by evaluator from the above | Reviewer's call, but the rule is: any P0 criterion failed → "fail"; all pass → "ok"; budget exhausted before convergence → "stalled". |
| 10 | `meets_done_when` | boolean derived from `overall_status` | "ok" → true; anything else → false. |

If a Step 5 audit reports that the skill "does not define evaluation_result schema", that is correct — we **delegate** the schema to ratchet/evaluator and supply the signals each field needs. The audit's job is to verify each field's signal exists; not to find the schema in this skill.

---

## §7.2 做判分离 (separation of make-vs-judge) — verification checklist

§7.2 of the design doc requires that "the agent that makes (writes code) and the agent that judges (decides done) are separate sessions". For each artifact this skill emits, verify the separation is enforced:

- **existence.sh**: runs in a child shell, no session state shared with implementer. ✓ structural separation.
- **unit / integration tests**: pytest/vitest is a separate process with no LLM in the loop. ✓ structural separation.
- **e2e tests**: same — Playwright is a separate process. ✓ structural separation.
- **mutation.sh**: separate process. ✓ structural separation.
- **fitness rubrics**: ⚠ **conventional separation only.** The rubric file's "How to run" instructs the user to open a **fresh Claude session** (no implementer context) and paste the rubric + artifacts. This is honor-system, not mechanical. The rubric file MUST contain this instruction verbatim — see `fitness-rubric-guide.md`.

The Step 5 audit should verify that no artifact's design assumes "the agent that wrote the code also scores its own output". The first four layers are structurally safe; the fitness layer is contractually safe via the rubric's how-to-run text.

---

## §7.5 anti-reward-hacking — surface check

The reviewer should confirm three things are present in the artifact tree:

1. **mutation.sh exists and asserts kill-rate ≥ threshold.** Without this, coverage thresholds incentivize `assert True`.
2. **At least one PBT exists per `behavior.*.property_based` entry.** PBTs close the "implementer memorized example cases" loop.
3. **PBT generators are reasonably wide.** A PBT whose generator only emits 2-3 input shapes is no better than an example test. Reviewer reads each generator and checks it explores the input space.

If any of the three is missing, that is a Step 4 quality issue (`/test-suite-generator` should have emitted them) — push back to the artifact author, not to ratchet.

---

## Reviewer's narrative report — recommended structure

A Step 5 audit (e.g. the kind the iter-* validation produces) should produce a report with these sections, in order:

1. **§7.2 separation** — table mapping each artifact to its separation mechanism (structural / conventional / none).
2. **§7.3 inputs / outputs** — confirm Step 5 inputs (Step 4 artifacts + impl code) are all present; confirm Step 5 output (evaluation_result) is delegable to ratchet's evaluator.
3. **§7.4 schema field walk** — the 10-field table above, marked ✓ / partial / ⚠ per field.
4. **§7.5 anti-reward-hacking** — the three checks above.
5. **§9 role separation** — confirm no skill or artifact is claiming to *be* the Step 5 implementation agent (every skill should disclaim this in its "When to refuse / redirect" or "After…" section).

If a reviewer follows this checklist, they will not re-derive the schema from §7.4 mid-audit (the failure mode that produced iter-1 P1-1 through P1-5). Use this file as the audit guide.
