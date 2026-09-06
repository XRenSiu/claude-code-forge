# 形态草案 — sdlc-ring-audit（合并稿，供 G1 裁决）

> 每条决策一行，形如 `- [F-nn] <决策> ← PSL-xxx[, PSL-yyy]`。无引用的决策不允许存在。
> 本稿由三次隔离推导（derived/v1、v2、v3）按语义对齐合并：一致的决策直接采；分歧点带 `[D-n]` 标记并给出**临时取向**，
> 最终取向由 G1 定（见 divergence.md）。签字后本文件即功能文档；sha256 进 `g1-record.md`。

source_psl: plugins/sdlc/dogfood/ring-audit/PSL-sdlc-ring-audit.md
derivation_run: merged from 3 of 3

## 实体与数据形态

- [F-01] Finding 与 Part 一对一，固定四维 `missing / needed / implemented / naming`，每维是 `{verdict, psl_ids[≥1], evidence[≥1]}` 三元组；缺任一维、任一维 psl_ids 为空或 evidence 为空即为非法记录，停在候选态 ← PSL-002, PSL-003, PSL-010, PSL-014, PSL-017
- [F-02] `implemented.verdict` 是枚举 `declared | compiled | verified`，每个已达态各带一条证据路径（SKILL.md 路径 / verify 脚本 + gate.json / 行为层运行记录），未达态显式写 `not_reached: <缺什么>`；verified 态另附 `calibrated: bool`；空白态归 `missing` 维；整份 audit.yaml 不出现布尔型"已实现" `[D-1 临时取向：三态 + 两个边态，待 G1]` ← PSL-010, PSL-007
- [F-03] `naming` 维是复合值 `{provenance: authored | adopted, artifact_or_position: <名>, fit: fits | misfit, suggested_name?, rename: false}`；`rename` 为常量 false，存在的目的是让检查脚本能拒绝任何 true；adopted 且与上游同名的 Part 判 fits，即使名字不是产物名 ← PSL-014
- [F-04] Gap 记录持有 `atoms ⊆ {Knowledge, Capability, Judgment, Control}` 与状态 `identified_no_part | has_part`，以及 `necessity: necessary | unnecessary` 与一句 deletion 测试；Part 声明填充但 atoms 为空集 → 其 Finding 的 `needed.verdict = overfill`；Gap 归属于 Ring，落在每个 Ring 自己的 `missing` 键下 `[D-2 临时取向：每 Ring 的 missing，待 G1]` ← PSL-016, PSL-002, PSL-017
- [F-05] Artifact 记录持有唯一 `producer: <Part>`；同一 Artifact 名出现两个 producer 时，两个 Part 的 Finding 都标 `needed.verdict = merge_candidate: <另一 Part>`，审计者不当场裁掉一个；产物为 0 的 Part 记 `role ∈ {gate, orchestrator}` 说明它为何不生产 ← PSL-001
- [F-06] Artifact 记录持有 `checked_by: [<Gate>...]`，Gate 记录带 `kind: script | human`（human 仅 G1 / G2 / G3）；`checked_by` 为空的 Artifact 使其 producer 的 `implemented` 不得高于 `declared`，evidence 写 `no_gate`；审计者不得以"读了代码觉得能跑"抬到 compiled `[D-3 临时取向：无 Gate ⇒ 最高 declared，待 G1]` ← PSL-015, PSL-006, PSL-010
- [F-07] Finding 带状态 `candidate | evidenced | adjudicated` 与追加式 `adjudications[]`，每条含 `gate: G1 | G3, signer, signer_kind: human | delegated_agent, authorization_ref`；推翻不改写原判定，只追加一条带 `supersedes` 的新记录 ← PSL-005, PSL-006, PSL-003
- [F-08] Part 记录 `loop: loops.yaml#<id> | null`，null 必附 `loop_reason`；只写引用，不复述环契约内容 ← PSL-011

## 界面 / 接口形态

- [F-10] 报告按 Ring 分节（R0–R8 各一节 + 脊柱一节，脊柱按一条 Ring 记录处理），每节一张表、每 Part 一行、四列判定、每格内联 PSL-ID；没有 Part 的 Ring 节仍出现并写"无 Part" ← PSL-011, PSL-010, PSL-002, PSL-014
- [F-11] 报告必有"缺少"一节，为空也保留并写"本次无"；每条 = Gap 原子 + 所在 Ring + 必要性 + deletion 一句话 + 去向；两类缺少（`source: lifecycle_blank | newly_identified`）带标签、同表不混排 `[D-4 临时取向：分标签，待 G1]` ← PSL-017, PSL-002
- [F-12] 报告是 `audit.yaml` 的投影，两者同目录，报告头部写 yaml 与检查脚本的相对路径；不一致时以 yaml 为准；`audit.yaml` 顶层为 `rings:` 列表，每项 `{id, question, parts[], missing[]}` `[D-7 临时取向：rings 列表，待 G1]` ← PSL-015, PSL-011
- [F-13] 检查脚本接口 `check_audit.py <audit.yaml> [--psl <PSL.md>]`，exit 0 当且仅当：Ring 集合 = {R0…R8, spine} ∧ 每 Part 四维齐 ∧ 每维 psl_ids 非空且都在 PSL 规律索引内 ∧ 每 Ring 有 `missing` 键 ∧ 每个 identified_no_part 的 Gap 出现在某 Ring 的 missing 中 ∧ 无 Artifact 有两个 producer ∧ `rename` 全为 false ∧ 人签门有 signer；失败 exit 1 并打印失败谓词名与定位；脚本只核对 signer 存在，不代签 ← PSL-004, PSL-015, PSL-001, PSL-006
- [F-14] 检查脚本对报告的 exit 0 只有在同一次运行里对"删掉任一 Ring 的变体"给出 exit 1 之后才算证据，变体运行记录写进 run_evidence；没有变体记录的 exit 0 标 `uncalibrated` `[D-5 临时取向：采 v3，待 G1]` ← PSL-007, PSL-010
- [F-15] 报告必有 `run_evidence` 节：本次审计作为一次运行走过的 Part 状态路径、每道门的 `signer / signer_kind / authorization_ref`、skill 源码问题的外部去向（skill-issues.md 路径）；`signer_kind = delegated_agent` 时不得渲染为"人签"；审计自身的 implemented 只写到 compiled ← PSL-010, PSL-006, PSL-003
- [F-16] 每条 Finding 带 `disposition: fix_list | issue | none`，报告末尾的提案清单是按 disposition 对 Finding 的分组视图（每条 `{id, source: Finding-id | Gap-id, destination, text}`），不是独立实体；没有 source 的提案不允许存在；`naming.fit = misfit` 的 disposition 只能是 `issue` 或 `none` ← PSL-014, PSL-013, PSL-003

