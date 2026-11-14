# Project development context

The default skill workflow establishes a development harness, not merely a test runner. The model reads and reconciles the project; the generator renders the reviewed decisions. Dependency detection alone never creates an architectural rule (Electron does not imply Vue or Pinia).

## Survey and author

Read root/module instructions, README, package scripts, native configs, representative source boundaries, test fixtures and current CI. Reuse existing architecture/design documents, skills, hooks and workflows. Preserve their ownership. For each rule, explain an actual project constraint, identify its source and choose the narrowest useful directory scopes. A file name or folder tree is not evidence of a rule's content or host activation.

Prepare a context JSON outside the repository, then pass it with `bootstrap --context <file> --host dual`. It is installed as project-owned `.harness/context.json`. Subsequent edits go there, followed by a reviewed bootstrap plan. Fields:

```json
{
  "schema_version": 1,
  "project": "Example",
  "summary": "Describe the real system, module ownership and authoritative docs.",
  "rules": [{
    "id": "toolchain",
    "title": "Toolchain",
    "scopes": ["."],
    "sources": ["package.json", "README.md"],
    "body": "Use the project's pinned package manager and native check commands."
  }, {
    "id": "api",
    "title": "API boundary",
    "scopes": ["src/api"],
    "sources": ["README.md", "src/api/index.ts"],
    "body": "State the confirmed API boundary and approved implementation path."
  }],
  "workflows": [{
    "id": "feature",
    "title": "Behavior change",
    "when": "Adding or changing observable behavior",
    "steps": ["Read the contract and affected source.", "Implement and verify the relevant behavior, then run the full harness."],
    "sources": ["README.md"]
  }],
  "assessment": []
}
```

The abbreviated example deliberately leaves assessment empty: it cannot be applied until the model records all ten areas. Each row has `area`, `status` (`configured`, `manual`, `not-applicable`, `gap`), a concrete `detail` and nonempty existing `sources`:

| Area | Required investigation |
| --- | --- |
| toolchain | Versions, installation, workspace scripts, local environment prerequisites |
| architecture | Ownership, protocols, data boundaries, source of truth, UI conventions where applicable |
| testing | Focused checks, full graph, isolation, skips, real-service/native qualification |
| security | Trust/permission boundaries, credentials, data handling and external side effects |
| delivery | Review criteria, candidate-bound evidence, release/acceptance separation |
| ci | Existing pipeline or a runnable local CI proposal; state unexecuted remote coverage |
| hosts | Claude and Codex loading, scope routing, overrides, context budget, real-session evidence |
| skills | Reuse installed/project task procedures; document any missing useful procedure |
| hooks | Need for an event hook, existing configuration and version contract; do not generate unqualified hooks |
| maintenance | Rule owners, source review, regeneration, drift diagnostics and verified-failure feedback |

`configured` describes wiring, never successful execution. Explain every manual, inapplicable or missing capability. Fill a useful gap in the user's authorized scope; do not just mark everything manual to finish. Do not manufacture agents, skills or `.claude/workflows` folders as decoration: workflow documents must be linked from the entry, and executable integrations require their actual host contracts.

Use project-specific workflows for features, bug reproduction, interface/schema changes, UI changes and delivery when applicable. Include actual commands, expected evidence and failure handling. Keep general software advice out. Rules contain concise decisions with references, not entire copied documents. Mechanically enforceable invariants belong in native type/lint/test tools; prose is behavioral guidance.

## Host compilation

- Canonical authoring input: `.harness/context.json`. Readable generated references: `docs/development/rules/`, `workflows/` and their index.
- Claude Code: `.claude/rules/project-harness-<id>.md`. Global rules omit `paths`; directory rules use `<directory>/**/*`. Existing custom rules/settings are preserved.
- Codex: global rules and an explicit scoped-rule routing index in the root `AGENTS.md`; scoped rules in directory `AGENTS.md` managed blocks. Codex builds the initial chain from root to the starting directory, so the root routing instruction tells a root-started agent to read relevant module rules before cross-directory work. This is not a claim that Codex natively loads `.claude/rules` or arbitrarily discovers nested instructions.
- `dual` generates both. `portable` produces references and checks without host activation. Directory scopes intentionally have identical subtree semantics; arbitrary filename globs are not silently widened for Codex.
- Existing human content remains outside managed blocks. Existing edited generated content stops an upgrade. Removed scopes/rules retire only owned outputs and managed blocks. Internal instruction symlinks share one physical edit; external links and shadowing `AGENTS.override.md` require reconciliation. CLAUDE imports of AGENTS are diagnosed because they can duplicate guidance.

## Verification and maintenance

The project-owned `project-context.mjs` verifies profile/render equality, scoped/root blocks, native check presence, reserved context-check wiring, overrides, sources and the approximate Codex instruction budget. It does not certify the semantics of a rule or a host's runtime loading. Source changes produce warnings for human/model semantic review; missing sources or generated drift fail. Re-running bootstrap without `--context` cannot silently accept changed source fingerprints.

`project-doctor.mjs [receipt.json]` runs static diagnostics without the factory. The required `harness-context` check participates in the existing full graph; it cannot be the only native verification. Empty native checks remain incomplete.

After verified recurring failures, update the existing rule/test owner, cite the incident/decision, regenerate both hosts and re-run checks. Never turn untrusted task data into authorization. Keep host traces, CI execution and release acceptance distinct from local consistency receipts.

Host contracts checked 2026-11-14: [Claude rules](https://code.claude.com/docs/en/memory#path-specific-rules), [Codex instruction discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md). New-session testing remains necessary for installed versions and user configuration.
