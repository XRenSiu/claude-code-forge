# 形态草案 — sdlc-ring-audit（审计交付物的形态）

> 每条决策一行，形如 `- [F-nn] <决策> ← PSL-xxx[, PSL-yyy]`。无引用的决策不允许存在（先把常识写进 PSL 再引）。
> 签字后本文件即功能文档；sha256 进 `g1-record.md`。

source_psl: plugins/sdlc/dogfood/ring-audit/PSL-sdlc-ring-audit.md
derivation_run: 2 of 3

## 实体与数据形态

- [F-01] Finding 与 Part 一对一，固定四维 missing / needed / implemented / naming；每维是一个 `{verdict, psl_ids, evidence}` 三元组，`psl_ids` 非空且只允许规律索引里的 ID，`evidence` 是文件路径 / gate.json 字段 / smoke 行之一 ← PSL-003, PSL-007
- [F-02] `implemented.verdict` 是枚举 {declared, compiled, verified}，每一态各带一条证据路径，未达到的态写明缺什么证据（如 "L2 未跑"）而不是省略；verified 态另附 `calibrated: bool` 说明尺子是否经校准；整份 `audit.yaml` 中不出现布尔型"已实现" ← PSL-010, PSL-007
- [F-03] Part 记录 `artifact`（0 或 1 个）；检查脚本按 artifact 反查生产者，同一 Artifact 出现两个 Part 时把两条 Finding 的 `needed.verdict` 都置为 `merge_candidate`；产物为 0 的 Part 记 `role ∈ {gate, orchestrator}` 说明它为何不生产 ← PSL-001
- [F-04] Part 记录 `gaps`，取值是 {Knowledge, Capability, Judgment, Control} 的子集，每个原子附 deletion 测试一句话（"撤掉后引擎会…"）；空集时 `needed.verdict = overfill` ← PSL-016, PSL-002
- [F-05] Artifact 记录 `gates`（0..n），每条 `{kind ∈ {script, human_gate}, ref}`；script 引 verify 脚本路径或 gate.json，human_gate 引 G1 / G2 / G3；gates 为空的 Artifact 自动生成一条 Gap 进 `missing:` ← PSL-015, PSL-006
- [F-06] Part 记录 `loop`（loops.yaml#id 或 null）；null 必须带 `loop_reason`，脊柱上的 Part 允许 null 但同样要写原因 ← PSL-011
- [F-07] `naming` 维的结构是 `{origin ∈ {authored, adopted}, fit ∈ {artifact_name, position_name, mismatch}, suggested_name?, renamed: false}`；`renamed` 是常量字段，存在的目的是让检查脚本能拒绝任何 true ← PSL-014
- [F-08] `missing.verdict ∈ {present, blank}`（blank = lifecycle 登记但无承载）；没有任何 Part 的 Gap 不进 Finding，进顶层 `missing:` 节，该节必有、可为空数组，每条 Gap 带 `source ∈ {lifecycle_blank, newly_identified}`、`necessity ∈ {necessary, unnecessary}` 与 deletion 一句话 ← PSL-017, PSL-002
- [F-09] Finding 带 `status ∈ {candidate, evidenced, adjudicated}`；candidate 不写入 `audit.yaml`；adjudicated 通过追加 `adjudication: {by, accepted | overturned, note}` 实现，原四维不改写、不删除 ← PSL-005, PSL-007

## 界面 / 接口形态

