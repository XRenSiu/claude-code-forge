# PDForge

> Product Development Forge - AI 驱动的结构化产品开发工作流

## Overview

PDForge 是一个 Claude Code 插件，提供完整的 7 阶段产品开发方法论。它将模糊的用户想法转化为生产就绪的代码，并在整个过程中强制执行高质量标准。

### 核心价值

- **防止「收到需求就写代码」的认知陷阱**：强制执行结构化的分析和设计流程
- **TDD 铁律**：没有失败的测试就没有代码
- **多层审查**：规格合规、代码质量、安全漏洞三层验证
- **断路器保护**：智能检测卡住状态，防止无限循环

---

## Installation

将此插件放置在 Claude Code 的 plugins 目录中：

```bash
# 全局安装
~/.claude/plugins/pdforge/

# 或项目级安装
your-project/.claude/plugins/pdforge/
```

---

## 7 阶段开发流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PDFORGE 7 阶段工作流                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  阶段 1: 需求分析                                                        │
│  ┌────────────────┐                                                     │
│  │ 用户想法       │──▶ brainstorming ──▶ prd-generator ──▶ PRD        │
│  └────────────────┘                                                     │
│           │                                                             │
│           ▼                                                             │
│  阶段 2: 系统设计                                                        │
│  ┌────────────────┐                                                     │
│  │ PRD            │──▶ architect ──▶ ADR + 架构文档                    │
│  └────────────────┘                                                     │
│           │                                                             │
│           ▼                                                             │
│  阶段 3: 任务规划                                                        │
│  ┌────────────────┐                                                     │
│  │ 设计文档       │──▶ planner ──▶ 2-5 分钟任务计划                    │
│  └────────────────┘                                                     │
│           │                                                             │
│           ▼                                                             │
│  阶段 4: 开发实现                                                        │
│  ┌────────────────┐                                                     │
│  │ 任务计划       │──▶ implementer + tdd-guide ──▶ 代码 + 测试        │
│  └────────────────┘                                                     │
│           │                                                             │
│           ▼                                                             │
│  阶段 5: 质量审查                                                        │
│  ┌────────────────┐    ┌─────────────────────────────────┐              │
│  │ 代码 + PRD     │──▶ │ spec-reviewer                   │              │
│  │                │    │ code-reviewer                   │              │
│  │                │    │ security-reviewer               │              │
│  └────────────────┘    └─────────────────────────────────┘              │
│           │                                                             │
│           ▼                                                             │
│  阶段 6: 修复验证                                                        │
│  ┌────────────────┐                                                     │
│  │ 审查反馈       │──▶ issue-fixer ──▶ 系统性修复                      │
│  └────────────────┘                                                     │
│           │                                                             │
│           ▼                                                             │
│  阶段 7: 交付部署                                                        │
│  ┌────────────────┐                                                     │
│  │ 通过审查的代码  │──▶ deployer + doc-updater ──▶ 生产环境            │
│  └────────────────┘                                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### 完整流水线（从想法到部署）

```bash
# 从一个想法开始完整流程
/pdforge --from-idea "用户认证功能，支持 OAuth2 和 JWT" --fix --loop

# 启用 brainstorming 需求澄清
/pdforge --from-idea "用户认证功能" --brainstorm --fix --loop

# 带自动修复和验证循环
/pdforge --from-idea docs/ideas/payment-v2.md --fix --loop 5
```

### 分阶段执行

```bash
# 阶段 1: 需求分析
/brainstorm "用户认证功能"
/prd docs/designs/2025-01-24-user-auth.md

# 阶段 2: 系统设计
/design docs/prd/user-auth-prd.md

# 阶段 3: 任务规划
/plan docs/adr/user-auth-adr.md

# 阶段 4: 开发实现
/tdd docs/plans/user-auth-plan.md

# 阶段 5: 质量审查
/accept --fix --loop docs/prd/user-auth-prd.md src/auth/

# 阶段 6: 修复验证
/fix docs/reviews/user-auth-review.md

# 阶段 7: 交付部署
/deploy --env staging
/update-docs
```

