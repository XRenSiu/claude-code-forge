# retro — evaluation marker

**gate_pass: `static_only`** · tier: production · evaluated_layers: `[structural]` · date: 2026-09-05

> Author-run structural pass (skillwise L0 linter + `bash plugins/ai-dlc/eval/smoke.sh`). Not a decorrelated read, not an L2 run.
> Created in the 2026-09-05 re-split (docs/design-notes.md): the lifecycle had no carrier for this ring.

## Scripts run
- `metrics.py` — exports lead time / rounds / reflow distribution / G1 rate / human-AC ratio / escapes / waivers from a fixture archive (moved here from ai-dlc/scripts)

## Fix list
- L2: run on ≥2 archived features and check every proposal has target/change/verify_by and reaches its destination (proposal file / Open Questions / gate fix_list)
