# G3 记录 — sdlc-ring-audit

> 本文件是 G3 这道门的签字记录。判决在文末的 YAML 块，理由在正文。
> 依 `done_when.yaml` 的 rules 第 4 条：human AC AC-005-a / AC-006-a 只在这里裁，从不自动通过。

---

## 签字性质

| 项 | 值 |
|---|---|
| 门 | `G3` |
| 签字人 | `g3-judge` |
| signer_kind | `delegated_agent` — **代签（delegated），不是人签** |
| 授权 | user instruction 2026-09-05: '需要人审核的地方，请你弄一个子agent代替我审核一下' |
| 渲染规定 | 本记录与 `audit.yaml` / `AUDIT.md` 中一律渲染为「代签（delegated）」（F-15 / PSL-006） |
| 判定基准 | 分支 `docs/1-sdlc-ring-audit`，PR #2（draft） |

### 这道门的机械强度（必须先说这个）

裁 AC-006-a 之前先把针对本门自身的发现读进来（g3-input 第 13 项）：

- `sdlc_state.py` 的 `cmd_gate` 对 **G3 pass 不检任何输入**。对照 G1 pass 要求 `world.derived_dir` 是存在的目录、
  G2 pass 要求 `lock.path` 是存在的文件（`sdlc_state.py#L384-L392`），G3 那一支是空的。
  三道门里唯一一道**盖章不看纸**的门。→ gap `R6/newly_identified/control/g3-pass-has-no-input-precondition`、提案 `P-R6-01`。
- `signer_kind = delegated_agent` 的 `--authorization` **只是自由文本**（`sdlc_state.py#L394-L395`），
  没有任何一处核对这段授权是否真的来自人。→ gap `R6/unenforced_rule/control/gate-signer-must-be-human`、提案 `P-R6-11`；
  `dos.yaml` R008「三道门只能人签」的 `enforced_by` 是 `user_workflow`。

**因此：机制无法区分本签字与一段伪造的授权字符串。** 本记录的效力全部来自下面列出的、可被任何人重跑的复现，
不来自"门已盖章"这个事实。这是本次代签最大的限度，写在最前面而不是脚注里。

### 本判官**亲自复现**了什么（不采信记录的自述）

全部在 shipping 分支上跑，非引用他人结论：

| 复现 | 结果 | 与记录是否一致 |
|---|---|---|
| `check_audit.py` 全量（带 `--psl` + 5 个 required agent） | **exit 0** · rings 10 · parts_total 42 · 全部谓词 0 · `calibration_twin_recorded: true` | 与 `run_evidence.check_runs[0]` 逐字一致 |
| 同上 `--variant delete-ring:R6` | **exit 1** · `ring_missing: R6` · rings 9 · parts_total 31 · orphan_gaps 18 · required_parts_missing 2 | 与 `check_runs[1]` 的 observed **逐字一致** |
| `replay_card_commits.sh` | **exit 0** · `ok: true` · card_commits **15** · **card_commits_touching_audited_dirs 0** · rejected 0 · non_card_touching **8** | 卡数与 non_card 数已漂移（记录为 14 / 4）；**承重不变量 0 未变** |
| `render_audit.py audit.yaml -o <scratch>` 后与 `AUDIT.md` 比对 | **sha256 完全相同** `962cc2f6…d016d4` | AUDIT.md **未被手改**，是 audit.yaml 的确定性投影 |
| 解压 `iteration-003/impl-snapshot.tar.gz` 与工作树逐字节 `cmp` | **10 / 10 相同，0 differing**（head 移动到 79b4736 后再验一次仍 0） | 我裁的就是评审过的那份字节 |
| 读隐藏集 `holdout_run.json` + `holdout_manifest.yaml` | variants 10 · hits 6 · misses 4；4 个未命中**逐一对应** `known_gaps.yaml` 的 **KG-01..04** | 一致（不引隐藏变体正文） |
| 39 条 proposal.source 是否可解析（g3-input 第 16 项） | **39 / 39 可解析**（落在 42 个 Assessment id 或 73 个 Gap id 内），**0 悬空** | 把"人读替代"升级成了机械证据 |
| `git diff --stat 0be2770^..a2deb83 -- <三个被审目录>` | **空** | 与 `git_diff_stat.output: ''` 一致 |
| 同一命令对**当前 HEAD** | **非空**（5 files / 14 insertions / 5 deletions） | 已由 cr-005 披露（其记的 11 insertions 又已增长） |
| 四条无 footer 提交与首个 Card 提交的先后 | `git merge-base --is-ancestor` 判定：**四条全部早于** `0be2770` | 证实 mf-002 的错标属实 |
| `verify_commit.py` 单 ref / 空 range / `A..` 三种形态 | 单 ref **exit 2**、空 range **exit 2**、`A..` 正确解析（`#L94` 用 `is not None`、`#L206` 右端缺省取 HEAD） | cr-001 / cr-004 / fix-verifier 两条 NEW_ISSUES 的修法**确在分支上** |
| `bash plugins/sdlc/eval/smoke.sh` | **196 passed, 0 failed** | pr-body Verification 段仍写 193（见条件 C-4） |
| `gh pr view 2` | draft · MERGEABLE · `statusCheckRollup: []` · reviewDecision 空 | 证实 Known issues G 段「checks_green 是空转」属实 |

