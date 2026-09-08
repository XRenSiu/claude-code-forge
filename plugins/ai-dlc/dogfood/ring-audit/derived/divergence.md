n: 1                       # 独立推导次数；本轮是 G1 第一轮否决后的定向重推，未做分歧检验
consistent_decisions: 27   # 本轮 27 条决策全部来自 round1 合并稿中 G1 接受的决策或 g1-record.md 的裁决；无新分歧点

# 分歧集 — sdlc-ring-audit（第二轮，定向重推）

> **未做分歧检验**。理由：round1（n=3，derived/round1/divergence.md）的 7 条分歧 D-1…D-8（无 D-6）已在 g1-record.md 逐条裁定
> （D-3 / D-4 / D-5 / D-7 accepted；D-1 / D-2 / D-8 rule_error → PSL 改至 v2），本轮输入是"PSL v2 + g1-record.md 的裁决"，
> 按 g1-record.md 决定节的建议，n=1 定向重推合法；分歧表的位置由下面的"裁决 → 落点"对照表替代。
> G1 预判：若坚持 n=3，分歧应收敛到 ≤ 2。

## G1 裁决 → 落点对照

| # | G1 ruling | applied in | note |
|---|---|---|---|
| 1 | E-1 implemented 三态统一 + `calibrated` 附注；"空白"移出 Part 态 | F-02, F-04, F-11 | 空白 = Ring.missing 里 source=lifecycle_blank 的 Gap |
| 2 | E-2 关联段加 Ring 暴露 0..n Gap、Part 填 Gap N:N；Ring 加 `question` | F-04, F-11, F-12 | dos-proposal 关系 Ring EXPOSES Gap 1:N、Part FILLS Gap N:N；Ring.question 进 audit.yaml rings[] |
| 3 | E-3 Finding 四维 → 三维，"缺少"由 Ring 级 Gap 回答 | F-01, F-10, F-11, F-13 | missing 维删除；每环表末尾 Gap 行；检查脚本谓词改"三维齐" |
| 4 | E-4 Finding 改名 Assessment | F-01, F-95 | dos-proposal 对象 Assessment；F-95 明确不做"叫 Finding" |
| 5 | E-5 裁决只 G3 或报告人审；Gate(kind=human) 裁决 0..n Assessment | F-07 | adjudications[].gate ∈ {G3, report_review}；G1 不出现；dos-proposal 关系 ADJUDICATES 描述 "kind=human, G3 only" |
| 6 | E-6 脊柱 = id=spine 的 Ring；人签门归所检产物的环；Part 粒度与 kind 去 script | F-08, F-10 | kind ∈ {skill, agent, asset, human_gate}；G1→R0、G2→R2、G3→R6；脚本 = 该 skill 的 Gate 或 Capability |
| 7 | E-7 Gate 加 signer / signer_kind / authorization_ref；Evidence 值类型 {kind, ref} | F-01, F-07, F-13, F-15 | Evidence 四 kind 各对应一种 ref；检查脚本检 kind 在枚举、ref 非空 |
| 8 | E-8 Acceptance 加 A8（审计动过被审目录吗） | F-93, 验收挂钩 A8 | 卡提交 git diff 为空；verifier bug 修复记 deviation 单独提交 |
| 9 | E-9 来路标注修正（lifecycle.md 制品映射表 + ARCHITECTURE §7） | F-11 | lifecycle_blank 的 evidence 指向这两处 |
| 10 | E-10 不建模只引用：Run / skill 源码问题 / PSL 规律 | F-15 | run_evidence 只引用 slug / state.json / ledger；skill-issues.md 是账本事件投影；v3 的跨运行指纹不进 |
| 11 | E-11 规律分形态层 / 内容层；PSL-008 / 009 / 012 由 Assessment 引用 | 本稿头注；全稿 | 三条不出现在任何 F 行；verify_derived 的 uncited flag 属预期 |
| 12 | E-12 "缺少"三种来源，加 dos.yaml `enforced_by ≠ system` 的规则 | F-04, F-11 | source ∈ {lifecycle_blank, newly_identified, unenforced_rule}；R001 / R008 / R010 / R017 是候选 Control 缺口 |
| 13 | P-1 adopted 不免检，fit 对每个 Part 判 | F-03, F-23 | provenance 不参与 fit，只决定 misfit 的去向理由 |
| 14 | P-2 每 Part 四维 / missing 一维 → 三维 + Ring.missing | F-01, F-11 | 同 E-3 |
| 15 | P-3 同阶段条件替代不算第二生产者 | F-05, F-13, F-20 | alternatives_of 字段；implement / card-implementer / ratchet 豁免；donewhen-extract / acceptance-spec 该触发 |
| 16 | P-4 loop_reason 只对 loop_back 端点 / generator / verifier 要求 | F-09 | 其余 Part 的 null 无需理由 |
| 17 | P-5 Finding 命名 | F-95 | 同 E-4 |
| 18 | P-6 形式化程度接受；人读报告一 Part 一行、PSL-ID 做脚注、机器读 audit.yaml 才带全字段 | F-10, F-12 | via UI-1 / UI-2 |
| 19 | D-1 三态 + calibrated；空白不是 Part 的态 | F-02 | 同 E-1 |
| 20 | D-2 Gap 落在每 Ring 自己的 `missing` 键 | F-04, F-11, F-12, F-13 | 同 E-2 |
| 21 | D-3 无 Gate 的 Artifact：producer ≤ declared **并** 一条 Control 缺口进 missing | F-06 | 两个后果同时成立；不再请求补 Workflow φ |
| 22 | D-4 两类缺少分标签，加第三来源 | F-04, F-11 | 同 E-12 |
| 23 | D-5 检查脚本自校准是证据必需项 | F-14 | 缺变体记录的 exit 0 标 uncalibrated |
| 24 | D-7 audit.yaml 顶层 `rings:` 列表，每项 {id, question, parts[].assessment, missing[]} | F-12 | — |
| 25 | D-8 Gate(kind=human) ADJUDICATES Assessment，仅 G3；不加 Part CARRIES Gate | F-07 | 同 E-5；dos-proposal 无 CARRIES 关系 |
| 26 | 三问 3 装饰引用：F-10 ← PSL-011、F-12 ← PSL-011、F-13 ← PSL-004 | F-10, F-12, F-13 | F-10 改引 PSL-017 / PSL-010 并注 via UI-1；F-12 只引 PSL-015 并注 via UI-2；F-13 保留 PSL-004 但加了它真正推出的子句（审计完成由 exit 码给出，审计者不自宣） |
| 27 | 三问 1 Ring 行：Ring 归属从 graph.yaml Node.role 派生并给证据行 | F-08, F-24 | ring_evidence 写行号；§1 与 Node.role 不一致 → Assessment，不调和 |
| 28 | 三问 1 Gap 行：Gap.state 不存储，派生 | F-04, F-13 | 检查脚本谓词"每个无 FILLS 边的 Gap 在其 Ring 的 missing 中" |
| 29 | 三问 1 Gate 行：script 渲染为"闸"，禁止"门" | F-06, F-13, F-94 | — |
| 30 | 欠定去向：Proposal → open_questions | F-16, PSL 欠定 | 跨 Part 提案用两个 source 权宜 |
| 31 | 欠定去向：Gate 与 Loop.verifier 是两个角色一个实体 | F-09 | 不重复计数 |
| 32 | 对账后果：Part ⊋ Node∖stage；无节点的 Part 显式列出并成为 Assessment | F-08, F-24 | pr-reviewer.md、四个数据资产 |
| 33 | 对账后果：现状 Q006 的 done_when.yaml ×2 该触发、卡文件 ×3 / github:pr ×2 不该触发 | F-05, F-20 | 同 P-3 |
| 34 | Open Q：必要 = deletion 测试在生命周期高度上读，闭合所需是其证据 | F-21 | contested 留给残余 |
| 35 | Open Q：命名建议本次不落地，但对所有 Part 诚实判 fit，misfit → issue | F-03, F-16, F-23, F-91 | rename: false 常量保留 |
| 36 | Open Q：主读者是插件作者；使用者的一句话留 README | F-10, F-16 | 报告人读版一 Part 一行 |
| 37 | Open Q：缺少只登记 + issue 草稿，不实现 | F-11, F-92 | — |
| 38 | Open Q：外部证据替代品有条件接受（标 substitute、必跑删环变体、仅本次 dogfood） | F-14, F-15 | evidence_kind: substitute |

