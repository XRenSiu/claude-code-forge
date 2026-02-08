---
name: forge-pipeline
description: >
  Agent Teams 7 阶段产品开发流水线。从需求到部署，每个关键决策点使用对抗辩论。
  Use when: (1) 新项目完整开发, (2) 复杂功能需要高质量保证, (3) 需要团队级并行开发。
  Triggers: "forge teams", "team pipeline", "adversarial development"
when_to_use: |
  - 新项目从零开发
  - 复杂功能需要高质量保证
  - 需要并行开发加速
  - 需要红队级安全审查
version: 1.0.0
---

# Forge Pipeline - Agent Teams 7 阶段对抗协作流水线

**将 pdforge 的单 agent 顺序流水线升级为多 agent 对抗协作流水线。**

每个关键决策点不再由一个 agent 拍脑袋决定，而是由多个 agent 辩论、竞争、交叉验证后达成共识。

Announce at start: "I'm using the forge-pipeline skill to orchestrate a 7-phase adversarial development pipeline with Agent Teams."

> **前置条件**: 需要启用 Agent Teams 实验性功能。
> 在 settings.json 中添加: `"env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" }`

---

## vs. pdforge 对比

| 维度 | pdforge | forge-teams |
|------|---------|-------------|
| Agent 模式 | 单 agent 顺序执行 | 多 agent 并行对抗 |
| 需求分析 | 线性分析 + PRD | 对抗辩论 → 共识 PRD |
| 系统设计 | 单架构师 | 多方案竞标 + 评审 |
| 任务规划 | 单规划师 | 规划 + 风险对抗审查 |
| 代码实现 | 逐任务顺序实现 | 并行实现 + TDD 守卫 |
| 质量审查 | 顺序多审查员 | 红队 vs 蓝队对抗 |
| 修复验证 | 线性修复 | 对抗式假设竞争调试 |
| 交付部署 | 单 agent 交付 | 交叉验收 + 交付 |
| 偏见防御 | 流程纪律 | 结构化对抗 |
| Token 消耗 | 中等 | 高（5-20x） |
| 适合场景 | 标准开发 | 高质量/安全关键开发 |

---

## 7 阶段总览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FORGE-TEAMS 对抗协作流水线                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  P1: REQUIREMENTS DEBATE    需求对抗辩论 ──────────────────▶ PRD        │
│         │                                                              │
│         ▼                                                              │
│  P2: ARCHITECTURE BAKEOFF   架构竞标 ─────────────────────▶ ADR        │
│         │                                                              │
│         ▼                                                              │
│  P3: PLANNING + RISK        规划 + 风险对抗 ──────────────▶ Plan       │
│         │                                                              │
│         ▼                                                              │
│  P4: PARALLEL IMPL          并行实现 + TDD 守卫 ──────────▶ Code       │
│         │                                                              │
│         ▼                                                              │
│  P5: RED TEAM REVIEW        红队 vs 蓝队 ────────────────▶ Report      │
│         │                                                              │
│         ├──[有问题]──▶ P6                                              │
│         └──[通过]────▶ P7                                              │
│                                                                         │
│  P6: ADVERSARIAL DEBUG      对抗调试 + TDD 修复 ─────────▶ Fixes       │
│         │                                                              │
│         └──────────▶ P5 (重新审查)                                     │
│                                                                         │
│  P7: CROSS ACCEPTANCE       交叉验收 + 交付 ─────────────▶ Deploy      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Requirements Debate (需求对抗辩论)

**目的**: 通过多视角对抗辩论，生成高质量共识 PRD，避免单一视角盲点。

**团队组成**:

| 角色 | 职责 | 数量 |
|------|------|------|
| Optimist Analyst | 关注可行性、用户价值、快速交付 | 1 |
| Pessimist Analyst | 关注风险、边界情况、技术债务 | 1 |
| User Advocate | 代表终端用户，关注体验和可用性 | 1 |
| Arbitrator (Lead) | 协调辩论，综合生成共识 PRD | Lead 自己 |

