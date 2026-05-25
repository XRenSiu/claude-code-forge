# meta-judge-protocol.md — synthesis-only, no re-review

The meta-judge is the single point that consolidates all 8 evaluator outputs (plus rebuttals) into a state decision. It is also the most failure-prone component if it strays from its remit. This document operationalizes the four actions meta-judge may take and the hard wall on everything else.

## The hard wall (iron rule 6, restated)

Meta-judge MUST NOT:
- Read implementation source files itself.
- Re-grade an evaluator's verdict by independently looking at the code.
- Form opinions about specific findings beyond "what does the evidence support".
- Spawn additional evaluators or re-prompt existing ones.

Meta-judge MAY ONLY:
1. **Dedupe** — collapse findings that reference the same `file:line + root_cause`.
2. **Weight** — boost confidence on multi-source / cross-vendor agreement, penalize single-source / same-vendor.
3. **Arbitrate** — when two findings contradict on the same `file:line`, decide based on evidence strength (NOT vote count).
4. **Classify** — apply the four-state ratchet rules to emit a decision.

Anything else is an iron-rule-6 violation. The moment meta-judge starts forming its own view of "is this code actually buggy", it stops being a judge and becomes a sycophantic super-reviewer.

---

## Action 1 — Dedupe

Two findings are duplicates iff:
- They reference the same `file` AND overlapping `line_range` (any overlap counts).
- AND their `root_cause` is semantically equivalent (the *thing* being reported, not the *wording*).

Algorithm:
1. Bucket all surviving findings (post-rebuttal) by `file` field.
2. Within each bucket, cluster by `line_range` overlap.
3. Within each cluster, compare `root_cause` text. Use an LLM call only for semantic equivalence; literal substring match is the fast path.
4. Merge clusters into `merged_findings`. Each merged finding records its source finding IDs.

A merged finding's `synthesized_severity` is the max severity among its sources (P0 > P1 > P2 > P3). A merged finding's `synthesized_root_cause` is the longest of the source root_causes (most detailed) — do NOT paraphrase; pick one verbatim.

## Action 2 — Weight

For each merged finding:

```
base_confidence = 0.5 (default)
+ 0.2 per additional distinct source role (capped at +0.4)
+ 0.2 per cross-vendor source (capped at +0.2)
- 0.2 if only one source AND single-vendor
- 0.3 if the originating evaluator self-reported low confidence in the finding
```

Resulting `confidence` in [0.0, 1.0]. Cross-vendor multi-source findings (3+ roles, 2+ vendors) routinely hit 0.9+; single-source single-vendor low-confidence findings hover at 0.0-0.2 and are usually dropped at action 4.

`confidence_boost` is the delta from the per-finding baseline — useful for explaining the synthesized confidence to the user. Record both fields in the output.

## Action 3 — Arbitrate

Conflicts are findings on the same `file:line` with contradictory verdicts (one says "bug here", another says "behavior correct" or "no issue").

Process:
1. Compare evidence on both sides:
   - Reproduction scenarios with concrete inputs > abstract claims.
   - Multi-step traces > single-line observations.
   - Cross-vendor support > same-vendor support.
2. If one side is clearly stronger, take that side; the loser is moved to `rebutted_findings:` with `arbitrated: true` flag.
3. If both sides have comparable evidence, classify as `NEEDS_HUMAN` — meta-judge does NOT decide. Surface the conflict to the user verbatim.

**Voting is forbidden.** Three roles saying "bug" and one saying "no bug" with a stronger reproduction is decided FOR no-bug. Evidence quality > evaluator count.

## Action 4 — Classify (four-state ratchet + NEEDS_HUMAN escape)

In strict order — check the conditions top to bottom, stop at first match.

### A. `NEEDS_HUMAN` (escape hatch)
Triggered when:
- Any conflict from action 3 ended in "comparable evidence, cannot decide".
- `requirement-tracer` reported `requires_human_verification` on any REQ.
- Cross-vendor evaluators disagreed on a P0/P1 finding (independent of arbitration result).

This bypasses the four-state machine and asks the user the specific question(s). The skill does NOT end — it waits for user input, folds the answer in, and re-runs action 4.

