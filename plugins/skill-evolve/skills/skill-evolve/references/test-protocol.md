# 独立 Subagent 评估协议（Test Protocol）

> 评估必须由**独立 subagent** 执行，不能由主 agent 自评。这是避免「自己给自己打高分」的关键。

---

## 为什么必须独立

主 agent 在 mutate 之后，知道改了什么、为什么改、希望怎么得分。这个上下文会污染评分——它会倾向于在「自己费力写出来的段落」上手下留情。

独立 subagent **不知道**：
- 这是初评还是复评
- 上一版本长什么样
- 改了哪一段
- 主 agent 的目标分数

它只看：当前 SKILL.md 全文 + rubric + 测试 prompt。

---

## Spawn 标准 Prompt（评估 subagent）

每次评分都用以下 prompt 模板调用 `Agent` 工具，subagent_type 选 `general-purpose`：

```
你是一位严格的 SKILL.md 评估员。任务：根据下面的 rubric 给目标 SKILL.md 打分。

## 评估目标

文件：<absolute path to target SKILL.md>

请用 Read 工具读取该文件全文。

## 评分 Rubric

<完整粘贴 references/rubric.md 全文>

## 测试 Prompt（用于效果维度第 7、8 项）

测试集（必须全部跑）：
1. <test_prompt_1>  期望方向：<expected_1>
2. <test_prompt_2>  期望方向：<expected_2>
3. <test_prompt_3>  期望方向：<expected_3>
边缘测试：<edge_prompt>  期望：表现适度不确定 / 给出降级方案

执行方式（每个测试 prompt 都跑两遍，做对比）：
- **with_skill**：假装你是一个全新的 Claude Code agent，刚加载这个 SKILL.md，严格按 SKILL.md 指令回答（不要凭常识；指令含糊就按字面执行）。写入 `with_skill_output`。
- **baseline**：假装你是一个**没有加载任何 skill** 的通用 Claude，仅凭通用能力回答同一个 prompt。写入 `baseline_output`。
- 对比两者：`beats_baseline` = with_skill 是否明显优于 baseline。
- **若 with_skill 劣于 baseline**（带 skill 还不如不带）→ 该测试 sub_score = 0，并置顶层 `negative_transfer: true`。这是致命项，必须如实标，不许护短。

## 输出要求

只输出严格的 JSON（rubric 中规定的 schema），不要任何额外说明。
不要给出"建议改进"——你不是改进者，你是评分员。

## 反作弊

- 不要假设「这个 skill 应该是好的」
- 不要因为指令"看起来很专业"就给高分；专业用语 ≠ 可执行指令
- 一个 8 分以上的维度必须有具体段落支撑
- 一个 4 分以下的维度必须有「为什么扣分」的具体证据
```

---

## 评估 subagent 的输入参数清单

每次 spawn 时必须显式传入：

| 参数 | 来源 | 用途 |
|------|------|------|
| `target_skill_path` | 用户/CLI 参数 | subagent 读取目标 |
| `rubric_md` | references/rubric.md 全文 | 评分依据 |
| `test_prompts[]` | 用户提供 / 自动推断 | 跑效果维度 |
| `expected_directions[]` | 同上 | 判分依据 |

**禁止传入**：上一版本分数、改动 diff、目标分数、轮次编号、KEEP/REVERT 历史。

---

## 多评委是默认（不是补救）

SkillLens 实测：**单个** AI 评委做成对判断准确率只有 46.4%——比掷硬币还差。本 rubric 是绝对锚点评分（比成对选优可靠），但仍带主观成分，所以：

**默认每次评分 spawn 2 个相互独立的评委 subagent**（相同输入、互不可见）：
- 每维取两份的**中位数**（2 份时即均值四舍五入），`total` 按合并后的维度分重算
- 两份总分差 ≤ 5 → 稳定，正常 KEEP/REVERT
- 差 6-10 → 记录警告，仍取中位数继续
- 差 > 10 → **暂停循环**，让用户检查 rubric 是否太主观；不要继续 mutate
- 两份在 `negative_transfer` 上不一致 → 视为 true（从严），并 spawn 第 3 个评委裁决

单评委只在「成本敏感的快速预览」时允许，且必须在 experiments.tsv 标 `single_judge`。

## 降级模式：无 subagent 工具时（dry_run）

若当前环境没有 Agent/subagent 工具（如 claude.ai）：
- 你自己分阶段扮演评委：先彻底切换角色「我是没见过改动的陌生评估员」，只读 SKILL.md 全文 + rubric，不参考自己 mutate 时的推理
- with_skill / baseline 两遍推演都自己做，但**必须在 experiments.tsv 的该行标 `dry_run`**
- dry_run 的分数可信度低于真 subagent，不能作为「已达目标分、可交付」的唯一依据——交付前提示用户「这是干跑估分」

---

## 测试 Prompt 自动生成（无用户提供时）

如果用户没提供 3 个测试 prompt，按以下规则自动生成：

1. **从 SKILL.md description 抽取动词 + 名词**（如 "evaluate persona skill" → 测试 1）
2. **从 when_to_use 列表抽取场景**（每场景一个测试 prompt）
3. **从 Triggers 字段抽取一种用户措辞**（如 "优化 skill" → 测试 prompt 直接复用此触发词）
4. **边缘测试**：把 description 中的关键名词替换成相邻领域的词（如 "skill" → "agent definition"）

自动生成的测试集要写入 `baseline.md` 让用户审查；用户可以替换。

---

## 反作弊 checklist

启动每一轮评估前，检查 prompt 是否泄露了不该泄露的信息：

- [ ] prompt 中没有出现 "改进版"、"v2"、"new"、"updated"、"better"
- [ ] prompt 中没有出现 "之前是 X 分"、"目标涨到 Y 分"
- [ ] prompt 中没有出现 git diff、"删除了 X"、"新增了 Y"
- [ ] subagent_type 选的是通用 agent，不是有偏见的特化 agent
- [ ] 测试 prompt 没变（同一轮的 baseline 和 re-eval 必须用相同测试集）

任一未通过 → 评分作废，重新 spawn。
