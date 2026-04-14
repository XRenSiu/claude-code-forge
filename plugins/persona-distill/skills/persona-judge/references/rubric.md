---
rubric: persona-judge
version: 0.1.0
total_max: 110
pass_threshold_raw: 82
density_floor: 3.0
borrowed_from: softaworks/agent-toolkit/skill-judge + nuwa-skill three-tests + anti-distill density
---

# persona-judge Rubric / 评分细则

> 满分 **110 raw**，默认通过线 **82 raw**（约 74.5%）。所有 gating 使用 **raw 分**；归一化到 /100 仅用于展示，可能丢失精度（见 `../../../contracts/validation-report.schema.md` §Scoring Math）。

## Overview

本 rubric 将 "这个 persona skill 到底有多像本人" 拆成 12 个可打分维度，合计 **110 raw**。维度来源分三脉：(a) **nuwa 6 项** —— Known / Edge / Voice 三测（来自 nuwa-skill Phase-4）加上 Knowledge Delta / Mindset Transfer / Anti-Pattern Specificity 三条真实性门槛，共同回答 "输出像不像本人"；(b) **skill-judge 3 项** —— Specification Quality（frontmatter/trigger）、Structure（行数/层级/progressive disclosure）、Primary Source Ratio（一手来源比），回答 "作为 skill 工程品是否合格"；(c) **结构真实性 2 项 + 密度 1 项** —— Internal Tensions 与 Honest Boundaries 确保 persona 不是单调英雄像，Density 用反向 anti-distill 分类器防止 "结构完整但全是废话"。6 + 3 + 2 + 1 = 12。

10 分维度 × 10 = 100；5 分维度（Specification Quality、Structure）× 2 = 10；合计 **110 raw**。任意 2 个或更多维度得 0 分 → 强制 FAIL；`density_score < 3.0` → 强制 FAIL（见 §Critical Failure Rules）。维度顺序与 `validation-report.schema.md` frontmatter `dimensions:` 字段严格一致，便于机读对齐。

## Dimension Table / 维度表

| # | Dimension | Max | Source | Measurement | Failure (=0) Condition |
|---|-----------|-----|--------|-------------|------------------------|
| 1 | Known Test / 已知题 | 10 | nuwa Phase-4 | 3 道已知问题与本人公开答复的语义/措辞接近度 | 3 题在实质上全部答错或严重跑题 |
| 2 | Edge Test / 越界题 | 10 | nuwa Phase-4 | 1 道语料未覆盖的问题，是否以本人口吻诚实表达不确定 | 自信地编造（confident hallucination） |
| 3 | Voice Test / 口吻盲测 | 10 | nuwa Phase-4 | 100 字盲测由人或 LLM 评审识别为本人概率 | 与通用助手完全无法区分 |
| 4 | Knowledge Delta / 知识增量 | 10 | nuwa authenticity | 相较 baseline Claude，这个 skill 新增了哪些本人特有内容 | 与 baseline 完全无差异 |
| 5 | Mindset Transfer / 思维迁移 | 10 | nuwa authenticity | 思考框架/决策路径被传递，而非仅事实堆砌 | 只有事实，无框架 |
| 6 | Anti-Pattern Specificity / 反模式具体度 | 10 | nuwa authenticity | 组件中反模式是否具体可证伪 | 仅有 "要专注用户" 式通用警告 |
| 7 | Specification Quality / 规格质量 | 5 | skill-judge | frontmatter 完整 + description + triggers 可发现 | frontmatter 缺失/畸形导致 Claude 加载失败 |
| 8 | Structure / 结构 | 5 | skill-judge | 行数预算 + 层级 + progressive disclosure 合规 | 单体巨型文件或内部链接断裂 |
| 9 | Density / 密度 | 10 | anti-distill 反向分类 | 段落加权密度分（见 `./density-scoring.md`）；< 3 强制 FAIL | 总分 < 3（此时整个 skill 直接 FAIL） |
| 10 | Internal Tensions / 内在矛盾 | 10 | SPEC-04 / nuwa | 至少 `required_tensions`（默认 2）对未解矛盾被显式记录 | 0 对矛盾，或所有矛盾都被 "妥善解决" |
| 11 | Honest Boundaries / 诚实边界 | 10 | SPEC-04 / nuwa | 至少 `required_boundaries`（默认 3）条具体局限 | 0 条，或仅 "我可能有偏见" 式套话 |
| 12 | Primary Source Ratio / 一手来源比 | 10 | skill-judge | manifest 中 `source.type == primary` 的比例 ≥ `primary_source_min` | manifest 不含 source 元数据，或比例为 0 |

