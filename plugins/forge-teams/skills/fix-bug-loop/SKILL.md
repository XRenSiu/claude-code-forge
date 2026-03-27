---
name: forge-fix
description: >
  独立 bug 修复入口。描述 bug → 对抗调试定位根因 → TDD 修复 → 独立验证 → 循环直到修好。
  支持快速路径（简单 bug 直接修）和三层迭代控制（Fixer→Advisor→Replanner）。
  Use when: (1) 已知 bug 需要快速修复, (2) 不想走完整 pipeline, (3) 间歇性故障需要对抗调试。
  Triggers: "forge fix", "fix this bug", "修复这个bug", "帮我修", "fix bug loop"
argument-hint: <bug-description> [--loop N] [--quick] [--team-size <small|medium|large>]
when_to_use: |
  - 已知 bug 需要独立修复入口
  - 不想走完整 7 阶段流水线
  - 间歇性故障需要对抗调试
  - 简单 bug 需要快速修复路径
  - 用户明确请求 bug 修复
version: 1.0.0
disable-model-invocation: true
---

# Forge Fix - 独立 Bug 修复

**描述 bug → 对抗调试定位根因 → TDD 修复 → 独立验证 → 循环直到修好。**

这是 forge-teams 的独立 bug 修复入口。复用已有的对抗调试引擎（hypothesis-investigator、devils-advocate、evidence-synthesizer、issue-fixer），但提供独立编排、快速路径分流和三层迭代控制。

Announce at start: "I'm using the forge-fix skill to create an agent team that will locate and fix this bug through adversarial debugging and TDD."

> **前置条件**: 需要启用 Agent Teams 实验性功能。
> 在 settings.json 中添加: `"env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" }`

## 用法

```bash
/forge-fix <bug-description> [options]
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `<bug-description>` | bug 描述（文本、文件路径、或错误日志） | 必填 |
| `--loop <N>` | 最大修复-验证循环次数 | `3` |
| `--quick` | 快速路径：跳过对抗调试，直接用 issue-fixer 修复（适用于简单 bug） | 不启用 |
| `--team-size <size>` | 假设调查团队规模（small=3 假设, medium=4, large=5） | `medium` |
| `--no-verify` | 修复后跳过独立验证（不推荐） | 启用验证 |

## 示例

```bash
# 直接描述 bug
/forge-fix "支付回调间歇性超时，大约每10次失败2次"

# 简单 bug，快速路径
/forge-fix "登录页面 CSS 错位" --quick

# 复杂 bug，加大团队 + 增加循环
/forge-fix "高并发下 Redis 连接池泄漏" --team-size large --loop 5

# 从错误日志修复
/forge-fix "npm test 报错: TypeError: Cannot read property 'id' of undefined at src/user.ts:42"
```

## 输出目录

```
docs/forge-fix/
└── [bug-slug]-[timestamp]/
    ├── intake.md              # 问题信息收集
    ├── hypotheses.md          # 假设列表（非 quick 模式）
    ├── debate-log.md          # 对抗辩论记录（非 quick 模式）
    ├── verdict.md             # 根因判定
    ├── fix-report.md          # TDD 修复报告
    ├── verification.md        # 独立验证报告
    └── summary.md             # 最终修复摘要
```

---

## Quick vs Full Path Decision (快速路径分流)

```
用户描述 bug
    │
    ├── --quick 指定 → 快速路径
    │
    └── 未指定 → Lead 评估复杂度
        │
        ├── 简单信号 → 建议快速路径（用户确认）
        │   - 单文件、单函数问题
        │   - 错误信息直接指向根因（如 TypeError at file:line）
        │   - 纯 UI/CSS 问题
        │   - typo 或明显逻辑错误
        │
        └── 复杂信号 → 完整对抗调试路径
            - 间歇性故障
            - 多个可能根因
            - 涉及并发/状态/竞态
            - 跨模块/跨服务
            - "时有时无"、"偶尔"、"不稳定"
