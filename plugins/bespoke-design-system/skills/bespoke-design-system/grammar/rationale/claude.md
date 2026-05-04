# Rationale — claude (Anthropic)

> 三段式 rationale 抽取自 `source-design-systems/claude/DESIGN.md`。Dialect A —— literary salon aesthetic + parchment + serif。

## Visual Theme & Atmosphere

### decision: Parchment canvas #f5f4ed evoking premium paper, not screens

原 DESIGN.md 段落（auto-backfill）：
> Claude's interface is a literary salon reimagined as a product page — warm, unhurried, and quietly intellectual. The entire experience is built on a parchment-toned canvas (`#f5f4ed`) that deliberately evokes the feeling of high-quality paper rather than a digital surface. Where most AI product pages lean into cold, futuristic aesthetics, Claude's design radiates human warmth, as if the AI itself has good taste in interior design.
- **trade_off**: 标准 white canvas（行业默认） ↔ parchment cream（与 book/literary 联想）
- **intent**: 让 AI 工具看起来像"有品味的同伴" 而不是"powerful tool"——刻意去技术化
- **avoid**:
  - cold sterile glass（与 literary 调性冲突）
  - 过暖（变 vintage / nostalgic）

### decision: Custom Anthropic Serif for headlines (single weight 500)

原 DESIGN.md 段落（auto-backfill）：
> The signature move is the custom Anthropic Serif typeface — a medium-weight serif with generous proportions that gives every headline the gravitas of a book title. Combined with organic, hand-drawn-feeling illustrations in terracotta (`#c96442`), black, and muted green, the visual language says "thoughtful companion" rather than "powerful tool." The serif headlines breathe at tight-but-comfortable line-heights (1.10–1.30), creating a cadence that feels more like reading an essay than scanning a product page.
- **trade_off**: sans-serif tech default ↔ serif 文学权威
- **intent**: 让每个标题有 book-title gravitas——读起来像散文而非产品页
- **avoid**:
  - sans-serif 用于 headline（破坏 literary 调性）
  - serif weight 700+（破坏 single-weight consistency）

### decision: Exclusively warm neutrals — every gray has yellow-brown undertone

原 DESIGN.md 段落（auto-backfill）：
> **Organic Illustrations**
> - Hand-drawn-feeling vector illustrations in terracotta, black, and muted green
> - Abstract, conceptual rather than literal product diagrams
> - The primary visual personality — no other AI company uses this style
- **trade_off**: 中性灰阶 ↔ 全暖灰（chromatic discipline）
- **intent**: 让产品 feel "lived-in"——所有灰都互相协调
- **avoid**:
  - cool blue-grays anywhere
  - 混搭暖冷灰（破坏 cohesion）

## Color

### decision: Terracotta Brand #c96442 — earthy, deliberately un-tech

原 DESIGN.md 段落（auto-backfill）：
> **Brand Terracotta**
> - Background: Terracotta Brand (`#c96442`)
> - Text: Ivory (`#faf9f5`)
> - Radius: 8–12px
> - Shadow: ring-based (`#c96442 0px 0px 0px 0px, #c96442 0px 0px 0px 1px`)
> - The primary CTA — the only button with chromatic color
- **trade_off**: 蓝紫 tech default（专业但通用） ↔ terracotta（独特但反传统）
- **intent**: 让 brand 色 anti-tech——温暖、土感、deliberately not Silicon Valley
- **avoid**:
  - 蓝紫 brand（与 OpenAI/Mistral 等同质化）
  - 装饰使用 terracotta

### decision: #141413 near black with olive warmth — warmest "black" in tech

原 DESIGN.md 段落（auto-backfill）：
> What makes Claude's design truly distinctive is its warm neutral palette. Every gray has a yellow-brown undertone (`#5e5d59`, `#87867f`, `#4d4c48`) — there are no cool blue-grays anywhere. Borders are cream-tinted (`#f0eee6`, `#e8e6dc`), shadows use warm transparent blacks, and even the darkest surfaces (`#141413`, `#30302e`) carry a barely perceptible olive warmth. This chromatic consistency creates a space that feels lived-in and trustworthy.
- **trade_off**: pure #000000 ↔ olive-tinted near-black
- **intent**: 让 dark text 仍然在 warm system 内——不破坏整套色温
- **avoid**:
  - pure black（破坏 warm cohesion）
  - 太亮 dark gray（对比下降）

### decision: Focus Blue #3898ec — only cool color in entire system

