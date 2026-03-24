---
name: forge-pipeline
description: >
  Agent Teams 7 阶段产品开发流水线。从需求到部署，每个关键决策点使用对抗辩论。
  支持意图自动识别：bug 描述自动进 P6 调试，审查请求自动进 P5 红队审查，新功能走完整流水线。
  Use when: (1) 新项目完整开发, (2) 复杂功能需要高质量保证, (3) 需要团队级并行开发,
  (4) 已有代码需要红队审查, (5) 已知 bug 需要对抗式调试。
  Triggers: "forge teams", "team pipeline", "adversarial development", "review my code", "debug this bug",
  "fix this bug", "为什么会", "帮我查", "帮我看看", "代码审查", "代码体检"
when_to_use: |
  - 新项目从零开发
  - 复杂功能需要高质量保证
  - 需要并行开发加速
  - 需要红队级安全审查
  - 已有代码需要独立审查（--skip-to 5）
  - 已知 bug 需要对抗式根因分析（--skip-to 6）
version: 1.7.0
---

# Forge Pipeline - Agent Teams 7 阶段对抗协作流水线

**多 agent 对抗协作流水线——每个关键决策点由多个 agent 辩论、竞争、交叉验证后达成共识。**

Announce at start: "I'm using the forge-pipeline skill to orchestrate a 7-phase adversarial development pipeline with Agent Teams."

> **前置条件**: 需要启用 Agent Teams 实验性功能。
> 在 settings.json 中添加: `"env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" }`

---

## Intent Detection & Auto-Routing (意图识别与自动路由)

当用户未指定 `--skip-to` 或 `--phase` 时，Lead **必须**先分析 `<requirement>` 内容，自动判定最佳入口。

### 路由决策树

```
用户输入 <requirement>
    │
    ├── 指定了 --skip-to N → 按 --skip-to 逻辑（恢复 or bootstrap）
    ├── 指定了 --phase N   → 单阶段执行
    │
    └── 未指定 → Lead 分析意图
        │
        ├── 意图 = BUG_FIX     → bootstrap P6（对抗调试）
        ├── 意图 = CODE_REVIEW  → bootstrap P5（红队审查）
        └── 意图 = NEW_FEATURE  → 完整流水线 P1→P7
```

### 意图判定规则

Lead 按以下信号判断意图类型：

| 意图 | 信号关键词/模式 | 路由 |
|------|----------------|------|
| **BUG_FIX** | bug、报错、崩溃、失败、超时、异常、间歇性、复现、regression、error、fix、修复、排查、定位、根因、为什么会… | → bootstrap P6 |
| **CODE_REVIEW** | 审查、review、体检、安全检查、代码质量、漏洞扫描、帮我看看这段代码、有没有问题 | → bootstrap P5 |
| **NEW_FEATURE** | 开发、实现、做一个、新增、创建、支持XX功能、重构（大范围）、从零开始 | → 完整流水线 P1→P7 |

**判定优先级**: BUG_FIX > CODE_REVIEW > NEW_FEATURE

> 当意图不明确时（如 "优化支付模块"），Lead 应视为 NEW_FEATURE 走完整流水线，因为优化通常涉及需求分析和架构决策。

### 自动路由后的行为

- **BUG_FIX → P6**: 等同于 `--skip-to 6`，`<requirement>` 作为 bug 描述，进入 Phase 0 Information Intake
- **CODE_REVIEW → P5**: 等同于 `--skip-to 5`，`<requirement>` 作为审查上下文，进入 Phase 0 Bootstrap
- **NEW_FEATURE → P1**: 正常完整流水线，`<requirement>` 作为需求输入

### 示例

