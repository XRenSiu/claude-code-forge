# 原语与资产索引

这份文档回答一个问题：**手上这件事，有没有现成的脚本；有的话它检什么、退出码什么意思。**

它存在的理由是一次机械盘点。2026-09-06 数过一遍：8 个脚本、26 个资产在当时的六份文档里一次都没出现过。
一个自称「每一步产物要么被脚本检、要么被门挡」的插件，却没有一处能查到脚本清单。
使用者只能靠读源码或猜。

`eval/smoke.sh` 有一条期望盯着这份文档。任何 `skills/*/scripts/` 下的脚本或 `skills/*/assets/` 下的资产，
如果不在这里出现，冒烟就红。文档漂移在这个插件里是可以被机器发现的事。

> 文风残余（`humanlint --genre reference`）：标题密度 23/1k、最长连续平句 5。
> 两项都是索引类文档的固有形态——正文短、表多、表格行被当成等长句子。按 humanize 的交付契约，
> 改过一轮仍 flag 就交付并列出残余，不继续磨。

## 怎么读退出码

退出码分三类。别混。

| 类别 | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| 预门（`verify_*` / `validate_*` / `lint_*`） | 过（可能带 flag） | 拒（产物不合格） | IO 或用法错误 | 不用 |
| 结构闸（`verify_structure.py`、`verify_review_complete.py`） | 全部声明的都求值且满足 | 有一条被违反 / 显式否定 | IO 或用法错误 | 声明了但无法求值，**不是通过** |
| 术语传感器（`verify_vocabulary.py`，B 档） | 计入的发现 ≤ 阈值 | 超阈值（告警，不是一票否决） | IO 或用法错误 | 没有本体 / 词表为空，**未检不是通过** |
| 状态机与生成器（`aidlc_state.py`、`tune.py`） | 命令成功 | 前置条件不满足 | 用法错误 | 不用 |

flag 不等于 reject。预门过了但带 flag，意思是「机器判不了这条，路由给人」。
把 flag 当没看见，等于把该人判的东西默认判过。

---

## 脚本

### 脊柱与状态（`skills/ai-dlc/scripts/`）

| 脚本 | 干什么 | 关键退出码 |
|---|---|---|
| `aidlc_state.py` | 生命周期状态机：`init` / `show` / `set` / `advance` / `gate` / `card` / `size` / `plan` / `doctor` / `repo` / `note` / `notes` / `autonomy` / `fail` / `waive` / `report` / `check-clean` / `graph` / `loops` / `ledger` / `archive`。**状态由它拥有，不手改** | 0 成功 · 1 前置不满足（`doctor` 的 1 = 有 error 级发现，它从不阻断门禁）· 2 用法 |
| `lock_done_when.py` | 契约的两段锁：`sign --stage g2\|l5` 算文件哈希并记签字人 | 0 · 1 拒 · 2 IO |
| `trace.py` | 决策迹查询：`why <AC-id>` / `impact` / `render` / `lint` | 0 · 1 · 2 |
| `verify_graph.py` | `graph.yaml` 的五条 lint（写范围有界 / 圈必须归环 / 评估者→实现者只带 fix_prompt / 人节点有恢复绑定 / fan_in 有 merge） | 0 · 1 拒 |
| `verify_loop.py` | `loops.yaml` 的环契约（generator ≠ verifier、stop 四键齐） | 0 · 1 拒 |
| `verify_sizing.py` | 体量网格的八条 lint：阶段名在 ORDER 里 / never_skippable 覆盖三道门 / 没有一档绕过它 / 每条 skip 有 why / **兜底档一个阶段也不跳（极性）** / `needs` 与 `when` 一致 / 每一档的剩余路径 `next_allowed` 真的放行（直接 import 真的那份，不重实现）/ **`repo_assets` 的键与档位在封闭集里且每档都有一条要求** | 0 · 1 拒 · 2 用法/IO（**没有 3**：网格是自带资产，读不到是错误不是「未求值」） |
| `repo_assets.py` | X1 仓库级制品在不在（候选路径序：仓库根 → `docs/` → `ontology/`，`.aidlc/` 最后且命中即告警）、进没进 git（`git ls-files`）。被 `aidlc_state.py init/doctor/repo/prereqs`、`verify_issue.py --require-dos`、`lint_cards.py --require-dos` 共用——一份候选表，不是六份 | 0 齐全且都进了 git · 1 有缺失 / 未 tracked / 位置不共享 · 2 用法/IO |

