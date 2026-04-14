---
name: integration
description: Cross-skill wiring, interface contracts, and known limitations for persona-distill v0.1.0
version: 0.1.0
---

# persona-distill — Integration & Known Limitations

> How the 5 skills and 3 contracts wire together, and the honest list of v1 gaps.

---

## 1. Integration topology

```
             ┌─────────────────────────────────────────┐
             │           persona-debate                 │
             │    (moderator orchestrates 2-5 skills)   │
             └──────────────┬──────────────────────────┘
                            │ reads manifest.json for each
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ {persona     │  │ {persona     │  │ {persona     │
    │  skill A}    │  │  skill B}    │  │  skill C}    │
    └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
           │                 │                 │
           │ emits           │                 │
           │ manifest.json   │                 │
           ▼                 ▼                 ▼
      ┌──────────────────────────────────┐
      │     contracts/manifest.schema.json │
      │     (THE integration hub)          │
      └────┬──────────────────────┬────────┘
           │                      │
           │ consumed by          │ consumed by
           ▼                      ▼
    ┌──────────────┐        ┌──────────────┐
    │ persona-router│        │ persona-judge │
    │  (scoring)   │        │  (validation) │
    └──────┬───────┘        └──────┬───────┘
           │                       │
           │ recommendations       │ emits validation-report.md
           ▼                       ▼
    (user or persona-debate)   contracts/validation-report.schema.md
                                       │
                                       │ consumed by
                                       ▼
                              ┌──────────────────┐
                              │  distill-meta    │
                              │  Phase 4 gate    │
                              │  (validator agent)│
                              └──────────────────┘
                                       ▲
                                       │ produces persona skills
                                       │
                              ┌──────────────────┐
                              │  distill-collector│
                              │  (corpus ingest, │
                              │   scaffolding)   │
                              └──────────────────┘
```

## 2. Contract-to-skill mapping

| Contract | Producer | Consumer(s) |
|----------|----------|-------------|
| `contracts/manifest.schema.json` | `distill-meta` (via `templates/manifest-template.json` at generation time) | `persona-judge`, `persona-router`, `persona-debate`, any produced persona skill |
| `contracts/validation-report.schema.md` | `persona-judge` | `distill-meta` (Phase 4 gate in `agents/validator.md`); user (standalone eval) |
| `contracts/component-contract.md` | `distill-meta` (every file in `references/components/`) | All 9 schemas; `persona-judge` rubric validates conformance |

## 3. Wave-by-wave implementation record

See `../../docs/forge-teams/persona-distill-20260414-151128/phase-3-planning/plan.json` for the full 61-task decomposition. Delivered in 5 waves:

| Wave | Purpose | Files |
|------|---------|-------|
| 1 | Scaffolding + 3 contracts + 5 SKILL.md entrypoints | 9 |
| 2 | distill-meta references (decision tree, 9 schemas, 18 components, 5 extraction frameworks, 3 source policies, output-spec) + persona-judge rubric | 38 |
| 3 | 9 distill-meta agents + 3 templates + 3 persona-judge internals | 15 |
| 4 | distill-collector (5) + persona-router (3) + persona-debate (2) | 10 |
| 5 | README, LICENSE, this integration doc, marketplace.json registration | 4 |

## 4. Cross-skill interface checkpoints

### distill-meta → persona-judge

- `distill-meta/agents/validator.md` spawns `persona-judge` via Task tool
- Reads ONLY the `overall_score_raw` and `verdict` fields from `validation-report.md`'s YAML frontmatter (not the body)
- Gate: `verdict: PASS` → Phase 5 | `CONDITIONAL_PASS` → Phase 5 + surface Recommended Actions | `FAIL (loop<3)` → Phase 2 retry | `FAIL (loop≥3)` → blocked

### persona-router → manifest.json

- Scans `.claude/skills/`, `~/.claude/skills/`, `~/.claude/plugins/cache/*/skills/` (configurable order) for `manifest.json` with `persona_distill_version` field
- Validates each against `contracts/manifest.schema.json`; skipped → WARN, not fail
- Scoring weights: schema_type_relevance 0.25 + domain_overlap 0.30 + component_coverage 0.20 + density_bonus 0.15 + primary_source_bonus 0.10 = **1.00**

### persona-debate → participant skills

- Participants provided as explicit list OR piped from `persona-router` recommendations
- Moderator agent validates each participant's `manifest.json`; invokes skills via Task
- Three modes (round-robin / position-based / free-form), each with explicit turn state machine in `persona-debate/references/modes.md`
- Hard cap: 3 rounds; max 5 participants

