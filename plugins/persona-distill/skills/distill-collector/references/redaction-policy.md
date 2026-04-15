---
contract_version: 0.3.0
applies_to: distill-collector — PII redaction at write-time
status: RUNNABLE
references:
  - ./cli-spec.md
  - ../../distill-meta/references/output-spec.md
  - ../scripts/redactor.py
changelog:
  - 0.3.0 — Added Chinese + Western street address patterns (CN-ADDR, ADDR), Chinese full-name heuristic (CN-NAME, introducer-gated to reduce false positives on historical/place names), and sensitive-topic inline flags (FLAG:MEDICAL / FLAG:POLITICAL / FLAG:RELIGIOUS). Flags tag content for human review without hashing — reviewers decide per-instance. Closes integration.md §6.2 S1 (partial — full NER is still v2 work).
  - 0.2.0 — Unified write-time policy + embedded test vectors in redactor.py.
---

# Redaction Policy — Unified Write-Time PII Filter

> **[RUNNABLE]** This document pins the regex patterns, placeholder format,
> and override behavior that every parser (text, av, image-doc) MUST apply at
> **write-time** before Markdown is persisted to `knowledge/`. The reference
> implementation now ships under `../scripts/redactor.py` (stdlib-only
> Python 3.9+); the §6 test vectors are embedded as `unittest` cases and run
> via `python redactor.py --test`. Users implementing their own import
> scripts MUST still follow this spec — `distill-meta` Phase 1.5 trusts the
> `redaction: applied-vYYYYMMDD` frontmatter tag as an unforged claim.

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

### 1.6 Street addresses (v0.3.0)

```regex
# Chinese address: optional 省/自治区 + 市 + optional 区/县 + 路/街 + 号
# Anchored on 号 suffix to avoid false positives on partial locations.
(?:[\u4e00-\u9fa5]{2,8}(?:省|自治区|特别行政区))?
[\u4e00-\u9fa5]{2,10}市
(?:[\u4e00-\u9fa5]{1,10}(?:区|县))?
[\u4e00-\u9fa5\w]{2,30}(?:路|街|巷|大道|胡同)
[\u4e00-\u9fa5\w]*?\d+号

# Western address: number + 1-5 words + street-type
\b\d{1,5}\s+(?:[A-Z][a-z]+\s+){1,5}
(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way)\b
```

### 1.7 Chinese full names (v0.3.0, introducer-gated)

```regex
# Must be preceded by an introducer word to reduce false positives on
# historical figures / place names that happen to start with a surname.
(?:我叫|他叫|她叫|名字叫|名字是|名字|姓名|联系人|客户|用户|员工|
  老师|同学|经理|总监|先生|女士)
\s*[<top-100-百家姓>][\u4e00-\u9fa5]{1,2}\b
```

