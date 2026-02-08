# 阶段 1：对抗需求分析 (Adversarial Requirements)

> 通过产品倡导者 vs 技术怀疑者辩论，产出经过技术可行性验证的 Battle-tested PRD

---

## 📋 阶段概述

| 维度 | 说明 |
|------|------|
| **目标** | 通过产品倡导者 vs 技术怀疑者辩论，产出经过技术可行性验证的 PRD |
| **输入** | 用户需求描述、现有代码库 |
| **输出** | Battle-tested PRD（`docs/prd/[feature]-prd.md`） |
| **上游阶段** | 无（流水线起点） |
| **下游阶段** | 对抗架构设计（阶段2） |

---

## 🧩 组件清单

| 类型 | 名称 | 说明 |
|------|------|------|
| **Agent** | `product-advocate` | 产品倡导者，从用户价值角度撰写 PRD (sonnet) |
| **Agent** | `technical-skeptic` | 技术怀疑者，挑战可行性 (sonnet) |
| **Skill** | `adversarial-requirements` | Phase 1 编排: 7 步协议 |
| **Command** | `/forge-teams --phase 1` | 单独执行阶段1 |
| **Rule** | `adversarial-protocol.md` | 10 条对抗辩论规则 |

---

## 💡 为什么这样设计

### 单 Agent PRD 的问题

单个 Agent 从简短的需求描述生成 PRD 时，系统性地犯以下错误：

```
单 Agent PRD 生成过程：
┌──────────────────────────────────────────────────────┐
│ 1. 阅读用户需求："添加用户认证"                        │
│ 2. 阅读代码库（快速浏览）                              │
│ 3. 生成 PRD：                                        │
│    - FR-001: OAuth2 登录 ← 乐观估计"3 天"            │
│    - FR-002: 密码重置   ← 假设现有邮件系统可用         │
│    - FR-003: 2FA        ← 没查代码库是否支持           │
│ 4. 假设标记：[⚠️ ASSUMED] 散落各处                    │
│ 5. 没人挑战这些假设                                    │
└──────────────────────────────────────────────────────┘
```

具体问题：

| 问题 | 单 Agent 表现 | 实际影响 |
|------|-------------|---------|
| 乐观估计 | 没有代码库深度分析就给出工作量估计 | 实施时发现比预期复杂 3-5x |
| 遗漏边界情况 | 只考虑 happy path | 实施阶段才发现关键边界 |
| 可行性盲区 | PRD 描述的功能可能在当前代码库极难实现 | 大量返工或方案推翻 |
| 假设堆积 | 标记了 `[⚠️ ASSUMED]` 但没人验证 | 假设进入设计和实施阶段 |

pdforge 的 prd-generator 已经做了很好的改进（假设标记、13 项检查清单），但 **假设仍然是同一个 Agent 自己标记的** — 它可能不知道自己不知道什么。

---

### 为什么 Advocate vs Skeptic（而不是 3+ Roles）

**最简对抗结构**：2 个角色是消除核心偏差的最小配置。

```
角色对立模型：
┌────────────────────────┐    ┌────────────────────────┐
│   Product Advocate     │    │   Technical Skeptic    │
│                        │    │                        │
│ 目标：最大化用户价值    │◄──►│ 目标：暴露技术风险      │
│ 视角：用户、业务        │    │ 视角：代码库、架构      │
│ 倾向：扩大范围          │    │ 倾向：缩小范围          │
│ 工具：Read, Write, Edit│    │ 工具：Read, Grep, Glob  │
│       Grep, Glob, Bash │    │       Bash（只读）      │
└────────────────────────┘    └────────────────────────┘
            │                             │
            └──────────┬──────────────────┘
                       ▼
              ┌────────────────┐
              │      Lead      │
              │  (主 session)  │
              │ 综合 + 仲裁    │
              └────────────────┘
```

**为什么不是 3+ 角色（用户分析师 + 技术专家 + 业务分析师 + 设计师）？**

| 考量 | 2 角色 | 3+ 角色 |
|------|--------|--------|
| Token 成本 | ~4x pdforge | ~6-10x pdforge |
| 收敛难度 | 2 轮即可 | 需要 3-4 轮，可能无法收敛 |
| 核心张力覆盖 | Desirability vs Feasibility | 覆盖更多维度但边际收益递减 |
| 协调复杂度 | Lead 仲裁 2 方意见 | Lead 需要协调 N 方，角色重叠 |

核心洞察：**需求阶段最重要的张力是"想要什么" vs "能做什么"**。Advocate/Skeptic 的分裂精确覆盖了这个张力。增加更多角色的边际收益不值得翻倍的成本。

