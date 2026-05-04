# B4 — 带 Rationale 生成

> 当 SKILL.md 主流程进入 B4 时读取本文件作为执行指引。引用 `references/shape-grammar.md`、`references/reflective-practice.md`、`references/design-md-spec.md` 加深理解。

## 你的任务

把 B3 的自洽规则子集**翻译**成 DESIGN.md 草稿（标准 9-section），并为每个决策产**三段式 Provenance Report**。

**严格约束**：

- 你是**翻译者**，不是创造者。任何决策都必须能追溯到 B3 子集里某条具体规则。
- 不向用户追问任何信息。
- 不引入 B3 子集之外的新规则。

---

## ⚠️ ANTI-PHANTOM 硬约束（v1.5.0 新增 — 必读必行）

**问题历史**：v1.4.0 之前 B4 在缺规则锚点时会编造 plausible-sounding rule_ids（如 `vercel-typography-geist-system-002` 不存在但听起来对）。P0 闸门虽能抓出，但用户首轮拿到的 provenance 含编造引用就破信任。

**v1.5.0 起强制三道闸**：

### 闸 1：写每条 inheritance.source_rules 之前先 echo 验证

**每**写一条 `source_rules: [X]`，**先**在工作内存里：

```
检查规则 X：
  - 在 B3 自洽子集里？  □ 是  □ 否（→ STOP，禁止使用）
  - 实际 rule_id 字符串完全一致（含 system 前缀和数字后缀）？  □ 是  □ 否（→ STOP）
  - 该规则的 why.establish / why.avoid / why.balance / action 字段我能逐字引用？  □ 是  □ 否（→ 改写 original_rationale 直到能引用）
```

**禁止编造启发式**：
- 不要根据"system X 应该有 Y 类规则"猜 rule_id（即使猜中了也算违规）
- 不要把范围参数（如 `brand_hue_range: [240, 270]`）压成虚构 scalar 默认值（如 "Linear 默认值 250"）
- 不要把"我推断 system X 也支持这个原则"写进 source_rules（推断不是继承）

### 闸 1.5（v1.5.1 新增）：original_rationale 必须 verbatim quote 不许 paraphrase

v1.5.0 之后发现的失误：B4 写 `original_rationale` 时把 rule.action 字段 paraphrase
得太自由，结果偏离了原文意思——例如：

- `notion-components-subtle-card-radius-010.action` 实际是 `card_radius_default_px: 4`（**单值**）
  → 我把它 paraphrase 成"radius 在 4-8 区间"（**伪造的 range**）
- `notion-typography-4-weight-system-007.action` 实际是 `weights_used: [400, 500, 600, 700]`（**允许 700**）
  → 我把它 paraphrase 成"窄 weight ladder, 不靠 700"（**完全相反**）

这都不是 phantom rule_id（rule 真存在），而是 **rule 内容 paraphrase 误读**，
危害几乎一样大。

**v1.5.1 起强制**：

- `original_rationale` 字段必须包含至少一段 **verbatim quotation** 来自该 rule 的
  `action` / `why.establish` / `why.avoid` / `why.balance` 字段，格式如下：

  ```yaml
  original_rationale: |
    <rule_id>.action 字段（verbatim）：
      <key1>: <value1>
      <key2>: <value2>
    why.establish: <一字不差>
    why.avoid: <一字不差>
  ```

- 然后才能用自己话总结这条规则的"意图"——但**总结必须紧贴 verbatim 内容，不许扩张**。

**好榜样**：

```yaml
original_rationale: |
  linear-app-color-translucent-borders-003.action 字段（verbatim）：
    border_strategy: semi-transparent white on dark surfaces
    border_alpha_range: [0.05, 0.08]
    avoid_solid_dark_borders_on_dark_bg: true
  why.avoid: [hard_edge_visual_walls, opaque_borders_on_dark]
```

**坏榜样**（v1.5.0 真实发生）：

```yaml
# 错 1：把 single value 4 说成 range 4-8
original_rationale: |
  notion-components-subtle-card-radius-010：卡片 radius 在 4-8 区间。

# 错 2：忽略 rule 实际允许 700，把它当成"反对 700"的证据
original_rationale: |
  notion-typography-4-weight-system-007 同支持"窄 weight ladder"，不靠 700 砸读者。
```

