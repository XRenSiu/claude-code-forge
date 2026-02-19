---
name: self-healing
description: 自愈协议。定义心跳、任务迁移、交叉验证、健康评分和优雅降级机制，提升 Phase 4 并行实现的容错能力。
---

# Self-Healing Protocol Rules

本规则定义 forge-teams 并行实现阶段 (Phase 4) 的自愈机制。当 Agent 停滞、崩溃或产生回归时，系统自动检测、恢复和调整，而非等待人工干预。

**适用范围**: Phase 4 (Parallel Implementation)。其他阶段继续使用 `team-coordination.md` Rule 6 的基础 idle 检测。

**核心理念**: 检测要快、恢复要自动、降级要有序。

```
┌─────────────────────────────────────────────────────────────────┐
│                    SELF-HEALING FEEDBACK LOOP                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Rule 1: Heartbeat ──▶ 检测问题                                  │
│          │                                                       │
│          ▼                                                       │
│  Rule 4: Health Scoring ──▶ 量化影响                              │
│          │                                                       │
│          ▼                                                       │
│  Rule 2: Task Migration ──▶ 恢复工作                              │
│          │                                                       │
│          ▼                                                       │
│  Rule 3: Cross-Validation ──▶ 验证恢复                            │
│          │                                                       │
│          ▼                                                       │
│  Rule 5: Graceful Degradation ──▶ 调整团队结构                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Rule 1: Heartbeat Protocol (心跳协议)

### 1.1 心跳消息格式

```
[HEARTBEAT]
Agent: {agent-name}
Task: T{id} - {title}
Phase: RED / GREEN / REFACTOR / COMMIT / IDLE
Files Touched: [自上次心跳以来接触的文件列表]
Warnings: [任何异常情况，或 NONE]
```

### 1.2 心跳间隔

| 规则 | 说明 |
|------|------|
| TDD 阶段转换 | 每次 RED→GREEN、GREEN→REFACTOR、REFACTOR→COMMIT 转换时发送 |
| 长阶段补发 | 如果在同一 TDD 阶段工作超过 3 分钟，补发一次心跳 |
| 复用原则 | `[PROGRESS UPDATE]` 和 `[TASK COMPLETED]` 消息**等价于心跳** |

**关键设计**: 心跳与 TDD 阶段转换自然对齐。正常工作的 agent 每 1-3 分钟就有一次阶段转换，几乎不需要发送专门的 `[HEARTBEAT]`。只有在长时间停留在同一阶段时才需要补发。这意味着**正常情况下心跳开销接近零**。

### 1.3 停滞检测阈值

Lead 根据以下阈值判断 agent 状态：

| 级别 | 条件 | Lead 动作 |
|------|------|----------|
| HEALTHY | 最后心跳 < 3 min | 无需操作 |
| WARN | 3-6 min 无心跳 (1 次缺失) | SendMessage 状态检查，Health -10 |
| STALL | 6-9 min 无心跳 (2 次缺失) | 准备迁移，最后通知，Health -20 |
| DEAD | 9+ min 无心跳 (3 次缺失) | 执行迁移，Health -25 |

### 1.4 Lead 心跳追踪

Lead 维护每个 agent 的心跳记录：

```
[HEARTBEAT TRACKER]
| Agent | Last Heartbeat | Status | Consecutive Misses |
|-------|---------------|--------|-------------------|
| implementer-1 | 2 min ago | HEALTHY | 0 |
| implementer-2 | 7 min ago | STALL | 2 |
| implementer-3 | 1 min ago | HEALTHY | 0 |
```

**重要**: 系统自动发送的 idle notification **不算**心跳。只有 agent 主动发送的 `[HEARTBEAT]`、`[PROGRESS UPDATE]`、`[TASK COMPLETED]` 才计入。

---

## Rule 2: Automatic Task Migration (自动任务迁移)

### 2.1 迁移触发条件

| 触发 | 动作 |
|------|------|
| STALL 检测到 (2 次心跳缺失) | 发送 `[MIGRATION PREPARE]` 作为最后机会 |
| DEAD 检测到 (3 次心跳缺失) | 立即执行迁移 |
| Agent 报告不可恢复错误 | 立即执行迁移 |
| `[BLOCKED]` 超过 5 分钟无解决 | Lead 主动提议迁移 |

### 2.2 状态捕获协议

迁移前，Lead 必须捕获当前状态：

```
[MIGRATION STATE CAPTURE]
Stalled Agent: {agent-name}
Task: T{id}
Last Known TDD Phase: {从最后心跳/进度更新推断}
Committed Work: {检查 git log --oneline --grep="[T{id}]"}
Uncommitted Files: {从最后心跳的 Files Touched 推断}
Remaining Tasks: {该 agent 未完成的任务列表}
Dependencies Affected: {等待该 agent 的下游任务}
```

**判断已提交 vs 未提交**:

```bash
# 检查任务是否有已提交的工作
git log --oneline --grep="[T{id}]"
```

| 结果 | 含义 | 新 agent 起点 |
|------|------|-------------|
| 有 `[T{id}]` 提交 | RED 或 GREEN 阶段已提交 | 从提交处继续 |
| 无 `[T{id}]` 提交 | 任务未产出任何提交 | 从头开始 |

### 2.3 迁移执行

```
执行顺序:
1. Lead 发送 shutdown_request 给停滞 agent (best-effort，可能无响应)
2. Lead 通过 TaskUpdate 移除停滞 agent 的任务 owner
3. Lead 选择目标 agent:
   a) 优先: 健康分最高 + 剩余任务最少的现有 agent
   b) 备选: spawn 新的替换 agent
