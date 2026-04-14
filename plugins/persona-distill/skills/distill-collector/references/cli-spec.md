---
contract_version: 0.2.0
applies_to: distill-collector
status: PARTIAL-RUNNABLE
references:
  - ../SKILL.md
  - ../../distill-meta/references/output-spec.md
  - ../scripts/
---

# distill-collector — Unified CLI Specification

> **[PARTIAL-RUNNABLE]** This document defines the **contract** for a CLI
> named `distill-collector`. v0.2.0 ships **4 runnable parsers** under
> `../scripts/` (covering iMessage / email / Twitter / generic text); the
> remaining commands stay spec-only stubs. See §10 for the runnable subset
> and SKILL.md for the rationale (risks TEC-01 / TEC-02 / EST-02 — we promote
> a parser only when its input shape has been stable for ≥2 years).

Inspired by `agenmod/immortal-skill/immortal_cli.py`. All commands share the
global flags:

```
--output-root <path>     default: ./  (persona skill root containing knowledge/)
--dry-run                print the plan, do not write
--no-redact              skip redaction; warns loudly (see redaction-policy.md)
--log-level {debug,info,warn,error}
```

Exit code convention (applies to every command):

| Code | Meaning |
|------|---------|
| 0    | success |
| 2    | usage error (bad flags, missing args) |
| 3    | environment error (tool pointer not installed, e.g. `yt-dlp` missing) |
| 4    | input error (file unreadable, corrupt export) |
| 5    | output error (cannot write under `knowledge/`) |
| 10   | partial success (some records skipped; see stderr for count) |
| 20   | scaffolding stub: command is spec-only in v0.2.0, no runner available |

Code `0` is the success path for `scripts/redactor.py` (including
`--test`-vector success) and the four runnable parsers under §10.

---

## 1. `distill-collector platforms`

**Synopsis**: List supported platforms + per-platform maturity.

**Arguments**: none.

**Outputs** (stdout, table):

```
PLATFORM       MATURITY     TOOL-POINTER
wechat         reference    wechatDataBackup
qq             spec         QQExport
feishu         spec         feishu-export (official)
slack          reference    slack-export-viewer
dingtalk       spec         (manual export → generic)
imessage       reference    imessage-exporter
telegram       reference    telegram-export
email          reference    mbox/eml → generic
twitter        reference    twitter archive zip
generic-text   stub         (this skill, minimal reference)
audio-video    reference    whisper + ffmpeg + yt-dlp
image          reference    tesseract + exiftool
document       reference    pdfplumber / python-docx / ebooklib
```

Maturity legend:

- **spec** — only contract documented; no tool pointer vetted.
- **reference** — contract + a vetted third-party tool pointer.
- **stub** — a minimal reference implementation could ship (currently only
  `generic-text` qualifies).

**Exit**: 0 on print.
**Scaffolding note**: v1 prints the above table **statically**; maturity is
sourced from `text-parsers.md`, `av-pipeline.md`, `image-doc-parsers.md`.

---

## 2. `distill-collector setup <platform>`

**Synopsis**: Print credential / export preparation steps for a platform.
v1 performs **no** credential handling — it only prints instructions.

**Arguments**:

- `<platform>` — one of the values listed by `platforms`.

**Outputs** (stdout, markdown): a mini-runbook pulled from
`text-parsers.md` / `av-pipeline.md` / `image-doc-parsers.md` for that platform:
required export path, which third-party tool to install, where its output will
land on disk, what to feed back into `collect` / `import`.

**Example**:

```
$ distill-collector setup wechat
# WeChat setup
1. Install wechatDataBackup (Windows / macOS-via-parallels only).
2. Export conversations for contact X to ./exports/wechat/X/.
3. Then:  distill-collector collect --platform wechat --target ./exports/wechat/X
```

**Exit**: 0 on print. 2 if platform unknown. **20** if platform is `spec`-only.
**Scaffolding note**: No network calls, no keychain access. This command is
effectively `man`-style help.

---

## 3. `distill-collector collect --platform X --target Y`

**Synopsis**: Ingest a prepared export into `knowledge/chats/` (for chat
platforms) or `knowledge/articles/` (for email/twitter long-form).

**Arguments**:

- `--platform X` — required; must appear in `platforms`.
- `--target Y` — required; path to the prepared export directory or archive.
- `--subject <name>` — optional; the target persona's canonical display name;
  used by redaction as the "do not hash" anchor.
- `--since YYYY-MM-DD` / `--until YYYY-MM-DD` — optional date window.
- `--format <override>` — optional; forces a specific parser (e.g.
  `--format generic` when auto-detect fails).

**Outputs**: writes Markdown under
`{output-root}/knowledge/chats/{platform}/{conversation-slug}.md` per
`distill-meta/references/output-spec.md §2.4`. Each file carries the
frontmatter fields mandated by output-spec (`tier`, `tier_reason`,
`source_policy`, `author_of_record`, `captured_at`, plus
`redaction: applied-vYYYYMMDD`).

Writes / appends `knowledge/chats/{platform}/INDEX.md` with the list of
conversations, date range, record count, redaction state.

**Example**:

```
$ distill-collector collect --platform slack --target ./slack-export.zip \
      --subject "Alice Zhang" --since 2024-01-01
[SCAFFOLDING-ONLY] would parse slack-export.zip using slack-export-viewer,
                   write 37 conversations to ./knowledge/chats/slack/
```

