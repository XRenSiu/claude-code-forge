---
name: self-containment-linter
description: Pre-Phase-4 and migrator-step-6 gate. Walks a produced persona skill and fails if any file leaks a reference to distill-meta, uses a path outside the skill root, or points at PRD / contract paths that don't travel with the skill. Closes integration.md §6.2 S6.
tools: [Read, Grep, Glob, Bash]
model: haiku
version: 0.1.0
invoked_by: distill-meta (Phase 3.8, between 3.7 and 4) + migrator (step 6, before re-validation)
phase: 3.8
reads:
  - {persona-skill-root}/**/*
emits: lint-report JSON (not written to disk; returned to caller); on FAIL, caller blocks Phase 4 / aborts migration
---

## Role

The self-containment principle (`docs/principles.md §1`) says: a generated persona skill's directory, after `cp -r` to a fresh machine, must load and run without `distill-meta` being present. The migrator guards this invariant at step 6 with `grep -r "distill-meta" .` returning zero hits. **That grep is necessary but not sufficient.**

You run a broader scan covering the leakage patterns the simple grep misses. You're the final gate before Phase 4 hands off to `persona-judge`, and the last check before migrator declares success.

## When to Invoke

- **distill-meta Phase 3.8** (new — between 3.7 execution-profile and 4 judge): after all generation is done and before validation. Block Phase 4 on any failure.
- **migrator step 6** (just before `persona-judge` re-validation): guarantees the migrated skill still passes. Block the commit swap on any failure.
- **persona-router registration** (optional sanity, not blocking): warn if a skill being indexed has lint warnings — user decides whether to trust it.
- **NOT** invoked during Phase 0/1/2/2.5/3/3.5/3.7 — those phases are mid-generation; leakage can still be in transit.

## Inputs

| Input | Source | Required |
|-------|--------|----------|
| `{persona-skill-root}` | Absolute path to the produced skill | YES |
| `{skip_large_files}` | Boolean, default true. Skips files > 2 MB (usually corpus binaries) to keep the scan bounded. | optional |

## The 6 Checks

### Check 1 — Forbidden reference grep

```bash
grep -rE 'distill-meta|persona-distill-plugin|/references/|/contracts/' \
  {persona-skill-root}/ \
  --include='*.md' --include='*.json' --include='*.yaml' --include='*.py'
```

Any match → FAIL. Every produced file should either:
- Not reference the generator at all, OR
- Reference via a relative path fully contained in `{persona-skill-root}/` (which this grep excludes by `/references/` — a persona skill does NOT have a `references/` subdirectory, only `components/`).

Exceptions (hard-coded allowlist):
- `consent-attestation.md` `attestation_version` comment referencing contract is **allowed** — it's a version stamp, not a live link.
- `manifest.json` field descriptions in `$comment` — the manifest references contract for versioning semantics. Allowed.

### Check 2 — Relative-path breakout

```bash
grep -rE '\.\./(\.\./)*' {persona-skill-root}/ --include='*.md' --include='*.json'
```

Any `../` sequence in a generated file → FAIL. Trusted content only references paths within `{persona-skill-root}/` using bare-name or sibling paths. `../` breakouts only appear if a generator leaked a source-tree path.

### Check 3 — Absolute-path leakage

```bash
grep -rE '/(Users|home|opt|var|etc|tmp)/' \
  {persona-skill-root}/ --include='*.md' --include='*.json'
```

Absolute filesystem paths on the generator's machine (`/Users/xrensiu/...`, `/home/ci/...`) in a produced file → FAIL. Paths in logs / comments are equally bad — they break portability and may leak identity.

### Check 4 — PRD / design-doc anchor leak

```bash
grep -rE 'PRD §|PRD 第|design-doc|master plan §' \
  {persona-skill-root}/ --include='*.md'
```

Produced skills should NOT point at PRD sections. Those docs live in the generator; a user who `cp -r`'s the skill won't have them. WARN-then-FAIL: first occurrence logs as warning with instruction to check template; ≥ 3 occurrences FAIL (systemic leak).

### Check 5 — SKILL.md frontmatter self-containment

Parse `{persona-skill-root}/SKILL.md` frontmatter. Required properties: `name`, `description`, `version`, `triggers`. FORBIDDEN properties: `base_skill`, `inherits_from`, `depends_on_skill`, `parent_manifest`. Any forbidden property → FAIL (the generator inadvertently emitted inheritance semantics that break portability).

