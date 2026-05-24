# Step 4 attempt-2 — test-suite-generator output manifest

**Worker:** Step-4 Worker subagent (attempt 2)
**Date:** 2026-05-24
**Skill:** `plugins/done-when-pipeline/skills/test-suite-generator` (v0.1.0)
**Input contract:** `specs/forge-skill-validation/iter-1-step3-attempt-2-artifacts/done_when.yaml`
**Input spec:** `specs/forge-skill-validation/iter-1-step3-attempt-2-artifacts/spec.md`
**Output root:** `specs/forge-skill-validation/iter-1-step4-attempt-2-artifacts/`

This manifest documents the second run of Step 4 against the regenerated
v1-strict Step 3 contract. References were re-read after Fixer's revisions
(iron rules #9 and #10 added; 4-A fail-fast and 4-D verbatim rules made
explicit in both SKILL.md and the sub-module references).

---

## 0 — Bootstrap

- Input contract `done_when.yaml`: v1 strict (bare-string test names under
  `behavior.*`; single-key existence entries; `judge: persona-judge` for
  both fitness entries). Schema validation walked per
  `references/done-when-schema-validator.md`; no rejection conditions met.
- Top-level `based_on:` covers all seven REQs (REQ-001 … REQ-007).
- Language detection: project has no `package.json` / `pyproject.toml` at
  feature scope. Following the Step 4 attempt-1 convention adopted for
  this validation thread:
  - Unit + integration → **Python (pytest + Hypothesis)**.
  - E2E → **TypeScript (Playwright)** (default when no other e2e tool
    is configured; per `references/sub-modules/e2e-generator.md`).
  - Mutation → **mutmut** (Python).
- Output directory: `specs/forge-skill-validation/iter-1-step4-attempt-2-artifacts/`.
- `references/ears-to-test-matrix.md`, `references/pbt-property-types.md`,
  and all six `references/sub-modules/*.md` files re-read prior to each
  sub-step (per iron rule "re-read before every sub-step").

---

## 4-A — Existence

| Field | Value |
|---|---|
| File | `existence/existence.sh` |
| Idiom | Fail-fast (`set -euo pipefail` at top; `check()` helper exits 1 on first failure) |
| Checks count | **20** — covers all 20 existence entries in `done_when.yaml` (10 functions / 4 routes / 6 db fields) |
| Forbidden patterns audit | `if … then PASS=…` (none), `Passed:/Failed:` tally (none) — verified by grep |
| Smoke run | exits 1 immediately on first check (`ResolveMentionRecipients` not present); fail-fast confirmed live |

The header explicitly documents the fail-fast policy and names the
`done-when-pipeline §6.2` and 4-A sub-module reference for the forbidden
pattern. Each `check "label" cmd` exits 1 on its own failure via
`|| { ...; exit 1; }` — there is no PASS/FAIL counter.

---

## 4-B — Unit

| Field | Value |
|---|---|
| Files | `unit/test_mention_pipeline.py` (REQ-001..REQ-004), `unit/test_mention_edit_delete.py` (REQ-005, REQ-006), `unit/test_dnd_lifecycle.py` (REQ-007, DND state machine) |
| Example-based tests | **27** (matches `done_when.yaml.behavior.unit_tests.example_based`) |
| Property-based tests | **9** (matches `done_when.yaml.behavior.unit_tests.property_based`) |
| Total `def test_*` | **36** (verbatim names verified by script — see "Verbatim audit" below) |
| PBT archetype routing | name suffix → pattern from `references/pbt-property-types.md`: `_idempotent` (1), `_monotonic` (1), `_invariant` (4 — three on REQ-002/REQ-003/REQ-004/REQ-006), `_reversible` (1), `_boundary` (1), `_state_machine` (1) |
| `max_examples` | 500 (matches `thresholds.pbt_runs_per_property` >= 500) |
| File header | every file includes Generated-by header + Source spec + REQ coverage list |
| Mock policy | none — pure unit tests on pure factories |

PBT state-machine entry `test_dnd_lifecycle_state_machine_is_well_formed`
wraps a `RuleBasedStateMachine.TestCase` inside a verbatim-named pytest
function so the discoverable test identifier exactly equals the YAML
entry.

---

## 4-C — Integration

| Field | Value |
|---|---|
| Files | `integration/conftest.py` (testcontainers fixtures), `integration/test_mention_flows.py` (example), `integration/test_mention_properties.py` (PBT) |
| Example-based tests | **6** (matches `done_when.yaml.behavior.integration_tests.example_based`) |
| Property-based tests | **2** (matches `done_when.yaml.behavior.integration_tests.property_based`) |
| Total `def test_*` | **8** (verbatim verified) |
| Dependencies | Real Postgres (`postgres:16-alpine`), real Redis (`redis:7-alpine`) via `testcontainers`. No HTTP mocks, no DB mocks. Iron rule #4 honored. |
| Cross-boundary asserts | each example test asserts at the HTTP API boundary **and** in the DB — catches the interface-drift class of failures |
| State-machine fixture | `_MutedChannelPersistenceMachine` (RuleBasedStateMachine) explores mute/unmute + app-restart cycle to verify per-channel mute persistence across restarts (REQ-002 glossary clause iii) |

