# done_when.yaml validator checklist (schema v1)

Run this before sub-step 4-A. If any check fails, **bail out** and tell the user the contract is malformed. Do not try to generate tests against a broken contract.

**Authoritative schema:** Appendix C of `done-when-pipeline.md` (schema v1). This checklist mirrors it literally — entries on `existence:` are single-key mappings with **no sub-fields**, and entries under `behavior.*` are **bare strings** (not mappings). Any extra sub-fields = malformed.

---

## Mandatory keys

- [ ] `feature:` is present and is kebab-case
- [ ] `based_on:` is a non-empty list of REQ IDs (the union across the contract — this is the v1 traceability anchor)
- [ ] `created_at:` is present (ISO-8601)
- [ ] `created_by:` is present (skill name; e.g. `acceptance-spec`)
- [ ] `existence:` is present (may be empty list for feature with no concrete existence claims, but the key must exist)
- [ ] `behavior:` is present and contains at least one of `unit_tests`, `integration_tests`, `e2e_tests`
- [ ] `behavior.thresholds:` is present and includes `mutation_kill_rate:` (this is mandatory per the iron rules)
- [ ] `fitness:` is present (may be empty list)
- [ ] `spec_drift_threshold:` is present with `max_fix_loops_before_escalation: <integer>`

---

## Cross-reference checks

- [ ] Every REQ ID in the top-level `based_on:` exists in the sibling `spec.md`. Reverse direction is also a smell — if `spec.md` has a REQ that doesn't appear in `based_on:`, either the REQ has no testable claim (should have been flagged upstream) or it was forgotten when writing the contract.
- [ ] No test name in `behavior.*` references an entity / verb / domain term that isn't grounded somewhere in `spec.md`.

---

## Existence — type & shape checks (v1 strict)

For each `existence:` entry:
- [ ] Has **exactly one** of the five v1 kinds: `file`, `function`, `route`, `db_field`, `frontend_component`.
- [ ] Has **no other keys**. If you see `based_on:` / `kind:` / `class:` / `description:` etc. on an existence entry → the contract was written against a non-v1 schema. Reject and tell the user to regenerate via `/acceptance-spec` (which now emits strict v1).

---

## Behavior — type & shape checks (v1 strict)

For each entry under `behavior.unit_tests.example_based` / `behavior.unit_tests.property_based` / `behavior.integration_tests.example_based` / `behavior.integration_tests.property_based` / `behavior.e2e_tests`:

- [ ] The entry is **a bare string** (the test name), not a mapping.
- [ ] If it is a mapping (with `name:` / `based_on:` / `property_type:` / `dependencies:` / `tool:` sub-fields), the contract is non-v1 — reject and tell the user to regenerate.
- [ ] Test names are descriptive snake_case (or the project-canonical convention).
- [ ] For entries under `property_based:` — the name should end in (or contain) one of the six archetype tokens: `_invariant`, `_idempotent`, `_reversible`, `_boundary`, `_monotonic`, `_state_machine`. If the archetype cannot be inferred from the name, raise a warning and ask the user to rename — the PBT pattern dispatcher in 4-B keys off the name.

`behavior.thresholds:` is expected to contain four keys: `unit_coverage`, `integration_coverage`, `mutation_kill_rate`, `pbt_runs_per_property`. Any extra threshold key is a soft warning, not a hard failure.

---

## Fitness — type & shape checks (v1 strict)

For each `fitness:` entry:
- [ ] Has `criterion:` (one-line description)
- [ ] Has `judge:` ∈ **{persona-judge, programmatic, manual}**  ← this is the v1 enum from Appendix C
- [ ] If `judge: persona-judge` → has `score_threshold:`. The rubric markdown file is an artifact this skill produces (4-F) — it is **not** a contract field. If the contract has a `rubric_file:` key, treat it as malformed (it was a non-v1 extension).
- [ ] If `judge: programmatic` → no `score_threshold:` required (pass/fail).
- [ ] If `judge: manual` → has `score_threshold:` (a human still needs a bar).
- [ ] If `judge: llm-rubric` → **reject as malformed.** This was a legacy value from earlier drafts. The v1 enum from Appendix C does not include `llm-rubric`; the LLM-as-judge path is `persona-judge`. Tell the user to regenerate via `/acceptance-spec`.
- [ ] No other keys on the fitness entry.

---

## spec_drift_threshold — type & shape checks (v1 strict)

- [ ] Has exactly one sub-field: `max_fix_loops_before_escalation: <integer>`.
- [ ] If the contract has `applies_to:` (or any other sub-field) on `spec_drift_threshold:`, treat it as malformed — v1 defines only the one field.

---

## Sanity warnings (do not block, but report)

- ⚠ `fitness:` has more than 3 entries → likely over-using LLM-judge; suggest moving some to `behavior:`
- ⚠ `e2e_tests:` has more than 5 entries → likely too E2E-heavy; suggest moving some to integration
- ⚠ All tests are example-based, no `property_based:` entries → review whether any REQ is actually a good PBT candidate; the spec is unusual if zero properties exist
- ⚠ `mutation_kill_rate:` threshold is < 0.7 → below the recommended floor; ask the user to confirm
- ⚠ `spec_drift_threshold.max_fix_loops_before_escalation:` > 5 → ratchet will loop a long time before escalating; confirm this is intentional

---

## How to report failures to the user

If any **mandatory** check or **v1 strict type** check fails:

```
The done_when.yaml contract is malformed against schema v1 (Appendix C of done-when-pipeline.md).
I can't safely generate tests from it.

Failures:
- <specific check that failed>
- <specific check that failed>

Suggested action: re-run /acceptance-spec to regenerate the contract,
or fix the listed issues by hand and re-invoke me.
```

Do not attempt to patch the contract yourself — it's the user's intent encoded; only the user (or the acceptance-spec skill) should change it.
