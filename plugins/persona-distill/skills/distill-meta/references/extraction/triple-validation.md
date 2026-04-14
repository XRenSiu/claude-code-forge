---
extraction_method: triple-validation
version: 0.1.0
purpose: 强制每一条提取出的 mental-model 或 decision-heuristic 必须被 3 个「相互独立」的语料片段支撑，杜绝单点样本带来的幻觉与过拟合。
consumed_by:
  - ../components/mental-models.md
  - ../components/decision-heuristics.md
  - persona-judge (用于 Primary Source Ratio 维度)
borrowed_from: https://github.com/alchaincyf/nuwa-skill/blob/main/references/extraction-framework.md
iteration_mode: single-pass
---

## Purpose

在 Phase 2 维度提取中，针对 mental-models 与 decision-heuristics 两类"思维断言"，强制执行三重验证（Triple Validation）。每一条被写入组件文件的断言必须能被 3 段来自不同来源的语料独立支持；否则降级为"候选"不写入产物，或在 honest-boundaries 中记录为"证据不足"。

此方法直接抄自 nuwa-skill/references/extraction-framework.md（[UNVERIFIED-FROM-README]），是 public-mirror 与 mentor schema 能否通过 persona-judge Known Test 的前置条件。

## When to Invoke

在 7-Phase 流程中的调用时机：

- **Phase 2「维度提取」**：在 mental-models-extractor 与 decision-heuristic-extractor 两个并行 agent 各自输出初稿之后、写入 `knowledge/components/*.md` 之前。
- **Phase 4「质量验证」**：persona-judge 反向调用本方法重新核对 Primary Source Ratio；若某条断言找不到 3 个独立来源，扣该维度分。
- **不在** Phase 0/1/1.5/3/5 触发。

## Input Schema

调用方必须提供：

- `{corpus}` — 已通过 Phase 1 清洗后的语料全集，至少 **3 种不同来源** 且总量 ≥ 200 段落。每段必须带 metadata：`{source_id, source_type, date, medium, audience}`。
- `{candidate_claims}` — mental-models-extractor / decision-heuristic-extractor 的初稿输出，每条形如 `{claim_id, statement, tentative_citations: [...]}`。
- `{target}` — 当前正在蒸馏的 persona 标识符（如 `steve-jobs-mirror`），用于日志追踪。
- `{existing_components}` — 已定稿的其它组件文件路径列表，供 cross-check 引用一致性。

若 `{corpus}` 来源种类 < 3，本方法直接返回 `INSUFFICIENT_SOURCES`，由上游决定是否降级 schema。

## Prompt Template

以下 prompt 原样传递给 sub-agent 执行。替换 `{...}` 占位符即可。

```
你是 triple-validation extractor。你的任务是核验一批「思维断言」是否各自满足"3 个独立来源"标准。

# 输入
- Persona 目标：{target}
- 候选断言列表（JSON 数组）：{candidate_claims}
- 语料全集（按 source_id 索引）：{corpus}
- 已定稿组件（相对路径）：{existing_components}

# 独立性判定规则（必须全部满足才算"独立"）
对任意两段引用 A 与 B，只有当以下 ≥ 2 条成立时才判为"独立"：
1. time-separated：A.date 与 B.date 相距 ≥ 90 天。
2. medium-separated：A.medium ≠ B.medium（访谈 / 书面文章 / 公开演讲 / 社交媒体 / 内部备忘录 属于不同 medium）。
3. audience-separated：A.audience ≠ B.audience（普通公众 / 专业同行 / 下属 / 一对一私信 属于不同 audience）。

同一场访谈里的 3 句话 → 不独立（全部 time-same + medium-same + audience-same）。
同一篇文章的 3 个段落 → 不独立。
本人同一次演讲被 3 家媒体转载 → 算 1 个来源，不独立。

# 执行步骤
对每条 candidate claim：
1. 在 {corpus} 中 grep 出所有潜在支撑段落，最多 10 段。
2. 从中挑 3 段，两两跑独立性判定。若找不到 3 段两两独立的组合 → status = INSUFFICIENT。
3. 若找到 → status = VALIDATED，输出 3 段引用（verbatim，保留原文语言）+ 各自 metadata。
4. 对 VALIDATED 的断言，再做一次"反证检查"：在 {corpus} 中搜索是否存在明确反驳该断言的段落；若有 → status = CONTESTED，并附反证引用。

# 输出
严格按 Output Schema 返回 JSON，不加任何解释文字。
```

## Output Schema

sub-agent 必须返回如下 JSON 数组；每个元素对应一条 candidate claim：

```json
[
  {
    "claim_id": "mm-003",
    "statement": "产品决策优先级永远是 用户体验 > 工程可行性 > 市场调研",
    "status": "VALIDATED | CONTESTED | INSUFFICIENT",
    "citations": [
      {
        "source_id": "int-2005-stanford",
        "quote": "…",
        "date": "2005-06-12",
        "medium": "public_speech",
        "audience": "general_public"
      }
    ],
    "independence_check": {
      "pair_1_2": ["time-separated", "medium-separated"],
      "pair_1_3": ["medium-separated", "audience-separated"],
      "pair_2_3": ["time-separated", "audience-separated"]
    },
    "counter_evidence": null
  }
]
```

`INSUFFICIENT` 的条目不写入产物；`CONTESTED` 的条目可写入但必须在 internal-tensions.md 中登记。

## Quality Criteria

persona-judge 或人工审阅者按以下标准验证：

1. **三独立**：每条 VALIDATED 断言的 3 段引用两两独立性标记齐全且真实可核对。
2. **原文保留**：quote 字段必须 verbatim，不得改写或翻译；语料是中文就保留中文。
3. **元数据完整**：source_id / date / medium / audience 四项不得为空或 "unknown"。
4. **反证透明**：CONTESTED 条目必须显式列出反证来源，不得静默忽略。
5. **总通过率**：单次调用中 VALIDATED 条目 ÷ 全部 candidate 应 ≥ 60%，否则提示 Phase 1 语料不足，建议回退到 Phase 1.5 Research Review。

## Failure Modes

| 坏提取 | 如何识别 |
|--------|----------|
| 3 段引用全部来自同一访谈 | independence_check 三对全空或仅 ["same"] |
| 引用被改写（非 verbatim） | 在 {corpus} 中 grep quote 原文不命中 |
| metadata 伪造（如日期虚构） | 随机抽样核对 source_id 索引 |
| 将 candidate 的"语气相似"误判为"支持该断言" | 引用段落与 statement 语义对不齐；由 persona-judge Known Test 暴露 |
| INSUFFICIENT 被强行改成 VALIDATED | counter_evidence 字段恒为 null + 低独立性维度命中 |

## Borrowed From

- 来源：[nuwa-skill/references/extraction-framework.md](https://github.com/alchaincyf/nuwa-skill/blob/main/references/extraction-framework.md) `[UNVERIFIED-FROM-README]`
- PRD 对应条目（§3.5「借鉴与改造对照」）：

  > | 三重验证 | nuwa/references/extraction-framework.md | 直接抄 |

- 本文件相对原版的改动：增加了 time/medium/audience 三条独立性细则（PRD §3.2 未写细节，由本实现补齐）；新增 CONTESTED 状态与 internal-tensions.md 的联动。
