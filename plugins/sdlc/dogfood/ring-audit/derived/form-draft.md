# 形态草案 — sdlc-ring-audit（第二轮，定向重推稿，供 G1 第二轮裁决）

> 每条决策一行，形如 `- [F-nn] <决策> ← PSL-xxx[, PSL-yyy]`。无引用的决策不允许存在。
> 本稿是 G1 第一轮否决（归因 rule_error，PSL 改至 v2）后的 n=1 定向重推：输入 = PSL v2 + `g1-record.md` 的逐条裁决。
> round1 合并稿（derived/round1/）里 G1 接受的决策原样保留；G1 裁定的决策按裁决改写；每条改动的落点见 `divergence.md` 的对照表。
> 第三轮（本稿）：G1 第二轮否决（归因 derivation_error，PSL 不动；PSL v2.1 只做了非阻塞措辞整理"报告人审即 G3"）后只改 F-05 / F-07 / F-08 与建议项 F-03，其余决策与第二轮逐字节相同；逐 F 行 diff 见 `round-diff.md`。
> 只引用形态层规律（PSL-001…007、010、011、013…017）；PSL-008 / 009 / 012 是内容层，由 Assessment.needed 引用，不在本稿出现。
> 真正来源是 UI Contract / Acceptance / Design Principles 的决策，借最近的形态层规律并在决策末尾注 `(via UI-n / A-n / DP-n)`，让引用不装饰。
> 签字后本文件即功能文档；sha256 进 `g1-record.md`。

source_psl: plugins/sdlc/dogfood/ring-audit/PSL-sdlc-ring-audit.md
derivation_run: 1 of 1 (targeted re-derivation after G1 round 1; round 3 applies G1 round-2 rulings to F-05 / F-07 / F-08 and the recommended F-03 relaxation)

## 实体与数据形态

