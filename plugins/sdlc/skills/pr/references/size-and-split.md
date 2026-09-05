# 体量、拆分、draft、base 推断

## 体量分级（diff 行数 = added + deleted，不含 lockfile 与生成文件）

| 级 | 行数 | review 期望 | 处置 |
|---|---|---|---|
| XS | < 50 | < 30 min | 直接建 |
| S | < 200 | < 1 h | 直接建 |
| M | < 500 | < 2 h | 直接建；Reviewer focus 必填 |
| L | < 1000 | 半天 | flag：建议拆；不拆要在 Notes 说为什么 |
| XL | ≥ 1000 | review 质量崩 | **拒**：必拆（`--allow-xl` 只在纯生成 / 迁移 / 重命名类 diff 时用，并说明） |

## 拆分策略（按依赖顺序，不是流程）

1. **先重构后功能**：纯移动 / 重命名 / 抽函数一个 PR（行为不变，测试不动），功能另一个。
2. **按卡**：/sdlc 下每张卡天然是一个可独立 review 的 PR；卡有 `depends_on` 时用 stacked PR。
3. **按目录 / 模块**：上游模块先合，下游后合。
4. **生成文件单独**：lockfile、snapshot、schema 生成物单独一个 `chore:` PR。

## Draft 判据

- 预门 flags 非空（L 体量、untested、锁附提案）→ draft；
- 等 CI 第一次结果 → draft；
- 想先让一个人看方向 → draft + 指定 reviewer；
- 其余 → ready。draft → ready 是 `gh pr ready`。

## base 推断

```
git config --get branch.$(git branch --show-current).merge      # 显式配置
gh repo view --json defaultBranchRef -q .defaultBranchRef.name   # 默认分支
```
两者都没有 / 有 develop 与 main 并存 → 问用户，不猜。

## 与 base 同步

落后 → `git merge origin/<base>`（保留 review 锚点）；**不 rebase 已推送分支**。冲突 → 停，交人。
