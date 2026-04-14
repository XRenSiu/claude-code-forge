# 8 维评分 Rubric（满分 100）

> 这份 rubric 是 skill-evolve 的"度量衡"。所有 subagent 打分时，必须把这份原文作为 prompt 的一部分一字不差地传给评估 agent，不要二次概述。

整体配比：**结构维度 60 分 + 效果维度 40 分**。前者是静态分析，后者是真正干跑测试。

---

## 结构维度（60 分）

每维满分 10 分，0/2/5/8/10 五档锚点评分。

### 1. 工作流清晰度（Workflow Clarity, 0-10）

> 步骤是否有序、可执行、无歧义。一个新 agent 第一次读 SKILL.md 能不能立刻知道「先做什么、再做什么」。

- **10**：用编号阶段（Phase 0/1/2…）或编号步骤明确分隔；每步有动作动词（执行性）；步骤间依赖明确
- **8**：阶段化叙述但缺少编号；偶有跳跃但能跟上
- **5**：长段落叙述，需要读两遍才能理出顺序
- **2**：只有原则、没有步骤
- **0**：完全无流程描述

### 2. 边界条件（Boundary Handling, 0-10）

> 异常输入、失败回退、超出范围、用户中断如何处理是否被定义。

- **10**：明确列出 3+ 种异常场景及对应动作；有失败回退路径；有「不要做什么」的负面清单
- **8**：列出主要异常但回退路径模糊
- **5**：提到「如果失败就报错」但不具体
- **2**：只有正向 happy path
- **0**：无任何边界讨论

### 3. 检查点设计（Checkpoint Design, 0-10）

> 流程中是否有中间验证点 / 用户确认点 / 可恢复的存档点。

- **10**：每个关键阶段后都有 checkpoint（用户确认 / 文件落盘 / 状态可查询）；中断后能恢复
- **8**：有 checkpoint 但分布不均，部分长流程缺失
- **5**：只在最终输出前有一个 checkpoint
- **2**：完全 fire-and-forget
- **0**：连最终输出都不可验证

### 4. 指令具体性（Instruction Specificity, 0-10）

> 指令是否给出模板、示例、数字约束、具体路径，而非抽象原则。

- **10**：每个关键指令都配有：模板（代码块）/ 示例输入输出 / 数字约束（行数、字数、轮数）/ 具体文件路径
- **8**：大部分指令具体，少数仍抽象
- **5**：原则与示例约 1:1
- **2**：通篇是「应该」「需要」「最好」
- **0**：纯口号

### 5. 触发覆盖度（Trigger Coverage, 0-10）

> frontmatter 的 description / when_to_use / Triggers 字段是否覆盖真实使用场景的多种说法。

- **10**：description 含中英双语；triggers 列出 ≥6 种用户可能的措辞（含正式/口语/缩写）；when_to_use 含 3+ 个正面场景 + 1+ 个反面场景
- **8**：覆盖大部分场景但缺少口语 / 反面场景
- **5**：只列了 2-3 个标准触发词
- **2**：只有一个触发词
- **0**：触发字段缺失或模糊到无法路由

### 6. 架构精简度（Architecture Conciseness, 0-10）

> 主 SKILL.md 是否精简（建议 ≤500 行），知识是否合理拆分到 references/ 与 templates/。

- **10**：SKILL.md ≤500 行；详细规则放 references/；模板放 templates/；目录树清晰
- **8**：SKILL.md ≤800 行，分层基本清晰
- **5**：SKILL.md 1000+ 行，所有内容塞在一处
- **2**：SKILL.md 2000+ 行
- **0**：所有内容混在一起且无目录结构

---

## 效果维度（40 分）

不能只看文本，必须**让独立 subagent 加载这个 SKILL.md 然后干跑**。每个测试都要记录 agent 实际输出。

### 7. 已知测试通过率（Known Test Pass Rate, 0-20）

