---
description: 三阶段验收审查（规格+代码+安全）。支持多种规格输入方式、选择性审查员、自动修复循环。具备断路器保护、问题指纹追踪和会话恢复功能。
argument-hint: [--spec|--code|--security] [--skip-spec|--skip-code|--skip-security] [--fix] [--fix-blockers] [--loop [N]] [--feature <name>] [--status <status>] [--spec-dir <dir>] [--resume <session>] [--output <path>] <spec-files...> <code-path>
---

## Mission

执行三阶段验收审查（规格合规、代码质量、安全漏洞），从选定的审查角度进行评估。**必须输出持久化报告文件**。可选自动修复发现的问题并在智能断路器保护下重新验证。

---

## 规格输入方式

### 直接指定

**单个文件**：
```bash
/accept docs/prd/user-auth.md src/auth/
```

**多个文件**：
```bash
/accept docs/prd/auth.md docs/prd/session.md src/auth/
```

**Glob 模式** (`--spec-pattern`)：
```bash
/accept --spec-pattern "docs/prd/v2/*.md" src/
```

**目录扫描** (`--spec-dir`)：
```bash
/accept --spec-dir docs/prd/payment/ src/payment/
```

### 索引驱动

对于多功能项目，维护 `specs/manifest.json` 索引文件：

```json
{
  "version": "1.0",
  "features": [
    {
      "name": "user-auth",
      "description": "用户认证和会话管理",
      "specs": ["docs/prd/auth/login.md", "docs/prd/auth/session.md"],
      "code": ["src/auth/**", "src/middleware/auth.ts"],
      "status": "complete"
    },
    {
      "name": "payment-checkout",
      "description": "支付处理和结账流程",
      "specs": ["docs/prd/payment/checkout.md"],
      "code": ["src/payment/**"],
      "status": "in-progress"
    }
  ]
}
```

**按功能名** (`--feature`)：
```bash
/accept --feature user-auth
/accept --feature user-auth --feature payment-checkout
```

**按状态** (`--status`)：
```bash
/accept --status in-progress
/accept --status in-progress --fix --loop
```

---

## 审查员选择

### 包含标志（只运行指定的）

| 标志 | 说明 |
|------|------|
| `--spec` | 只运行规格审查 |
| `--code` | 只运行代码审查 |
| `--security` | 只运行安全审查 |

组合使用：`--spec --code` 运行规格和代码审查，跳过安全审查

### 排除标志（运行除指定外的所有）

| 标志 | 说明 |
|------|------|
| `--skip-spec` | 跳过规格审查 |
| `--skip-code` | 跳过代码审查 |
| `--skip-security` | 跳过安全审查（不推荐） |

**默认行为**：无标志 = 运行全部三个审查

---

## 自动修复选项

### 修复标志

| 标志 | 说明 |
|------|------|
| `--fix` | 审查后自动修复所有问题 |
| `--fix-blockers` | 审查后仅自动修复 blocker 问题 |
| 无标志 | 仅审查不修复（默认） |

### 循环标志（需配合 `--fix`）

| 标志 | 说明 |
|------|------|
| `--loop` | 修复后重新验证，最多重复 3 次（默认） |
| `--loop <N>` | 设置最大迭代次数（1-10） |

**循环行为**：
- 所有问题解决后提前停止
- 断路器触发后停止
- 收到完成承诺后停止
- 每次迭代在会话目录中生成独立报告

---

## 断路器

断路器通过检测卡住状态防止无限或浪费的循环。

### 断路器状态

| 状态 | 符号 | 行为 |
|------|------|------|
| **CLOSED** | 🟢 | 正常运行，继续修复 |
| **HALF-OPEN** | 🟡 | 测试恢复中，仅修复 blocker |
| **OPEN** | 🔴 | 检测到卡住，停止修复，需人工干预 |

### 阈值配置

| 阈值 | 默认 | 标志 | 说明 |
|------|------|------|------|
| 无进展轮数 | 2 | `--cb-no-progress <N>` | N 轮问题指纹相同后打开断路器 |
| 相同错误轮数 | 3 | `--cb-same-error <N>` | N 轮修复失败相同后打开断路器 |
| 问题增加率 | 50% | `--cb-increase <N>` | 问题增加 N% 后打开断路器 |
| 最大修复尝试 | 3 | `--cb-max-attempts <N>` | N 次尝试后将问题标记为 blocked |

### 断路器显示

