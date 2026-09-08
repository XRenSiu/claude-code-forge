# maintenance-vs-genuine.md — failure classification protocol

Borrowed from Playwright Healer Agent. Every test failure goes through this classifier before becoming a finding. The single most damaging failure mode of `qa-reviewer` is misclassifying a genuine bug as maintenance — when in doubt, classify `genuine`.

## The asymmetry

| Misclassification | Cost |
|---|---|
| Genuine flagged as maintenance | Real bug ships. Customer impact. Hard to detect downstream. |
| Maintenance flagged as genuine | User spends 2-5 minutes confirming. Annoying. Easy to detect. |

**The asymmetry is ~1000:1 in damage. Bias the classifier accordingly.**

## Three categories

| Category | What it means | What to do |
|---|---|---|
| `maintenance` | The test rotted (selector / fixture / timing). Impl is fine. | Surface in `maintenance_issues:`. Optionally auto-fix if `--auto-fix-maintenance`. Not a finding. |
| `genuine` | The impl is wrong (assertion captures real behavior; impl violates it). | Becomes a finding in `qa_report.findings:`. Severity from runner. |
| `needs_human` | Cannot decide with confidence. | Becomes a finding tagged `classification_uncertain: true`. Surface the specific question for human input. |

## Heuristics by failure type

### Selector / DOM-target failure (E2E, browser)

Symptoms: `TimeoutError: locator.click: Locator not found`, `Element not visible`, `Element detached during action`.

Likely **maintenance** if:
- The test was passing in `--baseline` AND the impl diff didn't touch the relevant page / component.
- The selector is brittle (`.btn-3:nth-child(4)`) — semantic selectors fail less.
- A nearby element exists with similar text/role; the page just reorganized.

Likely **genuine** if:
- The element does not exist in the rendered DOM (verify via screenshot or `page.content()`).
- The impl diff renamed / removed the target component.
- The test was added in this iteration (no baseline) AND impl arguably should have rendered it.

Classifier should read the test's `data-testid` / selector → grep the impl for that ID → if found, genuine (impl has it but interaction fails); if not found, check git_log for when it disappeared → maintenance (renamed by harmless refactor) or genuine (deleted by impl).

### Assertion-message-only failure (unit, integration)

Symptoms: `AssertionError: expected X to equal Y, got Z`.

Likely **maintenance** if:
- The expected value is hardcoded to a value that the spec hasn't updated (e.g. test expects `2025-09-15` because that was today's date when test was written).
- The test uses a fixture that includes a date / id that changes per run.

Likely **genuine** if:
- The assertion is semantic (`subscription.status === 'cancelled'`) and the impl returns something else.
- The runner's diff shows a structural mismatch (extra field, missing field, wrong type).

Classifier should diff `expected` vs `actual` and ask: "is the difference due to time / randomness / environment, or due to logic?" Time/random/env = maintenance, logic = genuine.

### Timing / flake failure (E2E, integration)

Symptoms: same test passes on rerun, fails sometimes; `wait` insufficient; race window in test setup.

Likely **maintenance** if:
- Rerunning the test in isolation passes.
- The test uses a fixed `sleep(N)` rather than a condition wait.

Likely **genuine** if:
- Rerunning the test in isolation still fails.
- The race condition reproduces with a `--repeat=10` flag.
- The race is in the impl (not the test setup).

Classifier should request a rerun if the test category is timing-suspicious. `--repeat=10`: if 0/10 pass → genuine; if 8-10/10 pass → maintenance; if 3-7/10 pass → `needs_human` (flake is real, ship-risk is non-zero).

### Resource / environment failure (any layer)

Symptoms: `ConnectionError: localhost:5432 refused`, `OSError: too many open files`.

Likely **maintenance** if:
- The user's local environment is missing a dependency (Postgres not running).
- Tests pass in CI but fail locally.

Likely **genuine** if:
- The impl is leaking resources (filehandles, connections, processes).
- A new test triggered exhaustion that the impl couldn't handle.

Classifier should check: did the *impl* allocate the resource that exhausted? If yes, genuine (resource leak). If no (local env issue), maintenance.

### PBT counterexample failure (unit, property-based)

Symptoms: `Hypothesis found failing example: x=42, y=''`.

**Always genuine** by default. Property-based tests find real bugs almost always — they're hard to write, and a counterexample input has a deterministic reason for failing. Only classify maintenance if:
- The property assertion itself is too strong (`forall x: f(x) > 0` but the spec allows negative outputs). In that case it's a `spec-drift` situation, not a test bug or impl bug — surface as `needs_human` with note "PBT property may be over-strong vs spec".

### Mutation survivor (L5)

Surviving mutants are NOT failures per se — they're diagnostics. They don't get classified. They go into `mutation.surviving_mutants:` and contribute to the kill rate but don't become findings unless the *kill rate* falls below threshold.

## Classifier prompt template

The classifier (typically Haiku) gets this prompt per failure:

```
You are a test-failure classifier. Output exactly one of:
- maintenance
- genuine
- needs_human

INPUTS:
test_file: {file}:{line}
test_name: {test_name}
test_body: |
  {test code, ~30 lines around the failing assertion}
failure_evidence:
  type: {selector | assertion | timing | resource | pbt}
  message: {raw runner output}
  baseline_state: {passed | failed | absent}
  impl_diff_relevance: {touched | not_touched | partial}
  reruns_attempted: {0 | N}
  reruns_passed: {0 | N}

DECISION RULES (apply in order, first match wins):
1. PBT counterexample with concrete input → genuine.
2. Selector failure AND impl diff did not touch the page → maintenance (auto_fix_available if selector is text-based, else needs_human).
3. Assertion mismatch is purely temporal (date/random/uuid) → maintenance.
4. Test passed in baseline AND impl diff is not relevant → maintenance.
5. Rerun N times: 0 pass → genuine; ≥80% pass → maintenance; otherwise → needs_human.
6. Resource exhaustion AND impl allocated the resource → genuine.
7. Anything else → needs_human if uncertain, otherwise genuine.

OUTPUT (YAML):
classification: <maintenance | genuine | needs_human>
confidence: <high | medium | low>
reasoning: <one sentence>
auto_fix_available: <bool — only meaningful if classification: maintenance>
proposed_fix: <one-line patch description — only if auto_fix_available: true>
```

The classifier should NOT write code, run tools, or look at impl files beyond what the inputs provide. Its job is the 3-way decision, fast. If it needs more info, output `needs_human`.

## Auto-fix gating

When `--auto-fix-maintenance` is passed AND a failure is classified as `maintenance` with `auto_fix_available: true`:

1. Apply the proposed fix (selector update, timing wait insertion, fixture refresh).
2. Re-run the test.
3. If pass: record in `maintenance_issues:` with `auto_fixed: true` + diff.
4. If still fail: revert the fix and re-classify (likely `needs_human` this time).

**Never auto-fix without `--auto-fix-maintenance`.** Default behavior surfaces the fix as a suggestion only.
