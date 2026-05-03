# Tacit Knowledge Boundary — 品味为什么必须人审

> 本文档是本 skill 的产品诚实声明的理论依据。它解释为什么 5 项 check 全过 ≠ 这份 DESIGN.md 有品味。这是 SKILL.md §1.4 / 铁律 3 / B6 negotiation-summary 的引用源。

## 1. Tacit Knowledge（默会知识）的概念

### Polanyi 1966

哲学家 Michael Polanyi 在 *The Tacit Dimension*（1966）中提出：

> "We know more than we can tell."（我们知道的比我们能说出的多）

**默会知识**指的是难以用语言完全表达的知识——骑自行车、识别面孔、判断设计是否有品味——这些都是**人能做到但说不清楚怎么做到**的知识。

与之相对的是**显性知识**（explicit knowledge），即可以写在书上、传授给他人、形式化为算法的知识——数学公式、化学反应、WCAG 对比度规则等。

### 设计品味属于哪一类

设计品味是 **tacit knowledge** 的典型例子。设计师可以说"这个间距不对"但很难精确说出为什么——往往是基于成千上万小时的看 / 做积累出的直觉。

## 2. 学界共识：Design Taste 无法形式化

### Schön 1983 — Reflective Practice

Donald Schön 在 *The Reflective Practitioner* 中分析专业判断（包括设计判断）的本质：**reflection-in-action**——边做边判断，且这种判断的逻辑无法事先用规则表达。

设计师的"我觉得这样不对"是 reflection-in-action 的产物，规则化失败。

### Cross 2011 — Design Thinking

Nigel Cross 在 *Design Thinking: Understanding How Designers Think and Work* 综合多年设计研究后总结：

> 设计专长依赖"Designerly Ways of Knowing"——一种独特的、难以形式化的认知模式。

### CHI 2024 Graphic Design Tacit Knowledge Research

最近的 HCI 研究（CHI 2024 / DRS 2024 等）通过大规模 protocol analysis 实证：即使顶级设计师也**无法**完整解释其判断逻辑——很多决策"just feels right"。

## 3. 任何声称"AI 自动生成有品味设计"的产品都是伪科学

### 三个反证

**反证 1：训练数据的悖论**
如果"有品味的设计判断"可以被训练数据习得，那么 AI 生成的就是已有数据的统计平均。但**统计平均不是品味**——品味本质是 outlier judgment，是判断什么是真正好的（即使训练集中没有）。

**反证 2：Goodhart's Law 应用**
任何把"品味"形式化为 metric 的尝试，一旦该 metric 被优化，品味就停止意味着 metric 描述的东西。例：早期 SEO 把"权威性"形式化为 backlink 数量，结果整个产业 game 这个 metric，"权威性"变成"backlink 多"，品味丧失。

**反证 3：神经美学（Neuroaesthetics）的实证**
Semir Zeki 等神经美学研究表明：审美判断激活前额叶 + 岛叶等多个脑区，且**没有单一"品味中枢"**。这意味着品味是分布式的、context-dependent 的、无法通过任何单一算法捕获。

## 4. 本 skill 的诚实定位

### 5 项 check 能做的（下限保证）

| check | 拦掉什么 |
|---|---|
| **coherence_check** | 数学错误（对比度不足 / 间距不上 grid / 色相无 scheme） |
| **archetype_check** | 语境错配（用 Hero archetype 但配 pastel 色板） |
| **kansei_coverage_check** | 调性不响应用户画像（用户要 mystical 但产物只 modern） |
| **neighbor_check** | 跑出已知好设计的范围（hallucinate 出从未见过的奇怪组合） |
| **rationale-judge** | 论证不通（inheritance 编造 / adaptation 反 Kansei） |

### 5 项 check **不能**做的

> ❌ 判断"这份设计有品味"
> ❌ 替代设计师的最终判断
> ❌ 区分"独创新方向"和"奇怪 hallucinate"（neighbor_check 只能拦掉后者，无法识别前者的价值）

### 结论：这是带论证的初稿，不是成品

skill 的产物**必须**经过设计师终审。它替代的是"用户硬选 5 个固定方向"或"硬选别人 DESIGN.md"这个低质量起点，**不是替代设计师**。

## 5. 引用本文档的位置

- `SKILL.md §1.4` 产品诚实声明
- `SKILL.md` 铁律 3：B6 必须明确告知"品味需自审"
- `prompts/b6-output-formatting.md` 的 negotiation-summary 模板
- `prompts/b5-p0-gate.md` 的 verdict 解释

## 6. 参考文献

- Polanyi, Michael (1966). *The Tacit Dimension*. University of Chicago Press.
- Schön, Donald (1983). *The Reflective Practitioner: How Professionals Think in Action*. Basic Books.
- Cross, Nigel (2011). *Design Thinking: Understanding How Designers Think and Work*. Berg.
- Zeki, Semir (1999). *Inner Vision: An Exploration of Art and the Brain*. Oxford UP.
- Goodhart, Charles (1975). "Problems of Monetary Management." 提出 Goodhart's Law。
