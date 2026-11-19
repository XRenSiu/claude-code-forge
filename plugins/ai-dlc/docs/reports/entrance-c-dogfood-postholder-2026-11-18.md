# Entrance C dogfood on PostHolder (2026-11-18/19)

Forge c893954 (ai-dlc 1.30.0, trusted-acceptance 0.10.0, fvkit 1.4.0) was vendored into PostHolder
(TypeScript monorepo, about 55k lines) with `scripts/harness/vendor-forge.py`, and every stage of entrance C
was run: survey scan → isolated `target-surveyor` (survey, lift, contracts) → fresh-context
`formal-reviewer` (props) → `fv props run` / `fv contracts check --run` / `fv external --engine crosshair`.
The stateful-model target went on to entrance B in the same session. Fixes found here shipped as
ai-dlc 1.30.1 / trusted-acceptance 0.10.1 (fvkit 1.4.1).

## What ran

| Step | Result on PostHolder |
|---|---|
| C1 `fv survey scan` | 5 s; 375 TS files, 2881 signals, 18 existing fvkit specs, 19 fix commits in 103 after unshallowing (the first scan on the shallow clone saw 57 commits) |
| C2 survey (isolated agent) | 5 targets, 2 maintainer questions answered through the host's question dialog; a 6th (code-verifier) added when the user asked that every tool be exercised (`source: {kind: user}`) |
| C4 lift T5 | round 1 ABLE_TO_FAIL, then the fresh reviewer failed all 10 checks on F5 with a one-line change each; round 2 strengthened every check with a table-driven test, all reviewer changes CAUGHT |
| generated-inputs T2 | hand-written seeded generator (maintainer declined a dependency), 6 properties, 24 breakages CAUGHT |
| C5 contracts T3 | probe reproduced a real defect: concurrent dispatches overrun a monthly budget (commit transaction does not re-check it) |
| C5 contracts T4 | 5 MATCH, no probe; one reading left to the maintainer |
| code-verifier T6 | CrossHair on fvkit's own verdict functions: FAIL on 1.4.0, NO_COUNTEREXAMPLE_FOUND on 1.4.1 |

## Issues found in the skill (fixed unless noted)

| # | Where | Issue | Fix |
|---|---|---|---|
| 1 | `contracts.classify` | Word search: an exit-0 probe printing `ERROR: … CONFIRMED …` or `NOT  CONFIRMED` was read as a confirmed defect, contrary to bug_validator ("Print exactly CONFIRMED or NOT CONFIRMED … with any additional detail after the keyword"; "ERROR or non-zero exit → error"). Found by CrossHair (T6) through a structured contract; the unconstrained-string contract found nothing even at 180 s per condition — a live demonstration of why CrossHair is capped at E1. | 1.4.1 reads verdict lines: ERROR line → error; both or neither verdict line → error |
| 2 | `external.run` | The engine runs in the spec's directory but received the spec / config / tool paths as given: every relative `--spec` failed with "File not found" (ERROR). | paths resolved before the engine starts; the receipt still records them as given |
| 3 | `fv contracts check` | No receipt: probe reruns (the only executed evidence of C5) could not be retained, bound to a commit or re-validated. | `--out` writes an E0 `contracts` receipt; `fv validate` re-derives each probe from its recorded stdout |
| 4 | `fv survey check` | No receipt either (static, re-runnable). | open |
| 5 | survey ids | `S<n>` / `C<n>` / `X<n>` are positional: a new scanned file before a cited one renumbers everything after it, and any new fvkit spec makes the survey STALE. Workable (exclude the survey's own evidence directory; re-scan and re-pin at the end) but brittle. | open — content-addressed ids would survive unrelated edits |
| 6 | role of files | `.harness/formal/**/checks/*.py` is classed `product` (no tooling dir in its path). | open, cosmetic |

Not skill issues: 5 failures in `eval/smoke.sh` (release bump / rollback / vana remote-tracking checks) fail identically on a clean c893954 worktree in this container — they depend on the git remotes available here.

## What worked as designed

- The fresh-context props reviewer is the strongest step: round 1 of T5 was ABLE_TO_FAIL yet every check was a single fixed example; the reviewer's one-line changes (each keeping all tests green) became breakages the strengthened checks now catch.
- `fv props run` isolation with `isolation.link: [node_modules]` works for a pnpm workspace: nested `*/node_modules` hold only relative symlinks and resolve inside the copy.
- Function-contract probes through the public Hub found a real defect in minutes; T4's all-MATCH result stayed honest (E0, a reading surfaced rather than buried).
- Survey questions (≤5, human-answered) fit the host's question dialog well; the answers flowed into entrance B's requirements verbatim.
