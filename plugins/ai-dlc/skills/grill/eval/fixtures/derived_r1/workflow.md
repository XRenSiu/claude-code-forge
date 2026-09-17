# Workflow — memory-time-search

## Σ · 发生了什么
- 当用户输入相对时间时，`TimeRef` 被解析并与 `Era` 集合求交；重叠 ≥ 2 → ambiguous。（← PSL-003, PSL-005）

## φ · 消歧判据
- 若 ambiguous，则按场景丰富度排序展示候选；对的结果呈现为时期卡。（← PSL-007）

## γ · 约束
- done_when: 空输入被拒绝；重叠时出现消歧提示。
