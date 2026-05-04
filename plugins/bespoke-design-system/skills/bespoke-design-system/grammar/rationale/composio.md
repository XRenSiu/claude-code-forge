# Rationale — composio

> 三段式 rationale 抽取自 `source-design-systems/composio/DESIGN.md`。

## Visual Theme

### decision: nocturnal command center — pitch-black canvas + bioluminescent cyan accents

原 DESIGN.md 段落（verbatim）：
> Composio's interface is a nocturnal command center — a dense, developer-focused darkness punctuated by electric cyan and deep cobalt signals. The entire experience is built on an almost-pure-black canvas (`#0f0f0f`) where content floats within barely-visible containment borders, creating the feeling of a high-tech control panel rather than a traditional marketing page. It's a site that whispers authority to developers who live in dark terminals.

- **trade_off**: 营销 light theme（普世可读） ↔ developer-terminal dark（贴身份）
- **intent**: 让 marketing 页面对 developer 像 IDE 一样自然，营销不再是 friction
- **avoid**: 浅色 SaaS marketing canvas / 多色 product showcase / brand 渐变 hero

## Color

### decision: white-opacity borders (4-12%) replace box-shadow as the depth mechanism

原 DESIGN.md 段落（verbatim）：
> - **Border Mist 12** (`rgba(255,255,255,0.12)`): Highest-opacity border treatment — used for prominent card edges and content separators.
> - **Border Mist 10** (`rgba(255,255,255,0.10)`): Standard container borders on dark surfaces.
> - **Border Mist 08** (`rgba(255,255,255,0.08)`): Subtle section dividers and secondary card edges.
> - **Border Mist 06** (`rgba(255,255,255,0.06)`): Near-invisible containment borders for background groupings.
> - **Border Mist 04** (`rgba(255,255,255,0.04)`): The faintest border — used for atmospheric separation only.

- **trade_off**: drop-shadow 层级（Material 标准） ↔ border-opacity 层级（dark-first 自洽）
- **intent**: 在 dark surface 上 drop shadow 不可见，改用 border opacity 五档实现层级语言
- **avoid**: 黑色 box-shadow on dark（不可见）/ 强 colored border / 1px solid 白（太刺眼）

## Typography

### decision: ultra-tight heading line-heights (0.87-1.0) — compression as authority

原 DESIGN.md 段落（verbatim）：
> - **Compression creates authority**: Heading line-heights are drastically tight (0.87-1.0), making large text feel dense and commanding rather than airy and decorative.

- **trade_off**: 标准 1.2-1.4 line-height（轻盈呼吸） ↔ 0.87-1.0（dense authority）
- **intent**: 让 heading 像 IDE 紧密多行注释 — 让密度本身传 credibility
- **avoid**: 1.5+ relaxed heading（marketing 飘） / display 装饰间距 / 玩味字距

## Typography

### decision: dual font — abcDiatype for marketing voice, JetBrains Mono for technical credibility

原 DESIGN.md 段落（verbatim）：
> - **Dual personality**: abcDiatype carries the marketing voice — geometric, precise, friendly. JetBrains Mono carries the technical voice — credible, functional, familiar to developers.

- **trade_off**: 单一字族（语义统一） ↔ 双字族（dual voice 切换）
- **intent**: 让 mono 不是装饰而是 credibility signal — code 出现 = 真的能跑
- **avoid**: 装饰 mono / 代码用 sans / 单字族 marketing 通用感

## Components

### decision: hard-offset brutalist shadow (4px 4px 0px) on select cards — raw retro-computing edge

原 DESIGN.md 段落（verbatim）：
> Composio uses shadows sparingly and with deliberate contrast. The hard-offset brutalist shadow is the signature — it breaks the sleek darkness with a raw, almost retro-computing feel.

- **trade_off**: 全 sleek（一致 modern） ↔ 选择性 brutalist（破打）
- **intent**: 让 dark+cyan 太 polished 时，retro-computing shadow 撕一道边
- **avoid**: 软 diffuse shadow on signature cards / 多卡片都加 hard shadow（失去节制）/ 普通 SaaS 圆角投影
