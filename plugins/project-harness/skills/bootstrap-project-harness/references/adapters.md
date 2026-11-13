# Supported adapters

Two independent dimensions: stack bindings describe how the project checks work; host entries describe how an agent discovers them. Runtime dispatch is through `reporter`, not a new rule language.

| Stack / reporter | v0.1 behavior | Qualification limit |
| --- | --- | --- |
| Node / TypeScript | package and workspace inventory, lock conflicts, Node pin, Vitest discovery | no automatic dependency installation |
| Vue / Electron | same native toolchain; explicit command bindings for process-boundary fixtures | desktop/native E2E needs its own platform and resources |
| Vitest | JSON assertion matrix and counts | installed version validated by project run |
| ESLint | per-file JSON counts and rule messages | ignored/fatal rows distinguished; native config owns semantics |
| Node test runner | final TAP counters and named subtests | Node 22+; file-only wrapper results are insufficient evidence |
| Claims | expected claim IDs and nonzero denominator | producer remains trusted project code |

| Host | Generated entry | What is not inferred |
| --- | --- | --- |
| Codex | managed verification pointer in AGENTS.md or its internal authoritative symlink target | .claude rules/hooks do not automatically become Codex rules/hooks |
| Claude Code | managed pointer in CLAUDE.md | presence does not prove session loading or hook execution |
| Portable | runtime, manifest and usage doc only | no host activation |

Install the factory itself in the host's supported skill directory. The development package installs in `~/.codex/skills/bootstrap-project-harness` for the current Codex environment; project-scoped distribution can use `.agents/skills/`. Claude uses `.claude/skills/`. The same self-contained skill content works through thin host metadata. Do not mirror the whole `.claude` tree into a different host and claim parity.

v0.1 emits no hooks because their payload/version contracts require separate runtime qualification. It reuses native CLI/CI enforcement. Future adapters should declare supported syntax, resolution, platform and host version and add real fixtures. A static doctor never upgrades itself to a live compatibility verdict.
