# sdlc 架构：是什么、如何运转、如何使用

> 一句话：**sdlc 是一条产研自闭环的流水线——世界 → 契约 → 标准 → 计划 → 实现 → 验收 → 交付 → 学习，每一步的产物要么被脚本检，
> 要么被一道只能人签的门挡住；失败按层回流而不是原地重试；账本只增不删，逃逸缺陷回到世界层校准。**
> 它对齐 *Spec Loop v1.2 × done_when Pipeline* 的全部环节（U1–U3/G1、L1–L8/G2/G3、X1–X3），写法遵循 skillwise 四原子，
> 运行时遵循 SKILL.state（状态文件是充分统计量）与 WikiSkill（账本非对称回滚）。

---

## 1. 九环与一根脊柱

> v0.6.0 起这张图是**数据**：`skills/sdlc/assets/graph.yaml`（52 节点 · 67 边：阶段 / skill / agent / 人；sequential · conditional ·
> fan_out · fan_in · loop_back · interrupt · handoff）。`python3 skills/sdlc/scripts/sdlc_state.py graph render` 生成 mermaid；
> `graph check` 让它与状态机的 ORDER 互相断言；`verify_graph.py` 检五条性质（见 §3.7）。下面的 ASCII 是给人读的摘要。

```
                       ┌──────────────────────── 脊柱 /sdlc ────────────────────────┐
                       │  state.json（脚本校验迁移） · ledger.md（只增） · routing.yaml（分层预算 · 指纹终止）  │
                       │  G1 世界裁决 · G2 判据冻结 · G3 例外复核（只能人签）                                   │
                       └────────────────────────────────────────────────────────────┘
 R0 世界        /psl ──▶ /psl-derive ──▶ [G1 人] ─────────────────────────────┐   PSL 轨才走；TASK 轨从 R2 起
 R1 本体        /dos-extract（现状） · /invariant-extract（□） · dos-proposal（应然，来自 R0）  ── 横切：词表闭包
 R2 契约        /issue ──▶ /donewhen-extract | /acceptance-spec(+convert) ──▶ done_when.yaml v2 ──▶ [G2 人] 锁
 R3 标准        /test-suite-generator（按卡分批） · /spec-compile（可判性阶梯） ──▶ /calibrate（标准的标准）── L5 二次锁
 R4 计划        /plan-cards ──▶ cards/CARD-xx.yaml（lint 三项 + 40k）
 R5 实现        /implement（隔离实现者 · 白名单执行器）· /commit · /ratchet（跑到达标为止的卡）
 R6 验收        /acceptance-fleet ──▶ 六审查 skill ──▶ /meta-judge ──▶ 四态棘轮 ──▶ [G3 人]     单 PR 手审：/pr-review
 R7 交付        /pr ──▶ /review-loop（评论当主张）──▶ merge（人）──▶ /release（tag · changelog · 验证 · 回滚）
 R8 学习        /issue --escape（逃逸缺陷）──▶ /retro（基线 · 回流分布 · 提案落层）──▶ 回到 R0/R1/R2 的变更提案
```

