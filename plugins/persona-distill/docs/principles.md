---
name: principles
description: The theory behind persona-distill — why distillation is parameterized composition, why self-containment is non-negotiable, why tensions are signal not noise, why execution ≠ description
version: 0.3.0
---

# persona-distill — 设计原理（Principles）

> 为什么这套插件长成这样。不是「怎么用」，是「**为什么这样设计**」。如果你要 fork、贡献 schema、或把它接到别的系统，先读这份。

---

## 一句话立场

**Persona ≠ 提示词模板。Persona = 可组合组件在参数化 schema 下的稳定压缩。**

一个人、一个领域、一套规则，本质上都是「用有限文字编码一个可被另一个 agent 复现的认知行为」。我们不相信"写一个牛逼 system prompt 就能模拟乔布斯"——那是幻觉。我们相信的是：**先分解（9 schema × 18 component），再提取（三重验证 + 七轴 DNA），再压缩（density + conflicts），再验证（12 维 + 活体测试）**。每一步都是可审计的工程行为，而不是艺术。

---

## 四大核心原则

### 1. Self-Contained（自包含）—— 产物独立于生产者

**规则**：生成的 `alice-friend-skill/` 目录 `grep -r "distill-meta"` 必须返回 0。

**为什么**：
- 插件生态的基础协议是「可分发」。依赖生成器的产物等于没产物——卸载 persona-distill 后，alice 不能继续跑。
- 自包含也是**分发信任**的前提：你拿到一个别人做的 persona skill，能直接加载运行；不必先装插件、不必跑 migration、不必理解内部引用。
- v0.2.0 的 migrator 在升级 persona skill 时也强制维护这个不变量——升级后再 grep 一次，有任何引用就回滚。

**反面**：任何"运行时动态加载组件库"的设计。这等于把生产者的生命周期绑进了产物，破坏独立性。

### 2. Progressive Disclosure（渐进披露）—— 入口极薄，深度按需

**规则**：`SKILL.md` 只负责触发判定 + 高阶编排；`references/` 放详细规则，`agents/` 放并行子任务，`templates/` 放产物骨架。任何单个文件不超过 ~500 行。

**为什么**：
- Claude Code 的上下文窗口是有限的。一次性灌入 2000 行 SKILL.md 等于**主动**降低 agent 的推理质量。
- 按需加载让用户能在不读完整个知识库的情况下调用 skill——「蒸馏张三」的用户不需要预先理解 18 个组件。
- 这份原则也决定了 docs 的结构：本文件是入口摘要，`integration.md` 是布线细节，`schema-contribution-guide.md` 是扩展协议。

### 3. No Interrogate（不盘问）—— 默认路径兜底一切

**规则**：用户说「蒸馏张三」，不要反问「是什么 schema / 用什么语料 / 目的是什么」。自动走默认路径，在 Phase 0 末尾把推断结果**展示**给用户，允许修正。

**为什么**：
- 盘问是敌对交互。用户想要结果，不想要表单。
- 大多数默认选择可以从一两句话的意图 + 代码库信号中推断（例如有没有聊天记录、是不是自己、用户的语气），推错了用户一句话就能改。
- 盘问式产品会在第三次使用时被卸载。

**边界**：Phase 1.5 的 Research Review checkpoint 是**唯一**的必需用户确认点——因为只有用户能判断「语料是否能反映真实的他」。其他都默认兜底。

### 4. Preserve Tensions（保留张力）—— 矛盾是信号，不是噪声

**规则**：提取阶段遇到"他既喜欢极简又收藏大量工具"、"白天温和晚上暴躁"、"公开场合和私下观点相反"这种矛盾，**不抹平**。写到 `internal-tensions.md`（稳定的极性）或 `knowledge/conflicts.md`（事实层面的矛盾）。

**为什么**：
- 真实的人就是矛盾的。把乔布斯压缩成「完美主义 + 偏执」是 wikipedia，不是 persona。
- 矛盾是角色扮演深度的**主要来源**——询问 persona 在极端场景下的选择时，张力决定它回答什么。抹平 = 塌缩成平均值。
- v0.2.0 的 Phase 3.5 `conflict-detector` agent 自动扫描 4 类矛盾（事实 / 价值迁移 / 言行不一 / 组件内自相矛盾），只 surface 不 resolve——用户是最终裁决者。

**区分**：
- `internal-tensions.md`：稳定存在的极性（「他是个既想掌控又想自由的人」）——是**特征**。
- `knowledge/conflicts.md`：事实层面的不一致（「三处语料说 2005 年去了日本，一处说 2006」）——是**待验证**。

---

## 关键设计取舍

### 为什么是 9 schema × 18 component，不是 1 个大模板？

固定模板的问题：蒸馏「自己」、「已故爷爷」、「八字推算规则」用**同一套字段**显然荒谬。

9 种 schema 是**行为类型学**的归类：
- 自我（self）：只有你能知道的内心声音
- 协作（collaborator / mentor）：你需要他如何响应工作场景
- 亲密（loved-one / friend）：你需要他保留情感记忆
- 公共（public-mirror / public-domain）：你需要他的方法论和思考方式
- 领域（topic）：你需要一块知识的"代理人"
- 规则（executor）：你需要一套可计算+可解释的算法

