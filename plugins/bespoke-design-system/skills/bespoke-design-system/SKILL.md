---
name: bespoke-design-system
description: >-
  为用户的产品需求生成专属设计系统（DESIGN.md OD 方言 9-section 格式）。
  通过对一组已有设计系统素材做规则反推 + 双向 rationale 生成，
  避免 AI slop，每个决策可追溯可论证。
  素材库可来自任何渠道（开源集合如 OD ~140 套 / awesome-design-md、用户自有的设计系统），
  输出可被任何 DESIGN.md 兼容工具消费（如 OD、Claude Design、Stitch）。
  支持 interactive（一次性追问，硬上限 7 题）和 auto（零追问，默认推断）两种模式。
  也支持维护规则库（增量拆解新 DESIGN.md / 沉淀高频 adaptation / 重建关系图 / 批量导入外部集合）。
  触发词：" 设计系统 " / " 调性 " / " UI 风格 " / " bespoke design " / " DESIGN.md " /
  " 拆解设计系统 " / " 导入 OD " / " 沉淀 adaptation "。
argument-hint: "[mode=interactive|auto] <product-brief> | maintain <subcommand>"
version: 1.4.0
user-invocable: true
---

# Bespoke Design System — 专属设计系统生成器

你被调用来处理 **$ARGUMENTS**：可能是为一个产品需求生成专属 DESIGN.md（**主流程，99% 调用**），也可能是维护规则库（增量拆解新素材、批量导入集合、沉淀高频 adaptation、重建关系图）。

**开始时告诉用户：**

- 主流程：" I'm using the bespoke-design-system skill to generate a tailored DESIGN.md for your product. "
- 维护流程：" I'm using the bespoke-design-system skill in maintenance mode to <update / import / extract / consolidate>. "

---

## 一、本质（必读，每次都要在心里过一遍）

> 把任意一组 DESIGN.md 素材里 " 做对了的设计判断 " 形式化成**可计算、可组合、可演化的设计语法**，然后用这套语法为每个新用户做一次**新的设计判断**，且每个判断都必须能回答 " **为什么对这个用户对** "。

### 产品诚实声明（v4 新增）

本 skill 产出的是**带论证的 DESIGN.md 初稿**，不是成品。

**它能做到的**：
- 内在协调性（配色/排版/间距的数学关系正确）— 完全可量化
- 语境贴合性（匹配 archetype 和 Kansei 画像）— 离散判据 + 半量化
- 不出格（不会跑出已知好设计的范围）— 可量化下限保证

**它做不到的**：
- 判断"这份设计有品味" — 学界共识：tacit knowledge 无法形式化（Polanyi 1966；CHI 2024）
- 替代设计师的最终判断 — 品味这一关必须由人完成

定位上，它替代的是"用户硬选 5 个固定方向"或"硬选别人的 DESIGN.md"这个低质量起点，**不是替代设计师**。详见 `references/tacit-knowledge-boundary.md`。

### 五条铁律

1. **双向 Rationale 对称**：拆解时怎么提取 rationale，生成时就怎么产出 rationale。生成时的 rationale 必须三段式：`inheritance`（来源）+ `adaptation`（调适）+ `justification`（协同）。
2. **一次性追问铁律**（interactive）：所有澄清问题必须在 B1a 一次性问完，硬上限 7 条，超过则强制 B1a 重新规划聚焦。**B2 之后绝不向用户追问任何信息**——不管是 B3 冲突、B4 决策、B5 闸门失败，都不许打断用户。
3. **品味需自审**（v4 新增）：B5 的 5 项 check 全过 ≠ 这份 DESIGN.md 有品味。B6 的 negotiation-summary 必须明确告知用户"品味终审需由人完成"。引用 `references/tacit-knowledge-boundary.md`。
4. **不产生 AI slop**：紫渐变 + Inter + 圆角卡片那一套是 anti-pattern。每个决策都要在 `references/anti-slop-blacklist.md` 上过一遍。
5. **模式选择交给用户**：模式是用户对 " 我愿意花多少时间换多少精度 " 的偏好，不是技术问题。skill 不替用户决定。

---

## 二、触发分流（第一步必做）

解析 `$ARGUMENTS` 与最近的用户消息，判断走哪条主路径：

### 主流程：生成 DESIGN.md

**触发条件**：用户描述产品需求并希望得到设计系统、调性方案、UI 风格指南、设计 token、设计基底等。即使用户表述很模糊（例如 " 我想做个八字 SaaS"、" 给我做个设计调性 "），只要意图是 " 获得设计系统 "，都走这里。

→ 进入 §三 主流程

### 维护流程

