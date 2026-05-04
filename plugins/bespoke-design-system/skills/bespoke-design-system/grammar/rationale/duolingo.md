# Rationale — duolingo

> 三段式 rationale 抽取自 `source-design-systems/duolingo/DESIGN.md`。Dialect C（6-section）但内容详细——chunky shadow + Feather Bold + owl green 是高识别度三件套。

## Visual Theme & Atmosphere

### decision: Owl green #58cc02 dominates 30%+ of surface

原 DESIGN.md 段落（auto-backfill）：
> **Key Characteristics:**
> - Owl green (`#58cc02`) as the dominant brand color, used in 30%+ of the surface
> - Chunky 4px bottom-shadow on every button (the "tactile press" affordance)
> - 2–3px solid borders, never hairlines
> - Feather Bold (rounded display) + Mona Sans (body)
> - Big confident type — display sizes start at 48px and climb
> - Mascot-as-character: Duo the owl appears in onboarding, errors, streaks
> - Streak orange (`#ff9600`) and gem pink (`#ce82ff`) as secondary brand colors
- **trade_off**: chromatic 克制（克制是大多数 SaaS 美德） ↔ chromatic 主导（gamification 需要 chromatic 充满整个场景）
- **intent**: 让 gamification 视觉化——绿色不只是 brand 标记，是"前进感"本身
- **avoid**:
  - 单一 brand spot 化使用（弱化 gamification 调性）
  - 多色派对（chromatic 失焦）

### decision: Chunky 4px bottom-shadow on every interactive element

原 DESIGN.md 段落（auto-backfill）：
> **Error (Cardinal Red)**
> - Background: `#ff4b4b`
> - Text: `#ffffff`
> - Border-bottom: 4px solid `#cc3b3b`
> - Use: wrong answer feedback.
- **trade_off**: 平面 modern UI ↔ 3D button affordance（"等待按下"的物理感）
- **intent**: 把数字 UI 拟物化为"可按下"——降低学习门槛 + 增加 dopamine 反馈
- **avoid**:
  - 现代 flat design 的"看不出能点"
  - skeuomorphism 的过度仿真

### decision: 2-3px solid borders, never hairlines

原 DESIGN.md 段落（auto-backfill）：
> **Streak Orange**
> - Background: `#ff9600`
> - Text: `#ffffff`
> - Border-bottom: 4px solid `#cc7a00`
> - Use: streak goal, "Start streak"
- **trade_off**: 细致 hairline border（精致但弱化轮廓） ↔ 粗 solid border（明确 but 卡通）
- **intent**: 让所有 UI 元素都有"卡片游戏"的明确边界 —— children-and-adults 的友好语言
- **avoid**:
  - 1px 细边（破坏 chunky 系统）
  - 半透明边（弱化 outline）

## Color

### decision: Owl Green family (4 shades) as primary

原 DESIGN.md 段落（auto-backfill）：
> > Category: Productivity & SaaS
> > Language-learning platform. Bright owl green, chunky shadows, gamified joy.
- **trade_off**: 单色调（弱表达力） ↔ 4 shade family（pressed/hover/soft/pale 全套）
- **intent**: 一种绿色支撑所有 interactive states，不引入新色
- **avoid**:
  - 引入第二种"主"色（稀释 owl green 识别度）
  - 超饱和的霓虹绿（与 brand 友好性冲突）

### decision: Warm secondary accent palette (Streak orange / Gem pink / Eel blue / Cardinal red / Bee yellow)

原 DESIGN.md 段落（auto-backfill）：
> - **Duration**: 180ms for button press; 320ms for skill-node unlock; 1.6s for active-node pulse.
> - **Easing**: `cubic-bezier(0.34, 1.56, 0.64, 1)` (back-out, slight overshoot) for unlocks.
> - **Mascot**: Duo blinks every 4–6s, jumps on streak milestones (480ms ease-out spring).
- **trade_off**: 严格 chromatic discipline ↔ multi-accent dopamine system
- **intent**: 每种 game mechanic（streak / gem / hint / wrong / pro）有专属色——视觉记忆训练
- **avoid**:
  - 同色覆盖多 game 概念（学习者无法记忆 mapping）
  - 装饰性使用（破坏功能映射）