```bash
# Lead 自动识别 → BUG_FIX → bootstrap P6
/forge-teams "支付回调间歇性超时，大约每10次失败2次"
/forge-teams "用户登录后 session 偶尔丢失"
/forge-teams "CI 跑到 integration test 就挂，本地没问题"

# Lead 自动识别 → CODE_REVIEW → bootstrap P5
/forge-teams "帮我审查下 src/payment/ 的安全性"
/forge-teams "这段认证代码有没有问题"
/forge-teams "上线前帮我做个代码体检"

# Lead 自动识别 → NEW_FEATURE → 完整流水线
/forge-teams "用户认证功能，支持 OAuth2 和 JWT"
/forge-teams "做一个暗色模式切换"
/forge-teams "支付系统重构"

# 显式指定，覆盖自动判定
/forge-teams --skip-to 5 "支付回调间歇性超时"   # 强制走 P5 审查
/forge-teams --skip-to 6 "帮我审查下安全性"       # 强制走 P6 调试
```

> **`--skip-to` 始终优先于自动路由**。当用户显式指定了 `--skip-to`，Lead 不做意图识别，直接按指定阶段执行。

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

## Pipeline State Management (.forge-state.json)

每次 pipeline 运行会在输出目录 `docs/forge-teams/[feature]-[timestamp]/` 下创建并维护一个 `.forge-state.json` 文件，用于支持跨 context 恢复。

### 文件格式

```json
{
  "feature": "用户认证功能",
  "timestamp": "20260324-103000",
  "requirement": "用户认证功能，支持 OAuth2 和 JWT",
  "requirement_attachments": [],
  "team_size": "medium",
  "current_phase": 1,
  "status": "in_progress",
  "phases": {
    "1": { "status": "completed", "started_at": "...", "completed_at": "..." },
    "2": { "status": "in_progress", "started_at": "...", "completed_at": null },
    "3": { "status": "pending" },
    "4": { "status": "pending" },
    "5": { "status": "pending" },
    "6": { "status": "pending" },
    "7": { "status": "pending" }
  },
  "artifacts": {
    "prd": "phase-1-requirements/prd.md",
    "adr": null,
    "plan": null,
    "code_report": null,
    "red_team_report": null,
    "debug_fixes": null,
    "acceptance": null
  },
  "options": {
    "no_red_team": false,
    "fix": false,
    "loop": 3
  },
  "interrupted_at": null,
  "progress_memo": null
}
```

### 需求附件保存

用户的需求输入可能包含非文本内容（图片、PDF、设计稿等）。这些内容在 `/clear` 后会从 context 中丢失，因此 P1 启动时 Lead **必须**将它们持久化：

1. 在输出目录下创建 `attachments/` 子目录
2. 将用户提供的图片、文件**复制**到 `attachments/`（保留原始文件名）
3. 将相对路径记入 `requirement_attachments` 数组

```
docs/forge-teams/[feature]-[timestamp]/
├── .forge-state.json
├── attachments/               ← 需求附件
│   ├── design-screenshot.png
│   └── original-prd.pdf
└── phase-1-requirements/
    └── ...
```

恢复时 Lead 从 `requirement_attachments` 读取路径，重新加载这些文件作为需求上下文。

> **注意**: `requirement` 字段存储**纯文本部分**，`requirement_attachments` 存储**非文本附件的相对路径**。两者互补，共同还原完整的原始需求。

### 生命周期

| 时机 | 动作 |
|------|------|
| Pipeline 启动（新 run） | **创建** `.forge-state.json`，写入 requirement、team_size、options，所有 phases 为 pending |
| 每个阶段开始时 | **更新** `current_phase`、该阶段 `status` → `in_progress`、`started_at` |
| 每个阶段完成时 | **更新** 该阶段 `status` → `completed`、`completed_at`、对应 `artifacts` 路径 |
| Pipeline 全部完成 | **更新** `status` → `completed` |
| P5→P6 回退 | **更新** `current_phase` → 6，P6 `status` → `in_progress` |
| Context 容量告警 | **更新** `interrupted_at`、`progress_memo`，执行主动保存协议 |
| Pipeline 异常退出 | 当前阶段保持 `in_progress`（恢复时从此阶段重新开始） |

### Incremental Write Rule (增量写入规则)

**核心原则**: 每个 Agent 的输出必须在 Lead 收到后**立即**写入文件，不得等到阶段结束再批量写入。这确保了 context 被截断时不会丢失已完成的工作。

