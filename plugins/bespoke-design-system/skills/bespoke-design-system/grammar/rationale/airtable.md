# Rationale — airtable

> 三段式 rationale 抽取自 `source-design-systems/airtable/DESIGN.md`。

## Visual Theme

### decision: white canvas + deep navy text + Airtable Blue as the only chromatic accent

原 DESIGN.md 段落（verbatim）：
> Airtable's website is a clean, enterprise-friendly platform that communicates "sophisticated simplicity" through a white canvas with deep navy text (`#181d26`) and Airtable Blue (`#1b61c9`) as the primary interactive accent.

- **trade_off**: enterprise authority（深色严肃栅格） ↔ creative-friendly approachable（浅画布+一抹蓝）
- **intent**: 让 spreadsheet 工具读起来像 Swiss-precision 出版物，而不是 SAP 仪表盘
- **avoid**: 多色 dashboard 感 / pure-white 医疗器械感 / 深色 enterprise 冷感

## Color

### decision: blue-tinted multi-layer shadow as the ambient warmth

原 DESIGN.md 段落（verbatim）：
> **Blue-tinted** (`rgba(0,0,0,0.32) 0px 0px 1px, rgba(0,0,0,0.08) 0px 0px 2px, rgba(45,127,249,0.28) 0px 1px 3px, rgba(0,0,0,0.06) 0px 0px 0px 0.5px inset`)

- **trade_off**: 中性灰 shadow（中立稳） ↔ 蓝色调 shadow（让品牌色渗到 chrome 里）
- **intent**: 让阴影本身也带 brand temperature，统一 chrome 的冷暖感
- **avoid**: 黑灰 drop shadow 的 generic SaaS 感 / 强对比 hard shadow

## Typography

### decision: Haas + Haas Groot Disp dual family with positive letter-spacing

原 DESIGN.md 段落（verbatim）：
> The Haas font family (display + text variants) creates a Swiss-precision typography system with positive letter-spacing throughout.

- **trade_off**: 单一字族（实施简单） ↔ display+text 双字族（display 担任视觉锚）
- **intent**: 用 Swiss neogrotesque 调性传 enterprise 信任感，正字距加 readability airy
- **avoid**: Inter 通用感 / 负字距 compression 工具感 / 衬线 editorial 感

## Components

### decision: 12px button radius / 16-32px card radius — comfortably rounded, never sharp

原 DESIGN.md 段落（verbatim）：
> - Radius: 2px (small), 12px (buttons), 16px (cards), 24px (sections), 32px (large), 50% (circles)

- **trade_off**: 4-8px 严苛 geometry（精度感） ↔ 12-32px 中性圆角（友好 enterprise）
- **intent**: 让 chrome 不刻意工程化也不刻意软萌，处于"专业但好接近"的中间地带
- **avoid**: 直角 brutalist 感 / 9999px pill 玩具感 / sub-8 sharp 的医疗仪器感

## Do's and Don'ts

### decision: positive letter-spacing on body is mandatory, heavy shadows forbidden

原 DESIGN.md 段落（verbatim）：
> ### Do: Use Airtable Blue for CTAs, Haas with positive tracking, 12px radius buttons
> ### Don't: Skip positive letter-spacing, use heavy shadows

- **trade_off**: 紧字距 dense（信息量大） ↔ 正字距 airy（呼吸感）
- **intent**: 让 spreadsheet 工具的 chrome 不像 spreadsheet — 留一口气
- **avoid**: 0 letter-spacing 的密集 dashboard 感 / heavy drop shadow 的 Material 感
