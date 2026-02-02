---
name: requesting-code-review
description: 定义何时、如何请求代码审查。在完成任务步骤后或 PR 合并前激活。
---

# 请求代码审查

**核心原则**：审查不是可选的。每个有意义的代码变更都需要经过审查。

宣告开始时说："I'm using the requesting-code-review skill to ensure proper review process."

## 触发时机

### 必须请求审查的情况

| 场景 | 审查类型 | 原因 |
|------|----------|------|
| 完成计划中的任务步骤 | 三阶段审查 | 确保符合计划且质量达标 |
| PR 准备合并 | 完整审查 | 合并前的最后质量门 |
| 涉及认证/授权 | 安全审查必需 | 安全风险最高的领域 |
| 涉及支付/敏感数据 | 安全审查必需 | 合规和数据保护要求 |
| 修改核心业务逻辑 | 规格+代码审查 | 确保正确性和可维护性 |

### 可以跳过审查的情况

| 场景 | 条件 |
|------|------|
| 纯文档更新 | 不涉及代码逻辑 |
| 依赖版本 bump | 只有 lockfile 变更 |
| 格式化变更 | 仅空格/缩进/格式 |
| 测试修复 | 测试本身的修复（非逻辑变更） |

> ⚠️ **注意**：即使可以跳过，遇到不确定时宁可审查。

## 审查前检查清单

在请求审查之前，确保以下事项：

### 自检清单

- [ ] **代码可编译**：`npm run build` 或 `tsc --noEmit` 通过
- [ ] **测试通过**：`npm test` 全绿
- [ ] **格式化完成**：`npm run format` 或 `prettier --check`
- [ ] **Lint 通过**：`npm run lint` 无错误
- [ ] **没有调试代码**：无 `console.log`, `debugger`, `TODO: remove`

### 检测命令

```bash
# 快速自检脚本
echo "🔍 Running pre-review checks..."

# 1. TypeScript 编译
echo "Checking TypeScript..."
npx tsc --noEmit || { echo "❌ TypeScript errors"; exit 1; }

# 2. 测试
echo "Running tests..."
npm test || { echo "❌ Tests failed"; exit 1; }

# 3. Lint
echo "Running lint..."
npm run lint || { echo "❌ Lint errors"; exit 1; }

# 4. 调试代码检查
echo "Checking for debug code..."
grep -rn "console.log\|debugger\|TODO:\s*remove" --include="*.ts" src/ && {
  echo "⚠️ Found debug code"
}

echo "✅ Pre-review checks passed"
```

## 审查流程

质量审查采用多阶段流程，**顺序不可颠倒**：

```
┌─────────────────────────────────────────────────────────────┐
│                    审查流程                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   阶段 0: 设计还原审查 (design-reviewer) [按需]              │
│   └── 检查：视觉还原度、布局结构、组件映射                    │
│   └── 触发：上下文有设计参考（Figma URL/截图/设计稿）时       │
│       │                                                     │
│       ▼ 通过后（或无设计参考时跳过）                          │
│                                                             │
│   阶段 1: 规格合规审查 (spec-reviewer)                       │
│   └── 检查：实现是否满足 PRD 和计划中的所有需求               │
│   └── 通过条件：需求覆盖 100%，无缺失实现                     │
│       │                                                     │
│       ▼ 通过后                                              │
│                                                             │
│   阶段 2: 代码质量审查 (code-reviewer)                       │
│   └── 检查：代码质量、最佳实践、可维护性                      │
│   └── 通过条件：无严重问题，重要问题已知晓                    │
│       │                                                     │
│       ▼ 通过后                                              │
│                                                             │
│   阶段 3: 安全审查 (security-reviewer) [按需]                │
│   └── 检查：OWASP Top 10，敏感数据处理                       │
│   └── 触发：涉及认证/授权/敏感数据时必需                      │
│       │                                                     │
│       ▼ 全部通过                                            │
│                                                             │
│   ✅ 审查完成，可以合并                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 为什么这个顺序？

| 顺序 | 原因 |
|------|------|
| 先设计后规格 | 视觉还原是最直观的验证，提前发现布局/组件级问题 |
| 先规格后质量 | 先确保"做对的事"，再确保"做得好" |
| 先质量后安全 | 先解决逻辑问题，安全审查才有意义 |
| 设计审查可选 | 不是所有代码都有设计参考 |
| 安全审查可选 | 不是所有代码都涉及安全敏感领域 |

## 如何请求审查

### 准备审查材料

```markdown
## 审查请求