**触发条件**：用户**明确**说要维护规则库或素材库，例如：

- " 拆解新的 DESIGN.md" / " 把这份 design.md 加进来 " → `scripts/add-new-design-system.md`
- " 导入 OD 的素材 " / " 从 awesome-design-md 拉一批 " → `scripts/import-from-collection.md`
- " 重新拆解 / 跑一遍提取 " → `scripts/extract-grammar.md`
- " 重建关系图 " / " 关系图坏了 " → `scripts/rebuild-graph.md`
- " 沉淀 adaptation" / " 合并高频调适 " → `scripts/consolidate-adaptations.md`

→ 进入 §四 维护流程，按子命令读取对应的 scripts 子文档执行

### 边界情况

- 用户说 " 帮我看看 Linear 的设计 " ≠ 维护流程。这是 " 阅读素材 " 而非 " 加入素材 "，应直接 Read `source-design-systems/linear/DESIGN.md` 并解释。
- 用户既要生成又要导入：先确认顺序（多数情况先导入、再生成），按用户回答串行执行。

---

## 三、主流程：生成 DESIGN.md

### B0 — 模式分流

模式由**用户**决定，三种来源（按优先级）：

1. `$ARGUMENTS` 含 `mode=interactive` 或 `mode=auto` → 按指定
2. 用户消息明确说 " 直接给我一份 " / " 不要问我 " / "auto" / " 全自动 " / " 别问 " / " 不打断 " → **auto**
3. 否则 → **默认 interactive**

**输出第一条状态**：

```
Mode: <interactive | auto>
Product brief: <从用户原始请求摘要 1-2 句>
Source registry: <读 grammar/meta/source-registry.json，告诉用户当前规则库覆盖了哪些设计系统>
```

如果 `grammar/rules/` 是空的（首次安装、没拉素材），**停下并提示用户**：" 当前规则库为空。建议先导入起步素材（OD ~140 套或 awesome-design-md），或加入你自己的 DESIGN.md。要现在导入吗？" 不要硬着头皮在空规则库上生成。

### B1 — 调性画像构建（按模式分支）

#### B1a — interactive 模式：一次性追问

读 `prompts/b1a-question-batching.md` 作为该步骤的工作指引。

**B1a 内部 4 步**：

1. 解析原始需求，识别所有 " 做出好设计需要但当前不知道 " 的维度（参考 `references/kansei-theory.md`、`references/brand-archetypes.md`）
2. 按 `criticality` 排序，**top-7 进入 batch**，其余走默认推断
3. 输出 `clarification_batch`（schema 见 §六 数据 Schema 3.3.6）给用户，**等用户一次性回答**
4. 解析回答 + 走默认推断的字段，合成完整调性画像（schema 见 §六 3.3.5）

**铁律**：

- 问题数量**硬上限 7 条**。如果识别出 >7 个维度，必须聚焦到最关键的 7 条，其余走默认。
- **永远不在生成中途追问**。B1a 想漏一次的成本远低于 B4/B5 中途打断用户。
- 每条问题必须标注 `criticality`（high/medium/low）和 `why_we_ask`（为什么这条问题对设计判断有效）。
- 问题前置一段 `preamble`：" 我准备开始为你的产品设计一份专属的设计系统。在开始之前，我有几个问题需要一次性问完——回答完之后，我会一气呵成地完成整个设计，中途不会再打断你。"

#### B1b — auto 模式：全自动推断

读 `prompts/b1b-auto-inference.md` 作为该步骤的工作指引。

**B1b 工作方式**：

1. 从用户需求关键词推断 `product_category`
2. 查 `grammar/meta/defaults.yaml` 拿到该 category 的 likely_archetypes、likely_kansei、avoid_kansei、sd_defaults
3. 用所有可用上下文（用户消息历史、当前项目内容、CLAUDE.md 等）覆盖默认值
4. 仍缺的字段走默认；**所有推断字段在画像的 `inferred_fields` 列表中标注**

**铁律**：

- 不向用户提任何问题。
- 推断必须可追溯：每个 `inferred_fields` 项要在 B6 的 `negotiation-summary.md` 中暴露，让用户能针对性反馈。

### B2 — 规则检索

读 `prompts/b2-rule-retrieval.md` 作为该步骤的工作指引。

**输入**：调性画像 + `grammar/rules/*.yaml`（含 `_generated.yaml`）

**输出**：候选规则集（典型 100–200 条）

**三层检索机制**：

