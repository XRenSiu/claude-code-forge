# Rationale — bmw

> 三段式 rationale 抽取自 `source-design-systems/bmw/DESIGN.md`。

## Typography

### decision: BMWTypeNextLatin Light (300) for 60px uppercase display headings — whispered authority

原 DESIGN.md 段落（auto-backfill）：
> **Shadow Philosophy**: BMW uses virtually no shadows. Depth is created entirely through the contrast between dark photographic sections and white content sections — the automotive lighting does the elevation work.
- **trade_off**: 重 weight 显式（强调） ↔ light weight 低声（authority through restraint）
- **intent**: 让 hero 像精密机械低吟，不靠 weight 砸读者
- **avoid**: 700+ display / 装饰 serif / 中等 weight 的中庸

### decision: weight 300 display + weight 900 navigation — extreme weight contrast

原 DESIGN.md 段落（auto-backfill）：
> **Key Characteristics:**
> - BMWTypeNextLatin Light (weight 300) uppercase for display — whispered authority
> - BMW Blue (`#1c69d4`) as singular accent — used only for interactive elements
> - Zero border-radius detected — angular, sharp-cornered, industrial geometry
> - Dark hero photography + white content sections — showroom lighting rhythm
> - CSS variable-driven theming: `--site-context-*` tokens for brand flexibility
> - Weight 900 for navigation emphasis — extreme contrast with 300 display
> - Tight line-heights (1.15–1.30) throughout — compressed, efficient, German engineering
> - Full-bleed automotive photography as primary visual content
- **trade_off**: 单一 weight ladder（一致） ↔ 极端 300 vs 900 对比（typographic drama）
- **intent**: display 低声 + navigation 高声 = brand voice tension
- **avoid**: 中等 weight ladder / 单一 weight flatness

### decision: single font family BMWTypeNextLatin from 60px display to 16px body

原 DESIGN.md 段落（auto-backfill）：
> The typography is built on BMWTypeNextLatin — a proprietary typeface in two variants: BMWTypeNextLatin Light (weight 300) for massive uppercase display headings, and BMWTypeNextLatin Regular for body and UI text. The 60px uppercase headline at weight 300 is the defining typographic gesture — light-weight type that whispers authority rather than shouting it. The fallback stack includes Helvetica and Japanese fonts (Hiragino, Meiryo), reflecting BMW's global presence.
- **trade_off**: 多字体（声音分工） ↔ 单字体（unity through one typeface）
- **intent**: 让一种字体在不同 size + weight 下表达全部 hierarchy
- **avoid**: 多字体复杂度 / serif/sans 混排

## Color & Layout

### decision: zero border-radius — angular, sharp-cornered industrial geometry

原 DESIGN.md 段落（auto-backfill）：
> BMW's website is automotive engineering made visual — a design system that communicates precision, performance, and German industrial confidence. The page alternates between deep dark hero sections (featuring full-bleed automotive photography) and clean white content areas, creating a cinematic rhythm reminiscent of a luxury car showroom where vehicles are lit against darkness. The BMW CI2020 design language (their corporate identity refresh) defines every element.
- **trade_off**: 圆角 friendliness ↔ 直角 industrial geometry
- **intent**: 让 chrome 像精密机械——angular precision 是 BMW DNA
- **avoid**: 大圆角 friendly / sub-8 indecision / pill 装饰

### decision: signature blue (#1c69d4) used sparingly — interactive only, never decoratively

原 DESIGN.md 段落（auto-backfill）：
> > Category: Automotive
> > Luxury automotive. Dark premium surfaces, precise German engineering aesthetic.
- **trade_off**: 装饰 blue（活泼） ↔ interactive-only blue（克制权威）
- **intent**: 让 blue 像 instrument cluster 高亮——出现即交互
- **avoid**: 装饰 blue / 多色 brand / 低饱和 blue

### decision: CSS variable-driven theming (`--site-context-*`) for multi-brand deployment

原 DESIGN.md 段落（auto-backfill）：
> What makes BMW distinctive is its CSS variable-driven theming system. Context-aware variables (`--site-context-highlight-color: #1c69d4`, `--site-context-focus-color: #0653b6`, `--site-context-metainfo-color: #757575`) suggest a design system built for multi-brand, multi-context deployment where colors can be swapped globally. The blue highlight color (`#1c69d4`) is BMW's signature blue — used sparingly for interactive elements and focus states, never decoratively. Zero border-radius was detected — BMW's design is angular, sharp-cornered, and uncompromisingly geometric.
- **trade_off**: hardcoded color（简单） ↔ context variables（multi-brand 灵活）
- **intent**: 让设计系统适应 BMW Group 多品牌（BMW / Mini / Rolls-Royce）部署
- **avoid**: 硬编码 brand 色 / 每品牌独立设计系统