| 环 | 问题 | skill | 产物（一产物一生产者） | 门 / 闸 |
|---|---|---|---|---|
| R0 世界 | 这个产品为什么这样运转 | `psl`、`psl-derive` | `PSL-<x>.md`、`derived/{dos-proposal,workflow,form-draft,divergence}` | `verify_psl.py`、`verify_derived.py`、**G1** |
| R1 本体 | 系统里有什么、叫什么、什么不可违反 | `dos-extract`、`invariant-extract` | `dos.yaml`、`decisions.md`、不变量卡 | `verify_dos.py`、`verify_card.py`；agent 无写权 |
| R2 契约 | 什么算做完 | `issue`、`donewhen-extract`、`acceptance-spec` | issue、`spec.md`、**`done_when.yaml` v2** | `verify_issue.py`、`verify_done_when.py`、`validate_done_when_v2.py`、**G2**（`lock_done_when.py sign --stage g2`） |
| R3 标准 | 判据怎么被机器执行 | `test-suite-generator`、`spec-compile`、`calibrate` | `tests/<f>/`、`behavior`（manifest）、`compile_manifest.yaml`、`calibration_report.yaml` | `derive_counts / gen_existence / check_verbatim_names`、`verify_compile.py`、`verify_calibration.py`；L5 二次锁 |
| R4 计划 | 怎么拆成无上下文可做的卡 | `plan-cards` | `cards/CARD-xx.yaml` | `lint_cards.py` |
| R5 实现 | 按卡做、按卡提交 | `implement`、`commit`、`ratchet` | diff、commit、卡状态 | `verify_commit.py`（白名单 · 锁 · secrets）、`sdlc_state.py fail`（指纹升级） |
| R6 验收 | 三档验收，谁一票否决 | `acceptance-fleet` + `code-reviewer` `qa-reviewer` `pm-reviewer` `spec-drift-detector` `spec-gaming-detector` + `meta-judge`；`pr-review` | `ratchet-log/iteration-NNN/`、`final-state.json`、`findings.yaml` | A 档一票否决 / B 档告警 / C 档请求人；**G3** |
| R7 交付 | 合入与发布 | `pr`、`review-loop`、`release` | PR、收敛证据日志、tag、`CHANGELOG`、`releases/vX.md` | `verify_pr.py`、`pr-poll.sh done`、`verify_release.py`；merge / push tag 是人类动作 |
| R8 学习 | 流程病在哪层；环的参数该不该调 | `issue --escape`、`retro`、**`tune`** | `escape-defects.md`、`retro/retro-<date>.md`、`metrics.json`、`tune/harness-proposals-<date>.yaml` + patch | `metrics.py`、`tune.py`、`apply_proposal.py`（只出 diff）；提案不自动生效 |

**脊柱 `/sdlc`** 不做任何一环的活，只做五件事：持有状态（`sdlc_state.py`）、记账（`ledger.md` + 类型边伴生 `trace.jsonl`）、路由失败
（`routing.yaml` v2，含收敛检测）、把三道门编译成"不跑就 advance 不了"、把图与环声明成数据（`graph.yaml` / `loops.yaml` / `triggers.yaml`）。

---

## 2. 制品链：一个产物只有一个生产者

```
需求原文 ─psl─▶ PSL ─psl-derive─▶ derived/ ─G1─▶ 签字版形态草案(sha256)
                                                  │
代码 ─dos-extract─▶ dos.yaml ◀─对账(人,G1记录)─ dos-proposal.yaml
失败记忆 ─invariant-extract─▶ 不变量卡 ─┐
                                        ▼
需求/形态草案 ─issue─▶ issue(AC v2 雏形) ─donewhen-extract / acceptance-spec+convert─▶ done_when.yaml v2 ─G2─▶ .done_when.lock(stage g2)
                                                                                          │
                                        plan-cards ◀──────────────────────────────────────┤
                                            │ cards/                                       │
                                            ▼                                              ▼
                                        implement ─commit─▶ diff/commits        test-suite-generator + spec-compile ─▶ tests/ + behavior ─calibrate─▶ 校准报告
                                            │                                              │ lock --stage l5
                                            └──────────────▶ acceptance-fleet ◀────────────┘
                                                                  │ final-state.json
                                                        pr ─▶ review-loop ─▶ merge ─▶ release ─▶ archive(specs/<slug>/)
                                                                                        │
                                                                  escape ─▶ retro ─▶ 变更提案 → R0/R1/R2
```

**契约 v2 是全线的转轴（裁决 C1/C2/C3 的落实）。** `done_when.yaml` v2 = v1 超集：`acceptance`（以 AC 为单位，G2 签它）+
`existence` 只留观察边界 + `behavior` 降为 tests-manifest 种子（L5 由非实现者填并二次锁）+ `rules` / `thresholds`（六审查
skill 与 meta-judge 照旧读）+ `constraints` / `budgets`。`sdlc_state.py advance g2` 会跑 `validate_done_when_v2.py`——契约形状不对
就冻结不了。`acceptance-spec` 产出的 v1 经 `convert_v1_to_v2.py` 变成骨架，由 `/donewhen-extract` 或人补齐 AC。

