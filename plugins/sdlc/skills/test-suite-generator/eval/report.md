# test-suite-generator — evaluation marker (sdlc copy)

**gate_pass: `static_only`** · tier: production · evaluated_layers: `[structural]` · date: 2026-09-05

> Imported into sdlc from **done-when-pipeline v1.1.0** (this repo's canonical version; qanat holds an older 2026-06-13 copy). Body kept;
> a wiring section was appended. This is an author-run structural pass (skillwise L0 linter + `bash plugins/sdlc/eval/smoke.sh`),
> not a decorrelated read and not an L2 with/without comparison.

## Scripts run
- `derive_counts.py` — counts derived from the example contract (--json)
- `gen_existence.py` — emits a fail-fast existence script (set -euo pipefail, no if-wrapped checks)
- `check_verbatim_names.py` — all contract names present → 0; a tests dir missing names → 1 under --check

## Residual
- sub-steps 4-A…4-E (12 linter step-hits) inherited; six-cell classification pending

## Fix list
- L2: run inside a real /sdlc acceptance stage (specs/<feature>/ with done_when.yaml + tests/) and compare with the source plugin's behaviour
- classify the inherited phase-map order into the six cells or rewrite as φ/γ (skillwise §3)
