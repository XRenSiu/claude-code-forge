<!-- PR body — 段落序是产物序（verify_pr.py 检）。标题另给：type(scope): subject -->

## Summary

<两三句：做了什么、为什么、对用户可见的变化。>

## Scope

- do: <本 PR 覆盖的行为，逐条；与 issue 的 Scope.do 对齐>
- dont: <明确不在本 PR 的（越界类评论对照这里）>

## Linked issue

Closes #<N>            <!-- 或 Refs #<N>（不关闭） -->

## Changes

- `<path or module>` — <一句>
- …

## Verification

```bash
<跑过的命令，逐条；带结果摘要>
npm test            # 128 passed
```

- Red-green: <tests/x.test.ts failed on <base-sha>, passes here | n/a>
- untested — 未找到测试入口 <!-- 若如此 -->

<!-- 否定断言（"某类提交没碰某些目录"）用卡范围的回放仪器，不用会失效的原始 diff：
     ✅ replay_card_commits.sh → card_commits_touching_audited_dirs: 0   （只看卡的提交，分支再长也不变）
     ❌ git diff --stat <首个卡提交>^..HEAD -- <目录>  → 空                （任何非卡提交落在后面就变假，I-79）
     非要写原始 diff：两端都钉死 `<sha>^..<记录时的 sha>` 并注明记录时刻。 -->

## Acceptance mapping

| AC | kind | evidence |
|---|---|---|
| AC-001-a | mechanical | `tests/search/time.test.ts::disambiguates_era_overlap` ✅ |
| AC-001-b | mechanical | `tests/search/time.test.ts::rejects_empty_query` ✅ |
| AC-002-a | human | judge: product · evidence: demo（待 G3） |

## Risk & rollback

- risk: <低/中/高 + 一句为什么>
- blast radius: <影响的模块 / 用户 / 数据>
- rollback: <revert 即可 | 需要迁移回滚：<步骤>>
- feature flag: <name | none>

## Reviewer focus

- <最值得看的一处：file:line — 为什么>
- <第二处>

<!-- --pre-review 时必填：建 PR 前自审 ≤ 2 轮后仍存活的发现；每条带 file:line；没有就写 none。A 档 / P0 不许出现在这里——修掉它 -->
## Known issues

- none

<!-- 可选 -->
## Notes

- size: <XS|S|M|L|XL> · cards: CARD-01, CARD-02 · lock: <ok | changed_with_proposal>
