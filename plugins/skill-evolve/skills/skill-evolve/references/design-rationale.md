# 设计理由（Design Rationale）

> 为什么 skill-evolve 长成这样？三个上游 + 三个取舍。

---

## 三个上游

### 1. Karpathy autoresearch（2026.03）

Karpathy 用一个 630 行 Python 脚本让 agent 在小型 LLM 训练上自主实验：修改超参数 → 训 5 分钟 → 检查指标 → 保留或丢弃 → 重复。在他**已手动调优多年**的项目上，agent 仍然找出 20 个改进（11% 效率提升）。

**借鉴**：
- 「修改 → 验证 → 保留/回滚」的 hill-climbing 主循环
- `experiment:` 前缀的 git commit 协议
- 失败实验留在 git history 用作未来诊断

### 2. alchaincyf/darwin-skill（2026.03）

花叔把 autoresearch 的范式从 ML 训练**迁移到 SKILL.md 优化**。核心创新：把"训练指标"换成 8 维 rubric，把"代码修改"换成文本修改，把"训练循环"换成 evaluate-improve-test-keep/revert 循环。

**借鉴**：
- 8 维 rubric（结构 6 维 + 效果 2 维，60+40 配比）
- 独立 subagent 评分（避免自评偏差）
- 与生成器（女娲）的角色边界划分

### 3. Anthropic skill-creator + Singularity-Claude

前者贡献了 60/40 train/test split 防过拟合的思想；后者贡献了「Haiku 评估降本，Sonnet 精评提质」的多模型策略。skill-evolve 暂未实现这两点（MVP 阶段不需要），但在 `references/rubric.md` 末尾留了校准提示作为种子。

---

## 三个取舍

### 1. 为什么是 8 维不是 12 维？

考虑过 persona-distill 的 12 维 rubric。结论：**12 维对 persona skill 合适（要捕捉人格复杂度），对通用 skill 过拟合**。

skill-evolve 优化的是任意 SKILL.md（工具型、流程型、知识型……），rubric 必须是「所有 skill 都共享的本质」。8 维已经覆盖了：流程、边界、检查点、具体性、触发、架构、已知效果、边缘+风格——再细分会导致维度间相关性过高，hill-climbing 会在相关维度上反复刷分而非真改进。

### 2. 为什么是 hill-climbing 不是遗传算法？

EvoPrompt（ICLR 2024）证明遗传算法在 prompt 优化上比 hill-climbing 强 25%，但需要：
- 维护多个变体（成本×N）
- 设计交叉/变异算子（复杂度高）
- 适应度函数稳定（rubric 必须极其可靠）

MVP 选 hill-climbing 是因为：**单变体、原子修改、强 git 兜底**，三者组合给出的「可解释性」远胜遗传算法。用户能看到「我改了第 47 行的一句话，A 维度从 5 涨到 7」，这种因果链是遗传算法天然丢失的。

未来如果遇到「连续 10 轮无提升」的局部最优，再考虑加变异机制。

### 3. 为什么强制独立 subagent 而不是「让模型保持中立」？

Anthropic 的 constitutional AI 研究显示：模型在「修改 + 评分」同上下文中，**系统性地**给自己改的版本打高分（偏差约 +8-15%）。哪怕在 prompt 里明确要求「中立评分」也无法消除。

唯一可靠的解法是 **context isolation**：评分 agent 在新 context 中启动，看不到改动历史。这是 darwin-skill 的核心机制，也是 skill-evolve 必须照搬的。

成本：每轮多一次 agent spawn（约 1-3 美分）。收益：评分可信度从 60% 提到 95%。值得。

---

## 与 persona-distill 的 persona-judge 的关系

`persona-judge` 是**一次性评分器**：跑一次 12 维测试，输出 PASS/CONDITIONAL_PASS/FAIL，不迭代。
`skill-evolve` 是**迭代进化器**：跑 N 轮评分 + mutate，直到收敛。

如果你只想知道「这个 skill 现在多好」→ 用 persona-judge（或借鉴它的 12 维 rubric）。
如果你想「让它真的变好」→ 用 skill-evolve。

两者可以串联：先 persona-judge 一次拿基线 → 进 skill-evolve 循环 → 收敛后再 persona-judge 一次终评。这种「外部评分员 + 内部进化器」的双闸门设计值得未来探索。

---

## 不做什么（明确的 non-goals）

skill-evolve 的 MVP 边界很重要：

- ❌ **不生成新 skill**：那是 distill-meta / nuwa 的领域
- ❌ **不评估非 SKILL.md 文件**：本 skill 只优化 SKILL.md 自身，不优化 references/、templates/ 内的内容
- ❌ **不并行 mutate**：原子性是核心约束，并行破坏因果归因
- ❌ **不修改 frontmatter 的 name 字段**：那会破坏 plugin.json / marketplace.json 的引用
- ❌ **不自动批量优化整个仓库**：批量模式是 v0.2 目标，MVP 只支持单个 skill

这些边界不是「以后也不做」，是「MVP 不做以避免范围爆炸」。每条都对应一个明确的 v0.x 升级路径。
