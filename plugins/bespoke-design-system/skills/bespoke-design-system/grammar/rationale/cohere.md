# Rationale — cohere

> 三段式 rationale 抽取自 `source-design-systems/cohere/DESIGN.md`。

## Visual Theme

### decision: enterprise polished command deck — black/white/cool-gray with extreme chromatic restraint
- **trade_off**: 多色 brand（活力） ↔ 极致 monochrome（enterprise authority）
- **intent**: 让 AI 看起来是 serious infrastructure 不是 consumer toy
- **avoid**: 消费者级配色 / 多 chromatic / 装饰性 color

### decision: 22px signature border-radius (cloud-like containment)
- **trade_off**: 中等圆角（普适） ↔ 22px signature（独特识别）
- **intent**: 让 card radius 成为品牌识别——既不是 sharp engineering 也不是 friendly large
- **avoid**: 8/12/16 standard radius / 圆角缺失工程感

## Color

### decision: purple-violet only in photographic hero bands and gradient sections
- **trade_off**: 全 monochrome（极简） ↔ purple-only-in-photography（戏剧对比）
- **intent**: 限制 chromatic 到大幅 photography hero，让它出现时携带最大视觉重量
- **avoid**: 装饰性 purple / multi-section chromatic distribution

### decision: interactive blue (#1863dc) only on hover/focus states
- **trade_off**: 静态 blue（清晰） ↔ 动态 blue（节俭）
- **intent**: blue 只在交互瞬间出现——hover/focus 时的"觉醒"信号
- **avoid**: 静态 blue 链接 / blue 装饰用法

## Typography

### decision: serif for declaration (CohereText) + sans for utility (Unica77)
- **trade_off**: 单字体（一致） ↔ serif+sans（声音分工）
- **intent**: serif 给 headline 出版研究权威感；sans 处理功能性文字
- **avoid**: 单字体 flatness / 装饰 serif 滥用

### decision: negative tracking at scale (-1.2 to -1.44px @60-72px) + single body weight (400)
- **trade_off**: 多 weight ladder（hierarchy 丰富） ↔ 单 weight + size only（克制）
- **intent**: hierarchy 靠 size 和 spacing，不靠 weight 对比
- **avoid**: 700 bold body / 多 weight 噪声