### 本判官**没有**验证什么

- **没有**独立重跑 instrument mutation（0.767 / 23-30）与 fixture mutation（24/24）——采信 `calibration_report.yaml` 与 holdout 记录。
- **没有**逐字复核 42 个 Part 全部 126 个维度的证据锚（`file:line` / `gate_json:` 共 299 条）是否句句属实；
  只做了跨 7 个环 7 个 Part 的 **71 个内容片段**的投影保真抽查（0 丢失）与全量结构解析。
- **没有**重跑六个评审者（fleet）——采信 `iteration-003/fleet-outputs/` 与 meta-judge 的合并，但**自己重跑了** meta-judge
  据以判定的三条机械事实（两次 check 运行 + 回放），这正是 mf-013「exit 0 来自自报」要求的。
- **没有**做行为层对比运行（带 skill / 不带 skill）。全部 42 个 Part 无一到 `verified`，本门也不提供 verified 证据。
- **不是人。** 见上文「这道门的机械强度」。

---

## AC-005-a 判决 — `ui:AUDIT.md#ring-tables`（judge: tech）

### **pass**

依 `tests/ring-audit/checklist_G3.md`（l5 锁内，本轮未改）14 个框逐条核。核法：对 `AUDIT.md` 全量解析出
**42 个 Part 行 + 33 个 missing 行**（与首部「10 环 · 42 配件 · 73 缺口 · 33 处登记为缺少」自洽），逐列判，非抽样印象。

| # | 框 | 判 | 证据 |
|---|---|---|---|
| 1 | 每个 Part 行给出 Gap 原子集合 | ✅ | 42/42 第 3 列非空；原子取自 Knowledge/Capability/Judgment/Control 闭集（PSL-016） |
| 2 | 独占 Artifact（或 `role gate \| orchestrator`） | ✅ | 42/42 第 4 列非空；`audit.yaml` 中 42 个 Part 全部有 `artifact` 字段；`role gate` × 5（五个 human_gate）、`role orchestrator` × 2 |
| 3 | Gate：script 写「闸」、human 写「门」 | ✅ | `check_audit.py` 报 `script_gates_rendered_as_door: 0`；全文渲染成「门」的只有 `G1`/`G2`/`G3`（各自计 1/2/2 次），无一处 script 写成门 |
| 4 | Loop（`loops.yaml#<id>` 或 null） | ✅ | 42/42 合法：26 个 `null` + 16 个 loop id（lifecycle 5 · review_loop 4 · card_retry 2 · acceptance_ratchet 2 · hill_climb 2 · ratchet 1） |
| 5 | deletion 写出具体错误产物或漏检 | ✅ | 42/42 有 `撤掉后：` 句；长度 min 102 / 中位 218 / max 322 字符 |
| 6 | 不接受「流程会断」一类泛语 | ✅ | 对 42 条逐条扫「流程会断 / 走不下去 / 会断 / 无法继续 / 流程中断 / 不能继续 / 跑不下去」：**0 命中**。最短的三条也都点名具体错误产物（如 psl：「交出一个 created_at 字段加日历筛选器，产物技术正确、产品错误」） |
| 7 | naming 先写来路再写贴合 | ✅ | 42/42 匹配 `(authored\|adopted) → **(fits\|misfit)**`；19 adopted / 23 authored |
| 8 | misfit 给建议名且更贴产物或位置 | ✅ | 唯一 misfit `tune` → 建议名 `harness-tune`；理由成立：产物是 `harness-proposals-<date>.yaml`、位置是 `hill_climb` 环，而 target 恰是封闭集，"调什么"正是原名唯一没说的东西 |
| 9 | misfit 标「不重命名」 | ✅ | `tune` 行含 **不重命名**；`check_audit.py` 报 `rename_true: 0`（42 个 Part 无一处 rename=true） |
| 10 | `pr-review` vs `code-reviewer` 带 Artifact 对照与裁决 | ✅ | SDP-04：`pr-review` → `.sdlc/review/*.yaml`、`github:review`；`code-reviewer` → `ratchet-log/iteration-NNN/code-review-*.yaml`；共同产物**无** → **`distinct_exits`**，边界问题交 `P-R6-08` |
| 11 | `donewhen-extract` vs `acceptance-spec` 同上 | ✅ | SDP-01：共同产物 `done_when.yaml` → **`merge_candidate`**，F-05 三条件**三缺二**（只满足 (a)），双方互指，交 `P-02-01` |
| 12 | missing 行带来源标签 | ✅ | 33/33：lifecycle_blank 9 · newly_identified 13 · unenforced_rule 11 |
| 13 | 每条 missing 带 necessity | ✅ | 33/33（全部 `necessary`） |
| 14 | 每条 missing 带 deletion 一句 | ✅ | 33/33 有 `撤掉 / 不补它：`；长度 min 78 / 中位 194 / max 423；泛语扫描 **0 命中** |