## Per-Dimension Detail / 分维度细则

### 1. Known Test — 已知题（max 10）

**Source**: nuwa-skill Phase 4 三测之 Known。
**Measurement**: 从语料中抽 3 道 **本人公开答复已知** 的问题，让 persona skill 回答；与原答对比语义一致性、关键词复现率、判断方向。3 道题的**选题要求**：(a) 覆盖不同知识域（避免同领域扎堆）；(b) 原答案长度 ≥ 100 字（短答缺乏打分信号）；(c) 公开时间距今 < 5 年（时效漂移可控）。
**Reproduction of test items**: 3 道题原文 **必须在 `Test Evidence` 段完整贴出**，含本人原答 URL / 出处，便于复评。
**Anchors**:
- **10**: 3/3 近乎逐词命中（near-verbatim），关键名词术语与倾向完全一致。
- **7**: 3/3 语义一致但措辞有偏差，或 2/3 近逐词 + 1/3 语义一致。
- **5**: 2/3 语义一致，1/3 方向偏离。
- **3**: 1/3 命中，2/3 跑题或空泛。
- **0**: 全部 3 题在实质上答错。

### 2. Edge Test — 越界题（max 10）

**Source**: nuwa-skill Phase 4 三测之 Edge。
**Measurement**: 构造 1 道确认 **语料未覆盖** 的问题；观察 persona 是否 (a) 以本人口吻 (b) 诚实表达不确定 (c) 说明为什么此题越界。
**Anchors**:
- **10**: 以本人口吻表达不确定，并指出知识边界。
- **7**: 表达不确定但口吻偏通用。
- **5**: 回避而非承认。
- **3**: 含糊作答，未标注不确定。
- **0**: 自信地编造（confident hallucination）。

### 3. Voice Test — 口吻盲测（max 10）

**Source**: nuwa-skill Phase 4 三测之 Voice。
**Measurement**: 100 字节选答复，交给 **人类或独立 LLM 评审**（不知来源）判断是否可被识别为本人。
**Anchors**:
- **10**: 毫无歧义识别，附可指向的语言特征（口头禅、节奏、典型隐喻）。
- **7**: 识别正确但信心低。
- **5**: 评审在 2-3 个候选间摇摆。
- **3**: 仅凭话题/领域猜对，语言特征模糊。
- **0**: 与通用助手不可区分。

### 4. Knowledge Delta — 知识增量（max 10）

**Source**: nuwa authenticity pillar。
**Measurement**: 将同一问题分别交给 (a) baseline Claude (b) 应用 persona skill 的 Claude，比对新增的本人特有事实 / 判断 / 案例数。
**Anchors**:
- **10**: 至少 5 条 baseline 不会自然给出的本人特有内容。
- **7**: 3-4 条新增。
- **5**: 1-2 条新增。
- **3**: 仅重新表述 baseline 内容。
- **0**: 无任何可检测的增量。

### 5. Mindset Transfer — 思维迁移（max 10）

**Source**: nuwa authenticity pillar。
**Measurement**: 考察是否传递 **本人如何思考**（决策启发式、取舍框架、优先级排序），而非仅 "本人相信 X"。
**Anchors**:
- **10**: 决策启发式清晰、可复用到新情境。
- **7**: 有框架但边界不清。
- **5**: 有倾向没有框架。
- **3**: 事实堆砌穿插口号。
- **0**: 只有事实，无任何可迁移的思考模式。

### 6. Anti-Pattern Specificity — 反模式具体度（max 10）

