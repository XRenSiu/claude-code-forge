# Workflow — sdlc-ring-audit

> Σ 写"审计者做 X 时世界里发生了什么"，φ 写"歧义如何裁决、对的结果长什么样"。
> 禁止 Step 1/2/3、步骤 N、阶段 N、首先/然后/接着/最后 串。投影自 PSL-sdlc-ring-audit.md 的 Workflow / Acceptance / State Machine 层。

## Σ · 发生了什么

- 当审计者读一个 Ring 时，该 Ring 上每个 Part 被放到四个坐标上：它填哪个 Gap、独占哪个 Artifact、哪道 Gate 检它、属于哪个 Loop；
  一个 Finding 随之从"候选"成形为"有证据"。（← PSL-002, PSL-001, PSL-015, PSL-011）
- 当某个 Gap 在一个 Ring 上找不到承载它的 Part 时，它浮现为"缺少"，进入"缺少"节；lifecycle 已登记的空白也在这里重新出现。（← PSL-017）
- 当两个 Part 被发现独占同一个 Artifact 时，它们浮现为"合并候选"；Finding 的 needed 维标记之。（← PSL-001）
- 当 Finding 被 G1 / G3 的人（或代签 agent）接受或推翻时，它从"有证据"流转到"已裁决"；被推翻的 Finding 保留在账本里不删。（← PSL-005, PSL-006）
- 当审计者读一个 Part 的名字时，先判它的来路（新写 / 收编），再判名字与 Artifact 或位置的贴合；建议进 Finding，不触发重命名。（← PSL-014）
- 当审计报告落盘时，同构的 `audit.yaml` 一起落盘，检查脚本对它跑一次；报告的"本次运行的证据"节记录状态机路径与签字人。（← PSL-015, PSL-010）

## φ · 消歧判据

- 若一个 Part 疑似重复另一个（同一判据两个出口），则以 Artifact 裁：产物不同 → 不重复；产物相同 → 合并候选。对的结果呈现为
  Finding.needed 里的一句裁决 + 两个 Artifact 的名字。（← PSL-001）
- 若一个 Part 是否"必要"有争议，则以 deletion 测试裁：撤掉它引擎会做错 → 必要；只是"流程图上有格子" → 不必要。
  deletion 测试与"流水线闭合所需"给出不同答案时，两者并列写进 Finding，不合并成一个词。（← PSL-002）
- 若"已实现"要判定，则返回三态之一（声明 / 编译 / 验证）与各态的证据路径；布尔"✓"是错的形状。（← PSL-010）
- 若名字被判"不贴合"，则对的结果是"建议名 + 不重命名的理由（内部引用 / 上游同步）"，而不是一次 rename。（← PSL-014）
- 若某 Finding 没有证据（无 gate.json / smoke 行 / 文件路径 / PSL-ID 可引），则它不进报告，留在候选。（← PSL-010, PSL-017）
- 若审计者想修改被审 skill 的 SKILL.md 让判定变好，则禁止：评估者与被评估者分离；问题进 skill-issues.md 与提案。（← PSL-003）

## γ · 约束（done_when 形式）

- done_when: 九环 + 脊柱全覆盖 ∧ 每个 Part 四维判定齐且每维 ≥ 1 PSL-ID ∧ "缺少"节存在 ∧ `audit.yaml` 过检查脚本（对报告 exit 0；对删掉任一环的变体 exit 1）∧
  报告的证据节列出三道门的签字人与代签授权。（← PSL-015, PSL-006）
- 机器可判到此为止；"某个 Part 的 Gap 归类对不对"是 G1 / G3 的残差。（← PSL-010）
