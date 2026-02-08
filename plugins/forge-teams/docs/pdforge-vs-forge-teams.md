# pdforge vs forge-teams 详细对比指南

> 两个插件不是竞争关系，而是互补——pdforge 是快速开发工具，forge-teams 是质量保障工具

---

## 📋 核心差异

### 一句话总结

| 插件 | 定位 |
|------|------|
| **pdforge** | 单 Agent 高效流水线——用流程纪律保障质量 |
| **forge-teams** | 多 Agent 对抗协作流水线——用结构化对抗消除认知偏差 |

### Agent 模式差异

```
pdforge (Subagent 模式):
┌──────────┐
│ Main Agent│
└────┬─────┘
     │ 调用
     ▼
┌──────────┐
│ Subagent │ → 返回结果 → Main Agent
└──────────┘
     ↑
     │ 无法通信
     ↓
┌──────────┐
│ Subagent │ → 返回结果 → Main Agent
└──────────┘

特点：
• 单向通信（Main → Sub → Main）
• 顺序执行（一个完成再调下一个）
• Subagent 之间完全隔离
• 适合独立任务（审查、生成、修复）


forge-teams (Agent Teams 模式):
┌──────────┐
│   Lead   │
└──┬───┬───┘
   │   │ SendMessage (双向)
   ▼   ▼
┌──────┐   ┌──────┐
│Agent │◄─►│Agent │
│  A   │   │  B   │
└──┬───┘   └───┬──┘
   │           │ SendMessage (双向)
   ▼           ▼
┌──────┐   ┌──────┐
│Agent │◄─►│Agent │
│  C   │   │  D   │
└──────┘   └──────┘

特点：
• 多向通信（Agent ↔ Agent via SendMessage）
• 可并行执行（多 Agent 同时工作）
• Agent 之间可通信、可协作、可竞争
• 适合对抗/协作任务（辩论、竞标、交叉验证）
```

---

## 🧩 逐阶段详细对比

### 总览表

| 阶段 | pdforge 角色 | forge-teams 角色 | 核心改变 |
|------|-------------|-----------------|---------|
| **P1 需求** | prd-generator (1 agent) | advocate + skeptic (2 agents) | 从生成到辩论 |
| **P2 设计** | architect (1 agent) | architect x2 + critic + arbiter (4 agents) | 从独白到竞标 |
| **P3 规划** | planner (1 agent) | planner + risk-assessor (2 agents) | 增加风险审查 |
| **P4 实现** | implementer (N, 顺序) | implementer (N, 并行) + sentinel | 从顺序到并行 |
| **P5 审查** | reviewer x4 (顺序) | reviewer x4 + red-team + synthesizer (并行) | 从被动到主动攻击 |
| **P6 修复** | systematic-debugging (1 agent) | investigator x3 + devil's advocate + synthesizer | 从线性到竞争 |
| **P7 部署** | deployer (1 agent) | deployer + verifier (2 agents) | 增加独立验证 |

---

### P1 需求分析

```
pdforge:
┌────────────────┐        ┌──────────┐
│ prd-generator  │ ──────▶│   PRD    │
│ (单 agent 分析) │        └──────────┘
└────────────────┘
  阅读需求 → 分析 → 生成 PRD（线性流程）

forge-teams:
┌─────────────────┐     ┌───────────────────┐
│ product-advocate│◄───►│technical-skeptic   │
│ (倡导者/opus)    │     │(怀疑者/sonnet)     │
└────────┬────────┘     └────────┬──────────┘
         │ 辩论 (2 轮)            │
         └────────────┬───────────┘
                      ▼
               ┌──────────┐
               │共识 PRD   │
               └──────────┘
```

| 维度 | pdforge | forge-teams |
|------|---------|-------------|
| 需求分析 | 单 agent 线性分析 | Advocate 提案 + Skeptic 挑战 |
| 可行性检查 | 隐含在分析中 | Skeptic 用代码库证据反驳不可行的需求 |
| 范围膨胀风险 | 高（Agent 倾向于乐观） | 低（Skeptic 制衡范围膨胀） |
| 输出 | PRD | 经过辩论的共识 PRD |

