# Manifest Scanner — Discovery Mechanism

**Owner**: `persona-router`
**Referenced from**: `SKILL.md` §"Step 2 — Scan Installed Persona Skills" / §"Discovery mechanism"
**Input contract**: `plugins/persona-distill/contracts/manifest.schema.json`

This file specifies **how router finds installed persona skills** on disk. It is intentionally
narrow: router reads only `manifest.json` files, never SKILL.md bodies or knowledge directories.

---

## 1. Scan Paths (Ordered)

Router walks the following directories **in order**. Order matters because later paths can
shadow earlier ones (same `identity.name` → keep the first occurrence, record the rest as
`shadowed`).

| Priority | Path | Scope |
|---------:|------|-------|
| 1 | `<repo>/.claude/skills/*/manifest.json` | Project-local personas checked into the repo. |
| 2 | `~/.claude/skills/*/manifest.json` | User-global personas, private to the machine. |
| 3 | `~/.claude/plugins/cache/*/skills/*/manifest.json` | Plugin-marketplace installs (cached). |

### Configurability

The scan order is **not hardcoded**. Router accepts an optional config (`router.config.json`
or inline env `PERSONA_ROUTER_SCAN_PATHS`) whose value is a JSON array of path templates,
e.g.:

```json
{
  "scan_paths": [
    "./.claude/skills/*/manifest.json",
    "~/.claude/skills/*/manifest.json",
    "~/.claude/plugins/cache/*/skills/*/manifest.json"
  ]
}
```

When overridden, router uses the user-supplied order verbatim. When absent, it falls back
to the default table above. Router reports the effective order in every run.

---

## 2. Detection Rule

A directory counts as a **persona skill** iff it contains a `manifest.json` whose top-level
object has a `persona_distill_version` field (string, SemVer).

```
dir/
├── manifest.json     ← parsed
│     └── "persona_distill_version": "0.1.0"   ← REQUIRED marker
├── SKILL.md          ← ignored by router
└── knowledge/        ← ignored by router
```

This marker exists to **distinguish persona skills from regular Claude Code skills** that
may also ship a `manifest.json` for unrelated reasons. Regular skills without the marker
are silently skipped (not warned), since they are not the router's concern.

> **Why `persona_distill_version` and not e.g. `schema_type`?**
> `schema_type` is itself part of the persona-distill contract; using it as the discovery
> marker would conflate "is this ours" with "what kind is it". A dedicated version marker
> survives future schema evolution without re-plumbing discovery.

---

## 3. Validation

Each candidate `manifest.json` is validated against
`plugins/persona-distill/contracts/manifest.schema.json` (JSON Schema draft-07).

| Outcome | Router action |
|---------|---------------|
| Parse error (invalid JSON) | Skip. Warn: "`{path}`: not valid JSON — skipped." |
| Schema validation fails | Skip. Warn: "`{path}`: manifest does not match contract — skipped. First error: `{error_path}: {message}`." |
| Validation passes | Keep. Add `{path, manifest}` to the in-memory list. |

**Non-fatal by design**: a single broken manifest must not abort the scan. Router always
continues and presents a warning summary to the user **before** emitting recommendations.

### Warning surface

At the end of a run the user sees something like:

```
Scanned 23 candidate directories across 3 paths.
  → 21 valid persona manifests loaded.
  → 2 skipped:
     - ~/.claude/skills/foo/manifest.json: missing required field 'fingerprint'
     - .claude/skills/bar/manifest.json: not valid JSON (unexpected token at line 14)
```

Silent skipping is an anti-pattern (see SKILL.md §Anti-patterns). The user must be able to
audit why a persona they "know is installed" did not show up in recommendations.

---

## 4. Output Shape

Scanner returns an **in-memory list** (no file I/O beyond reads):

```ts
type ScanResult = {
  effective_scan_paths: string[];      // the order actually used
  loaded: Array<{
    path: string;                      // absolute path to manifest.json
    manifest: Manifest;                // schema-validated
  }>;
  skipped: Array<{
    path: string;
    reason: string;                    // one-line human-readable
  }>;
};
```

No persistence. No caching. See §6 below.

---

## 5. Shadowing and De-duplication

Two manifests may share `identity.name` (e.g. a user has a repo-local `mentor-lisi` that
shadows a home-directory version). Rule:

- **Keep first** by scan-path priority (repo beats user beats plugin-cache).
- **Record shadows** in `skipped` with reason `"shadowed by <path>"`. They are not errors,
  but the user should know their expectation of "which mentor-lisi is used" is observable.

If `identity.name` is missing (schema allows it under `required`, so this is a validation
failure), the manifest is skipped upstream by §3.

---

## 6. No Caching in v1

Router **re-scans on every invocation**. Reasons:

1. Persona skills are installed/uninstalled across sessions; stale cache → wrong recs.
2. Scan cost is O(N) on directory reads, which is cheap even for N=100.
3. A cache layer introduces invalidation bugs that outweigh its benefit at current scale.

If future profiling shows scan-time is material (say, N >> 500), add a content-addressed
cache keyed on `(path, mtime, fingerprint)`. Not now.

---

## 7. Known Limitations

| Limitation | Consequence | Mitigation |
|------------|-------------|-----------|
| **Environment-dependent paths**: Claude Code's actual skill install location varies across OS, project setup, and marketplace version. | Router may miss personas installed in non-standard locations. | Expose scan config (§1). Report effective paths (§3 warning surface) so user can spot absence. |
| **No network discovery**: router does not query any remote index. | Personas published but not yet installed locally are invisible. | Out of scope. Install first, route second. |
| **Symlinks**: not followed by default on some platforms. | A symlinked persona may be missed. | Document; user can replace symlink with real directory or add to `scan_paths`. |
| **Case sensitivity**: `~/.claude/Skills/` vs `~/.claude/skills/` behaves differently on case-insensitive filesystems. | Possible double-count on macOS HFS+. | De-duplicate by canonicalized absolute path. |

None of these are solved silently. Every limitation that bites a given run is surfaced in
the warning summary.

---

## 8. Progressive Disclosure

- High-level flow: `SKILL.md` §"Step 2 — Scan Installed Persona Skills".
- Scoring of discovered manifests: `references/matching.md`.
- Output rendering: `templates/recommendation-template.md`.
- Input contract: `contracts/manifest.schema.json`.