```

---

## Quick Path (快速路径)

适用于简单、根因明显的 bug。不组建对抗 team，直接定位修复。

```
┌─────────────────────────────────────────────────────────┐
│                    QUICK PATH                             │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Step 1: INTAKE          收集 bug 信息                    │
│          ↓               错误信息 + 代码位置               │
│                                                           │
│  Step 2: LOCATE          定位根因                         │
│          ↓               Lead 直接分析（不组 team）        │
│                                                           │
│  Step 3: TDD FIX         issue-fixer 修复                 │
│          ↓               RED → GREEN → VERIFY             │
│                                                           │
│  Step 4: VERIFY          独立验证                         │
│                          quality-sentinel 交叉验证         │
│                                                           │
│  [LOOP]: 失败 → 回到 Step 2（最多 N 轮）                  │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### Quick Path 执行

**Step 1: Intake**

收集基本 bug 信息：

```bash
# 获取错误信息
npm test 2>&1 | tail -30

# 查看最近变更
git log --oneline -10
git diff HEAD~3

# 环境信息
node -v && npm -v
```

**Step 2: Locate**

Lead 直接分析根因（不 spawn team）：
- 读取错误指向的文件
- 追踪调用链
- 确定根因位置

**Step 3: TDD Fix**

Spawn issue-fixer：

```
Agent (spawn):
  subagent_type: "forge-teams:issue-fixer"
  name: "issue-fixer"
  prompt: |
    Root Cause: [Lead 分析的根因]
    Location: [file:line]
    Fix Direction: [修复方向]

    执行 TDD 修复：复现测试(RED) → 最小修复(GREEN) → 回归验证(VERIFY)
```

**Step 4: Verify**

Spawn 独立验证 agent（quality-sentinel）在全新上下文中：
1. 读取 bug 描述
2. 读取修复 diff
3. 独立判断修复是否解决问题
4. 运行完整测试套件

---

## Full Path (完整对抗调试路径)

适用于复杂 bug。组建对抗调试 team，假设竞争 + Devil's Advocate 挑战。

```
┌─────────────────────────────────────────────────────────────────┐
│                       FULL PATH                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Phase 0: INTAKE           收集完整问题信息                       │
│           ↓                                                       │
│                                                                   │
│  Phase 1: HYPOTHESIZE      生成 3-5 个竞争假设                    │
│           ↓                                                       │
│                                                                   │
│  Phase 2: TEAM ASSEMBLY    Investigators + DA + Synthesizer       │
│           ↓                                                       │
│                                                                   │
│  Phase 3: DEBATE           2-3 轮对抗辩论                         │
│           ↓                收敛: >=8/10 或领先>=3 或 3轮后        │
│                                                                   │
│  Phase 4: VERDICT & FIX    根因判定 → TDD 修复                    │
│           ↓                                                       │
│                                                                   │
│  Phase 5: INDEPENDENT      独立验证 agent 交叉确认                │
│           VERIFY                                                  │
│                                                                   │
│  [3-LAYER LOOP]:                                                  │
│    Inner: Fixer 重试 (max 5)                                      │
│    Middle: Advisor 策略调整 (max 3)                                │
│    Outer: Replanner 重新理解 (max 2)                               │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 0: Problem Intake (信息收集)

**目的**: 收集足够信息以生成高质量假设。

必须收集的信息（同 adversarial-debugging 的 Phase 0）：

- [ ] **确切错误信息**: 完整的错误输出/堆栈跟踪
- [ ] **复现步骤**: 如何可靠地重现问题？
- [ ] **预期行为 vs 实际行为**: 应该发生什么？实际发生了什么？
- [ ] **最近更改**: 问题出现前改了什么？
- [ ] **环境信息**: 版本、操作系统、依赖版本
- [ ] **频率和模式**: 总是出现？偶尔？特定条件下？

```bash
# 自动收集信息
npm test 2>&1 | tee /tmp/error.log
git log --oneline -10
git diff HEAD~5
node -v && npm -v
```

**如果关键信息不足，停下来向用户提问，不进入 Phase 1。**

### Phase 1-3: Adversarial Debugging (对抗调试)

**直接复用 adversarial-debugging skill 的 Phase 1-3 协议**：

1. **假设生成**: 3-5 个独立、可证伪假设（team-size 控制数量）
2. **Team 组建**: N investigators + Devil's Advocate + Evidence Synthesizer
3. **对抗辩论**: 2-3 轮 INVESTIGATE → REPORT → CHALLENGE → RESPOND → SYNTHESIZE

团队规模映射：
| team-size | 假设数 | Investigators | DA | Synthesizer | 总计 |
|-----------|--------|---------------|-----|-------------|------|
| small | 3 | 3 | 1 | 1 | 5 |
| medium | 4 | 4 | 1 | 1 | 6 |
| large | 5 | 5 | 1 | 1 | 7 |

收敛条件（同 adversarial-debugging）：
- **强收敛**: 一个假设 >= 8/10 且所有挑战已回应
- **弱收敛**: 一个假设明显领先 (>= 3 分差)
- **强制收敛**: 3 轮后选择最强假设

### Phase 4: Verdict & TDD Fix

从 Evidence Synthesizer 收集根因判定后，spawn issue-fixer 执行 TDD 修复：

```
Agent (spawn):
  subagent_type: "forge-teams:issue-fixer"
  name: "issue-fixer"
  prompt: |
    ## Verdict
    Root Cause: [根因描述]
    Location: [file:line]
    Fix Direction: [修复方向]
    Risk Areas: [风险点]

    ## Bug Context
    [Phase 0 收集的完整信息]

    执行 TDD 修复：
    1. 写复现测试 (RED)
    2. 实施最小修复 (GREEN)
    3. 全套件回归验证 (VERIFY)
