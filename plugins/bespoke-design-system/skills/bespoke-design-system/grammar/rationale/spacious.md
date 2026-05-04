# Rationale — spacious

> 三段式 rationale 抽取自 `source-design-systems/spacious/DESIGN.md`（生成式 stub，3KB）。
> ⚠️ 该 DESIGN.md 是抽象 token table（"Layout & Structure" archetype 的 generic 模板），无具体产品案例 — 多数 rule 置信度 ≤ 0.5。

## Color & Typography

### decision: minimal clean — primary blue (#3B82F6) + 4 semantic colors + Open Sans body
- **trade_off**: 装饰 ↔ 极简 generic（appropriate to "spacious" archetype）
- **intent**: 让该 archetype 的代表色和字体作为 default baseline
- **avoid**: 装饰多色 / 装饰 serif / 紧凑节奏

### decision: 8pt baseline grid + Open Sans body + Montserrat display
- **trade_off**: 4-base 灵活 ↔ 8pt 标准（spacious / breathing emphasis）
- **intent**: 让"spacious"调性有更宽节奏
- **avoid**: 紧 4-base / 装饰 serif

## Typography

### decision: type scale 12/14/16/18/24/30/36 — wider step than dense systems
- **trade_off**: 紧 step（密度） ↔ 宽 step（spacious）
- **intent**: 让每级 size 跨度大，体现 spacious archetype
- **avoid**: 紧 12-13-14 step / 装饰 size