**执行流程**:
1. Lead 解析需求输入，准备辩论上下文
2. TeamCreate: `"req-debate-[feature]"`
3. Spawn 3 个分析师，各自独立分析需求
4. 每个分析师提交分析报告 (via SendMessage)
5. Lead 启动辩论：乐观 vs 悲观，用户代言人仲裁
6. 最多 3 轮辩论，达成共识
7. Lead 综合产出 PRD
8. Shutdown team + TeamDelete

**产出**: `docs/forge-teams/[feature]/phase-1-requirements/prd.md`

**进入下一阶段条件**: PRD 通过质量检查（13 项），所有分析师无 blocker 级异议。

---

## Phase 2: Architecture Bakeoff (架构竞标)

**目的**: 通过多方案竞标和独立评审，选出最优架构方案。

**团队组成**:

| 角色 | 职责 | 数量 |
|------|------|------|
| Architect A | 提出架构方案 A（倾向性能/简单） | 1 |
| Architect B | 提出架构方案 B（倾向扩展/安全） | 1 |
| Review Panel | 独立评审两个方案，给出评分 | 1 |

**执行流程**:
1. TeamCreate: `"arch-bakeoff-[feature]"`
2. 将 PRD 分发给两个架构师
3. 两个架构师独立设计方案 + ADR
4. Review Panel 按评分标准评审：
   - 可行性 (25%)
   - 可维护性 (25%)
   - 性能 (20%)
   - 安全性 (15%)
   - 技术债风险 (15%)
5. Lead 基于评审结果选择或融合方案
6. Shutdown team + TeamDelete

**产出**: `docs/forge-teams/[feature]/phase-2-architecture/adr.md`

**进入下一阶段条件**: ADR 包含所有架构决策，Review Panel 评分 >= 7/10。

---

## Phase 3: Planning + Risk Review (规划 + 风险对抗审查)

**目的**: 生成任务计划并通过对抗式风险审查验证计划可行性。

**团队组成**:

| 角色 | 职责 | 数量 |
|------|------|------|
| Planner | 基于 ADR 生成任务分解 | 1 |
| Risk Analyst | 审查计划中的风险点 | 1 |

**执行流程**:
1. TeamCreate: `"planning-[feature]"`
2. Planner 生成任务分解（依赖关系 + 复杂度估计）
3. Risk Analyst 审查每个任务：
   - 依赖风险：是否有循环依赖？
   - 估计风险：复杂度是否低估？
   - 集成风险：接口是否清晰？
   - 技术风险：是否依赖未验证技术？
4. Planner 回应风险审查，修正计划
5. Lead 确认最终计划
6. Shutdown team + TeamDelete

**产出**: `docs/forge-teams/[feature]/phase-3-planning/plan.json`

**进入下一阶段条件**: 所有高风险项已有缓解方案，无循环依赖。

---

## Phase 4: Parallel Implementation (并行实现)

**目的**: 多 agent 并行实现任务，TDD 守卫强制执行测试纪律。

**团队组成**:

| 角色 | 职责 | 数量 |
|------|------|------|
| Implementer | 按计划实现任务（delegate mode） | 1-3 |
| TDD Guard | 审查每个任务的 TDD 合规性 | 1 |

**执行流程**:
1. TeamCreate: `"impl-[feature]"`
2. 按依赖关系将任务分配给 Implementer（无依赖的任务可并行）
3. 每个 Implementer 使用 delegate mode 实现任务：
   - Red: 先写失败测试
   - Green: 写最少代码通过测试
   - Refactor: 重构保持测试通过
4. TDD Guard 审查每个提交：
   - 测试覆盖率是否达标？
   - 是否先写测试后写代码？
   - 是否有未测试的核心路径？
5. 任务完成后 Lead 验证集成
6. Shutdown team + TeamDelete