```
┌─────────────────────────────────────────────────┐
│ 🔌 断路器状态                                    │
├─────────────────────────────────────────────────┤
│ 状态: 🟢 CLOSED                                  │
│                                                 │
│ 指标:                                           │
│   ├── 无进展轮数: 0 / 2                         │
│   ├── 相同错误轮数: 0 / 3                       │
│   ├── 问题趋势: ↓ 下降                          │
│   └── 被阻塞问题: 0                             │
│                                                 │
│ 历史:                                           │
│   Round 1: 8 问题 → 5 已修复, 3 剩余            │
│   Round 2: 3 问题 → 2 已修复, 1 剩余            │
└─────────────────────────────────────────────────┘
```

### 断路器触发

```
🔴 断路器 OPEN

触发原因: 连续 2 轮无进展
证据:
  - Round 2 问题: [#3, #5, #7]
  - Round 3 问题: [#3, #5, #7]（相同）

动作: 循环已终止
建议: 问题 #3, #5, #7 需要人工干预

强制继续（不推荐）:
  /accept --resume <session> --cb-reset
```

---

## 问题指纹追踪

每个问题获得唯一指纹，用于准确的进度追踪。

### 指纹生成

```
Fingerprint = hash(
  file_path +           # 如 "src/auth/login.ts"
  line_range +          # 如 "42-58"
  issue_type +          # 如 "blocker", "important", "minor"
  reviewer_source +     # 如 "SPEC", "CODE", "SECURITY"
  description_hash      # 描述前 100 字符，标准化
)
```

### 进度检测算法

```
Round N 问题:   [fp_a, fp_b, fp_c, fp_d]
Round N+1 问题: [fp_b, fp_e]

分析:
  ✅ 已解决: fp_a, fp_c, fp_d（已移除）
  🆕 新增:   fp_e（可能是回归或新发现）
  ➡️ 持续:   fp_b（未变化）

Progress = resolved_count > 0
         OR (new_count > 0 AND 是修复导致的回归)
```

### 指纹 vs 计数检测对比

| 场景 | 计数方式 | 指纹方式 |
|------|----------|----------|
| 问题移动到不同行 | "无进展" ❌ | 正确追踪 ✅ |
| 修复 2 个引入 1 个 | "有进展" (3→2) | "有进展" + 标记回归 ✅ |
| 相同问题不同描述 | "无进展" ❌ | 正确识别相同问题 ✅ |
| 描述拼写修正 | "有进展" ❌ | 正确忽略 ✅ |

---

## 完成承诺

子代理可通过承诺标记信号完成状态。

### 承诺标记

| 标记 | 含义 | 循环行为 |
|------|------|----------|
| `<promise>ALL_RESOLVED</promise>` | 修复者确信所有问题已修复 | 重新验证并退出（如确认） |
| `<promise>BLOCKED:原因</promise>` | 无法继续需人工输入 | 标记为 blocked，可能退出 |
| `<promise>NEEDS_HUMAN:原因</promise>` | 需要人工决策 | 暂停并提示用户 |
| `<promise>PARTIAL:N_fixed</promise>` | 部分已修复，其他剩余 | 继续循环处理剩余 |

### Issue-Fixer 承诺用法

```markdown
## 修复摘要

修复了 6 个问题中的 5 个。

### 被阻塞问题

问题 #4: 需要数据库 schema 变更
- **状态**: 🚧 BLOCKED
- **原因**: 需要迁移脚本和 DBA 审批
- **解除条件**: 迁移审批并部署后

<promise>BLOCKED:问题 #4 需要数据库迁移</promise>
```

### 承诺行为

**ALL_RESOLVED**：
1. 重新运行验证（快速检查）
2. 如无问题 → 成功退出
3. 如有问题 → 继续循环（承诺过早）

**BLOCKED**：
1. 标记指定问题为 blocked
2. Blocked 问题从"剩余"计数中排除
3. 如仅剩 blocked 问题可成功退出循环
4. `--strict` 标志：将 blocked 视为失败，不退出

**NEEDS_HUMAN**：
1. 暂停循环执行
2. 显示原因和选项给用户
3. 等待用户输入或超时（默认 5 分钟）
4. 用户可：继续、跳过问题或中止

---

## 会话恢复

会话可在中断后恢复。

### 会话状态文件

每个会话在 `.accept_session.json` 中维护状态：

