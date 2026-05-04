# Rationale — nike

> 三段式 rationale 抽取自 `source-design-systems/nike/DESIGN.md`。

## Visual Theme

### decision: aggressively monochromatic UI — color from product photography only
- **trade_off**: 多色 brand（消费者品牌活泼） ↔ 黑白 UI（让 product 是色彩源）
- **intent**: 让 athlete photography / sneaker imagery 是唯一情感色彩
- **avoid**: 装饰性 brand 色 / 多色 UI 抢镜 / 与产品色竞争

## Color

### decision: Nike Black (#111111) — fractionally softer than pure #000
- **trade_off**: 纯黑（最大对比） ↔ 略软近黑（reading experience softer）
- **intent**: text 阅读舒适且仍有 Nike 锐气
- **avoid**: 纯黑 / 暖近黑 / 中等灰

### decision: functional color only (Red / Blue / Green / Orange) — never decorative
- **trade_off**: brand 多色（活泼） ↔ semantic-only chromatic（克制）
- **intent**: red = 错误 / sale；blue = 链接；green = 成功；orange = badge——颜色即语义
- **avoid**: 装饰性 brand 色 / 颜色作 hierarchy / 多色 UI

## Typography

### decision: Nike Futura ND with line-height 0.90 — typographic shockwave on hero
- **trade_off**: 标准 lh 1.0+（呼吸） ↔ 0.90 极紧（impossibly tight, 击穿 imagery）
- **intent**: 让 display headline 像视觉拳击——不是文字，是 statement
- **avoid**: 标准 lh / 装饰 serif / 中等 weight 散漫

### decision: split typography — Nike Futura ND display + Helvetica Now body
- **trade_off**: 单字体（一致） ↔ split display/body（inspiration vs execution duality）
- **intent**: display = inspiration（aspirational headline），body = execution（functional clarity）
- **avoid**: 单 family flatness / 装饰 display / 通用 system body

## Components

### decision: 30px pill buttons + full-bleed photography (no border radius on imagery)
- **trade_off**: 中等 radius（普适） ↔ pill + 0 imagery radius（duality of softness vs edge）
- **intent**: button 友好但 imagery 紧贴边缘 = action + raw energy
- **avoid**: 软化 imagery / 直角 button / 装饰 frame