**14 / 14 全部 ✅ → AC-005-a pass。**

### 附：投影保真（AUDIT.md 有没有丢东西）

AC-005-a 观察的是 `AUDIT.md`，而 F-12 规定 yaml 为准。两项独立证据表明投影无损：

1. **字节级**：用 `render_audit.py` 重新渲染 `audit.yaml` 到临时目录，与仓库里的 `AUDIT.md` **sha256 完全相同**。
   AUDIT.md 没有被手工编辑过，是确定性投影。
2. **内容级**：跨 R0 / R2 / R5 / R6 / R7 / R8 / spine **7 个环 7 个 Part**，把 yaml 侧的
   `artifact` / `deletion_test` / 三维 evidence.ref / shortfall / note / suggested_name 共 **71 个片段**做规范化包含比对：
   **0 丢失**。42 个 Part id、39 条 proposal id 全部在 md 中出现。
3. 疑似重复对表由 `render_audit.py` 从 `artifacts[]` **现算**并与登记值比对，不一致会打「登记 ≠ 现算」；
   全文该字样仅出现 1 次，且是表头解释句本身，**无一对不一致**。

### 为什么 mf-009 没有把 AC-005-a 拉下来

mf-009（三个 Part 记 `compiled` 而其产物 `checked_by` 皆空）我裁**成立**（见下文 mf-009 条），
但它不构成 AC-005-a 的 fail，理由三条：

1. AC-005-a 的 statement 与 checklist 14 框规定的是每行**给出什么**（形状与齐备），不是每个判定值我都同意；
2. F-06 的封顶规则**从未被编译进** `check_audit.py`（holdout 作者已把它标为 contract-level gap），
   本轮不存在一把冻结的尺子可以拿来判这三行"违规"——需要我先把读法**定下来**，而这正是 G3 tech 的职责；
3. 契约要求「改冻结字节的项一律 defer，不当场应用」。以 mf-009 fail 掉 AC-005-a 等于强制改字节，与该纪律冲突。

**报告并未隐藏它**：这三行自己就把矛盾渲染在同一行里（产物列写着「（无闸 → 封顶 declared）」而 implemented 列写着
`compiled`），`agent.pr-reviewer` 更带一条 `resolved_by: pending_G3` 的 adjudication 把正反两方理由都写出来。
这是**如实上报**，不是粉饰——所以裁项而不裁 AC。

---

## AC-006-a 判决 — `ui:AUDIT.md#run-evidence`（judge: product）

### **pass**（附 4 条必办条件，见「对账」）

| # | 框 | 判 | 证据 |
|---|---|---|---|
| 1 | G1 签字人 / signer_kind / 授权引用 | ✅ | `g1-judge` · `delegated_agent` · `g1-record.md#签字性质`（含授权原文） |
| 2 | G2 同上 | ✅ | `g2-judge` · `delegated_agent` · `.done_when.lock#authorization` |
| 3 | G3 同上 | ✅ **有条件** | 冻结字节里 G3 = `pending`，signer / signer_kind / authorization 均为 `—`。**这是签字时点唯一可能且诚实的状态**：要求我在自己尚未裁决的字节里先看到自己的签名，是时序上不可能的自指。三元组由本记录补齐 → **条件 C-1** |
| 4 | delegated_agent 不渲染为「人签」 | ✅ | 全部渲染为 **代签（delegated）**；小节导语直书「**本次三道门没有一道是人签**」；`check_audit.py` 报 `delegated_without_authorization_ref: 0`、`human_gates_without_signer: 0` |
| 5 | check-audit 对 audit.yaml 的 exit 0 记录 | ✅ | 完整命令（**含 `--psl`**）+ 观察值；**本判官重跑逐字一致** |
| 6 | 删环变体 exit 1 记录（`--variant delete-ring:<id>`） | ✅ | 完整命令（**含 `--psl`**）+ 观察值；**本判官重跑逐字一致**，含 orphan_gaps 18 / required_parts_missing 2 这两个连带谓词与 twin_note 的解释 |
| 7 | 缺变体记录时标 `uncalibrated`，A6 如实带出 | ✅ | 变体在场，故渲染「**本次：变体记录在场，exit 0 可作证据**」；`calibration_twin_recorded: true`。逻辑与标记方向都对 |
| 8 | Card-footer 提交对三个被审目录的 `git diff --stat`，且为空 | ✅ | 记录值在其记录 head（`a2deb83`）**经我复现确为空**；承重不变量 `card_commits_touching_audited_dirs` 在当前 HEAD 仍为 **0**（15 条 Card 提交全过） |
| 9 | 列出 `skill-issues.md` 的路径 | ✅ | 路径已列（计数 67 已陈旧，见条件 C-3；**框要求的是路径**） |
| 10 | 外部证据标 `substitute` | ✅ | 档位 **`substitute`**，`valid_for: this dogfood only` |
| 11 | `substitute` 不渲染为用户验证 | ✅ | 明写「这是外部证据的**替代品**，不是用户验证，也不是行为层的对比运行」 |

