# Rationale — intercom

> 三段式 rationale 抽取自 `source-design-systems/intercom/DESIGN.md`。

## Visual Theme

### decision: warm off-white canvas + editorial magazine register — AI-first helpdesk

原 DESIGN.md 段落（verbatim）：
> Intercom's website is a warm, confident customer service platform that communicates "AI-first helpdesk" through a clean, editorial design language. The page operates on a warm off-white canvas (`#faf9f6`) with off-black (`#111111`) text, creating an intimate, magazine-like reading experience.

- **trade_off**: pure white SaaS（commodity 感）↔ warm off-white（editorial intimacy）
- **intent**: 让 helpdesk 平台读起来像 magazine 的 reading experience，不像 ticketing tool
- **avoid**: pure white canvas / 冷蓝灰 SaaS / 棕色 cozy（咖啡馆感）

## Typography

### decision: Saans with -2.4px letter-spacing at 80px + 1.00 line-height — billboard-compressed headlines

原 DESIGN.md 段落（verbatim）：
> The typography uses Saans — a custom geometric sans-serif with aggressive negative letter-spacing (-2.4px at 80px, -0.48px at 24px) and a consistent 1.00 line-height across all heading sizes. This creates ultra-compressed, billboard-like headlines that feel engineered and precise.

- **trade_off**: relaxed display（呼吸优雅）↔ -2.4px 1.00 ultra-compression（billboard 工程感）
- **intent**: 让 headline 在 warm canvas 上保持 engineered-precise 锋利度
- **avoid**: 0 letter-spacing display / 1.2+ line-height heading / serif editorial heading

## Color

### decision: Fin Orange (#ff5600) as singular AI-brand accent — never decoratively used

原 DESIGN.md 段落（verbatim）：
> The signature Fin Orange (`#ff5600`) — named after Intercom's AI agent — serves as the singular vibrant accent against the warm neutral palette.

- **trade_off**: 多色 brand palette（rich）↔ 单一 Fin Orange（语义专属）
- **intent**: 让 orange 出现 = AI features，把 brand color 绑给 AI agent 身份
- **avoid**: orange 装饰 / orange 文字非 AI 上下文 / 多 brand accent

## Components

### decision: 4px button radius — sharp geometry against warm surface

原 DESIGN.md 段落（verbatim）：
> What distinguishes Intercom is its remarkably sharp geometry — 4px border-radius on buttons creates near-rectangular interactive elements that feel industrial and precise, contrasting with the warm surface colors. Button hover states use `scale(1.1)` expansion, creating a physical "growing" interaction.

- **trade_off**: 8-12px friendly button radius（warm 一致性） ↔ 4px sharp（industrial 对比）
- **intent**: 让 button 与 warm canvas 形成 sharp/soft 对比，industrial precision 在 warm 中显眼
- **avoid**: 8-12px 圆角 button（失去对比）/ 0px 完全直角（生硬）/ 9999px pill（friendly 过度）

## Components

### decision: scale(1.1) hover + scale(0.85) active — physical "growing/pressing" interaction

原 DESIGN.md 段落（verbatim）：
> Button hover states use `scale(1.1)` expansion, creating a physical "growing" interaction. The border system uses warm oat tones (`#dedbd6`) and oklab-based opacity values for sophisticated color management.

- **trade_off**: opacity hover（轻微回应）↔ scale(1.1) hover（物理生长）
- **intent**: 让 button 有"长大/被按压"的物理回应，magazine 感的 chrome 也有触感
- **avoid**: 单纯 opacity hover（无触感）/ scale > 1.15（卡通感）/ 复杂多步动画

## Color

### decision: warm oat border (#dedbd6) replaces cool gray — every neutral is warm

原 DESIGN.md 段落（verbatim）：
> ### Don't
> - Don't round buttons beyond 4px
> - Don't use Fin Orange decoratively
> - Don't use cool gray borders — always warm oat tones
> - Don't skip the negative tracking on headings

- **trade_off**: cool gray border 标准（设计 token 通用） ↔ warm oat tone（temperature 一致）
- **intent**: 让所有 neutral 共享 warm bias，温度感不分裂
- **avoid**: `#e5e7eb` Tailwind 冷灰 / `#f3f4f6` 冷 surface / 蓝灰 border on warm canvas
