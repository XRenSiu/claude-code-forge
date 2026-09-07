# sdlc (v0.12.0)

完整的软件开发生命周期，分三段。上半段建世界：PSL → 推导产物 → G1 人裁决。
下半段收敛交付：issue → 分支 → 判据冻结 → 任务卡 → 按卡实现与提交 → PR → review 跟进 → 合入归档 → 逃逸缺陷登记。
横切三条：DOS 本体与不变量、回流路由与预算、度量。
每一步的产物要么能被脚本检，要么被一道只能人签的门挡住。没有第三种。

写法遵循 skillwise 的四原子纪律：Knowledge、Capability、Judgment、Control，不写 Step 1/2/3。
运行时遵循 SKILL.state（状态文件是充分统计量，脚本校验迁移）与 WikiSkill（账本只增不删）。
流程对齐 *Spec Loop v1.2 × done_when Pipeline*：U1–U3 / G1、L1–L8 / G2 / G3、X1–X3。

## 二十八个 skill（九环 + 脊柱，见 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)）

> v0.6.0：按 loop engineering / graph engineering 的透镜重看（[`docs/proposals/loop-graph-engineering.md`](docs/proposals/loop-graph-engineering.md)）。图（`graph.yaml`）与六个环（`loops.yaml`）成为数据并被 lint；每个环绑到 `/goal` `/loop` Stop hook `/schedule`（`triggers.yaml`）；收敛检测加 oscillation / plateau / impossible（routing v2）；账本有了类型边伴生 `trace.jsonl`；`/pr --pre-review`；新 skill `/tune` 闭合 hill-climbing 环。

### 脊柱与交付主干（本插件原创）

| skill | 一句话 | 机械预门 | 调起 |
|---|---|---|---|
| `/sdlc` | 生命周期编排：状态机 + 账本（+ trace.jsonl）+ 路由表 v2（收敛检测）+ 三道人签的门 + 图 / 环 / 触发声明 | `sdlc_state.py`（graph · loops · check-clean · report）`verify_graph.py` `verify_loop.py` `trace.py` `lock_done_when.py` | 仅人显式 |
| `/issue` | 需求 / bug / 逃逸缺陷 → 可证伪的 GitHub issue（AC v2 形状、双轨判据、DOS 闭包） | `verify_issue.py` | 模型可 |
| `/commit` | 原子 Conventional Commit；白名单 / G2 锁 / secrets / 调试代码三道闸 | `verify_commit.py` | 模型可 |
| `/pr` | PR body 产物序（范围声明 / Closes / 验证证据 / AC→证据 / 风险回滚）+ 体量分级 XL 必拆 + `--pre-review`（≤ 2 轮隔离自审，存活写 Known issues） | `verify_pr.py` | 模型可 |
| `/review-loop` | 零 token 阻塞等待（或 `/loop` `/goal` `/schedule` 触发）、评论当待验证主张、编译态终止绑定、早停与 sycophancy 代理；ACCEPT / REJECT / REPLY / ESCALATE / SKIPPED | `pr-poll.sh` | 仅人显式 |
| `/pr-review` | 审查侧：Detective Loop、P0/P1 必带复现、5 条上限、三档归位、发成 GitHub review（永不 approve） | `post_review.py` | 模型可 |
| `/plan-cards` | L4：契约 → 自包含任务卡；REQ 一卡一主、无写冲突、名词可解析、≤ 40k | `lint_cards.py` | 模型可 |
| `/implement` | L6：按卡实现的隔离契约（实现者只见卡 + AC 子集 + 红基线）；白名单执行器；同指纹升级 | `verify_commit.py` · `sdlc_state.py` | 模型可 |
| `/release` | L8 交付：SemVer 推导、changelog ↔ tag ↔ notes 一致、回滚先于部署、验证绿才完成 | `verify_release.py` | 模型可 |
| `/retro` | X3 学习：基线 → 回流分布 + 逃逸缺陷因果链 + 契约返工率 → 提案落层（psl / dos / invariant / ac / routing / skill） | `metrics.py` | 模型可 |
| `/tune`（新） | X3 harness 闭环：六个环的 trace → 环参数提案（routing 预算 / 指纹阈值 / MAX_ROUNDS / 隔离等级 / fix_list，封闭集）→ diff / patch → 人开 PR；样本 < 2 只记基线 | `tune.py` `apply_proposal.py`（只出 diff） | 模型可 |

> v0.12.0：按 AWS AI-DLC 2.0 的一手研究对照补五条缺口（[`docs/reports/aidlc-gap-2026-09-07.md`](docs/reports/aidlc-gap-2026-09-07.md)）。
> **广度成为网格**（`sizing.yaml` v2 的 `stages:` + `never_skippable`，`verify_sizing.py` 七条 lint 让它与
> `sdlc_state.py` 的 ORDER / prereqs 互相断言——原来 S 档声明豁免两项、代码只实现一项，且无人发现）；
> 深度与测试量成为另外两个正交旋钮（测试量是下界，`derive_counts.py --strategy` 检，exit 4）；
> 早定档 + 飞行中重定档（`size --from-issue --early`，结构上够不到 S；已走过的阶段冻结）；
> **解释日记** `notes.md` 四格 + 门禁逐字仪式 + 晋升下轮生效（Open questions 不晋升，没有 org 通道）；
> 自治阶梯 `autonomy`（只问一次、跨会话、不代签门）与跳过的依赖警告；`plan` / `doctor`；
> reviewer 截断契约（`verify_review_complete.py`，把不变量 14 从脚本扩到 agent）；
> 跨制品术语 sensor（`verify_vocabulary.py`，B 档）。

