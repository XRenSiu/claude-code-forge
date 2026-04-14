---
name: persona-debate
description: >
  编排 2-5 个已安装的 persona skill 围绕同一问题做结构化辩论，产出真正的多视角对话（而非单 persona 的独白）。
  Use when: (1) 问题需要多视角对照, (2) 用户点名多个 persona 一起聊, (3) 单一 persona 给出的答案过于单薄。
  Triggers: "persona debate", "多 persona 辩论", "debate this question with X, Y, Z", "多视角讨论"
when_to_use: |
  - 用户明确请求多个 persona 同时发言（"让 Jobs / Munger / Naval 一起聊聊这个问题"）
  - 决策类问题，需要对立视角互相挑战
  - 单个 persona 的回答你已经看过，想再加两三个视角做对照
  - 已安装 ≥2 个 persona skill（manifest.json 符合 persona-distill 契约）
  - 不适合：开放闲聊（没有明确问题） / 仅装 1 个 persona / 需要超过 5 个参与者
version: 0.1.0
---

# persona-debate

**一个 persona = 一个视角。debate = 真正的多视角对话。**

大多数 persona skill 被单独调用时只能给出"我（某 persona）会这样想"的独白。但真实世界里的好决策，往往是几位不同背景的人互相挑战之后才浮现的。`persona-debate` 编排 2-5 个已安装 persona skill 围绕同一问题发言，由一个 moderator agent 充当主席协调轮次，最后汇总分歧、收敛点、一句话"如果必须选"的判语。

灵感来源：`诸子.skill`（我们无法访问原件，在此基础上重新推导模式）。

Announce at start: "I'm using the persona-debate skill to orchestrate a multi-persona debate with a moderator agent coordinating turns."

## Three Modes

辩论的组织方式有三种（细节见 `references/modes.md`）：

| 模式 | 一句话说明 | 适合 |
|------|-----------|------|
| **Round-robin** | N 位参与者按固定顺序发言，共 3 轮。每轮每人一次。 | 默认。视角均衡，节奏清晰。 |
| **Position-based** | 开辩前给每位参与者分派立场（支持 / 反对 / 中立），逼出对立。 | 决策类问题（"要不要做 X？"），需要对立视角。 |
| **Free-form** | 谁相关谁说话，moderator agent 在最后做综合。 | 探索性问题，参与者专长差异大；但容易跑题，moderator 强制 ≤3 轮。 |

用户未指定时默认 Round-robin。

## How Participants Are Chosen

两条路径：

1. **用户显式列出**：例如 "debate with Jobs, Munger, Naval"。本 skill 通过名字匹配已安装 persona skill 的 `manifest.json.identity.name` / `display_name`。
2. **由 persona-router 推荐后转入**：用户先跑 `persona-router` 得到一组推荐 persona，再把它们作为辩论参与者传给本 skill。这条路径不需要本 skill 实现路由逻辑——直接接受上游结果。

约束：参与者数量 `2 ≤ N ≤ 5`。少于 2 没有"辩"，多于 5 难以保持连贯。

## Invocation via Moderator Agent

**为什么要 moderator**：Claude Code 的 skill 之间不应互相直接调用（会绕过主 agent 的上下文管理，也不符合本仓库其他 skill 的做法）。我们用一个 moderator agent 作为"主席"——由主 agent spawn 一次，moderator 再依次"向每位 persona 提问"，把回应收集成一个 transcript。

Moderator agent 的定义在 `agents/moderator.md`。它会：

- 读取每个参与 persona 的 `manifest.json`（字段定义见 `contracts/manifest.schema.json`），从 `schema_type` 推断可能的论证风格（e.g. `mentor` 倾向给建议，`public-domain` 倾向给框架，`executor` 倾向给操作步骤），从 `identity.description` 理解人物定位。
- **不重新实现 persona**——它扮演的是主席，不是 persona 本人。轮到某 persona 发言时，moderator 模拟该 persona 的发言（基于其 SKILL.md 和 knowledge/ 能暴露出来的信号），质量天花板由 persona skill 自身决定。
- 执行所选模式的轮次控制（详见 `references/modes.md`）。
- 在结束时产出综合段落。

