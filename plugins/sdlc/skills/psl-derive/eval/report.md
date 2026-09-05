# psl-derive — evaluation marker

**gate_pass: `static_only`** · tier: production · evaluated_layers: `[structural]` · date: 2026-09-05

> Author-run structural pass only (skillwise L0 linter + `bash plugins/sdlc/eval/smoke.sh`). Not a decorrelated
> two-judge read, not an L2 with/without comparison. Runtime claims are predictions.

## Verdict
- Tier-1 (structural): PASS (author-run) — no step-march, exit via `verify_derived.py`, routes by gap, high-risk fenced.
- Tier-2 (effect delta): NOT RUN → `static_only`.

## Scripts run
- `verify_derived.py` — good derived dir passes (4 files, all decisions cite existing PSL-IDs, dos-proposal passes verify_dos.py, no invented entities, divergence n:3 with agenda); bad dir rejected on 4 independent breaches (decision without ref, fake PSL-099, Step 1 in workflow, invented DateFilterCard)

## Fix list
- L2: run N=3 isolated derivations on one real PSL and hold a real G1 — measure whether the divergence set actually surfaces the PSL's underdetermined slots
- DOS proposal ↔ dos-extract actual ontology reconciliation is still manual (G1 record); a reconcile skill is a registered blank
