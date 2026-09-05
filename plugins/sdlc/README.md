# sdlc (v0.2.0)

完整的软件开发生命周期：**上半段建世界**（PSL → 推导产物 → G1 人裁决）、**下半段收敛交付**（issue → 分支 →
判据冻结 → 任务卡 → 按卡实现与提交 → PR → review 跟进 → 合入归档 → 逃逸缺陷登记）、**横切**（DOS 本体与不变量、
回流路由与预算、度量）。每一步的产物要么能被脚本检，要么被一道只能人签的门挡住。

写法遵循 skillwise 的四原子纪律（Knowledge / Capability / Judgment / Control，不写 Step 1/2/3），
运行时遵循 SKILL.state（状态文件是充分统计量，脚本校验迁移）与 WikiSkill（账本只增不删）。
流程对齐 *Spec Loop v1.2 × done_when Pipeline*：U1–U3 / G1、L1–L8 / G2 / G3、X1–X3。

## 二十七个 skill（九环 + 脊柱，见 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)）

### 脊柱与交付主干（本插件原创）

| skill | 一句话 | 机械预门 | 调起 |
|---|---|---|---|
| `/sdlc` | 生命周期编排：状态机 + 账本 + 路由表 + 三道人签的门 | `sdlc_state.py` `lint_cards.py` `lock_done_when.py` `metrics.py` | 仅人显式 |
| `/issue` | 需求 / bug / 逃逸缺陷 → 可证伪的 GitHub issue（AC v2 形状、双轨判据、DOS 闭包） | `verify_issue.py` | 模型可 |
| `/commit` | 原子 Conventional Commit；白名单 / G2 锁 / secrets / 调试代码三道闸 | `verify_commit.py` | 模型可 |
| `/pr` | PR body 产物序（范围声明 / Closes / 验证证据 / AC→证据 / 风险回滚）+ 体量分级 XL 必拆 | `verify_pr.py` | 模型可 |
| `/review-loop` | 零 token 阻塞等待、评论当待验证主张、编译态终止绑定；ACCEPT / REJECT / REPLY / ESCALATE / SKIPPED | `pr-poll.sh` | 仅人显式 |
| `/pr-review` | 审查侧：Detective Loop、P0/P1 必带复现、5 条上限、三档归位、发成 GitHub review（永不 approve） | `post_review.py` | 模型可 |
| `/plan-cards` | L4：契约 → 自包含任务卡；REQ 一卡一主、无写冲突、名词可解析、≤ 40k | `lint_cards.py` | 模型可 |
| `/implement` | L6：按卡实现的隔离契约（实现者只见卡 + AC 子集 + 红基线）；白名单执行器；同指纹升级 | `verify_commit.py` · `sdlc_state.py` | 模型可 |
| `/release` | L8 交付：SemVer 推导、changelog ↔ tag ↔ notes 一致、回滚先于部署、验证绿才完成 | `verify_release.py` | 模型可 |
| `/retro` | X3 学习：基线 → 回流分布 → 提案落层（psl / dos / invariant / ac / routing / skill） | `metrics.py` | 模型可 |

### 上半段 · 建世界（引自 looper；加了 sdlc 接线）

| skill | 一句话 | 机械预门 |
|---|---|---|
| `/psl` | 把一个体验性需求写成完整 PSL（六层 + Open Questions），承重未知不默认填 | `verify_psl.py` |
| `/psl-derive`（新写） | 读完 PSL 先推三样再谈代码：DOS 提案 / Workflow / 形态草案（每条决策 ← PSL-ID）+ N 次推导的分歧集 = G1 议程 | `verify_derived.py` |

### 横切 X1 · 本体与不变量（引自 looper）

| skill | 一句话 | 机械预门 |
|---|---|---|
| `/dos-extract` | 从代码 + 文档反向抽 Design Ontology Spec（12 节 dos.yaml + decisions.md），四个分类判断 | `verify_dos.py` · `inventory.py` |
| `/invariant-extract` | 从失败记忆溯因 + 代码演绎抽一块领地的 □ 常驻不变量卡；硬不变量 propose-only | `verify_card.py` |

### 契约与标准（引自 qanat；加了术语映射 + 接线）