**Source**: nuwa authenticity pillar。
**Measurement**: 检查组件文件中 "本人反对什么 / 不做什么" 是否具体到可证伪（指名场景、给出反例）。
**Anchors**:
- **10**: 每条反模式都有具体情境 + 反例 + 本人明确反对。
- **7**: 多数具体，少量泛化。
- **5**: 一半具体一半泛化。
- **3**: 大多数是 "避免过度工程化" 式通用警告。
- **0**: 仅有通用警告，无任何本人特有反模式。

### 7. Specification Quality — 规格质量（max 5）

**Source**: softaworks/agent-toolkit/skill-judge。
**Measurement**: SKILL.md frontmatter 完整性 + description 可触发性 + triggers 列表质量。
**Anchors**:
- **5**: frontmatter 全字段齐备；description 含 "use when" 三场景；triggers 覆盖中英双语自然语。
- **3**: 字段齐但 triggers 过窄 / description 偏总结而非触发。
- **1**: 缺少 `description` 或 `when_to_use`。
- **0**: frontmatter 缺失或畸形，导致 Claude 无法发现/加载该 skill。

### 8. Structure — 结构（max 5）

**Source**: softaworks/agent-toolkit/skill-judge。
**Measurement**: 行数预算（SKILL.md < 300 行）+ progressive disclosure（深度内容下沉到 `references/`）+ 内部链接完整。
**Anchors**:
- **5**: SKILL.md 250-300 行内、深度内容下沉、所有相对链接可达。
- **3**: 行数超标 10-30% 或 1-2 处断链。
- **1**: 单体化严重 / 多处断链。
- **0**: 单一文件承载全部内容（无 references/components）或链接系统性损坏。

### 9. Density — 密度（max 10）

**Source**: 反向使用 `anti-distill` 4 级分类器。
**Measurement**: 见 `./density-scoring.md`。对每个段落打 `REMOVE`(+2) / `MASK`(+1) / `SAFE`(0) / `DILUTE`(-1)，求和归一化到 [0, 10]。
**Anchors**:
- **10**: 平均每段 ≥ 1.5 加权分，几乎无 DILUTE 段。
- **7**: 均值 ~1.0，少量 DILUTE。
- **5**: 均值 ~0.6，DILUTE 段占比 < 20%。
- **3**: **硬底线** —— 若低于此则 `verdict: FAIL`，不论总分。
- **0**: 大部分段落为 "正确废话"。
**Hard rule**: `density_score < 3.0` → 强制 FAIL。

### 10. Internal Tensions — 内在矛盾（max 10）

**Source**: SPEC-04（risk assessment），阈值 **默认 2，借自 nuwa-skill**，可在 `config.yaml` 覆写。
**Measurement**: 统计 persona 中被显式记录 **未解决** 的矛盾对（如 "注重效率 vs 注重关怀"）。
**Anchors**:
- **10**: ≥ `required_tensions` 对（默认 2），每对都有具体情境、无强行调和。
- **7**: 达数量但 1 对被勉强 "合题"。
- **5**: 低于阈值 1 对，但已有内容质量高。
- **3**: 仅 1 对且含糊。
- **0**: 0 对矛盾，或所有矛盾都被 "妥善解决" / 英雄化处理。

### 11. Honest Boundaries — 诚实边界（max 10）

**Source**: SPEC-04，阈值 **默认 3，借自 nuwa-skill**，可在 `config.yaml` 覆写。
**Measurement**: persona 中具体陈述的 "这个 skill 做不到 / 会犯错 / 语料缺失" 的条目。
**Anchors**:
- **10**: ≥ `required_boundaries`（默认 3）条具体边界，均指向场景 / 时间窗 / 领域。
- **7**: 条数达标但 1 条偏通用。
- **5**: 条数低于阈值 1 条，其余具体。
- **3**: 仅 1-2 条，且表述空泛。
- **0**: 0 条，或仅 "我可能有偏见" 式通用免责声明。

### 12. Primary Source Ratio — 一手来源比（max 10）

**Source**: softaworks/agent-toolkit/skill-judge。
**Measurement**: 读取 `manifest.json` 中 `sources[]`，统计 `type == "primary"` 的比例 `r`。
**Anchors** (linear scaling below 0.5)：
- **10**: `r ≥ primary_source_min`（默认 0.5）。
- **8**: `r ∈ [0.4, 0.5)`。
- **5**: `r ∈ [0.25, 0.4)`。
- **3**: `r ∈ [0.1, 0.25)`。
- **0**: `r < 0.1`，或 manifest 无 source 元数据。

