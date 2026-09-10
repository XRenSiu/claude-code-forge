---
name: ai-dlc
description: >-
  补引擎自己给不出的三个缺口：跨会话的生命周期状态（SKILL.state 式的充分统计量——脚本校验
  迁移，引擎只提议，历史进只增不删的账本）、失败按层归因回流而不是"塞回实现层再试一次"的
  路由表 + 分层预算 + 指纹终止（X2），以及三道只能人签的门（G1 世界裁决 / G2 判据冻结 /
  G3 例外复核）的不可跳过绑定。效果：一句需求或一个 issue → 双轨判定 → issue → 分支 →
  done_when 冻结 → 任务卡 → 按卡实现 + 提交 → PR → review 跟进 → 合入归档 → 逃逸缺陷登记，
  每一步的产物要么能被机器检，要么被一道门挡住。Use when: "走一遍完整开发流程" / "从需求到
  合入" / "aidlc" / "按流水线做这个需求" / "帮我把这个 issue 做完提 PR" / "resume AI-DLC" /
  "ship this feature end to end" / "run the lifecycle"。NOT for: 只想提交一次 commit（/commit）、
  只想发 PR（/pr）、只想审别人的 PR（/pr-review）、只想盯一个已有 PR 的评论（/review-loop）——
  单点动作直接用对应 skill，进流水线反而慢。前置：git 仓库内、gh 已认证、python3。
argument-hint: "<需求一句话 | 需求文件路径 | #issue> [--track psl|task] [--resume <slug>] [--autopilot] [--dry-run]"
version: 1.1.0
user-invocable: true
# 只能由人显式调起：它会建 issue、开分支、发 PR、自动回帖——都是公开且部分不可逆的动作，
# 不能因为对话里出现"需求""流程"就被模型自行调起。它是编排者，没有别的 skill 依赖它。
disable-model-invocation: true
---

# AI-DLC — 一条流水线，每一步能被机器检或被门挡住

本文件只写引擎给不出的东西：生命周期的形状（Σ）、每个阶段"做完了"怎么判（φ）、脚本拥有的
状态与门（γ）、原语的存在性（Π）。**怎么走、先后、如何并行是你（引擎）的份额——下面的顺序
只在它是依赖顺序或不可逆顺序时才出现，不是流程规定。**

## 缺口（Control + Judgment + Knowledge）

deletion 测试：撤掉本 skill，让引擎"把这个需求做完提 PR"。它会直接改代码、写一条 commit、
`gh pr create --fill`，验收判据从未被写下（更谈不上冻结），测试失败就在实现层重试到上下文
耗尽，review 评论被当指令照抄，合入后的问题无处登记。缺口真实存在，且三类都有：

- **γ**：状态不在引擎记忆里而在文件里；三道门不可跳过；失败按层回流而非原地重试；
- **φ**：每个阶段的完成判据（下表）——大多能机械检；机器不可判的残差声明路由到人；
- **Σ**：生命周期的依赖结构、两条轨道、邻居 skill 的产物形状。

## 世界（Σ）：生命周期的形状

参考 *Spec Loop v1.2 × done_when Pipeline*（2026-09-04 对账）。上半段建世界，下半段收敛交付，
横切三条。本插件是**下半段的交付主干**；上半段与契约/测试生成是可选邻居，缺席不阻塞。

