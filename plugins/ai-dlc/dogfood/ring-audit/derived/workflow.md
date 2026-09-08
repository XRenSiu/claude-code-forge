# Workflow — sdlc-ring-audit（第二轮，定向重推）

> Σ 写"审计者做 X 时世界里发生了什么"，φ 写"歧义如何裁决、对的结果长什么样"。
> 禁止 Step 1/2/3、步骤 N、阶段 N、首先/然后/接着/最后 串。投影自 PSL-sdlc-ring-audit.md v2 的 Workflow / State Machine / Acceptance 层，
> 按 g1-record.md 的裁决更新：Assessment 三维、Ring.missing、Ring 归属从 Node.role 派生、只有 G3 裁 Assessment（报告人审即 G3）；第二轮：同阶段条件替代三条件、human_gate 覆盖五个人节点。

## Σ · 发生了什么

- 当审计者读一个 Ring 时，该 Ring 上每个 Part 被放到四个坐标上：它填哪个 Gap（SKILL.md 的"缺口"段与 deletion 测试）、独占哪个 Artifact（ARCHITECTURE §1 产物列与 graph.yaml writes）、哪道 Gate 检它（闸或门）、它在哪个 Loop 里（loops.yaml）；Part 的 Ring 归属不是审计者写的，是 graph.yaml Node.role 经现状本体 Ring 映射推出的，证据是 graph.yaml 行号；一个 Assessment 随之从"候选"成形为"有证据"，三维各带 PSL-ID 与 Evidence{kind, ref}。（← PSL-002, PSL-001, PSL-015, PSL-011）
- 当一个 Gap 在其 Ring 上没有任何 Part FILLS 它时，它出现在该 Ring 的 missing 里，带来源标签（lifecycle_blank / newly_identified / unenforced_rule）；有 Part 填它时它从 missing 中消失——这是派生，不是状态写入。（← PSL-017, PSL-016）
- 当两个 Part 被发现独占同一个 Artifact 且不是同阶段条件替代时，它们浮现为"合并候选"，两条 Assessment 的 needed 维标记之；是同阶段条件替代时只记 alternatives_of，不算争——同阶段条件替代 = 同一 stage 节点 handled_by 内 + 带 when 守卫的 conditional 边选执行者 + 同 schema Artifact，三条件缺一不算，数据源 graph.yaml。（← PSL-001）
- 当一个 Artifact 没有任何 Gate 检它时，两件事同时发生：其生产者的 implemented 停在"已声明"，且一条 Control 缺口进该 Ring 的 missing。（← PSL-015, PSL-010, PSL-016）
- 当审计者读一个 Part 的名字时，来路（新写 / 收编）与贴合（名字 = 产物名或位置名）各判一次，收编不免检；建议名进 Assessment.naming，不触发重命名。（← PSL-014）
- 当 Assessment 被 G3（报告人审即 G3；人或带授权引用的代签 agent）接受或推翻时，它从"有证据"流转到"已裁决"；被推翻的判定保留，新判定以 supersedes 追加；报告合入后的推翻是逃逸缺陷，喂下一次审计运行。G1 不裁 Assessment——G1 裁的是本形态草案。（← PSL-005, PSL-006）
- 当审计报告落盘时，同构的 audit.yaml 一起落盘，检查脚本对它跑两遍：完整版 exit 0，删掉任一 Ring 的变体 exit 1；两遍都进 run_evidence，缺变体的 exit 0 标 uncalibrated；审计完成与否由 exit 码给出。（← PSL-015, PSL-007, PSL-004）
- 当审计运行推进时，它同时是被审对象的一次行为层证据：run_evidence 引用 Run 的 slug / state.json / ledger，签字人与 signer_kind 落在门上，替代外部证据标 substitute，skill 源码问题只以 skill-issues.md 路径出现。（← PSL-010, PSL-006）

## φ · 消歧判据

- 若一个 Part 疑似重复另一个，则以 Artifact 裁：产物不同 → 不重复（同一判据的两个出口）；产物相同 → 合并候选；同阶段条件替代 → 不是争。对的结果呈现为 needed 维里的一句裁决 + 两个 Artifact 的名字。（← PSL-001）
- 若一个 Part 是否"必要"有争议，则以 deletion 测试在生命周期高度上裁："撤掉它，这条流水线会不会产出错的或不可验证的东西"；"闭合所需"是 deletion 失败的一种证据而不是第二标准；残余冲突写 contested 并列两句理由，留给 G3。（← PSL-002）
- 若"已实现"要判定，则返回三态之一（声明 / 编译 / 验证）与各态的 Evidence，未达态写 not_reached；"编译"= 有 verify 脚本或被门挡；布尔"✓"是错的形状；"空白"不是答案——空白是 Ring.missing 的事。（← PSL-010）
- 若名字被判"不贴合"，则对的结果是"建议名 + 不重命名的理由（收编：上游同步 / 内部引用；新写：另开 G2 变更提案）"，而不是一次 rename；收编的 Part 同样要有 fit 判定。（← PSL-014）
- 若某 Assessment 某维没有 Evidence（无 file / gate_json / smoke / run_record 可引），则它不进报告，留在候选。（← PSL-010, PSL-017）
- 若检 Artifact 的是脚本，则报告写"闸"，不写"门"；"门"只指 G1 / G2 / G3；签字人是代签 agent 时渲染为代签并附授权引用。（← PSL-006, PSL-015）
- 若 ARCHITECTURE §1 与 graph.yaml Node.role 对某 Part 的归属不一致，或某 Part 有文件无节点，则它成为一条 Assessment（两个来源并列），审计者不调和、不改任何一份。（← PSL-011, PSL-003）
- 若审计者想修改被审 skill 的文件让判定变好，则禁止：评估者与被评估者分离；问题进 skill-issues.md 与提案；为过门而修的 verifier bug 记为账本 deviation 单独提交。（← PSL-003, PSL-005）

## γ · 约束（done_when 形式）

- done_when: 九环 + 脊柱全覆盖 ∧ 每个 Part 三维判定齐 ∧ 每维 ≥ 1 PSL-ID 与 ≥ 1 Evidence ∧ 每环 missing 键存在（可为空）∧ audit.yaml 过检查脚本且删环变体 exit 1 有记录 ∧ G1 / G2 / G3 签字人、signer_kind 与代签授权在报告可见 ∧ 被审目录在卡提交里 git diff 为空。（← PSL-015, PSL-006, PSL-003）
- 机器可判到此为止；"这个 Part 的 Gap 归类对不对"是 G3 的残差（报告人审即 G3）。（← PSL-010）
