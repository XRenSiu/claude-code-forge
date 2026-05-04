# Rationale — arc

> 三段式 rationale 抽取自 `source-design-systems/arc/DESIGN.md`。

## Visual Theme

### decision: frosted-glass + saturated gradient backdrop as scenery (chrome dissolves into wallpaper)

原 DESIGN.md 段落（auto-backfill）：
> **Glass (Secondary)**
> - Background: `rgba(255, 255, 255, 0.7)`
> - Backdrop: `blur(20px)`
> - Text: `#1a1a1f`
> - Border: 1px solid `rgba(255, 255, 255, 0.4)`
> - Padding: 10px 20px
> - Radius: 12px
- **trade_off**: 标准 chrome（普适、固定） ↔ chrome-as-scenery（mood-driven、user-themed）
- **intent**: 浏览器边框不是容器，是背景——translucent surfaces 让 page 与 chrome 融为一体
- **avoid**: 硬边 chrome / 固定品牌色 / 离散 panel borders

### decision: theme color is user-driven (peach-coral / violet-fuchsia / mint-cyan presets)

原 DESIGN.md 段落（auto-backfill）：
> Arc Browser dissolves the boundary between the chrome and the page. Where Chrome and Safari treat the browser frame as a container, Arc treats it as scenery — the toolbar fades into the system wallpaper, the sidebar carries gradient warmth from the user's chosen "theme color", and translucency is everywhere. The visual signature is **frosted glass plus a single saturated gradient** — most often a peach-to-coral or violet-to-fuchsia bloom — that sets the emotional temperature of the entire window.
- **trade_off**: 固定品牌色（一致性） ↔ 用户主题（情绪自由）
- **intent**: 让品牌色成为 user mood，不是公司标识
- **avoid**: 强加单一品牌色 / 限制用户表达

## Color

### decision: gradient-as-primary-surface, frosted glass over it

原 DESIGN.md 段落（auto-backfill）：
> > Category: Productivity & SaaS
> > "The browser that browses for you." Translucent surfaces, gradient warmth, sidebar-first layout.
- **trade_off**: 实色 surface（清晰） ↔ 渐变 + 半透明（mood + 深度）
- **intent**: 让 surface 自带 mood，不靠 illustration / decoration
- **avoid**: 实色 panel / 边缘断层

## Typography & Components

### decision: squircle-soft 12-16px radii everywhere; pills (9999) for tags

原 DESIGN.md 段落（auto-backfill）：
> Shapes are squircle-soft: 12–16px radii on cards, 8px on tabs, 9999px pills for tags. Borders are rare — Arc prefers tinted background washes (`rgba(255, 255, 255, 0.5)` over the gradient) to delineate panes.
- **trade_off**: 严苛 geometry（精度） ↔ squircle softness（亲和）
- **intent**: 让 chrome 感觉 "alive but not sharp" — Apple-grade affordance
- **avoid**: 直角 chrome / 8px 以下小圆角（不够 squircle）

### decision: subtle shadows (0 8px 32px rgba(0,0,0,0.08)) over the gradient

原 DESIGN.md 段落（auto-backfill）：
> **Key Characteristics:**
> - Translucent frosted-glass surfaces over a saturated gradient background
> - Theme-color gradients (peach-coral, violet-fuchsia, mint-cyan) as the primary mood
> - Inter for product chrome, Argent CF (serif) for marketing display
> - Squircle-soft 12–16px radii everywhere
> - Sidebar-first layout: tabs, spaces, and bookmarks live on the left, not the top
> - Color picker is a brand surface — themes are user-driven, not fixed
> - Subtle shadows (`0 8px 32px rgba(0,0,0,0.08)`) over the gradient backdrop
- **trade_off**: 阴影（柔软） ↔ 边框（精度）
- **intent**: 在渐变背景上用大模糊低透明度阴影暗示 panel 浮起
- **avoid**: 硬边 / 高对比阴影
