# Rationale — coinbase

> 三段式 rationale 抽取自 `source-design-systems/coinbase/DESIGN.md`。

## Color

### decision: Coinbase Blue (#0052ff) as singular brand accent on white binary palette

原 DESIGN.md 段落（auto-backfill）：
> **Blue Bordered**
> - Border: `1px solid #0052ff`
> - Background: transparent
- **trade_off**: 多色 fintech（活泼） ↔ 单一 deep blue（金融可信赖）
- **intent**: 让金融可靠感通过 blue+white 二元色码传递
- **avoid**: 多色 brand 系统 / 紫色 crypto vibe / 暖色装饰

### decision: alternating white sections + dark (#0a0b0d, #282b31) feature sections

原 DESIGN.md 段落（auto-backfill）：
> The button system uses a distinctive 56px radius for pill-shaped CTAs with hover transitions to a lighter blue (`#578bfa`). The design alternates between white content sections and dark (`#0a0b0d`, `#282b31`) feature sections, creating a professional, financial-grade interface.
- **trade_off**: 单一 light/dark（一致） ↔ 交替 sections（视觉节奏）
- **intent**: light 主导信息密度，dark 强调 feature highlight
- **avoid**: 全 dark 沉闷 / 全 light 平淡

## Typography

### decision: four-font proprietary family (Display/Sans/Text/Icons)

原 DESIGN.md 段落（auto-backfill）：
> > Category: Fintech & Crypto
> > Crypto exchange. Clean blue identity, trust-focused, institutional feel.
- **trade_off**: 单字体（普适） ↔ 四 proprietary（brand authority）
- **intent**: 让字体本身成为 fintech trust marker（vs 通用 system fonts）
- **avoid**: 通用 sans / 单一字体扁平表达

### decision: 80px display hero + 1.00 line-height (tight)

原 DESIGN.md 段落（auto-backfill）：
> Coinbase's website is a clean, trustworthy crypto platform that communicates financial reliability through a blue-and-white binary palette. The design uses Coinbase Blue (`#0052ff`) — a deep, saturated blue — as the singular brand accent against white and near-black surfaces. The proprietary font family includes CoinbaseDisplay for hero headlines, CoinbaseSans for UI text, CoinbaseText for body reading, and CoinbaseIcons for iconography — a comprehensive four-font system.
- **trade_off**: 标准 display（保守） ↔ 80px + 1.0 lh（最大冲击）
- **intent**: hero 字号是品牌 statement
- **avoid**: 中等 display / 1.2+ lh 散漫

## Components

### decision: 56px radius pill CTA buttons with blue hover transition

原 DESIGN.md 段落（auto-backfill）：
> **Key Characteristics:**
> - Coinbase Blue (`#0052ff`) as singular brand accent
> - Four-font proprietary family: Display, Sans, Text, Icons
> - 56px radius pill buttons with blue hover transition
> - Near-black (`#0a0b0d`) dark sections + white light sections
> - 1.00 line-height on display headings — ultra-tight
> - Cool gray secondary surface (`#eef0f3`) with blue tint
> - `text-transform: lowercase` on some button labels — unusual
- **trade_off**: 标准 8/12 radius（普适） ↔ 56px pill（fintech confidence）
- **intent**: pill 让 CTA 像 token / coin —— crypto 视觉隐喻
- **avoid**: sharp button / 中等圆角的中庸
