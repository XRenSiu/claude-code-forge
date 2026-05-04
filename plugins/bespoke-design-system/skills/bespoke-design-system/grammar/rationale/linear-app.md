# Rationale — linear-app

> 三段式 rationale 抽取自 `source-design-systems/linear-app/DESIGN.md`。
> 显式 rationale 来自 DESIGN.md 散文段落 + Do's/Don'ts；推断条目标 `[inferred]`。

## Visual Theme & Atmosphere

### decision: dark-mode-first as native medium (not light theme darkened)

原 DESIGN.md 段落（auto-backfill）：
> **Button-style Input**
> - Text: `#8a8f98`
> - Padding: 1px 6px
> - Radius: 5px
> - Focus shadow: multi-layer stack
- **trade_off**: 标准 web 亮底（普适、低门槛） ↔ darkness as native medium（信息密度通过亮度梯度表达）
- **intent**: 让产品以工程精度感呈现——内容如星光在黑色画布上浮现
- **avoid**:
  - 把亮主题简单"反相"成暗主题的普通做法
  - 用纯黑（#000000）造成的窗口感切割
  - 暗模式常见的"游戏 UI"或"科技品牌"过度修饰

### decision: brand indigo-violet (#5e6ad2) as the only chromatic accent

原 DESIGN.md 段落（auto-backfill）：
> **Search Input**
> - Background: transparent
> - Text: `#f7f8f8`
> - Padding: 1px 32px (icon-aware)
- **trade_off**: 全 monochrome（极致克制） ↔ 多色品牌系统（活泼但分散注意）
- **intent**: 让品牌色成为视觉锚点，控制注意力路径
- **avoid**:
  - 纯蓝带来的"医疗器械感"或"通用 SaaS 感"
  - 紫色装饰化使用导致的"游戏 UI 感"
  - 把 brand 色用在非交互元素上的稀释

## Color

### decision: 4-tier achromatic text scale (#f7f8f8 → #d0d6e0 → #8a8f98 → #62666d)

原 DESIGN.md 段落（auto-backfill）：
> **Icon Button (Circle)**
> - Background: `rgba(255,255,255,0.03)` or `rgba(255,255,255,0.05)`
> - Text: `#f7f8f8` or `#ffffff`
> - Radius: 50%
> - Border: `1px solid rgba(255,255,255,0.08)`
> - Use: Close, menu toggle, icon-only actions
- **trade_off**: 多对比度等级（信息层级清晰） ↔ 视觉噪声（梯度过细难辨别）
- **intent**: 在暗背景上用 4 级亮度构建可读的信息层级，不依赖颜色变化
- **avoid**:
  - 用纯白 #ffffff 造成视觉灼烧
  - 用过低对比的灰造成可读性丧失

### decision: semi-transparent white borders (rgba(255,255,255,0.05-0.08)) instead of solid dark

原 DESIGN.md 段落（auto-backfill）：
> **Pill Button**
> - Background: transparent
> - Text: `#d0d6e0`
> - Padding: 0px 10px 0px 5px
> - Radius: 9999px
> - Border: `1px solid rgb(35, 37, 42)`
> - Use: Filter chips, tags, status indicators
- **trade_off**: 实色边框（明确） ↔ 半透明白边框（融入背景但需要细节）
- **intent**: 让边界存在但不喧宾夺主——"如月光下绘出的线框"
- **avoid**:
  - 实色暗边在暗底上的视觉断层
  - 边框成为视觉"墙"切割空间

## Typography

### decision: Inter Variable + cv01,ss03 + 510 weight as signature

原 DESIGN.md 段落（auto-backfill）：
> **Small Toolbar Button**
> - Background: `rgba(255,255,255,0.05)`
> - Text: `#62666d` (muted)
> - Radius: 2px
> - Border: `1px solid rgba(255,255,255,0.05)`
> - Shadow: `rgba(0,0,0,0.03) 0px 1.2px 0px 0px`
> - Font: 12px weight 510
> - Use: Toolbar actions, quick-access controls
- **trade_off**: 标准 Inter（普适但通用） ↔ Inter+OpenType+510（独特但需要一致执行）
- **intent**: 把 Inter 改造成 Linear 自己的字体——cv01 单层 a + ss03 几何调整 + 介于 regular 和 medium 之间的 510 weight，强调而不喧哗
- **avoid**:
  - 通用 Inter 默认导致的"AI slop"识别度
  - weight 700 bold 的过度强调
  - weight 500 medium 的过粗感

### decision: aggressive negative letter-spacing at display sizes (-1.584px@72px → normal@16px)

原 DESIGN.md 段落（auto-backfill）：
> > Category: Productivity & SaaS
> > Project management. Ultra-minimal, precise, purple accent.
- **trade_off**: 字距宽松（呼吸感） ↔ 紧密负字距（压缩、工程化）
- **intent**: 让大字号显得 minified、像优化过的代码——压缩、精确、有权威感
- **avoid**:
  - display 文字松散的"广告腔"
  - 字距过紧造成可读性下降（所以小字号回到 normal）

## Components

### decision: button backgrounds at near-zero opacity (rgba(255,255,255,0.02-0.05))

原 DESIGN.md 段落（auto-backfill）：
> **Subtle Button**
> - Background: `rgba(255,255,255,0.04)`
> - Text: `#d0d6e0` (silver-gray)
> - Padding: 0px 6px
> - Radius: 6px
> - Use: Toolbar actions, contextual buttons
- **trade_off**: 实色按钮（明确可点） ↔ 几乎不可见的按钮（克制、融入界面）
- **intent**: 让 UI 元素不喊叫——按钮存在但不打扰，悬停时通过背景透明度提升揭示交互
- **avoid**:
  - 实色暗灰按钮在暗底上的"游离感"
  - 渐变按钮的科技品牌感

