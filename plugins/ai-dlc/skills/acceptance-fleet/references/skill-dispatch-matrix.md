# skill-dispatch-matrix.md — v0.x role → v1.0+ skill mapping

This is the operational table for S1 (dispatch fleet). It says: which sub-skill to invoke, with what arguments, on which model / vendor, and where the output lands. It also documents the migration mapping from v0.x roles to v1.0+ skill invocations for users updating from the old monolithic fleet.

---

## v0.x → v1.0+ migration table

| v0.x role (embedded in old SKILL.md) | v1.0+ skill invocation |
|---|---|
| `test-runner` (Haiku, programmatic) | `/qa-reviewer` (its L2-L5 layers cover this) |
| `existence-checker` (Haiku) | `/qa-reviewer` (its L1 layer covers this) |
| `requirement-tracer` (Opus + LOCATE/READ/RETRIEVE) | `/pm-reviewer` (Agent-as-Judge paradigm — direct match) |
| `design-reviewer` (Opus → Sonnet) | merged into `/code-reviewer --focus=logic` + `/pm-reviewer` (intent vs literal split between them) |
| `adversarial-reviewer` (cross-vendor) | `/code-reviewer --focus=security --adversarial` (with cross-vendor preference) |
| `edge-case-hunter` (Opus) | merged into `/code-reviewer --focus=logic` (edge-case hunting is part of logic review now) |
| `e2e-explorer` (Opus + Playwright) | `/qa-reviewer` L4 with Playwright MCP |
| `spec-gaming-detector` (Opus + git_diff) | `/spec-gaming-detector` (extracted as standalone skill, same content + diff mode protocol) |
| `meta-judge` (S3 phase) | `/meta-judge` (extracted as standalone skill) |

A new skill `/spec-drift-detector` was added in v1.0+; it didn't have a v0.x equivalent (drift was detected indirectly via the SPEC_DRIFT ratchet state recurrence pattern).

---

## Before the matrix: derive the parameters, do not type them

Every `$PREV_*` and every threshold below comes from one call, made once at S0:

```bash
eval "$(scripts/next_iteration.py "$RATCHET_LOG" "$N" --done-when "$SPEC_DIR/done_when.yaml")"
```

It sets `ITER_DIR`, `PREV_ITER_DIR`, `PREV_SNAPSHOT`, `PREV_GAMING_SCORE`, `PREV_QA_REPORT`,
`PREV_PM_REVIEW`, `GAMING_TRAJECTORY`, `GAMING_DONE_BELOW`, `GAMING_BLOCK_AT`, `PREV_GAMING_BAND`,
`SPEC_DRIFT_TRIGGER`, `BASELINE_DISCREPANCY`. Missing values come back empty so `${VAR:+--flag="$VAR"}`
omits the flag; exit 1 means the predecessor is missing or the configured band is empty — stop, do not
dispatch (iron rule 6).

This exists because iteration-003 of the sdlc-ring-audit run was handed `--baseline-score 3.5` when
iteration-002 had produced 4.0: the task file was made by editing the previous one, and the sed moved the
label but not the number. Reading both the value and its path from the same place makes that class of edit
impossible. Save the script's stdout as `$ITER_DIR/dispatch-params.sh`.

---

## v1.0+ dispatch matrix

The orchestrator spawns 7 sub-skill calls per iteration (3 code-reviewer focuses + 4 other skills). Always in parallel.

### `/code-reviewer --focus=security --adversarial`

**Always invoke** — security is the highest-impact focus.

```bash
/code-reviewer "$IMPL_DIFF_OR_REF" \
  --focus=security \
  --adversarial \
  --rules="$SPEC_DIR/CLAUDE.md"  # if exists, else omit
```

| Setting | Value |
|---|---|
| Output → | `ratchet-log/iteration-NNN/fleet-outputs/code-reviewer-security.yaml` |
| Model (strong isolation) | **Codex GPT-5 or Gemini Pro 3 (cross-vendor)** |
| Model (medium isolation) | Claude Opus 4.7 |
| Model (weak isolation) | Claude Opus 4.7 (with caveat) |
| Tool budget | 20 calls |

### `/code-reviewer --focus=logic`

**Always invoke** — logic is where most non-security bugs live.

```bash
/code-reviewer "$IMPL_DIFF_OR_REF" \
  --focus=logic \
  --rules="$SPEC_DIR/CLAUDE.md"
```

| Setting | Value |
|---|---|
| Output → | `code-reviewer-logic.yaml` |
| Model | Claude Opus 4.7 |
| Tool budget | 20 calls |

### `/code-reviewer --focus=perf` (skip on hotfix)

**Invoke unless** `--context.is_hotfix == true` (hotfix PRs deprioritize perf review for speed).

```bash
/code-reviewer "$IMPL_DIFF_OR_REF" \
  --focus=perf
```