4. Lead 发送 [TASK MIGRATION] 消息给目标 agent
5. Lead 更新 File Ownership Map
```

### 2.4 迁移消息格式

```
[TASK MIGRATION]
Migrated Task: T{id} - {title}
Previous Agent: {stalled-agent-name}
Last Known State: {RED / GREEN / REFACTOR / none}
Committed Work: {YES / NO, if YES: commit hash}
Your Action:
  - If committed: Read the commit, verify tests pass, continue from next phase
  - If not committed: Start from scratch using task description
  - Run: git log --oneline --grep="[T{id}]" to check
Files Ownership: [转移的文件列表]
Priority: HIGH (迁移任务优先于队列中的其他任务)
```

### 2.5 替换 Agent Bootstrap

当需要 spawn 新 agent 替代停滞者时，spawn prompt 必须包含:

1. 原始任务分配 (从 TaskList 获取)
2. 哪些任务已被其他 agent 完成 (已完成列表)
3. 更新后的 File Ownership Map
4. 明确指令: 先检查 `git log` 再开始任何任务
5. 自愈协议要求: 心跳、交叉验证

---

## Rule 3: Cross-Validation (交叉验证)

### 3.1 任务完成后全套件运行

**铁律**: 每个任务完成并 commit 后，运行完整测试套件，不只跑自己的测试。

```
COMMIT Phase 扩展:
1. git add [specific-files]
2. git commit -m "[T{id}] {type}: {description}"
3. 运行完整测试套件: npm test 2>&1  ← 新增
4. 如果全部通过: 继续报告完成
5. 如果有失败: 检查失败的测试属于谁
   - 属于自己的任务: 修复后重新提交
   - 属于其他 agent 的任务: 发送 [CROSS-FAILURE ALERT]
```

### 3.2 交叉验证报告格式

```
[CROSS-VALIDATION]
Task Completed: T{id}
Own Tests: PASS ({N} tests)
Full Suite: PASS / FAIL
  Total: {N} tests
  Passing: {M}
  Failing: {K}
  Failed Tests: [失败测试名称列表，如有]
Impact Assessment:
  - 其他 agent 的失败测试: [列表]
  - 可能原因: [评估]
Action: NONE / ALERT_LEAD
```

### 3.3 交叉失败告警

当发现其他 agent 的测试失败时:

```
[CROSS-FAILURE ALERT]
Reporter: {agent-name}
Trigger Task: T{id} (我的任务可能导致了失败)
Failed Tests:
  - {test_name}: belongs to T{other_id} (owned by {other_agent})