- [F-01] Assessment 与 Part 一对一，固定三维 `needed / implemented / naming`，每维是 `{verdict, psl_ids[≥1], evidence[≥1]}` 三元组，每条 evidence 是值对象 `{kind ∈ {file, gate_json, smoke, run_record}, ref}`（file → 路径；gate_json → 路径#键；smoke → 冒烟记录行；run_record → 账本事件 id）；缺任一维、psl_ids 为空、evidence 为空或某条 evidence 缺 kind / ref 即为非法记录，停在候选态；没有 `missing` 维——"缺少"由 Ring.missing 回答；判定单位一律叫 Assessment，不叫 Finding ← PSL-002, PSL-003, PSL-010, PSL-014, PSL-017
- [F-02] `implemented.verdict` 是枚举 `declared | compiled | verified`，每个已达态各带一条 evidence（declared → {file, SKILL.md / agent.md 路径}；compiled → {gate_json, verify 脚本 + gate.json static_only} 或被门挡的证据；verified → {run_record 或 smoke, 行为层运行}），未达态显式写 `not_reached: <缺什么>`；verified 时另附 `calibrated: bool`，false 渲染为"已验证（未校准）"；"空白"不是 implemented 的态，空白是所在 Ring 的 missing 里的一条 Gap；整份 audit.yaml 不出现布尔型"已实现" ← PSL-010, PSL-007
- [F-03] `naming` 维是复合值 `{provenance: authored | adopted, artifact_or_position: <名>, fit: fits | misfit, suggested_name?, rename: false}`；fit 对每个 Part 都判，判据只有一条：名字与独占 Artifact 的名或所在位置名同词干或同义 → fits（不要求字面相等：calibrate / dos-extract / retro 这类同词干的名字是 fits，否则 naming 列变噪声），否则 misfit（动词短语、上游领域词与产物不符都算 misfit）；provenance 不参与 fit 判定，只决定 misfit 的去向理由（adopted → "不重命名：上游同步 / 内部引用"，authored → "不重命名：另开 G2 变更提案"）；`rename` 为常量 false，存在的目的是让检查脚本能拒绝任何 true ← PSL-014
- [F-04] Gap 记录是值对象 `{atoms ⊆ {Knowledge, Capability, Judgment, Control}, source ∈ {lifecycle_blank, newly_identified, unenforced_rule}, necessity ∈ {necessary, unnecessary, contested}, deletion_test: 一句话, evidence[≥1]}`，不存储"有没有 Part 填"——它由 `Part FILLS Gap` 边派生（无边 = 出现在所在 Ring 的 missing；有边 = 从 missing 移出），一个 Gap 可被多个 Part 填（N:N，六个审查 skill 共填一个 Judgment 缺口是常态）；Gap 归属于恰一个 Ring；Part 声明填充但 atoms 为空集 → 其 Assessment 的 `needed.verdict = overfill` ← PSL-016, PSL-002, PSL-017
- [F-05] Artifact 记录 `{id: graph.yaml Node.writes 的路径模式 ∪ ARCHITECTURE §1 产物列, producer: <Part>, alternatives_of?: <stage>}`；同一 Artifact 出现两个 producer 且两者不是同阶段条件替代时，两个 Part 的 Assessment 都标 `needed.verdict = merge_candidate: <另一 Part>`，审计者不当场裁掉一个；同阶段条件替代由三个条件共同定义、数据源是 graph.yaml、缺一不算：(a) 两个 Part 出现在同一 `stage.<x>` 节点的 handled_by 里；(b) 它们之间由一条带 `when` 守卫的 `conditional` 边选择执行者；(c) 它们写同一 schema 的 Artifact；implement / card-implementer / ratchet 三条件全满足（graph.yaml L29 stage.implement handled_by；L320–321 从 implement 出发的两条 conditional 边）→ 记 `alternatives_of` 并豁免，不算第二生产者；donewhen-extract / acceptance-spec 只满足 (a)（L26 stage.contract），无 conditional 边且 v1 ≠ v2 形状 → 不豁免，触发 merge_candidate（与现状 Q008 一致）；产物为 0 的 Part 记 `role ∈ {gate, orchestrator}` 说明它为何不生产 ← PSL-001
- [F-06] Artifact 记录 `checked_by: [<Gate>...]`，Gate 记录带 `kind: script | human`（human 仅 G1 / G2 / G3），报告与 audit.yaml 把 script 渲染为"闸"、禁止渲染为"门"；`checked_by` 为空的 Artifact 有两个后果同时成立：其 producer 的 `implemented` 不得高于 `declared`（evidence 写 {file, <Part 目录>} 并注 `no_gate`，审计者不得以"读了代码觉得能跑"抬到 compiled），且一条 Control 原子的 Gap `{source: newly_identified}` 进该 Artifact 所在 Ring 的 missing ← PSL-015, PSL-010, PSL-016, PSL-006
- [F-07] kind=human 的 Gate 记录带 `signer / signer_kind ∈ {human, delegated_agent} / authorization_ref`（delegated_agent 时必填）；Assessment 带状态 `candidate | evidenced | adjudicated` 与追加式 `adjudications[]`，每条 `{gate: G3, signer, signer_kind, authorization_ref, supersedes?}`；裁决 Assessment 的 Gate 只能是 kind=human 的 G3——报告人审就是 G3 的内容（"这个 Part 的 Gap 归类对不对"是 G3 裁的 human AC），不是第四道门；报告合入后再推翻某条 Assessment 是逃逸缺陷，喂下一次审计 Run 的新 Assessment 并以 `supersedes` 关联；G1 不出现在 adjudications 里（G1 裁的是本形态草案，那时一条 Assessment 都不存在）；推翻不改写原判定，只追加一条带 `supersedes` 的新记录 ← PSL-005, PSL-006
- [F-08] Part 记录 `{id, kind ∈ {skill, agent, asset, human_gate}, ring, ring_evidence, provenance, loop}`；kind 里没有 script——skill 目录下的脚本是该 skill 的 Gate（checked_by）或 Capability，不是独立 Part；stage 节点不是 Part；`ring` 不手填，从 graph.yaml `Node.role` 经现状本体 composition.Ring 的映射推出（world→R0 … learning→R8，orchestrator→spine），`ring_evidence` 写 graph.yaml 行号；human_gate 覆盖 graph.yaml 全部五个 kind=human 节点，不只三道门：持有 Gate 对象的三个归它检的 Artifact 所在的 Ring（G1→R0、G2→R2、G3→R6），human.merge → R7、human.harness-review → R8（ARCHITECTURE §1 表 R7 / R8 门闸列），ring_evidence 写 graph.yaml 行号（L239–243、L269–273），"文档写三道门、数据有五个人节点"的出入成为这两个 Part 的一条 Assessment（现状 Q004），不由本稿调和；human_gate 不归 spine；spine 上的 Part 是 sdlc skill 与 graph / loops / routing / triggers 四个数据资产；没有图节点的 Part（agents/pr-reviewer.md、四个数据资产）写 `ring_evidence: no_node` 并按 ARCHITECTURE §1 落环 ← PSL-011, PSL-015, PSL-006
- [F-09] Part 记录 `loop: loops.yaml#<id> | null`；只在 Part 是 graph.yaml 某条 loop_back 边的端点或某 Loop 的 generator / verifier 而 loop 仍为 null 时才必附 `loop_reason`，其余 Part 的 null 不需要理由（环契约属于圈，不属于每个配件）；只写引用，不复述环契约内容；Loop.verifier 若恰是脚本，它同时也是一道闸，两个角色各自引用同一实体，不重复计数 ← PSL-011, PSL-015