| Setting | Value |
|---|---|
| Output → | `code-reviewer-perf.yaml` |
| Model | Claude Sonnet 4.6 (cheaper; perf signals are pattern-recognition) |
| Tool budget | 15 calls |

### `/qa-reviewer`

**Always invoke** — test execution is non-negotiable.

```bash
/qa-reviewer "$SPEC_DIR/tests/" \
  --thresholds="$SPEC_DIR/done_when.yaml" \
  ${PREV_QA_REPORT:+--baseline="$PREV_QA_REPORT"} \
  --output="$ITER_DIR/fleet-outputs/qa-reviewer.yaml"

# then project the report down to measurements — this file, not the report, is what drift may read
scripts/qa_facts.py "$ITER_DIR/fleet-outputs/qa-reviewer.yaml" \
  --output="$ITER_DIR/fleet-outputs/qa-measurements.yaml"
```

| Setting | Value |
|---|---|
| Output → | `qa-reviewer.yaml` |
| Main model | Claude Sonnet 4.6 |
| Classifier model | Claude Haiku 4.5 |
| Layers | all (existence/unit/integration/e2e/mutation) unless `--layers` overridden |
| Wall clock | typically 2-10 min depending on test count + mutation |

### `/pm-reviewer`

**Always invoke** — compliance check is core to acceptance.

```bash
/pm-reviewer "$SPEC_DIR/spec.md" "$IMPL_ROOT" \
  --severity-marks="<critical_req_ids>" \
  ${PREV_PM_REVIEW:+--prev-review="$PREV_PM_REVIEW"} \
  --output="$ITER_DIR/fleet-outputs/pm-reviewer.yaml"
```

| Setting | Value |
|---|---|
| Output → | `pm-reviewer.yaml` |
| Model | Claude Opus 4.7 (reasoning + tool use heavy) |
| Tool budget | 20 calls per REQ |

### `/spec-drift-detector`

**Invoke from iteration 2 onward** (no baseline in iteration 1; drift detection needs history). For iteration 1, write a placeholder that says so — `skipped: no baseline before iteration 2` plus `signals: []` — and proceed. A placeholder with an empty findings list and nothing else is indistinguishable from a drift detector that ran and found nothing, which is the confusion S1.5 exists to prevent; `skipped:` is a declaration, silence is not.

```bash
/spec-drift-detector "$SPEC_DIR/spec.md" "$IMPL_ROOT" \
  --history-depth=100 \
  --qa-measurements="$ITER_DIR/fleet-outputs/qa-measurements.yaml" \
  --output="$ITER_DIR/fleet-outputs/spec-drift-detector.yaml"
```

**Never `--qa-report`.** Passing `qa-reviewer.yaml` here is what broke iron rule 2 and got recorded as an
isolation breach in the sdlc-ring-audit run: it hands the drift detector qa's findings, severities and
GO/NO-GO decision while drift is still forming its own opinion. `scripts/qa_facts.py` projects the report
down to its measurements — counts, coverages, durations, layers run, mutation totals — and refuses to
write a file that still carries `decision`, `decision_reasons`, `findings`, `num_findings`,
`maintenance_issues`, `regressions`, `caveats` or a surviving mutant's `hint`. Facts cross the wall;
judgments do not. `qa_facts.py --check <file>` re-verifies any file before it is passed on.

| Setting | Value |
|---|---|
| Output → | `spec-drift-detector.yaml` |
| Model | Claude Opus 4.7 |
| Dependencies | `/qa-reviewer` must complete first, then `qa_facts.py` — the measurement projection is the dependency, not the report. The orchestrator can still spawn drift in parallel; it waits for `qa-measurements.yaml` to appear via filesystem polling. |
| Isolation | measurements only. A drift finding citing this file counts as ONE source at `/meta-judge` (qa and drift reading the same number is shared input, not corroboration); a drift finding citing a qa *finding* or verdict is an isolation breach, because the projection makes it impossible to obtain honestly. |

### `/spec-gaming-detector`

**Always invoke** — gaming check is the contract's anti-reward-hacking shield.

```bash
/spec-gaming-detector "$SPEC_DIR/spec.md" "$IMPL_ROOT" \
  ${SPEC_ROBUSTNESS:+--spec-robustness="$SPEC_DIR/spec-robustness.md"} \
  ${PREV_SNAPSHOT:+--history="$PREV_SNAPSHOT"} \
  ${PREV_GAMING_SCORE:+--baseline-score="$PREV_GAMING_SCORE"} \
  --output="$ITER_DIR/fleet-outputs/spec-gaming-detector.yaml"
```

| Setting | Value |
|---|---|
| Output → | `spec-gaming-detector.yaml` |
| Model (strong isolation) | **Codex GPT-5 or Gemini Pro 3 (cross-vendor)** |
| Model (medium/weak isolation) | Claude Opus 4.7 |
| `--history` | `$PREV_SNAPSHOT`, empty before iteration 2 |
| `--baseline-score` | `$PREV_GAMING_SCORE` — read from iteration N-1's own `spec-gaming-detector.yaml`, never copied from a task template |
| `--spec-robustness` | provided if `spec-robustness.md` exists |