Possible Cause: [评估]
My Commit: {hash}
Recommended Action: [revert my commit / coordinate with other agent / investigate]
```

**处理流程**:
1. Reporter **立即停止**，不继续下一个任务
2. Lead 收到 alert 后，要求 sentinel 独立验证
3. Sentinel 确认是否真的是回归 (排除 in-progress 干扰)
4. Lead 决定: revert、修复、还是协调

### 3.4 Wave 边界验证

当一个并行组 (Wave) 的所有任务完成后，在释放下一波之前进行硬卡点验证:

```
[WAVE BOUNDARY VERIFICATION]
Wave: {N}
Tasks Completed: [列表]
Verification:
  [ ] npm run build — 通过
  [ ] npm test — 全部通过
  [ ] npm run type-check — 通过 (如果有)
  [ ] git status --porcelain — 无未提交变更
Result: PASS → proceed to Wave {N+1} / FAIL → investigate before proceeding
```

**执行者**: Lead 请求 quality-sentinel 执行验证 (sentinel 有 Bash 访问权限且是只读角色，适合运行验证命令)。

**失败处理**: 如果 Wave 边界验证失败:
1. **不释放**下一波任务
2. 分析失败原因 (哪个 commit 引入了问题)
3. 创建修复任务分配给相关 implementer
4. 修复后重新验证
5. 验证通过后释放下一波

---

## Rule 4: Agent Health Scoring (Agent 健康评分)

### 4.1 初始分与评分事件

每个 agent 初始分 **100**，上限 **150**，下限 **0**。

| 事件 | 分数变化 | 理由 |
|------|---------|------|
| 任务成功完成 | +5 | 可靠交付 |
| 交叉验证通过 (全套件绿色) | +10 | 无回归 |
| Sentinel 质量评分 ≥ 8/10 | +5 | 高质量工作 |
| 心跳缺失 (WARN) | -10 | 通信中断 |
| 停滞事件 (STALL) | -20 | 显著延迟 |
| 交叉验证失败 (破坏他人测试) | -15 | 引入回归 |
| Quality Issue: Critical | -30 | 严重质量问题 |
| Quality Issue: High | -15 | 重要质量问题 |
| Quality Issue: Medium | -5 | 轻微质量问题 |
| 需要任务迁移 (从该 agent 迁出) | -25 | Agent 无法完成 |

**评分不对称设计**: 负面事件的扣分大于正面事件的加分，因为漏检问题 (false negative) 比过度谨慎 (false positive) 代价更高。

### 4.2 阈值与动作

| 健康分 | Agent 状态 | Lead 动作 |
|-------|----------|----------|
| 80-150 | HEALTHY | 正常运行 |
| 50-79 | DEGRADED | 重新分配下一波的复杂任务给更健康的 agent |
| 30-49 | CRITICAL | 停止分配新任务，将剩余任务重新分配 |
| 0-29 | FAILING | 发送 shutdown_request，必要时 spawn 替换 |

### 4.3 健康仪表盘

Lead 在 Wave 完成后或阶段结束时输出健康仪表盘:

```
[HEALTH DASHBOARD]
| Agent | Score | Tasks Done | Stalls | Migrations | Quality Avg |
|-------|-------|-----------|--------|------------|-------------|
| implementer-1 | 115 | 5/5 | 0 | 0 | 8.5/10 |
| implementer-2 | 65 | 3/4 | 1 | 0 | 7.0/10 |
| implementer-3 | 40 | 2/5 | 2 | 1 | 6.0/10 |
```

### 4.4 评分校准

健康评分由 Lead 根据观察事件维护，是**决策辅助**而非硬性规则:

- 如果所有 agent 的分数在正常运行后都低于 50 → 说明评分过于激进，Lead 可以在 Wave 边界进行**评分重置**
- 如果所有 agent 分数相近且差异在 10 分以内 → 视为等效，不做区别对待
- Lead 始终拥有任务分配的最终决定权

---

## Rule 5: Graceful Degradation (优雅降级)

### 5.1 Level 1: 单 Agent 丢失

```
条件: 1 个 implementer DEAD 且无法替换

处理:
1. Broadcast: "[DEGRADATION L1] {agent-name} lost. Redistributing {N} remaining tasks."
2. 更新 File Ownership Map: 将其文件转移给剩余 agent
3. 按健康分将任务重新分配给剩余 agent
4. 继续并行执行 (N-1 个 agent)
5. 如有必要调整 Wave 计划 (部分 Wave 可能需要串行化)
```

### 5.2 Level 2: 多 Agent 丢失

```
条件: 2+ 个 implementer DEAD

