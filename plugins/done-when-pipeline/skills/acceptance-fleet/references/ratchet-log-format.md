# ratchet-log-format.md — full layout of `ratchet-log/iteration-NNN/`

Every iteration of `/acceptance-fleet` writes a complete trace. The trace is the contract — downstream consumers (debugging, training-data extraction, audit) read from here, not from console output.

## Top-level layout

```
specs/<feature>/
├── (spec.md, done_when.yaml, spec-robustness.md, etc — owned by /acceptance-spec)
└── ratchet-log/
    ├── iteration-001/
    ├── iteration-002/
    ├── iteration-003/
    └── ...
```

`ratchet-log/` lives as a sibling of the spec artifacts. Each iteration is sequentially numbered with three-digit zero-padding (`iteration-001`, `iteration-002`, ...) — supports up to 999 iterations per feature (anything past ~20 is almost certainly a stuck SPEC_DRIFT / GAMING_RISK situation that should have been escalated earlier).

## Per-iteration layout

```
ratchet-log/iteration-NNN/
├── timestamp.txt
├── isolation.json
├── input-manifest.json
├── impl-snapshot.txt              # OPTIONAL but recommended
├── impl-diff.patch                # OPTIONAL — diff vs previous iteration's impl-snapshot
├── fleet-outputs/
│   ├── test-runner.yaml
│   ├── existence-checker.yaml
│   ├── requirement-tracer.yaml
│   ├── design-reviewer.yaml
│   ├── adversarial-reviewer.yaml
│   ├── edge-case-hunter.yaml
│   ├── e2e-explorer.yaml
│   └── spec-gaming-detector.yaml
├── rebuttals/
│   └── <originating-finding-id>.yaml
├── meta-judge-output.yaml
├── final-state.json
├── screenshots/                   # OPTIONAL — e2e-explorer outputs
│   └── <finding-id>-<desc>.png
└── <state-specific report>.md     # exactly one of:
                                   #   fix-prompt.md
                                   #   spec-drift-report.md
                                   #   gaming-risk-report.md
                                   #   needs-human.md
```

## File-by-file specification

### `timestamp.txt`
One line, ISO-8601 UTC, when the iteration started.

```
2026-05-25T14:32:07Z
```

### `isolation.json`
What isolation level the iteration ran at + which model went to which role. See `evaluation-isolation-levels.md` for the schema. Required.

### `input-manifest.json`
Checksums of every input file the iteration consumed, so we can reconstruct exactly what the evaluators saw even if files change later.

```json
{
  "spec_md_sha256": "abc123...",
  "done_when_yaml_sha256": "def456...",
  "spec_robustness_md_sha256": "ghi789...",
  "tests_directory_sha256": "jkl012...",
  "impl_root_sha256": "mno345..."
}
```

`tests_directory_sha256` and `impl_root_sha256` are computed by recursively hashing all files in those directories (deterministic order).

### `impl-snapshot.txt`
Tarball of the implementation files this iteration evaluated. Optional but strongly recommended — without it, `impl-diff.patch` can't be reconstructed for spec-gaming-detector's diff mode.

### `impl-diff.patch`
`git diff` between this iteration's impl-snapshot and the previous iteration's. Required if there is a previous iteration; absent for iteration-001.

### `fleet-outputs/<role>.yaml`
One file per role, per `finding-schema.yaml`. Always 8 files (or fewer if a role was skipped — but the skipped role still has a YAML with `skipped: <reason>`).

### `rebuttals/<finding-id>.yaml`
One file per finding that went through the rebuttal pass.

```yaml
finding_id: ar-001
originating_role: adversarial-reviewer
rebutter_role: requirement-tracer
rebutter_model: claude-opus-4-7
timestamp: 2026-05-25T14:35:12Z
verdict: rebutted | stands | ambiguous
rebuttal_text: |
  <the rebutter's reasoning, verbatim>
evidence_offered: |
  <if rebutted: what evidence supports the rebuttal>
  <if stands: 'no rebuttal possible — finding's evidence is concrete'>
```

