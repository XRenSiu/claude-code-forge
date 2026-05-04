# Rationale — apple

> 三段式 rationale 抽取自 `source-design-systems/apple/DESIGN.md`. Dialect A —— premium electronics + binary section rhythm。

## Visual Theme & Atmosphere

### decision: Binary section rhythm — `#000000` chapters alternating with `#f5f5f7` neutral fields

原 DESIGN.md 段落（auto-backfill）：
> Level | Treatment | Use |
> |------|-----------|-----|
> | Level 0 | Flat neutral surfaces (`#ffffff`, `#f5f5f7`, `#000000`) | Main narrative and product stages |
> | Level 1 | Subtle border containment (`#d2d2d7`, `#86868b`) | Filters, input fields, utility cards |
> | Level 2 | Soft shadow (`rgba(0,0,0,0.
- **trade_off**: 单一 surface 一致 ↔ 黑白章节交替（戏剧性视觉节奏）
- **intent**: 让 marketing page 像 cinematic 章节切换——dark 是 hero，light 是 detail
- **avoid**:
  - 单 surface（视觉单调）
  - 多色 surface（破坏 chromatic 克制）

### decision: Two operating modes in one system — showcase mode + transaction mode

原 DESIGN.md 段落（auto-backfill）：
> Across the five analyzed pages, the rhythm is consistent but not monolithic. Marketing surfaces (homepage and Environment) use cinematic black-and-light chaptering, while commerce surfaces (Store and Shop flows) introduce tighter spacing, more utility controls, and denser card stacks without breaking the core brand grammar. The result is one system with two gears: showcase mode and transaction mode.
- **trade_off**: 两个独立 design system（差异） ↔ 一个 system 两 gear（cohesion）
- **intent**: 让 marketing 与 commerce 共享 token 但 density 不同——showcase 松，commerce 紧
- **avoid**:
  - marketing 与 commerce 完全独立（破坏 brand 一致性）

### decision: Hardware/imagery carries narrative weight — UI chrome stays visually thin

原 DESIGN.md 段落（auto-backfill）：
> > Category: Media & Consumer
> > Consumer electronics. Premium white space, SF Pro, cinematic imagery.
- **trade_off**: chrome 装饰（attractive） ↔ chrome 隐形（让 product 表达）
- **intent**: 让 hardware finish 成为视觉中心——UI 是相框
- **avoid**:
  - chrome 与 hardware 视觉竞争
  - 简化 hardware imagery（违反 product-first）

## Color

### decision: Triple-foundation neutrals (Black #000000 + Pale Gray #f5f5f7 + White #ffffff)

原 DESIGN.md 段落（auto-backfill）：
> Do
> - Use the neutral triad (`#000000`, `#f5f5f7`, `#ffffff`) as the structural foundation.
- **trade_off**: 多色基础 ↔ 三 neutral 锚（chromatic 极简）
- **intent**: 让 dark/light/white 三种 chapter 类型成为系统结构
- **avoid**:
  - 引入第四 base（破坏三元 rhythm）
  - 灰阶 ladder（与三元结构冲突）

### decision: Single Apple Action Blue family (#0071e3 / #0066cc / #2997ff)

原 DESIGN.md 段落（auto-backfill）：
> Secondary & Accent
> - **Apple Action Blue** (`#0071e3`): Primary action fill and focus-signaling brand accent.
- **trade_off**: 多 brand 色 ↔ 单一 blue family（accessibility + recognition）
- **intent**: 让 user 视觉直觉知道"这是 action / link"——蓝色就是交互信号
- **avoid**:
  - 多 brand 色（破坏 single-signal）
  - 装饰 blue 使用（稀释 action 信号）

### decision: Near-black ink #1d1d1f (not pure black) for text

原 DESIGN.md 段落（auto-backfill）：
> Near-Black Ink** (`#1d1d1f`): Primary text and dark-fill control color on light canvases.
- **trade_off**: pure #000000（极致对比） ↔ 1.1% off-black（warmth）
- **intent**: 让 text 在 light surface 上有 micro-warmth——不冰冷
- **avoid**:
  - pure black text（破坏 warm subtlety）

### decision: Dark surface stepping (Graphite A/B/C/D - 4 step)

原 DESIGN.md 段落（auto-backfill）：
> Graphite Surface D** (`#2a2a2c`): Darkest elevated step used for separation in richer dark scenes.
- **trade_off**: 单 dark surface ↔ 4-step dark ladder
- **intent**: 让 dark 章节内部有层级（card / control / panel）但仍保持 chromatic 克制
- **avoid**:
  - 单 dark（无 hierarchy）
  - 大色差 step（破坏 subtlety）

## Typography

### decision: SF Pro Display + SF Pro Text 双 family，hierarchy via family role

原 DESIGN.md 段落（auto-backfill）：
> Helvetica, Arial, sans-serif`
> - **Text Family:** `SF Pro Text`, fallbacks `SF Pro Icons, Helvetica Neue, Helvetica, Arial, sans-serif`
> - **Usage Split:** Display family handles hero/product headlines and merchandising headings; Text family handles navigation, controls, labels, and dense commerce copy.
- **trade_off**: 单一 family（identity） ↔ 双 family（display vs text 分工）
- **intent**: 让 hero 用 Display，dense retail 用 Text——一套字体两种 reading 模式
- **avoid**:
  - SF Pro Text 用于 hero（破坏 display impact）
  - SF Pro Display 用于 dense retail（密度不对）

### decision: Display sizes 80px hero + tight tracking -1.2px

原 DESIGN.md 段落（auto-backfill）：
> Hierarchy
> | Role | Size | Weight | Line Height | Letter Spacing | Notes |
> |------|------|--------|-------------|----------------|-------|
> | Hero Display XL | 80px | 600 | 1.
- **trade_off**: 标准 hero 56-64 ↔ 80px billboard scale
- **intent**: 让 product launch 视觉上"巨大但克制"——大字号但 tight tracking
- **avoid**:
  - 大字号 + 正字距（loose advertising 感）
  - 小字号 hero（弱化 product launch）

### decision: 600 dominant emphasis weight, 700 selective, 300 sparingly

原 DESIGN.md 段落（auto-backfill）：
> Measured weight ladder:** 600 is the dominant emphasis weight; 700 appears selectively; 300 is used sparingly for contrast in larger lines.
- **trade_off**: weight ladder 多 ↔ 主用 600 + selective use of 700/300
- **intent**: 让 hierarchy 主要在 600，特殊 contrast 用 700 或 300
- **avoid**:
  - 全 700 bold（loud）
  - 全 300 light（弱化 authority）

## Components

### decision: Pill/capsule action family (18px to 980px radius)

原 DESIGN.md 段落（auto-backfill）：
> Pill/Capsule Action Family:** large capsule actions at `18px`-`56px` radii and extreme pill links at `980px`.
- **trade_off**: 矩形 button（serious） ↔ pill 渐变（soft authority）
- **intent**: 让 CTA 有 Apple 标志性的"软精确"——既不锐利也不全圆
- **avoid**:
  - 矩形 CTA（破坏 capsule signature）
  - 极端 pill（破坏 anchored 感）

### decision: Restraint depth — contrast and surface separation do most of layering work

原 DESIGN.md 段落（auto-backfill）：
> Depth is intentionally restrained. Apple favors tonal contrast, surface stepping, and compositional hierarchy over heavy shadow stacks.
- **trade_off**: 多 shadow elevation ladder ↔ contrast-led separation
- **intent**: 让 depth 来自 surface 颜色变化，不是 shadow 堆叠
- **avoid**:
  - 重 shadow stack（违反 restraint）
  - 完全无 elevation（缺 hierarchy）

### decision: Border-led containment in dense retail (vs heavy card ornamentation)

原 DESIGN.md 段落（auto-backfill）：
> Use border-led containment in dense retail contexts instead of heavy card ornamentation.
- **trade_off**: card 装饰（明确） ↔ border 包围（克制）
- **intent**: 让 retail/configurator 的 dense info 有 structure 但不占视觉重
- **avoid**:
  - 厚边框（视觉重）
  - 无边界（dense info 失结构）

### decision: Configurator option stacks + selectors + contextual pricing

原 DESIGN.md 段落（auto-backfill）：
> Depth is intentionally restrained. Apple favors tonal contrast, surface stepping, and compositional hierarchy over heavy shadow stacks.
- **trade_off**: 静态 product page ↔ interactive configurator
- **intent**: 让 buy-flow 是 progressive selection——chip + radio + summary
- **avoid**:
  - 长 form（破坏 progressive）

## Layout

### decision: 8px base + dense micro-steps (2/4/6/7/8/9/10/12/14/17/20)

原 DESIGN.md 段落（auto-backfill）：
> Typography is the stabilizer. SF Pro Display carries hero and merchandising hierarchy with compact line heights and controlled tracking, while SF Pro Text handles product metadata, navigation, filters, and dense selection UI. The typography stays understated, but the scale range is wide enough to support both billboard hero messaging and micro utility labels.
- **trade_off**: 严格 8 倍数 ↔ 含 micro-step
- **intent**: 让 padding 在严格 grid 上有 fine-grained 选择——retail 复杂 UI 需要
- **avoid**:
  - rigid 8 only（破坏 retail density）

### decision: Showcase pages central column / commerce pages multi-column

原 DESIGN.md 段落（auto-backfill）：
> > **Source Pages:** `https://www.apple.com/`, `https://www.apple.com/environment/`, `https://www.apple.com/store`, `https://www.apple.com/shop/buy-iphone/iphone-17-pro`, `https://www.apple.com/shop/accessories/all`
- **trade_off**: 一致 layout ↔ context-aware（showcase 大 column / commerce dense grid）
- **intent**: 让 layout 跟随 reading mode——hero 单 column / shopping 多 column
- **avoid**:
  - 强制单 layout（不适合 commerce）

### decision: Section transitions via surface change (not decorative dividers)

原 DESIGN.md 段落（auto-backfill）：
> Across the five analyzed pages, the rhythm is consistent but not monolithic. Marketing surfaces (homepage and Environment) use cinematic black-and-light chaptering, while commerce surfaces (Store and Shop flows) introduce tighter spacing, more utility controls, and denser card stacks without breaking the core brand grammar. The result is one system with two gears: showcase mode and transaction mode.
- **trade_off**: 显式 dividers（结构感） ↔ surface change（cinematic）
- **intent**: 让 section 切换像"场景切换"而非"页面分段"
- **avoid**:
  - 厚 dividers（破坏 cinematic）

## Voice / Brand-implicit

### decision: Voice = restrained product-first, hardware narrative

原 DESIGN.md 段落（auto-backfill）：
> Apple's web language is a precision editorial system that alternates between gallery-like calm and retail-density information blocks. The visual tone stays restrained: broad neutral canvases, quiet chrome, and product imagery given almost all of the expressive weight. The interface is engineered to disappear so hardware, materials, and finish options become the narrative foreground.
- **trade_off**: 营销 hyperbole ↔ product-spec restrained
- **intent**: 让 copy 像 product-launch keynote——claims 大但 tone 克制
- **avoid**:
  - 营销 superlatives
  - 过度技术 specs（破坏 narrative）

## Anti-patterns

- 不要 broad secondary accents 与 Apple Blue 竞争
- 不要重 shadow / glow / decorative gradient
- 不要混 fonts / loose tracking
- 不要单 radius 全 components（破坏 capsule/circle/pill 系统）
- 不要厚 borders / loud effects 在 commerce
- 不要消除 dark/light chapter rhythm
- 不要把 marketing 和 purchase 当独立 systems

---

## 抽取统计

- 显式 rationale: 13 条
- 推断 [inferred]: 0 条
- 9-section 覆盖：完整 dialect A，含特殊性（dual-mode showcase/commerce + section rhythm）