## 界面 / 接口形态

- [F-10] 报告按 Ring 分节（R0–R8 各一节 + 脊柱一节，脊柱是 `id=spine` 的一条 Ring），每节一张表、每 Part 一行、三列判定（needed / implemented / naming），PSL-ID 做脚注不挤进格内；每环表末尾是该环 missing 里的 Gap 行，渲染标"（缺少）"并带来源标签；没有 Part 的 Ring 节仍出现并写"无 Part"；implemented 列只出现三态之一 (via UI-1) ← PSL-017, PSL-010
- [F-11] 每个 Ring 的 `missing` 是 Gap 列表（可为空，空时写 `[]` 且报告写"本次无"），取代全局"缺少"节；每条 = atoms + source 标签 + necessity + deletion 一句话 + disposition，三种来源同表带标签列、不混排不省略：lifecycle_blank 的 evidence 是 lifecycle.md 制品映射表或 ARCHITECTURE §7 的那一行；unenforced_rule 的 evidence 是 dos.yaml 里 `enforced_by ∈ {user_workflow, not_enforced}` 的规则 id（R001 / R008 / R010 / R017）；newly_identified 的 evidence 是引出它的 Assessment 或无 Gate 的 Artifact；本次识别的缺少不在审计内实现 (via A5) ← PSL-017, PSL-002, PSL-016
- [F-12] 报告是 `audit.yaml` 的投影，两者同目录，报告头部写 yaml 与检查脚本的相对路径，不一致时以 yaml 为准；`audit.yaml` 顶层为 `rings:` 列表，每项 `{id, question, parts[], missing[]}`，`question` 取 ARCHITECTURE §1 表"问题"列，`parts[].assessment` 为 `{needed, implemented, naming}`；只有 audit.yaml 带全字段（Evidence 结构、adjudications、ring_evidence），人读报告不带 (via UI-2) ← PSL-015
- [F-13] 检查脚本接口 `check_audit.py <audit.yaml> [--psl <PSL.md>]`，exit 0 当且仅当：Ring 集合 = {R0…R8, spine} ∧ 每 Part 三维齐 ∧ 每维 psl_ids 非空且都在 PSL 规律索引内 ∧ 每维 evidence 非空且每条 kind 在枚举内、ref 非空 ∧ 每 Ring 有 `missing` 键 ∧ 每个无 FILLS 边的 Gap 出现在其 Ring 的 missing 中 ∧ 无 Artifact 有两个非 `alternatives_of` 的 producer ∧ `rename` 全为 false ∧ human Gate 有 signer 且 delegated_agent 附 authorization_ref ∧ 无 script Gate 被渲染为"门"；失败 exit 1 并打印失败谓词名与定位；脚本只核对 signer 存在，不代签；审计是否完成由这个 exit 码给出，审计者不得在报告里自宣"完成" ← PSL-015, PSL-001, PSL-006, PSL-004
- [F-14] 检查脚本对报告的 exit 0 只有在同一次运行里对"删掉任一 Ring 的变体"给出 exit 1 之后才算证据，两次运行记录都写进 run_evidence；没有变体记录的 exit 0 标 `uncalibrated`、不当证据，A6 的回答必须如实带出这个标记 (via A6) ← PSL-007, PSL-010
- [F-15] 报告必有 `run_evidence` 节：本次审计作为一次 sdlc Run 走过的状态机路径（只引用 Run 的 slug / state.json / ledger 路径，不重建 Run）、每道门的 `signer / signer_kind / authorization_ref`、外部证据的替代品（检查脚本机械检查 + 代签 agent 独立读）标 `evidence_kind: substitute` 且不得渲染成用户验证、仅对本次 dogfood 有效、skill 源码问题的去向路径（skill-issues.md，它是 Run 账本事件的投影，不是 Part 的 implemented 逆向流转证据）；`signer_kind = delegated_agent` 时不得渲染为"人签"；审计自身的 implemented 只写到 compiled (via UI-3, A7) ← PSL-006, PSL-010, PSL-007
- [F-16] Assessment 与 Gap 各带 `disposition: fix_list | issue | none`，报告末尾的提案清单是按 disposition 的分组视图（每条 `{id, source: Assessment-id | Gap-id, destination, text}`），不是独立实体；没有 source 的提案不允许存在；`naming.fit = misfit` 的 disposition 只能是 `issue` 或 `none`；跨 Part 的提案（如合并两个 Part）以两个 source 表达，这是 Proposal 未建实体前的权宜；提案只到人手里，审计运行内不执行任何提案 ← PSL-014, PSL-013, PSL-002
- [F-17] 扩展 F-13：`check_audit.py` 接口加 `[--rings R0,..] [--required-parts a,b,..]`；谓词加 `required_parts_missing`（given 里列出的 Part 名不在 audit.yaml 对应 Ring 的 parts 里 → 计数 + exit 1 `required_part_missing`）、`parts_total`（全部 Ring 的 Part 数）；`parts_without_assessment` 受 `--rings` 限定；不改任何既有谓词，F-13 的 exit 0 条件随之并含"给出 `--required-parts` 时 `required_parts_missing = 0`" ← PSL-015, PSL-004

