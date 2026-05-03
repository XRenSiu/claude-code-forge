# DESIGN.md 9-Section 标准（OD 双方言并存）

> 本 skill 输出兼容 OD（`nexu-io/open-design`，~140 套）+ `VoltAgent/awesome-design-md` 生态。**实测仓库内有两大主流方言并存（A: 48% / B: 42%）**，本 skill 内部用统一的规则 schema，输出时按用户选择或素材主导方言决定 section 命名。

## 重要历史

早期 spec 草稿写过 `Color / Typography / Spacing / Layout / Components / Motion / Voice / Brand / Anti-patterns` 这套命名。**实测发现这就是 Dialect B**（OD 仓库 137 套中 57 套用此方言，约 42%）——并非虚构。同时另有 Dialect A（66 套，48%）使用 `Visual Theme & Atmosphere / Color Palette & Roles / Typography Rules / Component Stylings / Layout Principles / Depth & Elevation / Do's and Don'ts / Responsive Behavior / Agent Prompt Guide`。两者**都是事实标准**。

## 两大方言对照

---

## Dialect A 模板（66 套使用，含 apple / linear-app / vercel / stripe / notion / claude）

```markdown
# Design System for <Product Name>

## 1. Visual Theme & Atmosphere    ← 元 section（散文综合）
## 2. Color Palette & Roles         ← rule-bearing
## 3. Typography Rules              ← rule-bearing
## 4. Component Stylings            ← rule-bearing
## 5. Layout Principles             ← rule-bearing
## 6. Depth & Elevation             ← rule-bearing
## 7. Do's and Don'ts               ← 元 section（反向汇总 anti-pattern）
## 8. Responsive Behavior           ← 元 section（layout 派生）
## 9. Agent Prompt Guide            ← 元 section（综合派生）
```

## Dialect B 模板（57 套使用，含 brutalism / bento / openai / mistral-ai / 等）

```markdown
# Design System for <Product Name>

## 1. Visual Theme & Atmosphere    ← 元 section
## 2. Color                         ← rule-bearing
## 3. Typography                    ← rule-bearing
## 4. Spacing & Grid                ← rule-bearing
## 5. Layout & Composition          ← rule-bearing
## 6. Components                    ← rule-bearing
## 7. Motion & Interaction          ← rule-bearing
## 8. Voice & Brand                 ← 元 section（综合派生）
## 9. Anti-patterns                 ← 元 section（反向汇总）
```

## 内部统一规则 section slug（rule.section 字段枚举）

无论素材是哪种方言，规则 yaml 里的 `section` 字段必须从下面**统一的 8 个 rule-bearing slug** 中选：

| slug | Dialect A 输出位置 | Dialect B 输出位置 |
|---|---|---|
| `color` | § 2 Color Palette & Roles | § 2 Color |
| `typography` | § 3 Typography Rules | § 3 Typography |
| `spacing` | § 5 Layout Principles 内 | § 4 Spacing & Grid |
| `layout` | § 5 Layout Principles | § 5 Layout & Composition |
| `components` | § 4 Component Stylings | § 6 Components |
| `depth_elevation` | § 6 Depth & Elevation | § 6 Components 散文段落 |
| `motion` | § 4 散文 + § 9 Agent Guide | § 7 Motion & Interaction |
| `voice` | § 1 / § 9 散文段落 | § 8 Voice & Brand 内的 voice 部分 |

`anti_patterns` 是特殊 slug——既不在 rule-bearing 里也不算元 section，规则在 yaml 里独立标 `section: anti_patterns`，B6 输出时映射到 Dialect A § 7 Don't 列表 / Dialect B § 9 Anti-patterns。

每个 section 都**必须存在**（OD 兼容工具按位置解析）。即使 degraded，也必须存在并加 `> ⚠️ degraded` 提示。

## B6 阶段如何选方言

1. 用户调用时显式指定（`mode=auto dialect=A`）→ 按指定
2. 主导素材风格岛的方言（B3 阶段输出的 `dominant_dialect` 字段）→ 默认按主导方言
3. 都没有 → 默认 Dialect A（更工程化、含 Agent Prompt Guide，对 AI 工具更友好）

无论哪种方言，三份产物（DESIGN.md / provenance.yaml / negotiation-summary.md）都不变；只是 DESIGN.md 文件的 section 编号和命名不同。

---

## 规则承载 section vs 元 section（关键区分）

9 个 section 在本 skill 内部分两类：

### 5 个**规则承载 section**（rule-bearing）

`grammar/rules/*.yaml` 中的规则的 `section` 字段**必须**从这 5 个 slug 中选：

| Section | slug | 规则内容 |
|---|---|---|
| Color Palette & Roles | `color` | 调色板、对比策略、语义色规则 |
| Typography Rules | `typography` | 字体家族、weight 系统、letter-spacing、scale 规则 |
| Component Stylings | `components` | 按钮、输入、卡片、导航等组件样式规则 |
| Layout Principles | `layout` | 间距、栅格、容器、断点规则 |
| Depth & Elevation | `depth_elevation` | 阴影系统、z-index 层、深度策略规则 |

### 4 个**元 section**（meta / derivative）

这 4 个 section 在 B4 阶段**由其它 section 的规则 + 调性画像 + brief 综合生成**，不直接对应任何 rule。规则 yaml 中**不应该**用这些 slug：

