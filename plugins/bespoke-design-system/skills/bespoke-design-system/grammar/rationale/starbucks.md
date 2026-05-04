# Rationale — starbucks

> 三段式 rationale 抽取自 `source-design-systems/starbucks/DESIGN.md`。

## Visual Theme

### decision: warm cream canvas (#f2f0eb / #edebe9) — references café materials not cold white

原 DESIGN.md 段落（auto-backfill）：
> Whitespace carries the feeling of "plenty of space in the café." Section padding leans generous (40–64px). Content blocks are separated by whitespace rather than dividers. The cream canvas (`#f2f0eb`) is itself a visual breath between white cards and green feature bands.
- **trade_off**: 纯白 canvas（普适） ↔ 暖 cream（café material 隐喻）
- **intent**: canvas 让人想起 paper napkins / café walls / wood finishes，与店内体验同源
- **avoid**: 纯白 #fff 临床感 / 冷灰 / 装饰性 cream

## Color

### decision: 4-tier green system (Starbucks / Accent / House / Uplift) each mapped to specific role

原 DESIGN.md 段落（auto-backfill）：
> - Primary CTA: "Green Accent (`#00754A`)"
> - Primary CTA text: "White (`#ffffff`)"
> - Brand heading: "Starbucks Green (`#006241`)"
> - Feature band / footer: "House Green (`#1E3932`)"
> - Page canvas: "Neutral Warm (`#f2f0eb`)"
> - Card canvas: "White (`#ffffff`)"
> - Heading text on light: "Text Black (`rgba(0,0,0,0.87)`)"
> - Body text on light: "Text Black Soft (`rgba(0,0,0,0.58)`)"
> - Body text on dark-green: "Text White Soft (`rgba(255,255,255,0.70)`)"
> - Rewards accent: "Gold (`#cba258`)"
> - Rewards text: "Rewards Green (`#33433d`)"
> - Destructive: "Red (`#c82014`)"
- **trade_off**: 单 brand green（一致） ↔ 4-tier 分工（h1 vs CTA vs footer vs accent）
- **intent**: 让"绿"不是装饰而是结构化品牌系统——每层 green 有特定 surface role
- **avoid**: 单 green 一刀切 / 多色装饰 / 非系统化 chromatic

### decision: gold (#cba258) only on Rewards-status ceremony — never general accent

原 DESIGN.md 段落（auto-backfill）：
> - **Gold** (`#cba258`): Reserved almost exclusively for Rewards-status ceremony — Gold-tier callouts, partnership badges (SkyMiles, Bonvoy), and premium-feeling accents. Never a general-purpose brand color.
> - **Gold Light** (`#dfc49d`): Softer gold for background washes on gold-tier sections.
> - **Gold Lightest** (`#faf6ee`): Cream-gold page-surface wash used under partnership sections on the Rewards page — ties the gold accent back into the warm neutral system.
- **trade_off**: gold 装饰（活泼） ↔ gold 仅 ceremony（克制 + valued）
- **intent**: 让 gold 出现时携带 ceremony 重量——partnership badges / status 成就
- **avoid**: 装饰性 gold / 多 gold 用法稀释 / general-purpose gold

## Components

### decision: 50px full-pill universal buttons + scale(0.95) active press

原 DESIGN.md 段落（auto-backfill）：
> When refining existing screens generated with this design system:
> 1. Focus on ONE component at a time
> 2. Reference specific color names and hex codes from this document
> 3. Use natural language descriptions ("warm cream canvas," "four-tier green system") alongside exact values
> 4. Preserve the 50px pill + `scale(0.95)` active state universally
> 5. Check that greens are mapped to their correct role (Green Accent for CTA, Starbucks Green for heading, House Green for band)
> 6. Don't introduce gradients — the system is color-block
> 7. Keep SoDoSans tracking at `-0.01em` / `-0.16px` across the board
- **trade_off**: 标准 button radius（普适） ↔ pill + 微缩动效（hospitality + tactile）
- **intent**: 让 buttons 像 store signage — friendly, legible, never shouting
- **avoid**: 直角 / 中等 radius / 静态 button

### decision: Frap floating CTA — 56px circle in Green Accent w/ layered shadow

原 DESIGN.md 段落（auto-backfill）：
> **8. Frap — Floating Circular Order Button**
> - Background: `#00754A` (Green Accent)
> - Icon: `#ffffff`
> - Size: `5.6rem / 56px` (standard), `4rem / 40px` (mini variant)
> - Radius: `50%` (full circle)
> - Fixed bottom-right, `-0.8rem` touch offset for extra tap comfort
> - Shadow stack: base `0 0 6px rgba(0,0,0,0.24)` + ambient `0 8px 12px rgba(0,0,0,0.14)`
> - Active state: ambient shadow fades to `0 8px 12px rgba(0,0,0,0)`
> - This is the product's signature elevation element — it floats over every scrolled surface
- **trade_off**: standard CTA placement（一致） ↔ floating circle（signature feature）
- **intent**: 让 ordering experience 有 "iconic move" 视觉记忆点
- **avoid**: hidden CTA / 弱 elevation / 多 floating button 竞争

## Typography

### decision: SoDoSans + serif (Lander Tall) for Rewards + script (Kalam) for Careers

原 DESIGN.md 段落（auto-backfill）：
> - **Primary:** `SoDoSans, "Helvetica Neue", Helvetica, Arial, sans-serif` — Starbucks' proprietary corporate typeface, used across nearly every surface
> - **Loading Fallback:** `"Helvetica Neue", Helvetica, Arial, sans-serif` — what users see before SoDoSans loads
> - **Rewards Serif:** `"Lander Tall", "Iowan Old Style", Georgia, serif` — used on specific Rewards-page headline moments for a warm editorial feel
> - **Careers Script:** `"Kalam", "Comic Sans MS", cursive` — used exclusively for Careers-page "cup name" decorative touches, referencing the hand-written names on Starbucks cups
- **trade_off**: 单 family（一致） ↔ 三 family 分上下文（disciplined surface diversity）
- **intent**: 让字体应 surface 切换——但每种字体只在特定 page 出现
- **avoid**: 多字体随机出现 / family flatness / 装饰 serif 滥用
