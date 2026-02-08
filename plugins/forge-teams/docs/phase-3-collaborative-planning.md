# 阶段 3：协作规划 (Collaborative Planning)

> 将架构设计分解为可执行的 2-5 分钟任务，经过独立风险评估验证

---

## 📋 阶段概述

| 维度 | 说明 |
|------|------|
| **目标** | 将架构设计分解为可执行的 2-5 分钟任务，经过风险评估验证 |
| **输入** | ADR + 架构文档（来自阶段2） |
| **输出** | 任务计划文档（含风险注解和依赖关系） |
| **上游阶段** | 对抗架构设计（阶段2） |
| **下游阶段** | 并行实现（阶段4） |

---

## 🧩 组件清单

| 类型 | 名称 | 模型 | 说明 |
|------|------|------|------|
| **Agent** | `planner` (general-purpose) | sonnet | 分解任务、写计划 |
| **Agent** | `risk-assessor` (general-purpose) | sonnet | 评估风险、验证依赖 |
| **Skill** | 无独立 skill | - | 由 forge-pipeline SKILL 编排 |
| **Rule** | `team-coordination.md` | - | 团队协作规则 |

```
┌───────────────────────────────────────────────────────────────┐
│                    阶段 3 组件拓扑                              │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│    ┌─────────────────┐        ┌──────────────────────┐       │
│    │   ADR + 架构文档  │───────▶│  Planner Agent       │       │
│    │   (阶段2 产出)   │        │  (general-purpose)   │       │
│    └─────────────────┘        └──────────┬───────────┘       │
│                                          │                    │
│                                          ▼                    │
│                               ┌──────────────────────┐       │
│                               │  初版任务计划          │       │
│                               │  (含依赖 + 文件所有权) │       │
│                               └──────────┬───────────┘       │
│                                          │                    │
│                                          ▼                    │
│                               ┌──────────────────────┐       │
│                               │  Risk Assessor Agent  │       │
│                               │  (general-purpose)    │       │
│                               └──────────┬───────────┘       │
│                                          │                    │
│                                          ▼                    │
│                               ┌──────────────────────┐       │
│                               │  风险报告 + 修改建议   │       │
│                               └──────────┬───────────┘       │
│                                          │                    │
│                                          ▼                    │
│                               ┌──────────────────────┐       │
│                               │  Planner 修改计划     │       │
│                               │  (逐条回应建议)       │       │
│                               └──────────┬───────────┘       │
│                                          │                    │
│                                          ▼                    │
│                               ┌──────────────────────┐       │
│                               │  最终任务计划          │       │
│                               │  (含风险注解)         │       │
│                               └──────────────────────┘       │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## 💡 为什么这样设计

### 为什么是协作而非对抗

Planning is less subjective than requirements or architecture:

| 对比维度 | 阶段1-2（对抗） | 阶段3（协作） |
|---------|---------------|-------------|
| 主观性 | 高（需求理解、架构权衡） | 低（任务分解有客观标准） |
| 评判标准 | 模糊（"好的架构"） | 清晰（2-5 min, testable, independent） |
| 辩论价值 | 高（暴露盲点） | 低（任务可验证） |
| 最佳交互 | 全对抗辩论 | 审查+建议 |

Task decomposition has clear criteria:
- **粒度可量化**: 2-5 分钟可完成
- **可测试性可判断**: 有无验证命令
- **独立性可检查**: 依赖关系是否最小化

Risk assessment is fact-based:
- 依赖版本是否存在且兼容
- API 是否可用
- 文件所有权是否有冲突

因此使用 **collaborative** model: Planner produces, Risk Assessor reviews and flags. Not full debate.

---

### 为什么需要独立 Risk Assessor

Planner has **optimism bias** when estimating:

```
┌─────────────────────────────────────────────────────────────┐
│              Planner 的三大乐观偏差                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 耦合低估                                                │
│     Planner: "Task A 和 Task B 互不影响"                    │
│     Reality: Task A 的 interface 变更破坏 Task B 的 import  │
│                                                             │
│  2. 集成风险忽略                                            │
│     Planner: "各任务完成后集成即可"                          │
│     Reality: 集成本身需要独立的测试和调试任务                 │
│                                                             │
│  3. 依赖假设                                                │
│     Planner: "使用 @latest 版本即可"                        │
│     Reality: @latest 有 breaking change，需要锁定版本       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Risk Assessor provides independent reality check:
- **依赖验证**: 检查任务依赖是否存在且版本兼容
- **高风险识别**: 标记涉及安全、性能、外部 API 的任务
- **集成缺口**: 检查是否遗漏集成测试任务
- **文件冲突预检**: 验证文件所有权映射无重叠（为 P4 做准备）

---

### 关键设计决策