---

## Directory Structure

```
pdforge/
├── .claude-plugin/
│   └── plugin.json           # 插件元数据
├── README.md                 # 本文档
├── docs/                     # 阶段文档
│   ├── phase-1-requirement-analysis.md
│   ├── phase-2-system-design.md
│   ├── phase-3-task-planning.md
│   ├── phase-4-development-implementation.md
│   ├── phase-5-quality-review.md
│   ├── phase-6-fix-verification.md
│   └── phase-7-delivery-deployment.md
├── agents/                   # 12 个专业 Agent
│   ├── prd-generator.md
│   ├── architect.md
│   ├── planner.md
│   ├── implementer.md
│   ├── tdd-guide.md
│   ├── build-error-resolver.md
│   ├── spec-reviewer.md
│   ├── code-reviewer.md
│   ├── security-reviewer.md
│   ├── issue-fixer.md
│   ├── deployer.md
│   └── doc-updater.md
├── commands/                 # 命令定义
│   ├── brainstorming.md
│   ├── prd.md
│   ├── design.md
│   ├── plan.md
│   ├── tdd.md               # TDD 开发模式
│   ├── build-fix.md         # 构建错误修复
│   ├── review.md
│   ├── accept.md
│   ├── fix.md
│   ├── deploy.md
│   ├── update-docs.md
│   ├── learn.md
│   └── pdforge.md           # 主协调器
├── skills/                   # Skills 定义
│   ├── brainstorming/
│   ├── planning-with-files/
│   ├── writing-plans/
│   ├── test-driven-development/
│   ├── subagent-driven-development/
│   ├── executing-plans/       # 快速执行模式
│   ├── requesting-code-review/
│   ├── systematic-debugging/
│   ├── finishing-a-development-branch/
│   └── figma-to-code/
└── rules/                    # 规则约束
    ├── agents.md
    ├── patterns.md
    ├── testing.md
    ├── coding-style.md
    ├── security.md
    └── git-workflow.md
```

---

## Commands

| 命令 | 阶段 | 说明 |
|------|------|------|
| `/pdforge` | 全流程 | 主协调器，从想法到部署的完整流水线 |
| `/brainstorm` | 1 | 苏格拉底式需求澄清 |
| `/prd` | 1 | 生成产品需求文档 |
| `/design` | 2 | 系统设计和 ADR 生成 |
| `/plan` | 3 | 创建任务计划 |
| `/tdd` | 4 | 启动测试驱动开发 |
| `/build-fix` | 4 | 修复构建/类型错误 |
| `/review` | 5 | 单次代码审查 |
| `/accept` | 5 | 三阶段验收审查 + 自动修复循环 |
| `/fix` | 6 | 系统性问题修复 |
| `/deploy` | 7 | 部署到环境 |
| `/update-docs` | 7 | 更新文档 |
| `/learn` | 7 | 提取可复用模式 |

---

## Agents

| Agent | 阶段 | 用途 | 工具 |
|-------|------|------|------|
| `prd-generator` | 1 | 生成 PRD | Read, Grep, Glob |
| `architect` | 2 | 系统架构设计 | Read, Grep, Glob, Bash |
| `planner` | 3 | 任务分解 | Read, Grep, Glob |
| `implementer` | 4 | 任务执行 | Read, Write, Edit, Grep, Glob, Bash |
| `tdd-guide` | 4 | TDD 工作流指导 | Read, Write, Edit, Grep, Glob, Bash |
| `build-error-resolver` | 4 | 构建错误修复 | Read, Write, Edit, Grep, Glob, Bash |
| `design-reviewer` | 5 | 设计还原审查（Figma/截图） | Read, Grep, Glob, Bash |
| `spec-reviewer` | 5 | PRD 合规审查 | Read, Grep, Glob |
| `code-reviewer` | 5 | 代码质量审查 | Read, Grep, Glob, Bash |
| `security-reviewer` | 5 | 安全漏洞审查 | Read, Grep, Glob, Bash |
| `issue-fixer` | 6 | 问题修复 | Read, Write, Edit, Grep, Glob, Bash |
| `doc-updater` | 7 | 文档更新 | Read, Write, Edit, Grep, Glob, Bash |
| `deployer` | 7 | 环境部署 | Read, Bash |

