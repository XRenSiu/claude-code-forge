# invariant-extract — evaluation marker

**gate_pass: `static_only`** · tier: production · evaluated_layers: `[structural]` · date: 2026-06-24

> **What this is (and is not).** This is a persistent record of a *structural* (Tier-1) review
> done by **2 independent judges emulating** skillwise's ruler (`docs/THEORY.md §1-4` +
> `write-skill` construction invariants + `shared/effect-gate.md`). It is **NOT** a run of the
> installed `evaluate-skill` skill (that skill is not installed in this repo), and **NOT** an
> official skillwise certification. The machine-readable verdict is `gate.json` beside this file.

## Verdict

- **Tier-1 (structural): PASS** — no blocking findings remain.
- **Tier-2 (effect delta): NOT RUN** → `static_only`. No held-out Territory set + executor was
  available; per `effect-gate.md`, a production skill whose required effect layer is unrun is
  `static_only` (structurally sound, effect unverified), **not** a certified `pass`.

## How it was reached (2 rounds, measure-after-change)

1. **Round 1** (2 judges): one blocking — the exit section overstated `verify_card.py` as "the
   only guarantee" when the semantic □/◊ half is flagged, not verified. Fixed (reworded to
   "mechanical pre-gate + real guarantee = judge call + human seam + delta_exist").
2. **Round 2** (2 fresh judges, 4-eyes): all blocking **closed**; both independently confirmed
   the `project→negate→narrow` operator order is **§8-exempt** (intrinsic epistemic order, not a
   welded step-march). Both ran `verify_card.py` and confirmed its rejects are **product-level**
   (auto-installed hard invariant / no-provenance / ◊-on-card), not well-formedness.
3. **Post-re-judge nit fixed**: moved "EARS-shaped" out of the mechanical-reject list (the script
   only checks non-empty; EARS *shape* is a judge call).

## To upgrade `static_only` → certified `pass`

Run the effect delta: pick ≥1 Territory with real `failure.memory`, run the extraction
**with and without** the skill on a held-out set, assert on the produced invariant card
(not the wording), require `delta_exist > 0` with zero regressions. Then update `gate.json`.
