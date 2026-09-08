# 变更提案 — change-proposal-<NNN>.md

> G2 之后改被锁文件（done_when.yaml / contract.yaml / tests/**）的唯一合法路径：同一 diff 附带本文件。
> 没有它，锁定检查（A 档）直接拒绝。有它，放行并计入 task_reflows（X2 的"任务级回流"由此可数）。

**日期**: <YYYY-MM-DD>　**提案人**: <name>　**签字人**: <name>

## 改哪条

| 文件 | AC / REQ | 改前 | 改后 |
|---|---|---|---|

## 为什么

<证据：反例 / 反馈 / 无法实现的契约>

## 归因层

- [ ] task（判据写错 / 写漏）
- [ ] ontology（DOS 不变量冲突）
- [ ] world（PSL 规律冲突 → 应重开 G1，而不是只改 AC）

## 重新冻结

- 新 `.done_when.lock` sha256: `<hash>`　签字: <name>
