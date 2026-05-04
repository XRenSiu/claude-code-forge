# Rationale — elevenlabs

> 三段式 rationale 抽取自 `source-design-systems/elevenlabs/DESIGN.md`。

## Visual Theme

### decision: near-white canvas with warm stone undertones — Apple-like generosity, but warmer

原 DESIGN.md 段落（verbatim）：
> ElevenLabs' website is a study in restrained elegance — a near-white canvas (`#ffffff`, `#f5f5f5`) where typography and subtle shadows do all the heavy lifting. The design feels like a premium audio product brochure: clean, spacious, and confident enough to let the content speak (literally, given ElevenLabs makes voice AI). There's an almost Apple-like quality to the whitespace strategy, but warmer — the occasional warm stone tint (`#f5f2ef`, `#777169`) prevents the purity from feeling clinical.

- **trade_off**: pure white minimalism（clinical） ↔ warm stone tint（cozy 但不土）
- **intent**: 让 voice-AI 的 brochure 感"premium 但不冷"，warm 又不"乡村风"
- **avoid**: 冷蓝灰 minimalist（医疗器械） / 暖米色 cozy（咖啡馆）/ pure-white Apple clone

## Typography

### decision: Waldenburg weight 300 (light) for display — lightness IS the brand

原 DESIGN.md 段落（verbatim）：
> - **Light as the hero weight**: Waldenburg at 300 is the defining typographic choice. Where other design systems use bold for impact, ElevenLabs uses lightness — thin strokes that feel like audio waveforms, creating intrigue through restraint.

- **trade_off**: bold heading 抢眼（grab attention） ↔ light heading 引人凝视（intrigue through restraint）
- **intent**: 让 hairline display 视觉等价于音频波形细节 — 听觉品牌的视觉对位
- **avoid**: 700 bold display / 500 medium hero / weight 400 默认（中庸无个性）

## Color

### decision: warm-tinted shadows (rgba 78,50,23,0.04) — shadows have color, not just darkness

原 DESIGN.md 段落（verbatim）：
> What makes ElevenLabs distinctive is its multi-layered shadow system. Rather than simple box-shadows, elements use complex stacks: inset border-shadows (`rgba(0,0,0,0.075) 0px 0px 0px 0.5px inset`), outline shadows (`rgba(0,0,0,0.06) 0px 0px 0px 1px`), and soft elevation shadows (`rgba(0,0,0,0.04) 0px 4px 4px`) — all at remarkably low opacities. The result is a design where surfaces seem to barely exist, floating just above the page with the lightest possible touch. Pill-shaped buttons (9999px) with warm-tinted backgrounds (`rgba(245,242,239,0.8)`) and warm shadows (`rgba(78,50,23,0.04)`) add a tactile, physical quality.

- **trade_off**: 中性黑 shadow（generic SaaS） ↔ warm brown shadow（温度统一到品牌）
- **intent**: 让 elevation 也带 warm bias，整个 chrome 共享温感而非分裂
- **avoid**: pure black shadow / cool gray shadow / 高 opacity shadow（>0.1 破坏 ethereal）

## Typography

### decision: positive letter-spacing on Inter body (+0.14 to +0.18px) — airy reading rhythm

原 DESIGN.md 段落（verbatim）：
> - **Positive letter-spacing on body**: Inter uses +0.14px to +0.18px tracking across body text, creating an airy, well-spaced reading rhythm that contrasts with the tight display tracking (-0.96px).

- **trade_off**: 0 默认 tracking（标准）↔ +0.14-0.18 微正 tracking（呼吸感）
- **intent**: 让正文读起来像 audio waveform 之间的空气 — 不挤
- **avoid**: 负 letter-spacing on body（compressed unfriendly） / 过大 +0.5+ tracking（公告感）

## Components

### decision: 9999px pill buttons with warm stone fill + warm shadow — tactile signature

原 DESIGN.md 段落（verbatim）：
> **Warm Stone Pill**
> - Background: `rgba(245, 242, 239, 0.8)` (warm translucent)
> - Text: `#000000`
> - Padding: 12px 20px 12px 14px (asymmetric)
> - Radius: 30px
> - Shadow: `rgba(78, 50, 23, 0.04) 0px 6px 16px` (warm-tinted)
> - Use: Featured CTA, hero action — the signature warm button

- **trade_off**: 黑 pill（高对比 commodity CTA） ↔ warm stone translucent（tactile 物理）
- **intent**: 让 hero CTA 触觉上像石头 — 物理在场感而非数字感
- **avoid**: 实色黑 pill 标准 CTA / pure white pill / 高 opacity warm fill（失去 translucency）
