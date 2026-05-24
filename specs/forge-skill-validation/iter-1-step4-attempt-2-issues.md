# Audit — Step 4 attempt 2

**Auditor:** independent subagent
**Date:** 2026-05-24
**Worker manifest:** `specs/forge-skill-validation/iter-1-step4-attempt-2-output.md`
**Artifacts root:** `specs/forge-skill-validation/iter-1-step4-attempt-2-artifacts/`
**Spec authority:** `Documents/Downloads/done-when-pipeline.md` §6.1–6.8 + 附录 B
**Contract:** `specs/forge-skill-validation/iter-1-step3-attempt-2-artifacts/done_when.yaml`

Audit scope per directive: verify attempt-1's two P0s are eliminated, then re-walk
the §6.1–6.8 硬性约束 list.

---

## Headline verdict

**P0 count: 0.**
Both attempt-1 P0s are confirmed eliminated:

- **P0-1 (E2E verbatim names):** PASS — every Playwright `test()` first arg is
  byte-for-byte equal to the corresponding YAML name. Zero paraphrases.
- **P0-2 (existence fail-fast):** PASS — `existence.sh` uses `set -euo pipefail`
  + a `check()` helper that exits 1 on first failure. Zero count-all idioms,
  zero PASS/FAIL counters.

Remaining findings are quality (P1) and cosmetic (P2). None block the
artifact from being usable as the Step 5 implementation contract.

---

## P0-1 verification — E2E verbatim names

Method: extracted the first string-literal argument from every Playwright
`test(...)` call in `e2e/*.spec.ts`, compared to YAML `behavior.e2e_tests` as
sets.

| YAML entry | `test(...)` first arg in file | match |
|---|---|---|
| `test_mentioned_member_sees_in_app_banner_in_active_channel` | `'test_mentioned_member_sees_in_app_banner_in_active_channel'` (mentioned-member-sees-banner.spec.ts:18) | ✓ byte-for-byte |
| `test_member_in_dnd_sees_only_badge_increment_no_banner_no_sound` | `'test_member_in_dnd_sees_only_badge_increment_no_banner_no_sound'` (member-in-dnd-sees-badge-only.spec.ts:17) | ✓ byte-for-byte |
| `test_deleted_mention_message_retracts_visible_banner` | `'test_deleted_mention_message_retracts_visible_banner'` (deleted-mention-retracts-banner.spec.ts:17) | ✓ byte-for-byte |

Grep for the attempt-1 paraphrase signatures (`test('mentioned member …'`,
`test('member in DND …'`, `test('deleted mention message …'`) → zero hits.

Human-readable description has been correctly relocated to (a) `test.describe()`
titles, and (b) leading comments inside the `test()` body — exactly the
relocation the Fixer-revised SKILL rule prescribes.

**Result: P0-1 fixed.**

---

## P0-2 verification — existence fail-fast

`existence/existence.sh`:

- Line 16: `set -euo pipefail` present.
- Lines 21–25 define `check()`:
  ```bash
  check() {
    local label="$1"; shift
    "$@" >/dev/null 2>&1 || { echo "✗ FAIL: $label" >&2; exit 1; }
    echo "✓ $label"
  }
  ```
  Each invocation exits 1 on first failure via `|| { …; exit 1; }`.
- Grep for forbidden patterns: `if … then PASS=` (0), `PASS=` (0), `FAIL=` (0),
  `Passed:` (0), `Failed:` (0). The script has no counter at all.
- Final line is `echo "✓ All 20 existence checks passed"` — unreachable when any
  check fails (correct fail-fast semantics).
- 20 `check "…"` lines, matching the 20 entries in `done_when.yaml.existence`.

The Worker manifest also reports a live smoke run that exited 1 on the first
missing symbol; this is consistent with the script as written.

**Result: P0-2 fixed.**

---

## §6 硬约束 re-walk

### 1. 子步骤齐全度 (4-A … 4-F)

All six sub-step outputs present:

| Sub-step | Path | Status |
|---|---|---|
| 4-A existence | `existence/existence.sh` | ✓ |
| 4-B unit | `unit/{test_mention_pipeline,test_mention_edit_delete,test_dnd_lifecycle}.py` | ✓ |
| 4-C integration | `integration/{conftest,test_mention_flows,test_mention_properties}.py` | ✓ |
| 4-D e2e | `e2e/{*.spec.ts, fixtures.ts, playwright.config.ts}` | ✓ |
| 4-E mutation | `mutation/{pyproject.toml, mutation.sh, README.md}` | ✓ |
| 4-F fitness | `fitness/{*.rubric.md, README.md}` | ✓ |

