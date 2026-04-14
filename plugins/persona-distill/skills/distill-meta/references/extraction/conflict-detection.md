---
extraction_method: conflict-detection
version: 0.1.0
purpose: 在 Phase 2 组件定稿之后、Phase 3 组装之前，跨组件与跨语料自动交叉核对"事实性矛盾"，写入 `knowledge/conflicts.md`。surfaces 矛盾，绝不 resolve。
consumed_by:
  - ../../agents/conflict-detector.md
  - persona-judge（可选消费：用 `conflicts.md` 作为 Primary Source Ratio / Honest Boundaries 的反向核对）
borrowed_from: https://github.com/pseudoyu/immortal-skill
emits: knowledge/conflicts.md
iteration_mode: single-pass
---

## Purpose

本方法检测的是**事实性矛盾**（factual contradictions）：两份来源对同一个事实断言 X 给出相互否定的描述（一边说 X，另一边说 ¬X）。
它**不是** `internal-tensions`——后者记录的是 persona 同时持有、长期并存、无意调和的**稳定对立极**（A 与 B 都真），例如"完美主义 vs 交付节奏"。两者在语义层面**不重叠**：

| 文件 | 记录什么 | 判据 |
|------|---------|------|
| `components/internal-tensions.md` | persona 长期**同时持有**的稳定两极（A 真 ∧ B 真，两者都被 persona 承认） | A、B 在同一抽象层级且 persona **拒绝调和** |
| `knowledge/conflicts.md` | 来源 / 组件 / 时期之间的**事实不一致**（A 与 ¬A 不能同真） | 至少一方陈述错误，或 persona 改变立场，或声称 vs 行为不符 |

见 `../components/internal-tensions.md` 的 §Anti-example——"同时怀有 A、B 并行"是 tension；"A 文件说 X、B 文件说 ¬X"是 conflict。必须两边交叉引用，防止 agent 把一方错归另一方。

设计原则来自 master plan §9 决定 #8 "矛盾是真实感的来源，不能被抹平"（借自 immortal-skill 的 `conflicts.md` 模式，`[UNVERIFIED-FROM-README]`）。**本方法只 surface，不 resolve**——`suggested_handling` 字段永远是"如何让两条都保留下去"的指引，不是"选哪条对"的裁决。

## When to Invoke

- **Phase 3.5「冲突检测」**（新增阶段）：Phase 2.5 iterative-deepening 合并完成之后、Phase 3 skill-assembly 开始之前。
- **Phase 4「质量验证」**（可选）：persona-judge 可反向调用本方法重扫，若新增 conflict 未被记录 → 扣 Honest Boundaries 维度分。
- **不在** Phase 0/1/1.5/2/2.5/5 触发。

## Taxonomy of Conflicts

以下 4 类穷举本方法允许识别的 kind。其它（如"不同人对他的评价相左"——那是语料偏见，由 corpus-scout 处理）不在此范围。

### (a) Factual — 两份来源对同一事实断言直接冲突

*Mini-example*: 访谈文稿说 persona "从未读过 Heidegger"；persona 的 2012 博客原文引用了 Heidegger 第三章。→ 两份来源对"是否读过 X"给出 ¬/∧ 关系的断言。

### (b) Value-shift — 早期 vs 晚期语料显示**立场已改变**

*Mini-example*: 2005 演讲 "开源是未来唯一的选择"；2020 访谈 "当年对开源的信仰是幼稚的"。→ persona 自己已调和（`suggested_handling = TIMEBOUND`），不是 tension，因为它被明确"放弃 A 选 B"过。

### (c) Stated-vs-behavioral — persona 声称 X，行为模式表现 ¬X

*Mini-example*: `components/identity.md` 写"极度厌恶会议"（来自 hard-rules 声明）；`components/decision-heuristics.md` 基于日程语料显示"每周主动发起 ≥ 8 次一对多会议"。→ 声称与行为不符。

