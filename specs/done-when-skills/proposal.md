# Proposal: done-when-skills

## Why
The `done-when-pipeline` plugin contains two skills (`acceptance-spec`, `test-suite-generator`) that claim to implement Steps 1-4 of the `done-when-pipeline.md` design doc. Without an independent check, we cannot tell whether the implementation matches the design or whether each skill, when run faithfully on real input, actually produces what its SKILL.md and references promise.

## What
This meta-spec treats "do the two skills conform to design" as a feature. It encodes the design doc's claims as EARS REQs, derives mechanical verification checks, and runs them against the existing plugin files. Any mismatch is logged and fixed; the loop continues until clean.

## Non-goals
- Re-implementing the skills (they exist; only verification + targeted fixes).
- End-to-end execution via the live Claude Code Skill tool (the plugin requires a session restart; this dogfooding pass runs the source directly).
- Step 5 (execution of generated tests against a real implementation) and Step 6 (ratchet's closed loop) — those hand off to other skills and are outside this verification's scope.
- Mutation testing on the plugin source — the plugin is markdown, not executable code; structural lints replace this layer.

## Decisions made during clarify
- Source of truth is `/Users/xrensiu/Documents/Downloads/done-when-pipeline.md` — source: clarify Q21 / Q22.
- Both skills live in one plugin, `done-when-pipeline`, in claude-code-forge — source: clarify Q19.
- Output of acceptance-spec is 4 files (proposal/spec/tasks/done_when.yaml) — source: clarify Q02.
- done_when.yaml schema matches source doc Appendix C — source: clarify Q03.
- test-suite-generator accepts either a `specs/<feature>/` directory or a `done_when.yaml` path — source: clarify Q07.
- Target test pyramid composition is 6 layers with 50/35/15 unit/integration/e2e ratio target — source: clarify Q08.
- Generated tests are runnable code, not scaffolding — source: clarify Q09.
- Target language is auto-detected from project manifests — source: clarify Q10.
- PBT property type comes from `property_type:` in done_when.yaml — source: clarify Q11.
- Fitness rubrics are persona-judge-consumable markdown — source: clarify Q13.
- Integration with ratchet is a **manual hand-off**: user translates our outputs into ratchet's own Goal/Criteria/Scope/done_when format; ratchet does not auto-parse our YAML. — source: clarify Q15 (Round 2, after ISSUE-002 fix landed in INTEGRATION.md).
- Fitness rubrics are scored by a **manual fresh-Claude-session workflow** — no packaged automation exists. The original mention of persona-judge / named personas was a category error and has been removed. — source: clarify Q17/Q18 (Round 2, after ISSUE-003 fix).

## Linked artifacts
- spec.md — EARS contract
- tasks.md — verification work decomposition (not implementation)
- done_when.yaml — machine-verifiable check list
- _skill-issues.md — running log of issues found during this dogfooding pass
