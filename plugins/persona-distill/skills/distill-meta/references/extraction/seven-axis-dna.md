---
extraction_method: seven-axis-dna
version: 0.1.0
purpose: 对 persona 的"表达风格"沿 7 个正交轴做 1-5 分量化，产出可复用的 expression-dna 矢量 + 每轴一个正例与一个反例。轴名与 ../components/expression-dna.md §"The Seven Axes" 严格对齐（formality / abstraction / assertiveness / sentence-length / vocabulary-domain / emotionality / persuasion-style），确保 voice-test fingerprint 可跨生成端与评估端复现。
consumed_by:
  - ../components/expression-dna.md
  - persona-judge (用于 Voice Test 盲测基线)
borrowed_from: https://github.com/alchaincyf/nuwa-skill/blob/main/references/extraction-framework.md
iteration_mode: single-pass
---

## Purpose

将 persona 的语言表达从"感性印象"转成"结构化矢量"，供 Phase 3 组装时生成 expression-dna.md，并供 Phase 4 persona-judge Voice Test 作盲测基线。七个轴覆盖词汇层、句法层、语用层三个范围，彼此尽量正交，避免风格向量坍缩到单一维度。

此方法是 nuwa-skill 的核心创新之一（PRD §3.5、§6 标记为"直接抄"/"核心创新"），是所有 persona schema 的共用组件。

## When to Invoke

- **Phase 2「维度提取」** 中由 dna-quantifier agent 调用；与 triple-validation、tension-finder 并行。
- **Phase 2.5「迭代深化」**：若 iterative-deepening 扫描出未覆盖的风格现象，可局部重跑单个轴。
- **Phase 4**：persona-judge 使用本矢量生成盲测题目，不在此重跑提取，只做比对。

## Input Schema

- `{corpus}` — primary corpus（该 persona 亲口/亲笔的一手文本），**≥ 200 lines** 且来自 ≥ 2 种 medium。二手转述不计入行数。
- `{target}` — persona 标识符。
- `{existing_components}` — 若已存在 identity.md，读取其 `language` 字段确定输出主语言。

硬性前置：primary corpus < 200 lines 时返回 `INSUFFICIENT_CORPUS`，交由上游在 Phase 1.5 Research Review Checkpoint 决定是否降级。

## Prompt Template

以下 prompt 原样传递给 sub-agent：

```
你是 seven-axis-dna quantifier。你的任务是对 {target} 的表达风格沿 7 个轴打分，并为每个轴提供一个正例和一个反例。

# 七轴定义（与 ../components/expression-dna.md §"The Seven Axes" 对齐；1 = 极低 / 3 = 中性 / 5 = 极高）
A1  formality（正式度）
     casual ↔ formal；1 = slang/emoji/口语；3 = conversational-pro；5 = formal-written。
A2  abstraction（抽象度）
     concrete ↔ abstract；1 = 全是具体例子；3 = 例子与原则并重；5 = 全是抽象原则。
A3  assertiveness（确定性）
     hedging ↔ certain；1 = 大量"可能/或许"；3 = 混合；5 = 平铺直叙的断言。
A4  sentence-length（句长/结构）
     short ↔ compound；1 = ≤7 字短句；3 = 12-18 字；5 = 长复合句嵌套从句。
A5  vocabulary-domain（词汇域）
     general ↔ specialized-jargon；1 = 日常词；3 = 轻量术语；5 = 不加解释的领域术语。
A6  emotionality（情绪表达）
     reserved ↔ expressive；1 = 冷静克制；3 = 有节制情感；5 = 感叹/情绪形容词/强第一人称情感。
A7  persuasion-style（说服风格，三极）
     data ↔ story ↔ appeal-to-authority；1 = data-first；3 = story-first；5 = authority-first。

# 输入
- 目标 persona：{target}
- 一手语料（≥200 lines）：{corpus}
- 已存在组件（读 identity.language）：{existing_components}

# 执行步骤
对每个轴 A1..A7：
1. 在 {corpus} 中采样至少 20 段，统计该轴相关特征出现率。
2. 打分 1-5（允许 0.5 粒度）。
3. 从 {corpus} 摘一段最能体现该得分的 verbatim 正例（20-60 字/词）。
4. 基于该得分 + 该 persona 的反面，构造一句"persona 不会说的话"作为 anti-example（由你生成，非 corpus 原文）。anti-example 要在同一话题 + 同一语境下偏离该轴 ≥ 2 分。
5. 写一行 rationale 说明为什么打这个分（引用统计 / 高频特征）。

# 禁止
- 禁止为让轴分"好看"而挑 cherry-picked 极端片段；必须能代表整体分布。
- 禁止 anti-example 抄 corpus；它是生成的负样本。
- 禁止把 7 个分数全部打在 3-4 区间（表达力坍缩），若出现必须在 rationale 中说明该 persona 确实风格中庸。

# 输出
严格按 Output Schema 返回 JSON，不加任何解释。
```

