# 阶段 3：任务规划 (Task Planning)

> 将设计分解为 2-5 分钟可完成的具体任务

---

## 📋 阶段概述

| 维度 | 说明 |
|------|------|
| **目标** | 将设计分解为可执行的小任务 |
| **输入** | PRD + 架构设计（来自阶段1、2） |
| **输出** | 任务列表（每个任务 2-5 分钟） |
| **上游阶段** | 系统设计（阶段2） |
| **下游阶段** | 开发实现（阶段4） |

---

## 🧩 组件清单

| 类型 | 名称 | 来源 | 说明 |
|------|------|------|------|
| **Agent** | `planner` | PDForge | 任务分解，生成执行计划 |
| **Skill** | `writing-plans` | PDForge | 计划编写规范 |
| **Command** | `/plan` | PDForge | 快捷入口 |
| **Rule** | `agents.md` | PDForge | Agent 委派规则 |
| **Hook** | - | - | 无特定 Hook |

---

## 🔧 组件详解

### 1. planner Agent

**Frontmatter 配置**：

```yaml
---
name: planner
description: 创建详细实现计划。复杂功能实现前必须使用。
tools: Read, Grep, Glob
model: opus
---
```

**职责**：

1. 分析 PRD 和架构文档
2. 分解为 2-5 分钟任务
3. 确定任务依赖顺序
4. 为每个任务指定验证方法

**产出**：`docs/plans/YYYY-MM-DD-[feature].md`（可选 `.json` 格式）

---

### 2. writing-plans Skill

**触发条件**：创建任务分解、编写实现计划时

**Frontmatter**：

```yaml
---
name: writing-plans
description: Use when breaking work into tasks. Triggers: "创建计划", "任务分解"
---
```

**核心原则 - 2-5 分钟规则**：

> 每个任务必须清晰到"缺乏判断力、无项目上下文、厌恶测试的初级工程师"都能在 2-5 分钟内完成。

**任务必须包含**：

| 要素 | 说明 | 示例 |
|------|------|------|
| 精确文件路径 | 具体到文件名 | `src/auth/login.ts` |
| 完整代码 | 可直接复制的代码，非伪代码 | 见下方示例 |
| 验证命令 | 可执行的测试命令 | `npm test -- --grep "login"` |
| 预估时间 | 2-5 分钟范围内 | `3min` |
| 依赖关系 | 依赖哪些前置任务 | `["T001", "T002"]` |

**任务格式示例**：

```markdown
### Task T003: 创建 User 模型

**File**: `src/models/user.ts`
**Action**: Create new file
**Estimate**: 3min
**Dependencies**: [T001]

**Code**:
```typescript
import { Schema, model, Document } from 'mongoose';

export interface IUser extends Document {
  email: string;
  passwordHash: string;
  createdAt: Date;
}

const userSchema = new Schema<IUser>({
  email: { type: String, required: true, unique: true },
  passwordHash: { type: String, required: true },
  createdAt: { type: Date, default: Date.now }
});

export const User = model<IUser>('User', userSchema);
```

**Verify**: 
```bash
npx tsc --noEmit src/models/user.ts
```
```

**任务顺序标准**：

```
1. 数据模型/架构优先
2. 业务逻辑服务其次
3. API 端点第三
4. UI 组件最后
5. 测试与组件同步（TDD）
```

---

### 3. /plan 命令

**语法**：

```bash
/plan <prd_path>
/plan <prd_path> --design <design_path>
/plan --quick "<功能描述>"
/plan <prd_path> --format json
```

**参数**：

| 参数 | 说明 | 示例 |
|------|------|------|
| `<prd_path>` | PRD 文档路径 | `docs/prd/auth.md` |
| `--design` | 设计文档路径 | `docs/architecture/auth.md` |
| `--quick` | 快速计划（无需 PRD） | `"添加密码重置"` |
| `--format` | 输出格式 | `json`, `md` |
| `--output` | 指定输出路径 | `docs/plans/custom.md` |

**示例**：

```bash
# 基本用法
/plan docs/prd/user-auth.md

# 带设计文档
/plan docs/prd/user-auth.md --design docs/architecture/auth.md

# JSON 输出
/plan docs/prd/user-auth.md --format json

# 快速计划（无需 PRD）
/plan --quick "添加密码重置功能"
```

