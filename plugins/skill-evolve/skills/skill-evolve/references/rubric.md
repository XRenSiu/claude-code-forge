# 9 维评分 Rubric（满分 100）

> 这份 rubric 是 skill-evolve 的"度量衡"。所有 subagent 打分时，必须把这份原文作为 prompt 的一部分一字不差地传给评估 agent，不要二次概述。

整体配比：**结构维度 60 分 + 效果维度 40 分**。前者是静态分析，后者是真正干跑测试。

## v0.2 的 rubric 升级（来自 SkillLens / SkillOpt 研究）

复旦×微软 **SkillLens**（arXiv 2605.23899）实测了「什么样的 skill 真正有效」，结论直接重塑了这份 rubric：

1. **三个高信号维度**：失败机制编码 / 可执行具体性 / 高风险行动黑名单——这三维各自单独就能把「成对判断准确率」从 46.4% 提到 64%+，合起来到 **73.8%**。本版把它们提为**结构维度里权重最高的三维（共 32/60）**。
2. **排版/格式几乎不预测效果**：把同一份 skill 重写成不同排版，下游效果在统计上无差异（p > 0.34）。所以「工作流清晰度」「架构精简度」这类偏化妆的维度被**降权**。
3. **必须测负迁移**：SkillLens 发现 25% 的 skill 实际**拖累**了 agent（某些领域 47%）。所以效果维度强制跑**「带 skill vs 不带 skill」基线对比**，而不只是「带 skill 做对没」。带 skill 还不如不带 = 负迁移 = 致命，不允许 KEEP / 不允许交付。

---

## 结构维度（60 分）

每维按 0/2/5/8/10 五档锚点评分，再乘各自权重折算。下面每维标注了 **满分权重**。

### 1. 触发与 Frontmatter 质量（Trigger & Frontmatter, 满分 8）

> frontmatter 的 description / when_to_use / Triggers 是否覆盖真实使用场景的多种说法，能否被正确路由。

- **10**：description 含中英双语；triggers 列 ≥6 种用户措辞（含正式/口语/缩写）；when_to_use 含 3+ 正面场景 + 1+ 反面场景
- **8**：覆盖大部分场景但缺口语 / 反面场景
- **5**：只列 2-3 个标准触发词
- **2**：只有一个触发词
- **0**：触发字段缺失或模糊到无法路由

### 2. 工作流清晰度（Workflow Clarity, 满分 8）

> 步骤是否有序、可执行、无歧义。（注：SkillLens 表明「读起来顺」本身不强预测效果，故此维降权——别为了排版漂亮反复刷这一维。）

- **10**：编号阶段/步骤明确分隔；每步有动作动词；步骤间依赖明确
- **8**：阶段化叙述但缺编号；偶有跳跃但能跟上
- **5**：长段落叙述，需读两遍才能理出顺序
- **2**：只有原则、没有步骤
- **0**：完全无流程描述

### 3. 失败机制编码（Failure-Mechanism Encoding, 满分 12）★ SkillLens 高信号维

> 不能只写「正确流程」，必须写清**什么情况会出错、出错了走哪条分支**——即可执行的 `如果 X 则 Y，否则 Z`。这是 SkillLens 验证过的第一高信号维度，**列举异常 ≠ 编码失败机制**。

- **10**：关键步骤都配「触发条件 → 失败征兆 → 分支动作」三元组；有 3+ 条 `如果…则…否则…` 形式的可执行分支；失败可被检测并有回退
- **8**：主要失败路径有分支，但部分只描述"会失败"没给"走哪条"
- **5**：列了异常场景，但停在「如果失败就报错/重试」级别，不具体到分支
- **2**：只有正向 happy path，异常一笔带过
- **0**：无任何失败机制讨论

### 4. 可执行具体性（Executable Specificity, 满分 12）★ SkillLens 高信号维

> 指令要么明确、要么不写——**禁止「建议 / 可以考虑 / 视情况而定 / 最好 / 尽量」等软化措辞**。SkillLens 验证过的第二高信号维度。配模板 / 示例 / 数字约束 / 具体路径。

