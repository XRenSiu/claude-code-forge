---
policy_version: 0.1.0
default_language: zh
borrowed_from: https://github.com/alchaincyf/nuwa-skill [UNVERIFIED-FROM-README]
applies_to: distill-collector (ingestion filter), persona-judge (primary_source_ratio)
---

# Source Whitelist — 高信度来源白名单

> Sources that have historically demonstrated **high primary/secondary fidelity**: long-form
> interviews with raw transcripts, first-person essays, newsroom with fact-checking discipline.

## Core Rules

- **Whitelisted sources count 1.0× weight** when computing `primary_source_ratio`.
- **Grey sources (unlisted, non-blacklisted) count 0.5× weight.**
- **Blacklisted sources count 0× weight** (see `blacklist.md`).

These weights feed `manifest.json → sources.primary_ratio`, which persona-judge reads for the
`Primary Source Ratio` rubric dimension (≥0.5 required to score ≥5/10).

## Chinese Defaults (default_language: zh)

| 来源 | 默认 tier | 备注 |
|------|----------|------|
| 36氪（深度栏目，非快讯） | secondary | 长访谈常附录音，可升 primary 若引用原录音 |
| 晚点 LatePost | secondary | 编辑部信用高，paraphrase 忠实；部分访谈含大段直引 |
| 财新 | secondary | 事实核查严格，商业/政策领域优先采用 |
| 虎嗅（精选长文，selectively） | secondary | 按作者筛选；普通专栏视为 grey |
| 一席 / 圆桌派 / GQTalk | primary | 本人亲述演讲或对谈，近似一手 |
| 本人亲自运营的公众号 / 博客 / Newsletter | primary | 直接作者文本 |
| 本人受访的纸媒/学刊 原文 | primary | 引用原话部分；编辑导语视为 secondary |

### 升降级规则 / Tier Adjustments

- 访谈含 raw transcript 或录音 → primary（即使媒体本身只是 secondary）。
- Whitelist 来源若被证明该篇为转载/二次编辑 → 降为 grey。
- 未列出但有明确作者署名 + 可溯源链接 → grey（0.5×），不是自动 primary。

## English Stub (default_language: en)

> TODO: populate via English-corpus review (SPEC-05).

Placeholder candidates:

- **The Information** — subscription reporting, high primary-source density on tech execs.
- **Stratechery** (Ben Thompson) — author's own analytical writing; primary for Thompson,
  secondary for others he discusses.
- **Primary interview transcripts** — Lex Fridman Podcast transcripts, Tim Ferriss Show
  transcripts, Acquired podcast show-notes.
- **The author's own blog / book / newsletter** — always primary (Paul Graham essays,
  Patrick Collison's site, etc.).
- High-rigor newsrooms: The New Yorker long-form profiles, NYT Magazine.

## Override Procedure

Per-persona overrides live in the persona skill's `config.yaml` under
`source_policy.whitelist_overrides`. Overrides MUST cite reason + review date (ISO-8601).
