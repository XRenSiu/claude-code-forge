# Bespoke Design System

> 为每个产品需求生成专属的 DESIGN.md，每个决策都可追溯、可论证、可协商。

## 这个 skill 解决什么

围绕 **DESIGN.md 9-section 标准（OD 方言：Visual Theme & Atmosphere / Color Palette & Roles / Typography Rules / Component Stylings / Layout Principles / Depth & Elevation / Do's and Don'ts / Responsive Behavior / Agent Prompt Guide）** 已经形成一批资产集合（OD 仓库已收录 ~140 套：Linear / Stripe / Vercel / Notion / Apple 等知名产品的设计系统、`VoltAgent/awesome-design-md` 社区库、各团队内部 DESIGN.md），但它们的使用方式仍然停留在"**选一套整套用**"——即使再像，**也不属于自己的产品调性**。

更深层的问题：这些 DESIGN.md 集合作为"**已被验证的设计判断的样本集**"的潜力完全没被利用。它们是壳子，不是可借鉴、可学习、可重组的设计资产。

本 skill 的本质：

> 把任意一组 DESIGN.md 素材里"做对了的设计判断"形式化成**可计算、可组合、可演化的设计语法**，然后用这套语法为每个新用户做一次新的设计判断，且每个判断都必须能回答"**为什么对这个用户对**"。

## 三个不一样的地方

| 维度 | 传统做法 | 本 skill |
|---|---|---|
| 素材使用 | 整套套用 / 参数拼贴 | 反向工程出"设计语法"，正向用语法重新做判断 |
| Rationale | 单向（只描述结果） | **双向对称**：拆解时产 rationale，生成时也产 rationale |
| 交互成本 | 多轮往复盘问 | 一次性追问铁律：B1 问完所有问题，生成中途绝不打断；或 auto 零追问 |
| 资产演化 | 静态 | 高频 adaptation 自动沉淀为新规则，规则库随场景有机生长 |

## 输出物

每次生成产三份：

1. **`DESIGN.md`** — OD 方言 9-section 格式（Visual Theme & Atmosphere / Color Palette & Roles / Typography Rules / Component Stylings / Layout Principles / Depth & Elevation / Do's and Don'ts / Responsive Behavior / Agent Prompt Guide），可被任何 DESIGN.md 兼容工具消费（OD、Claude Design、Stitch、未来兼容工具）
2. **`provenance.yaml`** — 完整决策追溯，每条决策包含 `inheritance`（来源规则 + 来源系统 + 原始 rationale）+ `adaptation`（调适项与原因）+ `justification`（与其它决策的协同性、Kansei 覆盖、冲突检查）
3. **`negotiation-summary.md`** — 用户可读摘要，关键决策的 rationale 用自然语言；auto 模式下额外标注哪些字段是推断的，便于针对性反馈

## 使用方式

### 主入口（生成）

```
帮我设计一个八字 SaaS 的设计系统
```

skill 自动判断模式：

- **默认 interactive**：一次性把所有需要补充的问题打包问完（硬上限 7 条），生成中途绝不再问
- **auto**：用户说 "直接给我一份" / "不要问我" / "auto" / "全自动" → 零追问，所有缺失字段走默认推断并在 provenance 中标注

### 维护入口

```
帮我把 OD 的 ~140 套素材导进来
```

或：

```
拆解 ./my-design.md 加入素材库
```

或：

```
沉淀最近 7 次都出现的 saturation 调适
```

### 双模式选择由用户决定

模式不是技术问题，而是用户对"我愿意花多少时间换多少精度"的偏好。skill 不替用户决定。

## 素材库

**不绑定特定素材源**。可任意混合：

- **OD ~140 套**（首次安装时推荐起步源，从 `nexu-io/open-design` 拉取；持续增长中）
- **awesome-design-md**（`VoltAgent/awesome-design-md` 社区库）
- **用户自己的内部 DESIGN.md**
- **任意其它 DESIGN.md 集合**

每套素材在 `grammar/meta/source-registry.json` 登记来源、许可、提取时间。

## 工作流程

### 阶段 A — 素材拆解（维护入口，低频）

每套 DESIGN.md 跑 4 步：

1. **A1 Token 层提取** → `grammar/tokens/<system>.json`（精确参数事实锚点）
2. **A2 Rationale 层抽取** → `grammar/rationale/<system>.md`（trade_off / intent / avoid 三段式）
3. **A3 Rule 层抽象** → `grammar/rules/<system>.yaml`（参数化模式 + Kansei 标签 + emerges_from 可信度证据）
4. **A4 关系图构建** → `grammar/graph/rules_graph.json`（depends_on / constrains / co_occurs_with / conflicts_with 有向图）

### 阶段 B — 生成（主入口，每次调用）

```
B0 模式分流（interactive | auto）
    ↓
B1a 一次性追问（≤7 题，interactive）  /  B1b 全自动推断（auto）
    ↓
B2 规则检索（Archetype 硬筛 + Kansei 软排 + SD 距离修正，候选 100-200 条）
    ↓
B3 冲突解决（图算法：消解冲突、补依赖、聚风格岛 → 自洽 40-60 条）
    ↓
B4 带 Rationale 生成（inheritance + adaptation + justification 三段式）
    ↓
B5 P0 闸门（rationale-judge subagent 对抗式评审，限 2 轮迭代）
    ↓
B6 输出三份产物
```

**铁律**：B2 之后绝不向用户追问任何信息。

## 自演化机制

每次成功生成都更新 `grammar/meta/adaptation-stats.json`。当某条 adaptation 出现 ≥5 次（默认阈值），由 `consolidate-adaptations.md` 子流程提议沉淀为新规则。

新规则 `provenance: generated`，与原生规则区分，便于独立回滚。规则库随真实使用场景有机生长，逐渐覆盖原本素材库覆盖不到的产品 niche。

## 文件结构

```
skills/bespoke-design-system/
├── SKILL.md                     # 主入口
├── prompts/                     # B 阶段 7 个步骤模板
├── scripts/                     # 维护流程子文档
├── subagents/rationale-judge.md # P0 闸门
├── references/                  # 理论文档（按需引用）
├── grammar/                     # 规则库（核心资产）
├── source-design-systems/       # 素材库
└── examples/                    # 端到端案例
```

详见 [`skills/bespoke-design-system/SKILL.md`](skills/bespoke-design-system/SKILL.md)。

## 理论基础

| 理论 | 角色 |
|---|---|
| Reverse Engineering for Design Systems (Thoughtworks 2026) | 拆解总框架 |
| Design Rationale Capture (Schön 1983) | rationale 必须叙事化 |
| Shape Grammar (Stiny & Gips 1971) | 规则反推 + 规则生成 |
| Kansei Engineering (广岛大学 1970s) | 调性词与设计参数的桥梁 |
| A Pattern Language (Alexander 1977) | 规则关系图建模 |
| Brand Archetype (Mark & Pearson) | 用户需求的离散分类 |
| Semantic Differential (Osgood 1950s) | 连续维度的调性测量 |

## 安装

通过 Claude Code marketplace 安装：

```
/plugin install bespoke-design-system@claude-code-forge
```

首次安装后，可选地拉取起步素材：

```
帮我导入 OD 的 ~140 套设计系统
```

## License

MIT © 2026 XRenSiu
