# sdlc (v0.1.0)

软件开发生命周期的**交付主干**：需求 → issue → 分支 → 判据冻结 → 任务卡 → 按卡实现与提交 → PR →
review 跟进 → 合入归档 → 逃逸缺陷登记。每一步的产物要么能被脚本检，要么被一道只能人签的门挡住。

写法遵循 skillwise 的四原子纪律（Knowledge / Capability / Judgment / Control，不写 Step 1/2/3），
运行时遵循 SKILL.state（状态文件是充分统计量，脚本校验迁移）与 WikiSkill（账本只增不删）。
流程对齐 *Spec Loop v1.2 × done_when Pipeline* 的下半段 L1–L8 + G2/G3 + 横切 X2/X3。

## 六个 skill

| skill | 一句话 | 机械预门 | 调起 |
|---|---|---|---|
| `/sdlc` | 生命周期编排：状态机 + 账本 + 路由表 + 三道人签的门 | `sdlc_state.py` `lint_cards.py` `lock_done_when.py` `metrics.py` | 仅人显式 |
| `/issue` | 需求 / bug / 逃逸缺陷 → 可证伪的 GitHub issue（AC v2 形状、双轨判据、DOS 闭包） | `verify_issue.py` | 模型可 |
| `/commit` | 原子 Conventional Commit；白名单 / G2 锁 / secrets / 调试代码三道闸 | `verify_commit.py` | 模型可 |
| `/pr` | PR body 产物序（范围声明 / Closes / 验证证据 / AC→证据 / 风险回滚）+ 体量分级 XL 必拆 | `verify_pr.py` | 模型可 |
| `/review-loop` | 零 token 阻塞等待、评论当待验证主张、编译态终止绑定；ACCEPT / REJECT / REPLY / ESCALATE / SKIPPED | `pr-poll.sh` | 仅人显式 |
| `/pr-review` | 审查侧：Detective Loop、P0/P1 必带复现、5 条上限、三档归位、发成 GitHub review（永不 approve） | `post_review.py` | 模型可 |

四个隔离子 agent：`review-triager`（只读分诊）、`comment-fixer`（单线程 TDD 修复）、`pr-reviewer`
（只读审查）、`fix-verifier`（全新上下文验证）。

## 安装

```bash
/plugin marketplace add XRenSiu/claude-code-forge
/plugin install sdlc@claude-code-forge
```

前置：`git`、`gh`（已 `gh auth login`）、`jq`、`python3` + `pyyaml`。

## 最短用法

```bash
# 单点
/issue "用户可以按'上个月'这类相对时间搜索记忆"        # → 结构化 issue（先给你看再建）
/commit --issue 42                                     # → 预门 + 自检 + 提交
/pr --issue 42 --done-when specs/x/done_when.yaml      # → 预门 + 确认 + 建 PR
/review-loop 57                                        # → 跟进 PR #57 的评论直到收敛
/pr-review 57 --focus security --post                  # → findings.yaml → GitHub review

# 全流程（显式调起；--autopilot 免逐步确认，但三道门仍要人签）
/sdlc "用户可以按相对时间搜索记忆" --track task
/sdlc --resume memory-time-search
```

## 状态与产物

```
.sdlc/<slug>/state.json     # 充分统计量（脚本拥有；不手改）
.sdlc/<slug>/ledger.md      # 只增不删的账本
.sdlc/pr-watch/pr-<N>.*     # review-loop 的水位线 / 计数器 / 证据日志
cards/CARD-xx.yaml          # L4 任务卡
.done_when.lock             # G2 冻结
specs/<slug>/               # 归档（metrics.py 的数据源）
```

## 与邻居的关系（缺席不阻塞）

- `looper`：`/psl`（PSL 轨建世界）、`/dos-extract`（dos.yaml 给闭包检查）、`/invariant-extract`
- `done-when-pipeline`：`/acceptance-spec`（issue → done_when.yaml）、`/test-suite-generator`、`/acceptance-fleet` + 六审查 skill
- `ratchet` / `forge-teams` / `pdforge`：实现侧

全景与空白清单：[`docs/lifecycle.md`](docs/lifecycle.md)；路由与归因：[`docs/routing.md`](docs/routing.md)；
借鉴与取舍：[`docs/design-notes.md`](docs/design-notes.md)。

## 诚实声明

所有 skill 处于 `static_only`：结构过审、脚本在 fixtures 上冒烟；带/不带 skill 的行为层对比未跑。
静态读不是裁决。各 skill 的 `eval/gate.json` 记录了冒烟结果与 fix_list。