**g2-judge 条件 3–5（`failure-report-002-holdout.md`）**

| 条件 | 判 | 证据 |
|---|---|---|
| 11 项 `known_gaps` 渲染齐全 | ✅ | KG-01..KG-11 全表，逐条带 spec 出处 / expected_token / status，全部 `open → change-proposal-002` |
| holdout 摘要渲染为 delegated | ✅ | 见证人 `orchestrator` · **代签（delegated）** · `render_as: delegated` — F-15，未渲染为人的验证 |
| A6 / F-14 措辞 | ✅ | 逐字为 `instrument mutation 0.767 (23/30); fixture mutation 24/24; holdout 6/10 with 4 known gaps — never the unqualified word 'calibrated'`，是所要求措辞的超集 |
| 绝不出现无限定的 "calibrated" | ✅ | 全文 grep：出现处或为字段值 `calibrated: false`、或为空隙名 `uncalibrated-*`、或为「未过 calibrate / 未校准」。**没有一处**声称这把尺子已校准 |
| 4 个 holdout 未命中 = KG-01..04 | ✅ | 读隐藏集 `holdout_run.json` / `holdout_manifest.yaml` 亲验：4 个未命中与 KG-01（waived 无 waiver_ref）/ KG-02（proposal source 悬空）/ KG-03（重复环 id）/ KG-04（signer_kind 越枚举）**一一对应**。（依纪律不引隐藏变体正文） |

### 这一门真正的问题是「记录会不会说实话」，答案是：会

AC-006-a 判的是产品层的**如实上报**。我把自己独立发现的每一处差额，拿去比对记录**有没有先说**：

| 我独立发现的差额 | 记录有没有先说 | 方向 |
|---|---|---|
| `AUDIT.md:976` 标「自第一个 Card 提交起」，但那 4 条提交**全部早于**首个 Card 提交，该标签下真值是 **0**（我用 `merge-base --is-ancestor` 证实） | **说了** — Known issues **F / mf-002**，点名 `render_audit.py:533` 与 `AUDIT.md:976`，并直书「标签下的真值是 0」 | **自曝其短**（把自己写得比实际更脏） |
| `non_card_commits_touching_audited_dirs` 记 4、现况 **8** | **说了** — Known issues **G**，附现场重算命令，并列出七条的分类 | 自曝其短 |
| `git diff --stat 0be2770^..HEAD` 原始命令对当前 HEAD **已非空** | **说了** — cr-005 / I-79，连「5 files / 11 insertions」都写了（现已增至 14 insertions） | 自曝其短 |
| `skill_issues_count` 记 67，现 grep 得 **81** | **说了机制** — mf-005 记「67 vs 4ddb362 上 69，记录时冻结的计数」；具体数字又已增长 → 条件 C-3 | 轻微低报 |
| `statusCheckRollup` 为空、无任何 CI | **说了** — Known issues G：「`checks_green: true` 是**空转**……这与"检查通过"不是一回事，全文任何地方都不得写成后者」 | 自曝其短 |
| review 环结构性不可收敛（作者不能批准自己的 PR） | **说了** — I-69，并说明评审实质在建 PR 前已交付 | 自曝其短 |
| drift 经 `--qa-report` 读到 qa 输出，违反无串扰铁律 | **说了** — 裁为有界接受且**未打折** drift 的 11 条信号 | 自曝其短 |
| gaming 轨迹实为 [3.5, 4.0, 4.0] **持平**（非下降） | **说了** — I-72，检测器被错传基线，检测器自报了不一致 | 自曝其短 |
| card 预算 **4/3** 超支、task 预算 2/2 耗尽 | **说了** — 三次豁免记在状态与账本 | 自曝其短 |
| 42 个 Part **0 个 verified** | **说了** — 作为报告结尾的「铁律」段，而不是脚注 | 自曝其短 |

