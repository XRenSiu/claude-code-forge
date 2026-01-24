# Subagent 创建准则

> PDForge 最佳实践总结

---

## 一、什么是 Subagent？

**本质**：一个独立的 AI 实例，拥有全新的上下文，不继承父对话的任何历史。

**比喻**：你请来的**外部专家**。他不知道你之前做了什么、想了什么，只看到你给他的材料，给出独立判断。

```
┌─────────────────────────────────────┐
│           Main Agent                │
│  (有完整的对话历史和项目上下文)       │
│                                     │
│    dispatch("code-reviewer", {      │
│      CODE_PATH: "src/auth/",        │
│      PLAN_DOC: "docs/plan.md"       │
│    })                               │
│         │                           │
│         ▼                           │
│  ┌─────────────────────────────┐    │
│  │     Subagent (新上下文)      │    │
│  │  只看到传入的参数            │    │
│  │  独立执行，返回结果          │    │
│  └─────────────────────────────┘    │
│         │                           │
│         ▼                           │
│    收到结构化结果                    │
└─────────────────────────────────────┘
```

---

## 二、何时使用 Subagent？

### 核心判断标准

| 问题 | 是 → Subagent |
|------|---------------|
| 需要"不知道实现过程"的客观视角吗？ | ✅ |
| 任务有清晰的输入/输出边界吗？ | ✅ |
| 希望模拟"另一个人"来做这件事吗？ | ✅ |
| 需要"新鲜眼睛"独立评估吗？ | ✅ |

### 典型使用场景

| 场景 | 原因 |
|------|------|
| **Code Review** | 审查者不应知道实现者的"心路历程"，避免自己给自己放水 |
| **Security Audit** | 需要"攻击者视角"，与开发者视角不同 |
| **Test Generation** | 测试应基于规格而非实现，避免写出"验证实现"的测试 |
| **Documentation** | 文档写给"不知道代码的人"看，需模拟读者视角 |
| **Spec Compliance** | 严格对照规格，不接受"差不多就行" |
| **Performance Analysis** | 需要客观度量，不受主观影响 |

---

## 三、Subagent 文件结构

```markdown
---
name: agent-name
description: [角色定位]. [触发条件]. [核心价值].
tools: Tool1, Tool2, Tool3
model: inherit
---

# 1. 角色设定（简短有力）
# 2. 触发场景（使用 <examples>）
# 3. 输入规范
# 4. 执行逻辑
# 5. 输出格式
# 6. 核心原则
```

---

## 四、Frontmatter 编写准则

### 4.1 Name（名称）

```yaml
# ✅ 好的命名
name: code-reviewer
name: security-auditor
name: test-generator

# ❌ 避免的命名
name: CodeReviewer      # 不要用驼峰
name: code_reviewer     # 不要用下划线
name: reviewer          # 太模糊
```

**准则**：
- 使用 `kebab-case`（小写+连字符）
- 名称应直接表明职责
- 2-3 个单词最佳

### 4.2 Description（描述）⭐ 关键

Description 是 Claude 决定是否调用这个 Subagent 的关键依据。

```yaml
# ✅ 好的描述（三段式）
description: Senior Engineer code reviewer. Invoke after completing a plan step or before merging PRs. Validates against plan documents and catches bugs before production.
#            ↑ 角色定位              ↑ 触发条件                                        ↑ 核心价值

# ❌ 差的描述
description: Reviews code.  # 太模糊，不知道何时调用
description: A helpful agent that can review your code and provide feedback...  # 太啰嗦
```

**描述三要素**：
1. **角色定位**：这是什么级别/类型的专家
2. **触发条件**：什么情况下应该调用
3. **核心价值**：调用它能得到什么

### 4.3 Tools（工具）

```yaml
# 只读审查类
tools: Read, Grep, Glob

# 需要执行检测命令
tools: Read, Grep, Glob, Bash

# 需要修改文件
tools: Read, Write, Edit, Bash
```

**准则**：
- **最小权限原则**：只给必要的工具
- 审查类 Subagent 通常**不需要 Write/Edit**
- 如果需要执行检测命令，必须给 Bash

### 4.4 Model（模型）

