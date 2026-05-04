# Rationale — pinterest

> 三段式 rationale 抽取自 `source-design-systems/pinterest/DESIGN.md`。

## Visual Theme

### decision: warm inspiration-driven canvas — slightly warm white + craft-like neutral undertone

原 DESIGN.md 段落（auto-backfill）：
> **Secondary Sand**
> - Background: `#e5e5e0` (warm sand gray)
> - Text: `#000000`
> - Padding: 6px 14px
> - Radius: 16px
> - Focus: same semantic border system
- **trade_off**: 冷蓝 tech 平台调（mainstream） ↔ 暖白 + olive/sand 中性（lifestyle magazine）
- **intent**: 让浏览像 craft / lifestyle 翻杂志，不像 corporate tech
- **avoid**: 冷蓝 platform 感 / 临床 white / 多色 brand

## Color

### decision: Pinterest Red (#e60023) — singular bold accent, never subtle, always confident

原 DESIGN.md 段落（auto-backfill）：
> **Primary Red**
> - Background: `#e60023` (Pinterest Red)
> - Text: `#000000` (black — unusual choice for contrast on red)
> - Padding: 6px 14px
> - Radius: 16px (generously rounded, not pill)
> - Border: `2px solid rgba(255, 255, 255, 0)` (transparent)
> - Focus: semantic border + outline via CSS variables
- **trade_off**: 中等饱和 brand（克制） ↔ 高饱和 red（confident statement）
- **intent**: red 是 brand statement，不是装饰也不是状态色
- **avoid**: 弱化 red / 多色 brand / 装饰性 red

### decision: warm-tinted neutral scale — olive/sand grays (#91918c, #62625b, #e5e5e0) not cool steel

原 DESIGN.md 段落（auto-backfill）：
> Pinterest's website is a warm, inspiration-driven canvas that treats visual discovery like a lifestyle magazine. The design operates on a soft, slightly warm white background with Pinterest Red (`#e60023`) as the singular, bold brand accent. Unlike the cool blues of most tech platforms, Pinterest's neutral scale has a distinctly warm undertone — grays lean toward olive/sand (`#91918c`, `#62625b`, `#e5e5e0`) rather than cool steel, creating a cozy, craft-like atmosphere that invites browsing.
- **trade_off**: 冷灰（普适 tech） ↔ 暖灰（lifestyle / craft）
- **intent**: 让 UI background / surface 像 paper / fabric 自然材料
- **avoid**: 冷蓝灰 / 纯灰 / 装饰多色

### decision: plum-tinted near-black text (#211922) — warm with hint of plum

原 DESIGN.md 段落（auto-backfill）：
> **Circular Action**
> - Background: `#e0e0d9` (warm light)
> - Text: `#211922` (plum black)
> - Radius: 50% (circle)
> - Use: Pin actions, navigation controls
- **trade_off**: 纯黑（精度） ↔ 暖近黑 + plum undertone（warm depth）
- **intent**: text 暖暖的不冷
- **avoid**: 纯黑 / 蓝 undertone / 中等灰

## Components

### decision: generous radius scale 12-40px + 50% circles

原 DESIGN.md 段落（auto-backfill）：
> What distinguishes Pinterest is its generous border-radius system (12px–40px, plus 50% for circles) and warm-tinted button backgrounds. The secondary button (`#e5e5e0`) has a distinctly warm, sand-like tone rather than cold gray. The primary red button uses 16px radius — rounded but not pill-shaped. Combined with warm badge backgrounds (`hsla(60,20%,98%,.5)` — a subtle yellow-warm wash) and photography-dominant layouts, the result is a design that feels handcrafted and personal, not corporate and sterile.
- **trade_off**: 中等 radius ↔ 大 radius（friendly + handcrafted）
- **intent**: 让 chrome 像 hand-cut / handcrafted feel
- **avoid**: 直角 / 中等 8-12 中庸 / 装饰 corner

### decision: 3-tier design token architecture (--comp-* / --sema-* / --base-*)

原 DESIGN.md 段落（auto-backfill）：
> The typography uses Pin Sans — a custom proprietary font with a broad fallback stack including Japanese fonts, reflecting Pinterest's global reach. At display scale (70px, weight 600), Pin Sans creates large, inviting headlines. At smaller sizes, the system is compact: buttons at 12px, captions at 12–14px. The CSS variable naming system (`--comp-*`, `--sema-*`, `--base-*`) reveals a sophisticated three-tier design token architecture: component-level, semantic-level, and base-level tokens.
- **trade_off**: 单层 token（简单） ↔ 3-tier（component / semantic / base 分工）
- **intent**: 让 token 系统支持大型多产品 design 系统的可演化性
- **avoid**: 硬编码值 / 单层 token 不可扩展
