---
name: test-suite-generator
description: >-
  Turn an EARS spec + done_when.yaml contract into the full test pyramid: existence
  checks (ripgrep/tree-sitter), unit tests (example-based + property-based), integration
  tests (with testcontainers, no mocks), e2e (Playwright/Cypress/Appium/Maestro), and
  mutation-testing configuration as an anti-reward-hacking layer (mutmut/Stryker/PIT).
  Walks five sub-steps (4-A existence / 4-B unit / 4-C integration / 4-D e2e / 4-E
  mutation) ONE BATCH AT A TIME — a known failure mode is "generate all tests at
  once → quality collapse"; this skill explicitly serializes the batches. Each
  generated test is tagged with `based_on: [REQ-IDs]` so the trace from requirement
  → test is mechanical. The former 4-F "fitness rubric" sub-step was retired in
  v1.0.0 per the HTML v2 §3.5 corollary (fitness-check dissolution) — most of its
  content re-routes to programmatic verification in other layers; the genuinely-
  unautomatable ~10% is handled by /pm-reviewer's `requires_human_verification`
  verdict, not an LLM rubric. Triggers: "generate tests for spec X" / "derive
  test suite" / "build verification battery" / "/test-suite-generator" /
  pointing at any specs/<feature>/ directory.
argument-hint: "<path to specs/<feature>/ or path to done_when.yaml>"
version: 1.0.0
user-invocable: true
---

# test-suite-generator — EARS spec → full test pyramid

You are invoked to turn an upstream acceptance-spec output (a `specs/<feature>/` directory containing `spec.md` and `done_when.yaml`) into the actual test files that an independent agent can execute to verify implementation.

**Say once at the start, then start working:**
> "I'm using the test-suite-generator skill. I'll walk five sub-steps (existence → unit → integration → e2e → mutation), one batch at a time. Each generated test traces back to a REQ-ID via `based_on:`."

Do not narrate further — just walk the sub-steps.

---

## Iron rules (re-read before every sub-step)

