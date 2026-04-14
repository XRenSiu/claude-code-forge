---
contract_version: 0.1.0
applies_to: distill-collector — text/chat platforms
status: SCAFFOLDING-ONLY
references:
  - ./cli-spec.md
  - ./redaction-policy.md
  - ../../distill-meta/references/output-spec.md
---

# Text & Chat Platform Parsers — Reference

> **[SCAFFOLDING-ONLY]** None of the platform-specific parsers in this document
> ship as runnable code in v1. For each platform we document: (a) the export
> method the user must perform, (b) the canonical third-party tool pointer,
> (c) the target output path + Markdown schema. Only `generic-text` ships a
> minimal reference impl (see §11). Rationale: risks TEC-02 / EST-02 — shipping
> 8 platform parsers that each depend on moving DB schemas is a liability.

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
| iMessage   | `chat.db` from `~/Library/Messages/`                   | `imessage_reader`            | `knowledge/chats/imessage/{contact}.md`  | spec-only  |
| Telegram   | Telegram Desktop → "Export chat history" (HTML/JSON)   | `telegram-export`            | `knowledge/chats/telegram/{chat}.md`     | spec-only  |
| Email      | `.mbox` / `.eml` from mail client                      | `mbox-reader` / stdlib mail  | `knowledge/articles/email/{thread}.md`   | spec-only  |
| Twitter/X  | Account settings → "Download your data" (ZIP)          | twitter-archive JSON         | `knowledge/articles/twitter/{year}.md`   | spec-only  |
| Generic    | Hand-typed / copy-paste to `.txt` / `.md`              | (this skill)                 | configurable via `--destination`         | **stub**   |

> All "spec-only" rows mean: the contract below is binding; the runner is the
> user's responsibility (third-party tool output → `distill-collector import
> --format generic`). See cli-spec.md §3 for exit-code semantics.

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

## 6. iMessage  `[USER-RESPONSIBILITY]`

**Input shape**: `~/Library/Messages/chat.db` on macOS (SQLite). Requires Full Disk Access to read.

**Tool pointer**: [`imessage_reader`](https://github.com/niftycode/imessage_reader) or [`imessage-exporter`](https://github.com/ReagentX/imessage-exporter). The latter emits HTML/TXT; run the TXT output through `distill-collector import --format generic`.

**Output schema**: `knowledge/chats/imessage/{contact}.md`. Phone numbers in the `contact` field are redacted per redaction-policy §2 (email-style placeholder).

**Parser status**: spec-only.

---

## 7. Telegram  `[USER-RESPONSIBILITY]`

**Input shape**: Telegram Desktop → Settings → Advanced → "Export Telegram data" (HTML or JSON).

**Tool pointer**: [`telegram-export`](https://github.com/expectocode/telegram-export) for API-side; Desktop's built-in export is the safer route.

**Output schema**: `knowledge/chats/telegram/{chat-slug}.md`. Media messages collapsed to `_[attachment: type → redacted]_`.

**Parser status**: spec-only.

---

## 8. Email  `[USER-RESPONSIBILITY]`

**Input shape**: `.mbox` (Apple Mail, Thunderbird) or directory of `.eml` files.

**Tool pointer**: Python stdlib `mailbox` / `email` modules; no third-party tool required, but still out-of-scope for v1 runner. One thread = one file.

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

**Parser status**: spec-only (goes to `articles/`, not `chats/`, because email threads are long-form).

---

## 9. Twitter / X  `[USER-RESPONSIBILITY]`

**Input shape**: "Download your archive" ZIP containing `tweet.js` + media folder.

**Tool pointer**: no single vetted tool; treat `tweet.js` as JSON (strip the `window.YTD.tweets.part0 = ` prefix) and emit Markdown.

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

**Parser status**: spec-only.

---

## 10. Generic Text  **[stub — minimal reference OK]**

**Input shape**: any UTF-8 plain text or Markdown file the user hands over.

**Tool pointer**: this skill itself, via `distill-collector import --format
generic`.

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

**Parser status**: **stub** — can ship a ~50-line reference implementation in
a later wave without violating the scaffolding constraint, because it has no
platform-specific dependency. Not shipped in this wave (spec docs only).

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
