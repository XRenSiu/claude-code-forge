# Verification

Preflight the Node major and command effects. The runner takes a candidate digest before and after checking; formatter/project writes invalidate the receipt until rerun. Each execution has a fresh artifact directory and complete expected check list. Collect all independent results even when one fails. Failed prerequisites become NOT_RUN, not successful skips.

Statuses: PASS = executed evidence met criteria; FAIL = executed evidence found violation; ERROR = start/timeout/parser/infrastructure failure; NOT_RUN = no execution or no substantive denominator; NOT_APPLICABLE = outside the predeclared platform scope. All-not-applicable or empty required check sets cannot pass. Test skips remain counted and limit coverage even when other assertions pass. A successful static checker only proves its analyzed scope.

For a new rule, use real project parsers/resolvers. Test both valid and invalid imports, aliases and applicable syntax. Ensure rejection names the expected rule, not a parse or unresolved-import error. Keep mutations in disposable copies. For existing tree adoption, scan the applicable tree first; resolve real violations or use an explicit migration baseline rather than hiding them.

Timeout/cancellation cleans the process group on macOS/Linux. Windows process-tree cleanup has not been qualified; do not claim Windows support. Logs have bounded capture; exceeding it is ERROR. Report files must come from the current run directory.

Keep report artifacts separate from test temporary workspaces. An artifact directory outside the target can still be inside another Git repository or Node package. Repointing TMPDIR there changes fixture behavior through ancestor Git discovery and inherited package.json `type`. Use system temp by default; if a test intentionally overrides it, retain that choice. Doctor reports enclosing temp scopes, and receipts record the effective per-check temporary directory, scope and environment digests. Non-path environment values are hashed rather than disclosed.

`doctor` compares managed asset hashes and optional receipt digests. It reports host discovery UNKNOWN until a real session trace is inspected. To test discovery, open a new target-host session, make a natural audit/verification request and inspect its tool trace for loading the intended skill/entry and actually using it. Keep model/CLI versions, scope, command results, duration and token metadata if available. Missing cost data is unknown.

Generated runtime is independently usable from `scripts/project-verify.mjs`. Native CI should invoke the same checks or this entry, using its own approved job and candidate identity. Local JSON is self-reported evidence. The current implementation deliberately leaves external_acceptance NOT_REQUESTED; it does not fabricate protected CI acceptance.
## Worktree dependencies and writable caches

Inspect `node_modules` when reusing dependencies in a sandboxed worktree. A directory symlink also redirects caches to the source checkout. Tests can report every assertion as passed and still exit nonzero when a results cache is unwritable; preserve that ERROR and inspect stderr. Keep cache directories local, using an isolated candidate or a local dependency directory with read-only package links. Do not widen sandbox access to the original checkout or modify test selection just to get a green result. A diagnostic manifest with `--no-cache` is separate evidence and cannot certify the unchanged original bindings. Re-run those bindings after correcting the environment.