| 阶段 | 增量写入文件 | 写入时机 |
|------|------------|---------|
| P1 | `debate-transcript.md` | 每轮辩论完成后追加 |
| P2 | `proposal-{a,b}.md`, `evaluation.md` | 每个方案/评审完成后立即写入 |
| P3 | `plan.json`, `risk-assessment.md` | 各自完成后立即写入 |
| P5 | `{role}-review.md` (每个审查员), `cross-examination.md` | 每个审查员完成后立即写入 |
| P6 | `hypotheses.md` (Evidence Board 更新), `debate-log.md` | 每轮辩论后追加 |
| P7 | `acceptance-{a,b}.md` | 每个 Reviewer 完成后立即写入 |

### phase-N-progress.md (编排备忘录)

Lead 在每个阶段维护一份 `phase-N-progress.md` 进度备忘录，**常规更新**（不仅仅是紧急情况）。

**内容**:
- 当前子步骤（如 "P2 Phase B: Critic 评审中"）
- 已完成的 agent 及其结论摘要
- 待完成的事项
- Lead 的判断笔记（辩论走向、关键分歧等）

**更新时机**: 每个重要子步骤完成后（如 agent 返回结果、辩论轮次结束）。

### Context Monitoring (上下文容量监控)

Lead 必须持续监控 context 使用量并按阈值采取行动：

| 阈值 | 状态 | 动作 |
|------|------|------|
| < 60% | 🟢 Normal | 正常执行 |
| 60%-75% | 🟡 Warning | 评估是否有足够空间完成当前阶段；如不够，准备保存 |
| > 75% | 🔴 Critical | **强制保存**，不再启动新的子步骤 |

> **重要**: Claude Code 在 ~83% 时自动触发 auto-compact，保存必须在此之前完成。

### Proactive Save Protocol (主动保存协议)

当 context 进入 Critical 状态时，Lead 执行以下流程：

1. **完成当前原子操作** — 不要中途中断正在执行的 agent
2. **写入中间产物** — 将所有已收到但未写入的 agent 输出写入文件
3. **写入进度备忘录** — 更新 `phase-N-progress.md`
4. **更新 .forge-state.json** — 写入 `interrupted_at`（ISO 时间戳）和 `progress_memo`（备忘录文件路径）
5. **清理团队** — shutdown + TeamDelete
6. **输出恢复命令** — 告诉用户执行 `/clear` 然后使用 `--skip-to N --feature [feature]` 恢复

### --skip-to 恢复协议

当使用 `--skip-to N` 恢复时，Lead **必须**按以下顺序执行：

1. **定位 feature 目录**:
   - 如果指定了 `--feature`：直接定位 `docs/forge-teams/[feature]/`
   - 否则：扫描 `docs/forge-teams/*/` 下所有 `.forge-state.json`
     - 筛选 `status` 不为 `completed` 的 run
     - 如果只有 1 个：自动选中
     - 如果有多个：列出所有未完成的 run（feature 名、当前阶段、最后活动时间），请用户选择
     - 如果没有：报错，提示没有可恢复的 run

2. **验证前序产物**:
   - 读取 `.forge-state.json`，确认 phase 1 到 N-1 的 `status` 均为 `completed`
   - 确认 `artifacts` 中对应文件存在且非空
   - 如果验证失败：报错并提示缺少哪些产物

3. **恢复上下文**:
   - 从 `.forge-state.json` 读取 `requirement`、`team_size`、`options`
   - 如果 `requirement_attachments` 非空，读取 `attachments/` 下的所有附件文件（图片、PDF 等）
   - 加载对应 artifacts 文件（PRD、ADR、plan 等）
   - **如果 `progress_memo` 非空**：读取对应的 `phase-N-progress.md` 文件，理解精确的中断位置
     - 仅 spawn 未完成的 agent（已完成的从文件加载结果）
     - 从中断的子步骤继续，而非从阶段开头重新开始
   - 从 phase N 开始执行，无需用户重新输入 requirement