**两段锁（裁决 C6）。** G2 锁判据（`--stage g2`）；L5 测试写完后再签一次（`--stage l5`，含 `tests/**` 与填好的 `behavior`）。
之后任何被锁文件出现在 diff 都要同一 diff 附 `change-proposal-*.md`，否则 `verify_commit.py` / `verify_pr.py` 拒。

---

## 3. 如何运转

### 3.1 状态机（脚本拥有，引擎只提议）

```
intake → track → issue → branch → contract → g2 → cards → implement → acceptance → pr → review → g3 → merge → release → archive
```

每个 `advance <stage>` 对着 `state.json` 检前置条件（不是对着引擎的说法）：

| 进入 | 必须已成立 |
|---|---|
| issue | track ∈ {psl, task}；PSL 轨还要 `gates.g1 = pass` |
| g2 | `contract.done_when` 存在 **且过 v2 校验** |
| cards | `gates.g2 = pass` ∧ `lock.path` 存在 |
| implement | `cards.lint_passed = true` ∧ 至少一张卡登记 |
| acceptance | 所有卡 `done` |
| pr | `acceptance.evaluation_result` 或 `acceptance.skipped_reason`（TASK 轨轻量，留痕） |
| g3 / merge | `review.done`；G3 required 时 `gates.g3 = pass` |
| release | `merge.sha` |
| archive | `release.done = true` 或 `release.skipped_reason` |

`--force --reason` 可以豁免，但豁免被写成 waiver（账本 + state），`/retro` 会数它。

### 3.2 三道门（只能人签）

| 门 | 何时 | 输入 | 脚本强制什么 |
|---|---|---|---|
| **G1 世界裁决**（PSL 轨） | 推导产物之后、issue 之前 | `derived/` + 分歧集 | `gate g1 --verdict pass` 要求 `world.derived_dir` 存在；reject 必须归因 `derivation_error | rule_error`（世界层计数 +1） |
| **G2 判据冻结** | 契约写完、拆卡之前 | `done_when.yaml` v2（+ contract.yaml） | pass 要求 `lock.path` 存在；契约必须过 v2 校验 |
| **G3 例外复核** | 验收之后、合入之前 | human AC 清单 + 失败报告 + 假设台账 | 产品需求默认触发；`gates.g3.required=false` 要显式 set 留痕 |

### 3.3 回流路由（X2）：失败归层，不原地重试

`sdlc_state.py fail --signal <信号>` 读 `routing.yaml`：给候选层（card ⊂ plan ⊂ task ⊂ ontology ⊂ world）、处理者、
动作、该层计数与预算余量、指纹重复次数、是否升级。**同层同指纹连续 2 次 = 无进展，立即升级**；预算按轨道分
（PSL 轨 task 回流 2，TASK 轨 1；单卡 3）；世界层不设上限——本来就该停下来交人。`/acceptance-fleet` 的四态
（FIX / SPEC_DRIFT / GAMING_RISK / NEEDS_HUMAN）与 `/ratchet` 的 kill/restart 都映射到这张表。升级时产出失败报告
（候选层 + 证据 + 已排除 + 建议回退），那是 G3 的输入——人不看原始日志。

### 3.4 信息隔离（评估者与被评估者分离）

- 实现者（`/implement`、`card-implementer`）只拿到卡 + 状态摘要 + AC 子集 + 红基线；看不到评审判据、隐藏集、其他卡。
- 评审 skill 的输出只给人和 `/meta-judge`；给实现者的是 fix-prompt（file:line + 改法，不含评审者身份与置信度）。
- `/calibrate` 的 holdout（隐藏变体集）放在实现者不可读的环境；`/review-loop` 的 verifier 与 fixer 隔离。
- 跨供应商评估器可用时用在最容易同源盲区的两个槽（对抗式 code-review、spec-gaming）。

