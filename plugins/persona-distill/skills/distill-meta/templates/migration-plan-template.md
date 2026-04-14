<!--
  template: migration-plan-template
  owner: agents/migrator.md (step 4 of references/migration.md §Migration Procedure)
  produces: {persona_skill_path}/.migration/plan.md
  conforms_to:
    - references/migration.md §Migration Plan
    - contracts/manifest.schema.json (v0.2.0)

  PLACEHOLDER GUIDE — migrator agent fills each {ALL_CAPS_SNAKE} token when rendering the plan.

  | Placeholder                  | Source                                                          |
  | ---------------------------- | --------------------------------------------------------------- |
  | {PERSONA_SLUG}               | from manifest.identity.name                                     |
  | {PLAN_GENERATED_AT}          | ISO 8601 UTC timestamp                                          |
  | {FROM_DISTILL_META_VERSION}  | manifest.distill_meta_version (or "unknown" for legacy)         |
  | {TO_DISTILL_META_VERSION}    | current persona-distill plugin version                          |
  | {SNAPSHOT_PATH}              | absolute path to .migrating-backup/{slug}-{ISO8601}/            |
  | {COMPONENT_ROWS}             | one table row per component (see row template below)            |
  | {TOTAL_COMPONENTS}           | len(components_used)                                            |
  | {COMPONENTS_NEEDING_BUMP}    | count of rows where current_version != new_version              |
  | {COMPONENTS_USER_EDITED}     | count of rows where user_edited == true                         |
  | {PATCH_COUNT}                | count of rows with risk_level == PATCH                          |
  | {MINOR_COUNT}                | count of rows with risk_level == MINOR                          |
  | {MAJOR_COUNT}                | count of rows with risk_level == MAJOR                          |
  | {AUTO_APPROVE_PATCH_BUMPS}   | "true" or "false"                                               |
  | {REGRESSION_THRESHOLD}       | integer, default 5                                              |

  ROW TEMPLATE (rendered per component into {COMPONENT_ROWS}):
    | {slug} | {current_version} | {new_version} | {risk_level} | {user_edited} | {diff_summary_one_line} | {approval_required} |
-->

# Migration Plan — {PERSONA_SLUG}

- **Generated at**: {PLAN_GENERATED_AT}
- **From distill-meta version**: {FROM_DISTILL_META_VERSION}
- **To distill-meta version**: {TO_DISTILL_META_VERSION}
- **Snapshot (rollback source)**: `{SNAPSHOT_PATH}`
- **Auto-approve PATCH bumps**: {AUTO_APPROVE_PATCH_BUMPS}
- **Regression threshold**: {REGRESSION_THRESHOLD} raw-score points

## Summary

- Components evaluated: **{TOTAL_COMPONENTS}**
- Components needing upgrade: **{COMPONENTS_NEEDING_BUMP}**
- Components user-edited (will NOT auto-patch): **{COMPONENTS_USER_EDITED}**
- Risk distribution: PATCH={PATCH_COUNT} / MINOR={MINOR_COUNT} / MAJOR={MAJOR_COUNT}

## Per-Component Plan

| Slug | Current | New | Risk | User-edited? | Diff summary | Approval |
|------|---------|-----|------|--------------|--------------|----------|
{COMPONENT_ROWS}

## Approval Rules

- **PATCH** (typo / format polish, backward-compatible) — auto-applied when `auto_approve_patch_bumps=true`; snapshot is still taken.
- **MINOR** (added optional field, backward-compat) — requires user Y/N after diff review.
- **MAJOR** (renamed section, removed field, breaking schema change) — requires explicit `ACCEPT` per file.
- **user_edited=true** — ALWAYS refuses auto-patch; only offers diff with KEEP MINE / ACCEPT THEIRS / MERGE MANUALLY.

## Next Step

To apply this plan, re-invoke the migrator with `mode: APPLY`:

```
migrator --persona_skill_path <path> --distill_meta_root <path> --mode APPLY
```

Rollback (if needed post-apply):

```
cp -r {SNAPSHOT_PATH} <persona_skill_path>
```

## Notes

- Knowledge `fingerprint` will NOT change (knowledge/ is not touched by migration).
- `components_fingerprint` WILL change for any accepted upgrade.
- `validation_score` will be reset to `null` and re-computed by persona-judge at step 7.
- `migration_history[]` gets a new entry whether the migration commits or halts.
