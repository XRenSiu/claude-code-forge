# extract-grammar — 单套 DESIGN.md 拆解 4 步流程

> 被 `add-new-design-system.md` / `import-from-collection.md` / `rebuild-graph.md` 调用，也可独立跑。

## 输入

一个具体的 `<system_name>`（例如 `linear`），其 DESIGN.md 已经位于 `source-design-systems/<system_name>/DESIGN.md`。

## 输出

- `grammar/tokens/<system_name>.json`
- `grammar/rationale/<system_name>.md`
- `grammar/rules/<system_name>.yaml`
- 更新 `grammar/graph/rules_graph.json`（增量）

---

## A1 — Token 层提取

### 目标

把 9-section 中所有显式参数结构化，作为后续步骤的事实锚点。

### 步骤

1. Read `source-design-systems/<system_name>/DESIGN.md`
2. 按 schema（SKILL.md §六 3.3.1）提取：
   - **Color**：所有 hex / rgb / hsl 值，区分 primary / neutral_scale / semantic
   - **Typography**：字体家族、scale 数组、line_height 规则
   - **Spacing**：base unit + scale 数组
   - **Radius / Shadow / Motion**：所有原始值
   - **Components**：button / card / input 等的描述（保留原文）
3. 写到 `grammar/tokens/<system_name>.json`，源字段 `source` 设为对应集合（如 "open-design-71"），`extracted_at` 用当前 ISO 8601

### 质量检查

- [ ] 9 个 section 都被扫描，缺失项标 `null` 而非省略
- [ ] 颜色值统一格式（建议 hex；hsl 的转 hex 时同时保留原始 hsl 在 `_raw` 字段）
- [ ] scale 数组元素是 number 不是 string

---

## A2 — Rationale 层抽取

### 目标

把每个 token 背后的"为什么"叙事化，**必须三段式**：`trade_off` / `intent` / `avoid`。

### 步骤

1. 重新读 DESIGN.md，重点关注每个 section 中的散文段落（不仅是参数表）
2. 对每个关键决策（一套设计系统通常 30-60 个）抽取：
   - `decision`：用一句话描述这个决策（例如"主色 #5E6AD2 偏紫的冷蓝"）
   - `trade_off`：在哪两端取了平衡（例如"工程精度感 ↔ 人文温度"）
   - `intent`：希望传达的核心感受（例如"严肃但不冷漠"）
   - `avoid[]`：明确想避免的视觉/感受（例如["纯蓝带来的医疗器械感", "纯紫带来的游戏 UI 感"]）
3. 如果 DESIGN.md 没明说 trade_off / avoid，**用文本证据推断**——但必须在 rationale 文件里加注 `[inferred]`，让后续读者知道哪条不是原文
4. 写到 `grammar/rationale/<system_name>.md`，按 section 分组

### 质量检查

- [ ] 每个 decision 三段式都有内容（trade_off / intent / avoid 都不是空字符串）
- [ ] avoid 项的措辞是具体的（"医疗器械感"），不是抽象的（"不专业感"）
- [ ] 推断条目标 `[inferred]`
- [ ] 如果某个 section（如 voice / motion）DESIGN.md 写得很简短，rationale 也对应简短，**不**强行编造

---

## A3 — Rule 层抽象

### 目标

把具体值（`#5E6AD2`）抽象成参数化模式（`hue: 240°-260°`），打 Kansei 标签作为 B 阶段检索的通用语言。

### 步骤

1. 读 tokens.json + rationale.md
2. 对每个 rationale decision 输出一条 rule，schema 见 SKILL.md §六 3.3.3：
   - `rule_id`：`<system>-<section>-<sequence>` 例如 `linear-color-balance-001`
   - `preconditions.product_type`：从 DESIGN.md 推断（这套设计系统主要服务什么类型产品）
   - `preconditions.tone`：从 rationale.intent 提取
   - `preconditions.kansei`：用 `references/kansei-theory.md` 的词表，给 3-5 个调性词
   - `action`：把具体值转参数化范围（hex → hue/saturation/lightness 区间；px → 倍数关系；font → category + tone）
   - `why.establish` / `why.avoid` / `why.balance`：直接复制 rationale 的对应字段
   - `emerges_from`：[<system_name>]（首次拆解时只有自己）
   - `provenance: original`
   - `confidence: 0.5`（首次单一系统拆解默认中等；后续合并 / 共现会自动调高）