处理:
1. Broadcast: "[DEGRADATION L2] Multiple agents lost. Switching to sequential mode."
2. 将所有剩余任务整合给最健康的存活 agent
3. 从并行执行切换为顺序执行
4. Quality sentinel 继续抽查 (如果存活)
5. Lead 提供更主动的逐任务指导
```

### 5.3 Level 3: 全面故障退回

```
条件: 所有 implementer DEAD 或 只剩 sentinel

处理:
1. Broadcast: "[TOTAL DEGRADATION] All implementers lost."
2. Shutdown sentinel (sentinel 无法实现代码)
3. TeamDelete
4. Lead 切换为独立执行模式 (pdforge 式顺序实现)
5. Lead 直接按 TDD 纪律实现剩余任务
6. 在报告中记录: "Degraded from parallel to solo execution at task T{id}"
```

### 5.4 降级公告

降级使用 `broadcast` 通知所有存活 agent — 这是 broadcast 的合法使用场景 (所有人需要知道团队结构变化)。

---

## Rule 6: Mechanism Integration (机制联动)

### 6.1 联动流程

5 个机制形成闭环:

```
Heartbeat (R1) ──检测──▶ Health Scoring (R4) ──量化──▶ Task Migration (R2)
                                                           │
                                                           ▼
Graceful Degradation (R5) ◀──调整── Cross-Validation (R3) ──验证──┘
```

### 6.2 场景联动表

| 场景 | 触发机制 | 联动流程 |
|------|---------|---------|
| Agent 正常工作 | R1 only | 更新追踪，继续 |
| Agent 缺失 1 次心跳 | R1 + R4 | WARN + Health -10 |
| Agent 停滞 (2 次缺失) | R1 + R2 + R4 | 准备迁移 + Health -20 |
| Agent 死亡 (3 次缺失) | R1 + R2 + R4 + R5 | 执行迁移 + 调整团队 |
| 交叉验证发现回归 | R3 + R4 | Alert + 引起者 Health -15 |
| 多 Agent 死亡 | R1 + R2 + R4 + R5 | 顺序模式退回 |
| Wave 边界到达 | R3 | 完整验证后释放下一波 |

### 6.3 系统性停滞处理

**关键区分**: 全员同时沉默 ≠ 个别 agent 停滞。

```
IF 所有 implementer 在同一时间窗口变为 WARN:
  1. 这很可能是系统性问题 (环境故障、共享依赖缺失)
  2. Broadcast 状态检查请求
  3. IF 所有人报告相同 blocker:
     → 这是环境问题，不扣 Health 分
     → 修复环境问题
     → 恢复执行
  4. IF 无人响应:
     → 尝试 spawn 一个诊断 agent 检查环境
     → IF 环境有问题: 修复后恢复
     → IF 环境正常: 触发 Level 3 降级
```

### 6.4 心跳开销管理

| 团队规模 | 心跳严格度 | 理由 |
|---------|----------|------|
| Small (2 implementers) | 宽松 (5 min 间隔) | Lead 容易观察到状态 |
| Medium (3-4 implementers) | 标准 (3 min 间隔) | 默认配置 |
| Large (5+ implementers) | 严格 (2 min 间隔) | 大团队需要更频繁的信号 |

---

## Summary: Self-Healing Quick Reference

```
┌─────────────────────────────────────────────────────────────────┐
│                    SELF-HEALING QUICK REFERENCE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  HEARTBEAT: Implementer → Lead, every 3 min                     │
│    (PROGRESS UPDATE / TASK COMPLETED 也算)                       │
│                                                                  │
│  STALL DETECTION:                                                │
│    WARN (3-6 min) → STALL (6-9 min) → DEAD (9+ min)            │
│                                                                  │
│  TASK MIGRATION:                                                 │
│    State Capture → Shutdown → Reassign → New Agent Picks Up     │
│                                                                  │
│  CROSS-VALIDATION:                                               │
│    Each task: run full suite → alert if others' tests break     │
│    Each wave: build + test + type-check before next wave        │
│                                                                  │
│  HEALTH SCORING:                                                 │
│    Start: 100 | +5/+10 per success | -10/-20/-30 per failure    │
│    <50: redistribute | <30: replace                              │
│                                                                  │
│  DEGRADATION:                                                    │
│    L1: N-1 parallel | L2: sequential | L3: solo executor        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