| 阶段 | 产物 | 承载 | 为什么在这个位置（依赖 / 不可逆） |
|---|---|---|---|
| intake | 需求原文 + slug | 你 | — |
| track | `psl` / `task` | /issue 的双轨判据（DOS 闭包失败 = 客观触发） | 形态未定的需求先建世界（U 段），否则交出"技术正确、产品错误" |
| U1/U2 世界（仅 PSL 轨） | `PSL-<名>.md` | /psl（本插件） | 世界是形态的定律；`verify_psl.py` 过门 |
| U3 推导产物（仅 PSL 轨） | `derived/{dos-proposal.yaml, workflow.md, form-draft.md, divergence.md}` | /psl-derive（本插件） | 先推三样再谈代码；每条形态决策 ← PSL-ID；N 次推导取分歧集 = G1 议程 |
| G1（仅 PSL 轨） | `g1-record.md` | **人**（`gate g1` 要求 `world.derived_dir` 存在） | 唯一能拦"正确的错误"的门；否决必须归因（推错了 / 规律错了） |
| X1 本体（任一轨，有存量代码时）**一次性、仓库级** | 项目目录里的 `dos.yaml` + `decisions.md` + `agent-map.md` + `invariants/`，**全部进 git** | /dos-extract · /invariant-extract（本插件） | 闭包检查与卡的 dos_slice 的解析源；应然本体（dos-proposal）与现状本体对账在 G1 记录里做。它在 issue **之前**：`/issue --dos` 的闭包是"客观触发 PSL 轨"那条判据的全部依据，没有本体时它不是失败也不是通过，是**没算**。`aidlc_state.py repo` 报落地状态，`sizing.yaml.repo_assets` 说每档要求到哪一级 |
| issue | GitHub issue（TASK 雏形：EARS + AC v2 + 假设台账 + 依赖 DOS） | /issue | 没有 issue 就没有 `Closes #N`；AC 在这里第一次被写下 |
| branch | `<type>/<issue>-<slug>` | 你 | 不在 main 上做事 |
| contract | `done_when.yaml`（+ `contract.yaml` 条件触发） | /donewhen-extract（AC 优先）或 /acceptance-spec（EARS spec.md 形态），都在本插件 | 判据契约，方案盲写；阈值溯源、happy/unhappy 配对、矛盾与覆盖两检；S2.5 自对抗留痕给 spec-gaming。**REQ 粒度须能按 ≤ 40k 的卡切分**——L4 的"REQ 一卡一主 + ≤ 40k"是反压，读集超 40k 的 REQ 在这里按分区拆最便宜，G2 之后要走变更提案 |
| G2 | `.done_when.lock`（stage g2） | **人**签，`lock_done_when.py sign --stage g2`；`advance g2` 先跑 `validate_done_when_v2.py` | 签完就锁：冻结的是判据不是测试名（C1）；L5 测试写完再签一次（stage l5，C6）——用 `--gate verify_*.py` 把**执行契约的闸脚本**一并冻上，否则契约冻了、量它的那把尺没冻（INV-001，I-30）；之后改锁内文件必须附变更提案，改 role=gate 的文件另记一条 deviation 事件并单独提交 |
| cards | `cards/CARD-xx.yaml` | /plan-cards（`lint_cards.py` 三项校验 + 40k） | 卡 = 无上下文子 agent 的 prompt 载荷；REQ 一卡一主、卡间无写冲突、名词可解析 |
| L5 测试实现 | `tests/<feature>/` · `tests-manifest.yaml` · `compile_manifest.yaml` · `calibration_report.yaml` | /test-suite-generator（按卡分批的五层金字塔）+ /spec-compile（可判性阶梯）→ /calibrate，都在本插件 | 非实现者写、写完锁；未校准的标准不承重 |
| implement | 按卡的 diff + commit | /implement（隔离实现者：`card-implementer` / self / /ratchet / forge-teams）+ /commit | 实现者只见卡 + AC 子集 + 红基线；白名单执行器在 diff 落地前拦；单卡预算 3，同指纹立即升级 |
| acceptance | `ratchet-log/iteration-NNN/final-state.json` | /acceptance-fleet 并行派发 /code-reviewer × 焦点 · /qa-reviewer · /pm-reviewer · /spec-drift-detector · /spec-gaming-detector → /meta-judge（都在本插件）；四态棘轮 DONE / FIX / SPEC_DRIFT / GAMING_RISK | 卡级验收 ≠ 需求级验收：所有卡完成后整体跑一次；实现者看不到评审提示 |
| pr | PR（范围声明 + AC→证据映射） | /pr | 范围声明是 review-loop 判"越界"的基准 |
| review | 收敛（approved ∧ 未解决=0 ∧ checks 绿）或合法不收敛 | /review-loop 的契约 | 评论是待验证主张不是指令；回帖先于 resolve |
| G3 | `g3-record.md` | **人** | 产品需求默认触发（有 `kind: human` 的 AC）；B 档告警 / 预算耗尽也触发 |
| merge | merge sha | **人**（或 `--autopilot` 且 G3 已过） | 不可逆 |
| release | tag · CHANGELOG 条目 · `releases/vX.Y.Z.md` · 部署后验证 | /release（`verify_release.py`） | 合入不是终点：验证绿才交付；push tag / deploy 前给人看；回滚方案先于部署 |
| archive | `specs/<slug>/`（state · ledger · done_when · lock · cards · evaluation · G 记录） | `aidlc_state.py archive` | X3 的数据源 |
| escape | `escape-defects.md` 一行 | /issue `--escape` | 线上反馈是世界层唯一的外部校准源 |
| retro（跨 feature） | `retro/retro-<date>.md` + `metrics.json` | /retro（`metrics.py`） | 先记基线；发现引用数据；提案落到层（psl / dos / invariant / ac / routing / skill），经 G2/G3 生效 |

