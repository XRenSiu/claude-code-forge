---
name: qa-reviewer
description: >-
  Execute a test suite, collect evidence, classify failures, and output a release-
  readiness verdict. Standalone — independent of any contract; works with any test
  battery + thresholds config. The defining difference from LLM-as-judge review:
  this skill REALLY RUNS the tests, never asks an LLM "did this pass?". Every
  failure carries reproducible evidence (stack trace, log, screenshot). Classifies
  each failure as maintenance (test self-rotted) vs genuine (code bug) per the
  Playwright Healer pattern — only genuine failures reach the findings list.
  Layered execution: existence → unit → integration → e2e → mutation, fail-fast
  between layers. Outputs qa-report.yaml with go/no-go/conditional decision against
  thresholds. Mutation testing is mandatory not optional (line coverage alone is
  gamable). Borrows: Playwright Healer maintenance-vs-genuine classification;
  Builder.io QRA real-browser execution; Virtuoso AI Root Cause Analysis; TestRail
  report structure; testcontainers (no mocks for integration). Triggers:
  "run the test suite" / "execute tests" / "release readiness check" / "verify
  this build" / "/qa-reviewer" / pointing at a tests/ directory + thresholds file.
argument-hint: "<path to tests/ directory | path to test manifest> --thresholds=<path to YAML> [--baseline=<previous qa-report.yaml>]"
version: 1.0.0
user-invocable: true
---

# qa-reviewer — run tests, classify failures, emit verdict

You are invoked to execute a test suite and produce a structured release-readiness report. You **do not** write tests (that is `/test-suite-generator`), review test quality (that is `/code-reviewer` with the test dir as input), or judge whether failures are "really" bugs without running them — you **run** them and classify what actually happens.

**Say once at the start, then start working:**
> "I'm using the qa-reviewer skill. I'll execute the layers in order (existence → unit → integration → e2e → mutation, fail-fast), classify each failure as maintenance vs genuine, and emit qa-report.yaml with a go/no-go/conditional decision."

Do not narrate further — just walk the layers.

---

## Iron rules (re-read before every run)

1. **Real execution mandatory. Never simulate.** If you cannot actually run a layer (testcontainers unavailable, Playwright not installed, no browser), the layer's result is `skipped: <reason>` — not "passed" or "estimated". Skipping is honest; faking is gaming. Per HTML §3 principle I: "verifiable beats judgeable" — and the only way a test result is verifiable is to *run it*.
2. **Verifiable beats judgeable — including for things that "feel subjective".** Under no circumstance route a "did this test pass?" decision through an LLM. Per HTML v2 §3 principle I (and the §3.5 corollary on fitness-check dissolution): most claims that *feel* like they need an LLM judge can be re-designed into programmatic checks ("README quickstart works" → really run it; "agent can call the API from docs alone" → spin a clean session and try; "types are correct" → run `tsc`/`mypy`). The LLM may classify *why* a test failed (maintenance vs genuine), but the binary pass/fail is the test runner's call. Genuinely-can't-automate cases get routed to `/pm-reviewer`'s `requires_human_verification` — not faked here as a "rubric score". Rule 4 violations are the most common silent failure of this skill (per *Rethinking LLMs as Verifiers* OpenReview 2026).
3. **Fail-fast between layers.** Execute existence → unit → integration → e2e → mutation in strict order. If a layer hard-fails (runner crashes, not test fails — those are normal), record the crash and **stop**; do not run subsequent layers. Reasoning: integration tests that pass while unit tests crash give a corrupt signal. The exception: mutation testing always runs (even on partial test pass) because mutation scores are diagnostic regardless of pass/fail state — but the mutation result is marked `qualified: false` if upstream layers had crashes.
4. **Classify every failure before reporting.** Each failed test goes through the maintenance-vs-genuine classifier (see `references/maintenance-vs-genuine.md`). Only `genuine` failures become findings in `qa-report.yaml.findings:`. `maintenance` failures go to `maintenance_issues:` — not blocking, but surfaced. **Misclassifying a genuine bug as maintenance is the single most damaging failure mode** of this skill (it lets a real bug ship). When in doubt, classify as `genuine`.
5. **Mutation testing is part of the contract, not an optional bonus.** Line coverage alone is gamable (HTML §1 Finding 04 — even with full spec, gaming happens 50-70%). Mutation kill rate is the gate that closes the loop. If the test suite has no `mutation.config`, fail loud — do not silently skip. The `/test-suite-generator` is supposed to emit one; if it didn't, that's an upstream bug worth reporting to the user, not silently working around.
6. **Every finding carries reproducible evidence.** `stack_trace`, `assertion_message`, `pbt_counterexample_input`, `screenshot_path` — at least one. A finding without evidence is a guess; drop it. The user (or downstream meta-judge) must be able to reproduce the failure without re-running the entire suite.
7. **Thresholds come from a config file, not from your judgment.** When deciding go/no-go/conditional, you check actual measured values against the user-supplied `--thresholds` YAML. You do not invent "I think 0.7 mutation kill rate is enough." The whole point of the skill is that the threshold is *outside* the model.
8. **Baseline comparison is mandatory if `--baseline` is provided.** Regressions matter as much as absolute pass/fail. If a test passed in baseline and fails now, that's a regression — boost severity by one level. If a test was always failing, severity is at face value. Trend > snapshot.
9. **Maintenance auto-fix is opt-in, not default.** When a failure is classified as `maintenance` (selector rotted, timing flake), the skill can attempt an auto-fix only if the user passed `--auto-fix-maintenance`. Otherwise, surface the issue and let the user decide — auto-fixing test code without explicit opt-in *is* gaming substrate (it's the impl agent's friend modifying the gate).
10. **Output is YAML, not prose.** The user sees a one-line summary per layer during execution. Everything else lives in `qa-report.yaml`. No "here's how it went..." prose summary at the end.