- **10**：关键指令零软化措辞；每条配模板（代码块）/ 示例 I-O / 数字约束（行数、字数、轮数）/ 具体路径
- **8**：大部分指令具体，残留极少数软化措辞
- **5**：原则与具体约 1:1；软化措辞与硬指令混杂
- **2**：通篇「应该」「需要」「最好」「视情况」
- **0**：纯口号，无任何可直接执行的指令

### 5. 高风险行动黑名单（High-Risk Action Blacklist, 满分 8）★ SkillLens 高信号维

> 是否有**独立章节**明确告诉模型「绝对不要做什么」。SkillLens 验证过的第三高信号维度——黑名单不是散落在正文里的零星提醒，而是集中、显眼、可核对的一节。

- **10**：有独立的「不要做 / Never / 禁止」章节；列 ≥3 条具体高风险动作（含为什么危险）；与正文流程交叉引用
- **8**：有集中的负面清单但条目偏少或缺「为什么」
- **5**：负面提醒散落在正文，无独立章节
- **2**：仅 1 条零星「注意不要…」
- **0**：完全没有任何禁止性约束

### 6. 检查点设计（Checkpoint Design, 满分 6）

> 流程中是否有中间验证点 / 用户确认点 / 可恢复的存档点。

- **10**：每个关键阶段后都有 checkpoint（用户确认 / 文件落盘 / 状态可查）；中断后能恢复
- **8**：有 checkpoint 但分布不均，部分长流程缺失
- **5**：只在最终输出前有一个 checkpoint
- **2**：完全 fire-and-forget
- **0**：连最终输出都不可验证

### 7. 架构精简度（Architecture Conciseness, 满分 6）

> 主 SKILL.md 是否精简、知识是否合理分层。（注：SkillLens 表明纯格式重排不改变效果，此维**已大幅降权**——不要为了刷它做无意义的拆分/重排。）

- **10**：SKILL.md ≤500 行；详规则放 references/；模板放 templates/；目录树清晰
- **8**：SKILL.md ≤800 行，分层基本清晰
- **5**：1000+ 行，全塞一处
- **2**：2000+ 行
- **0**：全混在一起且无目录结构

---

## 效果维度（40 分）

不能只看文本，必须**让独立 subagent 加载这个 SKILL.md 干跑，并跑一个不加载 skill 的基线做对比**。每个测试都要记录两组实际输出。

### 8. 实测增益 vs 无 skill 基线（Measured Gain over Baseline, 满分 25）★ 单一最大权重

> 这是整套 rubric 信号最强的一维（对标 Darwin 的「实测表现」）。用 3 个有明确期望方向的 prompt，**各跑两遍**：一遍带 skill（with_skill），一遍不带 skill 只用通用 Claude（baseline）。判三件事：① with_skill 是否完成意图？② 相比 baseline 提升明不明显？③ 有没有引入负面影响（冗余/跑偏/格式怪/比 baseline 还差）？

每个测试 0-7 分（共 21，截至 20）+ 增益调整：
- **7**：with_skill 完全按 SKILL.md 流程、输出正确、且**明显优于 baseline**
- **5**：with_skill 方向正确并优于 baseline，但跳过某些 SKILL.md 明确要求的步骤
- **3**：with_skill 方向部分正确，或与 baseline 难分高下（skill 没带来增益）
- **1**：with_skill 跟没加载差不多
- **0 或负迁移**：with_skill **劣于** baseline → 该测试记 0 且置顶层 `negative_transfer: true`

**负迁移是致命项**：任一测试 with_skill < baseline，本维封顶 8 分，并设 `negative_transfer: true`。带 skill 还不如不带的 skill，分数再高也不许 KEEP、不许交付。

3 个测试 prompt 来源（按优先级）：① 用户提供的 expected behavior 测试集；② SKILL.md 的 examples / when_to_use 场景；③ 自动生成（基于 description 推断典型用户问题，须用户在 Phase 0.5 确认）。

### 9. 边缘 + 负迁移 + 风格（Edge + Negative-Transfer + Voice, 满分 15）

> 边缘：超出 skill 设计范围的相邻问题；负迁移：skill 在边缘问题上是否反而误导；风格：输出是否有该 skill 的辨识度。

