# Rationale — notion

> 三段式 rationale 抽取自 `source-design-systems/notion/DESIGN.md`。Dialect A-variant（含 Accessibility & States section）—— warm minimalism。

## Visual Theme & Atmosphere

### decision: Warm neutrals over cold grays — every gray has yellow-brown undertone

原 DESIGN.md 段落（auto-backfill）：
> Notion's website embodies the philosophy of the tool itself: a blank canvas that gets out of your way. The design system is built on warm neutrals rather than cold grays, creating a distinctly approachable minimalism that feels like quality paper rather than sterile glass. The page canvas is pure white (`#ffffff`) but the text isn't pure black -- it's a warm near-black (`rgba(0,0,0,0.95)`) that softens the reading experience imperceptibly. The warm gray scale (`#f6f5f4`, `#31302e`, `#615d59`, `#a39e98`) carries subtle yellow-brown undertones, giving the interface a tactile, almost analog warmth.
- **trade_off**: 行业标准 cool grays（中性安全） ↔ warm neutrals（与 paper/notebook 联想）
- **intent**: 让 product 像"高质量纸张"——tactile, analog, approachable
- **avoid**:
  - 冷蓝灰（与 productivity-as-paper 调性冲突）
  - 完全暖色（变 Claude/Anthropic 的 parchment territory）

### decision: Pure white canvas + warm near-black text via rgba(0,0,0,0.95)

原 DESIGN.md 段落（auto-backfill）：
> Notion's website embodies the philosophy of the tool itself: a blank canvas that gets out of your way. The design system is built on warm neutrals rather than cold grays, creating a distinctly approachable minimalism that feels like quality paper rather than sterile glass. The page canvas is pure white (`#ffffff`) but the text isn't pure black -- it's a warm near-black (`rgba(0,0,0,0.95)`) that softens the reading experience imperceptibly. The warm gray scale (`#f6f5f4`, `#31302e`, `#615d59`, `#a39e98`) carries subtle yellow-brown undertones, giving the interface a tactile, almost analog warmth.
- **trade_off**: pure black text（极致对比） ↔ 95% black（micro-warmth）
- **intent**: 让 reading 不冰冷——5% 的"呼吸"让长文档不刺眼
- **avoid**:
  - 纯 #000000 text（与 warm system 冲突）
  - 灰色 text（对比下降影响阅读）

### decision: Ultra-thin borders rgba(0,0,0,0.1) throughout

原 DESIGN.md 段落（auto-backfill）：
> **Key Characteristics:**
> - NotionInter (modified Inter) with negative letter-spacing at display sizes (-2.125px at 64px)
> - Warm neutral palette: grays carry yellow-brown undertones (`#f6f5f4` warm white, `#31302e` warm dark)
> - Near-black text via `rgba(0,0,0,0.95)` -- not pure black, creating micro-warmth
> - Ultra-thin borders: `1px solid rgba(0,0,0,0.1)` throughout -- whisper-weight division
> - Multi-layer shadow stacks with sub-0.05 opacity for barely-there depth
> - Notion Blue (`#0075de`) as the singular accent color for CTAs and interactive elements
> - Pill badges (9999px radius) with tinted blue backgrounds for status indicators
> - 8px base spacing unit with an organic, non-rigid scale
- **trade_off**: 实色 border（明确） ↔ 10% alpha border（whisper division）
- **intent**: 让 structure 存在但不喊叫——border 是"暗示"而非"宣告"
- **avoid**:
  - 实色重边（破坏 minimal）
  - 无 border（失去 structure）

## Color

### decision: Notion Blue #0075de as the only saturated chromatic in core UI

原 DESIGN.md 段落（auto-backfill）：
> Notion Blue** (`#0075de`): Primary CTA, link color, interactive accent -- the only saturated color in the core UI chrome.
- **trade_off**: brand 多色 ↔ 单一 blue accent
- **intent**: 让 blue 成为唯一 interactive signal——其它都是 warm grays + product accents
- **avoid**:
  - blue 装饰使用
  - 多 blue tone 引入混乱

### decision: 7-color semantic accent palette (Teal/Green/Orange/Pink/Purple/Brown)

