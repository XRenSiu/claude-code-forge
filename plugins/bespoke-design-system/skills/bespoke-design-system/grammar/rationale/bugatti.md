# Rationale — bugatti

> 三段式 rationale 抽取自 `source-design-systems/bugatti/DESIGN.md`。

## Visual Theme

### decision: cinema-black canvas + monochrome austerity (only black, white, and one gray)

原 DESIGN.md 段落（verbatim）：
> The other signature is **monochromatic austerity**. The entire homepage uses exactly three colors at rest: `#000000`, `#ffffff`, and `#999999` (mid gray for disabled/tertiary states). There is no accent, no brand blue, no hazard color, no commerce orange, no gradient wash. The designers have made a conscious decision that Bugatti's color system should be the car paint itself — the page is a black velvet display stand, and the only color that exists is whatever blue-on-black lacquer the hero vehicle happens to be wearing today.

- **trade_off**: brand 多色识别度（CTA 显眼） ↔ 让 product photography 独占色彩
- **intent**: 把网页变成黑天鹅绒 display stand，让车的颜色发声而不是 chrome 的颜色
- **avoid**: brand-blue accent / commerce-orange CTA / 任何 gradient wash / 多色 dashboard

## Color

### decision: pure #000000 not near-black — refusal of warm/charcoal compromise

原 DESIGN.md 段落（verbatim）：
> - **Velvet Black** (`#000000`): The entire canvas. Not near-black, not warm black — the pure HTML `#000`. Bugatti treats this as a display-stand surface, the way a jewelry brand treats a black velvet cloth.

- **trade_off**: 暖黑（reduce eye-strain，软） ↔ 纯黑（museum vitrine，冷）
- **intent**: 让 canvas 有"博物馆级 vitrine"的零反射感，不让暖黑稀释 monumentality
- **avoid**: `#0a0a0a` 等近黑（developer-tool 感）/ warm black（cozy 感）/ off-black（spotify 感）

## Typography

### decision: Bugatti Display at 288px — architectural scale as primary brand gesture

原 DESIGN.md 段落（verbatim）：
> The single most distinctive move in the entire system is **scale**: the `Bugatti Display` typeface runs at **288px** at hero moments. Two hundred and eighty-eight pixels. That is not a typo — the dembrandt sweep extracted a heading style rendered at an 18rem size, ALL CAPS, line-height 1.0, meant to be read the way you read a brand mark on the front of a Chiron: from across a showroom floor. At 288px the headline is no longer text, it is architecture.

- **trade_off**: 60-80px"网站合理"hero（reading） ↔ 288px architectural（sculpture）
- **intent**: 让 type 不再是 type 而是建筑物 — 视觉等价于车标的物理重量
- **avoid**: 标准 hero 48-72px / display weight bold / 多行 hero（必须单词或两词撑场）

## Typography

### decision: zero bold — scale (not weight) is the only hierarchy device

原 DESIGN.md 段落（verbatim）：
> - **There is no bold.** Every weight in the extracted tokens is regular (400). Bugatti does not use weight for hierarchy — it uses scale. When you need emphasis, make the type bigger, not heavier.

- **trade_off**: weight contrast（小空间灵活） ↔ scale-only（每次强调都需占空间）
- **intent**: 强迫每次强调消耗 layout space，迫使设计不再 cluttered
- **avoid**: 700 bold heading / 500 medium body / weight-driven hierarchy

## Components

### decision: rectangle / 6px / 9999px — three-radius scale, no in-between

原 DESIGN.md 段落（verbatim）：
> Three values. No `12px`, no `24px`, no `20px`. Bugatti's radius system is the most restrained of any site in this catalog — the brand has made an active decision that "slightly rounded rectangle" is a vulgar shape, and committed to either true rectangle or true pill.

- **trade_off**: 8/12/16 友好渐进尺度（标准 SaaS） ↔ 0/6/9999 三档极端（couture）
- **intent**: 让"略微圆角"成为禁忌 — 要么真正方，要么真正 pill，没有妥协形态
- **avoid**: 12px 通用 SaaS radius / 16px Material radius / sub-6 微调 radius

## Anti-Patterns

### decision: chrome must be silent — no shadows, no gradients, no glows

原 DESIGN.md 段落（verbatim）：
> **That is the entire depth system.** There are 1 shadows in the extracted token set (zero meaningful `box-shadow` values — just a placeholder). Bugatti does not use drop shadows. It does not use elevation rings. It does not use glowing focus states. Depth is implied by the 1px hairline of a border or the presence of a vignette gradient — nothing more.

- **trade_off**: 标准 elevation system（Material 化层级） ↔ 全平 + hairline border（chrome 不发声）
- **intent**: 让 chrome 给产品摄影让位 — 阴影/光晕都是从 product 上而非 chrome 上来
- **avoid**: drop shadow / glassmorphism / glow focus / multi-layer elevation