1. **Archetype 主原型硬筛**：preconditions.brand_archetypes 含画像 primary archetype 的规则全部纳入候选
2. **Kansei 软排**：按规则 preconditions.kansei 与画像 kansei_words.positive 的 Jaccard 相似度排序；排除任何 preconditions.kansei 与 `reverse_constraint` 直接冲突的规则
3. **SD 距离修正**：用 semantic_differentials 的 L2 距离对候选集做最终重排

**关键**：直接在**规则层**检索，不在 DESIGN.md 层。候选集应宽，冲突解决留到 B3。

### B3 — 冲突解决与自洽化

读 `prompts/b3-conflict-resolution.md` 作为该步骤的工作指引。引用 `references/pattern-language.md`。

**输入**：B2 候选集 + `grammar/graph/rules_graph.json`

**输出**：自洽规则子集（典型 40–60 条）

**确定性图算法**（不让模型判断冲突）：

1. **冲突消解**：扫描候选集中 `conflicts_with` 关系。同时存在的对，留 Kansei 匹配度（B2 评分）高的，剔除另一条。
2. **依赖补全**：对每条留下来的规则，沿 `depends_on` 反向闭包，把所有依赖项纳入。
3. **风格岛聚集**：计算候选集内规则两两 `co_occurs_with` 频率的图密度。优先保留密度高的子图（" 自洽风格岛 "）；孤立点若与画像匹配度低则剔除。
4. **覆盖检查**：确认 5 个 rule-bearing section（`color / typography / components / layout / depth_elevation`）都至少有规则覆盖；缺的 section 用 `defaults.yaml` 中该 product_category 的 backstop 规则补。4 个元 section（Visual Theme / Do's and Don'ts / Responsive / Agent Guide）由 B4 阶段从 rule-bearing 派生，不需要在 B3 单独覆盖。

### B4 — 带 Rationale 生成

读 `prompts/b4-generation-with-rationale.md` 作为该步骤的工作指引。引用 `references/shape-grammar.md`、`references/reflective-practice.md`。

**输入**：B3 自洽规则子集 + 调性画像

**输出**：DESIGN.md 草稿 + Provenance Report（schema 见 §六 3.3.7）

**核心约束**：

- 每个决策**必须**产 `inheritance` + `adaptation` + `justification` 三段。
- 模型工作严格限定为 " 把规则集翻译成 DESIGN.md 的语言并产 rationale"，**不创造新规则**。任何看起来像新规则的判断都必须能追溯到 B3 子集里的某条；否则视为越权。
- **不向用户追问任何信息**。

**adaptation 必须记录**：

- `fully_aligned_kansei`：规则原本就支持的画像 kansei 词
- `needs_extension_kansei`：规则不直接支持但通过调适可以支持的 kansei 词
- `modifications`：每条调适列出 `dimension`（saturation / lightness / scale / etc.）、`from`、`to`、`reason`
- `preserved`：从规则原状照搬的部分

### B5 — P0 闸门（v4 重写：4 个 check + 1 个 LLM judge 并行）

读 `prompts/b5-p0-gate.md` 作为该步骤的工作指引。详细判据见 `references/` 下各理论文档。

**5 项独立检查并行执行**：

| Check | 判什么 | 实现 | 通过条件 |
|---|---|---|---|
| **coherence_check** | 合理：内在协调（数学公式） | `checks/coherence_check.py` | 0 blocker（WCAG body 失败为 blocker），score ≥ 0.55 |
| **archetype_check** | 贴合：archetype always/never list | `checks/archetype_check.py` | primary 0 blocker（never 触发为 blocker） |
| **kansei_coverage_check** | 贴合：Kansei 覆盖度 + 反向词冲突 | `checks/kansei_coverage_check.py` | 覆盖率 ≥ 80% AND 0 reverse_violation |
| **neighbor_check** | 品味下限：corpus 最近邻距离 | `checks/neighbor_check.py` | 距离 < 0.3 pass / 0.3-0.6 needs_review / ≥ 0.6 reject |
| **rationale-judge** | 论证质量（独立维度） | `agents/rationale-judge.md` via Agent 工具 | verdict = pass |

**5 项全过 → B6 出货**
**任一 reject → 整体 reject → 回 B4 重做（限 2 轮）**
**任一 needs_revision → 回 B4 带反馈重做（限 2 轮）**

**重要**：5 项全过 ≠ 这份 DESIGN.md 有品味。它只保证下限（数学正确 + 语境贴合 + 不跑出范围 + 论证通），不保证上限。最终品味关必须由人完成（铁律 3）。

**铁律**：**限 2 轮迭代**。两轮还过不了 → 标记"持续失败"，输出当前最好的版本 + 所有 issues 列表给用户判断。**不**追问用户。

### B6 — 输出与协商接口

读 `prompts/b6-output-formatting.md` 作为该步骤的工作指引。

