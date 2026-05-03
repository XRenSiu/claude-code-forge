# Rationale — mintlify

> 三段式 rationale 抽取自 `source-design-systems/mintlify/DESIGN.md`。Dialect A-variant（含 Dark Mode + Accessibility & States）但实际拆解走 dialect A 主路径——documentation 平台特化。

## Visual Theme & Atmosphere

### decision: White canvas + atmospheric green-to-white gradient hero
- **trade_off**: 纯白克制 ↔ atmospheric gradient（让 documentation 不像办公文档，而像"思想之云"）
- **intent**: 让 documentation 有 ethereal intelligence 感——文档本身飘在噪音之上
- **avoid**:
  - 灰底文档（学院/官僚感）
  - 重渐变（破坏 reading-first 调性）

### decision: Brand Green #18E299 + reading-optimized neutrals
- **trade_off**: chromatic 主导 ↔ chromatic 锚点（CTA + focus + hover 仅）
- **intent**: 绿色暗示"清新、智能、可读"——但克制使用让 reading 不被打扰
- **avoid**:
  - 绿色装饰使用（大面积绿背景）
  - 多 chromatic 竞争 reading 注意力

## Color

### decision: Inter color binary — #0d0d0d (near-black) text + #18E299 green accent
- **trade_off**: 多色 hierarchy ↔ 二元 + 单 accent
- **intent**: 让 reader focus on prose，accent 只在交互瞬间出现
- **avoid**:
  - 纯黑 #000000（对比过硬，长读眼累）
  - 超饱和绿（与 reading-first 冲突）

### decision: 7-tier gray neutral scale (50/100/200/400/500/700/900)
- **trade_off**: 4-tier 简单 ↔ 7-tier 细分
- **intent**: documentation 需要 fine-grained type/border/disabled 区分
- **avoid**:
  - 单一灰阶（无法表达 syntax-highlight / annotation 层级）

## Typography

### decision: Inter primary + Geist Mono for code only
- **trade_off**: 单一 family ↔ display + body + mono 三 family
- **intent**: 让 prose 用 Inter 优化长读，code 用 mono 严格分隔——reader 视觉上"知道"现在在读什么
- **avoid**:
  - 单一 family（code 与 prose 难区分）
  - mono 用于 prose（密度过高）

### decision: Display tight tracking (-0.8 to -1.28px at 40-64px)
- **trade_off**: 普通 tracking ↔ 紧密 negative tracking
- **intent**: 让 documentation 标题"压缩"——像写好的 doc heading 而非营销 hero
- **avoid**:
  - 正字距（破坏文档调性）
  - body 也紧密（损害可读性）

### decision: 1.50 line-height for body (16-18px)
- **trade_off**: 1.4 紧凑 ↔ 1.5 generous
- **intent**: documentation 长读必需——line-height = reading comfort
- **avoid**:
  - 1.3 以下（学院教材紧迫感）
  - 1.7+（章节式松散，不适合 docs）

### decision: Three weights only (400/500/600), no bold 700
- **trade_off**: 5+ weight ladder ↔ 3-weight discipline
- **intent**: hierarchy via size + tracking, weight 仅 secondary 信号
- **avoid**:
  - bold body emphasis（破坏 reading flow）

## Components

### decision: Ultra-round corners (16px containers / 24px featured / 9999px buttons-pills)
- **trade_off**: 锐角工程感 ↔ 圆角友好感
- **intent**: 让 documentation 不像企业 SaaS——approachable 但 still rigorous
- **avoid**:
  - 4px 标准圆角（普通现代 SaaS）
  - 完全方角（学院刻板）

### decision: 5% opacity borders + barely-there shadows
- **trade_off**: 实色边框（明确） ↔ 5% alpha border + 0.03-0.06 shadow
- **intent**: 让 separation 极轻——白卡片在白底上的 division 是"暗示"而非"宣告"
- **avoid**:
  - 实色 border 重视觉
  - 重 box-shadow 夺注意力

### decision: Buttons green primary + neutral secondary, no decorative gradient
- **trade_off**: gradient button（dynamic） ↔ flat solid（calm）
- **intent**: 让 CTA 突出但不过度——documentation user 不需要被推销
- **avoid**:
  - 渐变 button（marketing 感）
  - decorative shadow 系统

## Layout

### decision: 8px base + generous section padding 48-96px
- **trade_off**: 紧凑 dashboard ↔ generous reading
- **intent**: 让 sections 有"章节"感——space between concepts
- **avoid**:
  - 紧凑 navigation-style spacing（破坏 reading rhythm）

### decision: White canvas only — no gray sections
- **trade_off**: 灰底 alternation ↔ pure white throughout
- **intent**: depth through borders + whitespace, not surface color shifts
- **avoid**:
  - 灰色 section 增加视觉噪音

## Voice / Brand-implicit

### decision: Voice = approachable + rigorous + developer-aware [inferred]
- **trade_off**: 专业冷峻 ↔ 友好但严谨
- **intent**: documentation user 是 developer——voice 应该 respects intelligence
- **avoid**:
  - 营销 hyperbole
  - 过度教学化（patronizing）

## Anti-patterns

- 不要 documentation 用纯 #000000（长读硬）
- 不要灰底 section（破坏 reading-first 调性）
- 不要 bold weight body emphasis（破坏 reading flow）
- 不要装饰渐变 button（marketing 感不对）
- 不要重 shadow（破坏 reading focus）
- 不要 mono for prose（密度过高）

---

## 抽取统计

- 显式 rationale: 11 条
- 推断 [inferred]: 1 条（Voice）
- 9-section 覆盖：完整 + dialect A-variant 的额外 section（dark_mode/accessibility）数据预留