如果 verbatim quotation 显示规则**实际不支持**当前决策（如 notion-007 实际允许
700 for display），**必须从 source_rules 删掉这条引用**——不可硬撑解释。

### 闸 2：缺锚点时诚实声明 derived_from_brief

如果某个决策在 B3 子集里**找不到任何支持的规则**：

```yaml
- decision: <X>
  inheritance:
    source_rules: []          # 必须为空数组，不是占位 placeholder
    source_systems: []        # 必须为空
    original_rationale: |
      ⚠️ 此决策无规则库支持（已检查 B3 子集 N 条规则均无相关锚点）。
      派生自：<brief 中的具体段落 / archetype 默认 / 工业惯例>。
  adaptation:
    fully_aligned_kansei: []
    needs_extension_kansei: [<相关 kansei>]
    modifications: []
  justification:
    design_argument: |
      <为什么这个决策仍然合理 — 不能省，否则 P0 闸门会扣分>
  confidence: low             # 无锚点决策必须 low
  derived_from_brief: true    # 必填字段
```

**好榜样**：

- ❌ "Vercel 直接用 Geist 体现这一原则" + 编 `vercel-typography-geist-system-002`
- ✅ "Linear typography rule 要求 geometric/humanist sans + OpenType + 拒绝 Inter；选 Geist 是符合这组约束的现成字体（brief-derived，非规则原文要求）"

### 闸 3：调适越界必须显式标注（v1.9.0 扩展为 4 类）

每个 modification 必须把 source field 与 to value 的关系归到下面 4 类之一，**不许混淆或省略**。

#### 类 A：source 是范围 / 列表 / 显式枚举值

source rule 的 `action` 字段是**范围**或**显式枚举**时（如 `brand_hue_range: [240, 270]`、`weights_used: [400, 500, 600]`、`cta_verbs: [start, get_started, contact_sales]`）：

- 落在范围/枚举内 → 正常 modifications，**out_of_source_range: false**
- 落在范围/枚举外 → **必须** `out_of_source_range: true` + reason 解释为什么故意越界

```yaml
- dimension: saturation
  from: "[0.40, 0.55]"        # 引用规则原文的范围
  to: 0.60
  out_of_source_range: true
  reason: |
    deliberate excursion ...
```

#### 类 B：source 是标量（scalar）

source rule 的 field 是**单一标量值**时（如 `card_radius_default_px: 4`、`border_alpha_default: 0.05`）：

- 完全照搬 → 不该出现在 modifications，应在 `preserved` 列出
- **任何**值变化都是 out-of-source（标量没有"范围内"的概念）

```yaml
- dimension: border_alpha_default
  from: 0.05 (verbatim mintlify scalar — NOT a range)
  to: 0.06
  out_of_source_range: true     # 标量任何变化都是 true
  reason: |
    标量 0.05 → 0.06 不存在 in-range 一说
```

**禁止**：把标量的微小变化标 `out_of_source_range: false` 并写"in-band micro-adjustment"——标量没有 band。

#### 类 C：跨规则救援（cross-rule rescue）

当 to value 对**所引用的某条 source rule** 越界，但同时**对该 decision 引用的另一条 source rule** 在范围内时：

- **必须**用分离字段标记：`out_of_source_range_for_<rule_or_system>: true|false`（每条 source rule 一个）
- **必须**加 `cross_rule_rescue` 字段解释：哪条规则越界、哪条规则提供 in-source 锚点
- 跨规则救援的 source rule 必须真在 `inheritance.source_rules` 列表里——不能从未列出的规则借范围

```yaml
- dimension: border_alpha_default
  from: "0.05 (mintlify scalar) / [0.05, 0.08] (linear range)"
  to: 0.06
  out_of_source_range_for_mintlify: true
  out_of_source_range_for_linear-app: false
  cross_rule_rescue: |
    mintlify 的 0.05 是标量，0.06 越界。但 linear 的 [0.05, 0.08]
    范围内，所以跨规则救援成立。linear 已在本 decision 的 source_rules
    列表中（不是从外面借的）。
  reason: ...
```

