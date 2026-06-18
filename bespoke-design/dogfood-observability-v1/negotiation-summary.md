# 设计协商摘要 — 自托管可观测性工具

## 这份设计的核心调性（3-5 句）

它把可观测性从"监控墙"重新想象成"阅读一份存档报纸"。暖纸色画布（`#faf7f1`）、墨黑正文、**衬线大标题**，以及一条像报纸专栏一样自上而下阅读的单列时间线——而不是 Datadog 那种彩虹仪表盘。克制是全部要义：唯一的暖色锚点（oxblood `#8c2f2a`）、发丝线分隔代替方框与阴影、只有真正的日志载荷才用等宽字体。赌注是：工程师会盯着它看几个小时，一页排版考究的纸面比一墙互相竞争的色块更能维持注意力。

## 关键决策

| 决策 | 一句话 rationale | 来源系统 |
|---|---|---|
| 暖纸画布 + 色调分层（无阴影） | 长时间盯屏减眩光；深度靠纸色台阶不靠阴影 | github（hairline-not-shadow）|
| **衬线大标题（Newsreader），mono 只给日志载荷** | "存档报纸"身份的承载者；dev 工具里用衬线是有意的签名 | **transformational（无规则来源，概念派生）** |
| 单一 oxblood 强调色 | 唯一 chromatic，暖色呼应纸面（拒绝 dev 默认冷蓝=anti-slop） | linear-app（single-chromatic 纪律）|
| 单列 ≤760px + 边栏时间戳 + 慷慨段距 | 报纸专栏的可控行宽；可读性优先于仪表盘铺张 | mintlify + ant |

## 推断字段清单（auto 模式，供你针对性反馈）

- `brand_archetypes`: 推断 Sage（主）+ Creator（次）。概念 C 另带 Outlaw。
- `kansei`: 取**三个发散概念的并集**（structured/precise/calm/dense/legible/editorial/authoritative/raw/terminal-native/confident）——故意不塌缩到 developer_tool 品类质心。
- `semantic_differentials`: warm/cold 与 modern/classical 都设为 0.0（宽），因三概念在这两轴上分歧大。
- **3 个概念种子**：A 潜艇仪表（暗/密/克制）· B 编辑大报（衬线/暖/阅读，**胜出**）· C 粗野终端（mono/生/挑衅）。

## ⚠️ 品味终审需由人完成（铁律 3）

> 这份 DESIGN.md 通过了 6 项闸门（数学协调 0.65 / archetype Sage / kansei 覆盖 0.80 / neighbor 独特 0.130 / 论证 pass / **taste-critic 独特 0.92**），但**这不等于它有大师级品味**。taste-critic 确认它"有一个能说清的身份、不是 Linear 换皮",但**"warm 衬线纸面对一个要盯几小时的工具是不是正确的眼疲劳赌注"——必须由你（人）拍板**。学界共识：tacit knowledge 无法形式化（Polanyi 1966；CHI 2024）。

## 已知限制

- **kansei 覆盖 0.80（恰好过线）**：`raw` / `terminal-native` 未覆盖——它们属于**未被选中的概念 C**（粗野终端），与胜出的编辑方向天然相反。这是"并集 kansei vs 单一胜出概念"的张力（见 skill-issue #4）。如果你更想要 `raw/terminal-native`，告诉我"改选概念 C"，我会回 B4b 展开 C。
- **rationale-judge 给了 1 个 inheritance warning**（github 规则的 `why.avoid` 被我从 `soft_shadow_elevation` 误述为 `heavy_`）+ 1 个 confidence warning（layout 决策 high 但源规则自信 <0.7）。均为 warning 非 blocker，已据实修正 provenance。

## 协商接口

想改某个决策？告诉我具体哪个、改成什么方向。例如：
- "我不要衬线，改回 mono dev 风" → 我回 B4.5 重选（很可能切到候选 C 粗野终端）
- "暖纸太亮，要暗一点" → 我回 B4b 调 canvas，但会重新核 neighbor 距离别掉回 Linear 簇
- "我要 raw/terminal-native" → 改选概念 C，回 B4b 展开
