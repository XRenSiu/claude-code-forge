# Credits & Prior Art

> 设计综合了以下参考库的模式。标注 `[UNVERIFIED-FROM-README]` 的，是因为仓库无法 clone，只能从 README 片段反向推导，细节可能有偏差。

## 核心参考（Tier 1 — 必读）

| 库 | 贡献 | 本插件取之处 |
|----|------|------------|
| [alchaincyf/nuwa-skill](https://github.com/alchaincyf/nuwa-skill) | 认知 OS、三重验证、7 轴 DNA、6 agent 并行、Phase 0→4 主流程 | `public-mirror` schema 蓝本；提取框架基础；Research Review Checkpoint；Self-Contained 原则；`[UNVERIFIED-FROM-README]` |
| [titanwings/colleague-skill](https://github.com/titanwings/colleague-skill) | 双层架构（Work + Persona）、5 层人格、采集脚本、merger / correction | `collaborator` schema 蓝本；`persona-5layer`、`correction-layer` 组件；`[UNVERIFIED-FROM-README]` |
| [notdog1998/yourself-skill](https://github.com/notdog1998/yourself-skill) | 自蒸馏双层（self + persona）、WeChat/QQ parser | `self-memory` 组件；采集脚本参考；`[UNVERIFIED-FROM-README]` |
| [leilei926524-tech/anti-distill](https://github.com/leilei926524-tech/anti-distill) | 4 级密度分类器（SAFE / DILUTE / REMOVE / MASK）、稀释策略 | 反向用作**正向**密度评分；`persona-judge` density-scoring；`[UNVERIFIED-FROM-README]` |

## 新一代多维蒸馏（Tier 2）

| 库 | 贡献 | 本插件取之处 |
|----|------|------------|
| [agenmod/immortal-skill](https://github.com/agenmod/immortal-skill) | 7 persona 模板、12+ 平台、conflicts.md、统一 CLI、snapshot | `distill-collector` CLI 规格；`conflicts.md` 模式；Phase 3.5 冲突检测；migration tool 的 version+correction；`[UNVERIFIED-FROM-README]` |
| [titanwings/ex-skill](https://github.com/titanwings/ex-skill) · [perkfly/ex-skill](https://github.com/perkfly/ex-skill) | 6 层人格、memories + persona、星盘/MBTI/依恋 | `loved-one` schema（6 层）；`shared-memories` + `emotional-patterns` 组件；`[UNVERIFIED-FROM-README]` |
| [jinchenma94/bazi-skill](https://github.com/jinchenma94/bazi-skill) | Python computation + interpretation layer 分离、规则库 YAML | `executor` schema；`computation-layer` / `interpretation-layer` 组件分离；`[UNVERIFIED-FROM-README]` |
| midas.skill | N 维框架（方法论而非单人） | `public-domain` schema；`domain-framework` 组件；`[UNVERIFIED-FROM-README]` |
| cyber-figures | "5 轮蒸馏 / 405 段全文扫描发现 Layer 3" | Phase 2.5 迭代深化理念；Jaccard 收敛；`[UNVERIFIED-FROM-README]` |

## 评估体系（Tier 3）

| 库 | 贡献 | 本插件取之处 |
|----|------|------------|
| [softaworks/agent-toolkit/skill-judge](https://github.com/softaworks/agent-toolkit) | 8 维 skill 评估 rubric | `persona-judge` 12 维 rubric 在其基础上扩充（+ density + anti-gaming + 3 live tests） |

## 认知科学学术引用（v0.3.0 execution-profile 组件）

v0.3.0 新增的 `execution-profile` 组件 / `cdm-4sweep` 提取方法论 / `execution-profile-extractor` agent 基于以下**同行评审论文与权威著作**。这些**不是** `[UNVERIFIED-FROM-README]`——可被 persona-judge 直接引用。

| 文献 | 贡献 | 本插件取之处 |
|------|------|------------|
| Klein, G. (1998). *Sources of Power: How People Make Decisions*. MIT Press. | Recognition-Primed Decision 模型；"80% 专家决策是识别→第一反应，不是列表权衡" 的现场数据 | `execution-profile` 红线 2（RPD 风格）的学术依据；否决 Decision Making 段的 GPT 中性列表对比句式 |
| Hoffman, R. R., Crandall, B., & Shadbolt, N. (1998). Use of the Critical Decision Method to elicit expert knowledge. *Human Factors*, 40(2), 254-276. | Critical Decision Method 4-sweep 标准化协议（Incident → Timeline → 10-Probe → What-If） | `cdm-4sweep.md` 的主方法；Sweep 3 的 10 项 probe |
| Crandall, B., Klein, G., & Hoffman, R. R. (2006). *Working Minds: A Practitioner's Guide to Cognitive Task Analysis*. MIT Press. | CDM 操作手册 + Knowledge Audit 姊妹方法（past_and_future / big_picture / noticing 等 8 项） | 10 项 probe 的精简清单；execution-profile-extractor 的 Sweep 4 后 reverse-review |
| Klein, G., Ross, K. G., Moon, B. M., et al. (2003). Macrocognition. *IEEE Intelligent Systems*. | 8 类宏观认知活动（Sensemaking / Decision Making / Planning / Adaptation / Problem Detection / Coordination / Managing Uncertainty / Mental Simulation） | execution-profile 的 8 段骨架；顺序不可变 |
| Ericsson, K. A., & Ward, P. 关于自述 vs 行为差异的一系列工作 | "专家说的不是专家做的"——self-report 与实际行为系统性偏离 | `execution-profile` 红线 1 的学术依据；evidence 不能全是自述 |

**诚实提醒**：CTA/CDM 原本是**人采访人**的方法。本插件是 LLM 从已有语料"模拟采访"。部分 probe（如"如果时间多一倍"）没有现实对应物，只能基于材料推断。这意味着提取质量有上限——比凭空总结高得多，但离真正的专家采访有差距。具体损耗需要跑对照实验（v1.0.0 dog-food 前置）。

## 概念蓝本（URL 未知）

- **图鉴.skill** — 跨 persona 图谱、按需调度 → `persona-router` 的 scheduler 思路
- **诸子.skill** — 多 persona 辩论与对垒 → `persona-debate` 的 3 种模式（round-robin / position-based / free-form）

## 设计决策清单

为什么这么做（master-plan §9 原始讨论的浓缩）：

1. **为什么不做"3 个固定架构 skill"**：colleague 5 层 / ex 6 层 / nuwa 三维 / immortal 四维没有任何两个一样，说明架构必须**参数化**。
2. **为什么 9 种 schema 不合并**：合并后每种的组件组合差异依然存在，不如显式列出。
3. **为什么 `executor` 不独立成 skill**：它就是 `computation-layer` 组件 + 话术，没必要另起炉灶。
4. **为什么 `computation-layer` 不只属于 executor**：它可以挂到任何 schema（蒸馏一个量化交易导师）。
5. **为什么 persona-judge 是核心不是可选**：没有量化评估的蒸馏就是玄学，质量无法改进。
6. **为什么 router 和 debate 是可选**：在 persona skill 数量 < 10 之前没价值。
7. **为什么产物必须自包含**：防止生成的 persona skill 依赖 distill-meta。借鉴 nuwa 的核心原则。
8. **为什么保留 `conflicts.md`**：矛盾是真实感的来源，不能被抹平。借鉴 immortal-skill。
9. **为什么强制 Research Review Checkpoint**：不让 AI 蒙头跑完，人工介入一次可以避免很多错误。借鉴 nuwa。
10. **为什么把 anti-distill 的 classifier 反向用**：正向（密度评分）比反向（防蒸馏）更有价值。
11. **为什么 v0.3.0 引入 execution-profile（第 19 个组件）**：描述 ≠ 执行。`mental-models` 给"他怎么想"、`decision-heuristics` 给 IF-THEN 规则、`expression-dna` 给"怎么说"——三者加起来仍然是描述性的。加载 persona skill 后让 Claude 执行实际任务（拆解问题、选方案、判断要不要回头改），它会在决策瞬间漂回"标准中性助手"——描述没告诉它"现在这一秒该做什么"。execution-profile 用 Klein RPD + CDM 4-sweep 从具体事件反推指令性条款填这个缺口。

## 诚实的边界

- **没真正 clone 并运行任何一个参考库**，所有结构都是基于搜索结果和 README/SKILL.md 片段。具体 prompt 细节可能和原库有偏差。
- **9 种 schema 没有经过实际蒸馏验证**——所有 schema 的 manifest 都带 `unvalidated: true`。
- **Phase 2.5 迭代深化是理念扩充，不是成熟方法**——cyber-figures 的经验说明这件事有价值，怎么系统化做好还需要探索。
- **`computation-layer` 作为通用挂件是设想**——实际可能绝大多数 schema 不需要它。
- **本方案和现有方案的差异化点**：主要在"参数化 schema + 生成后生态（router / debate / migrator）+ 密度评分 + 社区 schema 扩展"四个点。生态继续演进，这些差异可能会被覆盖。

---

详细的集成拓扑和已知限制见 [`integration.md`](./integration.md)。