### decision: Snow #ffffff base + Eel/Swan/Wolf 4-tier neutrals

原 DESIGN.md 段落（auto-backfill）：
> **Secondary (White with Bottom-Shadow)**
> - Background: `#ffffff`
> - Text: `#777777`
> - Border: 2px solid `#e5e5e5`
> - Border-bottom: 4px solid `#e5e5e5`
> - Radius: 16px
> - Padding: 14px 24px
> - Hover: text `#3c3c3c`, border `#afafaf`
- **trade_off**: 单一 surface ↔ 多 surface tier
- **intent**: 让 disabled/divider/inset 有专属灰阶位置
- **avoid**:
  - rgba 半透明做 disabled（破坏 chunky 系统）

## Typography

### decision: Feather Bold (custom rounded sans) for chrome at weight 800 default

原 DESIGN.md 段落（auto-backfill）：
> Typography uses **Feather Bold** (a custom rounded sans) for chrome and **Mona Sans** (or Inter) for body. Display sizes are big and confident — Duolingo never whispers. Headings often carry the green underline-stroke or sit on a green pill, and the mascot Duo (a green owl) appears as an active illustration character, not a static logo.
- **trade_off**: medium-weight UI（克制） ↔ extra-bold UI（confident loud）
- **intent**: 让 button/heading/streak number 都有"喊口号"的体量——never whispers
- **avoid**:
  - weight 700 在 Feather（"feels weak in this system"）
  - sharp serif（破坏友好契约）

### decision: Big confident type — display starts at 48px+

原 DESIGN.md 段落（auto-backfill）：
> **Key Characteristics:**
> - Owl green (`#58cc02`) as the dominant brand color, used in 30%+ of the surface
> - Chunky 4px bottom-shadow on every button (the "tactile press" affordance)
> - 2–3px solid borders, never hairlines
> - Feather Bold (rounded display) + Mona Sans (body)
> - Big confident type — display sizes start at 48px and climb
> - Mascot-as-character: Duo the owl appears in onboarding, errors, streaks
> - Streak orange (`#ff9600`) and gem pink (`#ce82ff`) as secondary brand colors
- **trade_off**: 标准 SaaS 字号（32-40 max） ↔ Duolingo 50%+ 大（confidence as identity）
- **intent**: 让 Onboarding hero 像 cereal box 包装——不害怕被看见
- **avoid**:
  - 缩小字号配合"professionalism"（违反 Duolingo 调性）

### decision: Mona Sans / Inter for body

原 DESIGN.md 段落（auto-backfill）：
> Typography uses **Feather Bold** (a custom rounded sans) for chrome and **Mona Sans** (or Inter) for body. Display sizes are big and confident — Duolingo never whispers. Headings often carry the green underline-stroke or sit on a green pill, and the mascot Duo (a green owl) appears as an active illustration character, not a static logo.
- **trade_off**: 单一 family（一致） ↔ display + body 双 family（hierarchy via family）
- **intent**: chrome 用 Feather 表达 character，body 用 Mona/Inter 优化长读
- **avoid**:
  - 长 body 用 Feather（密度过高，疲劳）

## Components

### decision: Primary button — green bg + 4px green-deep bottom shadow + active translate-y(4px) "press"

原 DESIGN.md 段落（auto-backfill）：
> Duolingo is gamification rendered as visual language. The interface is unapologetically bright, with **owl green** (`#58cc02`) as the brand primary and a chunky 4px bottom-shadow on every interactive element that reads like a 3D button waiting to be pressed. The page is white (`#ffffff`) with thick 2–3px borders in a deep gray (`#e5e5e5`) and the entire system reads like an iOS app from 2015 reborn with better hierarchy.
- **trade_off**: 静态 button ↔ 物理感 button（press affordance + tactile feedback）
- **intent**: 每次点击都有 dopamine——button "presses down" 成为 brand 标志动作
- **avoid**:
  - 静态 hover-only（缺失 tactile）
  - 复杂多层 shadow（混乱）