**禁止**：从 source_rules 之外的规则借范围"救援"——那是 phantom citation，违反闸 1。

#### 类 D：source 字段未定义具体值（concretization）

当 source field 显式声明**不指定具体值**（如 vercel 的 `chromatic_accent_count: small_set_with_strict_semantic_role` — 字面是"小集合，未定数量"）：

- 选择具体值是**concretization**，**不是** out-of-source（source 没设上下界，怎么界定越界？）
- **必须**用 `concretization_of_undefined: true` 字段，而不是 `out_of_source_range`
- reason 必须说明：源字段为什么是 undefined、为何 OPC 选这个具体值

```yaml
- dimension: accent_set_size
  from: "small_set_with_strict_semantic_role (vercel — undefined cardinality)"
  to: 4
  concretization_of_undefined: true
  out_of_source_range: false        # 显式 false 防误读
  reason: |
    vercel 的 source 字段是文字描述非数字，"small_set" 没有 cardinality
    上下界。OPC 选 4 是 concretization 不是 excursion。
```

**confidence 政策（v1.9.0 明确）**：
- `out_of_source_range: true` → 单独触发 confidence ≤ medium（即使有 cross-rule rescue）
- `concretization_of_undefined: true` → **不**单独触发降级；但若 decision 同时有 out_of_source_range modification，整体仍降 medium
- 多个 concretization_of_undefined 也不降级，因为 source 本身就允许多种 concretization

#### 类 E：模式保留 + 字面值替换（pattern_preserved）

当 source field 是**字面例子列表**而非 closed enum（如 vercel 的 `cta_verbs: [start_deploying, get_started, contact_sales]` — 这是产品特定的字面例子，意图是"模式 = imperative short verbs"）：

- 替换字面列表 → `out_of_source_range: true`（字面值不一样了）
- 但 underlying 模式保留 → 加 `pattern_preserved: <pattern_name>` 字段说明
- pattern_preserved 不是降级豁免——confidence 仍按 out_of_source_range 政策走 medium

```yaml
- dimension: cta_verb_set
  from: "vercel literal: [start_deploying, get_started, contact_sales]"
  to: "OPC: [Resume, Halt, Replace skill, Approve & continue]"
  out_of_source_range: true           # 字面替换是越界
  pattern_preserved: imperative_short_action_verbs
  reason: |
    vercel.cta_verbs 是产品特定字面例子，OPC 替换为 OPC 特定动词，但
    voice_personality 字段（imperative_short_action_verbs 模式）verbatim 保留。
```

### 闸 4：输出前的 self-check 清单（v1.9.0 扩展）

写完整份 provenance 后，**在输出前**逐条过：

- [ ] 每条 `source_rules` 项都能在 B3 子集里找到（grep 验证）
- [ ] 每条 `source_systems` 项都至少有一条 `source_rules` 来自该 system
- [ ] **每个 modification 必须归到闸 3 的 5 类之一**（A 范围/列表 / B 标量 / C 跨规则救援 / D concretization / E pattern preserved）——不许混类或省略类别字段
- [ ] **标量字段（类 B）的任何变化都必须 out_of_source_range: true** —— 不许把标量微调标 false 写 "in-band"
- [ ] **跨规则救援（类 C）所救援的 source rule 必须真在本 decision 的 source_rules 列表里** —— 不能从未列出的规则借范围
- [ ] **concretization_of_undefined（类 D）和 out_of_source_range 互斥** —— 不能同时为 true
- [ ] 每条 `confidence: high` 的决策都没有 out_of_source_range（concretization_of_undefined 可以有）
- [ ] 每条无锚点决策都有 `derived_from_brief: true` + `confidence: low|medium`
- [ ] **顶层有 `kansei_primary_addresser` 矩阵**（见闸 5）

**任何一项不过 → 不许输出，回到该决策修正。**

### 闸 5：kansei coverage 矩阵（v1.9.0 新增）

per-decision 的 `user_kansei_coverage` 字段（addressed_in_this_decision / addressed_elsewhere）容易出现**双向循环引用**——A 说"sovereign 由 B addressed_elsewhere"，B 又说"sovereign 由 A addressed_elsewhere"，结果谁都没真锚定。