### (d) Component-self — 两个组件基于**同一批语料**提取出不兼容断言

*Mini-example*: `mental-models.md` 得出 "决策优先级永远是用户体验 > 工程"；`decision-heuristics.md` 从同批案例得出 "在 P0 交付前工程约束永远 override 用户体验"。→ 两个组件对同一决策过程给出相反方向的提取。

**特别说明**：如果两个 claim 其实只是**措辞不同但语义一致**（"喜欢 X" vs "偏好 X"、"总是做 X" vs "通常做 X"），**不是** conflict，进入 §Failure Modes "near-contradictions"。

## Detection Procedure

### Step 1 — Build claim index per component

对每个 `knowledge/components/*.md`，抽取形如 `{claim_id, component, statement, source_ids: [...], polarity}` 的索引项。`polarity` 是对否定词 / 量词的粗糙标注（例如 "never / always / only / > 50%" 都是强极性）。

### Step 2 — Pairwise compare claims across components

对任意两条跨组件 claim (A, B) ——若 A 与 B 议题相同 **且** polarity 相反（或数值断言不相交），flag 为候选。

- 语义否定：A.statement 经否定重写后与 B.statement 余弦相似 ≥ 0.75 → 候选。
- 数值不一致：A 说 "80% 的时间"，B 说 "罕见 / < 10%" → 候选。

### Step 3 — Temporal scan

对同议题簇内 claim，若其 `source_ids` 时间戳分布跨 ≥ 3 年且中位数差 ≥ 2 年，**且** polarity 相反，标记为 `kind = value-shift`。

### Step 4 — Stated-vs-behavioral scan

把 `identity.md` / `hard-rules.md` 里的**声称式断言**（"I never X"、"always Y"）作为左手；把 `decision-heuristics.md` / `mental-models.md` 观察到的**行为模式**（统计出的高频行动）作为右手；若声称与行为 polarity 相反 → `kind = stated-vs-behavioral`。

### Step 5 — 写入 `knowledge/conflicts.md`

按 §Output Format 渲染，保留幸存（未被合并 / 未被降级为 near-contradiction）的 conflict 条目。

## Output Format

`knowledge/conflicts.md` 结构：

```markdown
---
detector_version: 0.1.0
generated_at: <ISO8601>
persona_fingerprint: <manifest.fingerprint>
total_conflicts: <N>
auto_resolved: 0   # MUST be 0; this detector never resolves
---

## User-Appended Conflicts

<!-- 保留用户手写条目，verbatim 不动；若无则省略整个 H2 -->

## Auto-Detected Conflicts

### conflict-01
- id: cf-01
- kind: factual | value-shift | stated-vs-behavioral | component-self
- components_involved: [<component-slug>, <component-slug>]
- claim_a:
    statement: "<tight paraphrase 或 verbatim>"
    source_id: "<file#Lxx or corpus item>"
    date: "<YYYY-MM-DD 或 unknown>"
- claim_b:
    statement: "<...>"
    source_id: "<...>"
    date: "<...>"
- evidence_a: "<verbatim quote>"
- evidence_b: "<verbatim quote>"
- confidence: LOW | MED | HIGH
- suggested_handling: PRESERVE_BOTH | FLAG_FOR_USER | TIMEBOUND
- handling_note: "<一句话解释为什么选这个 handling，不得包含『正确答案是 X』>"

### conflict-02
…
```

### `suggested_handling` 枚举

**本字段只能取以下三值之一；任何"裁决哪条正确"的措辞都被视为违规**：

| 值 | 何时使用 | 下游效果 |
|----|---------|---------|
| `PRESERVE_BOTH` | 两条都可能真，或都部分真 | Phase 3 组装时两条都进对应组件 |
| `FLAG_FOR_USER` | agent 置信度不足判断该怎么对待 | 在 Phase 5 delivery 总结中明确告诉用户 |
| `TIMEBOUND` | Value-shift 类：claim A 发生在 YYYY-a、claim B 发生在 YYYY-b | 两条都保留并标注时期，thought-genealogy 可引用 |