### B. `GAMING_RISK`
Triggered when:
- `spec-gaming-detector.gaming_risk_score >= 7`, OR
- `gaming_risk_score` grew monotonically by ≥ 2 per iteration for 2+ iterations (trend escalation), OR
- A `surfaced_vector` from `spec-robustness.md` was triggered AND the same vector triggered in the previous iteration (chronic vector).

Action: emit `gaming-risk-report.md`. Do NOT generate a fix-prompt — the impl agent gaming the contract means the contract is the problem, not the impl. Return control to `/acceptance-spec`.

### C. `SPEC_DRIFT`
Triggered when:
- PBT counterexamples consistent with the literal REQ text recurred across `SPEC_DRIFT_TRIGGER` iterations (default 3 from `spec_drift_threshold.max_fix_loops_before_escalation`), OR
- A `requirement-tracer` finding of "not_compliant" on a REQ recurred across 3+ iterations despite the impl changing each iteration (the spec wording is internally contradictory).

Action: emit `spec-drift-report.md`. Do NOT generate a fix-prompt. Return control to `/acceptance-spec`.

### D. `DONE`
Triggered when ALL of:
- `test-runner.run_report` shows all layers passing.
- All `done_when.yaml.behavior.thresholds:` met.
- All `existence-checker.existence_checks` are `pass`.
- `requirement-tracer.per_req_compliance` is `fully_compliant` for every REQ (or `requires_human_verification` with an explicit user OK from a prior `NEEDS_HUMAN` cycle).
- `gaming_risk_score < 3`.
- No blocking merged finding with `synthesized_severity` ∈ {P0, P1}.

Action: end the loop. No state-specific report needed.

### E. `FIX` (default)
Anything else. Generate `fix-prompt.md` from blocking findings.

---

## Output schema (meta-judge-output.yaml)

```yaml
meta_judge:
  iteration: <int>
  duration_seconds: <int>
  state_decision: DONE | FIX | SPEC_DRIFT | GAMING_RISK | NEEDS_HUMAN

  threshold_evaluation:
    - threshold: <text>
      actual: <value>
      passed: <bool>
    - ...

  deduplicated_findings:
    - merged_finding_id: mf-001
      sources:
        - { role: <role>, finding_id: <id>, vendor: <vendor> }
      confidence_boost: <float>          # +0.0 to +0.6
      synthesized_severity: <P0|P1|P2|P3>
      issue: <text>                      # one-sentence summary
      blocking: <bool>

  rebutted_findings:
    - { role: <role>, finding_id: <id>, rebutter: <role>, rebuttal_summary: <text>, arbitrated: <bool> }

  conflict_arbitration:
    - between: [<role-a-finding-id>, <role-b-finding-id>]
      on: <file>:<line>
      verdict: <chosen-side> | needs_human
      reasoning: <text>

  needs_human_items:
    - question: <text>
      surfaced_by: <role>
      blocking: <bool>

  fix_prompt_basis:                      # only populated when state_decision = FIX
    - <merged_finding_id>
    - ...

  spec_drift_counter: <int>              # how many consecutive iterations the same drift signal has appeared
  gaming_risk_score: <int>               # this iteration's score, 0-10
  gaming_risk_trajectory: [<int>, ...]   # last 5 iterations' scores for trend analysis

  notes: |
    <free-form context for the human reader — anything worth flagging that
    doesn't fit a structured field>
```

---

## Common failure modes and their fixes

### "Meta-judge keeps emitting NEEDS_HUMAN for the same issue"
Meta-judge is correctly refusing to decide an ambiguous conflict. The fix is upstream: rewrite the relevant REQ to remove the ambiguity (return to `/acceptance-spec`).

### "Meta-judge is dropping findings I expected to see"
Check the rebuttal pass — most "missing" findings are findings that got rebutted in S2. If a rebutter is too aggressive (rebuts findings that should stand), the rebuttal pass needs tightening, not the meta-judge.

### "Meta-judge is taking too long"
Dedupe is the expensive step (semantic equivalence between root_causes). Cache root_cause embeddings within the iteration if running >50 findings total. Don't sacrifice the dedupe — without it, the fix-prompt has redundant items and the impl agent thrashes.

### "Meta-judge's classification doesn't match my intuition"
Read the rules top to bottom — classification is strict ordering. If your intuition says "this should be DONE", check the gaming_risk_score and the requirement-tracer per-REQ compliance; usually one of those is the blocker. If classification feels truly wrong, the rules need updating — not the per-run output.