```yaml
model: inherit     # 继承父 Agent 的模型（推荐）
model: sonnet      # 指定使用 Sonnet
model: opus        # 指定使用 Opus（更智能但更慢）
model: haiku       # 指定使用 Haiku（更快但能力弱）
```

---

## 五、角色设定准则

### 5.1 建立可信度

```markdown
# ✅ 好的角色设定
You are a principal engineer conducting code review with the wisdom of someone who has debugged too many 3am production incidents. You've seen elegant code become unmaintainable, "temporary" hacks last for years, and simple oversights cause catastrophic failures.

# ❌ 差的角色设定
You are a code reviewer. Review the code.
```

**技巧**：
- 使用**具体经历**建立专业形象
- 描述**见过的问题**暗示审查能力
- 传达**审查态度**

### 5.2 明确核心哲学

```markdown
**Core Philosophy**: Review as if you'll be maintaining this code at 3am during an outage.
```

---

## 六、触发场景准则 ⭐ 关键

### 6.1 使用 `<examples>` 标签

```markdown
<examples>
<example>
Context: User completed a step from the implementation plan
user: "I've finished implementing the user authentication system"
assistant: "Let me review the implementation against the plan"
<commentary>Plan step completed → trigger review</commentary>
</example>

<example>
Context: NOT a review scenario
user: "Help me write the authentication module"
assistant: [Does NOT dispatch code-reviewer, proceeds with implementation]
<commentary>Implementation request → NOT a review trigger</commentary>
</example>
</examples>
```

### 6.2 必须包含反例

最后一个 example 展示**什么情况不应该触发**，同样重要。

---

## 七、输入规范准则

### 7.1 定义清晰的输入接口

```markdown
## Input Handling

**必需参数**：
- `CODE_PATH`: 要审查的文件/目录

**推荐参数**：
- `PLAN_DOC`: 计划文档路径
- `STANDARDS`: 编码规范

**可选参数**：
- `BASE_SHA` / `HEAD_SHA`: Git 提交范围
- `FOCUS`: 特定关注领域
```

### 7.2 说明处理逻辑

```markdown
When given paths, **READ THE CODE FIRST**.
When given a plan, **CHECK COMPLIANCE FIRST**.
When given SHA range, **RUN GIT DIFF FIRST**.
```

---

## 八、执行逻辑准则

### 8.1 分层优先级

```markdown
### 🔴 Must Pass (Blocking)
- Correctness
- Security
- Plan Compliance

### 🟡 Should Pass (Important)  
- Maintainability
- Error Handling

### 🟢 Advisory (Suggestions)
- Testing
- Documentation
```

### 8.2 提供检测手段 ⭐ 关键

**这是区分优秀 Subagent 的关键**：

```markdown
#### Type Safety

- [ ] No `any` abuse
- [ ] Minimal type assertions

**Detection Technique**:
```bash
# Find any abuse
grep -rn ": any\|as any" --include="*.ts" | grep -v "test\|spec" | head -20
```
```

---

## 九、输出格式准则

### 9.1 结构化模板

```markdown
## Output Format

```markdown
## Code Review Summary

**Assessment**: 🟢 APPROVE / 🟡 APPROVE WITH CHANGES / 🔴 REQUEST CHANGES
**Risk Level**: Low / Medium / High / Critical

---

## Strengths ✨
- **[Category]**: [Specific praise with file:line]

---

## Critical Issues 🔴 (Must Fix)

### 1. [Issue Title]
**Location**: `file.ts:L42-L58`
**Problem**: [Description]
**Fix**: [Code example]

---

## Action Items
- [ ] Fix critical issue X
- [ ] Address important issue Y
```
```

### 9.2 输出准则

| 准则 | 说明 |
|------|------|
| **先表扬后批评** | 总是以 Strengths 开始 |
| **具体位置** | 精确到 `file:line` |
| **说明原因** | 不只是"这不好"，要说"因为..." |
| **提供修复** | 每个问题附带解决方案 |
| **只输出有内容的部分** | 没有 Critical 就不要空的 Critical 节 |

---

## 十、反馈语气准则

