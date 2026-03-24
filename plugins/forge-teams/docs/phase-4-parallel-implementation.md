# 阶段 4：并行实现 (Parallel Implementation)

> 多 agent 并行实现任务，遵循 TDD 纪律，文件所有权驱动冲突预防

---

## 📋 阶段概述

| 维度 | 说明 |
|------|------|
| **目标** | 多 agent 并行实现任务，遵循 TDD 纪律 |
| **输入** | 任务计划（含文件所有权映射，来自阶段3） |
| **输出** | 已测试的代码 |
| **上游阶段** | 协作规划（阶段3） |
| **下游阶段** | 对抗审查（阶段5） |

---

## 🧩 组件清单

| 类型 | 名称 | 模型 | 说明 |
|------|------|------|------|
| **Agent** | `team-implementer` (×N) | sonnet | 并行任务执行者，可多实例 |
| **Agent** | `quality-sentinel` (×1) | sonnet | 质量哨兵，只读 |
| **Skill** | `parallel-implementation` | - | Phase 4 编排逻辑 |
| **Rule** | `team-coordination.md` | - | 文件冲突防止规则 |

```
┌───────────────────────────────────────────────────────────────┐
│                    阶段 4 组件拓扑                              │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│                    ┌──────────────┐                           │
│                    │  Lead (Main)  │                           │
│                    │  Delegate 模式│                           │
│                    └──────┬───────┘                           │
│                           │                                   │
│              ┌────────────┼────────────┐                     │
│              │            │            │                      │
│              ▼            ▼            ▼                      │
│     ┌──────────────┐ ┌──────────┐ ┌──────────────┐          │
│     │ implementer-1│ │impl-2    │ │ implementer-N│          │
│     │ Task: T001   │ │Task: T003│ │ Task: T005   │          │
│     │ Files: a,b   │ │Files: c,d│ │ Files: e,f   │          │
│     └──────────────┘ └──────────┘ └──────────────┘          │
│              │            │            │                      │
│              └────────────┼────────────┘                     │
│                           │                                   │
│                           ▼                                   │
│              ┌─────────────────────────┐                     │
│              │  quality-sentinel (×1)   │                     │
│              │  只读抽查已完成任务       │                     │
│              └─────────────────────────┘                     │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## 💡 为什么这样设计

### 为什么并行而非顺序

传统单 agent 顺序执行模式一次只运行一个任务。这种方式安全但速度慢。

```
┌─────────────────────────────────────────────────────────────┐
│           单 agent 顺序执行 vs forge-teams 并行执行            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  单 agent 顺序执行 (sequential):                             │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                       │
│  │ T1 │→│ T2 │→│ T3 │→│ T4 │→│ T5 │  Wall time: 5T       │
│  └────┘ └────┘ └────┘ └────┘ └────┘                       │
│                                                             │
│  forge-teams 并行执行 (parallel, 3 implementers):            │
│  ┌────┐ ┌────┐                                             │
│  │ T1 │→│ T4 │                    implementer-1             │
│  └────┘ └────┘                                             │
│  ┌────┐ ┌────┐                                             │
│  │ T2 │→│ T5 │                    implementer-2             │
│  └────┘ └────┘                                             │
│  ┌────┐                                                    │
│  │ T3 │                           implementer-3             │
│  └────┘                                                    │
│                          Wall time: ~2T                     │
│                                                             │
│  Token cost: ~same (same total work)                        │
│  Wall-clock time: reduced by N (parallelism factor)         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Key advantages of parallel execution:
- **Wall-clock time** reduced by factor N (number of parallel implementers)
- **Total token cost** is similar (same work, just concurrent)
- **Agent Teams** natively support parallel agent instances

---

### 为什么需要文件所有权

Parallel agents modifying the same file = **merge conflicts and race conditions**.

```
┌─────────────────────────────────────────────────────────────┐
│              文件所有权：并行安全的 #1 约束                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WITHOUT file ownership:                                    │
│                                                             │
│  implementer-1: Edit src/config.ts line 15 → add field A   │
│  implementer-2: Edit src/config.ts line 15 → add field B   │
│  Result: CONFLICT — one agent's changes overwritten         │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  WITH file ownership:                                       │
│                                                             │
│  P3 (planning) assigns:                                     │
│    T001 OWNS src/config.ts → implementer-1                  │
│    T003 READS src/config.ts → implementer-2 (read-only)     │
│  Lead verifies: no OWNS overlap → safe to parallelize       │
│  Result: NO CONFLICT — ownership prevents race condition    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

文件所有权处理策略:

| 情况 | 策略 | 示例 |
|------|------|------|
| 无重叠 | 并行执行 | T1 owns A, T2 owns B |
| 读依赖 | 并行执行 + 顺序约束 | T2 reads A (T1 must complete first) |
| 写重叠 | 顺序执行 | T1 owns C, T3 owns C → sequential |
| 共享文件 | 合并任务 | T1+T3 合并为一个 task |

---

### 为什么 Quality Sentinel（而不是事后审查）

```
┌─────────────────────────────────────────────────────────────┐
│         传统事后审查 vs Quality Sentinel 实时抽查              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Traditional (post-hoc):                                    │
│  T1 → T2 → T3 → T4 → T5 → [REVIEW] → find 3 issues       │
│                                         ↑ issues propagated │
│                                           across T3-T5      │
│                                                             │
│  Quality Sentinel (real-time):                              │
│  T1 ✓   T2 ✗ → fix task created                            │
│  T3 ✓   T4 ✓   T5 ✓                                       │
│         ↑ issue caught early, no propagation                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

