# Rationale — discord

> 三段式 rationale 抽取自 `source-design-systems/discord/DESIGN.md`。Dialect C（6-section）但内容详细——Blurple + dark-first + gg sans + 圆角方形头像变圆。

## Visual Theme & Atmosphere

### decision: Dark-first surfaces (3-step depth: #1e1f22 / #2b2d31 / #313338)
- **trade_off**: 双主题平等 ↔ dark 是默认（产品场景是 evenings/raids/voice）
- **intent**: 让 chat 在长会话中不刺眼——dark 不是 option，是 default home
- **avoid**:
  - light theme 作为唯一/主推（违反产品使用场景）
  - 单层 dark（无层级区分 channel/sidebar/chat）

### decision: Blurple #5865f2 reserved for brand mark + primary CTA + mention + "you"
- **trade_off**: 多 chromatic 表达 ↔ 单一 chromatic 锚点
- **intent**: 让 Blurple 成为"你"的标记——mention/CTA 都关于"用户的注意力"
- **avoid**:
  - 装饰使用稀释 Blurple 信号
  - 跨场景过度使用（status/error 都 Blurple）

## Color

### decision: Three-step background depth (Tertiary < Secondary < Primary)
- **trade_off**: 单 dark surface ↔ 3-step ladder
- **intent**: server-rail 最深、channel sidebar 中间、chat 表面最亮 —— 视觉权重 = 信息流方向
- **avoid**:
  - 反向（chat 比 sidebar 暗）
  - 过密（4+ steps 用户感知不到）

### decision: Status colors (Online green / Idle yellow / DND red / Offline gray)
- **trade_off**: 自定义 chromatic ↔ 通用 traffic-light（universal recognition）
- **intent**: 状态识别零学习成本——用户视觉 cognition 自动 mapping
- **avoid**:
  - 自创 status palette（破坏 universal）
  - status 与 brand 同色（Blurple 不能做 status）

### decision: Mention highlight = rgba(88, 101, 242, 0.1) soft blurple wash
- **trade_off**: 单色实色高亮 ↔ 低 alpha 钝化（不打断阅读流）
- **intent**: mention 让眼睛"扫到"，不让眼睛"停留过久"
- **avoid**:
  - 高 alpha mention（打扰阅读）
  - 灰色 mention（无 brand 关联）

## Typography

### decision: gg sans (Whitney-style custom) for all text
- **trade_off**: 单一 family ↔ display + body 双 family
- **intent**: chat 工具字体 budget 紧——单一 family 节省 load + 保持温度感
- **avoid**:
  - 引入 serif 装饰（工程性破坏）
  - 严格 geometric sans（过冷）

### decision: 16px message body — never shrink below 16
- **trade_off**: 紧密信息（更多消息一屏） ↔ 16px 锁定（长会话疲劳防止）
- **intent**: chat 本质是阅读工具——可读性优先于密度
- **avoid**:
  - 14px body（多年使用导致眼疲劳）
  - 字号 increment 制造 hierarchy（用 weight 代替）

### decision: Weight contrast over color contrast for hierarchy
- **trade_off**: 颜色 hierarchy ↔ weight hierarchy
- **intent**: dark surface 上颜色变化太隐晦，weight 变化更可读
- **avoid**:
  - 多色文字 hierarchy
  - 单 weight 全局（无 hierarchy）

## Components

### decision: Server avatars 16px radius rounded-square → 50% circle on hover
- **trade_off**: 静态形态 ↔ 形态动效（"focus 时变圆"）
- **intent**: 让 hover 这个动作有 character——morph 已经成为 brand 标识
- **avoid**:
  - 静态圆形（失去签名动作）
  - 静态方形（失去 friendly geometry）

### decision: Status dots 10x10px with 3px border (notch effect on avatar)
- **trade_off**: 平面 status indicator ↔ "notched" 立体感
- **intent**: 状态点感觉是"贴在 avatar 上"——视觉层级清晰
- **avoid**:
  - 1px hairline border（弱化 notch）
  - 完全无 border（融入 avatar 背景）

### decision: Cards/Embeds with 4px left-border in accent color
- **trade_off**: 全 outline border ↔ left-border-only（embedded link 标识）
- **intent**: 让 embed 在 chat 流中有"快速识别"——左边框颜色就告诉来源
- **avoid**:
  - 全 4-side outline（视觉重）
  - 无 border（融入 chat）

### decision: Tight chat-row spacing (4-8px between message groups)
- **trade_off**: 每条消息独立空间 ↔ 紧密分组（hours of scrollback 可扫）
- **intent**: chat 是滚动浏览工具——空间用在 group 之间，不是单条
- **avoid**:
  - 卡片化每条消息（破坏 chat 流）

## Layout

### decision: 4px base unit + fixed widths (rail 72 / sidebar 240 / member 240)
- **trade_off**: 自适应宽度 ↔ 固定宽度（chat tool 的 spatial vocabulary）
- **intent**: 让用户的肌肉记忆稳定——sidebar 永远在那个位置那个宽度
- **avoid**:
  - 响应式无固定 anchor（破坏 spatial memory）

## Motion

### decision: 350ms avatar circle-morph (snappy then settle)
- **trade_off**: 快 transition（无感） ↔ 中等 duration（让 morph 被看见）
- **intent**: morph 是 brand moment——值得 350ms 让用户感受
- **avoid**:
  - 100ms 太快（看不见）
  - 600ms+ 太慢（hover 卡顿）

### decision: 80ms tooltip fade
- **trade_off**: 长 fade（优雅但慢） ↔ 短 fade（即时反馈）
- **intent**: tooltip 是 functional——快出现快消失
- **avoid**:
  - 250ms+ fade（chat 操作密集时阻碍）

## Anti-patterns

- 不要在 chat 文字下 14px（可读性下降）
- 不要 Blurple 装饰使用（稀释 mention/CTA 信号）
- 不要单层 dark（破坏 3-step depth ladder）
- 不要给 status dot 用 Blurple（破坏 status mapping）
- 不要把 server avatar 静态化为圆形或方形（杀 morph 动作）
- 不要长 fade tooltip（阻碍密集操作）

---

## 抽取统计

- 显式 rationale: 14 条
- 推断 [inferred]: 0 条
- 6-section 覆盖：完整覆盖 dialect C
- chat 工具特化 rationale 较密集（avatar morph / mention wash / status notch）