| skill | 一句话 | 机械预门 |
|---|---|---|
| `/donewhen-extract` | 把 issue 的意图收紧成可签的 done_when：形容词→阈值、happy/unhappy 配对、矛盾与覆盖两检 | `verify_done_when.py` |
| `/spec-compile` | 把不变量 / done_when 按可判性下推：fitness fn / eval_case（example + property + metamorphic）/ 评判程序（PAJAMA） | `verify_compile.py` |
| `/calibrate` | 标准的标准：mutation score / agreement α / holdout / 隔离，四不可破全过才允许上线 | `verify_calibration.py` |

### 验收线（引自本仓库 done-when-pipeline v1.1.0 与 ratchet；各加 Wiring 段）

| skill | 一句话 | 机械预门 |
|---|---|---|
| `/acceptance-spec` | 自然语言 → EARS spec.md + done_when.yaml + spec-robustness.md（S2.5 自对抗） | `validate_done_when.py` |
| `/test-suite-generator` | done_when → 五层测试金字塔（existence / unit / integration / e2e / mutation），按卡分批 | `derive_counts.py` · `gen_existence.py` · `check_verbatim_names.py` |
| `/code-reviewer` | 焦点驱动 diff 审查（security / logic / perf / style），Detective Loop，5 条上限 | — |
| `/qa-reviewer` | 真跑测试，maintenance-vs-genuine 分类，go/no-go | — |
| `/pm-reviewer` | Agent-as-Judge 逐条需求合规；human AC 路由到 G3 | — |
| `/spec-drift-detector` | REQ/AC ↔ 代码事实分歧 + git 考古 | — |
| `/spec-gaming-detector` | 假设作者在作弊：6 种 RHD 模式；硬命中 = A 档 | `compute_score.py` |
| `/meta-judge` | 只综合不重审：去重 / 加权 / 仲裁 / 分类 → 单一 verdict | `compute_confidence.py` |
| `/acceptance-fleet` | 并行派发六审查 skill → meta-judge → 四态棘轮 DONE / FIX / SPEC_DRIFT / GAMING_RISK | — |
| `/ratchet` | 跑到达标为止：master 只评估、worker 只执行、卡住换人；用于需要迭代收敛的卡 | — |

五个隔离子 agent：`card-implementer`（单卡实现）、`review-triager`（只读分诊）、`comment-fixer`（单线程 TDD 修复）、`pr-reviewer`
（只读审查）、`fix-verifier`（全新上下文验证）。

> 与 `looper` / `done-when-pipeline` / `ratchet` 同时启用时 `/psl` 等同名，用命名空间 `/sdlc:<name>` 区分；源插件仍是上游，sdlc 内的副本带接线段。

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

# PSL 轨（体验性需求）：先建世界，G1 人签后才进 issue
/psl "用户可以按'上个月'这类相对时间搜索记忆"        # → PSL-memory-time-search.md
/psl-derive PSL-memory-time-search.md --n 3            # → derived/{dos-proposal,workflow,form-draft,divergence}
/donewhen-extract "#42"                                # → done_when 卡（G2 前的草案）；或 /acceptance-spec
/test-suite-generator specs/x/ && /spec-compile done_when.yaml && /calibrate <eval_case set>
/acceptance-fleet specs/x/                              # → 六审查 skill → meta-judge → DONE / FIX / SPEC_DRIFT / GAMING_RISK

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

- `forge-teams` / `pdforge`：实现侧的并行 / TDD 执行器（L6），有则用
- `looper`、`done-when-pipeline`、`ratchet`：本插件内含它们这条线上 skill 的副本；源插件仍是上游

架构 / 运转 / 使用：[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)；全景与空白清单：[`docs/lifecycle.md`](docs/lifecycle.md)；路由与归因：[`docs/routing.md`](docs/routing.md)；
借鉴与取舍：[`docs/design-notes.md`](docs/design-notes.md)。

## 诚实声明

所有 27 个 skill 处于 `static_only`：结构过审、22 个脚本在 fixtures 上冒烟（`bash plugins/sdlc/eval/smoke.sh`）；带/不带 skill 的行为层对比未跑。
静态读不是裁决。各 skill 的 `eval/gate.json` 记录了冒烟结果与 fix_list。
