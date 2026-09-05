# commit — evaluation marker

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

- `verify_commit.py` — in a temp repo: good staged + conventional message passes; 'update stuff' rejected; trailing period rejected; on main rejected; AKIA secret in added lines rejected; .env staged rejected; `debugger;` rejected; card whitelist in-list passes / overflow rejected; locked file without proposal rejected / with proposal passes (flag)

## Known residuals / fix list

- L2: run /commit on a real multi-concern diff and check the engine actually splits into two commits
- red-green evidence is manual (references/conventions.md) — no script

## To upgrade `static_only` → certified `pass`

New session (so `sdlc@claude-code-forge` is in the Skill list), run the L2 items above with and without the
skill on the same input, assert on the produced artifact (issue body / commit set / PR body / evidence log /
findings.yaml), require the with-skill run to clear conditions the without-skill run fails, then update `gate.json`.
