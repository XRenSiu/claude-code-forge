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
  --baseline="<prev iteration>/qa-reviewer.yaml" \
  --output="$ITER_DIR/fleet-outputs/qa-reviewer.yaml"
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
  --prev-review="<prev iteration>/pm-reviewer.yaml" \
  --output="$ITER_DIR/fleet-outputs/pm-reviewer.yaml"
```

| Setting | Value |
|---|---|
| Output → | `pm-reviewer.yaml` |
| Model | Claude Opus 4.7 (reasoning + tool use heavy) |
| Tool budget | 20 calls per REQ |

### `/spec-drift-detector`

**Invoke from iteration 2 onward** (no baseline in iteration 1; drift detection needs history). For iteration 1, output a placeholder file with `findings: []` and proceed.

```bash
/spec-drift-detector "$SPEC_DIR/spec.md" "$IMPL_ROOT" \
  --history-depth=100 \
  --qa-report="$ITER_DIR/fleet-outputs/qa-reviewer.yaml" \
  --output="$ITER_DIR/fleet-outputs/spec-drift-detector.yaml"
```

| Setting | Value |
|---|---|
| Output → | `spec-drift-detector.yaml` |
| Model | Claude Opus 4.7 |
| Dependencies | `/qa-reviewer` must complete first (perf evidence comes from there) — but the orchestrator can still spawn in parallel; spec-drift-detector waits for qa-reviewer's output via filesystem polling. |

### `/spec-gaming-detector`

**Always invoke** — gaming check is the contract's anti-reward-hacking shield.

```bash
/spec-gaming-detector "$SPEC_DIR/spec.md" "$IMPL_ROOT" \
  ${SPEC_ROBUSTNESS:+--spec-robustness="$SPEC_DIR/spec-robustness.md"} \
  ${PREV_SNAPSHOT:+--history="$PREV_ITER_DIR/impl-snapshot.tar.gz"} \
  ${PREV_GAMING_SCORE:+--baseline-score="$PREV_GAMING_SCORE"} \
  --output="$ITER_DIR/fleet-outputs/spec-gaming-detector.yaml"
```

| Setting | Value |
|---|---|
| Output → | `spec-gaming-detector.yaml` |
| Model (strong isolation) | **Codex GPT-5 or Gemini Pro 3 (cross-vendor)** |
| Model (medium/weak isolation) | Claude Opus 4.7 |
| `--history` | provided from iteration 2 onward |
| `--spec-robustness` | provided if `spec-robustness.md` exists |

---

## After all 7 sub-skills complete

Run `/meta-judge` (S2 of the orchestrator's phase map):

```bash
/meta-judge "$ITER_DIR/fleet-outputs/" \
  --rules="$SPEC_DIR/done_when.yaml" \
  --context="$CONTEXT_JSON" \
  --output="$ITER_DIR/meta-judge-output.yaml"
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

`/spec-drift-detector` has a soft dependency on `/qa-reviewer` (uses its qa-report for measurement-backed non-functional drift). The orchestrator can either:
- (a) Spawn drift detector at the end, after qa completes (sacrifices a bit of parallelism for cleaner data flow).
- (b) Spawn all 7 in parallel and have drift detector wait for qa-report.yaml to appear via filesystem polling.

Default behavior is (b) for max parallelism. If you see drift-detector running before qa, that's expected — it'll pause until qa-report.yaml shows up.

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

Suppressed skills emit `<skill>.yaml` with `{skipped: user_requested, findings: []}`. `/meta-judge` proceeds with the available subset; the resulting `final_verdict.caveats.suppressed_skills:` lists what was skipped.

Don't suppress `/qa-reviewer` or `/pm-reviewer` — those are the contract's load-bearing checks. The orchestrator refuses if either is in the skip list.