- [F-10] 报告按 Ring 组织：R0…R8 各一节加"脊柱"一节，每节一张表，每个 Part 一行，四列各是 `verdict (PSL-xxx)`；没有 Part 的 Ring 节仍要出现并写"无 Part" ← PSL-011, PSL-003
- [F-11] 报告是 `audit.yaml` 的投影：两者同目录并存，报告头部写 `audit.yaml` 与检查脚本的相对路径；两者不一致以 `audit.yaml` 为准，报告不得含 `audit.yaml` 里没有的判定 ← PSL-015
- [F-12] 检查脚本的接口是 `check_audit.py <audit.yaml> [--psl <PSL.md>]`，exit 0 当且仅当：九环 + 脊柱键齐 ∧ 每个 Part 四维齐 ∧ 每维 psl_ids 非空且全部存在于 PSL 规律索引 ∧ `missing:` 存在 ∧ 无未标记的空 gaps ∧ 无未标记的多生产者 Artifact ∧ `renamed` 全为 false；失败时 exit 1 并打印失败的谓词名与定位；删掉任一环的变体必 exit 1 ← PSL-015, PSL-004
- [F-13] 报告末尾是"提案"一节，每条 `{id, source: Finding-id | Gap-id, destination ∈ {skill_fix_list, new_issue, no_action}, text}`；没有 source 的提案不允许存在；提案只写去向，不在本次运行里执行 ← PSL-003, PSL-013
- [F-14] 报告与 `audit.yaml` 都有"本次运行的证据"节：本次审计作为一次 sdlc 运行走过的 Part 状态路径、每道门的 `signer ∈ {human, proxy_agent}` 与 `authorization`（代签必附）、skill-issues 文件路径；`--autopilot` 只影响逐步确认，不使 signer 字段可空 ← PSL-006, PSL-010

## 交互与消歧

- [F-15] 两个 Part 疑似重复时，呈现为一张两列 Artifact 对照（各自产物、各自消费者），裁决只有 {not_duplicate（同判据的两个出口）, merge_candidate}；产物不同即默认 not_duplicate，不看名字相似度 ← PSL-001
- [F-16] "必要"以 deletion 测试为默认裁决；当 deletion 测试与"流水线闭合所需"结论相反时，Finding 的 `needed` 维并列两句话并置 `necessity_conflict: true`，verdict 留空交 G1 / G3 裁，检查脚本对带 conflict 标记的空 verdict 放行 ← PSL-002, PSL-006
- [F-17] "名字合适吗"的回答里，来路列在产物与贴合之前：adopted 且 mismatch 时给 `suggested_name` 并显示"不重命名"字样；authored 且 mismatch 时同样只给建议；重命名动作在这份报告的任何位置都不出现 ← PSL-014

## 明确不做（从规律推出的否定）

- [F-90] 不产出 `{skill_name, exists}` 形状的勾叉清单；一张只有 ✓/✗ 的表即使内容全对，检查脚本也因"每维缺 psl_ids / evidence"而 exit 1 ← PSL-002, PSL-010
- [F-91] 不因某环 Part 数量少而生成"补一个配件"的提案；提案的 source 只能是一个已识别的 Gap-id 或 Finding-id，"R1 显得单薄"类提案没有 source 位可填 ← PSL-002
- [F-92] 审计不修改任何被审 Part 的 SKILL.md / gate.json / verify 脚本，也不执行重命名；发现的源码问题进 skill-issues 文件与提案，被审文件在审计前后 sha256 相同 ← PSL-003, PSL-014

## PSL 欠定

- **PSL 规律（被引用的 PSL-ID）**：Finding "四维各引用 ≥ 1 条 PSL 规律"，但规律不是 Domain Model 实体；本稿把它当作字符串字段 `psl_ids`，不建对象。若要做反向索引（哪条规律被引最多）需 PSL 把它升为实体。
- **提案（Proposal）**：Workflow φ 与 Personas 要求"提案清单（每条有去向）"，Domain Model 无此实体；本稿只把它作为报告的一个节（F-13），不进 DOS objects。
- **签字人 / 代签授权（Signer）**：Acceptance 与 γ 要求门的签字人与授权可见，Domain Model 无对应实体；本稿作为 Gate 的属性（F-14）处理。
- **审计运行本身（Run）**：Mental Model 说"审计本身是一次 sdlc 运行"，但没有 Run 实体；本稿把"本次运行的证据"作为顶层节而不建对象。
- **implemented 的态数**：Domain Model 写"三态"，State Machine 写五态（含 空白、已校准）；本稿取三态进 `implemented`，空白归 `missing` 维，已校准只在 verified 时以 `calibrated: bool` 附注（F-02）。这一分配是推导者选择，PSL 未定。
