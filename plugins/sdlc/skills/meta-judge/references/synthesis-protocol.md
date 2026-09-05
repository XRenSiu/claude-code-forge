# synthesis-protocol.md — operational detail of the 4 actions

The meta-judge is the single point that consolidates all review outputs into a state decision. It is also the most failure-prone component if it strays from its remit. This document operationalizes the four actions and the hard wall on everything else.

## The hard wall (iron rule 1, restated)

Meta-judge MUST NOT:
- Read implementation source files itself, except sparingly for evidence verification on a *contested* finding during arbitration (M3).
- Re-grade an evaluator's verdict by independently looking at the code.
- Form opinions about specific findings beyond "what does the evidence support".
- Spawn additional evaluators or re-prompt existing ones.
- "Helpfully" add observations not present in any source review.

Meta-judge MAY ONLY:
1. **Dedupe** — collapse findings that reference the same `file:line + root_cause`.
2. **Weight** — boost confidence on multi-source / cross-vendor agreement; penalize single-source / same-vendor.
3. **Arbitrate** — when two findings contradict on the same `file:line`, decide based on evidence strength (NOT vote count).
4. **Classify** — apply the rules-source to emit PASS / BLOCK_MERGE / NEEDS_HUMAN.

Anything else violates the hard wall.

---

## Action 1 — Dedupe

Two findings are duplicates iff:
- They reference the same `file:` AND overlapping `line_range:` (any overlap counts).
- AND their `root_cause:` is semantically equivalent (the *thing* being reported, not the *wording*).

### Algorithm

1. Bucket all surviving findings by `file:` field.
2. Within each file bucket, cluster by `line_range:` overlap.
3. Within each cluster, compare `root_cause:` text:
   - **Fast path**: literal substring match in either direction → duplicate.
   - **Slow path**: single LLM call per cluster, prompt: "Are these N findings reporting the same underlying issue, or different issues that happen to coincide at the same file:line? Reply yes/no with one-sentence rationale." — no tool calls in this LLM call.
4. Merge each cluster into a `merged_finding`:
   - `merged_finding_id: mf-NNN` (sequential)
   - `sources:` list with original `{role, finding_id, vendor}` records
   - `synthesized_severity:` = max severity among sources (P0 > P1 > P2 > P3)
   - `synthesized_root_cause:` = the longest of the source root_causes verbatim (most detailed)
   - `confidence_boost: 0.0` (filled in by Action 2)

### Pitfalls

- **Different file:line, same conceptual bug** is NOT a duplicate. Two reviewers might flag "this race condition" at different but related lines — keep them as separate findings unless line_ranges overlap.
- **Paraphrasing is forbidden.** Pick the verbatim longest source root_cause; never write your own summary. The source is the audit trail.
- **Severity collision.** If three sources report the same finding with severities P0/P1/P2, the merged finding is P0. Do not average.

---

## Action 2 — Weight

For each `merged_finding`:

```
base_confidence = 0.5

+ 0.2 per additional distinct source role (cap at +0.4)
   # e.g. code-reviewer + qa-reviewer + pm-reviewer = +0.4
+ 0.2 per additional vendor (cap at +0.2)
   # e.g. Claude + Codex (or Claude + Gemini) = +0.2; 3+ vendors caps at +0.2
- 0.2 if single-source AND single-vendor
- 0.3 if originating evaluator self-reported `confidence: low`
+ 0.1 if originating evaluator self-reported `confidence: high`
   # (only when evaluator's confidence field is populated; many won't have it)
```

Resulting `confidence ∈ [0.0, 1.0]`.

### Typical confidence values

| Pattern | Resulting confidence |
|---|---|
| 3+ roles, 2+ vendors, all high-confidence | 0.9 - 1.0 |
| 2 roles, 1 vendor | 0.7 |
| 1 role, 1 vendor, high confidence | 0.6 |
| 1 role, 1 vendor, medium confidence | 0.5 |
| 1 role, 1 vendor, low confidence | 0.0 - 0.2 |

### confidence_boost vs confidence

Both fields appear in the merged_finding output:
- `confidence` is the absolute number in [0, 1].
- `confidence_boost` is the delta from baseline 0.5 — useful for explaining "this finding got a boost because cross-vendor agreed."

Record both. The boost field is what makes the synthesis explainable to the user.

### Cross-vendor weighting matters

Per HTML §2 theory β + the Milvus benchmark: Claude + Gemini caught 91% of bugs found by a 5-vendor ensemble. Two vendors > five same-vendor instances. The `+ 0.2 per additional vendor` term is the synthesis-time encoding of that finding.

### When confidence is below a sensible threshold

Findings with final `confidence < 0.3` are typically dropped during M4 (classify) unless the rules explicitly require evaluating them. The threshold is implicit, not configurable — if the user wants different behavior, the rules source can use explicit `min_confidence: 0.5` syntax.

---

## Action 3 — Arbitrate

Conflicts are findings on the same `file:line` with contradictory verdicts (one says "bug here", another says "behavior correct" or "no issue").

### Process

1. Compare evidence on both sides:
   - Reproduction scenarios with concrete inputs > abstract claims.
   - Multi-step traces > single-line observations.
   - Cross-vendor support > same-vendor support.
   - Tool-traces support (LOCATE/READ/RETRIEVE from `/pm-reviewer`) > inference-only.
   - Test output evidence (from `/qa-reviewer`) > static analysis.
