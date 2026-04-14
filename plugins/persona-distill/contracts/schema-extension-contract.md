---
name: schema-extension-contract
description: Protocol for community-contributed persona schemas
version: 0.1.0
---

# Schema Extension Contract

> How the community adds a **10th, 11th, ... Nth** persona schema to `persona-distill` without breaking the 5-skill integration fabric or the self-containment guarantee of generated persona skills.

## 1. Purpose

The 9 core schemas (`self`, `collaborator`, `mentor`, `loved-one`, `friend`, `public-mirror`, `public-domain`, `topic`, `executor`) are not an exhaustive taxonomy of subject types. Real use will surface cases that deserve their own schema — e.g., `peer-ex-colleague`, `deceased-relative`, `product-as-persona`, `anonymous-collective`. This contract formalizes how community contributors propose such schemas via PR.

**Prior art**: the 7-personas template in the immortal-skill reference library `[UNVERIFIED-FROM-README]` demonstrated that a fixed roster is always eventually outgrown; the mechanism here is the natural extension.

**Non-goals**:

- **Not a dynamic runtime plugin system.** Community schemas ship as files in this repo via PR; they are not downloaded or fetched at runtime.
- **Not a way to bypass `component-contract.md`.** A community schema still composes from the 18 reserved component slugs (or declares new community components that themselves conform to `component-contract.md`).
- **Not a way to skip validation.** `distill-meta` Phase 0.5 MUST validate every schema file against this contract before accepting it; failing files are logged and skipped, never silently loaded.
- **Not a forum for derivative / vanity schemas.** The review checklist in §7 explicitly rejects Jaccard-similar or decision-branch-duplicative proposals.

## 2. File Layout

Community schemas live under a dedicated subdirectory to keep them visually and operationally separate from the 9 core schemas:

```
skills/distill-meta/references/
├── schemas/
│   ├── self.md                    ← core (9 files, do not modify here)
│   ├── collaborator.md
│   ├── ...
│   ├── executor.md
│   └── community/
│       ├── README.md              ← points readers to contribution guide
│       ├── <slug>.md              ← community schema definition
│       └── <slug>-corpus/         ← required test corpus (5-10 files)
│           ├── 01-source.md
│           └── ...
└── components/
    ├── <18 core component files>
    └── community/                 ← OPTIONAL; only if schema declares new components
        └── <component-slug>.md
```

Rules:

- Slug format: `^[a-z][a-z0-9-]*$`, globally unique across core + community.
- A community schema MAY NOT shadow a core schema name.
- Test corpus directory MUST be sibling of the schema file and named `<slug>-corpus/`.
- New community components MUST conform to `component-contract.md` (same frontmatter, H2 sections, slug reservation norms; slugs MUST NOT collide with the 18 core slugs).

## 3. Required YAML Frontmatter

Every community schema file starts with:

```yaml
---
schema: <slug>                          # matches filename stem
version: <semver>                       # this schema definition's version
author: <name or handle>                # PR author; used for manifest.schema_type_author
subject_type: person | domain | rule-system
required_components:                    # subset of 18 core slugs AND/OR community component slugs
  - <slug>
  - ...
optional_components:
  - <slug>
decision_tree_branch: "<predicate>"     # see §5; a deterministic boolean expression
test_corpus_hash: <sha256>              # SHA-256 over sorted concatenation of <slug>-corpus/*
unvalidated: true | false               # default true until a persona-judge dog-food run passes
review_status: draft | accepted         # maintainer-set during PR; contributor always writes `draft`
---
```

Field contracts:

- `schema` — MUST equal the filename stem and the community slug.
- `version` — SemVer, independent of core plugin version. See §8.
- `author` — stable identifier (GitHub handle, real name); recorded in `manifest.schema_type_author` of any persona skill generated from this schema.
- `subject_type` — one of the three values; persona skills generated from the schema MUST set `identity.subject_type` to a compatible enum value in `manifest.schema.json` (`person` → `real-person` | `composite` | `fictional`; `domain` → `topic`; `rule-system` → `rule-system`).
- `required_components` — at least 3, at most 18. The union `required_components ∪ optional_components` MUST NOT exceed 18 items (hard cap; larger numbers suggest a bundle of schemas, not a single schema — see §7).
- `decision_tree_branch` — a human-readable predicate expression over the `user_signals` fields from `decision-tree.md` §Output Schema. Example: `subject_type == "person" AND corpus_access == "private" AND relation == "ex-colleague"`. MUST be deterministic; no randomness, no time-of-day conditions.
- `test_corpus_hash` — SHA-256 over the sorted concatenation of the test corpus file contents. Recomputed by Phase 0.5 during discovery; mismatch → WARN (tampered corpus) and skip.
- `unvalidated` — MUST be `true` for first submission. A later PR can flip to `false` once a `persona-judge` run on the test corpus produces score ≥ 70.
- `review_status` — contributor always writes `draft`; maintainers flip to `accepted` on merge.

