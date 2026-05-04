# Rationale — huggingface

> 三段式 rationale 抽取自 `source-design-systems/huggingface/DESIGN.md`。

## Visual Theme

### decision: ML brand that refuses to look serious — sunshine yellow + cartoon emoji as identity

原 DESIGN.md 段落（verbatim）：
> Hugging Face is the rare ML brand that refuses to look serious. The hub leans into a sunshine-yellow accent (`#ffd21e`), a cartoon hugging-face emoji as the logo, and a confident **IBM Plex Mono** voice that reads more like a community zine than a research lab.

- **trade_off**: ML lab credibility（学院严肃感） ↔ community zine（玩味亲和）
- **intent**: 让 ML 平台的视觉对位是 community fanzine 而不是研究院冷感
- **avoid**: 学术蓝 / lab gray / 严肃 monospace 工程感 / 单调中性 SaaS palette

## Color

### decision: yellow as punctuation, never as surface — color-coded category accents handle taxonomy

原 DESIGN.md 段落（verbatim）：
> The page background is a clean off-white (`#fafafa`) with text in a deep slate (`#0d1117`), and the yellow appears in pull quotes, tags, "new" badges, and the model-card header strip — never as an entire surface, always as punctuation.

- **trade_off**: yellow 大面积（强 brand）↔ yellow 标点级（可读性 + 节制）
- **intent**: 让 yellow 出现就是"看这里"信号，而不是 brand 露面
- **avoid**: 整面 yellow 背景 / yellow 长文字 / yellow 与 category accent 同时打架

## Typography

### decision: IBM Plex Mono for headings + tags, sans only for paragraphs — config-file aesthetic

原 DESIGN.md 段落（verbatim）：
> The typographic system is monospace-forward in a way few product brands attempt: **IBM Plex Mono** for headings and tags, **Source Sans Pro** (or Inter) for body. The mix gives every page a "config file is the README" vibe — fitting for a platform built around `.gitattributes` and `model-card.md`.

- **trade_off**: sans heading 通用现代感 ↔ mono heading config-file 工程感
- **intent**: 让 headings 看起来像可粘到 Python 的 string — 平台 DNA 即可读
- **avoid**: serif heading / sans tag / mono 仅在 code block（错失身份）

## Components

### decision: 4-6px radii — closer to brutalist than rounded, "borders announce themselves"

原 DESIGN.md 段落（verbatim）：
> Shapes are crisp, not soft: 4–6px radii, 1px solid borders that announce themselves rather than hide. Tables are dense, with row hover in a faint gray (`#f3f4f6`).

- **trade_off**: 12-16px friendly radius（普世 SaaS）↔ 4-6px crisp（community-hub 工程感）
- **intent**: 让 chrome 像 GitHub 而非 Notion — 边界硬朗，density 友好
- **avoid**: 8px+ 圆角 SaaS chrome / 0px 完全硬朗（unreadable）/ 9999px pill on cards

## Components

### decision: category-tinted task tags (NLP blue, vision green, audio purple) — taxonomy as palette

原 DESIGN.md 段落（verbatim）：
> ### Category Accents (Model Tasks)
> - **NLP Blue** (`#2563eb`): Text/NLP task badges.
> - **Vision Green** (`#16a34a`): Computer-vision task badges.
> - **Audio Purple** (`#9333ea`): Audio/speech task badges.
> - **Multimodal Pink** (`#db2777`): Multimodal/diffusion task badges.
> - **Tabular Orange** (`#ea580c`): Tabular/structured task badges.

- **trade_off**: 单色 tag（一致简洁）↔ 五色 category tag（信息密度 + 类型识别）
- **intent**: 让 model browser 视觉直读 task 类型，不读文字也能粗扫
- **avoid**: 全 tag 同色（信息丢失）/ 自由发挥多色（taxonomy 失控）

## Voice

### decision: weight under 600 cap — "700 is too loud against yellow"

原 DESIGN.md 段落（verbatim）：
> - **Weight under 600**: 600 is the cap; 700 is too loud against yellow. Hierarchy is size and color.

- **trade_off**: 700 bold（信息层级强烈） ↔ 600 cap（与 yellow accent 共振不打架）
- **intent**: 让 weight 配合 yellow 的"punctuation"角色 — 不互抢眼球
- **avoid**: 700+ heading / 800 display / weight-driven hierarchy 在 yellow 旁