## PSL 欠定（PSL v2 之后仍无依据的项）

- **Proposal（提案）** — 出现在本轮 F-16；PSL v2 Open Questions 已列。仍是 Assessment.disposition / Gap.disposition 的投影，跨 Part 提案以两个 source 表达是权宜。建议：留 open_questions，若需要 owner / 状态再升实体。
- **UI-n / A-n / DP-n 引用锚** — 出现在本轮 F-10 / F-11 / F-12 / F-14 / F-15 / F-20 / F-22 / F-23 / F-92 / F-93；verifier 只认 PSL-NNN，只能借最近形态层规律并注 `(via …)`。建议：verify_derived 放开锚格式（skill-issues I-19）或 /psl 把三层编号纳入规律索引。
- **ReportReview（报告人审）是不是一道 Gate** — 出现在本轮 F-07；PSL v2 关联段写"Gate（kind=human，仅 G3 或报告人审）"，但 Domain Model 把 kind=human 限定为 G1/G2/G3。建议：进 PSL Domain Model 一句（报告人审 = G3 的一次 disposition，或第四道人签门）。
- **StageEquivalence（"同阶段"的判据）** — 出现在本轮 F-05；PSL-001 说"同阶段条件替代不算争"，未说"同阶段"由哪份数据判定，推导取 graph.yaml 从同一 stage 节点出发的 conditional 边。建议：PSL-001 或 Workflow φ 补一句数据来源（现状 Q003 指出 stage 列表有两个来源）。

