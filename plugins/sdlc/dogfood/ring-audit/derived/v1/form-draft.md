# 形态草案 — sdlc-ring-audit

> 每条决策一行，形如 `- [F-nn] <决策> ← PSL-xxx[, PSL-yyy]`。无引用的决策不允许存在（先把常识写进 PSL 再引）。
> 签字后本文件即功能文档；sha256 进 `g1-record.md`。

source_psl: plugins/sdlc/dogfood/ring-audit/PSL-sdlc-ring-audit.md
derivation_run: 1 of 3

> 本稿推导的"形态"是审计交付物的形状——报告、`audit.yaml`、检查脚本、Finding 记录——不是插件代码。
> 词表只用 PSL Domain Model 的七个实体：Ring / Part / Gap / Artifact / Gate / Finding / Loop。

## 实体与数据形态

- [F-01] `audit.yaml` 顶层按 Ring 分键（R0–R8 + 脊柱共十个键），每个 Ring 键必须出现，其下是该 Ring 的 Part 列表；只含空白态 Part 的 Ring 也保留键，不允许因"没东西"而省略 ← PSL-011, PSL-017
- [F-02] 每条 Part 记录携带四个坐标字段：`gaps`（⊆ {Knowledge, Capability, Judgment, Control}，可为空集）、`artifact`（0..1，独占）、`gates`（0..n，经 artifact 解析得到，不直接挂在 Part 上）、`loop`（0..1，loops.yaml#id） ← PSL-016, PSL-001, PSL-015, PSL-011
- [F-03] Finding 内嵌于 Part 记录、一对一，固定四个维度键 `missing` / `needed` / `implemented` / `naming`；每维是结构 {verdict, psl_ids[≥1], evidence[≥1]}，任何维度不得是裸布尔 ← PSL-010, PSL-002, PSL-014, PSL-017
- [F-04] `implemented.verdict` 取 Part 状态阶梯枚举 blank / declared / compiled / verified / calibrated；每一阶各带自己的证据路径（SKILL.md 路径 / verify 脚本 + gate.json / 行为层运行记录 / calibrate 记录），未到的阶显式写"未达"而不是省略 ← PSL-010, PSL-007
- [F-05] `naming` 维拆为 `origin`（authored / adopted）与 `fit`（fits / misfit），misfit 时附 `suggested_name`；记录里不存在任何 `rename` 动作字段，adopted 且与上游同名的 Part 判 fits，即使名字不是产物名 ← PSL-014
- [F-06] Gap 在 `audit.yaml` 是一等列表 `gaps`，每条带 `ring`、`atom`、`state`（identified_no_part / has_part）、`necessity`（needed / not_needed）与一句 deletion 测试理由；lifecycle 的空白登记同时以空白态 Part 与 identified_no_part 的 Gap 两种身份出现，不合并成一条 ← PSL-017, PSL-002, PSL-016
- [F-07] Gate 记录分两型：机械闸带 `script` 路径；人签门（G1 / G2 / G3）带 `signed_by`（人 / 代签 agent）与 `delegation_record`；Part 的逆向流转（脚本被删、门被绕）与 Finding 的裁决都作为追加的 `trace` 条目落在原记录上，不覆盖既有状态 ← PSL-006, PSL-005

## 界面 / 接口形态

- [F-10] 报告按 Ring 组织，每 Ring 一张表、每 Part 一行、四列判定（缺少 / 需要 / 实现三态 / 命名来路+贴合），每格末尾带该维引用的 PSL-ID；行序按 loops.yaml 中 Loop 的顺序，无 Loop 的 Part 排在该 Ring 表末 ← PSL-011, PSL-010, PSL-002, PSL-014
- [F-11] 报告必有"缺少"一节，为空也保留并写"本次无"；每条 = Gap 原子 + 所在 Ring + 必要性判定 + deletion 测试一句话 + 去向，两类缺少（lifecycle 空白 / 本次新识别）各带标签不混排 ← PSL-017, PSL-002
- [F-12] 报告与 `audit.yaml` 同构：每一表行对应恰一条 Part 记录、每一"缺少"条目对应恰一条 identified_no_part 的 Gap 记录；检查脚本双向核对同构，报告页首给出脚本路径 ← PSL-015, PSL-011
- [F-13] 检查脚本对完整 `audit.yaml` exit 0；遇下列任一即 exit 1：缺任一 Ring 键、任一 Part 四维不齐、任一维 psl_ids 为空或超出 PSL-001..017、identified_no_part 的 Gap 未出现在"缺少"、人签门无 signed_by、两个 Part 声明同一 Artifact；脚本只核对 signed_by 存在、不代签任何门；终止条件由脚本给出，不由审计者自己记 ← PSL-004, PSL-015, PSL-001, PSL-006
- [F-14] 报告必有"本次运行的证据"一节：本次 Finding 走过的状态路径（候选 / 有证据 / 已裁决各几条）、每道门的 signed_by 与 delegation_record、审计自身的 implemented 阶只写到 compiled（脚本过）而不自称 verified、发现的被审 Part 源码问题只给指向 skill-issues.md 的路径，不写进被审文件 ← PSL-010, PSL-006, PSL-003
- [F-15] 报告末尾的提案清单不是独立实体，而是 Finding 的 `destination` 字段（skill_fix_list / new_issue / no_action）的投影：`destination ≠ no_action` 的 Finding 各成一条；命名建议类 Finding 的 destination 只能是 new_issue，不能是就地改名 ← PSL-014, PSL-003

