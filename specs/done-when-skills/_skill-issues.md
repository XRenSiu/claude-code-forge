# done-when-pipeline skill self-validation — issue log

Run: 2026-05-24, Round 1
Method: dogfooding — use the two skills' own source to verify themselves
Source-of-truth doc: `/Users/xrensiu/Documents/Downloads/done-when-pipeline.md`

---

## Round 1 issues

Logged as discovered. Format: severity / where / what / why-it-matters / proposed-fix.

### ISSUE-001 — [skill source] acceptance-spec/SKILL.md: clarify-tag taxonomy introduced too late

**Severity:** medium
**Where:** `plugins/done-when-pipeline/skills/acceptance-spec/SKILL.md` §S1 and §S2
**Found in:** S1 of round 1 (writing the draft for the meta-self-verification feature)

**What:** S1 says "read `references/ears-syntax.md` once before writing" but does not mention `clarify-protocol.md`. The 3-tag taxonomy (`[ambiguity]` / `[missing edge]` / `[undefined term]`) is the gate for whether a `[?]` question is legal to ask, and S1 already generates the open-questions list — so the runner needs the taxonomy at S1 time, not S2 time.

**Why it matters:** when I ran S1 honestly, I had to pre-tag questions ahead of when the skill formally said the rule applies. A Claude that follows SKILL.md literally would emit untagged questions at S1 end, then have to re-tag them at S2 start (waste) or get them rejected at the round-1 send (worse — bad UX).

**Proposed fix:** in SKILL.md S1 step "before writing", add `clarify-protocol.md` to the must-read list. Or fold the 3-tag rule into SKILL.md body so it's available everywhere.

---

### ISSUE-002 — [integration claim, CONFIRMED] INTEGRATION.md describes a ratchet integration that does not exist

**Severity:** high
**Where:** `plugins/done-when-pipeline/INTEGRATION.md` §"Handoff: test-suite-generator → ratchet" + §"Spec-drift bailout"
**Found in:** S2 Q16 resolution; **verified by reading** `plugins/ratchet/skills/ratchet/SKILL.md`

**What (confirmed):** ratchet does NOT consume `done_when.yaml` directly. Its actual interface:
- Input: natural-language `Goal` + `Criteria` + `Scope`
- It writes its own `ratchet.md` (master prompt) + `evaluate.sh` (or `evaluate_criteria.md`) + `test_data/`
- Its `done_when:` block uses a different schema: `{success, convergence, budget}` — three termination conditions, ANY of which triggers stop.
- It does NOT read or honor a `spec_drift_threshold.max_fix_loops_before_escalation` field; the `convergence` field plays a similar role but is structurally different and worded differently.

**Why it matters:** every claim in INTEGRATION.md about ratchet's automatic handling of our contract is fiction. The "marquee feature" of spec-drift bailout, as documented, simply does not happen.

**Honest reality:** the user can still chain these skills, but it's a **manual handoff**: user invokes `/ratchet` with the goal "implement spec.md" + criteria "all tests in tests/<feature>/ pass" + frozen_files `[specs/, tests/]`. Ratchet then derives its own `evaluate.sh` (likely just `pytest tests/<feature>/ && bash tests/<feature>/existence.sh && bash tests/<feature>/mutation.sh`). The done_when.yaml we produce is *input material* for ratchet's Step 1-3, not a structural contract ratchet reads.

**Fix applied (this round):**
- Rewrite INTEGRATION.md §ratchet handoff to document the manual-handoff reality.
- Rewrite §spec-drift bailout to label `spec_drift_threshold` as guidance for the user / ratchet author (a hint to set `convergence` low), not an auto-honored field.
- Update `done-when-schema.yaml` block comment around `spec_drift_threshold:` to match.
- Update plugin README and marketplace description to drop the fictional claim.

---

### ISSUE-003 — [integration claim, CONFIRMED + WORSE] persona-judge is a persona-skill quality gate, not a generic fitness evaluator

**Severity:** high (was medium)
**Where:** `plugins/done-when-pipeline/INTEGRATION.md`, `fitness-rubric-guide.md`, `sub-modules/fitness-rubric.md`, `done-when-schema.yaml`, plugin README, marketplace description, worked example `subscription-cancellation/done_when.yaml`
**Found in:** S2 Q17 resolution; **verified by reading** `plugins/persona-distill/skills/persona-judge/SKILL.md`

**What (confirmed):**
- `persona-judge` skill EXISTS (`plugins/persona-distill/skills/persona-judge/SKILL.md`, version 0.1.0).
- But its purpose is **evaluating the quality of persona-distillation skills** (e.g. `steve-jobs-mirror`) on a 12-dimension rubric with density scoring. Input contract: "a persona skill root directory path (e.g. `~/skills/steve-jobs-mirror/`)". Output: `validation-report.md` with PASS/CONDITIONAL_PASS/FAIL.
- It does NOT take an arbitrary artifact (README, generated code, API reference) + a custom rubric + a persona name and return a score against that rubric. That capability does not exist in this marketplace.
- The personas I named (`integration-engineer-persona`, `non-technical-end-user-persona`, `oncall-sre-persona`) **do not exist** in persona-distill (grep returned zero hits). I invented them.

