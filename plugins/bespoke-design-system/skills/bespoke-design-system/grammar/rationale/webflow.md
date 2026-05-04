# Rationale — webflow

> 三段式 rationale 抽取自 `source-design-systems/webflow/DESIGN.md`。

## Visual Theme

### decision: tool-forward platform — clean white + Webflow Blue + rich secondary palette

原 DESIGN.md 段落（auto-backfill）：
> Webflow's website is a visually rich, tool-forward platform that communicates "design without code" through clean white surfaces, the signature Webflow Blue (`#146ef5`), and a rich secondary color palette (purple, pink, green, orange, yellow, red). The custom WF Visual Sans Variable font creates a confident, precise typographic system with weight 600 for display and 500 for body.
- **trade_off**: 单 chromatic 极简 ↔ blue + 多色 secondary（design without code 表达多样性）
- **intent**: 让 platform 看起来 capable + creative — 暗示用户产品可以多色
- **avoid**: 单色 platform 限制感 / 无 brand color / 装饰多色

## Color

### decision: Webflow Blue (#146ef5) primary + 6-color secondary (purple/pink/green/orange/yellow/red)

原 DESIGN.md 段落（auto-backfill）：
> **Key Characteristics:**
> - White canvas with near-black (`#080808`) text
> - Webflow Blue (`#146ef5`) as primary brand + interactive color
> - WF Visual Sans Variable — custom variable font with weight 500–600
> - Rich secondary palette: purple `#7a3dff`, pink `#ed52cb`, green `#00d722`, orange `#ff6b00`, yellow `#ffae13`, red `#ee1d36`
> - Conservative 4px–8px border-radius — sharp, not rounded
> - Multi-layer shadow stacks (5-layer cascading shadows)
> - Uppercase labels: 10px–15px, weight 500–600, wide letter-spacing (0.6px–1.5px)
> - translate(6px) hover animation on buttons
- **trade_off**: 单 brand（一致） ↔ 1+6 chromatic（rich palette signals creativity）
- **intent**: brand blue 是主色，secondary palette 暗示 platform 多色能力
- **avoid**: 单色限制感 / 多色无层级 / 装饰多色

## Typography

### decision: WF Visual Sans Variable — custom variable font + tight uppercase labels

原 DESIGN.md 段落（auto-backfill）：
> Webflow's website is a visually rich, tool-forward platform that communicates "design without code" through clean white surfaces, the signature Webflow Blue (`#146ef5`), and a rich secondary color palette (purple, pink, green, orange, yellow, red). The custom WF Visual Sans Variable font creates a confident, precise typographic system with weight 600 for display and 500 for body.
- **trade_off**: 通用 sans（普适） ↔ proprietary variable（precision + brand identity）
- **intent**: 让字体本身体现 "design without code" 的精度承诺
- **avoid**: 通用 system font / 装饰 serif / 单 weight

## Components & Layout

### decision: conservative 4-8px border-radius — sharp not rounded

原 DESIGN.md 段落（auto-backfill）：
> > Category: Design & Creative
> > Visual web builder. Blue-accented, polished marketing site aesthetic.
- **trade_off**: 大圆角 friendly ↔ 4-8 conservative（design tool 工程精度）
- **intent**: 让 chrome 像 design tool 不像 consumer app
- **avoid**: 大圆角 friendly / sub-4 sharp / pill 装饰

### decision: uppercase labels with wide letter-spacing (0.6-1.5px)

原 DESIGN.md 段落（auto-backfill）：
> **Key Characteristics:**
> - White canvas with near-black (`#080808`) text
> - Webflow Blue (`#146ef5`) as primary brand + interactive color
> - WF Visual Sans Variable — custom variable font with weight 500–600
> - Rich secondary palette: purple `#7a3dff`, pink `#ed52cb`, green `#00d722`, orange `#ff6b00`, yellow `#ffae13`, red `#ee1d36`
> - Conservative 4px–8px border-radius — sharp, not rounded
> - Multi-layer shadow stacks (5-layer cascading shadows)
> - Uppercase labels: 10px–15px, weight 500–600, wide letter-spacing (0.6px–1.5px)
> - translate(6px) hover animation on buttons
- **trade_off**: 小写 humanist ↔ uppercase + wide tracking（systematic + structural）
- **intent**: nav / category label 像 design system markers
- **avoid**: 小写 marketing / 紧字距 / 装饰 nav style