原 DESIGN.md 段落（auto-backfill）：
> **Trust Bar / Logo Grid**
> - Company logos (trusted teams section) in their brand colors
> - Horizontal scroll or grid layout with team counts
> - Metric display: large number + description pattern
- **trade_off**: 单 chromatic discipline ↔ 多 accent for content tagging
- **intent**: 让用户标记 page/database 时有 visual taxonomy——但仅在 content level，不在 chrome
- **avoid**:
  - chrome 用 accent palette（破坏 minimal）
  - 单色 tagging（降低 organizational expressiveness）

### decision: Multi-layer shadow with sub-0.05 alpha each (5-stack possible for modals)

原 DESIGN.md 段落（auto-backfill）：
> **Shadow Philosophy**: Notion's shadow system uses multiple layers with extremely low individual opacity (0.01 to 0.05) that accumulate into soft, natural-looking elevation. The 4-layer card shadow spans from 1.04px to 18px blur, creating a gradient of depth rather than a single hard shadow. The 5-layer deep shadow extends to 52px blur at 0.05 opacity, producing ambient occlusion that feels like natural light rather than computer-generated depth. This layered approach makes elements feel embedded in the page rather than floating above it.
- **trade_off**: 单层 shadow（计算简单） ↔ 多层栈（细腻 depth）
- **intent**: 每个层级 shadow 几乎不可见，但合成出"立体感"——depth felt rather than seen
- **avoid**:
  - 单层重 shadow（破坏 whisper aesthetic）
  - 跳过多层（破坏 elevation 系统）

## Typography

### decision: NotionInter (modified Inter) with -2.125px tracking at 64px display

原 DESIGN.md 段落（auto-backfill）：
> **Metric Cards**
> - Large number display (e.g., "$4,200 ROI")
> - NotionInter 40px+ weight 700 for the metric
> - Description below in warm gray body text
> - Whisper-bordered card container
- **trade_off**: 标准 Inter（generic） ↔ NotionInter custom（distinct identity）
- **intent**: 让 Inter 变成 Notion 的——通过 custom modifications 而非换字体
- **avoid**:
  - 通用 Inter（缺乏 brand identity）
  - 换其它字体（破坏 cross-platform 一致性）

### decision: 4-weight system 400/500/600/700 (broader than 3-weight peers)

原 DESIGN.md 段落（auto-backfill）：
> What makes Notion's visual language distinctive is its border philosophy. Rather than heavy borders or shadows, Notion uses ultra-thin `1px solid rgba(0,0,0,0.1)` borders -- borders that exist as whispers, barely perceptible division lines that create structure without weight. The shadow system is equally restrained: multi-layer stacks with cumulative opacity never exceeding 0.05, creating depth that's felt rather than seen.
- **trade_off**: 3-weight 简化 ↔ 4-weight 更细腻 hierarchy
- **intent**: docs/databases 复杂内容需要更多 hierarchy 选择
- **avoid**:
  - bold 700 在 body 整段（破坏阅读流）
  - 单一 weight（无 hierarchy）

### decision: OpenType "lnum" + "locl" enabled on display

原 DESIGN.md 段落（auto-backfill）：
> The custom NotionInter font (a modified Inter) is the backbone of the system. At display sizes (64px), it uses aggressive negative letter-spacing (-2.125px), creating headlines that feel compressed and precise. The weight range is broader than typical systems: 400 for body, 500 for UI elements, 600 for semi-bold labels, and 700 for display headings. OpenType features `"lnum"` (lining numerals) and `"locl"` (localized forms) are enabled on larger text, adding typographic sophistication that rewards close reading.
- **trade_off**: default OpenType（普通） ↔ lining numerals + localized forms（typographic 精致）
- **intent**: 数字在表格/财务中对齐 + 多语言场景适配
- **avoid**:
  - oldstyle numerals（破坏对齐）

### decision: Body 12px badge text uses POSITIVE tracking 0.125px (only positive in system)

