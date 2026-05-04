# Rationale — figma

> 三段式 rationale 抽取自 `source-design-systems/figma/DESIGN.md`。Dialect A 但极特殊——chrome 严格黑白二元 + 内容多色。

## Visual Theme & Atmosphere

### decision: Black-and-white interface chrome — color exists ONLY in product content

原 DESIGN.md 段落（auto-backfill）：
> **Black Solid (Pill)**
> - Background: Pure Black (`#000000`)
> - Text: Pure White (`#ffffff`)
> - Radius: circle (50%) for icon buttons
> - Focus: dashed 2px outline
> - Maximum emphasis
- **trade_off**: brand chromatic（视觉识别） ↔ chromatic-free chrome（让产品本身成为画廊艺术品）
- **intent**: 让 marketing page 像白墙美术馆——product screenshots 是展品，chrome 是相框
- **avoid**:
  - chrome 加 brand 色（与"画廊"调性冲突）
  - 多色 chrome 与多色产品 screenshots 视觉竞争

### decision: Vibrant multi-color hero gradient (electric green / yellow / purple / pink)

原 DESIGN.md 段落（auto-backfill）：
> **Hero Gradient Section**
> - Full-width vibrant multi-color gradient background
> - White text overlay with 86px display heading
> - Product screenshots floating within the gradient
- **trade_off**: 单色 hero（沉稳） ↔ 极致多色 gradient（"this is what your tool can create"）
- **intent**: 让 hero 本身就是 product capability 的证明——color is the output
- **avoid**:
  - 单色 hero（违反 product 价值主张）
  - 但仅在 hero——chrome 仍黑白

## Color

### decision: Pure binary — only #000000 and #ffffff in chrome

原 DESIGN.md 段落（auto-backfill）：
> The page presents a fascinating duality: the interface chrome is strictly black-and-white (literally only `#000000` and `#ffffff` detected as colors), while the hero section and product showcases explode with vibrant multi-color gradients — electric greens, bright yellows, deep purples, hot pinks. This separation means the design system itself is colorless, treating the product's colorful output as the hero content. Figma's marketing page is essentially a white gallery wall displaying colorful art.
- **trade_off**: 灰阶 ladder（细微层级） ↔ 严格 binary
- **intent**: 极致的 chromatic discipline——任何"灰" 都通过 alpha 实现（rgba black 或 white）
- **avoid**:
  - 灰阶 ladder（破坏 binary）
  - 引入第三种 chrome 色

### decision: Glass overlays via rgba alpha — black 0.08, white 0.16

原 DESIGN.md 段落（auto-backfill）：
> **Glass Dark**
> - Background: `rgba(0, 0, 0, 0.08)` (subtle dark overlay)
> - Text: Pure Black
> - Radius: circle (50%)
> - Focus: dashed 2px outline
> - Secondary action on light surfaces
- **trade_off**: 实色背景 ↔ 半透明 glass
- **intent**: 让 secondary action 在不引入新色的前提下有 surface depth
- **avoid**:
  - 实色 secondary（破坏 binary）
  - 高 alpha（变成实色）

## Typography

### decision: figmaSans variable font with unusual weight stops (320, 330, 340, 450, 480, 540, 700)

原 DESIGN.md 段落（auto-backfill）：
> **Product Tab Bar**
> - Horizontal pill-shaped tabs (50px radius)
> - Each tab represents a Figma product area (Design, Dev Mode, Prototyping, etc.)
> - Active tab highlighted
- **trade_off**: 标准 weight ladder (400/500/600) ↔ 自定义 micro-step weight
- **intent**: 让 hierarchy via 微小 weight 差异——330 vs 340 几乎不可察但结构化重要
- **avoid**:
  - blunt regular-vs-bold 对比（破坏 typographic 工具调性）
  - 标准 ladder（不够"design tool"）

### decision: Light as base — body 320-340 weight (lighter than typical 400)

原 DESIGN.md 段落（auto-backfill）：
> Figma's interface is the design tool that designed itself — a masterclass in typographic sophistication where a custom variable font (figmaSans) modulates between razor-thin (weight 320) and bold (weight 700) with stops at unusual intermediates (330, 340, 450, 480, 540) that most type systems never explore. This granular weight control gives every text element a precisely calibrated visual weight, creating hierarchy through micro-differences rather than the blunt instrument of "regular vs bold."
- **trade_off**: 标准 regular（行业默认） ↔ 320 ethereal（airy）
- **intent**: 让阅读有 design-tool 调性——光、精致、unintrusive
- **avoid**:
  - 普通 regular weight（无 character）
  - 极轻（不可读）

### decision: Negative tracking everywhere — even body -0.14 to -0.26

