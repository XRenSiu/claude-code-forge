# Risk Assessment — persona-distill-ecosystem (FULL scope)

**Assessed at**: 2026-04-14
**Overall Risk Level**: HIGH (with mitigations applied: MEDIUM)
**Total Risks**: 23 (Critical: 4, High: 11, Medium: 7, Low: 3 — plus 3 cross-cutting)

---

## Dimension 1 — Dependency Risk

| ID | Severity | Description | Mitigation (applied in plan) |
|----|----------|-------------|------------------------------|
| DEP-01 | CRITICAL | 15+ external reference repos (nuwa/colleague/ex/immortal/anti-distill/cyber-figures/midas/图鉴/诸子/bazi/etc.) cannot be cloned. PRD §10 self-admits all structures come from README fragments. | Every "抄 X" task re-derives from the fragment quoted in master plan. Any gap → explicit `[UNVERIFIED-FROM-README]` marker in the file. |
| DEP-02 | HIGH | 3 repos (`图鉴.skill`, `诸子.skill`, `midas.skill`) have no findable URLs yet are declared as blueprints for router/debate/public-domain. | public-domain schema re-derived from first principles (N-dim framework pattern). router/debate implemented from PRD §5.2/§5.3 descriptions only. |
| DEP-03 | HIGH | Internal circular risk: distill-meta Phase 4 → persona-judge; persona-router reads manifest.json from distill-meta; rubric → schemas. | **CONTRACT-01/02/03 shipped in wave 1** before any downstream implementation. |
| DEP-04 | HIGH | 16 components shared across 9 schemas; without explicit single-ownership they'll drift. | Components owned by 5 tasks (T017-T021), schemas reference-only. File-ownership matrix validated. |
| DEP-05 | MEDIUM | Phase 2.5 spec not frozen but Phase 2 tasks depend on its output contract. | Phase 2.5 shipped as single-pass scanner (T026); multi-round deferred with `TODO(v2)` comment. |
| DEP-06 | MEDIUM | computation-layer claimed cross-schema but only executor has concrete interface. | Scoped to executor in this run; cross-schema plug-in deferred. |

## Dimension 2 — Estimation Risk

| ID | Severity | Description | Mitigation |
|----|----------|-------------|------------|
| EST-01 | CRITICAL | ~100-180 files in one forge-teams run risks mid-run context exhaustion. | 5 waves with explicit state-save boundaries. forge-state.json updated after each wave. `phase-N-progress.md` per wave. |
| EST-02 | HIGH | distill-collector 15+ parsers × 200-500 LOC each = 4000-8000 LOC of unshippable binary-dependent code. | Collector scoped to **reference docs only** (T045-T049) — no runtime parser code. SKILL.md documents CLI contract; users bring their own scrapers. |
| EST-03 | HIGH | 9 schemas × (spec + components list + example + test) + 16 components + 12-dim rubric → 120-150 files realistic. | Components batched (16 comps → 5 tasks), schemas kept to 1 file each, examples deferred. Final estimate: ~110 files. |
| EST-04 | MEDIUM | PRD §8 own roadmap says Stage 1 MVP first; user overrode with "implement all". | User override accepted; mitigation = contract-first + wave boundaries. |
| EST-05 | MEDIUM | Context-break points predictable at wave boundaries. | Each wave ends with state update + handoff. Resume supported via `--skip-to`. |

## Dimension 3 — Integration Risk

| ID | Severity | Description | Mitigation |
|----|----------|-------------|------------|
| INT-01 | CRITICAL | `manifest.json` schema undefined but consumed by 3 skills. | **CONTRACT-01** in wave 1: `contracts/manifest.schema.json`. |
| INT-02 | HIGH | `validation-report.md` format must match between persona-judge producer and distill-meta consumer. | **CONTRACT-02** in wave 1: `contracts/validation-report.schema.md`. |
| INT-03 | HIGH | 16 components lack interface contract (naming, required sections, frontmatter). | **CONTRACT-03** in wave 1: `contracts/component-contract.md`. |
| INT-04 | HIGH | Phase 0.5 decision-tree output format undefined. | Decision-tree reference (T007) emits explicit JSON schema inline. |
| INT-05 | MEDIUM | Component copy-vs-reference semantics when producing persona skill. | Output-spec (T028) mandates: copy-with-inlining at generation. |
| INT-06 | MEDIUM | persona-debate assumes invocation protocol between persona skills. | Debate orchestrator agent (T054) uses moderator-proxy pattern (no direct skill-to-skill calls). |

