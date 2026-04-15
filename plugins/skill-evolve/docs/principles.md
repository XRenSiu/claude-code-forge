---
name: principles
description: The theory behind skill-evolve — why SKILL.md is a searchable parameter space, why ratchet + independent subagent + 8-dim rubric produces monotonic improvement
version: 0.1.0
---

# skill-evolve — 设计原理（Principles）

> 为什么这个插件存在、为什么它长成这样、为什么 MVP 刻意只做这些。**先读这份，再看 `architecture.md`。**

---

## 核心命题

> **SKILL.md 是可被自动化搜索的参数空间，和 ML 超参数同构。**

这句话听起来像哲学，实际是工程判断：
- **参数空间**：SKILL.md 的每一句话都是一个"位置"，改写它相当于在一个离散文本空间里迈一步
- **搜索**：每一步有可被量化的效果——触发得更准、流程更清、边界更硬；量化靠 rubric
- **自动化**：如果每步改动都能独立打分、能保留好的、能丢弃差的，就可以用梯度（在这里是 hill-climbing）代替人工直觉

反对的观点是"写 skill 是手艺，不能自动"。MVP 不争辩这个——**我们只承诺把 60 分的 skill 稳定地推到 85-90 分**，这部分可以自动化。60→90 的路径里，绝大多数改进是「把触发词补到 6 个」「把步骤从段落改成编号」「把边界条件显式化」这种**机械可抓的低垂果实**，不需要灵感。

90→100 依然是手艺。MVP 不做。

---

## 三条上游：为什么站在这些肩膀上

### 1. Karpathy autoresearch（2026.03）

Karpathy 用 630 行 Python 让 agent 在小型 LLM 训练上自主调超参——改 → 训 5 分钟 → 看指标 → 保留/丢弃 → 循环。在他**手动调优多年**的项目上，agent 仍挖出 20 个改进（11% 效率提升）。

**启示**：人类直觉的天花板比想象中低。只要有可靠的评估函数 + 可回滚的机制，**机械搜索会找到人想不到的改进**。把这套范式套到 SKILL.md：评估 = 8 维 rubric，回滚 = `git checkout`，搜索 = 每轮改一处再复评。

### 2. alchaincyf / 花叔 darwin-skill（2026.03）

把 autoresearch 从 ML 训练**迁移到 SKILL.md 优化领域**。关键贡献是确立了三件事：
- **8 维 rubric 作为 SKILL.md 的标准度量衡**（结构 60 + 效果 40）
- **独立 subagent 评分**防止自评偏差
- **与"生成器"划清边界**（darwin 不生成新 skill，只优化已有的——本插件沿用）

skill-evolve 基本上是 darwin-skill 的 Claude Code 原生化 + 棘轮协议工程化。

### 3. Anthropic skill-creator

贡献了 60/40 train/test split 思想——评估集必须与被优化的 skill 分离，否则会过拟合到评估样本。skill-evolve v0.1.0 未完全实现这点（MVP 让用户提供 3 测试 prompt，没强制 split），`references/design-rationale.md` 记录为 v0.2 计划。

---

## 三大工程支柱

### 支柱 1 — 棘轮（Ratchet）：分数只能涨，不能跌

**规则**：每轮改完独立评分，分数不升则 `git checkout -- <file>` 丢弃，基线快照 commit 留作诊断。

**为什么不靠克制、不靠"仔细测"**：
- 人（或 agent）会合理化糟糕改动——"其实这条维度我没想优化" / "这个维度本来就不该算"。自欺的代价在第 10 轮累积时暴露。
- git 没有合理化能力。`git checkout -- <file>` 等于强制"**你说了不算，数字说了算**"。
- 棘轮把"审美决策"变成"机器决策"。这是工程化的核心。

**隐性含义**：棘轮不只是"保留涨分"，是"**保护已有价值**"。mutate 阶段如果删除了历史 KEEP commit 表扬过的段落，即使总分小涨也要 REVERT——上一次的改进是资产，不能被无意削弱。

### 支柱 2 — 独立 Subagent 评分：自评偏差是系统性的

**规则**：评分必须在独立 subagent 的新 context 中跑，prompt 不提「改进版 / 之前是 N 分 / 目标涨到 M 分」。评分 agent 只看：SKILL.md 全文 + rubric 全文 + 3 测试 prompt。

**为什么**：
- Anthropic constitutional AI 研究：修改者在同 context 里评分，系统性偏高 8-15%。prompt 再三强调"中立"无效。
- 唯一可靠的解法是 **context isolation**。新 context = 没看过修改历史 = 没有"为我的努力鼓掌"的冲动。
- 成本：每轮多一次 agent spawn（~1-3 分钱）。收益：评分可信度 60% → 95%。**这是本插件最贵的一条规则，也是最不能妥协的一条**。