**产物路径**（默认；用户指定路径时覆盖）：

```
./bespoke-design/<slug>/
├── DESIGN.md                  # 标准 9-section，可被任何 DESIGN.md 兼容工具消费
├── provenance.yaml            # 完整决策追溯，审计用
└── negotiation-summary.md     # 用户可读摘要
```

`<slug>` 从产品需求中提取（kebab-case，例如 " 八字 SaaS" → `bazi-saas`）。如果当前目录就是产品仓库，直接写到 `./DESIGN.md` 并把 provenance/negotiation 放到 `./bespoke-design/`；询问用户偏好后再决定。

**negotiation-summary.md 必须包含**：

- 一段 " 这份设计的核心调性 "（自然语言，3-5 句）
- 关键决策表（每行：决策 / 一句话 rationale / 来源系统列表）
- auto 模式下额外加 " 推断字段清单 "（让用户能针对性反馈）
- 协商接口示例：" 如果你想改某个决策（比如 ' 我不要 ancient 改成 minimalist'），告诉我具体哪个；我会回到 B3 重排规则、再走一次 B4-B6。"

**自演化触发**：B6 完成后，更新 `grammar/meta/adaptation-stats.json`，每条出现的 adaptation 累计 occurrences。如果某条 adaptation `occurrences ≥ 5`，在结尾输出一条提示：" 检测到 N 条高频 adaptation 已达沉淀阈值，可运行 ` 沉淀 adaptation` 把它们提议为新规则。"

---

## 四、维护流程

按 `$ARGUMENTS` 或用户消息中的子命令分流，读取对应 scripts 子文档**严格按其步骤执行**：

| 子命令 | 子文档 | 干什么 |
|---|---|---|
| `add` / 加入单套 DESIGN.md | `scripts/add-new-design-system.md` | 单套 → 跑 A1-A4 → 增量更新关系图 |
| `import` / 批量从外部集合导入 | `scripts/import-from-collection.md` | 从 OD / awesome-design-md / 自定义 git 仓库批量拉，登记到 source-registry，去重，跑 A1-A4 |
| `extract` / 重新拆解某套 | `scripts/extract-grammar.md` | A1-A4 四步流程的标准化操作（被其它脚本调用，也可独立跑） |
| `rebuild` / 重建关系图 | `scripts/rebuild-graph.md` | 全量重算 `grammar/graph/rules_graph.json` |
| `consolidate` / 沉淀高频 adaptation | `scripts/consolidate-adaptations.md` | 扫描 adaptation-stats，提议新规则，用户确认后写入 `_generated.yaml` |

**通用规则**：

- 每次维护操作**必须**更新 `grammar/meta/version.json` 的 `rules_version`（minor +0.1.0；新规则添加是 minor，规则形态变更是 major）。
- 每次维护操作必须更新 `grammar/meta/source-registry.json`：对应素材的 `last_extracted_at` / `last_consolidated_at`。
- 维护操作不影响已经生成的 `examples/` 和 `provenance.yaml` 历史档案。

---

## 五、输出风格规范（贯穿全流程）

- 每个阶段开始前**先用一句话告诉用户当前在干什么**（"Now retrieving candidate rules from grammar..."）。
- 进入 B5 闸门时输出 verdict 和 issues 摘要；不要把 rationale-judge 的完整 JSON 倾泻给用户。
- B6 输出后用 markdown 表格列出三份产物路径和大小。
- 若任何步骤遇到不可恢复错误（grammar 损坏、素材为空），立刻停下、说明、给出修复建议；不要硬撑生成残缺产物。

---

## 六、数据 Schema 速查

下列 schema 是各阶段产出物的契约。详细字段语义见各 `prompts/` 与 `scripts/` 子文档；这里只列摘要供主流程查阅。

### 3.3.1 Token Schema (`grammar/tokens/<system>.json`)

```json
{
  "system_name": "linear",
  "source": "open-design-71",
  "extracted_at": "2026-05-03T10:00:00Z",
  "color":      { "primary": "#5E6AD2", "neutral_scale": ["..."], "semantic": {} },
  "typography": { "display_family": "...", "body_family": "...", "scale": [], "line_height_rules": {} },
  "spacing":    { "base": 4, "scale": [4,8,12,16,24,32,48,64] },
  "radius":     { "sm": 4, "md": 8, "lg": 12 },
  "contrast":   { "body_on_bg": 7.2 },
  "components": { "button": "...", "card": "..." }
}
```

### 3.3.2 Rationale Schema (`grammar/rationale/<system>.md`)

每个 decision 三段式：`decision` / `trade_off` / `intent` / `avoid[]`。

