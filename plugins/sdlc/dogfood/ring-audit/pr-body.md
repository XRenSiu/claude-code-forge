## Summary

sdlc 插件的第一次完整生命周期 dogfood：用插件自己的九环流程审计它自己的 42 个配件（28 skill、5 agent、4 脊柱资产、5 人签门），回答"是否缺少 / 是否必要 / 是否实现（三态）/ 名字是否合适"。产物是一份机器可读的 `audit.yaml`（10 环、42 Part、73 Gap、39 提案）与它的投影 `AUDIT.md`，由 `check_audit.py` 机械把关（F-13/F-17 谓词 + G1 三条解释规则）。对用户可见的变化：sdlc 插件多了一份带证据的自审报告，以及 67 条在跑流程时抓到的 skill 缺陷清单；被审目录（skills / agents / docs）在所有 Card 提交中零改动。

## Scope

- do: 按环组织的审计报告 AUDIT.md；同构的 audit.yaml；检查脚本 check-audit（含删环变体自校准）；每配件三维 Assessment（needed / implemented / naming，每维 ≥1 PSL-ID 与 ≥1 Evidence）；每环 missing；run_evidence（含 known_gaps 11 项与 holdout 摘要）；提案清单（每条有 source）；L5 测试套件 + 变异 + 校准报告；沿途修掉的 6 处 verifier / gate 缺陷（fix(sdlc) 提交，非 Card）
- dont: 不重命名任何 skill / agent；不修改被审的 SKILL.md / gate.json / 脚本**内容**。例外有二，均为非 Card 提交并经代签契约判官按 PSL-003 的 L122-123 豁免逐条裁定：① `fix(sdlc)` 提交只修**验证脚本自身的缺陷**（本次 4 条：587f371 / ebe270d / c729f76 / e198e0e）；② 一条 `chore` 版本 bump（0cf6b1a）把 CLAUDE.md 要求的三处 version 同步到位——六个文件各一行 version，不动任何被审散文、不移动任何行号；不实现本次识别出的缺少配件；不给确定性配件套世界模型；不把 static_only / delegated 写成更强

## Linked issue

Closes #1

## Changes

- `plugins/sdlc/dogfood/ring-audit/AUDIT.md` · `audit.yaml` · `render_audit.py` — 审计报告与其投影脚本（CARD-06）
- `plugins/sdlc/dogfood/ring-audit/check_audit.py` · `replay_card_commits.sh` · `audit.schema.md` — 机械闸、Card 提交回放、数据形态（CARD-01）
- `plugins/sdlc/dogfood/ring-audit/audit/rings-*.yaml` — 四个环组片段（CARD-02..05，各自隔离的实现者）
- `plugins/sdlc/dogfood/ring-audit/tests/ring-audit/` — 34 个 L5 测试 + 24 变异条目（非实现者作者，l5 锁）
- `plugins/sdlc/dogfood/ring-audit/{PSL-*.md, derived/, dos.yaml, invariants/, issue-body.md, done_when.yaml, cards/, g1-record.md, g2-record.md, change-proposal-001.md, failure-report-002-holdout.md, calibration_report.yaml, calibration/, skill-issues.md, g3-input.md}` — 世界 / 形态 / 本体 / 契约 / 卡 / 门记录 / 校准 / 缺陷清单
- `plugins/sdlc/skills/{psl-derive,issue,commit,sdlc}/scripts/*.py` · `plugins/sdlc/eval/smoke.sh` — 跑流程时抓到并修掉的 verifier / gate 缺陷（I-04/05/07/17/34/38/39/47/51/52），smoke +10
- `.gitignore` — 忽略 `.sdlc/` 运行时状态

## Verification

