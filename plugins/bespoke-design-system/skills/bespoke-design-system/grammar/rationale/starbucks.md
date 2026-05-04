# Rationale — starbucks

> 三段式 rationale 抽取自 `source-design-systems/starbucks/DESIGN.md`。

## Visual Theme

### decision: warm cream canvas (#f2f0eb / #edebe9) — references café materials not cold white
- **trade_off**: 纯白 canvas（普适） ↔ 暖 cream（café material 隐喻）
- **intent**: canvas 让人想起 paper napkins / café walls / wood finishes，与店内体验同源
- **avoid**: 纯白 #fff 临床感 / 冷灰 / 装饰性 cream

## Color

### decision: 4-tier green system (Starbucks / Accent / House / Uplift) each mapped to specific role
- **trade_off**: 单 brand green（一致） ↔ 4-tier 分工（h1 vs CTA vs footer vs accent）
- **intent**: 让"绿"不是装饰而是结构化品牌系统——每层 green 有特定 surface role
- **avoid**: 单 green 一刀切 / 多色装饰 / 非系统化 chromatic

### decision: gold (#cba258) only on Rewards-status ceremony — never general accent
- **trade_off**: gold 装饰（活泼） ↔ gold 仅 ceremony（克制 + valued）
- **intent**: 让 gold 出现时携带 ceremony 重量——partnership badges / status 成就
- **avoid**: 装饰性 gold / 多 gold 用法稀释 / general-purpose gold

## Components

### decision: 50px full-pill universal buttons + scale(0.95) active press
- **trade_off**: 标准 button radius（普适） ↔ pill + 微缩动效（hospitality + tactile）
- **intent**: 让 buttons 像 store signage — friendly, legible, never shouting
- **avoid**: 直角 / 中等 radius / 静态 button

### decision: Frap floating CTA — 56px circle in Green Accent w/ layered shadow
- **trade_off**: standard CTA placement（一致） ↔ floating circle（signature feature）
- **intent**: 让 ordering experience 有 "iconic move" 视觉记忆点
- **avoid**: hidden CTA / 弱 elevation / 多 floating button 竞争

## Typography

### decision: SoDoSans + serif (Lander Tall) for Rewards + script (Kalam) for Careers
- **trade_off**: 单 family（一致） ↔ 三 family 分上下文（disciplined surface diversity）
- **intent**: 让字体应 surface 切换——但每种字体只在特定 page 出现
- **avoid**: 多字体随机出现 / family flatness / 装饰 serif 滥用
