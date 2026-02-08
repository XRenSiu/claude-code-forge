---
name: team-coordination
description: Agent Teams 协调规则，所有 forge-teams 阶段必须遵守。
---

# Agent Teams Coordination Rules

本规则定义 forge-teams 所有阶段中 Agent Teams 的创建、通信、协调和清理标准。违反这些规则将导致团队协作失效或资源泄漏。

---

## Rule 1: Team Lifecycle (团队生命周期)

每个阶段的团队**必须**经历完整的四阶段生命周期：

```
CREATE ──▶ COORDINATE ──▶ SHUTDOWN ──▶ CLEANUP
```

### 1.1 CREATE 阶段

| 步骤 | API | 说明 |
|------|-----|------|
| 1 | TeamCreate | 创建团队，命名格式: `[phase]-[feature]` |
| 2 | TaskCreate | 为每个角色创建任务 |
| 3 | Spawn | 为每个角色创建 teammate |

**命名规范**:
```
团队名: req-debate-user-auth, arch-bakeoff-payment, red-team-api
Teammate 名: optimist-analyst, architect-a, red-team-1
```

| 允许 | 禁止 |
|------|------|
| `TeamCreate` 时指定 `team_name` 和 `description` | 不指定 `team_name` |
| 每个 teammate 有唯一名称 | 重复的 teammate 名称 |
| 任务描述包含完整上下文 | 只给任务标题，无上下文 |

### 1.2 COORDINATE 阶段

Lead 的职责：
1. 监控 TaskList 状态
2. 通过 SendMessage 传达指令
3. 接收 teammate 的报告
4. 仲裁分歧
5. 决定何时进入下一轮

| 允许 | 禁止 |
|------|------|
| Lead 协调、分配、仲裁 | Lead 自己执行调查/编码 |
| 通过 SendMessage 一对一沟通 | 依赖 teammate 自发协调 |
| 定期检查任务状态 | 完全不检查就等结果 |

### 1.3 SHUTDOWN 阶段

```
SendMessage:
  type: "shutdown_request"
  recipient: [teammate-name]
  content: "Phase [N] complete. Shutting down team."
```

- **必须**等待每个 teammate 的 `shutdown_response`（approve）
- 如果 teammate 拒绝 shutdown，了解原因后再决定
- 如果 teammate 无响应超过 2 分钟，可以强制继续

### 1.4 CLEANUP 阶段

```
TeamDelete
```

- **必须**在所有 teammate 确认 shutdown 后执行
- **必须**在下一阶段 TeamCreate 之前完成
- 不允许有"僵尸团队"残留

---

## Rule 2: Message Format Standards (消息格式标准)

所有 SendMessage 通信**必须**使用约定格式。

### 2.1 任务分配消息

```
[TASK ASSIGNMENT]
Phase: [阶段编号]
Role: [角色名称]
Objective: [具体目标]
Context: [必要上下文]
Deliverable: [期望产出格式]
Deadline: [截止条件，非时间]
```

### 2.2 状态报告消息

```
[STATUS REPORT]
Phase: [阶段编号]
Role: [角色名称]
Status: IN_PROGRESS / COMPLETED / BLOCKED
Progress: [完成百分比或描述]
Key Findings: [主要发现]
Blockers: [如有阻塞]
```

### 2.3 辩论消息

```
[DEBATE - ROUND N]
Position: [立场/观点]
Evidence: [支持证据，含文件路径和行号]
Counterpoint: [对对方论点的回应]
Confidence: X/10
```

### 2.4 仲裁消息

```
[ARBITRATION]
Disputed Point: [争议点]
Party A Position: [A 方观点]
Party B Position: [B 方观点]
Ruling: [仲裁结论]
Rationale: [仲裁理由]
```

### 何时用 message vs broadcast

