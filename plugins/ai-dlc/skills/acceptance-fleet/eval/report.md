# acceptance-fleet — evaluation marker (AI-DLC copy)

**gate_pass: `static_only`** · tier: production · evaluated_layers: `[structural]` · date: 2026-09-05

> Imported into AI-DLC from **done-when-pipeline v1.1.0** (this repo's canonical version; qanat holds an older 2026-06-13 copy). Body kept;
> a wiring section was appended. This is an author-run structural pass (skillwise L0 linter + `bash plugins/ai-dlc/eval/smoke.sh`),
> not a decorrelated read and not an L2 with/without comparison.

## Scripts run
- (no bundled script; structural read only)

## Residual
- pure orchestrator; S0–S5 phase map inherited (5 hits); gh-networked dispatch not exercised

## Fix list
- L2: run inside a real /ai-dlc acceptance stage (specs/<feature>/ with done_when.yaml + tests/) and compare with the source plugin's behaviour
- classify the inherited phase-map order into the six cells or rewrite as φ/γ (skillwise §3)
