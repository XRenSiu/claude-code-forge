# Rationale — notion

> 三段式 rationale 抽取自 `source-design-systems/notion/DESIGN.md`。Dialect A-variant（含 Accessibility & States section）—— warm minimalism。

## Visual Theme & Atmosphere

### decision: Warm neutrals over cold grays — every gray has yellow-brown undertone
- **trade_off**: 行业标准 cool grays（中性安全） ↔ warm neutrals（与 paper/notebook 联想）
- **intent**: 让 product 像"高质量纸张"——tactile, analog, approachable
- **avoid**:
  - 冷蓝灰（与 productivity-as-paper 调性冲突）
  - 完全暖色（变 Claude/Anthropic 的 parchment territory）

### decision: Pure white canvas + warm near-black text via rgba(0,0,0,0.95)
- **trade_off**: pure black text（极致对比） ↔ 95% black（micro-warmth）
- **intent**: 让 reading 不冰冷——5% 的"呼吸"让长文档不刺眼
- **avoid**:
  - 纯 #000000 text（与 warm system 冲突）
  - 灰色 text（对比下降影响阅读）

### decision: Ultra-thin borders rgba(0,0,0,0.1) throughout
- **trade_off**: 实色 border（明确） ↔ 10% alpha border（whisper division）
- **intent**: 让 structure 存在但不喊叫——border 是"暗示"而非"宣告"
- **avoid**:
  - 实色重边（破坏 minimal）
  - 无 border（失去 structure）

## Color

### decision: Notion Blue #0075de as the only saturated chromatic in core UI
- **trade_off**: brand 多色 ↔ 单一 blue accent
- **intent**: 让 blue 成为唯一 interactive signal——其它都是 warm grays + product accents
- **avoid**:
  - blue 装饰使用
  - 多 blue tone 引入混乱

### decision: 7-color semantic accent palette (Teal/Green/Orange/Pink/Purple/Brown)
- **trade_off**: 单 chromatic discipline ↔ 多 accent for content tagging
- **intent**: 让用户标记 page/database 时有 visual taxonomy——但仅在 content level，不在 chrome
- **avoid**:
  - chrome 用 accent palette（破坏 minimal）
  - 单色 tagging（降低 organizational expressiveness）

### decision: Multi-layer shadow with sub-0.05 alpha each (5-stack possible for modals)
- **trade_off**: 单层 shadow（计算简单） ↔ 多层栈（细腻 depth）
- **intent**: 每个层级 shadow 几乎不可见，但合成出"立体感"——depth felt rather than seen
- **avoid**:
  - 单层重 shadow（破坏 whisper aesthetic）
  - 跳过多层（破坏 elevation 系统）

## Typography

### decision: NotionInter (modified Inter) with -2.125px tracking at 64px display
- **trade_off**: 标准 Inter（generic） ↔ NotionInter custom（distinct identity）
- **intent**: 让 Inter 变成 Notion 的——通过 custom modifications 而非换字体
- **avoid**:
  - 通用 Inter（缺乏 brand identity）
  - 换其它字体（破坏 cross-platform 一致性）

### decision: 4-weight system 400/500/600/700 (broader than 3-weight peers)
- **trade_off**: 3-weight 简化 ↔ 4-weight 更细腻 hierarchy
- **intent**: docs/databases 复杂内容需要更多 hierarchy 选择
- **avoid**:
  - bold 700 在 body 整段（破坏阅读流）
  - 单一 weight（无 hierarchy）

### decision: OpenType "lnum" + "locl" enabled on display
- **trade_off**: default OpenType（普通） ↔ lining numerals + localized forms（typographic 精致）
- **intent**: 数字在表格/财务中对齐 + 多语言场景适配
- **avoid**:
  - oldstyle numerals（破坏对齐）

### decision: Body 12px badge text uses POSITIVE tracking 0.125px (only positive in system)
- **trade_off**: 全局 negative tracking（一致） ↔ 小字 positive（可读性优先）
- **intent**: 12px 不能压缩——会损伤识别
- **avoid**:
  - 12px 仍 negative（不可读）

## Components

### decision: Primary blue button + secondary translucent rgba(0,0,0,0.05) gray
- **trade_off**: 实色 secondary（明确） ↔ 半透明（融入 surface）
- **intent**: 让 secondary 在 chrome 上"几乎透明"——不打扰主操作
- **avoid**:
  - 实色 secondary 与 primary 视觉竞争
  - 完全无 secondary（hierarchy 不清）

### decision: Buttons with scale(0.9) on active + scale(1.05) on hover
- **trade_off**: 静态 button ↔ scale 反馈（haptic-ish）
- **intent**: 让 button click 有"按下感"但不像 Duolingo 物理 press
- **avoid**:
  - 完全静态（缺反馈）
  - 大幅 scale（破坏 minimal）

### decision: Card radius 4px subtle
- **trade_off**: 大 radius friendly ↔ 小 radius engineering
- **intent**: 让 cards 看起来 minimal 但不冷峻——4px 是"刚好软"
- **avoid**:
  - 0 radius（硬）
  - 12+ radius（破坏 minimal）

## Layout

### decision: 8px base + organic non-rigid scale (3/4/6/8/10/12/16/20/24/30)
- **trade_off**: 严格 8 倍数 ↔ 含 mid-step（10/30）
- **intent**: 让 padding 在严格 grid 上有 breathing 灵活——10px 比 8 或 12 更对的场景
- **avoid**:
  - 完全 rigid 8px（破坏 organic feel）

### decision: Section vertical 80-120px
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