---

### P2 系统设计

```
pdforge:
┌────────────────┐        ┌──────────┐
│   architect    │ ──────▶│   ADR    │
│ (单架构师)      │        └──────────┘
└────────────────┘
  分析 PRD → 设计架构 → 产出 ADR

forge-teams:
┌──────────────┐  ┌──────────────┐
│ architect-A  │  │ architect-B  │  独立设计（互不知道对方方案）
│ (方案 A)     │  │ (方案 B)     │
└──────┬───────┘  └──────┬───────┘
       │                 │
       └────────┬────────┘
                ▼
       ┌────────────────┐
       │ technical-critic│  审查两个方案
       │ (评审者/opus)    │
       └────────┬───────┘
                ▼
       ┌────────────────┐
       │ design-arbiter │  裁决选择
       │ (仲裁者/opus)   │
       └────────┬───────┘
                ▼
         ┌──────────┐
         │ 最优 ADR  │
         └──────────┘
```

| 维度 | pdforge | forge-teams |
|------|---------|-------------|
| 方案数量 | 1 个（可能提及替代方案但未深入） | 2+ 个（每个都经过深入设计） |
| 锚定风险 | 高（第一方案成为锚点） | 低（独立设计避免锚定） |
| 评审 | 无独立评审 | Critic 深入评审 + Arbiter 裁决 |
| 辩论轮数 | 0 | 3（最多） |

---

### P3 任务规划

| 维度 | pdforge | forge-teams |
|------|---------|-------------|
| 规划方式 | 单 planner 分解任务 | Planner 规划 + Risk Assessor 审查 |
| 风险评估 | 隐含 | 专职 risk-assessor 评估依赖风险、并行风险 |
| 并行性分析 | 无 | 为 P4 并行实现做准备 |
| 模式 | 线性生成 | 协作 + 审查 |

---

### P4 代码实现

```
pdforge:
Task 1 → Task 2 → Task 3 → Task 4 (顺序执行)
  ↓        ↓        ↓        ↓
 Done    Done     Done     Done

forge-teams:
Task 1 ─────→ Done ─→ Task 3 ──→ Done
Task 2 ─────→ Done ─→ Task 4 ──→ Done
       (并行)              (并行)
  ↑                    ↑
  └── Sentinel 监控 ───┘
```

| 维度 | pdforge | forge-teams |
|------|---------|-------------|
| 执行模式 | 顺序（一个完成再下一个） | 并行（多 agent 同时工作） |
| 任务分配 | Main agent 手动分配 | Agent 自主 claim + Lead 协调 |
| 代码质量守卫 | 无实时监控 | Quality Sentinel 实时巡检 |
| 集成风险 | 低（顺序执行天然集成） | 中（需要集成阶段，但 Sentinel 降低风险） |
| 速度 | 慢（线性） | 快（可并行的任务同时执行） |

---

### P5 质量审查

| 维度 | pdforge | forge-teams |
|------|---------|-------------|
| 审查方式 | 顺序（规格 → 代码 → 安全） | 并行（4 角色同时 + 红队） |
| 红队攻击 | 无 | 专职 Red Team Attacker 主动攻击 |
| 交叉验证 | 无 | 审查员之间可交叉验证发现 |
| 综合裁决 | 各审查员独立判定 | Review Synthesizer 综合裁决 |
| 缺陷检出率 | ~25-40% | ~70%+ |

---

### P6 修复/调试

| 维度 | pdforge | forge-teams |
|------|---------|-------------|
| 架构 | 4+1 阶段线性调试 | 5-Phase 对抗调试 |
| 假设 | 逐一验证 | 并行竞争调查 |
| 挑战 | 无（自我评估） | Devil's Advocate 专职挑战 |
| 判定 | Agent 自己判定 | Evidence Synthesizer 评分裁决 |
| 首次正确率 | ~40% | ~80%+ |

