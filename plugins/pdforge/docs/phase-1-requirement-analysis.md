# 阶段 1：需求分析 (Requirement Analysis)

> 将模糊的用户想法转化为结构化的产品需求文档（PRD）

---

## 📋 阶段概述

| 维度 | 说明 |
|------|------|
| **目标** | 将模糊需求转化为结构化 PRD |
| **输入** | 用户想法、需求描述、现有文档 |
| **输出** | PRD 文档 (`docs/prd/[feature]-prd.md`) |
| **下游阶段** | 系统设计（阶段2） |

---

## 🧩 组件清单

| 类型 | 名称 | 来源 | 说明 |
|------|------|------|------|
| **Skill** | `brainstorming` | PDForge | 苏格拉底式问答澄清需求 |
| **Subagent** | `prd-generator` | PDForge | 生成结构化 PRD |
| **Command** | `/brainstorm` | 自定义 | 启动需求澄清流程 |
| **Command** | `/prd` | PDForge | 生成 PRD 文档 |
| **Rule** | - | - | 无特定规则 |
| **Hook** | - | - | 无特定 Hook |

---

## 🔧 组件详解

### 1. brainstorming Skill

**触发条件**：设计新功能、修改核心行为、需求模糊时

**6 阶段流程**：

```
阶段1: 侦察      → 静默读取现有代码和文档
阶段2: 发散探索  → 思考至少 3 个可能方向
阶段3: 提问      → 苏格拉底式问答（每次只问 1 个问题）
阶段4: 收敛呈现  → 分块展示设计（每块 200-300 字）
阶段5: 文档      → 保存 design-doc
阶段6: 交接      → 指向下一步（不自行开始下一阶段）
```

**反合理化红旗列表**：

| AI 可能的借口 | 回应 |
|--------------|------|
| 「我已经知道怎么做了」 | 知道概念 ≠ 与用户对齐 |
| 「这个很简单」 | 简单的事更容易假设错误 |
| 「用户很急」 | 返工比多花 5 分钟更慢 |

**产出**：`docs/designs/YYYY-MM-DD-[feature].md`

---

### 2. prd-generator Subagent

**Frontmatter 配置**：

```yaml
---
name: prd-generator
description: 将用户需求转化为结构化 PRD。需求不清晰时使用。
tools: Read, Grep, Glob
model: opus
---
```

**5 阶段流水线**：

```
Parse Input → Codebase Analysis → PRD Generation → Quality Validation → Output
```

**输入类型支持**：

| 输入类型 | 来源 | 假设比例 |
|----------|------|----------|
| 结构化 | brainstorming 产出 | 最低（<10%） |
| 半结构化 | 用户自有文档 | 中等（20-30%） |
| 非结构化 | 简短描述 | 较高（30-50%） |

**13 项质量验证检查清单**：

- [ ] 问题定义清晰
- [ ] 目标用户明确
- [ ] 成功指标可测量
- [ ] User Stories 完整
- [ ] 验收标准可验证
- [ ] Functional Requirements 有编号和优先级
- [ ] Non-Functional Requirements 覆盖
- [ ] API Design 契约明确
- [ ] Data Model 完整
- [ ] 依赖关系识别
- [ ] 风险评估
- [ ] 假设已标记
- [ ] 开放问题已列出

**产出**：`docs/prd/[feature]-prd.md`

---

### 3. /brainstorm 命令

**语法**：

```bash
/brainstorm "<功能描述>"
/brainstorm "<功能描述>" --context <现有文档路径>
```

**示例**：

```bash
# 基本用法
/brainstorm "用户认证功能"

# 带上下文
/brainstorm "添加 OAuth 登录" --context docs/requirements/auth-notes.md
```

---

### 4. /prd 命令

**语法**：

```bash
/prd <输入源>
/prd "<简短描述>"
/prd <design-doc路径>
/prd <任意文档路径>
```

**参数**：

| 参数 | 说明 |
|------|------|
| `--output <path>` | 指定输出路径 |
| `--format json` | 同时输出 JSON 格式 |
| `--strict` | 严格模式，禁止高假设比例 |

**示例**：

```bash
# 从 design-doc 生成（推荐）
/prd docs/designs/2025-01-24-user-auth.md

# 从简短描述生成（快速验证）
/prd "添加密码重置功能"

# 从现有文档生成
/prd docs/requirements/feature-spec.md

# 严格模式
/prd docs/designs/payment.md --strict
```

---

## 🚀 使用流程

### 路径 A：需求模糊（推荐）

```bash
# Step 1: 启动需求澄清
/brainstorm "用户认证功能"

# Step 2: 回答 Claude 的问题（苏格拉底式问答）
# ... 多轮对话 ...

# Step 3: 确认设计文档
# 产出: docs/designs/2025-01-24-user-auth.md

# Step 4: 生成 PRD
/prd docs/designs/2025-01-24-user-auth.md

# 产出: docs/prd/user-auth-prd.md
```

### 路径 B：需求清晰

```bash
# 直接从现有文档生成 PRD
/prd docs/requirements/existing-spec.md
```

### 路径 C：快速验证（0→1 产品）

```bash
# 直接用简短描述生成 PRD
/prd "添加 OAuth2 登录，支持 Google 和 GitHub"
```

---

## 📊 使用场景判断

| 情况 | 推荐路径 | 命令 |
|------|----------|------|
| 需求模糊、有多种可能方案 | A | `/brainstorm` → `/prd` |
| 需求清晰、有现成文档 | B | `/prd [doc]` |
| 快速验证、MVP 阶段 | C | `/prd "描述"` |
| 修改核心行为 | A | `/brainstorm` → `/prd` |
| 简单功能添加 | B/C | `/prd` |

---

## ⚙️ 配置差异

### 0→1 产品

```yaml
requirement_analysis:
  prd_validation: basic        # 基础验证
  assumption_threshold: 40%    # 允许较高假设比例
```

### 1→100 产品

```yaml
requirement_analysis:
  prd_validation: full         # 完整验证
  assumption_threshold: 10%    # 低假设比例
```

> **Brainstorming** 不与产品模式绑定。使用 `--brainstorm` 参数显式启用，启用后两种模式下均执行完整 6 阶段流程。

---

## ⚠️ 注意事项

1. **每次只问一个问题**：brainstorming 阶段禁止一次问多个问题
2. **假设必须标记**：PRD 中所有推断内容必须标记 `[⚠️ ASSUMED]`
3. **交接必须明确**：brainstorming 完成后必须输出交接提示，不自行开始下一阶段
4. **Description 陷阱**：Skill 的 description 只写触发条件，不写工作流

---

## 🔗 下一阶段

完成 PRD 后，进入 **阶段 2：系统设计**：

```bash
/design docs/prd/user-auth-prd.md
```