## Critical Failure Rules / 致命规则

覆盖总分的强制 FAIL 条件（与 `../../../contracts/validation-report.schema.md` §Scoring Math 完全对齐）：

1. **`density_score < 3.0`** → `verdict: FAIL`。理由：防止结构工整的废话通过。
2. **≥ 2 个维度得 0 分** → `verdict: FAIL`，`critical_failures ≥ 2`。理由：单项 0 分是缺陷，多项 0 分是结构性坍塌。
3. **`manifest.json` schema 校验失败**（任一 `contracts/manifest.schema.json` 违规）→ `verdict: FAIL`，全 12 维清零，`critical_failures: 12`，`Recommended Actions` 必须列出具体 schema 违规。

## Verdict Mapping / 判决映射

按以下优先级求值，首个命中即终判：

| 条件 | Verdict |
|------|---------|
| 命中任一 Critical Failure Rule | **FAIL** |
| `raw ≥ pass_threshold_raw`（默认 82）且无致命项 | **PASS** |
| `raw ∈ [75, pass_threshold_raw)` 且无致命项 | **CONDITIONAL_PASS** |
| `raw ≥ pass_threshold_raw` 但恰有 1 个 0 分维度 | **CONDITIONAL_PASS** |
| 其他 | **FAIL** |

`CONDITIONAL_PASS` 的语义：**放行但附 `Recommended Actions`，由上游（distill-meta 或用户）决定是否继续迭代**。详见契约 §Contract for Consumers。

## PRD Discrepancy Note / PRD 差异说明

PRD §4.2 原文写 "**通过门槛 75**"（语境上接近归一化 /100 标尺），而 `validation-report.schema.md` 契约给出的是 `pass_threshold_raw: 82`（raw /110 标尺）。换算：`round(82 * 100 / 110) = 74.5`，四舍五入 **约等于 PRD 的 75 但不完全等同**。本 rubric 在以下原则上解决冲突：

- **契约优先** —— gating 逻辑一律使用 `pass_threshold_raw: 82`。契约是机读字段的权威来源，PRD 是意图表述。
- **PRD 精神保留** —— `CONDITIONAL_PASS` 段带 `[75, 82)` 恰好覆盖 PRD "75 能过" 的 spirit：raw 落在此区间的 skill **不会被判 FAIL**，只会被要求 review。换言之，PRD 的 75 从 "硬通过线" 降级为 "软通过线"，严苛程度提升但不背离 PRD 意图。
- 此差异已在 `## Summary` 段的生成模板中提示审计者感知。

## Configurable Thresholds / 可配阈值

用户通过 `plugins/persona-distill/skills/persona-judge/config.yaml` 覆写以下默认值（默认全部来自 nuwa-skill 基线）：

```yaml
pass_threshold_raw: 82       # PASS 下限（raw /110）
density_floor: 3.0           # density 硬底线
required_tensions: 2         # Internal Tensions 满分所需的未解矛盾对数
required_boundaries: 3       # Honest Boundaries 满分所需的具体边界数
primary_source_min: 0.5      # Primary Source Ratio 满分所需一手源比例
critical_failure_count: 2    # 触发强制 FAIL 的 0 分维度阈值
```

所有实际生效阈值 **必须写入** `validation-report.md` 的 `## Summary` 段末，保证每份 report 可独立复现判决。

## Anti-Gaming / 反作弊

用户可能用以下手段粉饰分数；评审者（人或 LLM）需按对应启发式识别并扣分：