```json
{
  "session_id": "a7f2",
  "feature": "user-auth",
  "started_at": "2025-01-15T14:30:25Z",
  "current_round": 2,
  "max_rounds": 3,
  "status": "in_progress",

  "specs": [
    "docs/prd/auth/login.md",
    "docs/prd/auth/session.md"
  ],
  "code_path": "src/auth/",

  "reviewers": {
    "spec": true,
    "code": true,
    "security": true
  },

  "circuit_breaker": {
    "state": "CLOSED",
    "no_progress_count": 0,
    "same_error_count": 0
  },

  "issues": {
    "fp_abc123": {
      "id": 1,
      "fingerprint": "fp_abc123",
      "severity": "blocker",
      "source": "SPEC",
      "status": "fixed",
      "fix_attempts": 1,
      "history": [
        {"round": 1, "action": "identified"},
        {"round": 1, "action": "fixed"}
      ]
    }
  },

  "rounds": [
    {
      "round": 1,
      "started_at": "2025-01-15T14:30:30Z",
      "completed_at": "2025-01-15T14:35:45Z",
      "issues_found": 8,
      "issues_fixed": 5,
      "issues_remaining": 3
    }
  ]
}
```

### 恢复命令

```bash
# 从会话目录恢复
/accept --resume docs/acceptance-reports/user-auth-20250115-143025-a7f2/

# 修改设置后恢复
/accept --resume <session> --loop 5  # 增加最大轮数

# 恢复并重置断路器（谨慎使用）
/accept --resume <session> --cb-reset

# 恢复特定功能（查找最新会话）
/accept --resume-feature user-auth

# 忽略现有会话开始新会话
/accept --new docs/prd/auth.md src/auth/
```

### 恢复行为

1. **加载会话状态**从 `.accept_session.json`
2. **跳过已完成工作**：已修复问题不重试，已完成轮次不重跑
3. **恢复断路器状态**
4. **从上轮继续**
5. **合并新问题**（重新验证时发现的）

### 中断会话检测

```
⚠️ 检测到中断会话

发现 'user-auth' 的未完成会话:
  会话: user-auth-20250115-143025-a7f2
  状态: Round 2 进行中（已中断）
  问题: 3 剩余, 5 已修复

选项:
  1. 恢复: /accept --resume docs/acceptance-reports/user-auth-20250115-143025-a7f2/
  2. 重新开始: /accept --new docs/prd/auth.md src/auth/
  3. 查看状态: /accept --session-status <session>
```

---

## 执行流水线

### 阶段 0: 会话初始化

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 会话已初始化
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

会话 ID: a7f2
目录: docs/acceptance-reports/user-auth-20250115-143025-a7f2/

规格文档:
  ├── docs/prd/auth/login.md
  └── docs/prd/auth/session.md

代码路径: src/auth/

断路器: 🟢 CLOSED
问题追踪: 指纹方式

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 阶段 1: 上下文收集

```
📋 验收审查设置
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

会话: user-auth-20250115-143025-a7f2

规格:
  ├── 来源: [manifest / 直接文件 / 目录]
  ├── 文件数: [count] 个规格文件已加载
  └── 重点: [特定区域如有]

审查员:
  ├── 规格审查: [✅ 启用 / ⭕ 跳过]
  ├── 代码审查: [✅ 启用 / ⭕ 跳过]
  └── 安全审查: [✅ 启用 / ⭕ 跳过]

自动修复: [🔧 所有问题 / 🔧 仅 Blocker / ⭕ 禁用]
循环: [🔄 启用 (最大 N) / ⭕ 禁用]

断路器:
  ├── 状态: 🟢 CLOSED
  ├── 无进展阈值: [N] 轮
  └── 相同错误阈值: [N] 轮

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 阶段 2: 选择性审查

执行选定的审查员：

**如启用规格审查 → 调用 spec-reviewer**：
- 焦点：PRD 合规性、功能覆盖、验收标准

**如启用代码审查 → 调用 code-reviewer**：
- 焦点：代码质量、可维护性、正确性

**如启用安全审查 → 调用 security-reviewer**：
- 焦点：OWASP Top 10、安全漏洞

### 阶段 3: 问题注册和指纹生成

审查后为每个问题生成指纹并注册到问题注册表。

### 阶段 4: 整合

编译结果到统一报告（带指纹）：

```markdown
# 🎯 验收审查报告

**会话**: [session-id]
**轮次**: [N] / [max]
**审查时间**: [date/time]
**规格文档**: [list]
**审查员**: [list]

---

## 📊 执行摘要

| 审查员 | 结论 | 关键问题 | Blocker |
|--------|------|----------|---------|
| 规格 | 🟢/🟡/🔴/⭕ | [count] | [count] |
| 代码 | 🟢/🟡/🔴/⭕ | [count] | [count] |
| 安全 | 🟢/🟡/🔴/⭕ | [count] | [count] |

