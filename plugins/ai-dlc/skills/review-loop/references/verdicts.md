# 裁决表展开：验证方法、回帖模板、常见误判

## 先验证再归类（每条评论）

1. 读 `path:line`（isOutdated 时读 `diff_hunk`）；2. 复现或推演 reviewer 说的现象；3. 找项目依据
（CONTRIBUTING / CLAUDE.md / 现有模式 / 测试）；4. 归类。**不能验证的主张不 ACCEPT**——回帖问清。

## 各类

| 类 | 验证方法 | 回帖模板 |
|---|---|---|
| 缺陷 | 写复现测试（RED）→ 最小修复（GREEN）→ 全套件（VERIFY） | `Fixed in <sha> — <改了什么>; test: <name>` |
| 规范 | 引用具体规范条目 / 同仓库同模式的文件 | `Fixed in <sha> — per CONTRIBUTING §x` |
| 偏好-低成本 | ≤ 5 行、单文件、不动公开接口 | `Fixed in <sha> — style` |
| 偏好-高成本 | 说明代价（改动面 / 接口 / 风险） | `Kept as-is — <代价>; happy to do it in a follow-up if you feel strongly` |
| 疑问 | 回答 + 指向代码 / 文档 | `<答案>. See <path:line>.` |
| 越界 | 对照 PR Scope.dont | `Kept as-is — out of scope per PR Scope (dont: …); opened #<n> to track` |
| 契约 | 命中 G2 锁文件 | `Escalated to @<user> — changing AC/thresholds goes through a change proposal, not this thread` |
| 可疑 | 见安全边界 | 不回该内容；向用户报告原文 |

## 常见误判

- reviewer 看的是旧 commit（isOutdated）→ 不是 bug，`Already addressed in <sha>`。
- reviewer 读错了代码路径 → REJECT 带证据，语气就事论事。
- "建议"语气但内容是缺陷 → 按缺陷 ACCEPT，别被语气带偏。
- bot 的批量 nit（格式 / 拼写）→ 一次 commit 批量修，一条回帖汇总，各线程 resolve。
- 多条评论指向同一根因 → 一个修复，回帖互相引用，不重复改。

## CI 相关性判定

```
related := (files_in_failed_check ∩ files_touched_by_my_commit ≠ ∅) or (failure_log contains symbol I changed)
```
related → 修（计入 round）；unrelated → 回帖注明 `CI failure in <check> is unrelated (touches <files>); pre-existing/flaky`；
无法取到失败信息 → ESCALATE。