## 交互与消歧

- [F-20] 两个 Part 疑似重复时，以 `audit.yaml` 的 Artifact 登记裁决：Artifact 不同 → 两行各写"同一判据的两个出口，不重复"；Artifact 相同 → 两行各写"合并候选"并互相引用；名字或描述相似本身不构成重复 ← PSL-001
- [F-21] `needed` 只以 deletion 测试裁（撤掉后引擎会做错 → needed）；当"流水线闭合所需"与 deletion 测试给出相反答案时，两个 verdict 并列写入该维并把该行标为待 G1 / G3 人裁，检查脚本不替人挑一个 ← PSL-002, PSL-006
- [F-22] 有 SKILL.md 但无 verify 脚本、无门的 Part，`implemented` 显示为 declared，且 compiled / verified 两阶各显式写"未达"及缺什么（无脚本 / 无门 / 无行为层运行）；不允许该格只写 declared 而省掉后两阶 ← PSL-010, PSL-017, PSL-015
- [F-23] 任一维 evidence 为空的 Finding 不进报告，留在 `audit.yaml` 的 `candidates` 列表里保持候选态且不删除；候选态条目在"本次运行的证据"节只计数、不展开 ← PSL-005, PSL-010

## 明确不做（从规律推出的否定）

- [F-90] 不出现任何 `exists` / `implemented: true` 之类的布尔列；只有勾叉的清单即使全对也被检查脚本拒绝（缺四维、缺 PSL-ID 即 exit 1） ← PSL-010, PSL-002
- [F-91] 审计不重命名任何 Part、不修改任何被审 Part 的 SKILL.md / agent.md / 脚本 / gate.json；交付物只有报告、`audit.yaml`、检查脚本与指向 skill-issues.md 的路径 ← PSL-003, PSL-014
- [F-92] 不因某 Ring 配件数量少而建议补 Part，无 Gap 记录支撑的建议直接不进报告；本次识别出的缺少不在审计内实现，只登记并给 new_issue 去向 ← PSL-002, PSL-017

## 验收挂钩（每条形态决策至少被一条 Acceptance 检到）

| Acceptance（按 PSL 原文顺序） | 挂钩的决策 |
|---|---|
| A1 问 R6 环有哪些配件、各填什么缺口 | F-01, F-02, F-06, F-10 |
| A2 问 pr-review 与 code-reviewer 是否重复 | F-02, F-20 |
| A3 问 donewhen-extract 名字是否合适 | F-05, F-15 |
| A4 问 implement 已实现了吗 | F-03, F-04, F-22 |
| A5 问哪些环节缺配件 | F-06, F-11, F-21, F-92 |
| A6 问这份审计能不能被机器检 | F-03, F-12, F-13, F-23, F-90 |
| A7 问审计者是谁、用什么身份签的门 | F-07, F-14 |
| （仅 γ 约束"审计者不得修改被审 SKILL.md"，无 Acceptance 条目） | F-91 |

F-91 只有 γ 约束能检到、没有 Acceptance 问句——按 derivation.md 的判据它接近装饰；建议 PSL 补一条"问审计有没有改过被审文件 → 返回被审目录的 git diff 为空"。

## PSL 欠定

- **提案（Proposal）**：Workflow φ 与 Acceptance 都说"提案清单 / 可直接开 issue 的提案"，Domain Model 却没有这个实体；本稿把它压成 Finding 的 `destination` 字段。承重：跨 Part 的提案（如合并两个 Part）挂在哪条 Finding 上，PSL 没说。
- **审计运行（Run）**：UI Contract 要"本次运行的证据"节，Mental Model 说审计本身是一次 sdlc 运行，但 Domain Model 里没有承载运行级证据的实体；本稿把签字人挂在 Gate、其余只做报告节、不建 yaml 对象。
- **skill 源码问题**：γ 说进 skill-issues.md，但它既不是 Finding 的四维之一也不是实体；本稿只给路径指向。承重：它是否算 Part 的 implemented 逆向流转证据。
- **Ring 的"问题"**：Domain Model 说每环回答一个问题但未定义字段；识别"没有 Part 的 Gap"本应以环的问题为锚，本稿未设 `question` 字段。
- **证据（evidence）的类型**：State Machine 列举了 gate.json / smoke 行 / 文件路径 / PSL-ID 四种来源，但无 schema；本稿用自由路径字符串。
- **Gap 的反向基数**：Domain Model 只写 Part 填 0..n Gap，未写一个 Gap 能否被多个 Part 填；本稿在 DOS 里按 N:N 处理。
