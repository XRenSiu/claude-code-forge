---
contract_version: 0.2.0
applies_to: distill-collector — text/chat platforms
status: PARTIAL-RUNNABLE
references:
  - ./cli-spec.md
  - ./redaction-policy.md
  - ../../distill-meta/references/output-spec.md
---

# Text & Chat Platform Parsers — Reference

> **[PARTIAL-RUNNABLE]** v0.2.0 promoted **iMessage / email / Twitter / generic**
> from spec-only to runnable Python scripts under `../scripts/`. The remaining
> 6 platforms (WeChat / QQ / Feishu / Slack / Dingtalk / Telegram) stay
> spec-only pending stable export formats. For each spec-only platform we
> document: (a) the export method the user must perform, (b) the canonical
> third-party tool pointer, (c) the target output path + Markdown schema.
> Rationale: risks TEC-02 / EST-02 — shipping parsers that each depend on
> moving DB schemas is a liability; we promote a parser only when the input
> shape has been stable for ≥2 years.

All parsers feed the unified pipeline defined in `cli-spec.md`. All writes go
under `knowledge/chats/{platform}/` (or `knowledge/articles/` for long-form
email/tweets) and all pass through the redaction pipeline in
`redaction-policy.md`.

## 0. Platform Summary Table

| Platform   | Export Method                                          | Tool Pointer                 | Output Path                              | Status     |
|------------|--------------------------------------------------------|------------------------------|------------------------------------------|------------|
| WeChat     | macOS/Win local DB dump                                | `wechatDataBackup`           | `knowledge/chats/wechat/{contact}.md`    | spec-only  |
| QQ         | TM DB export (Windows)                                 | `QQExport` / MobileQQ-export | `knowledge/chats/qq/{contact}.md`        | spec-only  |
| Feishu     | Admin → compliance export (CSV/JSON)                   | Feishu official export       | `knowledge/chats/feishu/{channel}.md`    | spec-only  |
| Slack      | Workspace export (ZIP of JSON)                         | `slack-export-viewer`        | `knowledge/chats/slack/{channel}.md`     | spec-only  |
| Dingtalk   | Admin compliance / phone-side manual export            | (manual → generic)           | `knowledge/chats/dingtalk/{channel}.md`  | spec-only  |
| iMessage   | `chat.db` from `~/Library/Messages/`                   | `scripts/imessage_parser.py` | `knowledge/chats/imessage/{contact}.md`  | **RUNNABLE** (see scripts/imessage_parser.py) |
| Telegram   | Telegram Desktop → "Export chat history" (HTML/JSON)   | `telegram-export`            | `knowledge/chats/telegram/{chat}.md`     | spec-only  |
| Email      | `.mbox` / `.eml` from mail client                      | `scripts/mbox_parser.py`     | `knowledge/articles/email/{thread}.md`   | **RUNNABLE** (see scripts/mbox_parser.py) |
| Twitter/X  | Account settings → "Download your data" (ZIP)          | `scripts/twitter_archive_parser.py` | `knowledge/articles/twitter/{year}.md` | **RUNNABLE** (see scripts/twitter_archive_parser.py) |
| Generic    | Hand-typed / copy-paste to `.txt` / `.md`              | `scripts/generic_import.py`  | configurable via `--destination`         | **RUNNABLE** (see scripts/generic_import.py) |

> "spec-only" rows mean: the contract below is binding; the runner is the
> user's responsibility (third-party tool output → `scripts/generic_import.py`).
> "**RUNNABLE**" rows mean a Python 3.9+ stdlib-only script is provided under
> `../scripts/`; see each platform section for the one-line invocation.
> See cli-spec.md §3 for exit-code semantics.

---

## 1. WeChat  `[USER-RESPONSIBILITY]`

