# Negotiation Summary — Code Review SaaS

## 这份设计的核心调性

这是一份属于 **Sage + Creator** 的设计——智者的克制和创造者的精度。它继承了 Linear 的"暗底为本"语言（near-black canvas + 单一冷调蓝色锚点 + 半透明白色边框），并采纳了 Vercel 的"色彩即功能"原则（status 色仅用于语义场合、绝不装饰）。整体调性追求 **engineered restraint**——每个视觉元素都有功能依据，没有营销腔的渐变和插画。在你的需求里"减少 review 噪音"被翻译成两条具体决策：(1) 把品牌色调整为略偏 teal 的冷蓝（`#4d7df0`），让它读起来支持而非警告；(2) 间距 scale 保留 20/24 的中段（diff/comment 的层级缩进需要它）但移除 Linear 的 19/22/28/35（在你的产品中是冗余）。

## 关键决策

| 决策 | 一句话 rationale | 来源系统 |
|---|---|---|
| Canvas Black `#0c0d0f` 主背景 | 暗底为本，比 Linear `#08090a` 微微提亮 0.01 减轻长会话时的代码-画布对比硬度 | linear-app |
| Review Blue `#4d7df0` 单一锚点 | 调到 220° hue + 0.50 saturation，让它 supportive 而非 aggressive | linear-app, vercel |
| Inter Variable + cv01,ss03 + 510 weight | 选 Inter 而非 Geist——后者的 -2.4px tracking 会把"紧迫"放大超过 review 工具的 calm | linear-app, vercel |
| 3-tier weight 400/510/590（无 700） | size+tracking 建立层级，不靠 weight；510 是 quiet emphasis 的关键 | linear-app, vercel |
| 半透明白边框 0.05–0.12 | 暗底上实色暗边形成视觉墙，半透明白让边界存在但不切割空间 | linear-app |
| 亮度叠加做深度（不用 drop shadow） | 暗底上 drop shadow 几乎不可见；亮度递进是该介质的原生深度系统 | linear-app |
| 间距 scale 修订 [4,7,8,11,12,16,20,24,32,48,64,96] | 保留 Linear 的光学修正（7/11）+ 借鉴 Vercel 的"中段不要 mood-based"原则 | linear-app, vercel |
| Voice = engineered restraint | CTA 词改成 workflow-bound 动词（"Submit review" / "Approve" 而非 "Get started"）| linear-app, vercel |
| Anti-patterns 加入 "not yet another enterprise SaaS" | 直接来自你的 brief 反向约束 | brief-derived |

## 推断字段（这次是 auto 模式）

> 这份设计在 auto 模式下生成。以下字段是从你的 brief 推断的——如果不准，告诉我具体哪一条，我会重排规则重新生成。

- `product_context.category`: 推断为 `developer_tool`（关键词 "代码审查" / "技术团队" / "工程师"）
- `brand_archetypes.primary`: 推断为 `Sage`（developer_tool 默认 + "judgment-worthy" 强调匹配 Sage 的 "convey truth"）
- `brand_archetypes.secondary`: 推断为 `Creator`（developer_tool 默认）
- `kansei_words.positive`: 推断为 `[structured, precise, modern, calm, confident, focused]`（默认 + "judgment-worthy" 加 focused）
- `kansei_words.reverse_constraint`: 推断为 `[ai_slop, generic_corporate, decorative, playful, ornate, aggressive]`（含通用反向 + brief "不要又一个企业 SaaS"）
- `semantic_differentials`: warm/cold +0.2, ornate/minimal +0.6, serious/playful -0.3, modern/classical -0.4

## 协商接口

如果你想改某个决策：

- **"我想要白底而不是暗底"** → 我会回到 B3 重排规则，把 Linear 的 dark-canvas 系列规则全 drop，改用 Vercel 的 white-minimalism 子图（5 条规则会回来），重新走 B4-B6
- **"主色不要这种蓝，给我点别的"** → 给我一个方向（例：'更暖'/'偏紫'/'更克制接近灰'），我会调整 Review Blue 的 hue/saturation 维度
- **"间距太密 / 太松"** → 直接告诉我，我会调整 scale 中段值
- **"voice 太严肃"** → 我会回到 B1 修改 SD `serious_to_playful` 然后重跑 B2-B6
- **"我想加上 mock screenshots / 插画指导"** → 当前 9-section 不含 illustration 指导，可以作为 appendix 补充

## 已知限制

- **Motion 维度数据稀疏**：两套源系统（Linear / Vercel）的 DESIGN.md 都没有专门 motion section，本设计的 motion 推断只能从 hover / focus 模式推出，**没有专门 motion 章节**。这是 OD 9-section 格式的结构性限制。
- **规则库覆盖窄**：当前规则库只含 2 套（linear-app + vercel），都是 dev-tool 类。如果你后续想生成不同类别（如灵性 SaaS / 高端电商），先导入更多素材。
- **没有插画 / icon set 指导**：标准 9-section 不覆盖此维度。
- **P0 闸门未运行**：本次为 pilot run，rationale-judge subagent 没有作为独立 agent 调用（见问题清单 #6）。所以 4 维度（inheritance / adaptation / justification / confidence）的对抗式评判没有发生——上述决策由生成方自审。生产环境必须独立 subagent 调用。