**v1.9.0 起强制**：provenance 顶层必须有 `kansei_primary_addresser` 矩阵，对**每个** user kansei.positive 词指定**唯一**的 primary addresser decision：

```yaml
kansei_primary_addresser:
  - kansei: structured
    primary_decision: "8px base spacing scale with optical micro-increments"
    primary_section: layout
    secondary_addressers:
      - "Translucent borders (color)"
      - "Pill status badge (components)"

  - kansei: precise
    primary_decision: "Display tracking curve — aggressive negative"
    primary_section: typography
    secondary_addressers: ...

  - kansei: composed
    primary_decision: null   # 显式 null 表示无 token-level decision
    note: see kansei_unaddressable.composed
```

**铁律**：
- 每个 user kansei.positive 词必须出现在矩阵里
- `primary_decision` 是**该 kansei 在 token level 最负责的那个 decision**——不许是 null 除非也在 `kansei_unaddressable` 顶层字段
- `primary_decision` 不允许两个 kansei 互指（A 是 B 的 primary AND B 是 A 的 primary 这种循环）
- 矩阵建立的关系图必须是 DAG（无环）

**Per-decision claim 与矩阵的协调约定（v1.9.0）**：

矩阵存在后，per-decision 的 `user_kansei_coverage.{addressed_in_this_decision, addressed_elsewhere}` 字段必须遵守：

1. **若该 decision 是某 kansei 的 matrix primary**：把这个 kansei 列在 `addressed_in_this_decision`，可标 `(matrix primary)` 后缀
2. **若该 decision 是 secondary**：把 kansei 列在 `addressed_elsewhere`，**必须**用反向指针格式 `kansei → 'matrix primary 决策名'`，不允许只写 kansei 名字
3. **不允许**两个 decision 都把同一个 kansei 列在 `addressed_in_this_decision`——只有 matrix primary 能这么写
4. 写完 provenance 后跑校验：每个 kansei 应该恰好有一个 decision 把它列在 addressed_in_this_decision，其他出现都是 addressed_elsewhere 形式

正确写法：

```yaml
# Decision A — 是 structured 的 matrix primary
user_kansei_coverage:
  addressed_in_this_decision: [structured (matrix primary)]
  addressed_elsewhere:
    - "calm → 'Translucent borders' (matrix primary)"

# Decision B — 是 structured 的 secondary，是 calm 的 matrix primary
user_kansei_coverage:
  addressed_in_this_decision: [calm (matrix primary)]
  addressed_elsewhere:
    - "structured → 'Decision A' (matrix primary)"
```

**为什么这样**：把 kansei 覆盖从分布式声明（每个 decision 各说各的）变成集中式权威（一处声明谁负责什么），消除循环引用同时让 reviewer 一眼看完全图。

---

## DESIGN.md 9-section 标准（OD 方言）

按 `references/design-md-spec.md` 的标准格式输出。**严格 9 个 section、严格顺序、含数字编号**：

1. **`## 1. Visual Theme & Atmosphere`**（散文 / 元 section）— 综合性总览，3-4 段 + Key Characteristics 列表
2. **`## 2. Color Palette & Roles`**（rule-bearing）— 按 role 分组的色板、Strategy 子段
3. **`## 3. Typography Rules`**（rule-bearing）— Font Family、Hierarchy 表、Principles
4. **`## 4. Component Stylings`**（rule-bearing）— Buttons / Cards / Inputs / Navigation / Distinctive
5. **`## 5. Layout Principles`**（rule-bearing）— Spacing / Grid / Whitespace Philosophy / Border Radius
6. **`## 6. Depth & Elevation`**（rule-bearing）— 层级表 + Shadow Philosophy 散文
7. **`## 7. Do's and Don'ts`**（元 section）— Do 列表 + Don't 列表，每条具体有立场
8. **`## 8. Responsive Behavior`**（元 section）— Breakpoints 表 / Touch Targets / Collapsing Strategy
9. **`## 9. Agent Prompt Guide`**（元 section）— Quick Color Reference + Example Component Prompts + Iteration Guide