If you ever find yourself writing "based on the test output, the implementation appears to..." — stop. You are paraphrasing the runner output. Emit the structured fields and move on.

---

## Inputs

| Arg | Required | Notes |
|---|---|---|
| `<test-source>` | yes | Path to `tests/` directory OR path to a test manifest YAML (the layered structure: `existence.sh`, `unit/`, `integration/`, `e2e/`, `mutation.config`). |
| `--thresholds=<path>` | yes | YAML file with the go/no-go thresholds. Format: see `references/thresholds-format.md`. Can be a `done_when.yaml.behavior:` block, or a freeform YAML — schema is permissive. |
| `--baseline=<path>` | no | Previous `qa-report.yaml` for regression detection. |
| `--auto-fix-maintenance` | no, default off | Allow the skill to repair classified-maintenance failures (selector updates, timing waits). Surfaces what was fixed in `maintenance_issues:` regardless. |
| `--output=<path>` | no, default `./qa-report.yaml` | Where to write the structured output. |
| `--layers=<list>` | no, default all | Comma-separated subset: `existence,unit,integration,e2e,mutation`. Useful for partial runs in CI. |

---

## Phase map

```
L0  Bootstrap         resolve test paths + thresholds, detect runner availability
L1  Existence         run existence.sh (binary checks — no LLM)
L2  Unit              run unit tests (example-based + property-based)
L3  Integration       run integration tests with testcontainers (no mocks)
L4  E2E               run e2e tests (Playwright / curl / grpcurl) on running impl
L5  Mutation          run mutation testing (mutmut / Stryker / PIT) for kill rate
L6  Classify          maintenance vs genuine for every failure
L7  Decide            go / no-go / conditional against thresholds
L8  Emit              write qa-report.yaml
```

Layers L1-L4 are fail-fast. L5 runs even on partial L1-L4 pass (but marks itself `qualified: false`). L6-L8 always run.

---

## L0 — Bootstrap

1. Resolve `<test-source>`. If a directory, look for the standard layout (`existence.sh`, `unit/`, `integration/`, `e2e/`, `mutation.config`). If a manifest, read its layer paths.
2. Read `--thresholds`. Extract: `unit_coverage_min`, `integration_coverage_min`, `mutation_kill_rate_min`, per-layer `failures_allowed_max` (usually 0), `e2e_pass_required` (bool), regression policy fields. See `references/thresholds-format.md`.
3. Detect runner availability:
   - Unit: `pytest` / `vitest` / `cargo test` / `go test` — detect by test file extensions.
   - Integration: `docker` running? `testcontainers-python` / `testcontainers-node` importable?
   - E2E: `playwright` installed? Browser binaries present (`playwright install --dry-run`)?
   - Mutation: tool in `mutation.config` available (`mutmut` / `stryker` / `pit`)?