`aidlc_state.py` 的子命令里最容易被漏的三个：

- `size`：按 `assets/sizing.yaml` 的六条规则推体量档，输入只有四个可数的量（改动文件数、AC 数、human AC 数、轨道）。
  `--commit` 才写进 state。缺省是 M，S 的豁免只认 `size_source=derived`。
- `repo`：**第一次把 /ai-dlc 带进一个仓库时先跑这条**。X1 的仓库级制品（`dos.yaml` / `decisions.md` /
  `agent-map.md` / `invariants/`）在不在、进没进 git、这一档要求到哪一级、缺了怎么补。它们是
  **一次性、仓库级、全组共用一份**的制品：做一次，之后每个 slug 由 `init` 自动发现，不必手 set 路径。
  缺席时下游是**未检**不是通过——`/issue` 的闭包会退回自评，卡的 `dos_slice` 无人解析。
  L 档与 PSL 轨 `dos.yaml` 是 required，`advance issue` 拦得住；绿地走 `--force --reason greenfield`。
- `check-clean --as-hook`：会话结束前拒绝在有待写失败报告或脏卡时收工。配 Stop hook 用，模板在
  `skills/ai-dlc/assets/hooks/`，不自动安装。

### 世界（R0，仅 PSL 轨）

| 脚本 | 所属 skill | 干什么 | 关键退出码 |
|---|---|---|---|
| `verify_psl.py` | psl | PSL 六层齐不齐、Workflow 里有没有 Step N 式步骤、验收是不是「问 X → 返回 Y」、规律有没有稳定的 PSL-NNN id | 0 · 1 拒 |
| `verify_derived.py` | psl-derive | 推导产物：每条形态决策必须引用一个 PSL-ID；N 次隔离推导的分歧集必须在 | 0 · 1 拒 |

### 契约（R2）

| 脚本 | 所属 skill | 干什么 | 关键退出码 |
|---|---|---|---|
| `verify_issue.py` | issue | issue body 的预门：模糊量词无阈值拒、缺 unhappy 孪生拒、observe 写文件路径拒；`--dos` 下词表闭包失败给 `force_track: psl` | 0 · 1 拒 · 2 IO |
| `verify_done_when.py` | donewhen-extract | done_when 卡的语义出口（矛盾检 + 覆盖检） | 0 · 1 拒 |
| `validate_done_when_v2.py` | donewhen-extract | **契约 v2 的唯一校验器**，编译在 `advance g2` 里。含 `constraints.structure` 的形状检查 | 0 · 1 拒 · 2 IO |
| `convert_v1_to_v2.py` | donewhen-extract | acceptance-spec 的 v1 契约 → v2 骨架 | 0 · 2 IO |
| `divergence.py` | donewhen-extract | **N 份隔离草案的分歧集**：按 (req, ears_type, observe) 对齐，报五类分歧，每条带要问用户的话 | 0 分歧在阈值内 · 1 必须澄清 · 2 用法 |
| `validate_done_when.py` | acceptance-spec | v1 契约的出口（历史形态） | 0 · 1 拒 |

### 本体与不变量（R1 / X1）