4. **更新状态**:
   - 将 `current_phase` 更新为 N
   - 清除 `interrupted_at` 和 `progress_memo`（恢复后重置）
   - 继续正常的阶段执行和状态更新

---

## --skip-to 智能降级 (Bootstrap Mode)

`--skip-to N` 支持两种模式，Lead 自动判定：

```
--skip-to N
    │
    ├── 找到 .forge-state.json 且 P1~P(N-1) 均 completed
    │   └── ✅ 恢复模式: 加载前序产物，从断点继续
    │
    └── 找不到 .forge-state.json，或前序产物不完整
        │
        ├── N = 5 → ✅ Bootstrap 审查模式: 从代码推导上下文，进入 P5
        ├── N = 6 → ✅ Bootstrap 调试模式: 从用户描述收集信息，进入 P6
        └── N < 5 → ❌ 报错: P1-P4 必须有前序产物，无法 bootstrap
```

> **设计原则**: P5/P6 的核心输入是**代码**和**问题描述**，这些用户可以直接提供；P1-P4 的核心输入是前一阶段的结构化产物（PRD → ADR → plan.json），跳过会丢失对抗辩论的价值，因此不支持 bootstrap。

### Bootstrap 审查模式 (--skip-to 5，无前序产物)

**触发条件**: `--skip-to 5`，且 Lead 检测不到已完成的 P1-P4 产物。

**Phase 0: Bootstrap (上下文推导)**

Lead 在进入 P5 之前，执行以下信息收集步骤：

1. **确定审查范围**:
   - 以当前项目根目录为审查根目录
   - 扫描目录结构，识别主要代码文件

2. **推导预期行为**（替代 PRD 的作用）:
   - 读取 `README.md`、`CONTRIBUTING.md` 等项目文档
   - 读取测试文件，推导功能预期
   - 读取代码注释和 JSDoc/docstring
   - 如果用户提供了 `<requirement>` 文本：作为最高优先级的预期行为依据
   - 生成 `inferred-spec.md` 保存到输出目录

3. **推导技术架构**（替代 ADR 的作用）:
   - 分析 `package.json` / `go.mod` / `pyproject.toml` 等依赖文件
   - 分析目录结构推导架构模式
   - 识别框架和关键技术栈
   - 生成 `inferred-architecture.md` 保存到输出目录

4. **创建 .forge-state.json**:
   ```json
   {
     "feature": "bootstrap-review-[timestamp]",
     "timestamp": "...",
     "requirement": "<用户提供的需求描述，或 'inferred from codebase'>",
     "mode": "bootstrap",
     "team_size": "medium",
     "current_phase": 5,
     "status": "in_progress",
     "phases": {
       "1": { "status": "skipped" },
       "2": { "status": "skipped" },
       "3": { "status": "skipped" },
       "4": { "status": "skipped" },
       "5": { "status": "in_progress", "started_at": "..." },
       "6": { "status": "pending" },
       "7": { "status": "skipped" }
     },
     "bootstrap": {
       "inferred_spec": "inferred-spec.md",
       "inferred_architecture": "inferred-architecture.md"
     },
     "artifacts": { ... },
     "options": { ... }
   }
   ```

5. **进入 P5**: 使用 `inferred-spec.md` 替代 PRD 传给 spec-reviewer，使用 `inferred-architecture.md` 替代 ADR 传给 code-reviewer，其余审查员（security-reviewer、red-team-attacker）正常工作——它们本来就直接读代码。

**P5 完成后的路由**:
- 无 blocker → 输出审查报告，pipeline 结束（bootstrap 模式不进入 P7）
- 有 blocker + 指定了 `--fix` → 自动进入 P6 对抗调试，修复后回到 P5 缩小范围复审
- 有 blocker + 未指定 `--fix` → 输出审查报告 + 问题清单，由用户决定后续

### Bootstrap 调试模式 (--skip-to 6，无前序产物)

**触发条件**: `--skip-to 6`，且 Lead 检测不到已完成的 P5 审查报告。

