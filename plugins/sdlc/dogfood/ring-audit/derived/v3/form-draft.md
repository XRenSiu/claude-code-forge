# 形态草案 — sdlc-ring-audit（审计交付物的形态：报告 / audit.yaml / 检查脚本 / Finding 记录）

> 每条决策一行，形如 `- [F-nn] <决策> ← PSL-xxx[, PSL-yyy]`。无引用的决策不允许存在（先把常识写进 PSL 再引）。
> 签字后本文件即功能文档；sha256 进 `g1-record.md`。
> 词表只用 PSL Domain Model 的七个实体：Ring / Part / Gap / Artifact / Gate / Finding / Loop。脊柱按 Domain Model 归入 Ring（作为一行 Ring 记录）。

source_psl: plugins/sdlc/dogfood/ring-audit/PSL-sdlc-ring-audit.md
derivation_run: 3 of 3

## 实体与数据形态

- [F-01] Finding 与 Part 一对一，固定四维 `missing / needed / implemented / naming`，每维是一个 `{verdict, psl_ids[≥1], evidence[]}` 三元组，缺任一维或任一维 `psl_ids` 为空即为非法记录 ← PSL-002, PSL-010, PSL-014, PSL-017
- [F-02] `implemented` 维的 verdict 是三值枚举 `declared | compiled | verified`（可加 `calibrated` 作第四值），每个已达状态各带一条证据路径（SKILL.md 路径 / verify 脚本 + gate.json 路径 / 行为层运行记录），未达状态显式写 `not_reached` 而不是省略 ← PSL-010
- [F-03] `naming` 维是复合值 `{provenance: authored | adopted, artifact_or_position: <名>, fit: fits | misfit, suggested_name?: <名>, rename: false}`，`rename` 字段为常量 false，不可被审计写成 true ← PSL-014
- [F-04] Gap 记录持有 `atoms ⊆ {Knowledge, Capability, Judgment, Control}` 与状态 `unidentified | identified_no_part | has_part`；被某 Part 声明填充但 `atoms` 为空集的 Part 在其 Finding 的 `needed` 维写 `overfill`；`needed` 维的 evidence 必含一句 deletion 测试（"撤掉它，引擎会 ___"） ← PSL-016, PSL-002, PSL-017
- [F-05] Artifact 记录持有唯一 `producer: <Part>`；audit.yaml 里同一 Artifact 名出现两个 producer 时，两个 Part 的 Finding 都被标 `merge_candidate: <另一 Part>`，而不是由审计者当场裁掉一个 ← PSL-001
- [F-06] 每条 Artifact 记录持有 `checked_by: [<Gate>...]`，Gate 记录带 `kind: script | human`（human 仅 G1/G2/G3）；`checked_by` 为空的 Artifact 使其 producer Part 的 `implemented` 维不得高于 `declared` 并在该维 evidence 写 `no_gate`，审计者不得以“读了代码觉得能跑”把它抬到 `compiled` ← PSL-015, PSL-006, PSL-010
- [F-07] Finding 记录带状态 `candidate | evidenced | adjudicated` 与追加式 `adjudications[]`，每条含 `gate: G1 | G3, signer, signer_kind: human | delegated_agent, authorization_ref`；推翻不改写原判定，只追加一条带 `supersedes: <前一条>` 的新记录 ← PSL-005, PSL-006, PSL-003

## 界面 / 接口形态

- [F-10] 报告按 Ring 分节（R0–R8 各一节 + 脊柱一节），每节一张表、每 Part 一行、四列判定、每格内联 PSL-ID；audit.yaml 以 `rings[].parts[].finding` 同构嵌套，Part 的 Loop 只写 `loop: loops.yaml#<id>` 引用而不复述环契约内容 ← PSL-011
- [F-11] 报告与 audit.yaml 各有一个必存在的 `missing` 节（可为空数组但键必在），内容为该 Ring 上状态为 `identified_no_part` 的 Gap，每条带 `necessity: necessary | unnecessary` 与 deletion 测试一句话；lifecycle 既有空白登记与本次新识别的 Gap 同列不分级 ← PSL-017, PSL-002
- [F-12] 报告有一个 `run_evidence` 节：本次审计作为一次运行走过的 Part 状态路径、每道 Gate 的 `signer / signer_kind / authorization_ref`、以及本次发现的被审 Part 源码问题的外部去向（skill-issues 文件路径）；`signer_kind` 为 `delegated_agent` 时报告不得渲染为"人签" ← PSL-010, PSL-006, PSL-003
- [F-13] 检查脚本的接口是 `check(audit.yaml) → exit 0 | 1`，exit 0 当且仅当：Ring 集合 = {R0…R8, spine} ∧ 每 Part 四维齐 ∧ 每维 `psl_ids` 非空且都在 PSL-001..017 内 ∧ 每 Ring 的 `missing` 键存在 ∧ 每个 `identified_no_part` 的 Gap 都出现在某 Ring 的 `missing` 中 ∧ 无 Artifact 有两个 producer；预算、终止、阈值都在脚本里，不靠审计者记忆 ← PSL-004, PSL-015, PSL-001
- [F-14] 检查脚本对报告的 exit 0 只有在同一次运行里对"删掉任一 Ring 的变体"给出 exit 1 之后才算证据，这次变体运行的记录写进 `run_evidence`；没有变体记录的 exit 0 在报告里标 `uncalibrated` ← PSL-007, PSL-010
- [F-15] 每条 Finding 带 `disposition: fix_list | issue | none`，报告末尾的清单只是按 `disposition` 对 Finding 的分组视图，不是独立实体；`naming` 维为 `misfit` 的 Finding 的 disposition 只能是 `issue`（变更提案）或 `none`，不能直接落为对 Part 的重命名 ← PSL-014, PSL-013

