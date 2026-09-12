# AI-DLC — evaluation marker

**gate_pass: `static_only`** · tier: production · evaluated_layers: `[structural]` · date: 2026-09-05

> **What this is (and is not).** An author-run *structural* pass: the skillwise L0 linter (0 blocking) and the
> plugin smoke suite (`bash plugins/ai-dlc/eval/smoke.sh`, 101/101 on fixtures). It is **not** a decorrelated
> two-judge read and **not** an L2 with/without-skill comparison. Per skillwise THEORY §7 an unguided read is
> ~46% accurate on "which skill is better"; everything here about runtime behaviour is a prediction.

## Verdict

- **Tier-1 (structural): PASS (author-run)** — no step-march, exit surface present, scripts present, description
  routes by gap (`Use when:` / `NOT for:`), high-risk section present, no persona content.
- **Tier-2 (effect delta): NOT RUN** → `static_only`.

## Scripts run (what the smoke suite actually exercised)

- `aidlc_state.py` — init/advance/set/gate/card/fail/archive: transition order enforced (skip refused), prerequisites checked against state (issue.number, lock.path, cards.lint_passed, cards done, evaluation/skip reason), --force requires --reason and writes a waiver row to ledger.md, G2 pass refused without lock.path, G1 reject refused without attribution, same-fingerprint 2nd failure → escalate:true, whitelist_overflow → escalate_to human, unknown signal refused; argparse bug (--slug after subcommand unrecognized) found by smoke and fixed same-day
- `lint_cards.py` — bad set rejected on 6 independent breaches (dup REQ, glob overlap, missing REQ-003, ac_ids not in done_when, dos closure, context>40k); good set passes; shared-file logic bug (`src/**` treated as covering root package.json) found by smoke and fixed same-day
- `lock_done_when.py` — sign → verify ok; tampered done_when.yaml → exit 1; same tamper + change-proposal-001.md → exit 2
- `metrics.py` — exports lead time / rounds / reflow distribution / G1 rate / human-AC ratio / escapes from a fixture archive

## Known residuals / fix list

- L2: run /ai-dlc end-to-end on one real TASK-track requirement in a fresh session (Skill list must pick up AI-DLC@claude-code-forge) and record the archive dir
- blank (registered in references/stages.md): contract.yaml schema; ontology-drift; psl-derive
- consider compiling the advance-prerequisite gate as a Stop hook once the flow stabilises (declared, not compiled today)

## To upgrade `static_only` → certified `pass`

New session (so `AI-DLC@claude-code-forge` is in the Skill list), run the L2 items above with and without the
skill on the same input, assert on the produced artifact (issue body / commit set / PR body / evidence log /
findings.yaml), require the with-skill run to clear conditions the without-skill run fails, then update `gate.json`.