**前提**: `<requirement>` 参数**必须提供** bug 描述。如果为空，Lead 直接报错提示用户提供 bug 描述。

**Phase 0: Information Intake (信息收集)**

Lead 在进入 P6 之前，执行信息收集（同 Adversarial Debugger 的 Phase 0）：

1. **收集 bug 信息**:
   - 从 `<requirement>` 参数获取用户的 bug 描述
   - 通过错误信息和 git history 推断相关文件

2. **自动补全上下文**:
   ```bash
   # 跑测试抓错误
   npm test 2>&1 | tee /tmp/error.log    # (或 pytest / go test 等)
   # 看最近变更
   git log --oneline -10
   git diff HEAD~5
   # 环境信息
   node -v && npm -v                     # (或 python --version 等)
   ```

3. **信息完整性检查**:
   - 必须有: 错误信息/现象、可疑代码范围
   - 最好有: 复现步骤、频率模式、近期变更
   - **如果关键信息不足，停下来向用户提问**，不进入假设生成阶段

4. **创建 .forge-state.json**:
   ```json
   {
     "feature": "bootstrap-debug-[timestamp]",
     "timestamp": "...",
     "requirement": "<bug 描述>",
     "mode": "bootstrap",
     "team_size": "medium",
     "current_phase": 6,
     "status": "in_progress",
     "phases": {
       "1": { "status": "skipped" },
       "2": { "status": "skipped" },
       "3": { "status": "skipped" },
       "4": { "status": "skipped" },
       "5": { "status": "skipped" },
       "6": { "status": "in_progress", "started_at": "..." },
       "7": { "status": "skipped" }
     },
     "bootstrap": {
       "bug_description": "<bug 描述>",
       "intake_log": "phase-0-intake.md"
     },
     "artifacts": { ... },
     "options": { ... }
   }
   ```

5. **进入 P6**: 使用收集到的信息作为输入，替代 P5 审查报告。直接进入假设生成 → 团队组建 → 对抗辩论 → 根因判定 → TDD 修复。

**P6 完成后的路由**:
- 修复完成 → 输出根因报告 + 修复记录，pipeline 结束
- 修复失败（3 轮辩论后仍无共识）→ 输出所有假设和证据，由用户决定后续

### Bootstrap 模式的限制

| 限制 | 说明 | 缓解方式 |
|------|------|---------|
| 无 PRD | spec-reviewer 基于推导的 `inferred-spec.md`，可能遗漏隐含需求 | 用户在 `<requirement>` 中提供关键需求点 |
| 无 ADR | code-reviewer 基于推导的架构理解，可能误判架构决策 | 用户指向项目已有的架构文档 |
| 无 P4 任务计划 | 无法判断文件归属是否合理 | P5 审查聚焦于代码质量和安全，不做任务级合规检查 |
| P7 不可用 | bootstrap 模式无需交付验收 | 如需完整交付，使用完整流水线模式 |

---

## Phase 1: Requirements Debate (需求对抗辩论)

**目的**: 通过多视角对抗辩论，生成高质量共识 PRD，避免单一视角盲点。

**团队组成**:

| 角色 | 职责 | 数量 |
|------|------|------|
| Product Advocate | 关注可行性、用户价值、快速交付 | 1 |
| Technical Skeptic | 关注风险、边界情况、技术债务 | 1 |
| Arbitrator (Lead) | 协调辩论，综合生成共识 PRD | Lead 自己 |

**执行流程**:
1. Lead 解析需求输入，准备辩论上下文
1.1. **创建 `.forge-state.json`**（仅 P1 首次执行时）：在 `docs/forge-teams/[feature]-[timestamp]/` 下创建状态文件，将用户传入的**原始需求原文**存入 `requirement` 字段；如果用户提供了图片、文件等非文本附件，复制到 `attachments/` 并将路径记入 `requirement_attachments`；同时记录 team_size、options，P1 status → `in_progress`
2. TeamCreate: `"req-debate-[feature]"`
3. Spawn 2 个分析师，各自独立分析需求
4. 每个分析师提交分析报告 (via SendMessage)
5. Lead 启动辩论：Product Advocate vs Technical Skeptic, Lead 仲裁
6. 最多 3 轮辩论，达成共识
7. Lead 综合产出 PRD
8. Shutdown team + TeamDelete