## Turn Structure

每轮的细节（开场白、提问模板、收敛条件、如何把前一位发言者的观点传给下一位）集中在 `references/modes.md`，避免本文件膨胀。核心结构：

```
Moderator 开场 → 亮出问题 → [Mode 决定的轮次序列] → Moderator 综合
```

## Output Format

单一 transcript 文件：

```
debate-{topic-slug}-{YYYYMMDD-HHMMSS}.md
```

结构：

```markdown
# Debate: {原始问题}

- Mode: round-robin | position-based | free-form
- Participants: {name1}, {name2}, ...
- Rounds: N

## Round 1

### {Persona A} (立场: 支持 / 无)
{发言内容}

### {Persona B} (立场: 反对 / 无)
{发言内容}

...

## Round 2
...

## Moderator Synthesis

### 最强分歧
- {A vs B on 议题 X}
- ...

### 收敛点
- {所有人都同意 Y}
- ...

### 如果必须选 (If-You-Had-To-Choose)
{一句话判语}
```

每段发言必须用 persona 名字标注，便于读者归因。

## Limitations（老实交代）

- **装机门槛**：至少需要 2 个符合 `manifest.schema.json` 契约的 persona skill 已安装。只装了 1 个 persona 跑不起来。
- **上限 5 人**：参与者超过 5 个 → moderator 难以维持连贯，轮次膨胀，transcript 变成流水账。硬性拒绝。
- **Moderator 是影子**：moderator 对参与者的"扮演"能力受限于它能从 SKILL.md / manifest / knowledge 里读到的信号。如果底层 persona 密度低（persona-judge 给分 < 6），debate 里它的发言也会显得空洞。**辩论质量 ≤ 参与 persona 的质量**。
- **Free-form 会飘**：自由发言模式容易跑题或少数人独占话筒。moderator 强制最多 3 轮、每人发言次数差距 ≤ 1，但仍可能需要主 agent 手动干预。
- **不做事实检查**：persona 说错了历史 / 数字，moderator 不会纠正——它只是主席，不是裁判。要事实核查请用其他 skill。
- **成本**：一次 3 轮 5 人辩论 ≈ 5×3=15 次 persona 发言 + 1 次综合 ≈ 比单 persona 问答贵 10-15 倍 token。

## Progressive Disclosure

本文件只说"是什么 / 怎么用 / 有什么限制"。以下细节在单独文件：

- 三种模式的轮次逻辑、提问模板、收敛条件 → `references/modes.md`
- Moderator agent 的行为规范、提示词模板、manifest 读取逻辑 → `agents/moderator.md`
- manifest 契约字段含义 → `contracts/manifest.schema.json`

## Anti-patterns

| 坏做法 | 为什么失败 | 正确做法 |
|--------|-----------|---------|
| 只拉 1 个 persona 也叫 debate | 没有"辩" | 至少 2 人，拒绝单人 |
| 拉 7 个 persona 让气氛热闹 | transcript 成流水账，无人记得前文 | 硬上限 5 |
| Skill 之间直接互相调用 | 绕过主 agent 上下文，难以追踪 | 一律通过 moderator agent |
| Moderator 帮 persona 补全观点 | 污染了"这是 X 说的"归因 | moderator 只做主席，不替 persona 加戏 |
| Free-form 跑到第 7 轮 | 收益递减 | 强制 ≤3 轮 |
| 不保存 transcript | 辩论过完就丢 | 每次都落盘为 `debate-*.md` |

## Core Principle

> **"One persona gives you a view. A debate gives you the shape of the disagreement."**
>
> 单个 persona 给你一个视角；debate 给你的是分歧的形状——而真正有价值的决策信息，恰恰藏在分歧里。
