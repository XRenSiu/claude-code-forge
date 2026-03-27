# Forge Teams

**Agent Teams 驱动的 7 阶段对抗协作产品开发流水线** - 让多个 AI agent 在每个关键决策点辩论、竞争和交叉验证。

## What is forge-teams?

forge-teams 是基于 Agent Teams 的 7 阶段对抗协作产品开发流水线。它在每个关键决策点使用多 agent 对抗协作，通过辩论、竞争和交叉验证来提升决策质量：

```
forge-teams (多 agent 对抗):
  需求辩论 → 架构竞标 → 风险审查 → 并行实现 → 红队攻防 → 对抗调试 → 交叉验收
    3-4        3         2         2-4        3-5        3-5        2-3  agents
```

## Why?

### 单 agent 开发的根本缺陷

1. **锚定效应**: 第一个想到的方案很可能不是最优的，但 agent 会锚定在上面
2. **确认偏误**: agent 倾向于寻找支持自己结论的证据，忽略反面证据
3. **视角盲点**: 单一视角无法覆盖安全、性能、可用性、可维护性等多个维度
4. **审查失效**: 自己审查自己的代码，很难发现自己的盲点

### forge-teams 的解决方案

每个关键决策点由多个 agent 从不同角度竞争和辩论：

| 决策点 | 单 agent 问题 | forge-teams 解决方案 |
|--------|-------------|-------------------|
| 需求分析 | 遗漏边界情况 | 乐观 vs 悲观 vs 用户代言人 辩论 |
| 系统设计 | 锚定第一方案 | 多方案竞标 + 独立评审 |
| 任务规划 | 低估风险 | 规划 + 对抗式风险审查 |
| 代码实现 | 顺序瓶颈 | 并行实现 + TDD 守卫 |
| 质量审查 | 自己审查自己 | 红队攻击 vs 蓝队防御 |
| 问题修复 | 治标不治本 | 假设竞争 + 对抗式根因分析 |
| 交付验收 | 走过场 | 多 agent 交叉验收 |

---

## 7 Phase Pipeline

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

## Prerequisites

需要启用 Agent Teams 实验性功能：

```json
// settings.json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

---

## Quick Start

### 完整流水线

```bash
# 从需求开始完整对抗协作流程
/forge-teams "用户认证功能，支持 OAuth2 和 JWT"

# 大团队 + 自动修复
/forge-teams "支付系统重构" --team-size large --fix --loop 5
```

### 独立 Bug 修复

```bash
# 描述 bug → 对抗调试定位根因 → TDD 修复 → 独立验证
/forge-fix "支付回调间歇性超时，大约每10次失败2次"

# 简单 bug 走快速路径（跳过对抗调试）
/forge-fix "登录页面 CSS 错位" --quick

# 复杂 bug，加大团队 + 增加循环
/forge-fix "高并发下 Redis 连接池泄漏" --team-size large --loop 5
```

### 独立需求验证

```bash
# 描述需求 → 检查现有代码是否已实现 → 差距报告
/forge-verify "用户可以通过邮箱注册，密码至少8位，注册后发送验证邮件"

# 验证 + 自动补齐缺失实现（TDD 方式）
/forge-verify "支持 OAuth2 登录和 JWT token 刷新" --fix --loop 3

# 严格模式 + 检查测试覆盖
/forge-verify requirements.md --strict --with-tests
```

### 单阶段执行

```bash
# 只执行需求对抗辩论
/forge-teams "暗色模式切换" --phase 1

# 只执行红队审查
/forge-teams --phase 5
```

### 从中间恢复

```bash
# 从阶段 3 开始（需要已有 PRD + ADR）
/forge-teams --skip-to 3