**文件冲突防御**: 每个 Implementer 只编辑分配给自己的文件。Lead 通过任务分配确保无重叠。如有共享文件，使用顺序写入。

**产出**: 生产级代码 + 测试

**进入下一阶段条件**: 所有任务完成，TDD Guard 无 blocker，测试通过。

---

## Phase 5: Red Team Review (红队审查)

**目的**: 通过攻防对抗发现代码中的安全漏洞、逻辑缺陷和规格偏差。

**团队组成**:

| 角色 | 职责 | 数量 |
|------|------|------|
| Red Team Attacker | 主动寻找漏洞和缺陷 | 1-2 |
| Blue Team Defender | 回应攻击，评估风险，提出修复 | 1 |
| Arbitrator | 仲裁攻防双方的分歧 | 1 |

**Red Team 攻击维度**:
- **安全**: SQL 注入、XSS、CSRF、认证绕过、权限提升
- **规格合规**: 是否满足 PRD 中的所有需求？
- **代码质量**: 命名、结构、可维护性
- **边界情况**: 空值、极端输入、并发场景
- **性能**: N+1 查询、内存泄漏、阻塞操作

**执行流程**:
1. TeamCreate: `"red-team-[feature]"`
2. Red Team 独立攻击（每个攻击者分配不同维度）
3. Red Team 提交攻击报告 (via SendMessage)
4. Blue Team 回应每个攻击：
   - ACCEPT: 承认问题，提出修复方案
   - DISPUTE: 提供证据反驳攻击
   - MITIGATE: 承认问题但说明风险可控
5. Arbitrator 仲裁有争议的攻击
6. Lead 汇总最终审查报告
7. Shutdown team + TeamDelete

**产出**: `docs/forge-teams/[feature]/phase-5-red-team/`

**进入下一阶段条件**:
- 无 blocker 问题: 直接进入 Phase 7
- 有 blocker 问题: 进入 Phase 6 修复

---

## Phase 6: Adversarial Debugging (对抗调试)

**目的**: 对 Phase 5 发现的问题进行对抗式根因分析和 TDD 修复。

**团队组成**:

| 角色 | 职责 | 数量 |
|------|------|------|
| Hypothesis Investigator | 调查每个假设 | 1-3 |
| Devil's Advocate | 挑战调查员的发现 | 1 |
| Evidence Synthesizer | 综合证据，产出判定 | 1 |

**执行流程**:
1. 对每个 blocker 问题，运行 adversarial-debugging 协议
2. TeamCreate: `"debug-[feature]-[issue]"`
3. 生成 3-5 个竞争假设
4. Spawn 调查员并行调查
5. 2-3 轮对抗辩论
6. Evidence Synthesizer 产出根因判定
7. TDD 修复：写复现测试 → 实现修复 → 验证通过
8. Shutdown team + TeamDelete

**修复后回退**: 修复完成后，回到 Phase 5 重新进行红队审查（仅针对修改部分），最多循环 3 次。

**产出**: `docs/forge-teams/[feature]/phase-6-debugging/`

**进入下一阶段条件**: Phase 5 重新审查通过，无 blocker 问题。

---

## Phase 7: Cross Acceptance + Delivery (交叉验收 + 交付)

**目的**: 多 agent 交叉验收确保代码就绪，然后完成交付。

**团队组成**:

| 角色 | 职责 | 数量 |
|------|------|------|
| Acceptance Reviewer A | 从需求角度验收 | 1 |
| Acceptance Reviewer B | 从技术角度验收 | 1 |
| Doc Updater | 更新文档 | 1 |

**执行流程**:
1. TeamCreate: `"delivery-[feature]"`
2. Reviewer A 检查 PRD 合规性（所有需求是否实现）
3. Reviewer B 检查技术质量（架构决策是否执行）
4. 两个 Reviewer 交叉确认
5. Doc Updater 更新 README、API 文档、CHANGELOG
6. Lead 生成最终流水线摘要报告
7. Shutdown team + TeamDelete