```

### Phase 5: Independent Verification (独立验证)

**核心增强**: 修复完成后 spawn 一个独立验证 agent，在全新上下文中验证修复质量。

```
Agent (spawn):
  subagent_type: "forge-teams:quality-sentinel"
  name: "fix-verifier"
  prompt: |
    你是本次修复的独立验证者。在全新上下文中验证修复质量。

    ## Bug Description
    [原始 bug 描述]

    ## Fix Applied
    [修复 diff / commit 信息]

    ## Verification Checklist
    1. 读取 bug 描述，理解原始问题
    2. 读取修复 diff，理解修改内容
    3. 判断：修复是否真的解决了问题？
    4. 判断：修复是否引入新问题？
    5. 运行完整测试套件
    6. 检查修复范围是否最小化

    ## Output
    Verdict: VERIFIED / NEEDS_REWORK / NEW_ISSUES
    Details: [具体说明]
```

---

## Three-Layer Iteration Control (三层迭代控制)

```
外层 (Replanner) — 最多 2 轮
├── 中层 (Advisor) — 最多 3 轮
│   ├── 内层 (Fixer) — 最多 5 轮
│   │   ├── TDD Fix (issue-fixer)
│   │   ├── Independent Verify (quality-sentinel)
│   │   ├── 通过 → 提交 ✅
│   │   └── 失败 → 更新上下文 → 重试
│   └── 连续内层失败 → Advisor 介入
│       ├── RETRY_MODIFIED: 换修复思路
│       ├── SPLIT: 拆成多个子问题
│       ├── ACCEPT_WITH_DEBT: 记录技术债跳过
│       └── ESCALATE: 升级到外层
└── 外层接管
    ├── 重新理解问题（回到 Phase 0 重新收集信息）
    └── 放弃 + 输出详细失败报告
```

### 内层: Fixer Loop

每次内层循环：
1. issue-fixer 执行 TDD 修复
2. quality-sentinel 独立验证
3. 通过 → 完成
4. 失败 → 更新失败上下文（为什么失败、哪里不对）→ issue-fixer 重试

**最大内层轮次**: min(5, `--loop N`) 次

### 中层: Advisor Decision

当内层连续失败 2 次时，Lead 作为 Advisor 介入评估：

| 策略 | 触发条件 | 动作 |
|------|---------|------|
| **RETRY_MODIFIED** | 修复方向正确但细节有误 | 更新修复指导，重进内层 |
| **SPLIT** | 发现是多个独立子问题 | 拆分为多个 fix task，逐个修复 |
| **ACCEPT_WITH_DEBT** | 问题非关键且修复成本过高 | 记录技术债，标记为已知问题，跳过 |
| **ESCALATE** | 根因判定可能有误 | 升级到外层重新理解问题 |

### 外层: Replanner

当中层 ESCALATE 时：
1. 重新审视所有失败上下文
2. 回到 Phase 0 重新收集信息（可能有新的线索）
3. 重新生成假设并组建对抗调试团队
4. 如果第二轮外层仍然失败 → 放弃，输出详细失败报告

### Circuit Breaker (断路器)

**总循环上限**: `--loop N`（默认 3）跨越所有层级。无论处于哪一层，达到总上限后立即停止。

断路器触发时输出：
```markdown
# Fix Bug Loop 断路器触发