PASS.

### 2. 测试名 1:1 对账 (verbatim audit)

Set-diff with `done_when.yaml`:

| Layer | YAML count | File count | YAML\Files | Files\YAML |
|---|---:|---:|---|---|
| unit (example + PBT) | 36 | 36 | ∅ | ∅ |
| integration (example + PBT) | 8 | 8 | ∅ | ∅ |
| e2e | 3 | 3 | ∅ | ∅ |

PASS — every single test name is verbatim. (Worker manifest claim verified
independently.)

### 3. existence.sh ↔ existence YAML coverage

`done_when.yaml.existence` has 20 entries (10 functions, 4 routes, 6 db fields).
`existence.sh` has exactly 20 `check` invocations covering the same 20 names.

PASS.

### 4. example_based ↔ WHEN-THEN derivation

Spot-checked each unit example test against `spec.md` EARS clauses:

- `test_individual_mention_in_top_level_channel_fires_all_four_surfaces` ← REQ-001
  "WHEN a member is `@`-mentioned in a team chat channel, THE system SHALL
  attempt delivery … concurrently on the push, in-app banner, sound, and
  unread-badge surfaces". Direct.
- `test_mention_under_dnd_suppresses_push_banner_sound` ← REQ-002 "WHILE …
  in Do-Not-Disturb mode, THE system SHALL silence …".
- `test_mention_to_non_member_of_channel_emits_no_notification` ← REQ-003
  "IF a user is mentioned in a channel of which they are not currently a
  member, THEN the system SHALL NOT deliver …".
- `test_self_mention_emits_no_notification` ← REQ-004 IF-clause.
- `test_edit_adding_new_mention_triggers_fresh_mention_pipeline` ← REQ-005 WHEN.
- `test_delete_retracts_in_app_banner_for_unopened_notification` ← REQ-006 WHEN.
- `test_dnd_deactivation_does_not_fire_retroactive_push` ← REQ-007 IF.

Every example test docstring cites the REQ-ID it derives from, and the
assertions trace to spec text. None are empty shells.

PASS.

### 5. PBT — uses Hypothesis, not `assert True`

- 9 unit PBTs + 2 integration PBTs = 11 PBTs, all decorated with `@given(...)`
  or `RuleBasedStateMachine.rule()`.
- 11 of 11 have `@settings(max_examples=500, deadline=None)` per the
  `thresholds.pbt_runs_per_property >= 500` contract.
- Grep for `assert True` in `unit/` and `integration/` → 0 hits.
- Property archetypes cover all six from `pbt-property-types.md`:
  idempotent (1), monotonic (1), invariant (5), reversible (1), boundary (1),
  state_machine (1).

PASS for the gross "no assert-True" gate. **See P1-001 / P1-002 below** for
quality issues inside two of the PBT bodies.

### 6. Mutation threshold 0.70

`mutation.sh` line 13: `THRESHOLD=70` (percent) — matches
`thresholds.mutation_kill_rate >= 0.70`. `mutation.sh` exits 1 below
threshold. PASS.

### 7. Fitness rubrics — not generic prompts

Both rubric files contain:

- Source REQ list.
- Verbatim criterion text (matches `done_when.yaml.fitness[*].criterion`).
- Verbatim `score_threshold` (`>= 8/10`).
- `judge: persona-judge` (not `llm-rubric`).
- JudgeBench accuracy-drop warning (55.6% → 42.9%) at top.
- 4 weighted sub-dimensions per file, weights sum to 1.0 (0.40+0.20+0.20+0.20
  and 0.50+0.20+0.20+0.10).
- Per-anchor concrete pass conditions at 1 / 4 / 7 / 10.
- "How to run" with the manual fresh-Claude-session workflow + the disclaimer
  that the existing `persona-judge` skill cannot consume these rubrics today.
- Re-run / ±0.5 boundary policy.

PASS — these are genuine multi-dimensional rubrics, not generic LLM prompts.

### 8. §6.8 EARS-句式 → 测试层级 映射合规性

The 矩阵 in §6.8:

| 句式 | 单元 | 集成 | E2E | PBT |
|---|---|---|---|---|
| Ubiquitous SHALL | ✓ | ✓ | ✗ | 强 |
| Event-driven WHEN | ✓ | ✓ | ✓ | 中 |
| State-driven WHILE | ✓ | ✓ | ✗ | 强 |
| Unwanted IF | ✓ | ✗ | ✗ | 弱 |
| Optional WHERE | ✓ | ✓ | ✓ | 弱 |

Observed mapping in artifacts (from spec.md REQ types):

| REQ | 句式 | Unit | Integ | E2E | matrix says | gap? |
|---|---|---|---|---|---|---|
| REQ-001 | Event-driven | ✓ | ✓ | ✓ | unit + integ + e2e | none |
| REQ-002 | State-driven | ✓ | ✓ | ✓ | unit + integ + **no e2e** | minor — see P2-001 |
| REQ-003 | Unwanted | ✓ | ✗ | ✗ | unit only | none |
| REQ-004 | Unwanted | ✓ | ✗ | ✗ | unit only | none |
| REQ-005 | Event-driven | ✓ | ✓ | ✗ | unit + integ + e2e | minor — see P2-002 |
| REQ-006 | Event-driven | ✓ | ✓ | ✓ | unit + integ + e2e | none |
| REQ-007 | Unwanted | ✓ | ✓ | ✗ | unit only | minor — see P2-003 |

REQ-002 is State-driven; the matrix says no E2E, but `done_when.yaml` (and the
artifact) include an e2e test for it. This is not a hard violation — the
matrix is a "should derive at least these levels" guide, not an upper bound.
Flagged as P2 because the manifest does not note the deviation from the
matrix.

Same reasoning for REQ-007 having an integration test despite being "Unwanted".

### 9. Mutation runner path — not currently runnable

`mutation/pyproject.toml` runner line:
```
runner = "pytest -x tests/channel-mention-notifications/unit/"
```
The actual generated unit tests live at
`specs/forge-skill-validation/iter-1-step4-attempt-2-artifacts/unit/`. The path
`tests/channel-mention-notifications/unit/` does not exist in the repo today.

This is **expected by design** — the manifest explicitly says mutation is "Not
run … too slow per 4-E rule" and the path reflects where the unit tests will
live once the implementer relocates them under the project's standard
`tests/` tree. The README also says "Adjust this list when the implementation
lands."

Not a P0/P1 violation because the path is **aspirational and labeled as such**.
Flagged as P2 (P2-004) only for the soft-failure that if someone runs
`bash mutation.sh` today, mutmut will fail with a misleading error. A
one-line "this path will be valid post-relocation" comment in `mutation.sh`
(currently only in `mutation/README.md` and `pyproject.toml`) would close
the gap.

---

## P0 issues

**None.**

The two attempt-1 P0s (`E2E paraphrase`, `existence count-all`) are both
verified fixed. No new P0s detected.

---

## P1 issues (quality)

### P1-001 — DND state-machine PBT mostly asserts its own bookkeeping

**File:** `unit/test_dnd_lifecycle.py` lines 65–171
**Class:** `DNDLifecycleStateMachine`

Three claimed invariants (i / ii / iii) but only one of them actually
exercises real implementation code:

| invariant | what is observed | observation source |
|---|---|---|
| (i) `push_banner_sound_never_fire_under_dnd` (lines 144–151) | `self.surfaces_fired_history[-1]` | **the state machine's own list** populated by `deliver_mention` (lines 118–127) via Python `if/else`, NOT by calling `DispatchMentionNotification`. The "invariant" is tautologically true given how `deliver_mention` is written. |
| (ii) `unread_badge_is_non_decreasing` (lines 153–158) | `self.unread_badge_count` | **the state machine's own counter** incremented by `self.unread_badge_count += 1` at line 127. `assert self.unread_badge_count >= 0` is trivially true. The docstring even concedes this: *"…structurally guaranteed; the assertion documents the property."* |
| (iii) no retroactive surfaces on deactivate | `OnDNDDeactivated(...)['surfaces_fired']` (lines 130–141, in `_on_deactivate`) | real call — this part exercises actual implementation. |

So the value of this PBT is roughly **1/3 of what its docstring claims**.

This is not a hard violation of §6.6 (mutation testing) — it's a quality
weakness in the PBT layer. But it is exactly the failure-mode §6.6 warns
about: a PBT that *looks* like a property-based test but in practice only
re-asserts what the test fixture already controls. Mutation testing in the
project (when eventually run) will quickly expose this — surviving mutants
will pile up around `push_banner_sound_never_fire_under_dnd` because
mutating implementation code cannot kill an assertion that doesn't reach
implementation code.