---

## After all 7 sub-skills complete, before /meta-judge

Run the completeness gate (S1.5 of the orchestrator's phase map). Every output above must carry a
`review_complete:` block; this is what decides whether the dispatch produced verdicts at all.

```bash
python3 scripts/verify_review_complete.py "$ITER_DIR/fleet-outputs/" \
  --size "$SIZE" \
  --out "$ITER_DIR/review-completeness.yaml"
```

| Setting | Value |
|---|---|
| Output → | `review-completeness.yaml` (iteration root, not `fleet-outputs/`) |
| Model | none — this is a script, and that is the point: the judgement "did this review finish" must not itself be a review |
| Exit | 0 all complete → run `/meta-judge` · 1 an explicit `incomplete` · 3 missing / unparseable / unmarked / `findings_count` disagreement · 2 usage |
| On 1 or 3 | `--clear` the offending output (it moves to `fleet-outputs/stale/`), re-dispatch **that one review only** with the same arguments this matrix gives it, re-run the gate. At most one re-dispatch per review per iteration; a second failure is recorded and forces S3 rule A0 |

The expected set follows the dispatch above: `--size M` is `qa-reviewer` + `spec-gaming-detector`,
`--size L` is all seven. When `--skip` narrowed the dispatch, pass the actual set with
`--expect a,b,c` — the suppressed skills' `{skipped: user_requested}` files still satisfy the gate,
because a declared omission is not a silent truncation.

## Then run /meta-judge

Run `/meta-judge` (S2 of the orchestrator's phase map):

```bash
/meta-judge "$ITER_DIR/fleet-outputs/" \
  --rules="$SPEC_DIR/done_when.yaml" \
  --context="$CONTEXT_JSON" \
  --output="$ITER_DIR/meta-judge-output.yaml"
```

`$CONTEXT_JSON` carries the one declared shared input so meta-judge can weight it without guessing:

```json
{"feature": "<name>", "iteration": 3, "is_hotfix": false,
 "shared_inputs": [{"from": "qa-reviewer", "to": "spec-drift-detector",
                    "file": "fleet-outputs/qa-measurements.yaml", "kind": "measurements_only"}]}
```

| Setting | Value |
|---|---|
| Output → | `meta-judge-output.yaml` |
| Model | Claude Opus 4.7 (always — meta-judge never uses weaker) |
| Tool budget | 5 reads (M3 evidence verification only) |

---

## Parallelism notes

The 7 sub-skill calls launch simultaneously. The orchestrator:

1. Spawns all 7 with their respective commands.
2. Polls `fleet-outputs/` for completion of each.
3. Once all 7 are present (or marked `skipped:`), invokes `/meta-judge`.

`/spec-drift-detector` has a soft dependency on `/qa-reviewer` (it uses qa's measurements for measurement-backed non-functional drift). The orchestrator can either:
- (a) Spawn drift detector at the end, after qa completes and `qa_facts.py` has written the projection (sacrifices a bit of parallelism for cleaner data flow).
- (b) Spawn all 7 in parallel and have drift detector wait for `qa-measurements.yaml` to appear via filesystem polling.

Default behavior is (b) for max parallelism. If you see drift-detector running before qa, that's expected — it'll pause until `qa-measurements.yaml` shows up. It waits for the projection, never for `qa-reviewer.yaml`: if the raw report is what appears first, that is a wiring bug, not an early start.

---

## Wall-clock expectations

| Phase | Time (typical) | Time (slow) |
|---|---|---|
| S0 bootstrap | <5s | <30s |
| S1 dispatch (parallel, gated by slowest skill) | 3-8 min | 20+ min (mutation testing) |
| S2 meta-judge | 30-60s | 2 min |
| S3-S5 ratchet + persist | <30s | 1 min |

Per-iteration total: 4-10 minutes typical, up to 25 minutes for the first iteration when mutation testing runs against a fresh codebase.

---

## Skipping sub-skills

The user can suppress sub-skills via:

```bash
/acceptance-fleet "$SPEC_DIR/" --skip=spec-drift-detector,code-reviewer-perf
```

Suppressed skills emit `<skill>.yaml` with `{skipped: user_requested, findings: []}` — the `skipped:` key is what the S1.5 completeness gate reads to tell a declared omission from a truncated run, so a suppressed skill must still write its file. `/meta-judge` proceeds with the available subset; the resulting `final_verdict.caveats.suppressed_skills:` lists what was skipped.

Don't suppress `/qa-reviewer` or `/pm-reviewer` — those are the contract's load-bearing checks. The orchestrator refuses if either is in the skip list.