**总体状态**: 🟢 就绪 / 🟡 警告 / 🔴 未就绪
**断路器**: 🟢 CLOSED / 🟡 HALF-OPEN / 🔴 OPEN

---

## 🔴 Blocker（必须修复）

### 问题 #1 [fp:abc123]
- **来源**: 规格审查
- **位置**: `src/auth/login.ts:42-58`
- **指纹**: `abc123`
- **状态**: ⏳ 待处理
- **修复尝试**: 0
- **描述**: [description]
- **建议修复**: [fix]

---

## 📊 进度追踪

| 指纹 | 状态 | 尝试 | 历史 |
|------|------|------|------|
| abc123 | ✅ 已修复 | 1 | R1: 发现 → R1: 修复 |
| def456 | ⏳ 待处理 | 2 | R1: 发现 → R1: 失败 → R2: 失败 |
| xyz789 | 🚧 阻塞 | 1 | R1: 发现 → R1: 阻塞 |
```

### 阶段 5: 自动修复 + 验证循环（带断路器）

```
┌─────────────────────────────────────────────────────────────────┐
│            修复 + 验证循环（带断路器）                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  每轮开始前:                                                    │
│    └── 检查断路器状态                                           │
│         ├── 🔴 OPEN → 立即退出                                  │
│         ├── 🟡 HALF-OPEN → 仅修复 blocker                       │
│         └── 🟢 CLOSED → 正常运行                                │
│                                                                 │
│  Round N:                                                       │
│    ├── 审查 → 收集问题（带指纹）                                │
│    ├── 与 Round N-1 比较指纹                                    │
│    │    ├── 计算: 已解决、新增、持续                            │
│    │    └── 更新断路器指标                                      │
│    ├── 检查完成承诺                                             │
│    │    ├── ALL_RESOLVED → 验证并退出                           │
│    │    ├── BLOCKED → 标记问题，可能退出                        │
│    │    └── NEEDS_HUMAN → 暂停等待输入                          │
│    ├── 修复问题（尊重 blocked 状态）                            │
│    └── 更新会话状态                                             │
│                                                                 │
│  退出条件:                                                      │
│    ├── ✅ 所有问题已解决（无待处理指纹）                        │
│    ├── ✅ 仅剩 blocked 问题（非 --strict 模式）                 │
│    ├── ✅ 收到完成承诺并验证通过                                │
│    ├── 🔴 断路器 OPEN                                           │
│    ├── 🛑 达到最大迭代次数                                      │
│    └── 👤 用户请求停止                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 阶段 6: 总结报告

```markdown
# 🔄 验收审查总结

**功能**: user-auth
**会话**: a7f2
**目录**: docs/acceptance-reports/user-auth-20250115-143025-a7f2/
**规格**: docs/prd/auth/login.md, docs/prd/auth/session.md
**开始**: 2025-01-15 14:30:25
**完成**: 2025-01-15 14:42:18
**耗时**: 11m 53s
**总轮数**: 2 / 最大 3
**最终状态**: ✅ 全部通过
**退出原因**: 所有问题已解决

---

## 🔌 断路器最终状态

| 指标 | 最终值 | 阈值 | 状态 |
|------|--------|------|------|
| 状态 | 🟢 CLOSED | - | 正常 |
| 无进展轮数 | 0 | 2 | ✅ |
| 相同错误轮数 | 0 | 3 | ✅ |
| 问题趋势 | ↓ 下降 | - | ✅ |

---

## 📈 轮次历史

| 轮次 | 发现 | 修复 | 阻塞 | 剩余 | 进度 |
|------|------|------|------|------|------|
| 1 | 8 | 5 | 1 | 2 | ✅ +5 |
| 2 | 2 | 2 | 0 | 0 | ✅ +2 |

---

## 📊 问题解决追踪

| 指纹 | 问题 | 来源 | 状态 | 尝试 | 解决轮次 |
|------|------|------|------|------|----------|
| abc123 | 登录验证 | SPEC | ✅ 已修复 | 1 | Round 1 |
| def456 | 缺少测试 | CODE | ✅ 已修复 | 1 | Round 1 |
| ghi789 | 错误处理 | CODE | ✅ 已修复 | 2 | Round 2 |
| mno345 | Schema 变更 | CODE | 🚧 阻塞 | 1 | 需人工 |

---

## 💡 建议

1. ✅ 所有活跃问题已解决 - 可以合并
2. ⚠️ 被阻塞问题 mno345 需单独追踪
3. 考虑为修复的竞态条件添加集成测试

---

## 🔄 恢复信息

如需恢复此会话:
```bash
/accept --resume docs/acceptance-reports/user-auth-20250115-143025-a7f2/
```

---

*生成时间: 2025-01-15 14:42:18*
```