**边缘子项（0-8）**：
- **8**：明确识别超范围 + 给降级方案 / 相关 skill 推荐，且不比 baseline 差
- **5**：适度不确定但仍尝试合理回答
- **2**：硬答，错误自信（且若比 baseline 还差，标负迁移）
- **0**：崩溃

**风格子项（0-7）**：
- **7**：输出明显带本 skill 的格式 / 用语 / 结构（阶段编号、专属术语、模板填充）
- **5**：风格部分体现，与通用输出可区分
- **2**：与不加载 skill 的通用回答几乎无差
- **0**：风格反向（输出像别的 skill）

---

## subagent 评分输出 Schema（强制）

每次评估 subagent 必须返回严格 JSON：

```json
{
  "rubric_version": "2.0",
  "skill_path": "<被评估的 SKILL.md 路径>",
  "negative_transfer": false,
  "scores": {
    "trigger_frontmatter":      { "weighted": 7,  "raw_anchor": "8档",  "rationale": "<引用具体段落>" },
    "workflow_clarity":         { "weighted": 6,  "raw_anchor": "8档",  "rationale": "..." },
    "failure_mechanism":        { "weighted": 9,  "raw_anchor": "8档",  "rationale": "..." },
    "executable_specificity":   { "weighted": 10, "raw_anchor": "8档",  "rationale": "..." },
    "highrisk_blacklist":       { "weighted": 4,  "raw_anchor": "5档",  "rationale": "..." },
    "checkpoint_design":        { "weighted": 4,  "raw_anchor": "8档",  "rationale": "..." },
    "architecture_conciseness": { "weighted": 5,  "raw_anchor": "8档",  "rationale": "..." },
    "measured_gain": {
      "weighted": 16,
      "test_results": [
        { "prompt": "...", "expected_direction": "...", "with_skill_output": "...", "baseline_output": "...", "beats_baseline": true,  "sub_score": 5 },
        { "prompt": "...", "expected_direction": "...", "with_skill_output": "...", "baseline_output": "...", "beats_baseline": true,  "sub_score": 5 },
        { "prompt": "...", "expected_direction": "...", "with_skill_output": "...", "baseline_output": "...", "beats_baseline": true,  "sub_score": 4 }
      ],
      "rationale": "（注：若任一 beats_baseline 为 false 且 with_skill 劣于 baseline，则该 sub_score=0 且顶层 negative_transfer=true）"
    },
    "edge_negtransfer_voice": {
      "weighted": 11,
      "edge_sub_score": 6,
      "voice_sub_score": 5,
      "edge_prompt": "...",
      "edge_with_skill_output": "...",
      "edge_baseline_output": "...",
      "voice_analysis": "<100 字风格分析>"
    }
  },
  "total": 72,
  "weakest_dimension": "highrisk_blacklist",
  "weakest_rationale": "<最弱维度的核心问题，要可被 mutate 阶段直接动手>"
}
```

- 每维 `weighted` 已经是「锚点 raw 分 × 该维权重 / 10」折算后的值；`total` = 9 维 weighted 之和（满分 100）。
- `negative_transfer` 为 true 时，**无论 total 多高都不许 KEEP、不许交付**（见 ratchet-protocol 决策表）。
- `weakest_dimension` 是**下一轮 mutate 的输入**，必须可执行——不要写「整体不够好」这种废话。

---

## 校准指南（开始迭代前必读）

启动 skill-evolve 之前，**强烈建议**先在 3-5 个已知好/坏的 skill 上跑一次评估，校准 rubric：

1. 选 1 个公认高质量 skill（如 Anthropic 官方 skill-creator）+ 2 个粗糙 skill
2. 让 2 个独立 subagent 分别评分（多评委是默认，见 test-protocol）
3. 检查：高质量 skill 是否 ≥80？粗糙 skill 是否 ≤50？两个 subagent 分差是否 ≤10？负迁移项是否被正确识别？
4. 若任一不满足 → 不要启动自动循环，先调 rubric 锚点描述

**inter-rater reliability** 是这套机制的根。rubric 不稳，循环越跑越歪——这正是 SkillLens 46.4% 警告的本质。