## 交互与消歧

- [F-20] 两个 Part 被疑重复时，Finding 的 evidence 并列两者的 Artifact 记录：Artifact 不同 → verdict 写 `distinct_exits`（同一判据的两个出口）；Artifact 相同 → 两者都写 `merge_candidate`；不用名字相似度或功能描述相似度裁 ← PSL-001
- [F-21] `needed` 维上 deletion 测试与"流水线闭合所需"给出相反答案时，verdict 写 `contested`，evidence 并列两句理由，adjudication 留空等 G1/G3 人裁，审计者不折成单一答案 ← PSL-002, PSL-006
- [F-23] 审计再次运行时，与上一次 `fingerprint`（Part + 四维 verdict）完全相同且状态未变的 Finding 不重复进报告正文，而是在 `run_evidence` 记为 `no_progress` 并升级为 disposition `issue`；连续相同即换层信号 ← PSL-008, PSL-012

## 明确不做（从规律推出的否定）

- [F-90] 不做布尔 `implemented: true/false` 字段，不做 ✓/✗ 勾叉列，audit.yaml schema 里不允许出现布尔型的实现判定 ← PSL-010
- [F-91] 不在审计运行内执行任何 Part 重命名，不生成重命名 diff；名字建议止于 Finding 的 `suggested_name` 与 disposition `issue` ← PSL-014, PSL-013
- [F-92] 不以"某 Ring 上 Part 数量少 / 覆盖率低"生成任何补配件建议；`missing` 节每条必须指向一个带 `atoms` 的 Gap 记录，没有 Gap ID 的"缺少"不进 audit.yaml ← PSL-002, PSL-016
- [F-93] 审计运行内不修改任何被审 Part 的 SKILL.md / gate.json / 脚本，也不为已识别的 `identified_no_part` Gap 新建 Part；两者只以 Finding 的 evidence 与 disposition 落地 ← PSL-003, PSL-017

## 验收挂钩（每条形态决策至少被 PSL Acceptance 一条检到；A1–A7 按 PSL Acceptance 节顺序）

| F-id | 挂钩 | F-id | 挂钩 |
|---|---|---|---|
| F-01 | A1, A4 | F-14 | A6 |
| F-02 | A4 | F-15 | A3, A5 |
| F-03 | A3 | F-20 | A2 |
| F-04 | A1, A5 | F-21 | A5 |
| F-05 | A2 | F-23 | A7（弱挂钩：仅经 run_evidence 可检） |
| F-06 | A1, A4, A6 | F-90 | A4 |
| F-07 | A7 | F-91 | A3 |
| F-10 | A1, A6 | F-92 | A5 |
| F-11 | A5 | F-93 | A7（弱挂钩：仅经 run_evidence 的去向路径可检） |
| F-12 | A7 | — | — |
| F-13 | A6 | — | — |

## PSL 欠定

- **Proposal（提案）**：Workflow φ 与 UI Contract 都要求"末尾提案清单，每条有去向"，但 Domain Model 没有 Proposal 实体；本稿把它降为 Finding 的 `disposition` 字段（F-15）。若提案需要自己的 owner / 状态 / 生命周期（如 issue 已开 / 已关），就需要一个 PSL 目前没有的实体。
- **Evidence（证据）**：State Machine 说 Finding 要"有证据（gate.json / smoke 行 / 文件路径 / PSL-ID）"，但证据不是实体，四种证据形态也没有统一的记录形状；本稿把它写成每维的 `evidence[]` 自由字符串（F-01），机器只能检非空，检不了"这条证据是否指向真实文件"。
- **Signer / Authorization（签字人 / 代签授权）**：Acceptance 要求每道门的签字人与代签授权记录可见，但两者都不是 Domain Model 实体；本稿把它们写成 adjudication 的字段（F-07、F-12）。代签授权本身该长什么样（谁授权、授权到哪一步、能否撤回）PSL 未给。
- **Run（本次运行）**：Mental Model 说"审计本身是一次 sdlc 运行"，F-12 / F-14 / F-23 都依赖"本次运行"这个容器（状态路径、变体运行记录、上次运行的指纹），但 PSL 没有 Run 实体，也没有说两次运行之间的 Finding 如何关联；F-23 的 `fingerprint` 定义是本稿即兴，属承重槽。
- **脊柱是否是一个 Ring**：Domain Model 把脊柱与 R0–R8 并列写在 Ring 一格里，UI Contract 写"R0–R8 + 脊柱"；本稿按"脊柱是一条 Ring 记录（id=spine）"处理（F-10、F-13），若脊柱其实是跨 Ring 的容器（Part 可同时属脊柱与某 Ring），Ring CONTAINS Part 的 1:N 基数就不成立。
- **Gate 与 Loop 的关系**：Loop 有 generator / verifier / stop，verifier 显然与 Gate 重叠，但 PSL 没说 Loop 的 verifier 是否就是某个 Gate；本稿的 DOS 提案未在两者间建关系。
