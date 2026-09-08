# round-diff — <feature> form-draft.md，第 <n-1> 轮 → 第 <n> 轮（逐决策）

> 定向重推要证明的事只有一件：**只有 G1 裁定点对应的决策发生了变化**。这份 diff 就是那个证明。
> 左 = `round<n-1>/form-draft.md`（归档，第三方可重算 sha256），右 = 当前 `form-draft.md`。
> 左侧必须指向归档路径而不是"上一轮"——`verify_derived.py --round <n>` 检这一条。
> 生成方式（可复现）：两版各跑 `grep '^- \[F-' form-draft.md`，再 `diff` 两份输出。

左侧 sha256: `<round<n-1>/form-draft.md 的 sha256>`
F 行数：第 <n-1> 轮 <a>，第 <n> 轮 <b>

变动的 F-id：<[F-05] [F-07] …>

```diff
< - [F-05] <上一轮原文> ← PSL-001
---
> - [F-05] <本轮原文> ← PSL-001
```

## 未落在 diff 里的改动

非决策行（头注、验收挂钩表、PSL 欠定节）的变动不进这份 diff，写进 `divergence.md` 的
「G1 裁决 → 落点」表；dos-proposal.yaml / workflow.md 的同步改动同样在那里逐条对上。
