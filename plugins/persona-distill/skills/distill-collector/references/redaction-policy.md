---
contract_version: 0.1.0
applies_to: distill-collector — PII redaction at write-time
status: SCAFFOLDING-ONLY
references:
  - ./cli-spec.md
  - ../../distill-meta/references/output-spec.md
---

# Redaction Policy — Unified Write-Time PII Filter

> **[SCAFFOLDING-ONLY]** This document pins the regex patterns, placeholder
> format, and override behavior that every parser (text, av, image-doc) MUST
> apply at **write-time** before Markdown is persisted to `knowledge/`.
> v1 ships the contract here; the regexes are the source of truth even though
> no single binary runs them end-to-end in this wave. Users implementing
> their own import scripts MUST follow this spec — `distill-meta` Phase 1.5
> trusts the `redaction: applied-vYYYYMMDD` frontmatter tag as an unforged
> claim. `distill-collector import --format generic` is expected to run this
> for real (it is the one runnable command in v1 per cli-spec.md §5).

Redaction applies at **write time**, not as a post-hoc scan. Rationale: if
the source file is later deleted, the repo must not retain PII that
propagates into commits.

---

## 1. Categories & regex patterns

Each pattern is anchored to word boundaries where possible. Patterns are
intentionally **permissive on false positives**; user fixes via
`--no-redact` on a per-invocation basis.

### 1.1 Phone numbers

```regex
# China mobile (11-digit, starts with 13-19)
\b1[3-9]\d{9}\b

# International (E.164-ish): + country code + 6-14 digits, optional spaces/dashes
\+\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}

# US (XXX) XXX-XXXX or XXX-XXX-XXXX
\b\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}\b
```

### 1.2 Email addresses

```regex
[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}
```

### 1.3 ID numbers

```regex
# China 身份证: 18 digits, last can be X
\b\d{17}[\dXx]\b

# US SSN: XXX-XX-XXXX
\b\d{3}-\d{2}-\d{4}\b
```

### 1.4 Credit cards (Luhn not validated, regex-only v1)

```regex
# Visa / MC / Amex rough ranges; 13-19 digits with optional spaces/dashes
\b(?:\d[\s\-]?){13,19}\b
```

False-positive prone on long numeric sequences (e.g., transaction IDs); this
is acceptable for v1 — the redacted placeholder still preserves anchor
identity in downstream analysis.

### 1.5 API keys / tokens

```regex
# OpenAI-style
\bsk-[A-Za-z0-9]{20,}\b

# AWS access key
\bAKIA[0-9A-Z]{16}\b

# GitHub PAT (classic + fine-grained)
\bghp_[A-Za-z0-9]{36,}\b
\bgithub_pat_[A-Za-z0-9_]{80,}\b

# Google API key
\bAIza[0-9A-Za-z_\-]{35}\b

# Slack bot / user tokens
\bxox[baprs]-[A-Za-z0-9\-]{10,}\b

# Generic "Bearer" header
\bBearer\s+[A-Za-z0-9._\-]{20,}\b
```

---

## 2. Placeholder format

Redacted matches are replaced by `[REDACTED:<KIND>-<4char-hash>]`, where
`<4char-hash>` is the first 4 hex chars of `SHA-256(match + persona-salt)`.
The salt is the `fingerprint` seed from `manifest.json` when available,
otherwise the literal string `"distill-collector-v1"`.

| Category    | Placeholder example          |
|-------------|------------------------------|
| phone       | `[REDACTED:PHONE-3a9f]`      |
| email       | `[REDACTED:EMAIL-HASH-7c21]` |
| id (CN/US)  | `[REDACTED:ID-1b8e]`         |
| credit card | `[REDACTED:CARD-004d]`       |
| api key     | `[REDACTED:KEY-ff12]`        |
| geo (EXIF)  | `[REDACTED-GEO]`             |