---

## 4-D — E2E

| Field | Value |
|---|---|
| Files | `e2e/playwright.config.ts`, `e2e/fixtures.ts`, plus three `*.spec.ts` files (one per `done_when.yaml.e2e_tests` entry) |
| Tool | Playwright (web default — no Cypress/Maestro config detected) |
| Entries | **3** — well under the >5 push-back threshold |
| `test(...)` first-arg verbatim | **3/3 verified** — match YAML character-for-character (see "Verbatim audit" below) |
| Forbidden paraphrases audit | `test('mentioned member …'`, `test('member in DND …'`, `test('deleted mention message …'` — zero matches |
| Selectors | `data-test=` only (per 4-D rule) |
| Per-test isolation | each test seeds its own member via `/_test/seed_member` helper; no shared state |
| Human-readable description | lives in `test.describe(...)` title + leading comment inside the test body (never in `test()` first arg) |

---

## 4-E — Mutation

| Field | Value |
|---|---|
| Files | `mutation/pyproject.toml` (mutmut config), `mutation/mutation.sh` (runner), `mutation/README.md` |
| Threshold | **70%** (matches `thresholds.mutation_kill_rate: ">= 0.70"`) |
| Scope | `paths_to_mutate = "src/notifications/"` — scoped to feature, not the whole `src/` (avoids polluting the denominator) |
| Runner | `pytest -x tests/channel-mention-notifications/unit/` (fail-fast on first failing test per mutant — speedup) |
| Anti-cheating message | embedded in README ("if you bypass this script, you re-open the reward-hacking hole") |
| Not run | mutation suite NOT executed — too slow per 4-E rule |

---

## 4-F — Fitness

| Field | Value |
|---|---|
| Files | `fitness/README.md`, `fitness/oncall_engineer_edge_case_prediction.rubric.md`, `fitness/glossary_partition_agreement.rubric.md` |
| Entry count | **2** (matches `done_when.yaml.fitness`; under the 3-entry warning threshold) |
| Judge kinds | both `persona-judge` (LLM-as-judge); zero `judge: llm-rubric` (would be rejected) |
| `score_threshold:` honored | both rubrics restate `>= 8/10` |
| Audience archetype | self-contained 5-line inline description; no external persona-library dependency |
| Sub-dimensions | rubric 1 has 4 weighted sub-dimensions summing to 1.0; rubric 2 has 4 summing to 1.0 |
| Concrete anchors | every sub-dimension has 1 / 4 / 7 / 10 anchors with concrete pass conditions |
| JudgeBench warning | both rubric files include the 55.6%→42.9% accuracy warning at the top |
| "How to run" | both files include the manual fresh-Claude-session workflow + the note that the existing `persona-judge` skill is scoped to distilled-persona evaluation (cannot consume these rubrics today) |
| Re-run policy | both files include the within-±0.5 second-pass rule |

---

## Verbatim audit (the key P0 fix)

Cross-referenced every test name against `done_when.yaml`. Method:
extract bare strings under `behavior.unit_tests`, `behavior.integration_tests`,
`behavior.e2e_tests`; extract `def test_*` from Python files and
`test('test_*'` first-args from `.spec.ts` files; set-diff.

| Layer | YAML count | Generated count | Match? |
|---|---:|---:|---|
| Unit (example + PBT) | 36 | 36 | ✓ exact |
| Integration (example + PBT) | 8 | 8 | ✓ exact |
| E2E | 3 | 3 | ✓ exact |

Set diffs were empty in both directions for every layer.

---

## Pyramid ratio sanity (per `references/ears-to-test-matrix.md`)

| Layer | This run | Recommended (AI-coding-era) |
|---|---:|---:|
| Unit | 36 / 47 = 77% | ~50% |
| Integration | 8 / 47 = 17% | ~35% |
| E2E | 3 / 47 = 6% | ~15% |

