# Rationale — stripe

> 三段式 rationale 抽取自 `source-design-systems/stripe/DESIGN.md`. Dialect A —— fintech + weight 300 elegance + blue-tinted shadows。

## Visual Theme & Atmosphere

### decision: White canvas + Deep Navy `#061b31` headings + Stripe Purple `#533afd` accent
- **trade_off**: 蓝紫 fintech 通用 ↔ 独特蓝紫组合 + warm navy（不是 black）
- **intent**: 让 financial 不冰冷——deep navy + saturated purple 比 black + cold blue 更温暖
- **avoid**:
  - 纯黑 heading（与 warm fintech 冲突）
  - cold-blue accent（变成 enterprise software）

### decision: weight 300 as signature display weight
- **trade_off**: 标准 600-700 hero（command attention） ↔ weight 300（confident enough not to shout）
- **intent**: 让 headline whisper 而非 shout——lightness 是 luxury 的 signal
- **avoid**:
  - bold hero（与 luxury fintech 冲突）
  - 极轻 weight 100（破坏 readability）

### decision: Blue-tinted multi-layer shadows `rgba(50,50,93,0.25)` + `rgba(0,0,0,0.1)`
- **trade_off**: 标准 neutral shadow ↔ 蓝紫调 shadow（atmospheric depth）
- **intent**: 让 elevation 也带 brand color——shadow 是"twilight sky"而非 generic 灰
- **avoid**:
  - 纯灰 shadow（破坏 brand atmosphere）
  - 单层 shadow（破坏 parallax depth）

## Color

### decision: Stripe Purple #533afd — saturated blue-violet, not cold purple
- **trade_off**: 紫色装饰风险 ↔ saturated brand identity
- **intent**: 让 fintech 不只是"蓝色信任"——加入 violet 暗示 sophistication
- **avoid**:
  - 纯蓝 brand（generic fintech）
  - 装饰 purple（破坏 brand discipline）

### decision: Deep Navy #061b31 for headings (not black)
- **trade_off**: pure black heading（极致对比） ↔ deep navy（warm + financial-grade）
- **intent**: 让 heading 与 brand purple 共生——navy 是 purple 的"沉稳基础"
- **avoid**:
  - pure black（破坏 navy-purple harmony）

### decision: 5-shade purple ladder (Hover/Deep/Light/Mid + primary)
- **trade_off**: 单一 purple ↔ multi-state ladder
- **intent**: 让 interactive states 都有专属 purple 状态——hover/active/selected/disabled
- **avoid**:
  - 单 purple + opacity（破坏 ladder discipline）

### decision: Ruby + Magenta accents — for gradient/decoration only, not interactive
- **trade_off**: 多 brand 色 interactive ↔ ruby/magenta 仅装饰
- **intent**: 让 gradient hero 装饰丰富，但 interactive 锚点仍清晰单一（purple）
- **avoid**:
  - ruby/magenta 用于 button（破坏 single-cta-color）

## Typography

### decision: sohne-var with `"ss01"` enabled globally
- **trade_off**: 默认 sohne-var（generic） ↔ `ss01` stylistic set（distinct alternates）
- **intent**: 让所有 text 都是 Stripe 的——通过 OpenType 而非换字体
- **avoid**:
  - 跳过 ss01（变 generic sohne）

### decision: Weight 300 default for headings AND body
- **trade_off**: 不同 weight for hierarchy ↔ uniform 300 + size hierarchy
- **intent**: 让 lightness 成为 brand voice——所有文字都 whisper
- **avoid**:
  - 600-700 任何尺寸（破坏 luxury whisper）

### decision: Negative letter-spacing aggressive at display (-1.4 at 56px)
- **trade_off**: open tracking（airy） ↔ tight tracking（compressed engineering）
- **intent**: 让大字号显得"minified for production"——code-like compression
- **avoid**:
  - 正字距 display（破坏 engineered 感）

### decision: `"tnum"` for tabular numbers in financial data
- **trade_off**: 默认 numerals（行内一致） ↔ tnum（tabular alignment for data）
- **intent**: 让 financial display 数字对齐——expected fintech standard
- **avoid**:
  - oldstyle numerals in tables（破坏对齐）

### decision: Conservative border radius 4-8px — no pill, no large rounding
- **trade_off**: friendly soft radius ↔ conservative engineering radius
- **intent**: 让 fintech 看起来"engineering-trustworthy"——soft 但 not playful
- **avoid**:
  - pill button（破坏 fintech professionalism）
  - 0 radius（破坏 micro-warmth）

## Components

### decision: Multi-layer card shadow with negative spread
- **trade_off**: 单层 shadow（简单） ↔ 4-layer stack with negative spread
- **intent**: 让 card 有 parallax depth——深层蓝紫远 + 浅层黑近，sound dimensional
- **avoid**:
  - 单层 shadow（缺 parallax）
  - positive spread（shadow 散开破坏 verticality）

### decision: Dashed borders for placeholder/drop zones
- **trade_off**: 实线 border default ↔ dashed for "open/incomplete" semantic
- **intent**: 让 user 视觉知道"这里可放置"——不需要 explanation
- **avoid**:
  - 实线 placeholder（破坏 affordance）

### decision: Brand Dark `#1c1e54` sections for immersive moments
- **trade_off**: 全 white surface ↔ dark brand sections alternation
- **intent**: 让 narrative 有 immersive 章节——marketing rhythm
- **avoid**:
  - 单一 white surface（视觉单调）
  - black sections（与 navy-purple system 冲突）

## Layout

### decision: 8px base + dense small-end (4/6/8/10/11/12 - every 2px)
- **trade_off**: 严格 8 倍数 ↔ 含 mid-step micro 增量
- **intent**: financial UI 需要 fine-grained alignment——chart annotations / table cells
- **avoid**:
  - rigid 8-only（破坏 financial precision）

### decision: Dense data + generous chrome
- **trade_off**: 全密集（信息超载） ↔ 全松散（信息不足）
- **intent**: 让 data tables/charts tight，外围 chrome breathing——controlled density
- **avoid**:
  - 全 dense（窒息）
  - 全 generous（财务数据散乱）

## Voice / Brand-implicit

### decision: Voice = engineering luxury + financial-grade restraint
- **trade_off**: 营销 friendly fintech ↔ engineered restraint
- **intent**: 让 copy 像"engineering paper but published as luxury magazine"
- **avoid**:
  - 营销 bro tone
  - 过度 jargon

## Anti-patterns

- 不要 weight 600-700 sohne-var headlines（破坏 weight-300 signature）
- 不要 large radius / pill 在 cards/buttons（破坏 conservative）
- 不要 neutral gray shadows（必须 blue-tinted）
- 不要跳过 ss01（破坏 brand typography）
- 不要 pure black headings（必须 deep navy）
- 不要 ruby/magenta interactive use
- 不要 positive tracking display
- 不要 ruby/magenta 用于 button/link

---

## 抽取统计

- 显式 rationale: 13 条
- 推断 [inferred]: 0 条
- 9-section 覆盖：完整 dialect A
- 极特殊：weight 300 + blue-tinted shadow + ss01 是 Stripe 的不可复制三件套
