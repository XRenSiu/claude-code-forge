# Rationale — airbnb

> 三段式 rationale 抽取自 `source-design-systems/airbnb/DESIGN.md`. Dialect A —— travel marketplace + photography-driven。

## Visual Theme & Atmosphere

### decision: Pristine white canvas + full-bleed photography as hero element

原 DESIGN.md 段落（auto-backfill）：
> **Guest Favorite Award Lockup** (featured prominently on high-rated listing detail pages)
> - Centered rating number rendered at 44–56px 700-weight
> - Two hand-drawn laurel-wreath SVG illustrations flanking left and right at ~48px tall
> - Below: "Guest Favorite" label at 12px 700 uppercase with `0.32px` tracking, and a short sub-label at 14px 500 Ash Gray
> - Full-width block, no container border — sits directly on white canvas
- **trade_off**: 工程化 chrome ↔ photography-first（"interface 消失，让 listing 呼吸"）
- **intent**: 让 chrome 退后到 photo 后面——product = listing photos，UI 只是 frame
- **avoid**:
  - 装饰 chrome 与 photo 视觉竞争
  - 灰底（弱化 photo 质感）

### decision: Rausch coral-pink #ff385c as single-accent brand color

原 DESIGN.md 段落（auto-backfill）：
> ```
> linear-gradient(90deg, #ff385c 0%, #e00b41 50%, #92174d 100%)
> ```
- **trade_off**: 多色 brand（动态） ↔ 单一 coral 锚点（极致 chromatic discipline）
- **intent**: 让 Rausch 成为"重大决定"的标志——Reserve / Search / Wishlist 是用户旅程的关键时刻
- **avoid**:
  - 装饰 Rausch 使用（稀释 commit-action 信号）
  - 多 chromatic 竞争 attention

### decision: 3D rendered category icons paired with typographic tabs

原 DESIGN.md 段落（auto-backfill）：
> **Top Nav (Desktop)**
> - Height: ~80px
> - Background: `#ffffff`
> - Left: Airbnb wordmark+logo lockup in Rausch (102×32px)
> - Center: tri-tab category picker (Homes / Experiences / Services) with 36–48px 3D icons stacked above 16px 500 labels; active tab has a 2px Ink Black underline
> - Right: "Become a host" text link, then 32px circular globe (language), then 36px hamburger avatar menu
> - Border-bottom: 1px solid Hairline Gray `#dddddd`
- **trade_off**: 平面 icon + 大字（标准） ↔ 3D 渲染插画 + tabs（跨 medium）
- **intent**: 让 categories（Homes/Experiences/Services）有 toy-like 触感——unusual 但 anchored
- **avoid**:
  - 平面 icon（过工具感）
  - 全 illustration（破坏 typographic backbone）

## Color

### decision: 90% of all text uses Ink Black #222222 (singular text token)

原 DESIGN.md 段落（auto-backfill）：
> **Date Picker**
> - Calendar grid: 7-column layout, circular `50%` day cells 40–44px wide
> - Selected range: Ink Black `#222222` background with white numerals
> - Start/end anchors: larger filled circles; middle dates use Soft Cloud `#f7f7f7` tint
- **trade_off**: 多 text shade（hierarchy via gray） ↔ 单一 Ink Black + weight contrast
- **intent**: 让 chrome 极致简化——text 几乎不变色，hierarchy 靠 weight + size
- **avoid**:
  - 灰色 text 多 tier（与 photography-first 竞争）

### decision: Tier-color coding (Plus magenta / Luxe deep purple / Rausch standard)

原 DESIGN.md 段落（auto-backfill）：
> **Search Bar** (primary home page)
> - Background: `#ffffff`
> - Border: 1px solid Hairline Gray `#dddddd` wrapping all three segments (Where / When / Who)
> - Radius: 32px (full pill)
> - Shadow: `rgba(0, 0, 0, 0.04) 0 2px 6px 0` — subtle floating feel
> - Structure: three segments divided by thin vertical dividers, each segment has a 12px 500 label above a 14px 500 placeholder
> - Submit: Rausch circular icon button at the right edge, 48px diameter
- **trade_off**: 单一 brand color（一致） ↔ 产品 tier 专属色（差异化）
- **intent**: 让用户无需 read 标签就知道 tier 等级——color = price tier mapping
- **avoid**:
  - 多 brand 混用（破坏 tier 识别）

