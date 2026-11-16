# Commands and contracts

All commands require Node 22+. `<skill>` is the installed skill directory. Use a task artifact directory outside the target project. Paths supplied to command bindings are reviewed code; discovery never executes them.

```sh
node <skill>/scripts/harness.mjs survey --root <repo> --out <task>/inventory.json
node <skill>/scripts/harness.mjs bootstrap --root <repo> --host dual --context <task>/context.json --authorization-ref "current user request" --checks <task>/checks.json --out <task>/plan.json
node <skill>/scripts/harness.mjs plan --root <repo> --proposal <task>/proposal.json --out <task>/plan.json
node <skill>/scripts/harness.mjs apply --root <repo> --plan <task>/plan.json --accept-plan <plan-digest> --state-dir <task>/transactions
node <skill>/scripts/harness.mjs verify --root <repo> --artifact-dir <task>/runs --out <task>/verification.json
node <skill>/scripts/harness.mjs doctor --root <repo> --receipt <receipt-file> --out <task>/doctor.json
node <skill>/scripts/harness.mjs recover --root <repo> --journal <unfinished-journal>
```

`bootstrap` emits a plan, never writes the project. Omit `--checks` to discover root Vitest or preserve existing bindings. A project with no discoverable supported checks gets an empty binding set; verification cannot pass until populated. Host choices: `dual`, `codex`, `claude-code`, `portable`. A supplied context defaults new installations to `dual`; upgrades preserve their host unless explicitly changed. Existing managed asset edits produce a merge conflict rather than overwrite.

Development bootstrap requires a source-backed profile under the skill workflow; see [development-context.md](development-context.md). `--context` writes the reviewed definition to `.harness/context.json`, compiles rules/workflows/host entries and adds the required `harness-context` check. Existing context is reused when omitted; changed profiles/sources require explicit review and `--context` to refresh fingerprints. The low-level no-context path remains verification-only.

Project-owned commands after adoption:

```sh
node scripts/project-context.mjs
node scripts/project-doctor.mjs /path/outside/project/run/receipt.json
node scripts/project-verify.mjs /path/outside/project/results
```

Custom proposal shape:

```json
{
  "purpose": "Close a confirmed native lint gap",
  "authorization_ref": "User requested implementation and validation",
  "operations": [{
    "path": "relative-file",
    "content": "complete desired UTF-8 content",
    "before_hash": null,
    "reason": "Why this change is needed",
    "source": "Instruction or verified incident path"
  }],
  "checks": []
}
```

For an existing file, `before_hash` must be its current SHA-256, not null. `content: null` deletes an existing file. Review full new contents and a normal diff. The plan adds after hashes and a digest, rejects stale proposals and duplicate/unsafe paths. No arbitrary patch program is evaluated.

Check binding example (replace actual file selection with the project's scope):

```json
{
  "id": "unit-tests",
  "executable": "node",
  "argv": ["node_modules/vitest/vitest.mjs", "run", "--reporter=json", "--outputFile={artifact_dir}/vitest.json"],
  "cwd": ".",
  "depends_on": [],
  "timeout_ms": 180000,
  "reporter": "vitest-json",
  "report_file": "vitest.json",
  "required": true,
  "effects": "temporary-artifacts"
}
```

`node` resolves to the current runtime. `argv` is passed without a shell; use an actual reviewed script for shell pipelines. `env` is an optional map; keep secrets out of plans. `platforms` narrows declared applicability; it is visible in receipts. `stdin` is optional fixture input. `report_file` is relative to that check's fresh artifact directory. `{artifact_dir}` expands only in argv. Dependencies form an acyclic graph; ready independent checks run in parallel.

Reporters: `vitest-json`, `eslint-json`, Node's `tap`, `claims-json`, and indexed `product-json` (see [product-verification.md](product-verification.md)). Claims require `expected_claims` and output `{ "schema_version": 1, "complete": true, "examined": 1, "claims": [{ "id": "expected-id", "status": "PASS" }] }`. Missing/duplicate/extra claims are errors. `exit-code` is diagnostic only and cannot produce PASS.

Contracts are defined in scripts/lib/contracts.mjs, validated at runtime, and exported as JSON Schema in the developer package. Future schema versions require explicit migration. Unrecognized versions are rejected.

Exit codes: `verify` 0 = applicable required checks passed with evidence, 1 = complete execution found failure, 2 = incomplete execution or invalid input. `doctor` 0 = no detected wiring or evidence failure, 1 = a failure was found; UNKNOWN remains explicit and `verified` stays false. Product execution is reported separately per entry and in `product_verified`. `project-learn.mjs` uses 1 for a recorded product FAIL or unsuccessful qualification; see [learning.md](learning.md). Other factory commands 0 = command completed, 2 = input/operation error. A successful bootstrap/apply is not successful verification.
