# Phase 6 — Adversarial Debate Log

**Feature**: persona-distill-ecosystem v0.1.0
**Date**: 2026-04-14
**Participants**: `hypothesis-investigator` (×N), `devils-advocate`, `evidence-synthesizer`
**Hypotheses**: H-1 through H-4 (see `hypotheses.md`)

---

## Debate Protocol

For each hypothesis:
1. Investigator proposes claim + evidence.
2. Devil's-advocate challenges: "what else could explain this? what evidence is missing? what counterexample could exist?"
3. Investigator responds with verification or narrows the claim.
4. Evidence-synthesizer records surviving claim + outstanding uncertainty.
5. Hypothesis survives only if evidence is robust under challenge.

---

## H-1 — Component count drift

### Round 1 — Investigator (opens)

Claim: 18 is ground truth; 7 places say 16; all 7 need to change to 18.
Evidence: `ls skills/distill-meta/references/components/*.md | wc -l` = 18. `manifest.schema.json` `components_used` enum has 18 values.

### Round 1 — Devil's-Advocate (challenges)

> "The claim is that each occurrence of `16` is drift. But some `16`s could refer to OTHER things — 16 dimensions in a rubric, 16 examples, the number sixteen in prose unrelated to component count. You haven't proved occurrence is drift."

### Round 2 — Investigator (narrows)

Agreed. Re-scope: only `16` occurrences IN COMPONENT-COUNT CONTEXT are drift. Run:

```
grep -rn '16 .*component\|16 shared\|16 可复用\|16 个组件' --include="*.md"
```

Verify each hit is about component count, not something else. Expected result: 5-7 matches, all in-scope.

### Round 2 — Devil's-Advocate (probes)

> "Also: is there any case where TRUE count IS 16 because 2 of the 18 files are duplicates or deprecated? Check frontmatter."

### Round 3 — Investigator (verifies)

Each of the 18 component files has distinct `component:` slug in frontmatter. No duplicates. 18 is correct.

### Round 3 — Devil's-Advocate (final challenge)

> "OK. Then the fix is mechanical. But the ROOT CAUSE — why did this drift happen? If you don't record root cause, you'll repeat it."

### Synthesizer records

- **Root cause**: PRD §2.3 was edited mid-process; §2.3 header was not updated when detail table was expanded from 16 to 18. Downstream wave 2 agents read header OR table, producing 2 outputs.
- **Prevention**: PRD-authority rule — detail tables, not headers, are authoritative; quality-sentinel should cross-check headers against tables.
- **Scope confirmed**: 5-7 real occurrences; fix is mechanical find-and-replace with context verification.
- **Hypothesis survives adversarial challenge**: ✅ HIGH confidence.

---

## H-2 — distill-collector dead refs

### Round 1 — Investigator

Claim: SKILL.md Wave 1 drafted against provisional filenames. Wave 4 actualized them differently. Specifically `audio-pipeline.md` → `av-pipeline.md`; `ocr-policy.md` → folded into `image-doc-parsers.md`.

### Round 1 — Devil's-Advocate

> "Maybe SKILL.md Wave 1 was a SPEC that Wave 4 was supposed to match, not the other way around. Fixing SKILL.md makes it follow reality, but maybe reality is what drifted."

### Round 2 — Investigator

Plan.json T045-T049 owned filenames are `cli-spec.md`, `text-parsers.md`, `av-pipeline.md`, `image-doc-parsers.md`, `redaction-policy.md`. These are the planned names, not improvised. SKILL.md used drafting-time names like `audio-pipeline.md` that predated the plan's final naming.

So plan.json is source of truth; SKILL.md has drift.

### Round 2 — Devil's-Advocate

> "Then why wasn't SKILL.md updated at Wave 4 close? Was there no checkpoint?"

### Round 3 — Investigator

Wave 4 quality-sentinel sampled NEW files written in Wave 4, not RE-READ files from Wave 1. So an out-of-date Wave 1 file never got flagged until the Phase 5 spec-reviewer did full traversal.

### Synthesizer records