### decision: Brand gradient narrow use — only on wordmark + search button

原 DESIGN.md 段落（auto-backfill）：
> This coral → magenta sweep is the "branded moment" — never used as a full surface, only as a narrow pill fill or logo treatment.
- **trade_off**: 全 surface 渐变 ↔ 极窄"branded moment"（pill fill 或 logo only）
- **intent**: 让 gradient 是 occasional brand moment 而非系统 background
- **avoid**:
  - 大面积 gradient（破坏 photography-first）

## Typography

### decision: Airbnb Cereal VF — single family carries 8px to 28px

原 DESIGN.md 段落（auto-backfill）：
> **Pill Tab Button** (category selector "Homes / Experiences / Services")
> - Background: transparent
> - Text: Ink Black `#222222`, Airbnb Cereal 500, 16px
> - Padding: 8px 14px
> - Active state: 2px Ink Black underline beneath the label
> - Paired with a 36–48px 3D-rendered illustrated icon above the label
- **trade_off**: display + body 双 family（hierarchy via family） ↔ 单一 family (identity from family)
- **intent**: 让 brand identity 内置于 typeface 本身——所有 text 都是"Airbnb"的声音
- **avoid**:
  - 引入第二 family（破坏 single-voice）
  - 字号大幅跳跃（破坏 family integrity）

### decision: Body weight 500 (not 400) — "the new regular"

原 DESIGN.md 段落（auto-backfill）：
> Weights observed in the extracted tokens: 500, 600, 700. No 400-regular — the system's "body" weight is 500, which gives every block of text a subtle extra density that reads as confident and deliberate.
- **trade_off**: 标准 400 regular（轻） ↔ 500 medium（subtle confidence）
- **intent**: 每段 paragraph 有微微 confident texture——not loud, just deliberate
- **avoid**:
  - 400 regular（过 default）
  - 600+ in body（变 loud）

### decision: Negative tracking on display only (-0.18 to -0.44 at 20-28px), 0 at body

原 DESIGN.md 段落（auto-backfill）：
> What makes the system unmistakably Airbnb is how much *faith* it places in content. Property photos are displayed at hero scale, 4:3 with edge-to-edge radius treatment. Category switching happens through a tri-tab picker (Homes / Experiences / Services) that uses 3D rendered illustrated icons (a pitched-roof house, a hot-air balloon, a service bell) — physical, tactile, almost toy-like — paired with crisp `Airbnb Cereal VF` labels. This is the rare consumer product where 3D renders and purely typographic UI coexist without tension.
- **trade_off**: 全局 tight tracking ↔ display tight + body normal
- **intent**: 让 headlines feel chiseled, body 保持 reading comfort
- **avoid**:
  - body 也 negative（损可读）
  - display 也正字距（破坏 chiseled）

### decision: Tight line-height for headlines 1.18-1.25, generous for body 1.43

原 DESIGN.md 段落（auto-backfill）：
> OpenType features: `salt` (stylistic alternates) is used on the compact 11px and 14px 600-weight labels — likely for tighter numerals and special-character shaping. No ligature or fractional-numeral features observed.
- **trade_off**: 一致 line-height ↔ display tight + body relaxed
- **intent**: 让 listing title 紧凑有力，property description 适合长读
- **avoid**:
  - body 紧凑（不适合阅读）

### decision: No all-caps except 8px superscript

原 DESIGN.md 段落（auto-backfill）：
> **Primary CTA** ("Reserve", "Search", "Add dates")
> - Background: Rausch `#ff385c`
> - Text: Canvas White `#ffffff`, Airbnb Cereal 500, 16px
> - Padding: ~14px vertical, 24px horizontal
> - Radius: 8px (rectangular) or 50% (circular icon variant)
> - Border: none
> - Active/pressed: `transform: scale(0.92)` plus a 2px `#222222` focus ring at `0 0 0 2px`
- **trade_off**: 大写 emphasis ↔ sentence case + weight contrast
- **intent**: 大写让 chrome 喊叫——Airbnb 不喊叫
- **avoid**:
  - 大写 button labels（与 friendly 调性冲突）

## Components

### decision: Sticky booking panel with overlapping rounded card