| 场景 | 方式 | 理由 |
|------|------|------|
| 分配任务给特定 teammate | `message` | 只与目标相关 |
| 回复特定 teammate | `message` | 一对一沟通 |
| 辩论中的挑战/回应 | `message` | 定向交流 |
| 阶段完成通知 | `broadcast` | 所有人需要知道 |
| 紧急阻塞问题 | `broadcast` | 所有人需要停下 |
| 最终判定结论 | `broadcast` | 所有人需要知道 |

**关键原则**: 默认用 `message`，只在真正需要所有人知道时用 `broadcast`。Broadcast 消耗是 N 倍（N = teammate 数量）。

---

## Rule 3: Task List Management (任务列表管理)

### 3.1 任务状态追踪

每个阶段**必须**维护清晰的任务列表：

```
TaskCreate:
  subject: "[Phase N] [角色] - [具体任务]"
  description: |
    [完整的任务描述]
    [期望产出]
    [约束条件]
```

### 3.2 任务更新规则

| 何时更新 | 更新什么 |
|---------|---------|
| Teammate 开始工作 | Status → IN_PROGRESS |
| Teammate 完成任务 | Status → COMPLETED, 附上结果 |
| 遇到阻塞 | Status → BLOCKED, 说明原因 |
| Lead 取消任务 | Status → CANCELLED |

### 3.3 任务依赖

- 有依赖关系的任务**必须**标注依赖
- 被依赖的任务完成后才能启动下游任务
- Lead 负责按依赖顺序释放任务

---

## Rule 4: File Conflict Prevention (文件冲突防御)

**核心规则**: 同一时间，一个文件只能由一个 agent 编辑。

### 4.1 文件所有权分配

在 Phase 4（并行实现）中：

```
[FILE OWNERSHIP]
Implementer-1:
  - src/auth/login.ts
  - src/auth/register.ts
  - tests/auth/login.test.ts

Implementer-2:
  - src/api/routes.ts
  - src/api/middleware.ts
  - tests/api/routes.test.ts

SHARED (sequential write):
  - src/config/index.ts
  - package.json
```

### 4.2 共享文件处理

当多个 agent 需要修改同一文件时：

1. Lead 指定写入顺序
2. 先写的 agent 完成后通知 Lead
3. Lead 通知下一个 agent 可以写入
4. **绝不允许**两个 agent 同时编辑同一文件

### 4.3 冲突检测

如果发现文件冲突：
1. 立即停止相关 agent
2. Lead 检查冲突内容
3. 决定保留哪个版本或合并
4. 通知受影响的 agent 重新基于最新版本工作

---

## Rule 5: Team Size Guidelines (团队规模指南)

### 5.1 按阶段推荐规模

| 阶段 | Small (2-3) | Medium (3-5) | Large (5-7) |
|------|-------------|--------------|-------------|
| P1 需求辩论 | 2 分析师 | 3 分析师 | 3 分析师 + 领域专家 |
| P2 架构竞标 | 2 架构师 | 2 架构师 + 评审 | 3 架构师 + 2 评审 |
| P3 规划风险 | 1 规划 + 1 风险 | 1 规划 + 1 风险 | 2 规划 + 2 风险 |
| P4 并行实现 | 1 实现 + 1 TDD | 2 实现 + 1 TDD | 3 实现 + 2 TDD |
| P5 红队审查 | 1 红 + 1 蓝 | 2 红 + 1 蓝 + 1 仲裁 | 3 红 + 2 蓝 + 1 仲裁 |
| P6 对抗调试 | 2 调查 + 1 DA | 3 调查 + 1 DA + 1 综合 | 5 调查 + 1 DA + 1 综合 |
| P7 交付验收 | 2 验收 | 2 验收 + 1 文档 | 3 验收 + 2 文档 |

### 5.2 何时用哪个规模

| 条件 | 推荐规模 |
|------|---------|
| 小功能 (<500 行预估) | Small |
| 标准功能 (500-3000 行) | Medium |
| 复杂功能 (>3000 行) | Large |
| 安全关键功能 | Large (特别是 P5) |
| 快速验证 | Small |

---

## Rule 6: Idle Teammate Handling (空闲 Teammate 处理)

