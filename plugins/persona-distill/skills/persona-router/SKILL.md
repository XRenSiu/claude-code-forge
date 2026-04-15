---
name: persona-router
description: >
  跨 persona 智能调度器。当用户装了多个 persona skill 时，router 读取它们的 manifest.json，
  根据当前问题推荐最合适的 1-3 个 persona 来回答。
  Use when: (1) 已装 10+ 个 persona skill, (2) 不确定该问哪个 persona, (3) 想要多视角意见,
  (4) 准备启动 persona-debate 但不知道叫谁来。
  Triggers: "which persona", "ask multiple personas", "推荐 persona", "调度 persona",
  "哪个 persona", "问谁合适"
when_to_use: |
  - 用户安装的 persona skill 数量 >= 10，手动选择产生摩擦
  - 用户问题跨领域，不明显指向单一 persona
  - 需要为 persona-debate 自动挑选参辩人
  - 想批量扫描"谁有资格回答这个问题"
  - 不建议使用：persona skill 数量 < 10 时手动挑选更快
version: 0.1.0
---

# Persona Router

**从已安装的 N 个 persona skill 里，挑出最懂这个问题的 1-3 个。**

Announce at start: "I'm using the persona-router skill to scan installed persona manifests and recommend the best matches for your question."

## Overview

当你蒸馏了十几个 persona skill（同事、导师、公众人物、领域专家……），每次面对一个新问题，你都要在脑子里过一遍"这个问题谁最懂"。Router 把这步自动化：读所有 persona 的 `manifest.json`，按问题语义打分，给出排序推荐，你挑一个或几个触发。

Router **不回答问题**，只负责**把合适的 persona 推到你面前**。

## When Router Adds Value (Be Honest)

PRD 明确指出：

> **"router 和 debate 在 persona skill 数量 <10 之前没价值。"**
> — `docs/.../prd.md` §8 Q6

在下面这些情况，**不要用 router**：

| 场景 | 更好的做法 |
|------|-----------|
| 只装了 1-3 个 persona | 直接叫名字 |
| 问题明显属于某个 persona 的主场 | 直接触发那个 persona |
| 你想要的是"多方辩论"而非"挑人" | 直接用 `persona-debate` |
| persona 总数 <10 | 手动挑更快，router 开销反而亏 |

Router 的回报曲线在 persona 数 >= 10 后才变陡。

## The Single Input Contract

Router 只读一种输入：**符合 `contracts/manifest.schema.json` 的 `manifest.json` 文件**。

这是 **router 唯一认识的格式**。任何 persona skill 如果没有合规的 manifest，router 会直接跳过（并在报告中列出）。Contract 路径（相对仓库根）：

```
plugins/persona-distill/contracts/manifest.schema.json
```

Schema 里 router 实际用到的字段：
- `schema_type` — 9 种 persona schema 之一
- `identity.name` / `identity.display_name` / `identity.description` / `identity.domains` / `identity.subject_type` — 匹配语义
- `components_used` — 19 个共享组件的激活集合（v0.3.0 起含 execution-profile）
- `triggers` — 触发短语（用来做二次验证）
- `density_score` / `validation_score` — 质量信号
- `unvalidated` — 未验证警告

不在 schema 里的字段 router 一律忽略。

## Four-Step Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    PERSONA ROUTER FLOW                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Step 1: 接收用户问题                                        │
│           ↓                                                 │
│  Step 2: 扫描 installed persona skills                      │
│           └─ 读所有 manifest.json                           │
│              （符合 contracts/manifest.schema.json）         │
│           ↓                                                 │
│  Step 3: 在匹配维度上打分                                    │
│           ├─ schema_type relevance                          │
│           ├─ identity.domains keyword overlap               │
│           ├─ components_used coverage                       │
│           └─ density_score / validation_score 调权           │
│           ↓                                                 │
│  Step 4: 输出 1-3 条推荐（rationale 可见）                   │
│           └─ 按 templates/recommendation-template.md 格式   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Step 1 — Receive Question

直接从用户消息取。必要时 router 可以反问一句澄清问题类型（"这是想听策略判断，还是找人帮你做事？"），但默认不要多嘴。

### Step 2 — Scan Installed Persona Skills

**发现机制**：扫描用户 Claude Code skills 目录下所有子目录，读取每个子目录里的 `manifest.json`，用 `contracts/manifest.schema.json` 验证。

**路径约定**（按优先级）：

1. 项目级：`<repo>/.claude/skills/*/manifest.json`
2. 用户级：`~/.claude/skills/*/manifest.json`
3. 插件产物：`<plugin-dir>/skills/*/manifest.json`

