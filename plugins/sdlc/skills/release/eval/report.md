# release — evaluation marker

**gate_pass: `static_only`** · tier: production · evaluated_layers: `[structural]` · date: 2026-09-05

> Author-run structural pass (skillwise L0 linter + `bash plugins/sdlc/eval/smoke.sh`). Not a decorrelated read, not an L2 run.
> Created in the 2026-09-05 re-split (docs/design-notes.md): the lifecycle had no carrier for this ring.

## Scripts run
- `verify_release.py` — temp repo: pre-tag pass with consistent changelog/notes/bump; post-tag fails before tag; passes with tag on HEAD; refuses to overwrite an existing tag; bump mismatch (patch for a feat) rejected; empty Rollback rejected

## Fix list
- L2: one real release with a --verify-cmd; check release.done stays false on red verification
- deploy systems are out of scope — the skill only gates the artifacts and the irreversible actions