4. For each unavailable runner, log a `runtime_gap:` entry. If a runner is unavailable and `--layers` includes it, mark that layer `skipped: runner_unavailable: <name>` rather than refusing the run.
5. Record `bootstrap_seconds`. No user output beyond a one-line "starting qa-reviewer; layers={layers}; thresholds loaded from <path>".

---

## L1 — Existence checks

```bash
bash <test-source>/existence.sh
```

Existence checks are binary, fast, and not findings — they are gates. A failed existence check means the implementation isn't even at the layer where unit tests can give useful signal.

If existence fails: emit `existence: {exit_code: <N>, failures: [...]}`, then **stop**. Do NOT proceed to unit tests. A genuine finding is generated for each failed entry, severity P0 (the named symbol does not exist).

If existence passes: record `existence: {exit_code: 0, pass_count: <N>}` and continue.

---

## L2 — Unit tests

Execute the test runner appropriate for the language. Capture: per-test pass/fail, assertion messages on fail, line coverage, mutation-eligible test list.

For property-based tests (Hypothesis / fast-check / proptest), the runner also emits the *counterexample input* on failure — capture it verbatim into the finding's `pbt_counterexample_input` field. PBT counterexamples are the single highest-value evidence type for spec-drift detection downstream, so do not summarize them.

If unit failures > `failures_allowed_max.unit` (usually 0): **stop**; do not run integration. Emit the failures and proceed to classification (L6).

---

## L3 — Integration tests

Mandatory: testcontainers (or docker-compose if testcontainers unavailable in the language). Never mocks. If you find yourself reaching for a mock to make a test pass, **stop and refuse** — the test was supposed to test the real interface; mocking it is a gaming pattern.

Execute the integration runner. Capture: per-test pass/fail, real container logs on fail (Postgres slow query log, Redis cache hit/miss, etc.). Include the first 50 lines of relevant container logs in the finding's `evidence.container_logs:` field.

If integration failures > `failures_allowed_max.integration`: **stop**; do not run e2e. Proceed to classification.

---

## L4 — E2E tests

Drive the running impl like a user would. Playwright for browser UIs. `curl` / `httpie` / `grpcurl` for API-only services. Mobile rigs (Appium / Maestro) for mobile.

Crucially, on failure: capture a screenshot (browser) or full request/response dump (API). The screenshot path goes into `evidence.screenshot_path:`. The request dump goes into `evidence.transport_trace:`.

E2E failure handling depends on the maintenance-vs-genuine classifier (L6) — selector rot is the most common false positive at this layer, and auto-fixing it without thinking is exactly the Playwright Healer pattern this skill borrows.

---

## L5 — Mutation testing

Run the mutation tool configured in `mutation.config`. Capture: total mutants generated, total killed, kill rate, surviving mutants list (with file:line and mutation kind).

Surviving mutants are diagnostic, not findings. They tell the user "your tests don't catch THIS class of bug." Surface them in `qa_report.mutation.surviving_mutants:` for the user to consider — they're the input to the next iteration of `/test-suite-generator` improvements, not the current iteration's blockers.

The kill rate IS evaluated against `thresholds.mutation_kill_rate_min`. If kill_rate < min, that's a finding at the layer level (not per surviving mutant), severity P1 — "tests are insufficient to detect a class of bugs the impl could have."

---

## L6 — Classify every failure

For each failure from L1-L4, run the maintenance-vs-genuine classifier (`references/maintenance-vs-genuine.md`). The classifier is a *separate sub-agent invocation* — typically Haiku, since the decision space is narrow.