| 决策 | 选项 A | 选项 B | 选择 | 原因 |
|------|--------|--------|------|------|
| 交互模式 | 对抗辩论 | 协作审查 | **协作** | 任务分解较客观，辩论价值低 |
| Risk Assessor 角色 | 挑战者 | 审查者 | **审查者** | 审查+建议，不需要对抗姿态 |
| 交互轮数 | 多轮 (2-3) | 单轮 | **单轮** (planner -> risk -> planner修改) | 一轮风险审查足够 |
| 任务粒度 | 5-15 分钟 | 2-5 分钟 | **2-5 分钟** | 与 pdforge writing-plans 保持一致 |
| 文件所有权 | 不标注 | 显式标注 | **显式标注** | 为 P4 并行实现做准备 |
| Risk Assessor 模型 | opus | sonnet | **sonnet** | 风险审查不需要深度推理 |

---

### 协作 vs 对抗决策矩阵

```
                高 ┌────────────────────────────────────┐
                   │                                    │
                   │   P1 需求        P2 架构            │
       辩论价值     │   ★ 对抗         ★ 对抗            │
                   │                                    │
                   │                                    │
                   │              P3 规划                │
                低 │              ★ 协作                 │
                   └────────────────────────────────────┘
                   低 ─────── 主观性 ──────── 高
```

---

## 🔧 组件详解

### 1. Planner (general-purpose agent)

**角色定义**:

```yaml
name: planner
type: general-purpose
model: sonnet
tools: Read, Grep, Glob, Bash
```

**职责**:

1. 读取 ADR + 架构文档（阶段 2 产出）
2. 按 pdforge writing-plans 标准分解任务（2-5 分钟粒度）
3. 标注任务间依赖关系（DAG 形式）
4. 标注文件所有权（为 P4 并行实现做准备）
5. 为每个任务指定验证方法

**任务模板**:

```markdown
### Task T003: 创建 UserService

**File**: `src/services/user-service.ts`
**Owner**: implementer-1
**Action**: Create new file
**Estimate**: 4min
**Dependencies**: [T001, T002]
**Risk Level**: LOW

**Code**:
[完整可执行代码]

**Verify**:
```bash
npx jest src/services/user-service.test.ts
```

**File Ownership**:
- OWNS: `src/services/user-service.ts`
- OWNS: `src/services/__tests__/user-service.test.ts`
- READS: `src/models/user.ts` (dependency, not modified)
```

**文件所有权标注规则**:

| 标注 | 含义 | P4 影响 |
|------|------|---------|
| `OWNS` | 该任务独占修改权 | 其他并行任务不可修改此文件 |
| `READS` | 该任务只读依赖 | 不产生冲突 |
| `SHARED` | 多任务需修改 | 必须顺序执行或合并为同一任务 |

---

### 2. Risk Assessor (general-purpose agent)

**角色定义**:

```yaml
name: risk-assessor
type: general-purpose
model: sonnet
tools: Read, Grep, Glob, Bash
```

**职责**:

独立审查 Planner 产出的计划，从 5 个维度进行风险评估。

**5 维度风险评估框架**:

| 维度 | 检查内容 | 典型问题 |
|------|---------|---------|
| **依赖风险** | 外部依赖版本、API 可用性 | `@latest` 有 breaking change |
| **估计风险** | 任务时间估计合理性 | "3min" 任务实际需要 15min |
| **集成风险** | 任务间接口兼容、集成测试 | 缺少集成测试任务 |
| **技术风险** | 复杂算法、并发、性能 | 未考虑 race condition |
| **安全风险** | 认证、授权、数据泄露 | 缺少输入验证任务 |

**风险报告格式**:

```markdown
## Risk Assessment Report

### 总体评估: 🟡 MEDIUM RISK

### 依赖风险
- [HIGH] T003 依赖 `some-lib@^3.0.0`，但 v3 有已知 XSS 漏洞
  建议: 锁定 `some-lib@2.8.5`，新增 T003a 验证兼容性

### 估计风险
- [MEDIUM] T007 估计 3min，但涉及 3 个文件 + 2 个测试文件
  建议: 拆分为 T007a (实现, 3min) + T007b (测试, 3min)

### 集成风险
- [HIGH] T004-T006 之间缺少集成测试任务
  建议: 新增 T006a 集成测试（验证 API → Service → Model 链路）

### 技术风险
- [LOW] 无重大技术风险

### 安全风险
- [MEDIUM] T005 处理用户输入但无验证任务
  建议: 在 T005 验证步骤中增加输入验证测试

### 文件所有权冲突
- [HIGH] T003 和 T005 都标注 OWNS `src/config/index.ts`
  建议: 将 T005 对 config 的修改合并到 T003，或改为 SHARED + 顺序执行
```

---

### 3. Planner 修改回应

Planner 收到风险报告后，必须**逐条回应**:

| 回应类型 | 含义 | 操作 |
|---------|------|------|
| **ACCEPTED** | 采纳建议 | 修改计划 |
| **PARTIALLY ACCEPTED** | 部分采纳 | 修改计划 + 说明理由 |
| **REJECTED** | 不采纳 | 必须给出详细理由 |

**回应格式示例**:

