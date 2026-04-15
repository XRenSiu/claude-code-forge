---
name: integration
description: Cross-skill wiring, interface contracts, and known limitations for persona-distill v0.2.0
version: 0.2.0
---

# persona-distill — Integration & Known Limitations

> How the 5 skills and 4 contracts wire together, what v0.2.0 added on top of v0.1.0, and the honest list of remaining gaps.

## v0.2.0 change summary

- **Phase 2.5 upgraded to multi-round** with Jaccard convergence detection (≤ 3 rounds) + auto-patch-back via new `candidate-merger` agent. Single-pass v0.1.0 behavior preserved as `max_rounds=1` back-compat.
- **Phase 3.5 Conflict Detection** added (new `conflict-detector` agent + `extraction/conflict-detection.md`). Writes `knowledge/conflicts.md` with 4 conflict kinds (factual / value-shift / stated-vs-behavioral / component-self); strictly separated from `internal-tensions` (stable polarities). Agent never auto-resolves; `suggested_handling` ∈ {PRESERVE_BOTH, FLAG_FOR_USER, TIMEBOUND}.
- **distill-collector partial-runnable**: 4 of 12 parsers runnable (iMessage / email / twitter / generic) via stdlib-only Python in `scripts/`. `redactor.py` embeds §6.1/§6.2 test vectors as self-tests. Remaining 6 chat platforms + AV pipeline + image/doc pipeline remain spec-only (third-party tool dependencies).
- **Migration tool** (new `migrator.md` agent + `references/migration.md` + `templates/migration-plan-template.md`): upgrades previously-generated persona skills when component library bumps. Preserves self-containment (grep -r "distill-meta" must return 0 after migration). PLAN/APPLY modes; rollback via snapshot; user-edited files refused.
- **Schema community extension** (new `contracts/schema-extension-contract.md` + `docs/schema-contribution-guide.md` + `references/schemas/community/` discovery directory). Core 9 schemas + community schemas; `manifest.schema_type_origin: core|community` differentiates.
- **Manifest schema bumped to v0.2.0** with 5 new migration fields (`distill_meta_version`, `components_fingerprint`, `last_migrated_at`, `migration_history[]`, widened `components_used[]` via oneOf for backward compat) + 2 community fields (`schema_type_origin`, `schema_type_author`). All additions are additive; v0.1.0 manifests still validate.
- **Contracts count: 3 → 4** (added `schema-extension-contract.md`).

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
| `contracts/manifest.schema.json` (v0.2.0) | `distill-meta` (via `templates/manifest-template.json` at generation time); `migrator` (on upgrade) | `persona-judge`, `persona-router`, `persona-debate`, any produced persona skill |
| `contracts/validation-report.schema.md` | `persona-judge` | `distill-meta` (Phase 4 gate in `agents/validator.md`); user (standalone eval) |
| `contracts/component-contract.md` | `distill-meta` (every file in `references/components/`) | All 9 core + community schemas; `persona-judge` rubric validates conformance |
| `contracts/schema-extension-contract.md` (v0.2.0 new) | community contributors | `distill-meta` Phase 0.5 discovery validates each community schema before loading |

**Schema extensibility**: the `references/schemas/community/` subdirectory is a discovery sibling of the 9 core schema files. `distill-meta` Phase 0.5 enumerates both directories, validates community files against `contracts/schema-extension-contract.md`, and builds a deterministic ordered schema list (core canonical-order + community alphabetical). Failing community files are logged (`schema_extension_warn:`) and skipped — never loaded. Persona skills produced from a community schema carry `schema_type_origin: community` + `schema_type_author` in their manifest, allowing `persona-router`, `persona-judge`, and `persona-debate` to differentiate at downstream consumption time without breaking the contract hub.

## 3. Wave-by-wave implementation record

See `../../docs/forge-teams/persona-distill-20260414-151128/phase-3-planning/plan.json` for the full 61-task decomposition. Delivered in 5 waves:

| Wave | Purpose | Files |
|------|---------|-------|
| 1 | Scaffolding + 3 contracts + 5 SKILL.md entrypoints | 9 |
| 2 | distill-meta references (decision tree, 9 schemas, 18 components, 5 extraction frameworks, 3 source policies, output-spec) + persona-judge rubric | 38 |
| 3 | 9 distill-meta agents + 3 templates + 3 persona-judge internals | 15 |
| 4 | distill-collector (5) + persona-router (3) + persona-debate (2) | 10 |
| 5 | README, LICENSE, this integration doc, marketplace.json registration | 4 |
| 6 (v0.3.0) | Phase 3.7 addition: `references/extraction/cdm-4sweep.md` + `references/components/execution-profile.md` + `agents/execution-profile-extractor.md` (+ manifest schema enum + rubric anti-gaming entries) | 3 new + 7 edited |

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
3. **distill-collector partial-runnable** (v0.2.0): 4 runnable paths ship (iMessage / email / twitter / generic via `scripts/`); 6 chat platforms (WeChat / QQ / Feishu / Slack / Dingtalk / Telegram) + AV pipeline + image OCR / document extraction remain spec-only due to volatile third-party export formats. Users of remaining platforms must wire their own export → `generic_import.py`.
4. **computation-layer executor-only**: cross-schema attachment is conceptual; real interface exists only for executor.
5. **Scoring normalization fragile**: raw /110 score is authoritative; /100 normalized is display-only. Rubric explicitly warns against gating on normalized.
6. **Discovery env-dependent**: `persona-router` filesystem scan paths vary across Claude Code installs; router reports which paths it scanned when empty.
7. **Anti-gaming heuristics not exhaustive**: 8 patterns documented; sophisticated gaming is still possible.
8. **Phase 3.5 conflict detection is heuristic** (v0.2.0): LLM-driven cross-referencing surfaces obvious contradictions but can miss subtle shifts; agent only surfaces, never resolves — user is final arbiter.
9. **Migration tool detects but does not auto-resolve user edits** (v0.2.0): user-modified component files in a produced persona skill are REFUSED for auto-patch; migrator falls back to diff display only.
10. **Community schemas require manual PR review** (v0.2.0): no automated CI for `schema-extension-contract.md` conformance yet; human maintainer review is the gate.

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

## 8. v2 roadmap (post-v0.2.0)

Shipped in v0.2.0 (removed from roadmap): multi-round Phase 2.5 with Jaccard convergence, auto-patch of candidates, migration tool, automatic conflicts.md detection, runnable iMessage/email/twitter/generic parsers.

Remaining:

- Cross-schema computation-layer attachment interface (still executor-only).
- Chinese/English source-policy parameterization (English whitelist/blacklist populated).
- config.yaml for persona-judge configurable thresholds (scaffolded; not wired).
- Seven-axis DNA taxonomy reconciliation (v0.2.0 applied alias-table bandage; v2 should canonicalize short-names).
- Runnable `distill-collector` parsers for WeChat + QQ + Feishu + Slack + Dingtalk + Telegram + AV pipeline + OCR / document extraction (all still spec-only).
- Dog-food end-to-end validation removing `unvalidated: true` banners from validated schemas (v1.0.0 prerequisite).
- Task-tool skill invocation semantics for persona-debate moderator.
- `5layer / 6layer` DRY refactor (duplicated paragraphs).
- `manifest.schema.json` maxLength caps + `fingerprint-verifier` agent (closes S4).
- Untrusted-input delimiter convention for corpus-in-prompt concatenation (closes S3).
- NER-based free-text PII redactor (closes S1).
- Signed `consent-attestation.md` + corpus proper-noun cross-check (closes S2).
- `pass_threshold_raw` lock-range + second-judge independent run (closes S5).
- Self-containment-linter agent + rename "Extraction Prompt" → preserve-at-copy section (closes S6).
- `source_privacy` dimension across source-policies + Phase 1.5 public-vs-private gate (closes S7).
- CI for `schema-extension-contract.md` conformance (automated community PR validation).

---

**Status**: v0.2.0 — spec-complete; 4 runnable parser paths; multi-round Phase 2.5, Phase 3.5 conflict detection, migration tool, and community schema extension mechanism all wired. Dog-food validation still pending for v1.0.0.
