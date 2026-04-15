---
extraction_method: cdm-4sweep
version: 0.1.0
purpose: 把 persona 从"描述"转成"执行指令"——用 Klein 的 Recognition-Primed Decision 模型 + Cognitive Task Analysis 里的 Critical Decision Method 4 扫描协议，从具体事件反推 8 类宏观认知活动下的情境-行动对。
consumed_by:
  - ../components/execution-profile.md
  - ../../agents/execution-profile-extractor.md
  - persona-judge（用作 Execution-Readiness 维度评分输入，v0.3.0）
borrowed_from:
  - Klein, G. (1998). Sources of Power — RPD model
  - Hoffman, R. R., Crandall, B., & Shadbolt, N. (1998). Use of the Critical Decision Method to elicit expert knowledge. Human Factors, 40(2), 254-276.
  - Crandall, B., Klein, G., & Hoffman, R. R. (2006). Working Minds: A Practitioner's Guide to Cognitive Task Analysis
  - Klein, G., Ross, K. G., Moon, B. M., et al. (2003). Macrocognition. IEEE Intelligent Systems
iteration_mode: four-sweep
---

## Purpose

Persona skills 的常见失败模式是：`mental-models` / `decision-heuristics` 等组件产出的都是**描述性**句子（"他倾向于用户优先"、"重视长期价值"），下游 Claude 执行任务时没法把描述翻译成动作。本方法从 `knowledge/` 的**具体事件**出发，用 CDM 4-sweep 把事件里的决策瞬间显式化为**指令性**的"情境 → 动作"条款，并按 Macrocognition 的 8 类宏观认知骨架归档。产出直接喂给 `components/execution-profile.md`。

与 `triple-validation` 正交：triple-validation 校验的是"这个观点有没有 3 个独立来源"；cdm-4sweep 追问的是"那个具体事件里他到底抓了什么信号、排除了什么选项、模拟了什么后果"。triple 解决"是不是真的"，4-sweep 解决"怎么照着做"。

## Theoretical Backbone / 三层理论根基

| 层 | 作用 | 来源 |
|---|------|------|
| **RPD**（Recognition-Primed Decision） | 解释专家"识别情境 → 第一可行方案 → 心理模拟"的真实决策方式；80% 专家决策不是列表权衡，是模式识别。 | Klein 1989 / 1998 |
| **Macrocognition 8 类** | 任意任务执行时反复出现的 8 类认知活动，作为 Profile 的分类骨架。 | Klein 等 2003 |
| **CDM**（Critical Decision Method） | 从语料里"反向采访"具体事件、套标准 probe 追问隐性知识的提取协议。 | Hoffman / Crandall / Shadbolt 1998；Crandall 等 2006 |

本方法强制**从事件出发、不从抽象出发**：材料来源限定 `knowledge/`（Phase 1 清洗后的一手语料），禁止从 `components/` 里已经总结过的描述倒推——后者会让 LLM 编内容。

## Macrocognition 8 类（Profile 的分类骨架）

Execution Profile 必须且仅包含以下 8 段，顺序不可变。每段下面写**指令性句子**（做 X 不做 Y），不是描述性句子（倾向 X）。

1. **情境判断 / Sensemaking** — 看到任务时抓什么信号、怎么判定"这是什么情况"。
2. **方案抉择 / Decision Making** — 多个可行做法时的选择标准与方式（注意 RPD 红线：多数时候是"识别 → 第一反应"，不是 3 选 1 列表比较）。
3. **步骤规划 / Planning** — 任务拆解原则、先做什么后做什么。
4. **计划调整 / Adaptation** — 计划撞墙时重做 vs 局部修补的阈值。
5. **异常发现 / Problem Detection** — 对"不对劲"的敏感度、容易忽略哪类信号。
6. **协同 / Coordination** — 何时找用户、何时自己决定、工具偏好。
7. **不确定性管理 / Managing Uncertainty** — 信息不全时的默认动作、容忍多少未知就动手。
8. **心理模拟 / Mental Simulation** — 做之前在脑子里跑一遍的程度（精细度、时长、后果想象）。

## When to Invoke

- **Phase 3.7「Execution Profile 提取」**：Phase 3 组装完成后、Phase 3.5 conflict-detector 并行（或紧接其后）运行。依赖 `knowledge/`（必要）和 `components/`（仅作反向校验，**不作为提取源**）。
- **Phase 4「质量验证」**（可选）：persona-judge 可反向调用 Red-Line Check 查漏。
- **不在** Phase 0/1/1.5/2/2.5/3.5/5 触发。

## Inputs

