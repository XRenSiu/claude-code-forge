# Rationale — shopify

> 三段式 rationale 抽取自 `source-design-systems/shopify/DESIGN.md`。

## Visual Theme

### decision: dark-first digital theatre — near-black canvas with deep forest green undertone

原 DESIGN.md 段落（auto-backfill）：
> Shopify.com is a dark-first digital theatre — a website that stages its commerce platform like a cinematic premiere. The entire experience unfolds against an abyss of near-black surfaces that carry the faintest whisper of deep forest green (`#02090A`, `#061A1C`, `#102620`), creating a nocturnal atmosphere that feels less like a SaaS marketing page and more like an exclusive product reveal at a tech keynote. This darkness isn't cold or corporate — it's the warm, enveloping dark of a luxury experience, like sitting in the front row of a darkened auditorium.
- **trade_off**: 标准 dark theme（普适） ↔ "luxury auditorium" dark（warm enveloping）
- **intent**: 让 commerce platform 像 product reveal at tech keynote
- **avoid**: 冷蓝 dark / 临床 dark / 普通 SaaS dark

## Color

### decision: 4-tier dark canvas with green undertone (#02090A → #061A1C → #102620)

原 DESIGN.md 段落（auto-backfill）：
> - **Void** (`#000000`): Root page background — true black for maximum depth
> - **Deep Teal** (`#02090A`): Card surfaces, content containers — near-black with green undertone
> - **Dark Forest** (`#061A1C`): Section backgrounds with visible green character
> - **Forest** (`#102620`): Elevated dark surfaces, header backgrounds — the warmest dark shade
> - **Dark Card Border** (`#1E2C31`): Card borders on dark surfaces, subtle boundary definition
- **trade_off**: 单 dark canvas（一致） ↔ green-tinted 4-tier（warm enveloping depth）
- **intent**: dark canvas 不冷不黑，是 "nocturnal forest" — warm + organic
- **avoid**: 纯黑 / 蓝 dark / linear cool dark

### decision: Neon Green (#36F4A4) only on focus rings + interactive highlights

原 DESIGN.md 段落（auto-backfill）：
> Color is used with extreme restraint. The primary accent is Shopify Neon Green (`#36F4A4`) — an electric mint that appears exclusively on focus rings and accent highlights, pulsing like a bioluminescent signal against the dark canvas. Softer green tints (Aloe `#C1FBD4`, Pistachio `#D4F9E0`) provide atmospheric washes. White is the only text color that matters on dark surfaces, while a zinc-based neutral scale (`#A1A1AA` through `#3F3F46`) handles the hierarchy of quiet information. The result is a design that makes commerce technology feel like it belongs in a science-fiction future.
- **trade_off**: 装饰 green（活泼） ↔ neon 仅 focus（bioluminescent signal）
- **intent**: 让 neon green 像 bioluminescent signal — 仅交互瞬间出现
- **avoid**: 装饰 neon / 多 chromatic / 静态 neon link

## Typography

### decision: NeueHaasGrotesk weight 330 (impossibly light) at 96px display — etched in light

原 DESIGN.md 段落（auto-backfill）：
> **Body:** Inter-Variable
> - Fallbacks: Helvetica, Arial, sans-serif
> - OpenType features: `ss03`
> - Available weights: 400, 420, 450, 500, 550 (variable)
> - Used for body text, links, buttons, UI elements
- **trade_off**: 标准 weight 400+（可读） ↔ 330 ultralight 96px（ethereal presence）
- **intent**: 让 headline 像 "etched in light, not printed in ink"
- **avoid**: 普通 weight 400 + 中等 size / 装饰 serif / 重 weight

### decision: variable weights at unusual stops (420, 450, 550) — precision signal

原 DESIGN.md 段落（auto-backfill）：
> **Display:** NeueHaasGrotesk (refined Helvetica descendant, variable font)
> - Fallbacks: Helvetica, Arial, sans-serif
> - OpenType features: `ss03` (stylistic set 3 — distinctive letterform alternates)
> - Available weights: 330, 360, 400, 500, 750 (variable)
> - Used for all headings, hero text, and large display elements
- **trade_off**: 标准 weight stops (400/500/600) ↔ 在 stop 之间（detail signal）
- **intent**: 让 typography precision 暗示 "company that sweats every detail"
- **avoid**: 标准 weight stops / 装饰 weight 跳跃

## Components

### decision: 9999px full-pill buttons + ss03 OpenType feature for distinctive letterforms

原 DESIGN.md 段落（auto-backfill）：
> **Key Characteristics:**
> - Dark-first design with deep forest-teal undertones (not pure black)
> - Ultra-light display typography (weight 330) at monumental scale (96px) creating an ethereal presence
> - Neon Green (`#36F4A4`) as the singular high-energy accent against darkness
> - Full-pill buttons (9999px radius) as the primary interactive shape
> - Layered, multi-stage box shadows creating photographic depth
> - Product screenshots embedded in dark UI contexts, matching the surrounding darkness
> - Zinc-based neutral scale for text hierarchy — balanced between warm and cool
- **trade_off**: 标准 button radius（普适） ↔ 9999 full-pill（bioluminescent shape match）
- **intent**: pill button 与 neon green 同源 — 都是 organic biolumine 形态
- **avoid**: 直角 / 中等 radius / 装饰 corner