> v0.10.0 实现了 `docs/reports/raising-the-floor-2026-09-05` 的五条缺口：A 档加结构闸
> （`constraints.structure` + `verify_structure.py`，声明了但没法求值 = exit 3，不是通过）；`dos-extract` 产
> `agent-map.md`（`--probe` 逐条真跑命令，陷阱必须有来路），`plan-cards` 按卡切片进 `card_context.md`；
> `donewhen-extract` 的 `divergence.py` 用 N 份隔离草案给 TASK 轨一个不靠自评的模糊度信号；
> `sizing.yaml` + `sdlc_state.py size` 按体量分档，缺省不给豁免；`eval/effect/` 是这个插件一直缺的行为层对照。

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

# 三个旋钮与两条新通道（v0.12），单点也能用
python3 skills/sdlc/scripts/sdlc_state.py plan                                 # 这次跑几个阶段、几道门、跳了什么
python3 skills/sdlc/scripts/sdlc_state.py doctor                               # 装置健康度（建议性，从不阻断）
python3 skills/sdlc/scripts/verify_sizing.py                                   # 体量网格与代码互相断言
python3 skills/sdlc/scripts/sdlc_state.py note --kind interpretation --text …  # 含糊处当场做了什么选择
python3 skills/sdlc/scripts/sdlc_state.py notes --for-gate g2                  # 门禁仪式：逐字念，不筛选
python3 skills/dos-extract/scripts/verify_vocabulary.py --dos dos.yaml …       # 跨制品术语漂移（B 档）
python3 skills/acceptance-fleet/scripts/verify_review_complete.py …            # 审查没跑完 ≠ 没发现问题

# 五处新配件（v0.10–0.11），单点也能用
python3 skills/sdlc/scripts/sdlc_state.py size --base origin/main --commit    # 体量分档（缺省 M，S 要证据换）
python3 skills/qa-reviewer/scripts/verify_structure.py --done-when done_when.yaml --base origin/main
python3 skills/donewhen-extract/scripts/divergence.py d1.yaml d2.yaml d3.yaml  # N 份草案的分歧 = 要澄清的槽
python3 skills/dos-extract/scripts/verify_agent_map.py agent-map.md --probe    # 仓库地图，命令逐条真跑
python3 skills/acceptance-fleet/scripts/pick_evaluators.py                      # 跨供应商分配 + 同源留痕
```

## 状态与产物

```
.sdlc/<slug>/state.json     # 充分统计量（脚本拥有；不手改）
.sdlc/<slug>/ledger.md      # 只增不删的账本（记已经发生的错）
.sdlc/<slug>/notes.md       # 解释日记四格（记含糊处当场做了什么选择）——只增不删
.sdlc/learnings/project.md  # 晋升后的项目规则；下一次 init 才编译进去（本轮不生效）
.sdlc/pr-watch/pr-<N>.*     # review-loop 的水位线 / 计数器 / 证据日志
cards/CARD-xx.yaml          # L4 任务卡
.done_when.lock             # G2 冻结
specs/<slug>/               # 归档（metrics.py 的数据源）
```

`.sdlc/` 是**运行时状态，不入库**。把它加进仓库的 `.gitignore`。真正要留下的是 `specs/<slug>/`：
`sdlc_state.py archive` 在收尾时把状态、账本、trace 与契约一起复制过去，retro 的 `metrics.py` 只读那里。
两者搞混的后果是：要么把每一次门的中间态提交进历史，要么归档为空、下一次 retro 没有基线可比（dogfood I-01）。

## 与邻居的关系（缺席不阻塞）

- `forge-teams` / `pdforge`：实现侧的并行 / TDD 执行器（L6），有则用
- `looper`、`done-when-pipeline`、`ratchet`：本插件内含它们这条线上 skill 的副本；源插件仍是上游

## 文档

| 想知道什么 | 看哪份 |
|---|---|
| 这东西是什么、怎么运转、怎么用 | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| **手上这件事有没有现成脚本，它检什么、退出码什么意思** | [`docs/reference.md`](docs/reference.md)（全部脚本与资产的索引，冒烟盯着不许漏） |
| **这个插件自己被验到什么程度，哪些话还不能说** | [`docs/evaluation.md`](docs/evaluation.md) |
| 每个环节由谁承载、哪些还空着 | [`docs/lifecycle.md`](docs/lifecycle.md) |
| 失败往哪回、预算怎么算 | [`docs/routing.md`](docs/routing.md) |
| 为什么这样设计、什么有意不做 | [`docs/design-notes.md`](docs/design-notes.md) |
| 为什么不同人用同一个 agent 质量差那么多 | [`docs/reports/raising-the-floor-2026-09-05.md`](docs/reports/raising-the-floor-2026-09-05.md) |
| 行为层对照怎么跑、读数是多少 | [`eval/effect/README.md`](eval/effect/README.md) |

## 诚实声明

所有 28 个 skill 处于 `static_only`：结构过审、脚本在 fixtures 上冒烟（`bash plugins/sdlc/eval/smoke.sh`）。
**行为层对比不再是零**：`eval/effect/` 是带 / 不带 skill 的对照题库与跑分器，已在 1 个任务 × 3 个 arm 上真跑过一轮（`eval/effect/baseline.md`）。那一轮的主要产物是**题目自己的 bug**，不是 arm 的排名。`score.py` 在样本 < 5 个任务时一律回 `insufficient_sample`，不许拿它宣称插件有效。
v0.6.0 的收敛阈值（指纹历史 6、震荡周期 2–3、plateau 3 轮、sycophancy 0.95）与 tune 的 40% / 50% 规则是文献先验，未在真实运行上校准。
静态读不是裁决。各 skill 的 `eval/gate.json` 记录了冒烟结果与 fix_list。
