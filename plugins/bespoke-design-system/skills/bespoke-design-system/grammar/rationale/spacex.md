# Rationale — spacex

> 三段式 rationale 抽取自 `source-design-systems/spacex/DESIGN.md`。

## Visual Theme

### decision: photographic exhibition — text on full-bleed image, no panels/cards/borders/shadow/grid

原 DESIGN.md 段落（auto-backfill）：
> > Category: Media & Consumer
> > Space technology. Stark black and white, full-bleed imagery, futuristic.
- **trade_off**: 传统 design system（结构化 chrome） ↔ "exhibition + type system"（极致克制）
- **intent**: 让 SpaceX 的 aerospace photography 占满 viewport，UI 消失到只剩 ghost button
- **avoid**: cards / containers / panels / 装饰 / 多色 / 多 button

### decision: pure black (#000) canvas + spectral white (#f0f0fa) text — no other colors

原 DESIGN.md 段落（auto-backfill）：
> What makes SpaceX distinctive is its radical minimalism: no shadows, no borders (except one ghost button border at `rgba(240,240,250,0.35)`), no color (only black and a spectral near-white `#f0f0fa`), no cards, no grids. The only visual element is photography + text. The ghost button with `rgba(240,240,250,0.1)` background and 32px radius is the sole interactive element — barely visible, floating over the imagery like a heads-up display. This isn't a design system in the traditional sense — it's a photographic exhibition with a type system and a single button.
- **trade_off**: 多色信号（普适） ↔ 单色 + 单 text（cinematic minimalism）
- **intent**: 让 photography 是唯一色彩源，text 是唯一信号
- **avoid**: 纯白 #ffffff（spectral 微蓝紫 mimics starlight）/ 多色装饰 / 任何 chromatic

## Typography

### decision: D-DIN universal uppercase + positive letter-spacing 0.96-1.17px

原 DESIGN.md 段落（auto-backfill）：
> The typography system uses D-DIN, an industrial geometric typeface with DIN heritage (the German industrial standard). The defining characteristic is that virtually ALL text is uppercase with positive letter-spacing (0.96px–1.17px), creating a military/aerospace labeling system where every word feels stenciled onto a spacecraft hull. D-DIN-Bold at 48px with uppercase and 0.96px tracking for the hero creates headlines that feel like mission briefing titles. Even body text at 16px maintains the uppercase/tracked treatment at smaller scales.
- **trade_off**: 小写 humanist（普适） ↔ uppercase + wide tracking（military/aerospace voice）
- **intent**: 让所有文字像 official documentation / mission briefing
- **avoid**: 小写 marketing / 紧字距 / decorative typography

### decision: two-weight strict hierarchy (D-DIN-Bold 700 + D-DIN 400 only)

原 DESIGN.md 段落（auto-backfill）：
> **Ghost Button**
> - Background: `rgba(240, 240, 250, 0.1)` (barely visible)
> - Text: Spectral White (`#f0f0fa`)
> - Padding: 18px
> - Radius: 32px
> - Border: `1px solid rgba(240, 240, 250, 0.35)`
> - Hover: background brightens, text to `var(--white-100)`
> - Use: The only button variant — "LEARN MORE" CTAs on photography
- **trade_off**: 多 weight ladder（hierarchy 丰富） ↔ 仅两 weight（mission-critical 简洁）
- **intent**: 让 hierarchy 极简如 mission control panel
- **avoid**: 中间 weight 500/600 / 装饰 weight contrast

### decision: tight line-height 0.94-1.00 — compressed mission-critical communication

原 DESIGN.md 段落（auto-backfill）：
> SpaceX's website is a full-screen cinematic experience that treats aerospace engineering like a film — every section is a scene, every photograph is a frame, and the interface disappears entirely behind the imagery. The design is pure black (`#000000`) with photography of rockets, space, and planets occupying 100% of the viewport. Text overlays sit directly on these photographs with no background panels, cards, or containers — just type on image, bold and unapologetic.
- **trade_off**: 宽 lh（呼吸） ↔ 紧 lh（密度 + efficiency）
- **intent**: text 像 instrument readout 紧凑高效
- **avoid**: 1.5 标准 lh / 散漫 typography
