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

### 6.1 Wakeup Guard 基础机制（所有阶段通用）

**问题**: Lead 在等待 teammate 回复时，会阻塞在"等新消息"状态。如果对方卡住不响应，Lead 自己也无法主动触发状态检查，导致整条流水线停摆。

**解决**: Lead 每次通过 SendMessage 发送**期望对方回复才能继续的消息**时，必须同时调用 `ScheduleWakeup` 设置守卫定时器。守卫到期时 Lead 被叫醒，主动扫描收件箱与状态，避免无限阻塞。

**守卫到期时的标准检查**:

1. 扫描收件箱：目标 teammate 是否已回复？
   - **有回复** → 处理，结束本轮守卫
   - **无回复** → 进入升级阶梯（见 6.2 / 6.3）
2. 记录守卫事件：时间戳、检查结果、采取的动作

**原则**:
- Wakeup Guard **不替代**响应监听，而是兜底 — Lead 在任何时候收到回复都应立即处理，守卫只是防止永久阻塞
- 同一 teammate 刚被确认有回复 → 重置守卫计数，不累加到下一阶段
- 即使 Lead 被叫醒时发现一切正常，也应重新 `ScheduleWakeup` 继续下一轮守卫，直到期望的交付完成

### 6.2 非 Phase 4 阶段的应用 (P1, P2, P3, P5, P6, P7)

**首次 Wakeup 时长**（按任务类型）:

| 任务类型 | 首次 Wakeup T |
|---------|---------------|
| 调查任务 | 5 min |
| 辩论回合 | 3 min |
| 代码实现 | 10 min |

**三阶段升级流程**（全部由 `ScheduleWakeup` 硬性触发）:

```
T=0     Lead 发送 SendMessage + ScheduleWakeup(T)
        │
T=T     守卫#1 到期 → 扫描收件箱
        ├─ 有回复 → 处理，结束守卫
        └─ 无回复 → 发 [IDLE CHECK] + ScheduleWakeup(+2min)
        │
T=T+2   守卫#2 到期 → 扫描收件箱
        ├─ 有回复 → 处理，结束守卫
        └─ 无回复 → 发 [IDLE URGENT] + ScheduleWakeup(+2min)
        │
T=T+4   守卫#3 到期 → 扫描收件箱
        ├─ 有回复 → 处理，记录迟到
        └─ 无回复 → 标记 STUCK，执行替换 / 重新分配 / 跳过
```

**消息模板**:

```
[IDLE CHECK]  — Nudge 1/2
To: [teammate-name]
Message: "Status check — {T} min since my last message. Please reply with:
  1. One-line current state (what you're doing now)
  2. Any blocker (describe if present)
  3. Continue autonomously or need help
If no reply in 2 min I will escalate."
```

```
[IDLE URGENT]  — Nudge 2/2
To: [teammate-name]
Message: "Second status check — {T+2} min silent. Last chance before I
reassign this task and spawn a replacement. Reply with status or blocker now."
```

**Stuck Teammate 替换**（守卫#3 到期无回复时）:

1. 发送 `shutdown_request`（best-effort，不等待回复）
2. 如需要，spawn 新 teammate 接替任务
3. 新 teammate 从上一次已知状态继续

### 6.3 Phase 4 (Parallel Implementation) — 自愈协议

> **Phase 4 使用自愈协议替代基础 idle 检测。** 完整定义见 `rules/self-healing.md`。

Phase 4 的 idle 检测由心跳协议驱动，比被动轮询更精确：

| 级别 | 条件 | 动作 |
|------|------|------|
| WARN | 3-6 min 无心跳 | 状态检查 + Health -10 |
| STALL | 6-9 min 无心跳 | 准备迁移 + Health -20 |
| DEAD | 9+ min 无心跳 | 执行迁移 + Health -25 |

Phase 4 还提供：
- **自动任务迁移** (self-healing.md Rule 2) — 代替手动重新分配
- **健康评分** (self-healing.md Rule 4) — 量化 agent 可靠性
- **交叉验证** (self-healing.md Rule 3) — 每个任务完成后全套件验证
- **优雅降级** (self-healing.md Rule 5) — 3 级有序退化

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
     - 如果是 Implementer (Phase 4): 使用自愈协议
       → 任务迁移 (self-healing.md Rule 2)
       → 健康评分更新 (self-healing.md Rule 4)
       → 必要时触发降级 (self-healing.md Rule 5)
     - 如果是 Implementer (非 Phase 4): 重新分配任务
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

### 7.6 系统性故障 (Phase 4)

```
条件: 所有 implementer 同时停滞或崩溃
处理:
  1. Broadcast 状态检查，确认是否为系统性问题
  2. 检查环境问题 (构建是否失败、依赖是否缺失、共享服务是否宕机)
  3. 如果是环境问题: 修复环境，不扣健康分，恢复执行
  4. 如果原因不明: 尝试 spawn 诊断 agent 检查环境
  5. 如果无法恢复: 触发 Total Degradation (self-healing.md Rule 5.3)
     → Lead 退回独立顺序执行模式
  6. 在报告中记录: "Systemic failure at [时间], fallback to solo mode"
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