---

### P7 部署

| 维度 | pdforge | forge-teams |
|------|---------|-------------|
| 验证 | Deployer 自验证 | 独立 Verifier 验证 |
| 确认 | 单方确认 | 交叉确认（双方独立） |
| 回滚 | 手动 | 自动（任一方失败即回滚） |
| PRD 对照 | 无 | Verifier 逐条对照 PRD |

---

## 💡 选型决策树

```
需要开发什么？
    │
    ├── 快速原型 / MVP
    │   └── ✅ pdforge (--mode 0to1)
    │       Token: 低  质量: 足够  速度: 快
    │
    ├── 标准功能迭代
    │   └── ✅ pdforge (--fix --loop)
    │       Token: 中  质量: 好  速度: 中
    │
    ├── 核心功能（安全/性能关键）
    │   └── ✅ forge-teams (完整流水线)
    │       Token: 高  质量: 最高  速度: 慢
    │
    ├── 复杂架构决策
    │   └── ✅ forge-teams P2 (--phase 2)
    │       多方案竞标，独立评审
    │
    ├── 只需代码审查
    │   ├── 常规审查 → pdforge (/review)
    │   └── 安全关键审查 → forge-teams P5 (--phase 5)
    │       红队攻击 + 交叉验证
    │
    └── 复杂 Bug 修复
        ├── 原因相对明确 → pdforge (/fix + systematic-debugging)
        └── 原因不明/间歇性 → forge-teams P6 或 /adversarial-debugging
```

---

## 🔧 成本效益分析

### Token 消耗对比

| 场景 | pdforge Token | forge-teams Token | 倍数 | 质量提升 | 推荐 |
|------|-------------|-------------------|------|---------|------|
| 简单功能 | 1x | 5-10x | 5-10x | 低（pdforge 已足够） | pdforge |
| 标准功能 | 1x | 5-10x | 5-10x | 中（对抗审查有价值） | pdforge + forge-teams P5 |
| 核心功能 | 1x | 10-15x | 10-15x | 高（架构 + 审查提升大） | forge-teams |
| 安全关键 | 1x | 10-20x | 10-20x | 极高（红队不可替代） | forge-teams |
| Bug 修复（简单） | 1x | 8-12x | 8-12x | 低 | pdforge |
| Bug 修复（复杂） | 1x | 8-15x | 8-15x | 高（对抗假设值得） | forge-teams |
| 只做架构决策 | 1x | 3-5x | 3-5x | 高（竞标 vs 独白） | forge-teams P2 |
| 只做代码审查 | 1x | 4-8x | 4-8x | 高（红队攻击） | forge-teams P5 |

### 何时值得多花 Token

```
值得投资 forge-teams 的信号：

  代价高 ▲
         │  ■ 安全漏洞
         │  ■ 架构返工
         │  ■ 生产事故
         │                    ← 修复成本 > 对抗调试成本
         │  ■ 核心逻辑 Bug
         ├────────────────────────────────────────────
         │  ■ 普通功能迭代     ← 修复成本 < 对抗调试成本
         │  ■ UI 微调
         │  ■ 文档更新
         │
         └──────────────────────────────────────────▶ 频率
```

**经验法则**：如果 bug 修复或返工成本 > forge-teams 额外 Token 成本，就值得用 forge-teams。

---

## ⚙️ 15 维度全面对比

