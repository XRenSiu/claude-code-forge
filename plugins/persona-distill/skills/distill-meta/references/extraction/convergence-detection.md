---
extraction_method: convergence-detection
version: 0.1.0
purpose: 定义 Phase 2.5 多轮迭代深化中"候选集是否稳定"的判定方法 —— candidate identity hash 构造、Jaccard 相似度公式、阈值选择（0.8）、边界情况（首轮 / 轮数上限 / 空集）与 2-round worked example。
consumed_by:
  - ../extraction/iterative-deepening.md
  - ../../agents/iterative-deepener.md
borrowed_from: https://github.com/cyber-immortal/cyber-figures
iteration_mode: multi-round
---

## Purpose

Phase 2.5 的多轮深挖需要一个**可计算的停止准则**：何时认为"继续再扫一轮不会再挖出新东西"？本文件定义 `iterative-deepener` agent 在每轮末尾使用的收敛判定方法。核心思路：把每条候选归一化成一个 **identity hash**，用 Jaccard 相似度比较本轮候选集 `Sn` 与上一轮候选集 `Sn-1`；`J > 0.8` 即视为 CONVERGED。

单一数值阈值不是"最优解"，而是在**可观测、可审计、对 LLM 输出的小幅扰动鲁棒**三个约束下的折衷。详见 §Threshold。

## Candidate Identity Hash

候选身份的稳定性决定 Jaccard 是否有意义。候选的自然属性（如 pattern_description 原文）每轮措辞都会略有不同，直接字符串比较会让 Jaccard 总是 0。因此定义：

```
identity_hash = sha1(
    suggested_component || "|" ||
    canonical(pattern_description) || "|" ||
    top2_source_ids_sorted
)
```

各部分含义：

- `suggested_component` — 候选归属的组件相对路径（如 `../components/decision-heuristics.md`）。若候选经 attribution vote 裁定，使用 winner 路径。
- `canonical(pattern_description)` — pattern 描述的归一化形式：小写 → 去除所有标点 → 合并连续空白为单空格 → 去首尾空白。目的：对"同一模式、不同措辞"生成相同 token。
- `top2_source_ids_sorted` — 该候选 evidence 数组中 novelty 分排名前 2 的 source_id，按字典序排序后用 `+` 连接。若候选只有 2 段证据（低于门槛本不应提交，此处按保底处理）取这 2 个；若 3 段取前 2 个。使用 top2 而非全部是为了允许第三段证据在不同轮次有小扰动而不改变 hash。

**注意**：canonical 化**仅用于比对**，不替代输出中的原文 pattern_description（后者保持 LLM 原样，便于 review UI 显示）。

## Jaccard Formula

设 `Sn = { identity_hash | candidate ∈ round_n.candidates }`，
`Sn-1 = { identity_hash | candidate ∈ round_(n-1).candidates }`。

```
J(Sn, Sn-1) = |Sn ∩ Sn-1| / |Sn ∪ Sn-1|
```

当 `|Sn ∪ Sn-1| == 0`（两轮都无候选）→ 视作 CONVERGED（没有新东西可挖，也没有旧东西可对比）。

当 `|Sn-1| == 0 && |Sn| > 0` → J = 0（上一轮为空但本轮有新候选）。典型发生在 round 1 之后的首次有效扫描；此时即使 J = 0 也继续进入下一轮，不判为收敛。

## Threshold

**默认阈值：`0.8`**。

选择依据：

1. **对 LLM 小幅扰动鲁棒**：同一批候选在两次独立运行中因采样随机性会有 10%-15% 的 identity hash 漂移（观察值，来自 nuwa-skill / cyber-figures 相关实验报告 `[UNVERIFIED-FROM-README]`）；阈值设在 0.8 意味着只要"80% 候选稳定重现"即判定收敛，容忍一轮 20% 的扰动但阻止 50% 以上的真新发现被错误停止。
2. **防止提前收敛**：阈值若过低（如 0.5）会在 round 2 就误报收敛；过高（如 0.95）会让几乎不可能自然停止，总是跑满 3 轮反而削弱多轮判定的价值。
3. **可调**：`iterative-deepener` 接受 `{jaccard_threshold}` 参数；默认 0.8，用户可覆盖。

阈值与轮数上限（3）的关系：即使 J 始终 ≤ 0.8，在 round 3 结束后也强制 `converged = true`（status = MAX_ROUNDS_REACHED）——轮数上限本身是一种"人为稳定器"，避免在候选大量漂移的 persona 上无限扫描。

## Edge Cases

