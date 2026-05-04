# Rationale — framer

> 三段式 rationale 抽取自 `source-design-systems/framer/DESIGN.md`。

## Visual Theme

### decision: pure black void canvas — designer's nightclub, zero warmth

原 DESIGN.md 段落（verbatim）：
> Framer's website is a cinematic, tool-obsessed dark canvas that radiates the confidence of a design tool built by designers who worship craft. The entire experience is drenched in pure black — not a warm charcoal or a cozy dark gray, but an absolute void (`#000000`) that makes every element, every screenshot, every typographic flourish feel like it's floating in deep space.

- **trade_off**: warm dark cozy（comfortable）↔ absolute void（floating in deep space）
- **intent**: 让 product screenshot 像在深空漂浮，每个 flourish 都被 void 衬出来
- **avoid**: `#1a1a1a` 暖黑 / `#2d2d2d` 中灰 / 棕调黑 / 任何 cozy dark gray

## Typography

### decision: GT Walsheim with extreme negative letter-spacing (-5.5px at 110px) — compression as personality

原 DESIGN.md 段落（verbatim）：
> - **Compression as personality**: GT Walsheim's extreme negative letter-spacing (-5.5px at 110px) is the defining typographic gesture — headlines feel spring-loaded, urgent, almost breathless

- **trade_off**: 标准字距（呼吸） ↔ -5.5px 极端 compression（spring-loaded urgency）
- **intent**: 让 headline 像被压缩的弹簧 — 紧迫感来自字母互相挤靠
- **avoid**: 0 letter-spacing 默认 / 正 tracking display / -1px 微调（不够极端）

## Color

### decision: Framer Blue (#0099ff) as sole accent — links, borders, ring shadows only

原 DESIGN.md 段落（verbatim）：
> Framer Blue (`#0099ff`) is deployed sparingly but decisively — as link color, border accents, and subtle ring shadows — creating a cold, electric throughline against the warm-less black.

- **trade_off**: 多 accent 色丰富 ↔ 单一 accent 严格 throughline
- **intent**: 让 cold electric blue 成为唯一的 chromatic 信号 — 见 blue = 可点
- **avoid**: 紫 / 绿 / 渐变 accent / blue 用于装饰背景 / blue 文字非链接

## Components

### decision: pill buttons (40px-100px radius) — never sharp, never slightly-rounded

原 DESIGN.md 段落（verbatim）：
> ### Don't
> - Use warm dark backgrounds (no `#1a1a1a`, `#2d2d2d`, or brownish blacks)
> - Apply bold (700+) weight to GT Walsheim display text — medium 500 only
> - Introduce additional accent colors beyond Framer Blue — this is a one-accent-color system
> - Use large border-radius on non-interactive elements (cards use 10px–15px, only buttons get 40px+)

- **trade_off**: 卡片 12-15px 中等 radius（chrome 一致） ↔ button 40-100px pill（强对比）
- **intent**: 让 button 形态在 chrome 中"突出但不刺眼"——pill 是友好但极端的形状选择
- **avoid**: 8px squared-rounded button / 12-20px button radius（与 card 重叠失辨）

## Components

### decision: frosted glass pill (rgba(255,255,255,0.1)) on dark — glass without heavy blur

原 DESIGN.md 段落（verbatim）：
> - **Frosted Pill**: `rgba(255, 255, 255, 0.1)` background, black text (`#000000`), pill shape (40px radius). The glass-effect button that lives on dark surfaces — translucent, ambient, subtle

- **trade_off**: 实色 button（清晰） ↔ frosted translucent（环境融入）
- **intent**: 让 secondary button 在 void canvas 上"半在场"——既存在又不抢戏
- **avoid**: backdrop-filter blur 重 glassmorphism / 30%+ opacity（太显眼）/ 5%- opacity（消失）

## Depth

### decision: blue-tinted ring shadow (rgba(0,153,255,0.15)) replaces traditional border

原 DESIGN.md 段落（verbatim）：
> - **Blue-tinted ring shadows** at very low opacity (0.15) for containment — a signature move that subtly brands every bordered element

- **trade_off**: 1px solid 灰 border（中性） ↔ blue ring shadow（每条边都打 brand 标记）
- **intent**: 让每个 contained element 微弱地"发蓝光"——brand 渗到 chrome 边缘
- **avoid**: 实色 border / 黑色 ring shadow / 高 opacity ring（>0.3 太亮）
