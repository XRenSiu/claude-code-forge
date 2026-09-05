# pm-reviewer — evaluation marker (sdlc copy)

**gate_pass: `static_only`** · tier: production · evaluated_layers: `[structural]` · date: 2026-09-05

> Imported into sdlc from **done-when-pipeline v1.1.0** (this repo's canonical version; qanat holds an older 2026-06-13 copy). Body kept;
> a wiring section was appended. This is an author-run structural pass (skillwise L0 linter + `bash plugins/sdlc/eval/smoke.sh`),
> not a decorrelated read and not an L2 with/without comparison.

## Scripts run
- (no bundled script; structural read only)

## Residual
- no bundled script; phase map inherited (2 hits)

## Fix list
- L2: run inside a real /sdlc acceptance stage (specs/<feature>/ with done_when.yaml + tests/) and compare with the source plugin's behaviour
- classify the inherited phase-map order into the six cells or rewrite as φ/γ (skillwise §3)