## 已尝试
- 总循环次数: N
- 内层修复尝试: X
- Advisor 介入: Y
- Replanner 重启: Z

## 失败原因分析
[每次尝试的失败原因汇总]

## 建议
1. [人工排查方向 A]
2. [人工排查方向 B]
3. [可能需要更多信息]

## 已收集的所有证据
[假设列表、辩论记录、修复尝试、验证结果]
```

---

## State Management (状态管理)

输出目录：`docs/forge-fix/[bug-slug]-[timestamp]/`

```json
{
  "bug_description": "...",
  "timestamp": "20260327-103000",
  "mode": "full",
  "team_size": "medium",
  "loop_max": 3,
  "loop_current": 0,
  "status": "in_progress",
  "phases": {
    "intake": { "status": "completed" },
    "hypothesize": { "status": "completed" },
    "debate": { "status": "in_progress" },
    "verdict": { "status": "pending" },
    "fix": { "status": "pending" },
    "verify": { "status": "pending" }
  },
  "iteration": {
    "inner_attempts": 0,
    "advisor_interventions": 0,
    "replanner_restarts": 0
  },
  "artifacts": {
    "intake": "intake.md",
    "hypotheses": "hypotheses.md",
    "debate_log": "debate-log.md",
    "verdict": "verdict.md",
    "fix_report": "fix-report.md",
    "verification": "verification.md"
  }
}
```

---

## Incremental Write Rule (增量写入规则)

遵循 forge-teams 的增量写入原则——每个 agent 输出在 Lead 收到后**立即**写入文件：

| 阶段 | 写入文件 | 时机 |
|------|---------|------|
| Phase 0 | `intake.md` | 信息收集完成后 |
| Phase 1 | `hypotheses.md` | 假设生成后 |
| Phase 3 | `debate-log.md` | 每轮辩论后追加 |
| Phase 4 | `verdict.md` | 根因判定后 |
| Phase 4 | `fix-report.md` | TDD 修复完成后 |
| Phase 5 | `verification.md` | 独立验证完成后 |
| 最终 | `summary.md` | pipeline 结束时 |

---

## Team Cleanup Protocol (团队清理)

每次循环结束（无论成功失败），Lead 必须清理团队：

```
1. SendMessage shutdown_request → 所有活跃 agent
2. 等待确认
3. TeamDelete
```

新循环开始时重新 TeamCreate。

---

## Output Format (最终输出)

修复成功时：

```markdown
# Bug Fix Report

## Bug
**Description**: [原始 bug 描述]
**Root Cause**: [根因判定]
**Confidence**: X/10

## Fix
**Files Modified**: [文件列表]
**Approach**: [修复方法]
**Commit**: [commit hash]

## Verification
**Independent Verifier**: VERIFIED ✅
**Full Test Suite**: PASS (N tests)
**Regression**: None detected

## Process
- Path: Quick / Full (对抗调试)
- Hypotheses Investigated: N
- Debate Rounds: M
- Fix Attempts: K
- Total Loop Iterations: L
```

---

## Anti-patterns

| 坏行为 | 为什么失败 | 正确做法 |
|--------|-----------|---------|
| 复杂 bug 走快速路径 | 单线程分析容易锚定 | 评估复杂度，复杂 bug 走对抗调试 |
| 跳过独立验证 | 修复者自己验证有偏差 | 始终 spawn 独立验证 agent |
| 循环不收敛就死循环 | 浪费资源 | 断路器 + 三层升级 |
| 不记录失败上下文 | 下一轮重复同样错误 | 每次失败更新上下文传给下一轮 |
| Advisor 总选 RETRY | 没有根本改变策略 | 2 次相同策略失败后 ESCALATE |
| 不清理 Team | 资源泄漏 | 每轮结束 shutdown + TeamDelete |

---

## Core Principle

> **"Not every bug needs a team. But every team needs a plan B."**
>
> 不是每个 bug 都需要组建对抗 team。但每个对抗 team 都需要 Plan B。
> 简单问题用简单方案，复杂问题用对抗方案——关键是知道什么时候该升级。