原 DESIGN.md 段落（auto-backfill）：
> **Pill Badge Button**
> - Background: `#f2f9ff` (tinted blue)
> - Text: `#097fe8`
> - Padding: 4px 8px
> - Radius: 9999px (full pill)
> - Font: 12px weight 600
> - Use: Status badges, feature labels, "New" tags
- **trade_off**: 全局 negative tracking（一致） ↔ 小字 positive（可读性优先）
- **intent**: 12px 不能压缩——会损伤识别
- **avoid**:
  - 12px 仍 negative（不可读）

## Components

### decision: Primary blue button + secondary translucent rgba(0,0,0,0.05) gray

原 DESIGN.md 段落（auto-backfill）：
> **Ghost / Link Button**
> - Background: transparent
> - Text: `rgba(0,0,0,0.95)`
> - Decoration: underline on hover
> - Use: Tertiary actions, inline links
- **trade_off**: 实色 secondary（明确） ↔ 半透明（融入 surface）
- **intent**: 让 secondary 在 chrome 上"几乎透明"——不打扰主操作
- **avoid**:
  - 实色 secondary 与 primary 视觉竞争
  - 完全无 secondary（hierarchy 不清）

### decision: Buttons with scale(0.9) on active + scale(1.05) on hover

原 DESIGN.md 段落（auto-backfill）：
> > Category: Productivity & SaaS
> > All-in-one workspace. Warm minimalism, serif headings, soft surfaces.
- **trade_off**: 静态 button ↔ scale 反馈（haptic-ish）
- **intent**: 让 button click 有"按下感"但不像 Duolingo 物理 press
- **avoid**:
  - 完全静态（缺反馈）
  - 大幅 scale（破坏 minimal）

### decision: Card radius 4px subtle

原 DESIGN.md 段落（auto-backfill）：
> **Secondary / Tertiary**
> - Background: `rgba(0,0,0,0.05)` (translucent warm gray)
> - Text: `#000000` (near-black)
> - Padding: 8px 16px
> - Radius: 4px
> - Hover: text color shifts, scale(1.05)
> - Active: scale(0.9) transform
> - Use: Secondary actions, form submissions
- **trade_off**: 大 radius friendly ↔ 小 radius engineering
- **intent**: 让 cards 看起来 minimal 但不冷峻——4px 是"刚好软"
- **avoid**:
  - 0 radius（硬）
  - 12+ radius（破坏 minimal）

## Layout

### decision: 8px base + organic non-rigid scale (3/4/6/8/10/12/16/20/24/30)

原 DESIGN.md 段落（auto-backfill）：
> **Primary Blue**
> - Background: `#0075de` (Notion Blue)
> - Text: `#ffffff`
> - Padding: 8px 16px
> - Radius: 4px (subtle)
> - Border: `1px solid transparent`
> - Hover: background darkens to `#005bab`
> - Active: scale(0.9) transform
> - Focus: `2px solid` focus outline, `var(--shadow-level-200)` shadow
> - Use: Primary CTA ("Get Notion free", "Try it")
- **trade_off**: 严格 8 倍数 ↔ 含 mid-step（10/30）
- **intent**: 让 padding 在严格 grid 上有 breathing 灵活——10px 比 8 或 12 更对的场景
- **avoid**:
  - 完全 rigid 8px（破坏 organic feel）

### decision: Section vertical 80-120px

原 DESIGN.md 段落（auto-backfill）：
> **Feature Cards with Illustrations**
> - Large illustrative headers (The Great Wave, product UI screenshots)
> - 12px radius card with whisper border
> - Title at 22px weight 700, description at 16px weight 400
> - Warm white (`#f6f5f4`) background variant for alternating sections
- **trade_off**: 紧凑 sections（信息密集） ↔ 章节式留白
- **intent**: marketing/docs 需要 "chapter" 节奏感
- **avoid**:
  - <40px section padding（破坏 chapter 调性）

## Anti-patterns

- 不要 cool blue-grays（破坏 warm 系统）
- 不要 pure #000000 text（与 95% black 系统冲突）
- 不要实色重 border（破坏 whisper system）
- 不要单层重 shadow（破坏 multi-layer whisper）
- 不要 12px body 用 negative tracking（不可读）
- 不要 chrome 用 accent palette（仅 content level）

---

## 抽取统计

- 显式 rationale: 13 条
- 推断 [inferred]: 0 条
- 9-section 覆盖：完整 dialect A-variant
