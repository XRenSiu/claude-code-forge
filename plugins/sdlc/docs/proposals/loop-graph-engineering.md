# 提案：用 Loop Engineering / Graph Engineering 的透镜重看 sdlc（2026-09-05）

> 状态：**P1–P4 已于 2026-09-05 一次实施（sdlc v0.6.0）**，见 `docs/design-notes.md` 第三次整理与各 skill 的 `eval/gate.json`。
> 与提案的两处偏离：① 因果边命名为 `caused_by`（效果 → 原因），不是文献的 `caused`——只增日志只能向后指；② 四期版本 0.3.0–0.6.0
> 合并为一次 0.6.0。仍为 `static_only`；§6 的"先跑一次真实需求再校准阈值"仍然成立。
>
> 原文（以 v0.2.0 为基线）：目的：先把业界对两个概念的理解说清，再逐项对照 sdlc 现状，给出"改什么、加什么、
> 明确不做什么"以及分期与版本号。

---

## 0. 一句话结论

sdlc 在被这两个词命名之前就已经是一个"环套图"的系统：生成者与评估者分离、终止谓词编译进脚本、状态在磁盘、
三道人签的门、按层回流。**新词汇带来的不是新架构，而是四个真实缺口 + 一个"把隐式变显式"的机会**：

| 缺口 | 业界叫法 | sdlc 现状 |
|---|---|---|
| 环的收敛检测只有"同指纹 ×2" | convergence detection：oscillation / plateau / impossible | `sdlc_state.py fail` 只比对上一次指纹 |
| 环的触发靠自造 bash 轮询 | L3 event-driven loop；Claude Code 原生 `/goal` `/loop` Stop hook `/schedule` | `pr-poll.sh watch` sleep 轮询 |
| 没有"环改环"的外环 | L4 hill-climbing loop：traces → 分析 → 改 harness 参数（人审后生效） | `/retro` 出提案，但 routing 预算 / MAX_ROUNDS / 隔离等级从未被数据调过 |
| 账本是平表，决策没有类型边 | context graph / decision traces：`caused` `decided_by` `supersedes` `implements` | `ledger.md` 每行独立；"为什么门没拦住"要考古 |
| 图写在 ASCII 里，不是数据 | graph engineering：nodes / edges / state / contracts 可 lint | `ARCHITECTURE.md` 的图 + `sdlc_state.py` 硬编码线性链 |

---

## 1. 业界如何理解这两个词

### 1.1 词汇谱系（2026 年 6–7 月成形）

prompt → context → harness → **loop** → **graph** engineering。每一层继承下一层的弱点："一个环反复调用差的 harness
不会让错误变小，只会让它更快重复"（codecentric）。Loop engineering 由 Addy Osmani 2026-06 命名，Boris Cherny（Claude Code）
的表述是"I don't prompt Claude anymore… My job is to write loops"；graph engineering 2026-07 中在 X 上起势。

### 1.2 Loop Engineering：一个环的解剖

综合 Osmani / IBM / codecentric / arXiv 2607.00038 / AI Builder Club，一个"工程化的环"有七个部件：

| 部件 | 业界表述 | sdlc 里的对应物 |
|---|---|---|
| **Goal** | 每次迭代都重新评估的递归目标，带可测量的停止标准 | `done_when.yaml` v2；每张卡的 AC 子集；ratchet 的 P0 criteria |
| **Generator ≠ Verifier** | "The verifier is the bottleneck, not the generator"；自评失败是反模式 | card-implementer ↔ acceptance-fleet；ratchet master/worker；review-loop verifier/fixer；meta-judge 硬墙 |
| **Stopping rule** | 三路：success / convergence（N 轮无进展）/ budget；Claude `/goal` 另有 **Impossible** 判决 | `pr-poll.sh done/round/strike`；`fail` 的预算 + 指纹；ratchet 的 done_when 三条件。**缺 impossible** |
| **Memory on disk** | "the model forgets everything between runs so the memory has to be on disk"；progress / learnings / dead-ends | `state.json`（充分统计量）、`ledger.md`、ratchet 的 `learnings.md` / `dead-ends.md`、pr-watch 证据日志 |
| **Fresh context** | Ralph loop：每次迭代新上下文，状态从磁盘读；Anthropic 长跑 harness：initializer / coding agent 分离 + progress 文件 + "leave the environment in a clean state" | card-implementer 是新上下文；`/sdlc --resume` 从 state.json 续。**缺 clean-state 强制** |
| **Trigger** | cron / webhook / 事件 / 另一个 agent——去掉人手敲回车 | 只有 `pr-poll.sh watch`（bash sleep）；未绑定 `/goal` `/loop` Stop hook `/schedule` |
| **Feedback routing** | 结果按信号路由回环的某一层，不是塞回起点 | `routing.yaml` + 分层预算——这是 sdlc 最强的部分 |

