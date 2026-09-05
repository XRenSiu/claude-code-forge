# PSL — memory-time-search

## Vision

- PSL-001 [Σ] 记忆产品里，时间不是时间戳，是"有场景的时期"（era）。根命题：用户回忆靠场景锚定，不靠日历。
  推出的形态决策：搜索结果不是日期列表。推出的数据决策：`Era` 是一等实体。

## Mental Model

- PSL-002 [Σ] 用户说"上个月"时想的是"那段日子发生了什么"，不是 30 天的区间。
  推出的形态决策：结果卡要带场景摘要。
- PSL-003 [Σ] 相对时间天然含糊；用户接受被反问一次，不接受被猜错。
  推出的形态决策：重叠时出消歧提示。

## Domain Model

- `Memory`：一次被捕获的瞬间（文本 / 图 / 位置）。
- `Era`：一段有场景的时期，聚合多条 `Memory`，有 `label`、`span`、`scenes`。
- `TimeRef`：用户输入的相对时间表达，带 `ambiguity` 属性。
- 关系：`Era` CONTAINS `Memory`（1:N）；`TimeRef` RESOLVES_TO `Era`（1:N，可多）。
- PSL-004 [Σ] 推翻的朴素表：`memories(created_at)` 加日历筛选器。这里 `Era` 不是 `created_at` 的区间，它由场景定义。

## State Machine

- `TimeRef`: entered → resolved(single) | ambiguous(≥2 eras) → chosen。
- PSL-005 [Σ] ambiguous 是合法终态之一，不是错误。

## Workflow

- [Σ] 用户输入相对时间时，世界里 `TimeRef` 被解析，与 `Era` 集合求交；重叠 ≥ 2 时进入 ambiguous。
- [φ] 消歧判据：候选 `Era` 按场景丰富度排序，展示候选而不是猜；对的结果呈现为"时期卡"，不是日期行。
- PSL-006 [φ] 空输入不解析，直接拒绝。
- PSL-007 [φ] 时期卡必须带场景摘要与代表性 `Memory`。

## Acceptance

- 问"上个月"（fixture: era-overlap）→ 返回消歧提示，候选 ≥ 2。
- 问 ""（空）→ 返回 400 empty_query。
- 问"住在柏林的时候"→ 返回一张时期卡，含场景摘要。

## Open Questions

- [γ→人] PSL-008 重叠阈值是 2 还是 3？（承重：决定何时消歧）
