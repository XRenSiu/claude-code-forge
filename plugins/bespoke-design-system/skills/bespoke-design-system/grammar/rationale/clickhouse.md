# Rationale — clickhouse

> 三段式 rationale 抽取自 `source-design-systems/clickhouse/DESIGN.md`。

## Visual Theme

### decision: high-performance cockpit — neon yellow-green (#faff69) on obsidian black (#000)
- **trade_off**: 普通 dark theme（mainstream） ↔ 极端 neon-on-black（speed signal）
- **intent**: 让"速度"在视觉上不读字就能感知——颜色对比即性能宣告
- **avoid**: 中等对比 / 冷蓝 dev tool / 装饰性 chromatic

## Color

### decision: pure black canvas (#000000) — terminal-grade
- **trade_off**: near-black 暖底（温度） ↔ 纯黑（terminal authority）
- **intent**: 与 console / terminal 同源，让产品像"数据库 raw 视图"
- **avoid**: 暖近黑 / 冷紫蓝 / 中等 dark canvas

### decision: neon volt as sole chromatic accent (CTA / border / highlight only)
- **trade_off**: 多色信号（明确） ↔ 单 neon（visual intensity）
- **intent**: 让 neon 出现时携带最大注意权重
- **avoid**: 多 chromatic / 装饰 neon / 低对比 neon

## Typography

### decision: Inter at weight 900 (Black) for display hero up to 96px
- **trade_off**: 中等 weight（普适） ↔ 900 black（physical mass）
- **intent**: 让 typography 像 "性能" 宣告——physical, almost architectural presence
- **avoid**: 600/700 中等 weight / 装饰 serif / 软字体

### decision: uppercase labels with wide tracking (1.4px) for navigation
- **trade_off**: 小写小字（普适） ↔ uppercase + wide tracking（technical authority）
- **intent**: nav label 像 "system flag" 出现，不像 marketing 链接
- **avoid**: 小写 nav / 紧字距 / 装饰 nav style