> **Limitation — Environment-dependent discovery**:
> Claude Code 实际的 skill 安装位置取决于运行环境（项目 vs 用户 vs plugin marketplace）。
> Router 无法保证一次扫描拿到全部，只能基于当前会话可见的目录列表。
> 当发现 0 个合规 manifest 时，router 会**显式告诉用户扫描了哪些路径、为何为空**，
> 而不是静默失败。

对每一个找到的 `manifest.json`：
- Schema 校验失败 → 加入 "skipped (invalid manifest)" 清单，告知用户
- Schema 校验通过 → 进入打分

### Step 3 — Score on Matching Dimensions

四个打分维度（细节见 `references/matching.md`，此处仅概览）：

| 维度 | 做什么 | 举例 |
|------|--------|------|
| **schema_type relevance** | 根据问题性质选偏好的 schema 类型 | "我该不该换工作" → mentor / public-mirror 优先，friend / topic 次之 |
| **identity.domains overlap** | 问题关键词与 `identity.domains` 的重叠 | 问题含 "后端架构" → domains 含 "backend"/"architecture" 的 persona 加分 |
| **components_used coverage** | 问题需要的组件是否被激活 | 策略性问题 → 偏好含 `mental-models` + `decision-heuristics` 的 persona |
| **quality signals** | `density_score` 和 `validation_score` 调权 | 同分情况下，higher density wins；`unvalidated: true` 扣分并 flag |

> **最终得分的公式、权重、阈值参见 `references/matching.md`。**
> SKILL.md 只承诺维度本身，不 hardcode 数字。

### Step 4 — Emit 1-3 Recommendations

输出格式遵循 `templates/recommendation-template.md`（T006 产出，router 消费）。每条推荐必须包含：
- persona name + schema_type
- 主要匹配理由（domains / components 命中点）
- 已知弱点或 unvalidated 警告（如有）

**Inline Example Output**:

```
建议调用（按匹配度排序）：

1. colleague-zhangsan (collaborator, work-capability) — 覆盖后端架构，
   近期做过类似 API 设计决策
2. steve-jobs-mirror (public-mirror, mental-models) — 产品判断视角，
   对 trade-off 取舍有明确框架
3. mentor-lisi (mentor, decision-heuristics) — 有类似决策经验可供参照

⚠ mentor-lisi 的 manifest 标记 unvalidated=true，回答请交叉验证。

你挑一个或多个触发即可。需要直接进入辩论吗？→ persona-debate
```

推荐数量规则：
- 默认上限 3
- 若没有任何 persona 的任一维度得分超过"最低推荐阈值"（见 `references/matching.md`），router 输出 0 条推荐 + 诚实说明"无强匹配"
- 绝不硬凑 3 条

## Integration with persona-debate

Router 的输出可以直接 pipe 进 `persona-debate`：

```
router 输出 3 条推荐
     │
     ▼
用户确认 / 选 N 条
     │
     ▼
persona-debate 以这 N 条为参辩人启动
```

交接约定：router 把推荐清单以 persona name 列表形式交给 debate，debate 自己去 spawn persona。router 不做 debate 的职责。

## Constraints & Principles

1. **唯一输入 = `manifest.json`**。Router 不读 persona 的 knowledge 目录，不读 SKILL.md 正文，只读 manifest。这是刻意的——manifest 是 persona-distill 生态的**公共接口**。
2. **不回答问题**。Router 只推荐，不代答。
3. **诚实优先于装忙**。匹配不好就输出 0 条 + 解释，不要凑数。
4. **可审计**。每条推荐附带 rationale，用户能看到"为什么是它"。
5. **环境限制要显式 surface**，不要假装扫描到了全宇宙的 persona。

## Anti-patterns

| 坏行为 | 为什么失败 | 正确做法 |
|--------|-----------|---------|
| 为了凑 3 条而降低阈值 | 污染用户决策 | 没有强匹配就输出 0 条 |
| 读 manifest 之外的文件做匹配 | 破坏公共接口 | 严格只读 `manifest.json` |
| 对 schema 校验失败的 manifest 静默跳过 | 用户不知道丢了啥 | 明确列出 skipped 清单 |
| 在 persona 数 <10 时推销自己 | 违背 PRD 定位 | 主动提示"手动选更快" |
| 同时启动 debate | 越权 | 只推荐，让用户决定是否进 debate |

## Progressive Disclosure

本 SKILL.md 控制在 < 250 行。深度内容分散在：

- `references/matching.md` — 打分维度的具体公式、权重、阈值、corner case
- `templates/recommendation-template.md` — 推荐输出格式（T006 交付）
- `contracts/manifest.schema.json` — 输入契约（T001 已交付）

## Core Principle

> **"A good router earns its keep only when choosing gets hard.
>  When you have three personas, call them by name. When you have thirty, call the router."**
>
> 好的调度器只在"挑选本身变难"时才有价值。三个 persona 直接叫名字，三十个才叫 router。