| # | 维度 | pdforge | forge-teams |
|---|------|---------|-------------|
| 1 | **Agent 模式** | Subagent（隔离） | Agent Teams（可通信） |
| 2 | **通信模型** | 单向（Main → Sub → Main） | 多向（Agent ↔ Agent） |
| 3 | **并行能力** | 无（顺序执行） | 有（多 Agent 同时工作） |
| 4 | **偏见防御** | 流程纪律（强制步骤） | 结构化对抗（角色分离 + 辩论） |
| 5 | **决策方式** | 单 Agent 判断 | 多 Agent 辩论 → 仲裁者裁决 |
| 6 | **质量保障** | 审查 + 修复循环 | 对抗审查 + 红队 + 交叉验证 |
| 7 | **调试方法** | 4+1 阶段线性 | 竞争假设 + 对抗辩论 |
| 8 | **部署验证** | 自验证 | 交叉验证（独立验证者） |
| 9 | **Token 消耗** | 中等（1x） | 高（5-20x） |
| 10 | **速度** | 中等 | 调查并行快 / 辩论耗时 |
| 11 | **适用场景** | 标准开发、快速迭代 | 高质量、安全关键开发 |
| 12 | **学习曲线** | 低（顺序流程直观） | 中（需理解对抗模式） |
| 13 | **可审计性** | 审查报告 | 辩论记录 + 评分矩阵 + 证据板 |
| 14 | **前置条件** | 无特殊要求 | 需启用 Agent Teams 实验性功能 |
| 15 | **与 CI/CD 集成** | Hook + 自定义命令 | 同（可复用 pdforge 的 Hook） |

---

## 🚀 迁移路径

### 渐进式采用 forge-teams

不需要一次性全面切换。从投资回报率最高的阶段开始：

```
采用路径（按 ROI 排序）：

Step 1 ─────────────────────────────────────────────────
  forge-teams P5 (对抗审查)
  • ROI 最高：红队攻击几乎总能发现单人审查遗漏的问题
  • 风险最低：只是在 pdforge 实现后增加审查步骤
  • 命令：/forge-teams --phase 5

Step 2 ─────────────────────────────────────────────────
  forge-teams P2 (对抗架构设计)
  • ROI 高：架构决策是高杠杆的（修改成本随时间指数增长）
  • 适合：重大功能开发前的架构选型
  • 命令：/forge-teams --phase 2

Step 3 ─────────────────────────────────────────────────
  forge-teams P1 (对抗需求分析)
  • ROI 中高：减少需求膨胀和不切实际的承诺
  • 适合：重要功能的需求定义
  • 命令：/forge-teams --phase 1

Step 4 ─────────────────────────────────────────────────
  forge-teams 完整流水线 (P1-P7)
  • ROI 高但成本也高：适合关键功能
  • 适合：安全关键、性能关键的核心功能
  • 命令：/forge-teams
```

### 每个步骤的预期收益

| 采用步骤 | 额外 Token | 质量提升 | 建议频率 |
|---------|-----------|---------|---------|
| P5 (审查) | +4-8x | 缺陷检出率 25% → 70% | 每次重要发布前 |
| P2 (设计) | +3-5x | 避免架构锚定 | 重大功能开发前 |
| P1 (需求) | +2-3x | 减少范围膨胀 | 季度级功能规划 |
| 完整流水线 | +10-20x | 全面质量保障 | 核心/安全关键功能 |

---

## 🔧 混合使用模式

### 模式 1：pdforge 开发 + forge-teams 审查

```
pdforge 负责开发（P1-P4-P6-P7）
forge-teams 负责审查（P5 only）

┌────────────────────────────────────────────────────┐
│                                                    │
│  pdforge /brainstorm → /prd → /design → /plan     │
│                                                    │
│  pdforge /tdd (实现)                               │
│       │                                            │
│       ▼                                            │
│  forge-teams /forge-teams --phase 5 (对抗审查)      │
│       │                                            │
│       ├── APPROVE → pdforge /deploy                │
│       │                                            │
│       └── REQUEST CHANGES → pdforge /fix --loop    │
│              └── 修复后 → 再次 forge-teams P5       │
│                                                    │
└────────────────────────────────────────────────────┘
```

**优势**：pdforge 的高效开发 + forge-teams 的深度审查

---

### 模式 2：pdforge 快速迭代 + forge-teams 关键节点