## 交互与消歧

- [F-20] 两个 Part 疑似重复时，evidence 并列两者的 Artifact 记录（各自产物、各自消费者）：Artifact 不同 → verdict `distinct_exits`（同一判据的两个出口，如 pr-review 的 GitHub review 与 code-reviewer 的 findings.yaml）；相同且不是同阶段条件替代 → 两者都 `merge_candidate`（如 donewhen-extract 与 acceptance-spec 都写 done_when.yaml 且形状不同，该触发）；相同但是同阶段条件替代 → `alternatives_of`，不触发；名字或描述相似本身不构成重复 (via A2) ← PSL-001
- [F-21] `needed` 以 deletion 测试为唯一裁决标准，且在生命周期高度上读："撤掉它，这条流水线会不会产出错的或不可验证的东西"，而不是"引擎会不会拒绝往下走"；"流水线闭合所需"不是第二标准，是 deletion 失败的一种 evidence（如撤掉 psl-derive，引擎照样推导，但 G1 无物可裁，世界层错误延迟到验收才暴露 = 会做错）；两者读完仍冲突的残余 verdict 写 `contested`、evidence 并列两句理由、`necessity_conflict: true`，adjudication 留空交 G3 / 报告人审，检查脚本对带 conflict 标记的 contested 放行 ← PSL-002, PSL-006
- [F-22] 有 SKILL.md 但无 verify 脚本、无门的 Part，`implemented` 显示 declared，且 compiled / verified 两态各显式写 `not_reached` 及缺什么（无脚本 / 无门 / 无行为层运行）；不允许只写 declared 而省掉后两态，也不允许因"有 SKILL.md 且描述完整"抬到 compiled (via DP-1) ← PSL-010, PSL-017, PSL-015
- [F-23] "名字合适吗"的回答里来路列在产物与贴合之前，随后是 fit 判定，misfit 时给 `suggested_name` 并显示"不重命名"字样及理由；authored 与 adopted 都给出 fit 判定，adopted 不是免检（如 donewhen-extract 收编自 qanat、产 done_when.yaml → fits；ratchet 收编自 ratchet、先查它独占什么产物再判） (via A3, DP-3) ← PSL-014
- [F-24] ARCHITECTURE §1 表与 graph.yaml `Node.role` 对某 Part 的归属不一致（如门 / 编排者 vs 脊柱），或某 Part 有文件无节点，直接成为一条 Assessment（`ring_evidence` 注 `role_conflict` 或 `no_node`，两个来源并列），审计者不在审计里调和两份数据，也不改任何一份 ← PSL-011, PSL-003

## 明确不做（从规律推出的否定）