### 3.5 三档验收（C9）

| 档 | 检查项 | 执行者 | 效力 |
|---|---|---|---|
| A 机械 | 测试 / lint / 类型 / secrets / 白名单 / 锁 / 新增依赖 / REQ 覆盖 / 隐藏集 / 契约硬命中 / 有复现的缺陷 | 脚本、`qa-reviewer`、`spec-gaming-detector`（硬）、`pr-review` 缺陷类 | 一票否决 |
| B 结构 | 复杂度 / 重复 / 公共 API 变更 / diff 体量 / spec-drift / gaming 软命中 | `code-reviewer`、`spec-drift-detector`、`pr-review` | 超阈值告警，有界可进 |
| C 判断 | human AC / 架构意图 / 可读性 | `pm-reviewer`（只路由）、`meta-judge`、`pr-review` C 档 | 请求人工（G3） |

### 3.6 账本与非对称回滚

产物（代码、卡、PR、契约版本）可以回滚；判据、失败记录、被拒的修复、路由决定、豁免**不回滚**（`ledger.md` 只增）。
`/review-loop` 的证据日志同理：被 reviewer 推翻的 verdict 保留原记录。`/retro` 读这些账本，把"又栽在这儿了"变成提案。

**决策迹（v0.6.0）。** `ledger.md` 每行同时写进 `trace.jsonl`，事件之间用封闭集的类型边相连：`caused_by`（回流 → 失败、
失败报告 → 回流、逃逸缺陷 → AC 变更）、`decided_by`（→ 路由规则 / 签字人 / 门记录）、`supersedes`（新版 AC → 旧版）、
`implements`（commit → 卡 → AC）、`references`、`depends_on`、`rejected_alternative`。只增日志只能向后指，所以因果边写成
"效果指向原因"。`trace.py why AC-003` 走出"AC 为什么改：隐藏集失败 → R08 回流 → 变更提案 by 张三"；`impact` 走出改它波及的
卡与 commit；`metrics.py` 从边算逃逸缺陷因果链深度与契约返工率——"为什么门没拦住"从考古变成一条查询。不上图数据库。

### 3.7 图与环是数据（v0.6.0）

- **`graph.yaml`** 节点带边界身份（`reads` / `must_not_read` / `writes` / `authority`），边带类型与守卫，回边带 `loop:`。
  `verify_graph.py` 五条 lint，每条对应 graph engineering 点名的一种生产失败：① skill/agent 节点写范围有界；② 去掉 loop_back 后
  必须是 DAG，且每条 loop_back 引用的环有预算和可测的成功谓词（"通过条件不可测的无界循环"）；③ 评估者 → 实现者的边只能携带
  `fix_prompt` / `accepted_claim`（"执行顺序 ≠ 信息可见性"）；④ 人节点必须声明 `resume_binding`（"人工恢复绑到错误 checkpoint"）；
  ⑤ fan_in 必须有 `merge`（"并发写无合并规则"）。实测：首版声明就被 lint ② 抓到两处未标环归属的圈（验收扇入回交、review 修复验证回交）。
- **`loops.yaml`** 六个环同一契约：`card_retry` · `ratchet` · `acceptance_ratchet` · `review_loop` · `lifecycle` · `hill_climb`，
  字段 level（LangChain 四层）/ timescale（Ng 三尺度）/ generator ≠ verifier / stop 四键（success · convergence · budget · impossible）/
  memory / fresh_context / trigger / escalate_to。`verify_loop.py` 检；`sdlc_state.py loops` 一屏看每个环的预算消耗。
- **`triggers.yaml`** 每个环绑到 Claude Code 原生原语：`/goal`（独立小模型判 Met / Not yet / Impossible，条件里的退出码必须回显）、
  `/loop`、Stop hook（`check-clean --as-hook`，模板 `assets/hooks/stop-clean-state.json`，不自动安装）、`/schedule`。
  `pr-poll.sh` 仍是谓词，只是不再是唯一的等待方式。

