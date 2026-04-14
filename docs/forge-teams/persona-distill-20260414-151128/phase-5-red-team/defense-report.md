# Phase 5B — Defense Review Report

**Feature**: persona-distill-ecosystem v0.1.0
**Reviewers**: spec-reviewer (sonnet) + code-reviewer (sonnet)
**Date**: 2026-04-14
**Scope**: PRD coverage, plugin-layer conformance, contract internal consistency, file-ownership adherence, progressive-disclosure compliance.

---

## Part 1 — Spec Review (spec-reviewer)

**Verdict**: **ACCEPT WITH B1 + 4 MINOR** (non-blocking; routes to P6 and integration.md §5).

### Coverage matrix (PRD → implementation)

| PRD section | Requirement | Covered? | Evidence |
|-------------|-------------|----------|----------|
| §1.1 | "Self-contained persona skill produced" | ✅ | `SKILL.md §Self-Contained Principle`; template drops extraction sections |
| §1.2 | Output directory spec | ✅ | `references/output-spec.md` |
| §2.3 (hdr) | "16 shared components" | ⚠️ | Header says 16; detail table lists 18 (B1 — see below) |
| §2.3 (table) | 18 component listing | ✅ | 18 files under `components/` |
| §2.4 | `computation-layer` cross-schema | 📋 | Only executor wire-up; experimental elsewhere (honest label) |
| §3.2 | 7-phase workflow | ⚠️ | All phases shipped, but Phase 2.5 is single-pass (v1 degradation documented) |
| §3.3 | 9-way schema decision tree | ✅ | `references/decision-tree.md` |
| §4.2 | 12-dim rubric | ✅ | `persona-judge/references/rubric.md` |
| §4.2 | Pass threshold 75 (normalized) | ⚠️ | Contract uses 82 raw; CONDITIONAL_PASS band bridges |
| §7 | 9 schemas | ✅ | All 9 files shipped (all `unvalidated: true`) |
| §7 | Schema 4 "6-layer" | ✅ | `schemas/loved-one.md` + `components/persona-6layer.md` |
| §8 Stage 1 MVP | distill-meta + 3 schemas | ✅ (over-delivered — 9 schemas) |
| §8 Stage 2 | persona-judge + Phase 4 gate | ✅ | `agents/validator.md` wires it |
| §8 Stage 3 | distill-collector multi-modal | 📋 | Scaffolding only (honest v1 doc) |
| §8 Stage 4 | router + debate + schema extension | ⚠️ (router + debate shipped; extension mechanism unshipped) |
| §9 #1-#10 | Design-decision preservation | ✅ | Each decision traceable to a component or contract |

### B1 — `16` vs `18` component drift `[BLOCKER]`

**Location**: 7 places.
- `components/README-style` batch headers say "16"
- `references/components/README-of-pattern.md` (implicit sections) reference "16"
- `SKILL.md §Components` says "18 可复用组件" (correct)
- Detail table in PRD §2.3 lists 18 (correct)
- persona-judge rubric references "16" in one place

**Why blocker**: manifest.schema.json enum for `components_used` lists 18 values. A reader will get a different answer depending on which file they read first. Downstream a persona skill declaring `components_used: 17` cannot easily judge right/wrong.

**Reconciliation**: 18 is authoritative (matches manifest enum and detail tables). All `16` references must be bumped to `18`. Routes to **P6**.

### Minor findings (4)

| # | Finding | Location | Severity |
|---|---------|----------|----------|
| M1 | Seven-axis DNA: `extraction/seven-axis-dna.md` axis names differ from `components/expression-dna.md` labels. Mapping step needed at Phase 3. | extraction + components | Minor (functional; confusing) |
| M2 | `distill-collector/SKILL.md` references old filenames (`audio-pipeline.md`, `ocr-policy.md`); actual Wave 4 files use `av-pipeline.md`, `image-doc-parsers.md` | distill-collector SKILL.md | Minor (dead refs) |
| M3 | PRD §7 Schema 6 says research files at skill root; §1.2 says `knowledge/` — conflict | public-mirror.md | Minor (doc reconcile) |
| M4 | PRD §3.2 mentions "8-dim rubric"; §4.2 says 12-dim — contradiction within PRD | N/A (upstream) | Minor (note in rubric.md) |

All 4 route to P6 adversarial-debug.

---

## Part 2 — Code Review (code-reviewer)

**Verdict**: **ACCEPT WITH 2 HIGH + 3 MINOR** (non-blocking; routes to P6).

### Adherence matrix (engineering quality)

