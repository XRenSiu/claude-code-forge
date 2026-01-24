# 上下文压缩策略

> 当 context window 接近限制时如何处理

## 为什么需要压缩

```
Context Window 有限（约 200k tokens）
↓
长对话后 context 填满
↓
性能下降（Lost in the Middle 效应）
↓
被迫 /clear 丢失上下文
```

**目标**: 在 context 满之前主动压缩，保留关键信息

---

## 压缩等级

### Level 1: 轻度压缩（context 50-70%）

**做什么**:
- 将工具输出的详细结果替换为摘要
- 将长代码块移到 findings.md

**示例**:
```
# 压缩前
[完整的 500 行测试输出]

# 压缩后
测试结果: 45/50 通过，详见 progress.md#test-run-1
```

### Level 2: 中度压缩（context 70-85%）

**做什么**:
- 将已完成阶段的详细记录移到 progress.md
- task_plan.md 中只保留一行摘要
- 只保留最近 3 次工具调用的完整结果

**示例**:
```
# 压缩前（在 task_plan.md）
### Phase 1: 理解需求
- 阅读了 src/auth/login.ts
- 发现使用 JWT 认证
- Token 存储在 localStorage
- 有 refresh token 机制
- 详细分析见下...

# 压缩后
### Phase 1: 理解需求 ✓
→ JWT 认证，详见 findings.md#auth-analysis
```

### Level 3: 重度压缩（context > 85%）

**做什么**:
- 只在 context 保留 task_plan.md 的核心部分
- 所有详细信息都在文件系统
- 每次操作前重读相关文件部分

**示例**:
```
# Context 中只保留
Goal: 修复登录 bug
Current Phase: 3 (Implement fix)
Next: 修改 validateToken() 函数
Errors: 见 task_plan.md#errors
```

---

## 压缩触发条件

| 信号 | 压缩等级 |
|------|----------|
| 对话超过 50 次来回 | Level 1 |
| 感觉响应变慢 | Level 2 |
| 收到 context 接近限制的警告 | Level 3 |
| 主动执行 /clear 前 | Level 3 |

---

## 压缩操作清单

### 执行 Level 1 压缩

- [ ] 将大于 100 行的工具输出移到 findings.md
- [ ] 用摘要 + 引用替换原位置
- [ ] 在 progress.md 记录压缩操作

### 执行 Level 2 压缩

- [ ] 执行 Level 1 所有操作
- [ ] 将已完成阶段的详细信息移到 progress.md
- [ ] task_plan.md 中已完成阶段只保留一行
- [ ] 只保留最近 3 次工具结果

### 执行 Level 3 压缩

- [ ] 执行 Level 1, 2 所有操作
- [ ] 确保 task_plan.md 完整更新
- [ ] 确保 findings.md 完整更新
- [ ] 确保 progress.md 完整更新
- [ ] 可以安全执行 /clear

---

## 压缩后的恢复

压缩后，信息存在于文件系统而非 context。

**工作模式变化**:
```
# 压缩前
直接使用 context 中的信息
↓
# 压缩后
每次需要信息时读取相关文件部分
```

**示例**:
```
需要之前的分析结果
↓
读取 findings.md#auth-analysis
↓
使用信息
↓
不保留在 context，下次需要再读
```

---

## 压缩记录模板

在 progress.md 中记录每次压缩：

```markdown
## Context Compression Log

### Compression: 2024-01-15 14:30

**原因**: Context 约 75%
**等级**: Level 2

**压缩内容**:
- Phase 1 详细记录 → progress.md#session-1
- 测试输出 → progress.md#test-run-1
- 代码分析 → findings.md#code-analysis

**保留引用**:
- findings.md#auth-analysis
- findings.md#error-patterns
- progress.md#session-2
```

---

## 反模式

| 反模式 | 后果 | 正确做法 |
|--------|------|---------|
| 等到被迫 /clear 才保存 | 丢失信息 | 主动压缩 |
| 压缩后不记录 | 不知道信息在哪 | 记录压缩操作 |
| 删除而非移动 | 信息永久丢失 | 移动到文件 |
| 压缩关键决策 | 会重复讨论 | 决策永远保留 |