**Input shape**: local chat database from WeChat macOS (`~/Library/Containers/com.tencent.xinWeChat/.../MSG*.db`) or Windows (`Documents\WeChat Files\{wxid}\Msg\`). Accounts are per-device-encrypted; extraction is the user's job.

**Tool pointer**: [`wechatDataBackup`](https://github.com/git-jiadong/wechatDataBackup) (Windows-first, read the project's own OS support matrix). Feed its Markdown export to `distill-collector import --format generic`.

**Output schema** — one file per contact `knowledge/chats/wechat/{contact-slug}.md`:

```markdown
---
tier: primary
tier_reason: direct conversation with subject
source_policy: private-chat
author_of_record: "{subject-name}"
captured_at: 2026-04-14T00:00:00Z
platform: wechat
contact: "PersonA"
redaction: applied-v20260414
---

## 2024-03-02

**14:32 · {subject-name}**: ...

**14:33 · PersonA**:
> quoted: "earlier message..."
... reply body ...

_[attachment: image → redacted — see knowledge/media/INDEX.md]_
```

**Parser status**: spec-only. Do not invent DB-schema parsing in v1.

---

## 2. QQ  `[USER-RESPONSIBILITY]`

**Input shape**: TM / PCQQ message DB (Windows path `Documents\Tencent Files\{qq}\Msg3.0.db`). Android MobileQQ DB extraction requires root.

**Tool pointer**: `QQExport` / community tools (verify signature before use). Output must be reshaped into the same per-contact Markdown schema as WeChat.

**Output schema**: identical to WeChat §1 but `platform: qq` and path `knowledge/chats/qq/{contact}.md`.

**Parser status**: spec-only.

---

## 3. Feishu (Lark)  `[USER-RESPONSIBILITY]`

**Input shape**: tenant admin → compliance → chat-export. Produces CSV/JSON per channel or per user.

**Tool pointer**: Feishu official compliance export (no third-party reimplementation recommended — the official format changes yearly).

**Output schema**: one file per channel `knowledge/chats/feishu/{channel-slug}.md`, same conversation block shape (`**HH:MM · speaker**: body`). Thread replies rendered as `  - **HH:MM · speaker (thread)**: body`.

**Parser status**: spec-only.

---

## 4. Slack  `[USER-RESPONSIBILITY]`

**Input shape**: workspace admin "Export workspace data" → ZIP of per-channel JSON files.

**Tool pointer**: [`slack-export-viewer`](https://github.com/hfaran/slack-export-viewer) for browsing; for Markdown conversion use a small user script that iterates the JSON files.

**Output schema**: `knowledge/chats/slack/{channel-slug}.md`. User mentions (`<@U12345>`) resolved via `users.json`; anchor identity (`--subject`) preserved as speaker name, all others hashed per redaction-policy §2.

**Parser status**: spec-only.

---

## 5. Dingtalk  `[USER-RESPONSIBILITY]`

**Input shape**: enterprise compliance export, or phone-side manual copy → `.txt`.

**Tool pointer**: no widely-vetted third-party tool; route through `generic` import.

**Output schema**: `knowledge/chats/dingtalk/{channel-slug}.md` with the same speaker-prefixed block format.

**Parser status**: spec-only.

---

## 6. iMessage  **[RUNNABLE]**

**Runnable path**: `scripts/imessage_parser.py` reads `chat.db` directly via stdlib `sqlite3`, handles Core Data timestamps + `attributedBody` blobs, and writes per-contact Markdown.

```
python scripts/imessage_parser.py --db ~/Library/Messages/chat.db \
    --subject "Alice Z" --destination ./alice-persona [--since 2024-01-01]
```

**Input shape**: `~/Library/Messages/chat.db` on macOS (SQLite). Requires Full Disk Access to read; copy the file to a working dir if you prefer not to grant FDA to the Python interpreter.

**Tool pointer (legacy / alternative)**: [`imessage_reader`](https://github.com/niftycode/imessage_reader) or [`imessage-exporter`](https://github.com/ReagentX/imessage-exporter). The latter emits HTML/TXT; run the TXT output through `scripts/generic_import.py`. The shipped script supersedes both for the common case.

**Quirks handled**: (a) dates stored as nanoseconds-since-2001 on Catalina+ vs. seconds on older macOS — auto-detected by magnitude; (b) message text in either `text` column or `attributedBody` NSArchiver blob — best-effort UTF-8 byte-scan, falling back to `[UNREADABLE-ATTRIBUTED-BODY]`.

**Output schema**: `knowledge/chats/imessage/{contact-slug}.md`. Phone numbers / emails in the `contact` frontmatter field are redacted per redaction-policy §2 before slugification, so the file path itself does not leak PII.

**Parser status**: **runnable** (v0.2.0).

---

## 7. Telegram  `[USER-RESPONSIBILITY]`

**Input shape**: Telegram Desktop → Settings → Advanced → "Export Telegram data" (HTML or JSON).

**Tool pointer**: [`telegram-export`](https://github.com/expectocode/telegram-export) for API-side; Desktop's built-in export is the safer route.

**Output schema**: `knowledge/chats/telegram/{chat-slug}.md`. Media messages collapsed to `_[attachment: type → redacted]_`.

**Parser status**: spec-only.

---

## 8. Email  **[RUNNABLE]**

**Runnable path**: `scripts/mbox_parser.py` reads `.mbox` via stdlib `mailbox`, filters threads to those the subject participates in, strips nested `>>` quote chains, and writes one Markdown file per thread.

```
python scripts/mbox_parser.py --mbox ./All-Mail.mbox --subject "Alice Z" \
    --email-address alice@example.com --destination ./alice-persona
```

**Input shape**: `.mbox` (Apple Mail, Thunderbird, mbox export from Gmail Takeout). `.eml` directories are out of scope for v0.2.0 — concatenate them into an mbox first if needed.

**Tool pointer (legacy / alternative)**: stdlib `mailbox` / `email` modules — that's exactly what the shipped script wraps. No third-party tool required.

**Quoted-reply handling**: lines starting with one `>` are kept (one level of quote context); lines with `>>` or deeper are stripped; signature blocks beginning `-- \n` are dropped.

**Output schema**: one file per thread under `knowledge/articles/email/{YYYY-MM}-{thread-subject-slug}.md`, with:

```markdown
---
tier: primary
source_policy: private-correspondence
author_of_record: "{subject}"
platform: email
thread_subject: "..."
redaction: applied-v20260414
---

**From**: {subject} <REDACTED:EMAIL-HASH-XXXX>
**Date**: 2024-01-08

{body}

---

**From**: PersonA <REDACTED:EMAIL-HASH-YYYY>
**Date**: 2024-01-09

{body}
```

**Parser status**: **runnable** (v0.2.0); writes to `articles/`, not `chats/`, because email threads are long-form.

---

## 9. Twitter / X  **[RUNNABLE]**

**Runnable path**: `scripts/twitter_archive_parser.py` accepts the Twitter "Download your data" ZIP **or** an extracted directory, strips the `window.YTD.tweets.part0 = ` JS prefix from `data/tweets.js`, and emits one file per year.

```
python scripts/twitter_archive_parser.py --archive ./twitter-2024-archive.zip \
    --subject "Alice Z" --destination ./alice-persona
```

**Input shape**: "Download your archive" ZIP containing `data/tweets.js` (or legacy `data/tweet.js`) + media folder.

**Tool pointer (legacy / alternative)**: no single vetted third-party tool; the shipped script is the canonical runner. `@handle` mentions are flattened to `[REDACTED-HANDLE]` in the Markdown to avoid leaking other users' identities.

**Output schema**: one file per year `knowledge/articles/twitter/{YYYY}.md`:

```markdown
---
tier: primary
source_policy: public-posts
author_of_record: "{subject}"
platform: twitter
year: 2024
redaction: applied-v20260414
---

## 2024-03-02 14:32

tweet body...

  - reply to: @PersonA → [REDACTED-HANDLE]
```

**Parser status**: **runnable** (v0.2.0).

---

## 10. Generic Text  **[RUNNABLE]**

**Runnable path**: `scripts/generic_import.py` is the most stable path — works on any UTF-8 `.txt` / `.md` file regardless of source platform.

```
python scripts/generic_import.py --source ./notes.txt --subject "Alice Z" \
    --destination ./alice-persona
```

It auto-detects whether the input looks like a chat (any line matching `speaker:` prefix) and routes output to `chats/generic/` or `articles/generic/` accordingly.

**Input shape**: any UTF-8 plain text or Markdown file the user hands over.

**Tool pointer**: `scripts/generic_import.py` (was: this skill via the planned CLI).

**Heuristic rules** (the only parsing v1 is expected to actually run):

1. Blank line = message boundary.
2. Leading `^\s*([^:\n]{1,40}):\s` = speaker prefix; left side becomes speaker.
3. Leading `^> ` = quoted prior message (preserved as blockquote).
4. Lines starting with `[image]`, `[video]`, `[file]` become
   `_[attachment: … → redacted]_`.
5. If no speaker prefix detected in the whole file, wrap the content as a
   single article under `knowledge/articles/generic/{slug}.md` instead of
   `chats/`.

**Output schema**: same frontmatter shape as the platform-specific files
above, `platform: generic`, `source_policy: user-provided`.

**Parser status**: **runnable** (v0.2.0). Ships under 200 lines of stdlib.

---

## 11. Cross-platform invariants

- **Speaker resolution**: only `--subject` survives unhashed. Every other
  speaker is mapped to a stable `PersonA / PersonB / …` alias per
  redaction-policy §3.
- **Timestamps**: normalized to local ISO8601 in the frontmatter and kept as
  the emitter's local time in the body (do not silently re-tz).
- **Attachments**: never written into `knowledge/chats/`. Pointers go to
  `knowledge/media/` per output-spec.md §1. Redaction of images themselves is
  out-of-scope for v1 (see redaction-policy.md §4).
- **Empty conversations**: skipped with a log line; no empty Markdown file
  created.
- **Encoding**: everything UTF-8. Legacy GBK etc. must be transcoded upstream.

## 12. Unsupported (explicit non-goals for v1)

- Discord — no user demand yet; would follow the same pattern.
- LINE / KakaoTalk / WhatsApp — export formats change often; user can always
  fall back to `import --format generic`.
- Real-time incremental sync — every collection is a one-shot snapshot.
- Cross-platform identity merging — handled downstream by
  `distill-meta` Phase 2, not here.