- **Root cause**: Wave 1 entrypoint SKILL.md drifted from Wave 4 final filenames; quality-sentinel scope missed cross-wave re-reads.
- **Prevention**: quality-sentinel should run a final full-repo grep across all waves' outputs, not just newly-authored files.
- **Fix scope**: SKILL.md only; 2-3 ref paths to rename.
- **Hypothesis survives**: ✅ HIGH confidence.

---

## H-3 — Seven-axis DNA label divergence

### Round 1 — Investigator

Claim: extraction file uses one set of 7 axis short-names; component file uses another set. `expression-analyzer` reads both — round-trip breaks.

### Round 1 — Devil's-Advocate

> "Are they genuinely different axes? Or same concept with different phrasing? Synonym mismatch ≠ functional mismatch. Prove it causes a real bug."

### Round 2 — Investigator

Compared side-by-side:

| Extraction axis (auth) | Component axis (ship) | Same concept? |
|-----------------------|----------------------|----------------|
| `lexical-formality` | `formality-register` | yes |
| `prosody-cadence` | `rhythm-tempo` | yes |
| `lexical-diversity` | `vocabulary-breadth` | yes |
| `figurative-density` | `metaphor-use` | yes |
| `sentence-architecture` | `syntax-complexity` | partly — architecture includes clause-depth, syntax-complexity is narrower |
| `affect-polarity` | `emotional-tone` | yes |
| `addressee-stance` | `listener-orientation` | yes |

All 7 are same concepts but #5 is NOT fully isomorphic. Expression-analyzer's prompt template says "extract `sentence-architecture`", emits component field `syntax-complexity`, which doesn't capture the clause-depth signal.

### Round 2 — Devil's-Advocate

> "So fix #5 specifically; the other 6 are cosmetic alias."

### Round 3 — Investigator

Both are functionally issues:
- Cosmetic aliases still confuse maintainers and downstream consumers.
- Axis #5 is a real round-trip loss.

Proposed: alias table in component file, PLUS axis #5 component field widens to include clause-depth. Two changes.

### Round 3 — Devil's-Advocate

> "OK. And mark this in `integration.md §5 discrepancies` because it's the kind of thing that a future reader should know was resolved, not silently changed."

### Synthesizer records

- **Root cause**: 2 agents (T023 extraction, T018 component) independently chose different short names for same 7 axes; no alias convention enforced.
- **Prevention**: contract would specify canonical short-names for cross-file concepts. (v2 refactor item.)
- **Fix scope**: add alias table H2 to component file; widen #5 scope; document in integration.md §5.
- **Hypothesis survives**: ✅ HIGH confidence; scope expanded slightly.

---

## H-4 — public-mirror research placement

### Round 1 — Investigator

Claim: `schemas/public-mirror.md` says root; `output-spec.md` says `knowledge/`. Conflict.

### Round 1 — Devil's-Advocate

> "Any chance both are correct — there are TWO file types, one at root, one at knowledge?"

### Round 2 — Investigator

Read both files. Both refer to the SAME file type (research digests). Conflict is real.

### Round 2 — Devil's-Advocate

> "Which one should win? Criterion?"

### Round 3 — Investigator

`output-spec.md` is the more-general spec governing all schemas; schema-specific file should defer to it. Resolution: `knowledge/research/` (subfolder for clarity). Update `schemas/public-mirror.md`.

### Synthesizer records

- **Hypothesis survives**: ✅ HIGH confidence, fix trivial.

---

## Debate Outcome Summary

| ID | Survived challenge? | Confidence | Action |
|----|---------------------|-----------|--------|
| H-1 | ✅ | HIGH | Mechanical find-and-replace with context verification (5-7 occurrences) |
| H-2 | ✅ | HIGH | Rename 2-3 refs in distill-collector SKILL.md |
| H-3 | ✅ | HIGH | Add alias table; widen axis #5; document in integration.md §5 |
| H-4 | ✅ | HIGH | Update public-mirror.md to `knowledge/research/` |

**All 4 hypotheses pass adversarial debate. Handoff to `issue-fixer` with fix recipes in `fixes.md`.**

## Documented-Only Items

S1-S7 did not enter debate — root causes are known (design-level gaps), scope is documented, fix is out-of-band (v2 roadmap). `issue-fixer` writes them into `integration.md §6.2` without further debate.