### `meta-judge-output.yaml`
Per `finding-schema.yaml` § meta-judge output. The single most important file.

### `final-state.json`
The compact summary used by anything that needs the iteration's verdict without parsing meta-judge-output.

```json
{
  "iteration": 3,
  "state_decision": "FIX",
  "blocking_findings_count": 2,
  "gaming_risk_score": 5,
  "spec_drift_counter": 0,
  "duration_seconds_total": 487,
  "cost_usd_estimated": 0.72,
  "next_action": "feed fix-prompt.md to fresh implementation session; re-invoke /acceptance-fleet"
}
```

### State-specific reports
Exactly one of these, depending on `state_decision`:

- `fix-prompt.md` — when `FIX`. The prompt to feed back to the implementation agent. See `fix-prompt-template.md`.
- `spec-drift-report.md` — when `SPEC_DRIFT`. Lists the REQs that consistently produce PBT counterexamples + suggested clarify directions.
- `gaming-risk-report.md` — when `GAMING_RISK`. Lists the gaming vectors that landed + suggested contract adjustments.
- `needs-human.md` — when `NEEDS_HUMAN`. The specific questions requiring human input.

If the state is `DONE`, no state-specific report — the iteration directory itself is the artifact.

---

## Cross-iteration aggregation files (at `ratchet-log/` root)

After each iteration completes, the skill updates two summary files at `ratchet-log/` root:

### `ratchet-log/summary.json`
The whole feature's ratchet history at a glance.

```json
{
  "feature": "subscription-cancellation",
  "total_iterations": 4,
  "current_state": "DONE",
  "iteration_states": ["FIX", "FIX", "FIX", "DONE"],
  "gaming_risk_trajectory": [2, 3, 5, 2],
  "spec_drift_counter": 0,
  "started_at": "2026-05-25T14:00:00Z",
  "completed_at": "2026-05-25T16:42:11Z",
  "total_cost_usd_estimated": 2.84,
  "final_iteration": "iteration-004"
}
```

### `ratchet-log/findings-history.jsonl`
Append-only JSON-lines log of every distinct finding that ever appeared, with which iterations it landed in and when it was resolved.

```jsonl
{"first_iteration": 1, "last_iteration": 2, "finding_signature": "src/billing/cancel.ts:47:concurrent_race", "originating_role": "adversarial-reviewer", "resolved_at_iteration": 3}
{"first_iteration": 2, "last_iteration": 4, "finding_signature": "src/billing/cancel.ts:88:tier_lookup_table", "originating_role": "design-reviewer", "resolved_at_iteration": 4}
```

This is the substrate for spotting "findings that take many iterations to fix" (indicates spec-vs-code ambiguity) and "findings that flap" (impl regression patterns).

---

## What MUST NOT be deleted

- No iteration directory may be deleted by the skill itself.
- No file inside an iteration directory may be truncated by the skill itself.
- No screenshot may be downsampled or compressed by the skill itself.

The user may garbage-collect old iteration directories manually; the skill does not.

## What CAN be deleted

- The user may delete `ratchet-log/` entirely to start a feature's acceptance loop fresh. The skill detects an absent log and starts at iteration-001.
- The user may delete individual iteration directories if they are confident they don't need the trace. The skill picks up from `max(existing_iteration_NNN) + 1` regardless of gaps.

---

## Size expectations

Per iteration, typical sizes:
- `fleet-outputs/` aggregate: ~50-200 KB (depends on finding count + evidence verbosity)
- `meta-judge-output.yaml`: ~20-50 KB
- `impl-snapshot.txt`: project-dependent; can be hundreds of KB to a few MB
- `screenshots/`: 0 to a few MB depending on e2e coverage

A typical feature with 4 iterations produces a `ratchet-log/` in the 5-20 MB range. Worth keeping in version control IF the team uses it as training data; otherwise gitignore and treat as ephemeral.