**四层嵌套模型**（LangChain "The Art of Loop Engineering"，是目前最被引用的分层）：

1. **Agent Loop**——模型调工具直到任务完成。sdlc：单卡实现。
2. **Verification Loop**——输出对 rubric 打分，不过则带反馈重试；人可以当 grader。sdlc：acceptance-fleet 四态棘轮、review-loop、ratchet。
3. **Event-Driven Loop**——外部事件（webhook / 定时 / 消息）触发运行并更新真实系统；人可在出口审批。sdlc：**几乎没有**。
4. **Hill-Climbing Loop**——生产 trace 喂给分析 agent，改写 harness 配置（prompt / tools / grading rules）；"返回箭头不是回到顶部，
   而是伸进去直接改 agent loop"；改动先过人审。sdlc：`/retro` 是半个（出提案不闭环）。

**三个时间尺度**（Andrew Ng，AI Builder Club 转述）：agentic coding loop（分钟）/ developer feedback loop（十分钟到小时）/
external feedback loop（天到周）。"赢的团队不是生成代码最多的，而是让三个环都在转、且各自诚实匹配时间尺度的。"
sdlc 对应：卡级 / G1-G3 与 review / 逃逸缺陷 → retro。

**失败模式**（arXiv 2607.01641 "When Agents Do Not Stop"、2607.00038、agentpatterns、SWE-Review 2607.06065）：

- 无限循环：终止条件缺失、无法识别完成、工具持续失败——检测手段是 **fingerprinting（重复的 action-observation 对）、
  state repetition（周期性状态）、progress metrics（朝目标推进的度量）**。
- 幻觉传播、目标漂移、规格博弈（spec gaming）、反馈不足。
- **Reviewer sycophancy**（reviewer 被 resolver 的自信解释说服）、**over-iteration**（在相似解之间震荡）、**收敛到低质量平台**
  （三个信号都稳了但产物差——需要换方案不是再迭代）。
- 收敛 ≠ 正确："convergence signals measure whether the output is stabilizing, not whether it is right"。
- 人的一侧：comprehension debt、intent debt、cognitive surrender；"Build the loop. Stay the engineer."
- 预算：无人看管 + 弱 verifier = 静默烧钱（Uber 案例：4 个月超支后设 $1,500/月硬顶）。

**Claude Code 原生原语**（code.claude.com/docs/en/goal，2026-09 现状）：

| 原语 | 下一轮何时开始 | 何时停 | 评估者 |
|---|---|---|---|
| `/goal <condition>` | 上一轮结束 | 小模型判 **Met / Not yet met / Impossible**；或不可恢复错误；连续数轮无工具调用自动停 | 独立小模型（默认 Haiku），只看 transcript，不跑命令 |
| `/loop [interval]` | 时间间隔到，或模型自定节奏（ScheduleWakeup） | 人停或模型判完 | 无 |
| Stop hook | 每轮结束 | 你的脚本（确定性）或 prompt（模型判） | 自定 |
| `/schedule` | cron（云端 routine） | — | — |

`/goal` 本质是 session 级的 prompt-based Stop hook；条件要写成"Claude 的输出能证明的东西"（如 `npm test exits 0`），
可加 `or stop after 20 turns` 做预算；后台任务未完时延迟评估并按 30 分钟起指数退避 check-in。

### 1.3 Graph Engineering：多个环怎么连

**定义**（Aishwarya Srinivasan / AI Builder Club，被最多引用）："wiring multiple specialized agents or steps into a graph:
nodes that do the work, edges that route between them, and shared state flowing along those edges." 判据一句话：
"the difference is who decides the path, the agent or you"——环里是 agent 选路，图里是你声明合法路径、agent 在节点边界内活动。

**三种不同的"图"**（puppyone，唯一把歧义摊开的来源）：

1. **Execution / orchestration graph**——节点是 agent / 函数 / 模型调用 / 路由器 / 人的检查点；边回答"接下来谁跑、谁控制路径"。LangGraph、ADK、AutoGen GraphFlow。
2. **Graph of loops and controls**——节点是评估器 / 重试 / 策略检查 / 反馈环；回答"多个改进与治理环如何约束系统"。**尚在成形，定义最松，但恰好是 sdlc 所属的那一种。**
3. **Knowledge / context / memory graph**——节点是实体或事实，边是带时间与来源的类型关系；**context graph**（cognee / Neo4j / Atlan）= 会话触及的知识图切片 + **decision traces**（约束、权衡、决定性信号、理由）。

三者不可互换："execution order does not automatically define information visibility"——调度图决定谁先跑，不决定它能看到什么。

**四个部件**：nodes（有边界身份：工具、写范围、权限）、edges（sequential / conditional / fan-out / fan-in / loop-back / interrupt）、
shared state（类型化、写归属明确）、**contracts**（输入输出、权限、预算、停止条件）。

