# 提交约定（Conventional Commits + 本流水线的三条补充）

## type

| type | 用途 | 会不会出现在 changelog |
|---|---|---|
| feat | 新行为 | 是 |
| fix | 修 bug | 是 |
| perf | 性能 | 是 |
| refactor | 不改行为的重构 | 否 |
| test | 只动测试 | 否 |
| docs / style / chore / ci / build | 文档 / 格式 / 维护 / CI / 构建 | 否 |
| revert | 回滚，subject 写 `revert: <原 subject>`，body 写 `This reverts commit <sha>` | 是 |
| wip | 仅非 main 分支的安全点；合入前 squash 掉 | 否 |

`type!:` 或 footer `BREAKING CHANGE:` 表示不兼容变更，body 必须写迁移方式。

## scope

模块 / 包 / 目录名，小写，`a-z0-9-./`。monorepo 用包名；跨包用 `*` 不如拆成两次提交。

## 三条补充

1. **卡即关注点**：在 /ai-dlc 下一个 commit 只属于一张卡（footer `Card: CARD-xx`）。
2. **锁文件改动必须带提案**：`done_when.yaml` / `contract.yaml` / `tests/**`（写完锁后）出现在 diff
   → 同一 diff 必须含 `change-proposal-*.md`，消息 type 用 `chore(contract):` 或 `test:` 并在 body 引用提案。
3. **红-绿证据（TDD 模式）**：
   - 先提测试 commit：`test(scope): add failing test for AC-001-a`，body 写
     `Red: fails on <base-sha> — <一行失败输出>`。
   - 再提实现 commit：`feat(scope): …`，body 写 `Green: tests/<x> passes`。
   - 本插件没有红-绿脚本（登记为空白）；手工做法：`git stash` 实现 → 跑测试确认红 → `git stash pop`。

## 分支命名

`<type>/<issue>-<slug>`：`feat/42-memory-time-search`、`fix/57-null-user`。小写、连字符、≤ 50 字符。

## 不该进仓库的东西

`.env*`（除 `.env.example`）、`*.pem`、`id_rsa*`、`*.key`、`node_modules/`、`dist/`、`build/`、`__pycache__/`、
`.DS_Store`、大二进制（> 5MB 用 LFS 或别提）。

## 自检入口推断

| 存在 | 跑 |
|---|---|
| package.json scripts.test / lint / typecheck | `npm run test` / `lint` / `typecheck`（或 pnpm / yarn） |
| Makefile `test` | `make test` |
| pyproject.toml / pytest.ini | `pytest -q` |
| Cargo.toml | `cargo test` |
| go.mod | `go test ./...` |
| 都没有 | 照常提交，body 注明 `untested — 未找到测试入口` |
