# Rationale — github

> 三段式 rationale 抽取自 `source-design-systems/github/DESIGN.md`。

## Color

### decision: 14px body + dense list rows + hairline borders
- **trade_off**: 16px 标准 body（普适可读） ↔ 14px 密集（power-user 一屏看更多）
- **intent**: 让产品成为 "diff/build/PR 工具" — 信息密度是品牌
- **avoid**: 16px 默认 / 大留白 / 视觉噪声 / 装饰性 padding

### decision: Primer Blue (#0969da) + GitHub Green (#1a7f37) 双 chromatic anchor
- **trade_off**: 单 chromatic（极致克制） ↔ 双 chromatic（链接 + 状态分工）
- **intent**: blue = 通用交互（链接 / focus / CTA），green = 合并 / 成功（产品语义）
- **avoid**: 多 chromatic 竞争 / 装饰性 brand 色 / 消费者级饱和度

### decision: hairline gray borders (#d0d7de) instead of shadow elevation
- **trade_off**: shadow（柔软深度） ↔ hairline border（工程精度）
- **intent**: 让 panel 边界靠 1px 边框定义，不靠空间或阴影
- **avoid**: 软阴影 / 圆角卡片浮起 / 视觉柔化

## Typography

### decision: system-ui across the entire product, no custom webfont
- **trade_off**: custom typeface（独特调性） ↔ system-ui（即时渲染 + 跨 OS 一致）
- **intent**: GitHub 的声音是"你已在的系统"的声音
- **avoid**: 加载 webfont 延迟 / 跨 OS 渲染差异

## Components

### decision: pill status badges with strong color semantics
- **trade_off**: 通用 chip（中性） ↔ 强语义状态徽章（颜色即含义）
- **intent**: open/merged/closed/draft 一眼可识别
- **avoid**: 通用 tag / 颜色装饰用法

### decision: zero radius on dark theme borders + Octicon at 16/24px
- **trade_off**: 圆角 friendliness ↔ 严苛 geometry
- **intent**: 工程精度 + 单 stroke icon 一致性
- **avoid**: 大圆角消费者感 / 多 stroke 复杂度