**Exit**: 0 on full success, 10 on partial (skipped corrupt records), 20 for
spec-only platforms (prints the pointer to the third-party tool and exits).

**Scaffolding note**: **v1 never actually parses binary DB exports.** For every
platform except `generic-text`, `collect` prints a pointer to the canonical
third-party tool and exits 20. The contract is preserved so future
implementers (or the user's own script) drop into the same shape.

---

## 4. `distill-collector transcribe <file>`

**Synopsis**: Convert audio/video into a transcript under
`knowledge/transcripts/`.

**Arguments**:

- `<file>` — required; local audio (`.m4a/.mp3/.wav/.flac`), local video
  (`.mp4/.mov/.mkv/.webm`), or URL (handled via `yt-dlp`).
- `--model {base,small,medium,large-v3}` — Whisper model size; default `small`.
- `--language <code|auto>` — default `auto`.
- `--diarize` — speaker diarization flag; optional, requires extra tooling.

**Outputs**: writes
`{output-root}/knowledge/transcripts/{slug}-{ISO8601}.md` with timestamped
paragraphs and a media pointer in `knowledge/media/{slug}.md` (metadata only,
not the raw bytes). See `av-pipeline.md` for command templates.

**Example**:

```
$ distill-collector transcribe ./interview.mp4 --model medium --language zh
[SCAFFOLDING-ONLY] would run:
  ffmpeg -i interview.mp4 -vn -acodec copy interview.aac
  whisper interview.aac --model medium --language zh \
          --output_format txt --output_dir ./knowledge/transcripts/
```

**Exit**: 0 on success, 3 if Whisper/ffmpeg/yt-dlp missing, 20 (scaffolding).

**Scaffolding note**: v1 prints the command it **would** run, does not exec.

---

## 5. `distill-collector import <file> --format generic`

**Synopsis**: Manual text import. The most stable and only actually-runnable
path in v1.

**Arguments**:

- `<file>` — required; a UTF-8 plain-text or Markdown file.
- `--format {generic,markdown,lines}` — default `generic` (heuristic line
  parsing: blank line = message boundary, `name:` prefix = speaker).
- `--destination {chats,articles,transcripts}` — default `chats`.
- `--subject <name>` — anchor identity for redaction.

**Outputs**: one Markdown file under the chosen subdirectory, carrying the
standard frontmatter + `redaction: applied-vYYYYMMDD`.

**Example**:

```
$ distill-collector import ./notes.txt --format generic --destination articles \
      --subject "Alice Zhang"
wrote ./knowledge/articles/notes-20260414.md  (redaction: applied-v20260414)
```

**Exit**: 0 on success, 4 on input error, 5 on output error.

**Scaffolding note**: `import --format generic` is the one command that v1
**is expected to actually run** in a reference implementation; all other
commands default to exit-20 stubs. Keeping this hot path runnable is what
lets distill-meta's Phase 1 always have a fallback.

---

## 6. Invariants across all commands

1. Every write path MUST lie under `{output-root}/knowledge/`. Writing outside
   is a fatal bug (exit 5).
2. Every Markdown written MUST pass through redaction (see
   `redaction-policy.md`) unless `--no-redact` is set.
3. Every file MUST carry the frontmatter required by
   `distill-meta/references/output-spec.md §2.4`.
4. No command mutates `components/`, `manifest.json`, `versions/`, or
   `validation-report.md` — those are distill-meta's territory.
5. Commands are **idempotent where possible**: re-running `import` on the same
   input produces byte-identical output (modulo timestamps in the frontmatter's
   `generated_at`, which is normalized to the input file's mtime when present).

---

## 10. Runnable subset (v0.2.0)

The four CLIs below ship as standalone Python 3.9+ scripts under
`../scripts/`. They use only stdlib (`sqlite3`, `mailbox`, `zipfile`, `json`,
`hashlib`, `re`, `argparse`) — no `pip install` step. Each script calls
`scripts/redactor.py` before writing (unless `--no-redact` with the §5 stderr
warning).

| CLI command (spec) | Concrete runner | Covers |
|--------------------|-----------------|--------|
| `import --format generic` (§5) | `scripts/generic_import.py` | any UTF-8 .txt / .md → chat or article |
| `collect --platform imessage` (§3) | `scripts/imessage_parser.py` | macOS `chat.db` → per-contact .md |
| `collect --platform email` (§3) | `scripts/mbox_parser.py` | `.mbox` → per-thread .md |
| `collect --platform twitter` (§3) | `scripts/twitter_archive_parser.py` | Twitter "Download your data" zip → per-year .md |
| (shared infra) | `scripts/redactor.py` | regex PII redactor + embedded §6 self-tests |

One-liners (each writes under `{destination}/knowledge/...`):

```bash
python scripts/generic_import.py --source notes.txt --subject "Alice Z" --destination ./alice
python scripts/imessage_parser.py --db ~/Library/Messages/chat.db --subject "Alice Z" --destination ./alice
python scripts/mbox_parser.py --mbox All-Mail.mbox --subject "Alice Z" --email-address alice@example.com --destination ./alice
python scripts/twitter_archive_parser.py --archive twitter-archive.zip --subject "Alice Z" --destination ./alice
python scripts/redactor.py --test     # validate redaction conformance
```

The remaining commands (`platforms`, `setup`, `transcribe`, and `collect` for
WeChat/QQ/Feishu/Slack/Dingtalk/Telegram) remain exit-20 stubs in v0.2.0; the
contract above is preserved so future implementers / user scripts drop into
the same shape.
