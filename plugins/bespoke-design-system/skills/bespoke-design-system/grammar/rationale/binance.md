# Rationale — binance

> 三段式 rationale 抽取自 `source-design-systems/binance/DESIGN.md`。

## Visual Theme

### decision: digital trading floor — two-tone composition (white surfaces + #222126 dark panels) + Binance Yellow gold ingot

原 DESIGN.md 段落（auto-backfill）：
> Binance.US radiates the polished urgency of a digital trading floor — a space where money moves and decisions happen in seconds. The design is a two-tone composition that alternates between stark white trading surfaces and deep near-black panels (`#222126`), creating a visual rhythm that mirrors the bull-and-bear duality of crypto markets. Binance Yellow (`#F0B90B`) cuts through this monochrome foundation like a gold ingot on a steel desk — unmistakable, confident, and engineered to guide every eye toward the next action.
- **trade_off**: 单一调（一致） ↔ 两调 + gold accent（market-rhythm visual）
- **intent**: 让金融操作感通过视觉节奏传递——bull/bear 二元
- **avoid**: 单调 dashboard / 多色干扰 / 暖色装饰

### decision: golden yellow (#F0B90B) as singular brand — gold ingot on steel desk

原 DESIGN.md 段落（auto-backfill）：
> - **Binance Yellow** (`#F0B90B`): The signature — primary CTA backgrounds, brand accent, active states, link color. The single most important color in the system
> - **Binance Gold** (`#FFD000`): Lighter gold variant used for pill button borders, secondary CTA fills, and golden gradient highlights
> - **Light Gold** (`#F8D12F`): Soft gold for gradient endpoints and hover-adjacent states
- **trade_off**: 多色 fintech ↔ singular gold（established finance signal）
- **intent**: gold = warmth + 价值 + crypto-meets-fortune 隐喻
- **avoid**: 装饰性 gold / 多色 brand / saturation 过低无 ingot 感

## Color

### decision: alternating white sections + deep near-black (#222126) feature sections

原 DESIGN.md 段落（auto-backfill）：
> - **Pure White** (`#FFFFFF`): Primary page canvas, card surfaces, light section backgrounds
> - **Snow** (`#F5F5F5`): Subtle surface differentiation, input backgrounds, alternating row fills
> - **Binance Dark** (`#222126`): Dark section backgrounds, footer canvas, "Trusted by millions" panel — a near-black with a faint purple undertone
> - **Dark Card** (`#2B2F36`): Card surfaces within dark sections, elevated dark containers
> - **Ink** (`#1E2026`): Button text on yellow backgrounds, deepest text color on light surfaces
- **trade_off**: 单 surface（一致） ↔ 交替（trading floor 节奏）
- **intent**: 让 section 切换像 trading session — open/close 视觉信号
- **avoid**: 全 dark 沉重 / 全 light 平淡 / >2 surface tones

## Typography

### decision: BinancePlex proprietary across all text levels

原 DESIGN.md 段落（auto-backfill）：
> The interface speaks the language of fintech trust. Custom BinancePlex typography gives every headline and data point a proprietary gravitas, while generous whitespace and restrained decoration keep the focus on numbers, charts, and call-to-action buttons. The design avoids visual complexity in favor of operational clarity — every element exists to either inform or convert. Product screenshots of the mobile trading app dominate the middle sections, presented on floating device mockups against golden gradients, reinforcing that this is a platform you carry with you.
- **trade_off**: 通用 sans（普适） ↔ proprietary（fintech gravitas）
- **intent**: 让字体本身携带 fintech trust marker
- **avoid**: 通用 system fonts / 装饰字体

## Components

### decision: 50px radius pill CTAs that demand attention

原 DESIGN.md 段落（auto-backfill）：
> **Key Characteristics:**
> - Two-tone light/dark section alternation — white surfaces for trust, dark panels for depth
> - Binance Yellow (`#F0B90B`) as the singular accent color driving all primary actions
> - BinancePlex custom typeface providing proprietary brand identity at every text level
> - Pill-shaped CTA buttons (50px radius) that demand attention
> - Floating device mockups on golden gradients for product showcasing
> - Crypto price tickers with real-time data prominently displayed
> - Shadow-light elevation with subtle 5% opacity card shadows
- **trade_off**: 标准 button radius（普适） ↔ 50px pill（gold token 隐喻）
- **intent**: pill CTA 像 token / coin —— 与 crypto 视觉同源
- **avoid**: sharp button / 中等 radius