## Dimension 4 — Technical Risk

| ID | Severity | Description | Mitigation |
|----|----------|-------------|------------|
| TEC-01 | HIGH | Whisper/yt-dlp/OCR require user-side binary deps. | Collector ships as **scaffolding-only** — docs describe pipeline, no runnable code. |
| TEC-02 | HIGH | WeChat/QQ/iMessage parsers require platform-specific DB extraction. | Single reference parser (generic text import) + pointers to third-party tools (wechatDataBackup etc.). |
| TEC-03 | MEDIUM | computation-layer Python execution has env assumptions. | Executor example limited to pure-stdlib; ta-lib/bazi examples documented not shipped. |
| TEC-04 | MEDIUM | distill-meta SKILL.md "<300 lines" constraint vs needing to encode 9 schemas + 16 components + 7 phases. | SKILL.md acts as pure router; references loaded progressively. |
| TEC-05 | MEDIUM | PII redaction promised but unspecified. | Minimal redactor (phone/email/ID regex) + user-responsibility disclaimer (T049). |
| TEC-06 | LOW | `fingerprint` field has no algorithm. | CONTRACT-01 specifies SHA256 of sorted knowledge/*.md concat. |

## Dimension 5 — Design/Spec Risk

| ID | Severity | Description | Mitigation |
|----|----------|-------------|------------|
| SPEC-01 | CRITICAL | PRD §10: 9 schemas not validated by real distillation. | All 9 ship with `[UNVALIDATED]` banner in frontmatter. Dog-food deferred post-P7. |
| SPEC-02 | HIGH | Phase 2.5 iterative deepening is concept not methodology. | Ships as single-pass gap scanner; multi-round `TODO(v2)`. |
| SPEC-03 | HIGH | computation-layer as universal attachment is speculation. | Executor-only scope (covered in DEP-06). |
| SPEC-04 | HIGH | Hardcoded thresholds (≥2 tensions, ≥3 boundaries) copied from nuwa README. | Made configurable via `persona-judge/config.yaml` with nuwa defaults. |
| SPEC-05 | MEDIUM | Source blacklist/whitelist Chinese-only. | Parameterized by language; Chinese default + English stub. |
| SPEC-06 | MEDIUM | conflicts.md detection mechanism undefined. | Spec as user-appended file; auto-detection deferred. |
| SPEC-07 | MEDIUM | 12-dim scoring 110→100 normalization fragile. | Use raw /110 with threshold 82; documented in rubric. |
| SPEC-08 | LOW | Self-contained + component-copy → drift vs updated library. | Version recorded in manifest; migration tool = v2. |

## Cross-Cutting Risks

| ID | Severity | Description | Mitigation |
|----|----------|-------------|------------|
| CCR-01 | CRITICAL | Reference-library ghosts: PRD directs "直接抄" across 15+ unreachable repos. | Implementers forbidden from inventing content; must quote PRD fragment or mark `[UNVERIFIED]`. |
| CCR-02 | CRITICAL | Single-run context exhaustion. | 5-wave plan with state-save at each boundary. |
| CCR-03 | HIGH | No dog-food validation of 9-schema design. | Flagged as post-P7 follow-up; UNVALIDATED banners in shipped files. |

---

## Top 5 Must-Mitigate (all applied in plan.json)

1. **Freeze integration contracts in wave 1** (CONTRACT-01/02/03) — done.
2. **Scope collector to reference-only** — done (T045-T049 are spec docs, no parsers).
3. **Wave boundaries with state-save** — forge-pipeline's built-in `.forge-state.json` + `phase-N-progress.md` used after each wave.
4. **UNVALIDATED banner on all 9 schemas** — implementer brief mandates this.
5. **Re-derive from PRD fragments, mark gaps as [UNVERIFIED]** — implementer brief mandates this.

---

## Verdict

**Plan Status**: APPROVED with mitigations applied.
**Conditions**: All 5 top mitigations incorporated into plan.json. Wave-1 contracts are non-negotiable gate.