Why keep a 4-hex suffix? It preserves **anchor identity** — the same phone
number across the corpus maps to the same placeholder, so downstream schema
detection can still detect "PersonA calls this number repeatedly" without
leaking the number itself.

---

## 3. Speaker-name handling (not a regex — referenced for completeness)

The `--subject <name>` argument on `collect` / `import` / `transcribe` is the
only name that survives. Every other speaker is mapped to a stable alias
from the pool `PersonA, PersonB, PersonC, …`, assigned in order of first
appearance per file. Mapping lives in-memory per invocation; no cross-file
alias table is persisted in v1 (that is a v2 concern — identity merging
happens at `distill-meta` Phase 2).

---

## 4. Scope limits (things v1 deliberately does NOT redact)

- **Photographs themselves**. Faces in images are **not** blurred. Users who
  need that must pre-process images before handing them to the pipeline.
  This is a **[USER-RESPONSIBILITY]**.
- **Street addresses**. No reliable free regex across languages; v2 will
  address via an NER model. v1 leaves addresses in plaintext.
- **Birth dates / ages** when not in an ID pattern.
- **IP addresses**. Not redacted by default in v1.
- **Usernames / handles** (`@alice`). Treated as speaker aliases per §3, not
  stripped.
- **Free-text names** appearing in the prose (e.g., "I met with John
  yesterday"). Not caught by any regex — this is a structural limitation of
  regex-based redaction.

Every shipped Markdown file carries `redaction: applied-vYYYYMMDD`; that tag
attests to **these regexes having run**, not a guarantee of zero PII.

---

## 5. User override: `--no-redact`

`--no-redact` on any write command disables every pattern in §1. When set:

1. The CLI prints a prominent warning to stderr:

   ```
   [WARN] --no-redact is set. Raw PII will be written to disk.
          This may violate privacy obligations. Proceed? [y/N]
   ```

2. On confirmation, every output file gets `redaction: disabled` in its
   frontmatter instead of `applied-vYYYYMMDD`. Downstream `distill-meta`
   Phase 1.5 flags these files as `RAW` and halts unless the user also
   acknowledges at that phase.

3. `--no-redact` is never the default; there is no config-file toggle to
   make it silent. This is intentional friction.

---

## 6. Test vectors

Implementers of this policy MUST pass these test cases before claiming
conformance.

### 6.1 Positive cases (redaction MUST trigger)

| Input snippet                             | Expected placeholder kind |
|-------------------------------------------|---------------------------|
| `my cell is 13812345678`                  | `PHONE`                   |
| `email alice@example.com for details`     | `EMAIL-HASH`              |
| `身份证 110101199001011234`                | `ID`                      |
| `SSN 123-45-6789`                         | `ID`                      |
| `key sk-AbCdEf1234567890XyZqRsTuVwX`      | `KEY`                     |

### 6.2 Negative cases (redaction MUST NOT trigger)

| Input snippet                             | Why |
|-------------------------------------------|-----|
| `let's meet at 12345`                     | 5 digits, too short for any phone pattern |
| `version 1.2.3.4`                         | dotted-numeric, not an IP/phone/ID pattern (v1 does not redact IPs) |
| `@alice replied`                          | handle, not an email |

### 6.3 Known false-positive case (acceptable)

| Input snippet                             | Behavior |
|-------------------------------------------|----------|
| `transaction id 4532015112830366`         | May match `CARD` regex (16 digits). Accepted v1 limitation. User can `--no-redact` that specific file. |

---

## 7. Integration point

Every parser in `text-parsers.md`, `av-pipeline.md`, `image-doc-parsers.md`
is required to call redaction on the final Markdown string **before** writing
to disk. The ordering is:

```
parser → markdown-text → redact(markdown-text) → write(path, redacted)
                                   │
                                   └── frontmatter's `redaction:` set here
```

No parser is permitted to write, then retro-redact. Users / downstream skills
rely on the file-on-disk being the redacted copy from the first moment it
exists.
