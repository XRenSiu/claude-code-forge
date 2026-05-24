# done_when.yaml validator checklist

Run this before sub-step 4-A. If any check fails, **bail out** and tell the user the contract is malformed. Do not try to generate tests against a broken contract.

---

## Mandatory keys

- [ ] `feature:` is present and is kebab-case
- [ ] `based_on:` is a non-empty list of REQ IDs
- [ ] `existence:` is present (may be empty list for feature with no concrete existence claims, but the key must exist)
- [ ] `behavior:` is present and contains at least one of `unit_tests`, `integration_tests`, `e2e_tests`
- [ ] `behavior.thresholds:` is present and includes `mutation_kill_rate:` (this is mandatory per the iron rules)
- [ ] `fitness:` is present (may be empty list)
- [ ] `spec_drift_threshold:` is present with `max_fix_loops_before_escalation: <integer>`

---

## Cross-reference checks

- [ ] Every `based_on:` REQ ID referenced anywhere in the file exists in the sibling `spec.md`. If `spec.md` has REQ-001 through REQ-006, no test or existence entry may reference REQ-007.
- [ ] The top-level `based_on:` list is a *superset* of every REQ referenced anywhere in `existence:` / `behavior:` / `fitness:`.
- [ ] Every REQ in the top-level `based_on:` is referenced by at least one entry in `existence:` *or* `behavior:`. Unreferenced REQs are a smell: either the REQ has no testable claim (should have been flagged upstream) or it was forgotten when writing the contract.

---

## Type checks

For each `existence:` entry:
- [ ] Has exactly one of: `file`, `function`, `route`, `db_field`, `frontend_component`, `env_var`, `cli_command`
- [ ] Has `based_on:` (non-empty list)

For each test entry under `behavior:`:
- [ ] Has `name:` (snake_case typical)
- [ ] Has `based_on:` (non-empty list)
- [ ] If under `property_based:` — has `property_type:` ∈ {invariant, idempotent, reversible, boundary, monotonic, state_machine}
- [ ] If under `integration_tests:` — has `dependencies:` (may be empty list)
- [ ] If under `e2e_tests:` — has `tool:` ∈ {playwright, cypress, appium, maestro}

For each `fitness:` entry:
- [ ] Has `criterion:` (one-line description)
- [ ] Has `judge:` ∈ {programmatic, llm-rubric, manual}
- [ ] If `judge: llm-rubric` → has `rubric_file:` and `score_threshold:`
- [ ] If `judge: persona-judge` → **reject as malformed.** This was a category error in earlier drafts; the `persona-judge` skill evaluates persona-skill quality, not arbitrary artifacts. Caller should use `judge: llm-rubric`.
- [ ] If `judge: programmatic` → no score_threshold required (pass/fail)
- [ ] If `judge: manual` → has a clear pass/fail checklist or pointer to one

---

## Sanity warnings (do not block, but report)

- ⚠ `fitness:` has more than 3 entries → likely over-using LLM-judge; suggest moving some to `behavior:`
- ⚠ `e2e_tests:` has more than 5 entries → likely too E2E-heavy; suggest moving some to integration
- ⚠ All tests are example-based, no `property_based:` entries → review whether any REQ is actually a good PBT candidate; the spec is unusual if zero properties exist
- ⚠ `mutation_kill_rate:` threshold is < 0.7 → below the recommended floor; ask the user to confirm
- ⚠ `spec_drift_threshold.max_fix_loops_before_escalation:` > 5 → ratchet will loop a long time before escalating; confirm this is intentional

---

## How to report failures to the user

If any **mandatory** check fails:

```
The done_when.yaml contract is malformed. I can't safely generate tests from it.

Failures:
- <specific check that failed>
- <specific check that failed>

Suggested action: re-run /acceptance-spec to regenerate the contract,
or fix the listed issues by hand and re-invoke me.
```

Do not attempt to patch the contract yourself — it's the user's intent encoded; only the user (or the acceptance-spec skill) should change it.
