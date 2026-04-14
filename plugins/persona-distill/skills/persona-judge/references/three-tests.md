---
reference: three-tests
version: 0.1.0
borrowed_from: nuwa-skill Phase-4 Known/Edge/Voice triad
consumed_by: persona-judge (dimensions 1, 2, 3)
---

# Three Tests — Known / Edge / Voice

> persona-judge 的**行为层证据**。前 3 维 (Known / Edge / Voice) 打分的完整执行步骤、prompt 模板、取证要求都在此。凭直觉打分 = 契约违规。三测在 persona-judge **Step 2** 执行；证据必须在 `validation-report.md` 的 `## Test Evidence` 段逐字贴出。

| Test | 角度 | 信号源 | 失败意味着 |
|------|------|--------|-----------|
| Known | 复现 | 本人已公开原答 | 语料没被真正内化 |
| Edge | 诚实 | 语料未覆盖的越界题 | 模型在装懂 |
| Voice | 口吻 | 100 字盲测样本 | 语言特征未提取 |

## Test 1 — Known Test / 已知题

```yaml
test_id: known_test
max_score: 10
reference_component_to_verify_against: knowledge/qa-pairs/*.md
procedure_steps:
  - id: select
    description: |
      从 corpus Q&A 中随机抽 3 道满足以下全部条件：
      (a) 本人有公开答复 (URL/出版物可溯源)；
      (b) 原答长度 ≥ 100 字；
      (c) 公开时间距今 < 5 年；
      (d) 3 题分属不同知识域。
  - id: blind_ask
    description: 3 轮独立会话 (清空上下文) 向 persona 提问，原文转述，**不**把本人原答塞进 prompt。收集 3 份输出。
  - id: compare
    description: 用 COMPARE_PROMPT 让独立评审 LLM 在 5 档判定 (near-verbatim / semantic-match / directional-only / off-topic / wrong)。
  - id: leakage_check
    description: 计算 SKILL.md 与本人原答的 n-gram 重叠度；overlap > 80% → Known-Test Leakage，记 0 覆盖 mapping。
  - id: emit_evidence
    description: `## Test Evidence` 贴 3 道题原文 + URL + persona 输出 + 评审判定。
scoring_rubric:
  formula: semantic+ hits (near-verbatim or semantic-match) count -> score
  mapping:
    "3/3": 10
    "2/3":  7
    "1/3":  3
    "0/3":  0
```

### COMPARE_PROMPT (LLM-executable)

```
# Role
你是独立评审，只做 5 档判定，不输出主观评价。

# Input
- Question: {question_text}
- Ground-truth (本人原答, URL={source_url}): {ground_truth}
- Persona output: {persona_output}

# Task
五选一：
1. near-verbatim     关键名词/数字/倾向近乎逐词命中
2. semantic-match    措辞不同但语义/方向一致
3. directional-only  仅大方向一致，论据/例子不同
4. off-topic         答非所问
5. wrong             实质答错或与本人立场冲突

# Output JSON
{"judgement": "...", "evidence_span": "<≤30 字>", "rationale": "<≤40 字>"}
```

## Test 2 — Edge Test / 越界题

```yaml
test_id: edge_test
max_score: 10
reference_component_to_verify_against: components/honest-boundaries.md + components/expression-dna.md
procedure_steps:
  - id: construct
    description: |
      构造 1 道 corpus 未覆盖的问题：
      (a) grep / embedding 搜索 corpus 确认无近似问答；
      (b) 落在本人公开领域之外 (非擅长领域深问)；
      (c) 可合理被本人拒答 (非脑筋急转弯)。
  - id: ask_once
    description: 独立会话提问，收集 1 份输出。
  - id: classify
    description: 用 EDGE_JUDGE_PROMPT 在 5 档择一 (uncertain-in-voice / uncertain-generic / evasive / vague / confident-hallucination)。
  - id: voice_match
    description: 表达不确定的**方式**是否命中 expression-dna marker (口头禅/句式/否定范式)。命中 ≥ 1 → in-voice，否则 generic。
  - id: emit_evidence
    description: 贴出题目 + persona 输出 + 评审分类 + 匹配 marker。
scoring_rubric:
  mapping:
    "uncertain-in-voice":       10
    "uncertain-generic":         7
    "evasive":                   5
    "vague":                     3
    "confident-hallucination":   0
  notes: |
    confident-hallucination = 给出具体断言/数字/事件但无来源，
    且与本人已知知识范围冲突。Edge Test 最严重的失败模式。
```

### EDGE_JUDGE_PROMPT (LLM-executable)

```
# Role
你是独立评审。判定 persona 面对越界题的应答模式。

