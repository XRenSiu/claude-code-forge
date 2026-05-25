# test-layer-protocol.md — per-layer execution recipes

Each layer has a specific runner, parser, and common pitfall list. This document is the operational supplement to `SKILL.md` § "Phase map".

---

## L1 — Existence

### What it is

A `existence.sh` script (or equivalent for non-Unix runtimes) that verifies every entry in the spec's `existence:` block resolves to actual code. Outputs binary pass/fail per entry.

### Command

```bash
bash <tests>/existence.sh
```

The script's exit code is the gate: 0 = all pass, non-zero = at least one fail.

### Parser

For each line of output:
```
PASS: file:src/billing/cancel.ts
PASS: function:CancelSubscriptionUseCase at src/billing/cancel.ts:14
FAIL: route:POST /api/subscription/cancel — searched src/routes/, src/api/
```

Parse into a list of `{kind, target, status, matched_at | searched_globs}` records.

### Pitfalls

- `bash` not available on Windows — fall back to a parallel `existence.ps1` if present, else mark layer `skipped: shell_unavailable`.
- Some existence checks are slow (recursive AST grep over large monorepo) — record per-check timing; if a single check takes >10s, suggest the user narrow the search path.

---

## L2 — Unit tests

### Runners by language

| Language | Default runner | Coverage tool |
|---|---|---|
| Python | `pytest` | `pytest-cov` |
| TypeScript / JavaScript | `vitest` (preferred) or `jest` | built-in `--coverage` |
| Go | `go test` | `-cover` |
| Rust | `cargo test` | `cargo-tarpaulin` |
| Java | `mvn test` or `gradle test` | JaCoCo |
| Swift | `swift test` | `xcrun llvm-cov` |

Detect by file extensions in `<tests>/unit/`. If multiple languages, run each in parallel and aggregate.

### Property-based tests

Property-based tests live in the same `unit/` directory but require special handling on failure: the runner emits a *counterexample input* that must be captured verbatim.

| Framework | Counterexample capture |
|---|---|
| Hypothesis (Python) | parse "Falsifying example" line |
| fast-check (JS/TS) | parse `counterexample:` field in fast-check output |
| proptest (Rust) | parse `minimal failing input` |
| jqwik (Java) | parse "Falsified" with sample |
| QuickCheck (Haskell, Erlang, etc.) | parse "Failed:" with input |

Counterexample goes into `evidence.pbt_counterexample_input:` verbatim, no summarization. The counterexample is the most valuable single output of property-based testing for downstream spec-drift detection.

### Coverage

Capture line coverage (and branch coverage if the tool supports it). Both go into `qa_report.results.unit.line_coverage:` / `.branch_coverage:`.

If `--thresholds` specifies branch coverage but the tool doesn't support it → mark `branch_coverage: unsupported_by_runner`, do not block.

### Pitfalls

- Pytest's `--cov` defaults to "show in terminal" — pass `--cov-report=json:coverage.json` to get machine-readable output.
- Vitest randomizes test order by default — for reproducibility in CI, pass `--no-random`.
- Some Go projects use build tags (`// +build integration`) to separate unit / integration; respect the tag when invoking.
- PBT counterexamples can be huge structures — truncate the *raw output* in the finding to 1KB, but always retain the `counterexample_seed:` or `shrunk_example:` for reproduction.

---

## L3 — Integration tests

### Mandatory infrastructure

`testcontainers` (or `docker-compose`) brings up real dependencies: Postgres, Redis, Kafka, S3 (LocalStack), etc. **Mocks are forbidden** at this layer — mocks hide interface drift, which is the failure mode that catches AI-generated code most often.

| Language | testcontainers package |
|---|---|
| Python | `testcontainers` |
| Node.js | `testcontainers` (npm) |
| Go | `testcontainers-go` |
| Java | `testcontainers` (JVM canonical) |
| Rust | `testcontainers-rs` |

If testcontainers is not available in the language → check for `docker-compose.test.yml`; if present, use it. Otherwise mark layer `skipped: integration_infra_unavailable`.

### Container log capture

On failure, capture the first 50 lines of each relevant container's log:

```python
# pseudo
for container in failure_relevant_containers:
    log_excerpt = container.logs()[-50:]  # last 50 lines
    finding.evidence.container_logs[container.name] = log_excerpt
```

Postgres slow query log, Redis cache hit/miss patterns, Kafka broker errors — these are diagnostic gold.

### Pitfalls

- Containers can take 5-30s to start; do NOT impose unit-test-speed deadlines on integration.
- `localhost` inside a container ≠ `localhost` on the host — use the testcontainers-provided `get_container_host_ip()`.
- Some integration tests share state across cases — record `test_order_dependency: suspected` if you see this pattern; it makes regressions harder to localize.

