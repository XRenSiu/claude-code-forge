---
name: release
description: >-
  补引擎自己给不出的缺口：合入之后到"交付完成"之间的产物序与不可逆动作的门——版本号按 SemVer 从
  Conventional Commits 推导、CHANGELOG 条目与 tag 一致、发布说明必须带回滚方案与验证清单、部署后
  验证先于宣布完成、逃逸缺陷登记入口在发布说明里可达——由 verify_release.py 检产物。效果：merge sha 进，
  tag + changelog + release notes + 部署验证记录出。Use when: "发版" / "打 tag" / "写 changelog" /
  "部署" / "release" / "ship it" / 合入之后。NOT for: 建 PR（/pr）、合并（人类动作）、登记线上缺陷
  （/issue --escape，本 skill 只放入口）。前置：merge 已完成，在目标仓库内。
argument-hint: "[--version X.Y.Z | --bump auto|patch|minor|major] [--base <prev tag>] [--deploy-cmd '<cmd>'] [--verify-cmd '<cmd>'] [--dry-run]"
version: 0.1.0
user-invocable: true
---

# release — 合入不是终点，交付才是

产物：`CHANGELOG.md` 新条目、git tag `vX.Y.Z`、`releases/vX.Y.Z.md`（发布说明：变更 / 验证 / 回滚 / 逃逸缺陷入口）、
部署后验证记录。本文件写：发布在流水线里是什么、什么算交付完成、原语与出口、不可逆动作前的门。
用什么部署系统是你的份额（或仓库的事）。

## 缺口（Judgment + Control + Capability）

deletion 测试：撤掉本 skill，引擎在合入后说"完成"就停；没有版本、没有 changelog、部署了没验、出问题不知道
怎么回滚、线上反馈无处登记——世界层只在 G1 一处校准。缺的是产物序判据、不可逆动作（tag / push tag /
deploy）前的确认门、和把机械半边编译掉的验证器。

## 世界（Σ）

- **版本从提交推导**（Conventional Commits）：范围内有 `feat!`/`BREAKING CHANGE` → major；有 `feat` → minor；
  只有 `fix`/`perf`/其他 → patch。`--bump auto` 就是这个规则；人可覆盖但要在发布说明写为什么。
- **tag 与 changelog 是同一事实的两个投影**：`CHANGELOG.md` 的 `## [X.Y.Z] - YYYY-MM-DD` 与 tag `vX.Y.Z` 必须一致。
- **不可逆序（Σ 第 2 格）**：push tag、deploy 到生产、删旧版本——这些之前必须有回滚方案与确认。
- **部署后验证先于宣布完成**：`--verify-cmd`（健康检查 / 冒烟）绿了才是 `release.done=true`；红了 → 回滚方案生效。
- **逃逸缺陷登记入口**：发布说明末尾固定一段"发现问题？`/issue --escape` 并引用本版本"——线上反馈是世界层唯一的
  外部校准源（参考文档 L8）。
- **关于用户的 Σ**："发一下"= 全套（tag + changelog + notes + verify）；"只打 tag"= 仍要 changelog 条目一致；
  "先不部署"= `release.skipped_reason` 留痕，不算交付完成。

## 判据（φ）

- `verify_release.py --version X.Y.Z`：CHANGELOG 含该版本条目且日期合法；tag 存在（或 `--pre-tag` 模式下待打）且指向
  merge sha；`releases/vX.Y.Z.md` 含 Changes / Verification / Rollback / Escape 四段且 Rollback 非空；版本 ≥ 上一 tag；
  bump 与提交类型一致（`--bump auto` 时）。
- 部署验证：`--verify-cmd` exit 0（或注明 `unverified: <原因>`，此时 `release.done` 不能为 true）。
- 残差：回滚方案是否真的可执行（人判）。

## 原语（Π）

- `scripts/verify_release.py --version X.Y.Z [--changelog CHANGELOG.md] [--notes releases/vX.Y.Z.md] [--base <prev tag>] [--bump auto] [--pre-tag]`
  —— exit 0 / 1 / 2。**打 tag 前必须跑**（`--pre-tag`），**宣布完成前再跑一次**（不带 `--pre-tag`）。
- `assets/release_notes_template.md` · `assets/changelog_entry_template.md`。
- `references/semver-and-rollback.md` —— bump 规则、回滚方案的最小要素、部署验证清单。
- `git tag -a vX.Y.Z -m …`、`git push origin vX.Y.Z`、`gh release create`（存在性声明）。

## 门（γ）

- **打 tag / push tag / deploy 前给人看**：展示版本、changelog 条目、发布说明、将执行的命令；确认再做。`--dry-run` 只产文件不打 tag 不部署。
- **done_when**：`verify_release.py` exit 0 ∧ verify-cmd 绿 ∧ `sdlc_state.py set release.version=… release.tag=… release.done=true`。
- 在 `/sdlc` 里：`advance archive` 要求 `release.done=true` 或 `release.skipped_reason`。

## 失败机制

- changelog 条目与 tag 不一致 → 拒，改一处对齐，不打第二个 tag。
- 部署验证红 → 执行回滚方案（发布说明里的），`release.done=false`，`/issue --escape` 登记，账本记 `release_rollback`。
- 没有部署系统 / 库项目 → `--deploy-cmd` 省略，交付 = tag + changelog + notes；verify-cmd 可为 `npm pack --dry-run` 之类。
- 已存在同名 tag → 停，交人（不覆盖 tag）。

## 高危黑名单（不可豁免）

- 绝不无确认 push tag / deploy 到生产；绝不删除或移动已推送的 tag。
- 绝不在验证红时宣布完成；绝不没有回滚方案就部署。
- 绝不手改版本号而不更新 changelog。

## 接线

上游：`/sdlc` merge 阶段（`merge.sha`）。下游：`sdlc_state.py advance archive`；`/issue --escape`（逃逸缺陷）；`/retro`（读发布记录）。

## 本 skill 自身的出口门

`eval/gate.json`：`static_only`——`verify_release.py` 在临时仓库 fixtures 上冒烟（一致的 changelog+tag+notes 过；缺 Rollback / 版本不一致 / bump 不符 各被拒）。行为层未跑。
