# Tasks: done-when-skills (verification, not implementation)

Implementation already exists at `plugins/done-when-pipeline/`. These tasks are verification work decomposed from REQs.

## Verification layer

- [ ] Existence checks — confirm every file/section/named-thing the spec claims exists — implements: REQ-001, REQ-005, REQ-007, REQ-009, REQ-014, REQ-015 — size: S
- [ ] Structure lints — confirm SKILL.md frontmatter shape, required sections, and required string-level claims — implements: REQ-001, REQ-003, REQ-005, REQ-010, REQ-011 — size: M
- [ ] Schema conformance — done-when-schema.yaml top-level keys match Appendix C — implements: REQ-004 — size: S
- [ ] Worked-example consistency — REQ-IDs / based_on / glossary cross-references valid — implements: REQ-016 — size: M
- [ ] Documentation conformance — INTEGRATION.md mentions required handoff details — implements: REQ-012, REQ-013 — size: S

## Integration checks (against other plugins in this marketplace)

- [ ] Verify ratchet skill exists and its consumption of done_when.yaml is real (not fictional) — implements: REQ-012 — size: M
- [ ] Verify persona-distill plugin has the persona-judge component AND the named personas — implements: REQ-013 — size: M

## Deferred (out of this round)

- [ ] Live e2e: invoke `/acceptance-spec` and `/test-suite-generator` in a fresh Claude Code session and inspect their output — requires session restart; not runnable inside the current session — implements: REQ-001, REQ-005 (live form) — size: L