**四层可分离的状态**（puppyone）：control-flow state（编排器拥有）/ message context（context builder 拥有）/
durable artifacts（治理层）/ graph knowledge（检索层）。混在一起是可避免的风险。

**类型边**（Flowtivity）："the edge type IS the knowledge"——六种覆盖生产场景：`supersedes` `depends_on` `decided_by` `caused`
`implements` `references`。无类型的 "related to" 不能支撑多跳推理（85% 单跳准确率 5 跳后只剩 44%）。

**何时值得上图**（AI Builder Club / puppyone 一致）：只在真实边界出现时——不同专长与工具集、不同权限、独立证据源、确定性审批、
隔离的失败与重试、跨运行的持久交接。"Most tasks never need it. Over-engineering is the default failure mode."
成本盈亏点（Flowtivity）：每轮通过率 > ~50% 时并行图才比串行环便宜。

**生产失败清单**（puppyone，"来自契约缺失而不是拓扑错误"）：节点间 state schema 漂移；跨授权边界的上下文泄漏；非幂等重放；
**通过条件不可测的无界循环**；并发写共享字段无合并规则；**人工恢复绑定到错误的 run / 过期 checkpoint**；可观测性只显示执行顺序不显示
证据来源；多个 agent 互相强化同一错误。LangChain 2026 State of Agent Engineering：>60% 生产事故归于状态管理失败。

---

## 2. 对照：sdlc 已经有什么、缺什么

### 2.1 Loop 维度

| 部件 | 现状评级 | 具体 |
|---|---|---|
| Generator ≠ Verifier | **强** | 四处分离 + 隔离等级 L0–L3（禁 L0，最低 L2，推荐跨供应商）；meta-judge 不复审 |
| Stopping rule | **中** | success / budget 有；convergence 只有"同指纹连续 2 次"；**无 oscillation、无 plateau、无 impossible** |
| Memory on disk | **强** | state.json / ledger.md / learnings / dead-ends / 证据日志；账本只增 |
| Fresh context | **中** | 实现者新上下文 ✔；`/sdlc` 自身跨 session 只靠 `--resume`；**无 clean-state 出口强制**（gate.json fix_list 已登记"Stop hook 待编译"） |
| Trigger（L3） | **弱** | 只有 pr-poll.sh 的 bash sleep；未绑定 `/goal` `/loop` Stop hook `/schedule` |
| Hill-climbing（L4） | **弱** | retro 产出 `routing` / `skill` 提案，但没有从 trace 算"预算该不该调"的脚本；skill 演化外包给邻居 |
| 环的统一契约 | **无** | 六个环（卡重试 / ratchet / 四态棘轮 / review-loop / 阶段机 / retro）各自一套词：retries · rounds · strikes · iterations · MAX_ROUNDS；无统一 schema，无"当前活跃环"总览 |

### 2.2 Graph 维度

| 部件 | 现状评级 | 具体 |
|---|---|---|
| Nodes 有边界身份 | **强** | 卡的 allowed/forbidden files、agent 的 tools/model、写权限（agent 无写权）、评估者提示不给实现者 |
| Edges 可读可 lint | **弱** | 线性链硬编码在 `sdlc_state.py`；分叉（PSL/TASK）、扇出（六审查）、扇入（meta-judge）、中断（G1/G2/G3）、回边（routing.yaml）分散在散文与两处代码 |
| Shared state 分层 | **中** | control-flow（state.json）与 durable（ledger / specs）分开 ✔；message context（card_context.md）✔；四层未显式命名 |
| Contracts per node | **中** | 每个 SKILL.md 有 φ/γ，但**没有机器可读的节点契约**（输入 / 输出 / 权限 / 预算 / 停止） |
| Correlation IDs | **中** | slug · card · fingerprint · thread id 有；但账本行之间没有引用 |
| Typed edges / decision traces | **无** | ledger.md 平表；G1/G3 记录、失败报告、变更提案、被拒修复、review verdict 各是孤立文件 |
| Human interrupts 与恢复绑定 | **强** | 三道门编译进 advance；锁哈希防契约漂移；`--resume` 读 state.json |
| 幂等重放 | **强** | 水位线、prereq 检查、原子写 |
| 多 agent 同源盲区 | **强** | 跨供应商隔离等级、对抗式审查槽位 |

结论：**sdlc 的"图"是真的但不可见；"环"是真的但收敛检测粗、触发靠手、没有外环。** 下面每个方案只对准一个缺口。

---

## 3. 方案（七项，按缺口一一对应）

### 方案 A · 把图从散文变成数据：`graph.yaml` + `verify_graph.py`

**对准**：Edges 不可 lint；Contracts 不可读；ARCHITECTURE.md 的图与代码可能漂移。

**做什么**

