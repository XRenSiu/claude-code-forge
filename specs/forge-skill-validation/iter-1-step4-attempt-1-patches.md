# Step 4 Attempt 1 — Fixer Patches

**Fixer**: subagent
**Scope**: only `plugins/done-when-pipeline/skills/test-suite-generator/`
**Driver issues file**: `iter-1-step4-attempt-1-issues.md`
**Strategy**: pin down the two P0 root causes (paraphrased e2e names, count-all existence) by making the rules **explicit and hard** in SKILL.md iron rules + 4-A/4-D sections, and by **rewriting the sub-module reference docs** so the templates the next Worker copies cannot lead them astray. Paraphrased example code is rewritten to be verbatim. Forbidden patterns are listed by name.

---

## Issues addressed

| ID | Title | Status |
|---|---|---|
| **P0-1** | E2E test names paraphrased (`'mentioned member sees in-app banner …'` instead of `'test_mentioned_member_sees_in_app_banner_in_active_channel'`) | **Fixed** — verbatim rule now stated in iron rule #9, SKILL §4-D, `e2e-generator.md`, `unit-test-generator.md`, `integration-generator.md`; example code rewritten to verbatim |
| **P0-2** | `existence.sh` wraps checks in `if … fi`, defeating `set -e`; header comment ("after counting all") contradicts §6.2 | **Fixed** — iron rule #10 added, SKILL §4-A explicitly forbids `if`-wrap and count-all summary, `existence-extractor.md` template rewritten to true fail-fast, forbidden pattern shown by name |

P1/P2 issues intentionally **not** touched per this Fixer's narrow mandate (P0-only).

---

## Files modified

1. `plugins/done-when-pipeline/skills/test-suite-generator/SKILL.md`
   - Iron rules §9 (verbatim names) and §10 (fail-fast existence) added.
   - §4-A rewritten: required `cmd || { echo …; exit 1; }` idiom shown; forbidden `if … fi` and "count-all" tally explicitly named.
   - §4-D rewritten: verbatim test name rule for `test('<name>', …)` / `it(...)` made hard with a table of correct/forbidden examples.

2. `plugins/done-when-pipeline/skills/test-suite-generator/references/sub-modules/existence-extractor.md`
   - "Hard rule: fail-fast" section added at top.
   - Template `check()` helper rewritten to fail-fast (no `if`, no PASS/FAIL counters, no summary block).
   - "Forbidden pattern (do NOT generate this)" block added that names the exact wrong-pattern Worker emitted.
   - Header comment fixed: no more contradictory "after counting all".

3. `plugins/done-when-pipeline/skills/test-suite-generator/references/sub-modules/e2e-generator.md`
   - Rule list grew a §6 ("Verbatim test name (CRITICAL)").
   - New top-level "Verbatim test name (hard rule)" section with a correct/forbidden table targeting the exact YAML entries the Worker paraphrased.
   - Playwright example block rewritten: `test('test_mentioned_member_sees_in_app_banner_in_active_channel', …)` verbatim from YAML, with human-readable description moved into a comment and a `test.describe(...)` wrapper.
   - Cypress example block rewritten with verbatim `it()` arg + reminder comment.

4. `plugins/done-when-pipeline/skills/test-suite-generator/references/sub-modules/unit-test-generator.md`
   - "Hard rule: verbatim test name" section added.
   - TypeScript vitest example rewritten: `test('test_cancel_is_idempotent', …)` instead of `test('cancel is idempotent (REQ-001)', …)`, with REQ tag moved to a comment.

5. `plugins/done-when-pipeline/skills/test-suite-generator/references/sub-modules/integration-generator.md`
   - Verbatim-name pointer added at the top.
   - TypeScript supertest example rewritten: `test('test_cancel_api_returns_200_and_correct_payload', …)`.

---

## Per-file before/after with rationale

### 1. `SKILL.md` — iron rules expansion

**Before** (8 iron rules; nothing on verbatim names or fail-fast):
```md
8. **Pyramid ratio rebalanced for AI-coding.** … 50/35/15 …
```

**After** (added §9 and §10):
```md
9. **Verbatim test names from `done_when.yaml`.** … TS/JS `test('…')` / `it('…')` is the trap …
10. **Existence script is fail-fast (`set -e`), not count-all.** … Wrapping checks in `if … then PASS=… else FAIL=… fi` defeats `errexit` — that pattern is forbidden.
```

