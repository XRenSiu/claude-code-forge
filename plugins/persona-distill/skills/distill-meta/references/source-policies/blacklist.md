---
policy_version: 0.1.0
default_language: zh
borrowed_from: https://github.com/alchaincyf/nuwa-skill [UNVERIFIED-FROM-README]
applies_to: distill-collector (ingestion filter), persona-judge (primary_source_ratio)
---

# Source Blacklist — 降质来源黑名单

> Sources on this list are heavily weighted **against** persona quality. They are noisy,
> para-phrased, SEO-farmed, or emotionally-inflated and tend to destroy voice fidelity.

## Core Rule

> **Blacklisted sources do NOT count toward `primary_source_ratio` in persona-judge.**
> They may still be ingested (`distill-collector` will not reject them outright), but they
> are tagged `tier: tertiary` in `knowledge/**` frontmatter and contribute 0× weight when
> computing the ratio declared in `manifest.json → sources.primary_ratio`.

If more than 40% of ingested corpus is blacklisted, `distill-collector` MUST surface a
warning to the user before proceeding to Phase 2 extraction.

## Chinese Defaults (default_language: zh)

| 来源 | 原因 / Reason |
|------|---------------|
| 知乎 | 半匿名用户改写 + 投票驱动的"金句化"扭曲真实观点；高赞答案常为二次加工 |
| 公众号（非本人运营） | 自媒体转述、标题党、情绪放大；常为二手或三手信息 |
| 百度百科 | 编辑门槛低、来源不透明、大量复制粘贴；典型三手来源 |
| 微博热搜 | 情绪驱动摘录、脱离语境的单句截图、不可溯源 |
| 今日头条 / 抖音图文 | 算法优化的标题诱饵，内容多为聚合二次创作 |
| 搜狐号 / 网易号等聚合号 | 与公众号同问题，且常有水军批量复制 |

### 例外 / Exceptions

- 若本人亲自运营且长期更新的公众号 / 知乎专栏 → 移至 **whitelist**（tier: primary）。
- 本人参与的知乎 Live / 圆桌直接回答 → tier: primary（不因平台被连坐）。

## English Stub (default_language: en)

> TODO: populate via English-corpus review (tracked in SPEC-05, language-parameterization).

Placeholder candidates (not yet verified — do not enforce in code until reviewed):

- Wikipedia **user-space pages** and talk pages (main-space articles are handled under
  primary-vs-secondary.md as tertiary, not blacklisted).
- **Medium churn content** — SEO-farmed motivational posts, "10 lessons from X" listicles
  that paraphrase without citation.
- **Low-effort aggregator blogs** — Business Insider-style quote-mining, content farms,
  "Famous quotes by …" compilations.
- LinkedIn influencer posts that paraphrase without source links.

## Override Procedure

Users may add / remove entries in the **persona-skill's own** `config.yaml` under
`source_policy.blacklist_overrides`. The global defaults here are the fallback; per-persona
overrides take precedence. Overrides MUST cite a reason and an ISO-8601 review date.