**变更类型**: Feature / Bugfix / Refactor / Security
**关联文档**: 
- PRD: docs/prd/feature-name.md
- 计划: docs/plans/feature-plan.md

**变更范围**:
- src/auth/login.ts (新增)
- src/auth/session.ts (修改)
- tests/auth/login.test.ts (新增)

**自检结果**:
- [x] TypeScript 编译通过
- [x] 测试通过 (覆盖率: 85%)
- [x] Lint 通过
- [x] 无调试代码

**需要重点关注**:
- 会话超时逻辑 (login.ts:L45-L60)
- 并发登录处理 (session.ts:L30)

**安全相关**: 是 (涉及认证)
```

### 调用审查员

```
# 阶段 0: 设计审查（有设计参考时）
dispatch design-reviewer with {
  DESIGN_REFERENCE: "https://figma.com/design/abc123/... 或 /path/to/screenshot.png",
  CODE_PATH: "src/views/**/*.vue"
}

# 阶段 1: 规格审查
dispatch spec-reviewer with {
  SPEC_DOC: "docs/prd/feature-name.md",
  CODE_PATH: "src/auth/**/*.ts",
  WHAT_WAS_IMPLEMENTED: "用户登录和会话管理"
}

# 阶段 2: 代码审查（规格通过后）
dispatch code-reviewer with {
  CODE_PATH: "src/auth/**/*.ts",
  PLAN_DOC: "docs/plans/feature-plan.md",
  FOCUS: "error-handling, session-management"
}

# 阶段 3: 安全审查（涉及认证时）
dispatch security-reviewer with {
  CODE_PATH: "src/auth/**/*.ts",
  FOCUS: "authentication, session-management"
}
```

## 处理审查反馈

### 反馈优先级

| 级别 | 含义 | 处理方式 |
|------|------|----------|
| 🔴 Critical | 必须修复才能合并 | 立即修复 |
| 🟡 Important | 应该修复，可协商 | 本次或下次修复 |
| 🟢 Suggestion | 可选改进 | 记录后续改进 |

### 反馈处理流程

```
收到反馈
    │
    ├── 🔴 Critical
    │   └── 立即修复 → 重新请求审查
    │
    ├── 🟡 Important
    │   ├── 同意 → 立即修复 或 创建 Issue
    │   └── 不同意 → 讨论，提供理由
    │
    └── 🟢 Suggestion
        ├── 同意 → 创建 Issue（下次迭代）
        └── 不同意 → 解释原因，无需行动
```

### 修复后重新审查

修复问题后，只需重新审查**修改的部分**和**相关影响**：

```
# 重新审查（指定变更范围）
dispatch code-reviewer with {
  CODE_PATH: "src/auth/login.ts",
  BASE_SHA: "fix-start-sha",
  HEAD_SHA: "HEAD",
  FOCUS: "fixed-issues"
}
```

## 审查通过标准

### 可以合并的条件

- [ ] 设计审查（如需要）：🟢 MATCH 或 🟡 PARTIAL（无 Must Pass 失败）
- [ ] 规格审查：🟢 PASS
- [ ] 代码审查：🟢 APPROVE 或 🟡 APPROVE WITH CHANGES
- [ ] 安全审查（如需要）：🟢 SECURE 或 🟡 NEEDS ATTENTION（已知风险可接受）
- [ ] 所有 🔴 Critical 问题已修复
- [ ] 所有 🟡 Important 问题已修复或有明确计划

### 不能合并的情况

- 设计审查返回 🔴 MISMATCH（Must Pass 维度失败）
- 任何阶段返回 🔴 FAIL / REQUEST CHANGES / CRITICAL ISSUES
- 存在未修复的 🔴 Critical 问题
- 测试覆盖率低于阈值（默认 80%）
- 安全扫描发现高危漏洞

## 红旗列表（反合理化）

| 想法 | 现实 |
|------|------|
| "这只是小改动，不需要审查" | 小改动也可能有大影响。审查。 |
| "时间紧，先合并再审查" | 技术债务会在最糟糕的时候爆发。审查。 |
| "我已经自己检查过了" | 你看不到自己的盲点。审查。 |
| "这是简单的 bugfix" | 修复一个 bug 可能引入另一个。审查。 |
| "审查太慢了" | 生产事故更慢。审查。 |

## 核心原则

1. **审查是质量门**：不是障碍，是保护
2. **顺序不可颠倒**：先设计（如有），后规格，再质量，最后安全
3. **自检先行**：不要浪费审查员时间
4. **反馈是礼物**：批评代码不是批评人
5. **持续改进**：每次审查都是学习机会
