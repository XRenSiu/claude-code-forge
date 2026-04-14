---
extraction_method: iterative-deepening
version: 0.2.0
purpose: 在 Phase 2 产出初稿之后，对原始语料做多轮（最多 3 轮）覆盖差集扫描，寻找未被任何现有组件捕获的模式。v2 新增收敛判定、跨组件归属投票和高置信度自动回填。
consumed_by:
  - Phase 2.5 编排（distill-meta 主流程）
  - 所有 ../components/*.md （候选可能补录到任一组件）
  - agents/candidate-merger.md （执行 auto-patch-back）
borrowed_from: https://github.com/cyber-immortal/cyber-figures
iteration_mode: multi-round
---

## Purpose

cyber-figures 经验（PRD §2 / §9）：「Layer 3 是 405 段全文扫描后才发现的」——好的蒸馏是多轮深挖的结果。本方法承担 Phase 2.5 的"反复扫一遍"职责：在 Phase 2 各组件 agent 写完初稿之后，拿完整语料对现有组件做"覆盖差集"检测；每轮产出一批候选，用户裁决后高置信度项自动回填，直到候选集合相对上一轮收敛（Jaccard > 0.8）或达到 3 轮上限为止。

### V2 EXECUTION (multi-round now live)

PRD §3.2 原始意图是 3 轮迭代；v0.1.0 出于风险评估 DEP-05 / SPEC-02 收紧到 single-pass。v0.2.0 恢复 PRD §3.2 的 3 轮流程，并补齐收敛判定、轮间去重、跨组件归属投票、以及"高置信度候选自动回填"四项支撑机制。

> **History note**：v0.1.0 曾以 `iteration_mode: single-pass` 运行，仅做一次再扫描，所有候选 100% 交人工裁决，不做自动 merge。v0.2.0 在保留"人工裁决闭环"作为默认的同时，新增 `AUTO` 裁决通道用于自动回填——此路径仅对 `possible_novelty_score ≥ 0.75` 的候选开放，且所有 auto-patch 都写入 merge log 供事后审计。**v1 single-pass 语义仍然受支持**：调用方传 `max_rounds = 1` 即退化为 v1 行为。

```text
TODO(v3): 跨 persona 的 cross-skill novelty mining
  - 当同一 target 被多次蒸馏时，把历史 skill 的 excluded_candidates 作为冷启动输入。
  - 本版本不做——多轮迭代已解决单 skill 内部的收敛需求。
```

## When to Invoke

- **Phase 2.5**：Phase 2 所有组件 agent 完成且 Research Review 过后；先于 Phase 3 Skill 组装。
- **多轮调用**：由 `iterative-deepener` agent 在单次 Phase 2.5 内自动循环最多 3 轮；每轮结束等待 distill-meta 的 user-verdict 回执后再决定是否进入下一轮。
- 用户可在 Phase 5 之后手动再次触发完整 Phase 2.5（新一次多轮循环），此为"追加深挖"。

## Input Schema

- `{corpus}` — Phase 1 清洗后的全量语料（不是抽样），**完整原文**。
- `{target}` — persona 标识符。
- `{existing_components}` — Phase 2 已写入的所有 `knowledge/components/*.md` 文件路径 + 其文本内容。**必须全部包含**。每轮之间 `existing_components` 会因上一轮 auto-patch 而更新，必须重新读取。
- `{schema}` — 当前 schema 名；决定候选可归入哪些组件类型。
- `{phase2_stats}` — Phase 2 输出的覆盖率元数据。
- `{prior_round_candidates}` — 上一轮的 surviving candidates（含 ACCEPT / AUTO 已回填 + DEFER 待议；REJECT 已剔除）。轮 1 为空数组。
- `{max_rounds}` — 默认 3；传 1 则退化为 v0.1.0 single-pass 行为。
- `{jaccard_threshold}` — 默认 0.8；见 `convergence-detection.md`。

## Prompt Template

```
你是 iterative-deepening scanner（v2 multi-round 版）。本次是 round {N}/{max_rounds}。

# 工作模式
- 本轮目标：在 {target} 的完整语料上找出到目前为止（Phase 2 + 前 N-1 轮 auto-patch）仍未捕获的模式。
- 你本身不写组件文件——auto-patch 由 candidate-merger agent 执行，你只产出候选清单 + novelty 打分。
- 你必须计算本轮候选集与上一轮 {prior_round_candidates} 的 Jaccard 相似度（见 ../extraction/convergence-detection.md），并在输出中显式报告 converged 标记。

# 输入
- Persona：{target}
- Schema：{schema}
- 全量语料：{corpus}
- 当前已定稿组件（含前 N-1 轮 auto-patch 结果）：{existing_components}
- Phase 2 覆盖统计：{phase2_stats}
- 上一轮 surviving candidates：{prior_round_candidates}
- 本轮序号：{N}；上限：{max_rounds}；Jaccard 阈值：{jaccard_threshold}

# 执行步骤
1. **Carry-over 去重**：对 {prior_round_candidates} 中 status ∈ {ACCEPT, AUTO} 的条目，算出其 candidate identity hash（见 convergence-detection.md），将这些 hash 加入本轮 scan 的排除集。
2. **覆盖差集**：基于 source_id / verbatim 片段匹配，找出 {corpus} 中未被 {existing_components} 引用、且 candidate identity hash 不在排除集中的段落。
   - coverage_gap_ratio = 未覆盖段落数 / 总段落数；< 0.1 → status = NO_GAPS，跳到步骤 6。
3. **聚类**：按议题 / 语气 / 决策模式 / 关系网络聚类未覆盖段落；每簇 ≥ 3 段才算候选。
4. **候选画像（每簇）**：
   a. 判断候选最可能归入的组件。若 ≥ 2 个组件都合理 → 在 candidate 字段中列出 `attribution_vote_needed: true` 并附候选组件列表（由上游 spawn 3 个归属投票 mini-agent 决断；见 §Cross-Component Attribution Voting）。
   b. 1 句话 pattern_description；3 段 verbatim 证据（均来自一手语料，source_id 不得在 blacklist）。
   c. 与现有组件做语义相似度；max_similarity > 0.7 → flagged_as_duplicate = true。
   d. 计算 candidate identity hash。
5. **打分排序**：按 possible_novelty_score 降序。
6. **收敛判定**：
   - 若 N == 1 → converged = false，prior_round_jaccard = null（首轮无可比对象）。
   - 否则：jaccard = |Sn ∩ Sn-1| / |Sn ∪ Sn-1|（集合元素为 candidate identity hash）。
   - jaccard > {jaccard_threshold} → converged = true，下一轮不再启动。
   - jaccard ≤ {jaccard_threshold} 且 N < max_rounds → converged = false，distill-meta 在本轮 user verdict 到齐后再唤起下一轮。
   - N == max_rounds → converged = true（轮数上限亦视作"停止"，但在 status 中显式标注 MAX_ROUNDS_REACHED 以供人审）。
7. **auto-patch hinting**：对 possible_novelty_score ≥ 0.75 的候选，在输出中把 suggested_verdict 设为 "AUTO"，其余设为 "REVIEW"。最终 verdict 由用户确认，你不直接写文件。

# 失败模式（必须主动避免）
- 复述 Phase 2 已写内容 → 相似度 > 0.7 必须 flagged_as_duplicate = true。
- 复述上一轮 ACCEPT 候选 → identity hash 命中 carry-over 排除集仍被提交 → 直接拒收。
- 把二手转述当一手证据 → source_id 指向 blacklist。
- 簇内 < 3 段凑数 → 丢弃而非输出。
- jaccard > {jaccard_threshold} 但输出 converged = false → 结构性失败，拒收。

# 输出
严格按 Output Schema 返回 JSON。高置信候选 (AUTO) 仍须用户点头才由 candidate-merger 合并。
```

## Multi-Round Protocol

1. **Round 1** — 无 carry-over；扫描整份 corpus；输出候选清单 + jaccard = null + converged = false。等待 distill-meta 把 user verdict 附回（每条 ACCEPT / AUTO / REJECT / DEFER）。
2. **Round 2** — 输入 round 1 ACCEPT + AUTO + DEFER 合集作为 `prior_round_candidates`；existing_components 已被 round 1 auto-patch 更新；重新计算覆盖差集 + jaccard。若 jaccard > 0.8 → converged = true，停止。
3. **Round 3** — 入参同 round 2（基于 round 2 的 surviving 集）；本轮无论 jaccard 取值，`converged` 被强制设为 true，status 附加 `MAX_ROUNDS_REACHED`；不再启动 round 4。
4. 每轮之间必须经过 user verdict（或自动 AUTO 路径的 merge log 回执）后才进入下一轮；不得并行多轮。

## Convergence Detection

- 候选身份哈希（candidate identity hash）= `sha1(suggested_component || "|" || canonical(pattern_description) || "|" || top2_source_ids)`。
- canonical 化：去除标点、统一小写、合并连续空白；仅用于比对，不改变输出中的原文。
- Jaccard 公式：`J(Sn, Sn-1) = |Sn ∩ Sn-1| / |Sn ∪ Sn-1|`，集合元素为上述 hash。
- 阈值：`jaccard > 0.8` → CONVERGED。阈值的选择与边界情况详见 `convergence-detection.md`。
- 首轮（N = 1）不做 Jaccard 判定，prior_round_jaccard = null。

## Cross-Round Dedup

- **carry-over 规则**：若某候选在第 N 轮被裁决为 ACCEPT 或 AUTO（即 candidate-merger 已合并到组件文件），其 identity hash 进入排除集，第 N+1 轮扫描时**跳过**与该 hash 匹配的新候选，不再视作"新发现"。
- REJECT 候选同样进入排除集（避免反复提议被用户否决的模式），但记录在 `excluded_candidates[]` 便于审计。
- DEFER 候选**不**进入排除集——用户明确表示"下轮再看"。
- existing_components 文件在 round 之间会因 auto-patch 增长；下一轮的覆盖差集计算必须基于最新版本。

## Cross-Component Attribution Voting

当本轮某候选的 `attribution_vote_needed = true`（≥ 2 个组件都可能是它的归属地）时：

1. distill-meta 为该候选 spawn **3 个并行的 ephemeral 归属投票 mini-agent**（各自独立读取 corpus + 候选 evidence + 候选组件列表）。
2. 每个 mini-agent 只输出一个 JSON：`{candidate_id, vote: "<component_slug>", rationale}`。
3. 多数决（majority wins）。
4. **平票时**（3 票对 1v1v1 或 2 候选组件 1v1）：按"现有覆盖更小的组件优先"规则裁定——统计各候选组件当前文件行数，分配给行数最小者。此规则鼓励均衡覆盖，避免强势组件吞并新候选。
5. 投票结果写入输出的 `attribution_votes[]`，供用户在 review UI 中看到完整票型。

投票仅在被请求时 spawn；无歧义候选不投票（suggested_component 直接生效）。

## Auto-Patch Rules

仅当以下条件同时成立时，candidate-merger agent 才执行 auto-patch：

1. `possible_novelty_score ≥ 0.75`；
2. `user_verdict ∈ {ACCEPT, AUTO}`；
3. `flagged_as_duplicate = false`；
4. 所有 evidence 的 `source_id` 均**不**在 blacklist（`../source-policies/blacklist.md`）。

auto-patch 具体写入规则（详见 `../../agents/candidate-merger.md`）：

- **追加位置**：目标组件文件底部新增 H3 `### Added in round {N}`（若该 H3 已存在则 append 到同一 H3 下）。
- **内容格式**：`- pattern_description` + `- evidence:` 三条 `source_id → verbatim quote`。
- **版本**：目标组件文件 frontmatter `version` 按 patch level bump（0.1.0 → 0.1.1）。
- **audit**：每条 auto-patch 向 `knowledge/phase25-merge-log.md` append 一行 `{round, candidate_id, target_component, score, user_verdict, timestamp}`。

REJECT / DEFER 候选由 distill-meta 归档到 `excluded_candidates` / `deferred_candidates`，不触发 candidate-merger。

## Output Schema

```json
{
  "target": "steve-jobs-mirror",
  "mode": "multi-round",
  "round_index": 2,
  "max_rounds": 3,
  "status": "OK | NO_GAPS | INSUFFICIENT_CORPUS | MAX_ROUNDS_REACHED",
  "converged": false,
  "prior_round_jaccard": 0.62,
  "coverage_gap_ratio": 0.14,
  "candidates": [
    {
      "candidate_id": "p25-r2-01",
      "identity_hash": "a1b2c3d4e5f6…",
      "suggested_component": "../components/decision-heuristics.md",
      "attribution_vote_needed": false,
      "pattern_description": "在产品 demo 前 48 小时亲走 happy path 并否决任何需要解释的交互。",
      "evidence": [
        {"source_id": "bio-2011-ch21", "quote": "…"},
        {"source_id": "int-2007-d5", "quote": "…"},
        {"source_id": "team-2003-memo", "quote": "…"}
      ],
      "novelty_check": {
        "max_similarity_to_existing": 0.31,
        "flagged_as_duplicate": false
      },
      "possible_novelty_score": 0.82,
      "suggested_verdict": "AUTO"
    }
  ],
  "attribution_votes": [
    {
      "candidate_id": "p25-r2-03",
      "contenders": ["../components/mental-models.md", "../components/decision-heuristics.md"],
      "votes": ["decision-heuristics", "decision-heuristics", "mental-models"],
      "winner": "../components/decision-heuristics.md",
      "tie_break_applied": false
    }
  ],
  "auto_patched": [
    {
      "candidate_id": "p25-r1-04",
      "target_component": "../components/honest-boundaries.md",
      "patched_in_round": 1,
      "component_version_after": "0.1.1",
      "merge_log_line": "r1 p25-r1-04 -> honest-boundaries score=0.81 verdict=AUTO ts=2026-04-14T10:12:33Z"
    }
  ],
  "carry_over_excluded": ["9f8e7d…","3c4b5a…"],
  "notes": [
    "round 2 相比 round 1 Jaccard=0.62，未收敛，等待 user verdict 后进入 round 3。"
  ]
}
```

**写入策略（v2）**：REVIEW 候选仍由用户逐条 ACCEPT / REJECT / DEFER；AUTO 候选在用户最终确认 Phase 2.5 report 后由 candidate-merger 合并。scanner 本身不写任何组件文件。

## Quality Criteria

1. **多轮纪律**：`mode = "multi-round"`；`round_index ∈ [1, max_rounds]`；每轮之间 existing_components 快照必须刷新。
2. **收敛诚实**：`converged = true` 当且仅当 `prior_round_jaccard > jaccard_threshold` 或 `round_index == max_rounds`；不允许 jaccard > 0.8 却 converged = false。
3. **覆盖差集真实**：coverage_gap_ratio 基于实际 source_id / verbatim 匹配。
4. **Carry-over 生效**：round ≥ 2 时，排除集内 hash 对应的候选不得再次出现在 candidates[]。
5. **Novelty 可验**：max_similarity_to_existing 由显式嵌入比较得出。
6. **证据门槛**：每候选 ≥ 3 段 verbatim 引用，source_id 均指向一手语料。
7. **attribution 审计**：每条 `attribution_vote_needed = true` 的候选必须在 attribution_votes[] 有对应 3 票记录；tie_break_applied 字段反映是否触发"小覆盖优先"规则。
8. **auto-patch 闭环**：auto_patched[] 中的 `component_version_after` 必须与目标组件文件当前 frontmatter version 一致；否则说明 merge 未真正落盘，拒收。

## Failure Modes

| 坏提取 | 如何识别 |
|--------|----------|
| False-positive deepening：把 Phase 2 内容换词重报 | novelty_check.max_similarity > 0.7 但仍 flagged false |
| 跨轮复读：复述上一轮 ACCEPT 候选 | identity hash 命中 carry-over_excluded |
| Jaccard > 0.8 但输出 converged = false | 结构性失败，说明 agent 在拖延 early-stop |
| Jaccard ≤ 0.8 但强行 converged = true | 绕过多轮约束；出现在 round 1 尤其可疑 |
| 归属投票被伪造 | attribution_votes[].votes.length ≠ 3 或 winner ∉ contenders |
| auto-patch 未真正写入 | auto_patched 存在但 phase25-merge-log 无对应行 / 目标组件 version 未 bump |
| 二手转述冒充一手证据 | source_id 指向百度百科/知乎（blacklist） |
| 候选簇 < 3 段即输出 | evidence.length < 3 |
| NO_GAPS 被强改 OK 以凑候选 | coverage_gap_ratio < 0.1 但 candidates 非空 |

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

- v2 note：本文件 v0.2.0 恢复了 PRD §3.2 原始的 3 轮意图（v0.1.0 曾出于 DEP-05 / SPEC-02 风险评估收紧到 single-pass）；Jaccard 阈值、身份哈希构造、跨组件投票、auto-patch 条件为本实现补齐（PRD 未细化到这一层）。
