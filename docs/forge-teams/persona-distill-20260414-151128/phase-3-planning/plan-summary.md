# Phase 3 Plan Summary — persona-distill-ecosystem

- **Total tasks**: 61 (58 implementation + 3 contracts)
- **Waves**: 5
- **Estimated files created**: ~110
- **Plugin**: `plugins/persona-distill/`
- **Skills**: distill-meta, persona-judge, distill-collector, persona-router, persona-debate

## Wave breakdown

| Wave | Tasks | Purpose | Max Parallelism |
|------|-------|---------|-----------------|
| 1 | T001-T006 + CONTRACT-01/02/03 (9) | Plugin scaffolding + 5 SKILL.md entrypoints + 3 integration contracts | 9-way |
| 2 | T007-T029 (23) | distill-meta references: 9 schemas, 16 components (batched as 5 tasks), 5 extraction frameworks, 3 source policies, output-spec + persona-judge rubric | 23-way |
| 3 | T030-T044 (15) | 9 distill-meta agents + 3 templates + 3 persona-judge internals | 15-way |
| 4 | T045-T054 (10) | distill-collector (5) + persona-router (3) + persona-debate (2) | 10-way |
| 5 | T055-T058 (4) | README, LICENSE, integration doc, marketplace.json bump | 3-way + serial |

## Key risk-mitigation structure (from risk-assessor)

- **Contracts-first**: Wave 1 includes CONTRACT-01/02/03 (manifest schema, validation-report schema, component contract) before any downstream implementation, so persona-judge/router/debate have a stable target.
- **File ownership**: All `files_owned` paths disjoint across wave; only `.claude-plugin/marketplace.json` is SHARED — serialized into T057 alone.
- **distill-collector scoped to reference-spec-only**: No runtime parsers shipped (Whisper/yt-dlp/WeChat SQLite extraction are user-environment-dependent). Deliverable is CLI spec + parser contracts + detect-and-instruct stubs.
- **Reference repos unclonable (PRD §10)**: All "抄 nuwa/colleague" tasks re-derive from the fragments already quoted in the master plan; any gaps get an inline `[UNVERIFIED]` marker.