1. **Verifiable beats judgeable.** Programmatic checks (assertion-based tests, AST inspection, mutation kill rate) beat LLM-as-judge on speed, cost, consistency. Per HTML v2 §3 principle I (and §3.5 corollary): most claims that *feel* like they need an LLM judge can be re-designed as programmatic checks — "README quickstart works" → really run it; "agent can call API from docs alone" → spin a clean session; "types are correct" → run `tsc`/`mypy`. The ~10% genuinely-unautomatable cases are routed to `/pm-reviewer`'s `requires_human_verification` verdict, not to a fake LLM rubric here. This skill does NOT emit fitness rubrics in v1.0.0 (former 4-F was retired).
2. **One batch at a time.** Generate → write to disk → run → iterate. Then proceed. **Never generate all six batches in one pass** — empirically, LLM test generation quality collapses past a few dozen tests in a single prompt. The doc that motivates this skill names this as Pitfall #2; do not be the next person to step on it.
3. **PBT property type is recovered from the test name.** Under schema v1 (Appendix C of `done-when-pipeline.md`), every leaf entry under `behavior.*.property_based` / `behavior.*.example_based` / `e2e_tests` is a **bare string** — there is no `property_type:` sub-field on the entry. Parse the test name suffix to infer the property archetype (one of: `invariant` / `idempotent` / `reversible` / `boundary` / `monotonic` / `state_machine`). E.g. `test_cancel_is_idempotent` → idempotent pattern. Read `references/pbt-property-types.md` to know which pattern to emit. If a property-based name does not encode a recognisable archetype, **the requirement is not a good PBT candidate** — emit an example-based test instead and tell the user the name should be revised upstream.
4. **No mocks for integration tests.** Use testcontainers (or equivalent) to spin up real Postgres / Redis / Kafka / etc. Mocks hide interface drift, which is exactly the failure mode that catches AI-generated code most often. If the language lacks testcontainers, fall back to docker-compose; do not fall back to mocks.
5. **Mutation testing is mandatory, not optional.** A done_when that only enforces coverage ≥ 80% will incentivize the implementer to write `assert True` to inflate the number. Mutation kill rate ≥ 70% is the gate that closes that loop. Always emit a `mutation.config` file (4-E).
6. **Every generated test carries `based_on:`.** Either as a comment header in the test file (`# based_on: REQ-001, REQ-003`), or as part of the test name when the language convention favors it. Tests without traceability cannot be culled when a REQ is dropped, and cannot be explained when they fail.
7. **No inventing requirements.** If a property occurs to you that isn't in any REQ, **do not** add a test for it. Either push back upstream ("REQ-NNN seems to imply X — should that be a separate REQ?") or skip it. Tests must derive from the spec, not from your own intuition about what a good system does.
8. **Pyramid ratio rebalanced for AI-coding.** Per the source doc, AI-written code is more likely to fail at module boundaries (interface mismatches, protocol confusions). Target ~50% unit / ~35% integration / ~15% e2e — not the traditional 70/20/10. Push slightly more weight into integration than you might be used to.
9. **Verbatim test names from `done_when.yaml`.** The string the framework records as the test identifier must equal the YAML entry character-for-character (prefix, underscores, suffix). Python `def test_*` is naturally fine; TS/JS `test('…')` / `it('…')` is the trap because it accepts arbitrary strings. Human-readable descriptions go in comments, `describe()` blocks, or annotations — never in the `test()` first argument. See §4-D for the full rule + forbidden-pattern examples; this exists because downstream tooling (`/ratchet`, evaluators) `grep`s contract names against produced files, and any paraphrase breaks traceability.
10. **Existence script is fail-fast (`set -e`), not count-all.** The script in §4-A MUST exit on the first failing check. Wrapping checks in `if … then PASS=… else FAIL=… fi` defeats `errexit` — that pattern is forbidden. See §4-A for the required idiom and the explicit list of forbidden patterns.
11. **Test-only API endpoints must be registered as existence claims.** Any endpoint the test suite calls but that is not part of the user-facing contract (`/api/_test/*`, `/api/_internal/*`, hidden test-hook query/body fields like `_force_surface_outcomes`) MUST be added to `done_when.yaml.existence:` as a `route:` entry — otherwise the test suite implicitly demands a bigger contract than the contract makes explicit (spec drift). If `done_when.yaml` was emitted by `/acceptance-spec` and does not list these endpoints, either (a) **push back upstream** ("the contract is missing test-hook endpoints X, Y, Z — regenerate via `/acceptance-spec` to include them") or (b) add the entries here and note the augmentation in the manifest you emit at the end of the skill. Never ship a test suite that calls undeclared endpoints. See §4-A for the existence list and §4-C for the test-hook conventions.
12. **Self-report version comes from this SKILL.md frontmatter, not a hardcoded literal.** Every emitted file's "Generated by test-suite-generator/X.Y.Z" header MUST be filled in by reading the `version:` value from this `SKILL.md`'s YAML frontmatter at generation time. Do NOT paste a version literal lifted from `references/sub-modules/*.md` templates (those use a `<skill-version>` placeholder for this exact reason). The downstream audit signal is: artifact self-report mismatch with `plugin.json` ⇒ skill source bug. See §4-B "Version-string substitution rule" for the canonical reminder.

13. **Each REQ's test layer set should match §6.8 of the design doc (the EARS-type → test-layer matrix).** When deciding which tests in `done_when.yaml.behavior.*` correspond to which REQ:
    - Look up the REQ's EARS type in `references/ears-to-test-matrix.md`.
    - The row says which layers (unit / integration / e2e) are "usually expected" for that type and which are typically absent.
    - **If the YAML already lists tests** for a layer the matrix marks `–` (e.g. an e2e test for a State-driven or Unwanted REQ), generate it but flag the deviation in the file header comment (`# matrix-deviation: REQ-XXX State-driven gets e2e per Step 3 contract`).
    - **If the YAML omits tests** for a layer the matrix marks `✓`, do NOT invent them — that's iron rule 7 ("No inventing requirements"). Just note the omission in the manifest.
    The matrix is a *sanity-check on the contract*, not an override of it. But the deviations need to be visible so Step 5/6 reviewers can decide whether to push back on Step 3 or accept the choice.