**产出**: `docs/forge-teams/[feature]/summary.md`

---

## Phase Transition Rules (阶段转换规则)

### 正向推进条件

| 从 | 到 | 条件 |
|----|----|------|
| P1 | P2 | PRD 质量检查通过，无 blocker 异议 |
| P2 | P3 | ADR 评审 >= 7/10，方案已选定 |
| P3 | P4 | 计划无循环依赖，高风险项有缓解方案 |
| P4 | P5 | 所有任务完成，TDD 合规，测试通过 |
| P5 | P6 | 有 blocker 问题需要修复 |
| P5 | P7 | 无 blocker 问题 |
| P6 | P5 | 修复完成，需要重新审查 |
| P7 | 完成 | 交叉验收通过 |

### 回退条件

| 条件 | 动作 |
|------|------|
| P2 评审 < 5/10 | 回退 P1 重新分析需求 |
| P4 集成失败 | 回退 P3 修正计划 |
| P5-P6 循环 > 3 次 | 断路器触发，人工干预 |
| 任何阶段 team 创建失败 | 报错退出 |

---

## Team Lifecycle Management (团队生命周期)

每个阶段**必须**遵循以下生命周期：

```
CREATE ──▶ COORDINATE ──▶ SHUTDOWN ──▶ CLEANUP
  │            │              │            │
  │  TeamCreate│  SendMessage │ shutdown_   │ TeamDelete
  │  TaskCreate│  TaskUpdate  │ request     │
  │  Spawn     │  Monitor     │ Wait ack    │
  └────────────┴──────────────┴────────────┘
```

### 关键约束

1. **每个阶段创建独立团队** - 不同阶段的团队互相隔离
2. **当前阶段团队必须在下一阶段开始前清理完毕**
3. **Lead 不参与具体调查** - 使用 delegate mode 协调
4. **每个对抗辩论最多 3 轮**
5. **Implementer 使用 delegate mode 以获得完整工具权限**

---

## Global Constraints (全局约束)

### 必须遵守

| # | 约束 | 原因 |
|---|------|------|
| 1 | 每阶段独立 team | 防止上下文污染 |
| 2 | Team 用完即清理 | 防止资源泄漏 |
| 3 | 对抗辩论 <= 3 轮 | 收益递减，防止死循环 |
| 4 | Implementer 用 delegate mode | 需要完整文件操作权限 |
| 5 | 文件写入互斥 | 两个 agent 不得同时编辑同一文件 |
| 6 | 证据优先 | 所有论点必须有具体证据 |
| 7 | 遵循 adversarial-protocol 规则 | 所有对抗阶段统一规则 |
| 8 | 遵循 team-coordination 规则 | 所有团队通信统一规范 |

### 禁止行为

| # | 行为 | 后果 |
|---|------|------|
| 1 | 跨阶段共享 team | 阶段隔离失效 |
| 2 | Lead 自己写代码 | 协调员角色混淆 |
| 3 | 跳过辩论直接判定 | 失去对抗核心价值 |
| 4 | 隐藏不利证据 | 结论不可信 |
| 5 | 辩论超过 3 轮 | 浪费 token |
| 6 | 不清理 team 就开下一阶段 | 资源泄漏 |

---

