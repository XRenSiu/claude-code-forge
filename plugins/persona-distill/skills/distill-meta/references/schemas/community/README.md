---
name: community-schemas-index
description: Directory marker for community-contributed persona schemas
version: 0.1.0
---

# Community Schemas

Community-contributed persona schemas live here.

**How to contribute**: see `plugins/persona-distill/docs/schema-contribution-guide.md` for the step-by-step walk-through, and `plugins/persona-distill/contracts/schema-extension-contract.md` for the authoritative contract your schema must satisfy.

**Layout expected inside this directory**:

```
community/
├── README.md                  (this file)
├── <slug>.md                  (schema definition; frontmatter + 7 H2 sections)
└── <slug>-corpus/             (required test corpus, 5-10 files)
    ├── 01-*.md
    └── ...
```

**Status in v0.2.0**: empty. The first community schema merged here will open that door. Until then, `distill-meta` Phase 0.5 discovers zero community schemas, logs `schema_extension_info: community_count=0`, and falls through to the 9 core branches exclusively.

**Note on determinism**: discovery ordering is alphabetical by slug across files in this directory. If you contribute a schema, expect it to be evaluated in alphabetical position relative to other community schemas, after all 9 core schemas are exhausted.
