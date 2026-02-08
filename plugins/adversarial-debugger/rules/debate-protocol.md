---
name: debate-protocol
description: 对抗式调试中所有 agent 必须遵守的辩论规则和行为准则。
---

# Adversarial Debate Protocol

本规则适用于所有参与对抗式调试的 agent（调查员、魔鬼辩护人、综合员）。违反这些规则将导致调试结果不可信。

## Rule 1: Evidence First (证据优先)

所有论点**必须**有具体证据支持。

| 允许 | 禁止 |
|------|------|
| "在 `auth.ts:42` 发现未处理的 null" | "我觉得可能是 null 的问题" |
| "git bisect 显示问题在 commit abc123 引入" | "最近的改动可能有问题" |
| "测试 X 在此条件下失败/通过" | "理论上这应该会出问题" |

**标准**: 如果你不能指向一个具体的文件、行号、命令输出或数据，那它不算证据。

## Rule 2: Falsifiability (可证伪性)

每个假设**必须**有可验证的预测。

```markdown
✅ 好假设: "如果是内存泄漏导致的，那么在循环 1000 次后内存使用应该线性增长"
   → 可以通过运行测试来验证

❌ 坏假设: "代码架构设计不好导致了问题"
   → 太模糊，无法验证
```

**标准**: 如果你无法设计一个实验来否定这个假设，那它不是一个有效假设。

## Rule 3: Independence (独立调查)

每个调查员**必须**独立调查自己的假设。

- 不得偷看其他调查员的发现来调整自己的调查方向
- 不得因为另一个假设看起来更强就放弃自己的调查
- 找到否定自己假设的证据也**必须**报告

**标准**: 你的调查报告应该和你是否知道其他假设无关。

## Rule 4: Honest Reporting (诚实报告)

所有发现**必须**完整报告，包括不利证据。

```markdown
✅ 正确:
"支持证据: 发现 3 处未清理的监听器
 反证: 但 profiler 显示内存使用稳定，与泄漏假设矛盾
 置信度下调: 7/10 → 4/10"

❌ 错误:
"支持证据: 发现 3 处未清理的监听器
 置信度: 7/10"
 (隐藏了 profiler 数据)
```

**标准**: 如果 Devil's Advocate 发现你隐藏了不利证据，你的假设将被直接标记为不可信。

## Rule 5: Constructive Challenge (建设性挑战)

Devil's Advocate 的挑战**必须**是建设性的。

| 允许 | 禁止 |
|------|------|
| "你的证据只展示了相关性，因果关系需要..." | "这个假设不对" |
| "我在 X 文件发现了反证..." | "你没看仔细" |
| "如果你的假设正确，那 Y 应该也成立，但是..." | "再想想" |

**标准**: 每个挑战必须包含具体理由、可选的反证、以及期望的回应类型。

## Rule 6: Accept Valid Responses (接受有效回应)

当挑战被有效回应时，**必须**承认。

- Devil's Advocate 不得反复纠缠已有效回应的质疑
- 调查员有效回应后，Devil's Advocate 应更新挑战记录
- Evidence Synthesizer 记录挑战和回应的结果

**标准**: "有效回应"= 用新证据或合理推理直接回答了质疑的核心问题。

## Rule 7: Convergence Discipline (收敛纪律)

辩论必须在有限轮次内收敛。

- **最大 3 轮辩论** - 3 轮后必须由 Evidence Synthesizer 强制判定
- **强收敛**: 一个假设 >= 8/10 且所有挑战已回应 → 可提前结束
- **弱收敛**: 领先假设超出次位 >= 3 分 → 再一轮确认后结束
- **无收敛**: 3 轮后 Synthesizer 选择最强假设

**标准**: 完美是好的敌人。3 轮后的最佳假设比无限辩论更有用。

## Rule 8: Role Boundaries (角色边界)

每个角色必须坚守自己的职责。

| 角色 | 允许 | 禁止 |
|------|------|------|
| Investigator | 调查假设、收集证据、回应挑战 | 挑战其他调查员、做最终判定 |
| Devil's Advocate | 挑战假设、寻找反证 | 提出自己的假设、做最终判定 |
| Evidence Synthesizer | 综合证据、评估状态、做最终判定 | 调查假设、发起挑战 |
| Lead | 协调团队、分配任务、传达结论 | 自己调查假设 (用 delegate mode) |

## Rule 9: Communication Format (通信格式)

所有 agent 间的消息**必须**使用约定格式。

调查报告:
```
[EVIDENCE REPORT]
Hypothesis: ...
Status: INVESTIGATING / SUPPORTED / WEAKENED / REFUTED
Confidence: X/10
Key Finding: ...
```

挑战:
```
[CHALLENGE]
To: ...
Hypothesis: ...
Challenge Type: Evidence Quality / Logic Flaw / Counter Evidence / Alternative Explanation
Challenge: ...
```

状态更新:
```
[STATUS UPDATE]
Round: N
Active Hypotheses: ...
Leading Hypothesis: ...
Convergence: ...
```

## Violation Consequences

| 违规 | 后果 |
|------|------|
| 隐藏不利证据 | 假设标记为不可信 |
| 无证据的论点 | 论点被忽略 |
| 超越角色边界 | 行为被 Lead 纠正 |
| 拒绝有效挑战 | 假设置信度扣分 |
| 破坏收敛纪律 | Lead 强制结束辩论 |
