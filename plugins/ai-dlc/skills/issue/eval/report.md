# issue — evaluation marker

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

- `verify_issue.py` — good body 0 rejects (with --dos closure ok); vague expect → reject; missing unhappy twin → reject; file-path observe → reject; DOS closure failure → reject + force_track: psl; --kind bug good passes, missing Repro rejected

## Known residuals / fix list

- L2: create one real issue via /issue in a repo with dos.yaml and check the DOS-closure trigger actually forces the PSL track in conversation
- gh issue create / edit path not exercised (needs a live repo)

## To upgrade `static_only` → certified `pass`

New session (so `AI-DLC@claude-code-forge` is in the Skill list), run the L2 items above with and without the
skill on the same input, assert on the produced artifact (issue body / commit set / PR body / evidence log /
findings.yaml), require the with-skill run to clear conditions the without-skill run fails, then update `gate.json`.
