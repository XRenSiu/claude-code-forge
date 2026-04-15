---
name: schema-contribution-guide
description: How to contribute a new persona schema to persona-distill via PR
version: 0.1.0
---

# Schema Contribution Guide

> For first-time contributors. Read `contracts/schema-extension-contract.md` as the authoritative spec; this guide is the friendly walk-through.

## 1. What a schema is

A **persona schema** is a named recipe that tells `distill-meta` which of the 19 components to compose (and in what runtime order) for a given *kind* of subject — e.g., a public thinker, a work collaborator, a rule-system like 八字. Nine core schemas ship with the plugin; this guide shows how you add a tenth.

## 2. Step-by-step

1. **Fork** `claude-code-forge`. Work on a branch named `schema/<slug>`.
2. **Create the schema file** at `plugins/persona-distill/skills/distill-meta/references/schemas/community/<slug>.md`. Use the frontmatter template in §3 below.
3. **Compose from the 19 core components** first. Only declare a new community component if you genuinely need one; new components ship under `skills/distill-meta/references/components/community/<new-slug>.md` and MUST conform to `contracts/component-contract.md`.
4. **Write a minimal test corpus** of 5-10 files under `skills/distill-meta/references/schemas/community/<slug>-corpus/`. Cover at least: one normal case, one boundary case (where the schema barely applies), one refusal case (where the persona must decline).
5. **Compute `test_corpus_hash`**: SHA-256 over the sorted concatenation of the corpus file contents. Any stable tool works (e.g., `shasum -a 256` on a concatenated tarball); record the digest in frontmatter.
6. **Dry-validate** locally: open a throwaway Claude Code session, invoke `distill-meta` with a prompt that should route to your schema, and confirm Phase 0.5 picks it. If it doesn't, the `decision_tree_branch` predicate is wrong.
7. **Run `persona-judge`** on a persona generated from your test corpus. Attach the `validation-report.md` to the PR description. Score must be ≥ 70 on raw rubric.
8. **Open a PR** titled `feat: community schema <slug>`. Fill in the PR template; reference `schema-extension-contract.md §7` and confirm you followed the checklist.

## 3. Worked example: `peer-ex-colleague`

Suppose you want to distill a former coworker you no longer work with — close enough to have private corpus (old Slack DMs, emails) but distant enough that `collaborator` feels wrong because the work context is stale.

### 3.1 Proposed schema file

Filename: `skills/distill-meta/references/schemas/community/peer-ex-colleague.md`

```yaml
---
schema: peer-ex-colleague
version: 0.1.0
author: jane-doe
subject_type: person
required_components:
  - hard-rules
  - identity
  - shared-memories
  - work-capability
  - persona-5layer
  - expression-dna
  - honest-boundaries
  - correction-layer
optional_components:
  - internal-tensions
decision_tree_branch: >
  object_type == "person" AND corpus_access == "private"
  AND relation == "peer" AND work_context == "former"
test_corpus_hash: <sha256-of-corpus>
unvalidated: true
review_status: draft
---
```

Followed by the 7 required H2 sections from contract §4.

### 3.2 Diff patch sketch (what the PR touches)

```
 plugins/persona-distill/skills/distill-meta/references/schemas/
+  community/peer-ex-colleague.md                    (new)
+  community/peer-ex-colleague-corpus/               (new, 7 files)
+    01-slack-dm-normal.md
+    02-email-thread-boundary.md
+    ...
+    07-refusal-case.md

 plugins/persona-distill/skills/distill-meta/references/decision-tree.md
   (no edit — community branch loaded by discovery, not baked in)

 plugins/persona-distill/contracts/manifest.schema.json
   (no edit — v0.2.0 already supports schema_type_origin: community)
```

Note that no core file is edited; the whole contribution is additive and scoped to `community/`.

### 3.3 What the decision tree sees at runtime

Phase 0.5 walks core decision-tree.md; the user prompt "蒸馏我以前的同事张三" sets `relation = peer` but no existing core branch matches "former work context." The agent then walks the community list alphabetically, evaluates `peer-ex-colleague`'s `decision_tree_branch`, it matches, schema chosen. `manifest.schema_type_origin` is set to `community` and `manifest.schema_type_author` to `jane-doe`.

## 4. Anti-patterns

These will earn a PR rejection. Avoid them.

- **Too similar to an existing schema.** If your `required_components` overlap with an existing schema with Jaccard ≥ 0.8, you're proposing a rename, not a schema. Consider a PR that broadens the existing schema instead.
- **Component overreach.** A schema requiring more than 19 components is a bundle, not a schema. Split it, or — more likely — reconsider whether your subject type really differs from 3 existing schemas stacked together.
- **No test corpus.** PRs without a test corpus or with fewer than 5 corpus files are closed immediately. The corpus is how maintainers verify your schema works at all.
- **Ambiguous decision branch.** A predicate that overlaps an existing branch without adding a new signal creates a runtime conflict. Always add at least one differentiator (a new `user_signals` field, a boolean refinement).
- **Vanity schemas.** "My specific friend Alice" is not a schema; it's a persona. Schemas abstract over *kinds* of subjects. If your `decision_tree_branch` mentions a specific person by name, it's not a schema.
- **Bypass tricks.** Declaring `unvalidated: false` on first submission; setting `review_status: accepted` yourself; omitting `test_corpus_hash`. Automated checks catch these.
- **Core slug collision.** Reusing any of the 9 core schema slugs or any of the 19 component slugs. Discovery will skip and warn.
- **Runtime-unfriendly branches.** Predicates that depend on non-deterministic state (time, random, env vars) break the Phase 0.5 determinism guarantee.

## 5. Review SLA and common rejection reasons

| Dimension | SLA |
|-----------|-----|
| First maintainer response | within 14 days of PR |
| Iteration rounds typical | 2-3 |
| Merge once accepted | within 7 days |

**Common rejection reasons** (in descending order of frequency):

1. Missing or undersized test corpus.
2. `persona-judge` score below 70 on attached run.
3. Jaccard overlap ≥ 0.8 with existing schema.
4. `decision_tree_branch` duplicates an existing branch.
5. New components added that don't conform to `component-contract.md`.
6. Schema is effectively a single-persona template, not a kind.
7. `Borrowed From` citations vague or absent when borrowing is obvious.
8. Frontmatter fields missing / typed wrong.

If your PR is rejected, the closing comment will cite the specific §7 checkbox that failed. Address it and re-open.

---

**Ready to start?** Read `contracts/schema-extension-contract.md` once front-to-back, then copy the frontmatter template above into a new file under `schemas/community/`. Good luck.
