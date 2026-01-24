# Manus Context Engineering 原理

> 参考来源：Manus AI（被 Meta 以 20 亿美元收购）的 Context Engineering 实践

## 核心洞察

### 1. Context Window 是稀缺资源

```
Context Window = RAM（易失、有限、昂贵）
Filesystem = Disk（持久、无限、便宜）
```

**含义**：
- 能外部化的信息就外部化到文件
- Context 中只保留「指针」和关键决策信息
- 文件系统是「工作记忆磁盘」

### 2. Lost in the Middle 效应

LLM 对 context window 中间的内容注意力较弱。

```
┌─────────────────────────────────────┐
│ [原始目标 - 在开头，容易被遗忘]      │  ← 开始
│ ...                                  │
│ [50+ 工具调用]                       │  ← 中间（注意力最弱）
│ ...                                  │
│ [刚读取的 task_plan.md - 获得注意力!] │  ← 末端（注意力最强）
└─────────────────────────────────────┘
```

**解决方案**：
- 频繁重读 task_plan.md
- 将目标推到 context 末端
- 末端内容获得更多「注意力」

### 3. 错误是学习材料

传统做法：出错后重试，不留痕迹
正确做法：保留错误记录，让模型「看到」失败

**为什么有效**：
- 失败信息隐式更新模型的「先验」
- 看到之前的错误会避免重复
- 错误追踪是真正 agentic 行为的关键指标

### 4. Pattern Mimicry（模式模仿）问题

LLM 会模仿 context 中的模式，导致：
- 重复相同的失败行为
- 陷入「动作-观察」循环

**解决方案**：
- 引入结构化变化打破重复模式
- 保留错误让模型「看到」不应该重复的行为

## 三文件系统设计

### task_plan.md

**目的**：追踪目标、阶段、决策、错误

**为什么需要**：
- 防止目标漂移（50+ 调用后忘记原始目标）
- 记录决策（为什么选择 A 而不是 B）
- 追踪错误（避免重复同样的失败）

### findings.md

**目的**：存储研究发现和技术笔记

**为什么需要**：
- 防止信息只存在于 context 中然后丢失
- 为 context 减负（详细内容外部化）
- 跨会话保留发现

### progress.md

**目的**：会话日志和测试结果

**为什么需要**：
- 追踪执行历史
- 记录测试结果
- 支持会话恢复

## 关键规则

### 5 次规则

每执行 5 次工具调用后，重读 task_plan.md。

**原理**：
- 将目标推到 context 末端
- 防止 Lost in the Middle
- 保持对原始目标的注意力

### 2-Action 规则

每 2 次 view/browser 操作后，保存到 findings.md。

**原理**：
- 强制外部化发现
- 防止信息只存在于 context
- 为 context 减负

### 会话恢复的 5 问检查

1. 我在做什么？ → 读 task_plan.md Goal
2. 我做到哪了？ → 读 task_plan.md Phases
3. 我学到了什么？ → 读 findings.md
4. 什么失败过？ → 读 task_plan.md Errors
5. 下一步是什么？ → 读当前阶段

## Context 压缩策略

当 context 接近限制时：

1. **保持最近的工具调用完整**
2. **旧结果只保留引用/路径**
3. **总结过长的历史**

```
压缩层级：
Raw（原始）> Compaction（压缩）> Summarization（总结）
```

## Manus 的后续优化

Manus 在实践中发现：
- 使用 todo.md 规划时，约 33% 的 actions 用于更新它
- 后来改用专门的 Planner Sub-agent 来优化

**对我们的启示**：
- 规划文件的维护有成本
- 但这个成本换来的是：目标不漂移、错误不重复、信息不丢失
- 在当前阶段，这个 trade-off 是值得的

## 参考资料

1. [Manus Context Engineering Blog](https://manus.ai/blog/context-engineering)
2. [Lance Martin 的 Manus 架构分析](https://blog.langchain.dev/manus-architecture/)
3. [Lost in the Middle 论文](https://arxiv.org/abs/2307.03172)
