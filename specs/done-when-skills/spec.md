# Spec: done-when-skills

## REQ-001 (Event-driven) — acceptance-spec slash command exists and is discoverable
WHEN the user invokes the slash command `/acceptance-spec`,
THE Claude Code marketplace registry SHALL surface a skill named `acceptance-spec` declared `user-invocable: true` whose `name:` frontmatter field equals `acceptance-spec` and whose `version:` is a valid SemVer string.
source: clarify Q01 / Q02; SKILL.md `user-invocable: true` line.

## REQ-002 (Event-driven) — acceptance-spec consumes a NL brief and writes four files
WHEN the `acceptance-spec` skill is invoked with a natural-language requirement,
THE skill SHALL, on successful completion, write exactly four artifacts into a feature output directory: `proposal.md`, `spec.md`, `tasks.md`, `done_when.yaml`.
source: clarify Q02; source doc §5.3.

## REQ-003 (Ubiquitous) — acceptance-spec enforces a strict clarify protocol
THE `acceptance-spec` skill SHALL, in its SKILL.md, state explicitly:
  (a) that only three question types are legal during clarify (`ambiguity` / `missing edge` / `undefined term`);
  (b) a per-round question budget of 3-5;
  (c) a maximum-round hard cap of 5;
  (d) a stop-and-split bail-out when round 5 still has open [?].
source: clarify Q04; source doc §4.3-4.4.

## REQ-004 (Ubiquitous) — the done_when.yaml schema documented by acceptance-spec matches source-doc Appendix C
THE done_when schema documented at `acceptance-spec/references/done-when-schema.yaml` SHALL contain the following top-level keys: `feature`, `based_on`, `existence`, `behavior` (with sub-keys `unit_tests`, `integration_tests`, `e2e_tests`, `thresholds`), `fitness`, `spec_drift_threshold`.
source: clarify Q03; source doc Appendix C.

## REQ-005 (Event-driven) — test-suite-generator slash command exists and is discoverable
WHEN the user invokes the slash command `/test-suite-generator`,
THE Claude Code marketplace registry SHALL surface a skill named `test-suite-generator` declared `user-invocable: true` whose `name:` frontmatter equals `test-suite-generator` and whose `version:` is a valid SemVer string.
source: clarify Q01.

## REQ-006 (Event-driven) — test-suite-generator accepts both input shapes
WHEN `test-suite-generator` is invoked with EITHER a `specs/<feature>/` directory path OR a `done_when.yaml` path,
THE skill's SKILL.md SHALL document acceptance of both input shapes in its S0/bootstrap section.
source: clarify Q07.

## REQ-007 (Ubiquitous) — test-suite-generator covers all six pyramid layers
THE `test-suite-generator` skill SHALL provide a dedicated reference sub-module for each of the six pyramid layers: existence-extractor, unit-test-generator, integration-generator, e2e-generator, mutation-config, fitness-rubric.
source: clarify Q08; source doc §6.1; SKILL.md resource index.

## REQ-008 (Ubiquitous) — test-suite-generator covers the PBT property archetypes
THE `test-suite-generator` skill SHALL document the six PBT property archetypes (`invariant`, `idempotent`, `reversible`, `boundary`, `monotonic`, `state_machine`) at `references/pbt-property-types.md`, each with at least one runnable code example per supported language.
source: clarify Q11; SKILL.md iron rule 3.

## REQ-009 (Ubiquitous) — test-suite-generator covers all supported language tool stacks
THE `test-suite-generator` skill SHALL document concrete tool-stack choices at `references/tooling-by-language.md` for at least: Python, TypeScript/JavaScript, Swift, Kotlin/Java, and a cross-language layer (ripgrep / tree-sitter / Playwright).
source: clarify Q10; source doc §10.1.

## REQ-010 (Ubiquitous) — mutation testing is documented as mandatory, not optional
THE `test-suite-generator` skill SHALL state explicitly (in SKILL.md iron rules AND in `references/anti-cheating-mutation.md`) that mutation_kill_rate >= 0.70 is a mandatory threshold, with rationale tied to anti-reward-hacking.
source: source doc §6.6 (anti-cheating section); SKILL.md iron rule 5.

