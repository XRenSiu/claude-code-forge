# Rationale — lovable

> 三段式 rationale 抽取自 `source-design-systems/lovable/DESIGN.md`。

## Visual Theme

### decision: warm parchment background (#f7f4ed) — not white, not beige, deliberate cream

原 DESIGN.md 段落（verbatim）：
> Lovable's website radiates warmth through restraint. The entire page sits on a creamy, parchment-toned background (`#f7f4ed`) that immediately separates it from the cold-white conventions of most developer tool sites. This isn't minimalism for minimalism's sake — it's a deliberate choice to feel approachable, almost analog, like a well-crafted notebook.

- **trade_off**: pure white developer tool 标准感 ↔ parchment cream（analog notebook 感）
- **intent**: 让 AI builder 平台第一眼"非 cold dev tool"，approachable 不工程
- **avoid**: pure white / 棕米色 cozy（厨房感）/ light gray developer tool 标准

## Typography

### decision: Camera Plain Variable — humanist warmth instead of geometric tech

原 DESIGN.md 段落（verbatim）：
> The custom Camera Plain Variable typeface is the system's secret weapon. Unlike geometric sans-serifs that signal "tech company," Camera Plain has a humanist warmth — slightly rounded terminals, organic curves, and a comfortable reading rhythm. At display sizes (48px–60px), weight 600 with aggressive negative letter-spacing (-0.9px to -1.5px) compresses headlines into confident, editorial statements.

- **trade_off**: geometric sans（tech credibility）↔ humanist 圆润 terminals（warmth）
- **intent**: 让字体本身就传"非冷感 dev tool"信号，圆润 terminal 是 humanist 名片
- **avoid**: Inter/Geist/Helvetica 通用 geometric / 衬线 editorial / mono dev 感

## Color

### decision: opacity-driven gray scale — all grays derived from #1c1c1c

原 DESIGN.md 段落（verbatim）：
> What makes Lovable's visual system distinctive is its opacity-driven depth model. Rather than using a traditional gray scale, the system modulates `#1c1c1c` at varying opacities (0.03, 0.04, 0.4, 0.82–0.83) to create a unified tonal range. Every shade of gray on the page is technically the same hue — just more or less transparent. This creates a visual coherence that's nearly impossible to achieve with arbitrary hex values.

- **trade_off**: 离散 hex gray scale（精确控制）↔ 同 hue + opacity（数学 coherence）
- **intent**: 让所有 gray 共享同一 hue 的数学根源，coherence 不靠手感对齐
- **avoid**: Tailwind gray scale（冷蓝绿混杂）/ 离散 #aaa #888 #666（hue drift）

## Components

### decision: inset shadow on dark buttons (white 0.5px top + dark ring + soft drop) — pressed-into-surface

原 DESIGN.md 段落（verbatim）：
> **Shadow Philosophy**: Lovable's depth system is intentionally shallow. Instead of floating cards with dramatic drop-shadows, the system relies on warm borders (`#eceae4`) against the cream surface to create gentle containment. The only notable shadow pattern is the inset shadow on dark buttons — a subtle multi-layer technique where a white highlight line sits at the top edge while a dark ring and soft drop handle the bottom. This creates a tactile, pressed-into-surface feeling rather than a hovering-above-surface feeling.

- **trade_off**: floating elevation（hover above 立体）↔ inset pressed-into-surface（tactile press）
- **intent**: 让 button 是被按进去的物理按键，而非漂浮的 floating panel
- **avoid**: 大 drop shadow / floating glassmorphism / 单层 inset（缺白边光感）

## Typography

### decision: variable-weight 480 — "lighter than semibold but stronger than regular"

原 DESIGN.md 段落（verbatim）：
> - **Variable weight as design tool**: The font supports continuous weight values (e.g., 480), enabling nuanced hierarchy beyond standard weight stops. Weight 480 at 60px creates a display style that feels lighter than semibold but stronger than regular.

- **trade_off**: 标准 400/500/600/700 stops（实施简单）↔ 480 自定义中间值（hierarchy nuance）
- **intent**: 让 hierarchy 用 weight 微调而非粗暴跳档，semantic 落在 standard 之间
- **avoid**: 仅 400/600 二段 / 700 bold display / 任何 weight 跳档过大

## Components

### decision: full pill (9999px) only for action pills + icon buttons — never rectangular CTAs

原 DESIGN.md 段落（verbatim）：
> ### Don't
> - Don't apply 9999px radius on rectangular buttons — pills are for icon/action toggles
> - Don't use sharp focus outlines — the system uses soft shadow-based focus indicators
> - Don't mix border styles — `#eceae4` for passive, `rgba(28,28,28,0.4)` for interactive

- **trade_off**: 全 pill button（friendly一致）↔ pill 仅限 toggle/icon（角色专属）
- **intent**: 让 pill 形状自带语义"toggle/action"，rectangle 留给 primary CTA
- **avoid**: 9999px primary CTA / 6px pill toggle / mixed pill+rect 在 same context