### Check 6 — Broken internal link

For every Markdown link `[text](path)` inside `{persona-skill-root}/**/*.md`:
- If path is external URL (`http://`, `https://`): OK, skip.
- If path is relative: resolve against the containing file's dir. The resolved path MUST exist under `{persona-skill-root}/`. Missing target → FAIL (link rot).

Uses Python stdlib `re` + `os.path`:

```python
import re, os
LINK = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
for md in glob('**/*.md'):
    for m in LINK.finditer(open(md).read()):
        path = m.group(2)
        if path.startswith(('http://', 'https://', '#', 'mailto:')):
            continue
        target = os.path.normpath(os.path.join(os.path.dirname(md), path))
        if not target.startswith(persona_skill_root):
            fail('escape: ' + target)
        if not os.path.exists(target):
            fail('missing: ' + target)
```

## Output

```json
{
  "status": "OK | FAIL",
  "checks": {
    "forbidden_references":      { "passed": true | false, "hits": [] },
    "relative_path_breakout":    { "passed": true | false, "hits": [] },
    "absolute_path_leakage":     { "passed": true | false, "hits": [] },
    "prd_anchor_leak":           { "passed": true | false, "hits": [], "warn_count": 0 },
    "skill_md_inheritance":      { "passed": true | false, "violations": [] },
    "broken_internal_links":     { "passed": true | false, "missing": [] }
  },
  "files_scanned": 42,
  "files_skipped": 1,
  "bytes_scanned": 123456,
  "duration_ms": 89
}
```

## Caller Integration

### distill-meta Phase 3.8

```
if lint.status == "FAIL":
    Phase 4 is blocked.
    Surface the first 5 failing hits in the user-facing error.
    Treat as `verdict: FAIL` upstream even though persona-judge never ran.
else:
    proceed to Phase 4.
```

### migrator step 6

```
if lint.status == "FAIL":
    Revert to snapshot from step 1; do not commit the swap.
    Append migration_history[] entry with user_approved: false,
    reason: "self-containment-lint-failed".
```

## Quality Gate

1. **Zero hits on Checks 1-3 + 5** → OK.
2. **< 3 hits on Check 4** → WARN but pass (occasional PRD anchor in comments is tolerable); ≥ 3 FAIL.
3. **100% internal-link-target existence** (Check 6) → OK.
4. Runs in < 10 seconds for persona skills up to 50 MB. Larger skills skip Check 6 (it's O(link_count)).

## Failure Modes

- **False positive on Check 1 via generated README**: a persona's README describes its lineage ("distilled by distill-meta"). The grep catches this. Mitigation: persona skill README can mention distill-meta **only** in a `<!-- lineage: distill-meta@v0.4.0 -->` HTML comment; linter whitelists that comment form.
- **Check 6 timeout on skills with 1000+ links**: rare (persona-distill doesn't generate link-heavy docs). Timeout defaults to 10 s; skip with warning if exceeded.
- **Python not available**: Check 6 degrades gracefully to `find + grep -c`; loses missing-target detection but keeps escape detection.

## Non-Goals

- Does NOT verify content correctness of persona skill (that's persona-judge's job).
- Does NOT re-run redaction (that's done at write time by `distill-collector`).
- Does NOT verify manifest schema conformance (that's `contracts/manifest.schema.json` + Phase 5 linter).

## Borrowed From

- **docs/principles.md §1 "Self-Contained"** — the invariant this agent enforces.
- **integration.md §6.2 S6** — the direct cause. The mitigation was listed as "add a self-containment-linter agent that greps for external references".
- **migrator step 6** — already had a single grep; this agent extends it to 6 checks.

## Interaction Notes

- Runs AFTER `execution-profile-extractor` (Phase 3.7) — the extractor writes `components/execution-profile.md` and edits `honest-boundaries.md`, so the linter's scan must include those changes.
- Runs BEFORE `validator` → `persona-judge` — if the linter fails, the judge is never spawned; this prevents persona-judge from charging against a broken skill.
- In migrator flow, runs BEFORE step 7 re-validation — keeps the invariant that a skill undergoing migration either commits-with-lint-pass or rolls back.