---

## L4 — E2E tests

### Runners

| Target | Runner |
|---|---|
| Web UI | `playwright test` (preferred; cross-browser + headless built-in) |
| Web UI (legacy) | `cypress run` |
| API only | direct `curl` / `httpie` / `grpcurl` calls (no separate runner) |
| Mobile | `appium` or `maestro test` |
| Desktop | `playwright` (Electron) or platform-specific |

E2E presupposes the impl is *running*. The skill expects:
- A `dev_server` is already up (don't try to start one — that's an orchestration concern outside this skill's scope).
- The base URL / API endpoint is in the test config or env var.

If no running impl → mark layer `skipped: impl_not_running`.

### Screenshot capture

For browser E2E failures:

```javascript
// pseudo
test.afterEach(async ({ page }, testInfo) => {
  if (testInfo.status !== 'passed') {
    await page.screenshot({ path: `screenshots/${testInfo.title}.png`, fullPage: true });
  }
});
```

Path goes into `evidence.screenshot_path:`. Use absolute paths, not relative — the report consumer (meta-judge, user) might be in a different working directory.

### API E2E without a UI

For API-only services: capture full request / response (headers + body) into `evidence.transport_trace:`. Truncate body to 4KB if larger; full body to a side file.

### Pitfalls

- Playwright's default timeout is 30s per assertion — for slow ops (file upload, batch process), set per-test timeouts via `test.setTimeout()`.
- Mobile test runs are *slow*; budget 1-5 minutes per scenario.
- E2E flakes are mostly selector / timing; the maintenance-vs-genuine classifier (L6) handles this.

---

## L5 — Mutation testing

### Runners by language

| Language | Tool | Config file |
|---|---|---|
| Python | `mutmut` | `mutmut_config.py` or `setup.cfg [mutmut]` |
| TypeScript / JavaScript | `stryker` | `stryker.conf.mjs` |
| Java | `pitest` | `pom.xml` / `build.gradle` |
| Rust | `cargo-mutants` | `Cargo.toml [package.metadata.mutants]` |
| Go | `gremlins` | `gremlins.yaml` |

Mutation tools work by: (1) generating syntactic mutations of the source (e.g. `<=` → `<`, `+` → `-`, `if` → `if !`), (2) running the test suite per mutation, (3) counting how many mutations made tests fail ("killed") vs survived.

A high kill rate (≥0.7) means the test suite catches subtle bugs. A low kill rate means tests are weak — they pass the impl, but they would also pass a buggy version of the impl.

### Output

```yaml
mutation:
  tool: mutmut
  config: tests/<feature>/mutation.config
  mutants_generated: 62
  mutants_killed: 47
  kill_rate: 0.758
  surviving_mutants:
    - file: src/billing/cancel.ts
      line: 47
      mutation_kind: "boundary <= to <"
      what_was_mutated: "if (subscription.end_date <= now) ..."
      hint: "no test catches the boundary case end_date == now"
  qualified: true       # false if upstream layers had crashes
  duration_seconds: 421
```

### Pitfalls

- Mutation testing is *slow* — budget 5-60 minutes depending on impl + test count. Run last; do not block the dev loop on it; consider CI-only.
- Some mutations are equivalent (semantically identical to original) and will never be killed — those are false negatives in the survival list. Most mutation tools (`mutmut`, `stryker`) have heuristics to filter; trust them.
- A mutation tool crash counts as `qualified: false`; the kill rate is undefined until rerun.

---

## L6 — Classify (covered in `maintenance-vs-genuine.md`)

---

## Cross-layer concerns

### Parallelism

L1, L2, L3 can run in parallel if the runners are independent (different processes, no shared DB / port). L4 (E2E) usually wants to run last because it depends on a running impl that might be perturbed by L3 tests. L5 (mutation) runs last because it's the slowest.

Default order: L1 → L2 (parallel with L3 if possible) → L4 → L5.

### Caching

Test result caching (`pytest-cache`, vitest `--changed`) can speed up reruns but introduces "did the test actually run?" ambiguity. **Disable test caching in `/qa-reviewer`** unless `--cache-ok` is passed. The whole point of running this skill is to actually run the tests.

### Timing budget per layer (rough)

| Layer | Typical | Slow case |
|---|---|---|
| L1 existence | <5s | <30s |
| L2 unit | <30s | <5min |
| L3 integration | <5min | <30min |
| L4 e2e | <10min | <60min |
| L5 mutation | <30min | hours |

If a layer exceeds 3x typical, log a `slow_layer:` warning in the report. Slow tests are usually a sign of (a) missing parallelism, (b) hidden integration test in the unit layer, or (c) actually exercising a slow real path that should be unit-mocked.
