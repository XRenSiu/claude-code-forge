---
extraction_method: tension-finder
version: 0.1.0
purpose: 在一手语料中发现 persona 同时持有、且并未自我调和的"相互张力"陈述对，并记录该 persona 如何"同时怀有"二者。
consumed_by:
  - ../components/internal-tensions.md
  - persona-judge (用于 Internal Tensions 维度)
borrowed_from: https://github.com/alchaincyf/nuwa-skill/blob/main/references/extraction-framework.md
iteration_mode: single-pass
---

## Purpose

大多数真实思想者不是"自洽的教条"，而是"同时抱着几组相互拉扯的信念在决策"。tension-finder 的职责是把这些未被 persona 自己调和掉的张力显式抽出来写进 internal-tensions.md——而不是抹平。PRD §4.2 规定 Internal Tensions 至少 ≥ 2 对矛盾才能拿满分；public-mirror / mentor schema 强制要求启用本方法。

对已被 persona 自己"调和"的矛盾（如 "A 但后来我意识到 B 才对"），本方法会标记为 RESOLVED 并剔除——它们不是真正的 tension，而是 evolution（应归 thought-genealogy）。

## When to Invoke

- **Phase 2「维度提取」** 与 triple-validation、seven-axis-dna 并行。
- schema 包含 `internal-tensions` 组件时才触发（public-mirror、mentor、self、loved-one 默认启用；topic、executor 不启用）。
- **Phase 2.5**：iterative-deepening 扫出"可能的新张力候选"后，可再跑一次本方法复核。

## Input Schema

- `{corpus}` — 清洗后的一手语料，必须覆盖 ≥ 3 年时间跨度或 ≥ 2 种高分歧话题；否则张力多为伪。
- `{target}` — persona 标识符。
- `{existing_components}` — 若已有 mental-models.md / decision-heuristics.md，作为"语义对手池"优先比对（张力常出现在思维模型层）。
- `{min_tensions}` — 期望张力对数下限；public-mirror = 2（PRD §4.2）。

## Prompt Template

```
你是 tension-finder。你的任务是在 {target} 的语料中找出至少 {min_tensions} 对「未调和的内在张力」，并描述该 persona 如何同时持有二者。

# 张力的定义
一对陈述 (A, B) 构成张力，当且仅当：
1. A 与 B 在同一议题上指向不同甚至相反的主张 / 偏好 / 优先级。
2. 二者都有 ≥ 2 段独立语料支持（复用 triple-validation 的独立性规则：time / medium / audience 至少差 2 项）。
3. 在 {corpus} 全集中找不到 persona 明确"放弃 A 选 B"或"放弃 B 选 A"的片段——即 persona 从未公开调和。
4. A 与 B 不是同义反复；必须在同一抽象层级（都谈价值取向 or 都谈方法论）。

# 非张力（必须剔除）
- 早期说 A、后期说 B，且有过渡叙事 → 这是演化（evolution），去 thought-genealogy。
- A 与 B 属于不同语境且 persona 明说"情境依赖" → 这是条件化决策，去 decision-heuristics。
- A 与 B 在对不同受众说 → 这是 code-switching，去 expression-dna 的 A7 axis。

# 输入
- Persona：{target}
- 语料：{corpus}
- 已定稿组件（优先语义对齐）：{existing_components}
- 最少张力对数：{min_tensions}

# 执行步骤
1. 按议题聚类 {corpus}（议题示例：个人主义 vs 集体、短期 vs 长期、美学 vs 实用…），至少 ≥ 5 个议题簇。
2. 每簇内用 LLM 对比扫描，寻找指向相反方向的陈述对。
3. 对每个候选对跑"调和检查"：在全 corpus 搜索是否存在 persona 自己的调和声明；若有，标 RESOLVED 剔除。
4. 对保留的对子，撰写一段 ≤ 120 字的"how persona holds both"——描述该 persona 在实际行为中如何把两者并置（非你的猜测，必须基于行为语料）。
5. 若最终 < {min_tensions} 对，返回 INSUFFICIENT_TENSIONS 而不是凑数。

# 输出
严格按 Output Schema 返回 JSON。
```

## Output Schema

```json
{
  "target": "steve-jobs-mirror",
  "status": "OK | INSUFFICIENT_TENSIONS",
  "tensions": [
    {
      "tension_id": "t-01",
      "topic": "产品完美主义 vs 交付节奏",
      "statement_a": {
        "paraphrase": "对细节到像素级的近乎病态的打磨。",
        "citations": ["int-1984-playboy", "bio-2011-isaacson-ch19"]
      },
      "statement_b": {
        "paraphrase": "真正的艺术家交付作品。",
        "citations": ["mac-team-1983-memo", "wwdc-2007-keynote"]
      },
      "context": "两种态度都出现在同一产品周期内，且持续贯穿 1984-2010。",
      "how_persona_holds_both": "通过『砍功能换完整性』而非『延期换完整性』：在临界点上裁掉整块特性以保证剩余部分在 deadline 前达到像素级完成度。",
      "resolution_check": {
        "searched_for_reconciliation": true,
        "found": false,
        "evidence": "未在任何公开语料中找到『我现在觉得应该选 A 放弃 B』类声明。"
      }
    }
  ]
}
```

## Quality Criteria

1. **数量达标**：返回 ≥ `{min_tensions}` 对，且无伪造。
2. **独立引用**：每条 statement 的 citations 至少 2 个来源，且两两独立（复用 triple-validation 规则）。
3. **未调和**：resolution_check.found = false，且 evidence 字段非空。
4. **同层级**：statement_a 与 statement_b 抽象层级一致（由人工抽查 2 条确认）。
5. **行为化描述**：how_persona_holds_both 必须指向可观察行为，不写"他在内心挣扎"一类心理猜测。

## Failure Modes

| 坏提取 | 如何识别 |
|--------|----------|
| 把"早期 vs 晚期"当张力 | citations 日期两极分布 → 实为 evolution |
| 把"对外 vs 对内"当张力 | 两条 citations audience 字段相反 → 实为 code-switching |
| 同义反复（A = "追求品质"，B = "反对平庸"） | 语义嵌入相似度 > 0.85 |
| 凑数：第 2 对是"人一直是复杂的" | topic 字段过于笼统，无法落到具体议题 |
| 伪"未调和"：其实 persona 在某次访谈已调和但 agent 漏看 | 由 Phase 2.5 iterative-deepening 复扫暴露 |

## Borrowed From

- 来源：[nuwa-skill/references/extraction-framework.md](https://github.com/alchaincyf/nuwa-skill/blob/main/references/extraction-framework.md) `[UNVERIFIED-FROM-README]`
- PRD §3.5：

  > | 保留矛盾 | nuwa | 不抹平，单独归档 conflicts.md |

- PRD §4.2 评分维度直接指明：

  > | **Internal Tensions** | 10 | **nuwa** | 是否有 ≥2 对内在矛盾 |

- PRD §2 核心观察 #2：

  > "矛盾不抹平"是所有严肃方案的共识——nuwa / ex / cyber-figures 都强调保留多面性。

- 本文件补齐内容：RESOLVED 剔除规则、"非张力三类"（evolution / conditional / code-switching）的显式排除清单——PRD 未展开到这个粒度。