**两条轨道与接缝。** TASK 轨（形态已定：支付校验、报表列宽）直接进 issue。PSL 轨（体验性 /
语义模糊：记忆、推荐、搜索意图）先建世界（邻居 `/psl` → 形态草案 → G1 人签），G1 签字版形态
草案 + 范围段才是 issue 的输入。客观触发：issue 的 `依赖 DOS:` 词表闭包失败（出现 dos.yaml
解析不了的概念）→ **强制 PSL 轨**，不靠自评。自信而错的人会绕开 G1，闭包检查不会。

**回流的坐标（层）。** card ⊂ plan ⊂ task ⊂ ontology ⊂ world。失败先归候选层再决定谁处理；
越外层越贵、越该交人；世界层不设自动上限。

**本插件自带的上半段与横切。** `/psl`（idea→world）→ `/psl-derive`（U3 推导 + 分歧集）→ G1；
`/dos-extract`（code→world，`dos.yaml` 给闭包检查）、`/invariant-extract`（□ 常驻不变量）——
这两条是**仓库级、一次性**的，做一次全组共用（下面「X1 仓库级制品」一节）；
`/donewhen-extract`（L3 契约）→ `/spec-compile`（L5 编译成 fitness fn / eval_case / 评判程序）→ `/calibrate`
（标准的标准：mutation score / agreement / holdout / 隔离）。它们各自有 `verify_*.py` 预门与 `接线` 段。

**本插件自带的下半段验收线（引自 done-when-pipeline v1.1.0）。** `/acceptance-spec`（EARS 契约）→
`/test-suite-generator`（五层金字塔）→ `/acceptance-fleet` 派发 `/code-reviewer` · `/qa-reviewer` · `/pm-reviewer` ·
`/spec-drift-detector` · `/spec-gaming-detector` → `/meta-judge`（四态棘轮）；`/ratchet`（跑到达标为止的卡）。
它们的 SKILL.md 末尾都有 "Wiring in AI-DLC" 段说明与状态机、路由表、三档、G3 的接法。

**可选邻居（缺席不阻塞）。** `forge-teams` / `pdforge`（实现侧的并行 / TDD 执行器）。有则用，无则由你自己或
`/ratchet` 做实现；账本里记 `executor`。

**关于用户的 Σ。** "做完"在用户口中常指"PR 发了"；本 skill 的 done 是 archive。用户说
"先别合"= 停在 review 之后等人；"直接合"≠ 跳过 G3，G3 有 human AC 时仍要人签。

## X1 仓库级制品（进 git，全组共用一份）

`dos.yaml` / `decisions.md` / `agent-map.md` / `invariants/` **不是这一次运行的产物**，是这个仓库的。
它们该在**项目目录里、提交进 git**：本体是团队的共同词表，一份没进版本库的词表不是"有本体"，
是"你有本体"。`.aidlc/` 是 per-run 运行时状态（`init` 自己会警告它没被 gitignore），放这里同时错两次
——换个 feature 找不到，换个人更找不到。

```
aidlc_state.py repo --scope plugins/<pkg>   # 在不在 · 进没进 git · 这一档要求到哪一级 · 缺了怎么补
aidlc_state.py repo --path dos              # 只打印命中的路径，给 `--dos $(…)` 这类接线用
aidlc_state.py init --scope plugins/<pkg>   # 记进 world.scope，之后每次发现都带上它
```

**monorepo：一个 package 一份本体。** `--scope` 先在那个目录里找，找不到再回落到仓库根——
所以"一份仓库级 `agent-map.md` + 每个 package 一份 `dos.yaml`"是可表达的。把只覆盖某一个
package 的本体放在仓库根，是拿 scope 撒谎（dos-extract 的 edge case：一个 package 一个
bounded context）。本仓库自己就是这个形状：根上一份 agent-map，`plugins/ai-dlc/dos.yaml` 一份。

**你不手 set 这些路径。** `init` 用 `scripts/repo_assets.py` 在项目目录里按候选序发现它们
（`--scope` 的 package 目录 → 仓库根 → `docs/` → `ontology/`，`.aidlc/` 排最后且命中即告警），
并用 `git ls-files` 核对它们进没进版本库，然后写进 `world.*`（含 `world.scope`）。
每个 slug 手抄一遍仓库级事实，抄错一份没人会发现。

**缺席时下游是"未检"不是"通过"**——这是这一节存在的全部理由：