| Input | 源 | 必需 |
|-------|----|------|
| `{knowledge_dir}` | `{persona-skill-root}/knowledge/` | YES（事件来源） |
| `{existing_components_dir}` | `{persona-skill-root}/components/` | YES（仅反向 audit，不提取） |
| `{expression_dna_path}` | `components/expression-dna.md`（如果存在） | optional（用于 Drift Prevention 段输出） |
| `{target}` | persona 标识符 | YES |
| `{incident_budget}` | 最少挑出的非常规事件数；默认 5，上限 10 | optional |

若 `{knowledge_dir}` 事件密度不够（整库可识别的 decision point < 10），本方法直接返回 `INSUFFICIENT_EVENTS`，由上游（distill-meta）决定是否降级：**跳过 execution-profile 组件 + 在 `honest-boundaries.md` 追加一条"事件证据不足以蒸馏执行画像"**。

## Procedure — 4 Sweeps

### Sweep 1 — Incident Identification

从 `{knowledge_dir}` 挑 5-10 个**具体的、有挑战性的、非常规事件**。**不要**"他一般怎么做"；**要**"那次他做了什么"。

选择偏好（同等价值时按此排序）：
1. 事件里包含明确的**转向点**（backtracking、推翻上一秒判断）
2. 事件里有**多个可选路径**被 persona 显式排除
3. 事件发生在**不确定/时间压力**下
4. 事件跨多个组件可能冲突的断言（links to Phase 3.5 conflicts）

每个 incident 产出 `{incident_id, source_id, one-line summary, why-challenging}`。

### Sweep 2 — Timeline Construction

对每个 incident，画一条 timeline（文字表述即可），标出 **decision points**（关键判断或转向的时刻）。每个 decision point 至少包含：

- `t`：事件线上的相对时刻（t0, t1, t2...）
- `what_happened`：verbatim 或 ≤1 行总结
- `what_changed`：这一刻把事件引向了哪条叉路

保留**所有** decision point，不在此 sweep 删减；后续 sweep 会用 probe 筛选。

### Sweep 3 — Deepening with Standard CDM Probes

对每个 decision point，套用 **10 项 CDM 标准探针**（Crandall et al. 2006, Table 4.2 的精简版）。每项只在"材料允许得到可追溯的答案"时回答，**不准脑补**；没答案就写 `no-evidence`。

| # | Probe | 中文追问 | 用途 |
|---|-------|---------|------|
| 1 | Cues | 他抓住了什么信号？ | 喂给 Sensemaking / Problem Detection |
| 2 | Knowledge | 他需要知道什么才能这么判断？ | 暴露前置知识、判 honest-boundaries |
| 3 | Analogues | 这让他想起什么类似的过往情况？ | 喂给 Sensemaking 的"模式识别" |
| 4 | Goals | 那一刻他在追求什么？ | 喂给 Decision Making 的权衡 |
| 5 | Options | 他考虑了 / 排除了哪些做法？为什么？ | 喂给 Decision Making、破"RPD 列表误判" |
| 6 | Experience | 新手在这里会怎么搞错？ | 喂给 Anti-Pattern Specificity |
| 7 | Aiding | 什么信息/工具能让这个决策更轻松？ | 喂给 Coordination |
| 8 | Time pressure | 时间多一倍，他会做不一样吗？ | 喂给 Managing Uncertainty |
| 9 | Errors | 有没有可能搞砸？怎么搞砸？ | 喂给 Problem Detection |
| 10 | Hypotheticals | 如果 X 不一样，他会怎么改？ | 喂给 Adaptation |

**重要**：probe 8 和 10 带有反事实（counterfactual）性质，很多情况下 `knowledge/` 给不出直接答案。这类 probe 允许"回答：no-evidence，原因：无反事实材料"——**不允许 LLM 凭印象编**。no-evidence 越诚实，后续 Honest Boundaries 段越可信。

### Sweep 4 — What-If Validation

把每个 decision point 的**一个输入条件**改一个值，问从 `knowledge/` 能不能推断出这个 persona 会怎么变。

- **能推出**（找到 ≥ 1 段 knowledge 材料作为支持）→ 保留对应指令，标 `confidence: high`。
- **推不出但材料与假设相容** → 保留，但标 `confidence: medium`。
- **推不出且材料空白** → **剔除**对应指令，改写到 `honest-boundaries.md` 的"推断能力不足"段。

这一步是防 LLM 幻觉的最后一道闸。

### 归档

把 Sweep 3 的答案按 Macrocognition 8 类归档，写成指令性句式："做 X 不做 Y"。每条指令必须带：

