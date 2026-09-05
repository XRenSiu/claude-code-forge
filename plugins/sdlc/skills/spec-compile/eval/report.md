# spec-compile — evaluation marker

**gate_pass: `static_only`** · tier: production · evaluated_layers: `[structural]` · date: 2026-06-24

> **What this is (and is not).** A persistent record of a *structural* (Tier-1) review by independent
> judges **emulating** skillwise's ruler (`docs/THEORY.md §1-4` + `write-skill` construction invariants
> + `shared/effect-gate.md`). It is **NOT** a run of the installed `evaluate-skill` skill (not installed
> here), and **NOT** an official skillwise certification. Machine-readable verdict: `gate.json` beside this file.

## Verdict

- **Tier-1 (structural): PASS** — no blocking findings (round 1 passed; 2 non-blocking hardenings applied).
- **Tier-2 (effect delta): NOT RUN** → `static_only`. No held-out spec set + executor; per `effect-gate.md`
  a production skill whose required effect layer is unrun is `static_only` (structurally sound, effect unverified).

## How it was reached (2 rounds, measure-after-change)

1. **Round 1** (1 judge): **PASS, 0 blocking.** The load-bearing altitude discipline was confirmed enforced —
   a `structural`-decidability clause routed to line 2/3 rejects as "routed UP the ladder — keyline violated";
   example-only behavioral batteries reject; free-form / non-binary / no-evidence G2 dimensions reject;
   `calibration_pending` is mandatory (compiled ≠ certified). Two **non-blocking** items: (a) the script only
   checked gate consistency *when present* (an omitted `gate` passed), under-delivering the SKILL's "names its
   gate" claim; (b) the high-risk list omitted the inverse gaming vector (a false `structural` label to dodge G2).
2. **Fix**: `verify_compile.py` now rejects a routed clause with no `gate` (robust to missing key AND empty value)
   while keeping the present-but-inconsistent reject; SKILL.md high-risk list adds the false-decidability-label item.
3. **Round 2** (1 fresh judge, 4-eyes): both addressed, **no regression** — gate-omitted → REJECT, gate present+correct
   → exit 0, routing-up → REJECT, valid behavioral manifest → exit 0. Changes are strictly additive (a tightening +
   a doc line).

## To upgrade `static_only` → certified `pass`

Run the effect delta: on held-out specs (a 常驻不变量 + a 本次验收), run compilation **with and without** the skill; assert the
routing pushes DOWN the ladder where decidable and emits non-example-only behavioral batteries — require
`delta_exist > 0` with zero regressions. Then update `gate.json`.