| 脚本 | 所属 skill | 干什么 | 关键退出码 |
|---|---|---|---|
| `verify_dos.py` | dos-extract | dos.yaml 预门：>7 对象拒、UI/impl 后缀名拒、关系引用未声明对象拒、`open_questions` 空拒 | 0 · 1 拒 |
| `inventory.py` | dos-extract | 演绎扫描：名词 / 动词频次表，给分类判断当材料 | 0 |
| `count_terms.py` | dos-extract | 文档通道的机械原语：词频统计 | 0（除非文件读不了） |
| `dos_closure.py` | dos-extract | **「一个 DOS 词能不能被解析」的唯一定义**；`verify_issue.py`、`lint_cards.py`、`verify_vocabulary.py` 都 import 它 | 库，非命令行 |
| `verify_vocabulary.py` | dos-extract | **跨制品术语传感器（B 档）**：契约 / 卡 / spec / issue / PR body 的**散文**里出现、`dos.yaml` 解析不了的领域名词，每条带 file:line 与本体里最近的可解析邻居；另报本体里无人使用的词（弱证据，不计入）。`--out` 缺省**不落文件**（B 档随手跑，不该在工作区留残留），要 facts 显式给 `--out`，要机器读用 `--json` | 0 过 · 1 超阈值 · 2 IO · **3 没有本体 = 未检**（`--require-ontology` → 1） |
| `reconcile_dos.py` | dos-extract | 应然本体（psl-derive 的提案）↔ 现状本体逐条对账 | 0 · 1 有冲突 |
| `verify_agent_map.py` | dos-extract | **仓库地图的预门**：`--probe` 逐条真跑命令并比对期望退出码；陷阱必须有来路；占位符拒 | 0 · 1 拒 · 2 IO |
| `verify_card.py` | invariant-extract | 不变量卡：无 provenance 拒、hard 必须 propose、◊ 混进 □ 拒 | 0 · 1 拒 |

### 计划与实现（R4 / R5）

| 脚本 | 所属 skill | 干什么 | 关键退出码 |
|---|---|---|---|
| `lint_cards.py` | plan-cards | 卡的三项校验（REQ 全覆盖且一卡一主 / 卡间无写冲突 / **`dos_slice` 结构化字段**的名词可解析）+ 上下文 ≤ 40k。卡的**散文**（title / notes）归 `verify_vocabulary.py`，两者不重叠 | 0 · 1 拒 · 2 IO |
| `slice_agent_map.py` | plan-cards | **按卡切仓库地图**：命令全给，目录 / 禁区 / 陷阱只给与 `allowed_files` 相交的行 | 0 · 1 缺节 · 2 IO |
| `verify_commit.py` | commit | 落地前三道闸：卡白名单溢出、G2 锁哈希、secrets 与调试代码 | 0 · 1 拒 · 2 git/IO |
| `commit.sh` | commit | 过闸后提交的薄封装 | — |

### 标准与测试（R3）

| 脚本 | 所属 skill | 干什么 | 关键退出码 |
|---|---|---|---|
| `derive_counts.py` | test-suite-generator | 从契约推每层该有多少测试 | 0 |
| `gen_existence.py` | test-suite-generator | 存在性测试的生成器（**不是闸**，没有拒绝路径） | 0 |
| `check_verbatim_names.py` | test-suite-generator | 测试名与契约 manifest 逐字一致 | 0 · 1 不一致 |
| `capture_red_baseline.py` | test-suite-generator | **红基线**：实现前跑一次，记录哪些测试是红的；实现者拿它自证红→绿 | 0 · 1 基线不是红 |
| `verify_compile.py` | spec-compile | 可判性阶梯的产物检（fitness fn / eval_case / 评判程序） | 0 · 1 拒 |
| `verify_calibration.py` | calibrate | **标准的标准**：mutation score / Krippendorff α ≥ 0.80 / holdout / 隔离，四不可破 | 0 元闸过 · 1 拒 |

### 验收（R6）

