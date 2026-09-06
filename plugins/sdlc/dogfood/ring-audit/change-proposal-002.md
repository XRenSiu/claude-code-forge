# 变更提案 — change-proposal-002.md

> G2 之后改被锁文件（`done_when.yaml` / `contract.yaml` / `tests/**`）的唯一合法路径：同一 diff 附带本文件。
> 没有它，锁定检查（A 档）直接拒绝。有它，放行并计入 task_reflows。

**日期**: 2026-09-06　**提案人**: l5-tests-cp002（隔离的非实现者测试作者）+ 编排者
**签字人**: g1-judge 出解释裁决（delegated_agent）；本提案由编排者依用户 2026-09-06 授权代行人的确认

## 改哪条

被锁文件只在 `tests/ring-audit/**`（l5 锁）。`done_when.yaml`（20 条 AC，fb5af3f0…）、签字版形态 `derived/form-draft.md`（746c56ef…）、`dos.yaml`、`PSL` **一个字节不改**——G1 的七条裁决全部标注 `contract_bytes_must_change: no`。

| 文件 | 改前 | 改后 |
|---|---|---|
| `tests/ring-audit/test_check_audit.py` | 34 个方法 | **52** 个（+18；每条新方法断言 exit code **与**具体 token） |
| `tests/ring-audit/fixtures/` | 24 份 | **39** 份（+15：7 条裁决各自的拒绝面与接受面） |
| `tests/ring-audit/mutation.config.yaml` | 24 条 | **36** 条 |
| `tests/ring-audit/tests-manifest.yaml` · `fixtures/MUTANTS.md` | 同步 | 同步（`test_to_ac` 写明每条新 token 挂在哪个 AC 及理由） |

## 为什么

`check_audit.py` 的七处行为与签字版形态不符，其中**六处是仪器错了**（fail-open 或过严），一处是 G3 已裁而未编成谓词。这不是新需求：全部七条来自本次 run 自己的隐藏集未命中、存活的仪器变体与 G3 的裁定。

G1 于 2026-09-06 开解释轮逐条裁决（`g1-interpretations.md`，代签），给出谓词、error token 与 killing fixture 的必备内容。**测试作者与仪器实现者互相隔离**，各自只依据该裁决工作：

- 测试作者对**当时的**仪器录得 12/52 红（11 条 fail-open 面、1 条过严面），红基线如实记录
- 实现者独立实现七条谓词，各自造最小 fixture 自证
- 合并后 **52/52 绿、变异 36/36 杀（1.0）** —— 两份从未互见的产物严丝合缝，这是那份裁决无歧义的证据

## 归因层

- [x] **task**（判据写错 / 写漏）——仪器与签字版形态不符；契约 AC 与形态字节都不动
- [ ] ontology　- [ ] world

## 预算

`task_reflows` 在本 run 已 **2/2 耗尽**（change-proposal-001；hidden_variant_fail）。本次为**第三次** task 层回流，超预算，须人确认。
依用户 2026-09-06 授权「需要人做的你就帮我做了当做人做的」，由编排者代行确认并以 `sdlc_state.py waive` 独立登记，**不**借 `advance --force` 顺带产生——豁免与推进是两件事（I-67 正是为此加的子命令）。

## 重新冻结

- 新 `.done_when.lock` sha256: `0b1f9385367eef6c13e85a415bdf0ff3e47fcae641911034e47021e24cfa2443`　签字: g2-judge（delegated_agent，同一授权；stage l5）
- 锁内文件: 60 项（含 2 个闸脚本，I-30 首次实际使用）