```markdown
## Planner Response to Risk Assessment

### 依赖风险 - T003 some-lib 版本
**Response**: ACCEPTED
**Action**: 锁定 some-lib@2.8.5，新增 T003a 验证兼容性

### 估计风险 - T007 时间估计
**Response**: PARTIALLY ACCEPTED
**Action**: 拆分 T007，但估计调整为 T007a (4min) + T007b (2min)
**Reason**: 实现部分涉及 3 个文件但改动都很小

### 集成风险 - 缺少集成测试
**Response**: ACCEPTED
**Action**: 新增 T006a 集成测试任务

### 文件所有权冲突 - config/index.ts
**Response**: ACCEPTED
**Action**: T005 对 config 的修改合并到 T003，T005 标记为 READS
```

---

## 🚀 使用流程

### 标准流程

```bash
# 单独执行阶段 3
/forge-teams --phase 3

# 从阶段 2 继续（自动获取 ADR + 架构文档）
/forge-teams --phase 2-3
```

### 执行时序

```
┌─────────────────────────────────────────────────────────────┐
│                    阶段 3 执行时序                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  t=0    Lead 启动阶段 3                                     │
│         │                                                   │
│  t=1    Lead 读取阶段 2 产出 (ADR + 架构文档)                │
│         │                                                   │
│  t=2    Lead 创建 Planner agent                             │
│         │                                                   │
│  t=3    Planner 分析文档 + 分解任务 + 标注所有权             │
│         │  ... (主要工作时间)                                │
│  t=N    Planner 完成初版计划                                │
│         │                                                   │
│  t=N+1  Lead 创建 Risk Assessor agent                      │
│         │                                                   │
│  t=N+2  Risk Assessor 独立审查计划                          │
│         │  ... (风险评估时间)                                │
│  t=M    Risk Assessor 完成风险报告                          │
│         │                                                   │
│  t=M+1  Planner 逐条回应建议、修改计划                      │
│         │                                                   │
│  t=M+2  Lead 验证最终计划完整性                              │
│         │                                                   │
│  t=END  阶段 3 完成，产出最终任务计划                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ vs pdforge 对比

| 维度 | pdforge (planner) | forge-teams (P3) | 增量价值 |
|------|-------------------|------------------|---------|
| 规划角色 | 单 planner agent | planner + risk assessor | 减少计划盲点 |
| 风险评估 | 无独立风险审查 | 独立 agent 5 维度审查 | 更健壮的计划 |
| 文件所有权 | 不标注 | 显式标注 (OWNS/READS/SHARED) | 为 P4 并行实现做准备 |
| 估计验证 | 无 | Risk Assessor 独立验证 | 更准确的时间估计 |
| 集成覆盖 | 不检查 | 检查是否遗漏集成测试 | 减少集成风险 |
| Token 开销 | 低（单 agent） | 中（2 agents, 1 轮） | ~1.5x pdforge |

### 什么时候用 pdforge 就够了

| 场景 | 推荐 | 原因 |
|------|------|------|
| 简单功能 (<10 tasks) | pdforge | 风险评估 overhead 不值得 |
| 无并行需求 | pdforge | 不需要文件所有权标注 |
| 独立模块 | pdforge | 集成风险低 |
| 复杂功能 (>15 tasks) | forge-teams P3 | 风险评估价值高 |
| 需要并行实现 | forge-teams P3 | 必须标注文件所有权 |
| 跨模块修改 | forge-teams P3 | 集成风险高 |

---

## ⚠️ 注意事项

### 必须遵守

1. **任务粒度严格 2-5 分钟**: 超过 5 分钟的任务必须拆分，与 pdforge writing-plans 标准一致
2. **文件所有权标注是硬需求**: 这是 P4 并行实现的前提，必须完成，不可跳过
3. **Risk Assessor 建议必须逐条回应**: Planner 必须对每条建议给出 ACCEPTED / PARTIALLY ACCEPTED / REJECTED + 理由
4. **SHARED 文件必须处理**: 标记为 SHARED 的文件要么合并任务，要么标记为顺序执行

### 反模式清单

| 反模式 | 问题 | 正确做法 |
|--------|------|---------|
| 跳过文件所有权标注 | P4 并行实现会产生冲突 | 每个任务必须标注 OWNS/READS |
| Risk Assessor 建议全部 REJECTED | 失去风险审查价值 | 至少解释每条拒绝理由 |
| 任务粒度 >10min | 执行者无法在合理时间内完成 | 拆分为 2-5min 子任务 |
| 缺少集成测试任务 | P4 完成后集成失败 | 为每个模块边界添加集成测试任务 |
| 依赖关系循环 | 任务无法排序 | 重新分解为 DAG |
| 伪代码代替完整代码 | 执行者需要自行判断 | 提供可直接复制的完整代码 |
| 忽略 SHARED 标注 | P4 并行冲突 | 合并任务或标记顺序执行 |

---

## 🔗 下一阶段

计划完成后，进入 **阶段 4：并行实现**：

```bash
# 自动进入下一阶段
/forge-teams --phase 4 --team-size medium

# 或从阶段 3 继续
/forge-teams --phase 3-4
```

阶段 4 将使用本阶段产出的文件所有权映射来分配并行任务。
