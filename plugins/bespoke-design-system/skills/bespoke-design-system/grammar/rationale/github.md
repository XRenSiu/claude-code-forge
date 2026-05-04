# Rationale — github

> 三段式 rationale 抽取自 `source-design-systems/github/DESIGN.md`。

## Color

### decision: 14px body + dense list rows + hairline borders

原 DESIGN.md 段落（auto-backfill）：
> - **Base unit**: 4px. Spacing scale: 4, 8, 12, 16, 24, 32, 40, 48.
> - **Page max-width**: 1280px (`Container-xl`).
> - **Sidebar**: 296px on desktop, collapses below 1012px.
> - **Row padding**: 16px horizontal, 12px vertical (lists are dense by design).
- **trade_off**: 16px 标准 body（普适可读） ↔ 14px 密集（power-user 一屏看更多）
- **intent**: 让产品成为 "diff/build/PR 工具" — 信息密度是品牌
- **avoid**: 16px 默认 / 大留白 / 视觉噪声 / 装饰性 padding

### decision: Primer Blue (#0969da) + GitHub Green (#1a7f37) 双 chromatic anchor

原 DESIGN.md 段落（auto-backfill）：
> The signature accents are the **Primer blue** (`#0969da`) for links and primary actions, and **GitHub green** (`#1a7f37`) for merged states, success, and the merge button itself. Both feel slightly muted compared to consumer-product blues and greens — saturated enough to read against the dense gray text, restrained enough to disappear into the background when several appear in one viewport.
- **trade_off**: 单 chromatic（极致克制） ↔ 双 chromatic（链接 + 状态分工）
- **intent**: blue = 通用交互（链接 / focus / CTA），green = 合并 / 成功（产品语义）
- **avoid**: 多 chromatic 竞争 / 装饰性 brand 色 / 消费者级饱和度

### decision: hairline gray borders (#d0d7de) instead of shadow elevation

原 DESIGN.md 段落（auto-backfill）：
> GitHub's surface is engineered, not decorated. Every pixel announces a stance: this is a tool for people who care about diffs, builds, and pull requests. The page background is a clean `#ffffff` (light) or `#0d1117` (dark), with content arranged on dense rectangular panes separated by hairline borders rather than negative space. Information density is the brand — list rows, code lines, repository headers, and notification cards are all packed close together so a power user can scan a hundred items without scrolling.
- **trade_off**: shadow（柔软深度） ↔ hairline border（工程精度）
- **intent**: 让 panel 边界靠 1px 边框定义，不靠空间或阴影
- **avoid**: 软阴影 / 圆角卡片浮起 / 视觉柔化

## Typography

### decision: system-ui across the entire product, no custom webfont

原 DESIGN.md 段落（auto-backfill）：
> Typography uses the **system-ui** stack across the entire product so text renders crisply on every OS, paired with **SFMono / Menlo / Consolas** for code. There is no editorial display font; GitHub's voice is the voice of the system you're already on.
- **trade_off**: custom typeface（独特调性） ↔ system-ui（即时渲染 + 跨 OS 一致）
- **intent**: GitHub 的声音是"你已在的系统"的声音
- **avoid**: 加载 webfont 延迟 / 跨 OS 渲染差异

## Components

### decision: pill status badges with strong color semantics

原 DESIGN.md 段落（auto-backfill）：
> > Category: Developer Tools
> > Code-forward platform. Functional density, blue-on-white precision, Primer foundations.
- **trade_off**: 通用 chip（中性） ↔ 强语义状态徽章（颜色即含义）
- **intent**: open/merged/closed/draft 一眼可识别
- **avoid**: 通用 tag / 颜色装饰用法

### decision: zero radius on dark theme borders + Octicon at 16/24px

原 DESIGN.md 段落（auto-backfill）：
> **Key Characteristics:**
> - True white canvas (`#ffffff`) or deep navy-black (`#0d1117`) — no warmth, no tint
> - Hairline gray borders (`#d0d7de`) define every pane and panel
> - Primer blue (`#0969da`) for links/primary; GitHub green (`#1a7f37`) for success/merge
> - system-ui for prose; SFMono for code — no custom typeface
> - Dense list rows with minimal padding; whitespace is rare
> - Octicon iconography at 16px / 24px — single-stroke, geometric, consistent
> - Pill-shaped status badges with strong color semantics
- **trade_off**: 圆角 friendliness ↔ 严苛 geometry
- **intent**: 工程精度 + 单 stroke icon 一致性
- **avoid**: 大圆角消费者感 / 多 stroke 复杂度