---

### 4. agents.md Rule

**作用**：定义何时委派给哪个 Agent

**planner Agent 触发条件**：

```markdown
## Agent 委派规则

当用户说：
- "计划实现..." → dispatch planner
- "分解任务..." → dispatch planner  
- "创建计划..." → dispatch planner
- "开始实现..." → 先检查是否有计划，无则 dispatch planner
```

---

## 🚀 使用流程

### 标准流程

```bash
# Step 1: 确保 PRD 和设计文档已完成
# PRD: docs/prd/user-auth.md
# Design: docs/architecture/user-auth-design.md

# Step 2: 启动任务规划
/plan docs/prd/user-auth.md --design docs/architecture/user-auth-design.md

# Step 3: planner agent 执行:
#    - 读取 PRD 和设计文档
#    - 激活 writing-plans skill
#    - 分解为 2-5 分钟任务
#    - 确定依赖顺序

# Step 4: 产出文件:
#    docs/plans/2025-01-24-user-auth.md
```

### 快速计划

```bash
# 简单功能，无需完整 PRD
/plan --quick "添加密码重置功能"
```

### JSON 格式输出

```bash
/plan docs/prd/feature.md --format json
```

输出示例 (`docs/plans/2025-01-24-feature.json`)：

```json
{
  "feature": "user-authentication",
  "created": "2025-01-24",
  "total_tasks": 8,
  "estimated_time": "30min",
  "tasks": [
    {
      "id": "T001",
      "title": "创建 User 模型",
      "file": "src/models/user.ts",
      "action": "create",
      "estimate": "3min",
      "dependencies": [],
      "code": "...",
      "verify": "npx tsc --noEmit"
    }
  ]
}
```

---

## 📊 计划文档模板

```markdown
# [Feature Name] Implementation Plan

**Created**: YYYY-MM-DD
**PRD**: docs/prd/xxx.md
**Design**: docs/architecture/xxx.md
**Total Tasks**: N
**Estimated Time**: Xmin

---

## Context

[Background from brainstorming and design]

---

## Tasks

### Task T001: [任务标题]

**File**: `path/to/file.ts`
**Action**: Create / Modify / Delete
**Estimate**: Xmin
**Dependencies**: []

**Code**:
```typescript
// 完整可执行代码
```

**Verify**:
```bash
# 验证命令
```

---

### Task T002: ...

---

## Execution Notes

- [ ] 按顺序执行任务
- [ ] 每个任务完成后运行验证
- [ ] 验证通过后再进入下一个任务
```

---

## ⚙️ 配置差异

### 0→1 产品

```yaml
task_planning:
  granularity: coarse         # 粒度可稍粗
  verification: basic         # 基础验证
  tdd_required: true          # 仍然需要 TDD
```

**推荐做法**：
- 任务粒度可稍粗（5-10 分钟）
- 但仍需包含验证命令

### 1→100 产品

```yaml
task_planning:
  granularity: fine           # 精细粒度
  verification: comprehensive # 完整验证
  tdd_required: true          # 必须 TDD
  code_review: true           # 任务完成后审查
```

**推荐做法**：
- 严格 2-5 分钟粒度
- 每个任务包含完整测试用例

---

## ✅ 计划质量检查清单

- [ ] 每个任务 2-5 分钟可完成
- [ ] 每个任务有精确文件路径
- [ ] 每个任务有完整代码（非伪代码）
- [ ] 每个任务有验证命令
- [ ] 任务依赖关系清晰
- [ ] 顺序符合：模型 → 服务 → API → UI
- [ ] 测试与实现同步

---

## ⚠️ 注意事项

1. **完整代码而非伪代码**：任务必须包含可直接执行的完整代码
2. **2-5 分钟铁律**：超过 5 分钟的任务必须拆分
3. **验证命令必须可执行**：不能是"检查是否正确"这样的描述
4. **TDD 不可跳过**：测试代码应在任务中明确
5. **Description 陷阱**：writing-plans 的 description 只写触发条件

---

## 🔗 下一阶段

完成任务规划后，进入 **阶段 4：开发实现**：

```bash
# 子代理驱动开发（高质量，1→100）
invoke("subagent-driven-development")

# 或批量执行（快速，0→1）
invoke("executing-plans")

# 启动 TDD
/tdd
```
