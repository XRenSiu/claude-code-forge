# tune — eval report (static_only, 2026-09-05)

- L0 structure: skillwise six cells (缺口 / Σ / φ / Π / γ / 黑名单), no Step 1/2/3, description carries Use when / NOT for.
- Scripts smoke (see `plugins/ai-dlc/eval/smoke.sh` "tune" block):
  - `tune.py` on `eval/fixtures/archive` (feat-a, feat-b) + `eval/fixtures/pr-watch` (PR 12 all-ACCEPT, PR 15 mixed) → 5 proposals, every one with target/current/proposed/evidence/expected_delta/risk/verify_by/delivered_as/apply; note on psl.card_retries (exhausted with convergence escalation → no change).
  - `tune.py` on `eval/fixtures/archive-single` → proposals [] + insufficient_samples.
  - `apply_proposal.py --id P-1 --dry-run` → unified diff on pr-poll.sh `MAX_ROUNDS` default; `--patch` writes a file and leaves targets untouched.
- Not run: real archives; cron trigger via /schedule; human.harness-review PR path.