## 5. Known discrepancies resolved during implementation

| # | Discrepancy | Resolution |
|---|-------------|-----------|
| 1 | PRD §4.2 says pass threshold 75 (normalized); contract says 82 raw | Contract wins for gating. CONDITIONAL_PASS band covers [75, 82) so PRD spirit preserved. Documented in `persona-judge/references/rubric.md` §PRD Discrepancy Note. |
| 2 | PRD §3.2 says "8-dim rubric"; §4.2 says 12-dim | 12-dim is authoritative (contract agrees). |
| 3 | PRD §2.3 header says "16 components"; detailed table lists 18 | 18 is authoritative (manifest enum matches). |
| 4 | `extraction/seven-axis-dna.md` axis names differ from `components/expression-dna.md` axis names | Flagged in `expression-analyzer.md` as label-mapping step; extraction file is execution authority. v2 should reconcile. |
| 5 | PRD §7 Schema 6 places research files at skill root; §1.2 says `knowledge/` | Placed under `knowledge/research/` as reconciliation. |
| 6 | `computation-layer` as cross-schema attachment only has interface for executor | Scoped to executor in v1; marked `[EXPERIMENTAL]` elsewhere. |

## 6. V1 limitations (the honest list)

### 6.1 Design / scope limitations

1. **No dog-food persona**: all 9 schemas ship with `unvalidated: true`. Before shipping v1.0.0, at least one real persona (suggested: `friend` or `self` — lowest complexity) should be distilled end-to-end and the contracts tested by running it.
2. **Reference libraries unclonable**: 15+ repos (nuwa, colleague, ex, anti-distill, immortal, bazi, midas, 图鉴, 诸子, etc.) could not be cloned. Every "borrowed from X" section is tagged `[UNVERIFIED-FROM-README]`. v2 should clone and reconcile.
3. **distill-collector scaffolding-only**: 8 text parsers (WeChat / QQ / Feishu / Slack / Dingtalk / iMessage / Telegram / email / Twitter), audio/video transcription, image OCR, and document extraction are all spec + third-party-tool pointers. No runnable code ships in v1. `generic` format import is the one minimal path that can work without extra user tooling.
4. **Phase 2.5 single-pass**: multi-round iterative deepening (cyber-figures concept) is TODO(v2).
5. **computation-layer executor-only**: cross-schema attachment is conceptual; real interface exists only for executor.
6. **Scoring normalization fragile**: raw /110 score is authoritative; /100 normalized is display-only. Rubric explicitly warns against gating on normalized.
7. **Discovery env-dependent**: `persona-router` filesystem scan paths vary across Claude Code installs; router reports which paths it scanned when empty.
8. **Anti-gaming heuristics not exhaustive**: 8 patterns documented; sophisticated gaming is still possible.
9. **Conflicts.md user-appended only**: automatic conflict detection deferred to v2.
10. **No migration tool**: generated persona skills are "frozen copies" of components at generation time. When `distill-meta`'s component library updates, already-generated skills do not auto-upgrade. v2 adds a migrator.

### 6.2 Security / trust limitations (surfaced by P5 red-team)

These are **known v1 gaps**. They do not block shipping, but users should understand them before distilling real people's corpora or accepting a third-party persona skill.