- 新增 `skills/sdlc/assets/graph.yaml`：
  ```yaml
  version: 1
  nodes:
    - id: implement          # skill | agent | human | script
      kind: skill
      reads: [cards/CARD-*.yaml, state.summary, ac_subset, red_baseline]
      must_not_read: [ratchet-log/**, spec-robustness.md, evaluator_prompts]   # 信息可见性 ≠ 执行顺序
      writes: [card.allowed_files]
      authority: {commit: true, post: false, resolve: false, sign: false}
      loop: card_retry        # 引用 loops.yaml
    - id: g2
      kind: human
      resume_binding: [lock.path, contract.done_when]   # 恢复时必须匹配的 state 字段
  edges:
    - {from: contract, to: g2, type: interrupt, guard: validate_done_when_v2}
    - {from: acceptance-fleet, to: [code-reviewer, qa-reviewer, pm-reviewer, spec-drift-detector, spec-gaming-detector], type: fan_out}
    - {from: [code-reviewer, ...], to: meta-judge, type: fan_in, merge: meta-judge.dedupe_weight_arbitrate}
    - {from: implement, to: plan-cards, type: loop_back, signal: same_card_same_fingerprint}   # 引用 routing.yaml
    - {from: track, to: [psl, issue], type: conditional, guard: dos_closure}
  ```
- 新增 `skills/sdlc/scripts/verify_graph.py`，lint 五条（每条对应 puppyone 的一个生产失败）：
  1. 每个 `kind: skill|agent` 节点 `writes` 非空且有界（无 `**` 全量）；
  2. **每个环（图中的圈）都能解析到一个 `loops.yaml` 条目，且该条目有 budget + stop 谓词**（"无界循环 + 不可测通过条件"）；
  3. 任何一条边若 `from` 是评估者节点、`to` 是实现者节点，则边上 `carries` 只能是 `fix_prompt`（不得携带 verdict 原文 / 评估者身份 / 置信度）；
  4. `kind: human` 节点必须有 `resume_binding`（防"恢复绑定到错误 run"）；
  5. `fan_in` 边必须声明 `merge`。
- `sdlc_state.py` 新增只读子命令：`graph next`（当前阶段的合法后继与守卫）、`graph render`（输出 mermaid 到 stdout，
  ARCHITECTURE.md §1 的图改为由它生成并在 smoke 里 diff）。**`advance` 的前置检查逻辑本期不改**，只加一条断言：
  `next_allowed` 与 graph.yaml 一致，不一致 smoke 失败——先让数据与代码互相监督，第二期再决定谁是源。

**不做什么**：不引入 LangGraph / ADK 运行时。skill 本身就是运行时，graph.yaml 是声明，读它的是 300 行 Python。

**验收**：`verify_graph.py` 在 fixture 上拒绝五类坏图；`graph render` 输出与 ARCHITECTURE.md 手绘图语义一致；smoke +6。

### 方案 B · 统一环契约：`loops.yaml` + `verify_loop.py`

**对准**：六个环六套词；没有"活跃环总览"；LangChain 的 >60% 状态事故论。

**做什么**

- 新增 `skills/sdlc/assets/loops.yaml`，每个环同一 schema：
  ```yaml
  - id: card_retry
    level: agent                    # agent | verification | event | hill_climbing（LangChain 四层）
    timescale: minutes              # minutes | hours | days（Ng 三尺度）
    goal: {predicate: ac_subset_green, script: qa-reviewer | test entry}
    generator: implement
    verifier: acceptance-fleet      # verify_loop.py 强制 generator ≠ verifier
    stop:
      success: ac_subset_green
      convergence: {fingerprint_repeat: 2, oscillation_period: [2, 3], plateau_rounds: null}
      budget: {ref: routing.budgets.<track>.card_retries}
      impossible: {signal: impossible_under_contract}      # 方案 C 新增
    memory: [state.json#cards.items, ledger.md]
    fresh_context: true
    trigger: turn_end
    escalate_to: plan
  - id: review_loop
    level: verification
    generator: comment-fixer | self
    verifier: human_reviewer | fix-verifier
    stop: {success: pr-poll.done==0|10, convergence: {empty_watches: 4, no_new_threads: 2}, budget: {rounds: 10, strikes: 3}}
    memory: [.sdlc/pr-watch/pr-N.json, counters.json]
    trigger: event(pr_activity) | interval        # 方案 D 绑定
  - id: hill_climb          # 方案 E
    level: hill_climbing
    timescale: days
  ```
  六个条目：`card_retry` · `ratchet` · `acceptance_ratchet`（四态）· `review_loop` · `lifecycle`（阶段机自身，budget = 各层预算总和）· `hill_climb`。
