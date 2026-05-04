# Rationale — cohere

> 三段式 rationale 抽取自 `source-design-systems/cohere/DESIGN.md`。

## Visual Theme

### decision: enterprise polished command deck — black/white/cool-gray with extreme chromatic restraint

原 DESIGN.md 段落（auto-backfill）：
> Cohere's interface is a polished enterprise command deck — confident, clean, and designed to make AI feel like serious infrastructure rather than a consumer toy. The experience lives on a bright white canvas where content is organized into generously rounded cards (22px radius) that create an organic, cloud-like containment language. This is a site that speaks to CTOs and enterprise architects: professional without being cold, sophisticated without being intimidating.
- **trade_off**: 多色 brand（活力） ↔ 极致 monochrome（enterprise authority）
- **intent**: 让 AI 看起来是 serious infrastructure 不是 consumer toy
- **avoid**: 消费者级配色 / 多 chromatic / 装饰性 color

### decision: 22px signature border-radius (cloud-like containment)

原 DESIGN.md 段落（auto-backfill）：
> **22px Card System**
> - The 22px border-radius is Cohere's visual signature
> - All primary cards, images, and containers use this radius
> - Creates a cloud-like, organic softness that's distinctive from the typical 8–12px
- **trade_off**: 中等圆角（普适） ↔ 22px signature（独特识别）
- **intent**: 让 card radius 成为品牌识别——既不是 sharp engineering 也不是 friendly large
- **avoid**: 8/12/16 standard radius / 圆角缺失工程感

## Color

### decision: purple-violet only in photographic hero bands and gradient sections

原 DESIGN.md 段落（auto-backfill）：
> **Purple Hero Bands**
> - Full-width deep purple sections housing product showcases
> - Create dramatic visual breaks in the white page flow
> - Product screenshots float within the purple environment
- **trade_off**: 全 monochrome（极简） ↔ purple-only-in-photography（戏剧对比）
- **intent**: 限制 chromatic 到大幅 photography hero，让它出现时携带最大视觉重量
- **avoid**: 装饰性 purple / multi-section chromatic distribution

### decision: interactive blue (#1863dc) only on hover/focus states

原 DESIGN.md 段落（auto-backfill）：
> Color is used with extreme restraint — the interface is almost entirely black-and-white with cool gray borders (`#d9d9dd`, `#e5e7eb`). Purple-violet appears only in photographic hero bands, gradient sections, and the interactive blue (`#1863dc`) that signals hover and focus states. This chromatic restraint means that when color DOES appear — in product screenshots, enterprise photography, and the deep purple section — it carries maximum visual weight.
- **trade_off**: 静态 blue（清晰） ↔ 动态 blue（节俭）
- **intent**: blue 只在交互瞬间出现——hover/focus 时的"觉醒"信号
- **avoid**: 静态 blue 链接 / blue 装饰用法

## Typography

### decision: serif for declaration (CohereText) + sans for utility (Unica77)

原 DESIGN.md 段落（auto-backfill）：
> **Key Characteristics:**
> - Bright white canvas with cool gray containment borders
> - 22px signature border-radius — the distinctive "Cohere card" roundness
> - Dual custom typeface: CohereText (display serif) + Unica77 (body sans)
> - Enterprise-grade chromatic restraint: black, white, cool grays, minimal purple-blue accent
> - Deep purple/violet hero sections providing dramatic contrast
> - Ghost/transparent buttons that shift to blue on hover
> - Enterprise photography showing diverse real-world applications
> - CohereMono for code and technical labels with uppercase transforms
- **trade_off**: 单字体（一致） ↔ serif+sans（声音分工）
- **intent**: serif 给 headline 出版研究权威感；sans 处理功能性文字
- **avoid**: 单字体 flatness / 装饰 serif 滥用

### decision: negative tracking at scale (-1.2 to -1.44px @60-72px) + single body weight (400)

原 DESIGN.md 段落（auto-backfill）：
> The design language bridges two worlds with a dual-typeface system: CohereText, a custom display serif with tight tracking, gives headlines the gravitas of a technology manifesto, while Unica77 Cohere Web handles all body and UI text with geometric Swiss precision. This serif/sans pairing creates a "confident authority meets engineering clarity" personality that perfectly reflects an enterprise AI platform.
- **trade_off**: 多 weight ladder（hierarchy 丰富） ↔ 单 weight + size only（克制）
- **intent**: hierarchy 靠 size 和 spacing，不靠 weight 对比
- **avoid**: 700 bold body / 多 weight 噪声
