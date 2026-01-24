---
name: fix
description: 启动修复流程。收到审查反馈或遇到问题时使用。
---

# /fix 命令

快速启动问题修复流程，自动激活 `issue-fixer` Agent 和 `systematic-debugging` Skill。

## 使用方式

```bash
# 基本用法：修复指定文件的问题
/fix src/auth/login.ts

# 根据审查报告修复
/fix --review docs/reviews/code-review-2024-01-15.md

# 修复特定优先级的问题
/fix --priority critical

# 启动验证循环（自动重新审查直到通过）
/fix --loop

# 指定最大循环次数
/fix --loop --max-rounds 5

# 修复并重新运行审查
/fix --loop src/auth/ --prd docs/prd/auth.md
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `<path>` | 要修复的文件或目录 | 当前目录 |
| `--review <file>` | 审查报告文件路径 | - |
| `--prd <file>` | PRD 文档（用于规格验证） | - |
| `--priority <level>` | 只修复指定优先级（critical/important/suggestion） | all |
| `--loop` | 启动验证循环 | false |
| `--max-rounds <n>` | 最大循环次数 | 5 |
| `--no-tdd` | 跳过 TDD（不推荐） | false |

## 执行流程

```
┌─────────────────────────────────────────────────────────────┐
│                      /fix 执行流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 解析输入                                                │
│     ├── 有 --review？→ 读取审查报告                         │
│     └── 无 --review？→ 扫描代码查找问题                     │
│                                                             │
│  2. 激活 systematic-debugging Skill                        │
│     └── 按 4+1 阶段分析每个问题                             │
│                                                             │
│  3. 调用 issue-fixer Agent                                 │
│     ├── 分类问题（CRITICAL/IMPORTANT/SUGGESTION）           │
│     ├── 根因分析                                            │
│     ├── TDD 修复                                           │
│     └── 验证修复                                            │
│                                                             │
│  4. 如果 --loop                                            │
│     ├── 重新运行审查                                        │
│     ├── 有新问题？→ 回到步骤 3                              │
│     ├── 全部通过？→ 完成                                   │
│     └── 超过 max-rounds？→ 停止，人工干预                   │
│                                                             │
│  5. 输出修复报告                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 验证循环机制

当使用 `--loop` 参数时，命令会自动进入验证循环：

```bash
# 验证循环伪代码
round = 0
while round < max_rounds:
    # 修复当前问题
    fix_result = issue_fixer.fix(issues)
    
    # 重新运行审查
    review_result = run_reviewers(code_path, prd)
    
    # 检查结果
    if review_result.all_pass:
        print("✅ 所有审查通过！")
        exit(0)
    
    if fix_result.no_progress:
        print("⚠️ 无进展，需要人工干预")
        exit(1)
    
    round += 1

print("⚠️ 达到最大轮数，需要人工干预")
exit(1)
```

### 断路器条件

验证循环会在以下情况下自动停止：

| 条件 | 行为 |
|------|------|
| 所有审查通过 | ✅ 成功退出 |
| 达到 max-rounds | ⚠️ 停止，人工干预 |
| 连续 3 轮无文件更改 | ⚠️ 无进展，停止 |
| 连续 5 轮相同错误 | ⚠️ 可能死循环，停止 |
| 成本超过阈值 | ⚠️ 资源保护，停止 |

## 示例场景

### 场景 1：修复审查反馈

```bash
# 收到 code-reviewer 的报告
/fix --review docs/reviews/auth-review.md

# 输出
# 🔍 读取审查报告...
# 📋 发现 2 个 CRITICAL，3 个 IMPORTANT 问题
# 🔧 开始修复 CRITICAL 问题...
# ✅ Issue 1/2 修复完成
# ✅ Issue 2/2 修复完成
# 🔧 开始修复 IMPORTANT 问题...
# ...
```

### 场景 2：验证循环

```bash
# 启动自动修复循环
/fix --loop src/auth/ --prd docs/prd/auth.md --max-rounds 3

# 输出
# 🔄 Round 1/3
#   🔍 运行审查...
#   📋 发现 1 个 CRITICAL 问题
#   🔧 修复中...
#   ✅ 修复完成
# 
# 🔄 Round 2/3
#   🔍 运行审查...
#   📋 发现 0 个 CRITICAL，1 个 IMPORTANT 问题
#   🔧 修复中...
#   ✅ 修复完成
#
# 🔄 Round 3/3
#   🔍 运行审查...
#   ✅ 所有审查通过！
#
# 📊 修复报告
#   总轮数: 3
#   修复问题: 2
#   新增测试: 3
#   修改文件: 4
```

### 场景 3：只修复关键问题

```bash
# 只修复 CRITICAL 问题（快速迭代时）
/fix --priority critical src/

# 输出
# 📋 过滤问题：只处理 CRITICAL
# 🔧 发现 1 个 CRITICAL 问题
# ...
```

## 与其他命令的关系

```
┌─────────────────────────────────────────────────────────────┐
│                       命令流程                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  /review          /accept           /fix                   │
│     │                │                │                     │
│     ▼                ▼                ▼                     │
│  代码审查 ───────▶ 验收审查 ───────▶ 问题修复               │
│     │                │                │                     │
│     │                │                │                     │
│     └────────────────┴────────────────┘                     │
│                      │                                      │
│                      ▼                                      │
│              /fix --loop（自动循环）                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 注意事项

1. **始终使用 TDD**：即使赶时间，也不要用 `--no-tdd`
2. **合理设置 max-rounds**：太小可能修不完，太大可能浪费资源
3. **关注断路器**：如果触发断路器，说明问题可能需要人工介入
4. **保留审查报告**：方便追溯修复历史

## 错误处理

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| "No review report found" | 未指定 --review 且无法自动检测 | 手动指定审查报告路径 |
| "Circuit breaker triggered" | 修复陷入循环 | 人工分析问题，可能需要重构 |
| "TDD validation failed" | 修复没有对应测试 | 确保每个修复都有测试覆盖 |
| "Max rounds exceeded" | 问题太多或太复杂 | 增加 max-rounds 或人工处理 |