**没有发现一处我查出来而记录没先说的实质差额。** 所有陈旧数字都是「冻结字节 vs 移动分支」这一**已披露机制**的实例，
且偏差方向压倒性地是**自曝其短**——把本次运行写得比实际更脏，不是更干净。这是 AC-006-a 想要的那种记录。

另有两处正面证据值得记下：
- **PR 正文明写** `AC-005-a / AC-006-a **待 G3 代签，未通过**`，从不渲染为 passed；meta-judge 的 rule 3 也
  `outcome: triggered → effect_applied: needs-human`，未自动放行。
- **孪生是被变异检验过的**：fix-verifier 独立复核发现我方为 cr-004 写的两条 smoke 孪生是**装饰性**的
  （坏解析器照样全绿），已重建为「暂存冻结字节 + 篡改留在 range 头」并用三个历史 bug 逐个变异证明（各杀 2 / 1 / 3 条）。
  我复现了修法确在分支上（`verify_commit.py#L94` 的 `is not None`、`#L206` 的右端缺省取 HEAD；单 ref 与空 range 均 **exit 2**）。
  一次运行肯把自己写的测试判为装饰性并重做，是本 run 证据纪律的最强正例。

---

## g3-input 逐项裁决（1–20 + mf-009）

> 纪律：**改冻结字节的项一律 defer 到 change-proposal-002，不当场应用。**

