# gh 命令速查（review-loop 专用）

## PR 基本操作

```bash
gh pr view <N> --json state,reviewDecision,url   # 状态快照
gh pr view --json number -q .number              # 当前分支的 PR 号
gh pr diff <N>                                    # 当前完整 diff
gh pr view <N> --json commits -q '.commits[-1].oid'  # 最新 commit SHA
gh pr view <N> --json body -q .body               # 读范围声明（Scope 段）
```

## 回帖

```bash
# 回复到行内评论线程（保持上下文，优先用这个）
gh api "repos/{owner}/{repo}/pulls/<N>/comments/<comment_id>/replies" \
  -f body='Fixed in a1b2c3d — 补上了空数组的早退分支'

# PR 级评论（回应 review 总评或 issue comment）
gh pr comment <N> --body '...'
```

`{owner}/{repo}` 占位符 gh 会自动填充，前提是在仓库目录内。回复行内线程用**线程首条评论的 id**
（顶层评论 id），不是后续回复的 id。

## 线程状态（仅 GraphQL 可查）

```bash
bash scripts/pr-poll.sh threads <N>
# threads[].{id,isResolved,isOutdated,path,line,opened_by,first_comment,reply_count}
```

`isOutdated: true` 表示该评论锚定的代码行已被后续 commit 改动——验证时对照评论里的 diff_hunk。

## 收束线程

```bash
bash scripts/pr-poll.sh resolve <N> <thread_id>   # thread_id = threads 输出里的 .threads[].id（PRRT_…）
# exit 0 = 已收束；exit 22 = 失败但非致命（无写权限 / 线程已删）
```

- thread id 是 GraphQL node id，**不是**评论的数字 id——回帖用数字 id，收束用 node id。
- fork 来的 PR 上作者往往没有写权限，收束会失败（exit 22），留给 reviewer 收。
- 反向 `unresolveReviewThread` 存在，但本 skill **不使用**——取消他人的收束是人类动作。

## CI 检查

```bash
gh pr checks <N>                 # 一次性查看
gh pr checks <N> --watch         # 阻塞等待全部检查结束（注意 bash 超时）
gh run view <run-id> --log-failed | head -200   # 取失败日志判相关性
```

## 常见坑

- `gh api ... --paginate` 必须加，评论超过 30 条时不加会静默丢数据。
- review 的时间字段是 `submitted_at`，评论是 `created_at`。
- `state: PENDING` 的 review 是草稿，必须忽略。
- 编辑过的评论 `created_at` 不变——按创建时间做水位线，评论被编辑不会重新触发。