```bash
bash plugins/sdlc/dogfood/ring-audit/tests/ring-audit/run_tests.sh          # existence=ok unittest=ok | Ran 34 tests | OK
bash plugins/sdlc/dogfood/ring-audit/tests/ring-audit/mutation.sh           # baseline_exit 0, killed 24/24, kill_rate 1.0
python3 plugins/sdlc/dogfood/ring-audit/check_audit.py plugins/sdlc/dogfood/ring-audit/audit.yaml --psl plugins/sdlc/dogfood/ring-audit/PSL-sdlc-ring-audit.md --required-parts "agent.card-implementer, agent.comment-fixer, agent.fix-verifier, agent.pr-reviewer, agent.review-triager"   # exit 0 · rings 10 · parts_total 42 · failed_predicates []
python3 plugins/sdlc/dogfood/ring-audit/check_audit.py plugins/sdlc/dogfood/ring-audit/audit.yaml --psl plugins/sdlc/dogfood/ring-audit/PSL-sdlc-ring-audit.md --variant delete-ring:R6   # exit 1 · ring_missing (F-14 twin)
bash plugins/sdlc/dogfood/ring-audit/replay_card_commits.sh                 # ok true · every Card commit inside its whitelist · touches_audited_dirs 0
bash plugins/sdlc/dogfood/ring-audit/replay_card_commits.sh   # AC-007-a 的证据：card_commits_touching_audited_dirs 0（卡范围仪器；原始 git diff 见下）
git diff --stat 0be2770^..a2deb83 -- plugins/sdlc/skills plugins/sdlc/agents plugins/sdlc/docs   # 记录时（a2deb83）为空；此后的非 Card 偏差提交会让同一命令对 HEAD 非空——见 Known issues G
python3 plugins/sdlc/skills/calibrate/scripts/verify_calibration.py plugins/sdlc/dogfood/ring-audit/calibration_report.yaml   # meta_gate PASS · instrument mutation 0.767 · holdout 6/10 with 4 known gaps
bash plugins/sdlc/eval/smoke.sh                                             # 193 expectations (190 + 3 cr-001 twins)
```

- Red-green: `tests/ring-audit/RED_BASELINE.txt` — 30/30 red at c729f76 (instrument absent), rev 2 19 ok / 15 FAIL at 57ebf2b (pre-ruling instrument present, attributed line by line); 34/34 green from 0be2770
- Calibration wording (binding, failure-report-002 条件 5): **instrument mutation 0.767; holdout 6/10 with 4 known gaps** — not "calibrated" unqualified

## Acceptance mapping

| AC | kind | evidence |
|---|---|---|
| AC-001-a | mechanical | `test_AC_001_a_F13_double_producer_unacknowledged_exit1_double_producer`, `test_AC_001_a_F13_spurious_merge_candidate_exit1_spurious_merge_candidate`, `test_AC_001_a_complete_exit0_rings10_parts_total42` ✅ 34/34 at HEAD |
| AC-001-b | mechanical | `test_AC_001_b_F14_variant_delete_ring_R6_exit1`, `test_AC_001_b_ring_removed_exit1_ring_missing` ✅ 34/34 at HEAD |
| AC-002-a | mechanical | `test_AC_002_a_F13_evidence_kind_outside_enum_exit1`, `test_AC_002_a_F13_evidence_ref_empty_exit1`, `test_AC_002_a_F13_unknown_psl_id_exit1_dims_with_unknown_psl_id_1` (+1) ✅ 34/34 at HEAD |
| AC-002-b | mechanical | `test_AC_002_b_empty_psl_ids_exit1_psl_id_missing` ✅ 34/34 at HEAD |
| AC-003-a | mechanical | `test_AC_003_a_F13_implemented_outside_enum_exit1_count1`, `test_AC_003_a_F13_rename_true_exit1_count1`, `test_AC_003_a_complete_implemented_and_rename_counts_zero` ✅ 34/34 at HEAD |
| AC-003-b | mechanical | `test_AC_003_b_boolean_implemented_exit1_boolean_implemented` ✅ 34/34 at HEAD |
| AC-004-a | mechanical | `test_AC_004_a_F13_orphan_gap_exit1_orphan_gaps_1`, `test_AC_004_a_F13_overfill_unmarked_exit1_overfill_unmarked`, `test_AC_004_a_F13_ring_without_missing_key_exit1_count1` (+2) ✅ 34/34 at HEAD |
| AC-004-b | mechanical | `test_AC_004_b_proposal_without_source_exit1_proposal_without_source` ✅ 34/34 at HEAD |
| AC-005-a | human | judge: tech · evidence: checklist → `tests/ring-audit/checklist_G3.md` + `g3-input.md`（待 G3 代签） |
| AC-006-a | human | judge: product · evidence: checklist → `tests/ring-audit/checklist_G3.md` + `g3-input.md`（待 G3 代签） |
| AC-007-a | mechanical | `test_AC_007_a_replay_card_commits_exit0_touching_zero` ✅ 34/34 at HEAD |
| AC-007-b | mechanical | `test_AC_007_b_card_commit_touching_skills_exit1_whitelist_overflow` ✅ 34/34 at HEAD |
| AC-008-a | mechanical | `test_AC_008_a_rings_R0_R2_spine_required_parts_exit0` ✅ 34/34 at HEAD |
| AC-008-b | mechanical | `test_AC_008_b_required_part_removed_R0_R2_spine_exit1_required_part_missing` ✅ 34/34 at HEAD |
| AC-009-a | mechanical | `test_AC_009_a_rings_R3_R5_required_parts_exit0` ✅ 34/34 at HEAD |
| AC-009-b | mechanical | `test_AC_009_b_required_part_removed_R3_R5_exit1_required_part_missing` ✅ 34/34 at HEAD |
| AC-010-a | mechanical | `test_AC_010_a_rings_R6_required_parts_exit0` ✅ 34/34 at HEAD |
| AC-010-b | mechanical | `test_AC_010_b_required_part_removed_R6_exit1_required_part_missing` ✅ 34/34 at HEAD |
| AC-011-a | mechanical | `test_AC_011_a_rings_R7_R8_required_parts_exit0` ✅ 34/34 at HEAD |
| AC-011-b | mechanical | `test_AC_011_b_required_part_removed_R7_R8_exit1_required_part_missing` ✅ 34/34 at HEAD |