### decision: brand CTA button reserved exclusively for primary actions

原 DESIGN.md 段落（auto-backfill）：
> **Ghost Button (Default)**
> - Background: `rgba(255,255,255,0.02)`
> - Text: `#e2e4e7` (near-white)
> - Padding: comfortable
> - Radius: 6px
> - Border: `1px solid rgb(36, 40, 44)`
> - Outline: none
> - Focus shadow: `rgba(0,0,0,0.1) 0px 4px 12px`
> - Use: Standard actions, secondary CTAs
- **trade_off**: 多处装饰（视觉一致） ↔ 单一锚点（注意力工程）
- **intent**: brand 色成为视觉路径的终点，引导用户到关键决策
- **avoid**:
  - 装饰性使用 brand 色稀释其作用
  - 多个 brand 色并列造成选择困难

## Layout & Elevation

### decision: luminance stepping replaces traditional shadow elevation

原 DESIGN.md 段落（auto-backfill）：
> Linear's website is a masterclass in dark-mode-first product design — a near-black canvas (`#08090a`) where content emerges from darkness like starlight. The overall impression is one of extreme precision engineering: every element exists in a carefully calibrated hierarchy of luminance, from barely-visible borders (`rgba(255,255,255,0.05)`) to soft, luminous text (`#f7f8f8`). This is not a dark theme applied to a light design — it is darkness as the native medium, where information density is managed through subtle gradations of white opacity rather than color variation.
- **trade_off**: 传统阴影（直观） ↔ 亮度叠加（暗底独有的深度系统）
- **intent**: 在暗底上传统阴影几乎不可见，改用背景亮度递进（rgba 白 0.02 → 0.04 → 0.05）建立层级
- **avoid**:
  - 在暗底上用深色 drop shadow 的"隐形阴影"
  - 完全无层级造成的扁平感

### decision: 8px base spacing with 7px/11px micro-adjustments for optical alignment

原 DESIGN.md 段落（auto-backfill）：
> **Primary Brand Button (Inferred)**
> - Background: `#5e6ad2` (brand indigo)
> - Text: `#ffffff`
> - Padding: 8px 16px
> - Radius: 6px
> - Hover: `#828fff` shift
> - Use: Primary CTAs ("Start building", "Sign up")
- **trade_off**: 严格倍数 grid（机械精确） ↔ 含光学修正（人眼可读但工程师能解释） [inferred]
- **intent**: 数学精确 + 光学修正——让 grid 看起来对齐而非数值对齐
- **avoid**:
  - 纯数学 grid 在某些尺寸下显得歪
  - 完全光学化造成的不可重现

### decision: section isolation via vertical padding (80px+) without dividers

原 DESIGN.md 段落（auto-backfill）：
> **Text Area**
> - Background: `rgba(255,255,255,0.02)`
> - Text: `#d0d6e0`
> - Border: `1px solid rgba(255,255,255,0.08)`
> - Padding: 12px 14px
> - Radius: 6px
- **trade_off**: 显式分割线（结构清晰） ↔ 留白即分隔（克制、空间叙事）
- **intent**: 让黑色背景本身成为分隔——空间分隔取代视觉分隔
- **avoid**:
  - 多余的水平线分割造成的视觉切片
  - 留白不足导致 section 互相溶解

## Voice / Brand-implicit

### decision: signature voice is "engineered, not designed" [inferred from typography + spacing decisions]

原 DESIGN.md 段落（auto-backfill）：
> The color system is almost entirely achromatic — dark backgrounds with white/gray text — punctuated by a single brand accent: Linear's signature indigo-violet (`#5e6ad2` for backgrounds, `#7170ff` for interactive accents). This accent color is used sparingly and intentionally, appearing only on CTAs, active states, and brand elements. The border system uses ultra-thin, semi-transparent white borders (`rgba(255,255,255,0.05)` to `rgba(255,255,255,0.08)`) that create structure without visual noise, like wireframes drawn in moonlight.
- **trade_off**: 设计感（艺术性） ↔ 工程感（精度感、构建感）
- **intent**: 让产品看起来像 build 出来的而不是 paint 出来的——所有装饰都有功能依据
- **avoid**:
  - 装饰性渐变 / 装饰性插画
  - "designed by committee" 的折中感
  - 过度品牌化的 marketing 腔调

## Anti-patterns（直接来自 Don'ts，整理为 anti-pattern 形式）

- **不要用 #ffffff 纯白做主文字** — 视觉灼烧，破坏 cool gray 调性
- **不要用实色暗边框** — 视觉墙切割空间
- **不要用 weight 700 bold** — 超过 590 破坏 quiet emphasis 系统
- **不要把 brand indigo 装饰化** — 稀释视觉锚点的功能
- **不要在 display 字号用正字距** — 破坏"compressed engineering"调性
- **不要用 drop shadow 做深度** — 暗底上无效，应该用亮度叠加
- **不要引入暖色** — 整套系统是 cool gray + cool brand

---

## 抽取统计

- 显式 rationale: 11 条
- 推断 rationale (`[inferred]`): 2 条（Voice、grid 光学修正部分）
- 9-section 覆盖：Visual Theme(2) + Color(2) + Typography(2) + Components(2) + Layout/Elevation(3) + Voice(1) + Anti-patterns(7)
- 缺失 section: Motion（OD 格式无专门 motion section，本套也无足够 motion 数据可抽）