# 从红队审查开始
/forge-teams --skip-to 5
```

---

## Phase-by-Phase Features

### Phase 1: Requirements Debate (需求对抗辩论)

多个分析师从不同角度审视需求，通过辩论达成共识 PRD：
- **Optimist Analyst**: 关注可行性和用户价值
- **Pessimist Analyst**: 关注风险和边界情况
- **User Advocate**: 代表终端用户视角
- 最多 3 轮辩论，Lead 仲裁生成共识 PRD

### Phase 2: Architecture Bakeoff (架构竞标)

多个架构师独立设计方案，通过评审竞标选出最优：
- **Architect A**: 提出方案 A（如倾向简单/性能）
- **Architect B**: 提出方案 B（如倾向扩展/安全）
- **Review Panel**: 按 5 维评分标准独立评审
- Lead 基于评审结果选择或融合方案

### Phase 3: Planning + Risk Review (规划 + 风险对抗审查)

任务规划经过对抗式风险审查：
- **Planner**: 生成任务分解和依赖关系
- **Risk Analyst**: 审查依赖风险、估计风险、集成风险、技术风险
- Planner 回应风险审查，修正计划

### Phase 4: Parallel Implementation (并行实现)

多 agent 并行实现任务，TDD 守卫强制测试纪律：
- **Implementers**: 并行实现无依赖的任务（delegate mode）
- **TDD Guard**: 审查每个提交的 TDD 合规性
- 文件所有权分配防止冲突

### Phase 5: Red Team Review (红队审查)

攻防对抗式代码审查：
- **Red Team**: 从安全、合规、质量、边界、性能 5 个维度攻击
- **Blue Team**: 回应攻击（ACCEPT / DISPUTE / MITIGATE）
- **Arbitrator**: 仲裁有争议的攻击
- 比传统代码审查发现更多隐蔽问题

### Phase 6: Adversarial Debugging (对抗调试)

对 Phase 5 发现的问题进行对抗式根因分析：
- **Hypothesis Investigators**: 并行调查竞争假设
- **Devil's Advocate**: 挑战调查员发现
- **Evidence Synthesizer**: 综合证据，产出根因判定
- TDD 修复：写复现测试 → 实施修复 → 验证通过

### Phase 7: Cross Acceptance (交叉验收)

多 agent 从不同角度交叉验收：
- **Acceptance Reviewer A**: 从需求角度验收
- **Acceptance Reviewer B**: 从技术角度验收
- **Doc Updater**: 更新文档
- 交叉确认确保无遗漏

---

## Token Cost Considerations

forge-teams 使用 Agent Teams 进行多 agent 并行协作，token 消耗较高：

| 团队规模 | 每阶段 Agent 数 | 总 Agent Sessions | 预估消耗 |
|---------|---------------|-------------------|---------|
| Small | 2-3 | 14-21 | 适中 |
| Medium | 3-5 | 21-35 | 较高 |
| Large | 5-7 | 35-49 | 高 |

**降低成本的建议**:
1. 只在关键阶段使用 forge-teams（如 `--phase 5` 只用红队审查）
2. 小功能用 `--team-size small`
3. 只有安全关键功能才用 `--team-size large`
4. 非关键功能可以跳过部分阶段（如 `--skip-to 4` 跳过辩论阶段）

---

## Agents

## Commands

| Command | 描述 | 需要 Agent Teams |
|---------|------|-----------------|
| `/forge-teams` | 7 阶段对抗协作流水线（完整 pipeline 或单阶段） | 是 |
| `/forge-fix` | 独立 bug 修复：对抗调试 → TDD 修复 → 独立验证 → 循环 | 是（快速路径除外） |
| `/forge-verify` | 独立需求验证：结构化 → 代码映射 → 差距报告 → 自动补齐（`--fix`） | 否 |

### 何时使用哪个命令？

| 场景 | 推荐命令 |
|------|---------|
| 新功能完整开发 | `/forge-teams "需求描述"` |
| 已知 bug，需要快速修复 | `/forge-fix "bug 描述"` |
| 简单 bug，根因明显 | `/forge-fix "bug 描述" --quick` |
| 检查需求是否已实现 | `/forge-verify "需求描述"` |
| 验证需求 + 自动补齐缺失 | `/forge-verify "需求描述" --fix` |
| 代码安全审查 | `/forge-teams --skip-to 5` |
| 复杂 bug，多个可能根因 | `/forge-fix "bug 描述" --team-size large` |

---

## Agents

forge-teams 定义了 23 个专用 agent，覆盖全部 7 个阶段：

| Agent | Phase | Model | 职责 |
|-------|-------|-------|------|
| `product-advocate` | P1 | opus | 从用户价值角度撰写 PRD，回应技术怀疑者挑战 |
| `technical-skeptic` | P1 | opus | 挑战 PRD 的技术可行性、隐藏复杂度、安全隐患 |
| `solution-architect` | P2 | opus | 独立分析 PRD 和代码库，产出完整架构方案参与竞标 |
| `technical-critic` | P2 | opus | 用深刻技术洞察力挑战每个架构决策 |
| `design-arbiter` | P2 | opus | 综合评判多个竞争架构方案，产出最终裁决 |
| `task-planner` | P3 | opus | 任务分解 + 依赖图 + 文件所有权注解（OWNS/READS/SHARED） |
| `risk-assessor` | P3 | opus | 5 维风险审查（依赖/估计/集成/技术/安全） |
| `team-implementer` | P4 | opus | 在并行实现阶段执行任务，遵循 TDD 纪律 |
| `quality-sentinel` | P4 | opus | 持续抽查已完成任务的代码质量，发现问题创建修复任务 |
| `red-team-attacker` | P5 | opus | 主动尝试破坏代码，构造真实攻击向量 |
| `code-reviewer` | P5 | opus | 蓝队代码质量审查（命名/结构/错误处理/性能/测试） |
| `security-reviewer` | P5 | opus | 蓝队防御安全审查（OWASP Top 10 + 认证/授权/数据保护） |
| `spec-reviewer` | P5 | opus | 蓝队规格合规审查（PRD 覆盖 + ADR 合规矩阵） |
| `design-reviewer` | P5 | opus | 设计还原审查（Figma MCP + Playwright 像素级对比） |
| `review-synthesizer` | P5 | opus | 统一所有审查发现，去重、排序、交叉验证，产出裁决 |
| `hypothesis-investigator` | P6 | opus | 独立调查特定 bug 假设，收集支持和否定证据 |
| `devils-advocate` | P6 | opus | 专职挑战所有假设的证据质量和逻辑完整性 |
| `evidence-synthesizer` | P6 | opus | 中立仲裁者，维护 Evidence Board，产出根因判定 |
| `issue-fixer` | P6 | opus | TDD 修复：复现测试 → 最小修复 → 回归验证 |
| `acceptance-reviewer` | P7 | opus | 双模式交叉验收（需求视角 A + 技术视角 B） |
| `doc-updater` | P7 | opus | 更新 README、API 文档、CHANGELOG、架构文档 |
| `deployer` | P7 | opus | 部署执行 + 前置检查 + 后置验证 + 回滚方案 |
| `build-error-resolver` | 通用 | opus | 构建/类型/lint 错误最小差异修复 |

> **Model 选择原则**: 所有 agent 统一使用 opus，确保每个阶段都有最强推理能力。详见 [设计哲学](docs/design-philosophy.md)。

---

## Skills

| Skill | 阶段 | 描述 |
|-------|------|------|
| `forge-teams` | 全流程 | `/forge-teams`: 7 阶段产品开发流水线，从需求到部署 |
| `adversarial-requirements` | P1 | 对抗式需求分析，产品倡导者 vs 技术怀疑者 |
| `adversarial-design` | P2 | 对抗式架构设计，多架构师竞标 + 评论家挑战 + 仲裁者裁决 |
| `parallel-implementation` | P4 | 并行实现，多 implementer 执行 + quality sentinel 抽查 |
| `adversarial-review` | P5 | 对抗式审查 + 红队攻击，多 agent 并行交叉检验 |
| `adversarial-debugging` | P6 | 对抗式调试，竞争假设 + 结构化辩论找根因 |
| `forge-fix` | 独立 | `/forge-fix`: 独立 bug 修复循环，快速路径分流 + 三层迭代控制（Fixer→Advisor→Replanner） |
| `forge-verify` | 独立 | `/forge-verify`: 独立需求验证，EARS 结构化 → 代码映射 → 差距报告 → 自动补齐（`--fix`） |

> P3 (规划) 和 P7 (验收) 由 `forge-teams` skill 内联编排，不需要独立 skill。
> `forge-fix` 和 `forge-verify` 是独立入口 skill，不依赖 7 阶段流水线。

---

## Documentation

详细的设计原理和使用指南：

| 文档 | 内容 |
|------|------|
| [设计哲学](docs/design-philosophy.md) | 认知偏差理论、对抗 vs 协作决策、角色分离原则 |
| [P1: 对抗式需求](docs/phase-1-adversarial-requirements.md) | 为什么 advocate vs skeptic？为什么 2 轮？ |
| [P2: 对抗式设计](docs/phase-2-adversarial-design.md) | 为什么竞标？为什么 critic + arbiter 分离？ |
| [P3: 协作规划](docs/phase-3-collaborative-planning.md) | 为什么协作而非对抗？文件所有权注解 |
| [P4: 并行实现](docs/phase-4-parallel-implementation.md) | 为什么并行？文件所有权约束？sentinel 的价值？ |
| [P5: 对抗式审查](docs/phase-5-adversarial-review.md) | 为什么红队主动攻击？攻防对抗模式详解 |
| [P6: 对抗式调试](docs/phase-6-adversarial-debugging.md) | 为什么竞争假设？devil's advocate 的作用？ |
| [P7: 验证部署](docs/phase-7-verified-deployment.md) | 为什么独立验证者？为什么交叉确认？ |

---

## Plugin Structure

```
forge-teams/
├── .claude-plugin/
│   └── plugin.json                    # Plugin manifest
├── agents/
│   ├── product-advocate.md            # P1: 产品倡导者
│   ├── technical-skeptic.md           # P1: 技术怀疑者
│   ├── solution-architect.md          # P2: 方案架构师
│   ├── technical-critic.md            # P2: 技术评论家
│   ├── design-arbiter.md              # P2: 设计仲裁者
│   ├── task-planner.md                # P3: 任务规划师
│   ├── risk-assessor.md               # P3: 风险评估师
│   ├── team-implementer.md            # P4: 团队实现者
│   ├── quality-sentinel.md            # P4: 质量哨兵
│   ├── red-team-attacker.md           # P5: 红队攻击者
│   ├── code-reviewer.md              # P5: 代码质量审查（蓝队）
│   ├── security-reviewer.md          # P5: 安全审查（蓝队）
│   ├── spec-reviewer.md              # P5: 规格合规审查（蓝队）
│   ├── design-reviewer.md            # P5: 设计还原审查
│   ├── review-synthesizer.md          # P5: 审查综合者
│   ├── hypothesis-investigator.md     # P6: 假设调查员
│   ├── devils-advocate.md             # P6: 魔鬼辩护人
│   ├── evidence-synthesizer.md        # P6: 证据综合者
│   ├── issue-fixer.md                 # P6: TDD 问题修复
│   ├── acceptance-reviewer.md         # P7: 交叉验收审查
│   ├── doc-updater.md                 # P7: 文档更新
│   ├── deployer.md                    # P7: 部署执行
│   └── build-error-resolver.md        # 通用: 构建错误修复
├── skills/
│   ├── forge-pipeline/
│   │   └── SKILL.md                   # /forge-teams: 7 阶段流水线主入口
│   ├── adversarial-requirements/
│   │   └── SKILL.md                   # P1: 对抗式需求 skill
│   ├── adversarial-design/
│   │   └── SKILL.md                   # P2: 对抗式设计 skill
│   ├── parallel-implementation/
│   │   └── SKILL.md                   # P4: 并行实现 skill
│   ├── adversarial-review/
│   │   └── SKILL.md                   # P5: 对抗式审查 skill
│   ├── adversarial-debugging/
│   │   └── SKILL.md                   # P6: 对抗式调试 skill
│   ├── fix-bug-loop/
│   │   └── SKILL.md                   # /forge-fix (name: forge-fix): 独立 bug 修复循环
│   └── verify-requirement/
│       └── SKILL.md                   # /forge-verify (name: forge-verify): 独立需求验证
├── rules/
│   ├── team-coordination.md           # Team lifecycle and communication rules
│   └── adversarial-protocol.md        # Adversarial debate rules (10 rules)
├── docs/
│   ├── design-philosophy.md           # 总体设计哲学
│   ├── phase-1-adversarial-requirements.md
│   ├── phase-2-adversarial-design.md
│   ├── phase-3-collaborative-planning.md
│   ├── phase-4-parallel-implementation.md
│   ├── phase-5-adversarial-review.md
│   ├── phase-6-adversarial-debugging.md
│   ├── phase-7-verified-deployment.md
├── README.md                          # This file
└── LICENSE                            # MIT License
```

---

## Author

**XRenSiu** (xrensiu@gmail.com)

---

## License

MIT