```markdown
## Feedback Tone Guide

| Instead of | Say |
|------------|-----|
| "This is wrong" | "This could cause [issue] because [reason]. Consider [alternative]." |
| "Why did you do this?" | "I'm curious about the reasoning—was there a constraint I'm missing?" |
| "Bad practice" | "This approach can lead to [problem]. A common alternative is [solution]." |
```

---

## 十一、完整示例模板

```markdown
---
name: code-reviewer
description: Senior Engineer code reviewer. Invoke after completing a plan step or before merging PRs. Validates against plan documents and catches bugs.
tools: Read, Grep, Glob, Bash
model: inherit
---

You are a principal engineer with deep experience in production systems.

**Core Philosophy**: Review as if you'll be maintaining this code at 3am during an outage.

## When to Use

<examples>
<example>
Context: User completed a step from the implementation plan
user: "I've finished implementing the user authentication system"
assistant: "Let me review the implementation against the plan"
<commentary>Plan step completed → trigger review</commentary>
</example>
</examples>

## Input Handling

**Required**:
- `CODE_PATH`: Files/directories to review

**Optional**:
- `PLAN_DOC`: Plan document for compliance check

## Review Dimensions

### 🔴 Must Pass
- [ ] Correctness
- [ ] Security

**Detection**:
```bash
grep -rn ": any" --include="*.ts" | head -10
```

### 🟡 Should Pass
- [ ] Maintainability
- [ ] Error Handling

### 🟢 Advisory
- [ ] Documentation

## Output Format

```markdown
**Assessment**: 🟢/🟡/🔴
**Risk Level**: Low/Medium/High

## Strengths ✨
...

## Critical Issues 🔴
...
```

## Feedback Tone

| Instead of | Say |
|------------|-----|
| "This is wrong" | "This could cause [issue]..." |

## Core Principles

1. **Specific over vague**: Point to exact lines
2. **Explain the why**: Not just "don't do X"
3. **Praise genuinely**: Good code deserves recognition
```

---

## 十二、检查清单

### Frontmatter
- [ ] name 使用 kebab-case
- [ ] description 包含角色、触发条件、价值
- [ ] tools 遵循最小权限原则

### 角色设定
- [ ] 有具体的专业形象
- [ ] 明确核心哲学

### 触发场景
- [ ] 使用 `<examples>` 定义
- [ ] 包含反例（什么时候不触发）

### 输入规范
- [ ] 参数定义清晰
- [ ] 有输入示例

### 执行逻辑
- [ ] 检查项分优先级
- [ ] 提供可执行的检测命令

### 输出格式
- [ ] 结构化模板
- [ ] 先表扬后批评
- [ ] 问题附带修复建议

### 反馈语气
- [ ] 建设性而非批判性
- [ ] 有话术对照表

### 长度控制
- [ ] 总长度在 200-400 行
- [ ] 没有重复内容

---

## 十三、常见错误

| 错误 | 问题 | 改进 |
|------|------|------|
| 没有 `<examples>` | Claude 不知道何时调用 | 添加 3-4 个触发场景示例 |
| 只有检查清单没有检测命令 | Subagent 无法主动发现问题 | 每个维度配套检测命令 |
| 输出模板太复杂 | 大量空表格浪费 token | 只输出有内容的部分 |
| 角色设定太弱 | Subagent 没有专业度 | 用具体经历建立可信度 |
| 权限过大 | Write/Edit 可能意外修改代码 | 审查类只给 Read 权限 |
| 没有优先级分层 | 所有问题同等重要 | 使用 🔴/🟡/🟢 分级 |
| 没有正向反馈 | 只批评不表扬 | 始终以 Strengths 开始 |

---

## 总结

**好的 Subagent = 清晰的职责 + 明确的触发 + 可执行的逻辑 + 结构化的输出**

```
┌─────────────────────────────────────────────────────────┐
│  Subagent 设计五要素                                     │
│                                                         │
│  1. 身份 — 我是谁？什么级别的专家？                        │
│  2. 触发 — 什么时候应该叫我？(用 examples 定义)            │
│  3. 输入 — 你要给我什么材料？                             │
│  4. 执行 — 我按什么逻辑工作？(有优先级、有检测手段)         │
│  5. 输出 — 我给你什么格式的结果？(结构化、可解析)           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**核心原则**：Subagent 是"另一个人"，需要客观视角和认知隔离的任务才用它。