| Check | Result | Evidence |
|-------|--------|----------|
| Plugin layout matches CLAUDE.md §"项目结构" | ✅ | `.claude-plugin/plugin.json`, `skills/*/SKILL.md`, contracts discoverable |
| SemVer triple-alignment (plugin.json / marketplace.json / SKILL.md frontmatter) | ✅ | All at 0.1.0 |
| JSON files validate | ✅ | plugin.json, marketplace.json entry, manifest-template.json, manifest.schema.json |
| Contract internal consistency (no cycles, no dead fields) | ✅ | verified manifest → validation-report → component chain |
| SKILL.md < 350 lines (progressive disclosure) | ✅ | 5/5 compliant (distill-meta = 226 lines) |
| Reference docs line budget | ✅ | all < 300 |
| File ownership disjoint across waves (no collision) | ✅ | verified against plan.json |
| Incremental-write rule (no batch-at-end writes) | ✅ | checkpoints visible in `.forge-state.json` |
| `[UNVERIFIED-FROM-README]` tagging consistent | ✅ | 104 occurrences across 54 files; no dangling citation without tag |

### H1 — `distill-collector/SKILL.md` dead references `[HIGH]`

**Location**: `skills/distill-collector/SKILL.md`.

**Finding**: SKILL.md entrypoint (written in Wave 1 before Wave 4 finalized filenames) references files like `references/audio-pipeline.md` and `references/ocr-policy.md` which were RENAMED in Wave 4 to `references/av-pipeline.md` and `references/image-doc-parsers.md`.

**Impact**: a Claude Code user invoking the distill-collector skill hits "file not found" when the skill tries to progressive-disclose the referenced sections.

**Root cause**: Wave 1 wrote SKILL.md speculatively; Wave 4 changed filenames during elaboration. No linter caught the dead refs because quality-sentinel only samples new files, not re-reads Wave 1 files.

**Fix**: update refs in `distill-collector/SKILL.md` to actual Wave 4 filenames. Routes to **P6**.

### H2 — Seven-axis DNA label mismatch `[HIGH]`

**Location**: `extraction/seven-axis-dna.md` (axes: `A1...A7` with specific names) vs `components/expression-dna.md` (different axis labels for the same 7 dimensions).

**Finding**: same conceptual 7 axes have DIFFERENT short names in the two files. E.g., extraction file calls axis 1 "lexical-formality"; component file calls it "formality-register". Downstream `expression-analyzer.md` agent must run a label-mapping step or outputs will be inconsistent with what the produced component expects.

**Impact**: functional — a persona skill's `expression-dna.md` can ship with fields that don't round-trip against re-validation.

**Fix**: resolve one way (extraction file is execution authority, per agent convention); component file's labels become aliases listed in a compat table. Routes to **P6**.

### Minor findings (3)

| # | Finding | Location | Severity |
|---|---------|----------|----------|
| m1 | `components/persona-5layer.md` and `components/persona-6layer.md` share 4 identical paragraphs verbatim (DRY violation) | components/persona-{5,6}layer.md | Minor (maintainability) |
| m2 | `persona-judge/references/rubric.md` has one inline reference to "16 components" | rubric.md | Minor (folds into spec B1) |
| m3 | `manifest.schema.json` string fields (`description`, `triggers[]`, `domains[]`) have no `maxLength` caps | manifest.schema.json | Minor (v2 tightening) |

m2 folds into spec B1 reconciliation; m1 + m3 route to integration.md §8 v2 roadmap rather than P6.

---

## Part 3 — Cross-Examination Notes

Where red-team findings intersect defense findings:

| Red-team ID | Defense finding | Agreement? |
|-------------|-----------------|------------|
| S4 (manifest under-constraint) | code m3 (no maxLength) | ✅ same root cause; red-team extends to fingerprint + validation_score forgeability |
| S6 (self-containment escape via correction-layer) | spec M2 (dead refs in distill-collector SKILL.md) | Related but distinct — different files, same class-of-bug (dead cross-references) |
| S5 (rubric gaming via config.yaml) | — | defense did not catch; red-team-only |
| S3 (prompt injection from corpus) | — | defense did not catch; red-team-only |
| S2 (consent bypass) | — | defense did not catch; red-team-only |
| S1 (free-text PII) | — | defense noted scaffolding but did not flag the redaction-stamp false-trust issue |
| S7 (schema privacy) | — | red-team-only |

**Observation**: spec-reviewer + code-reviewer covered 2/7 red-team findings independently. 5/7 of the critical/high findings required attacker mindset — confirmation that red-team is complementary, not redundant.

---

## Handoff

All findings routed to `arbitration.md` for unified verdict. B1 + H1 + H2 are must-fix before P7 (route to P6). Red-team S1-S7 are routed to integration.md §6.2 as honest v1 limitations (too deep for P6 to fix in time; documented as known v1 gaps).
