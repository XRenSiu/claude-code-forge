# Incremental application

Review the user's scope, complete proposed content, native config diff and each command's effects. Prior user authorization persists. `authorization_ref` is a human-readable pointer to that scope; it is not a machine-issued permission. `--accept-plan` binds the exact content that the caller reviewed.

The writer rejects absolute paths, parent traversal, `.git`, symlinks along write paths, duplicate targets and stale hashes. Instruction symlinks are resolved by bootstrap to their internal authoritative file before planning; other writes do not follow symlinks. Model-authored merges preserve unrelated content by reading it before creating the proposal. Managed runtime files use recorded hashes; locally edited assets require a manual merge plan.

All preconditions are checked before mutation and each target checked again at write time. A project lock serializes cooperating writers. Per-file temp/rename writes and an external journal support recovery. Every entry records prior content/mode and intended resulting hash before writing. On failure, restoration only touches files still equal to this transaction's output; a concurrent edit is preserved and reported as a recovery conflict. Recovery handles intent records left by a process crash. Inspect the recorded owner; only a dead process lock is reclaimed automatically.

External editors do not honor the lock. There is no filesystem-wide atomic transaction or adversarial race guarantee. Prefer an isolated worktree for multi-file changes and inspect final diff. Recovery may leave empty parent directories. The artifact directory contains backup contents; retain it under the user's normal local access controls and do not publish it.

For upgrades, run bootstrap again to detect generated-asset drift, rebuild a plan, then verify. Same-version reruns are idempotent. Schema migrations are explicit; v0.1 rejects unsupported schema versions instead of guessing.