| 作弊手段 | 描述 | 识别启发式 | 处置 |
|----------|------|------------|------|
| **Padding Tensions** | 编造虚假矛盾对凑够 `required_tensions` | 矛盾双方无独立实例支撑 / 情境为空 / "矛盾" 互为同义改写 | Internal Tensions 直接判 3 或 0 |
| **Boilerplate Boundaries** | 用 "我可能有偏见" / "知识有截止日期" 凑 `required_boundaries` | 边界未指向具体场景 / 时间窗 / 领域 | Honest Boundaries 直接判 3 或 0 |
| **Known-Test Leakage** | 把 Known Test 题目答案直接塞进 SKILL.md 主体 | 答案文本与 SKILL.md 字符串重叠度 > 80% | Known Test 记 0 并在 `## Weaknesses` 标注 `leakage` |
| **Density Inflation** | 堆砌高密度术语段以提升 REMOVE 计数但内容仍泛化 | anti-distill 分类器看术语还要看具体判断；评审抽查 3 段人工复核 | 以人工复核为准覆盖机器分 |
| **Primary Source Mislabel** | manifest 中把二手引用标为 `primary` | 抽查 3 条交叉验证来源 URL / 出版类型 | 直接归为 `secondary` 重算比例 |
| **Voice Mimicry Without Substance** | 刻意堆砌本人口头禅但无判断迁移 | Voice 高分但 Mindset Transfer 低于 3 的组合是红旗 | 在 `## Weaknesses` 强制记录 "voice-without-mindset" |
| **Component Link Theater** | 大量空组件文件撑起 progressive disclosure 表象 | 组件文件行数 < 20 或 80% 为标题的比例 > 30% | Structure 判 1 |
| **PRD Threshold Arbitrage** | 故意利用 75 与 82 的差异构造刚好卡在 [75, 82) 的 skill | 同一 persona 多次评估 raw 稳定落入此区间视为可疑 | 上游（distill-meta）记录迭代次数，超 3 次不再放行 `CONDITIONAL_PASS` |

核心原则：**rubric 是审计工具不是考试大纲**。任何试图把 rubric 当规范刷分的行为本身就是退化信号，评审者应倾向扣分而非纵容。

## Worked Examples / 打分示例

### Example A — Borderline CONDITIONAL_PASS

```
Known=7  Edge=6  Voice=8  KnowledgeDelta=7  Mindset=6  AntiPattern=7
Spec=4   Structure=4  Density=5  Tensions=8  Boundaries=7  PrimarySrc=8
Raw sum = 77  (7+6+8+7+6+7+4+4+5+8+7+8)
```
77 ∈ [75, 82)，无 0 分维度，density ≥ 3 → **CONDITIONAL_PASS**。必须写 `Recommended Actions` 聚焦 Density（5 → 目标 ≥ 7）和 Specification Quality。

### Example B — FAIL by density floor

```
Raw sum = 95 but density_score = 2.8
```
总分虽高，但 `density < 3.0` → **FAIL**，理由栏写 `density-floor-breach`，`Recommended Actions` 必须列出具体 DILUTE 段落路径。

### Example C — FAIL by critical-failure count

```
Known=0  Edge=0  Voice=9  ... raw = 85
```
raw ≥ 82 但 **2 个维度得 0** → **FAIL**。理由：测试基础不通过，高结构分无法补偿。

## Evaluator Workflow / 评审者工作流

1. **加载阈值** —— 先从 `config.yaml` 读覆写值，再按默认补齐；最终值写入 report 的 `## Summary`。
2. **计算原始分** —— 12 维分开计算，不允许 "总体印象打分后反向拆分" 的反模式。
3. **应用致命规则** —— Critical Failure Rules 优先于 Verdict Mapping。
4. **反作弊扫描** —— 跑完基础评分后按 `## Anti-Gaming` 的 8 条启发式逐一排查并在 `## Weaknesses` 记录发现。
5. **生成 Recommended Actions** —— 每条必须指向 **具体文件路径 + 具体改动**（契约要求）。无具体 action 的维度扣分无法复用。
6. **写入历史快照** —— 同时写 `validation-report.md` 和 `versions/validation-report-{ISO8601}.md`。

---

**Traceability**: 本文件所有阈值与致命规则均可溯源至 `../../../contracts/validation-report.schema.md`、`plugins/persona-distill/skills/persona-judge/SKILL.md`、SPEC-04（tensions / boundaries 阈值）、SPEC-07（raw-score gating + 110→100 display-only）。任何数值变更必须先改契约再改本文件并 bump version。