## REQ-011 (Ubiquitous) — fitness rubric guide warns about bad-rubric harm
THE `test-suite-generator` skill SHALL, in `references/fitness-rubric-guide.md`, cite the empirical finding that naively-written rubrics drop judge accuracy (with specific numbers: 55.6% → 42.9% on JudgeBench) and provide a structured-anchors template.
source: source doc §6.7 (重要警告); SKILL.md S4-F.

## REQ-012 (Ubiquitous) — ratchet integration is documented HONESTLY as a manual hand-off
THE plugin SHALL document, in INTEGRATION.md, the actual ratchet hand-off: that ratchet does NOT auto-parse `done_when.yaml`, that the user manually translates our outputs into ratchet's Goal/Criteria/Scope/done_when format, and that `spec_drift_threshold:` is guidance for the human translator (mapping to ratchet's `convergence` field) — not an auto-honored field.
source: clarify Q15 / Q16 (re-resolved Round 2 after ISSUE-002 fix).

## REQ-013 (Ubiquitous) — fitness-judge handoff is documented HONESTLY (no fictitious dependencies)
THE plugin SHALL, in INTEGRATION.md and `fitness-rubric-guide.md` and `sub-modules/fitness-rubric.md`:
  (a) NOT claim that `persona-judge` from persona-distill consumes fitness rubrics (it does not — it evaluates persona-skill quality);
  (b) document the `llm-rubric` rubric format as designed for a manual fresh-Claude-session workflow with no packaged automation today;
  (c) NOT reference any persona names that do not exist in `persona-distill` (the invented `integration-engineer-persona` / `non-technical-end-user-persona` / `oncall-sre-persona` must be replaced with self-contained audience-archetype blocks).
source: clarify Q17 / Q18 (re-resolved Round 2 after ISSUE-003 fix).

## REQ-014 (Ubiquitous) — plugin is correctly registered in the marketplace
THE plugin `done-when-pipeline` SHALL be registered in `.claude-plugin/marketplace.json` AND in `~/.claude/settings.json` `enabledPlugins`, with consistent `name` and `version` across `marketplace.json`, `plugin.json`, and both `SKILL.md` files.
source: clarify Q19; CLAUDE.md version-management rules.

## REQ-015 (Unwanted) — every reference file mentioned by SKILL.md exists on disk
IF a SKILL.md mentions a reference file under `references/`,
THEN THE referenced file SHALL exist at the stated path.
source: implicit from resource-index sections of both SKILL.md.

## REQ-016 (Ubiquitous) — the worked example is internally consistent
THE worked example under `acceptance-spec/references/examples/subscription-cancellation/` SHALL satisfy: every REQ-ID referenced in `done_when.yaml.based_on` (top-level and per-entry) exists in `spec.md`; every test name's `based_on:` refers only to existing REQ-IDs; the `existence:` entries do not conflict with the `tasks.md` decomposition.
source: implicit consistency requirement; SKILL.md S3 contract.

## Glossary

- **done_when.yaml** — the machine-verifiable acceptance contract produced by acceptance-spec; schema in source doc Appendix C. (source: clarify Q03)
- **EARS spec** — strictly the five-sentence-type EARS syntax with stable REQ-IDs, traceable via `source:` lines back to clarify rounds. (source: clarify Q04)
- **integration with ratchet** — manual hand-off: the user composes ratchet's Goal/Criteria/Scope/done_when by translating from our spec.md, tests/ tree, and done_when.yaml's thresholds. Ratchet itself does not parse our YAML; it runs its own Step 1-3 to derive its own evaluate.sh. (source: clarify Q15 re-resolved Round 2)
- **integration with fitness-judge** — there is no packaged fitness-judge skill. `llm-rubric` rubric files are scored by a fresh Claude session per the rubric's how-to-run block (manual workflow). The earlier mention of persona-judge from persona-distill was a category error and has been removed. (source: clarify Q17 re-resolved Round 2)
- **fitness rubric** — markdown file with structured sub-dimensions (3-7), concrete anchors at each score level, weighted aggregation, persona name. (source: clarify Q13)
- **mandatory mutation kill rate** — 0.70 minimum; anti-reward-hacking gate, not a stylistic preference. (source: source doc §6.6)