原 DESIGN.md 段落（auto-backfill）：
> **Glass Light**
> - Background: `rgba(255, 255, 255, 0.16)` (frosted glass)
> - Text: Pure White
> - Radius: circle (50%)
> - Focus: dashed 2px outline
> - Secondary action on dark/colored surfaces
- **trade_off**: 标准 tracking（可读默认） ↔ 全局 negative
- **intent**: 让所有文本"紧凑"——design tool 的精确语言
- **avoid**:
  - 正字距任何尺寸（违反图形精度）

### decision: figmaMono uppercase + positive tracking 0.54-0.6 for technical labels

原 DESIGN.md 段落（auto-backfill）：
> *Note: Figma's marketing site uses ONLY these two colors for its interface layer. All vibrant colors appear exclusively in product screenshots, hero gradients, and embedded content.*
- **trade_off**: 装饰 monospace ↔ structural mono labels
- **intent**: mono 大写带正字距 = 技术 signpost——"这里是 code-context"
- **avoid**:
  - mono 用于 prose（过密）
  - 小写 mono（弱化 signal）

## Components

### decision: Pill (50px) + circle (50%) button geometry

原 DESIGN.md 段落（auto-backfill）：
> **Key Characteristics:**
> - Custom variable font (figmaSans) with unusual weight stops: 320, 330, 340, 450, 480, 540, 700
> - Strictly black-and-white interface chrome — color exists only in product content
> - figmaMono for uppercase technical labels with wide letter-spacing
> - Pill (50px) and circular (50%) button geometry
> - Dashed focus outlines echoing Figma's editor selection handles
> - Vibrant multi-color hero gradients (green, yellow, purple, pink)
> - OpenType `"kern"` feature enabled globally
> - Negative letter-spacing throughout — even body text at -0.14px to -0.26px
- **trade_off**: 矩形 button 严肃 ↔ pill/circle organic
- **intent**: 让 UI 像 tool palette——organic、tactile、approachable
- **avoid**:
  - 标准 4-8px 矩形（与 design tool 调性冲突）
  - 极端尖角

### decision: Dashed 2px focus outline (echoing Figma editor selection handles)

原 DESIGN.md 段落（auto-backfill）：
> What makes Figma distinctive beyond the variable font is its circle-and-pill geometry. Buttons use 50px radius (pill) or 50% (perfect circle for icon buttons), creating an organic, tool-palette-like feel. The dashed-outline focus indicator (`dashed 2px`) is a deliberate design choice that echoes selection handles in the Figma editor itself — the website's UI language references the product's UI language.
- **trade_off**: 实线 focus ring（标准） ↔ dashed outline（self-referential 设计）
- **intent**: 让 web UI 引用自家 product UI——meta-design 的彩蛋
- **avoid**:
  - 标准实线 focus（错失 brand 时刻）

## Layout

### decision: 6px small / 8px standard radius for cards (despite pill buttons)

原 DESIGN.md 段落（auto-backfill）：
> **White Pill**
> - Background: Pure White (`#ffffff`)
> - Text: Pure Black (`#000000`)
> - Padding: 8px 18px 10px (asymmetric vertical)
> - Radius: pill (50px)
> - Focus: dashed 2px outline
> - Standard CTA on dark/colored surfaces
- **trade_off**: 全圆角统一 ↔ 卡片中等 radius + 按钮极端 radius（gradient of organicness）
- **intent**: cards 仍要 functional clarity，但 buttons 充分 expressive
- **avoid**:
  - cards 也 pill 化（损害 functional readability）

## Voice / Brand-implicit

### decision: design-tool-aware voice [inferred]

原 DESIGN.md 段落（auto-backfill）：
> > Category: Design & Creative
> > Collaborative design tool. Vibrant multi-color, playful yet professional.
- **trade_off**: 通用 marketing voice ↔ 设计师专用语言（assumes craft-level vocabulary）
- **intent**: 让 designer 读起来像同行说话——尊重 expertise
- **avoid**:
  - 解释术语过度
  - hyperbole 营销腔

## Anti-patterns

- 不要在 chrome 引入除黑白以外的色
- 不要标准 weight ladder（破坏 figmaSans 的 micro-step 哲学）
- 不要正字距任何尺寸
- 不要实线 focus（错失 dashed-outline brand 时刻）
- 不要多色 hero + 多色 chrome 同时存在
- 不要把 mono 字体用于 prose

---

## 抽取统计

- 显式 rationale: 11 条
- 推断 [inferred]: 1 条（Voice）
- 9-section 覆盖：完整 dialect A
- 极特殊：variable-font + binary-chrome + dashed-focus 是这套 system 的不可复制三件套