> 用 3 个有明确期望答案 / 期望方向的 prompt 测试，看 agent 加载该 skill 后能否做对。

每个测试 0-7 分（共 21 分，截至 20）：
- **7**：完全按 SKILL.md 流程执行，输出方向正确，关键步骤齐全
- **5**：方向正确但跳过某些 SKILL.md 明确要求的步骤
- **3**：方向部分正确或步骤错乱
- **1**：完全没按 skill 走，跟没加载差不多
- **0**：直接报错或拒答

3 个测试 prompt 来源（按优先级）：
1. 用户提供的 expected behavior 测试集
2. SKILL.md 的 examples / when_to_use 中的场景
3. skill-evolve 自动生成的标准测试集（基于 description 推断典型用户问题）

### 8. 边缘 + 风格测试（Edge + Voice Test, 0-20）

> 边缘 case：超出 skill 设计范围的相邻问题；风格：输出是否有该 skill 的辨识度。

**边缘子项（0-10）**：
- **10**：明确识别为超出范围 + 给出降级方案 / 相关 skill 推荐
- **7**：表达适度不确定但仍尝试合理回答
- **3**：硬答，给出错误自信
- **0**：崩溃

**风格子项（0-10）**：
- **10**：输出明显带本 skill 设计的格式 / 用语 / 结构（如阶段编号、专属术语、模板填充）
- **7**：风格部分体现，与通用 AI 输出可区分
- **3**：与不加载 skill 的通用回答几乎无差
- **0**：风格反向（输出像别的 skill）

---

## subagent 评分输出 Schema（强制）

每次评估 subagent 必须返回严格 JSON：

```json
{
  "rubric_version": "1.0",
  "skill_path": "<被评估的 SKILL.md 路径>",
  "scores": {
    "workflow_clarity": { "score": 7, "anchor": "8档", "rationale": "<引用具体段落>" },
    "boundary_handling": { "score": 4, "anchor": "5档", "rationale": "..." },
    "checkpoint_design": { "score": 6, "anchor": "5档", "rationale": "..." },
    "instruction_specificity": { "score": 8, "anchor": "8档", "rationale": "..." },
    "trigger_coverage": { "score": 9, "anchor": "10档", "rationale": "..." },
    "architecture_conciseness": { "score": 7, "anchor": "8档", "rationale": "..." },
    "known_test_pass_rate": {
      "score": 14,
      "test_results": [
        { "prompt": "...", "expected_direction": "...", "actual_output": "...", "sub_score": 5 },
        { "prompt": "...", "expected_direction": "...", "actual_output": "...", "sub_score": 5 },
        { "prompt": "...", "expected_direction": "...", "actual_output": "...", "sub_score": 4 }
      ],
      "rationale": "..."
    },
    "edge_voice_test": {
      "score": 13,
      "edge_sub_score": 7,
      "voice_sub_score": 6,
      "edge_prompt": "...",
      "edge_output": "...",
      "voice_analysis": "<100 字风格分析>"
    }
  },
  "total": 68,
  "weakest_dimension": "boundary_handling",
  "weakest_rationale": "<最弱维度的核心问题，要可被 mutate 阶段直接动手>"
}
```

`weakest_dimension` 字段是**下一轮 mutate 的输入**，所以必须可执行——不要写「整体不够好」这种废话。

---

## 校准指南（开始迭代前必读）

启动 skill-evolve 之前，**强烈建议**先在 3-5 个已知好/坏的 skill 上跑一次评估，校准 rubric：

1. 选 1 个公认高质量 skill（如 Anthropic 官方 skill-creator）+ 2 个粗糙 skill
2. 让 2 个独立 subagent 分别评分
3. 检查：高质量 skill 是否得 ≥80？粗糙 skill 是否得 ≤50？两个 subagent 分差是否 ≤10？
4. 若任一不满足 → 不要启动自动循环，先调 rubric 锚点描述

**inter-rater reliability** 是这套机制的根。rubric 不稳，循环越跑越歪。
