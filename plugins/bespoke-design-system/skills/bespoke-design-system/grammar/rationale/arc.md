# Rationale — arc

> 三段式 rationale 抽取自 `source-design-systems/arc/DESIGN.md`。

## Visual Theme

### decision: frosted-glass + saturated gradient backdrop as scenery (chrome dissolves into wallpaper)
- **trade_off**: 标准 chrome（普适、固定） ↔ chrome-as-scenery（mood-driven、user-themed）
- **intent**: 浏览器边框不是容器，是背景——translucent surfaces 让 page 与 chrome 融为一体
- **avoid**: 硬边 chrome / 固定品牌色 / 离散 panel borders

### decision: theme color is user-driven (peach-coral / violet-fuchsia / mint-cyan presets)
- **trade_off**: 固定品牌色（一致性） ↔ 用户主题（情绪自由）
- **intent**: 让品牌色成为 user mood，不是公司标识
- **avoid**: 强加单一品牌色 / 限制用户表达

## Color

### decision: gradient-as-primary-surface, frosted glass over it
- **trade_off**: 实色 surface（清晰） ↔ 渐变 + 半透明（mood + 深度）
- **intent**: 让 surface 自带 mood，不靠 illustration / decoration
- **avoid**: 实色 panel / 边缘断层

## Typography & Components

### decision: squircle-soft 12-16px radii everywhere; pills (9999) for tags
- **trade_off**: 严苛 geometry（精度） ↔ squircle softness（亲和）
- **intent**: 让 chrome 感觉 "alive but not sharp" — Apple-grade affordance
- **avoid**: 直角 chrome / 8px 以下小圆角（不够 squircle）

### decision: subtle shadows (0 8px 32px rgba(0,0,0,0.08)) over the gradient
- **trade_off**: 阴影（柔软） ↔ 边框（精度）
- **intent**: 在渐变背景上用大模糊低透明度阴影暗示 panel 浮起
- **avoid**: 硬边 / 高对比阴影
