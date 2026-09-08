# 失败报告 — sdlc-ring-audit · implement（calibrate 阶段）

> 路由的前提是归因器。本报告由引擎按 routing.yaml 的启发式生成候选层与证据，人只做确认或改判。
> 它是 G3 的输入——人不看原始日志。写完后 `sdlc_state.py report --path <本文件>` 清掉 pending.failure_report。

**信号**: `hidden_variant_fail`　**指纹**: `d1fc8380957b`　**层计数**: card=0 plan=0 task=2 ontology=0 world=1
**报告人**: calibrate（编排者代跑）　**日期**: 2026-09-06

## 当前状态

CARD-01（check_audit.py，08238cd）done；L5 测试 34/34 绿、fixture 变异 24/24、仪器级变异 23/30（0.767）；l5 锁第 2 次签（e217d10，43 文件）。校准报告四判据全过（`calibration_report.yaml`，verify_calibration PASS）。隐藏集：holdout-author（隔离，未读仪器与可见变体）在 CARD-01 关闭后写 10 个变体（8 应拒 / 2 应过），仪器命中 6 / 10：

| 变体 | 期望 | 实际 | 谓词出处 | 测试是否钉住 |
|---|---|---|---|---|
| hv_waived_without_waiver_ref | exit 1 | exit 0 | G1 规则 3c "waived 只能引用 state.json 的 waiver 记录" | 否——规则未命名 token，也未定引用字段 |
| hv_proposal_dangling_source | exit 1 proposal_without_source | exit 0 | AC-004-b given "lacking a source assessment or gap id" | 否——mutant 只删了 source 键；仪器只检非空 |
| hv_duplicate_ring_id | exit 1 | exit 0（rings=11） | AC-001-a expect `rings: 10`；thresholds `rings == 10` | 否——只在 complete 上断言计数，仪器无 ring_duplicate 谓词 |
| hv_signer_kind_outside_enum | exit 1 | exit 0 | F-07 signer_kind ∈ {human, delegated_agent} | 否——F-13 合取与 schema 谓词表都没有该 token |

4 个未命中全是**规格命名了、但测试与仪器都没编进谓词**的行为；命中的 6 个（含 2 个应过变体）说明仪器对已钉住的谓词既不漏也不过严。

## 收敛证据（fail 命令的 convergence 字段原样粘贴）

- **判定类型**: budget（task 2/2，track=psl）+ handler=human
- **指纹历史**（新在右）: `c8026b5b38d0 d1fc8380957b`（两个不同指纹：第一次是 lock_hash_mismatch/变更提案 001，第二次是本次；非 repeat，非 oscillation）
- **score 序列**: 无
- 这不是"再试一次"：预算耗尽的两次都是**契约层解释空隙**（G1 规则 3 纠正读法；本次 4 条谓词未命名），不是实现反复失败。

## 候选归因层

- **层**: task
- **依据**: routing.yaml `R08` hidden_variant_fail → action `ac_incomplete`："若隐藏集含 AC 没覆盖的行为，失败是规格缺陷，不是实现缺陷"
- **证据**: 上表第 4 列——4 条谓词各有规格出处、无一条被 tests/ring-audit 的 34 个方法或 24 个变体钉住；仪器 23/30 代码变异存活的 7 条（`calibration_report.yaml#surviving_mutants`）与这 4 条互补，都是"eval_case 缺"而不是"实现错"。

## 已排除的可能

- **card**：仪器对测试命名的全部 22 个 token 逐一命中（34/34、24/24）；实现者从未见过隐藏集，无从针对。把 4 条谓词直接塞进 check_audit.py 而不加测试 = 仪器行为只有隐藏证据、没有锁定证据，违背 L5"仪器行为由锁定测试钉住"。
- **ontology**：signer_kind / Gate.verdict 枚举在签字版形态 F-07 与 dos-proposal，不涉及 dos.yaml 不变量冲突。
- **world**：PSL 未触碰；4 条谓词与任一规律无矛盾，是落地缺口不是规律缺口。

## 建议回退目标（三选一，请人确认）

