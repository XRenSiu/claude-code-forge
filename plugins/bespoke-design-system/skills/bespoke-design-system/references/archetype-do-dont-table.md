# Archetype Do/Don't Table — 12 archetype 的视觉清单

> 本文档是 `checks/_shared/archetype_rules.json` 的可读版本。每个 archetype 有 `always` / `never` / `tend_to` 三类清单。json 里是机器可执行的断言，本文档是人类可读的解释。

> 详细 always/never 断言见 `checks/_shared/archetype_rules.json`，本文档侧重每个 archetype 的"为什么"和典型品牌对照。

## 12 Archetype 概览

| # | Archetype | 核心动机 | 典型品牌 | 视觉关键词 |
|---|---|---|---|---|
| 1 | **Sage** | 理解世界，传达真理 | Linear, Notion, Stripe（理性时刻）| 高对比 / 中性灰 / 单一克制 chromatic |
| 2 | **Magician** | 让神奇发生 | Apple keynote, Tesla, Mailchimp playful | 暗色基调 / 紫金属 / 慢 dramatic 动效 |
| 3 | **Hero** | 通过勇气证明 | Nike, BMW, Stripe Connect | 高对比 / 粗 stroke / 决断 chromatic |
| 4 | **Outlaw** | 颠覆规则 | Brutalism, Vimeo (early), Are.na | anti-design / 黑红 / 锐角 |
| 5 | **Explorer** | 寻找自由 | Patagonia, Airbnb, REI | 自然色 / humanist sans / 摄影 hero |
| 6 | **Creator** | 创造持久作品 | LEGO, Adobe, Figma, Vercel | 多色精度 / 强调几何 / craft 细节 |
| 7 | **Innocent** | 体验快乐和纯粹 | Coca-Cola, Dove, Aveeno | 柔色 / 圆角 / humanist 圆体 |
| 8 | **Lover** | 建立亲密连接 | Chanel, Tiffany, Godiva | 暖中性 / Didone serif / 大留白 |
| 9 | **Caregiver** | 保护和帮助 | Johnson & Johnson, UNICEF, Volvo | 蓝绿 / 圆角 / 软阴影 |
| 10 | **Ruler** | 建立秩序 | Rolex, Mercedes, IBM enterprise | 深色 + 暗金 / serif / 严格 grid |
| 11 | **Jester** | 享受当下 | Old Spice, M&M's, Mailchimp mature | 多色 / 渐变 / 弹性动效 |
| 12 | **Everyman** | 归属感 | IKEA, Target, Levi's, Slack | 中性 + 友好色 / humanist sans |

## 各 archetype 的 always / never / tend_to 详解

### 1. Sage（智者）

**Always**:
- WCAG AA 4.5+ body contrast — clarity 是 Sage 的根本
- 4px+ base spacing — 充足留白支持冷静的权威
- 单一 chromatic anchor 最多 — 克制本身就是信息

**Never**:
- 高饱和强调色（C > 0.7） — 破坏 calm authority [BLOCKER]
- 渐变背景（多于 1 个） — 削弱清晰
- 大圆角（> 16px） — 显得 playful 不像 sage
- 弹性 / bounce 动效 — Sage 动效是 functional 不是 theatrical

**Tend to**:
- 冷或中性色调
- 宽松 line-height ≥ 1.5

### 2. Magician（魔法师）

**Always**:
- 深色 surface（neutral L_min ≤ 0.20）
- 至少一个高饱和（C ≥ 0.5）chromatic 用于关键 CTA

**Never**:
- 纯 monochromatic 色板 — 失去神秘 layering
- 完全 flat（无 shadow / 无 depth） — 破坏 mystery

**Tend to**:
- 紫色 / 深蓝 / 金属色
- serif 或强 weight 对比表达 texture 差异

### 3. Hero（英雄）

**Always**:
- WCAG AA 4.5+ — 清晰大胆
- Weight ≥ 600 至少一个层级 — 命令感

**Never**:
- 全 weight < 500 — whisper-weight 缺乏命令 [BLOCKER]
- 全 pastel 色板 — 与力量冲突

**Tend to**:
- 高饱和决断色
- Sharp 几何（radius ≤ 8）

### 4. Outlaw（叛逆者）

**Always**:
- 显式 anti-pattern intent（anti-design 立场）

**Never**:
- 企业模板美学 [BLOCKER]
- 安全 SaaS 蓝紫（Outlaw 叛的就是这个）
- 装饰性精致打磨

**Tend to**:
- 高对比黑白 binary
- 极端 weight 对比

### 5. Explorer（探索者）

**Always**:
- 摄影作为 hero element

**Never**:
- 合成 / 过度渲染美学 — 损 authenticity

**Tend to**:
- 大地色调（棕 / 森林绿 / 海蓝）
- humanist 或 serif 字体

### 6. Creator（创造者）

**Always**:
- 允许内容多色（不锁用户审美）

**Never**:
- 把用户锁死在单一 aesthetic

**Tend to**:
- 克制中性 chrome + 丰富内容（Figma 模式）
- 有辨识度的 typography

### 7. Innocent（纯真者）

**Always**:
- 暖或柔色调
- 软圆角（≥ 8px）

**Never**:
- 严酷高对比
- 冷峻几何字体

**Tend to**:
- pastel / 软色调
- 圆体 humanist sans

### 8. Lover（情人）

**Always**:
- 大量留白 — 奢华就是空间

**Never**:
- 信息密集 layout
- 纯几何（缺乏 sensual）

**Tend to**:
- 暖色（米 / 玫粉 / 暗金）
- serif 特别是 Didone
- 精致细节（hairline / 软阴影）

### 9. Caregiver（照护者）

**Always**:
- WCAG AA — accessibility 是 caregiver 价值
- 软圆角（≥ 6px）

**Never**:
- 攻击性色板 [BLOCKER]
- 严酷锐利几何

**Tend to**:
- 蓝绿 + 暖色（trust + calm balanced）

### 10. Ruler（统治者）

**Always**:
- 严格 grid 对齐
- 含深色 / 金属

**Never**:
- 休闲 / playful 感
- 手写 / quirky 字体

**Tend to**:
- serif 或强 geometric sans
- 深色 / navy brand

### 11. Jester（弄臣）

**Always**:
- 高饱和（C ≥ 0.6）joy

**Never**:
- 企业严肃感 [BLOCKER]
- 纯 monochromatic（过度克制）

**Tend to**:
- 多 brand 色
- 大圆角（≥ 12px）
- bounce / overshoot 动效

### 12. Everyman（凡人）

**Always**:
- WCAG AA — friendly 必须 accessible

**Never**:
- 精英 / 排外感
- 神秘 / inaccessible

**Tend to**:
- humanist sans
- 暖 / 中性 / 中性暖（友好但不极端）

## 双原型组合

实际 brief 通常给两个 archetype（primary + secondary）。`archetype_check`：

- primary 的 `never` 是 **blocker**（违反就 reject）
- secondary 的 `never` 是 **warning**（违反就提醒）
- 两者的 `always` 不满足都是 **warning**

如果两个 archetype 在某条 rule 上冲突（如 Sage `never:saturation > 0.7` vs Jester `always:saturation ≥ 0.6`），primary 优先。

## 可执行规则数据

可执行的断言（`field` / `operator` / `value` 三元组）见 `checks/_shared/archetype_rules.json`。每条规则在 archetype_check.py 中通过 `_derived_signals(tokens)` 计算的派生信号来评估。