**Recommendation (not in scope to fix, just noting):** invariants (i) and
(ii) should call `DispatchMentionNotification` / `UnreadBadgeSurface` from
the rule bodies, and assert on the **returned** surface set / counter — not
the state-machine's own list/integer.

### P1-002 — `test_mention_dispatch_atomicity_across_surfaces_and_counters_invariant` does not test atomicity

**File:** `integration/test_mention_properties.py` lines 21–70
**Test:** `test_mention_dispatch_atomicity_across_surfaces_and_counters_invariant`

Name and docstring promise an **atomicity** invariant (all-or-nothing across
surfaces and counters). Body actually tests:

1. `body["delivered"] == any(outcome.values())` — the "delivered ⇔ at least
   one surface succeeded" invariant from REQ-001. This is a delivery
   *semantics* invariant, not atomicity.
2. `actual_badge == badge_success_count` — the per-call badge counter
   accumulates the count of successful badge surface calls. Again, not
   atomicity (no rollback test, no inverse-on-failure check).

There's no "if anything fails, nothing is observed" assertion anywhere in
the test. The §6.4 PBT example for cross-module atomicity (lines 421–433 of
the design doc) uses `system_state_snapshot()` and asserts
`before == after` on failure — that pattern is absent here.

This is a name↔body mismatch. The test as written is useful (it does test
real cross-boundary consistency between HTTP response and DB row), but its
name promises a property the body does not check. **Re-classification or
re-body needed, but P1 not P0** because the test does verify *something*
real.

### P1-003 — `fired` return-type contract is internally inconsistent

**File:** `unit/test_mention_pipeline.py`

The return value of `DispatchMentionNotification(...)` is used three
incompatible ways within the same file:

| line | use | implied type |
|---|---|---|
| 65–70 | `surfaces_fired = DispatchMentionNotification(...)` then `PushSurface.__name__ in surfaces_fired` | list[str] OR dict-keys[str] |
| 80–83 | `result = DispatchMentionNotification(..., surface_outcomes=...)` then `result["delivered"] is True` | dict |
| 168–171 / 241–244 | `fired = DispatchMentionNotification(...)` then `"PushSurface" not in fired` | dict-keys[str] / list[str] |
| 182–187 | `fired = DispatchMentionNotification(...)` then `"UnreadBadgeSurface" in fired` AND `fired["counters_after"]["unread_badge_count"] == 4` | dict where keys mix surface names AND `"counters_after"`/`"delivered"`/etc. |
| 269–270 | `result["mentioner_errors"] == []` | dict |
| 313–317 | `DispatchMentionNotification.apply(event, state=state)` — classmethod, no return | (different shape) |

An implementer trying to make all six call-sites pass must return a dict
where the keys are a **mix of surface names** (`"PushSurface"`,
`"InAppBannerSurface"`, …) AND metadata keys (`"delivered"`,
`"counters_after"`, `"counters_after_dict"`, `"surfaces_fired"`,
`"mentioner_errors"`). That is unusual / brittle: the test contract bakes in
a return type that no sane API designer would choose.

The PBT at line 313 even uses a **classmethod** (`DispatchMentionNotification.apply`)
that does not return anything — coexisting with all the dict-returning
call-sites on the same `DispatchMentionNotification` symbol.

This is a contract-quality issue. It will surface in Step 5 when the
implementer asks "what should this function actually return?" — and there
will be no consistent answer in the test suite. **P1, not P0**, because the
function name is grep-able and tests do exercise distinct behaviors; but
Step 5 will likely need a contract clarification or test patch.

### P1-004 — integration test `_force_surface_outcomes` test hook is undocumented in the contract

**File:** `integration/test_mention_properties.py` line 55

The atomicity PBT posts `{..., "_force_surface_outcomes": outcome}` to
`/api/messages` to drive arbitrary per-surface outcomes. This requires the
production API to accept (and respect) a `_force_surface_outcomes` field —
which is a **test-only side door** with no mention in `done_when.yaml` or
`spec.md`.

`/api/_test/seed_member`, `/api/_test/seed`, `/api/_test/post_mention_as_other`,
`/api/_test/messages/:id`, `/api/_internal/surface_log`,
`/api/_internal/surface_log?member=…` are all in similar shape — used by the
test suite, undefined by the contract. None appear in `existence` checks.