---

### 为什么 2 轮辩论（不是 3 轮）

需求辩论与架构辩论有根本区别：

| 维度 | 需求辩论 (P1) | 架构辩论 (P2) |
|------|-------------|-------------|
| 挑战类型 | 事实导向（代码库能不能做） | 判断导向（哪个方案更好） |
| 证据来源 | 代码库（客观） | 经验 + 权衡（主观） |
| 收敛速度 | 快（事实说了算） | 慢（需要多轮权衡） |
| 最优轮数 | 2 轮 | 3 轮 |

**2 轮的内容设计**：

| 轮次 | Advocate | Skeptic |
|------|----------|---------|
| Round 1 | 撰写完整 PRD（FR, NFR, Stories） | 深度分析代码库 → 7 类挑战 |
| Round 2 | 逐条回应挑战，修改 PRD | 评估回应质量，标记接受/拒绝 |

Round 2 后，Lead 综合双方意见，产出最终 PRD。

**为什么 3 轮对需求是 overkill**：Skeptic 的挑战主要是事实性的（"你说的功能需要重构这个模块，因为第 234 行..."）。一旦事实被呈现，结论很快明确。不像架构辩论中"REST vs GraphQL"那样有大量主观权衡空间。

---

### 关键设计决策

| 决策 | 选项 | 选择 | 原因 |
|------|------|------|------|
| 角色数量 | 2 vs 3-5 | 2 | 成本效益最优，覆盖核心张力 |
| 辩论轮数 | 2 vs 3 | 2 | 需求辩论基于事实，收敛快 |
| Skeptic 工具 | 只读 vs 读写 | 只读 | 怀疑者不需要修改代码，只需分析 |
| Lead 角色 | 独立 arbiter vs 主 session | 主 session | 减少 1 agent，Lead 有完整上下文 |
| 模型选择 | sonnet vs opus | sonnet | 需求分析不需要 opus 的推理深度 |
| PRD 格式 | 自定义 vs pdforge 兼容 | pdforge 兼容 | 输出可直接被 pdforge 工具链消费 |

---

## 🔧 组件详解

### 1. product-advocate Agent

```yaml
---
name: product-advocate
model: sonnet
tools: Read, Write, Edit, Grep, Glob, Bash
---
```

**职责**：从用户价值角度撰写完整的 PRD。

**5 步 PRD 生成协议**：

```
Step 1: Parse 用户需求 → 提取核心功能点
Step 2: Codebase Analysis → 理解现有架构（但不深入细节）
Step 3: PRD Draft → 生成结构化 PRD
       - Problem Statement
       - User Stories
       - Functional Requirements (FR-001, FR-002, ...)
       - Non-Functional Requirements
       - Success Metrics
Step 4: Self-Validation → 13 项检查清单
Step 5: Output → docs/prd/[feature]-prd.md
```

**行为规范**：

| 规范 | 说明 |
|------|------|
| 用户视角优先 | 每个 FR 必须连接到用户价值 |
| 乐观但不盲目 | 可以提出有挑战性的需求，但需标注风险 |
| 回应挑战 | 收到 skeptic 挑战后必须逐条回应（接受/反驳/修改） |
| 假设标记 | 沿用 pdforge 的 `[⚠️ ASSUMED]` 标记 |

---

### 2. technical-skeptic Agent

```yaml
---
name: technical-skeptic
model: sonnet
tools: Read, Grep, Glob, Bash  # 只读，无 Write/Edit
---
```

**职责**：深度分析代码库，从技术可行性角度挑战 PRD。

**为什么是只读权限**：Skeptic 的角色是分析和挑战，不是修改。给予 Write/Edit 权限会模糊角色边界，让 Skeptic 可能试图"修复"问题而不是指出问题。

**7 个挑战类别**：

| # | 类别 | 英文 | 关注点 |
|---|------|------|--------|
| 1 | 可行性 | Feasibility | 当前代码库能否支持这个功能？ |
| 2 | 隐藏复杂度 | Hidden Complexity | 看起来简单但实际需要大量改动的部分？ |
| 3 | 技术债 | Technical Debt | 实现此功能会引入多少新技术债？ |
| 4 | 性能影响 | Performance Impact | 对现有系统性能有何影响？ |
| 5 | 安全风险 | Security Risk | 引入哪些新的攻击面？ |
| 6 | 集成冲突 | Integration Conflict | 与现有模块的集成点有哪些潜在冲突？ |
| 7 | 边缘用例 | Edge Cases | PRD 未覆盖的关键边界条件？ |

