# Skill 验证总日志

**目标**: 验证 `acceptance-spec` 和 `test-suite-generator` 两个 skill 是否符合 `~/Documents/Downloads/done-when-pipeline.md` 设计。

**测试输入**（贯穿 6 个 Step）:
> 在团队聊天频道中,被 @mention 的成员会收到通知,但勿扰模式下静音。

**步骤映射**:

| Step | 设计文档章节 | 负责 skill | 关键产出 |
|------|------------|----------|---------|
| 1 | 三、需求草拟 | acceptance-spec (Step 1 部分) | EARS 草稿 + `[?]` 歧义清单 |
| 2 | 四、歧义消除 | acceptance-spec (clarify 循环) | 已消除歧义的 EARS + 决策溯源 |
| 3 | 五、规格固化 | acceptance-spec (模板填充) | proposal.md / spec.md / tasks.md / done_when.yaml |
| 4 | 六、验证物派生 | test-suite-generator | existence + unit + integration + e2e + mutation + fitness 六层 |
| 5 | 七、执行评估 | 移交边界 | skill 应明确声明 hand-off 到 /ratchet |
| 6 | 八、闭环迭代 | 移交边界 | skill 应明确声明 ratchet 主控 + spec drift 兜底 |

---

## 事件流水

- iter-1 / step1 / attempt-1: Worker ✔ → Auditor 出 issues (P0=0, P1=2, P2=4) → 进入分支 B
- **Step 1 CLEARED (attempt 1, P0=0, P1=2, P2=4)**
- iter-1 / step2 / attempt-1: Worker ✔（3 轮 / 5+5+2 题 / 12 个 `[?]` 清零）→ Auditor 出 issues (P0=0, P1=3, P2=4) → 进入分支 B
- **Step 2 CLEARED (attempt 1, P0=0, P1=3, P2=4)**
- iter-1 / step3 / attempt-1: Worker ✔（4 件套 + 磁盘文件）→ Auditor 出 issues (P0=2, P1=6, P2=3) → 进入分支 A
- iter-1 / step3 / attempt-1: Fixer ✔ 修了 11 个 skill 源码文件，对齐附录 C v1（done-when-schema.yaml / template / example / acceptance-spec SKILL.md / test-suite-generator SKILL.md + 6 ref 文件）
- iter-1 / step3 / attempt-2: Worker ✔（按修后 skill 重生 4 件套）→ Auditor ✔ (P0=0, P1=0, P2=1) → 进入分支 B
- **Step 3 CLEARED (attempt 2, P0=0, P1=0, P2=1)**

> ⚠️ **重要状态注记**: Step 3 在 attempt 2 才 cleared（attempt 1 出 P0=2）。这意味着如果按完成条件 1（"整轮中没有任何 Step 触发 attempt {K>1}"），iter-1 已经不能作为 FINAL CLEAN ITERATION。完成本轮所有 Step 后必须开 iter-2 重跑。

- iter-1 / step4 / attempt-1: Worker ✔（6 子步骤全产出，18 文件）→ Auditor 出 issues (P0=2, P1=6, P2=4) → 进入分支 A
- iter-1 / step4 / attempt-1: Fixer ✔ 修了 5 个 test-suite-generator 源码文件（SKILL.md 新增 iron rules #9/#10，sub-modules 全部硬化 verbatim + fail-fast）
- iter-1 / step4 / attempt-2: Worker ✔（按修后 skill 重生 18 文件，含 fail-fast existence.sh + verbatim e2e test 名）→ Auditor ✔ (P0=0, P1=4, P2=6) → 进入分支 B
- **Step 4 CLEARED (attempt 2, P0=0, P1=4, P2=6)**

> ⚠️ Step 4 也在 attempt 2 才 cleared，iter-1 进一步无法满足完成条件 1。继续完成 Step 5/6 后开 iter-2。

- iter-1 / step5 / attempt-1: Worker ✔（审 hand-off 边界声明完整性）→ Auditor ✔ (P0=0, P1=5, P2=4) → 进入分支 B
- **Step 5 CLEARED (attempt 1, P0=0, P1=5, P2=4)**
- iter-1 / step6 / attempt-1: Worker ✔ → Auditor 出 issues (P0=2, P1=6, P2=3) → 进入分支 A
- iter-1 / step6 / attempt-1: Fixer ✔ 修了 INTEGRATION.md (spec_drift_threshold 示例去掉过时 applies_to) 和 README.md (pipeline 图 + ratchet 表格不再暗示 auto-escalation)
- iter-1 / step6 / attempt-2: Worker ✔ → Auditor ✔ (P0=0, P1=6 继承, P2=3 新增) → 进入分支 B
- **Step 6 CLEARED (attempt 2, P0=0, P1=6, P2=3)**

---

## iter-1 总结

iter-1 完整跑完 6 个 Step。但 Step 3、Step 4、Step 6 都需要 attempt > 1 才 cleared。**iter-1 不满足完成条件 1（"整轮中没有任何 Step 触发 attempt {K>1}"）**。

修复过程发现的 skill 源码问题（已修复）:
- Step 3 attempt-1 → skill 内 schema 与设计文档附录 C 不一致（fitness judge enum / leaf 子字段越界）。Fixer 改了 11 个文件对齐 v1 字面 schema。
- Step 4 attempt-1 → existence 非 fail-fast / e2e test name paraphrase。Fixer 改了 5 个 test-suite-generator 文件加 iron rules #9/#10 + sub-modules 硬化。
- Step 6 attempt-1 → INTEGRATION.md 含过时 applies_to 示例 / README.md 暗示 ratchet 自动 escalate。Fixer 改了 INTEGRATION + README 让 plugin 级文档与 SKILL.md 严格 schema 一致。

进入 iter-2 用修后的 skill 完整重跑 6 个 Step，目标是每个 Step 都在 attempt 1 通过。

---

## iter-2