---

## Skills

| Skill | 用途 |
|-------|------|
| `brainstorming` | 6 阶段结构化设计对话 |
| `planning-with-files` | 基于文件的计划管理 |
| `writing-plans` | 2-5 分钟任务粒度规范 |
| `test-driven-development` | TDD 红-绿-重构循环 |
| `subagent-driven-development` | 高质量模式：每任务子代理 + 二阶段审查 |
| `executing-plans` | 快速模式：批量执行 + 检查点验证 |
| `requesting-code-review` | 审查前检查清单 |
| `systematic-debugging` | 4+1 阶段根因分析 |
| `finishing-a-development-branch` | 分支完成决策树 |
| `figma-to-code` | Figma 设计稿转项目代码（MCP + 组件注册表） |

---

## Rules

| 规则 | 说明 |
|------|------|
| `agents.md` | Agent 委派决策树和权限 |
| `patterns.md` | API 设计模式约束 |
| `testing.md` | 80% 覆盖率要求 |
| `coding-style.md` | 命名规范、TypeScript 严格模式 |
| `security.md` | 安全红线、OWASP Top 10 |
| `git-workflow.md` | 分支命名、提交信息、合并策略 |

---

## Key Design Principles

| 原则 | 实现 |
|------|------|
| **Token 效率** | 核心指令精简，详情按需加载 |
| **渐进披露** | 触发条件 → 核心流程 → 详细资源 |
| **强制性语言** | 「必须」「不允许」而非「建议」 |
| **推荐驱动** | 做推荐而非推卸判断 |
| **分块输出** | 200-300 字一块，等待确认 |
| **认知隔离** | 审查使用独立子代理 |

---

## Anti-Rationalization Guardrails

### TDD 铁律

| AI 借口 | 回应 |
|---------|------|
| 「我手动测试过了」 | 删除代码 |
| 「先写代码再补测试也一样」 | 不一样 |
| 「这个太简单不需要测试」 | 需要 |
| 「我之后会加测试」 | 不行 |
| 「这只是小改动」 | 同样流程 |

### Brainstorming 捷径

| AI 借口 | 回应 |
|---------|------|
| 「我已经知道怎么做了」 | 知道 ≠ 与用户对齐 |
| 「这个很简单」 | 简单的事更容易假设错误 |
| 「用户很急」 | 返工比多花 5 分钟更慢 |

### 调试铁律

| AI 借口 | 回应 |
|---------|------|
| 「我还没找到根因但有个修复方案」 | 不允许，必须完成阶段 1 |

---

## Configuration Modes

### 0→1 产品（MVP/创业）

```yaml
tdd_coverage: 50%
review: code_only
security_review: optional
max_fix_rounds: 2
execution_mode: executing-plans  # 快速模式
```

### 1→100 产品（成熟产品）

```yaml
tdd_coverage: 80%
review: full  # spec + code + security
adr: mandatory
max_fix_rounds: 5
execution_mode: subagent-driven-development  # 高质量模式
```

> **Brainstorming** 通过 `--brainstorm` 参数显式启用，不与产品模式绑定。

---

## Typical Workflows

### 全新功能

```bash
/pdforge --from-idea "用户认证 with OAuth2" --fix --loop
```

### 基于现有 PRD 迭代

```bash
/pdforge --from-prd docs/prd/auth-v2.md --fix --loop
```

### 快速实现（跳过审查）

```bash
/pdforge --from-idea "添加暗色模式" --skip-review
```

### 仅运行验收审查

```bash
/pdforge --accept-only docs/prd/feature.md --fix --loop 5
```

---

## Author

**XRenSiu** (xrensiu@gmail.com)

---

## License

MIT