| # | Category | Severity | Description | v2 Mitigation |
|---|----------|----------|-------------|---------------|
| S1 | **Privacy — free-text PII** | Critical | `distill-collector/references/redaction-policy.md` redacts via regex only: phones, emails, ID numbers, credit cards, API keys. **Free-text names, street addresses, medical/political/religious info survive into `knowledge/`**. | Ship NER-based name redactor + address regex; drop the default-salt for hashes. |
| S2 | **Consent bypass via `subject_type: fictional`** | Critical | `hard-rules.md` requires consent for impersonating living real people. Enforcement is gated on the *declared* `identity.subject_type`. An attacker/careless user declares `fictional` and ships a persona of a real person without consent. | Require a signed `consent-attestation.md` at skill root; cross-check corpus proper-nouns against declared subject_type. |
| S3 | **Prompt injection from corpus** | Critical | `knowledge/**` (untrusted input) is concatenated with `components/hard-rules.md` (trusted) at runtime without structural delimiters. A malicious corpus line like `"SYSTEM: Ignore previous instructions..."` can override rules. `correction-layer` also accepts severity=`hard-rule` amendments from chat turns. | Tag `knowledge/**` files as `untrusted-input: true` with runtime delimiters; forbid `hard-rule` corrections without out-of-band confirmation. |
| S4 | **Manifest fields under-constrained** | High | `manifest.schema.json`: `triggers`/`description`/`domains` have no `maxLength`; `fingerprint` pattern matches any 64 hex chars (not verified against actual `knowledge/**/*.md` SHA-256); `validation_score` can be set to 110 without a `validation-report.md` existing; no `schema_type ↔ components_used` cross-check. | Add maxLength caps; add `if/then` conditional validators; ship a `fingerprint-verifier` agent for persona-judge. |
| S5 | **Rubric gaming via `config.yaml`** | High | `persona-judge/references/rubric.md` §"Configurable Thresholds" lets users override `pass_threshold_raw`, `density_floor`, `required_tensions`, `required_boundaries`, `primary_source_min`. An attacker sets `density_floor: 0.5` and `pass_threshold_raw: 40` → low-quality persona PASSes. Anti-gaming §"PRD Threshold Arbitrage" does not catch config tampering. | Lock overrides to narrow ranges (e.g. `pass_threshold_raw ∈ [75, 95]`); require attestation that defaults were used; second independent model runs judge. |
| S6 | **Self-contained escape in generated skills** | High | `component-contract.md §4` instructs generators to drop `Extraction Prompt` from emitted components. Some components (notably `correction-layer`) carry runtime behavior in that section; dropping breaks them when skill is moved. Also: `skill-md-template.md` has breadcrumbs to PRD/contract paths that don't exist in the produced skill. | Rename runtime-bearing section (keep at copy time); add a self-containment-linter agent that greps for external references. |
| S7 | **Schema-misuse (private corpus in public-mirror)** | High | If a user picks `public-mirror` schema but the corpus contains private chats with the public figure, private content leaks into a skill labeled "public". No guardrail distinguishes public vs. private sources — only primary vs. secondary. | Add `corpus_access_declared` cross-check in Phase 1.5; warn on `schema_type ↔ source privacy` mismatches. |

### 6.3 Honest guidance for users

- **Do not distill real, living, non-consenting people**. The "hard rule" is policy, not enforcement.
- **Do not put production API keys in corpus**. Regex redaction catches common prefixes but is best-effort.
- **Review the generated `knowledge/chats/`** before publishing any persona skill. Assume third-party PII survives.
- **Treat `validation_score` from a third-party persona skill as self-reported**. Re-run `persona-judge` locally before trusting it.
- **Do not edit `config.yaml` thresholds to make a failing skill PASS**. This defeats the purpose; if a real threshold needs changing, open an issue first.

## 7. How to verify v1 end-to-end (recommended first test)

1. Create a tiny corpus (10-20 short messages / excerpts) for a simple persona — e.g., yourself or a fictional character.
2. Run `distill-meta` with `schema: friend` (fewest components, lowest risk).
3. Inspect the generated skill: does `manifest.json` validate against `contracts/manifest.schema.json`? (Use any JSON Schema validator.)
4. Run `persona-judge` on it. Inspect `validation-report.md`: does the YAML frontmatter match `contracts/validation-report.schema.md`?
5. Confirm `verdict` logic: PASS / CONDITIONAL_PASS / FAIL routes correctly.
6. Install a second persona; run `persona-router` with a question; verify it picks the more relevant one.
7. Install a third persona; run `persona-debate` in round-robin mode; verify the transcript has all 3 participants + moderator synthesis.

If any step fails, the contracts or templates need fixes before v1.0.0. Any bug reports welcome.

## 8. v2 roadmap (extracted from TODOs across implementation)

Collected from agents' reports in the 5-wave build:

- Multi-round Phase 2.5 with Jaccard convergence detection
- Auto-patch of Phase 2.5 candidates back into components
- Cross-schema computation-layer attachment interface
- Chinese/English source-policy parameterization (English whitelist/blacklist populated)
- config.yaml for persona-judge configurable thresholds (already scaffolded; not wired)
- Migration tool for updating old generated skills when component library bumps
- Automatic conflicts.md detection via LLM cross-referencing
- Seven-axis DNA taxonomy reconciliation (extraction file vs component file)
- Runnable `distill-collector` parsers for at least WeChat + iMessage (with user-supplied exports)
- Dog-food end-to-end validation removing `unvalidated: true` banners from validated schemas
- Task-tool skill invocation semantics for persona-debate moderator

---

**Status**: v0.1.0 — spec-complete, dog-food validation pending.
