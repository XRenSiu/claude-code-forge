# Issues 累计汇总

**全局计数**:
- P0: 0
- P1: 20
- P2: 22

---

## P1 列表（按 Step / attempt 分组）

### iter-1 / step1 / attempt-1
- **P1-1**: REQ-002 句式语义选择牵强（State-driven vs Unwanted）—— action 是一次性条件分支而非持续行为
- **P1-2**: REQ-002 跨 REQ 因果指代（`silence the notification produced by REQ-001`）破坏可独立派生测试性

### iter-1 / step2 / attempt-1
- **P1-1**: Round 3 仅 2 题，低于 4.3 节"每轮 3-5"下限；Worker 可以把 round 2 的 second-order 推迟一轮平衡，但没探讨此备选
- **P1-2**: 决策溯源在表格与 EARS source 行两处颗粒度不一致，下游 Step 3 取版本有歧义
- **P1-3**: REQ-005/006 延续 Step 1 跨 REQ 指代模式（依赖 REQ-001 已发的通知做二次操作），与 4.5 样例的"平行分支"模式偏离

## P2 列表（按 Step / attempt 分组）

### iter-1 / step1 / attempt-1
- **P2-1**: 草稿头部漏 `Feature:` 前缀
- **P2-2**: `[?]` 后问题书写格式与设计文档样例不一致
- **P2-3**: 歧义清单三份冗余（内嵌 + Open questions + 中文歧义清单）
- **P2-4**: 草稿正文中英文混排不统一

### iter-1 / step2 / attempt-1
- **P2-1**: Round 3 引言段把 skill 内部权衡过程暴露到产出正文
- **P2-2**: Glossary (working) 段在 Step 2 输出尾部出现，与 Step 3 spec.md 边界视觉模糊
- **P2-3**: REQ-001 内嵌定义子句过长（30+ 词），可读性下降
- **P2-4**: skill 调用过程简记 + 元日志段过厚，与 4.5 节样例的极简风格偏离

### iter-1 / step3 / attempt-2
- **P2-1**: spec.md REQ 段使用 "Extension:" / "Constraint:" 自创子标签（设计文档无禁止，但首次阅读可能产生 EARS 句式归属歧义）

### iter-1 / step4 / attempt-2 (P1 共 4)
- **P1-1**: `test_dnd_lifecycle_state_machine_is_well_formed` 部分 invariant 测的是状态机自己的 bookkeeping，不是真实 impl
- **P1-2**: `test_mention_dispatch_atomicity_across_..._invariant` 名字说原子性但断言只是 delivery 一致性
- **P1-3**: `DispatchMentionNotification` 返回类型在不同测试调用点不一致（list / dict 多种形态混用）
- **P1-4**: 测试用 API endpoint（/api/_test/*, /api/_internal/surface_log, _force_surface_outcomes）未在 done_when.yaml 中登记，spec-drift 风险

### iter-1 / step4 / attempt-2 (P2 共 6)
- **P2-1 至 P2-6**: 6.8 矩阵偏离（REQ-002 多了 e2e、REQ-005 少了 e2e、REQ-007 多了 integration，都源自 Step 3 契约而非 4-D/4-C bug），mutation.sh 路径文档不一致，manifest count 表述错，PBT alphabet 未文档化

### iter-1 / step5 / attempt-1 (P1 共 5)
- **P1-1**: Worker 未对照 §7.4 硬性 schema 的 10 个字段做逐项核实
- **P1-2**: `integration_tests.property_based.minimal_counterexample`（PBT shrink 反例如何被外部捕获）未审
- **P1-3**: `mutation_testing.surviving_mutants` 三元组未审
- **P1-4**: §7.2 做判分离原文未引为锚点
- **P1-5**: Translation guidance 不涵盖 fitness layer 如何回流到 ratchet

### iter-1 / step5 / attempt-1 (P2 共 4)
- **P2-1 至 P2-4**: Worker 主动声明"未读 source spec"是根因，越界事实陈述，引片冗余，做归属讨论越界

### iter-1 / step6 / attempt-2 (P1 共 6 — 全继承自 attempt-1)
- **P1-1**: 兜底机制（PBT 失败 → 退回 Step 2）两个 SKILL.md 自身不讲，仅 README + INTEGRATION
- **P1-2**: §8.3(a) 达标出口未声明
- **P1-3**: §8.3(b) 未达标出口的细分（PBT / mutation / e2e 不同 fix 路径）缺失
- **P1-4**: `budget: max 15 rounds` 出处不明
- **P1-5**: `max_fix_loops_before_escalation` (escalate 语义) vs ratchet `convergence` (stop 语义) 不完全等价
- **P1-6**: 判别 "spec wrong vs code wrong" 无可操作准则

### iter-1 / step6 / attempt-2 (P2 共 3 — 新增)
- **P2-1 至 P2-3**: 措辞精度、首屏信息密度问题
