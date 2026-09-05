## Summary

sdlc 插件的第一次完整生命周期 dogfood：用插件自己的九环流程审计它自己的 42 个配件（28 skill、5 agent、4 脊柱资产、5 人签门），回答"是否缺少 / 是否必要 / 是否实现（三态）/ 名字是否合适"。产物是一份机器可读的 `audit.yaml`（10 环、42 Part、73 Gap、39 提案）与它的投影 `AUDIT.md`，由 `check_audit.py` 机械把关（F-13/F-17 谓词 + G1 三条解释规则）。对用户可见的变化：sdlc 插件多了一份带证据的自审报告，以及 67 条在跑流程时抓到的 skill 缺陷清单；被审目录（skills / agents / docs）在所有 Card 提交中零改动。

## Scope

- do: 按环组织的审计报告 AUDIT.md；同构的 audit.yaml；检查脚本 check-audit（含删环变体自校准）；每配件三维 Assessment（needed / implemented / naming，每维 ≥1 PSL-ID 与 ≥1 Evidence）；每环 missing；run_evidence（含 known_gaps 11 项与 holdout 摘要）；提案清单（每条有 source）；L5 测试套件 + 变异 + 校准报告；沿途修掉的 6 处 verifier / gate 缺陷（fix(sdlc) 提交，非 Card）
- dont: 不重命名任何 skill / agent；不修改被审的 SKILL.md / gate.json / 脚本内容（fix(sdlc) 提交只改验证脚本的缺陷，且不在 Card 内）；不实现本次识别出的缺少配件；不给确定性配件套世界模型；不把 static_only / delegated 写成更强

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
git diff --stat 0be2770^..HEAD -- plugins/sdlc/skills plugins/sdlc/agents plugins/sdlc/docs   # (empty — AC-007-a)
python3 plugins/sdlc/skills/calibrate/scripts/verify_calibration.py plugins/sdlc/dogfood/ring-audit/calibration_report.yaml   # meta_gate PASS · instrument mutation 0.767 · holdout 6/10 with 4 known gaps
bash plugins/sdlc/eval/smoke.sh                                             # 190 expectations
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

__KNOWN_ISSUES__

## Notes

- size: XL（fixtures 23 × ~2k 行为生成数据；--allow-xl 理由：dogfood 产物不可拆，拆开会让 l5 锁与 Card 回放失去同一分支的可证性）· cards: CARD-01..06 · lock: changed_with_proposal (change-proposal-001; l5 re-signed, 43 files)
- gates: G1 pass (g1-judge, delegated_agent) · G2 pass (g2-judge, delegated_agent) · G3 pending → 代签裁决见 g3-record.md；所有代签均在用户 2026-09-05 "需要人审核的地方，请你弄一个子agent代替我审核一下" 的授权下，报告里一律渲染为 delegated
- task reflows 2/2 exhausted (change-proposal-001; hidden_variant_fail → failure-report-002, fallback A by g2-judge)
- 本 PR 分支只含本 run 的提交；同一工作区的另一 session 的 humanize 提交（100aa12 / df48739 / bf3f13e）不在此 PR
- 本 PR 分支 `pr/1-sdlc-ring-audit` 是 run 分支 `docs/1-sdlc-ring-audit` 的 cherry-pick 镜像：`audit.yaml#run_evidence` 与 `.sdlc/` 账本里引用的 commit sha（0be2770 / 08238cd / e217d10 …）是 run 分支上的；本分支同一提交 sha 不同。`replay_card_commits.sh` 按 Card footer 在任意分支重算，不依赖 sha
