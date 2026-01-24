---
name: planning-with-files
description: >
  Manus 风格的持久化 Markdown 规划系统，用于复杂多步骤任务。
  Use when: (1) 任务超过 3 步, (2) 研究需要多个来源, (3) 任务跨越多个会话,
  (4) 需要追踪错误和决策, (5) 容易忘记原始目标。
  Examples: "帮我实现这个功能", "研究一下 X", "这个 bug 怎么修", "重构这段代码"
allowed-tools: Bash, Read, Write, Edit
user-invocable: true
hooks:
  PreToolUse:
    - matcher: "Write|Edit|Bash"
      hooks:
        - type: prompt
          prompt: |
            检查距上次读取 task_plan.md 已执行多少次工具调用。
            如果 >= 5 次，先重读 task_plan.md 刷新目标。
            如果命令包含 rm/delete/drop，返回 permissionDecision: "ask"
            【会话开始时】如果项目目录存在 task_plan.md，执行会话恢复：读取三个文件重建上下文。
  PostToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: prompt
          prompt: "文件已修改。如果完成了某个阶段，更新 task_plan.md 状态。"
    - matcher: "Read|Bash"
      hooks:
        - type: prompt
          prompt: |
            2-Action Rule: 检查自上次保存后执行了多少次 view/browser 操作。
            如果 >= 2 次，必须将发现保存到 findings.md。
  Stop:
    - matcher: "*"
      hooks:
        - type: command
          command: "./scripts/check-complete.sh"
version: 2.0.0
---

# Planning with Files

## 核心原则

```
Context Window = RAM（易失、有限、昂贵）
Filesystem = Disk（持久、无限、便宜）

→ 重要信息写入磁盘，频繁重读保持注意力
→ 错误保留让模型学习，不要隐藏失败
```

## 三文件系统

| 文件 | 用途 | 更新时机 |
|------|------|----------|
| `task_plan.md` | 目标、阶段、决策、错误 | 阶段完成时、做决策时、遇到错误时 |
| `findings.md` | 研究发现、技术笔记 | 每 2 次 view/browser 后必须更新 |
| `progress.md` | 会话日志、测试结果 | 开始/结束阶段时、运行测试后 |

## 流程

### 启动任务

1. **判断任务类型**，选择模板：
   - 研究型 → `templates/task_plan_research.md`
   - 编码型 → `templates/task_plan_coding.md`
   - 调试型 → `templates/task_plan_debug.md`
   - 通用型 → `templates/task_plan.md`

2. **在项目目录创建三个文件**（不是 skill 目录）：
   ```bash
   cp ~/.claude/skills/planning-with-files/templates/task_plan.md ./task_plan.md
   cp ~/.claude/skills/planning-with-files/templates/findings.md ./findings.md
   cp ~/.claude/skills/planning-with-files/templates/progress.md ./progress.md
   ```

3. **填写 task_plan.md 的 Goal 部分**

### 执行中

**5 次规则**：每执行 5 次工具调用后，重读 task_plan.md
- 将目标推到 context 末端，获得更多注意力
- 防止「Lost in the Middle」效应

**2-Action 规则**：每 2 次 view/browser 操作后，保存到 findings.md
- 防止信息只存在于 context 中然后丢失
- 强制外部化发现

**错误追踪**：遇到错误立即记录到 task_plan.md 的 Errors 部分
- 保留失败让模型「看到」
- 避免重复同样错误

### 会话恢复（5 问检查）

当 context 被清空或新会话开始时，回答这 5 个问题：

1. **我在做什么？** → 读 task_plan.md 的 Goal
2. **我做到哪了？** → 读 task_plan.md 的 Phases（找 CURRENT 标记）
3. **我学到了什么？** → 读 findings.md
4. **什么失败过？** → 读 task_plan.md 的 Errors
5. **下一步是什么？** → 读 task_plan.md 的当前阶段

### 上下文压缩（当接近限制时）

1. 将详细工具结果替换为文件路径
2. 已完成阶段压缩为单行摘要
3. 只保留最近 3 次工具结果的完整内容
4. 其他信息确保已保存到三个文件中

### 完成任务

1. 确认所有阶段标记为 `[x]`
2. 确认 findings.md 包含所有重要发现
3. 更新 progress.md 的最终状态
4. Stop hook 会自动验证

## 反模式

| 坏行为 | 为什么失败 | 正确做法 |
|--------|-----------|---------|
| 不创建计划直接开始 | 50+ 调用后忘记目标 | 必须先创建 task_plan.md |
| 信息只放 context | context 清空后丢失 | 写入文件系统 |
| 删除/隐藏错误 | 模型会重复错误 | 保留错误记录 |
| 长时间不重读计划 | 目标漂移 | 每 5 次调用重读 |
| 研究后不保存发现 | 信息丢失 | 每 2 次操作保存 |
| 在 skill 目录创建文件 | 文件位置错误 | 在项目目录创建 |

## 你可能想跳过这个流程

| 借口 | 反驳 |
|------|------|
| 「任务很简单」 | 简单任务更容易忘记细节 |
| 「我记得目标」 | 50 次调用后你不会记得 |
| 「写文件太慢」 | 重做比多花 30 秒更慢 |
| 「这次是特例」 | 没有特例，规则就是规则 |
| 「用户很急」 | 目标漂移导致的返工更浪费时间 |

**如果任务超过 3 步，必须使用此系统。没有例外。**

## 资源

- `templates/` - 不同任务类型的计划模板
- `scripts/init-session.sh` - 会话初始化和恢复
- `scripts/check-complete.sh` - 完成验证
- `references/manus-principles.md` - Manus Context Engineering 原理