---

## Sub-step map

```
0     Bootstrap         read specs/<feature>/, validate done_when.yaml shape, detect target language
4-A   Existence         grep/AST script that proves each listed noun exists in code
4-B   Unit              one function/class at a time; example + property tests
4-C   Integration       multi-module; uses testcontainers; example + cross-module PBT
4-D   E2E               Playwright/Cypress/Appium/Maestro; few but real user journeys
4-E   Mutation          mutmut/Stryker/PIT config + invocation script
```

> **Removed in v1.0.0:** the former 4-F "Fitness rubric" sub-step is gone. Per HTML v2 §3.5 (fitness-check dissolution): the schema only keeps `existence + behavior + rules`. If you encounter a legacy `done_when.yaml` with a `fitness:` block, the schema validator (`references/done-when-schema-validator.md`) rejects it and asks the user to regenerate via `/acceptance-spec` v1.0+.

After each sub-step, write the files, run them (existence/unit immediately runnable; integration if testcontainers usable; e2e is fine to leave runnable-but-not-run), and proceed. Only on a hard failure do you stop and report.

---

## 0 — Bootstrap

1. Parse `$ARGUMENTS`. Accept either:
   - a `specs/<feature>/` directory (read `spec.md` + `done_when.yaml`)
   - a path directly to a `done_when.yaml` (resolve its sibling `spec.md`)
