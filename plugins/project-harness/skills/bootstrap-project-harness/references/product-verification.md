# Product operations, feature index and checker calibration

Start from a product promise and its user entry. Preserve native regression checks. A successful unit suite, installed harness or healthy server does not establish that the user operation worked.

## Feature index

Pass a reviewed JSON file to `bootstrap --features <file>`. Bootstrap preserves an existing index on upgrades, adds missing checks, validates their claim binding and generates `docs/verification-features.md`. Edit the project-owned `.harness/features.json`; regenerate its documentation through a reviewed plan. When retiring an entry, explicitly review the check graph too: bootstrap never silently deletes existing checks.

The index has `schema_version: 1` and a nonempty `features` array. Each feature has a stable `id`, `title`, existing requirement `sources`, and nonempty `entries`. An entry contains:

```json
{
  "id": "http", "check_id": "revoke-product", "surface": "http",
  "location": "PUT /api/access → GET /api/private",
  "driver": "scripts/verify-access.mjs",
  "checker_files": ["scripts/observe-access.mjs"],
  "fixture_files": ["scripts/access.fixture.json"],
  "claims": ["old-access-denied"], "evidence_types": ["http"],
  "prerequisites": ["Fresh local database; no live accounts"],
  "unsupported": ["Native desktop interaction"],
  "node_args": [], "timeout_ms": 60000
}
```

Supported surface labels: `http`, `web`, `desktop`, `cli`, `library`. Labeling an entry desktop does not automate a desktop: its driver must actually exercise that surface. List omitted UI, operating systems, real accounts and upstream behavior explicitly. The generated index is navigation, never a historical PASS reused as current evidence.

## Driver contract

An ESM driver exports all five async functions. Each receives `(ctx, instance)`; `launch(ctx)` returns `instance`.

| Phase | Responsibility |
|---|---|
| launch | Start the real isolated product; fixture setup may seed known data. |
| doctor | Probe the running instance and dependencies; return `{ready: true, instance_id: "..."}`. |
| drive | Perform the actual operation through its supported boundary. Preserve request and response observations. |
| observe | Assert product outcomes; return every indexed claim exactly once. |
| cleanup | Close owned connections/processes, including partial launch failures. |

`ctx.root`, `ctx.scratch`, `ctx.signal` and `ctx.entry` identify the candidate, system temporary directory, cancellation and entry. Use `ctx.spawn(executable, argv, options)` for owned subprocesses; environment inheritance is restricted, no shell is used. Honor the abort signal in long waits. Do not spawn detached children or access live accounts implicitly. Cleanup has a five-second grace period and remaining registered children are terminated.

Use `ctx.capture(type, name, sanitizedJson)` immediately after each operation to preserve bounded raw evidence outside the project **before cleanup**. If a later operation fails, completed observations must remain available for diagnosis. It returns an evidence ID. Do not capture tokens, private keys, arbitrary headers or unsanitized logs. Return observations like:

```js
return [{id: 'old-access-denied', status: response.status === 403 ? 'PASS' : 'FAIL',
  expected: '403 using the old authorization after revoke',
  actual: JSON.stringify(response), evidence_refs: [evidenceId]}]
```

Startup, timeout, missing observations and cleanup errors are `ERROR`, not assertion `FAIL`. `product-json` checks are required entries in the existing check graph. Product receipts bind candidate content, index, driver/checker, fixture and selected Node environment; raw artifacts have hashes, nonzero sizes and the indexed evidence types. Each invocation has a fresh `invocation_id`; the parent Harness or calibration runner supplies `PROJECT_HARNESS_INVOCATION` and checks the child report against it. Standalone runs create their own ID. Reusing an old report for a second run of unchanged source is rejected. Upgrade the generated runtime and wrappers together and rerun entries: older reports without invocation identity are historical evidence only. This identity detects accidental replay, not a hostile candidate capable of rewriting evidence. Installed dependencies and broader machine state are not certified by these digests. A candidate-owned observer remains self-check code.

## Calibrate against faults

Write a reviewed plan with `schema_version`, `feature_id`, `entry_id`, explicit `dependency_paths`, nonempty `required_faults`, and `mutations`. Each mutation has `id`, source `path`, exact unique `before`, replacement `after`, and the intended failing `claim_id`. Source dependencies linked into copies are reused; audit workspace imports so they do not accidentally run the original source instead of the mutant. All selected faults must be caught; this small targeted set is not a repository-wide mutation score.

Run `node scripts/project-calibrate.mjs <plan.json> <new-directory-outside-project>`. The runner executes a positive baseline, one disposable copy per fault, then the unchanged original as recovery. It never edits the original to inject faults. Driver, checker, fixture and harness edits are forbidden. Only exit 1 with a complete product lifecycle and the named business claim failing counts as `KILLED`. Surviving faults, compile errors, environment failures and incomplete runs cannot qualify the checker.

Bind the reviewed plan with the entry’s `calibration_plan` path before using it as an AI-DLC qualification gate. The runner and AI-DLC reject a substituted plan; an unbound entry may be explored locally but cannot claim current qualification.

The output keeps the exact plan, mutation preimage/postimage, baseline/fault/recovery product receipts, raw evidence and process logs. Scores are derived from these attempts. Validate the chain with trusted-acceptance's `acceptance.py validate-calibration` and pass its paths into AI-DLC's `execution_evidence`. Integrity does not prove an independent collector, a hidden holdout or formal acceptance. Those remain protected-control responsibilities.

When a fault survives, first inspect the observed product behavior, then strengthen the shared observer or driver. Change a contract only when its source was wrong and the relevant authority approves. Rerun positive, fault and recovery controls after any checker change; do not adjust a score or expectation to hide a failure.
