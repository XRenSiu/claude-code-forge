# calibrate — evaluation marker

**gate_pass: `static_only`** · tier: production · evaluated_layers: `[structural]` · date: 2026-06-24

> **What this is (and is not).** A persistent record of a *structural* (Tier-1) review by independent
> judges **emulating** skillwise's ruler (`docs/THEORY.md §1-4` + `write-skill` construction invariants
> + `shared/effect-gate.md`). It is **NOT** a run of the installed `evaluate-skill` skill (not installed
> here), and **NOT** an official skillwise certification. Machine-readable verdict: `gate.json` beside this file.

## Verdict

- **Tier-1 (structural): PASS** — the one blocking finding is closed.
- **Tier-2 (effect delta): NOT RUN** → `static_only`. No held-out standard set + executor; per `effect-gate.md`
  a production skill whose required effect layer is unrun is `static_only` (structurally sound, effect unverified).

## How it was reached (2 rounds, measure-after-change)

1. **Round 1** (1 judge): one blocking — `verify_calibration.py` ratchet-protected the agreement floor
   (`HARD_ALPHA_FLOOR=0.80`, rejecting `--min-alpha 0.7`) but left the **mutation threshold floorless**.
   `--min-mutation 0.3` let a `mutation_score` of 0.4 PASS (activation ALLOWED) — exactly the "lower the line to
   pass the standard" reward-hack the skill forbids in three places (an asymmetric ratchet hole; the script
   shipped a gate gameable by the move it tells you never to make). Three non-blocking: "proposed" field wording
   (now landed in dos 0.1.15), the ☐3 exit bullet missing `holdout_unexposed_confirmed`, and `agreement_alpha`
   vs `krippendorff_alpha` naming drift.
2. **Fix**: `HARD_MUTATION_FLOOR=0.70` added, enforced symmetrically with the alpha floor (reject + clamp). Doc
   fixes: SKILL.md says "Schema (landed, dos 0.1.15)" with the field-name map; ☐3 bullet adds
   `holdout_unexposed_confirmed`; the asset template's stale "拟增字段" comment corrected to "已落".
3. **Round 2** (1 fresh judge, 4-eyes): blocking **closed** — the Round-1 attack (mutation 0.4 via `--min-mutation 0.3`)
   now FAILS; both floors are symmetric and fail-closed on every malformed input. Doc fixes confirmed. Confirmed the
   skill is cleanly distinct from the runtime `calibration.resolved` event (a SIGNAL into it, not a collision).

## To upgrade `static_only` → certified `pass`

Run the effect delta: on held-out standards, run calibration **with and without** the skill; require it catches
decorative rulers (uncalibrated eval_case / low-agreement rubric) the engine would have shipped — `delta_exist > 0`,
zero regressions. Then update `gate.json`.
