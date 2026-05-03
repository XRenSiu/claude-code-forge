# B4 — 带 Rationale 生成

> 当 SKILL.md 主流程进入 B4 时读取本文件作为执行指引。引用 `references/shape-grammar.md`、`references/reflective-practice.md`、`references/design-md-spec.md` 加深理解。

## 你的任务

把 B3 的自洽规则子集**翻译**成 DESIGN.md 草稿（标准 9-section），并为每个决策产**三段式 Provenance Report**。

**严格约束**：

- 你是**翻译者**，不是创造者。任何决策都必须能追溯到 B3 子集里某条具体规则。
- 不向用户追问任何信息。
- 不引入 B3 子集之外的新规则。

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
