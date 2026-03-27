---
name: forge-verify
description: >
  独立需求验证入口。描述需求 → 结构化 → 映射代码实现 → 测试验证 → 差距报告。
  不需要 Agent Teams，使用 Lead 单 agent 流程。复用 spec-reviewer 的逐条验证方法论。
  Use when: (1) 验证需求是否已实现, (2) 检查功能完整性, (3) 交付前需求对照。
  Triggers: "forge verify", "verify requirement", "验证需求", "功能检查", "check implementation"
argument-hint: <requirement-description> [--strict] [--with-tests] [--format <matrix|summary>]
when_to_use: |
  - 需要验证某个需求是否已在项目中实现
  - 检查功能完整性
  - 交付前需求对照检查
  - 用户想知道 "这个功能做了没"
  - 用户明确请求需求验证
version: 1.0.0
disable-model-invocation: true
---

# Forge Verify - 独立需求验证

**描述需求 → 结构化 → 映射代码实现 → 测试验证 → 差距报告。**

这是 forge-teams 的独立需求验证入口。复用 spec-reviewer 的逐条验证方法论，但输入不依赖 P1 的 PRD，而是直接接收用户提供的需求描述。

Announce at start: "I'm using the forge-verify skill to check whether the described requirements are implemented in the current codebase."

> **注意**: 本 skill 不需要 Agent Teams，使用 Lead 单 agent 流程执行。

## 用法

```bash
/forge-verify <requirement-description> [options]
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `<requirement-description>` | 需求描述（文本、文件路径、或 URL） | 必填 |
| `--strict` | 严格模式：PARTIAL 视为 FAIL | 宽松模式 |
| `--with-tests` | 对每条 "已实现" 需求检查测试覆盖 | 不检查 |
| `--format <format>` | 输出格式：`matrix`（完整合规矩阵）或 `summary`（摘要） | `matrix` |
| `--scope <path>` | 限定验证范围到指定目录 | 整个项目 |

## 示例

```bash
# 用文字描述需求
/forge-verify "用户可以通过邮箱注册，密码至少8位，注册后发送验证邮件"

# 从文件加载需求
/forge-verify requirements.md

# 严格模式 + 检查测试覆盖
/forge-verify "支持 OAuth2 登录和 JWT token 刷新" --strict --with-tests

# 只检查特定目录
/forge-verify "API 支持分页和排序" --scope src/api/
```

## 输出目录

```
docs/forge-verify/
└── [requirement-slug]-[timestamp]/
    ├── structured-requirements.md  # 结构化需求
    ├── code-mapping.md             # 需求到代码映射
    ├── test-coverage.md            # 测试覆盖检查（--with-tests）
    ├── gap-report.md               # 差距报告
    └── summary.md                  # 最终摘要
```

---

## The 4-Phase Protocol

```
┌─────────────────────────────────────────────────────────────────┐
│                   VERIFY REQUIREMENT                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Phase 0: STRUCTURIZE     将大白话需求翻译成可验证条件             │
│           ↓               EARS 格式 + 验收标准                    │
│                                                                   │
│  Phase 1: CODE MAPPING    逐条需求搜索代码实现                     │
│           ↓               Grep + Glob + 代码阅读                  │
│                                                                   │
│  Phase 2: TEST VERIFY     检查测试覆盖（可选）                     │
│           ↓               对 "已实现" 的需求验证测试               │
│                                                                   │
│  Phase 3: GAP REPORT      综合差距报告                             │
│                            5 级分类 + 修复建议                     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 0: Requirement Structurization (需求结构化)

**目的**: 将用户的大白话需求翻译成可验证的结构化条件。

### Step 1: Load Requirements

```
IF 输入是文件路径:
    读取文件内容
ELIF 输入是文本:
    直接使用
```

### Step 2: Extract Verifiable Requirements

使用 EARS (Easy Approach to Requirements Syntax) 格式将需求翻译为可验证条件：

```markdown
## Structured Requirements

| ID | Type | EARS Format | Acceptance Criteria | Priority |
|----|------|-------------|---------------------|----------|
| REQ-001 | Functional | WHEN [条件] THE SYSTEM SHALL [行为] | [具体验收标准] | Must |
| REQ-002 | Functional | THE SYSTEM SHALL [行为] | [具体验收标准] | Must |
| REQ-003 | Edge Case | IF [条件] THEN THE SYSTEM SHALL [行为] | [具体验收标准] | Should |
| REQ-004 | Non-functional | THE SYSTEM SHALL [性能要求] | [量化指标] | Should |
```

