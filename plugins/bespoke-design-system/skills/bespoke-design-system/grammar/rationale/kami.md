# Rationale — kami

> 三段式 rationale 抽取自 `source-design-systems/kami/DESIGN.md`。

## Visual Theme

### decision: warm parchment canvas (#f5f4ed) — page is paper, not UI

原 DESIGN.md 段落（verbatim）：
> kami compresses into one sentence: **warm parchment canvas, ink-blue accent, serif carries hierarchy, no cool grays, no hard shadows.** It is not a UI framework — it is a constraint system for the page, designed to keep deliverables stable, clear, and unmistakably *printed*.

- **trade_off**: UI framework 通用感（widget rich）↔ paper constraint system（print fidelity）
- **intent**: 让产物读起来是"高质量印刷"而非"现代 app UI"
- **avoid**: pure white page / cool gray surface / 圆润大圆角 widget 感

## Color

### decision: single chromatic accent (ink blue #1B365D), ≤5% surface area — "more than that turns into ornament"

原 DESIGN.md 段落（verbatim）：
> - **Ink Blue** (`#1B365D`): The only chromatic color. CTAs, section numbers, link text on light surfaces, the left rule on a section title or quote, the active state of a switcher, the W500 metric value.
>
> > Rule: ink-blue covers ≤ **5% of document surface area**. More than that turns into ornament and the restraint collapses.

- **trade_off**: 多 brand color expressive（rich）↔ 单 ink-blue ≤5% surface（restraint）
- **intent**: 让 ink-blue 始终保持"标点"力度，超过 5% 就退化为装饰
- **avoid**: brand-blue 大色块 / 第二 accent 色 / gradient color wash / orange/red heat color

## Typography

### decision: serif-led hierarchy at single weight (500) — no bold, no italic

原 DESIGN.md 段落（verbatim）：
> ### Weight rules
> - Serif uses **only weights 400 and 500**. No 600, no 700, no 900.
> - `strong { font-weight: 500 }` is explicitly set so browsers don't synthesize bold.
> - Sans labels may use 500 or 600 at small sizes for legibility.
> - **No italic anywhere.** No `font-style: italic`. If emphasis is needed, switch the color to ink-blue or wrap in a tag.

- **trade_off**: bold + italic emphasis（universal markup）↔ ink-blue color emphasis（print constraint）
- **intent**: 让 emphasis 通过 color shift 实现，weight ≤500，italic 完全禁用
- **avoid**: 700+ bold heading / italic emphasis / weight-driven hierarchy / synthetic bold

## Color

### decision: tag fills must be solid hex pre-blended over parchment — never rgba

原 DESIGN.md 段落（verbatim）：
> ### Tag tints (solid, NOT rgba)
> Print renderers (WeasyPrint and friends) double-paint alpha fills, leaving a visible "double rectangle" on zoom. Tag and chip backgrounds must be solid hex, pre-blended over parchment:

- **trade_off**: rgba alpha fill（设计 flexible）↔ solid hex 预混（print 渲染稳）
- **intent**: 让 print pipeline 不出"双层矩形"——tag 在屏与纸上一致
- **avoid**: rgba(27,54,93,0.18) / 透明 tag fill / 多层 alpha overlay

## Color

### decision: all grays warm (R≈G>B), no cool blue-grays anywhere

原 DESIGN.md 段落（verbatim）：
> - All grays warm (R ≈ G > B), no cool blue-grays anywhere
> ...
> ### Forbidden colors
> - `#ffffff` as a page background
> - `#000000` anywhere
> - Any cool-gray surface (`#f8f9fa`, `#f3f4f6`, `slate-*`)
> - Any second saturated color (no second accent — pick ink-blue or pick nothing)

- **trade_off**: Tailwind cool gray（universal）↔ warm gray ramp（temperature 锁定）
- **intent**: 让所有 neutral 共享暖偏色——温度统一是 kami DNA
- **avoid**: slate-* gray / `#f3f4f6` / `#6b7280` / 任何 cool gray surface

## Depth

### decision: only ring shadow + whisper shadow (0 4px 24px rgba 0,0,0,0.05) — page is paper

原 DESIGN.md 段落（verbatim）：
> Three sanctioned levels — that is the entire system:
>
> | Level | Treatment | Use |
> |-------|-----------|-----|
> | Flat (0) | No shadow, no border | Body text, manifesto, paragraphs on parchment |
> | Ring (1) | `1px solid var(--border)` or `0 0 0 1px var(--brand)` | Cards, primary buttons, table edges |
> | Whisper (2) | `0 4px 24px rgba(0,0,0,0.05)` | Hovered cards, lifted hero containers, screenshots |

- **trade_off**: Material elevation 系统（数字层级）↔ 三档 print depth（纸张物理）
- **intent**: 让 elevation 不超过 5% opacity — 纸张本身没有 drop shadow
- **avoid**: 强 drop shadow / multi-layer composite shadow / glassmorphism / backdrop-filter
