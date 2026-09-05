# review-loop — evaluation marker

**gate_pass: `static_only`** · tier: production · evaluated_layers: `[structural]` · date: 2026-09-05

> **What this is (and is not).** An author-run *structural* pass: the skillwise L0 linter (0 blocking) and the
> plugin smoke suite (`bash plugins/sdlc/eval/smoke.sh`, 77/77 on fixtures). It is **not** a decorrelated
> two-judge read and **not** an L2 with/without-skill comparison. Per skillwise THEORY §7 an unguided read is
> ~46% accurate on "which skill is better"; everything here about runtime behaviour is a prediction.

## Verdict

- **Tier-1 (structural): PASS (author-run)** — no step-march, exit surface present, scripts present, description
  routes by gap (`Use when:` / `NOT for:`), high-risk section present, no persona content.
- **Tier-2 (effect delta): NOT RUN** → `static_only`.

## Scripts run (what the smoke suite actually exercised)

- `pr-poll.sh` — offline subcommands only: round → 0 then 30 at MAX_ROUNDS; strike → 0 then 31 at MAX_THREAD_STRIKES; counters json valid; corrupt counters self-heal. watch/snapshot/threads/resolve/done NOT run (need a live PR); logic is a near-verbatim adaptation of vana-builder pr-review-loop v0.4.0 which was run there

## Known residuals / fix list

- L2: run on one real PR with ≥3 comments (defect / question / out-of-scope) and check verdicts + reply-before-resolve
- linter persona hit at L58 is a false positive (the phrase describes prompt injection); no persona content shipped

## To upgrade `static_only` → certified `pass`

New session (so `sdlc@claude-code-forge` is in the Skill list), run the L2 items above with and without the
skill on the same input, assert on the produced artifact (issue body / commit set / PR body / evidence log /
findings.yaml), require the with-skill run to clear conditions the without-skill run fails, then update `gate.json`.