### 3.8 收敛检测（routing.yaml v2）

`fail` 命令每个 key 存最近 6 次指纹与 score：同指纹 ×2 = **repeat**；周期 2–3 往复 = **oscillation** → 派生 `oscillation_detected`
（R14，plan 层：在相似解之间震荡是方案层的权衡）；`--score` 连续 3 次不超过最佳 = **plateau** → R15（plan 层，允许一次探索性重写
再升级——ratchet 的做法提到路由表层面）；评估者判"在当前契约下不可能" = `impossible_under_contract` → R16（task 层，走变更提案；
只接受 `impossible_reporters` 里的 `--by`，实现者报被拒——对应 `/goal` 的 Impossible 判决）。收敛 ≠ 正确：三个信号都稳但产物差，
是换方案不是再迭代。任一升级置 `pending.failure_report`，`check-clean` 拒绝在没写报告时结束 session。

---

## 4. 五个闭环怎么闭

| 闭环 | 起点 → 终点 | 闭合机制 |
|---|---|---|
| 交付闭环 | 需求 → 合入 → 发布 | 状态机线性推进；每阶段产物过脚本或门；`release` 验证绿才算交付 |
| 失败闭环 | 任一阶段失败 → 正确的层 | `routing.yaml` + 指纹终止；失败报告 → G3；不在实现层重试世界层的错 |
| 校准闭环 | 线上逃逸缺陷 → 世界 / 本体 / 契约 | `/issue --escape`（归因层 + 为什么门没拦住）→ `/invariant-extract`（从失败抽不变量）→ `/psl` Open Questions / 变更提案 |
| 度量闭环 | 归档 → 流程改进 | `/retro`：基线 → 回流分布 → 提案落层（psl / dos / invariant / ac / routing / skill），提案经 G2/G3 生效 |
| 标准闭环 | 判据 → 测试 → 尺子本身 | `/spec-compile` 编译、`/calibrate` 证明尺子承重（mutation / α / holdout / 隔离）；未校准的标准不当证据 |
| **harness 闭环**（v0.6.0） | 六个环的 trace → 环自己的参数 | `/tune` 读归档 / pr-watch / results.tsv，按封闭 target 集出提案（routing 预算、指纹阈值、MAX_ROUNDS、隔离等级、fix_list），`apply_proposal.py` 只出 diff，人开 PR 合；样本 < 2 只记基线——LangChain 四层里的 Hill-Climbing Loop |

skill 正文的进化（第七个闭环）不在本插件：`skill-evolve` 邻居读各 skill 的 `eval/gate.json` fix_list（`/tune` 会往里写）。

---

## 5. 如何使用

### 5.1 安装与前置

```bash
/plugin marketplace add XRenSiu/claude-code-forge
/plugin install sdlc@claude-code-forge          # 之后重启 session
```
前置：`git`、`gh`（已 `gh auth login`）、`jq`、`python3` + `pyyaml`。与 looper / done-when-pipeline / ratchet 同时启用时，
同名 skill 用 `/sdlc:<name>`。

### 5.2 三种入口

**入口 A · 单点使用**（不进流水线，各 skill 独立可用）

```bash
/issue "用户可以按'上个月'这类相对时间搜索记忆"      # 结构化 issue，先给你看再建
/commit --issue 42                                   # 预门 + 自检 + 提交
/pr --issue 42 --done-when specs/x/done_when.yaml    # 预门 + 确认 + 建 PR
/review-loop 57                                      # 跟进 PR #57 直到收敛
/pr-review 57 --focus security --post                # 审别人的 PR
/dos-extract . ; /invariant-extract search           # 本体与不变量
/retro --archive specs/                              # 复盘：判据与世界的提案
/tune specs/ --pr-watch .sdlc/pr-watch               # 调参：环的参数提案（≥ 2 个归档）
python3 skills/sdlc/scripts/sdlc_state.py loops      # 六个环的预算消耗
python3 skills/sdlc/scripts/trace.py why AC-003      # 这条 AC 为什么改
```