原 DESIGN.md 段落（auto-backfill）：
> **Model Comparison Cards**
> - Opus 4.5, Sonnet 4.5, Haiku 4.5 presented in a clean card grid
> - Each model gets a bordered card with name, description, and capability badges
> - Border Warm (`#e8e6dc`) separation between items
- **trade_off**: 全暖 system 一致性 ↔ accessibility 需要 standard focus blue
- **intent**: 让 a11y 标准优先于 chromatic discipline——但仅限 focus ring
- **avoid**:
  - 暖色 focus（违反 a11y 共识）
  - cool 色其它地方（破坏暖系统）

## Typography

### decision: Anthropic Serif weight 500 ONLY for all headings

原 DESIGN.md 段落（auto-backfill）：
> **Dark Charcoal**
> - Background: Dark Surface (`#30302e`)
> - Text: Ivory (`#faf9f5`)
> - Padding: 0px 12px 0px 8px
> - Radius: comfortably rounded (8px)
> - Shadow: ring-based (`#30302e 0px 0px 0px 0px, ring 0px 0px 0px 1px`)
> - The inverted variant for dark-on-light emphasis
- **trade_off**: weight ladder（heading hierarchy via weight） ↔ single weight（hierarchy via size）
- **intent**: 让所有 heading 像同一作者写的——consistency as voice
- **avoid**:
  - 700 bold serif（破坏 single-weight）
  - 300 light serif（破坏 authority）

### decision: Anthropic Sans for UI, strict serif/sans split

原 DESIGN.md 段落（auto-backfill）：
> > Category: AI & LLM
> > Anthropic's AI assistant. Warm terracotta accent, clean editorial layout.
- **trade_off**: 单一 family（cohesive） ↔ serif/sans pair（functional split）
- **intent**: 让 reader 视觉直觉知道现在在读什么——content vs UI
- **avoid**:
  - sans-serif 用于 headline（破坏 literary）
  - serif 用于 button/label（破坏 functional clarity）

### decision: 1.60 line-height for body — significantly more generous than 1.4-1.5

原 DESIGN.md 段落（auto-backfill）：
> **White Surface**
> - Background: Pure White (`#ffffff`)
> - Text: Anthropic Near Black (`#141413`)
> - Padding: 8px 16px 8px 12px
> - Radius: generously rounded (12px)
> - Hover: shifts to secondary background color
> - Clean, elevated button for light surfaces
- **trade_off**: 紧凑 reading（信息密集） ↔ generous lanes（书的节奏）
- **intent**: 让 product 读起来像 book chapter 而非 dashboard
- **avoid**:
  - 1.4 以下（破坏 literary）
  - 1.7+ (loose unprofessional)

### decision: Headings tight 1.10-1.30 (serif needs more breathing room than sans)

原 DESIGN.md 段落（auto-backfill）：
> *Note: These are custom typefaces. For external implementations, Georgia serves as the serif substitute and system-ui/Inter as the sans substitute.*
- **trade_off**: 紧凑 sans ladder（机械） ↔ serif tight-but-not-claustrophobic
- **intent**: serif letterforms 需要 breathing room sans 不需要
- **avoid**:
  - 1.0 line-height for serif（破坏 letterform）

## Components

### decision: Ring shadow `0px 0px 0px 1px` — border-pretending-to-be-shadow

原 DESIGN.md 段落（auto-backfill）：
> **Shadow Philosophy**: Claude communicates depth through **warm-toned ring shadows** rather than traditional drop shadows. The signature `0px 0px 0px 1px` pattern creates a border-like halo that's softer than an actual border — it's a shadow pretending to be a border, or a border that's technically a shadow. When drop shadows do appear, they're extremely soft (0.05 opacity, 24px blur) — barely visible lifts that suggest floating rather than casting.
- **trade_off**: 标准 drop shadow（depth） ↔ ring shadow（border-like halo）
- **intent**: 让 button/card 在 hover/active 有"光晕"而非"阴影"——softer, warmer
- **avoid**:
  - 标准 drop shadow（cool, generic）
  - 实色 border 在交互态（缺乏 dynamism）

### decision: Generous border-radius 12-32px (no sharp corners)