| 情况 | 行为 |
|------|------|
| **Round 1（N = 1）** | `prior_round_jaccard = null`；`converged = false`（除非 status = NO_GAPS）。首轮没有可比对象，直接进入 round 2。 |
| **本轮 NO_GAPS**（coverage_gap_ratio < 0.1） | `converged = true` 且 `status = NO_GAPS`；立即停止，不计算 Jaccard。 |
| **两轮都空**（Sn = Sn-1 = ∅） | J 公式分母为 0；按约定 `J = 1.0`，`converged = true`。 |
| **上轮空、本轮非空**（Sn-1 = ∅, Sn ≠ ∅） | J = 0；`converged = false`；进入下一轮。 |
| **上轮非空、本轮空**（Sn-1 ≠ ∅, Sn = ∅） | J = 0；`converged = false`（没有新东西，但也没重复上轮；通常是 carry-over 排除集把候选全清空，表明"没 miss 了"）。**例外**：若同时满足 coverage_gap_ratio < 0.1 → status = NO_GAPS，converged = true。 |
| **Round 3（N = max_rounds）** | 无论 J 值多少，`converged = true` + `status 加 MAX_ROUNDS_REACHED`；不进入 round 4。 |
| **候选全被 attribution vote 改归属** | identity hash 因 suggested_component 变化而全变 → J = 0，converged = false。表明归属层发生重组，值得进入下一轮再稳定化。 |
| **用户把所有候选标 REJECT** | 下一轮 prior_round_candidates = []（REJECT 进 excluded_candidates 但不作为对比集）→ 退化为"首轮重来"；此时若本轮再次产出几乎相同候选 → 说明用户拒绝的是方向本身而非措辞问题，iterative-deepener 应在 notes 中告警"持续产出被拒模式"。 |

## Worked Example

假设 target = `steve-jobs-mirror`，max_rounds = 3，threshold = 0.8。

### Round 1

产出 4 个候选（简化表示为 hash 短码）：

```
S1 = { h_A, h_B, h_C, h_D }
```

prior_round_jaccard = null，converged = false。用户反馈：A / B / D 标 AUTO（合并），C 标 DEFER。

### Round 2

candidate-merger 合并 A / B / D 到各自 target_component；existing_components 更新。
排除集（ACCEPT/AUTO）= { h_A, h_B, h_D }；DEFER 的 h_C 不进排除集。

重新扫描，产出：

```
S2 = { h_C, h_E, h_F }
```

其中 h_C 仍来自之前那个被 DEFER 的簇（用户当时说"下轮再看"），h_E / h_F 是本轮新发现。

Jaccard 计算：

```
S1 ∩ S2 = { h_C }            → |intersection| = 1
S1 ∪ S2 = { h_A, h_B, h_C, h_D, h_E, h_F }  → |union| = 6
J(S2, S1) = 1 / 6 ≈ 0.167
```

0.167 ≤ 0.8 → `converged = false`，进入 round 3。

### Round 3（假设收敛）

用户对 round 2 把 E 标 AUTO、C / F 标 DEFER。排除集 += { h_E }。

Round 3 扫描产出：

```
S3 = { h_C, h_F }
```

（与 round 2 的 DEFER 集一致，没挖出新模式。）

```
S2 ∩ S3 = { h_C, h_F }       → |intersection| = 2
S2 ∪ S3 = { h_C, h_E, h_F }   → |union| = 3
J(S3, S2) = 2 / 3 ≈ 0.667
```

0.667 ≤ 0.8 → 按 Jaccard 本应继续，但 N == max_rounds = 3 → **强制 converged = true**，status = MAX_ROUNDS_REACHED。iterative-deepener 在 notes 中提示："Jaccard 未达 0.8 阈值即触顶 3 轮；建议用户人工审视 DEFER 集决定是否手动发起新一轮 Phase 2.5。"

### 对比：早停场景

若 round 2 产出几乎与 round 1 相同（典型"LLM 原地打转"）：

```
S2 = { h_A', h_B', h_D' }   # 其中 h_A' = h_A（canonical 化后相同），等等
S1 ∩ S2 = { h_A, h_B, h_D } → 3
S1 ∪ S2 = { h_A, h_B, h_C, h_D } → 4   # h_C 只在 S1
J = 3/4 = 0.75
```

0.75 ≤ 0.8 → 仍进 round 3。若 S3 ⊃ S2 的多数候选：

```
S2 ∩ S3 / S2 ∪ S3 = 3/3 = 1.0 > 0.8 → converged = true, status = OK
```

Round 3 早停，流程在这轮结束。

## Relationship to Other Specs

- **`iterative-deepening.md` §Multi-Round Protocol / §Convergence Detection** 引用本文件的 hash 构造与公式定义。
- **`iterative-deepener` agent Quality Gate 2** 依赖本文件对"Jaccard > 0.8 却 converged = false"的判定：任何违反即结构性失败。
- **`candidate-merger` agent** 不直接调用本文件；它的 audit log 提供 Jaccard 计算所需的"哪些候选在哪轮被 ACCEPT"事实。

## Borrowed From

- 来源：[cyber-figures](https://github.com/cyber-immortal/cyber-figures) `[UNVERIFIED-FROM-README]` —— "5 轮蒸馏后才发现 Layer 3" 为本判定方法的原始动机。
- PRD §3.2 Phase 2.5 原始设计（"最多 3 轮迭代 / 每轮产出上轮错过的 X / 用户确认后合并"）未给出具体收敛准则；Jaccard + 身份哈希 + 0.8 阈值 + 3 轮上限为本实现补齐。