This is the inverse of the existence-coverage problem: the test suite *implicitly*
demands a bigger contract than `done_when.yaml` makes explicit. The Step 5
implementer will ship test-only endpoints without traceability in the
acceptance spec — a small but real spec-drift risk.

**Recommendation (not in scope to fix):** either (a) add these test-only
routes to `done_when.yaml.existence` so they get grep-verified, or (b) make
explicit in the manifest that the integration suite depends on test-hook
endpoints the contract should also list.

---

## P2 issues (cosmetic / style)

### P2-001 — REQ-002 has an E2E test even though §6.8 matrix says State-driven sees no E2E layer

`done_when.yaml.behavior.e2e_tests[1]` = `test_member_in_dnd_sees_only_badge_increment_no_banner_no_sound`,
which derives from REQ-002 (State-driven). §6.8 says the matrix row for
State-driven is `E2E: ✗`. The matrix is best-practice guidance, not a hard
gate (the §6.5 rule is the hard one — "数量少而精, 只覆盖关键用户旅程", which 3 tests passes). The
worker is correct to include this test if Step 3 listed it, but the manifest
does not note the matrix-deviation.

### P2-002 — REQ-005 lacks an E2E test that §6.8 matrix says Event-driven gets

REQ-005 is Event-driven, matrix row says `E2E: ✓` is allowed. The contract
omits one, so the artifact omits one. This is the upstream Step 3 contract's
call (iron rule #7: no inventing requirements), not a generator bug. Noted
for symmetry with P2-001.

### P2-003 — REQ-007 has an integration test even though §6.8 matrix says Unwanted gets unit only

`done_when.yaml.behavior.integration_tests.example_based`
includes `test_dnd_window_expiry_does_not_trigger_resurfacing_dispatch`,
which derives from REQ-007 (Unwanted). Matrix row says `Integ: ✗`. Same
"contract over matrix" reasoning as P2-001; flagged for log-completeness.

### P2-004 — `mutation/mutation.sh` does not echo the "post-relocation" caveat

The path `tests/channel-mention-notifications/unit/` (assumed in
`pyproject.toml`) does not exist at the current artifact location. The
README explains this, but `mutation.sh` itself does not. Anyone who runs
`bash mutation.sh` today gets a confusing `mutmut run` failure. One comment
at the top of `mutation.sh` clarifying "expects the unit suite at
tests/channel-mention-notifications/unit/ — relocate or symlink before
running" would close the trap.

### P2-005 — Worker manifest miscounts invariant PBTs

Manifest line 63: *"`_invariant` (4 — three on REQ-002/REQ-003/REQ-004/REQ-006)"*.
The list names **four** REQs, and there are indeed **5** `*_invariant_*`
PBTs (3 in `test_mention_pipeline.py`, 1 in `test_mention_edit_delete.py`,
1 — `test_per_channel_mute_consistently_silences_across_restart_invariant`
— in integration). Cosmetic count error in the manifest narrative; does
not affect artifacts.

### P2-006 — Two PBT generators define narrow alphabets/labels but doc them inconsistently

`mention_dispatch_events` (line 290 of test_mention_pipeline.py) draws
`msg_id` from `st.text(alphabet="abcdef0123456789", min_size=4, max_size=8)`
— a narrow hex strategy. Reasonable; just not documented as "msg_id is
expected to be hex". For a generator-produced test it's fine, but a human
reader maintaining this in Step 6 may not realize.

Cosmetic, not affecting validity.

---

## Summary

| Category | Count |
|---|---:|
| P0 (hard violation, §6.1–6.7) | **0** |
| P1 (quality, surface in Step 5) | 4 |
| P2 (cosmetic / matrix deviation) | 6 |

Both attempt-1 P0s — E2E paraphrase and existence count-all — are verified
eliminated. The artifact is suitable to hand to Step 5 as the implementation
contract.

The four P1s cluster around two themes worth flagging to the human reviewer:

1. **PBT semantic depth** (P1-001, P1-002): two of the more ambitious PBTs
   are weaker than their names suggest. Mutation testing will surface this
   later but a Step 4 audit catches it cheaper.
2. **Test-only return shapes / endpoints** (P1-003, P1-004): the test
   suite implicitly defines API surface area that the formal `done_when.yaml`
   contract does not list. Spec-drift risk for Step 5 / 6.

None of these are generator-level §6 violations; they are contract /
quality observations the human reviewer can decide to push back on or
accept.
