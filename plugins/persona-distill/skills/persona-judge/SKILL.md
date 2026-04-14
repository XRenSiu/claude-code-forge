---
name: persona-judge
description: >
  Persona Skill 质量评估器。对任何 persona skill 执行 3 项测试 + 12 维 rubric + 密度评分，
  产出可机读的 validation-report.md 作为质量闸门。
  Use when: (1) distill-meta Phase 4 自动回调, (2) 用户主动评估已有 persona skill,
  (3) CI 中验证 persona skill 更新是否退化。
  Triggers: "evaluate persona", "评估 persona skill", "persona quality check", "persona judge"
when_to_use: |
  - distill-meta 在 Phase 4 自动调用，用于决定是否进入 Phase 5 交付
  - 用户手动对任何 persona skill 目录执行质量审计
  - 修改 persona skill 后做回归评估，对比历次分数
  - CI 流水线中作为 persona skill PR 的准入检查
version: 0.1.0
---

# persona-judge

**把"这个 persona 到底像不像"从直觉变成分数。**

Announce at start: "I'm using the persona-judge skill to run the 3-test / 12-dimension / density evaluation pipeline and emit a validation-report.md."

> 没有量化评估的蒸馏就是玄学，质量无法改进。 (PRD §9.5)
>
> A distillation without quantitative evaluation is mysticism — quality cannot improve.

## Overview

`persona-judge` 是整个 persona-distill 生态的**质量闸门**。它回答一个问题：
**"这个 persona skill 到底有多像本人，以及它的'像'能不能被复现和追踪？"**

输出是一份严格符合契约的 `validation-report.md`——frontmatter 被 `distill-meta` 机读用于 gating，body 被人类读用于改进。判决分 `PASS` / `CONDITIONAL_PASS` / `FAIL` 三档，全部可追溯到具体维度分数与测试证据。

## Two Trigger Modes

| 模式 | 来源 | 入参 | 输出 |
|------|------|------|------|
| **Auto** | `distill-meta` Phase 4 自动回调 | persona skill 根目录 + 本次 distill session id | `validation-report.md` + frontmatter 供 meta 读取 |
| **Manual** | 用户说 "evaluate X persona skill" / "评估 X persona skill" | persona skill 根目录（可任何来源，不必是 distill-meta 产出） | 同上 |

两种模式**流程完全一致**，区别仅在调用方如何消费结果。在 Auto 模式下，`distill-meta` 只读 frontmatter 字段做门禁判断；Manual 模式下完整展示 body 给用户。

## Input Contract

输入只有一个：一个 persona skill 的根目录路径（例如 `~/skills/steve-jobs-mirror/`）。

执行前必须：

1. 确认目录存在且包含 `SKILL.md`、`manifest.json`。
2. 用 `../../contracts/manifest.schema.json` 校验 `manifest.json`。校验失败 → 直接 `verdict: FAIL`，dimensions 全 0，`critical_failures: 12`，并在 `Recommended Actions` 中给出 schema 违规列表。
3. 从 manifest 读出 `schema` 字段（9 种之一）和 `components[]`，用于后续维度评分的上下文感知（例如 `internal_tensions` 仅对 `public-mirror` / `mentor` 强要求）。

## Evaluation Pipeline (5 Steps)

```
┌──────────────────────────────────────────────────────────────────┐
│  Step 1  LOAD           加载 persona skill + 校验 manifest       │
│          ↓                                                       │
│  Step 2  3-TEST         运行 Known / Edge / Voice 三项测试       │
│          ↓              详见 ./references/three-tests.md         │
│  Step 3  12-DIM SCORE   按 rubric 打分 12 个维度                 │
│          ↓              详见 ./references/rubric.md              │
│  Step 4  DENSITY        反向使用 anti-distill 分类器计算密度     │
│          ↓              详见 ./references/density-scoring.md     │
│  Step 5  EMIT REPORT    生成 validation-report.md + 历史快照     │
│                         遵守 ../../contracts/                    │
│                                 validation-report.schema.md      │
└──────────────────────────────────────────────────────────────────┘
```

每一步的详细算法、prompt、取证要求在 `./references/` 中，SKILL.md 仅保留骨架与契约。

## 12-Dimension Rubric (Summary)

满分 **110 raw**，通过门槛 **82 raw**（约 74.5%）。注意：**所有 gating 用 raw 分，normalized 仅用于展示**（契约 §Contract for Consumers）。

| # | Dimension | Max | 1-line Description |
|---|---|---|---|
| 1 | Known Test | 10 | 3 个已知问题的复现相似度（对照本人公开答复） |
| 2 | Edge Test | 10 | 1 个未覆盖问题的不确定性是否被诚实表达 |
| 3 | Voice Test | 10 | 100 字盲测：能否被识别为本人口吻 |
| 4 | Knowledge Delta | 10 | 相较 Claude 默认知识，新增了多少本人特有内容 |
| 5 | Mindset Transfer | 10 | 是否传递思维模式而非结论堆砌 |
| 6 | Anti-Pattern Specificity | 10 | 反模式是否具体非泛化（避免"要专注用户"式废话） |
| 7 | Specification Quality | 5 | frontmatter 完整性、触发描述质量 |
| 8 | Structure | 5 | 行数、层级、progressive disclosure 合理性 |
| 9 | Density | 10 | 高价值内容段落占比（见下节） |
| 10 | Internal Tensions | 10 | 是否有 ≥2 对内在矛盾（阈值可在 config.yaml 调整） |
| 11 | Honest Boundaries | 10 | 是否有 ≥3 条具体局限（阈值可在 config.yaml 调整） |
| 12 | Primary Source Ratio | 10 | 一手来源占比 > 50% |

