# round-diff — memory-time-search form-draft.md，第一轮 → 第二轮（逐 F 行）

> 机械证明：只有 G1 裁定点对应的 F 行发生变化。左 = `round1/form-draft.md` 的 F 行，右 = 本轮。
> 生成方式：两版各跑 `grep '^- \[F-' form-draft.md` 后 `diff`。

变动的 F-id：[F-20]

```diff
< - [F-20] 重叠 ≥ 2 时展示候选，不自动选 ← PSL-003
---
> - [F-20] 重叠 ≥ 2 时展示候选，不自动选；阈值常量 2（G1 裁 D-1） ← PSL-003, UI-2
```