2. If one side is clearly stronger, take that side. Move the loser to `rebutted_findings:` with `arbitrated: true` flag.
3. If both sides have comparable evidence:
   - You MAY make one `read_file` call (per iron rule 9) to look at the contested file:line for **evidence verification only**, not for re-judgment. If the read makes the resolution clear without forming your own opinion (e.g. one side said "this is the impl" and the other said "this is a comment" — the file shows literally which is right), apply that resolution.
   - Otherwise classify as `NEEDS_HUMAN` — meta-judge does NOT decide. Surface the conflict verbatim.

**Voting is forbidden.** Three roles saying "bug" and one saying "no bug" with a stronger reproduction is decided FOR no-bug. Evidence quality > evaluator count.

### What counts as "comparable evidence"

Subjective threshold, but the heuristic:
- Both sides have reproduction scenarios → comparable, weight by reproduction quality.
- Both sides cite the same evidence type (e.g. both static reads) → comparable.
- One side has runtime evidence (qa-reviewer test failure) and the other has static-only → NOT comparable; runtime wins.
- One side has cross-vendor support and the other is single-vendor → NOT comparable; cross-vendor wins.

### 4-Eyes Principle inside arbitration

If the conflict is between a finding F1 (originator: role-A) and a rebuttal F2 (originator: role-B that previously rebutted F1), and F2 is itself contested by F3 from role-A — there's a circular rebuttal pattern that violates 4-Eyes. Surface as `NEEDS_HUMAN` with the cycle made explicit in the audit trail; do not silently let the cycle close.

---

## Action 4 — Classify (final state machine)

Apply rules-source to surviving (deduped, weighted) findings. For each rule:

1. **Rule fires** (condition matches a finding) → record `triggered_by: <merged_finding_id>` plus the rule's effect.
2. **Rule passes** (condition does not match) → record `passed: true` for the audit trail.
3. **Rule cannot be evaluated** (would require code re-reading or external resource the rules source assumed) → record `cannot_evaluate: <reason>` and treat as `NEEDS_HUMAN` for that rule's domain.

After rule application, classify in strict order (first match wins):

### A. `NEEDS_HUMAN` (escape hatch)

Triggered when any of:
- Any conflict from action 3 ended in "comparable evidence, cannot decide".
- Any `pm-reviewer` finding has `verdict: requires_human_verification`.
- Cross-vendor evaluators disagreed on a P0/P1 finding (independent of arbitration result).
- A rule cannot be evaluated (requires data not present in any review).

Skill output ends with state `NEEDS_HUMAN`; the user (or upstream orchestrator like `/acceptance-fleet`) is expected to provide additional input.

### B. `BLOCK_MERGE`

Triggered when:
- Any rule with `severity: blocking` fires.
- Aggregate severity policy violated (e.g. rule says "no P0 findings"; a P0 survived).
- A non-blocking rule fires with a context flag (e.g. `--context` says `is_hotfix: false` AND a "minor refactor risk" rule fires).

### C. `PASS`

All other cases:
- All rules pass.
- No blocking findings.
- No unresolved NEEDS_HUMAN items.

---

## Default rules (when rules source is empty or unparseable)

If `--rules` is provided but the source yields zero parseable rules, meta-judge falls back to these defaults:

1. `any P0 finding blocks merge` — severity: blocking, applies_to: any-reviewer
2. `any P1 from pm-reviewer with verdict: not_compliant blocks merge` — severity: blocking
3. `qa-reviewer decision: NO-GO blocks merge` — severity: blocking
4. `spec-gaming-detector.gaming_risk_score >= 7 blocks merge` — severity: blocking
5. `pm-reviewer requires_human_verification on critical REQ → NEEDS_HUMAN` — severity: needs-human

These are deliberately conservative — better to over-block than under-block in default mode. The user is encouraged to provide explicit rules to tune.

---

## Output discipline

The output of M5 is `meta-judge-output.yaml` (or `final-verdict.yaml` for the standalone use case — same content, different filename per consumer). Every action you took is recorded:

- `deduplicated_findings:` — every merged_finding with full source provenance.
- `rebutted_findings:` — what got dropped during dedupe + arbitration, with rebutter and rationale.
- `conflict_arbitration:` — every conflict that went through M3 with the winning side + reasoning.
- `needs_human_items:` — every NEEDS_HUMAN question with the specific reason.
- `rules_evaluation:` — every rule's outcome.
- `state_decision:` — the final state.

The audit trail is the contract. The downstream consumer (user reading the report, `/acceptance-fleet` deciding the next ratchet state) reads ANY of these fields to understand how the decision was made. Do not truncate. Do not summarize. Verbatim is the contract.

---

## Common failure modes

### "Meta-judge keeps emitting NEEDS_HUMAN for the same issue across iterations"

Meta-judge is correctly refusing to decide an ambiguous conflict. The fix is upstream: rewrite the relevant REQ to remove the ambiguity (return to `/acceptance-spec`), or improve evidence on one side of the conflict.

### "Meta-judge is dropping findings I expected to see"

Check the dedupe log — most "missing" findings are findings that got dedup-merged with another. Look in `deduplicated_findings:` for the merged version. If a finding truly disappeared, it likely fell below the `confidence < 0.3` implicit threshold; check whether the source review reported it with low confidence.

### "Meta-judge took too long"

Dedupe is the expensive step (semantic equivalence between root_causes). Cache root_cause embeddings within the iteration if running >50 findings total. Don't sacrifice the dedupe — without it, downstream consumers thrash on redundant items.

### "Meta-judge's classification doesn't match my intuition"

Read the rules-evaluation section — classification is strict ordering. If your intuition says "this should be PASS", check whether a rule fired that you didn't expect. Often a default rule is the culprit; provide explicit `--rules` to override.