## Output Format (最终报告格式)

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  FORGE-TEAMS Pipeline Complete                                           ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  Feature: [feature-name]                                                  ║
║  Duration: [total-time]                                                   ║
║  Team Size: [small/medium/large]                                          ║
║  Status: [PASS / PASS WITH WARNINGS / BLOCKED]                            ║
║                                                                           ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │ Phase Results                                                       │  ║
║  ├─────────────────────────────────────────────────────────────────────┤  ║
║  │ P1 Requirements Debate:  [status] [debate rounds] [consensus]       │  ║
║  │ P2 Architecture Bakeoff: [status] [winning proposal] [score]        │  ║
║  │ P3 Planning + Risk:      [status] [tasks] [risk items mitigated]    │  ║
║  │ P4 Parallel Impl:        [status] [files] [test coverage]           │  ║
║  │ P5 Red Team Review:      [status] [attacks] [defended] [fixed]      │  ║
║  │ P6 Adversarial Debug:    [status] [hypotheses] [root causes]        │  ║
║  │ P7 Cross Acceptance:     [status] [reviewers agree]                 │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║                                                                           ║
║  Artifacts:                                                               ║
║    PRD:      docs/forge-teams/[feature]/phase-1-requirements/prd.md       ║
║    ADR:      docs/forge-teams/[feature]/phase-2-architecture/adr.md       ║
║    Plan:     docs/forge-teams/[feature]/phase-3-planning/plan.json        ║
║    Red Team: docs/forge-teams/[feature]/phase-5-red-team/                 ║
║    Summary:  docs/forge-teams/[feature]/summary.md                        ║
║                                                                           ║
║  Next Steps:                                                              ║
║    1. Review summary: docs/forge-teams/[feature]/summary.md               ║
║    2. Commit: git add -A && git commit -m "feat: ..."                     ║
║    3. Create PR or merge to main                                          ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## Anti-patterns

| 坏行为 | 为什么失败 | 正确做法 |
|--------|-----------|---------|
| 用 forge-teams 做简单任务 | Token 浪费 10x+ | 简单任务用 pdforge |
| 跳过 P1 对抗辩论 | PRD 有盲点 | 至少 2 轮辩论 |
| P2 只提出 1 个方案 | 失去竞标优势 | 至少 2 个独立方案 |
| P4 不用 delegate mode | Implementer 权限不足 | 必须 delegate |
| P5 Red/Blue 同一视角 | 失去对抗意义 | Red 必须主动攻击 |
| P6 跳过根因直接修 | 治标不治本 | 必须定位根因 |
| 不清理 team | 资源泄漏 | 每阶段结束必须 cleanup |
| 辩论超 3 轮 | 收益递减 | 3 轮后强制判定 |

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      FORGE-TEAMS QUICK REFERENCE                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  P1: REQUIREMENTS DEBATE                                                │
│      Team: optimist + pessimist + user-advocate                         │
│      Output: Consensus PRD                                              │
│                                                                         │
│  P2: ARCHITECTURE BAKEOFF                                               │
│      Team: architect-a + architect-b + review-panel                     │
│      Output: Winning ADR                                                │
│                                                                         │
│  P3: PLANNING + RISK                                                    │
│      Team: planner + risk-analyst                                       │
│      Output: Risk-reviewed Plan                                         │
│                                                                         │
│  P4: PARALLEL IMPLEMENTATION                                            │
│      Team: implementer(s) + tdd-guard                                   │
│      Output: Production Code + Tests                                    │
│                                                                         │
│  P5: RED TEAM REVIEW                                                    │
│      Team: red-team + blue-team + arbitrator                            │
│      Output: Attack/Defense Report                                      │
│                                                                         │
│  P6: ADVERSARIAL DEBUG                                                  │
│      Team: investigators + devil's-advocate + synthesizer               │
│      Output: Root Cause + TDD Fix                                       │
│                                                                         │
│  P7: CROSS ACCEPTANCE                                                   │
│      Team: reviewer-a + reviewer-b + doc-updater                        │
│      Output: Final Report + Docs                                        │
│                                                                         │
│  KEY RULES:                                                             │
│    - Each phase: CREATE -> COORDINATE -> SHUTDOWN -> CLEANUP             │
│    - Max 3 debate rounds per adversarial phase                           │
│    - Implementers use delegate mode                                      │
│    - No two agents edit the same file                                    │
│    - Evidence-first for all arguments                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Core Principle

> **"A decision made by consensus after adversarial debate is more robust than any individual decision."**
>
> 经过对抗辩论达成的共识决策，比任何个体决策都更健壮。
