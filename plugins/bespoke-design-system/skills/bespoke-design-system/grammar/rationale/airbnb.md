# Rationale — airbnb

> 三段式 rationale 抽取自 `source-design-systems/airbnb/DESIGN.md`. Dialect A —— travel marketplace + photography-driven。

## Visual Theme & Atmosphere

### decision: Pristine white canvas + full-bleed photography as hero element
- **trade_off**: 工程化 chrome ↔ photography-first（"interface 消失，让 listing 呼吸"）
- **intent**: 让 chrome 退后到 photo 后面——product = listing photos，UI 只是 frame
- **avoid**:
  - 装饰 chrome 与 photo 视觉竞争
  - 灰底（弱化 photo 质感）

### decision: Rausch coral-pink #ff385c as single-accent brand color
- **trade_off**: 多色 brand（动态） ↔ 单一 coral 锚点（极致 chromatic discipline）
- **intent**: 让 Rausch 成为"重大决定"的标志——Reserve / Search / Wishlist 是用户旅程的关键时刻
- **avoid**:
  - 装饰 Rausch 使用（稀释 commit-action 信号）
  - 多 chromatic 竞争 attention

### decision: 3D rendered category icons paired with typographic tabs
- **trade_off**: 平面 icon + 大字（标准） ↔ 3D 渲染插画 + tabs（跨 medium）
- **intent**: 让 categories（Homes/Experiences/Services）有 toy-like 触感——unusual 但 anchored
- **avoid**:
  - 平面 icon（过工具感）
  - 全 illustration（破坏 typographic backbone）

## Color

### decision: 90% of all text uses Ink Black #222222 (singular text token)
- **trade_off**: 多 text shade（hierarchy via gray） ↔ 单一 Ink Black + weight contrast
- **intent**: 让 chrome 极致简化——text 几乎不变色，hierarchy 靠 weight + size
- **avoid**:
  - 灰色 text 多 tier（与 photography-first 竞争）

### decision: Tier-color coding (Plus magenta / Luxe deep purple / Rausch standard)
- **trade_off**: 单一 brand color（一致） ↔ 产品 tier 专属色（差异化）
- **intent**: 让用户无需 read 标签就知道 tier 等级——color = price tier mapping
- **avoid**:
  - 多 brand 混用（破坏 tier 识别）

### decision: Brand gradient narrow use — only on wordmark + search button
- **trade_off**: 全 surface 渐变 ↔ 极窄"branded moment"（pill fill 或 logo only）
- **intent**: 让 gradient 是 occasional brand moment 而非系统 background
- **avoid**:
  - 大面积 gradient（破坏 photography-first）

## Typography

### decision: Airbnb Cereal VF — single family carries 8px to 28px
- **trade_off**: display + body 双 family（hierarchy via family） ↔ 单一 family (identity from family)
- **intent**: 让 brand identity 内置于 typeface 本身——所有 text 都是"Airbnb"的声音
- **avoid**:
  - 引入第二 family（破坏 single-voice）
  - 字号大幅跳跃（破坏 family integrity）

### decision: Body weight 500 (not 400) — "the new regular"
- **trade_off**: 标准 400 regular（轻） ↔ 500 medium（subtle confidence）
- **intent**: 每段 paragraph 有微微 confident texture——not loud, just deliberate
- **avoid**:
  - 400 regular（过 default）
  - 600+ in body（变 loud）

### decision: Negative tracking on display only (-0.18 to -0.44 at 20-28px), 0 at body
- **trade_off**: 全局 tight tracking ↔ display tight + body normal
- **intent**: 让 headlines feel chiseled, body 保持 reading comfort
- **avoid**:
  - body 也 negative（损可读）
  - display 也正字距（破坏 chiseled）

### decision: Tight line-height for headlines 1.18-1.25, generous for body 1.43
- **trade_off**: 一致 line-height ↔ display tight + body relaxed
- **intent**: 让 listing title 紧凑有力，property description 适合长读
- **avoid**:
  - body 紧凑（不适合阅读）

### decision: No all-caps except 8px superscript
- **trade_off**: 大写 emphasis ↔ sentence case + weight contrast
- **intent**: 大写让 chrome 喊叫——Airbnb 不喊叫
- **avoid**:
  - 大写 button labels（与 friendly 调性冲突）

## Components

### decision: Sticky booking panel with overlapping rounded card
- **trade_off**: 标准 form bottom ↔ overlapping card (visual hierarchy)
- **intent**: 让 booking panel 视觉上"important"——浮在 hero photo 上
- **avoid**:
  - inline form（视觉权重不够）

### decision: 4:3 / 16:9 photography with 14-20px corner rounding
- **trade_off**: full-bleed sharp（沉浸） ↔ rounded（friendly）
- **intent**: rounded photo 让 listing 像"卡片可拿"——而非"页面背景"
- **avoid**:
  - sharp 锐角（与 friendly 冲突）
  - 9999 pill（破坏 photo proportions）

### decision: Circular 50% icon buttons (back / share / favorite / arrows)
- **trade_off**: 矩形 icon button（标准） ↔ 圆形（floating 感）
- **intent**: 让 icon button 在 photo 上"浮动"——不抢 photo 视觉权重
- **avoid**:
  - 矩形 icon button（喧宾夺主）

## Layout

### decision: Hairline 1px #dddddd separators throughout
- **trade_off**: 厚 dividers（结构感） ↔ hairline 1px（whisper division）
- **intent**: 让 list items 有 subtle separation but 不打断 photo 视觉
- **avoid**:
  - 实色重 dividers
  - 完全无 separation（list 失去结构）

### decision: Sticky right-rail booking on desktop → bottom-anchored "Reserve" bar on mobile
- **trade_off**: 静态 booking ↔ sticky context-aware
- **intent**: 让 reserve action 永远 1-tap accessible
- **avoid**:
  - inline booking 按钮 lost in scroll

## Voice / Brand-implicit

### decision: Voice = warm + practical + travel-aspirational [inferred]
- **trade_off**: 冷峻 booking 机器（efficient） ↔ aspirational + warm
- **intent**: 让 marketing 文案像 friendly local recommending a place
- **avoid**:
  - 冷峻数据（破坏 aspirational）
  - 营销 hyperbole

## Anti-patterns

- 不要 chrome chromatic 装饰（与 photography-first 冲突）
- 不要 Rausch decorative 使用（稀释 key-action 信号）
- 不要全 surface gradient（破坏 photography 调性）
- 不要 body 用 weight 400（违反 500-as-regular）
- 不要 body 用 negative tracking（损可读）
- 不要大写 button labels（破坏 friendly 调性）
- 不要 sharp corner photos（与 friendly 冲突）
- 不要矩形 icon button on photo（视觉权重错）

---

## 抽取统计

- 显式 rationale: 12 条
- 推断 [inferred]: 1 条（Voice）
- 9-section 覆盖：完整 dialect A