- [F-90] 不产出 `{skill_name, exists}` 形状的勾叉清单；一张只有 ✓/✗ 的表即使内容全对，检查脚本也因每维缺 psl_ids / evidence 而 exit 1 ← PSL-010, PSL-002
- [F-91] 审计运行内不重命名任何 Part、不生成重命名 diff；名字建议止于 `suggested_name` 与 disposition `issue`，重命名是另一次 G2 变更提案的事 ← PSL-014, PSL-013
- [F-92] 不以"某 Ring 上 Part 数量少 / 覆盖率低"生成任何补配件提案；`missing` 每条必须指向一个带 atoms 与 source 的 Gap 记录；本次识别出的缺少只登记并给 issue 草稿，不在审计内实现 (via DP-2) ← PSL-002, PSL-016, PSL-017
- [F-93] 审计运行内不修改任何被审 Part 的 SKILL.md / agent.md / 脚本 / gate.json，也不为已识别的 Gap 新建 Part；被审目录（plugins/sdlc/skills、agents、docs）在卡提交里 git diff 为空；运行中为过门而修的 verifier bug 记为账本 `deviation`、单独提交、不算卡提交；问题进 skill-issues.md 与提案 (via A8) ← PSL-003, PSL-017, PSL-005
- [F-94] 不把 kind=script 的 Gate 渲染成"门"，"门"字只用于 kind=human 的 G1 / G2 / G3；机械闸一律写"闸"，audit.yaml 里以 `kind` 字段区分而不以名字区分 ← PSL-006, PSL-015
- [F-95] 审计词表里不出现 Finding 作为判定单位——Finding 是 R6 六个审查 skill 与 pr-review 的产物名（findings.yaml），本次审计要把它列为 Artifact；同一份报告里一个名字不同时指审计单位与被审产物，名字与所指贴合的判据同样用到审计自己的词表上 ← PSL-014

## 验收挂钩（每条形态决策至少被一条 Acceptance 检到；A1–A8 按 PSL v2 Acceptance 节顺序）

| Acceptance | 检到的决策 |
|---|---|
| A1 问"R6 有哪些配件、各填什么缺口" → Gap 原子集合、Artifact、Gate（闸 / 门分清）、Loop + 该环 missing | F-01, F-04, F-05, F-06, F-08, F-09, F-10, F-11, F-94, F-95 |
| A2 问"pr-review 与 code-reviewer 是否重复" → Artifact 对照 + 裁决 | F-05, F-20 |
| A3 问"donewhen-extract 名字合适吗" → 来路 / 产物 / 贴合 / 建议名 + 不重命名（收编同样给贴合） | F-03, F-16, F-23, F-91 |
| A4 问"implement 已实现了吗" → 三态各证据，不返回布尔 | F-02, F-22, F-90 |
| A5 问"哪些环节缺配件" → 每 Ring 的 missing：三种来源带标签，每条必要性 + deletion 一句 | F-04, F-11, F-16, F-21, F-92 |
| A6 问"能不能被机器检" → audit.yaml + 脚本路径，删环变体 exit 1 且有记录 | F-12, F-13, F-14, F-17 |
| A7 问"审计者是谁、用什么身份签的门" → 签字人、signer_kind、代签授权可见，代签不渲染为人签 | F-07, F-15 |
| A8 问"审计动过被审目录吗" → 被审目录 git diff 为空 + skill-issues.md 路径 | F-93, F-15, F-24 |

## PSL 欠定

（只列 PSL v2 之后仍无依据的项；round1 的十二条欠定去向见 g1-record.md"PSL 欠定 12 条的去向"表，本稿全部照裁决落地。）

- **Proposal（提案）** — 仍是 Assessment.disposition 与 Gap.disposition 的投影（F-16）；跨 Part 的提案（合并两个 Part）本稿以两个 source 表达，是权宜。建议：留 open_questions（PSL v2 已列），若提案需要 owner / 状态再升实体。
- **UI-n / A-n / DP-n 引用锚** — verifier 只认 PSL-NNN；F-10 / F-11 / F-12 / F-14 / F-15 / F-20 / F-22 / F-23 / F-92 / F-93 借最近形态层规律并注 `(via …)`。建议：verifier 放开锚格式（skill-issues I-19），或 /psl 把这三层编号纳入规律索引。
- （已裁，不再是欠定）第二轮草案曾把"报告人审是不是一道 Gate"与"'同阶段'的判据来源"列为欠定；G1 第二轮裁为 derivation_error（PSL 不动）：报告人审即 G3（F-07），同阶段 = 同一 stage 节点 handled_by + conditional 边选执行者 + 同 schema Artifact（F-05）。PSL 侧仅剩非阻塞措辞建议（Workflow φ 补同阶段一句），见 g1-record.md 第二轮。