**Why it matters worse:** every generated fitness rubric file we'd emit references a non-existent integration. The source design doc itself (§6.7, §10.3, §11.2) made the same conceptual error — assumed `persona-judge` was a generic fitness judge. We propagated that error into the skill source.

**Honest reality:** Step 4-F as designed needs a fitness-judge component that doesn't currently exist. Options:
  (a) Drop the persona-judge integration, document fitness rubrics as input to a "Claude-with-rubric" inline pattern (the user manually invokes Claude with the rubric file + artifact).
  (b) Suggest DeepEval for Python projects (the source doc already mentions this as alternative).
  (c) Note as future work: a dedicated "fitness-rubric-judge" skill would close this gap, but it isn't in scope here.

**Fix applied (this round):**
- Rewrite `fitness-rubric-guide.md` and `sub-modules/fitness-rubric.md`: remove all references to persona-judge as the consumer; replace with the honest "Claude-with-rubric inline" pattern.
- Remove all references to the invented personas (`integration-engineer-persona`, etc.) — replace with rubric templates that don't depend on personas existing.
- Update `done-when-schema.yaml`: `judge:` values become `programmatic | llm-rubric | manual` (drop `persona-judge`).
- Update `acceptance-spec/SKILL.md`: same enum.
- Update worked example `subscription-cancellation/done_when.yaml`: replace `judge: persona-judge / persona: <X>` with `judge: llm-rubric`.
- Update `INTEGRATION.md`: remove the persona-judge integration section; replace with the honest "fitness-judge does not yet exist as a packaged skill; use Claude inline" note.
- Update plugin README + marketplace description: drop the persona-judge integration claim.

---

### ISSUE-004 — [closed, not an issue] argument-hint frontmatter is correct

**Severity:** none (closed)
**Verified by:** `grep -r "argument-hint" plugins/*/skills/*/SKILL.md` shows the field is used by `bespoke-design-system`, `design-clone`, `forge-teams/*`. Format is standard.

---

---

## Round 1 → Round 2 transition: S1-S3 re-run results

After ISSUE-001 / ISSUE-002 / ISSUE-003 fixes landed in skill source (commit-equivalent: all files updated in place), I re-executed S1 → S2 → S3:

- **S1**: same 5 REQs drafted. New iron-rule wording (Round-1 fix) now tells me to tag every `[?]` at write-time. No new issues.
- **S2**: 21 questions, but Q15-Q18 resolutions are now honest (manual hand-off; no persona-judge integration). Did not trigger any new ISSUEs.
- **S3**: regenerated REQ-012 + REQ-013 in spec.md, and the corresponding `behavior:` block + `integration_tests:` in done_when.yaml, to reflect Round-2 honest contract. proposal.md decision list updated to remove "flagged as unverified" markers.

**Round-1 issues fixed and re-verified: ISSUE-001 ✓ / ISSUE-002 ✓ / ISSUE-003 ✓ / ISSUE-004 closed-as-not-an-issue.**

Proceeding to Step 4 (verification test derivation) and Step 5 (execution against existing plugin). Any further issues will be logged as Round 2 issues below.

---

## Round 2 issues

**None.** Step 4 (verification derivation) + Step 5 (execute) ran against the round-1-fixed source. Results:

- 4-A `existence.sh`: 24/24 pass
- 4-B `unit/test_structure_lints.py`: 25/25 pass (covers REQ-001 .. REQ-016 except 4-D/4-E/4-F which are N/A here)
- 4-C `integration/test_cross_plugin.py`: 4/4 pass

The integration checks include explicit assertions that confirm our Round-1 fixes landed correctly:
- `test_ratchet_skillmd_does_not_mention_done_when_yaml_consumption` — keeps us honest if a future ratchet release changes its interface (the test would fail and force us to revisit INTEGRATION.md).
- `test_no_invented_personas_referenced_anywhere_in_plugin` — guards against regression of the persona-judge category error.
- `test_no_file_in_plugin_claims_persona_judge_consumes_fitness_rubrics` — same.

## Final status

**Round 1: 3 substantive issues found, fixed, re-verified.**
**Round 2: 0 new issues. Pipeline clean.**

Deferred (out of this verification scope — needs Claude Code session restart):
- Live e2e: invoke `/acceptance-spec` and `/test-suite-generator` in a fresh session and confirm they behave as their SKILL.md describes.
- Fitness-rubric scoring: the "manual fresh-Claude-session workflow" is itself untested under live conditions.

These should be the next round if/when the user wants to extend the dogfooding.