| 维度 | 事后审查 | Quality Sentinel |
|------|---------|-----------------|
| 发现时机 | 全部完成后 | 实时（任务完成即检查） |
| 问题传播 | 问题可能扩散到后续任务 | 早发现早修复 |
| Overhead | 集中审查，时间长 | 低 overhead，随机抽查 |
| 修复成本 | 高（回溯修改多个文件） | 低（只修改当前任务） |

---

### Quality Sentinel 为什么只读

| 如果 Sentinel 可写 | 如果 Sentinel 只读 |
|-------------------|-------------------|
| 变成第二个 implementer | 保持 reviewer 角色 |
| 角色混淆：谁审查 sentinel 的代码？ | 角色清晰：sentinel 审查，implementer 修复 |
| 可能引入新 bug | 只创建 fix task，不修改代码 |
| 违反单一职责 | 严格单一职责 |

---

### 为什么 Lead 用 Delegate Mode

Lead (main session) does NOT implement code. It only:

| Lead 职责 | Lead 不做 |
|----------|----------|
| 分配任务 (TaskCreate) | 写代码 |
| 监控进度 (TaskList) | 修改文件 |
| 解决冲突和阻塞 | 运行测试 |
| 协调 implementer 间通信 | Debug |

Why: If Lead writes code, it becomes a **bottleneck** — can't coordinate while coding.

---

### 关键设计决策

| 决策 | 选项 A | 选项 B | 选择 | 原因 |
|------|--------|--------|------|------|
| 执行模式 | 顺序 | 并行 | **并行** | Agent Teams 的核心优势 |
| 冲突防止 | 文件锁 (runtime) | 所有权 (planning) | **所有权** | 预防优于检测 |
| 质量控制 | 事后审查 | 实时 sentinel | **实时** | 早发现早修复 |
| Sentinel 权限 | 读写 | 只读 | **只读** | 角色分离 |
| Implementer 数量 | 固定 | 动态 (2-5) | **动态** | 按任务数量调整 |
| TDD | 可选 | 强制 | **强制** | 确保代码质量和可验证性 |
| Lead 角色 | 参与实现 | 纯协调 | **纯协调** | 避免成为瓶颈 |

---

## 🔧 组件详解

### 1. team-implementer Agent (xN instances)

**角色定义**:

```yaml
name: team-implementer
model: sonnet
tools: Read, Write, Edit, Grep, Glob, Bash
```

**职责**:
- 自主从 TaskList claim 任务
- 严格 TDD: 写测试 -> 实现 -> 通过 -> 提交
- 通过 SendMessage 报告进度和阻塞
- 只修改自己 task 指定的文件

**TDD 执行循环**:

```
┌─────────────────────────────────────────────────────────────┐
│              Implementer TDD 循环 (每个 Task)                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────────┐                                        │
│  │ 1. Claim Task   │  SendMessage → Lead                    │
│  └────────┬───────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌────────────────┐                                        │
│  │ 2. Write Test   │  RED: test fails                       │
│  └────────┬───────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌────────────────┐                                        │
│  │ 3. Implement    │  GREEN: test passes                    │
│  └────────┬───────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌────────────────┐                                        │
│  │ 4. Refactor     │  GREEN: test still passes              │
│  └────────┬───────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌────────────────┐                                        │
│  │ 5. Verify       │  Run full verify command               │
│  └────────┬───────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌────────────────┐                                        │
│  │ 6. Report Done  │  SendMessage → Lead                    │
│  └────────────────┘                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**文件所有权执行规则**:

| 规则 | 说明 | 违反后果 |
|------|------|---------|
| 只修改 OWNS 文件 | 任务指定的文件 | Lead 拒绝提交 |
| 可读取 READS 文件 | 依赖文件 | 无后果（只读） |
| 不得修改未列出文件 | 计划外文件 | Lead 拒绝提交 |

---

### 2. quality-sentinel Agent (x1)

**角色定义**:

```yaml
name: quality-sentinel
model: sonnet
tools: Read, Grep, Glob, Bash  # 只读 — 无 Write, Edit
```

**职责**:
- 持续监控已完成的任务
- 随机抽查 + 全量扫描
- 发现问题 -> 创建修复 task（通过 SendMessage 通知 Lead）

**5 类抽查维度**:

| 抽查维度 | 检查内容 | 典型问题 |
|---------|---------|---------|
| **测试真实性** | 测试是否真正验证了功能 | 空测试、always-pass 断言 |
| **规范合规** | 是否符合架构 + ADR 约束 | 使用了被 ADR 否决的方案 |
| **调试残留** | 是否有调试代码遗留 | `console.log`, `debugger`, `TODO` |
| **错误处理** | 是否有完善的错误处理 | 裸 `catch(e) {}`, 吞掉错误 |
| **类型安全** | TypeScript 类型是否严格 | `any` 滥用, 非空断言 `!.` |

**抽查频率**:

```
┌─────────────────────────────────────────────────────────────┐
│              Sentinel 抽查策略                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  每完成 1 个 task → sentinel 抽查（概率 ~50%）              │
│  每完成 3 个 task → sentinel 全量扫描（必定）               │
│  所有 task 完成后 → sentinel 最终全量扫描                    │
│                                                             │
│  发现问题严重度:                                             │
│  CRITICAL → 立即通知 Lead，暂停相关 implementer             │
│  HIGH     → 创建修复 task，优先分配                         │
│  MEDIUM   → 创建修复 task，正常排队                         │
│  LOW      → 记录，不阻塞                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### 3. parallel-implementation Skill

**6 步编排流程**:

| 步骤 | 名称 | 说明 |
|------|------|------|
| Step 1 | **Plan Intake** | 读取 P3 产出的任务计划 |
| Step 2 | **Task Analysis** | 分析依赖关系 + 文件所有权，确定并行策略 |
| Step 3 | **Team Assembly** | 按任务数量创建 implementer + sentinel |
| Step 4 | **Parallel Execution** | 分配任务、监控进度、处理阻塞 |
| Step 5 | **Convergence** | 等待所有任务完成 + sentinel 最终扫描 |
| Step 6 | **Cleanup** | 验证集成、生成执行报告 |

**Step 2 详解 — 并行策略决定**:

```
┌─────────────────────────────────────────────────────────────┐
│              Task Analysis 并行策略决定                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  输入: Task Plan (含 OWNS/READS/SHARED 标注)                │
│                                                             │
│  Step 2a: 构建依赖 DAG                                     │
│    T1 ──→ T3 ──→ T5                                        │
│    T2 ──→ T4                                                │
│                                                             │
│  Step 2b: 检查文件所有权重叠                                 │
│    T1 OWNS [a.ts, b.ts]                                     │
│    T2 OWNS [c.ts, d.ts]     → 无重叠 → 可并行              │
│    T3 OWNS [e.ts]           → 依赖 T1 → T1 完成后启动      │
│    T4 OWNS [f.ts, a.ts]     → a.ts 与 T1 重叠！            │
│                                                             │
│  Step 2c: 生成执行计划                                      │
│    Wave 1: T1 ∥ T2 (并行)                                   │
│    Wave 2: T3 ∥ T4 (T4 等 T1 释放 a.ts)                    │
│    Wave 3: T5 (依赖 T3)                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Team Size 配置**:

| 配置 | Implementer 数量 | 适用场景 |
|------|-----------------|---------|
| `--team-size small` | 2 | <10 tasks, 简单功能 |
| `--team-size medium` | 3-4 | 10-20 tasks, 中等功能 |
| `--team-size large` | 5 | >20 tasks, 大型功能 |

---

## 🚀 使用流程

### 标准用法

```bash
# 中等团队 (3-5 implementers)
/forge-teams --phase 4 --team-size medium

# 小团队 (2 implementers)
/forge-teams --phase 4 --team-size small

# 大团队 (5 implementers)
/forge-teams --phase 4 --team-size large
```

### Lead 执行协议

```
┌─────────────────────────────────────────────────────────────┐
│              Lead Delegate Mode 协议                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Lead 在 P4 期间的完整职责:                                  │
│                                                             │
│  1. DISTRIBUTE                                              │
│     - 读取计划，按 Wave 分配任务                             │
│     - 通过 TaskCreate 分配给 implementer                    │
│                                                             │
│  2. MONITOR                                                 │
│     - 通过 TaskList 检查进度                                │
│     - 通过 SendMessage 接收状态更新                         │
│                                                             │
│  3. RESOLVE                                                 │
│     - 处理 implementer 间的文件冲突                         │
│     - 解决阻塞（依赖未完成、测试环境问题）                   │
│     - 分配 sentinel 创建的修复 task                         │
│                                                             │
│  4. CONVERGE                                                │
│     - 确认所有任务完成                                      │
│     - 触发 sentinel 最终扫描                                │
│     - 运行集成验证                                          │
│                                                             │
│  Lead 绝不做:                                               │
│     ✗ 写代码      ✗ 修改文件                                │
│     ✗ 运行测试    ✗ Debug                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ 单 agent 顺序方式 vs forge-teams 并行方式