```yaml
- category: sensemaking | decision_making | planning | adaptation | problem_detection | coordination | managing_uncertainty | mental_simulation
  instruction: "<做 X 不做 Y 的具体句式>"
  evidence:
    - incident_id: inc-03
      decision_point: t2
      source_id: "knowledge/corpus/<...>#L<line>"
      probe_hits: [cues, options, errors]
  confidence: high | medium
  red_line_passes: [1, 2, 3]   # 指下面§Three Red Lines 校验
```

## Knowledge Audit Checklist — 反向 Review（Sweep 4 之后）

用 Crandall 2006 里 CDM 的姊妹方法——Knowledge Audit——对 Profile 做一次反向巡检。Profile 写完后，逐项问"我覆盖了 persona 在这一项上的特点吗"，没覆盖的就是缺口：

1. **Past & Future** — 能从现状预测未来走势吗？基于什么？
2. **Big Picture** — 不被细节淹没看到整体的能力？
3. **Noticing** — 容易注意到别人忽略的什么？
4. **Job Smarts** — 有什么"老手才会的省事招"？
5. **Opportunities / Improvising** — 怎么从计划外机会里挤价值？
6. **Self-Monitoring** — 怎么知道自己做得对不对？
7. **Anomalies** — 能识别哪些"乍看正常但其实不对"的情况？
8. **Equipment Difficulties** — 工具 / 系统给他添乱时怎么办？

每项标 `covered | partial | gap`，`gap` 的项写到产物 `honest-boundaries.md` 的 `## Execution Profile Gaps` 段。

## Three Red Lines / 三条质量红线

以下反模式必须被 agent 或 persona-judge 强制检查。命中即 `red_line_passes` 相应项为 false，并触发指令重写。

### 红线 1：专家说的 ≠ 专家做的（Ericsson & Ward）

**反模式**：某条 instruction 的 evidence 全是 persona 的**自述**（访谈、自传里的自我描述），没有**行为/事件**佐证。
**判定**：evidence 的 source_id 至少有 1 条必须是"事件叙述"而非"持有某观点的自述"。
**处置**：若全自述 → 强制 `confidence: low`，在 instruction 末尾追加 `[SELF-REPORT-ONLY]` 标记。

### 红线 2：80% 专家决策是 RPD 风格，不是分析比较（Klein 现场数据）

**反模式**：`## Decision Making` 段里出现"列 3 个选项权衡利弊"之类的中性 GPT 句式。真实专家是"识别 → 第一反应"。
**判定**：grep 该段内 instruction，若 ≥ 50% 含 "weigh / compare / list options / pros-cons" 句式 → 红线 2 不过。
**处置**：整段重写，逼回"识别到 X 味道 → 直接做 Y"的句式；如果确实材料显示 persona 会做列表对比（罕见），保留但在 instruction 后附 `[ANALYTICAL-DEVIATION]` 标记。

### 红线 3：颗粒度必须是"情境-行动对"，不是抽象原则

**反模式**：`instruction: "注重长期价值"` —— Claude 执行时不知道"长期"在当前任务里指什么。
**正例**：`instruction: "识别到方案有'为未来不存在的需求做准备'的味道 → 直接砍掉，从剩下里选 6 个月后改起来代价最小的"`。
**判定**：grep instruction，若不含具体动词 + 具体对象 → 红线 3 不过。黑名单词根：`注重 / 倾向 / 重视 / 善于 / prefer / value / focus on`（当作谓语时）。
**处置**：重写或降级到 `honest-boundaries.md`；禁止保留抽象原则。

**三条红线全部通过** = `red_line_passes: [1, 2, 3]`；任一不过 = 指令标记失败并需重写或删除。

## Output Schema

本方法产出一个 JSON，交给 `execution-profile-extractor` agent 渲染成 `components/execution-profile.md`：

```json
{
  "target": "{target}",
  "status": "OK | INSUFFICIENT_EVENTS | PARTIAL",
  "incidents": [
    {
      "incident_id": "inc-01",
      "source_id": "knowledge/corpus/<path>",
      "summary": "<≤ 20 字>",
      "decision_points": [
        {
          "t": "t0",
          "what_happened": "<verbatim or ≤1 行>",
          "probes": {
            "cues": "<答案 or no-evidence>",
            "knowledge": "...",
            "analogues": "...",
            "goals": "...",
            "options": "...",
            "experience": "...",
            "aiding": "...",
            "time_pressure": "...",
            "errors": "...",
            "hypotheticals": "..."
          },
          "what_if_validation": {
            "altered_input": "<假设变动>",
            "inferred_change": "<推断出的变化 or null>",
            "confidence": "high | medium | dropped"
          }
        }
      ]
    }
  ],
  "instructions_by_category": {
    "sensemaking":          [ /* yaml instruction entries */ ],
    "decision_making":      [],
    "planning":             [],
    "adaptation":           [],
    "problem_detection":    [],
    "coordination":         [],
    "managing_uncertainty": [],
    "mental_simulation":    []
  },
  "knowledge_audit_gaps": [
    {"item": "past_and_future", "status": "covered | partial | gap", "note": "..."}
  ],
  "red_line_summary": {
    "red_line_1_fails": 0,
    "red_line_2_fails": 0,
    "red_line_3_fails": 0
  }
}
```

