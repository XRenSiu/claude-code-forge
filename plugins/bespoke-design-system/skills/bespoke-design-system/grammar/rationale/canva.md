# Rationale — canva

> 三段式 rationale 抽取自 `source-design-systems/canva/DESIGN.md`。

## Visual Theme

### decision: friendly face of design tools — invite-not-intimidate (vs Adobe authority)

原 DESIGN.md 段落（auto-backfill）：
> > Category: Design & Creative
> > Visual creation platform. Vivid purple-blue gradient, generous spacing, friendly geometry.
- **trade_off**: 专业 authority（gravitas） ↔ 友好邀请（accessibility）
- **intent**: 让设计工具看起来人人可用，不是专业人士专属
- **avoid**: 严苛 chrome / 黑底冷感 / 工程师感

### decision: signature purple-to-blue gradient (#7d2ae8 → #00c4cc) for brand & magic moments

原 DESIGN.md 段落（auto-backfill）：
> Canva is the friendly face of design tools — the brand makes a point of looking inviting where Adobe looks intimidating. The page is built on a clean white canvas (`#ffffff`) with a signature **purple-to-blue gradient** (`#7d2ae8` → `#00c4cc`) used in the brand mark, hero buttons, and Pro/Magic moments. Surfaces are generously padded, edges are gently rounded (8–16px), and shadows are soft and cool-toned.
- **trade_off**: 单色品牌（一致） ↔ gradient（mood + 转化感）
- **intent**: 让 Pro / Magic 时刻有 transformative 视觉信号
- **avoid**: 装饰性 gradient / 多 gradient 竞争 / 动态 gradient（保持静态）

## Color & Components

### decision: weight contrast over color — 800 hero / 700 section / 400 body

原 DESIGN.md 段落（auto-backfill）：
> **Primary (Gradient)**
> - Background: `linear-gradient(135deg, #7d2ae8, #00c4cc)`
> - Text: `#ffffff`
> - Padding: 12px 20px
> - Radius: 8px
> - Shadow: `0 2px 8px rgba(125, 42, 232, 0.2)`
> - Hover: shadow grows to `0 4px 14px rgba(125, 42, 232, 0.3)`
> - Use: hero CTAs, "Try Canva Pro"
- **trade_off**: 多色 hierarchy ↔ weight ladder hierarchy
- **intent**: 在多色 brand 之外让 typography weight 担纲层级
- **avoid**: 颜色 + weight 双重强调

### decision: 12-20px radii everywhere; 9999px pills for chips/tags

原 DESIGN.md 段落（auto-backfill）：
> **Key Characteristics:**
> - White canvas with a violet-to-cyan gradient (`#7d2ae8` → `#00c4cc`)
> - Canva Sans (rounded geometric) for everything; weight contrast over color
> - 12–20px radii everywhere; 9999px pills for chips and tags
> - Soft cool-toned shadows that grow on hover
> - Filled rounded iconography — never outlined
> - Vibrant secondary palette (coral, mint, tangerine) for category tags
> - Pro/Magic moments lit by a static gradient — no animation
- **trade_off**: 严苛 geometry（精度） ↔ 友好 radius（亲和）
- **intent**: 让所有 chrome 友好可亲，不刻意工程化
- **avoid**: 直角 chrome / 8px 以下小圆角

## Typography

### decision: Canva Sans — rounded geometric for everything (one family)

原 DESIGN.md 段落（auto-backfill）：
> Typography uses **Canva Sans** (a custom geometric sans) for chrome and prose, with rounded letterforms that share DNA with brands like Airbnb and Asana. Weight contrast does the heavy lifting — 800 for hero display, 700 for section heads, 400 for body — while size hierarchy is more compressed than typical product brands so cards and templates read at a glance.
- **trade_off**: 多字体（声音分工） ↔ 单 Canva Sans（友好统一）
- **intent**: 让一个 family 通过 weight 完成所有 hierarchy
- **avoid**: 多字体复杂度 / 装饰 serif 在 friendly tool 上的违和