---

## 报告输出结构

```
docs/acceptance-reports/
└── [feature]-[YYYYMMDD]-[HHmmss]-[session-id]/
    ├── .accept_session.json    # 会话状态（用于恢复）
    ├── round-1-review.md       # 初始审查
    ├── round-1-fixes.md        # Round 1 修复（如 --fix）
    ├── round-2-review.md       # 重新验证（如 --loop）
    ├── round-2-fixes.md        # Round 2 修复
    ├── round-3-review.md       # 最终验证
    └── summary.md              # 总体摘要
```

---

## 示例命令

```bash
# ===== 基本用法 =====

# 单个规格文件
/accept docs/prd/feature-auth.md src/auth/

# 多个规格文件
/accept docs/prd/auth.md docs/prd/session.md src/auth/

# 规格目录
/accept --spec-dir docs/prd/payment/ src/payment/

# Glob 模式
/accept --spec-pattern "docs/prd/v2/*.md" src/

# ===== 索引驱动 =====

# 按功能名（需 manifest）
/accept --feature user-auth

# 多个功能
/accept --feature user-auth --feature payment-checkout

# 按状态
/accept --status in-progress

# 组合
/accept --status in-progress --spec --code

# ===== 带自动修复 =====

# 修复所有问题
/accept --fix docs/prd/auth.md src/auth/

# 仅修复 blocker
/accept --fix-blockers --feature payment-checkout

# ===== 带循环 =====

# 默认循环（最大 3）
/accept --fix --loop docs/prd/auth.md src/auth/

# 自定义循环次数
/accept --fix --loop 5 --feature user-auth

# 调整断路器
/accept --fix --loop 5 --cb-no-progress 3 --cb-same-error 4 docs/prd/auth.md src/auth/

# ===== 会话恢复 =====

# 恢复中断的会话
/accept --resume docs/acceptance-reports/user-auth-20250115-143025-a7f2/

# 恢复功能的最新会话
/accept --resume-feature user-auth

# 重新开始（忽略现有会话）
/accept --new docs/prd/auth.md src/auth/

# ===== 选择性审查员 =====

# 仅规格审查
/accept --spec --feature user-auth

# 代码 + 安全（无规格）
/accept --code --security --status in-progress

# 除代码审查外全部
/accept --skip-code --fix --loop --feature payment-checkout
```

---

## 边缘情况处理

**如未提供规格**：
> 我需要规格文档来进行审查。请提供：
> - 文件路径: `/accept docs/prd/auth.md src/auth/`
> - 目录: `/accept --spec-dir docs/prd/ src/`
> - 功能名: `/accept --feature user-auth`（需 manifest）

**如未找到 manifest**：
> ⚠️ 未找到 Manifest 文件 `specs/manifest.json`
>
> 要使用 --feature 或 --status，请创建 manifest 文件：
> ```bash
> /accept --init-manifest  # 生成模板
> ```

**如断路器打开**：
> 🔴 断路器 OPEN - 循环已终止
>
> 以下问题无法自动解决：
> - [带指纹的问题列表]
>
> 选项：
> 1. 手动修复后恢复: `/accept --resume <session>`
> 2. 强制继续（不推荐）: `/accept --resume <session> --cb-reset`
> 3. 重新开始: `/accept --new <specs> <code>`

---

## 与其他命令的关系

| 命令 | 说明 |
|------|------|
| `/review` | 单次审查，无自动修复 |
| `/accept` | 三阶段审查 + 可选自动修复循环 |
| `/fix` | 单独的修复命令 |
| `/pdforge` | 完整流水线（包含 /accept） |

---

## 最佳实践

1. **先用 /review**：大型变更先用 `/review` 了解问题规模
2. **合理设置 --loop**：简单问题 2-3 轮，复杂问题 5+ 轮
3. **保留日志**：`--fix` 模式生成详细日志用于追溯
4. **分模块验收**：大型功能按模块分别验收
5. **关注断路器**：触发意味着需要人工介入，不要强行继续

---

## 注意事项

⚠️ **自动修复的局限性**：

- 适合明确的代码问题（类型错误、格式问题、简单 bug）
- 架构问题、需求歧义、复杂业务逻辑需要人工处理
- 断路器触发时应停下来思考，而不是提高轮数

⚠️ **资源消耗**：

- 每轮修复会调用多个 Agent，注意 token 消耗
- 设置 `--loop` 时考虑成本预算