**5 个 rule-bearing section**（`color / typography / components / layout / depth_elevation`）由规则的 `section` 字段直接对应。

**4 个元 section**（Visual Theme / Do's and Don'ts / Responsive / Agent Guide）由其它 section 的规则 + 调性画像 + brief 综合派生：

- **Visual Theme**：综合 5 rule-bearing section + 画像 archetype + kansei 写散文
- **Do's and Don'ts**：anti-pattern 规则（rule.section == `anti_patterns`） + 画像 reverse_constraint + 5 section 规则的 `why.avoid` 反向汇总
- **Responsive**：从 layout section 的 breakpoints 字段派生
- **Agent Prompt Guide**：从所有 section 关键决策抽取，给 AI agent 用

---

## 生成流程（按 section 逐个翻译）

### 阶段 1 — 写 5 个 rule-bearing section（Color / Typography / Components / Layout / Depth & Elevation）

对每个 rule-bearing section：

#### Step 1 — 拉规则

从 B3 子集筛出 `section == 当前section_slug` 的规则（slug 是 `color | typography | components | layout | depth_elevation`）。如果某条规则跨 section（罕见），重复使用。

### Step 2 — 翻译

把规则的 `action`（参数化模式）实例化为具体的 DESIGN.md 字段。例如：

规则：
```yaml
action:
  hue: blue with slight purple shift (240°-260°)
  saturation: medium-low (0.40-0.50)
  lightness: medium (0.50-0.60)
```

DESIGN.md：
```markdown
### Color > Primary
- value: #5E6AD2  (HSL 240° 45% 55%)
```

**调适规则**：当画像的 kansei / SD 与规则原 action 不完全一致时，必须调适。例如规则原本 `lightness: 0.55` 但画像 kansei 含 `ancient` → lightness 调到 0.32（暗色更接近古老感）。

### Step 3 — 写 Provenance Report

每个决策都必须产以下结构（schema 见 SKILL.md §六 3.3.7）：

```yaml
decision: 主色 #4A4080(深紫蓝)
section: color

inheritance:
  source_rules: [linear-color-balance-001]
  source_systems: [linear, vercel]
  original_rationale: |
    在工程精度感和人文温度之间取平衡。
    避免纯蓝的医疗冷感、纯紫的游戏感。

adaptation:
  fully_aligned_kansei: [structured, professional, calm]
  needs_extension_kansei: [mystical, ancient]
  modifications:
    - dimension: saturation
      from: 0.45
      to: 0.30
      reason: 降低饱和度让色彩更接近"夜空"而非"科技品牌"
    - dimension: lightness
      from: 0.55
      to: 0.32
      reason: 调暗增加古老感，呼应 ancient
  preserved:
    - hue: 250°（Linear 的"严肃但不冷漠"对当前场景同样成立）

justification:
  internal_consistency:
    - 与 typography 协同：深色背景的字体对比度已在 typography section 处理
    - 与 spacing 协同：神秘感的呼吸感已通过 1.5x base spacing 体现
  user_kansei_coverage:
    addressed_in_this_decision: [structured, calm, mystical, ancient]
    addressed_elsewhere: [trustworthy, professional]
    uncovered: []
  conflict_check:
    none

confidence: high
```

### Step 4 — 协同性核对

每写完一个 section 都暂停回看：

- 与已写完的前 N 个 section 的字段有冲突吗？（如 typography 用了 high-contrast 黑白但 color 又给了灰底灰字）
- 每条 `justification.internal_consistency` 都要能指向已写完的具体 section 字段，不能空泛

冲突 → 调当前 section 的决策（不动已写完的 section，避免反复）。如果发现根本性冲突（已写 section 也错），记录到 P0 闸门会发现的"global_issues"，由 B5 决定是否回炉。

### Step 5 — Anti-pattern 自查

每写完 section 都过一遍 `references/anti-slop-blacklist.md`：

- 用了紫色渐变？说明为什么这里**不是 slop**（场景特殊性）
- 用了 Inter？说明为什么这里**不是 slop**（确实匹配 archetype）
- 用了 12px 圆角卡片？说明为什么这里**不是 slop**（spacing 节奏的必然结果）

写不出来 → 说明就是 slop，必须调。

---

