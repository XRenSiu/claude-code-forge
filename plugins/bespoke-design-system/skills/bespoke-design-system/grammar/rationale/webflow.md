# Rationale — webflow

> 三段式 rationale 抽取自 `source-design-systems/webflow/DESIGN.md`。

## Visual Theme

### decision: tool-forward platform — clean white + Webflow Blue + rich secondary palette
- **trade_off**: 单 chromatic 极简 ↔ blue + 多色 secondary（design without code 表达多样性）
- **intent**: 让 platform 看起来 capable + creative — 暗示用户产品可以多色
- **avoid**: 单色 platform 限制感 / 无 brand color / 装饰多色

## Color

### decision: Webflow Blue (#146ef5) primary + 6-color secondary (purple/pink/green/orange/yellow/red)
- **trade_off**: 单 brand（一致） ↔ 1+6 chromatic（rich palette signals creativity）
- **intent**: brand blue 是主色，secondary palette 暗示 platform 多色能力
- **avoid**: 单色限制感 / 多色无层级 / 装饰多色

## Typography

### decision: WF Visual Sans Variable — custom variable font + tight uppercase labels
- **trade_off**: 通用 sans（普适） ↔ proprietary variable（precision + brand identity）
- **intent**: 让字体本身体现 "design without code" 的精度承诺
- **avoid**: 通用 system font / 装饰 serif / 单 weight

## Components & Layout

### decision: conservative 4-8px border-radius — sharp not rounded
- **trade_off**: 大圆角 friendly ↔ 4-8 conservative（design tool 工程精度）
- **intent**: 让 chrome 像 design tool 不像 consumer app
- **avoid**: 大圆角 friendly / sub-4 sharp / pill 装饰

### decision: uppercase labels with wide letter-spacing (0.6-1.5px)
- **trade_off**: 小写 humanist ↔ uppercase + wide tracking（systematic + structural）
- **intent**: nav / category label 像 design system markers
- **avoid**: 小写 marketing / 紧字距 / 装饰 nav style
