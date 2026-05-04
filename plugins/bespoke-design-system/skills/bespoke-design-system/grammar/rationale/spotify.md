# Rationale — spotify

> 三段式 rationale 抽取自 `source-design-systems/spotify/DESIGN.md`。

## Visual Theme

### decision: content-first darkness — UI 退到阴影里让 album art 与 podcast cover 发光
- **trade_off**: 标准 dark theme（高对比可读） ↔ content-first darkness（UI 让位给内容）
- **intent**: 让产品"消失"——音乐 / 播客 / 歌单作为唯一色彩源
- **avoid**: brand 色喧宾夺主 / UI chrome 抢内容戏 / chromatic 装饰

## Color

### decision: Spotify Green (#1ed760) as singular brand — never decorative, always functional
- **trade_off**: 多色 brand（活泼） ↔ 单 chromatic green（克制 + 强信号）
- **intent**: green = play / active / CTA 三位一体的功能信号
- **avoid**: 装饰性 green / 多色 brand 竞争 / non-functional brand 出现

### decision: 4-tier near-black canvas (#121212 / #181818 / #1f1f1f / #252525)
- **trade_off**: 单一深色 canvas（一致） ↔ 多层细微 lightness（深度信号）
- **intent**: 深色阶进取代 shadow，让 elevated cards 有"略微浮起"
- **avoid**: 纯黑 #000 单调 / shadow elevation 与 dark 冲突

## Typography & Components

### decision: pill-and-circle geometry — 500-9999px button radius + 50% circle play button
- **trade_off**: 标准 button radius（普适） ↔ 极端 pill + circle（tactile premium audio device）
- **intent**: 让 button 像 hardware controls——physical, rounded, touch-built
- **avoid**: 直角 / 中等 radius / 装饰性 corner

### decision: heavy 8px-24px shadow on elevated + inset border combo
- **trade_off**: flat（极简） ↔ heavy shadow + inset（tactile depth）
- **intent**: dialog / menu / elevated panel 像 physical layer 浮起
- **avoid**: shadow 缺失的扁平 / 单层 shadow 缺乏层级

### decision: SpotifyMixUI 全球字体栈，含 CJK/Arabic/Hebrew/Cyrillic/Devanagari fallback
- **trade_off**: 单 latin family（实施简单） ↔ multi-script fallback（global reach）
- **intent**: 覆盖 spotify 全球 80+ 国家受众
- **avoid**: 只 latin 的局限 / 通用 system font 缺品牌