**挑战格式规范**：

```markdown
### CHALLENGE-001: [类别] [标题]
**严重级别**: CRITICAL / SIGNIFICANT / ADVISORY
**相关代码**: `src/auth/session.ts:234-267`
**问题描述**: [具体问题]
**代码证据**:
[引用具体代码片段]
**影响评估**: [如果忽视此问题的后果]
**建议**: [可选的修改方向]
```

**关键约束**：所有挑战必须有代码证据（文件路径 + 行号）。没有证据的观点不构成有效挑战。

---

### 3. adversarial-requirements Skill

**7 步编排协议**：

```
┌─────────────────────────────────────────────────────────┐
│              adversarial-requirements 7 步协议            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Step 1: Intake                                         │
│  └─ 解析用户输入，确定功能范围                             │
│                                                         │
│  Step 2: Team Create                                    │
│  └─ 创建 team: product-advocate + technical-skeptic      │
│                                                         │
│  Step 3: Advocate Draft                                 │
│  └─ Task → product-advocate: 生成初始 PRD                │
│                                                         │
│  Step 4: Skeptic Challenge                              │
│  └─ Task → technical-skeptic: 阅读 PRD + 代码库 → 挑战   │
│                                                         │
│  Step 5: Debate (2 rounds)                              │
│  ├─ Round 1: Advocate 回应挑战                           │
│  └─ Round 2: Skeptic 评估回应，标记接受/拒绝              │
│                                                         │
│  Step 6: Synthesis                                      │
│  └─ Lead 综合双方意见，产出 Battle-tested PRD             │
│                                                         │
│  Step 7: Cleanup                                        │
│  └─ 关闭 team，输出最终 PRD 路径                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Step 详解**：

| Step | 执行者 | 输入 | 输出 | 失败处理 |
|------|--------|------|------|---------|
| Intake | Lead | 用户需求描述 | 结构化功能范围 | 需求太模糊 → 提示用户补充 |
| Team Create | Lead | — | Team ID | — |
| Advocate Draft | product-advocate | 功能范围 + 代码库 | 初始 PRD | — |
| Skeptic Challenge | technical-skeptic | 初始 PRD + 代码库 | 挑战列表 | 无重大挑战 → 跳过辩论 |
| Debate R1 | product-advocate | 挑战列表 | 回应 + 修改后 PRD | — |
| Debate R2 | technical-skeptic | 回应 | 评估报告 | — |
| Synthesis | Lead | PRD + 挑战 + 回应 + 评估 | Battle-tested PRD | — |
| Cleanup | Lead | — | 关闭 team | — |

---

## 🚀 使用流程

### 完整流水线中自动执行

```bash
# forge-teams 自动从阶段1开始
/forge-teams "用户认证功能"
```

### 单独执行阶段1

```bash
# 只执行需求分析阶段
/forge-teams "暗色模式" --phase 1
```

### 带上下文执行

```bash
# 提供额外上下文文档
/forge-teams "支付集成" --phase 1 --context docs/requirements/payment-notes.md
```

### 输出示例

Battle-tested PRD 与普通 PRD 的区别 — 包含技术风险注解：

```markdown
# PRD: 用户认证 (User Authentication)

## Problem Statement
[标准 PRD 内容...]

## Functional Requirements

### FR-001: OAuth2 登录
[⚠️ CHALLENGED → RESOLVED]
- 需要重构 session 管理模块
- 当前基于 cookie 的实现（src/auth/session.ts:45-89）需改为 JWT
- 技术风险: 中 | 预计额外工作: 2-3 tasks

### FR-002: 密码重置
[⚠️ CHALLENGED → MODIFIED]
- 原始需求假设现有邮件系统可直接使用
- Skeptic 发现: 邮件模块（src/mail/sender.ts）不支持 HTML 模板
- 修改: 新增邮件模板引擎集成任务

### FR-003: 双因素认证 (2FA)
[⚠️ CHALLENGED → DEFERRED to v2]
- Skeptic 挑战: 当前架构不支持异步验证流程
- Advocate 接受: 2FA 推迟到 v2，需要先完成 session 重构