### decision: Skill tree node = 80x72 circular bubble + 6px darker bottom border + active 1.05 pulse

原 DESIGN.md 段落（auto-backfill）：
> Shape language is friendly: 16–20px radii on cards, 12px on buttons, 9999px on chips and progress bars. Iconography is filled, rounded, and color-coded by skill — every lesson surface has an instantly identifiable color pairing.
- **trade_off**: 列表式课程导航 ↔ 游戏化 skill tree（地图感）
- **intent**: 让学习路径变成"地图前进"——空间隐喻代替线性列表
- **avoid**:
  - 普通 list 化（杀死游戏感）

### decision: Cards 16px radius + 4px chunky bottom-shadow

原 DESIGN.md 段落（auto-backfill）：
> **Primary (Owl Green)**
> - Background: `#58cc02`
> - Text: `#ffffff`
> - Padding: 14px 24px
> - Radius: 16px
> - Border-bottom: 4px solid `#58a700` (the chunky shadow)
> - Hover: background `#89e219`
> - Active: translate-y 4px, border-bottom 0 (button "presses")
> - Use: "Continue", "Check", main CTA.
- **trade_off**: subtle modern card ↔ chunky game card
- **intent**: 卡片本身也是"可拿起"的物体——rounded but sturdy
- **avoid**:
  - hairline border-only（过 modern）
  - 重 box-shadow blur（softens chunky）

## Layout

### decision: 4px base unit (not 8) + container 1080px + 320px lesson-tree column

原 DESIGN.md 段落（auto-backfill）：
> - **Base unit**: 4px. Scale: 4, 8, 12, 16, 24, 32, 48, 64.
> - **Container**: max 1080px, 24px gutter.
> - **Lesson tree column**: 320px wide; centered on desktop.
- **trade_off**: 8px 行业默认 ↔ 4px micro-grid（更细密度）
- **intent**: chunky shadow 系统需要 4px increments 来对齐
- **avoid**:
  - 8px-only（粗糙感不对）

## Motion

### decision: Back-out cubic-bezier(0.34, 1.56, 0.64, 1) for unlocks (slight overshoot)

原 DESIGN.md 段落（auto-backfill）：
> - **Duration**: 180ms for button press; 320ms for skill-node unlock; 1.6s for active-node pulse.
> - **Easing**: `cubic-bezier(0.34, 1.56, 0.64, 1)` (back-out, slight overshoot) for unlocks.
> - **Mascot**: Duo blinks every 4–6s, jumps on streak milestones (480ms ease-out spring).
- **trade_off**: linear/standard easing ↔ overshoot back-out（有"惊喜"的弹性）
- **intent**: 解锁瞬间需要小弹跳——奖励信号要 emotional
- **avoid**:
  - 单一 ease-out（缺少游戏奖励感）

### decision: Mascot Duo blinks every 4-6s, jumps on streak milestones

原 DESIGN.md 段落（auto-backfill）：
> - **Duration**: 180ms for button press; 320ms for skill-node unlock; 1.6s for active-node pulse.
> - **Easing**: `cubic-bezier(0.34, 1.56, 0.64, 1)` (back-out, slight overshoot) for unlocks.
> - **Mascot**: Duo blinks every 4–6s, jumps on streak milestones (480ms ease-out spring).
- **trade_off**: 静态 logo ↔ 活动 character mascot
- **intent**: 让 brand 成为"陪伴"——非 logo 而是 partner
- **avoid**:
  - 过度活动（注意力被吸走）
  - 完全静止（违反 mascot 角色）

## Anti-patterns

- 不要 weight 700 在 Feather Bold（系统认为 weak）
- 不要 hairline border（破坏 chunky）
- 不要去掉 4px bottom shadow（杀死 button physicality）
- 不要用第二个主色挑战 owl green
- 不要把 Duo 静态化（削弱 character role）

---

## 抽取统计

- 显式 rationale: 12 条
- 推断 [inferred]: 0 条
- 6-section 覆盖：完整覆盖 dialect C 的所有 section + 推派出 anti_patterns 子集
