# Rationale — cal

> 三段式 rationale 抽取自 `source-design-systems/cal/DESIGN.md`。

## Color

### decision: pure grayscale brand — no chromatic, boldness via monochrome
- **trade_off**: 品牌色（识别） ↔ 全 grayscale（克制 + 普世性）
- **intent**: 让 boldness 不靠色彩而靠对比 + typography
- **avoid**: 装饰性 brand 色 / 多色干扰

### decision: warm near-black (#242424) for headings
- **trade_off**: 纯黑（精度） ↔ 暖近黑（亲和）
- **intent**: 比 #000 略软的近黑保留权威感同时不冷
- **avoid**: 纯黑塑料 / 过暖灰

## Typography

### decision: Cal Sans display + Inter body — display 极紧字距 + 1.10 lh
- **trade_off**: 单字体（一致） ↔ 双字体（display speak / body explain 分工）
- **intent**: Cal Sans 让 hero 像被刻在页面，Inter 让 body 像 rock-solid 阅读
- **avoid**: 单字体 hero 平淡 / 装饰 display 字体滥用

## Components & Layout

### decision: shadow-first depth (11 shadow definitions, ring border + soft diffused + inset)
- **trade_off**: border-first（精度） ↔ shadow-first（柔软三维）
- **intent**: 在 monochrome 系统里靠 shadow 提供 depth，让 surface 微立体
- **avoid**: 1px border 切割 / shadow 单层缺乏 sophistication

### decision: wide radius scale 2-9999px (pill) — geometric versatility
- **trade_off**: 单一 radius 上限（一致） ↔ 全 spectrum（chrome 角色多样）
- **intent**: 不同 chrome 元素用不同 radius 表达不同 affordance
- **avoid**: 全 0 sharp / 全 8 中庸
