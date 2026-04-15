---
version: 0.2.0
purpose: Reference doc for migrating already-generated persona skills when distill-meta's component library or manifest schema bumps version, while preserving the self-containment invariant.
consumed_by: [agents/migrator.md]
references:
  - ../../../contracts/manifest.schema.json
  - ../../../contracts/component-contract.md
  - ../templates/migration-plan-template.md
changelog:
  - 0.2.0 — Added new-component discovery step (§New-Component Discovery). Addresses the v0.2.0 → v0.3.0 case where the library adds a component (e.g., `execution-profile`) to a schema's `optional_components` after a persona was already generated — the migrator now surfaces the new-component opt-in instead of silently passing the persona over.
  - 0.1.0 — Initial 7-step migration procedure.
---

# Persona-Skill Migration Reference

## Purpose

Persona skills produced by `distill-meta` are **self-contained** by design (see SKILL.md §Self-Contained Principle and master plan §9 decision #7): every component is *borrow-copied* into the persona's own `components/` directory, and the produced skill never reads back from `distill-meta`. This is non-negotiable.

When the central component library evolves (e.g. `expression-dna` 0.1.0 → 0.2.0 with a richer 7-axis output format), previously-generated persona skills are **frozen** — they keep the old copy and still work. The migrator exists for the case where a user explicitly wants to *upgrade* a frozen skill to the latest component definitions.

**Invariant**: after migration, the upgraded persona skill MUST still pass `grep -r "distill-meta" {persona-skill-root}/` with zero hits. Migration only **copies new content into the persona's own directory** and updates its `manifest.json`. The migrator never installs a runtime link, symlink, or import back to `distill-meta`.

## When to Migrate

Triggers (any one of):

1. **Explicit user request** — "升级这个 skill 的组件" / "migrate xxx-persona to latest distill-meta".
2. **distill-meta library bump where any used component changed** — Phase 0 of distill-meta (intent clarification) detects an existing persona skill at the target slug and finds at least one component in `manifest.components_used[]` whose current version in `distill-meta/references/components/<slug>.md` differs from the version recorded in the persona's manifest.
3. **Schema contract bump** — `contracts/manifest.schema.json` `$id` version differs from manifest's `distill_meta_version`. Includes the persona-distill plugin's own version bump that touched the schema.

The migrator is **opt-in**. Detection only surfaces a recommendation; nothing is overwritten without user approval (PATCH bumps may auto-apply per the agent's `auto_approve_patch_bumps` flag, but a snapshot is still taken).

## New-Component Discovery (v0.2.0 of this doc)

Before running the per-component version-diff pass (next section), the migrator also checks whether the **schema** (canonical definition in `distill-meta/references/schemas/<schema_type>.md`) now declares optional components that the persona's existing `manifest.components_used[]` does NOT carry. This happens when a library release adds a component to an existing schema's `optional_components:` list after the persona was already generated — e.g., v0.3.0 adds `execution-profile` to `public-mirror` and `mentor`.

Behavior:

1. Read `{distill_meta_root}/references/schemas/{manifest.schema_type}.md` frontmatter. Compute `schema.optional_components − manifest.components_used[]` = new-optional-candidates.
2. For each candidate, the migrator appends an `## Optional New Components` section to `plan.md` listing the slug, a one-line purpose from the component definition's frontmatter, and a default recommendation: `opt_in` if the component definition's `optional_for_schemas` explicitly names the current schema (bilateral agreement), else `skip`.
3. In `mode: APPLY`, opt-in candidates go through the same generation flow distill-meta would use for a fresh skill — the corresponding Phase-level extractor (e.g., `agents/execution-profile-extractor.md` for `execution-profile`) runs over the persona's existing `knowledge/`. If the extractor returns `INSUFFICIENT_EVENTS` / equivalent downgrade status, the migrator records the skip reason in `migration_history[]` rather than failing.
4. The migrator never opt-ins new REQUIRED components (that would indicate a MAJOR schema change — route to `schema-evolution-required` in Failure Modes instead).

This step is separate from the per-component version-diff pass below because it changes `components_used[]` membership, not just per-slug versions. User approval for opt-in candidates is REQUIRED in `mode: APPLY` — default is `skip` unless the user explicitly accepts.

## Migration Plan (diff report)

Before any writes, the migrator produces a `plan.md` (template: `templates/migration-plan-template.md`) at `{persona-skill-root}/.migration/plan.md`. The plan lists, **for each component** in `manifest.components_used[]`:

| Field | Value |
|---|---|
| `slug` | component slug |
| `current_version` | version recorded in persona's manifest |
| `new_version` | version from `distill-meta/references/components/<slug>.md` frontmatter |
| `diff_summary` | 2-3 line human summary of what changed in the Output Format section |
| `risk_level` | `PATCH` (typo / format polish) / `MINOR` (added optional field, backward compat) / `MAJOR` (renamed section, removed field, breaking schema change) |
| `user_edited` | `true` if the persona's current copy of this component diverges from its `original_component_hash` recorded in manifest (i.e. the user hand-edited it post-generation) |
| `approval_required` | PATCH = auto (with snapshot); MINOR = show diff and ask Y/N; MAJOR = explicit `ACCEPT` per file; `user_edited=true` = always REFUSE auto-patch and only offer diff |

The plan is the **only artifact** written in `mode: PLAN`. The user reviews it and re-invokes with `mode: APPLY` to execute.

## Migration Procedure (7 steps)

The migrator agent (`agents/migrator.md`) operationalizes the following:

1. **Lock & snapshot.** Move the persona skill directory to `{parent}/.migrating/{persona-slug}/` (staging copy) and snapshot the original to `{parent}/.migrating-backup/{persona-slug}-{ISO8601}/`. Both directories are siblings of the live skill, never inside it (avoids recursion in fingerprint/version code).

2. **Read manifest & derive used set.** Load `{persona-skill-root}/manifest.json`. Extract `components_used[]`, each entry's `version` (post-v0.2.0 widening — see contract), and the per-component `original_component_hash` if present.

3. **Compare versions.** For each used component, read the current file at `{distill_meta_root}/references/components/<slug>.md`. Read its frontmatter `version`. Diff against manifest's recorded version. Compute SHA-256 of the persona's *current* copy at `{persona-skill-root}/components/<slug>.md` (with stripped sections re-attached to a normalized form, see Failure Modes); compare against `original_component_hash` to detect user edits.

4. **Generate plan.md.** Per template. Write to `{persona-skill-root}/.migration/plan.md`. If `mode: PLAN`, STOP here and return the path.

5. **Per-approved component, apply the upgrade.** For each component the user has approved (per the per-risk-level approval rules in §Migration Plan):
   - Read the current source: `{distill_meta_root}/references/components/<slug>.md`.
   - Strip sections per `contracts/component-contract.md §4`: drop `## Extraction Prompt`, `## Failure Modes`, `## Borrowed From`.
   - Preserve the persona's existing frontmatter `produced_for` field (the manifest fingerprint at original generation time — do NOT recompute, since `knowledge/` is unchanged).
   - Update frontmatter `version` to the new component version.
   - Write over the old file at `{persona-skill-root}/components/<slug>.md`.
   - Compute the new SHA-256 of the just-written file and stage the value for manifest update (becomes the new `original_component_hash` for that slug).

6. **Update manifest.** Atomically:
   - Bump `distill_meta_version` to current persona-distill plugin version.
   - Update `components_used[].version` per slug to the new versions actually applied (skipped components keep their old version).
   - Update `components_used[].original_component_hash` per slug for components that were rewritten.
   - Recompute `fingerprint` per the SHA-256-of-sorted-component-file-hashes rule (NOTE: this is an additional invariant introduced for migration — the existing knowledge-based fingerprint stays unchanged because `knowledge/` was not touched; the *component* fingerprint is a separate field, see contract update §3 below). Emit as `components_fingerprint`.
   - SET `validation_score: null` (forces re-validation in step 7).
   - Append a `migration_history[]` entry: `{from_version, to_version, migrated_at, components_changed: [<slug>...], user_approved: true}`.
   - Update `last_migrated_at` to current ISO 8601 timestamp.

7. **Re-validate via persona-judge.** Invoke `persona-judge` against the staged copy. Read the resulting `validation-report.md` `overall_score_raw`. Compare to the score recorded in `migration_history[-2].validation_score_at_migration` (or the prior canonical `validation_score` saved before step 6 nulled it).
   - If the new score is **within 5 raw points** of the prior score (or improves), commit: rename `.migrating/{persona-slug}/` back to its live location, retain `.migrating-backup/` for one cycle, then prune.
   - If regression > 5 points, **HALT**. Surface the validation report's `## Recommended Actions` to the user. Do not auto-rollback; let the user choose to roll back or accept.

## Rollback

If step 7 fails (or the user rejects the regression), restore from `{parent}/.migrating-backup/{persona-slug}-{ISO8601}/`:

1. Delete `{parent}/.migrating/{persona-slug}/` (the failed staged copy).
2. The live skill location was untouched during steps 1-7, so it already holds the pre-migration state. (Step 1's "lock & snapshot" creates a *staging copy* in `.migrating/`; it does NOT move the live directory. The live directory only gets atomically swapped at the end of step 7.) If a partial swap occurred due to a crash, restore by `cp -r .migrating-backup/{persona-slug}-{ISO8601}/ {persona-skill-root}/`.
3. Append a `migration_history[]` entry with `user_approved: false` and reason `regression > 5 points` or `user_rejected`.

The backup is retained for **one successful migration cycle** then pruned. Override via `config.yaml → migration.backup_retain_count`.

## Failure Modes

| Mode | Detection | Migrator response |
|---|---|---|
| **User-edited component** | Hash of persona's current `components/<slug>.md` (normalized: frontmatter version + body) ≠ manifest's `original_component_hash` for that slug | REFUSE auto-patch. Surface diff between user edit and proposed new content. Require explicit user choice: KEEP MINE / ACCEPT THEIRS / MERGE MANUALLY. Default to KEEP MINE. |
| **Missing `original_component_hash`** | Manifest is pre-v0.2.0 or generated by a third party with no recorded baseline | Cannot detect user edits. Treat ALL components as `user_edited=true` (refuse auto-patch, force diff review per file). Log warning that this is a "third-party persona skill — no known prior state". |
| **Major schema change (component used → removed)** | Component slug in manifest is no longer present in `distill-meta/references/components/` | Mark as `risk_level: MAJOR` with sub-reason `component-deprecated`. Migrator does not auto-remove. User must explicitly opt in to drop the component (which may break the persona). |
| **Different component used** (schema evolved, e.g. `persona-5layer` → `persona-6layer`) | manifest's `schema_type` requires a component the manifest doesn't have | Surface as `schema-evolution-required`. Recommend re-running full distill-meta pipeline rather than patch-migrating. |
| **Fingerprint collision** | New `components_fingerprint` matches a fingerprint recorded in a sibling persona skill | Warn but do not block (fingerprints are advisory for caching, not security). |
| **Schema contract incompatibility** | `manifest.schema.json` v0.2.0 has fields the persona's manifest can't satisfy without re-generation | Halt with `schema-incompatible`; recommend full regeneration. |

## Manifest Fields Added in v0.2.0

The `contracts/manifest.schema.json` is bumped to **0.2.0** to support migration. New fields:

| Field | Type | Purpose |
|---|---|---|
| `distill_meta_version` | string (SemVer) | Version of `distill-meta` (or persona-distill plugin) at the time of last write. Distinct from `persona_distill_version` because that field tracks the plugin globally; this one tracks the specific generator/migrator that last touched the manifest. |
| `migration_history[]` | array of `{from_version, to_version, migrated_at, components_changed: [], user_approved: bool}` | Append-only ledger of all migration runs. Empty array on first generation. |
| `last_migrated_at` | string (ISO 8601) or null | Timestamp of last successful migration. `null` on first generation. |
| `components_used[]` (widened) | now `oneOf`: legacy `array of string` OR new `array of {slug, version, original_component_hash}` | Backward compat: pre-v0.2.0 manifests stay valid. New manifests use the object form so the migrator can detect user edits and version drift per slug. |
| `components_fingerprint` | string (64-hex SHA-256) | SHA-256 of sorted concat of `components/**/*.md` content hashes. Stable across migrations when no component changes. Distinct from `fingerprint` (which hashes `knowledge/`). |

The migrator REQUIRES the new fields to operate correctly; on a pre-v0.2.0 manifest it treats `original_component_hash` as missing (per Failure Modes) and runs in "third-party-skill" mode (diff-only, no auto-patch).

## Borrowed From

- **immortal-skill version+correction pattern** — the convention that persona skills carry both an immutable "as-distilled" baseline and a mutable correction layer; migration must preserve the correction-layer content untouched (it's user-owned, not distill-meta-owned). Migration only ever rewrites files under `components/` whose slug matches a distill-meta-owned component definition; `correction-layer.md` content is treated as user-edited by default.
- **master plan §9 decision #7 (self-contained)** — non-negotiable; cited at top of this doc.
- **nuwa-skill borrow-copy convention** — components are copied at generation/migration time, never linked.

## Anti-patterns

- **Symlinking `components/<slug>.md` back to `distill-meta/references/components/<slug>.md`** — would "fix" version drift but breaks self-containment. FORBIDDEN.
- **Recomputing the knowledge `fingerprint` during migration** — knowledge didn't change; only `components_fingerprint` changes. Recomputing both would mask actual knowledge edits made between migration runs.
- **Auto-applying MAJOR bumps without explicit per-file ACCEPT** — bypasses the user-approval gate.
- **Skipping the snapshot in step 1** — rollback becomes impossible. The snapshot is mandatory regardless of `auto_approve_patch_bumps`.
- **Migrating a third-party skill silently** — without `original_component_hash` we cannot tell user edits from generator output. Always surface the warning.
