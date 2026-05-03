# Anti-Slop Blacklist — AI Slop 黑名单

> "AI slop" 指那种一眼能识别为"AI 生成"的设计调性——通常是某些组合用得过滥导致失去识别度。本 skill 的目标之一就是不产 slop。

本文件列出**模式 + 检测规则 + 例外条件**。B5 闸门会跑这套规则；B4 生成时遇到可疑模式必须主动论证为什么这里不是 slop。

---

## 一、组合 slop（最高优先级）

最经典的 AI slop 是**几个元素叠加**形成的，单看某一个元素并无问题，组合起来就是 slop。

### Pattern A1: 紫渐变 + Inter + 12px 圆角卡片

- **触发条件**（同时满足）：
  - 主色或强调色含紫色渐变（hue 270-300°，linear-gradient）
  - 字体含 Inter 或 Inter 衍生（Inter Display / Tight）
  - 卡片 / 容器圆角在 8-16px 区间且使用 box-shadow
  - 整体 layout 是中心对齐 hero + 三栏 features
- **严重程度**：blocker（出现一律驳回）
- **例外**：仅当画像 reverse_constraint 显式不含 `ai_slop` 且产品需要极强 SaaS 通用感时（罕见，需要强证据）

### Pattern A2: 全部白底 + #8B5CF6 强调色 + 大留白 + 渐变文字

- **触发条件**：
  - 背景纯白
  - 唯一强调色在紫蓝区（hue 240-280°，saturation > 0.6）
  - 标题用渐变（gradient text-fill）
  - section 间距 ≥ 128px
- **严重程度**：blocker
- **例外**：用户明确要 "OpenAI 官网风格" 时（产品确实是 AI 工具，且画像 archetype 含 Sage+Creator）

### Pattern A3: 暗黑 + 霓虹绿 / 霓虹紫 + Bento Grid

- **触发条件**：
  - 暗色背景（lightness < 0.15）
  - 霓虹强调色（saturation > 0.85，lightness 0.5-0.7）
  - layout 含 bento-style asymmetric grid
- **严重程度**：blocker
- **例外**：画像明确含 `cyberpunk / neo-brutal` Kansei 词时

### Pattern A4: Cubic Bezier(0.16, 1, 0.3, 1) + Fade-up + Stagger

- **触发条件**：
  - 入场动画用 `cubic-bezier(0.16, 1, 0.3, 1)`（"emphasized" easing）
  - 元素从下方 20-40px fade-in
  - 多元素 stagger 延迟 50-150ms
- **严重程度**：warning（这套组合本身没错，但用得太多）
- **要求**：B4 必须在 motion section 论证这套动效与画像 personality 的协同性，而不是"因为大家都这么做"

---

## 二、单元素 slop（次要警告）

单看不算大错，但需要论证为什么不是默认选择。

### Pattern B1: 纯 Inter 字体（display + body 都用 Inter）

- **检测**：display_family == body_family == "Inter" / "Inter Display"
- **严重程度**：suspicion（可疑，必须论证）
- **论证要求**：必须在 typography 决策的 justification 中说明 Inter 是与画像 archetype 真正匹配的选择，而非默认值。例如 "Sage + Creator 的精度感与 Inter 的 mechanical 几何调性匹配"。论证不充分 → 升级为 warning

### Pattern B2: 8px grid + 16px radius + 24px padding

- **检测**：spacing.base == 8 AND radius.md ≈ 16 AND component padding ≈ 24
- **严重程度**：suspicion
- **论证要求**：说明这套 token 是从素材库哪条规则继承的，而非通用默认

### Pattern B3: 主色蓝紫色（hue 240-260°）

- **检测**：primary hue 在 240-260°
- **严重程度**：suspicion
- **论证要求**：Linear / Stripe / Vercel 等多个素材都用过这个色相，单单复用并不算错——但 inheritance 必须明确指向具体素材，不能说"普遍使用"

### Pattern B4: Hero CTA 文案 "Get started for free"

- **检测**：voice section 的 CTA 例子含 "Get started" / "Get started for free" / "Try it free"
- **严重程度**：suspicion
- **论证要求**：voice 必须基于 archetype + 画像 audience 选择。Sage 通常更克制（"Begin"、"Continue"），Hero 更有力度（"Start now"），Outlaw 更挑衅（"Break in"）。默认 "Get started" 是 slop

### Pattern B5: emoji 作为 section icon

- **检测**：components / layout 中描述用 emoji 作为图标
- **严重程度**：warning
- **论证要求**：除非画像含 Innocent / Jester / Everyman 原型，否则 emoji 是不严肃的视觉降级

---

## 三、动效 slop

### Pattern C1: 滚动视差 + 大量"AOS"风格 reveal

- **检测**：motion section 描述大量 scroll-triggered fade/slide reveals
- **严重程度**：warning
- **论证要求**：必须论证滚动动效与产品类型的匹配——长内容页 / 营销页可以；功能性 dashboard 不行

### Pattern C2: Magnetic cursor + 自定义跟踪光标

- **检测**：motion / interaction 描述含 "magnetic button" / "custom cursor follow"
- **严重程度**：warning
- **论证要求**：仅在画像含 Creator + 创意行业（设计、电影、艺术）时合理；通用 SaaS 不要用

### Pattern C3: Tilt-on-hover 卡片

- **检测**：components.card.hover 含 "rotate" / "tilt" / "perspective transform"
- **严重程度**：warning（已经从前几年的潮流变成 slop 候选）

---

## 四、内容 slop

### Pattern D1: 占位文案 "Lorem Ipsum" 或 "我们让 X 变得更简单"

- **检测**：voice example 含通用空话
- **严重程度**：blocker
- **要求**：所有 voice 示例必须是产品特定的、有 stance 的句子

### Pattern D2: 抽象图形 background

- **检测**：layout / components 描述大量"abstract gradients" / "blob shapes"
- **严重程度**：suspicion
- **论证要求**：与画像 personality 直接挂钩

---

## 检测算法（rationale-judge 用）

对 B4 草稿的每个 decision，对照本黑名单：

```
for pattern in blacklist:
    if pattern.detected_in(draft):
        if pattern.severity == "blocker":
            report_violation(pattern, decision_id, severity="blocker")
        elif pattern.severity == "warning":
            check if decision.justification adequately addresses pattern
            if not adequate:
                report_violation(pattern, decision_id, severity="warning")
        elif pattern.severity == "suspicion":
            require generation side to have provided justification
            if no justification:
                report_violation(pattern, decision_id, severity="warning")
            else:
                accept
```

---

## 维护本黑名单

slop 是流动的——今年的"独特"明年就是"烂大街"。本黑名单需要随时间更新。

**更新触发**：

- 当 P0 闸门同样的 false-positive / false-negative 出现 ≥ 5 次时
- 当 examples/ 中出现新的复发模式时
- 当用户主动反馈某个调性已经过时

更新方式：直接修改本文件，并 bump skill version（minor）。

**不要做**：

- 把所有"常见"模式都列入黑名单（结果是什么也不能生成）
- 把单一元素列为 blocker（黑名单的本质是组合 + 缺乏论证）