2. Validate `done_when.yaml` against `references/done-when-schema-validator.md` (a checklist; if you don't have an automated validator, walk the checklist manually). Bail out if `feature:` missing, if any `based_on:` references a REQ that does not exist in `spec.md`, or if `mutation_kill_rate` threshold is absent.
3. Detect the target language(s) of the project:
   - `package.json` → TypeScript / JavaScript
   - `pyproject.toml` / `requirements.txt` → Python
   - `Package.swift` / `*.xcodeproj` → Swift
   - `build.gradle*` → Kotlin / Java
   - mixed → emit per-language test trees, do not try to unify.
4. Read `references/tooling-by-language.md` to pick the concrete tool stack.
5. Decide output directory. Default to `tests/<feature>/` next to the spec; if the project has an established test root (`tests/`, `__tests__/`, `spec/`, `test/`), put a subdirectory `<that_root>/<feature>/` to match the project's convention.
6. Read `references/ears-to-test-matrix.md` so the per-sub-step generation logic is fresh.

No user output yet.

---

## 4-A — Existence checks

For each entry in `done_when.yaml`'s `existence:` block, emit one check line.

Read `references/sub-modules/existence-extractor.md` for the full grammar.

**Output:** a single script (`existence.sh` for shell-friendly projects, `existence.py` if Python-only stack). Each line:

- `file:` → `test -f <path>`
- `function:` → broadly-covering `rg` that matches ALL legal export forms (direct `export class|function|const|let|var`, `export default class|function`, and named re-exports `export { Name }` / `export { Name as Alias }`). For TS: `rg -qU "export\s+(default\s+)?(class|function|const|let|var)\s+<Name>\b|export\s*\{[^}]*\b<Name>\b" src/`. For Python: use `ast` introspection. Falling back to a too-narrow regex (e.g. `export\s+(class|function|const)\s+<Name>` only) produces false negatives on `export default …` and barrel re-exports — both are legitimate exported forms. See `references/sub-modules/existence-extractor.md` for the full per-kind recipe.
- `route:` → grep for the route declaration in router files
- `db_field:` → grep migration/schema files for `<table>.<column>`
- `frontend_component:` → grep for the component name in `src/components/`

(Schema v1 defines exactly these five kinds. Older drafts of this skill listed `env_var:` and `cli_command:`; those are not part of v1 — if you see them in a contract, the validator should have already rejected it. Bail out and ask the user to regenerate via `/acceptance-spec`.)

### Fail-fast is mandatory (do not "count-all-then-exit")

Per `done-when-pipeline.md` §6.2, existence checks MUST stop on the **first** failure (`set -e` semantics). The whole point is "fast-fail before behavior" — surfacing one missing symbol immediately is more valuable than a 20-line tally of everything that's missing.

**Required pattern** (each check):

```bash
set -euo pipefail   # MUST be on the first non-shebang line

echo "checking <label>..." && <check command> >/dev/null 2>&1 \
  || { echo "✗ FAIL: <label>" >&2; exit 1; }
echo "✓ <label>"
```

Or as a helper without `if`:

```bash
check() {
  local label="$1"; shift
  "$@" >/dev/null 2>&1 || { echo "✗ FAIL: $label" >&2; exit 1; }
  echo "✓ $label"
}
```

**Forbidden patterns** (these defeat `set -e` because `if`/`||`-with-assignment swallow the failure):

```bash
# WRONG — `if` context disables errexit; script counts and runs to the end.
if "$@" >/dev/null 2>&1; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

# WRONG — same problem with a PASS/FAIL tally + exit at the bottom.
echo "─────"
echo "Passed: $PASS · Failed: $FAIL"
if [[ $FAIL -gt 0 ]]; then exit 1; fi
```

If a user *insists* on a count-all-then-exit diagnostic mode, that's a SKILL-level upgrade discussion (and a different file name like `existence-diag.sh`); do not silently switch defaults.

Append at the end: `echo "✓ All <N> existence checks passed"`.

Run it. If it fails (which is expected on first run — the implementer hasn't written the code yet), that's fine — the script becomes part of the contract, not a current-pass requirement. Document this in a header comment, and make sure the header does NOT contradict the fail-fast behavior (no "after counting all" wording).

---

## 4-B — Unit tests

Read `references/sub-modules/unit-test-generator.md`.

For each test name in `done_when.yaml` `behavior.unit_tests`:

- Under schema v1 (Appendix C), entries are bare strings — there is no per-entry `based_on:` / `property_type:`. Re-derive the REQ link from the test name + the spec.md REQs (each REQ in spec.md has a `source:` line and a semantic anchor; the test name typically encodes the same anchor). When in doubt, attribute the test to the union top-level `based_on:` in `done_when.yaml`.
- If under `example_based:` → emit a direct WHEN-THEN test from the matching EARS REQ(s) in `spec.md`. Keep deterministic; no random data unless the REQ explicitly says "any input".
- If under `property_based:` → infer `property_type` from the test name suffix (see iron rule 3) and emit the matching pattern from `references/pbt-property-types.md`. Use Hypothesis (Python) / fast-check (TS) / jqwik (Kotlin). Skip for Swift unless the project already uses SwiftCheck.

Test file header:

```python
# Generated by test-suite-generator/<skill-version>
# Source spec: <relative path to spec.md>
# based_on: <comma-separated REQ IDs covered in this file>
```

**Version-string substitution rule.** Every "Generated by …" header (in every file you emit — `existence.sh`, unit/integration/e2e tests, `mutation.sh`, `stryker.conf.json`, `playwright.config.ts`, the top-level test README) MUST substitute `<skill-version>` with the version value read from this `SKILL.md`'s YAML frontmatter at the time of generation. **Do NOT hardcode** a version literal (e.g. `0.1.0`, `0.2.0`) — that decouples the artifact's self-report from the actual skill version and creates the dogfooding bug of "skill claims 0.3.x but produces files self-reporting 0.2.0". Read the frontmatter `version:` value once at S0/Bootstrap and use it consistently in every emitted header.

**Batch boundary:** generate the unit-test file(s), write to disk, run them (they will mostly fail — code does not exist yet — that is fine). Move on.

---

## 4-C — Integration tests

Read `references/sub-modules/integration-generator.md`.

For each test name in `behavior.integration_tests`:

- Under v1, integration entries are bare strings — there is no `dependencies:` sub-field. Infer required containers from the test name + spec.md (e.g. `_api_returns_200_` → http server + DB; `_triggers_confirmation_email_` → SMTP mock container). When ambiguous, look up the EARS REQ in spec.md and ask the user once for the dependency list.
- Use testcontainers for the inferred dependencies. Postgres / Redis / Kafka / SMTP-mock — all have container images.
- `example_based:` → end-to-end user-story tests, hitting real services.
- `property_based:` → cross-module invariants (state-machine PBT, atomicity properties). Use fast-check's `model` testing in TS or Hypothesis's `RuleBasedStateMachine` in Python.

Do not use HTTP mocks (`nock`, `responses`, `unittest.mock`). Use actual containers. If a service is genuinely external and uncontainerizable (Stripe production API), use the vendor's official sandbox endpoint, not a hand-rolled mock.

---

## 4-D — E2E tests

Read `references/sub-modules/e2e-generator.md`.

For each test name in `behavior.e2e_tests`:

- Under v1, e2e entries are bare strings — there is no `tool:` sub-field. Pick the e2e tool from the project's existing convention (look for `playwright.config.*`, `cypress.config.*`, `*.maestro.yaml`, an `appium`/`detox` import in package.json, etc.). If the project has none, default to Playwright (web) or Maestro (mobile); tell the user which you picked.
- Use `data-test=` selectors only (or `data-testid=`, whatever the project convention is). Do not select by text or CSS class — both are brittle.
- Keep the test short (5-15 actions). E2E is slow; cover the *one* journey, not its variants. Variant coverage belongs at the integration layer.

If `e2e_tests:` lists more than ~5 entries, push back: tell the user "this many E2E tests will be slow and flaky — consider moving some to integration." Then proceed if they insist.

### Test names MUST be verbatim from `done_when.yaml` (no paraphrasing)

**Hard rule** — the string passed to the test framework's identifier argument must equal the YAML entry **character-for-character**, including the `test_` prefix, all underscores, and any trailing archetype suffix.

This applies to every test layer (existence script labels, unit `def test_*`, integration `def test_*`, e2e `test('…', …)`). The reason: downstream consumers (`/ratchet`, Step 5 evaluators, audit scripts) `grep` the contract names against produced files; any paraphrase breaks contract ↔ implementation traceability.

| Layer | Framework | The verbatim slot |
|---|---|---|
| Unit (Python) | pytest | the `def test_<name>():` function name |
| Unit (TS) | vitest / jest | the first argument of `test('<name>', …)` |
| Integration | pytest / vitest | same as unit |
| E2E | Playwright / Cypress | the first argument of `test('<name>', …)` / `it('<name>', …)` |

Python's `def test_xxx` is naturally verbatim because the YAML uses the same `snake_case` identifier form; just paste it. TS/JS frameworks accept arbitrary strings — that flexibility is the trap. Do NOT "humanize" the YAML name into a sentence-cased English title.

**Correct (Playwright):**

```ts
// YAML entry: test_mentioned_member_sees_in_app_banner_in_active_channel
test('test_mentioned_member_sees_in_app_banner_in_active_channel', async ({ page }) => {
  // human-readable explanation lives in the comment, NOT in the test() title
  // — verifies: a mentioned member sees an in-app banner in the active channel.
  ...
});
```

**Forbidden** (this is the exact mistake to avoid):

```ts
// YAML entry: test_mentioned_member_sees_in_app_banner_in_active_channel
// WRONG: paraphrased to a sentence, dropped `test_` prefix and underscores.
test('mentioned member sees in-app banner in active channel', ...)

// WRONG: rewrote `_no_banner_no_sound` as `— no banner, no sound`.
test('member in DND sees only badge increment — no banner, no sound', ...)
```

If a human-readable description is desirable, put it in:

- A `describe(...)` block name (Playwright/vitest), OR
- A leading comment inside the test body, OR
- A Playwright tag/annotation (`test.info().annotations.push(...)`)

— but never in the `test()` first argument.

---

## 4-E — Mutation testing

Read `references/sub-modules/mutation-config.md`.

Emit:

- A config file matched to the language: `setup.cfg` / `pyproject.toml` block for mutmut; `stryker.conf.json` for Stryker (TS); `pom.xml` plugin block for PIT (Java).
- A `mutation.sh` (or equivalent npm script) that runs the mutation tool and asserts kill rate ≥ the threshold from `done_when.yaml`.
- A short README section pointing at this script and explaining the purpose ("if you bypass this, you re-open the reward-hacking hole the done_when pipeline closes").

The script must exit nonzero on kill-rate under threshold; this is the signal `ratchet` needs to decide "not done".

Do NOT run the mutation suite right now — it takes minutes-to-hours. Just emit and document.

---

## 4-F — Removed in v1.0.0

The former 4-F "Fitness rubric" sub-step is retired. See HTML v2 §3.5 (fitness-check dissolution) and the v1.0.0 frontmatter note for the reasoning. If you encounter a legacy `done_when.yaml` with a `fitness:` block, **bail out at sub-step 0** and tell the user to regenerate via `/acceptance-spec` v1.0+, which no longer emits `fitness:`.

Re-routing reference (for users migrating from v0.x contracts):

| Legacy fitness entry | New home |
|---|---|
| "README quickstart works zero-modification" | `/qa-reviewer` actually runs it (programmatic) |
| "Agent can call API from docs only" | `/qa-reviewer` e2e against a fresh-session caller (programmatic) |
| "API documentation complete" | `/code-reviewer` greps every export vs docs (static) |
| "Type signatures correct" | `/qa-reviewer` runs `tsc`/`mypy` (programmatic) |
| "Code satisfies spec intent" | `/pm-reviewer` Agent-as-Judge (already covers) |
| "Naming is idiomatic" | `/code-reviewer --focus=style` (already covers) |
| **"Documentation clarity"** | **`/pm-reviewer` → `requires_human_verification`** (genuinely needs human) |
| **"Tutorial flow"** | **`/pm-reviewer` → `requires_human_verification`** (genuinely needs human) |

---

## After all five sub-steps

Tell the user, in short bullets:

1. Output directory + the file tree (≤15 lines).
2. Counts: `<N> existence checks · <M> unit tests (<E> example / <P> PBT) · <I> integration tests · <K> e2e tests`.
3. Three runnable commands (existence, unit, mutation) the user can invoke immediately.
4. Step 5-6 next step: the user **manually translates** the upstream `done_when.yaml` (not the test files themselves) into a `/ratchet` invocation — Goal / Criteria / Scope / `done_when` block. Ratchet is the Step 5-6 master controller; it does **not** auto-parse `done_when.yaml`. Point them at `done-when-pipeline/INTEGRATION.md` for the verbatim translation recipe and the `spec_drift_threshold` ↔ `convergence` mapping.

### Counts must be verbatim from `done_when.yaml` (hard rule)

When emitting the counts line above AND when populating the same counts in the generated `tests/<feature>/README.md`'s "Counts" section, every number MUST be derived by **counting entries in the input `done_when.yaml`**, not by counting tests in the generated files or by inferring "we probably emitted 16 because there were 10 examples and 4 PBTs and we threw in some extras". Specifically:

- `<N>` existence checks = `len(done_when.yaml.existence)` — count entries verbatim.
- `<M>` unit tests = `len(behavior.unit_tests.example_based) + len(behavior.unit_tests.property_based)`; `<E>` = `len(.example_based)`; `<P>` = `len(.property_based)`. The relationship `M = E + P` is mathematical, not narrative — do NOT add helper or synthesized tests into the count.
- `<I>` integration tests = `len(integration_tests.example_based) + len(integration_tests.property_based)`.
- `<K>` e2e tests = `len(e2e_tests)`.

If your prose explanation diverges from those mathematical counts (e.g. "16 unit tests but actually the YAML lists 14"), the prose is wrong — re-count. **Never emit two contradicting numbers in the same artifact** (e.g. "16 unit tests" in the headline and "14 unit entries" in the footnote — exactly the iter-2 step2 P2-4 bug). If the test files end up containing more or fewer tests than the YAML promised, that is itself a skill bug that must be surfaced upstream (push back per iron rule 7 "No inventing requirements" / iron rule 9 "Verbatim test names") — not papered over by inflating the count in the README.

Do not implement the feature. Do not run the integration / e2e suites unless the user explicitly asks ("run integration"). Mutation is too slow to run by default.

---

## Step 5-6 hand-off — what the test suite feeds into

The test files this skill emits become the **acceptance contract** that Step 5 (execution) and Step 6 (closed-loop iteration) judge against. Two key handoff facts the user needs to know:

1. **Manual translation, not auto-parse.** Ratchet's Step 1-3 reads a NL goal + criteria + scope + a `done_when` block; it does NOT open `done_when.yaml` directly. The user copies values from `done_when.yaml` (thresholds, test commands, `spec_drift_threshold.max_fix_loops_before_escalation`) into ratchet's invocation form. See `done-when-pipeline/INTEGRATION.md` "Handoff: test-suite-generator → ratchet (manual)" for the verbatim recipe.

2. **Continuous PBT failure ≈ spec bug (design doc §12.1.IV).** If the implementer's `/ratchet` loop keeps failing the same PBT after multiple fix attempts, that is a signal the **spec** is wrong, not the code. The recommended response is **not** more code patches; it is to return to `/acceptance-spec` and narrow the REQ. Concretely: if the PBT's shrunk counterexample is *consistent with the literal text of the REQ that produced the test* (the REQ as written would also produce a misbehaving impl), the spec is wrong. If the counterexample contradicts the REQ's text, the code is wrong — stay in ratchet with more budget. There is no automated escalation in v0.1 — the user judges which side is broken after ratchet's `convergence` triggers stop. See `INTEGRATION.md` "Spec drift guidance" for the full decision.

---

## When to push back instead of generating

- **The spec has REQs with no testable claim** (e.g. "the system SHALL be intuitive") → tell the user "REQ-NNN is not testable as written; this is a `[?]` that should have been resolved upstream. Suggest re-running /acceptance-spec for that REQ." Pre-v1.0 the lazy way out was a fitness rubric — in v1.0+ this is rerouted to `/pm-reviewer`'s `requires_human_verification` verdict, but only after honest effort to make the REQ verifiable.
- **`done_when.yaml` lists a `property_type:` you cannot map to a pattern** → tell the user which entry, and ask whether to (a) reclassify as example-based, (b) drop it, (c) split the REQ to expose a different property. Do not invent a PBT pattern you don't actually know.
- **The target language has no PBT library** (Swift, mostly) → emit only example tests, document the gap in a README note. Do not try to fake a Hypothesis-style API in Swift.
- **Legacy contract has `fitness:` block** → bail out at sub-step 0 with a clear migration message: "this contract was generated under v0.x schema; v1.0+ has retired `fitness:` per HTML v2 §3.5. Regenerate via `/acceptance-spec` v1.0+."

---

## Resource index

- `references/ears-to-test-matrix.md` — which EARS type generates which test kinds, with PBT strength rating
- `references/pbt-property-types.md` — six property archetypes (invariant / idempotent / reversible / boundary / monotonic / state_machine) with generator snippets per language; also documents alphabet-narrowing requirements
- `references/tooling-by-language.md` — concrete install + import per language (Python / TS / Swift / Kotlin / Java)
- `references/anti-cheating-mutation.md` — why mutation testing is mandatory + how to read kill-rate output
- `references/done-when-schema-validator.md` — checklist for sanity-checking the input contract (v1.0+ schema: `existence + behavior + rules` only)
- `references/step-5-audit-checklist.md` — checklist for Step 5 reviewers auditing artifacts emitted by this skill
- `references/sub-modules/` — one file per sub-step (existence / unit / integration / e2e / mutation) with full output recipes
- `references/examples/` — generated test trees for the subscription-cancellation worked example