**EARS 句型**:
- **Ubiquitous**: THE SYSTEM SHALL [行为]（始终成立）
- **Event-driven**: WHEN [事件] THE SYSTEM SHALL [行为]
- **Unwanted behavior**: IF [条件] THEN THE SYSTEM SHALL [防御行为]
- **State-driven**: WHILE [状态] THE SYSTEM SHALL [行为]
- **Optional**: WHERE [特征] THE SYSTEM SHALL [行为]

### Step 3: Confirm with User

如果需求描述模糊，列出结构化结果供用户确认：

```
我从你的需求描述中提取了 N 条可验证需求：

1. REQ-001: [EARS 格式]
2. REQ-002: [EARS 格式]
...

是否准确？需要调整或补充吗？
```

**如果用户确认 → 进入 Phase 1。如果用户调整 → 更新后再进入 Phase 1。**

保存结构化需求到 `structured-requirements.md`。

---

## Phase 1: Code Mapping (代码映射)

**目的**: 逐条需求在代码中搜索对应实现。

### 搜索策略

对每条需求，按以下优先级搜索实现：

```
1. 关键词搜索 (Grep)
   → 从需求中提取核心动词和名词
   → 在 src/ 目录搜索

2. 文件结构搜索 (Glob)
   → 根据需求涉及的领域推断文件名模式
   → 如 "用户注册" → **/register*, **/signup*, **/auth*

3. 深度代码阅读 (Read)
   → 对搜索命中的文件深入阅读
   → 确认实现是否完整匹配需求
```

### 搜索命令模板

```bash
# 功能关键词搜索
grep -rn "[关键词1]\|[关键词2]" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" src/ | grep -v test | grep -v node_modules | head -30

# 文件名模式搜索
find src/ -name "*[关键词]*" -type f | head -20

# 路由/端点搜索（Web 项目）
grep -rn "app\.\(get\|post\|put\|delete\)\|router\.\(get\|post\|put\|delete\)" --include="*.ts" --include="*.js" src/ | head -20

# 组件搜索（React 项目）
grep -rn "export.*function\|export.*const\|export default" --include="*.tsx" --include="*.jsx" src/ | grep -i "[关键词]" | head -20
```

### 映射状态

对每条需求确定状态：

| Status | 定义 | 判定条件 |
|--------|------|---------|
| **IMPLEMENTED** | 完全实现 | 代码完整覆盖 EARS 格式的所有条件和行为 |
| **PARTIAL** | 部分实现 | 主要逻辑存在但缺少某些方面（如错误路径、边界条件） |
| **NOT_IMPLEMENTED** | 完全缺失 | 找不到对应实现代码 |
| **SUSPICIOUS** | 实现可疑 | 找到了实现但行为与需求描述不符 |
| **EXCEEDED** | 超出需求 | 实现了需求未要求的额外功能（仅记录） |

保存映射结果到 `code-mapping.md`。

---

## Phase 2: Test Verification (测试验证，可选)

**触发条件**: 指定了 `--with-tests` 参数。

对每条状态为 IMPLEMENTED 或 PARTIAL 的需求，检查是否有对应测试：

```bash
# 搜索对应测试
grep -rn "[功能关键词]" --include="*.test.*" --include="*.spec.*" --include="*_test.*" src/ test/ tests/ __tests__/ | head -20

# 检查测试覆盖的场景
grep -rn "describe\|it\|test\|expect" --include="*.test.*" --include="*.spec.*" [相关测试文件] | head -30
```

### 测试覆盖分类

| Status | 定义 |
|--------|------|
| **TESTED** | 有直接覆盖该需求的测试 |
| **PARTIALLY_TESTED** | 有相关测试但未覆盖全部验收标准 |
| **NOT_TESTED** | 找不到对应测试 |
| **TEST_MISMATCH** | 有测试但测试逻辑与需求不匹配 |

保存测试覆盖结果到 `test-coverage.md`。

---

## Phase 3: Gap Report (差距报告)

**目的**: 综合 Phase 1-2 结果，输出结构化的差距报告。

### 5 级分类

```markdown
## Gap Report

### 📊 Overall Status

| Category | Count | Percentage |
|----------|-------|------------|
| ✅ IMPLEMENTED + TESTED | X | XX% |
| ⚠️ IMPLEMENTED + NO_TEST | Y | XX% |
| 🟡 PARTIAL | Z | XX% |
| ❌ NOT_IMPLEMENTED | W | XX% |
| 🔍 SUSPICIOUS | V | XX% |

**Overall Compliance**: XX%
```

### 详细矩阵

