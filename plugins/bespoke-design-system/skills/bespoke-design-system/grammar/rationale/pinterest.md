# Rationale — pinterest

> 三段式 rationale 抽取自 `source-design-systems/pinterest/DESIGN.md`。

## Visual Theme

### decision: warm inspiration-driven canvas — slightly warm white + craft-like neutral undertone
- **trade_off**: 冷蓝 tech 平台调（mainstream） ↔ 暖白 + olive/sand 中性（lifestyle magazine）
- **intent**: 让浏览像 craft / lifestyle 翻杂志，不像 corporate tech
- **avoid**: 冷蓝 platform 感 / 临床 white / 多色 brand

## Color

### decision: Pinterest Red (#e60023) — singular bold accent, never subtle, always confident
- **trade_off**: 中等饱和 brand（克制） ↔ 高饱和 red（confident statement）
- **intent**: red 是 brand statement，不是装饰也不是状态色
- **avoid**: 弱化 red / 多色 brand / 装饰性 red

### decision: warm-tinted neutral scale — olive/sand grays (#91918c, #62625b, #e5e5e0) not cool steel
- **trade_off**: 冷灰（普适 tech） ↔ 暖灰（lifestyle / craft）
- **intent**: 让 UI background / surface 像 paper / fabric 自然材料
- **avoid**: 冷蓝灰 / 纯灰 / 装饰多色

### decision: plum-tinted near-black text (#211922) — warm with hint of plum
- **trade_off**: 纯黑（精度） ↔ 暖近黑 + plum undertone（warm depth）
- **intent**: text 暖暖的不冷
- **avoid**: 纯黑 / 蓝 undertone / 中等灰

## Components

### decision: generous radius scale 12-40px + 50% circles
- **trade_off**: 中等 radius ↔ 大 radius（friendly + handcrafted）
- **intent**: 让 chrome 像 hand-cut / handcrafted feel
- **avoid**: 直角 / 中等 8-12 中庸 / 装饰 corner

### decision: 3-tier design token architecture (--comp-* / --sema-* / --base-*)
- **trade_off**: 单层 token（简单） ↔ 3-tier（component / semantic / base 分工）
- **intent**: 让 token 系统支持大型多产品 design 系统的可演化性
- **avoid**: 硬编码值 / 单层 token 不可扩展
