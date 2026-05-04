# Rationale — nike

> 三段式 rationale 抽取自 `source-design-systems/nike/DESIGN.md`。

## Visual Theme

### decision: aggressively monochromatic UI — color from product photography only

原 DESIGN.md 段落（auto-backfill）：
> When refining existing screens generated with this design system:
> 1. Focus on ONE component at a time
> 2. Reference specific color names and hex codes from this document
> 3. Remember: product photography is the color — UI stays monochromatic
> 4. Use the grey scale for state changes: #F5F5F5 → #E5E5E5 → #CACACB → #707072
> 5. If something feels too colorful in the UI, it probably is — Nike keeps UI greyscale
> 6. Display type (Nike Futura) should ALWAYS be uppercase and never below 24px
> 7. Body type (Helvetica Now) should almost always be weight 500 for interactive elements
- **trade_off**: 多色 brand（消费者品牌活泼） ↔ 黑白 UI（让 product 是色彩源）
- **intent**: 让 athlete photography / sneaker imagery 是唯一情感色彩
- **avoid**: 装饰性 brand 色 / 多色 UI 抢镜 / 与产品色竞争

## Color

### decision: Nike Black (#111111) — fractionally softer than pure #000

原 DESIGN.md 段落（auto-backfill）：
> - **Nike Black** (`#111111`): The foundation — primary text, button backgrounds, nav text, hero overlays. Deliberately not pure black (#000000), creating a fractionally softer reading experience
> - **Nike White** (`#FFFFFF`): Primary page canvas, button text on dark, card surfaces, nav bar background
- **trade_off**: 纯黑（最大对比） ↔ 略软近黑（reading experience softer）
- **intent**: text 阅读舒适且仍有 Nike 锐气
- **avoid**: 纯黑 / 暖近黑 / 中等灰

### decision: functional color only (Red / Blue / Green / Orange) — never decorative

原 DESIGN.md 段落（auto-backfill）：
> - **Red**: `#FFE5E5` → `#EE0005` → `#530300`
> - **Orange**: `#FFE2D6` → `#FF5000` → `#3E1009`
> - **Yellow**: `#FEF087` → `#FCA600` → `#99470A`
> - **Green**: `#DFFFB9` → `#1EAA52` → `#003C2A`
> - **Teal**: `#D4FFFB` → `#008E98` → `#043441`
> - **Blue**: `#D6EEFF` → `#1151FF` → `#020664`
> - **Purple**: `#E4E1FC` → `#6E0FF6` → `#1C0060`
> - **Pink**: `#FFE1F3` → `#ED1AA0` → `#4C012D`
- **trade_off**: brand 多色（活泼） ↔ semantic-only chromatic（克制）
- **intent**: red = 错误 / sale；blue = 链接；green = 成功；orange = badge——颜色即语义
- **avoid**: 装饰性 brand 色 / 颜色作 hierarchy / 多色 UI

## Typography

### decision: Nike Futura ND with line-height 0.90 — typographic shockwave on hero

原 DESIGN.md 段落（auto-backfill）：
> **Display:** Nike Futura ND (custom condensed Futura variant exclusive to Nike)
> - Fallbacks: Helvetica Now Text Medium, Helvetica, Arial
> - Used exclusively for large uppercase display headlines
> - Characteristically tight line-height (0.90) and uppercase transform
- **trade_off**: 标准 lh 1.0+（呼吸） ↔ 0.90 极紧（impossibly tight, 击穿 imagery）
- **intent**: 让 display headline 像视觉拳击——不是文字，是 statement
- **avoid**: 标准 lh / 装饰 serif / 中等 weight 散漫

### decision: split typography — Nike Futura ND display + Helvetica Now body

原 DESIGN.md 段落（auto-backfill）：
> The typography system is the other half of Nike's visual identity. Massive uppercase headlines in Nike Futura ND — a custom condensed Futura variant with impossibly tight line-height (0.90) — punch through hero imagery like a typographic shockwave. Below the headlines, the workhorse Helvetica Now family handles everything from navigation to product descriptions with Swiss-precision clarity. This split between expressive display type and functional body type mirrors Nike's brand duality: inspiration meets execution.
- **trade_off**: 单字体（一致） ↔ split display/body（inspiration vs execution duality）
- **intent**: display = inspiration（aspirational headline），body = execution（functional clarity）
- **avoid**: 单 family flatness / 装饰 display / 通用 system body

## Components

### decision: 30px pill buttons + full-bleed photography (no border radius on imagery)

原 DESIGN.md 段落（auto-backfill）：
> > Category: E-Commerce & Retail
> > Athletic retail. Monochrome UI, massive uppercase type, full-bleed photography.
- **trade_off**: 中等 radius（普适） ↔ pill + 0 imagery radius（duality of softness vs edge）
- **intent**: button 友好但 imagery 紧贴边缘 = action + raw energy
- **avoid**: 软化 imagery / 直角 button / 装饰 frame