每种 schema 引用一组（不是全部）组件。18 个组件是**正交的认知切面**：identity 是"他是谁"、expression-dna 是"他怎么说"、mental-models 是"他怎么想"、emotional-patterns 是"他怎么感受"……任意两个组件都不可被对方完全替代。

**组合而非继承**：schema 只定义「哪些组件必选 / 可选 / 禁用」，不重新定义组件本身。这让共享组件的改进能惠及所有使用它的 schema——改 `mental-models.md` 的三重验证协议，自动影响所有依赖它的 schema，不需要改 9 个文件。

### 为什么是 `triple-validation`（三重验证）？

任何一个观点 / 行为模式，如果只能从语料中找到 1 次证据，它就是**噪音**。

规则：一个 mental model 被写进 persona skill，必须满足：
1. 至少 3 处语料独立提及
2. 至少 2 种不同场景（工作 / 闲聊 / 情绪 / 决策）
3. 至少 1 次"代价证据"（他为这个观点付出了什么——真正信的东西总有代价）

通不过三重验证的观点走 `honest-boundaries.md`——明确写「资料不足以判断他在 X 问题上的真实立场」。诚实胜过编造。

### 为什么多轮 Phase 2.5 + Jaccard 收敛？

单轮提取的问题：第一轮会漏掉"只在次要语境出现的模式"。多轮扫描每次用前一轮已提取的观点反向查询，寻找「这些观点没覆盖的维度」。

Jaccard（交集 ÷ 并集）> 0.8 表示新一轮提取的维度集合和上一轮高度重叠——收敛了，可以停。

硬上限 3 轮：防止无限提取低信号维度。经验上第 4 轮以后 Jaccard 很少低于 0.9，继续跑是浪费 token。

### 为什么 Phase 4 必须跑 persona-judge，且 `distill-meta` 不能自评？

自评偏差：修改者给自己打分，系统性地偏高 8-15%（Anthropic constitutional AI 研究）。

`persona-judge` 在**独立 context** 跑 12 维 rubric + 3 项活体测试（Known / Edge / Voice）。产出 `validation-report.md`，`distill-meta` 只读其 frontmatter（score + verdict），不读 body——**强制防止"自圆其说"**。

Verdict 分三档：
- **PASS** (≥82 raw) → 交付
- **CONDITIONAL_PASS** ([75, 82)) → 交付 + 显示建议整改项
- **FAIL** (<75) → 回 Phase 2 重跑；3 次仍 FAIL 阻塞交付

这是**外部评判员**模式，和 skill-evolve 的"独立 subagent 评分"同源。

### 为什么 density 评分独立于 12 维？

Density = 每 1KB 文字包含的信息量。一个 persona skill 可以在 12 维 rubric 上刷高分（每维都"提到"了），但密度低 = 全是套话。

独立的 density floor（< 3.0 强制 FAIL）防止**通过堆字数刷过 12 维**的作弊。这也是为什么 `persona-judge` 的 rubric 有反作弊章节。

### 为什么要 execution-profile（v0.3.0 新增）？

描述 ≠ 执行。`mental-models` 说"他怎么想"、`decision-heuristics` 给 IF-THEN 规则、`expression-dna` 说"怎么说"——三者加起来仍然是**描述性**的。加载 persona skill 后让 Claude 执行一个实际任务（拆解问题、选方案、判断要不要回头改），它会在**决策瞬间**漂回"标准中性助手"——因为描述没告诉它"现在这一秒该做什么"。

解法：从 `knowledge/` 的**具体事件**反推**指令性**的"情境 → 动作"条款。方法来自：

- **Klein 的 Recognition-Primed Decision 模型**（Klein 1998）：80% 专家决策不是列表权衡，是"识别情境 → 第一可行方案 → 心理模拟"。persona skill 的 Decision Making 段不能充斥"列 3 个选项权衡利弊"——那是 GPT 中性句式，不是 RPD 风格。
- **CDM（Critical Decision Method，Hoffman-Crandall-Shadbolt 1998）**：从具体事件反向采访、套 10 项标准 probe（cues / knowledge / analogues / goals / options / experience / aiding / time pressure / errors / hypotheticals）追问隐性知识。
- **Macrocognition 8 类**（Klein et al. 2003）：Sensemaking / Decision Making / Planning / Adaptation / Problem Detection / Coordination / Managing Uncertainty / Mental Simulation——任意任务执行时反复出现的 8 类认知活动，作为 Profile 的分类骨架。

三条必须强制检查的红线：
1. **专家说的 ≠ 专家做的**（Ericsson & Ward）—— evidence 不能全是自述，必须有事件/行为佐证。
2. **80% 专家决策是 RPD 风格，不是分析比较** —— Decision Making 段里"列表对比"句式占比 > 50% 是红旗。
3. **颗粒度必须是"情境-行动对"，不是抽象原则** —— 反例："注重长期价值"（Claude 不知道"长期"指什么）；正例："识别到方案有'为未来不存在的需求做准备'的味道 → 直接砍掉，从剩下里选 6 个月后改起来代价最小的"。

