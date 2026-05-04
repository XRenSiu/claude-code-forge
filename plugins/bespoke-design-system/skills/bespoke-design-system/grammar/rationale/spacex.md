# Rationale — spacex

> 三段式 rationale 抽取自 `source-design-systems/spacex/DESIGN.md`。

## Visual Theme

### decision: photographic exhibition — text on full-bleed image, no panels/cards/borders/shadow/grid
- **trade_off**: 传统 design system（结构化 chrome） ↔ "exhibition + type system"（极致克制）
- **intent**: 让 SpaceX 的 aerospace photography 占满 viewport，UI 消失到只剩 ghost button
- **avoid**: cards / containers / panels / 装饰 / 多色 / 多 button

### decision: pure black (#000) canvas + spectral white (#f0f0fa) text — no other colors
- **trade_off**: 多色信号（普适） ↔ 单色 + 单 text（cinematic minimalism）
- **intent**: 让 photography 是唯一色彩源，text 是唯一信号
- **avoid**: 纯白 #ffffff（spectral 微蓝紫 mimics starlight）/ 多色装饰 / 任何 chromatic

## Typography

### decision: D-DIN universal uppercase + positive letter-spacing 0.96-1.17px
- **trade_off**: 小写 humanist（普适） ↔ uppercase + wide tracking（military/aerospace voice）
- **intent**: 让所有文字像 official documentation / mission briefing
- **avoid**: 小写 marketing / 紧字距 / decorative typography

### decision: two-weight strict hierarchy (D-DIN-Bold 700 + D-DIN 400 only)
- **trade_off**: 多 weight ladder（hierarchy 丰富） ↔ 仅两 weight（mission-critical 简洁）
- **intent**: 让 hierarchy 极简如 mission control panel
- **avoid**: 中间 weight 500/600 / 装饰 weight contrast

### decision: tight line-height 0.94-1.00 — compressed mission-critical communication
- **trade_off**: 宽 lh（呼吸） ↔ 紧 lh（密度 + efficiency）
- **intent**: text 像 instrument readout 紧凑高效
- **avoid**: 1.5 标准 lh / 散漫 typography