```
┌────────────────────────────────────────────────────┐
│  功能规划阶段                                       │
│  ├── 普通功能 → pdforge /brainstorm → /prd         │
│  └── 重要功能 → forge-teams P1 (对抗需求分析)       │
│                                                    │
│  架构设计阶段                                       │
│  ├── 常规架构 → pdforge /design                    │
│  └── 复杂架构 → forge-teams P2 (对抗架构设计)       │
│                                                    │
│  实现阶段                                           │
│  └── 全部使用 pdforge /tdd (最高效)                 │
│                                                    │
│  审查阶段                                           │
│  ├── 常规审查 → pdforge /review                    │
│  └── 安全审查 → forge-teams P5 (红队攻击)          │
│                                                    │
│  调试阶段                                           │
│  ├── 简单 bug → pdforge /fix + systematic-debugging│
│  └── 复杂 bug → forge-teams P6 或 /adversarial-debugging │
│                                                    │
│  部署阶段                                           │
│  ├── Staging → pdforge /deploy staging             │
│  └── Production → forge-teams P7 (交叉验证)        │
│                                                    │
└────────────────────────────────────────────────────┘
```

**优势**：按风险级别选择工具，成本效益最优

---

### 模式 3：forge-teams 全流水线（关键功能）

```
forge-teams 完整 P1-P7 流水线

仅在以下场景使用：
├── 认证/授权系统
├── 支付/金融相关
├── 数据加密/安全
├── 核心 API 重构
├── 高并发性能关键路径
└── 合规/审计要求的功能
```

**优势**：最高质量保障，适合不允许出错的场景

---

## ⚠️ 常见误区

### 关于 forge-teams

| 误区 | 事实 |
|------|------|
| "forge-teams 比 pdforge 好" | 不是更好，是更严格。简单任务用 forge-teams 是浪费 |
| "用了 forge-teams 就不需要 pdforge" | forge-teams 只做质量保障，开发效率不如 pdforge |
| "对抗 = 所有地方都用辩论" | P3 规划和 P7 部署使用协作模式，不用对抗 |
| "更多 Agent = 更好" | Agent 数量有上限，超过后边际收益递减 |
| "forge-teams 能替代人工审查" | 重大决策仍需人工判断，forge-teams 提供更好的信息 |

### 关于 pdforge

| 误区 | 事实 |
|------|------|
| "pdforge 质量不够" | pdforge 的审查循环 (--fix --loop) 已经很强 |
| "pdforge 只适合简单项目" | pdforge 的 7 阶段流程覆盖完整开发周期 |
| "pdforge 没有安全审查" | 有 security-reviewer subagent |
| "pdforge 是遗留工具" | pdforge 是高效开发的首选，forge-teams 是补充 |

---

## 🔗 快速参考卡片

### pdforge 核心命令

| 命令 | 用途 | 对应阶段 |
|------|------|---------|
| `/brainstorm` | 头脑风暴 | P1 |
| `/prd` | 生成 PRD | P1 |
| `/design` | 系统设计 | P2 |
| `/plan` | 任务规划 | P3 |
| `/tdd` | TDD 实现 | P4 |
| `/review` | 代码审查 | P5 |
| `/accept --fix --loop` | 验收循环 | P5+P6 |
| `/fix` | 修复问题 | P6 |
| `/deploy` | 部署 | P7 |
| `/learn` | 提取学习 | P7 |

### forge-teams 核心命令

| 命令 | 用途 | 对应阶段 |
|------|------|---------|
| `/forge-teams` | 完整流水线 | P1-P7 |
| `/forge-teams --phase N` | 指定阶段 | PN |
| `/adversarial-debugging` | 对抗调试 | P6 |

### 决策速查

```
需要快速开发？         → pdforge
需要深度审查？         → forge-teams P5
需要架构决策？         → forge-teams P2
需要调试复杂 Bug？     → forge-teams P6
需要完整质量保障？     → forge-teams 完整流水线
需要混合使用？         → pdforge 开发 + forge-teams 审查
```