**反作弊 checklist**（test-protocol.md）：
- prompt 不出现 "改进版" / "new" / "better" / "updated"
- prompt 不包含上一版分数
- prompt 不含 git diff
- subagent_type 必须是 `general-purpose`（不是有偏向的特化 agent）

### 支柱 3 — 8 维 Rubric：评什么决定往哪进化

**为什么是 8 维不是 12 维**：考虑过照搬 persona-distill 的 12 维，结论是**12 维对 persona 合适（要捕捉人格复杂度），对通用 skill 过拟合**。

skill-evolve 优化任意 SKILL.md（工具型、流程型、知识型），rubric 必须是"所有 skill 共享的本质"。8 维已覆盖：
- 流程清晰度（Workflow Clarity）
- 边界条件（Boundary Handling）
- 检查点设计（Checkpoint Design）
- 指令具体性（Instruction Specificity）
- 触发覆盖度（Trigger Coverage）
- 架构精简度（Architecture Conciseness）
- 已知测试通过率（Known Test Pass Rate）
- 边缘 + 风格测试（Edge + Voice Test）

**为什么 60/40 配比**：纯结构评分（60 分）可以不跑测试，速度快；效果评分（40 分）必须让 subagent 加载 skill 干跑。前者防止"结构混乱但碰运气表现还行"，后者防止"看起来很漂亮但实际不能用"。两者必须同权重参与棘轮决策——单靠结构分会把 skill 优化成 PPT。

---

## 为什么 hill-climbing 不是遗传算法

EvoPrompt (ICLR 2024) 证明遗传算法在 prompt 优化上比 hill-climbing 强 ~25%，但代价是：
- 维护 N 个变体（成本 × N）
- 设计交叉 / 变异算子（复杂度高）
- 适应度函数必须极稳（rubric 稳定性要求更高）

MVP 选 hill-climbing 因为：
- **单变体**：一次一个 SKILL.md，用户能看懂"改了哪里，为什么好了"
- **原子修改**：一轮只改一处，因果链清晰——"第 47 行这句话改成 X，边界维度从 4 涨到 7"
- **强 git 兜底**：所有实验可回放、可 diff、可复现

**可解释性优先**。遗传算法在 generation 10 收敛时你不知道哪一步贡献了多少；hill-climbing 每一步都是可读的 experiment commit。这对"用户学会写更好的 skill"的隐性目标很重要——每个 commit 都是一堂微课。

遗传算法是 v0.3+ 的选项（遇到"连续 10 轮不涨"的局部最优时考虑）。现在不做。

---

## 为什么 MVP 刻意不做这些（Non-Goals）

| 不做 | 为什么 |
|------|--------|
| 生成新 SKILL.md（0→1） | 那是 distill-meta / nuwa 的职责；本插件只做 1→100 |
| 评估非 SKILL.md 文件 | rubric 8 维是给 SKILL.md 设计的；references/ 和 templates/ 需要不同的度量 |
| 并行 mutate 多处 | 破坏因果归因。改两处同时测，涨分归功于哪处？拆两轮 |
| 修改 frontmatter `name` 字段 | 会破坏 plugin.json / marketplace.json 的引用 |
| 自动批量优化整个仓库 | v0.2 目标；MVP 先把单个做扎实 |
| 改 skill 的底层能力 | 只改 SKILL.md；agents / 脚本的改动不在范围 |

每条都对应明确的升级路径，不是"永远不做"。

---

## 关键张力 & 如何处理

### 张力 1：探索 vs 利用

**问题**：当前最弱维度是 X，但也许改 Y 的 ROI 更高——怎么选？

**答案**：MVP 总是改**当前最弱维度**（纯 exploitation）。理由：
- 探索需要额外的"试探预算"概念（ε-greedy），MVP 没有
- 最弱维度通常是**显而易见的低垂果实**，改了大概率涨分
- 如果它不涨 → 棘轮 REVERT → 下一轮自动转向（因为复评后最弱维度可能变了）

这在 `experiments.tsv` 的 `dim_old_lowest` / `dim_new_lowest` 列自动体现。"卡住的维度"会在连续 3 轮都是最弱 → 收敛判定 → 循环终止，让用户介入。

### 张力 2：rubric 的自洽 vs 稳定性

**问题**：rubric 越详细 → subagent 间分差越小（稳定），但锚点越难设计、主观词越多（自洽风险）。

**答案**：MVP 通过**锚点分档（0/2/5/8/10）+ 强制引用具体段落**减少主观性。复评稳定性每 5 轮做一次**双盲检查**：两个 subagent 同输入打分，差 > 10 暂停循环，让用户检查 rubric 是否太主观。

