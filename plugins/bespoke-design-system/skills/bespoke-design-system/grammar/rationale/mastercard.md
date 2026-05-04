# Rationale — mastercard

> 三段式 rationale 抽取自 `source-design-systems/mastercard/DESIGN.md`。

## Visual Theme

### decision: warm putty-cream canvas + extreme radii (40/99/1000) — annual report meets brand magazine

原 DESIGN.md 段落（verbatim）：
> Mastercard's experience reads like a warm, editorial magazine built from soft stone and signal orange. The canvas is a muted putty-cream (`#F3F0EE`) — not white, not gray, but a color that feels like the paper of a premium annual report. On top of that canvas, everything that matters is shaped like a stadium, a pill, or a perfect circle. The dominant visual gesture is the **oversized radius**: heroes carry 40-point corners, cards go fully pill-shaped, service images are cropped into circular orbits, and buttons either complete the pill or fit snugly at 20 points. There are almost no sharp corners anywhere on the page.

- **trade_off**: 普通 fintech 冷蓝感 ↔ 编辑杂志暖纸感（warm putty + 极端 radii）
- **intent**: 让 60-year 老 payments 网络读起来像 modern brand magazine — institutional but editorial
- **avoid**: pure white SaaS canvas / 8-12px 中等 radius / 直角硬朗 fintech 感

## Components

### decision: circular portraits + white satellite CTAs + traced orange orbits — "constellation, not list"

原 DESIGN.md 段落（verbatim）：
> The second gesture is **orbit and trajectory**. Circular image masks don't sit still — they're connected by thin, hand-drawn-feeling orange arcs that span entire viewport widths, implying a constellation of services rather than a list. Each circle has a small attached "satellite" — a white micro-CTA holding an arrow icon — docked onto its perimeter like a moon. This is the most distinctive thing about Mastercard's current design language: the circles feel like they're in motion even though the page is still.

- **trade_off**: 卡片网格（标准信息架构）↔ 圆形 + orbit 弧线（constellation 隐喻）
- **intent**: 让 service 列表是星座而非清单，service 之间有引力而非顺序
- **avoid**: rectangular service card grid / arrow icons 单独无 satellite 上下文 / 直线 connectors

## Typography

### decision: MarkForMC at weight 450 for body — "softer than 500, firmer than 400"

原 DESIGN.md 段落（verbatim）：
> - **Weight 450 is load-bearing**. Most brands use 400/500/700; Mastercard uses 450 for body copy, which creates an unusually soft reading tone. Replacing it with 400 flattens the identity.

- **trade_off**: 400 标准 body（universal）↔ 450 半步重（柔和但有骨）
- **intent**: 让 body 读起来不平不脆，editorial soft tone 是字重不是字距
- **avoid**: 400 默认 body（缺识别度）/ 500 firm body（过硬）/ 多 weight 跳档

## Color

### decision: Signal Orange (#CF4500) reserved for consent/legal only — never marketing CTA

原 DESIGN.md 段落（verbatim）：
> ### Don't
> - Don't use pure white as a page background — it breaks the warm editorial tone
> - Don't round image frames at 8–16px — Mastercard either uses full-pill, 40px, or full-circle. In-between radii look generic
> - Don't use Signal Orange for marketing CTAs — it reads as cookie-consent orange and dilutes the legal color signal

- **trade_off**: orange 作为活力 brand CTA（吸睛）↔ orange 锁给 consent/legal（合规色信号）
- **intent**: 让 orange = "这是法律相关行动"，不混淆 marketing CTA 与 cookie consent
- **avoid**: orange marketing CTA / orange decorative wash / orange 文字 non-legal context

## Layout

### decision: radius gap rule — small (≤6) / medium-large (20-40) / full-pill (99+), middle absent

原 DESIGN.md 段落（verbatim）：
> The scale is unusual: most systems use 4/8/12/16. Mastercard skips those and commits to **either small (≤6), medium-large (20–40), or full-pill (99+)**. The middle ground of 8–12 is absent, which is why the UI feels either "precise and utility" or "soft and editorial" with no in-between.

- **trade_off**: 4/8/12/16 渐进 SaaS scale（universal）↔ 6/20-40/999 三档间断（双语态）
- **intent**: 让 UI 要么 sharp utility 要么 soft editorial，没有"圆角 SaaS"中间地带
- **avoid**: 8px / 12px / 16px radius any element / 渐进 radius scale / "略微圆角"形态

## Depth

### decision: atmospheric cushioning shadows (48px+ spread, ≤8% opacity) — never directional drop

原 DESIGN.md 段落（verbatim）：
> Mastercard uses shadows as **atmospheric cushioning**, not directional light. The Level 2 shadow has a 48px spread and only 8% opacity — it barely exists as dark pixels but creates a "the card is breathing above the canvas" feel. There are almost no hard-edged, tight shadows anywhere in the system. Border lines are preferred over shadows for functional delineation (form inputs, footer divider).

- **trade_off**: 锐利 directional shadow（标准 elevation）↔ 大 spread 低 opacity 大气垫（呼吸感）
- **intent**: 让 elevation 是"卡片在呼吸"而非"卡片有方向光"
- **avoid**: 0-12px spread shadow / >0.1 opacity shadow / 多 layer 复合 shadow