| 消费者 | 有本体 | 没有本体 |
|---|---|---|
| `/issue --dos` 的词表闭包 | 缺词 → reject + 强制 PSL 轨（**客观触发，不靠自评**） | 一条 `closure unchecked` 的 flag，放行 |
| `lint_cards.py --dos` 的 `dos_slice` | 名词不在本体 → reject | 一条 info |
| `verify_vocabulary.py` | B 档告警计入账本 | exit 3 = **未检** |
| `agent-map.md` → `slice_agent_map.py` → `card_context.md` | 实现者拿到"测试怎么跑、禁区在哪、陷阱有哪些" | 零行，自己猜 |

要求分档写在 `assets/sizing.yaml` 的 `repo_assets`（`verify_sizing.py` L8 核它）：
S 档 optional（三行修复上一次全仓库本体提取，成本高到没人愿意用，而**一条被绕过的流水线抬不高
任何人的下限**）· M 档 recommended（doctor warn）· L 档与 PSL 轨 dos 是 **required**，
`advance issue` 拦得住。绿地仓库没有存量代码、本体无处可抽，走
`advance issue --force --reason greenfield`——那是一条记进 waivers 与账本的豁免，不是一片空白。
`/issue` 与 `/plan-cards` 在这两档要带 `--require-dos`（没给 `--dos` 时自动发现，找不到才拒）。

## 状态（γ：脚本拥有控制状态，你拥有账本）

- **`.aidlc/<slug>/state.json`** 是这次运行的充分统计量（schema：`assets/state.schema.json`）。
  **你不手改它。** 一切迁移经 `scripts/aidlc_state.py` 校验后合并：`advance <stage>` 检查前置
  条件（对着状态检，不对着你的说法检）；不满足 → 拒绝并列出缺什么；`--force --reason` 可豁免，
  但豁免被记成 waiver（不是无声跳过）。
- **`.aidlc/<slug>/ledger.md`** 只增不删：每次失败、被拒的修复、路由决定、门的裁决、豁免。
  产物可回滚（代码、卡、PR），判据和失败记录不回滚（WikiSkill 非对称回滚）。下一轮读它，
  就不撞同一堵墙。
- **`.aidlc/<slug>/trace.jsonl`** 是账本的机器可读伴生：每行一个事件，`refs` 带类型边（`caused_by` / `decided_by` /
  `supersedes` / `implements` / `references` / `depends_on` / `rejected_alternative`，封闭集）。它是证据不是控制状态——
  损坏不影响预算与迁移。`scripts/trace.py why AC-003` 回答"这条 AC 为什么改、谁签的、上游是哪次失败"；`impact` 回答改它
  波及哪些卡与 commit；失败报告的"已排除的可能"由它预填。
- **`assets/graph.yaml` / `assets/loops.yaml` / `assets/triggers.yaml`** 把图、环、触发写成数据：`verify_graph.py` 五条 lint
  （写范围有界 · 每个圈有环契约 · 评估者→实现者只带 fix_prompt · 人节点有恢复绑定 · 扇入有 merge）；`verify_loop.py`
  （generator ≠ verifier · stop 四键 · budget 可解析）；`aidlc_state.py graph check` 让 ORDER 与 graph.yaml 互相断言。
- **上下文纪律（SKILL.state）。** 交给隔离子 agent 的只有：一张卡 + `aidlc_state.py show`
  的摘要 + 该卡的 AC 子集。不给整段对话历史，不给评审 skill 的提示词（实现者看不到评判者的
  小抄——训练期信息隔离在这里的形态）。
- **中断恢复**：`/ai-dlc --resume <slug>` 从 state.json 的 `stage` 继续；账本告诉你上次为什么停。

## 判据（φ）：每个阶段"做完了"怎么判

