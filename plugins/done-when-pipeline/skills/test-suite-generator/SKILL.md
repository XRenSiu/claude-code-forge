---
name: test-suite-generator
description: >-
  Turn an EARS spec + done_when.yaml contract into the full test pyramid: existence
  checks (ripgrep/tree-sitter), unit tests (example-based + property-based), integration
  tests (with testcontainers, no mocks), e2e (Playwright/Cypress/Appium/Maestro),
  mutation-testing configuration as an anti-reward-hacking layer (mutmut/Stryker/PIT),
  and a fitness-rubric file for the "Claude-with-rubric inline" manual workflow. Walks six sub-steps
  (4-A existence / 4-B unit / 4-C integration / 4-D e2e / 4-E mutation / 4-F fitness)
  ONE BATCH AT A TIME — a known failure mode is "generate all tests at once → quality
  collapse"; this skill explicitly serializes the batches. Each generated test is
  tagged with `based_on: [REQ-IDs]` so the trace from requirement → test is mechanical.
  Triggers: "generate tests for spec X" / "derive test suite" / "build verification battery"
  / "/test-suite-generator" / pointing at any specs/<feature>/ directory.
argument-hint: "<path to specs/<feature>/ or path to done_when.yaml>"
version: 0.1.0
user-invocable: true
---

# test-suite-generator — EARS spec → full test pyramid

You are invoked to turn an upstream acceptance-spec output (a `specs/<feature>/` directory containing `spec.md` and `done_when.yaml`) into the actual test files that an independent agent can execute to verify implementation.

**Say once at the start, then start working:**
> "I'm using the test-suite-generator skill. I'll walk six sub-steps (existence → unit → integration → e2e → mutation → fitness), one batch at a time. Each generated test traces back to a REQ-ID via `based_on:`."

Do not narrate further — just walk the sub-steps.

---

## Iron rules (re-read before every sub-step)

1. **Verifiable beats judgeable.** Programmatic checks (assertion-based tests, AST inspection, mutation kill rate) beat LLM-as-judge on speed, cost, consistency. Reach for the fitness rubric (4-F) **only** when there is no programmatic alternative.
2. **One batch at a time.** Generate → write to disk → run → iterate. Then proceed. **Never generate all six batches in one pass** — empirically, LLM test generation quality collapses past a few dozen tests in a single prompt. The doc that motivates this skill names this as Pitfall #2; do not be the next person to step on it.
3. **PBT must declare its property type.** Every property-based test in `done_when.yaml` has a `property_type:` field (one of: invariant / idempotent / reversible / boundary / monotonic / state_machine). Read `references/pbt-property-types.md` to know which pattern to emit. If you cannot identify the property type, **the requirement is not a good PBT candidate** — emit an example-based test instead and explain why.
4. **No mocks for integration tests.** Use testcontainers (or equivalent) to spin up real Postgres / Redis / Kafka / etc. Mocks hide interface drift, which is exactly the failure mode that catches AI-generated code most often. If the language lacks testcontainers, fall back to docker-compose; do not fall back to mocks.
5. **Mutation testing is mandatory, not optional.** A done_when that only enforces coverage ≥ 80% will incentivize the implementer to write `assert True` to inflate the number. Mutation kill rate ≥ 70% is the gate that closes that loop. Always emit a `mutation.config` file (4-E).
6. **Every generated test carries `based_on:`.** Either as a comment header in the test file (`# based_on: REQ-001, REQ-003`), or as part of the test name when the language convention favors it. Tests without traceability cannot be culled when a REQ is dropped, and cannot be explained when they fail.
7. **No inventing requirements.** If a property occurs to you that isn't in any REQ, **do not** add a test for it. Either push back upstream ("REQ-NNN seems to imply X — should that be a separate REQ?") or skip it. Tests must derive from the spec, not from your own intuition about what a good system does.
8. **Pyramid ratio rebalanced for AI-coding.** Per the source doc, AI-written code is more likely to fail at module boundaries (interface mismatches, protocol confusions). Target ~50% unit / ~35% integration / ~15% e2e — not the traditional 70/20/10. Push slightly more weight into integration than you might be used to.