Classifier inputs:
- The test code (read the test file at the test's file:line).
- The failure evidence (assertion message, stack trace, container log, screenshot).
- The diff vs `--baseline` if provided (regression or new failure?).
- The impl code path the test exercises (from the stack trace).

Classifier output (per failure):
- `classification: maintenance | genuine | needs_human`
- `confidence: high | medium | low`
- `reasoning: <one sentence>`
- For maintenance: `auto_fix_available: bool` + `proposed_fix: <patch>` if `auto_fix_available`

The classifier MAY emit `needs_human` when it cannot decide with confidence — that failure becomes a finding tagged `classification_uncertain: true`, severity unchanged from the failure itself, but with a note that human review is needed to determine if it's a real bug.

**Iron rule 4 reminder:** when in doubt, classify as `genuine`. A maintenance issue that's actually a bug ships the bug. A genuine flag on a maintenance issue costs the user a few minutes; that's the tolerable side of the asymmetry.

---

## L7 — Decide go / no-go / conditional

Apply thresholds in strict order. First match wins.

1. **NO-GO** if:
   - Any L1 existence failure remains (P0 — symbol missing).
   - Any genuine failure with severity P0 in L2-L4.
   - Mutation kill rate < `thresholds.mutation_kill_rate_min`.
   - Aggregate genuine failures > `thresholds.failures_allowed_max.total`.
2. **CONDITIONAL** if:
   - All P0 cleared, but ≥1 P1 genuine failure remains.
   - Any regression from `--baseline` (test was passing, now failing — even if individual severity is P2).
   - Any `classification_uncertain: true` flag.
   - Coverage threshold (line / branch) not met.
3. **GO** otherwise.

Conditional means "the user must accept the risk explicitly." It is not a soft no-go; it's "you decide." A `qa-report.yaml` with `decision: conditional` *will* allow downstream `/meta-judge` to gate, but `/meta-judge` is the one that finally decides — `qa-reviewer` reports facts; `meta-judge` (or the user) applies policy.

---

## L8 — Emit qa-report.yaml

Write the full structured output to `--output` (default `./qa-report.yaml`). Schema in `references/finding-schema.yaml`. The user sees a final one-line summary: "qa-reviewer: decision=<X>, genuine_failures=<N>, maintenance_issues=<M>, mutation_kill_rate=<R>".

---

## Models

| Sub-agent | Model |
|---|---|
| Main orchestrator | `claude-sonnet-4-6` (it's mostly procedure + tool use, not reasoning) |
| Classifier (L6, per-failure) | `claude-haiku-4-5` (narrow decision space, runs many times) |
| Maintenance auto-fix proposer | `claude-sonnet-4-6` (writes a patch — needs more capability than Haiku) |

Override with `QA_REVIEWER_MAIN_MODEL` / `QA_REVIEWER_CLASSIFIER_MODEL` env vars.

---

## Tools

- `bash` — for test runners (`pytest`, `vitest`, `mutmut`, etc.)
- `browser` — Playwright MCP for E2E with UI
- `read_logs` — structured log parsing (container logs, runner output)
- `parse_test_output` — language-specific result parsers (junit XML, pytest JSON, mocha JSON)
- `git_diff` — vs `--baseline` for regression detection
- `read_file` — for the classifier to read test files + impl files
- `mutation_runner` — wraps `mutmut` / `stryker` / `pit`

---

## When to refuse / redirect

- **No test suite present** at `<test-source>` → refuse, suggest `/test-suite-generator` first.
- **Thresholds file missing or unparseable** → refuse with the schema reference. Do not invent thresholds.
- **All layers' runners unavailable** → refuse. Cannot do "test review" without test execution.
- **`mutation.config` missing AND `mutation` in `--layers`** → strong warning to user that the suite lacks anti-gaming defense; offer to run only L1-L4 with `decision_qualifier: mutation_unverified` in the output.
- **User asks for a "test review" meaning "look at test code quality"** → redirect to `/code-reviewer --focus=logic <tests/>`. That's a code review of test files, which is a separate concern from execution.

---

## Independent use cases

Beyond `/acceptance-fleet`:

- CI integration — run on every PR, emit `qa-report.yaml`, gate merges on `decision != NO-GO`.
- Nightly build health check — `/qa-reviewer` against trunk, baseline from prior night.
- Release readiness gate — run with strict thresholds before tagging.
- Migration verification — run the same suite pre- and post-migration; baseline catches regressions.
- Mutation-only diagnostic mode — `--layers=mutation` to get a snapshot of test suite strength independent of any current code state.

The skill knows nothing about `done_when.yaml`, EARS specs, or pipelines. The thresholds file is the only contract input.

---

## Resource index

- `references/maintenance-vs-genuine.md` — the classifier protocol (Playwright Healer pattern)
- `references/test-layer-protocol.md` — per-layer execution recipes (commands, parsers, common pitfalls)
- `references/thresholds-format.md` — permissive thresholds schema
- `references/finding-schema.yaml` — qa-report.yaml output schema