### 6.1 检测空闲

如果一个 teammate 在以下时间内无响应：
- 调查任务: 5 分钟
- 辩论回合: 3 分钟
- 代码实现: 10 分钟

### 6.2 处理流程

1. **第一次**: SendMessage 询问状态
2. **第二次** (再等 2 分钟): SendMessage 明确催促
3. **第三次** (再等 2 分钟): 标记为 STUCK，重新分配任务或跳过

```
[IDLE CHECK]
To: [teammate-name]
Message: "Status check - please report your current progress. If blocked, describe the blocker."
```

### 6.3 Stuck Teammate 替换

如果 teammate 被标记为 STUCK：
1. 发送 shutdown_request
2. 如需要，spawn 新 teammate 接替任务
3. 新 teammate 从上一次已知状态继续

---

## Rule 7: Error Recovery (错误恢复)

### 7.1 TeamCreate 失败

```
原因: Agent Teams 功能未启用
处理:
  1. 提示用户设置 CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
  2. 退出流水线
```

### 7.2 Teammate Spawn 失败

```
原因: 资源不足或配额限制
处理:
  1. 减小团队规模（降级到 small）
  2. 如果 small 也失败，退出并通知用户
  3. 记录失败信息到日志
```

### 7.3 Teammate 崩溃 (mid-task)

```
处理:
  1. 标记相关任务为 FAILED
  2. 评估影响:
     - 如果是调查员: spawn 新调查员接替
     - 如果是 Devil's Advocate: Lead 临时充当
     - 如果是 Implementer: 重新分配任务
  3. 记录崩溃信息
```

### 7.4 辩论死锁

```
条件: 3 轮辩论后仍无收敛
处理:
  1. Evidence Synthesizer 强制判定
  2. 如果 Synthesizer 也无法判定，Lead 基于现有证据做决定
  3. 记录"强制判定"标记到报告中
```

### 7.5 Phase 5-6 循环超限

```
条件: Red Team → Debug → Red Team 循环超过 3 次
处理:
  1. 断路器触发
  2. 生成剩余问题报告
  3. 标记为 BLOCKED，请求人工干预
  4. 不阻止 Phase 7 的文档更新（但标记为 INCOMPLETE）
```

---

## Rule 8: Communication Protocol Summary (通信协议总结)

### 8.1 消息优先级

| 优先级 | 类型 | 处理 |
|--------|------|------|
| P0 CRITICAL | 文件冲突、安全漏洞 | 立即 broadcast + 暂停相关工作 |
| P1 HIGH | Blocker 发现、任务完成 | 尽快通知 Lead |
| P2 NORMAL | 进度更新、发现报告 | 下一轮检查时处理 |
| P3 LOW | 建议、观察 | 在最终报告中包含 |

### 8.2 Lead 消息处理流程

```
收到消息
  │
  ├── P0 CRITICAL → 立即处理
  │     ├── 文件冲突 → 停止相关 agent → 仲裁
  │     └── 安全漏洞 → broadcast 通知 → 标记 blocker
  │
  ├── P1 HIGH → 当前轮结束前处理
  │     ├── Blocker → 记录 → 安排 Phase 6 处理
  │     └── 任务完成 → 释放下游任务
  │
  ├── P2 NORMAL → 汇总到轮次报告
  │
  └── P3 LOW → 汇总到最终报告
```

---

## Violation Consequences (违规后果)

| 违规 | 后果 |
|------|------|
| 未清理 team 就开下一阶段 | Lead 立即执行 cleanup 再继续 |
| 两个 agent 同时编辑同一文件 | 回滚后一个 agent 的修改，重新排队 |
| Lead 自己执行调查/编码 | 流水线暂停，提醒 Lead 使用 teammate |
| Broadcast 滥用 | 提醒改用 message |
| Teammate 名称重复 | Spawn 失败，重新命名 |
| 跳过 shutdown 直接 TeamDelete | 可能导致 teammate 未完成清理 |
