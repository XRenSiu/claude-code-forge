# Forge Teams

**Agent Teams 驱动的 7 阶段对抗协作产品开发流水线** - 让多个 AI agent 在每个关键决策点辩论、竞争和交叉验证。

## What is forge-teams?

forge-teams 是 pdforge 的 Agent Teams 升级版。它将 pdforge 的 7 阶段产品开发流水线中的每个关键决策点，从单 agent 线性推理升级为多 agent 对抗协作：

```
pdforge (单 agent 顺序):
  需求 → 设计 → 规划 → 实现 → 审查 → 修复 → 交付
    1       1      1      1      1      1      1    agent

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

## vs. pdforge Comparison

| 维度 | pdforge | forge-teams |
|------|---------|-------------|
| Agent 模式 | 单 agent 顺序执行 | 多 agent 并行对抗 |
| 需求分析 | 线性分析 + PRD 生成 | 多视角对抗辩论 → 共识 PRD |
| 系统设计 | 单架构师设计 | 多方案竞标 + 独立评审 |
| 任务规划 | 单规划师分解 | 规划 + 对抗式风险审查 |
| 代码实现 | 逐任务顺序实现 | 并行实现 + TDD 守卫执法 |
| 质量审查 | 顺序多审查员 | 红队攻击 vs 蓝队防御 |
| 修复验证 | 线性修复 | 对抗式假设竞争调试 |
| 交付部署 | 单 agent 交付 | 多 agent 交叉验收 |
| 偏见防御 | 依赖流程纪律 | 结构化对抗消除 |
| Token 消耗 | 中等 | 高 (5-20x) |
| 速度 | 中等 | 快 (并行) 但总量更大 |
| 准确率/质量 | 高 | 更高 (多视角) |
| 适合场景 | 标准开发 | 高质量/安全关键开发 |

### 何时选择哪个

| 场景 | 推荐 |
|------|------|
| 快速原型 / MVP | pdforge (`--mode 0to1`) |
| 标准功能迭代 | pdforge (`--fix --loop`) |
| 核心功能首次开发 | forge-teams (`--team-size medium`) |
| 安全关键功能 | forge-teams (`--team-size large`) |
| 性能关键功能 | forge-teams (`--team-size medium`) |
| 简单 bug 修复 | pdforge 的 `/fix` |
| 复杂 bug 调试 | `adversarial-debugging` 或 forge-teams P6 |

---

## Token Cost Considerations

forge-teams 使用 Agent Teams 进行多 agent 并行协作，token 消耗显著高于 pdforge：

| 团队规模 | 每阶段 Agent 数 | 总 Agent Sessions | 相对 pdforge |
|---------|---------------|-------------------|-------------|
| Small | 2-3 | 14-21 | 3-5x |
| Medium | 3-5 | 21-35 | 5-10x |
| Large | 5-7 | 35-49 | 10-20x |

**降低成本的建议**:
1. 先用 pdforge 验证流程可行性
2. 只在关键阶段使用 forge-teams（如 `--phase 5` 只用红队审查）
3. 小功能用 `--team-size small`
4. 只有安全关键功能才用 `--team-size large`

---

## Agents

forge-teams 定义了 12 个专用 agent，分布在 5 个阶段：

| Agent | Phase | Model | 职责 |
|-------|-------|-------|------|
| `product-advocate` | P1 | sonnet | 从用户价值角度撰写 PRD，回应技术怀疑者挑战 |
| `technical-skeptic` | P1 | sonnet | 挑战 PRD 的技术可行性、隐藏复杂度、安全隐患 |
| `solution-architect` | P2 | sonnet | 独立分析 PRD 和代码库，产出完整架构方案参与竞标 |
| `technical-critic` | P2 | opus | 用深刻技术洞察力挑战每个架构决策 |
| `design-arbiter` | P2 | opus | 综合评判多个竞争架构方案，产出最终裁决 |
| `team-implementer` | P4 | sonnet | 在并行实现阶段执行任务，遵循 TDD 纪律 |
| `quality-sentinel` | P4 | sonnet | 持续抽查已完成任务的代码质量，发现问题创建修复任务 |
| `red-team-attacker` | P5 | opus | 主动尝试破坏代码，构造真实攻击向量 |
| `review-synthesizer` | P5 | opus | 统一所有审查发现，去重、排序、交叉验证 |
| `hypothesis-investigator` | P6 | sonnet | 独立调查特定 bug 假设，收集支持和否定证据 |
| `devils-advocate` | P6 | opus | 专职挑战所有假设的证据质量和逻辑完整性 |
| `evidence-synthesizer` | P6 | opus | 中立仲裁者，维护 Evidence Board，产出根因判定 |

> **Model 选择原则**: 创作者/调查者用 sonnet（高吞吐），挑战者/仲裁者用 opus（深度推理）。详见 [设计哲学](docs/design-philosophy.md)。

---

## Skills

| Skill | 阶段 | 描述 |
|-------|------|------|
| `forge-pipeline` | 全流程 | 7 阶段产品开发流水线，从需求到部署 |
| `adversarial-requirements` | P1 | 对抗式需求分析，产品倡导者 vs 技术怀疑者 |
| `adversarial-design` | P2 | 对抗式架构设计，多架构师竞标 + 评论家挑战 + 仲裁者裁决 |
| `parallel-implementation` | P4 | 并行实现，多 implementer 执行 + quality sentinel 抽查 |
| `adversarial-review` | P5 | 对抗式审查 + 红队攻击，多 agent 并行交叉检验 |
| `adversarial-debugging` | P6 | 对抗式调试，竞争假设 + 结构化辩论找根因 |

> P3 (规划) 和 P7 (验收) 由 `forge-pipeline` skill 内联编排，不需要独立 skill。

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
| [P5: 对抗式审查](docs/phase-5-adversarial-review.md) | 为什么红队主动攻击？vs pdforge 顺序审查？ |
| [P6: 对抗式调试](docs/phase-6-adversarial-debugging.md) | 为什么竞争假设？devil's advocate 的作用？ |
| [P7: 验证部署](docs/phase-7-verified-deployment.md) | 为什么独立验证者？为什么交叉确认？ |
| [pdforge vs forge-teams](docs/pdforge-vs-forge-teams.md) | 逐阶段差异分析、选型决策树、渐进采用路径 |

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
│   ├── team-implementer.md            # P4: 团队实现者
│   ├── quality-sentinel.md            # P4: 质量哨兵
│   ├── red-team-attacker.md           # P5: 红队攻击者
│   ├── review-synthesizer.md          # P5: 审查综合者
│   ├── hypothesis-investigator.md     # P6: 假设调查员
│   ├── devils-advocate.md             # P6: 魔鬼辩护人
│   └── evidence-synthesizer.md        # P6: 证据综合者
├── commands/
│   └── forge-teams.md                 # Main command definition
├── skills/
│   ├── forge-pipeline/
│   │   └── SKILL.md                   # 全流程编排 skill
│   ├── adversarial-requirements/
│   │   └── SKILL.md                   # P1: 对抗式需求 skill
│   ├── adversarial-design/
│   │   └── SKILL.md                   # P2: 对抗式设计 skill
│   ├── parallel-implementation/
│   │   └── SKILL.md                   # P4: 并行实现 skill
│   ├── adversarial-review/
│   │   └── SKILL.md                   # P5: 对抗式审查 skill
│   └── adversarial-debugging/
│       └── SKILL.md                   # P6: 对抗式调试 skill
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
│   └── pdforge-vs-forge-teams.md      # 对比指南
├── README.md                          # This file
└── LICENSE                            # MIT License
```

---

## Author

**XRenSiu** (xrensiu@gmail.com)

---

## License

MIT