| 阶段 | 机械可判（脚本） | 残差（判给人 / judge） |
|---|---|---|
| track | 闭包失败 → 强制 psl | 语义份额是否主导（/issue 双轨判据） |
| 世界 / 推导 / G1 | `verify_psl.py` 六层齐全无步骤；`verify_derived.py` 四文件 + 决策全带 PSL-ID + DOS 提案过 `verify_dos.py` + 不造实体 | 世界抓得对不对；分歧按哪个版本定（G1 人签） |
| contract（起草） | `verify_done_when.py`：模糊量词有阈值、happy 有 unhappy、无矛盾、覆盖 | 阈值是否反映 KPI（judge） |
| L5 标准 | `verify_compile.py` 不往上路由 / 非 example-only / 评判维度二元带证据；`verify_calibration.py` 四不可破 | 变异族对不对、参考解是否代表性 |
| issue | `verify_issue.py` 过：无模糊量词、happy 有 unhappy 孪生、observe 非文件路径、范围四项非空；`--require-dos` 时闭包必须真的算过（未检 = 拒）；`advance issue` 检 required 那级的 X1 制品 | AC 是不是这次最窄的可证伪条件 |
| contract / G2 | `validate_done_when_v2.py` 过（schema 2、AC 齐、existence 只留边界、forbidden_paths 含 tests/**）；`.done_when.lock` 存在且哈希匹配 | 判据对不对（人签） |
| cards | `lint_cards.py` 三项 + 上下文 ≤ 40k | 卡是否自包含 |
| implement | 每次 commit 过 `verify_commit.py`（白名单、锁、secrets）；单卡测试过 | 实现是否走了捷径（spec-gaming 邻居） |
| acceptance | `final-state.json` 存在；`/qa-reviewer` 真跑测试；`/spec-gaming-detector` 硬命中 = A 档；`meets_done_when` 由脚本比对阈值得出，不由评估 agent 宣布 | human AC → G3；`/meta-judge` NEEDS_HUMAN |
| pr | `verify_pr.py` 过：范围声明、Closes、验证证据、AC 映射、体量 ≤ L | 描述是否诚实 |
| review | `pr-poll.sh done` exit 0 或 10；合法不收敛 = 有 REJECT 悬而未决时停在 20 并汇报 | 争议线程的对错 |
| release | `verify_release.py` 过（changelog ↔ tag ↔ notes 一致、Rollback 非空、bump 与提交一致）；verify-cmd 绿 | 回滚方案是否真能执行 |
| merge / archive | `merge.sha`；`release.done` 或 `skipped_reason`；归档目录结构固定、`metrics.py` 读得出 | — |

**收敛检测（routing.yaml v2，`fail` 命令自动判）：** 每个 key 存最近 6 次指纹。同指纹连续 2 次 = repeat；周期 2–3 的往复
（A B A B）= **oscillation** → 派生信号 `oscillation_detected`（R14，plan 层：在相似解之间震荡是方案层的权衡）；`--score` 连续 3 次
不超过历史最佳 = **plateau** → R15（plan 层，允许一次探索性重写再升级）；评估者判"在当前契约下不可能" → `impossible_under_contract`
（R16，task 层，走变更提案；只接受 `routing.impossible_reporters` 里的 `--by`，实现者报被拒）。任一升级都置 `pending.failure_report`，
`check-clean` 与 Stop hook 模板据此拒绝结束 session，直到 `report --path` 清掉。

**失败机制（触发 → 症状 → 分支）：**

- 卡测试失败且指纹与上次不同 → `fail --signal card_test_fail --card CARD-xx` → 引擎再试一次；
- 同卡同指纹再现 → 脚本判 `escalate`（不等 3 次）→ 改卡（plan 层），不是再试；
- diff 溢出白名单 → `verify_commit.py` 拒；`fail --signal whitelist_overflow` → 停机交人；
- 被锁文件出现在 diff → 有 `change-proposal-*.md` 同 diff → 放行并计 task 回流；无 → 拒；
- PBT/测试连续 3 次以与 REQ 一致的反例失败 → 任务层（改 AC），**不许继续 patch 代码**；
- 反例引用 DOS 不变量 → 本体层；与 PSL 规律冲突 → 世界层（重开 G1）；
- review 线程往返达上限 → 冻结该线程交人，其余照常；
- 任一层预算耗尽 → 写失败报告（`assets/failure_report.md`：候选层 + 证据 + 已排除 + 建议回退）→ G3。

## 门（γ：三道人签 + 两个自动）

- **G1**（PSL 轨必过）：三问 checklist（实体对不对 / 有无技术对产品错 / 每条决策从哪条规律推出）
  写进 `g1-record.md`；否决必须归因 `derivation_error | rule_error`（脚本拒绝无归因的 reject）；
  PSL 轨至少一项外部证据（原型走查 / 用户验证）。
  **解释规则可追加、不触发变更提案**：裁决之后出的解释写进 `g1-interpretations.md`
  （模板 `assets/g1_interpretations.md`），该文件**不进 G2 锁**——解释自己的裁决是 G1 的合法职能，
  它不改签字版形态草案的任何一个字节（`lock_done_when.py sign` 直接拒绝把它锁进去，I-60）。
  锁的是签字版 `form-draft.md` 与记着它 sha256 的 `g1-record.md`；要改结论就是新的一次 G1，不是解释。
  分界线是**签字版有没有变**：补签（G2 回流引发的形态追加）改了签字版，写在 `g1-record.md` 的补签节里，
  该撞锁、该走变更提案；解释一个字节都没改，不该。
- **G2**（必过）：人确认判据、指派 human AC 的裁决人（`judge ∈ {product, design, tech}`），
  `lock_done_when.py sign --by <人>`。之后锁定检查进 A 档。
- **G3**（默认触发）：产品需求默认触发；纯内部质量需求且 B 档无告警时不请求人（`gates.g3.required=false`
  须显式 set 并留痕）。输入是失败报告与 human AC 清单，不是原始日志；假设台账逐条处置。
- **自动门**：`lint_cards.py`（进 implement 前）；整体验收（进 pr 前）。

`advance` 的前置条件把这些门编译成不可跳过——不是"你记得跑"，是"不跑就 advance 不了"。

## 回流路由（X2）：`assets/routing.yaml` 是数据不是散文

`aidlc_state.py fail --signal <signal>` 读它：给出候选层、处理者、动作、分层计数、预算余量、
指纹重复次数、是否升级。**你不覆盖脚本的 escalate 决定**；你可以在失败报告里改判候选层，
但那是提案，确认权在人。预算按轨道分（PSL 轨 task 回流 2，TASK 轨 1；单卡 3 两轨相同）。

## 原语（Π 的存在性——不叙述调用顺序）

- `scripts/aidlc_state.py` — init / show / set / advance / gate / card / fail / report / check-clean / graph check|next|render /
  loops / ledger / archive（`--help`）。`fail` 多了 `--score` 与 `--by`；`loops` 一屏看六个环的预算消耗；`check-clean --as-hook`
  是 Stop hook 的出口（模板 `assets/hooks/stop-clean-state.json`，不自动安装）。
  v1.1.0 新增 `repo`（X1 仓库级制品：在不在 · 进没进 git · 这一档要求到哪一级 · 怎么补）。
  v0.12.0 新增：`size --from-issue|--early`（早定档 + 飞行中重定档）、`plan`（启动前的有效规模）、
  `doctor`（装置健康度，建议性、从不阻断、不进 `advance` 的前置条件——会阻断的 doctor 就是第四道门）、
  `note` / `notes --for-gate`（解释日记与门禁仪式）、`autonomy`（自治阶梯）、`card --status skipped --reason`。
- `scripts/repo_assets.py` — X1 仓库级制品的**发现**（候选路径序）与 **git 核对**（`git ls-files`）。
  `aidlc_state.py` 的 `init` / `doctor` / `repo` / `prereqs("issue")`、`verify_issue.py --require-dos`、
  `lint_cards.py --require-dos` 共用这一份候选表——第二份候选表迟早与真的那份分叉（同 `graph check`）。
- `scripts/verify_sizing.py` — 体量网格的 lint（八条，L8 核 `repo_assets` 的键与档位）。L7 直接 `import aidlc_state` 用**真的那份** `next_allowed`
  把每一档的剩余路径走一遍：自己写第二份迟早与真的那份分叉，而分叉出来的那份会说"网格没问题"（同 `graph check`）。
- `scripts/lock_done_when.py` — `sign --stage g2|l5` / A 档 `verify`（exit 0 / 1 reject / 2 changed_with_proposal）。
- `scripts/verify_graph.py` / `scripts/verify_loop.py` / `scripts/trace.py why|impact|render|lint` — 图 / 环 / 迹的 lint 与查询。
- `assets/graph.yaml`（52 节点 · 67 边）· `assets/loops.yaml`（六个环）· `assets/triggers.yaml`（每个环绑到 `/goal` `/loop`
  Stop hook `/schedule`）· `assets/routing.yaml` v2（R14–R16）。
- `../plan-cards/scripts/lint_cards.py`（L4）、`../retro/scripts/metrics.py`（X3）、`../donewhen-extract/scripts/validate_done_when_v2.py`（契约 v2 校验，`advance g2` 自动调用）、`convert_v1_to_v2.py`（acceptance-spec v1 → v2 骨架）、`../release/scripts/verify_release.py`（L8）。
- 子 skill 的原语各自在其目录：`issue/scripts/verify_issue.py`、`commit/scripts/verify_commit.py`、
  `pr/scripts/verify_pr.py`、`review-loop/scripts/pr-poll.sh`、`pr-review/scripts/post_review.py`；
  上半段与横切：`psl/scripts/verify_psl.py`、`psl-derive/scripts/verify_derived.py`、
  `dos-extract/scripts/{inventory,verify_dos}.py`、`invariant-extract/scripts/verify_card.py`、
  `donewhen-extract/scripts/verify_done_when.py`、`spec-compile/scripts/verify_compile.py`、
  `calibrate/scripts/verify_calibration.py`；验收线：`acceptance-spec/scripts/validate_done_when.py`、
  `test-suite-generator/scripts/{derive_counts,gen_existence,check_verbatim_names}.py`、
  `spec-gaming-detector/scripts/compute_score.py`、`meta-judge/scripts/compute_confidence.py`。
  review 阶段**读 `../review-loop/SKILL.md` 并按其契约执行**（它 `disable-model-invocation`，
  用户显式启动 /ai-dlc 即视为授权跟进 review）。
- 模板：`assets/`（卡、账本、G1/G3 记录、失败报告（含收敛证据段）、变更提案、逃逸缺陷、Stop hook）。
- 邻居：`../tune/scripts/tune.py`（hill_climb 环：读归档与 pr-watch 出 harness 参数提案，`apply_proposal.py` 只出 diff）。

`<skill_dir>` = 本文件所在目录的绝对路径；插件根 = `<skill_dir>/../..`。脚本一律 `python3`/`bash`
显式调用，不 chmod（目录可能只读）。

## 三个旋钮：广度 / 深度 / 测试量（`assets/sizing.yaml` v2）

一套流程不分任务大小是 spec 工具的通病（Böckeler 2026 对 Kiro / spec-kit 的批评）。三行 bug 修复
走完 issue → 契约 → G2 → 卡 → 六审，成本高到没人愿意用，于是整条流水线被绕过——**一条被绕过的
流水线抬不高任何人的下限**。

v0.12.0 起这是三个**正交**旋钮（借鉴 AWS AI-DLC 2.0，见 `../../docs/reports/aidlc-gap-2026-09-07.md`）。
它们的强制力不同，文档不假装它们一样：

| 旋钮 | 是什么 | 谁强制 |
|---|---|---|
| 广度 | 跑哪些阶段（`stages:` 网格） | `next_allowed` / `prereqs` 按网格放行；`verify_sizing.py` 八条 lint |
| 测试量 | 验多少（`test_strategy`） | **下界**：`derive_counts.py --strategy`，低于地板 exit 4 |
| 深度 | 每个阶段产出多细（`depth`） | **只是声明**给 skill 读的输入。没有脚本能判"这份文档够不够细"——写在这里是为了不假装它是闸 |

```
aidlc_state.py size --from-issue issue-body.md --early --commit   # 还没 diff：只能推向 L 或留在 M
aidlc_state.py size --base origin/main --commit                   # 有 diff 之后：这里才够得到 S
aidlc_state.py plan                                               # 这次跑几个阶段、几道门、跳了什么、为什么
```

推导规则是数据（六条，按顺序求值）：PSL 轨 / 有 human AC / AC ≥ 8 / 改动 ≥ 15 文件 → L；
AC ≤ 2 且改动 ≤ 3 文件且 TASK 轨 → S；其余 M。输入只有四个可数的量，**没有形容词**。
AC 数从 `verify_issue.py` 的 `acceptance_stats` 或契约里读，files 从 `git diff` 数——
**数字和它的来路由同一次读产生**，issue 没过 `verify_issue.py` 就拒绝取数。

**极性不可反转（三重）**：① `init` 时 `size = M` / `size_source = default`；② skip 只认
`size_source ∈ {derived, derived_early}`，`set intake.size=S` 把来源打回 `manual`，一扇门也打不开；
③ `never_skippable` 里的阶段任何档都不能跳——**三道门在里面**，广度旋钮拧不掉门（不变量 6）。
漏填得到的是较严的路径，**一个靠遗漏就能打开的门不是门**。

**早定档给不出 S，是规则本来的形状而不是额外的限制**：S 的唯一入口需要 files，而缺一个量的规则不会
命中。`needs:` 把这件事写成声明，`verify_sizing.py` L6 核它与 `when:` 一致——从注释变成可证的性质。

**飞行中重定档只能改尚未开始的阶段**：落在当前阶段身后的 skip 一律丢弃并记 `size_recompose`。
一次已经付过的 G2 不会因为重定档被追认为"其实不用签"。

每个被跳的阶段写一条有类型的 `size_exemption` 进账本（带那条 skip 的 why），`/retro` 按档分桶数逃逸
缺陷——分档对不对，由下一次逃逸缺陷回答，不由拍脑袋回答。

## 解释日记（v0.12.0：`notes.md` 四格）

账本记的是**已经发生的错**（失败 / 回流 / 裁决 / 豁免），记不到"规格含糊处当场做了什么选择"。
`divergence.py` 抓的是事前 N 份隔离草案的分歧，抓不到实现中途的默认填充。那条通道是这个：

```
aidlc_state.py note --kind interpretation|deviation|tradeoff|open_question --text "…"
aidlc_state.py notes --for-gate g2            # 门禁仪式：逐字念，不改写、不筛选
aidlc_state.py note --promote n-0001 --to project --by <你>
```

四格的分法照抄 AWS AI-DLC，因为它分得对：前三格是可固化的知识，**Open questions 明确不晋升**——
它是研究项不是规则，脚本硬拒。作用域只有 `project`，**没有 team / org 通道**：提升是人在仓库之间
做的事，不是这个脚本的权限。晋升状态记在 `state.notes.promoted`，所以晋升不用回头改写日记的任何
一行——日记只增不删。

**下轮生效**：`init` 读 `.aidlc/learnings/project.md` 并记下哈希与条数。跑动中晋升的规则不影响本轮——
你前面批准过的门对应的是当时那套规则集合，框架不在跑动中抽掉地基（同不变量 13）。

## 自治阶梯（v0.12.0）

```
aidlc_state.py autonomy --level ask_each|auto_until_gate|auto_until_failure --by <你>
```

整个流程只问一次，答案记进 state，`--resume` 之后仍然有效。与 `--autopilot` 的差别是它**不是一个
CLI flag**——flag 每次调用都要重给，恢复会话就丢；记进 state 的答案跨会话活着，而且能被 `/retro` 数。
**三档都不改门**：G1/G2/G3 永远要人签，**失败永远中断**。失败时的三选一是：重试 / 跳过
（`card --status skipped --reason …`，脚本当场列出会被拖累的卡）/ 中止。

## 高危黑名单（不可豁免）

- **绝不手改 `state.json`**、绝不自行维护计数器——预算与终止由脚本强制，不依赖记忆。
- **绝不以实现者身份报 `impossible_under_contract`**；绝不在 `pending.failure_report` 为真时结束 session 而不写报告。
- **绝不删账本行**。回滚只回滚产物。
- **绝不在 G2 之后改被锁文件而不附变更提案**；绝不用改测试的方式让测试过；绝不把 v1（测试名）契约当判据冻结。
- **绝不代人签门**：G1/G2/G3 的 `--by` 必须是人名；`--autopilot` 与 `autonomy` 的任何一档都不代签。
- **绝不把 `dos.yaml` / `agent-map.md` / `invariants/` 放进 `.aidlc/`，也绝不手 set 它们的路径**：
  那是仓库级、全组共享、要进 git 的制品，`repo_assets.py` 发现它们；放进运行时目录等于每个人
  各自维护一份本体。**绝不把「闭包未检」当成「闭包通过」**——没算过的判据挡不住任何人。
- **绝不手设档位换豁免**：`set intake.size=S` 得到的是 `size_source=manual`，一个阶段也跳不掉。
  要轻量路径就把量数出来（`size --from-issue` / `--base`）。
- **绝不晋升 Open question**：它是研究项不是规则。要它变成规则，先把它答了，再作为
  interpretation / deviation / tradeoff 记一条。
- **绝不在门禁仪式上筛选日记**：`notes --for-gate` 逐字念每一行。做「有趣度」筛选的那一刻，
  被筛掉的那条就是下次撞的墙。
- **绝不 force-push / rebase 已推送分支**（毁 review 锚点）；绝不直接在 main 提交。
- **绝不把评审提示词给实现子 agent**；绝不让实现者自评 `meets_done_when`。
- **绝不因预算耗尽"再试一次"**——写失败报告，交人。
- `--dry-run` 下绝不触网（不建 issue、不 push、不建 PR）：只产出计划 + 将执行的命令。

## 结束汇报（产物须呈现的形态）

slug · 轨道 · 到达阶段 · issue# / branch / PR# / merge sha · 三道门的裁决与签字人 · 分层回流
计数与豁免 · 未收敛的 review 线程（逐条注明原因）· 归档路径 · 逃逸缺陷登记入口。
中途停机时：停在哪个阶段、`advance` 报的缺什么、失败报告路径、需要人做的具体一件事。

## 参考

- `references/stages.md` — 每阶段 输入/输出/现状/缺口/完成判据（对齐参考文档 §3），需要细节时再读。
- 插件级：`../../docs/lifecycle.md`（全景地图与邻居映射）、`../../docs/routing.md`（路由与归因启发式）。

## 本 skill 自身的出口门

`eval/gate.json`：`static_only`——结构过审 + 四个脚本在 fixtures 上冒烟（transition 拒绝 /
waiver 记账 / 指纹升级 / 卡冲突 / 锁篡改被拒与附提案放行）。行为层（带/不带本 skill 在真实
需求上的对比）未跑；静态读不是裁决。