- `verify_loop.py`：generator ≠ verifier；`stop` 四键齐全（允许 `null` 但必须显式）；`budget.ref` 能在 routing.yaml 解析；`memory` 路径落在归档布局内。
- `sdlc_state.py loops`：读 state.json 计数器 + pr-watch counters + ratchet results.tsv，打印每个活跃环的**预算消耗率**与最近指纹——一屏看清"钱花在哪个环"。
- 各 skill 的 SKILL.md 末尾加 `## 环契约` 一段，只写 `loops.yaml#<id>` 的引用，不复制内容（一个产物一个生产者）。ratchet 的 Step 1–5 重写为六格形态是**另一个已登记的 TODO**，本方案不顺手做。

**验收**：`verify_loop.py` 拒绝 generator==verifier 与缺 stop 键的 fixture；`loops` 子命令在 fixture 归档上输出六行。

### 方案 C · 收敛检测升级：oscillation / plateau / impossible

**对准**：只有"同指纹 ×2"；arXiv 2607.01641 的三种检测只编译了一种；`/goal` 的 Impossible 判决没有对应物；SWE-Review 的 over-iteration。

**做什么**（全部在 `sdlc_state.py fail` 与 `routing.yaml`）

- 指纹从"只存上一次"改为**每个 key 存最近 6 次**（`counters.fingerprint_history[key]`），新增三个判定：
  - **oscillation**：历史中出现周期 2 或 3 的重复（A B A B / A B C A B C）→ 视同无进展，信号 `oscillation_detected`，归 **plan 层**（"在相似解之间震荡 = 方案层的事"）。
  - **plateau**：`fail --score <float>` 可选；同 key 连续 N 次（默认 3，routing 可调）score 不升 → `plateau`，归 plan 层，动作 `explore_once_then_escalate`（ratchet 已有"收敛前一次探索性重写"，把它提到路由表层面，所有环共享）。
  - **impossible**：新信号 `impossible_under_contract`，由 verifier（acceptance-fleet / fix-verifier / 人）报，语义 = "在当前契约下不可能满足"（对应 `/goal` 的 Impossible）→ **task 层**，动作 `change_proposal_required`。实现者不得报此信号（verify: `--by` 必须是评估者节点或人）。
- `routing.yaml` 加三行：`R14 oscillation_detected → plan`，`R15 plateau → plan（explore_once_then_escalate）`，`R16 impossible_under_contract → task`。
- 失败报告模板 `failure_report.md` 增加"收敛证据"段：指纹历史、score 序列、判定类型——G3 的人看得到"是震荡还是平台"。
- `pr-poll.sh` **不改**：strike 已覆盖线程级震荡；改它需要真实 PR 才能验证。

**验收**：smoke 新增 fixture：A B A B 序列第 4 次 → `escalate: true, why: oscillation`；score 3 次不升 → plateau；实现者报 impossible 被拒。

### 方案 D · L3 触发层：绑定 Claude Code 原生原语

**对准**：Event-Driven Loop 几乎为零；pr-poll.sh 的 bash sleep 是自造轮询；gate.json fix_list 已登记"advance 前置门编译成 Stop hook"。

**做什么**

- 新增 `skills/sdlc/assets/triggers.yaml`：阶段 → 触发类型 → 绑定方式。
  | 阶段 / 环 | 触发 | 绑定 |
  |---|---|---|
  | implement（卡重试） | turn_end | `/goal "CARD-xx 的 AC 子集测试全绿且 verify_commit 通过，或 stop after <card budget> turns"` |
  | review_loop | event(pr_activity) / interval | 交互：`/loop 5m` 调 `pr-poll.sh snapshot`；无人值守：`/goal "pr-poll.sh done <PR> 打印 exit 0 或 10，或 stop after 10 turns"`；headless：`/schedule` 跑 `claude -p "/review-loop <PR>"` |
  | acceptance | after(all cards done) | 手动 / `/goal` 条件含 `sdlc_state.py show` 输出 |
  | retro / hill_climb | cron weekly | `/schedule` |
- `review-loop/references/triggers.md`：写清 `/goal` 评估者**只看 transcript 不跑命令**，所以 `pr-poll.sh done` 的退出码必须回显到对话；`MAX_WAIT` 与 Bash 超时的关系不变；`watch` 仍是合法路径（交互式长阻塞时最省 token），只是不再是唯一路径。
- 新增 `skills/sdlc/assets/hooks/stop-clean-state.json`（**模板，不自动安装**；design-notes 已决定不做插件级 hooks）：Stop hook 跑 `sdlc_state.py check-clean --slug <s>`，拒绝在"有卡 `doing` 且工作区脏 / 账本最后一行是 fail 且未写失败报告"时结束 session——Anthropic 长跑 harness 的 "leave the environment in a clean state" 编译态。
- `sdlc_state.py check-clean`：新子命令，exit 0 干净 / 1 脏并列出原因。

**不做什么**：不把 `pr-poll.sh` 删掉重写成 hook；不把 `/sdlc` 改成模型可自动调起（它建 issue、发 PR、回帖，必须人显式启动——Osmani："merge 仍是人的决定"）。

