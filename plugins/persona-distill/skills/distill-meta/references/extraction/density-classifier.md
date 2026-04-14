---
extraction_method: density-classifier
version: 0.1.0
purpose: 对 SKILL.md 及 knowledge/components/*.md 的每个语义段落打 4 级密度标签，并按 REMOVE+2 / MASK+1 / SAFE 0 / DILUTE-1 加权归一化到 0-10 的密度分数。
consumed_by:
  - persona-judge (Density 维度评分)
  - ../components/ 所有写入前的自检（可选）
borrowed_from: https://github.com/leilei926524-tech/anti-distill/blob/main/prompts/classifier.md
iteration_mode: single-pass
---

## Purpose

anti-distill 原本用 4 级分类器标记"哪些内容不该被大模型吸走"（REMOVE = 高价值要抽离，DILUTE = 注水要保留）。本项目反向使用：把它当作"高价值内容占比"的正向评分器——如果一个 persona skill 中 REMOVE/MASK 级段落很少、DILUTE 很多，说明蒸馏出的是正确废话，必须打回 Phase 2 重做。

PRD §4.3 将本方法定为 persona-judge 的核心创新评分维度，通过门槛：密度分 < 3 直接不通过。

## When to Invoke

- **Phase 4「质量验证」**：persona-judge 在计算 12 维分数时，对 SKILL.md 和每个组件文件整体跑一次。
- **Phase 2 末尾（可选）**：每个 component-extractor agent 写入文件前自检一次；密度过低直接回炉，不占用 persona-judge 的周期。
- **不在** Phase 0/1/1.5/3/5 触发。

## Input Schema

- `{target}` — 被评估的 skill / 组件文件路径。
- `{text_segments}` — 待评分内容按"段落"切分后的数组；一个段落 = 一个标题下的连续语义块或一个 bullet。推荐长度 40-300 字/词。
- `{schema}` — 当前 persona 的 schema 名（public-mirror / collaborator / ...），影响"什么算 SAFE"的边界（例如 executor schema 的流程规范天然更接近 SAFE，评分阈值要宽松 0.5）。
- `{existing_components}` — 已定稿组件路径列表，用于识别"跨组件重复段落"（重复的算 DILUTE）。

## Prompt Template

```
你是 density-classifier。你的任务是对 {target} 的每个段落打一个 4 级标签，并说明判断依据。

# 4 级标签（反向使用 anti-distill 分类器）
REMOVE  （高价值，+2）
  — 具体阈值 / 数字 / 反直觉经验 / persona 独有判断 / 可执行的精确步骤。
  — 例："决定砍功能的阈值：临近 deadline 7 天内新 bug 率 > 2/天就冻结特性"。

MASK    （中高价值，+1）
  — 个人网络 / 职业路径 / 非公开但结构化的人物关系 / 具体项目的内部抉择过程。
  — 例："2003-2005 与 X 合作时采用的内部评审节奏"。

SAFE    （通用知识，0）
  — 该领域任何专业人士都会写出的通识；非 persona 独有，但也不是空话。
  — 例："敏捷开发强调小步快跑"——任何 PM 都会说。

DILUTE  （低价值/正确废话，-1）
  — 大词 / 同义反复 / 无可操作性的价值观陈述 / 跨组件重复 / 模糊到无法证伪。
  — 例："我们要做伟大的产品"、"保持初心很重要"。

# 输入
- Persona：{target}
- Schema：{schema}
- 已定稿组件（用于重复检测）：{existing_components}
- 段落数组：{text_segments}

# 执行步骤
1. 逐段判断。不允许跳过；不允许一段打两个标签。
2. 对每段给一行 ≤ 30 字的 rationale，必须指向具体特征（"含阈值"/"同义反复"/"与 X 组件重复"）。
3. 跨组件重复检测：若某段与 {existing_components} 中某文件的某段语义相似度 > 0.9，自动降级为 DILUTE。
4. 计算密度分：
     raw = Σ (REMOVE*2 + MASK*1 + SAFE*0 + DILUTE*(-1))
     max = 段落总数 * 2
     min = 段落总数 * (-1)
     normalized_score = round( (raw - min) / (max - min) * 10 , 1 )
5. 返回明细 + 汇总。

# 禁止
- 禁止把"听起来有道理"的段落打 REMOVE；REMOVE 必须含具体 anchor（数字 / 命名实体 / 反直觉断言）。
- 禁止把 identity.md / hard-rules.md 中的结构化字段一律打 SAFE——有内容的字段按实质评分。

# 输出
严格按 Output Schema 返回 JSON。
```

## Output Schema

```json
{
  "target": "plugins/.../steve-jobs-mirror/SKILL.md",
  "schema": "public-mirror",
  "segment_scores": [
    {
      "segment_id": "s-001",
      "excerpt": "<前 40 字>",
      "tag": "REMOVE | MASK | SAFE | DILUTE",
      "weight": 2,
      "rationale": "含具体阈值与时间窗。"
    }
  ],
  "totals": {
    "REMOVE": 14,
    "MASK": 9,
    "SAFE": 22,
    "DILUTE": 6,
    "total_segments": 51
  },
  "raw_score": 25,
  "normalized_score": 6.8,
  "verdict": "PASS (>=3) | FAIL (<3)"
}
```

persona-judge 直接使用 `normalized_score` 作为 Density 维度（0-10）分数。

## Quality Criteria

1. **标签覆盖**：total_segments == segment_scores 长度；无遗漏。
2. **rationale 非空**：每段都有 ≤ 30 字判断依据。
3. **重复检测生效**：跨组件重复段落实际被标 DILUTE（抽查 3 条）。
4. **公平分布**：不允许 > 80% 段落打同一标签（极端偏置说明分类器偷懒）；若真的如此，输出 warning 字段。
5. **一致性**：对同一份文本重复调用两次，normalized_score 差异应 ≤ 0.5。
6. **门槛可执行**：verdict 字段能驱动 persona-judge 决定是否回 Phase 2（PRD §4.3：< 3 分不通过）。

## Failure Modes

| 坏提取 | 如何识别 |
|--------|----------|
| 把"正确废话"（如"要敬畏用户"）标 REMOVE | rationale 缺失 anchor（无数字/命名实体/反直觉断言） |
| 把具体阈值打 SAFE | rationale 写"通用知识"但段落里含数字/专名 |
| 把跨组件重复漏标为 DILUTE | 抽查发现与 existing_components 有高相似度但仍被打 SAFE+ |
| 一边倒全 REMOVE（过度乐观） | totals 中 REMOVE > 80%；真实 skill 极少有这种分布 |
| 把 manifest / YAML frontmatter 也参与评分 | 非散文内容不应打标签，应在切分阶段跳过 |

## Borrowed From

- 来源：[leilei926524-tech/anti-distill/prompts/classifier.md](https://github.com/leilei926524-tech/anti-distill/blob/main/prompts/classifier.md) `[UNVERIFIED-FROM-README]`
- PRD §3.5：

  > | 密度分类器 | anti-distill/prompts/classifier.md | 反向用作正向筛选 |

- PRD §4.3 明确反向使用方式：

  > 对 SKILL.md 的每一段内容打 4 种标签：REMOVE +2 / MASK +1 / DILUTE -1 / SAFE 0 → 归一化到 0-10。密度低于 3 分的 skill 不予通过。

- PRD §9 再次复述"反向用"理由：

  > 为什么把 anti-distill 的 classifier 反向用：正向（密度评分）比反向（防蒸馏）更有价值，而分类器本身是通用的。

- 本文件补齐内容：schema 相关阈值微调（executor 宽 0.5）、跨组件重复自动降级规则、verdict 字段——PRD 未规定这些执行细节。