原 DESIGN.md 段落（auto-backfill）：
> **Dark Primary**
> - Background: Anthropic Near Black (`#141413`)
> - Text: Warm Silver (`#b0aea5`)
> - Padding: 9.6px 16.8px
> - Radius: generously rounded (12px)
> - Border: thin solid Dark Surface (`1px solid #30302e`)
> - Used on dark theme surfaces
- **trade_off**: tech 4-8px（functional） ↔ literary 12-32px（approachable）
- **intent**: 让 UI 有"软纸"质感——manuscript margins 而非 dashboard cards
- **avoid**:
  - 锐角 4px（破坏 literary）
  - pill 9999（不够 anchored）

### decision: Light/Dark section alternation — chapter-like rhythm

原 DESIGN.md 段落（auto-backfill）：
> **Dark/Light Section Alternation**
> - The page alternates between Parchment light and Near Black dark sections
> - Creates a reading rhythm like chapters in a book
> - Each section feels like a distinct environment
- **trade_off**: 单一 surface（一致） ↔ alternation（章节感）
- **intent**: 让长 marketing page 有"翻页感"——不同 section 是不同 environment
- **avoid**:
  - 单 surface（视觉疲劳）
  - 多 surface（视觉混乱）

## Layout

### decision: 8px base + scale 3/4/6/8/10/12/16/20/24/30

原 DESIGN.md 段落（auto-backfill）：
> **Warm Sand (Secondary)**
> - Background: Warm Sand (`#e8e6dc`)
> - Text: Charcoal Warm (`#4d4c48`)
> - Padding: 0px 12px 0px 8px (asymmetric — icon-first layout)
> - Radius: comfortably rounded (8px)
> - Shadow: ring-based (`#e8e6dc 0px 0px 0px 0px, #d1cfc5 0px 0px 0px 1px`)
> - The workhorse button — warm, unassuming, clearly interactive
- **trade_off**: 严格 grid ↔ 含 mid-step 灵活
- **intent**: 让 padding 有"book typography"般的微调灵活
- **avoid**:
  - rigid 8 倍数（破坏 organic）

### decision: Section vertical 80-120px (estimated)

原 DESIGN.md 段落（auto-backfill）：
> **Key Characteristics:**
> - Warm parchment canvas (`#f5f4ed`) evoking premium paper, not screens
> - Custom Anthropic type family: Serif for headlines, Sans for UI, Mono for code
> - Terracotta brand accent (`#c96442`) — warm, earthy, deliberately un-tech
> - Exclusively warm-toned neutrals — every gray has a yellow-brown undertone
> - Organic, editorial illustrations replacing typical tech iconography
> - Ring-based shadow system (`0px 0px 0px 1px`) creating border-like depth without visible borders
> - Magazine-like pacing with generous section spacing and serif-driven hierarchy
- **trade_off**: dashboard density ↔ magazine spread breathing
- **intent**: 让每个 section 像 magazine spread——generous chapter pacing
- **avoid**:
  - 紧凑 dashboard 节奏（破坏 magazine spread 调性）
  - section padding < 64px（视觉密度过高）

## Voice / Brand-implicit

### decision: Voice = thoughtful companion, not powerful tool

原 DESIGN.md 段落（auto-backfill）：
> The signature move is the custom Anthropic Serif typeface — a medium-weight serif with generous proportions that gives every headline the gravitas of a book title. Combined with organic, hand-drawn-feeling illustrations in terracotta (`#c96442`), black, and muted green, the visual language says "thoughtful companion" rather than "powerful tool." The serif headlines breathe at tight-but-comfortable line-heights (1.10–1.30), creating a cadence that feels more like reading an essay than scanning a product page.
- **trade_off**: 力量营销（"the fastest" "most powerful"） ↔ 谦和但 capable
- **intent**: 让 AI 看起来像 "trusted advisor" 而非 "supreme intelligence"
- **avoid**:
  - hyperbole superlatives
  - 冷冰冰 technical specifications

## Anti-patterns

- 不要 cool blue-grays anywhere（破坏 warm system）
- 不要 bold weight 700+ on serif（破坏 single-weight）
- 不要 saturated colors beyond terracotta（破坏 muted palette）
- 不要 sharp corners < 6px（破坏 soft identity）
- 不要 heavy drop shadows（用 ring shadow）
- 不要 pure white #ffffff page bg（用 Parchment）
- 不要 geometric tech illustrations（用 hand-drawn organic）
- 不要 line-height < 1.40 for body
- 不要 mono for non-code prose
- 不要 sans for headlines

---

## 抽取统计

- 显式 rationale: 13 条
- 推断 [inferred]: 0 条
- 9-section 覆盖：完整 dialect A