| Section | 生成方式 |
|---|---|
| Visual Theme & Atmosphere | 综合 5 规则承载 section + 画像 archetype + kansei 写一段散文化的总览 |
| Do's and Don'ts | 从 anti-pattern 规则 + 画像 reverse_constraint + 5 规则承载 section 的 `why.avoid` 反向汇总 |
| Responsive Behavior | 主要从 layout section 的 `breakpoints` 字段派生 + brief 推断 |
| Agent Prompt Guide | 从 Quick Color Reference + 各 section 关键决策抽取，给 AI agent 用 |

---

## Anti-pattern 在哪里？

OD 方言**没有**独立的 `## Anti-Patterns` section（这是早期 skill 草稿的非标准虚构）。Anti-pattern 在 OD 标准中体现在两个位置：

1. **`## 7. Do's and Don'ts`**：Don'ts 子段落直接列出 anti-pattern
2. **散落于各 section 的散文段落**：例如 Color section 写"避免纯白文字"

本 skill 处理 anti-pattern 规则的方式：

- 规则 yaml 中可以有 `section: anti_patterns` 的规则（这是**规则库内部 slug**，不是输出 section）
- B4 阶段把这些规则 inline 到 `## 7. Do's and Don'ts` 的 Don'ts 列表 + 视情况复制到相关 section 的散文段落

---

## 各 section 详细模板

### 1. Visual Theme & Atmosphere（散文）

3-4 段散文，回答："如果一个用户从未见过这个产品，这份设计想让他/她在 30 秒内感受到什么？"

- 第 1 段：base canvas + 整体感觉（"a near-black canvas where content emerges from darkness"）
- 第 2 段：典型样式 example（"the typography system carries..." / "the elevation strategy is..."）
- 第 3 段：识别度——什么让这套设计**与众不同**（"what distinguishes this from other monochrome systems is..."）
- 末尾："Key Characteristics:" 列表，5-9 条

### 2. Color Palette & Roles

按 role 分组，每组列具体值（hex / rgba / hsla）+ 一句话用途：

- Background Surfaces / Text & Content / Brand & Accent / Status / Border & Divider / Overlay
- 末尾 Strategy 子段：palette type、contrast strategy、body-on-bg contrast ratio

### 3. Typography Rules

- Font Family（primary / mono / OpenType features）
- Hierarchy 表（role / font / size / weight / line height / letter spacing / notes）
- Principles：3-5 条原则（signature weight、tracking 规则、weight 系统约束等）

### 4. Component Stylings

按组件类型分组：

- Buttons（多变体：primary / ghost / pill / icon 等，每个含 bg / text / padding / radius / border / hover / use）
- Cards & Containers
- Inputs & Forms
- Badges & Pills（如有）
- Navigation
- Image Treatment
- Distinctive Components（产品特有的）

### 5. Layout Principles

- Spacing System：base / scale / 注释（光学修正、跳跃 scale 等）
- Grid & Container：max width / hero / feature 行为
- Whitespace Philosophy：散文（"darkness as space" / "gallery emptiness" 等）
- Border Radius Scale：从 micro 到 pill

### 6. Depth & Elevation

表格：Level / Treatment / Use（含 5-7 个层级）。

末尾 Shadow Philosophy 散文一段：解释为什么这套系统这样处理深度（多层 shadow vs luminance stepping 等）。

### 7. Do's and Don'ts

两列 / 两个子段：

```
### Do
- ...
- ...

### Don't
- ...
- ...
```

每条都是具体的、有立场的、可验证的（不是"do good design"这种空话）。

### 8. Responsive Behavior

- Breakpoints 表（name / width / key changes）
- Touch Targets
- Collapsing Strategy（hero / nav / cards / sections 在小屏的行为）
- Image Behavior

### 9. Agent Prompt Guide

给 AI agent 用的快速参考：

- Quick Color Reference（key tokens 列表）
- Example Component Prompts（5 条左右"build X with..."风格的具体提示）
- Iteration Guide（5-7 条 tips 帮 agent 迭代）

这是 OD 方言独有的 section——它让 DESIGN.md 不仅是描述，还是**给 AI 用的可操作指令集**。

---

## 严格规范

1. **顺序固定**：9 个 section 必须按上述顺序。OD 工具按位置解析。
2. **二级标题 + 编号**：`## 1. Visual Theme & Atmosphere` ——含数字编号（OD 约定）
3. **不允许新增顶级 section**：保持 9 个。扩展进对应 section 的子段落
4. **不允许重命名**：例如不能把 `## 7. Do's and Don'ts` 改成 `## 7. Anti-Patterns`

---

## Appendix（可选）

某些场景需要扩展字段（如自定义品牌资产、Inspirations、illustration 指导）。OD 标准允许在 9-section **之后**加 appendix：

```markdown
## 9. Agent Prompt Guide
...

---

## Appendix A: Inspirations
...

## Appendix B: Brand Assets
...
```

appendix 不影响 9-section 的兼容解析。本 skill 默认不输出 appendix——除非 brief 明确需要。

---

## 参考实现样例

- `nexu-io/open-design` 的 `design-systems/` 目录（~140 套真实例子）
- 本 skill 的 `source-design-systems/linear-app/DESIGN.md` 和 `vercel/DESIGN.md` 是经过验证的两个范例
- `examples/code-review-saas/output-design.md` 是本 skill 的端到端产出范例