## Output Schema

```json
{
  "target": "steve-jobs-mirror",
  "language": "zh | en",
  "axes": [
    {
      "axis_id": "A1",
      "name": "formality",
      "score": 4.0,
      "positive_example": "<verbatim quote from corpus>",
      "positive_source_id": "int-2005-stanford",
      "anti_example": "<generated sentence the persona would NOT say>",
      "rationale": "20 段采样中 17 段使用正式书面结构，几乎无缩略形式。"
    }
    /* …A2(abstraction) through A7(persuasion-style)… */
  ],
  "sampling_stats": {
    "total_segments_sampled": 140,
    "primary_corpus_lines": 312,
    "mediums_covered": ["public_speech", "written_essay", "interview"]
  }
}
```

`../components/expression-dna.md` 直接消费此 JSON 生成最终组件文件。

## Quality Criteria

1. **正交性**：7 轴得分不应全部聚在同一窄带；标准差 ≥ 0.8。
2. **正例 verbatim**：所有 positive_example 必须能在 {corpus} grep 命中。
3. **反例可感**：anti-example 读起来明显"不像 persona"；由人工 spot-check 3 条确认。
4. **语言一致**：输出 language 字段与 identity.md 一致；正例保留原文语言。
5. **采样充分**：sampling_stats.total_segments_sampled ≥ 100。
6. **Voice Test 可用**：persona-judge 能基于此矢量出 100 字盲测题并达到 ≥ 70% 辨识度（参见 PRD §4.2 Voice Test）。

## Failure Modes

| 坏提取 | 如何识别 |
|--------|----------|
| 7 轴全打 3 分 | 标准差 < 0.5；大概率 agent 偷懒 |
| 正例实际是二手转述 | source_id 指向访谈者/媒体而非 persona 本人 |
| anti-example 照搬 corpus | 在 {corpus} 中能 grep 命中 → 不是反例 |
| A4 情绪张力被字面词典误判 | 讽刺 / 反讽被当成中性；由 Voice Test 失败暴露 |
| 语料不足却强行输出 | sampling_stats.primary_corpus_lines < 200 但仍返回分数，而非 INSUFFICIENT_CORPUS |

## Borrowed From

- 来源：[nuwa-skill/references/extraction-framework.md](https://github.com/alchaincyf/nuwa-skill/blob/main/references/extraction-framework.md) `[UNVERIFIED-FROM-README]`
- PRD §3.5：

  > | 七轴 DNA | nuwa/references/extraction-framework.md | 直接抄 |

- PRD §6 将本方法列入"核心创新（nuwa-skill）"借鉴矩阵：

  > `alchaincyf/nuwa-skill` … 认知 OS 架构、三重验证、七轴 DNA、6 agent 并行、质量验证 …

- 本文件补齐内容：每轴的正例/反例/rationale 三件套格式、sampling_stats、正交性约束（PRD 未细化到轴级 schema，由本实现定义）。