## 第三轮改动（G1 第二轮裁决，归因 derivation_error，PSL 不动）

只改下列 F 行与 dos-proposal / workflow 的对应行，其余决策与第二轮逐字节相同；逐 F 行 diff 见 `round-diff.md`。

1. **残余 1 → F-07**：`adjudications[].gate` 只取 `G3`，删除 `report_review`——报告人审就是 G3 的内容（Gap 归类是 G3 裁的 human AC）；合入后的推翻是逃逸缺陷，喂下一次审计 Run 并以 `supersedes` 关联。dos-proposal 同步：Assessment.adjudications 枚举、lifecycle、R010、ADJUDICATES 描述、behaviors、agent_guidelines；Q002 关闭进 evolution_log 0.2.1。workflow.md 三处"G3 / 报告人审"改为 G3。
2. **残余 2 → F-05**：同阶段条件替代 = 三条件缺一不算、数据源 graph.yaml：(a) 同一 `stage.<x>` 节点 handled_by；(b) 之间由带 `when` 守卫的 `conditional` 边选执行者；(c) 同 schema Artifact。implement / card-implementer / ratchet 全满足（graph.yaml L29；L320–321）→ 豁免；donewhen-extract / acceptance-spec 只满足 (a)（L26）→ 触发 merge_candidate（现状 Q008）。旧括注"从同一 stage 节点出发的 conditional 边"删除。dos-proposal Artifact.alternatives_of 同步；Q003 关闭进 evolution_log 0.2.1。F-20 例子已正确，不动。
3. **N-1 → F-08**：`human_gate` 覆盖 graph.yaml 全部五个 kind=human 节点；持有 Gate 对象的三个归所检 Artifact 的环（G1→R0、G2→R2、G3→R6），human.merge → R7、human.harness-review → R8，ring_evidence 写行号（L239–243、L269–273）；文档三道门 vs 数据五人节点的出入成为这两个 Part 的 Assessment（现状 Q004）。dos-proposal Part.kind / Part.ring 描述与 composition.RingMembership 同步。
4. **建议项（非阻塞）→ F-03**：fit 判据改为"同词干或同义即 fits，不要求字面相等"，避免 calibrate / dos-extract / retro 被判 misfit。

未改：F-21 里的"交 G3 / 报告人审"按 PSL v2.1 读作同位语（报告人审即 G3），为保持 diff 只落在裁决点上未动；若 G1 要求字面统一，可在第三轮签字时一并改。
- F-17（G2 提案 id F-13a）来自 G2 E-11：契约 required_parts / parts_total 需要的检查脚本视图 + 加性谓词；由编排者按 g1-record.md《第三轮补签》的 diff 块落字节（G1 不写自己签的东西），sha 与 G1 预签一致 → 746c56ef…；divergence.md 不在签字范围内。
