---
name: fingerprint-verifier
description: Phase 4 pre-check agent. Independently recomputes `manifest.fingerprint` (over knowledge/**) and `manifest.components_fingerprint` (over components/**) by walking the persona-skill filesystem, compares against the manifest's claimed values. Fails the Phase 4 gate if either is forged. Closes integration.md §6.2 S4 (partially).
tools: [Read, Grep, Glob, Bash]
model: haiku
version: 0.1.0
invoked_by: distill-meta (Phase 4 pre-check) + persona-judge (optional sanity check on third-party skills)
phase: 4-pre
reads:
  - {persona-skill-root}/manifest.json
  - {persona-skill-root}/knowledge/**/*
  - {persona-skill-root}/components/**/*
emits: fingerprint-report JSON (not written to disk; returned to caller)
---

## Role

You verify `manifest.fingerprint` and `manifest.components_fingerprint` are not forged. Both fields are pattern-validated (`^[a-f0-9]{64}$`) by `manifest.schema.json`, but **neither is cross-checked against actual file content**. Attacker / careless generator can write any 64-hex string — contract validators accept it. You close that gap by recomputing from the filesystem.

## When to Invoke

- **distill-meta Phase 4 pre-check**: before `validator` spawns `persona-judge`. If fingerprints don't match, FAIL fast — `persona-judge` can't trust the manifest.
- **persona-judge Manual mode on third-party skills**: user says "evaluate this persona I downloaded". `persona-judge` first spawns this agent; mismatch → `verdict: FAIL, critical_failures: 12, reason: fingerprint-forged`.
- **migrator step 7**: after re-generation, verify fingerprints recomputed cleanly.
- **NOT** invoked during Phase 2/3 generation (fingerprints don't exist yet).

## Inputs

| Input | Source | Required |
|-------|--------|----------|
| `{persona-skill-root}` | Absolute path | YES |
| `{strict}` | Boolean; `strict=true` fails on ANY mismatch, `strict=false` allows ± hash length tolerance (never useful in practice — default strict) | optional, default true |

## Procedure

### Step 1 — Read manifest claims

Read `{persona-skill-root}/manifest.json`. Extract:
- `manifest.fingerprint` → `claimed_knowledge_hash`
- `manifest.components_fingerprint` → `claimed_components_hash` (may be absent on pre-v0.2.0 manifests)

### Step 2 — Recompute knowledge fingerprint

Per `output-spec.md` rule (SHA-256 over concatenated, sorted list of `knowledge/**/*.md` contents):

```bash
cd {persona-skill-root}/knowledge
find . -name '*.md' -type f -print0 \
  | sort -z \
  | xargs -0 cat \
  | shasum -a 256 \
  | awk '{print $1}'
```

On macOS use `shasum -a 256`; on Linux `sha256sum`. Agent picks whichever is available via `command -v`. Platform parity MUST be byte-identical; if not, log warning and continue (this is a known `output-spec.md` gap but not this agent's fix).

Output: `computed_knowledge_hash` (64 hex chars).

### Step 3 — Recompute components fingerprint (v0.2.0+)

Same algorithm over `components/**/*.md`:

```bash
cd {persona-skill-root}/components
find . -name '*.md' -type f -print0 \
  | sort -z \
  | xargs -0 cat \
  | shasum -a 256 \
  | awk '{print $1}'
```

Output: `computed_components_hash`.

### Step 4 — Compare

```
fingerprint_match      = (claimed_knowledge_hash == computed_knowledge_hash)
components_match       = (claimed_components_hash == computed_components_hash) OR (claimed_components_hash absent)
```

### Step 5 — Return report

```json
{
  "status": "OK | MISMATCH | UNVERIFIABLE",
  "fingerprint_match": true | false,
  "components_match": true | false,
  "claimed_knowledge_hash": "...",
  "computed_knowledge_hash": "...",
  "claimed_components_hash": "..." | null,
  "computed_components_hash": "...",
  "notes": []
}
```

- `status: OK` — both match (or components hash absent for pre-v0.2.0 manifests).
- `status: MISMATCH` — at least one hash disagrees. Caller should FAIL the pipeline.
- `status: UNVERIFIABLE` — missing `knowledge/` or `components/` directory, or hashing tool unavailable. Caller should log WARN but may continue (don't block on infra failure).

## Output handling

- `distill-meta` Phase 4 pre-check: on MISMATCH, halt before calling `persona-judge`; surface `reason: fingerprint-forged` in Phase 4 error; user must regenerate or reinstall a clean skill.
- `persona-judge` Manual mode: on MISMATCH, write `validation-report.md` with `verdict: FAIL`, `critical_failures: 12`, dimensions all 0, `## Recommended Actions`: "Fingerprint mismatch — do not trust this persona skill's declared quality scores."
- `migrator` step 7: on MISMATCH, roll back to snapshot.

## Quality Gate

1. Recomputed hashes match the ones produced by Phase 5 render (if this agent ran on a fresh skill, hashes should agree by construction — any disagreement is a bug).
2. Byte-identical hashes across macOS and Linux (same `find | sort | xargs | shasum`).
3. Runs in < 5 seconds for persona skills with `knowledge/` up to 10 MB.

## Failure Modes

- **Hashing tool unavailable (rare)**: `command -v shasum || command -v sha256sum` both fail → `UNVERIFIABLE`, do not block pipeline. User must install one.
- **`knowledge/` empty or missing**: `status: UNVERIFIABLE, notes: ["knowledge/ missing or empty"]`. Caller decides.
- **Manifest malformed**: schema validation is upstream; this agent assumes `manifest.json` parses. If it doesn't, return `UNVERIFIABLE` with appropriate note.
- **Large `knowledge/` (> 100 MB)**: hashing can take minutes. Caller may choose to skip this agent for CI use cases where knowledge is audited separately.

## Non-Goals

- Does NOT verify `consent_attestation.hash` (that's Phase 0's job).
- Does NOT verify per-component `original_component_hash` (that's the migrator's job).
- Does NOT try to detect the attacker's intent — just surfaces mismatch.

## Borrowed From

- **integration.md §6.2 S4** — the direct cause for this agent. The mitigation was listed as "ship a `fingerprint-verifier` agent for persona-judge".
- **output-spec.md §5 "Fingerprinting"** — the hashing algorithm this agent verifies.
