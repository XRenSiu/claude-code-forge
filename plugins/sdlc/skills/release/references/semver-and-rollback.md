# SemVer 推导、回滚最小要素、部署验证清单

## bump 推导（范围 = 上一 tag..merge sha 的提交）

| 命中 | bump |
|---|---|
| 任一 `type!:` 或 body 含 `BREAKING CHANGE:` | major |
| 否则任一 `feat` | minor |
| 否则（fix / perf / refactor / docs / chore …） | patch |

0.x 阶段：major 视为 minor（0.y+1.0），在发布说明注明。

## 回滚方案最小要素

1. 回到哪个版本（tag）或关哪个 flag；
2. 数据：有迁移就写反向迁移或"只读兼容"，没有就写"无迁移"；
3. 谁执行、多久内；
4. 验证回滚成功的命令。

## 部署验证清单（post-deploy）

- 健康检查 / 版本端点返回新版本号；
- 关键路径冒烟（与 done_when 的 mechanical AC 对应的 1–3 条）；
- 错误率 / 延迟在 SLO 内观察窗口（写明多久）；
- 红 → 立即回滚，不"再观察一下"。