**入口 B · TASK 轨全流程**（形态已定的需求）

```bash
/sdlc "导出报表增加 CSV 六列" --track task
#   → issue → branch → /donewhen-extract（或 /acceptance-spec + convert）→ 你签 G2
#   → /plan-cards → /test-suite-generator（按卡）→ /implement（每卡）→ /acceptance-fleet
#   → /pr → /review-loop → 你签 G3（有 human AC 时）→ 你合并 → /release → archive
```

**入口 C · PSL 轨全流程**（体验性 / 语义模糊的需求，或 issue 的 DOS 闭包失败被强制转轨）

```bash
/psl "用户可以按相对时间搜索记忆"                    # 世界；verify_psl.py
/psl-derive PSL-memory-time-search.md --n 3         # 推导产物 + 分歧集
#   → 你签 G1（g1-record.md：三问 + 分歧集逐条回应）
/sdlc "用户可以按相对时间搜索记忆" --track psl       # 从 issue 起同入口 B
```

### 5.3 人在哪里出现

| 时机 | 人做什么 | 命令 |
|---|---|---|
| G1 | 三问 + 分歧集回应 + 归因 | `sdlc_state.py gate g1 --verdict pass|reject --by <你> [--attribution …] --record g1-record.md` |
| G2 | 确认判据、指派 human AC 裁决人、签锁 | `lock_done_when.py sign --by <你> --stage g2 done_when.yaml` → `gate g2 --verdict pass` |
| 建 issue / 建 PR / 发 review / 打 tag / 部署前 | 看一眼再放行（`--yes` / `--autopilot` 可免，门不可免） | 各 skill 自带确认 |
| G3 | 裁决 human AC、处置 B 档告警与假设台账、确认失败报告的归因层 | `gate g3 --verdict pass|reject --record g3-record.md` |
| merge | 合并是人类动作 | GitHub |
| 逃逸缺陷 | 归因到层 | `/issue --escape` |

### 5.4 中断与恢复

`/sdlc --resume <slug>` 从 `state.json.stage` 继续；`ledger.md` 说明上次为什么停；`/review-loop` 的水位线与计数器
保证评论不重复处理、预算跨会话延续。`state.json` 不手改。

### 5.5 产物落点

```
.sdlc/<slug>/state.json · ledger.md        specs/<slug>/（归档：state · ledger · done_when · lock · cards · evaluation · G 记录）
.sdlc/pr-watch/pr-<N>.*                    cards/CARD-xx.yaml · .done_when.lock · tests/<feature>/ · ratchet-log/
derived/ · PSL-<x>.md · dos.yaml          releases/vX.Y.Z.md · CHANGELOG.md · escape-defects.md · retro/retro-<date>.md
```

---

## 6. 自洽规则（设计不变量）

1. **一个产物只有一个生产者；契约只有一种 schema（v2）**，其他形态经转换后进入。
2. **判据先于代码，测试非实现者写且写完锁**（两段锁）；改契约或测试只能走变更提案。
3. **实现者看不到评估者**；评估者的输出经 meta-judge / 人再回到实现者（fix-prompt）。
4. **预算与终止由脚本强制**（状态机、路由表、pr-poll.sh），引擎不自行维护计数器。
5. **账本只增不删**；产物可回滚，判据与失败记录不回滚。
6. **三道门只能人签**；`--autopilot` 免的是逐步确认，不是门。
7. **未校准的标准不当证据**（`calibration_pending`）；`meets_done_when` 由脚本比对，不由评估 agent 宣布。
8. **失败归层再处理**；同指纹重复 = 无进展 = 升级，不是重试。
9. **合入不是终点**：release 验证绿才交付；逃逸缺陷必须回到层。
10. **静态过审 ≠ 有效**：所有 skill `static_only`，行为层未跑就不说"已验证"。
11. **图与环是数据，不是散文**：节点有写范围，每个圈有环契约，评估者到实现者只带 fix_prompt，人节点有恢复绑定——`verify_graph.py` 检。
12. **收敛 ≠ 正确**：repeat / oscillation / plateau 都是"换层"的信号，不是"再试一次"的理由；`impossible` 只能由评估者说。
13. **harness 改动经人**：`/tune` 只出 diff；routing / 脚本默认值 / fix_list 的改动都是 PR。