| 脚本 | 所属 skill | 干什么 | 关键退出码 |
|---|---|---|---|
| `verify_structure.py` | qa-reviewer | **A 档的结构闸**：圈复杂度（增量与绝对值）、重复块、依赖方向，只看本次 diff | 0 过 · 1 违反 · 2 IO · **3 声明了但无法求值** |
| `next_iteration.py` | acceptance-fleet | 从上一轮 ratchet-log 推下一轮的派发参数 | 0 · 1 上一轮不自洽 |
| `qa_facts.py` | acceptance-fleet | 把 qa-reviewer 的报告投影成**测量值**，供 spec-drift 比对 | 0 · 1 不是 qa 报告 |
| `verify_review_complete.py` | acceptance-fleet | **审查完成度闸（fleet S1.5，meta-judge 之前）**：每份 fleet 产物必须自带 `review_complete:` 标记，且 `findings_count` 与实到发现条数一致；`--clear` 在重派前把陈旧产物移进 `stale/`（移不删，且只在给定目录内动手） | 0 全部到齐且完成 · 1 显式声明没跑完 · 2 IO / 用法 · **3 缺文件 / 解析不了 / 缺标记 / 数目不符——不是通过**（`--require-complete` 把 3 变 1） |
| `pick_evaluators.py` | acceptance-fleet | **跨供应商分配**：探测可用供应商，按同源盲区排名分配，分不到就留 `same_vendor_caveat` | 0（无论是否跨供应商）· 2 配置读不了 |
| `compute_score.py` | spec-gaming-detector | 六种 RHD 模式的 gaming_risk_score（0–10） | 0 |
| `compute_confidence.py` | meta-judge | 多源 / 跨供应商发现的置信度加权 | 0 |
| `post_review.py` | pr-review | findings.yaml → GitHub review（**永不 approve**） | 0 · 1 · 2 |

### 交付与学习（R7 / R8）

| 脚本 | 所属 skill | 干什么 | 关键退出码 |
|---|---|---|---|
| `verify_pr.py` | pr | PR body 的产物序 + 体量分级（XL 必拆）+ 锁文件改动需附提案 | 0 · 1 拒 |
| `pr-poll.sh` | review-loop | 零 token 阻塞等待；预算与终止谓词编译在脚本里 | 0 收敛 · 30 预算耗尽 |
| `verify_release.py` | release | changelog ↔ tag ↔ notes 一致、回滚先于部署、验证绿才算交付 | 0 · 1 拒 |
| `metrics.py` | retro | X3 导出：lead time / 回流分布 / G1 拦截率 / human AC 占比 / 逃逸率 / 豁免数 / **按体量分桶** | 0 |
| `tune.py` | tune | 环的参数提案（封闭 target 集）：routing 预算、指纹阈值、MAX_ROUNDS、隔离等级、**跨供应商分配**、fix_list | 0 |
| `apply_proposal.py` | tune | 把提案变成 diff / patch —— **只出 diff，从不自动应用** | 0 · 1 |

### 插件自身的评估（`eval/`）

| 脚本 | 干什么 |
|---|---|
| `eval/smoke.sh` | 全仓脚本的冒烟期望；`--only <ERE>` 过滤，`--mutate <file> <old> <new>` 做变异自检（基线必须先绿，否则拒绝出结论） |
| `eval/effect/run.py` | 行为层对照的 `prepare` / `collect`；隔离断言、副本收分、mtime 判污染 |
| `eval/effect/score.py` | 汇总；样本 < 5 或差距在噪声带内**拒绝下结论**；两个维度分开判 |
| `eval/fixtures/anchor_crosscheck.py` | 证据锚点的独立交叉核对（不共用被测实现） |

---

## 资产（数据与模板）

先是数据。脚本读它，改它就改行为。