| # | 事由 | 裁决 | 理由（一句） |
|---|---|---|---|
| 1 | F-06 封顶粒度（字面执行会把 `dos-extract` 压回 declared） | **accept** | F-06 按**独占 Artifact** 读，不按"该 Part 沾到的每一个产物"读：它要防的是配件为**自己的产品**索取未挣得的成熟度；无闸的副产物是该登记的缺口（已登记），不是对配件的降级。**注意此裁并不救 mf-009 那三个——它们的独占产物本身就无闸。** |
| 2 | F-16 与 `audit.schema.md` 的 disposition 枚举不一致 | **defer-to-change-proposal-002** | 片段按 schema 走是对的（数据面自洽优先）；但 `{fix_list, issue, none}` vs `{none, issue}` 两份规格必须归一，且要有谓词——现状两者都不检（= mf-013）。 |
| 3 | R010 / R017 不在 R0–R2/spine，须核四条宪法规则各至少登记一次 | **accept** | 我机械复算：R001 3 条（R5·R6·spine）、R008 3 条（R6·R7·spine）、R010 3 条（R3·R6·R8）、R017 2 条（R6·R7），合计 **11 = 全部 `unenforced_rule` 缺口数**，无落单。PSL-017 成立。 |
| 4 | naming 维 41 fits / 1 misfit，还有没有区分度 | **defer-to-change-proposal-002** | 判定不错，但**信息量近乎为零**（区分度 1/42 = 2.4%）：F-03 的"同词干即 fits"在产物本就按 skill 命名时几乎恒真。建议加第二谓词（名字有没有说出**改什么 / 产什么**，正是 `tune` 被判 misfit 的那条），或把 naming 降为 advisory。 |
| 5 | `implement` / `agent.comment-fixer` 双方 merge_candidate | **defer-to-change-proposal-002** | 双记正确、**不当场裁掉一个**正确：F-05 三条件对着 `graph.yaml` 行锚逐条判，三缺二。审计的职责是把争议产物摆上台，不是替架构改图。解决走 `P-R5-01`。 |
| 6 | `agent.comment-fixer` 的环（R5 vs R7） | **defer-to-change-proposal-002** | 记 **R5 + 双源 ring_evidence** 正确：`graph.yaml` 的 `Node.role` 是机器可读的单一真源，ARCHITECTURE §1 的归类是叙述视图。两源真的打架时并列而不调和，是诚实做法。归一走 `P-R5-02`。 |
| 7 | `agent.pr-reviewer` 判 compiled 还是 declared（`pending_G3`） | **reject compiled → declared** | 拒的闸 `verify_pr.py --pre-review` 作用于**下游投影**（PR 正文 Known issues 段），不是本 agent 的 `findings.yaml`——后者 `checked_by` 为空。**下游产物上的闸不能把上游生产者编译**，否则"被谁挡"与"挡的是不是它"就分不开了。字节改动 defer。 |
| 8 | 上游 `code-reviewer` 收编为 `pr-reviewer`，与 R6 撞名 | **defer-to-change-proposal-002** | 记为 PSL-014「收编保留上游名」的一次**受迫偏离**是对的（R6 已占用该名）。要改的是规则说法（skill 保留上游名 / agent 按产物命名），不是这次的记录。走 `P-R7-01` / `P-R6-07`。 |
| 9 | `graph.yaml` 中 `pr` 与 `human.harness-review` 的 writes 同为字面 `github:pr` | **accept** | 两个不同的 PR 共用一个字面串，是**图的源码缺陷**，不是真的 R001 双生产者；按两个 Artifact 登记 + 判 `distinct_exits` + 记 `P-R8-06` 是正解。 |
| 10 | `agent.review-triager` / `agent.fix-verifier` 的环（R6 vs R7） | **defer-to-change-proposal-002** | 与第 6 项**同根因**（review-loop 宿主的 agent 归属），同样裁法：`role=evaluator` → R6，双源并列不调和。建议与第 6 项**合并成一条提案**处理，别拆两处。 |
| 11 | 计算原语算不算闸（`meta-judge` / `spec-gaming-detector` 判 declared） | **accept** | 判得对，而且这是本片段**最有分量**的一条：除 IO 错误外无非零退出路径的脚本**拒绝不了任何东西**，`compute_score.py` 自己的收尾行把阈值交给消费者。PSL-010 的 compiled 要的是**存在拒绝出口**。⚠️ 同一条原则若一致适用，就必须把 `tune`（`tune.py` 自述"报告工具"、exit 0 恒成立）与 `agent.pr-reviewer` 一并压到 declared——这正是我裁 mf-009 的依据。R6 用了这条尺，R7/R8 没用，**不一致的是那两处，不是这里**。 |
| 12 | `meets_done_when` 的两个洞记成两个 Gap 而非一个 | **accept** | 粒度正确：两者**来源不同**（`lifecycle_blank` vs `unenforced_rule`）、**原子不同**（`capability+control` vs `control`）、**修法不同**（`P-R6-02` 写比对脚本 vs `P-R6-03` 把它移出 SETTABLE）。合成一条会掩盖"修了一个另一个仍开着"。 |
| 13 | `sdlc_state.py` 四处（G3 pass 无输入前置；代签授权只是自由文本 等） | **accept** | 已读进本门自身的判定，写在开头「这道门的机械强度」而非脚注。这是本记录**效力来源**的限定条件。走 `P-R6-01` / `P-R6-11`。 |
| 14 | 顶层 `suspected_duplicate_pairs[]` 超出 G2 冻结形态 | **defer-to-change-proposal-002** | **接受为投影辅助**：非承重（`render_audit.py` 从 `artifacts[]` 现算并会打「登记 ≠ 现算」，我验证 5 条**全部一致**），且 AC-005-a 点名要的跨卡对照任何单张卡都写不出来。形态登记（连同 `audit.schema.md` 六 vs 八注册表，mf-007/mf-008）defer。 |
| 15 | 报告底线：16 declared / 26 compiled / **0 verified**；三门两代签；外部证据 substitute | **accept**（附更正） | 底线诚实且被放在报告结尾的「铁律」段。**按我对 mf-009 的裁决，更正为 19 declared / 23 compiled / 0 verified**（字节改动 defer）。「0 verified」这一条无论如何不变。 |
| 16 | KG-02：39 条 source 由人工核对可解析，是人读替代 | **accept（已升级为机械证据）** | 我用脚本对 42 个 Assessment id + 73 个 Gap id 做闭包解析：**39/39 可解析，0 悬空**。数据面现在有机械证据；**仪器面的空隙（检查器只验非空）仍是 KG-02**，留在 change-proposal-002。 |
| 17 | run_evidence 的 replay 计数是快照 | **accept** | 现场复现：14 → **15** 条 Card 提交、4 → **8** 条 non_card，而**承重不变量 `card_commits_touching_audited_dirs` 两次都是 0**。记录对"什么会漂、什么不漂"的表述准确。 |
| 18 | 一条 adjudication `resolved_by: pending_G3` | **reject compiled → declared（本裁即为该 adjudication 的解）** | 见第 7 项。字节更新时该 adjudication 应从 `pending_G3` 改为记本记录为 resolver，不应继续挂 pending。 |
| 19 | 顶层 `unenforced_rules[]` 同为形态外的键 | **defer-to-change-proposal-002** | 与第 14 项同裁，且这条**是改进**：它把 PSL-017 的四条宪法规则登记从硬编码改成按 `evidence.ref` 现算（我复算 4/4 成立）。但 `audit.schema.md` 列六个注册表而数据与渲染器用八个，schema 必须补上（mf-007 / mf-008）。 |
| 20 | 回放范围要不要扩到 `origin/main` 以满足记录义务 | **accept 现范围；reject 扩范围的要求** | AC-007-a 的 `given` 把回放**限定在 Card 提交**上；我已证实那四条提交**全部是首个 Card 提交 `0be2770` 的祖先**，故在 AC 自己的窗口内该字段本就该是 **0**。扩到 `origin/main` 会**改变 AC-007-a 在量什么**。记录义务由 `commit-table.md` + `run_evidence.non_card_commits_touching[]`（逐 sha 列出）已经满足。**真正要修的是标签（mf-002），不是范围。** |
| **mf-009** | R6/`human_gate.G3`、R7/`agent.pr-reviewer`、R8/`tune` 记 compiled 而其每个 Artifact 的 `checked_by` 皆空 | **reject compiled → 三者均应为 `declared`；字节改动 defer-to-change-proposal-002** | 见下方专条。 |