原 DESIGN.md 段落（auto-backfill）：
> **Detail Page Booking Panel** (sticky right rail on room/experience pages)
> - Background: `#ffffff`
> - Radius: 14–20px
> - Border: 1px solid Hairline Gray `#dddddd`
> - Shadow: `rgba(0, 0, 0, 0.02) 0 0 0 1px, rgba(0, 0, 0, 0.04) 0 2px 6px 0, rgba(0, 0, 0, 0.1) 0 4px 8px 0` — a stacked three-layer subtle elevation
> - Padding: 24px
> - Width: ~370px, pinned 120–140px below the viewport top
> - Content: price headline → date picker → guest dropdown → primary CTA → "You won't be charged yet" footnote
- **trade_off**: 标准 form bottom ↔ overlapping card (visual hierarchy)
- **intent**: 让 booking panel 视觉上"important"——浮在 hero photo 上
- **avoid**:
  - inline form（视觉权重不够）

### decision: 4:3 / 16:9 photography with 14-20px corner rounding

原 DESIGN.md 段落（auto-backfill）：
> Airbnb's 2026 design feels like a travel magazine that happens to be an app — pristine white canvases give way to full-bleed photography, and the interface itself disappears so the listings can breathe. The signature Rausch coral-pink (`#ff385c`) is used sparingly but unmistakably: search CTA, active tab indicator, primary action button, the occasional price or wishlist heart. Everything else is a disciplined grayscale, with `#222222` carrying almost every line of text.
- **trade_off**: full-bleed sharp（沉浸） ↔ rounded（friendly）
- **intent**: rounded photo 让 listing 像"卡片可拿"——而非"页面背景"
- **avoid**:
  - sharp 锐角（与 friendly 冲突）
  - 9999 pill（破坏 photo proportions）

### decision: Circular 50% icon buttons (back / share / favorite / arrows)

原 DESIGN.md 段落（auto-backfill）：
> **Icon-Only Circular Button** (back arrow, share, favorite, carousel controls)
> - Background: `#f2f2f2` (slightly off-white) or white with 1px translucent black border
> - Icon: `#222222` outline stroke, 16–20px
> - Size: 32–44px diameter
> - Radius: 50%
> - Active/pressed: `transform: scale(0.92)`; subtle 4px white ring `0 0 0 4px rgb(255,255,255)` to separate from colorful photography backgrounds
- **trade_off**: 矩形 icon button（标准） ↔ 圆形（floating 感）
- **intent**: 让 icon button 在 photo 上"浮动"——不抢 photo 视觉权重
- **avoid**:
  - 矩形 icon button（喧宾夺主）

## Layout

### decision: Hairline 1px #dddddd separators throughout

原 DESIGN.md 段落（auto-backfill）：
> **Secondary Button** ("Become a host", outlined tertiary actions)
> - Background: `#ffffff`
> - Text: Ink Black `#222222`, Airbnb Cereal 500, 14–16px
> - Padding: 10px 16px
> - Radius: 20px (pill) or 8px (rectangular)
> - Border: 1px solid Hairline Gray `#dddddd`
- **trade_off**: 厚 dividers（结构感） ↔ hairline 1px（whisper division）
- **intent**: 让 list items 有 subtle separation but 不打断 photo 视觉
- **avoid**:
  - 实色重 dividers
  - 完全无 separation（list 失去结构）

### decision: Sticky right-rail booking on desktop → bottom-anchored "Reserve" bar on mobile

原 DESIGN.md 段落（auto-backfill）：
> The newest surface is the **Experiences** product line — same chrome, but richer card density, more photography, and a center-anchored booking panel with sticky right-rail pricing. Listing detail pages (both rooms and experiences) follow a tight template: full-bleed hero image grid → overlapping rounded booking card (sticky on scroll) → amenities → reviews (Guest Favorite awards use a big centered `4.81` rating with a laurel-wreath lockup) → map → host profile → disclosures. The rhythm is consistent whether you're booking a room or a yacht tour.
- **trade_off**: 静态 booking ↔ sticky context-aware
- **intent**: 让 reserve action 永远 1-tap accessible
- **avoid**:
  - inline booking 按钮 lost in scroll

## Voice / Brand-implicit

### decision: Voice = warm + practical + travel-aspirational [inferred]

原 DESIGN.md 段落（auto-backfill）：
> > Category: E-Commerce & Retail
> > Travel marketplace. Warm coral accent, photography-driven, rounded UI.
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