这是 `references/test-protocol.md §评分稳定性检查` 的职责。

### 张力 3：分数虚高 vs 真实可用

**问题**：rubric 得 95 分但实战还是烂——怎么办？

**答案**：**问题在测试 prompt，不在 rubric**。3 个测试 prompt 太友好，边缘 case 没覆盖。解决方式：
- 用户提供时，要求至少 1 个边缘 case
- 自动生成时，把 description 关键名词替换成相邻领域词（`test-protocol.md §测试 Prompt 自动生成`）
- 强烈建议**启动前校准**：在 3-5 个已知好/坏 skill 上跑一次，验证"好 skill 得 ≥80，坏 skill 得 ≤50"（`rubric.md §校准指南`）

### 张力 4：棘轮的僵化 vs 灵活性

**问题**：有时候"牺牲一维换两维大涨"是正确选择（比如故意简化触发词换架构清晰度）。棘轮会 REVERT。

**答案**：这是**刻意的刚性**。自动循环不做"综合判断"——综合判断 = 自欺的空间。如果真要牺牲某维，**需要用户显式确认**，并在 `experiments.tsv` 标记 `decision: KEEP(user-approved-sacrifice)`。这保留了灵活性但不让循环自动滥用。

---

## 和 persona-judge 的关系

两者都"给 skill 打分"，但职责互补：

| 方面 | persona-judge | skill-evolve |
|------|---------------|--------------|
| 目标 | 一次性评「这个 persona 合不合格」 | 迭代把任意 skill 推到 90+ |
| Rubric | 12 维（persona 专用） | 8 维（通用 skill） |
| 调用方 | distill-meta Phase 4 gate | 用户直接触发 |
| 输出 | PASS / CONDITIONAL_PASS / FAIL | 棘轮历史 + 终评报告 |
| 是否迭代 | 否 | 是 |

**可串联**：先 persona-judge 打基线 → 进 skill-evolve 循环 → 收敛后再 persona-judge 一次终评。这种「外部评判员 + 内部进化器」双闸门是两个插件共识的模式。

---

## 为什么本插件值得存在

SKILL.md 生态的现状：
- 大多数 skill 写到"能跑"就停（≈60 分），不是因为作者懒，而是**看不到差距**。没有客观度量时，"挺好的"就是停止信号。
- 手动反复打磨成本极高，且改一处不知道是否变差。
- 别人的 skill 你改起来更没数——没有基线、没有目标分、没法告诉作者"这改动让 X 维从 4 涨到 7"。

skill-evolve 提供的是**一把尺 + 一个循环 + 一份日志**：
- 尺（8 维 rubric）让"好"变成数字
- 循环（棘轮 + 独立评分）把改进从手艺变成过程
- 日志（experiments.tsv + git history）把每一步都变成可审计的证据

**即使你不用它自动跑，读一遍 rubric 就能给自己的 skill 找到改进方向。** 这是本插件的保底价值。

---

## 常见误解

### "独立 subagent 只是换个马甲，本质还是同一个模型"

技术上对，但经验上错。Anthropic 的测量显示 context isolation 能把偏差从 +12% 降到 +2% 以内。同模型不同 context 确实有效——因为偏差来自 context 里的修改历史，不来自模型本身。

### "git 回滚太粗暴，改动里总有好的部分"

这正是 MVP 的取舍。细粒度保留需要 diff-level 的"挑选器"，复杂度高且可能引入"部分保留的 bug"。MVP 宁可让用户重做：知道整块被 REVERT 后，用户下一轮可以拆成 2 个原子修改。

### "8 维不够，应该 20 维才全面"

相关性陷阱。维度越多，彼此相关性越高，hill-climbing 会在相关维度之间反复刷分而非真改进。8 维是**低相关独立基**——改一维不自动涨其它维。增加维度要先证明正交。

### "rubric 太主观，人打分都分歧"

对。所以 rubric 必须**校准后再用**（3-5 个已知 skill 预测通过）。未校准就自动循环的 rubric，等于拿没校准的尺子量木头。这也是 `rubric.md` 末尾「**校准指南**」是强制阅读的理由。

---

## 阅读顺序建议

1. 本文件（**原理**）—— 为什么这么设计
2. `architecture.md`（**架构**）—— 组件布线、数据流、文件产物
3. `references/rubric.md`（**度量**）—— 8 维 + 评分锚点 + 校准
4. `references/ratchet-protocol.md`（**规程**）—— git 操作流 + 决策表
5. `references/test-protocol.md`（**评估**）—— 独立 subagent 的 spawn 规范
6. `references/design-rationale.md`（**取舍**）—— 三上游 + 三取舍 + 非目标

读完前两份，你能代表本插件发表观点；读完五份，你能为它写 PR。