### mf-009 专条（G3 tech 明确裁项）

**先确认事实**：我在 `audit.yaml` 上机械复算，"记 compiled 且其**全部**产物 `checked_by` 为空"的 Part **恰好是这三个**，不多不少。

**读法之争的裁决**：F-06 按**独占 Artifact** 读（同第 1 项）。但这**救不了这三个**——它们的独占产物本身就无闸：

| Part | 独占产物 | checked_by | 报告自己怎么渲染的 |
|---|---|---|---|
| `human_gate.G3` | `g3-record.md` | `[]` | 「（无闸 → 封顶 declared）」 |
| `agent.pr-reviewer` | `findings.yaml (pre-review)` | `[]` | 「（无闸 → 封顶 declared）」 |
| `tune` | `tune/harness-proposals-<date>.yaml`、`tune/*.patch` | `[]`、`[]` | 「（无闸 → 封顶 declared）」 |

**三行都在同一行里既写着「封顶 declared」又写着 `compiled`。** 支撑 compiled 的第三种读法是
"该配件的工具链里**某处**存在拒绝出口，哪怕那个出口不检这件产物"——这比 F-06 的文字**弱**，且与第 11 项裁定的原则冲突。

逐个看，三者都站不住：
- **`human_gate.G3`** 最清楚：它的 Gate 列写的是「门 `G3`」——**由它自己把关**，循环论证。而报告自己举的证据
  （`sdlc_state.py`）恰恰记着「cmd_gate 对 G3 pass 不检任何输入」，**这条证据是反对 compiled 的**。
  对照组决定性：同为 human_gate 的 `merge` 与 `harness-review`（同样「无闸无门」）**被正确地记为 `declared`**；
  `G1` / `G2` 的 `checked_by` 非空，`compiled` 名副其实。**只有 G3 破例。**
- **`agent.pr-reviewer`**：闸作用于下游投影（第 7 项）。
- **`tune`**：note 自己承认「'每条提案 9 项齐'这条判据没有编译态出口」；`apply_proposal.py` 的结构性控制约束的是
  **应用**环节，不是提案文件本身。

**裁决：三者均应记 `declared`。** 报告底线相应更正为 **19 declared / 23 compiled / 0 verified**。

**但字节不当场改**（契约纪律）。这不影响本次判决方向：更正只会让报告**更保守**，
不会把任何已通过的机械 AC 推翻（`check_audit.py` 不编译 F-06，故 exit 0 不受影响；
`implemented` 仍在三态枚举内，`boolean_implemented` / `implemented_outside_enum` 仍为 0）。

**统计：10 accept · 3 reject · 8 defer-to-change-proposal-002。**

---

## 对账 — 一个真人要在没有我的情况下签这份字，得先有什么

我是代签，不是人。下面这几件事**我做不了**，必须由人补上，否则这道门的强度就只有上文那些复现所能提供的强度：

1. **一次行为层对比运行。** 42 个 Part **无一到 `verified`**，因为全线没有"带 skill / 不带 skill"的对照。
   人要签"九环做到位了"，需要至少一条真实任务在两种条件下跑出可比产物。
   `check_audit.py` 的 exit 0 只说**这份文档形状齐全**——报告自己的「铁律」段就是这么写的，我确认这句话是对的。
2. **真外部证据。** 现在是 `substitute`（机械检查 + 代签 agent 独立读），`valid_for: this dogfood only`。
   人签需要一份不由本流水线产生的证据。
3. **一个不是本流水线造出来的读者。** 本次全部评审者、全部三道门的签字者都是 Claude；
   `isolation.json` 自述隔离是**协议级而非 OS 级**，且编排者同时撰写了评审提示。跨厂商在本机不可用（codex 二进制缺失、gemini 缺席）。
4. **把 G3 这道门自己补上闸。** 只要 `cmd_gate` 的 G3 pass 不检任何输入、`--authorization` 仍是自由文本，
   "谁签的、凭什么签"就无法机械核验——包括本次签字。这是 `P-R6-01` / `P-R6-11`。

### 必办条件（不阻断本判决，但必须在 merge 前完成）

