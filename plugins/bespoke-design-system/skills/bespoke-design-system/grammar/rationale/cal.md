# Rationale — cal

> 三段式 rationale 抽取自 `source-design-systems/cal/DESIGN.md`。

## Color

### decision: pure grayscale brand — no chromatic, boldness via monochrome

原 DESIGN.md 段落（auto-backfill）：
> **Key Characteristics:**
> - Purely grayscale brand palette — no brand colors, boldness through monochrome
> - Cal Sans custom geometric display font with extremely tight default letter-spacing
> - Multi-layered shadow system (11 definitions) with ring borders + diffused shadows + inset highlights
> - Cal Sans for headings, Inter for body — clean typographic division
> - Wide border-radius scale from 2px to 9999px (pill) — versatile rounding
> - White canvas with near-black (#242424) text — maximum contrast, zero decoration
> - Product screenshots as primary visual content — the scheduling UI sells itself
> - Built on Framer platform
- **trade_off**: 品牌色（识别） ↔ 全 grayscale（克制 + 普世性）
- **intent**: 让 boldness 不靠色彩而靠对比 + typography
- **avoid**: 装饰性 brand 色 / 多色干扰

### decision: warm near-black (#242424) for headings

原 DESIGN.md 段落（auto-backfill）：
> Cal.com's website is a masterclass in monochromatic restraint — a grayscale world where boldness comes not from color but from the sheer confidence of black text on white space. Inspired by Uber's minimal aesthetic, the palette is deliberately stripped of hue: near-black headings (`#242424`), mid-gray secondary text (`#898989`), and pure white surfaces. Color is treated as a foreign substance — when it appears (a rare blue link, a green trust badge), it feels like a controlled accent in an otherwise black-and-white photograph.
- **trade_off**: 纯黑（精度） ↔ 暖近黑（亲和）
- **intent**: 比 #000 略软的近黑保留权威感同时不冷
- **avoid**: 纯黑塑料 / 过暖灰

## Typography

### decision: Cal Sans display + Inter body — display 极紧字距 + 1.10 lh

原 DESIGN.md 段落（auto-backfill）：
> Cal Sans, the brand's custom geometric display typeface designed by Mark Davis, is the visual centerpiece. Letters are intentionally spaced extremely close at large sizes, creating dense, architectural headlines that feel like they're carved into the page. At 64px and 48px, Cal Sans headings sit at weight 600 with a tight 1.10 line-height — confident, compressed, and immediately recognizable. For body text, the system switches to Inter, providing "rock-solid" readability that complements Cal Sans's display personality. The typography pairing creates a clear division: Cal Sans speaks, Inter explains.
- **trade_off**: 单字体（一致） ↔ 双字体（display speak / body explain 分工）
- **intent**: Cal Sans 让 hero 像被刻在页面，Inter 让 body 像 rock-solid 阅读
- **avoid**: 单字体 hero 平淡 / 装饰 display 字体滥用

## Components & Layout

### decision: shadow-first depth (11 shadow definitions, ring border + soft diffused + inset)

原 DESIGN.md 段落（auto-backfill）：
> > Category: Productivity & SaaS
> > Open-source scheduling. Clean neutral UI, developer-oriented simplicity.
- **trade_off**: border-first（精度） ↔ shadow-first（柔软三维）
- **intent**: 在 monochrome 系统里靠 shadow 提供 depth，让 surface 微立体
- **avoid**: 1px border 切割 / shadow 单层缺乏 sophistication

### decision: wide radius scale 2-9999px (pill) — geometric versatility

原 DESIGN.md 段落（auto-backfill）：
> The elevation system is notably sophisticated for a minimal site — 11 shadow definitions create a nuanced depth hierarchy using multi-layered shadows that combine ring borders (`0px 0px 0px 1px`), soft diffused shadows, and inset highlights. This shadow-first approach to depth (rather than border-first) gives surfaces a subtle three-dimensionality that feels modern and polished. Built on Framer with a border-radius scale from 2px to 9999px (pill), Cal.com balances geometric precision with soft, rounded interactive elements.
- **trade_off**: 单一 radius 上限（一致） ↔ 全 spectrum（chrome 角色多样）
- **intent**: 不同 chrome 元素用不同 radius 表达不同 affordance
- **avoid**: 全 0 sharp / 全 8 中庸