3. 写到 `grammar/rules/<system_name>.yaml`

### 关键：参数化的颗粒度

| 维度 | 具体值 | 参数化模式 |
|---|---|---|
| Color | `#5E6AD2` | `hue: 240°-260°, saturation: 0.40-0.50, lightness: 0.50-0.60` |
| Spacing | `16px` | `base * 4`（如果 base=4） |
| Type scale | `[12,14,16,18,24,32,48]` | `geometric ratio ~1.25-1.5` 或 `linear +2px steps for body / +8px for display` |
| Radius | `8px md` | `medium-soft (4-12px)` |
| Easing | `cubic-bezier(0.16,1,0.3,1)` | `out-expo (gentle, dramatic landing)` |

### 质量检查

- [ ] 每条规则都有完整 preconditions（product_type 不为空 / kansei 不为空）
- [ ] action 是参数化的，不是具体值（具体值已在 tokens.json）
- [ ] kansei 词与 `references/kansei-theory.md` 词表对齐（不要造词）
- [ ] confidence 在 [0, 1]

---

## A4 — Pattern Language 关系图构建（增量）

### 目标

把新规则与已有规则的 4 类关系（depends_on / constrains / co_occurs_with / conflicts_with）写入 `grammar/graph/rules_graph.json`。

### 步骤

#### depends_on

对每条新规则 R，扫描已有规则：

- 如果 R 的 action 引用了某个其它规则的产物（例如 R 是 button 颜色规则，依赖 color-palette 规则的 primary color），加 `depends_on: [{rule: <prereq>, reason: ...}]`
- 标准依赖关系（**color → 其它**、**typography → spacing**、**components → 全部**）默认补全

#### constrains

`A constrains B` 是 `B depends_on A` 的反向边。对每条新规则的 depends_on 自动写入对应的 constrains。

#### co_occurs_with（带频率）

对每条新规则 R，扫描所有 source systems 中是否同时出现"语义相似"的规则。频率计算：

```
frequency = systems_having_both / systems_having_either
```

如果新规则与某个旧规则在 ≥3 套素材中共现 → 加 `co_occurs_with: {rule: ..., frequency: ...}`。**首次拆解时这个数据可能不充分**，没关系——`scripts/rebuild-graph.md` 会全量重算。

#### conflicts_with

对每条新规则 R，扫描已有规则：

- 如果 R 的 `why.avoid` 包含旧规则的 `why.establish` → 加 `conflicts_with: {rule: ..., reason: 该规则的 establish 是 R 的 avoid}`
- 如果 R 和旧规则的 `action` 在同一 dimension 上是相反方向（一个高饱和度、一个低饱和度，且在同一 product_type 区间）→ 同样加 conflicts_with

### 质量检查

- [ ] 每条新规则的 4 类关系都已扫描（即使是空的）
- [ ] depends_on 的 reverse（constrains）已自动补
- [ ] co_occurs_with 频率值在 [0, 1]
- [ ] conflicts_with 必须有 reason 文本，不能是空字符串

---

## 收尾

1. 更新 `grammar/meta/source-registry.json`：该 system 的 `last_extracted_at`
2. 更新 `grammar/meta/version.json`：`rules_version` minor +0.1.0（新增系统）
3. 更新 `grammar/meta/provenance-index.json`：登记新规则的 rule_ids → system 映射

完成后输出：

```
✅ Extracted <system_name>
   tokens: NN fields
   rationale: NN decisions
   rules: NN rules
   graph: +NN nodes, +NN edges (depends_on: NN, constrains: NN, co_occurs: NN, conflicts: NN)
```