## Risk & rollback

- risk: 低 — 全部新增文件在 `plugins/sdlc/dogfood/ring-audit/` 与 `.sdlc/`（忽略）；被审目录零改动；6 处 verifier 修复各有 smoke 覆盖
- blast radius: sdlc 插件的 4 个验证脚本（verify_derived / verify_issue / verify_commit / sdlc_state, lock_done_when）行为收紧或修正；其余为文档与数据
- rollback: revert 即可；无迁移
- feature flag: none

## Reviewer focus

- `plugins/sdlc/dogfood/ring-audit/check_audit.py:248-315` — 规则 2 的 gaps / fills / missing 谓词（holdout 命中 2、未命中 0 在此段；KG-03 duplicate ring 在 `check_rings`）
- `plugins/sdlc/dogfood/ring-audit/audit.yaml#run_evidence` — known_gaps 11 项与 holdout 摘要是否按 F-15 渲染为 delegated
- `plugins/sdlc/skills/commit/scripts/verify_commit.py` — 锁检查改为内容哈希（I-52）与 basename 回退（I-38）

## Known issues

> 依 g2-judge 对 iteration-002 / 003 的解码列全。AC-005-a / AC-006-a **待 G3 代签，未通过**。校准措辞：**instrument mutation 0.767; holdout 6/10 with 4 known gaps**（不写无限定的 calibrated）。本节条目多于常规上限 5——这是一次审计自身的 dogfood，发现登记册本身就是交付物之一；每条带 `file:line` 锚点。

**A. 已知空隙（11 项，`plugins/sdlc/dogfood/ring-audit/calibration/known_gaps.yaml:1`，状态 open → change-proposal-002）**

- KG-01 `waived` 无 waiver_ref，G1 规则 3c 未命名 token — `plugins/sdlc/dogfood/ring-audit/check_audit.py:376`
- KG-02 / mf-003 proposal.source 只检非空、不解析（39 条 source 已人工核对可解析） — `plugins/sdlc/dogfood/ring-audit/check_audit.py:399`
- KG-03 重复环 id → rings 11 无谓词 — `plugins/sdlc/dogfood/ring-audit/check_audit.py:151`
- KG-04 / mf-007 signer_kind 超 F-07 枚举无 token — `plugins/sdlc/dogfood/ring-audit/check_audit.py:388`
- KG-05..KG-11 七个存活仪器变体 M03/M04/M07/M14/M22/M23/M28（ring_unexpected / parts_missing / evidence_missing / 跨环 gap 引用 / gate_verdict 枚举 / reject-waived 无 signer / --rings 视图） — `plugins/sdlc/dogfood/ring-audit/calibration/known_gaps.yaml:43`

**B. 契约 / 解释层延后项（change-proposal-002；须先开一轮 G1 解释再编谓词）**