### 3.3.3 Rule Schema (`grammar/rules/<system>.yaml`)

```yaml
rule_id: linear-color-balance-001
preconditions:
  product_type: [developer_tool, b2b_saas]
  tone: [professional, modern]
  kansei: [structured, calm, confident]
action:
  hue: blue with slight purple shift (240°-260°)
  saturation: medium-low (0.40-0.50)
  lightness: medium (0.50-0.60)
  contrast_with_bg: 4.5+
why:
  establish: engineering_credibility
  avoid: [medical_coldness, gaming_aesthetics]
  balance: precision ↔ warmth
emerges_from: [linear, vercel, supabase]
provenance: original   # original | generated | merged
confidence: 0.85
```

### 3.3.4 Rules Graph Schema (`grammar/graph/rules_graph.json`)

每个节点：`rule_id` + `relations.{depends_on, constrains, co_occurs_with[freq], conflicts_with}`。

### 3.3.5 调性画像 Schema (B1 输出)

```yaml
mode: interactive | auto
inferred_fields: [audience, ...]   # auto 模式下哪些字段是推断的
product_context:
  category: spiritual_saas
  audience: ...
  unique_constraints: [...]
brand_archetypes:
  primary: Sage
  secondary: Magician
kansei_words:
  positive: [mystical, ancient, trustworthy, structured, calm]
  reverse_constraint: [modern]
semantic_differentials:
  warm_to_cold: -0.2
  ornate_to_minimal: 0.3
  serious_to_playful: -0.7
  modern_to_classical: 0.0
```

### 3.3.6 Clarification Batch Schema (B1a 产出)

```yaml
clarification_batch:
  preamble: |
    我准备开始为你的产品设计一份专属的设计系统。
    在开始之前，我有几个问题需要一次性问完——
    回答完之后，我会一气呵成地完成整个设计，中途不会再打断你。
  questions:
    - id: audience
      question: ...
      type: single_select | multi_select | open_text | semantic_differential
      options: [...]
      why_we_ask: ...
      criticality: high | medium | low
  question_count: 5   # 上限 7
```

### 3.3.7 Provenance Report Schema (B4 输出)

每个决策三段式：`inheritance.{source_rules, source_systems, original_rationale}` + `adaptation.{fully_aligned_kansei, needs_extension_kansei, modifications[], preserved[]}` + `justification.{internal_consistency[], user_kansei_coverage, conflict_check}`。

详细字段见 `prompts/b4-generation-with-rationale.md`。

---

## 七、Anti-Patterns（绝对不能做）

- ❌ **不能在 B2 之后向用户追问任何信息**（包括 B3 / B4 / B5）
- ❌ **不能 interactive 模式下让 batch 超过 7 题**（超过就强制 B1a 重新规划）
- ❌ **不能在生成中途引入 B3 候选集之外的新规则**（B4 是翻译不是创造）
- ❌ **不能让 rationale-judge 评判方与 B4 生成方共享上下文**（必须独立 subagent）
- ❌ **不能让 P0 闸门超过 2 轮迭代**（卡住就退到更早阶段，不要无限 loop）
- ❌ **不能产 AI slop**（紫渐变 + Inter + 圆角卡片那一套，过 `references/anti-slop-blacklist.md`）
- ❌ **不能在空规则库上硬生成**（先提示用户导入起步素材）
- ❌ **不能让产物缺三段式 rationale 中的任何一段**（这是双向对称原则的核心）
- ❌ **不能让 auto 模式下推断字段在 negotiation-summary 里隐身**（必须显式列出供反馈）
- ❌ **不能不更新 adaptation-stats.json**（自演化机制依赖它）

---

## 八、参考资源

- `prompts/` — B 阶段每一步的执行指引
- `scripts/` — 维护流程的执行指引
- `../../agents/rationale-judge.md` — P0 闸门评判方（plugin 级 agent，通过 `Agent(subagent_type="rationale-judge", ...)` 调用）
- `references/` — 理论基础（按需引用，主流程不全读）
  - `kansei-theory.md` — 调性词与设计参数的桥梁
  - `brand-archetypes.md` — 12 原型分类
  - `shape-grammar.md` — 规则反推 + 生成机制
  - `pattern-language.md` — 规则关系图
  - `reflective-practice.md` — Rationale 叙事化
  - `design-md-spec.md` — DESIGN.md 9-section 标准
  - `anti-slop-blacklist.md` — AI slop 黑名单
- `grammar/meta/` — 规则库元数据（version / source-registry / provenance-index / adaptation-stats / defaults）
- `source-design-systems/_registry.md` — 素材库登记
