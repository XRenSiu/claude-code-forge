# Rationale — canva

> 三段式 rationale 抽取自 `source-design-systems/canva/DESIGN.md`。

## Visual Theme

### decision: friendly face of design tools — invite-not-intimidate (vs Adobe authority)
- **trade_off**: 专业 authority（gravitas） ↔ 友好邀请（accessibility）
- **intent**: 让设计工具看起来人人可用，不是专业人士专属
- **avoid**: 严苛 chrome / 黑底冷感 / 工程师感

### decision: signature purple-to-blue gradient (#7d2ae8 → #00c4cc) for brand & magic moments
- **trade_off**: 单色品牌（一致） ↔ gradient（mood + 转化感）
- **intent**: 让 Pro / Magic 时刻有 transformative 视觉信号
- **avoid**: 装饰性 gradient / 多 gradient 竞争 / 动态 gradient（保持静态）

## Color & Components

### decision: weight contrast over color — 800 hero / 700 section / 400 body
- **trade_off**: 多色 hierarchy ↔ weight ladder hierarchy
- **intent**: 在多色 brand 之外让 typography weight 担纲层级
- **avoid**: 颜色 + weight 双重强调

### decision: 12-20px radii everywhere; 9999px pills for chips/tags
- **trade_off**: 严苛 geometry（精度） ↔ 友好 radius（亲和）
- **intent**: 让所有 chrome 友好可亲，不刻意工程化
- **avoid**: 直角 chrome / 8px 以下小圆角

## Typography

### decision: Canva Sans — rounded geometric for everything (one family)
- **trade_off**: 多字体（声音分工） ↔ 单 Canva Sans（友好统一）
- **intent**: 让一个 family 通过 weight 完成所有 hierarchy
- **avoid**: 多字体复杂度 / 装饰 serif 在 friendly tool 上的违和