> 10 分维度 × 10 = 100；5 分维度 × 2 = 10；**合计 110 raw**。
> 每个维度的评分 rubric（0/3/5/7/10 五档锚点）详见 `./references/rubric.md`。

## Density Scoring

**一句话**：借用 `anti-distill` 的 4 级 classifier，反向使用——对 SKILL.md 和各组件文件的每个段落打 4 种标签 `REMOVE`（+2，高价值独特判断/具体阈值）、`MASK`（+1，中高价值网络/路径）、`SAFE`（0，通用常识）、`DILUTE`（-1，正确废话），求和归一化到 `[0, 10]` 即为 `density_score`。

**硬规则**：`density_score < 3.0` 强制 `verdict: FAIL`，不论总分。这是防止"看起来结构完整但全是废话"的 skill 蒙混过关。

算法细节、锚点例子、段落切分规则见 `./references/density-scoring.md`。

## Critical Failure Rules

以下任一条件触发**强制 FAIL**，覆盖总分：

| 规则 | 来源 | 判定 |
|------|------|------|
| 任意 **2 个或更多**维度得 0 分 | `../../contracts/validation-report.schema.md` §Scoring Math | `verdict: FAIL`, `critical_failures >= 2` |
| `density_score < 3.0` | 同上 | `verdict: FAIL` |
| `manifest.json` 校验失败 | `../../contracts/manifest.schema.json` | `verdict: FAIL`, 全 0 |

`CONDITIONAL_PASS` 的触发条件（raw ≥ 82 但有 1 个 0 分维度，或 raw ∈ [75, 82) 且无致命项）详见 `./references/rubric.md` §Verdict Decision Table。

## Output Location

| 路径 | 作用 |
|------|------|
| `{persona-skill-root}/validation-report.md` | **最新版**（canonical），`distill-meta` 与用户都从这里读 |
| `{persona-skill-root}/versions/validation-report-{ISO8601}.md` | **历史快照**，每次评估追加一份，便于回归对比 |

两份文件内容完全一致；`validation-report.md` 只是最新快照的镜像。文件内部结构必须严格遵守 `../../contracts/validation-report.schema.md` 定义的 frontmatter + body 双层格式。

## Configuration

阈值在 `./config.yaml` 中可调（SPEC-04，来自 risk assessment）：

```yaml
pass_threshold_raw: 82          # 默认 82 / 110；低于则 FAIL（除 CONDITIONAL_PASS 档）
density_floor: 3.0              # 密度硬底线
min_internal_tensions: 2        # internal_tensions 维度拿满分所需的最小矛盾对数（nuwa 默认）
min_honest_boundaries: 3        # honest_boundaries 维度拿满分所需的最小边界数（nuwa 默认）
primary_source_ratio_pass: 0.5  # primary_source_ratio 满分阈值
critical_failure_count: 2       # 触发强制 FAIL 的 0 分维度数量阈值
```

所有阈值都是**可覆盖的默认值**。评估前若用户传入 `--config path/to/custom.yaml`，以用户值优先。所有使用的阈值必须写入 `validation-report.md` 的 `## Summary` 段末注明，保证可复现。

## Integration with distill-meta

`distill-meta` Phase 4 调用本 skill 后，**只读取 frontmatter** 的两个字段做 gating：

- `verdict`（`PASS` / `CONDITIONAL_PASS` / `FAIL`）
- `overall_score_raw`（用于 loop counter 决策是否继续迭代）

它**不解析 body**。这意味着本 skill 必须保证 frontmatter 绝对可机读、字段命名与契约一致、无意外字段。body 的用途是给人读、给 `Recommended Actions` 回到 Phase 2 作为 fix-brief。

> 契约引用：`../../contracts/validation-report.schema.md` §"Contract for Consumers (distill-meta Phase 4 gate)"

## Progressive Disclosure

本 SKILL.md 保持在 **< 300 行**，仅承载：触发契约、流程骨架、维度清单、致命规则、输出契约。

**所有深度**（具体 prompt、锚点例子、段落切分算法、每维度评分 rubric、密度 classifier 细节）在：

- `./references/three-tests.md` — Known / Edge / Voice 三项测试的完整执行步骤
- `./references/rubric.md` — 12 维度各自的 0/3/5/7/10 锚点 + verdict decision table
- `./references/density-scoring.md` — 4 级 classifier 锚点 + 段落切分规则 + 归一化公式

Agent 按需加载，不要一次性灌入上下文。

## Anti-patterns

| 坏行为 | 为什么失败 | 正确做法 |
|--------|-----------|---------|
| 凭直觉打分不留证据 | 无法复现、无法回归 | Test Evidence section 必须贴测试原文 |
| 绕过契约直接改 frontmatter 字段名 | `distill-meta` 读不到，gating 崩溃 | 任何字段变更先改 `validation-report.schema.md` 并 bump 契约版本 |
| 无视 density 底线放行 | 让"结构完整的废话"污染生态 | `density < 3.0` 永远 FAIL，无例外 |
| 阈值硬编码在 SKILL.md | 用户无法调优 | 所有阈值走 `config.yaml` |
| 只跑 3 项测试不算 12 维 | 丢失 knowledge-delta / mindset / sources 维度 | 5 步必须全跑 |
| 覆盖 `validation-report.md` 不存历史 | 无法做回归对比 | 每次都写 `versions/validation-report-{ISO8601}.md` |

## Core Principle

> **"A persona skill that cannot be scored cannot be improved."**
>
> 不能被打分的 persona skill 不能被改进。
> 评估的目的不是给出判决，而是给出**下一次蒸馏该补什么**的可操作清单——
> 这也是为什么 `Recommended Actions` 必须具体到文件路径和具体改动。