**Note:** unit-heavy ratio. This reflects the contract (the upstream
`/acceptance-spec` step decided how many tests at each layer) — the
generator does NOT invent extra integration tests to "balance" the
pyramid (iron rule #7: "No inventing requirements"). The skew is a
signal worth flagging to the user but not a generator-side problem to
fix. If the user wants more integration coverage, they should re-run
Step 3 to extend the integration list.

---

## 与 attempt-1 相比的修正

attempt-1 had two P0 findings from review: (1) existence.sh used the
forbidden count-all idiom; (2) e2e `test()` first-args were paraphrased
sentence titles. Both are fixed in this attempt, and the references that
*allow* the broken patterns to slip past were tightened during Fixer's
pass between attempts (visible in iron rules #9 and #10 of SKILL.md;
the explicit forbidden-pattern blocks in `sub-modules/existence-extractor.md`
and `sub-modules/e2e-generator.md`).

Concrete changes vs. attempt-1:

### 4-A — fail-fast restored

- `existence.sh` now uses the `check()` helper (`cmd || { echo FAIL; exit 1; }`),
  with `set -euo pipefail` on line 16 (immediately after the header
  comment block). No `if cmd; then PASS=...; else FAIL=...; fi` pattern.
- No `Passed: X · Failed: Y` summary block at the bottom — only a single
  "All N checks passed" line that is unreachable when any check fails.
- Smoke run with the project's current empty `src/` tree exits with code
  `1` on the **first** check, prints the failing label, and stops — that
  is the contracted fail-fast behavior. attempt-1 by contrast continued
  through all checks and tallied them.
- Header comment explicitly documents: "Exits nonzero on the FIRST
  failure (set -e semantics)" — no contradicting language about
  counting.

### 4-D — verbatim e2e test names

- All three Playwright spec files now pass the **exact YAML name** as the
  first argument to `test(...)`:
  - `test('test_mentioned_member_sees_in_app_banner_in_active_channel', …)`
  - `test('test_member_in_dnd_sees_only_badge_increment_no_banner_no_sound', …)`
  - `test('test_deleted_mention_message_retracts_visible_banner', …)`
- attempt-1 had paraphrased these into sentence-cased English titles
  (e.g. `test('mentioned member sees in-app banner …'`) — that breaks
  the `grep` traceability path Step 5 evaluators use.
- The human-readable descriptions previously living in the `test()`
  first arg are now in (a) the `test.describe(...)` title around each
  test, and (b) a leading comment inside the test body explicitly
  labeled `// Human description (kept OUT of the test() first arg, …)`.

### 4-B / 4-C — verbatim audit extended

- Python's `def test_*` was naturally verbatim in attempt-1 (snake_case
  ↔ snake_case) but this attempt explicitly cross-checks all 36 unit
  and 8 integration names against the YAML via script, and the manifest
  records `[]` for both set-diffs (YAML\\defs and defs\\YAML).
- One name in the contract — `test_dnd_lifecycle_state_machine_is_well_formed`
  — names a state-machine PBT. This attempt wraps the `RuleBasedStateMachine`'s
  `TestCase` inside a plain pytest function with exactly that name, so
  the discovered test identifier verbatim-matches the YAML. attempt-1
  used the Hypothesis-idiomatic `TestSubscriptionStateMachine = …TestCase`
  module-attribute pattern, which produces a discoverable test name like
  `TestDNDLifecycleStateMachine.runTest` — not verbatim.

### Other improvements not strictly P0

- Existence checks now grep for export-style declarations *and* Python
  `def`/`class` (the unit tests target Python; the regex `(def|class|function|export\s+...)`
  works for both stacks).
- Integration tests assert at both the API boundary AND the DB row for
  every example case, per the integration generator guidance — caught
  by re-reading `references/sub-modules/integration-generator.md`.
- Fitness rubrics now include the JudgeBench accuracy-drop warning at
  the top of each file (attempt-1 had it only in the README).
- Both fitness rubric files include the "no auto-runner today" disclaimer
  inline, per the Fixer-era addition to `references/fitness-rubric-guide.md`.

---

## File tree (final)

```
specs/forge-skill-validation/iter-1-step4-attempt-2-artifacts/
├── e2e/
│   ├── deleted-mention-retracts-banner.spec.ts
│   ├── fixtures.ts
│   ├── member-in-dnd-sees-badge-only.spec.ts
│   ├── mentioned-member-sees-banner.spec.ts
│   └── playwright.config.ts
├── existence/
│   └── existence.sh
├── fitness/
│   ├── README.md
│   ├── glossary_partition_agreement.rubric.md
│   └── oncall_engineer_edge_case_prediction.rubric.md
├── integration/
│   ├── conftest.py
│   ├── test_mention_flows.py
│   └── test_mention_properties.py
├── mutation/
│   ├── README.md
│   ├── mutation.sh
│   └── pyproject.toml
└── unit/
    ├── test_dnd_lifecycle.py
    ├── test_mention_edit_delete.py
    └── test_mention_pipeline.py
```

18 files total.

---

## Runnable commands (from project root, post-implementation)

```bash
# Existence (fast — < 1s)
bash specs/forge-skill-validation/iter-1-step4-attempt-2-artifacts/existence/existence.sh

# Unit (after implementer creates src/notifications/* modules)
pytest specs/forge-skill-validation/iter-1-step4-attempt-2-artifacts/unit/ -v

# Mutation (slow — minutes to hours; pre-merge / nightly)
bash specs/forge-skill-validation/iter-1-step4-attempt-2-artifacts/mutation/mutation.sh
```

Integration and e2e are intentionally left runnable-but-not-run per the
4-C/4-D guidance — integration needs Docker for testcontainers, and e2e
needs the implementer's app deployed at `E2E_BASE_URL`.

---

## Next step suggestion

Hand the spec + this test suite to `/ratchet` as the implementation
contract. Surface the unit-heavy pyramid ratio (77/17/6) to the human
reviewer so they can decide whether to feed Step 3 back for a few more
integration tests before kicking off Step 5 implementation.