Without this introducer gate, a surname+given-name regex produces
unacceptable false-positive rates on Chinese prose (王维 the Tang poet,
张家口 the city, etc.). The trade-off: names in casual mention ("I ran
into 张伟 yesterday") without an introducer survive. NER is v2 work.

### 1.8 Sensitive-topic flags (v0.3.0, non-redacting)

These patterns do NOT hash/obscure content — they prepend an inline
`[FLAG:KIND]` tag so human reviewers can triage before publishing.

```regex
# Medical
(?:确诊|诊断|病史|患有|服用|处方|手术|化疗|
  diagnosed\s+with|suffers\s+from|prescribed|on\s+medication)

# Political
(?:党员|入党|政治面貌|支持.{0,3}党|反对.{0,3}党|
  party\s+member|voted\s+for|voting\s+record)

# Religious
(?:信仰|信教|皈依|受洗|伊斯兰|基督|佛教|道教|
  convert(?:ed)?\s+to|practicing\s+(?:christian|muslim|jewish|buddhist))
```

Rationale: these topics need human judgment — a medical diagnosis
mentioned in public biography differs from one from a private chat. The
flag surfaces the mention without deciding; reviewers use `--no-redact`
only for false-positive removal, not to suppress FLAG tags.

---

## 2. Placeholder format

Redacted matches are replaced by `[REDACTED:<KIND>-<4char-hash>]`, where
`<4char-hash>` is the first 4 hex chars of `SHA-256(match + persona-salt)`.
The salt is the `fingerprint` seed from `manifest.json` when available,
otherwise the literal string `"distill-collector-v1"`.

| Category          | Placeholder example          |
|-------------------|------------------------------|
| phone             | `[REDACTED:PHONE-3a9f]`      |
| email             | `[REDACTED:EMAIL-HASH-7c21]` |
| id (CN/US)        | `[REDACTED:ID-1b8e]`         |
| credit card       | `[REDACTED:CARD-004d]`       |
| api key           | `[REDACTED:KEY-ff12]`        |
| cn address (v0.3) | `[REDACTED:CN-ADDR-5f7a]`    |
| address (v0.3)    | `[REDACTED:ADDR-9c12]`       |
| cn name (v0.3)    | `[REDACTED:CN-NAME-e84d]`    |
| geo (EXIF)        | `[REDACTED-GEO]`             |
| flag (v0.3)       | `[FLAG:MEDICAL]<content>`    |

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

## 4. Scope limits (things v0.3.0 still deliberately does NOT redact)

- **Photographs themselves**. Faces in images are **not** blurred. Users who
  need that must pre-process images before handing them to the pipeline.
  This is a **[USER-RESPONSIBILITY]**.
- **Free-text names without an introducer**. CN-NAME pattern requires a
  preceding word like `联系人` / `客户` / `姓名` to fire. Casual mentions
  (`"和张伟聊天"`) survive. Full NER is v2 work.
- **English / Western full names**. No heuristic — the name space is too
  ambiguous with common words to regex safely. v2.
- **Birth dates / ages** when not in an ID pattern.
- **IP addresses**. Not redacted by default.
- **Usernames / handles** (`@alice`). Treated as speaker aliases per §3, not
  stripped.
- **Addresses without 号 suffix or street-type keyword**. Partial addresses
  (区 / 街 names alone) survive.

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
| `北京市朝阳区建国路88号` (v0.3)             | `CN-ADDR`                 |
| `广东省深圳市南山区科技园南路10号` (v0.3)   | `CN-ADDR`                 |
| `221 Baker Street London` (v0.3)          | `ADDR`                    |
| `1600 Pennsylvania Avenue` (v0.3)         | `ADDR`                    |
| `联系人张伟` (v0.3, introducer-gated)      | `CN-NAME`                 |
| `他去年确诊了糖尿病` (v0.3, flag)           | `[FLAG:MEDICAL]` prefix   |
| `她是 2015 年入党的` (v0.3, flag)           | `[FLAG:POLITICAL]` prefix |
| `2010 年皈依了佛教` (v0.3, flag)            | `[FLAG:RELIGIOUS]` prefix |

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
| `张伟的历史贡献` (v0.3)                    | CN-NAME **does NOT** fire (no introducer). Accepted — regex cannot distinguish historical figure from casual mention. |
| `在北京路开会` (v0.3)                      | CN-ADDR **does NOT** fire (no 号 suffix). Accepted — no anchor. |

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

---

## 8. Reference implementation (v0.2.0)

The runnable Python module lives at `../scripts/redactor.py`. It exposes:

```python
from redactor import redact
out = redact(input_text, salt="distill-collector-v1")  # str → str
```

and a CLI:

```
python redactor.py --in input.txt --out redacted.txt [--salt S] [--no-redact]
python redactor.py --test    # run all §6.1 / §6.2 vectors as unittests
```

Implementation notes:

- All §1 patterns live in a single ordered list inside `redactor.py`.
  Order matters: API-key patterns run before EMAIL/PHONE/CARD so that a
  long token like `sk-Ab...` is not double-matched.
- The `EMAIL-HASH` placeholder uses the suffix `-HASH-` (matching §2's
  example) instead of bare `-`, preserving downstream search heuristics
  that look for the `EMAIL-HASH-` prefix.
- The CLI exit codes mirror cli-spec.md: 0 success, 2 usage, 4 input,
  5 output. `--test` returns 0 if all vectors pass, 1 otherwise.
- All four runnable parsers (`generic_import.py`, `imessage_parser.py`,
  `mbox_parser.py`, `twitter_archive_parser.py`) call `redact()` before
  writing; `--no-redact` triggers the §5 stderr warning via the shared
  `_warn_no_redact` helper.