| 资产 | 谁读 | 是什么 |
|---|---|---|
| `ai-dlc/assets/routing.yaml` | `aidlc_state.py fail` | 回流路由表：信号 → 层 → 处理者 → 动作；分层预算；收敛检测阈值 |
| `ai-dlc/assets/sizing.yaml` | `aidlc_state.py size|plan|advance`、`verify_sizing.py` | v2：六条推导规则（带 `needs`）+ **`stages:` 广度网格** + `never_skippable`（三道门在里面）+ 每档的 `depth` / `test_strategy` + `recompose` 约束 + 预算覆盖 |
| `ai-dlc/assets/graph.yaml` | `verify_graph.py`、`aidlc_state.py graph` | 52 节点 / 67 边；节点带 `reads` / `must_not_read` / `writes` / `authority` |
| `ai-dlc/assets/loops.yaml` | `verify_loop.py`、`aidlc_state.py loops` | 六个环的契约：level / timescale / generator ≠ verifier / stop 四键 |
| `ai-dlc/assets/triggers.yaml` | 人 | 每个环绑到哪个原生触发（`/goal` `/loop` Stop hook `/schedule`） |
| `acceptance-fleet/assets/evaluators.yaml` | `pick_evaluators.py` | 供应商声明与探测命令；每个槽的同源盲区排名 |
| `donewhen-extract/references/done-when-v2-schema.yaml` | 人 + `validate_done_when_v2.py` | **契约的唯一 schema**；含 `constraints.structure` |
| `dos-extract/assets/dos_template.yaml` | 人 | DOS 的 12 节结构 |
| `invariant-extract/assets/invariant_card.yaml` | `verify_card.py` | 不变量卡的具名字段 |
| `donewhen-extract/assets/done_when_card.yaml` | `verify_done_when.py` | done_when 卡的具名字段 |
| `plan-cards/assets/card_template.yaml` | `lint_cards.py` | 任务卡的具名字段 |
| `spec-compile/assets/compile_manifest.yaml` | `verify_compile.py` | 可判性阶梯的产物清单 |
| `calibrate/assets/calibration_report.yaml` | `verify_calibration.py` | 校准报告的形状 |
| `pr-review/assets/findings_template.yaml` | 人 | 发现的三档归位形状 |
| `tune/assets/harness_proposals_template.yaml` | `apply_proposal.py` | 提案的具名字段 |

然后是模板。这些人填，脚本检产物。

| 资产 | 用在哪 |
|---|---|
| `issue/assets/issue_template.md` · `bug_extra.md` · `escape_extra.md` | issue body 的段落序；bug 与逃逸缺陷各多一段 |
| `ai-dlc/assets/g1_record.md` · `g1_interpretations.md` · `g2_record.md` · `g3_record.md` | 三道人签的门的记录形状 |
| `ai-dlc/assets/failure_report.md` | 升级时给 G3 的失败报告（人不看原始日志） |
| `ai-dlc/assets/ledger_template.md` | 账本的行形状 |
| `ai-dlc/assets/change_proposal.md` | 改锁内文件必须同 diff 附的变更提案 |
| `implement/assets/card_context.md` | **实现者能看到的全部输入**的形状（含 agent-map 切片） |
| `dos-extract/assets/agent_map_template.md` · `decisions_template.md` · `docs_extraction_prompt.md` · `dos_amendment_template.md` | 仓库地图 / 判断审计轨 / 文档扫描 / 本体修订 |
| `psl-derive/assets/workflow_template.md` · `form_draft_template.md` · `divergence_template.md` | U3 的三样推导产物 |
| `invariant-extract/assets/cross_territory_promotion_template.md` | 跨领地不变量的提升 |
| `pr/assets/pr_template.md` | PR body 的产物序 |
| `release/assets/changelog_entry_template.md` · `release_notes_template.md` | 交付产物 |
| `retro/assets/retro_template.md` | 复盘报告形状 |
| `acceptance-fleet/assets/round_diff_template.md` | 轮次间差异 |
| `issue/assets/escape_defect.md` | 逃逸缺陷登记行 |
