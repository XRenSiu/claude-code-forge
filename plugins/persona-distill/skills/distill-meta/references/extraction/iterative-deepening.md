---
extraction_method: iterative-deepening
version: 0.1.0
purpose: 在 Phase 2 产出初稿之后，对原始语料做一次全文再扫描，寻找未被任何现有组件捕获的模式，作为 Phase 2.5 候选项交给用户确认。
consumed_by:
  - Phase 2.5 编排（distill-meta 主流程）
  - 所有 ../components/*.md （候选可能补录到任一组件）
borrowed_from: https://github.com/cyber-immortal/cyber-figures
iteration_mode: single-pass
---

## Purpose

cyber-figures 经验（PRD §2 / §9）：「Layer 3 是 405 段全文扫描后才发现的」——好的蒸馏是多轮深挖的结果。本方法承担 Phase 2.5 的"再扫一遍"职责：在 Phase 2 各组件 agent 写完初稿之后，拿完整语料对现有组件做"覆盖差集"检测，吐出"可能漏掉的东西"交给用户裁决。

### V1 SCOPE LIMIT (Critical)

PRD §10 已明确声明："Phase 2.5 迭代深化是**理念，不是成熟方法**"。风险评估 DEP-05 与 SPEC-02 进一步收紧 v1 范围：

- **v1 只做单次再扫描（single-pass re-scan）**。
- **不做**真正的 3-round 迭代、收敛判定、自动回填。
- 所有需要"多轮收敛 + 自动 merge"的功能移到 v2 TODO。

```text
TODO(v2): multi-round iteration with convergence detection
  - 多轮：每轮输入是上轮的候选 + 本轮新语料切片，最多 3 轮。
  - 收敛判定：当新候选 / 前两轮候选 Jaccard 相似度 > 0.8 时停止。
  - 自动回填：用户高置信度通过的候选自动 patch 进对应组件文件。
  - 轮间去重：避免把同一现象反复当成"新发现"。
  - 跨组件归属判定：候选落到哪个组件需 LLM 投票而非单 agent 决定。
```

## When to Invoke

- **Phase 2.5**，在 Phase 2 所有组件 agent 完成且 Research Review 过后；先于 Phase 3 Skill 组装。
- **单次调用**，不循环；调用一次就退出。
- 用户可在 Phase 5 之后手动再次触发做"追加深挖"，但那仍是 single-pass。

## Input Schema

- `{corpus}` — Phase 1 清洗后的全量语料（不是抽样），**完整原文**。
- `{target}` — persona 标识符。
- `{existing_components}` — Phase 2 已写入的所有 `knowledge/components/*.md` 文件路径 + 其文本内容。**必须全部包含**，否则无法做覆盖差集。
- `{schema}` — 当前 schema 名；决定候选可归入哪些组件类型。
- `{phase2_stats}` — Phase 2 输出的覆盖率元数据（哪些 source_id 已被至少一个组件引用）。

## Prompt Template

```
你是 iterative-deepening scanner（v1 single-pass 版）。你的任务是在 {target} 的完整语料上找出 Phase 2 没有捕获的模式，作为 Phase 2.5 候选项。

# 工作模式
- 本次是 single-pass：跑一次就结束，不要在输出里规划"下一轮"。
- 你不回写任何组件文件；只生成候选清单交给用户裁决。

# 输入
- Persona：{target}
- Schema：{schema}
- 全量语料：{corpus}
- Phase 2 已定稿组件（完整文本）：{existing_components}
- Phase 2 覆盖统计：{phase2_stats}

# 执行步骤
1. 计算"语料覆盖差集"：
   - 在 {corpus} 中找出未被任何 {existing_components} 引用或解释的段落（通过 source_id 或 verbatim 片段匹配）。
   - 未覆盖段落数 / 总段落数 = coverage_gap_ratio；若 < 0.1，视作 Phase 2 已充分覆盖，直接返回 status = NO_GAPS。
2. 对未覆盖段落做聚类（议题 / 语气 / 决策模式 / 关系网络 …），每簇 ≥ 3 段才算"可能是漏掉的模式"。
3. 对每个候选簇：
   a. 判断它最可能归入哪个组件（mental-models / decision-heuristics / internal-tensions / thought-genealogy / honest-boundaries / expression-dna …）。
   b. 用一句话描述"这是什么模式"。
   c. 附 3 段 verbatim 证据。
   d. 与现有组件逐段做相似度对比；若相似度 > 0.7 标记为 LIKELY_DUPLICATE，不是真新发现。
4. 所有候选按 "possible_novelty_score" 降序返回（novelty_score ∈ 0..1，基于与现有组件的语义距离）。

# 失败模式（必须主动避免）
- 把 Phase 2 已经写过的内容换个措辞又报一遍 → 必须跑相似度对比，> 0.7 标 LIKELY_DUPLICATE。
- 把二手转述当作新模式 → 证据必须来自一手语料的 source_id。
- 为凑候选数而降低簇内段落数阈值 → 簇内 < 3 段必须丢弃。

# 输出
严格按 Output Schema 返回 JSON。候选只提议，不做自动 merge（v1 限制）。
```

## Output Schema

```json
{
  "target": "steve-jobs-mirror",
  "mode": "single-pass",
  "status": "OK | NO_GAPS | INSUFFICIENT_CORPUS",
  "coverage_gap_ratio": 0.23,
  "candidates": [
    {
      "candidate_id": "p25-01",
      "suggested_component": "../components/decision-heuristics.md",
      "pattern_description": "在产品 demo 前 48 小时会亲自走一遍 happy path 并否决任何需要解释的交互。",
      "evidence": [
        {"source_id": "bio-2011-ch21", "quote": "…"},
        {"source_id": "int-2007-d5", "quote": "…"},
        {"source_id": "team-2003-memo", "quote": "…"}
      ],
      "novelty_check": {
        "max_similarity_to_existing": 0.31,
        "flagged_as_duplicate": false
      },
      "possible_novelty_score": 0.72
    }
  ],
  "v2_todo_surfaced": [
    "本轮未做多轮收敛，某些候选可能在 round 2 才会稳定显现。"
  ]
}
```

**写入策略（v1）**：所有候选一律由用户在 Phase 2.5 review 中逐条裁决 `ACCEPT / REJECT / DEFER`；distill-meta 根据用户选择回写相应组件。scanner 本身不写文件。

## Quality Criteria

1. **single-pass 合规**：输出里不得出现"下一轮会…"类表述；`mode` 字段恒为 "single-pass"。
2. **覆盖差集真实**：coverage_gap_ratio 基于实际 source_id / verbatim 匹配，而非 agent 估算。
3. **novelty 可验**：max_similarity_to_existing 数值由显式嵌入比较得出，不是直觉。
4. **证据门槛**：每个候选 ≥ 3 段 verbatim 引用，且 source_id 均指向一手语料。
5. **无自动写入**：candidates 字段之外没有任何 side-effect；确保 v1 人类审核闭环不被跳过。
6. **不破坏 Phase 2**：当 coverage_gap_ratio < 0.1 时必须返回 NO_GAPS 而非硬造候选。

## Failure Modes

| 坏提取 | 如何识别 |
|--------|----------|
| False-positive deepening：把 Phase 2 内容换词重报 | novelty_check.max_similarity > 0.7 但仍标 false；抽查 3 条能 grep 出已存在 |
| 候选簇 < 3 段即输出 | evidence 数组长度 < 3 |
| 跨越 v1 边界，尝试多轮 | 输出字段出现 "round_2" / "iteration_index" / "converged" 等关键字 |
| 把二手转述当一手证据 | source_id 指向百度百科/知乎（blacklist），而非一手语料 |
| NO_GAPS 被强行改成 OK 以凑候选 | coverage_gap_ratio < 0.1 但 candidates 非空 |

## Borrowed From

- 来源：[cyber-figures](https://github.com/cyber-immortal/cyber-figures) `[UNVERIFIED-FROM-README]`
- PRD §1 / §2 核心观察 #4：

  > 质量靠迭代，不靠一次性：cyber-figures 那句「Layer 3 是 405 段全文扫描后才发现的」揭示了真相——好的蒸馏是多轮深挖的结果。

- PRD §3.2 Phase 2.5 定义：

  > Phase 2.5 迭代深化（新增，借鉴 cyber-figures）
  > ├── 全文扫描检测遗漏维度
  > ├── 最多 3 轮迭代
  > ├── 每轮产出"上轮错过的 X"
  > └── 用户确认后合并

- PRD §10 self-admitted limit：

  > Phase 2.5 迭代深化是**理念，不是成熟方法**。cyber-figures 的经验说明这件事有价值，但怎么系统化做好还需要探索。

- 本文件 v1 策略（single-pass、人类裁决闭环、不自动 merge）依据风险评估 DEP-05 + SPEC-02；PRD 写的是 3 轮，v1 主动收紧到 1 轮并把其余功能列入 TODO(v2)。