**Rationale**: iron rules are re-read before every sub-step (per the skill's own instruction), so this is the highest-leverage place to plant both P0 fixes. They will hit the Worker's working context on every batch.

---

### 2. `SKILL.md` §4-A — existence fail-fast made explicit

**Before**: §4-A said:
> Each check echoes `✓ <kind>: <thing>` or fails (`set -euo pipefail` at the top). The script returns nonzero on first failure. This is the fast-fail gate.

That was too soft — it stated the intent but not the **forbidden** patterns, so the Worker chose a friendlier "tally" implementation in good faith.

**After**: added a dedicated "Fail-fast is mandatory" subsection that:
1. Shows the required idiom (`<cmd> || { echo "FAIL: …" >&2; exit 1; }`) as the **only** acceptable form, and a `check()` helper that uses `||` rather than `if`.
2. Lists three forbidden patterns under "Forbidden patterns" headed with **WRONG** comments — the `if`/`else` body, the `PASS/FAIL` tally, and the trailing `if [[ $FAIL -gt 0 ]]; then exit 1; fi` summary. These are the exact patterns Worker emitted.
3. Tells the user how to request a count-all diagnostic mode if they really want one (separate filename, never default).

**Rationale**: P0-2 is fundamentally a docstring problem — the doc described intent but never said "do not wrap in `if`". Saying it explicitly is the smallest, most targeted fix.

---

### 3. `SKILL.md` §4-D — verbatim e2e names made hard

**Before**: §4-D was silent on the test identifier string itself; the only guidance was "data-test selectors", "short", "no fixed sleeps". A Worker reading only §4-D had no signal to keep the YAML name verbatim.

**After**: added a "Test names MUST be verbatim from `done_when.yaml` (no paraphrasing)" subsection that:
1. States the rule with a per-layer table (existence / unit / integration / e2e) showing where the verbatim slot lives.
2. Shows correct Playwright code with `test('test_mentioned_member_sees_in_app_banner_in_active_channel', …)`.
3. Shows the forbidden paraphrases with `// WRONG: paraphrased to a sentence` comments — using the **exact strings** the Worker produced, so a future Worker scanning for "this looks like what I'd write" gets a direct mirror of the failure mode.
4. Tells the Worker where to put human-readable description (comment / `describe()` / annotation) so the rule doesn't feel like it forbids useful information.

**Rationale**: same logic as 4-A — the rule needs to be visible in the section the Worker is reading when they generate the file.

---

### 4. `existence-extractor.md` — template rewrite

**Before**: the canonical template the Worker copies wholesale shipped the bug. The `check()` helper was:
```bash
if "$@" >/dev/null 2>&1; then
  echo "✓ $label"; PASS=$((PASS+1))
else
  echo "✗ $label" >&2; FAIL=$((FAIL+1))
fi
```
plus a trailing PASS/FAIL summary and `if [[ $FAIL -gt 0 ]]; then exit 1; fi`. This **is** the count-all pattern.

**After**: helper rewritten as:
```bash
check() {
  local label="$1"; shift
  "$@" >/dev/null 2>&1 || { echo "✗ FAIL: $label" >&2; exit 1; }
  echo "✓ $label"
}
```
Trailing summary reduced to a single `echo "✓ All existence checks passed"` that is only reached if every check passed (because the `||`-branch exits early). A "Forbidden pattern (do NOT generate this)" block right below shows the old (wrong) code with `# WRONG —` annotations so any future LLM that pattern-matches the wrong style gets the contradiction in the very same file.

Header comment fixed:
- Before: `# Run from project root. Exits nonzero on first failure (after counting all).` — self-contradictory.
- After: `# Run from project root. Exits nonzero on the FIRST failure (set -e semantics).`

**Rationale**: the Worker faithfully copied the doc's template. The bug was in the template, not the Worker.

---

### 5. `e2e-generator.md` — example rewrite + dedicated rule

**Before**:
```ts
test('user can cancel active subscription and sees expiry notice', async ({ page }) => { … });
```
The skill's own example uses a paraphrased sentence as the test title. The Worker copied this style.

**After**:
1. Added "Verbatim test name (hard rule)" section with correct/forbidden table that names the three exact e2e tests from the Worker's mistake.
2. Playwright example rewritten:
   ```ts
   // Maps to done_when.yaml e2e: test_mentioned_member_sees_in_app_banner_in_active_channel
   test.describe('Channel mention notifications — in-app banner', () => {
     test('test_mentioned_member_sees_in_app_banner_in_active_channel', async ({ page }) => { … });
   });
   ```
   — verbatim YAML name, human-readable framing in `describe` and a comment.
3. Cypress example rewritten similarly with verbatim `it()` arg.

**Rationale**: same as above. The doc's templates are normative; if they're paraphrased, downstream output will be paraphrased. The fix is to make the templates themselves verbatim.

---

### 6. `unit-test-generator.md` and `integration-generator.md` — verbatim rule + TS example fix

`unit-test-generator.md`: added a "Hard rule: verbatim test name" subsection that handles each language (Python `def` is naturally verbatim; TS `test('…', …)` is the trap; Swift `func test_…` is fine; Kotlin prefers `fun test_xxx` over backtick string identifiers when YAML is snake_case). TS vitest example rewritten to `test('test_cancel_is_idempotent', …)` from the older paraphrased `test('cancel is idempotent (REQ-001)', …)`.

`integration-generator.md`: added a one-line pointer at the top to the unit-test-generator's verbatim rule (avoids duplicating the full statement in two files). TS supertest example rewritten verbatim.

**Rationale**: P0-1 happened to be E2E in this run, but the same vulnerability exists for TS-stack unit / integration tests. Closing it at the source-of-truth (the reference docs) prevents the same bug surfacing in attempt 2 in a different layer.

---

## Issues intentionally NOT fixed (P1 / P2)

Per the Fixer brief — "只能改 P0 ... 不修 P1/P2"。

| ID | Why deferred |
|---|---|
| P1-1 (mutation path `tests/channel-mention-notifications/unit/` is dangling) | Ratchet/Step 5 surface concern; mutation config itself is structurally correct. |
| P1-2 (PBT uses `return` instead of `hypothesis.assume`) | Tests are not vacuous; vacuous-pass rate is bounded by 500 runs. Belongs in a future PBT-quality pass on `pbt-property-types.md`. |
| P1-3 (RuleBasedStateMachine fixture sharing causes state bleed across examples) | Real bug, but it's about fixture lifecycle understanding in `integration-generator.md`, not a P0 contract violation. |
| P1-4 (REQ-004 missing integration coverage) | Cannot resolve without re-reading spec.md to verify its EARS phrase type; outside Fixer scope. |
| P1-5 (Worker manifest self-contradiction 28 vs 27) | Manifest-level cosmetic, no source-code knob to turn. |
| P1-6 (`pytest.mark.integration` marker used only once) | SKILL doesn't currently mandate marker policy; out of scope. |
| P2-1 to P2-4 | Pure cosmetic / style observations. |

---

## Risk assessment

- **Scope of changes**: 5 files inside one skill. No changes to acceptance-spec, no changes to design doc, no changes to product artifacts.
- **Behavior change for next Worker attempt**:
  - Existence script will be true fail-fast — exits on first missing existence claim. **Downside**: less diagnostic info on a fresh run (the implementer sees only the first failure, not the full list). **Upside**: aligns with §6.2; the diagnostic case can be re-added later as a separate `existence-diag.sh` script if needed. Worth the trade per the design doc.
  - All test files will have verbatim YAML names as identifiers, which means human-readable scanning of `pytest -v` or Playwright HTML reports will be a little more terse (`test_mentioned_member_sees_in_app_banner_in_active_channel` instead of `mentioned member sees in-app banner in active channel`). This is the price of grep-able contract ↔ implementation traceability; the design doc and audit checklist already chose this trade-off.
- **No version bump**: this is mid-validation iteration of an unreleased plugin (`0.1.0`); per the Fixer brief, only skill source is touched, not release metadata. The orchestrator can decide whether attempt-2-passing warrants a version bump.
- **Forward compatibility**: every example in the sub-module docs that previously used a paraphrased test name has been rewritten. Future Workers shouldn't see the old style mirrored back to them anywhere in this skill's references.

---

## What attempt 2 should now do differently

1. When generating existence.sh, use the new fail-fast `check()` helper (no `if`, no PASS/FAIL counters). The reference template now embeds this directly.
2. When generating Playwright `*.spec.ts`, the first arg to `test()` MUST be the verbatim YAML name (e.g. `test('test_mentioned_member_sees_in_app_banner_in_active_channel', …)`). Same for vitest, jest, Cypress `it()`. Human description belongs in `describe()` / comment / annotation.
3. (Implicit) iron rules now include #9 and #10 covering both rules at the very top of SKILL.md, which the Worker re-reads at every sub-step boundary.
