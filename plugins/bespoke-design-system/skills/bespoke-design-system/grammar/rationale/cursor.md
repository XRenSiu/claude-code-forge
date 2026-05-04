# Rationale — cursor

> 三段式 rationale 抽取自 `source-design-systems/cursor/DESIGN.md`。

## Typography

### decision: three-font system — CursorGothic display + jjannon serif body + berkeleyMono code

原 DESIGN.md 段落（auto-backfill）：
> **Code Editor Previews**
> - Dark code editor screenshots with warm cream border frame
> - berkeleyMono for code text
> - Syntax highlighting using timeline colors
- **trade_off**: 单一字体系统（一致性） ↔ 三字体（编辑器三种声音：display 工程感、body 文学感、mono 编码感）
- **intent**: 字体本身就是 Cursor "code editor + literary thought" 双重定位的视觉化
- **avoid**: 通用 sans / Inter slop / 单字体系统的扁平表达

### decision: aggressive negative letter-spacing at display (-2.16px@72px → relaxed at body)

原 DESIGN.md 段落（auto-backfill）：
> > Category: Developer Tools
> > AI-first code editor. Sleek dark interface, gradient accents.
- **trade_off**: 标准 tracking（中性） ↔ 极端紧字距（compressed engineered feel）
- **intent**: 让 display 有 minified-engineered 质感
- **avoid**: 广告体松字距 / body sizes 上沿用 display tracking

## Color

### decision: warm near-black #26251e + accent orange #f54e00

原 DESIGN.md 段落（auto-backfill）：
> **Light Surface**
> - Background: `#f7f7f4` (Surface 100) or `#f2f1ed` (Surface 200)
> - Text: `#26251e` or `oklab(0.263 / 0.9)` (90%)
> - Padding: 0px 8px 1px 12px
> - Use: Dropdown triggers, subtle interactive elements
- **trade_off**: 纯黑（普适） ↔ 暖近黑（warm yellow undertone 文学感）
- **intent**: 与编辑器 dark canvas 同源，但带 warm undertone 让文字有"羊皮纸"温度
- **avoid**: 纯黑塑料感 / 冷蓝 undertone 的工程冷感

### decision: orange (#f54e00) only on CTA / link / brand moments

原 DESIGN.md 段落（auto-backfill）：
> **Pricing Cards**
> - Warm surface backgrounds with bordered containers
> - Feature lists using jjannon serif for readability
> - CTA buttons with accent orange or primary dark styling
- **trade_off**: 多色 ↔ 单 chromatic accent
- **intent**: warm urgent orange 与 warm dark 协同，CTA 像火苗
- **avoid**: orange 装饰用法 / 多 accent 竞争

## Layout

### decision: 8px base + sub-8px micro increments (1.5/2/2.5/3/4/5/6)

原 DESIGN.md 段落（auto-backfill）：
> **Secondary Pill**
> - Background: `#e6e5e0` (Surface 400)
> - Text: `oklab(0.263 / 0.6)` (60% warm brown)
> - Padding: 3px 8px
> - Radius: full pill (33.5M px)
> - Hover: text shifts to `var(--color-error)`
> - Use: Tags, filters, secondary actions
- **trade_off**: 纯 8 grid（粗糙） ↔ 8 + sub-8（光学微调）
- **intent**: 在 8 grid 大节奏内允许像素级精度
- **avoid**: 纯整数 8 倍数的僵硬

### decision: pill-shaped elements with 33.5M px radius (full-pill)

原 DESIGN.md 段落（auto-backfill）：
> **Primary (Warm Surface)**
> - Background: `#ebeae5` (Surface 300)
> - Text: `#26251e` (Cursor Dark)
> - Padding: 10px 12px 10px 14px
> - Radius: 8px
> - Outline: none
> - Hover: text shifts to `var(--color-error)` (`#cf2d56`)
> - Focus shadow: `rgba(0,0,0,0.1) 0px 4px 12px`
> - Use: Primary actions, main CTAs
- **trade_off**: 标准 pill（普适） ↔ extreme pill（visual confidence）
- **intent**: 让 pill 极端化作为 brand signature
- **avoid**: 中等圆角的优柔
