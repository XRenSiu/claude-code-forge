# Fix prompt — iteration 2 input for sdlc-ring-audit

The implementation in `plugins/sdlc/dogfood/ring-audit/` does not yet satisfy `plugins/sdlc/dogfood/ring-audit/done_when.yaml` at the bar the acceptance run set. Address the following issues. Do not modify `tests/**`, `done_when.yaml`, `dos.yaml`, `.done_when.lock`, the four `audit/rings-*.yaml` fragments, or anything under `plugins/sdlc/{skills,agents,docs}` — those are frozen or audited.

## Required fixes

- **`plugins/sdlc/dogfood/ring-audit/render_audit.py:435-441` (and every other cell write)** — free-text YAML values (signer, at, part id, needed.verdict, naming fields) are interpolated into GFM table rows without escaping `|`, so a crafted value renders a delegated gate as 人签 or prints "已实现 ✓". Route every cell through the existing `cell()` escaper (pipes, newlines, backticks) and render signer_kind from a closed map {human: 人签, delegated_agent: 代签（delegated）, other/None: 未知} rather than from the raw string. (REQ-006, AC-006-a)
- **`plugins/sdlc/dogfood/ring-audit/render_audit.py:512-594`** — assembly notes and the known-gaps lead-in hard-code counts (11 / 31 / 73 / 58 / 39) and the dos.yaml R001/R008/R010/R017 table as literals. Compute every number and row from the loaded `audit.yaml` (len of gaps / artifacts / proposals / gates; `unenforced_rule` gaps grouped by rule) so the projection cannot go stale. (REQ-004, REQ-006)
- **`plugins/sdlc/dogfood/ring-audit/render_audit.py:238-239`** — the 闸 · 门 column is built from `part.gates` only; `artifacts[].checked_by` (the F-06 field that caps a producer at declared when empty) is never rendered and disagrees for 8 of 42 Parts. Add a `checked_by` column (or append `· artifact 闸: …` in the same cell) sourced from artifacts[] for the Part's artifact ids, and print `（无闸 → 封顶 declared）` when it is empty. (REQ-005, AC-005-a)
- **`plugins/sdlc/dogfood/ring-audit/replay_card_commits.sh:53-57`** — commits without a `Card:` footer are skipped entirely, so a footer-less commit touching the audited dirs is invisible to the record. Keep the Card replay footer-scoped (that is AC-007-a's given), but ADD a second, clearly labelled pass over every commit in the branch range since the first Card commit that lists `non_card_commits_touching_audited_dirs` (count + shas) in the JSON; do not fold it into the gating count. (REQ-007)
- **`plugins/sdlc/dogfood/ring-audit/replay_card_commits.sh:67`** — `git diff --name-only <range>` runs with rename detection, so a file moved out of an audited dir with ≥50% similarity lists only its destination. Use `git diff --name-only --no-renames` (both here and when computing `touches_audited_dirs`). (REQ-007, AC-007-b)
- **`plugins/sdlc/dogfood/ring-audit/audit.yaml#run_evidence`** — the replay table cites shas from the CARD-06 worktree (pre-cherry-pick) that do not resolve on the feature branch. Re-run `replay_card_commits.sh` on the current branch and record the current output plus the branch name and HEAD in `run_evidence.check_runs` / `audited_dirs_diff`; state that shas are branch-specific. (REQ-006, AC-006-a)

## Deferred (contract-level; NOT for this iteration — routed to change-proposal-002)
- check_audit.py rule 1 trusts the self-reported `artifacts[]` and accepts any non-empty `alternatives_of` string (F-05's three graph conditions unchecked) — needs a new predicate + fixture + test.
- check_audit.py applies rule 2(e)'s same-ring clause to `fills[]`, which the G1 text attaches only to `missing[]` — needs a G1 interpretation before the instrument changes.

## Constraints
- Smallest change per issue; no refactors of adjacent code; no new tests (if you need one, stop and report CONTRACT_CHANGE_NEEDED).
- After every edit: `bash plugins/sdlc/dogfood/ring-audit/tests/ring-audit/run_tests.sh` must stay `existence=ok unittest=ok`, `bash …/mutation.sh` 24/24, and `python3 render_audit.py` must reproduce a byte-stable AUDIT.md on a second run.
- Commit through `verify_commit.py --card <CARD-01 or CARD-06 yaml> --lock …` with the matching `Card:` footer; render_audit.py / audit.yaml / AUDIT.md belong to CARD-06, replay_card_commits.sh to CARD-01.
