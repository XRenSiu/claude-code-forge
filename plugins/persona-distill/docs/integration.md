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
| 7 (v0.4.0) | Security hardening: `contracts/consent-attestation-contract.md` + `contracts/untrusted-corpus-contract.md` + `agents/fingerprint-verifier.md` + `agents/self-containment-linter.md` + `persona-judge/config.yaml` + `persona-judge/config.schema.json` + `scripts/telegram_parser.py` + `scripts/slack_parser.py` + redactor.py v0.3 (CN-ADDR/ADDR/CN-NAME/FLAG). Edits to hard-rules.md, correction-layer.md, honest-boundaries.md, primary-vs-secondary.md, manifest.schema.json, rubric.md, text-parsers.md, redaction-policy.md, skill-md-template.md, distill-meta SKILL.md (Phase 3.8 + 0-Gate). | 8 new + 11 edited |

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
3. **distill-collector partial-runnable** (v0.4.0): 6 runnable paths ship (iMessage / email / Twitter / generic / Telegram / Slack via `scripts/`); 4 chat platforms (WeChat / QQ / Feishu / Dingtalk) + AV pipeline + image OCR / document extraction remain spec-only due to volatile third-party export formats. Users of remaining platforms must wire their own export → `generic_import.py`.
4. **computation-layer executor-only**: cross-schema attachment is conceptual; real interface exists only for executor.
5. **Scoring normalization fragile**: raw /110 score is authoritative; /100 normalized is display-only. Rubric explicitly warns against gating on normalized.
6. **Discovery env-dependent**: `persona-router` filesystem scan paths vary across Claude Code installs; router reports which paths it scanned when empty.
7. **Anti-gaming heuristics not exhaustive**: 8 patterns documented; sophisticated gaming is still possible.
8. **Phase 3.5 conflict detection is heuristic** (v0.2.0): LLM-driven cross-referencing surfaces obvious contradictions but can miss subtle shifts; agent only surfaces, never resolves — user is final arbiter.
9. **Migration tool detects but does not auto-resolve user edits** (v0.2.0): user-modified component files in a produced persona skill are REFUSED for auto-patch; migrator falls back to diff display only.
10. **Community schemas require manual PR review** (v0.2.0): no automated CI for `schema-extension-contract.md` conformance yet; human maintainer review is the gate.
11. **execution-profile is LLM-simulated CTA, not real CDM interviews** (v0.3.0): CTA/CDM are originally **human-interviewing-human** methods. This plugin runs the protocol by having an LLM "interview" pre-existing corpus. Some probes (notably Sweep 3's `time_pressure` and `hypotheticals`) have no real counterfactual ground truth — they can only be inferred from the material. This **caps extraction quality**: better than asking Claude to summarize in one shot, but short of true expert elicitation. Exact loss has not been measured; `cdm-4sweep.md §Honest Limitation Admission` states this directly. A controlled A/B (skill with vs. without execution-profile on the same task set) is a v1.0.0 dog-food prerequisite.
12. **execution-profile's red-line 2 threshold is conservative** (v0.3.0): Klein's field data says ~80% of expert decisions are RPD-style (not analytical list-compare). The red-line triggers at >50% list-compare rather than >20%, to avoid false positives on legitimately analytical personas (quant traders, statisticians, regulators). If multiple public-mirror / mentor skills hit false-positive red-line-2 fails, the threshold should tighten to 30%.
13. **execution-profile only ships for public-mirror + mentor** (v0.3.0): other schemas (`self`, `collaborator`, `friend`, `loved-one`, `public-domain`) are expansion candidates but not yet validated. Those schemas set `execution_profile_completeness: not_applicable` in manifest. `topic` and `executor` are permanently excluded (no event-based personas).

### 6.2 Security / trust limitations

**v0.4.0 ships mitigations for all 7 original gaps (S1-S7)**. Each gap is
now marked **Partially closed** — the gap is smaller but not eliminated;
the "v2 Mitigation" column records the residual hole and what's still
needed. Users should still read each row before distilling real corpora.

| # | Category | Original Severity | Description | v0.4.0 Status | Residual Gap |
|---|----------|-------------------|-------------|---------------|--------------|
| S1 | **Privacy — free-text PII** | Critical | Regex-only redaction let names / addresses / medical+political+religious topics survive. | **Partially closed (v0.4.0)**: redactor v0.3 adds CN-ADDR, ADDR (Western), CN-NAME (introducer-gated), and FLAG:MEDICAL/POLITICAL/RELIGIOUS inline tags. | CN-NAME still misses non-introducer mentions; English / mixed-script names unhandled; full NER is v2 work. |
| S2 | **Consent bypass via `subject_type: fictional`** | Critical | No file-level attestation required. | **Partially closed (v0.4.0)**: `contracts/consent-attestation-contract.md` + Phase 0 gate + `manifest.consent_attestation` object required when `subject_type ∈ {real-person, composite}`. | Attacker can still declare `fictional` to bypass; no signature verification. Corpus proper-noun cross-check is v0.5. |
| S3 | **Prompt injection from corpus** | Critical | No structural separation between trusted rules and untrusted corpus. | **Partially closed (v0.4.0)**: `contracts/untrusted-corpus-contract.md` defines `<<<UNTRUSTED_CORPUS …>>>` delimiters; `hard-rules.md` mandates the Untrusted-Corpus Discipline paragraph verbatim; `correction-layer.md` gates `severity: hard-rule` corrections behind out-of-band confirmation. | Delimiters are a heuristic, not a sandbox. Sophisticated multi-step prompt-injection chains may still confuse the LLM. |
| S4 | **Manifest fields under-constrained** | High | No maxLength caps; `fingerprint` unverifiable against `knowledge/`; no schema_type ↔ components_used cross-check. | **Partially closed (v0.4.0)**: manifest schema v0.4 adds maxLength (triggers 200 / description 2000 / domains/items 80) + maxItems 20 on triggers/domains. `schema_type`-specific `allOf` rules require public-mirror to include {identity, mental-models, decision-heuristics, expression-dna} and executor to include {computation-layer, interpretation-layer}. `agents/fingerprint-verifier.md` recomputes hashes in Phase 3.8 pre-check + persona-judge Manual mode. | `validation_score` still settable without a real validation-report; full schema_type coverage (7 more schemas) is v0.5. |
| S5 | **Rubric gaming via `config.yaml`** | High | Thresholds were freely overridable, letting attackers set `density_floor: 0.5`. | **Closed (v0.4.0)**: `persona-judge/config.schema.json` locks every threshold to a sane range; persona-judge rejects out-of-range config at load time (`exit 3`). Config SHA-256 recorded in validation-report. | None for config-based gaming. A second-judge independent run is still v2 (redundant but blocks judge-collusion). |
| S6 | **Self-contained escape in generated skills** | High | Single `grep` in migrator missed subtle leakage (absolute paths, PRD anchors, broken internal links). | **Closed (v0.4.0)**: `agents/self-containment-linter.md` runs 6 checks in new Phase 3.8 and in migrator step 6. Any failure blocks Phase 4 / reverts migration. | None. Linter covers the documented attack surfaces. |
| S7 | **Schema-misuse (private corpus in public-mirror)** | High | No public/private distinction on sources. | **Partially closed (v0.4.0)**: `source-policies/primary-vs-secondary.md` v0.2 adds `access_level` (public / semi-public / private) orthogonal to tier. `manifest.corpus_access_declared` is required when mixed; Phase 1.5 warns on `schema_type=public-mirror` + non-public-only corpus AND `consent_method=implicit-public-figure` + non-public-only corpus. Slack parser tags `channels/*` as semi-public; Telegram tags everything as private. | Warning is advisory — user can still proceed. Hard-fail is v0.5. |
| S8 | **execution-profile red-line self-report via manifest fabrication** (v0.3.0) | Medium | persona-judge read producer's self-reported Red-Line Summary. | **Partial**: rubric §Anti-Gaming catches obvious fabrication via sampled evidence grep. | Independent re-check in persona-judge still v2. |

**Summary**: 7 gaps, 5 partially closed + 2 fully closed. v0.5 roadmap
addresses residuals (NER redactor, corpus proper-noun cross-check, full
schema coverage in components_used, hard-fail on access-level mismatch,
independent red-line re-check).

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

## 8. v2 roadmap (post-v0.4.0)

Shipped in v0.4.0: **7 security/trust gaps partially or fully closed**.
`contracts/consent-attestation-contract.md` (S2) + `contracts/untrusted-corpus-contract.md` (S3) added as 5th and 6th contracts. `agents/fingerprint-verifier.md` + `agents/self-containment-linter.md` added — both run in new **Phase 3.8** between execution-profile extraction and persona-judge. `persona-judge/config.yaml` + `config.schema.json` lock threshold overrides to sane ranges (S5, closed). `redactor.py` v0.3 adds Chinese/Western addresses + Chinese name heuristics + sensitive-topic flags (S1 partial). `primary-vs-secondary.md` v0.2 adds `access_level` dimension (S7). `manifest.schema.json` v0.4 adds maxLength caps, schema_type↔components_used cross-checks, consent_attestation field (S4 partial). 2 new parsers: `telegram_parser.py` + `slack_parser.py` (6 runnable total).

Shipped in v0.3.0: `execution-profile` component + `cdm-4sweep` extraction + Phase 3.7 + persona-judge rubric v0.2.0 (Mindset Transfer ±1 red-line coupling + 2 anti-gaming entries) + manifest schema v0.3.0 enum addition + migrator new-component discovery. Public-mirror and mentor schemas carry execution-profile as optional component.

Shipped in v0.2.0 (still removed from roadmap): multi-round Phase 2.5 with Jaccard convergence, auto-patch of candidates, migration tool, automatic conflicts.md detection, runnable iMessage/email/twitter/generic parsers.

Remaining:

**v0.4.0-derived roadmap (new):**

- **NER-based name redactor** (closes S1 residual): replace regex-only CN-NAME heuristic with a proper NER model. Requires dropping the "stdlib-only" rule for the redactor or shipping a small model file. Open question: local tiny-NER (spaCy / fastText) vs. LLM-call per paragraph.
- **Corpus proper-noun cross-check against declared `subject_type`** (closes S2 residual): at Phase 1.5, count distinct proper nouns in `knowledge/` and compare against `identity.name`. If `subject_type: fictional` but corpus is dominated by one real-name proper noun, warn or block.
- **Full schema_type ↔ components_used cross-check**: v0.4.0 covers public-mirror + executor; extend to the other 7 schemas.
- **Hard-fail on access-level mismatch** (closes S7 residual): v0.4.0 warns at Phase 1.5; v0.5 should halt and require user to either reclassify schema or strip private corpus.
- **Independent red-line re-check in persona-judge** (closes S8): recompute red-line summary from `knowledge/` evidence chains rather than reading producer's self-report.
- **Second-judge independent run** (defense-in-depth on S5): once config ranges are locked, a second LLM judge with different model family can catch ratings the first judge got wrong.
- **Parser coverage** (WeChat / QQ / Feishu / Dingtalk): the 4 remaining platforms. WeChat + QQ need proven third-party DB decryption tools stable enough to wrap; Feishu + Dingtalk need enterprise compliance export samples. Still constrained by stdlib-only.

**v0.3.0-derived roadmap:**

- **Phase 3.7 → Phase 2 consolidation**: `execution-profile-extractor` only truly depends on `knowledge/` + `identity.md` + (optional) `expression-dna.md`, so architecturally it could run in Phase 2 parallel with `mental-model-extractor` / `expression-analyzer`. Phase 3.7 was chosen for minimum disruption of existing Phase 2 orchestration. Consolidation pushes total phase count back down to 7.
- **execution-profile schema expansion**: extend to `self`, `collaborator`, `friend`, `loved-one`, `public-domain` — bilateral declaration required (both the component's `optional_for_schemas` and each schema's `optional_components:` must list it). Blocked on: dog-food evidence that the CDM 4-sweep produces usable output on smaller / more private corpora than public-mirror/mentor.
- **CTA fidelity controlled experiment**: A/B test — distill the same persona (a) without execution-profile (b) with execution-profile, give both to the same task set, blind-judge which produces more persona-specific decisions. Quantifies the "LLM-simulates-human-interviewer" quality cap. v1.0.0 dog-food prerequisite.
- **Red-line 2 threshold calibration**: current 50% list-compare cutoff is conservative vs. Klein's 80/20 field data. If dog-food shows few false positives on legitimately analytical personas, tighten to 30%.
- **execution-profile independent red-line re-check in persona-judge** (closes S8): don't trust producer's self-reported `Red-Line Summary`; recompute from `knowledge/` evidence chains.
- **execution-profile trace file optional compression**: `execution-profile-trace.md` can grow large on rich corpora (~10 incidents × ~3 decision points × 10 probes ≈ 300 entries). Consider gzip-compressing as `execution-profile-trace.md.gz` for persona skills > 1MB total.

**v0.2.0-derived roadmap (unchanged):**

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
