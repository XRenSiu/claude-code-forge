# B1a — 一次性追问（interactive 模式）

> 当 SKILL.md 主流程进入 B1a 时读取本文件作为执行指引。

## 你的任务

把"做出好设计需要但当前不知道"的所有维度**一次性**问完，硬上限 7 条。回答完后立刻进入 B2-B6，绝不再打断用户。

---

## Step 1 — 维度识别

读用户的产品需求，对照下面这张"信息缺口扫描表"，逐项打勾"已知 / 未知 / 可推断"：

| 维度 | 为什么影响设计判断 | 推断难度 |
|---|---|---|
| product_category | 整个 Kansei 与 Archetype 检索的起点 | 低（关键词通常足够） |
| target_audience | 决定信息密度、字号节奏、复杂度容忍度 | 中（需求描述常省略） |
| primary_use_context | 桌面长会话 / 移动碎片 / 嵌入式 → 影响 layout、interaction model | 中 |
| brand_archetype_primary | 整套调性的第一原型（Sage / Magician / Hero / Caregiver / Outlaw / Creator / Innocent / Lover / Ruler / Jester / Everyman / Explorer） | 中（关键词常带暗示） |
| brand_archetype_secondary | 第二原型，定调适方向 | 高（多数情况要问） |
| tone_pole_serious_playful | -1（严肃）↔ +1（顽皮）的 SD | 中 |
| tone_pole_warm_cold | 冷暖基调 | 中 |
| tone_pole_modern_classical | 现代轻盈 ↔ 传统厚重 | 中 |
| tone_pole_ornate_minimal | 装饰繁复 ↔ 极简留白 | 中 |
| reverse_constraints | 必须避免的调性词（"不要 X"） | 高 |
| competitive_reference | 用户心里把谁当假想敌 / 不想像谁 | 高 |
| unique_constraints | 行业 / 法规 / 受众的硬约束 | 高 |
| color_no_go | 颜色禁用区（文化 / 品牌冲突） | 高 |
| existing_assets | 已有 logo / VI / 字体 / 颜色 | 高 |

## Step 2 — 排序与裁剪

1. 给每个**未知**维度打 `criticality`：
   - **high**：缺它会让 B2 检索严重偏移（archetype、reverse_constraints、unique_constraints）
   - **medium**：缺它会让风格岛聚集错位（SD 维度、competitive_reference）
   - **low**：缺它会让产物略偏默认值（color_no_go、existing_assets）

2. 按 criticality 降序，再按"用户回答成本"升序（select 题 < open_text 题），取 **top-7** 进入 batch。

3. 其余未知维度**走默认推断**，记下来后续在 negotiation-summary.md 中暴露。

**硬规则**：如果识别出的 high criticality 维度 > 7 条，**重新规划**——通常意味着把多个细维度合并成一个高层选择题。例如别问 4 条 SD，问"在以下四组对极组合里选一组最贴近你产品调性的"。

## Step 3 — 编写问题

每条问题必须符合 schema：

```yaml
- id: <slug>
  question: <一句话，必须直接、不绕弯>
  type: single_select | multi_select | open_text | semantic_differential
  options: [...]                # select 类型必须给 3-6 个有意义的选项
  poles: [<左极>, <右极>]        # semantic_differential 类型必须给两端文字
  why_we_ask: <为什么这条问题对设计判断有效，一句话>
  criticality: high | medium | low
```

**问题质量要求**：

- **不**问"你想要什么风格"——这是把工作甩给用户
- 问可被翻译成 SD / Archetype / Kansei 的具体选择题
- 选项必须**有立场**，不要"现代风、简约风、专业风"这种空话
- 例子（好）：" 你希望产品的视觉感受更接近 ' 古老典籍的神秘感 '（Sage+Magician）还是 ' 现代极简的科技感 '（Sage+Creator）？"
- 例子（坏）：" 你想要什么颜色？" — 颜色应由 B4 推导，不该问用户

## Step 4 — 输出 batch

输出格式严格按 SKILL.md §六 3.3.6 的 `clarification_batch` schema。preamble 必须告知"问完就一气呵成、中途不再打断"。

输出后**等用户回答**，不主动进入 B2。

## Step 5 — 解析回答 + 合成画像

用户回答后：

1. 把 select / SD 答案直接映射到画像字段
2. open_text 答案用 NLP 方式提取关键词，映射到 kansei_words / unique_constraints
3. 走默认的字段从 `grammar/meta/defaults.yaml` 拿
4. 合成完整的"调性画像"（schema 见 SKILL.md §六 3.3.5），mode 字段填 `interactive`

**画像构建后立即进入 B2，不要再确认。**

---

## 检查清单（B1a 产出前必过）

- [ ] 问题数量 ≤ 7
- [ ] 每条问题都有 `criticality` 和 `why_we_ask`
- [ ] preamble 已声明"一气呵成、不再打断"
- [ ] high criticality 维度全部进入 batch（或合并进入）
- [ ] 没有问"你想要什么颜色 / 字体 / 圆角"这类越权问题
- [ ] 选项不空话、有立场