```markdown
### Compliance Matrix

| ID | Requirement (EARS) | Implementation Status | Test Status | Code Location | Notes |
|----|-------------------|----------------------|-------------|---------------|-------|
| REQ-001 | WHEN user submits email THE SYSTEM SHALL create account | ✅ IMPLEMENTED | ✅ TESTED | `src/auth/register.ts:L15-L40` | 完整实现 |
| REQ-002 | THE SYSTEM SHALL validate password >= 8 chars | ✅ IMPLEMENTED | ❌ NOT_TESTED | `src/auth/validate.ts:L10` | 缺少测试 |
| REQ-003 | WHEN registration completes THE SYSTEM SHALL send verification email | ❌ NOT_IMPLEMENTED | - | - | 完全缺失 |
| REQ-004 | IF email already exists THEN THE SYSTEM SHALL return error | 🟡 PARTIAL | ⚠️ PARTIALLY_TESTED | `src/auth/register.ts:L5` | 返回通用错误而非具体提示 |
```

### 按优先级排序的 Gap 列表

```markdown
### Critical Gaps (Must Fix)

#### GAP-001: [需求描述]
- **Requirement**: REQ-XXX
- **Status**: NOT_IMPLEMENTED
- **Impact**: [不满足此需求的影响]
- **Remediation**: [需要实现什么]
- **Estimated Scope**: [估计需要改动的文件/模块]

### Important Gaps (Should Fix)

#### GAP-002: [需求描述]
- ...

### Minor Gaps (Nice to Have)

#### GAP-003: [需求描述]
- ...
```

### Strict Mode 处理

当 `--strict` 启用时：
- PARTIAL 视为 FAIL（计入 Critical Gaps）
- IMPLEMENTED + NO_TEST 视为 Important Gap
- 总合规率计算更严格

保存差距报告到 `gap-report.md`。

---

## Final Output (最终输出)

```markdown
# Requirement Verification Report

## Summary
- **Requirements Analyzed**: N
- **Overall Compliance**: XX%
- **Mode**: [Standard / Strict]
- **Test Coverage Checked**: [Yes / No]

## Status Distribution
| Status | Count |
|--------|-------|
| ✅ Fully Implemented | X |
| ⚠️ Partially Implemented | Y |
| ❌ Not Implemented | Z |
| 🔍 Suspicious | W |

## Top Gaps
1. [最关键的缺失需求]
2. [第二关键的缺失需求]
3. [第三关键的缺失需求]

## Recommendation
[基于差距分析的下一步建议]
- 如果缺失严重: "建议使用 /forge-teams 启动完整开发流水线补齐功能"
- 如果基本完成: "建议使用 /forge-teams --skip-to 5 做一次红队审查确认质量"
- 如果全部通过: "需求已完全覆盖，可以进入部署阶段"
```

保存到 `summary.md`。

---

## Integration with Other Skills (与其他 Skill 的关系)

```
/forge-verify "需求描述"
      │
      ▼
  Verification Report
      │
      ├── 全部通过 → ✅ 完成
      │
      ├── 有 Gap → 用户决策
      │   ├── /forge-teams "补齐 [缺失需求]"     → 完整流水线补功能
      │   ├── /forge-teams --skip-to 5            → 红队审查已实现部分
      │   └── 手动修复
      │
      └── 可疑实现 → 用户决策
          ├── /forge-fix "行为与需求不符: [描述]"  → 对抗调试修复
          └── 手动排查
```

---

## Anti-patterns

| 坏行为 | 为什么失败 | 正确做法 |
|--------|-----------|---------|
| 不结构化直接搜索 | 搜索关键词不精准 | Phase 0 先翻译成 EARS 格式 |
| 只搜关键词不读代码 | grep 命中不等于实现 | 每个命中都要深入阅读确认 |
| PARTIAL 标为 IMPLEMENTED | 掩盖实际差距 | 严格按定义判定 |
| 不告诉用户下一步 | 差距报告无行动指引 | 每个 Gap 附带 Remediation |
| 忽略非功能需求 | 性能/安全需求同等重要 | 结构化时覆盖所有类型 |
| 只看 src/ 不看测试 | 没测试的实现是脆弱的 | `--with-tests` 检查测试覆盖 |
| 超出范围判定 | 没问的不要答 | 只验证用户提供的需求 |

---

## Core Principle

> **"The spec is the contract. The code is the delivery. Verification is the handshake."**
>
> 规格是契约，代码是交付，验证是握手确认。
> 不要假设"应该做了"——逐条验证，用代码位置证明。
