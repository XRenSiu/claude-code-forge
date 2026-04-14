# Phase 6 — Adversarial Debugging: Hypothesis Board

**Feature**: persona-distill-ecosystem v0.1.0
**Date**: 2026-04-14
**Input**: `phase-5-red-team/arbitration.md` — 4 P6-routed items (B1, H1, H2, M3) + 7 documented-only items (S1-S7)

---

## Hypothesis Slots

P6 treats each must-fix bug as a "hypothesis about root cause" that must survive adversarial challenge before a fix is applied. The 4 items enter as H-1 through H-4.

### H-1 — Component count drift (B1 from arbitration)

**Claim**: "Multiple files say `16 components` but the real count is `18`. This is a single-root issue: Wave 2 batch headers were written from a stale PRD revision that said 16, while detail tables used the post-revision count of 18."

**Evidence (initial)**:
- `components/` directory: 18 `.md` files (ls verified).
- `manifest.schema.json` `components_used` enum: 18 values.
- `PRD §2.3` header: "16 shared components" (stale); `PRD §2.3` detail table: 18 rows.
- 7 files with the "16" string (enumerated below).

**Occurrence list (7 places, grepped)**:
1. `skills/distill-meta/SKILL.md` — [NEEDS VERIFY — says "18" in current check, may have been fixed inline during Wave 5]
2. `skills/distill-meta/references/components/README-level` batch note in 1 component file
3. `skills/distill-meta/references/output-spec.md` — 1 reference
4. `skills/persona-judge/references/rubric.md` — 1 reference
5. `skills/persona-router/references/matching.md` — 1 reference (component_coverage dim)
6. `skills/persona-debate/references/modes.md` — 0 references (verify)
7. `docs/integration.md` (written in Wave 5) — initially said 16

**Alternative hypotheses to consider**:
- **Alt-A**: "Some `16`s refer to non-component things (16 dimensions, 16 anything-else) and are not drift."
- **Alt-B**: "The true count is 17 (one duplicate)."

**Expected falsifier**: `ls components/*.md | wc -l` → integer. If != 18, hypothesis is wrong.

**Confidence after evidence review**: HIGH (95%) — 18 physical files is ground truth; all `16` references need to become `18` unless they refer to a different `16`.

### H-2 — distill-collector dead refs (H1 from arbitration)

**Claim**: "`distill-collector/SKILL.md` was written in Wave 1 referencing planned filenames that Wave 4 later renamed. Dead refs are `references/audio-pipeline.md`, `references/ocr-policy.md`."

**Evidence (initial)**:
- Wave 4 actual files: `av-pipeline.md`, `image-doc-parsers.md`, `cli-spec.md`, `text-parsers.md`, `redaction-policy.md`.
- SKILL.md grep for "audio-pipeline" / "ocr-policy" → references that should be renamed.
- Also possibly `doc-parsers.md` referenced in SKILL.md but only `image-doc-parsers.md` exists.

**Alternative hypotheses**:
- **Alt-A**: "Wave 4 created BOTH the old AND the new names, and the old ones were later deleted. Check git log." (Unlikely per plan.json — files_owned lists only new names.)

**Expected falsifier**: `grep -n audio-pipeline\|ocr-policy skills/distill-collector/SKILL.md` returns 0 matches → hypothesis falsified. Any match → confirmed.

**Confidence**: HIGH (90%).

### H-3 — Seven-axis DNA label divergence (H2 from arbitration)

**Claim**: "`extraction/seven-axis-dna.md` and `components/expression-dna.md` use different short names for the same 7 axes. Agent `expression-analyzer.md` reads extraction file as prompt input but writes output that's re-read against component file's axis names. Result: round-trip fails."

**Evidence (initial)**:
- Both files exist; both cover 7 axes.
- Labels genuinely differ (e.g., "lexical-formality" vs "formality-register").

**Alternative hypotheses**:
- **Alt-A**: "Labels are synonyms; the mismatch is cosmetic and no consumer actually reads both." (Falsified: expression-analyzer agent reads BOTH.)
- **Alt-B**: "Extraction file is correct; component file is wrong." (Unresolvable without authority rule.)
- **Alt-C**: "Component file is correct; extraction file is wrong." (Same.)

**Resolution rule**: extraction file is execution authority (per agent-style convention: the prompt template rules); component file becomes the canonical shipping form — so we DO NOT rename component file labels; instead we ADD an alias table in component file mapping extraction labels → component labels. Expression-analyzer reads alias table.

**Confidence**: HIGH (85%) — divergence is real; resolution path via alias-table avoids disrupting either producer or consumer downstream.

### H-4 — public-mirror research file placement (M3 from arbitration)

**Claim**: "`schemas/public-mirror.md` says research files go at skill root; `references/output-spec.md` says under `knowledge/`. Conflict."

**Evidence (initial)**:
- Both statements present verbatim.
- PRD §1.2 says `knowledge/` hierarchy.

**Alternative**: — (self-evident conflict).

**Resolution rule**: apply `knowledge/research/` as the reconciliation path. Update `schemas/public-mirror.md` accordingly.

**Confidence**: HIGH (99%).

---

## Documented-Only Items (no P6 fix, routes to integration.md §6.2)

| ID | Why NOT fixed in P6 |
|----|---------------------|
| S1 | Fix requires NER model + redaction engine redesign; too large for P6 window. |
| S2 | Fix requires signed consent-attestation + corpus proper-noun cross-check infrastructure. |
| S3 | Fix requires `untrusted-input: true` tagging convention + runtime delimiter protocol across all extraction prompts. |
| S4 | Fix requires schema tightening + fingerprint verifier agent. |
| S5 | Fix requires config lock-ranges + attestation + second-judge independent run. |
| S6 | Fix requires renaming "Extraction Prompt" to preserve-at-copy + self-containment-linter agent. |
| S7 | Fix requires new `source_privacy` dimension across source-policies + Phase 1.5 gate. |

All 7 are genuine v1 gaps. Rather than half-fix, P6 will document them as known limitations with user guidance in `integration.md §6.2` + `§6.3 Honest guidance for users`.

---

## Hypothesis Board Status

| ID | Status | Next step |
|----|--------|-----------|
| H-1 | READY_FOR_DEBATE | Enumerate exact 7 occurrences; confirm with grep |
| H-2 | READY_FOR_DEBATE | Grep distill-collector SKILL.md; enumerate dead refs |
| H-3 | READY_FOR_DEBATE | Read both files; confirm 7 axis-name pairs that differ |
| H-4 | READY_FOR_DEBATE | Already self-evident; resolution path clear |

Handoff to `debate-log.md` for adversarial-protocol debate rounds.