**产出**: `docs/forge-teams/[feature]/phase-1-requirements/prd.md`

**状态更新**: P1 `status` → `completed`，`artifacts.prd` → 文件路径，`current_phase` → 2

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

**状态更新**: P2 `status` → `completed`，`artifacts.adr` → 文件路径，`current_phase` → 3

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

**状态更新**: P3 `status` → `completed`，`artifacts.plan` → 文件路径，`current_phase` → 4

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

**状态更新**: P4 `status` → `completed`，`artifacts.code_report` → `phase-4-implementation/report.md`，`current_phase` → 5

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

**状态更新**: P5 `status` → `completed`，`artifacts.red_team_report` → `phase-5-red-team/arbitration.md`，`current_phase` → 7（无 blocker）或 6（有 blocker）

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

**状态更新**: P6 `status` → `completed`，`artifacts.debug_fixes` → `phase-6-debugging/fixes.md`，`current_phase` → 5（回退重审）

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

**状态更新**: P7 `status` → `completed`，`artifacts.acceptance` → `phase-7-delivery/acceptance.md`，pipeline `status` → `completed`

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
| P5 | P7 | 无 blocker 问题（完整流水线模式） |
| P5 | 完成 | 无 blocker 问题（bootstrap 模式） |
| P6 | P5 | 修复完成，需要重新审查（完整流水线模式 or bootstrap P5 + `--fix`） |
| P6 | 完成 | 修复完成（bootstrap P6 模式） |
| P7 | 完成 | 交叉验收通过 |

### Bootstrap 模式路由

| 场景 | 入口 | 路由 |
|------|------|------|
| `--skip-to 5`（无产物） | Phase 0 Bootstrap → P5 | P5 通过 → 完成 |
| `--skip-to 5 --fix`（无产物） | Phase 0 Bootstrap → P5 | P5 有 blocker → P6 → P5 循环（最多 3 次） |
| `--skip-to 6`（无产物） | Phase 0 Intake → P6 | P6 修复完成 → 完成 |

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
| 9 | 每个阶段开始/结束时更新 `.forge-state.json` | 支持跨 context 恢复 |
| 10 | Agent 输出必须立即写入文件（增量写入） | 防止 context 截断丢失已完成工作 |
| 11 | Lead 持续更新 phase-N-progress.md | 支持精确恢复中断点 |
| 12 | Context > 75% 时执行主动保存协议 | 在 auto-compact 前保存状态 |

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
| 用 forge-teams 做简单任务 | Token 浪费 10x+ | 简单任务不需要 forge-teams |
| 跳过 P1 对抗辩论 | PRD 有盲点 | 至少 2 轮辩论 |
| P2 只提出 1 个方案 | 失去竞标优势 | 至少 2 个独立方案 |
| P4 不用 delegate mode | Implementer 权限不足 | 必须 delegate |
| P5 Red/Blue 同一视角 | 失去对抗意义 | Red 必须主动攻击 |
| P6 跳过根因直接修 | 治标不治本 | 必须定位根因 |
| 不清理 team | 资源泄漏 | 每阶段结束必须 cleanup |
| 辩论超 3 轮 | 收益递减 | 3 轮后强制判定 |
| 想修 bug 却跑完整流水线 | 浪费 P1-P4 | 用 `--skip-to 6 "bug 描述"` |
| `--skip-to 5` 不提供需求描述 | spec-reviewer 只能猜测预期行为 | 尽量附上简短的功能需求说明 |
| `--skip-to 6` 信息过少就开始 | 假设质量差 | Phase 0 会要求补全信息，配合它 |

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      FORGE-TEAMS QUICK REFERENCE                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  P1: REQUIREMENTS DEBATE                                                │
│      Team: product-advocate + technical-skeptic                          │
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