---

## 7. 覆盖矩阵与空白

| 参考文档环节 | 承载 | 状态 |
|---|---|---|
| U1/U2 PSL · U3 推导 · G1 | psl · psl-derive · gate g1 | 已有 |
| L1 TASK · 台账 | issue · acceptance-spec | 已有 |
| L2 接口契约 | — | **空白**（`verify_issue.py` 只 flag observe 未解析） |
| L3 DONE_WHEN v2 · G2 | donewhen-extract · validate v2 · lock --stage g2 | 已有 |
| L4 PLAN | plan-cards | 已有 |
| L5 测试 · 红绿 · 隐藏集 | test-suite-generator · spec-compile · calibrate · lock --stage l5 | 已有；红-绿脚本**空白** |
| L6 实现 · 白名单 · 指纹 | implement · commit · ratchet · sdlc_state fail | 已有 |
| L7 A/B/C · G3 | acceptance-fleet 六 skill · meta-judge · pr-review · gate g3 | 已有；`meets_done_when` 比对脚本**空白** |
| L8 合入 · 交付 · 逃逸 | pr · review-loop · release · issue --escape | 已有 |
| X1 DOS 生命周期 | dos-extract · invariant-extract · dos-proposal | 部分：应然↔现状对账、candidate 命名空间、ontology-drift **空白** |
| X2 路由 · 预算 | routing.yaml · sdlc_state fail | 已有 |
| X3 度量 | retro · metrics.py（+ trace 指标）· **tune**（harness 闭环） | 已有 |
| 环契约 / 图声明 / 触发绑定（loop & graph engineering） | loops.yaml · graph.yaml · triggers.yaml · verify_loop / verify_graph · check-clean | 已有（v0.6.0）；Stop hook 只有模板 |
| 收敛检测（oscillation / plateau / impossible） | routing.yaml v2 R14–R16 · `fail --score --by` | 已有；阈值是文献先验，待真实运行校准 |
| 决策迹 | trace.jsonl · trace.py · metrics 新指标 | 已有 |

---

## 8. 术语

| 词 | 含义 |
|---|---|
| PSL 轨 / TASK 轨 | 形态未定（先建世界）/ 形态已定（直接进契约）的两条轨道；DOS 闭包失败是客观转轨触发 |
| AC v2 | `kind: mechanical`（observe/given/expect）或 `kind: human`（statement/judge/evidence）的验收条目；契约的最小单位 |
| 卡 | 自包含的任务单元；实现者的全部输入 |
| 层 | card ⊂ plan ⊂ task ⊂ ontology ⊂ world：失败回流的坐标 |
| 指纹 | 失败输出的稳定摘要；同指纹重复 = 无进展 |
| 三档 | A 机械（否决）/ B 结构（告警）/ C 判断（请求人） |
| 两段锁 | G2 锁判据；L5 锁测试与 manifest |
| 隐藏集 | 冻结 AC 的变体，实现者不可读；calibrate 的 holdout |
| 账本 | `ledger.md`，只增不删的失败与决定记录 |
| static_only | 结构过审、脚本冒烟，但带/不带 skill 的行为对比未跑 |
| 环契约 | `loops.yaml` 一条：generator ≠ verifier、stop 四键、budget.ref、memory、trigger |
| 图 | `graph.yaml`：节点（边界身份）+ 边（类型 / 守卫 / 环归属）；每个圈必须归属一个环 |
| 迹 | `trace.jsonl`：账本的类型边伴生；`caused_by` 由效果指向原因 |
| oscillation / plateau / impossible | 三种"再试也没用"：往复 / 不涨 / 契约下不可能——分别归 plan / plan / task |
| hill_climb | 环改环的外环：trace → 参数提案 → 人开 PR |