| id | 条件 | 为什么 |
|---|---|---|
| **C-1** | 把 `audit.yaml#run_evidence.gates[G3]` 更新为 `verdict: pass` · `signer: g3-judge` · `signer_kind: delegated_agent` · `authorization_ref` 指向本记录，然后**用 `render_audit.py` 重渲染** `AUDIT.md`（确定性，不得手改） | 否则报告将永远显示 G3 `pending` 却对外称 G3 已过——那才是真的不诚实。`check_audit.py` 的 `human_gates_without_signer` / `delegated_without_authorization_ref` 两条谓词可机械验收这次更新 |
| **C-2** | 把 mf-009（三处 compiled → declared）、mf-002（`AUDIT.md:976` 的错标）、第 18 项的 adjudication 更新，一并列进 **change-proposal-002** | 都是改冻结字节的项，按纪律 defer；但必须**有去处**，不能就此消失 |
| **C-3** | 更新 `skill_issues_count`（记 67，现 `grep -c '^| I-'` 得 **81**），或在该单元格标为"记录时快照" | 记录的是"用这条命令数出来的值"，而该命令现在给出另一个数 |
| **C-4** | 更新 pr-body Verification 段的 smoke 计数（写 193，实测 **196 passed, 0 failed**）；该段的删环孪生命令缺 `--required-parts`（仍 exit 1，但与 `audit.yaml` 记录的命令不同字） | PR 正文是 AC-006-a 披露义务的落点，其可复现命令应当能逐字复现 |

C-1 是**硬条件**：它是本判决在字节上的落地。C-2 至 C-4 是记录卫生，不改变任何判定方向。

---

## Open Questions

1. **F-06 该不该编译成谓词？** 我这次是在**没有编译态尺子**的情况下裁读法的。若接受我的裁法，
   `checked_by == [] ⇒ implemented ≤ declared`（按独占产物）应当进 `check_audit.py`，否则下一次同样的分歧还得再裁一遍。
   注意它会与 F-17「不改任何既有谓词」相互作用——这是 change-proposal-002 要先过 G1 解释轮的原因。
2. **"闸"的定义要不要写死成"存在非零退出路径"？** 第 11 项与 mf-009 的整条推理都挂在这个定义上，
   而它目前只活在判官的读法里，不在任何规格文件里。建议写进 `audit.schema.md` 或 PSL。
3. **naming 维要不要留？** 41/42 fits。是补第二谓词，还是承认它是 advisory 并停止把它算作一个判定维度？（第 4 项）
4. **代签授权链条要不要收成引用？** 本次三道门全部代签，全部凭同一句自由文本授权。
   若 `--authorization` 收成"指向一份人写的授权文件并检存在"，至少代签会留下不可省略的痕迹。
5. **review 环在单人仓库里结构性不可收敛**（作者不能批准自己的 PR，`pr-poll.sh done` 的 APPROVED 项永不成立）。
   这不是本次的缺陷，是 harness 的设计前提问题——`review-loop` 需要一个单协作者模式，否则它在这类仓库里永远跑不完（I-69）。
6. **没有任何 CI。** `statusCheckRollup` 为空，我已复现。记录已诚实标注"checks_green 是空转"，
   但这意味着本仓库的所有"绿"都来自本地手跑。这是比本次任何一条 finding 都更基础的空隙。

---

```yaml
gate: G3
verdict: pass
ac_005_a: pass
ac_006_a: pass
signer: g3-judge
signer_kind: delegated_agent
authorization: "user instruction 2026-09-05: '需要人审核的地方，请你弄一个子agent代替我审核一下'"
record: plugins/sdlc/dogfood/ring-audit/g3-record.md
reviewed: {audit_yaml_sha256: c82dfc8e51f9e99e71c16b230b0949a6648339e106dd21fd85447f8c7894940e, AUDIT_md_sha256: 962cc2f654812be195cd918d1c28943ebeb84bbde0ab5f211a6a0ac7f1d016d4, head: 79b4736}
blocking_reasons: []
rulings_summary: "10 accept / 3 reject / 8 defer-to-change-proposal-002"
```

两个 human AC 都过。AC-005-a：checklist 14 框全中，42 个 Part 行与 33 个 missing 行逐列机械核过，
deletion 泛语扫描 0 命中，AUDIT.md 经重渲染证明是 audit.yaml 的**字节级**无损投影。
AC-006-a：两次 check 运行与回放我都亲自重跑并与记录逐字比对，holdout 4 个未命中确为 KG-01..04；
我独立查出的每一处差额——错标的 976 行、4→8 的计数漂移、失效的原始 diff 命令、空转的 checks_green——
**记录都先说了**，且方向压倒性是自曝其短。这是判 pass 的**决定性**理由。
mf-009 我裁**成立**：三处 `compiled` 应为 `declared`（底线更正为 19/23/0），但按纪律 defer，不当场改冻结字节。
merge 前必办 C-1：把 G3 的签字三元组写回 `audit.yaml` 并重渲染 `AUDIT.md`。
最后一句照录本 run 自己的铁律：**exit 0 说的是这份文档形状齐全，不是九环做到位了；
42 个配件无一到 `verified`，三道门无一是人签——这道门也不是。**
