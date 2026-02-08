# Adversarial Debugger

**Agent Teams 驱动的对抗式调试插件** - 让多个 AI agent 像科学家一样辩论 bug 的根因。

## Why?

单 agent 调试有一个根本性缺陷：**锚定效应**。

一旦找到一个看似合理的解释，agent 就会停止调查——即使真正的根因是别的东西。这就像只让一个侦探调查案件，他很可能过早锁定嫌疑人。

Adversarial Debugging 的解决方案：**让多个 agent 并行调查不同假设，然后相互挑战。**

```
传统调试:
  Agent → 假设 A → 调查 → "找到了!" (可能是错的)

对抗式调试:
  Agent-1 → 假设 A → 调查 → 报告证据 ─┐
  Agent-2 → 假设 B → 调查 → 报告证据 ─┤→ 辩论 → 根因
  Agent-3 → 假设 C → 调查 → 报告证据 ─┤
  Devil's Advocate → 挑战所有假设 ──────┤
  Synthesizer → 综合证据 → 最终判定 ────┘
```

## Features

- **Agent Teams**: 利用 Claude Code 的 Agent Teams 功能并行协作
- **假设竞争**: 多个调查员同时调查不同假设
- **Devil's Advocate**: 专职挑战者确保假设经过严格检验
- **证据综合**: 中立仲裁者跟踪所有证据并产出共识判定
- **结构化辩论**: 2-3 轮辩论，有明确的收敛条件
- **TDD 修复**: 定位根因后使用 TDD 方式修复

## Prerequisites

需要启用 Agent Teams 实验性功能：

```json
// settings.json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

## Quick Start

```bash
# 遇到复杂 bug 时
/adversarial-debugging

# 或描述问题
"用对抗式调试帮我找出这个间歇性崩溃的根因"
```

## How It Works

### Phase 0: Problem Intake
收集完整的问题信息：错误消息、复现步骤、环境信息。

### Phase 1: Hypothesis Generation
Lead 分析问题，生成 3-5 个相互独立、可证伪的假设。

### Phase 2: Team Assembly
自动创建 Agent Team：
- **Hypothesis Investigators** (x3-5): 每个假设一个调查员
- **Devil's Advocate** (x1): 挑战所有假设
- **Evidence Synthesizer** (x1): 综合证据，产出判定

### Phase 3: Adversarial Debate
结构化辩论，每轮包含：调查 → 报告 → 挑战 → 回应 → 综合

### Phase 4: Verdict & Fix
Evidence Synthesizer 产出根因判定，Lead 使用 TDD 实施修复。

## Plugin Structure

```
adversarial-debugger/
├── .claude-plugin/
│   └── plugin.json                 # Plugin manifest
├── agents/
│   ├── hypothesis-investigator.md  # Investigator agent (multi-instance)
│   ├── devils-advocate.md          # Challenger agent
│   └── evidence-synthesizer.md     # Synthesizer agent
├── skills/
│   └── adversarial-debugging/
│       └── SKILL.md                # Main orchestration skill
├── rules/
│   └── debate-protocol.md          # Debate rules for all agents
├── README.md
└── LICENSE
```

## When to Use

| Scenario | Use This? |
|----------|-----------|
| 原因明显的 bug | No - 直接修复 |
| 常规 bug，能逐步定位 | No - 用 systematic-debugging |
| 复杂 bug，多个可能根因 | **Yes** |
| 间歇性故障 | **Yes** |
| systematic-debugging 失败后 | **Yes** |
| 跨层级的问题 | **Yes** |

## Cost Considerations

对抗式调试使用多个 agent 并行工作，token 消耗较高：
- 3 个假设: ~5-7 个 agent sessions
- 5 个假设: ~7-9 个 agent sessions

建议在单 agent 调试无法解决时使用。

## License

MIT