- mf-004 / KG-08 规则 2e 的同环子句被用于 fills[]，G1 文本只对 missing[] — `plugins/sdlc/dogfood/ring-audit/check_audit.py:265`
- mf-006 gates[].kind 未对 {script, human} 校验，其他 kind 逃过两条规则 3 谓词 — `plugins/sdlc/dogfood/ring-audit/check_audit.py:371`
- mf-010 `--rings` 使 ring_unexpected 失效，与 F-17"不改任何既有谓词"冲突 — `plugins/sdlc/dogfood/ring-audit/check_audit.py:161`
- mf-013 alternatives_of 任意非空即豁免，F-05 三条件未检 — `plugins/sdlc/dogfood/ring-audit/check_audit.py:334`
- mf-007 / mf-008 形态文档列六个顶层注册表，数据与渲染器用八个（多出 unenforced_rules / suspected_duplicate_pairs） — `plugins/sdlc/dogfood/ring-audit/audit.schema.md:36`
- mf-012 exit-2 路径不出 JSON；mf-014 schema 前言自 5a6889c 起过时；mf-015 注册表可选 — `plugins/sdlc/dogfood/ring-audit/audit.schema.md:16`
- srg-003（AC-007-c 作为记录字段）· srg-006（实现期重签者规则）· I-68（S3 在 3 ≤ gaming < 7 无规则） — `plugins/sdlc/dogfood/ring-audit/skill-issues.md:75`