## 4. Required H2 Sections

A community schema file MUST contain, in order:

1. `## Purpose` — one paragraph explaining the subject type and why the 9 core schemas cannot cover it.
2. `## Decision Branch` — restates the `decision_tree_branch` predicate in prose + gives 2-3 example user prompts that should route here, and 2 adversarial prompts that should NOT.
3. `## Component Composition` — narrative version of the frontmatter's `required_components` + `optional_components`, explaining **why each component is there** and **what runtime order** they execute in.
4. `## Test Corpus Reference` — describes the `<slug>-corpus/` contents: how many files, what sources, what edge cases are covered (at minimum: normal case, boundary case, refusal case).
5. `## Quality Criteria` — which dimensions of `persona-judge`'s rubric this schema is especially sensitive to (minimum 3).
6. `## Known Limitations` — honest list. Must name at least one failure mode you haven't solved.
7. `## Borrowed From` — cite prior art; use `[UNVERIFIED-FROM-README]` marker if you could not verify the source directly, following the component-contract precedent.

Optional H2 sections:

- `## Example` — sketch of a hypothetical persona produced by this schema (not a real person).
- `## Interaction With Core Schemas` — when a user's query might equally match a core schema, which one wins?

## 5. Discovery

`distill-meta` Phase 0.5 — the schema-decision agent — performs discovery **before** walking the decision tree:

1. Enumerate `references/schemas/*.md` (core).
2. Enumerate `references/schemas/community/*.md` (community).
3. For each file, validate against this contract (§3 frontmatter + §4 required sections + §7 constraints the plugin can check statically).
4. Recompute `test_corpus_hash` from the sibling corpus directory; on mismatch, log WARN and skip the file.
5. Build an ordered schema list: **core schemas in the canonical order of decision-tree.md, then community schemas alphabetical by slug**. Two identical runs MUST produce identical ordering (determinism is non-negotiable).
6. The decision tree from `decision-tree.md` is walked first; if no core branch matches, each community schema's `decision_tree_branch` predicate is evaluated in alphabetical order and the first match wins.
7. If multiple community predicates match, the agent MUST surface the conflict to the user (see `decision-tree.md §Community Schemas`) rather than silently pick.

Failing schemas MUST be logged to `distill-meta`'s stdout with a single structured line per failure: `schema_extension_warn: slug=<s> reason=<r>`. They are NEVER loaded.

## 6. Manifest Update

Persona skills generated from a community schema MUST set:

- `manifest.schema_type` = the community schema slug.
- `manifest.schema_type_origin` = `"community"` (default for core schemas remains `"core"`).
- `manifest.schema_type_author` = the `author` field from the schema's frontmatter.

This lets downstream tools (`persona-router`, `persona-judge`, `persona-debate`) distinguish community personas at a glance — e.g., `persona-router` may choose to de-rank community-sourced personas in certain match contexts; `persona-judge` may apply a stricter threshold for `unvalidated: true` community schemas.

See `manifest.schema.json` v0.2.0 for the property definitions.

## 7. Review Checklist (for Maintainers)

A PR adding a community schema is reviewed against:

- [ ] Contract compliance: frontmatter fields all present and well-typed; H2 sections present and in order.
- [ ] Test corpus included under `<slug>-corpus/` with 5-10 files spanning normal / boundary / refusal cases.
- [ ] A `persona-judge` run on a persona generated from that corpus scores **≥ 70** on the raw rubric; report is attached to the PR description.
- [ ] No overlap with existing schema: compute Jaccard similarity `|A ∩ B| / |A ∪ B|` on `required_components` against every existing core and community schema; **must be < 0.8** vs. all of them.
- [ ] `decision_tree_branch` is non-duplicative: no existing branch uses the same predicate; if close, the new branch adds at least one additional signal.
- [ ] Slug does not collide with any of the 18 component slugs or any existing schema slug.
- [ ] Any new community components under `components/community/` themselves conform to `component-contract.md`.
- [ ] `author` field is set; `unvalidated: true`; `review_status: draft`.
- [ ] Claimed `Borrowed From` sources cited honestly; `[UNVERIFIED-FROM-README]` used when warranted.

Maintainers flip `review_status` to `accepted` on merge and optionally flip `unvalidated` to `false` if the attached persona-judge run is convincing.

## 8. Versioning

- Community schemas carry their own SemVer in frontmatter `version`, independent of the plugin or the core contracts.
- `distill-meta` tolerates a community schema whose contract major version is **at most one major behind** its own contract major version (i.e., a schema declaring conformance to `schema-extension-contract` v0.x is loadable by `distill-meta` running contract v1.x; v0.x schema under contract v2.x is skipped with WARN).
- When this contract itself is bumped to a new major version, an advisory note MUST be added here listing which frontmatter fields changed and how community contributors should migrate.

### Change log

- 0.1.0 — Initial contract. Defines file layout, frontmatter, discovery, manifest additions, review checklist, and versioning policy.