## 三段式 Provenance 的质量门槛

每个决策的三段式不能流于形式：

| 段 | 必须包含 | 不能是 |
|---|---|---|
| inheritance | 具体 rule_id 列表 + 至少一套 source system + 原始 trade_off/intent 文字 | "from various sources"（无具体引用） |
| adaptation | 如果有调适：列出每个 dimension / from / to / reason；如果完全照搬：明确 `preserved: ALL` 并说明原因 | 含糊的"slightly adjusted for the context" |
| justification | 至少一条 internal_consistency 指向具体已写 section + user_kansei_coverage 全字段 + conflict_check（none 或具体冲突） | "fits the user's needs"（没有可验证内容） |

---

## 输出物

1. **DESIGN.md 草稿**（路径暂时写到工作内存中，B5 通过后才落盘）
2. **Provenance Report**（YAML 数组，每条决策一项）
3. **Generation log**：记录哪些规则被使用了、每个 section 用了几条规则、调适的密度统计

把 (1)(2)(3) 都传给 B5。

---

### 阶段 2 — 写 4 个元 section（Visual Theme / Do's and Don'ts / Responsive / Agent Guide）

5 个 rule-bearing section 全写完后再写元 section。它们没有自己的规则——而是从已写的 section + 画像 + brief 综合派生。

**`## 1. Visual Theme & Atmosphere`**（注意它在最前，但**最后写**）：

1. 拿到所有 5 个 rule-bearing section 已写完的内容
2. 用 3-4 段散文综合：base canvas + 整体感觉 / 标志性样式举例 / 与其它系统的识别度区分
3. 末尾加 "Key Characteristics:" 列表，5-9 条要点，每条直接引用 rule-bearing section 的具体值

**`## 7. Do's and Don'ts`**：

1. 拉所有 `section == anti_patterns` 的规则的 `forbidden` 列表
2. 拉所有 5 rule-bearing section 规则的 `why.avoid` 反向汇总
3. 加上画像 `kansei_words.reverse_constraint` 的具体禁止表达
4. 拉 brief 中的 unique_constraints 反向（"不要又一个企业 SaaS" → Don't 列表条目）
5. 用 Do / Don't 两子段输出。Do 列表是反向的——基于 5 rule-bearing section 的 `why.establish` 提炼"做什么"

**`## 8. Responsive Behavior`**：

1. 主要派生自 layout section 的 breakpoints 字段
2. Touch Targets / Collapsing Strategy / Image Behavior 从 components section 推断
3. 如果 layout 规则没明确 breakpoints，用 brief 推断（developer_tool 默认含桌面优先；mobile-first 内容平台默认含 320/768/1024）

**`## 9. Agent Prompt Guide`**：

1. Quick Color Reference：从 color section 抽 6-10 个最关键的 token 做扁平列表
2. Example Component Prompts：从 components section 选 3-5 个组件，写"build X with..."风格的 prompt（含具体 px / hex / weight 值）
3. Iteration Guide：5-7 条 tips，是 5 rule-bearing section 关键约束的提炼

### Provenance 写在哪些 section？

每个 **rule-bearing** section 的每个决策都必须有 provenance 三段（inheritance + adaptation + justification）。

**元 section** 不需要每条都有完整三段，但必须有 `derived_from` 字段说明它综合了哪些 section / 哪些规则。

---

## 检查清单（B4 产出前必过）

- [ ] 9 个 section 全部生成，按顺序、含数字编号、用 OD 方言名字
- [ ] 5 个 rule-bearing section 每个都有规则覆盖（缺则 degraded）
- [ ] 4 个元 section 都基于已写的 rule-bearing section 派生（不凭空生成）
- [ ] 每个 rule-bearing 决策都有完整三段式（inheritance + adaptation + justification）
- [ ] 每个 inheritance.source_rules 都能在 B3 子集里找到
- [ ] 每个 adaptation.modifications 都有 reason 且 reason 不是空话
- [ ] 每个 justification.internal_consistency 都指向具体已写 section
- [ ] anti-slop 自查已跑，可疑用法都有解释
- [ ] **没有引入 B3 子集之外的新规则**
- [ ] **没有向用户追问任何信息**
