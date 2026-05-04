# Rationale — openai

> 三段式 rationale 抽取自 `source-design-systems/openai/DESIGN.md`。

## Visual Theme

### decision: research-lab-dressed-for-public — clinical / restrained / deliberately quiet

原 DESIGN.md 段落（auto-backfill）：
> > Category: AI & LLM
> > Calm, near-monochrome system anchored in deep teal-black with generous white space and editorial typography.
- **trade_off**: AI 多色 futuristic（mainstream） ↔ 安静 literary（research lab）
- **intent**: 让 AI 看起来像 research output 不是 consumer toy
- **avoid**: futuristic 装饰 / 多色渐变 / consumer AI vibe

## Color

### decision: true white canvas + deep teal-black ink (#0d0d0d) — slight cool subtle

原 DESIGN.md 段落（auto-backfill）：
> OpenAI's product surface reads like a research lab dressed for the public — clinical, restrained, deliberately quiet. The page background is a true white (`#ffffff`) layered against a near-black ink (`#0d0d0d`) with a subtle teal undertone, so even the text feels slightly cooled rather than aggressively dark. The result is a chromatic neutrality that puts model output, code, and prose front and center, not the chrome around them.
- **trade_off**: 纯黑 / 暖近黑 ↔ teal-undertone near-black (略冷 literary)
- **intent**: text 微冷增加 literary research 气质
- **avoid**: 纯黑 / 暖 ink / 高对比纯白纯黑

### decision: OpenAI Teal (#10a37f) as singular brand — only color in neutral system

原 DESIGN.md 段落（auto-backfill）：
> **Brand Accent**
> - Background: `#10a37f`
> - Text: `#ffffff`
> - Padding: 10px 18px
> - Radius: 12px
> - Hover: `#0a7a5e`
> - Use: Highlighted upgrade CTA, success path
- **trade_off**: 多色 ↔ 单 teal anchor（克制 + literary）
- **intent**: teal 取代蓝紫——避开 medical blue + AI gaming purple
- **avoid**: 多色 brand / 装饰 teal / 紫色 AI vibe / 医疗蓝

## Typography

### decision: Söhne / Inter at restrained weights (400/500/600) + Signifier serif for editorial

原 DESIGN.md 段落（auto-backfill）：
> The signature move is the use of **Söhne** (or its system stand-in `inter`) at restrained weights — 400 for body, 500 for nav and labels, 600 for emphasis — paired with **Signifier**, a contemporary serif used for editorial display. Where most AI brands lean futuristic, OpenAI's serif headlines give the product a quietly literary tone, as if every announcement is an essay.
- **trade_off**: 单 sans family（一致） ↔ sans body + serif editorial（literary tone）
- **intent**: serif 让 announcement 像 essay，sans 让 UI 静默不抢戏
- **avoid**: 单 family flatness / 装饰 serif / heavy weight 喧宾夺主

## Components & Layout

### decision: 8-12px radii + 9999 pills for tags — no harsh corners anywhere

原 DESIGN.md 段落（auto-backfill）：
> **Key Characteristics:**
> - True white canvas (`#ffffff`) with deep teal-black ink (`#0d0d0d`)
> - Söhne / Inter at modest weights (400, 500, 600) — restraint over assertion
> - Signifier serif for editorial display headlines
> - Soft 8–12px radii everywhere; 9999px pills for chips
> - Hairline borders (`#e5e5e5`) used sparingly; whitespace as primary divider
> - Single-color illustrations in deep teal — no gradients in marks
> - Generous line-height (1.55–1.65) and tracking near zero
- **trade_off**: 直角 engineering ↔ soft 8-12 radii（uniformly soft）
- **intent**: 整体 chrome 感觉 quiet + literary，无 harsh corners
- **avoid**: 直角 / 大圆角 friendly / 中等 radius indecision

### decision: hairline borders (#e5e5e5) used sparingly; whitespace as primary divider

原 DESIGN.md 段落（auto-backfill）：
> The shape system is uniformly soft: 8px–12px radii, 9999px pills for tags and chips, no harsh corners anywhere. Section transitions are denoted by whitespace rather than dividers; when borders appear they are `#e5e5e5` hairlines that read as the absence of color rather than its presence.
- **trade_off**: 多边框（结构清晰） ↔ 极少 hairline + 大量 whitespace（quietly literary）
- **intent**: section 切换靠 whitespace，border 仅少量出现
- **avoid**: 实色边框 / 多分隔线 / 装饰 border
