# plan-cards — evaluation marker

**gate_pass: `static_only`** · tier: production · evaluated_layers: `[structural]` · date: 2026-09-05

> Author-run structural pass (skillwise L0 linter + `bash plugins/ai-dlc/eval/smoke.sh`). Not a decorrelated read, not an L2 run.
> Created in the 2026-09-05 re-split (docs/design-notes.md): the lifecycle had no carrier for this ring.

## Scripts run
- `lint_cards.py` — bad card set rejected on 6 independent breaches (dup REQ, glob overlap, missing REQ-003, ac_ids not in done_when, dos closure, context>40k); good set passes (moved here from ai-dlc/scripts)

## Fix list
- L2: split one real frozen contract into cards and hand a card to card-implementer in a fresh session; check it finishes without asking for context
