# Per-commit table — origin/main..HEAD on docs/1-sdlc-ring-audit (g2-judge nh-003 ruling, record condition)

Generated at HEAD b87dc58 · 28 commits · run_card 11, run_deviation 3, run_docs 11, peer 3

forbidden_paths (done_when.yaml#constraints): `tests/**`, `**/tests/**`, `done_when.yaml`, `**/done_when.yaml`, `dos.yaml`, `**/dos.yaml`, `.done_when.lock`, `**/.done_when.lock`, `plugins/sdlc/skills/**`, `plugins/sdlc/agents/**`, `plugins/sdlc/docs/**`, `plugins/sdlc/dogfood/ring-audit/PSL-sdlc-ring-audit.md`, `plugins/sdlc/dogfood/ring-audit/derived/**`, `plugins/sdlc/dogfood/ring-audit/issue-body.md`, `plugins/sdlc/dogfood/ring-audit/g1-record.md`, `plugins/sdlc/dogfood/ring-audit/g2-record.md`, `.sdlc/**`

| sha | subject | class | Card footer | touches audited dirs | touches forbidden_paths |
|---|---|---|---|---|---|
| 587f371 | fix(sdlc): verifier and gate defects found by the ring-audit dogfood r | Run · deviation (PSL L122-123) | — | 7 (verify_commit.py, verify_issue.py, verify_derived.py, g1_record.md) | 7 (verify_commit.py, verify_issue.py, verify_derived.py) |
| 30bebf3 | chore: ignore .sdlc/ runtime state of the sdlc plugin | Run · docs/test/chore (orchestrator) | — | 0  | 0  |
| 5b71199 | docs(sdlc): ring-audit dogfood — world, ontologies, invariants, contra | Run · docs/test/chore (orchestrator) | — | 0  | 20 (PSL-sdlc-ring-audit.md, divergence.md, dos-proposal.yaml) |
| 100aa12 | feat(humanize): compile cold-read verdict, add keep-structure contract | peer (shared branch) | — | 0  | 0  |
| df48739 | chore: bump humanize to v0.3.0 with report genre, keep-structure (stru | peer (shared branch) | — | 0  | 0  |
| bf3f13e | docs(sdlc): add "raising the floor" report (2026-09-05) | peer (shared branch) | — | 4 (raising-the-floor-2026-09-05.cold-read-1.yaml, raising-the-floor-2026-09-05.cold-read-2.yaml, raising-the-floor-2026-09-05.html, raising-the-floor-2026-09-05.md) | 4 (raising-the-floor-2026-09-05.cold-read-1.yaml, raising-the-floor-2026-09-05.cold-read-2.yaml, raising-the-floor-2026-09-05.html) |
| ebe270d | fix(sdlc): gate pass clears a stale reject attribution (I-51) | Run · deviation (PSL L122-123) | — | 1 (sdlc_state.py) | 1 (sdlc_state.py) |
| 2456a5c | docs(sdlc): ring-audit G2 record and signed g2 lock (9 files, delegate | Run · docs/test/chore (orchestrator) | — | 0  | 2 (.done_when.lock, g2-record.md) |
| c729f76 | fix(sdlc): lock check compares landing content hash, not paths (I-52) | Run · deviation (PSL L122-123) | — | 1 (verify_commit.py) | 1 (verify_commit.py) |
| 57ebf2b | test(sdlc): ring-audit L5 suite — 30 red tests, 19 mutants, l5 lock | Run · docs/test/chore (orchestrator) | — | 0  | 30 (.done_when.lock, RED_BASELINE.txt, checklist_G3.md) |
| 0be2770 | feat(ring-audit): add check-audit CLI, commit replay and schema doc | Run · Card | CARD-01 | 0  | 0  |
| 08238cd | feat(ring-audit): require a signer on every non-pending gate verdict | Run · Card | CARD-01 | 0  | 0  |
| e217d10 | test(sdlc): ring-audit L5 re-encoded under G1 interpretation rules 1-3 | Run · docs/test/chore (orchestrator) | — | 0  | 31 (.done_when.lock, g1-record.md, RED_BASELINE.txt) |
| 5a6889c | docs(sdlc): ring-audit skill issues I-59..I-64, CARD-01 notes on G1 | Run · docs/test/chore (orchestrator) | — | 0  | 0  |
| fafcad7 | docs(sdlc): ring-audit calibration report, instrument mutants, cards | Run · docs/test/chore (orchestrator) | — | 0  | 0  |
| da8c315 | docs(sdlc): ring-audit hidden-set fallback A, signed by delegated G2 | Run · docs/test/chore (orchestrator) | — | 0  | 0  |
| d09c6df | docs(sdlc): ring-audit known_gaps artefact (11 items + holdout summary | Run · docs/test/chore (orchestrator) | — | 0  | 0  |
| 05963a5 | feat(ring-audit): audit fragment for rings R3-R5 (CARD-03) | Run · Card | CARD-03 | 0  | 0  |
| f8ef234 | feat(ring-audit): audit fragment for rings R7-R8 (CARD-05) | Run · Card | CARD-05 | 0  | 0  |
| 419a364 | feat(ring-audit): audit fragment for rings R0-R2 and spine (CARD-02) | Run · Card | CARD-02 | 0  | 0  |
| eba9796 | feat(ring-audit): audit fragment for ring R6 (CARD-04) | Run · Card | CARD-04 | 0  | 0  |
| 3441ba4 | feat(ring-audit): assemble audit.yaml from the four ring fragments | Run · Card | CARD-06 | 0  | 0  |
| 6326123 | feat(ring-audit): render AUDIT.md from audit.yaml (CARD-06) | Run · Card | CARD-06 | 0  | 0  |
| b24243d | fix(ring-audit): extend the replay record to CARD-06's own commits | Run · Card | CARD-06 | 0  | 0  |
| 5c84a5a | refactor(ring-audit): count the evidence tiers, don't hand-write them | Run · Card | CARD-06 | 0  | 0  |
| 843c3ee | docs(ring-audit): say what the replay snapshot cannot cover | Run · Card | CARD-06 | 0  | 0  |
| ebf5800 | docs(sdlc): ring-audit G3 input (18 rulings requested) and PR body dra | Run · docs/test/chore (orchestrator) | — | 0  | 0  |
| b87dc58 | docs(sdlc): ring-audit acceptance-fleet iteration-001 trace, NEEDS_HUM | Run · docs/test/chore (orchestrator) | — | 0  | 0  |

Reading: Card commits are gated by verify_commit.py --card (whitelist ∧ ¬forbidden); deviation commits are the PSL L122-123 carve-out (ledger kind=deviation rows I-04/05/07/17/34/38/39/47/51/52, late entries for ebe270d/c729f76); e217d10's touch of the locked set is legal via change-proposal-001 (R04); orchestrator docs commits touch no forbidden path; peer commits ride the shared branch and are not Run edits (main carries bf3f13e's twin fbc6a3c).