**C. nh-004：本轮所有修复都没有锁定测试覆盖（tests/** 已锁，测试进 change-proposal-002）**

- 清单：AUDIT.md golden-file 字节比对；atoms / id 含 `|` 的 fixture；signer_kind 人签 / agent 变体；含 CJK 路径与重命名移出的孪生仓库；空 main..HEAD 范围须 exit 0 + card_commits 0；小写 footer 提交须恰好出现在一遍里 — `plugins/sdlc/dogfood/ring-audit/ratchet-log/iteration-003/needs-human.md:1`

**D. 交给 G3 的裁项**

- mf-009 F-06 封顶：R6/human_gate.G3、R7/agent.pr-reviewer、R8/tune 记 compiled 而其每个 Artifact 的 checked_by 皆空 — `plugins/sdlc/dogfood/ring-audit/audit.yaml:1348`
- `g3-input.md` 第 1–20 项 + 三轮解码补充；AC-005-a / AC-006-a 待 G3，从不渲染为 passed — `plugins/sdlc/dogfood/ring-audit/g3-input.md:1`

**E. iteration-003 关闭的项（各由 ≥3 个评审复现为已修）**

- stale-sha 类、exit-vs-ok 类、空范围崩溃（it-002 的 mf-001 / mf-002 / mf-003）全部关闭；同轮关闭 quotePath 规避、pre-Card 扫描窗口、残余单元格插值、cmd/exit 未渲染 — `plugins/sdlc/dogfood/ring-audit/ratchet-log/iteration-003/meta-judge-output.yaml:1`
- g2-judge 在 shipping 分支上亲自复核：replay exit 0 / ok true / 15-0-0，`recorded_at_head` a2deb83 是 HEAD 的祖先，空范围在 main 的 scratch clone 里 exit 0 且出 JSON — `plugins/sdlc/dogfood/ring-audit/audit.yaml:3412`

**F. iteration-003 存活项（15 条中的 P1 / P3；11 条为设计上带过的复发项，见 A / B / D）**

- **mf-001（P1，由 a2deb83 引入）** `card_footer_of` 大小写敏感而 `has_card_footer` 不敏感，`card: CARD-xx` 拼法两遍都看不到；**未被利用**（本分支 15 条 footer 两种匹配都命中，独立于被质疑的匹配器验证） — `plugins/sdlc/dogfood/ring-audit/replay_card_commits.sh:60`
- **mf-002（P1，由 a2deb83 + 4ddb362 引入，四评审一致）** 该行标着"自第一个 Card 提交起"，而 yaml 的窗口是 `merge-base(main,HEAD)..HEAD`；四条命中提交全部早于第一个 Card 提交，标签下的真值是 **0**；`non_card_range_spec` 与清单未渲染 — `plugins/sdlc/dogfood/ring-audit/render_audit.py:533` 与 `plugins/sdlc/dogfood/ring-audit/AUDIT.md:976`；权威数据在 `plugins/sdlc/dogfood/ring-audit/audit.yaml:3412`
- mf-005（P3）`skill_issues_count` 记 67，4ddb362 上 grep 得 69——记录时冻结的计数 — `plugins/sdlc/dogfood/ring-audit/audit.yaml:3459`
- mf-011（P3）holdout 见证单元格把 `attested_by_kind` 原样打出而非走封闭映射（本次值 delegated_agent，渲染正确） — `plugins/sdlc/dogfood/ring-audit/render_audit.py:573`
- **审查阶段处置**：mf-001 / mf-002 若在 review 线程里被要求修，作为 CARD-01 / CARD-06 footer 提交经同一套预门落地并显式标 UNTESTED，由 review-loop 预算治理；除非 `check_audit.py` 或 yaml 记录的数据改变，否则不开 iteration-004 — `plugins/sdlc/dogfood/ring-audit/ratchet-log/iteration-003/needs-human.md:1`

**G. 过程记录**

- **review 环结构性不收敛（I-69，代签判官豁免，钉在 PR head efd45ac）**：`pr-poll.sh done` 的终止谓词是 APPROVED ∧ 0 未解决线程 ∧ checks 绿。后两条成立，第一条**不可能成立**——GitHub 禁止 PR 作者批准自己的 PR，本仓库只有一个协作者。评审的实质在建 PR 前已交付：两轮隔离 pr-reviewer + 一轮独立 fix-verifier，在本 PR 自己的验证器修复里抓出 5 个缺陷（锁门 fail-open、版本未同步、第一次修法的回归、不杀 mutant 的装饰性孪生、空 range 的第三扇门），全部修掉，0 条 A 档存活。**并且**：`checks_green: true` 是**空转**——`statusCheckRollup` 为空，本仓库没有配置任何 CI，这与"检查通过"不是一回事，全文任何地方都不得写成后者。合并仍是人的动作 — `plugins/sdlc/dogfood/ring-audit/skill-issues.md:79`

- 两轮修复各有 2/6 条发现是"修复自己引入的"；结构性成因是投影与其数据源分属两张卡且都无锁定测试 — `plugins/sdlc/dogfood/ring-audit/skill-issues.md:80`
- gaming 轨迹 [3.5, 4.0, 4.0] **持平**（iteration-003 的检测器被编排者任务文件错传基线 3.5，检测器自报了不一致） — `plugins/sdlc/dogfood/ring-audit/skill-issues.md:79`
- 隔离事件：`spec-drift-detector` 经其 `--qa-report` 参数读到 qa 的输出，与 fleet 的无串扰铁律冲突；裁为有界接受（qa 零发现，可继承的只有测量事实），drift 的 11 条信号不打折 — `plugins/sdlc/dogfood/ring-audit/skill-issues.md:78`
- card 预算 4/3（两次升级由代签判官豁免，授予已用尽）；task 预算 2/2 耗尽；三次豁免记在状态与账本 — `plugins/sdlc/dogfood/ring-audit/ratchet-log/iteration-003/final-state.json:1`
- 无 footer 提交的合法性（nh-003 裁决）与逐提交分类（28 条：Card 11 · 偏差 3 · 编排者文档 11 · peer 3） — `plugins/sdlc/dogfood/ring-audit/commit-table.md:1`
- 所有评审均为 claude 厂商，编排者撰写评审提示；隔离为协议级而非 OS 级 — `plugins/sdlc/dogfood/ring-audit/ratchet-log/iteration-003/isolation.json:1`
- 报告底线：0 verified / 26 compiled / 16 declared；三道门两道代签；G3 待定 — `plugins/sdlc/dogfood/ring-audit/AUDIT.md:1`
- **记录与现况的差额（出 PR 前的两条偏差提交）**：`AUDIT.md` / `audit.yaml` 冻结在 iteration-003 评审过的字节，其中 `non_card_commits_touching_audited_dirs` 记的是 **4**；分支现况写这段时是 **8**，且每多一条非 Card 的偏差提交就 +1（可用 `bash plugins/sdlc/dogfood/ring-audit/replay_card_commits.sh` 现场重算）。七条的分类：**PSL L122-123 的验证器偏差提交**（587f371 / ebe270d / c729f76 / e198e0e / aaf3d5b / 801a32e，最后三条是 PR 预审两轮 + 独立 fix-verifier 抓出的锁门 fail-open、其回归、以及空 range 的第三扇门）；**版本同步**（0cf6b1a，同一豁免的收尾）；**peer 的报告提交**（bf3f13e，main 已有孪生）。**Card 提交触碰被审目录仍为 0**（AC-007 成立，现场复现可得）。AUDIT.md 未重渲染——它是被评审过的那份。**并且**：`git diff --stat 0be2770^..HEAD -- <被审目录>` 这条**原始命令**在记录时（a2deb83）为空，但对**当前 HEAD** 已非空（5 files / 11 insertions）——正是那四条偏差提交与版本 bump 落在首个 Card 提交之后所致。AC-007-a 的证据是卡范围仪器（`card_commits_touching_audited_dirs` 恒为 0），不是这条会随分支增长而失效的原始命令；`audit.yaml#run_evidence.git_diff_stat` 冻结的是 a2deb83 时刻的真值（cr-005 / I-79） — `plugins/sdlc/dogfood/ring-audit/commit-table.md:1`
- **cr-003（B 档，本 PR 相对 origin/main 引入的回归）**：`verify_derived.py` 的 I-04 修法把 workflow.md 全文的引用行都剥掉再扫，整篇用 `> ` 引起来的工作流零命中通过；本次 run 的 PASS 仍成立（其 workflow.md 有真实非引用内容）。修法与 nh-004 的测试清单一并进合并后的跟进 PR — `plugins/sdlc/skills/psl-derive/scripts/verify_derived.py:95`
- **cr-001（A 档，出 PR 前已修）**：`verify_commit.py` 的落地内容豁免会在 `--range` 不含 `..` 时读到基线侧，被篡改的被锁文件因此 PASS；已改为拒绝单 ref 并按二/三点式取落地侧，smoke +3 — `plugins/sdlc/skills/commit/scripts/verify_commit.py:196`
- **cr-002（A 档，出 PR 前已修）**：七个 skills 文件改了而三处 version 未动，装着 0.6.0 的用户收不到修复；已 bump 至 0.7.0（skill 各自 0.1.1 / 0.3.0）。该规则没有机械门是本次抓到的流程缺口 — `plugins/sdlc/dogfood/ring-audit/skill-issues.md:76`

## Notes

- size: XL（fixtures 23 × ~2k 行为生成数据；--allow-xl 理由：dogfood 产物不可拆，拆开会让 l5 锁与 Card 回放失去同一分支的可证性）· cards: CARD-01..06 · lock: changed_with_proposal (change-proposal-001; l5 re-signed, 43 files)
- gates: G1 pass (g1-judge, delegated_agent) · G2 pass (g2-judge, delegated_agent) · G3 pending → 代签裁决见 g3-record.md；所有代签均在用户 2026-09-05 "需要人审核的地方，请你弄一个子agent代替我审核一下" 的授权下，报告里一律渲染为 delegated
- task reflows 2/2 exhausted (change-proposal-001; hidden_variant_fail → failure-report-002, fallback A by g2-judge)
- 本 PR 直接从 run 分支 `docs/1-sdlc-ring-audit` 发出（g2-judge 裁决：评审过的迭代之后不改写 shipping 分支的历史；worktree 提交 cherry-pick 上来是允许的，但 worktree sha ≠ shipping sha，所以 run_evidence 里记录的每个 sha 都必须在 shipping 分支上产生——iteration-001/002 的 stale-sha 发现正是违反了这一点；spec-gaming-detector 所称“违反不 cherry-pick 裁决”基于本段旧措辞的误引）。因此**同一工作区另一 session 的三条提交随行**：100aa12 feat(humanize)、df48739 chore bump humanize v0.3.0、bf3f13e docs(sdlc) report——三条都已以内容相同的 cherry-pick 落在 main（eab072b / 1b07bb2 / fbc6a3c），`git diff origin/main HEAD -- plugins/humanize .claude-plugin plugins/sdlc/docs/reports` 为空，本 PR 的内容 diff 不含它们；它们不是本 run 的编辑，逐提交分类见 `plugins/sdlc/dogfood/ring-audit/commit-table.md`（28 条：Card 11 · deviation 3 · docs/test/chore 11 · peer 3）
