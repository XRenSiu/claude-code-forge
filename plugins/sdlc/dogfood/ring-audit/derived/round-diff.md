# round-diff — sdlc-ring-audit form-draft.md，第二轮 → 第三轮（逐 F 行）

> 机械证明：只有 G1 第二轮裁决点对应的 F 行发生变化。左 = 第二轮审阅稿（sha256 13859dd63fffaa4bd59e34390f79d2cd3dc4df1b5a826584a356dee33ceb96f2 的 F 行），右 = 第三轮。
> 生成方式：`grep '^- \[F-' form-draft.md` 两版后 `diff`；非 F 行（头注、验收挂钩表、PSL 欠定节）不在此 diff 内，变动见 divergence.md "第三轮改动"。

F 行数：第二轮       27，第三轮       27

变动的 F-id：
[F-03] [F-05] [F-07] [F-08] 

```diff
3c3
< - [F-03] `naming` 维是复合值 `{provenance: authored | adopted, artifact_or_position: <名>, fit: fits | misfit, suggested_name?, rename: false}`；fit 对每个 Part 都判，判据只有一条：名字 = 独占 Artifact 的名或所在位置名 → fits，否则 misfit（动词短语、上游领域词与产物不符都算 misfit）；provenance 不参与 fit 判定，只决定 misfit 的去向理由（adopted → "不重命名：上游同步 / 内部引用"，authored → "不重命名：另开 G2 变更提案"）；`rename` 为常量 false，存在的目的是让检查脚本能拒绝任何 true ← PSL-014
---
> - [F-03] `naming` 维是复合值 `{provenance: authored | adopted, artifact_or_position: <名>, fit: fits | misfit, suggested_name?, rename: false}`；fit 对每个 Part 都判，判据只有一条：名字与独占 Artifact 的名或所在位置名同词干或同义 → fits（不要求字面相等：calibrate / dos-extract / retro 这类同词干的名字是 fits，否则 naming 列变噪声），否则 misfit（动词短语、上游领域词与产物不符都算 misfit）；provenance 不参与 fit 判定，只决定 misfit 的去向理由（adopted → "不重命名：上游同步 / 内部引用"，authored → "不重命名：另开 G2 变更提案"）；`rename` 为常量 false，存在的目的是让检查脚本能拒绝任何 true ← PSL-014
5c5
< - [F-05] Artifact 记录 `{id: graph.yaml Node.writes 的路径模式 ∪ ARCHITECTURE §1 产物列, producer: <Part>, alternatives_of?: <stage>}`；同一 Artifact 出现两个 producer 且两者不是同阶段条件替代（graph.yaml 里从同一 stage 节点出发的 conditional 边）时，两个 Part 的 Assessment 都标 `needed.verdict = merge_candidate: <另一 Part>`，审计者不当场裁掉一个；是同阶段条件替代（如 implement / card-implementer / ratchet 对卡文件与 github:pr）时记 `alternatives_of` 并豁免，不算第二生产者；产物为 0 的 Part 记 `role ∈ {gate, orchestrator}` 说明它为何不生产 ← PSL-001
---
> - [F-05] Artifact 记录 `{id: graph.yaml Node.writes 的路径模式 ∪ ARCHITECTURE §1 产物列, producer: <Part>, alternatives_of?: <stage>}`；同一 Artifact 出现两个 producer 且两者不是同阶段条件替代时，两个 Part 的 Assessment 都标 `needed.verdict = merge_candidate: <另一 Part>`，审计者不当场裁掉一个；同阶段条件替代由三个条件共同定义、数据源是 graph.yaml、缺一不算：(a) 两个 Part 出现在同一 `stage.<x>` 节点的 handled_by 里；(b) 它们之间由一条带 `when` 守卫的 `conditional` 边选择执行者；(c) 它们写同一 schema 的 Artifact；implement / card-implementer / ratchet 三条件全满足（graph.yaml L29 stage.implement handled_by；L320–321 从 implement 出发的两条 conditional 边）→ 记 `alternatives_of` 并豁免，不算第二生产者；donewhen-extract / acceptance-spec 只满足 (a)（L26 stage.contract），无 conditional 边且 v1 ≠ v2 形状 → 不豁免，触发 merge_candidate（与现状 Q008 一致）；产物为 0 的 Part 记 `role ∈ {gate, orchestrator}` 说明它为何不生产 ← PSL-001
7,8c7,8
< - [F-07] kind=human 的 Gate 记录带 `signer / signer_kind ∈ {human, delegated_agent} / authorization_ref`（delegated_agent 时必填）；Assessment 带状态 `candidate | evidenced | adjudicated` 与追加式 `adjudications[]`，每条 `{gate: G3 | report_review, signer, signer_kind, authorization_ref, supersedes?}`；裁决 Assessment 的 Gate 只能是 kind=human 的 G3 或报告人审，G1 不出现在 adjudications 里（G1 裁的是本形态草案，那时一条 Assessment 都不存在）；推翻不改写原判定，只追加一条带 `supersedes` 的新记录 ← PSL-005, PSL-006
< - [F-08] Part 记录 `{id, kind ∈ {skill, agent, asset, human_gate}, ring, ring_evidence, provenance, loop}`；kind 里没有 script——skill 目录下的脚本是该 skill 的 Gate（checked_by）或 Capability，不是独立 Part；stage 节点不是 Part；`ring` 不手填，从 graph.yaml `Node.role` 经现状本体 composition.Ring 的映射推出（world→R0 … learning→R8，orchestrator→spine），`ring_evidence` 写 graph.yaml 行号；human_gate 归它检的 Artifact 所在的 Ring（G1→R0、G2→R2、G3→R6），不归 spine；spine 上的 Part 是 sdlc skill 与 graph / loops / routing / triggers 四个数据资产；没有图节点的 Part（agents/pr-reviewer.md、四个数据资产）写 `ring_evidence: no_node` 并按 ARCHITECTURE §1 落环 ← PSL-011, PSL-015, PSL-006
---
> - [F-07] kind=human 的 Gate 记录带 `signer / signer_kind ∈ {human, delegated_agent} / authorization_ref`（delegated_agent 时必填）；Assessment 带状态 `candidate | evidenced | adjudicated` 与追加式 `adjudications[]`，每条 `{gate: G3, signer, signer_kind, authorization_ref, supersedes?}`；裁决 Assessment 的 Gate 只能是 kind=human 的 G3——报告人审就是 G3 的内容（"这个 Part 的 Gap 归类对不对"是 G3 裁的 human AC），不是第四道门；报告合入后再推翻某条 Assessment 是逃逸缺陷，喂下一次审计 Run 的新 Assessment 并以 `supersedes` 关联；G1 不出现在 adjudications 里（G1 裁的是本形态草案，那时一条 Assessment 都不存在）；推翻不改写原判定，只追加一条带 `supersedes` 的新记录 ← PSL-005, PSL-006
> - [F-08] Part 记录 `{id, kind ∈ {skill, agent, asset, human_gate}, ring, ring_evidence, provenance, loop}`；kind 里没有 script——skill 目录下的脚本是该 skill 的 Gate（checked_by）或 Capability，不是独立 Part；stage 节点不是 Part；`ring` 不手填，从 graph.yaml `Node.role` 经现状本体 composition.Ring 的映射推出（world→R0 … learning→R8，orchestrator→spine），`ring_evidence` 写 graph.yaml 行号；human_gate 覆盖 graph.yaml 全部五个 kind=human 节点，不只三道门：持有 Gate 对象的三个归它检的 Artifact 所在的 Ring（G1→R0、G2→R2、G3→R6），human.merge → R7、human.harness-review → R8（ARCHITECTURE §1 表 R7 / R8 门闸列），ring_evidence 写 graph.yaml 行号（L239–243、L269–273），"文档写三道门、数据有五个人节点"的出入成为这两个 Part 的一条 Assessment（现状 Q004），不由本稿调和；human_gate 不归 spine；spine 上的 Part 是 sdlc skill 与 graph / loops / routing / triggers 四个数据资产；没有图节点的 Part（agents/pr-reviewer.md、四个数据资产）写 `ring_evidence: no_node` 并按 ARCHITECTURE §1 落环 ← PSL-011, PSL-015, PSL-006
```