- **A（建议）· 记为棘轮项，本轮不动冻结契约**：4 条进 `calibration_report.yaml#gaps_routed_to.spec_compile`（已写）、AUDIT.md run_evidence 的 `known_gaps`、PR 的 Known issues 段，G3 据此裁决；下一轮以 change-proposal-002 一次补齐（4 fixture + 4 test + 仪器 4 谓词 + waiver_ref 字段），并把 task 预算重置。本轮以 `advance --force --reason` 的 waiver 记录接受"隐藏集 6/10"。
- **B · 立即走 change-proposal-002**（第三次 task 回流，超 PSL 轨预算 2 → 需要人明确加预算 1）：l5-tests 补 4 变体 + 4 测试并重签 l5；CARD-01 实现者补 4 谓词；再跑 holdout（需再造新的隐藏变体，否则已暴露）。代价：约一轮实现 + 一次重签 + 隐藏集失效。
- **C · 改判为 card 层**：只让 CARD-01 实现者补谓词、不动测试。**不建议**（见"已排除 · card"）。

## 请人确认

- [x] 确认候选层 **task**　- [ ] 改判为: —
- [x] 回退目标: **A**（棘轮项 + 本轮 waiver；冻结契约不动；**不追加 task 预算**）
- 签字: g2-judge（delegated_agent；authorization: user instruction 2026-09-05 '需要人审核的地方，请你弄一个子agent代替我审核一下'）· 2026-09-06 · 指纹 d1fc8380957b
- 裁决理由（摘）: 4 个未命中都是规格**命名了**却没编进任何谓词的行为（规则 3c / AC-004-b 措辞 / thresholds rings == 10 对 F-13 的"环集合" / F-07 枚举），是 eval_case 与解释空隙，不是实现缺陷；F-17 禁止新增既有谓词之外的谓词，C 会让仪器执行没有锁定测试钉住的行为；B 是一整个 L5 周期 + 新隐藏集，预算在第二个**不同**契约空隙上耗尽正是流水线在工作。A 下本仪器本轮只把关本 Run 自己产出的 audit.yaml，暴露面是文档级，G3 全量可见。
- **八项绑定条件**（编排者执行；违反任一则 A 失效）:
  1. 先记账：本块签字 + `sdlc_state.py report --path` 清 pending；决策事件带指纹 d1fc8380957b。
  2. waiver 范围：implement → 下一阶段的**唯一一次** `advance --force --reason`，理由原文 `hidden_variant_fail d1fc8380957b: holdout 6/10, misses waived_without_waiver_ref / proposal_dangling_source / duplicate_ring_id / signer_kind_outside_enum, accepted by g2-judge (delegated) per failure-report-002-holdout.md`；只覆盖本信号——CARD-02..06 须先 done、其余前置全满足；advance 报出任何别的问题就停下再问，不得扩大 waiver。
  3. AUDIT.md run_evidence 必带 `known_gaps`（11 项 = 4 个 holdout 未命中 + calibration_report 的 7 个存活仪器变体 M03/M04/M07/M14/M22/M23/M28，每项：名称 / 规格出处 / 期望 token 或 unspecified / status open → change-proposal-002）与 `holdout` 摘要 {ref holdout_run.json, instrument_head 5a6889c, variants 10, hits 6, misses 4, hit_rate 0.6, attested_by orchestrator delegated_agent}；按 F-15 渲染为 delegated，绝不渲染为人工验证。
  4. G3 必读 holdout_run.json 与 holdout_manifest.yaml（judge 可读，implementer 不可）；变体内容不得引入 AUDIT.md / PR / skill-issues / 任何卡。checklist_G3.md 应加此项——**该文件在 l5 锁内**，本轮不改锁：此项通过 G3 的输入提示与 g3-record 落实，checklist 修订并入 change-proposal-002（编排者偏差记录见账本）。
  5. A6（F-14）答案与 PR 的 Known issues 不得无限定地写"calibrated"：写 "instrument mutation 0.767; holdout 6/10 with 4 known gaps" 并列同一 11 项，链接本报告与 calibration_report.yaml。
  6. 不许变相 C：check_audit.py 本轮停在 08238cd，4 条谓词不得无测试加入；audit.schema.md §proposals "source 必须指向一个 Assessment id 或 Gap id" 属过度声明（仪器只检非空）——由编排者以非 Card 的 doc-only 提交更正。
  7. 不追加 task 预算：task_reflows 2/2 保持耗尽，本轮再有 task 层信号即再停等人；change-proposal-002 已在 calibration_report.yaml#gaps_routed_to 预登记，须**先**开一轮 G1 解释（waiver_ref 字段与 token；signer_kind_outside_enum token；环计数 vs 环集合；AC-004-b 悬空来源读法）再由 l5-tests 编 4 + 7 条 eval_case，随后**新造**隐藏集——现有 4 个未命中已因本报告曝光而作废。
  8. calibration_report.yaml 的 verdict.result 只在 holdout_run 块与 gaps_routed_to 原样保留时为 pass；二者任一被删，c3_holdout_pass 必须翻为 false。