## Technical Risk Summary (来自对抗辩论)
| 风险 | 严重级别 | 状态 | 缓解方案 |
|------|---------|------|---------|
| Session 重构 | CRITICAL | RESOLVED | 在 FR-001 中包含 |
| 邮件模板 | SIGNIFICANT | MODIFIED | 新增集成任务 |
| 异步验证 | CRITICAL | DEFERRED | 推迟到 v2 |
```

---

## ⚙️ vs pdforge 对比

| 维度 | pdforge (prd-generator) | forge-teams (P1) | 价值 |
|------|------------------------|------------------|------|
| **角色** | 单 agent 生成 PRD | advocate 写 + skeptic 挑战 | 减少乐观偏差 |
| **代码验证** | agent 自己读代码 | skeptic 独立深度分析代码库 | 更客观的技术评估 |
| **假设处理** | 标记 `[⚠️ ASSUMED]` | 辩论消除/验证假设 | 更少未验证假设进入后续阶段 |
| **输出格式** | PRD | Battle-tested PRD + 技术风险注解 | 更完整的决策信息 |
| **挑战追踪** | 无 | 每个 FR 标记挑战状态 | 透明的决策过程 |
| **Token 消耗** | 1x | ~4x | 需权衡质量收益 |

### 何时用 pdforge，何时用 forge-teams P1

| 场景 | 推荐 | 原因 |
|------|------|------|
| 简单功能添加 | pdforge | 低复杂度不值得对抗成本 |
| 核心架构改动 | forge-teams | 高风险决策需要技术验证 |
| 0→1 MVP | pdforge | 速度优先于完美 |
| 1→100 新功能 | forge-teams | 已有代码库约束需要验证 |
| 需求非常清晰 | pdforge | 无需辩论 |
| 需求有技术不确定性 | forge-teams | 辩论暴露隐藏风险 |

---

## 📊 工作流图

```
┌───────────────────────────────────────────────────────────────┐
│                  Phase 1: Adversarial Requirements            │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  用户输入                                                      │
│  ┌──────────────────┐                                        │
│  │ "用户认证功能"    │                                        │
│  └────────┬─────────┘                                        │
│           │                                                   │
│           ▼                                                   │
│  ┌──────────────────┐    TeamCreate                          │
│  │   Lead (Intake)  │───────────────┐                        │
│  └──────────────────┘               │                        │
│                               ┌─────▼──────┐                │
│                               │   Team     │                │
│                    ┌──────────┤            ├──────────┐      │
│                    │          └────────────┘          │      │
│              ┌─────▼──────┐                  ┌───────▼────┐ │
│              │  product-  │   SendMessage    │ technical- │ │
│              │  advocate  │◄────────────────►│  skeptic   │ │
│              └─────┬──────┘   (2 rounds)     └──────┬─────┘ │
│                    │                                │       │
│                    │  PRD + Responses               │       │
│                    │  Challenges + Evaluations      │       │
│                    └──────────┬──────────────────────┘       │
│                               │                              │
│                         ┌─────▼──────┐                      │
│                         │   Lead     │                      │
│                         │ Synthesis  │                      │
│                         └─────┬──────┘                      │
│                               │                              │
│                         ┌─────▼──────────────────────────┐  │
│                         │ Battle-tested PRD              │  │
│                         │ docs/prd/[feature]-prd.md      │  │
│                         └────────────────────────────────┘  │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## ⚠️ 注意事项

1. **Skeptic 只读**：technical-skeptic 没有 Write/Edit 权限，防止其修改代码库或 PRD。Skeptic 的输出通过 SendMessage 传递给 Lead，由 Lead 综合。
2. **证据优先**：skeptic 的所有挑战必须附带代码证据（文件路径 + 行号）。没有代码证据的挑战在综合阶段会被降权。
3. **Lead 仲裁**：2 轮辩论后 Lead 必须做出综合判定。不允许无限辩论——如果 2 轮后仍有分歧，Lead 做最终决定。
4. **不替代 brainstorming**：如果需求完全模糊（用户不知道自己要什么），先用 pdforge 的 brainstorming skill 澄清，再用 forge-teams P1 验证。
5. **挑战状态标记**：最终 PRD 中每个被挑战的 FR 必须标记状态：
   - `[CHALLENGED → RESOLVED]`：挑战已解决，FR 保留
   - `[CHALLENGED → MODIFIED]`：FR 根据挑战修改
   - `[CHALLENGED → DEFERRED]`：FR 推迟到后续版本
   - `[CHALLENGED → REJECTED]`：FR 因技术不可行被移除
6. **Token 预算意识**：P1 约消耗 pdforge PRD 生成的 4 倍 token。对简单功能，直接使用 pdforge 更经济。

---

## 🔗 下一阶段

PRD 完成后，进入 **阶段 2：对抗架构设计**。

```bash
# 完整流水线中自动流转
# 或手动触发：
/forge-teams --phase 2
```

阶段 2 将基于 Battle-tested PRD 进行架构竞标，详见 `docs/phase-2-adversarial-design.md`。