### `confidence` 评分规则

- `HIGH` = 双方都 ≥ 2 独立 source_id 支撑 + polarity 明确 + 议题同层级。
- `MED`  = 双方各 1 source_id，或 polarity 模糊但仍可区分。
- `LOW`  = 仅一方证据充分，或议题匹配度欠佳；此类 conflict 必须 `suggested_handling = FLAG_FOR_USER`。

## Quality Criteria

1. **双证据**：每条 conflict 必须 `evidence_a.source_id` ≠ `evidence_b.source_id`；同一 source 的内部不一致不是 conflict（是该 source 本身矛盾，由 corpus-scout 标注）。
2. **零自动裁决**：`auto_resolved` 永远 = 0；`suggested_handling` 永远 ∈ {PRESERVE_BOTH, FLAG_FOR_USER, TIMEBOUND}，任何含"正确 / 更可信 / 应采用"字样的 handling_note 直接拒收。
3. **置信度有据**：`confidence` ∈ {LOW, MED, HIGH}，按 §Output Format 中的规则判定，不许凭感觉。
4. **Kind 正交**：每条 conflict 单属一 kind；若一条 claim 同时触发 (b)+(c)，只取证据最强的一个——不要双重计数。
5. **与 internal-tensions 正交**：若一条候选 conflict 的 claim_a、claim_b 已出现在 `components/internal-tensions.md` 作为 tension pair → 不重复写入 conflicts.md；tension 在前，conflict 为冗余剔除。

## Failure Modes

| 坏提取 | 如何识别 | 正确做法 |
|--------|---------|---------|
| **漏掉 conflict**（false negative，这里比 false positive 更严重：persona 的真实感正来自矛盾显形） | Phase 4 persona-judge 跑 Known Test 时，用户输入一个诱发两面的提示，产物只给一面 → 必然是 conflict 没被登记 | 放宽 polarity 判定阈值到 0.65；倾向于多报、让 `FLAG_FOR_USER` 吸收不确定性 |
| **合并 near-contradictions** | 把 "喜欢 X" 与 "偏好 X" 当 conflict；把 "通常" 与 "总是" 当 conflict | near-contradiction 语义余弦 ≥ 0.85 时丢弃；量词差异非对立不是 conflict |
| **auto-resolve smuggling** | `handling_note` 含 "the 2020 statement supersedes" / "应以 X 为准" | 拒收；重写为中立陈述 "2005 与 2020 立场相反，TIMEBOUND 保留" |
| **重复 internal-tensions 的 pair** | conflict.claim_a / claim_b 精确匹配 `internal-tensions.md` 的 statement_a / statement_b | 剔除该 conflict；加 note "already-captured-as-tension" |
| **伪 source 交叉**：evidence_a 与 evidence_b 其实指向同一 source 的不同段落 | source_id 前缀相同 → 拒收 | 必须跨 source 才算 conflict，单 source 内矛盾归 corpus-scout |

## Borrowed From

- **immortal-skill** (`agenmod/immortal-skill`) — `conflicts.md` 文件模式原型。`[UNVERIFIED-FROM-README]`。master plan §9 决定 #8：
  > "矛盾是真实感的来源，不能被抹平——参考 immortal-skill 的 `conflicts.md`。"
- **PRD §3.2（Phase 3 Skill Assembly）**：原文把 `conflicts.md` 列为 Phase 3 的可选产物，最初只承认"用户人工追加"流。本方法把它扩展为 Phase 3.5 的自动探测流，新旧并存（见 `../../agents/conflict-detector.md` §Interaction with user-appended conflicts）。
- **与 tension-finder 的区别**：见本文件 §Purpose 的对照表；两者必须在各自文件顶部互相 pointer（`internal-tensions.md` 指向此处，此处指向 `internal-tensions.md`）。
