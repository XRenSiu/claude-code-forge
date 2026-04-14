# Phase 5C — Review Synthesis & Arbitration

**Feature**: persona-distill-ecosystem v0.1.0
**Synthesizer**: review-synthesizer (opus)
**Inputs**: `attack-report.md` (7 vectors), `defense-report.md` (spec B1 + 4 minor; code 2 HIGH + 3 minor)
**Date**: 2026-04-14

---

## Unified Findings Ledger (deduplicated & cross-validated)

| ID | Source(s) | Class | Severity | Blocker for P7? | Route |
|----|-----------|-------|----------|-----------------|-------|
| **B1** | spec | Spec drift | Blocker | YES | P6 (fix 16→18 in 7 places) |
| **H1** | code | Dead refs | High | YES | P6 (rename distill-collector SKILL.md refs) |
| **H2** | code | Label mismatch | High | YES | P6 (seven-axis DNA alignment) |
| **S1** | red-team | Privacy | Critical | NO | integration.md §6.2 (documented v1 gap) |
| **S2** | red-team | Consent bypass | Critical | NO | integration.md §6.2 |
| **S3** | red-team | Prompt injection | Critical | NO | integration.md §6.2 |
| **S4** | red-team + code m3 | Manifest under-constraint | High | NO | integration.md §6.2 + §8 v2 roadmap |
| **S5** | red-team | Rubric gaming | High | NO | integration.md §6.2 |
| **S6** | red-team | Self-containment escape | High | NO | integration.md §6.2 |
| **S7** | red-team | Schema privacy | High | NO | integration.md §6.2 |
| M1 | spec | DNA naming | Minor | — | Folded into H2 |
| M2 | spec | Dead refs | Minor | — | Folded into H1 |
| M3 | spec | Research placement | Minor | — | P6 (quick reconcile via `knowledge/research/`) |
| M4 | spec | Rubric dim count | Minor | — | Note in rubric.md (12 is authoritative) |
| m1 | code | 5layer/6layer DRY | Minor | — | integration.md §8 (v2) |
| m2 | code | Rubric "16 ref" | Minor | — | Folded into B1 |
| m3 | code | maxLength missing | Minor | — | Folded into S4 |

## Dedup / Fold Decisions

- **B1 absorbs m2**: same root cause (drift between 16 and 18 component counts).
- **H1 absorbs M2**: same finding (dead refs in distill-collector SKILL.md), spec found it while reading SKILL.md for coverage; code found it while verifying file-ownership.
- **H2 absorbs M1**: same seven-axis DNA label issue; spec flagged it through PRD coverage, code through engineering style.
- **S4 absorbs m3**: both are manifest.schema.json under-constraint; red-team extends to forgeable fingerprint + unvalidated validation_score, so keep S4 as the primary identifier and mark m3 as contributing evidence.

## Priority Queue for P6

**Must-fix (blockers for P7)**:

1. **B1 — 16→18 component drift** (7 places). Exhaustive find-and-replace candidates; each occurrence needs context check to confirm it's referring to the shared-component count vs. something else. Estimated time: 20 min.
2. **H1 — distill-collector dead refs** (1 file, ~5 refs). Rename to Wave 4 actual filenames. Estimated time: 10 min.
3. **H2 — Seven-axis DNA alignment** (2 files). Extraction file is execution authority (per agent convention); component file either adopts extraction names OR adds a `## Alias Table` H2 mapping old labels → new names. Expression-analyzer agent then reads the alias table. Estimated time: 30 min.
4. **M3 (small)** — public-mirror.md `knowledge/research/` placement reconcile. Estimated time: 5 min.

**Defer to integration.md §6.2 (honest v1 gaps, not blockers)**:

S1-S7. These are DESIGN-level gaps; fixing them requires new agents / new components / new contracts — too large for P6. Better to ship with honest documentation than rush.

## Cross-Reviewer Alignment

| Question | spec-reviewer | code-reviewer | red-team | synthesizer verdict |
|----------|---------------|---------------|----------|---------------------|
| Is plugin shippable? | yes w/ B1+M | yes w/ H1+H2 | yes, but users must understand S1-S7 | **yes, post-P6 (B1/H1/H2/M3 fixed), with security gaps documented** |
| Does manifest need tightening? | — | m3: yes | S4: yes, including fingerprint | **yes; v2 roadmap item**; honest §6.2 note in v1 |
| Does self-containment hold? | ✅ (header-level) | ✅ (structural) | ❌ S6: correction-layer breaks | **partially**; document S6 in §6.2, add `self-containment-linter` to v2 roadmap |
| Does consent gate work? | ✅ (policy exists) | ✅ (flag wired) | ❌ S2: bypass via subject_type | **policy-only, not enforcement**; document honestly |

## Final P5 Verdict

> **PROCEED TO P6** with 4 items (B1 + H1 + H2 + M3). After P6 closes those, PROCEED TO P7.
> **S1-S7 will be documented in `integration.md §6.2` during P6 as part of the P6 deliverable**, not fixed in v0.1.0. Users of v0.1.0 must be informed before distilling real corpora.

## Handoff to P6

P6 receives this ledger as input. P6 will:
- Write `hypotheses.md` with the 3+1 fixable bugs as candidate hypotheses.
- Run adversarial-debug debate rounds on each (evidence-backed).
- Execute TDD fixes via issue-fixer agent.
- Update integration.md §6.2 with S1-S7 as honest v1 limitations.
- Produce `fixes.md` summary → back to P5 re-review (incremental) → P7.
