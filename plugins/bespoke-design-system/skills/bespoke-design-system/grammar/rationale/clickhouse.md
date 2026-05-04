# Rationale — clickhouse

> 三段式 rationale 抽取自 `source-design-systems/clickhouse/DESIGN.md`。

## Visual Theme

### decision: high-performance cockpit — neon yellow-green (#faff69) on obsidian black (#000)

原 DESIGN.md 段落（auto-backfill）：
> > Category: Backend & Data
> > Fast analytics database. Yellow-accented, technical documentation style.
- **trade_off**: 普通 dark theme（mainstream） ↔ 极端 neon-on-black（speed signal）
- **intent**: 让"速度"在视觉上不读字就能感知——颜色对比即性能宣告
- **avoid**: 中等对比 / 冷蓝 dev tool / 装饰性 chromatic

## Color

### decision: pure black canvas (#000000) — terminal-grade

原 DESIGN.md 段落（auto-backfill）：
> What makes ClickHouse distinctive is the electrifying tension between the near-black canvas and the neon yellow-green accent. This color combination (`#faff69` on `#000000`) creates one of the highest-contrast pairings in any tech brand, making every CTA button, every highlighted card, and every accent border impossible to miss. Supporting this is a forest green (`#166534`) for secondary CTAs that adds depth to the action hierarchy without competing with the neon.
- **trade_off**: near-black 暖底（温度） ↔ 纯黑（terminal authority）
- **intent**: 与 console / terminal 同源，让产品像"数据库 raw 视图"
- **avoid**: 暖近黑 / 冷紫蓝 / 中等 dark canvas

### decision: neon volt as sole chromatic accent (CTA / border / highlight only)

原 DESIGN.md 段落（auto-backfill）：
> ClickHouse's interface is a high-performance cockpit rendered in acid yellow-green on obsidian black — a design that screams "speed" before you read a single word. The entire experience lives in darkness: pure black backgrounds (`#000000`) with dark charcoal cards (`#414141` borders) creating a terminal-grade aesthetic where the only chromatic interruption is the signature neon yellow-green (`#faff69`) that slashes across CTAs, borders, and highlighted moments like a highlighter pen on a dark console.
- **trade_off**: 多色信号（明确） ↔ 单 neon（visual intensity）
- **intent**: 让 neon 出现时携带最大注意权重
- **avoid**: 多 chromatic / 装饰 neon / 低对比 neon

## Typography

### decision: Inter at weight 900 (Black) for display hero up to 96px

原 DESIGN.md 段落（auto-backfill）：
> The typography is aggressively heavy — Inter at weight 900 (Black) for the hero headline at 96px creates text blocks that feel like they have physical mass. This "database for AI" site communicates raw power through visual weight: thick type, high-contrast neon accents, and performance stats displayed as oversized numbers. There's nothing subtle about ClickHouse's design, and that's entirely the point — it mirrors the product's promise of extreme speed and performance.
- **trade_off**: 中等 weight（普适） ↔ 900 black（physical mass）
- **intent**: 让 typography 像 "性能" 宣告——physical, almost architectural presence
- **avoid**: 600/700 中等 weight / 装饰 serif / 软字体

### decision: uppercase labels with wide tracking (1.4px) for navigation

原 DESIGN.md 段落（auto-backfill）：
> **Neon Primary**
> - Background: Neon Volt (`#faff69`)
> - Text: Near Black (`#151515`)
> - Padding: 0px 16px
> - Radius: sharp (4px)
> - Border: `1px solid #faff69`
> - Hover: background shifts to dark (`rgb(29, 29, 29)`), text stays
> - Active: text shifts to Pale Yellow (`#f4f692`)
> - The eye-catching CTA — neon on black
- **trade_off**: 小写小字（普适） ↔ uppercase + wide tracking（technical authority）
- **intent**: nav label 像 "system flag" 出现，不像 marketing 链接
- **avoid**: 小写 nav / 紧字距 / 装饰 nav style