**验收**：`check-clean` 在两种脏 fixture 上 exit 1；`triggers.yaml` 每个环都能在 `loops.yaml` 找到；文档级说明 `/goal` 条件写法与陷阱。

### 方案 E · L4 爬山环：`/tune`（traces → harness 参数提案 → 人审）

**对准**：Hill-Climbing Loop 缺失；retro 的 `routing` / `skill` 提案没有数据支撑的生成器；"返回箭头要伸进去改 agent loop"。

**做什么**

- 新 skill `skills/tune/`（或 `/retro --tune`；倾向独立 skill，因为产物与去向不同：retro 改**契约与世界**，tune 改**harness 参数**）：
  - `scripts/tune.py <archive_root> [--pr-watch .sdlc/pr-watch] [--ratchet-logs ...]`：从 state.json 计数器、ledger、pr-watch 证据日志、ratchet results.tsv 算**每个环的运行统计**：
    - 预算利用率（用了几成就升级 / 从未触顶 → 预算可能过宽）
    - 按 routing 规则的升级频次（R02 同指纹升级占比高 → 卡切分问题；R04 锁冲突高 → 契约写法问题）
    - 指纹重复命中率、oscillation / plateau 计数（方案 C 之后可得）
    - review verdict 分布：ACCEPT / REJECT / REPLY / ESCALATE 占比；**ACCEPT ≥ 95% 且线程 ≥ 5 → `sycophancy_suspect`**（SWE-Review 的 reviewer sycophancy 反向代理：本 skill 的 REJECT 是合法且被期望的）
    - strike 分布、bot 线程占比
    - 隔离等级使用分布与 GAMING_RISK 命中率的交叉
  - 产物 `tune/harness-proposals-<date>.yaml`，每条：`target`（封闭集：`routing.budgets.*` / `routing.fingerprint_repeat_limit` / `review-loop.MAX_ROUNDS|MAX_THREAD_STRIKES` / `acceptance-fleet.isolation_min` / `pr-review.b_tier_thresholds` / `code-reviewer.focus_allocation` / `<skill>.fix_list`）、`current`、`proposed`、`evidence`（引用数据行）、`expected_delta`（下次哪个指标怎么变）、`risk`。
  - `scripts/apply_proposal.py <proposal> --dry-run`：只打印将改的 diff；真实 apply 走 PR（改 routing.yaml / SKILL.md 的都是仓库文件）。**永不自动生效**——LangChain L4 的"harness 改动先过人审"是硬约束，retro 的"样本 1 不下结论"规则继承。
  - `skill` 通道：把提案写进目标 skill 的 `eval/gate.json` `fix_list`——这已是 skill-evolve 邻居的既定接口，tune 只是把"写 fix_list"从手工变成脚本。
- `loops.yaml` 登记 `hill_climb`（level: hill_climbing, timescale: days, generator: tune, verifier: human, trigger: cron）。
- `docs/ARCHITECTURE.md` §4 "五个闭环"改为六个：新增**harness 闭环**（trace → tune → 提案 → PR → 人合）。

**验收**：`tune.py` 在含 ≥ 2 个归档 + 1 个 pr-watch 日志的 fixture 上产出 ≥ 3 条提案且每条字段齐；`apply_proposal.py --dry-run` 对 routing 提案输出正确 diff；单归档 fixture 上只出基线不出提案。

### 方案 F · 决策迹图：`trace.jsonl` + 类型边 + `trace.py`

**对准**：账本平表；"为什么门没拦住"要考古；puppyone "可观测性只显示顺序不显示证据来源"；Flowtivity "the edge type IS the knowledge"。

**做什么**

- `ledger.md` **保持不变**（人读、只增）。新增机器可读的**伴生文件** `.sdlc/<slug>/trace.jsonl`，一行一个事件：
  ```json
  {"id":"ev-0042","at":"…","kind":"fail","node":"implement","signal":"card_test_fail","fingerprint":"a1b2c3",
   "refs":[{"type":"caused","target":"ev-0045"},{"type":"references","target":"cards/CARD-03.yaml"}]}
  {"id":"ev-0045","kind":"reflow","layer":"plan","refs":[{"type":"decided_by","target":"routing.R02"}]}
  {"id":"ev-0051","kind":"change_proposal","refs":[{"type":"supersedes","target":"done_when.yaml#AC-003@v1"},{"type":"decided_by","target":"g2-record.md#2026-09-06"}]}
  {"id":"ev-0060","kind":"commit","sha":"…","refs":[{"type":"implements","target":"CARD-03"},{"type":"implements","target":"AC-003-a"}]}
  ```
  边类型封闭集（Flowtivity 六种 + bespoke-design provenance 已用的一种）：`caused` `decided_by` `supersedes` `implements` `references` `depends_on` `rejected_alternative`。