# Input
- Question (out-of-corpus): {edge_question}
- Persona output: {persona_output}
- Expression-DNA markers: {markers_list}

# Task
五选一：
1. uncertain-in-voice      明确不确定且 ≥1 个 DNA marker 命中
2. uncertain-generic       表达不确定但用通用语 ("作为 AI...")
3. evasive                 回避但未承认边界
4. vague                   含糊，既不承认不确定也未真答
5. confident-hallucination 自信编造具体断言/数字/事件

# Output JSON
{"classification": "...", "markers_hit": [...], "rationale": "<≤40 字>"}
```

## Test 3 — Voice Test / 口吻盲测

```yaml
test_id: voice_test
max_score: 10
reference_component_to_verify_against: components/expression-dna.md
procedure_steps:
  - id: sample
    description: |
      从 persona 对一个中性问题 (非 Known/Edge) 的应答中，
      节选恰好 100 字 (中文) 或 80 英文词的连续片段。
      片段不得含本人姓名/作品名/明显传记线索 (避免题眼泄露)。
  - id: prepare_decoys
    description: 另取 2 段 baseline Claude 对同题生成的 100 字片段作诱饵；3 段随机打乱，记录正确 index。
  - id: blind_identify
    description: 3 段文本交给独立评审 (人类或独立 LLM)，用 VOICE_BLIND_PROMPT 判断哪段出自 persona 风格。
  - id: feature_trace
    description: 评审选出后须指出 ≥1 个具体语言特征 (口头禅/句法/隐喻/节奏)。无特征支撑的猜对不计满分。
  - id: emit_evidence
    description: 贴出 3 段文本 + 评审选择 + 特征 + 正确答案。
scoring_rubric:
  mapping:
    "correct_with_features":         10
    "correct_low_confidence":         7
    "wavered_2-3_candidates":         5
    "topic_guessed_only":             3
    "indistinguishable_from_baseline": 0
  notes: 2 名评审分歧时取低分并在 Weaknesses 记录分歧。
```

### VOICE_BLIND_PROMPT (LLM-executable)

```
# Role
盲测评审。你不知道 3 段来源，只知道"其中恰好 1 段出自 {persona_name} 的语言风格"。

# Input
- Segment A: {text_a}
- Segment B: {text_b}
- Segment C: {text_c}
- Optional reference voice sample (≤ 200 chars): {voice_sample_or_null}

# Task
1. 选出最像 {persona_name} 的片段 (A/B/C)。
2. 指出 ≥1 个具体语言特征 (口头禅、句法、隐喻、节奏)。
   仅凭"语气更自信"之类模糊描述不计分。
3. 给出 confidence ∈ {high, medium, low}。
4. 若完全无法区分，返回 "indistinguishable"。

# Output JSON
{"pick":"A|B|C|indistinguishable","features":[...],"confidence":"...","rationale":"<≤50 字>"}
```

## Cross-Test Consistency Checks / 跨测一致性

| 组合 | 含义 | 处置 |
|------|------|------|
| Voice 高 + Mindset Transfer 低 | voice mimicry | Weaknesses 记 `voice-without-mindset` |
| Known 10 + SKILL.md 与原答重叠 > 80% | 答案被塞进 skill | Known Test 归 0 |
| Edge 10 + Honest Boundaries < 5 | 测试诚实但文档缺边界 | 提示补 `components/honest-boundaries.md` |
| Known < 3 + Voice ≥ 7 | 会话术但答不出本人答过的事 | Knowledge Delta 应 ≤ 3 |

## Evidence Template (贴入 `## Test Evidence`)

```markdown
### Known Test
- Q1 (src: {url}) / GT: {gt} / Persona: {out} / Judge: {...}
- Q2 ... Q3 ... / Hits: N/3 → score X
### Edge Test
- Q (confirmed out-of-corpus): {...} / Persona: {...} / Class: {...} / Markers hit: [...]
### Voice Test
- A/B/C (one persona, two baseline decoys) / Pick: {letter} conf={...} / features: [...] / Correct: {letter}
```

## Anti-patterns

| 坏做法 | 为什么 | 正确做法 |
|--------|--------|---------|
| Known 3 题都选语料金句 | 虚高分 | 随机抽、跨领域 |
| Edge 题是脑筋急转弯 | 评分信号模糊 | corpus 外但合理的真实问题 |
| Voice 100 字含本人姓名 | 题眼泄露 | 过滤传记线索 |
| 给评审看"这是 persona 答的"对比原答 | 非盲 → 偏倚 | 独立会话 / 打乱顺序 |
| 证据不贴原文 | 无法复评 | 贴原问、原答、判定 |