| 维度 | 单 agent 顺序执行 | forge-teams (P4) | 增量价值 |
|------|-----------------|------------------|---------|
| 执行模式 | 顺序逐个执行 | 并行 Agent Teams | N 倍加速 |
| 质量控制 | 事后审查 | 实时 quality sentinel | 更早发现问题 |
| 冲突防止 | 不需要（顺序执行） | 文件所有权映射 | 并行安全保障 |
| TDD | 可选或强制 | agent 级别强制 | 确保代码质量 |
| 并行度 | 1 (顺序) | 2-5 (动态) | 可扩展 |
| Lead 角色 | 直接执行 | Delegate mode | 不成为瓶颈 |
| Token 开销 | 低 | 中（相似总量，略多协调 overhead） | 时间大幅缩短 |

### 何时选择单 agent 顺序执行

| 条件 | 推荐 | 原因 |
|------|------|------|
| <5 tasks | 单 agent 顺序 | 并行 overhead 不值得 |
| 高度耦合的任务 | 单 agent 顺序 | 无法有效并行 |
| 所有任务共享文件 | 单 agent 顺序 | 文件所有权无法隔离 |
| 时间不敏感 | 单 agent 顺序 | 并行的主要优势是时间 |

---

## ⚠️ 注意事项

### 硬约束

1. **文件所有权是硬约束**: 违反文件所有权的修改会被 Lead 拒绝，implementer 必须回退修改
2. **TDD 不可跳过**: 每个 implementer 必须遵循红-绿-重构循环，sentinel 会抽查测试真实性
3. **Sentinel 不修改代码**: 发现问题只创建 fix task，不自己修，保持角色分离
4. **Lead 不写代码**: Delegate mode 意味着只协调不实现，违反则成为瓶颈
5. **进度备忘录**: Lead 必须在每个 Task 完成时更新 `phase-4-progress.md`。P4 是最长阶段，context 中断风险最高，精确的进度记录是恢复的前提。

### 反模式清单

| 反模式 | 问题 | 正确做法 |
|--------|------|---------|
| Lead 写代码 | Lead 成为瓶颈，无法协调 | Lead 只协调，实现交给 implementer |
| Implementer 修改非 OWNS 文件 | 并行冲突 | 只修改任务指定的 OWNS 文件 |
| 跳过 TDD 红阶段 | 测试不真实 | 先写失败的测试，再实现 |
| Sentinel 修改代码 | 角色混淆 | Sentinel 只创建 fix task |
| 固定团队大小 | 资源浪费或不足 | 根据任务数量动态调整 |
| 忽略 Sentinel 发现 | 问题累积 | 及时分配修复 task |
| Wave 间无验证 | 下一波构建在错误上 | 每个 Wave 完成后验证再启动下一波 |

---

## 🔄 跨 Context 恢复支持

### 进度备忘录

Lead 维护 `phase-4-progress.md`，记录：
- 当前 Wave 编号和执行状态
- 每个 Implementer 的任务分配和完成状态
- Quality Sentinel 的抽查结果摘要
- 已完成的 Task 列表及其验证结果
- 文件所有权分配表

P4 是所有阶段中持续时间最长的阶段，进度备忘录尤其重要。Lead 应在每个 Task 完成时更新备忘录。

### 状态更新

| 时机 | .forge-state.json 更新 |
|------|----------------------|
| P4 开始 | `current_phase` → 4, P4 `status` → `in_progress`, `started_at` |
| P4 完成 | P4 `status` → `completed`, `completed_at`, `artifacts.code_report` → 文件路径, `current_phase` → 5 |
| Context 告警 | `interrupted_at`, `progress_memo` → `phase-4-progress.md` 路径 |

### 恢复后行为

P4 恢复时，Lead 从 `phase-4-progress.md` 读取：
- 已完成的 Task → 不重新执行
- 未完成的 Task → 重新分配给 Implementer
- Wave 进度 → 从中断的 Wave 继续

> **注意**: P4 的代码产出直接写入项目文件系统，不会因 context 中断丢失。进度备忘录的主要作用是避免重复执行已完成的 Task。

---

## 🔗 下一阶段

所有任务完成后，进入 **阶段 5：对抗审查**：

```bash
# 自动进入审查
/forge-teams --phase 5

# 含红队攻击
/forge-teams --phase 5 --red-team

# 省 token 模式（无红队）
/forge-teams --phase 5 --no-red-team
```

阶段 5 将对本阶段产出的所有代码进行并行审查 + 红队攻击。