- `sdlc_state.py` 的 `ledger_append` 同时写 trace.jsonl（同一次原子写；trace 损坏不影响 state 正确性——它是证据不是控制状态，与 pr-watch 证据日志同一原则）。`gate`、`fail`、`card --commit`、`set contract.*` 各自带默认 refs。
- 新脚本 `skills/sdlc/scripts/trace.py`：
  - `why <target>`：反向走 `caused` / `decided_by` / `supersedes` 到根，输出因果链（"AC-003 为什么改：R08 隐藏集失败 ev-0044 → 变更提案 ev-0051 → G2 重签 by 张三"）。
  - `impact <target>`：正向走 `implements` / `depends_on`（"改 AC-003 影响哪些卡与 commit"）。
  - `render [--since]`：mermaid。
  - `lint`：refs 的 target 必须可解析（事件 id / 文件#锚点 / routing 规则 id）；边类型 ∈ 封闭集。
- `/retro` 的 `metrics.py` 增加从 trace 边算的两个指标：**逃逸缺陷 → caused 链的深度与终点层**（回答"为什么门没拦住"）、**变更提案 → supersedes 的 AC 数**（契约返工率）。
- 失败报告模板的"已排除的可能"段由 `trace.py why` 预填候选。

**不做什么**：不上 Neo4j / cognee / 任何图数据库；不做 GraphRAG；不把 dos.yaml / PSL 搬进图（它们是知识层，已有自己的文件与 verify）。
这是 context graph 三义中最窄的一义——**决策迹**——用 jsonl + 200 行 Python 足够。

**验收**：fixture 归档上 `trace.py why AC-003` 输出 ≥ 3 跳链；`lint` 拒绝未知边类型与悬空 target；`metrics.py` 新指标在 fixture 上有值。

### 方案 G · review-loop 专项（用户点名）

对照业界 review-loop 结论（agentpatterns evaluator-optimizer / self-review loop、SWE-Review、Osmani、CodeRabbit）：

| 业界结论 | review-loop 现状 | 动作 |
|---|---|---|
| 评估者与修复者分离 | 可选隔离 agent（triager / fixer / verifier）✔ | 无 |
| 编译态终止 + 轮次 / 线程预算 | `done` / `round` / `strike` ✔ | 无 |
| 回帖先于 resolve；resolve 只在两种场景 | ✔ | 无 |
| **自审 2–3 轮后收益见顶，剩余发现写进 PR 让人看** | `/pr` 无预审；`/pr-review` 是 reviewer 侧工具 | `/pr --pre-review [--rounds 2]`：建 PR 前用 `pr-reviewer` agent（新上下文，跨供应商优先）审 diff，最多 2 轮修复；**存活的发现写进 PR body "Known issues"**（verify_pr.py 校验该段存在当 `--pre-review` 用过）。Osmani 数据：自审减少约 1/3 往返 |
| **Reviewer sycophancy** | 无度量 | 证据日志加 `verdict_distribution`；方案 E 的 tune 算 `sycophancy_suspect` |
| 收敛 ≠ 正确 | 合法不收敛（REJECT 悬而未决停在 exit 20）✔ | 无 |
| 早停：无新发现 | 只有 `MAX_EMPTY_WATCHES` | 证据日志层面加 `no_new_threads_streak`；连续 2 次 watch 有活动但零新线程且全部线程终态 → 提前调 `done`（不改 pr-poll.sh，在 SKILL.md 判据里加一条） |
| 触发绑定原生原语 | bash sleep | 方案 D |
| 环契约声明 | 无 | 方案 B（`loops.yaml#review_loop`） |
| bot 线程 strike 减半 | ✔ | 无 |

`review-loop` 保持 `disable-model-invocation: true`——它在公开 PR 上回帖、resolve，是 LangChain L2 里"人当 grader"的那种环，启动权必须在人。

---

## 4. 明确不做的（防止被词汇带跑）

1. **不换运行时**：不引入 LangGraph / Google ADK / Microsoft Agent Framework。skill + 脚本就是运行时；graph.yaml / loops.yaml 是声明。
2. **不建知识图谱**：context graph ≠ knowledge graph（puppyone、Srinivasan 都强调）。只做决策迹（方案 F），不碰 dos.yaml / PSL 的存储形态。
3. **不重命名 skill** 为 `loop-*` / `graph-*`（design-notes：保留上游名，内部引用不断）。
4. **不新增节点**：PSL/TASK 分叉、六审查扇出、三道人签中断是仅有的"真实边界"（AI Builder Club："every node must do work a loop couldn't"）。方案 A 只是把已有节点写成数据。
5. **不让任何门或合并自动化**：`--autopilot` 免的仍是逐步确认，不是门；Osmani："Build the loop. Stay the engineer."
6. **不把 pr-poll.sh 重写成 hook**：它已在 vana-builder 实跑过；只补触发绑定文档与 `check-clean`。
7. **不在本提案里重写 ratchet 的 Step 1–5**：那是已登记的六格归位 TODO，与本提案正交。