---

## Sub-step map

```
0     Bootstrap         read specs/<feature>/, validate done_when.yaml shape, detect target language
4-A   Existence         grep/AST script that proves each listed noun exists in code
4-B   Unit              one function/class at a time; example + property tests
4-C   Integration       multi-module; uses testcontainers; example + cross-module PBT
4-D   E2E               Playwright/Cypress/Appium/Maestro; few but real user journeys
4-E   Mutation          mutmut/Stryker/PIT config + invocation script
4-F   Fitness rubric    rubric file consumed manually by a fresh Claude session (no packaged auto-runner)
```

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
- `function:` → `rg -q "<name>" src/ || (ts-morph / python -c "import ast" — language-specific)`
- `route:` → grep for the route declaration in router files
- `db_field:` → grep migration/schema files for `<table>.<column>`
- `frontend_component:` → grep for the component name in `src/components/`
- `env_var:` → grep `.env.example` / `README` / `config/` for the var name
- `cli_command:` → invoke `<cli> --help` and grep for the subcommand

Each check echoes `✓ <kind>: <thing>` or fails (`set -euo pipefail` at the top). The script returns nonzero on first failure. This is the fast-fail gate.

Append at the end: `echo "✓ All <N> existence checks passed"`.

Run it. If it fails (which is expected on first run — the implementer hasn't written the code yet), that's fine — the script becomes part of the contract, not a current-pass requirement. Document this in a header comment.

---

## 4-B — Unit tests

Read `references/sub-modules/unit-test-generator.md`.

For each test name in `done_when.yaml` `behavior.unit_tests`:

- If under `example_based:` → emit a direct WHEN-THEN test from the EARS REQ(s) in its `based_on:`. Keep deterministic; no random data unless the REQ explicitly says "any input".
- If under `property_based:` → look at `property_type:` and emit the matching pattern from `references/pbt-property-types.md`. Use Hypothesis (Python) / fast-check (TS) / jqwik (Kotlin). Skip for Swift unless the project already uses SwiftCheck.

Test file header:

```python
# Generated by test-suite-generator/0.1.0
# Source spec: <relative path to spec.md>
# based_on: <comma-separated REQ IDs covered in this file>
```

**Batch boundary:** generate the unit-test file(s), write to disk, run them (they will mostly fail — code does not exist yet — that is fine). Move on.

---

## 4-C — Integration tests

Read `references/sub-modules/integration-generator.md`.

For each test name in `behavior.integration_tests`:

- Use testcontainers for any `dependencies:` listed. Postgres / Redis / Kafka / SMTP-mock — all have container images.
- `example_based:` → end-to-end user-story tests, hitting real services.
- `property_based:` → cross-module invariants (state-machine PBT, atomicity properties). Use fast-check's `model` testing in TS or Hypothesis's `RuleBasedStateMachine` in Python.

Do not use HTTP mocks (`nock`, `responses`, `unittest.mock`). Use actual containers. If a service is genuinely external and uncontainerizable (Stripe production API), use the vendor's official sandbox endpoint, not a hand-rolled mock.

---

## 4-D — E2E tests

Read `references/sub-modules/e2e-generator.md`.

For each test name in `behavior.e2e_tests`:

- Use the tool the entry specifies (`tool: playwright` / `cypress` / `appium` / `maestro`).
- Use `data-test=` selectors only (or `data-testid=`, whatever the project convention is). Do not select by text or CSS class — both are brittle.
- Keep the test short (5-15 actions). E2E is slow; cover the *one* journey, not its variants. Variant coverage belongs at the integration layer.

If `e2e_tests:` lists more than ~5 entries, push back: tell the user "this many E2E tests will be slow and flaky — consider moving some to integration." Then proceed if they insist.

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

## 4-F — Fitness rubric

Read `references/sub-modules/fitness-rubric.md` AND `references/fitness-rubric-guide.md`.

For each entry in `done_when.yaml` `fitness:`:

- If `judge: programmatic` → emit a small script (`fitness_<criterion>.sh` or `.py`) that returns pass/fail. Example: "README quickstart runs zero-modification" → a script that copies README code blocks into a sandbox dir and runs them.
- If `judge: llm-rubric` → emit a `fitness/<criterion>.rubric.md` file with:
  - **Audience archetype** — 3-5 lines describing exactly who the judge should simulate, written inline (NOT a reference to any external persona library — the `persona-distill` ecosystem's personas are not applicable here)
  - **Inputs** — paths to artifacts the judge will examine (README, API reference, generated code)
  - **Rubric** — a structured rubric with 3-7 sub-dimensions, each scored 1-10 with concrete anchors, summing/averaging to a final score
  - **Threshold** — the `score_threshold:` from the YAML, restated
  - **How-to-run block** — explicit instruction that this is consumed *manually* by a fresh Claude session (no packaged auto-runner exists yet)
- If `judge: manual` → emit a `fitness/<criterion>.manual-checklist.md` with a clear pass/fail checklist. A human must run this.
- If `judge: persona-judge` → **reject the entry.** The `persona-judge` skill in `persona-distill` evaluates persona-skill quality, not arbitrary artifacts. Tell the user to rewrite as `judge: llm-rubric` (or push the criterion to programmatic if possible).

**Hard warning embedded in every llm-rubric file:** "A naively-written rubric *hurts* judge accuracy (research: JudgeBench, GPT-4o accuracy 55.6% → 42.9% with bad rubric). If you are tempted to write a generic 'rate this 1-10', stop and design concrete anchors first." See `references/fitness-rubric-guide.md` for the full caution.

---

## After all six sub-steps

Tell the user, in short bullets:

1. Output directory + the file tree (≤15 lines).
2. Counts: `<N> existence checks · <M> unit tests (<E> example / <P> PBT) · <I> integration tests · <K> e2e tests · <F> fitness criteria`.
3. Three runnable commands (existence, unit, mutation) the user can invoke immediately.
4. The next-step suggestion: hand the spec + tests to `/ratchet` as the implementation contract.

Do not implement the feature. Do not run the integration / e2e suites unless the user explicitly asks ("run integration"). Mutation is too slow to run by default.

---

## When to push back instead of generating

- **The spec has REQs with no testable claim** (e.g. "the system SHALL be intuitive") → tell the user "REQ-NNN is not testable as written; this is a `[?]` that should have been resolved upstream. Suggest re-running /acceptance-spec for that REQ." Do not paper over it with a fitness rubric — that's lazy.
- **`done_when.yaml` lists a `property_type:` you cannot map to a pattern** → tell the user which entry, and ask whether to (a) reclassify as example-based, (b) drop it, (c) split the REQ to expose a different property. Do not invent a PBT pattern you don't actually know.
- **The target language has no PBT library** (Swift, mostly) → emit only example tests, document the gap in a README note. Do not try to fake a Hypothesis-style API in Swift.
- **`done_when.yaml` `fitness:` has more than 3 entries** → tell the user "fitness rubrics are last-resort; you have N>3 here, several of these probably belong in `behavior:` as programmatic checks. Want me to suggest which?" If they keep all of them, proceed.

---

## Resource index

- `references/ears-to-test-matrix.md` — which EARS type generates which test kinds, with PBT strength rating
- `references/pbt-property-types.md` — six property archetypes (invariant / idempotent / reversible / boundary / monotonic / state_machine) with generator snippets per language
- `references/tooling-by-language.md` — concrete install + import per language (Python / TS / Swift / Kotlin / Java)
- `references/anti-cheating-mutation.md` — why mutation testing is mandatory + how to read kill-rate output
- `references/fitness-rubric-guide.md` — how to write a rubric that does not hurt judge accuracy
- `references/done-when-schema-validator.md` — checklist for sanity-checking the input contract
- `references/sub-modules/` — one file per sub-step (existence / unit / integration / e2e / mutation / fitness) with full output recipes
- `references/examples/` — generated test trees for the subscription-cancellation worked example