## Quality Criteria

1. **事件可追溯** — 每条 instruction 至少 1 条 evidence 指向 `knowledge/` 内的具体行号 / 段落，grep 能命中。
2. **RPD 优先** — `decision_making` 段里"识别 → 第一反应"句式占比 ≥ 50%（除非语料本身证明 persona 是分析型）。
3. **覆盖 8 类** — 8 段都必须至少 1 条 instruction，否则该段改写为 `"No evidence in knowledge/; see honest-boundaries.md"`。
4. **诚实优先** — `what_if_validation` 的 `dropped` 条目必须反映到 `honest-boundaries.md`，count 与 dropped 条目数一致（±1）。
5. **三红线零失败** — 合格 Profile 要求 `red_line_*_fails` 全为 0；任一不为 0 阻塞 Phase 4 放行。

## Failure Modes

| 坏提取 | 如何识别 |
|--------|----------|
| 从 `components/` 抽象倒推 | evidence 的 source_id 指向 `components/*.md` 而非 `knowledge/`——**立即判废** |
| 8 类都填满但有 5 类是同一类改写 | instruction 之间 Jaccard > 0.7（词级）→ 合并并标 OVERFIT |
| "list 3 options then weigh" 充斥 decision_making | 红线 2 不过，整段必须改写 |
| what-if 全标 high confidence | 信号：agent 没真查材料，随手标 high。抽 3 条抽样复核 |
| no-evidence 为 0 条 | 诚实度红旗——真实语料不可能所有 probe 都有答案。强制重跑 Sweep 3 |

## Interaction with Other Components

- **Depends on** (read-only): `knowledge/corpus/**`、`components/identity.md`（仅用于 persona 名字标记）、`components/expression-dna.md`（仅用于 Drift Prevention 段的口吻自检提示词）。
- **Does not depend on** (禁止读取作为证据来源): `components/mental-models.md`、`components/decision-heuristics.md` —— 这些是描述性总结，作为 evidence 会污染 Profile 的执行性（红线 1 的衍生约束）。
- **Cross-check with** `components/internal-tensions.md`: 若某条 instruction 在不同 incident 里指向相反动作 → 这不是 Profile 的任务，交由 Phase 3.5 conflict-detector 处理；Profile 只记录"在 incident A 场景下 Y；在 incident B 场景下 ¬Y"，不调和。

## Honest Limitation Admission

CTA/CDM 原本是**人采访人**的方法，本实现是 LLM 从已有语料"模拟采访"。部分 probe（如 "如果时间多一倍"）没有现实对应物，只能基于材料推断。这意味着提取质量有上限——但比凭空让 Claude 总结高得多。具体损耗需要跑对照实验（见 `docs/integration.md` §Dog-food roadmap）。

本方法不适用于：
- 语料全部是 persona 的"观点文章"，零事件叙述（换用 public-mirror 的 `mental-models` 组件）。
- 蒸馏对象是"领域"而非"人"（topic schema 不包含 execution-profile）。
- 规则体系（executor schema）—— computation-layer 直接给出可执行规则，不需要从事件反推。

## Borrowed From

- Klein, G. (1998). *Sources of Power: How People Make Decisions*. MIT Press. — RPD 模型权威著作（§Three Red Lines 红线 2 的依据）
- Hoffman, R. R., Crandall, B., & Shadbolt, N. (1998). Use of the Critical Decision Method to elicit expert knowledge. *Human Factors*, 40(2), 254-276. — CDM 4-sweep 标准化论文
- Crandall, B., Klein, G., & Hoffman, R. R. (2006). *Working Minds: A Practitioner's Guide to Cognitive Task Analysis*. MIT Press. — 10 项 probe 清单与 Knowledge Audit 8 项目
- Klein, G., Ross, K. G., Moon, B. M., et al. (2003). Macrocognition. *IEEE Intelligent Systems*. — 8 类宏观认知活动的来源
- Ericsson, K. A., & Ward, P. — 关于自述 vs 行为差异的经典提醒（§Three Red Lines 红线 1）

学术文献**非** `[UNVERIFIED-FROM-README]`——这些是公开发表的同行评审论文 / 权威著作，persona-judge 允许直接引用。
