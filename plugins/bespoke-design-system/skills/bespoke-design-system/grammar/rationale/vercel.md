# Rationale — vercel

> 三段式 rationale 抽取自 `source-design-systems/vercel/DESIGN.md`。

## Visual Theme & Atmosphere

### decision: extreme white minimalism — gallery-like emptiness
- **trade_off**: 信息密度 ↔ 大量留白（每个 token 必须 earn its pixel）
- **intent**: 让产品看起来"无需证明也无需隐藏"——白色就是设计本身
- **avoid**:
  - 用色块或装饰填补空白制造的"忙碌感"
  - 白色被解读为"未完成"或"懒"

### decision: minimalism as engineering principle (not as decoration)
- **trade_off**: 极简风格美学（流行） ↔ 极简作为工程原则（每个删减都有理由）
- **intent**: 让界面像编译器看代码——unnecessary token stripped away
- **avoid**:
  - "看起来像极简但其实是装饰极简"的伪极简
  - 删减过头导致功能性下降

## Color

### decision: achromatic palette + functional workflow colors only
- **trade_off**: 单色系统（识别但单调） ↔ 多色系统（丰富但分散）
- **intent**: 颜色 = 功能。Workflow 色（Ship Red / Preview Pink / Develop Blue）只在 workflow 上下文使用
- **avoid**:
  - 装饰性使用 workflow 色稀释其语义
  - 引入暖色（橙黄绿）破坏 black/white 调性

### decision: #171717 instead of pure #000000 for text
- **trade_off**: 数学黑（精确） ↔ 偏暖近黑（micro-warmth 防止刺眼）
- **intent**: 微暖的近黑减少视觉硬度，但仍保持权威感
- **avoid**:
  - 纯 #000000 造成的"打印机墨水"感
  - 灰得太浅失去权威感

## Typography

### decision: Geist with extreme negative letter-spacing (-2.4 to -2.88px at 48px)
- **trade_off**: 标准字距（易读） ↔ 极致负字距（compressed, urgent, engineered）
- **intent**: 让 display 文字看起来"minified for production"——像优化过的代码
- **avoid**:
  - 字距过紧导致小字号可读性崩
  - 字距正向（任何时候都不该出现在 Geist 上）

### decision: three weights only (400/500/600), no bold body text
- **trade_off**: 多 weight 灵活（细分层级） ↔ 三 weight 严格（约束 → 一致性）
- **intent**: 通过 size + tracking 而非 weight 建立层级——窄 weight 范围强化系统化
- **avoid**:
  - weight 700 bold 在 body 上的"喊叫"
  - 不必要的 weight 变种

## Components / Elevation

### decision: shadow-as-border (box-shadow 0px 0px 0px 1px) replaces CSS border
- **trade_off**: 传统 CSS border（普适） ↔ shadow-border（圆角不裁剪、过渡更顺、视觉更轻）
- **intent**: 让 border 存在于 shadow layer——可与 elevation 共栈，更精细的层次
- **avoid**:
  - 传统 border 与 border-radius 在某些 transition 下的 clipping
  - 实色 border 的视觉重量

### decision: multi-layer shadow stacks (border + soft + ambient + inner #fafafa glow)
- **trade_off**: 单层阴影（简单） ↔ 多层堆叠（每层职责单一，整体精致）
- **intent**: 让卡片"feel built, not floating"——每层 shadow 有具体建筑学职责
- **avoid**:
  - 传统 Material Design 的"漂浮"感
  - 单层重 shadow 造成的"plastic"感
  - 跳过 inner #fafafa ring（"是它让卡片有内发光感"）

### decision: dark pill CTA reserved for primary actions only
- **trade_off**: 颜色按钮（明显） ↔ 黑色按钮（克制 + 工程化对比）
- **intent**: 在白底上用纯黑作为最强对比锚点，引导主操作
- **avoid**:
  - 装饰性使用黑色按钮稀释其作用
  - pill radius (9999) 用在 primary action 上（pill 留给 badge/tag）

## Layout

### decision: section padding 80px-120px+ with no color variation
- **trade_off**: 显式 section 分隔（结构感） ↔ 纯空间分隔（极简一致）
- **intent**: 留白本身就是 section 间的语言——不需要色块或线条
- **avoid**:
  - 用背景色变化制造的"section 套娃"
  - 留白不足导致内容拥挤

### decision: spacing scale jumps from 16 to 32 (no 20/24 in primary scale)
- **trade_off**: 连续梯度（灵活） ↔ 断裂跳跃（强制结构选择） [inferred]
- **intent**: 强制使用 16 或 32 而非中间值，避免"看心情选 spacing"
- **avoid**:
  - 16/20/24/28 这种含混梯度造成的不一致

## Voice / Brand-implicit

### decision: signature voice is "infrastructure made invisible" [inferred from extreme minimalism + functional color]
- **trade_off**: 显眼的品牌存在 ↔ 让基础设施隐形
- **intent**: 让用户感受到 Vercel 的存在不是通过装饰，而是通过结构本身
- **avoid**:
  - 营销腔调的产品宣传感
  - 浮夸的视觉效果

## Anti-patterns

- **不要用 CSS border** — 改用 shadow-border 技术
- **不要用 weight 700 在 body** — 600 是 heading 上限
- **不要把 workflow 色装饰化** — 只能用在 develop/preview/ship 上下文
- **不要 heavy shadow（opacity > 0.1）** — 系统是 whisper-level
- **不要正字距** — Geist Sans 永远 negative 或 0
- **不要 pill radius 在 primary button** — pill 留给 badge
- **不要跳过 inner #fafafa ring** — 它是卡片内发光的关键
- **不要引入暖色** — 调色板是 black/white + 功能色

---

## 抽取统计

- 显式 rationale: 10 条
- 推断 rationale (`[inferred]`): 2 条（Voice、spacing-jumps 部分）
- 9-section 覆盖：Visual Theme(2) + Color(2) + Typography(2) + Components/Elevation(3) + Layout(2) + Voice(1) + Anti-patterns(8)
- 缺失 section: Motion（与 linear-app 同样情况）