诚实提醒：CTA/CDM 原本是**人采访人**的方法；LLM 从语料"模拟采访"质量有上限。但比凭空让 Claude 总结高得多——损耗对照实验在 v1.0.0 前完成。

execution-profile **不取代**任何现有组件——它挂在组件图出口，把碎片编译成 Claude 运行时查询的"指令表"。见 `skills/distill-meta/references/extraction/cdm-4sweep.md`。

---

## 自包含与扩展性的矛盾，及其解法

自包含要求产物零依赖；扩展性要求组件 / schema 可迭代。两者冲突于一个问题：**旧 persona skill 用旧版组件，新版组件更好了，怎么升级？**

两种错误解法：
- 动态加载（违反自包含）
- 全部重跑（丢失用户编辑）

v0.2.0 的解法是 **Migrator Agent**（`agents/migrator.md` + `references/migration.md`）：
- `PLAN` 模式：只生成 diff，不改文件
- `APPLY` 模式：执行 diff，保留 `knowledge/` 和用户标注的编辑
- 用户手改过的组件文件**拒绝自动迁移**——显示 diff，让用户决定
- 迁移后 grep self-containment 不变量；违反则回滚

这把"升级"和"独立性"解耦了：升级是**生产者的一次性动作**，产物仍然自包含。

---

## 社区可扩展 schema —— 插件内的小型生态

v0.2.0 通过 `contracts/schema-extension-contract.md` 开放社区贡献。新 schema 只要：
1. 带约定 frontmatter（`schema_type_origin: community` 等字段）
2. 含 7 个 H2 段落（identity-requirements / component-map / extraction-pipeline / validation-focus / failure-modes / test-corpus / credits）
3. 附测试语料（能通过 `persona-judge` 密度与 rubric 最低分）

就可以放进 `references/schemas/community/` 并被 `distill-meta` Phase 0.5 自动发现。核心 9 schema 由维护者保证，community schema 谁贡献谁负责。`manifest.schema_type_origin` 让下游消费者（router / judge / debate）在需要时区分。

这是**「核心小 + 边缘开放」**的生态策略——和 CRAN / PyPI 的逻辑同源。

---

## 不做什么（Non-Goals）

1. **不做实时抓取**：distill-collector 只消化已导出的语料，不主动爬网站（合规边界）
2. **不做 persona-as-a-service**：产物是 skill 文件，不是 API endpoint
3. **不做 ground-truth 评估**：persona-judge 评"像不像这个人"，不评"说得对不对"——后者需要外部事实核查
4. **不做自动多 persona 融合**：融合 2 个 persona 成第三个会破坏两者的稳定压缩；想做融合请用 `persona-debate` 让它们对话
5. **不做跨会话记忆持久化**：persona skill 是"只读"的人格快照；对话中的 correction 写到 `correction-layer.md` 需要用户显式触发

---

## 诚实的边界（与 v1.0.0 的距离）

- 9 个 schema 都带 `unvalidated: true`——**还没有一个真实 persona 被端到端 dog-food 跑通过**。v1.0.0 前提。
- 7 个已知安全缺口（`integration.md §6.2`）——自由文本 PII / 同意绕过 / prompt injection / manifest 欠约束 / rubric gaming / 自包含逃逸 / schema 误用。使用真实语料前必读。
- 蒸馏规则体系（executor schema）的 computation-layer 接口只在 executor 内完整；跨 schema 的「可计算层挂载」是 v2。
- 6 个聊天平台（WeChat / QQ / Feishu / Slack / Dingtalk / Telegram）+ 音视频 + OCR 仍然 spec-only。得自己导出后管到 `generic_import.py`。

---

## 和其它相关项目的关系

- **nuwa-skill**：自包含产物思想的源头。persona-distill 扩展了它的 schema 参数化。
- **persona-judge**：本插件自带，但理念可复用——"独立评判员 + 活体测试"是通用模式。
- **skill-evolve**（同市场）：评判一次 vs 迭代进化的区别。可串联：judge 出基线 → evolve 循环 → judge 出终值。
- **forge-teams**：用 persona skill 做 agent 团队里的固定角色（"请 distilled-jobs 参加 P2 架构评审"）。这是下游使用。
- **Karpathy autoresearch / darwin-skill**：skill-evolve 的上游；persona-distill 的 Phase 2.5 多轮 + Phase 4 独立验证吸收了同样的"外部反馈循环"思想。

---

## 阅读顺序建议

1. 本文件（**原理**）—— 为什么这么设计
2. `architecture.md`（**架构**）—— 组件如何拼装、数据如何流动
3. `integration.md`（**布线**）—— 5 个 skill + 4 个契约的具体连接
4. `schema-contribution-guide.md`（**扩展**）—— 如何贡献新 schema
5. `credits.md`（**致谢**）—— 借鉴来源

按需深入。本文件读完，你已经能在设计对话中代表本插件发表观点。
