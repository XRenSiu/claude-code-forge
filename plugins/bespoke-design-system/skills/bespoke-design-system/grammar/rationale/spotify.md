# Rationale — spotify

> 三段式 rationale 抽取自 `source-design-systems/spotify/DESIGN.md`。

## Visual Theme

### decision: content-first darkness — UI 退到阴影里让 album art 与 podcast cover 发光

原 DESIGN.md 段落（auto-backfill）：
> **Shadow Philosophy**: Spotify uses notably heavy shadows for a dark-themed app. The 0.5 opacity shadow at 24px blur creates a dramatic "floating in darkness" effect for dialogs and menus, while the 0.3 opacity at 8px blur provides a more subtle card lift. The unique inset border-shadow combination on inputs creates a recessed, tactile quality.
- **trade_off**: 标准 dark theme（高对比可读） ↔ content-first darkness（UI 让位给内容）
- **intent**: 让产品"消失"——音乐 / 播客 / 歌单作为唯一色彩源
- **avoid**: brand 色喧宾夺主 / UI chrome 抢内容戏 / chromatic 装饰

## Color

### decision: Spotify Green (#1ed760) as singular brand — never decorative, always functional

原 DESIGN.md 段落（auto-backfill）：
> > Category: Media & Consumer
> > Music streaming. Vibrant green on dark, bold type, album-art-driven.
- **trade_off**: 多色 brand（活泼） ↔ 单 chromatic green（克制 + 强信号）
- **intent**: green = play / active / CTA 三位一体的功能信号
- **avoid**: 装饰性 green / 多色 brand 竞争 / non-functional brand 出现

### decision: 4-tier near-black canvas (#121212 / #181818 / #1f1f1f / #252525)

原 DESIGN.md 段落（auto-backfill）：
> Spotify's web interface is a dark, immersive music player that wraps listeners in a near-black cocoon (`#121212`, `#181818`, `#1f1f1f`) where album art and content become the primary source of color. The design philosophy is "content-first darkness" — the UI recedes into shadow so that music, podcasts, and playlists can glow. Every surface is a shade of charcoal, creating a theater-like environment where the only true color comes from the iconic Spotify Green (`#1ed760`) and the album artwork itself.
- **trade_off**: 单一深色 canvas（一致） ↔ 多层细微 lightness（深度信号）
- **intent**: 深色阶进取代 shadow，让 elevated cards 有"略微浮起"
- **avoid**: 纯黑 #000 单调 / shadow elevation 与 dark 冲突

## Typography & Components

### decision: pill-and-circle geometry — 500-9999px button radius + 50% circle play button

原 DESIGN.md 段落（auto-backfill）：
> **Dark Pill**
> - Background: `#1f1f1f`
> - Text: `#ffffff` or `#b3b3b3`
> - Padding: 8px 16px
> - Radius: 9999px (full pill)
> - Use: Navigation pills, secondary actions
- **trade_off**: 标准 button radius（普适） ↔ 极端 pill + circle（tactile premium audio device）
- **intent**: 让 button 像 hardware controls——physical, rounded, touch-built
- **avoid**: 直角 / 中等 radius / 装饰性 corner

### decision: heavy 8px-24px shadow on elevated + inset border combo

原 DESIGN.md 段落（auto-backfill）：
> What distinguishes Spotify is its pill-and-circle geometry. Primary buttons use 500px–9999px radius (full pill), circular play buttons use 50% radius, and search inputs are 500px pills. Combined with heavy shadows (`rgba(0,0,0,0.5) 0px 8px 24px`) on elevated elements and a unique inset border-shadow combo (`rgb(18,18,18) 0px 1px 0px, rgb(124,124,124) 0px 0px 0px 1px inset`), the result is an interface that feels like a premium audio device — tactile, rounded, and built for touch.
- **trade_off**: flat（极简） ↔ heavy shadow + inset（tactile depth）
- **intent**: dialog / menu / elevated panel 像 physical layer 浮起
- **avoid**: shadow 缺失的扁平 / 单层 shadow 缺乏层级

### decision: SpotifyMixUI 全球字体栈，含 CJK/Arabic/Hebrew/Cyrillic/Devanagari fallback

原 DESIGN.md 段落（auto-backfill）：
> The typography uses SpotifyMixUI and SpotifyMixUITitle — proprietary fonts from the CircularSp family (Circular by Lineto, customized for Spotify) with an extensive fallback stack that includes Arabic, Hebrew, Cyrillic, Greek, Devanagari, and CJK fonts, reflecting Spotify's global reach. The type system is compact and functional: 700 (bold) for emphasis and navigation, 600 (semibold) for secondary emphasis, and 400 (regular) for body. Buttons use uppercase with positive letter-spacing (1.4px–2px) for a systematic, label-like quality.
- **trade_off**: 单 latin family（实施简单） ↔ multi-script fallback（global reach）
- **intent**: 覆盖 spotify 全球 80+ 国家受众
- **avoid**: 只 latin 的局限 / 通用 system font 缺品牌
