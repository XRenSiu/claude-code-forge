# Release vX.Y.Z — <feature or theme>

merge: <sha> · date: YYYY-MM-DD · issues: #<n>, #<m> · PRs: #<p>

## Changes

- feat(scope): <一句>（#PR）
- fix(scope): <一句>（#PR）

## Verification

- pre-deploy: `<cmd>` → <结果>
- post-deploy: `<verify-cmd>` → <结果 / 时间>
- acceptance: specs/<slug>/ratchet-log/iteration-NNN/final-state.json → DONE

## Rollback

- how: `<revert / redeploy previous tag vX.Y.(Z-1) / feature flag off>`
- data: <有无迁移；回滚迁移步骤或"无迁移">
- owner: <name>

## Escape

发现问题？`/issue --escape` 并引用 `vX.Y.Z` 与 merge sha；归因层与"为什么门没拦住"写进 Attribution。