---

## 5. 分期与版本

| 期 | 内容 | 行为变化 | sdlc 版本 | 涉及 skill 版本 |
|---|---|---|---|---|
| **P1 声明** | 方案 A（graph.yaml + verify_graph + graph next/render）、方案 B（loops.yaml + verify_loop + `loops` 子命令）、方案 D 的 triggers.yaml + triggers.md | 无（只加数据、只读子命令、文档） | 0.2.0 → **0.3.0** | sdlc 0.1.0→0.2.0；review-loop / implement / ratchet / acceptance-fleet patch（加"环契约"引用段） |
| **P2 编译** | 方案 C（指纹历史 / oscillation / plateau / impossible + R14–R16）、方案 D 的 `check-clean` + Stop hook 模板、方案 G 的 `/pr --pre-review` 与早停判据 | 有：`fail` 判定更严；`/pr` 多一个可选门 | → **0.4.0** | sdlc minor；pr minor；review-loop minor；routing.yaml 版本 1→2 |
| **P3 迹** | 方案 F（trace.jsonl + trace.py + metrics 新指标 + 失败报告预填） | 有：账本双写 | → **0.5.0** | sdlc minor；retro minor |
| **P4 爬山** | 方案 E（`/tune` skill + tune.py + apply_proposal.py；ARCHITECTURE 六闭环） | 新 skill | → **0.6.0** | 新 skill 0.1.0；retro patch（接线） |

每期：`eval/smoke.sh` 追加期望；`gate.json` 保持 `static_only`，直到有一次真实 L2 运行。三处版本同步（SKILL.md / plugin.json / marketplace.json），
`chore: bump sdlc to vX.Y.Z with …` 单独提交。

---

## 6. 诚实的风险与优先级判断

- **最大的缺口不是任何一个方案，而是 fix_list 里的 L2**：sdlc 从未在真实需求 / 真实 PR 上跑过一遍。业界最强的共识
  （"the verifier is the bottleneck"、"收敛 ≠ 正确"）意味着：**P1 之后、P2 之前，先用现有六个环跑一个真实 TASK 轨需求**，
  拿到第一份 trace，再决定 P2–P4 的参数（方案 C 的阈值、方案 E 的统计口径都需要真实数据校准，否则是在 fixture 上调尺子）。
- 方案 A 有"数据与代码谁是源"的分叉风险：P1 用互相断言回避，P2 结束前要拍板（倾向 graph.yaml 为源，`advance` 读它）。
- 方案 F 的双写增加一处可能不一致：靠"trace 是证据不是控制状态"原则兜底，`trace.py lint` 进 smoke。
- 方案 E 最容易变成"自动调参"——封闭 target 集 + 永不 apply + 人审 PR 三道约束缺一不可。
- 词汇本身在快速漂移（graph engineering 三义并存、"context graph" 被 puppyone 明确标为歧义）；提案里用的每个词都在 §1 定了义，
  代码与文档里只用 sdlc 自己的词（环 / 层 / 门 / 指纹 / 账本 / 迹），业界词只出现在本文与 design-notes 的借鉴段。

---

## 7. 来源

Loop engineering：Addy Osmani《Loop Engineering》（addyosmani.com/blog/loop-engineering）；IBM Think《What Is Loop Engineering?》；
codecentric《Loop, Harness, Context Engineering: The Terms Explained》；LangChain《The Art of Loop Engineering》（四层：Agent / Verification /
Event-Driven / Hill-Climbing）；Aishwarya Srinivasan《Loop Engineering: The Missing Discipline》（Ng 三尺度）；AI Builder Club《Loop Engineering
Guide (2026)》；arXiv 2607.00038《Stop Hand-Holding Your Coding Agent》；arXiv 2607.01641《When Agents Do Not Stop》；arXiv 2607.06065
《SWE-Review》；arXiv 2604.25850《Agentic Harness Engineering》；agentpatterns.ai《Agent Self-Review Loop》《Convergence Detection》；
Addy Osmani《Self-Improving Coding Agents》；Anthropic Engineering《Effective harnesses for long-running agents》；Claude Code Docs
《Keep Claude working toward a goal》（code.claude.com/docs/en/goal）；ADTmag 2026-07-01；CodeRabbit《What is Loop engineering?》。

Graph engineering：Aishwarya Srinivasan《Graph Engineering Explained》；puppyone《What Is Graph Engineering for AI Agents? Execution Graphs,
Context Graphs, and Loops》；AI Builder Club《Graph Engineering Guide (2026)》；Flowtivity《From Loops to Graphs》（类型边六种、成本盈亏点）；
LangChain《3 Years of Graph Engineering with LangGraph》；cognee《Agent Memory: From Decision Traces to Predictive World Models》；
Neo4j《Introducing Create Context Graph》；Atlan《What Is a Context Graph?》。
