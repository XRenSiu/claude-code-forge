# Rationale — bmw

> 三段式 rationale 抽取自 `source-design-systems/bmw/DESIGN.md`。

## Typography

### decision: BMWTypeNextLatin Light (300) for 60px uppercase display headings — whispered authority
- **trade_off**: 重 weight 显式（强调） ↔ light weight 低声（authority through restraint）
- **intent**: 让 hero 像精密机械低吟，不靠 weight 砸读者
- **avoid**: 700+ display / 装饰 serif / 中等 weight 的中庸

### decision: weight 300 display + weight 900 navigation — extreme weight contrast
- **trade_off**: 单一 weight ladder（一致） ↔ 极端 300 vs 900 对比（typographic drama）
- **intent**: display 低声 + navigation 高声 = brand voice tension
- **avoid**: 中等 weight ladder / 单一 weight flatness

### decision: single font family BMWTypeNextLatin from 60px display to 16px body
- **trade_off**: 多字体（声音分工） ↔ 单字体（unity through one typeface）
- **intent**: 让一种字体在不同 size + weight 下表达全部 hierarchy
- **avoid**: 多字体复杂度 / serif/sans 混排

## Color & Layout

### decision: zero border-radius — angular, sharp-cornered industrial geometry
- **trade_off**: 圆角 friendliness ↔ 直角 industrial geometry
- **intent**: 让 chrome 像精密机械——angular precision 是 BMW DNA
- **avoid**: 大圆角 friendly / sub-8 indecision / pill 装饰

### decision: signature blue (#1c69d4) used sparingly — interactive only, never decoratively
- **trade_off**: 装饰 blue（活泼） ↔ interactive-only blue（克制权威）
- **intent**: 让 blue 像 instrument cluster 高亮——出现即交互
- **avoid**: 装饰 blue / 多色 brand / 低饱和 blue

### decision: CSS variable-driven theming (`--site-context-*`) for multi-brand deployment
- **trade_off**: hardcoded color（简单） ↔ context variables（multi-brand 灵活）
- **intent**: 让设计系统适应 BMW Group 多品牌（BMW / Mini / Rolls-Royce）部署
- **avoid**: 硬编码 brand 色 / 每品牌独立设计系统