## 交互与消歧

- [F-20] 两个 Part 疑似重复时，evidence 并列两者的 Artifact 记录（各自产物、各自消费者）：Artifact 不同 → verdict `distinct_exits`（同一判据的两个出口）；相同 → 两者都 `merge_candidate`；名字或描述相似本身不构成重复 ← PSL-001
- [F-21] `needed` 以 deletion 测试为默认裁决；与"流水线闭合所需"结论相反时，verdict 写 `contested`、evidence 并列两句理由、`necessity_conflict: true`，adjudication 留空交 G1 / G3，检查脚本对带 conflict 标记的 contested 放行 ← PSL-002, PSL-006
- [F-22] 有 SKILL.md 但无 verify 脚本、无门的 Part，`implemented` 显示 declared，且 compiled / verified 两态各显式写 `not_reached` 及缺什么（无脚本 / 无门 / 无行为层运行）；不允许只写 declared 而省掉后两态 ← PSL-010, PSL-017, PSL-015
- [F-23] "名字合适吗"的回答里来路列在产物与贴合之前：misfit 时给 `suggested_name` 并显示"不重命名"字样，无论 authored 还是 adopted ← PSL-014

## 明确不做（从规律推出的否定）

- [F-90] 不产出 `{skill_name, exists}` 形状的勾叉清单；一张只有 ✓/✗ 的表即使内容全对，检查脚本也因每维缺 psl_ids / evidence 而 exit 1 ← PSL-010, PSL-002
- [F-91] 审计运行内不重命名任何 Part、不生成重命名 diff；名字建议止于 `suggested_name` 与 disposition `issue` ← PSL-014, PSL-013
- [F-92] 不以"某 Ring 上 Part 数量少 / 覆盖率低"生成任何补配件提案；`missing` 每条必须指向一个带 atoms 的 Gap 记录；本次识别出的缺少不在审计内实现，只登记并给 issue 去向 ← PSL-002, PSL-016, PSL-017
- [F-93] 审计运行内不修改任何被审 Part 的 SKILL.md / agent.md / 脚本 / gate.json，也不为已识别的 Gap 新建 Part；被审目录在审计前后 git diff 为空 ← PSL-003, PSL-017

## 验收挂钩（每条形态决策至少被一条 Acceptance 检到；A1–A7 按 PSL Acceptance 节顺序）

| Acceptance | 检到的决策 |
|---|---|
| A1 问"R6 有哪些配件、各填什么缺口" → Gap / Artifact / Gate / Loop + 无 Part 的 Gap | F-01, F-04, F-05, F-06, F-08, F-10, F-11 |
| A2 问"pr-review 与 code-reviewer 是否重复" → Artifact 对照 + 裁决 | F-05, F-20 |
| A3 问"donewhen-extract 名字合适吗" → 来路 / 产物 / 贴合 / 建议名 + 不重命名 | F-03, F-23, F-91 |
| A4 问"implement 已实现了吗" → 三态各证据，不返回布尔 | F-02, F-22, F-90 |
| A5 问"哪些环节缺配件" → lifecycle 空白 ∪ 新识别，每条必要性 + deletion 一句 | F-04, F-11, F-92 |
| A6 问"能不能被机器检" → audit.yaml + 脚本路径，删环变体 exit 1 | F-12, F-13, F-14 |
| A7 问"审计者是谁、用什么身份签的门" → 签字人与代签授权可见 | F-07, F-15 |
| （γ 约束，弱挂钩）审计不改被审对象 | F-16, F-21, F-93 — 建议补一条 Acceptance（见 divergence.md 欠定末条） |

## PSL 欠定

见 `divergence.md` 的"PSL 欠定"节（十一条：Proposal、Evidence、Signer / Authorization、Run、skill 源码问题、Ring.question、Gap 反向基数、脊柱是否 Ring、Gate 与 Loop.verifier、PSL 规律是否实体、F-93 的验收挂钩）。本稿未把其中任何一个当作实体使用；v3 独有的跨运行指纹决策（F-23 in v3）因依赖不存在的 Run 实体而未进合并稿。
