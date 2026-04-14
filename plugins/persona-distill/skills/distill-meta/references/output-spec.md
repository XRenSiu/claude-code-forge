---
spec_version: 0.1.0
applies_to: distill-meta (Phase 5 delivery), consumed by persona-judge / persona-router / persona-debate
references:
  - ../../../contracts/manifest.schema.json
  - ../../../contracts/component-contract.md
  - ../../../contracts/validation-report.schema.md
---

# Persona Skill — Output Specification

> Authoritative spec for the directory that `distill-meta` produces. Every generated persona
> skill MUST conform. This spec is derived from PRD §1.2 + §3.4 and is bound by three
> contracts (see `references:` above). Changes here are breaking changes to the four consumer
> skills.

## 1. Directory Layout

```
{persona-slug}/
├── SKILL.md                 # entry point; per templates/skill-md-template.md
├── manifest.json            # machine contract; per contracts/manifest.schema.json
├── components/              # one file per activated component, copied with inlining
│   ├── identity.md
│   ├── hard-rules.md
│   ├── honest-boundaries.md
│   └── … (only components listed in manifest.components_used)
├── knowledge/               # corpus archive, desensitized per redaction-policy.md
│   ├── chats/               # 1:1 / group chat exports
│   ├── articles/            # long-form writing by/about the persona
│   ├── transcripts/         # interview / podcast transcripts
│   └── media/               # audio/video references (metadata only; raw media optional)
├── versions/                # snapshot per update (last 5 retained by default)
│   ├── 0.1.0/
│   └── 0.2.0/
├── conflicts.md             # append-only conflict ledger (user-appended + Phase 3.5 auto-detected)
└── validation-report.md     # latest persona-judge report (mirror of versions/validation-report-*.md)
```

All paths are relative to the persona skill root. No file outside this root is read at
runtime by the generated skill (per `component-contract.md §7`).

## 2. File-by-file Contract

### 2.1 `SKILL.md`

Generated from `distill-meta/templates/skill-md-template.md`. MUST declare a
`name` matching `{persona-slug}` and trigger phrases matching
`manifest.json → triggers[]`.

### 2.2 `manifest.json`

MUST validate against `contracts/manifest.schema.json` (Draft-07). Required fields include
`persona_distill_version`, `schema_type`, `components_used`, `identity`, `triggers`,
`fingerprint`, `version`, `generated_at`, `density_score`. Writer is `distill-meta` Phase 5;
readers are persona-judge (rubric routing), persona-router (matching on
`identity.description` + `triggers`), persona-debate (participant discovery).

### 2.3 `components/`

One markdown file per slug in `manifest.components_used`. Files MUST follow the
**copy-with-inlining** rule.

#### Copy-with-inlining Rule

- Components are **copied from `distill-meta/references/components/<slug>.md`**, not linked
  or cross-referenced.
- On copy: drop `Extraction Prompt`, `Failure Modes`, `Borrowed From` H2 sections (see
  `component-contract.md §4`).
- Keep `Purpose` + concrete `Output Format` content + `Examples`.
- Replace the frontmatter's `version` with the component definition version resolved at
  generation time; add `produced_for: <manifest.fingerprint>`.
- Rationale: each persona skill MUST be **self-contained**. A user moving the directory
  elsewhere, or re-publishing only this skill, should see zero dangling references.

### 2.4 `knowledge/`

Subdirectories group corpus by modality. Every file carries frontmatter per
`primary-vs-secondary.md §"How corpus-scout Tags Each Document"` (`tier`, `tier_reason`,
`source_policy`, `author_of_record`, `captured_at`). All files are desensitized per
`distill-collector/references/redaction-policy.md` before write.

### 2.5 `versions/`

Snapshot on each persona-skill update. Each snapshot is a full directory mirror of the
state at that version (excluding the `versions/` subtree itself to avoid recursion).

- Default retention: **last 5** snapshots.
- Override via user's `config.yaml → versioning.retain_count`.
- Oldest snapshots are pruned by `distill-meta` Phase 5 after a successful new write.

Validation reports for each run are mirrored here as
`versions/validation-report-{ISO8601}.md`; the canonical latest is at
`{persona-skill}/validation-report.md`.

### 2.6 `conflicts.md`

Append-only ledger of contradictions discovered between corpus items.

```markdown
## {YYYY-MM-DD} — {short-title}
- claim_a: "…"
- claim_b: "…"
- sources: [knowledge/articles/foo.md#L12, knowledge/transcripts/bar.md#L88]
- resolution: <string | "unresolved">
```

**Scope**: entries may be (a) **user-appended** during review, or (b) **auto-detected** by the
`conflict-detector` agent in Phase 3.5. Both share the file; user entries live under
`## User-Appended Conflicts`, auto entries under `## Auto-Detected Conflicts`, and the agent
MUST preserve user entries verbatim (see `agents/conflict-detector.md §Interaction with
user-appended conflicts`). Do not remove past entries — mark `resolution:` instead. The
detector never auto-resolves; `suggested_handling` ∈ {PRESERVE_BOTH, FLAG_FOR_USER, TIMEBOUND}.

### 2.7 `validation-report.md`

MUST conform to `contracts/validation-report.schema.md`. The canonical copy is the latest
evaluation; prior runs live under `versions/validation-report-*.md`. `distill-meta` Phase 4
reads `frontmatter.verdict` and `overall_score_raw` only (no markdown-body parsing).

## 3. Fingerprint Computation

The `manifest.fingerprint` field (64-hex SHA-256) is computed as follows:

1. Enumerate all files matching `knowledge/**/*.md` relative to persona root.
2. Sort the resulting paths lexicographically (UTF-8 byte order).
3. For each file, read its full byte contents (frontmatter + body, no normalization beyond
   UTF-8 decode).
4. Concatenate the contents in sorted path order, separated by a single `\n` delimiter.
5. SHA-256 the resulting byte string; lowercase hex.

Properties:

- **Stable** across rebuilds when `knowledge/` is unchanged (determinism requirement from
  `manifest.schema.json → fingerprint`).
- **Changes** on any knowledge edit (even a single character in a single file).
- Does **not** hash `components/`, `versions/`, or `manifest.json` itself (those are derived
  artifacts and would create circular dependencies).

## 4. Generation Order (distill-meta Phase 5)

1. Write `knowledge/**` (desensitized, tagged).
2. Compute `fingerprint`.
3. Copy-with-inline `components/**` from references.
4. Render `SKILL.md`.
5. Write `manifest.json` (with fingerprint + component versions).
6. Snapshot to `versions/{version}/`.
7. Run persona-judge → write `validation-report.md` + mirror to `versions/`.
8. Prune `versions/` beyond retention.

Failure in any step aborts the write and rolls back to the prior version directory.
