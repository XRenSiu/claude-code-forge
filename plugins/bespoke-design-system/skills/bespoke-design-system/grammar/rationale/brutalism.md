# Rationale — brutalism

> 三段式 rationale 抽取自 `source-design-systems/brutalism/DESIGN.md`。**注意**：OD 仓库的此条目是 dialect B 模板化产物，不是深度建模的 brutalist 设计——内容稀薄，多数 rationale 必须 [inferred] 自 brutalist 流派常识。

## Visual Theme & Atmosphere

### decision: anti-design aesthetic — raw, unadorned, jarring layouts

原 DESIGN.md 段落（auto-backfill）：
> > Category: Bold & Expressive
> > Raw, anti-design aesthetic inspired by concrete architecture with unadorned elements, jarring layouts, and functional minimalism.
- **trade_off**: 美学打磨（取悦审美） ↔ raw 直白（拒绝装饰修饰，让功能本身成为表达）
- **intent**: 让产品看起来像具体浇筑的混凝土——重、直接、无歉意 [inferred]
- **avoid**:
  - 过度精致打磨抹平 raw character
  - 装饰性元素稀释 anti-design 立场
  - 圆角软化破坏砖块感

## Color

### decision: Primary #DD614C terracotta-orange + #DAA144 mustard secondary

原 DESIGN.md 段落（auto-backfill）：
> - Favor Primary (#DD614C) for CTA emphasis.
> - Use Surface (#FFFFFF) for large backgrounds and cards.
> - Keep body copy on Text (#111827) for legibility.
- **trade_off**: 中性安全色 ↔ 大胆暖色（混凝土氧化锈色和黄铜的视觉关联）[inferred]
- **intent**: 用偏暖的橙黄而非冷色让 brutalism 不冰冷——是粗犷而非疏离
- **avoid**:
  - 冷蓝紫调（与混凝土美学冲突，会变 cyberpunk）
  - 装饰性渐变和 lerp 色（违反 anti-design）

### decision: White surface + Black text (functional binary)

原 DESIGN.md 段落（auto-backfill）：
> - **Primary:** `#DD614C` — Token from style foundations.
> - **Secondary:** `#DAA144` — Token from style foundations.
> - **Success:** `#16A34A` — Token from style foundations.
> - **Warning:** `#D97706` — Token from style foundations.
> - **Danger:** `#DC2626` — Token from style foundations.
> - **Surface:** `#FFFFFF` — Token from style foundations.
> - **Text:** `#111827` — Token from style foundations.
> - **Neutral:** `#FFFFFF` — Derived from the surface token for official format compatibility.
- **trade_off**: 多层灰阶 ↔ 二元黑白（极致简化为对比）
- **intent**: 让信息层级靠内容本身和粗 stroke 类型，不靠灰度梯度
- **avoid**:
  - 灰阶 ladder 减弱对比张力 [inferred]

## Typography

### decision: Darker Grotesque (display + body 同字体)

原 DESIGN.md 段落（auto-backfill）：
> Raw, anti-design aesthetic inspired by concrete architecture with unadorned elements, jarring layouts, and functional minimalism.
- **trade_off**: 文字层级靠 family 区分 ↔ 单一 family + size/weight 区分（更像 anti-design 的极简）
- **intent**: 用 Darker Grotesque 这种带历史感的 grotesque 表达 brutalism 的"上世纪建筑"调性 [inferred]
- **avoid**:
  - 优雅细体 serif（与混凝土美学反向）
  - geometric sans 的过度精确感

### decision: 9-tier weight (100-900 全开放)

原 DESIGN.md 段落（auto-backfill）：
> - **Scale:** desktop-first expressive scale
> - **Families:** primary=Darker Grotesque, display=Darker Grotesque, mono=JetBrains Mono
> - **Weights:** 100, 200, 300, 400, 500, 600, 700, 800, 900
> - Headings should carry the style personality; body text should optimize scanability and contrast.
- **trade_off**: 受限 weight ladder（系统化） ↔ 全开放 weight（表达自由）[inferred]
- **intent**: brutalism 容许 expressive scale，让 designer 在不同 section 用极端 weight 对比
- **avoid**:
  - 单一 medium 给出的"无表情"感

## Layout & Spacing

### decision: 4/8/12/16/24/32 spacing scale

原 DESIGN.md 段落（auto-backfill）：
> - **Spacing scale:** 4/8/12/16/24/32
> - Keep vertical rhythm consistent across sections and components.
> - Align columns and modules to a predictable grid; avoid ad-hoc offsets.
- **trade_off**: 工程化 8px grid ↔ 含 4px 微调（mini-step 应对密集排版）
- **intent**: 标准 8px backbone 加 4px 半步——保持 brutalism 的"jarring layouts"特征 [inferred]
- **avoid**:
  - 有机不规则间距（破坏粗犷的几何感）
  - 过度 generous 的留白（与 raw 拥挤美学冲突）

## Components

### decision: Buttons use #DD614C primary, neutrals for secondary

原 DESIGN.md 段落（auto-backfill）：
> - Buttons: primary action uses `#DD614C`; secondary actions stay neutral.
> - Inputs: strong focus-visible states, clear labels, and predictable error messaging.
> - Cards/sections: use consistent radii, spacing, and elevation strategy across the page.
- **trade_off**: 多色按钮 ↔ 单一 chromatic anchor（color discipline）
- **intent**: 让一个橙色按钮成为视觉锤——直接、不可错过
- **avoid**:
  - 多 CTA 同时高饱和 → 视觉竞争
  - 按钮装饰化（gradient / shadow）

## Motion

### decision: 150-250ms transitions, stable easing

原 DESIGN.md 段落（auto-backfill）：
> - Use subtle transitions that emphasize Primary (#DD614C) as the interaction signal.
> - Default to short, purposeful transitions (150–250ms) with stable easing.
> - Ensure hover, focus-visible, active, disabled, and loading states are explicit.
- **trade_off**: 戏剧性长动效 ↔ 短暂功能性动效
- **intent**: brutalism 的动效应该像建筑——直接，无戏剧
- **avoid**:
  - bounce / overshoot easing（太活泼）
  - 长 duration（softens raw character）

## Voice & Brand

### decision: concise, confident, action-oriented copy

原 DESIGN.md 段落（auto-backfill）：
> - Tone should reflect the visual style: concise, confident, and product-specific.
> - Keep microcopy action-oriented and avoid generic filler language.
> - Preserve the style identity in headlines while keeping UI labels literal and clear.
- **trade_off**: 抒情营销腔 ↔ 简洁命令式
- **intent**: anti-design 的 voice 也应该 anti-marketing——直接、无修辞 [inferred]
- **avoid**:
  - 通用填料语言
  - 装饰性文案 transitions

## Anti-patterns（直接来自原 DESIGN.md）

- 不要引入 off-palette 颜色（破坏 chromatic discipline）
- 不要扁平化 hierarchy（同字号 weight 全用）
- 不要装饰性效果减弱可读性
- 不要混用不相关视觉隐喻

---

## 抽取统计

- 显式 rationale: 5 条（来自原文 Do/Don't）
- 推断 rationale `[inferred]`: 6 条（OD 此条目内容稀薄，需 brutalist 流派常识补）
- 9-section 覆盖：Visual Theme(1), Color(2), Typography(2), Layout(1), Components(1), Motion(1), Voice(1), Anti-patterns(4)
- **质量警告**：原 DESIGN.md 是模板化产物，不是真正深度建模的 brutalist 系统。生成时 confidence 偏低。
