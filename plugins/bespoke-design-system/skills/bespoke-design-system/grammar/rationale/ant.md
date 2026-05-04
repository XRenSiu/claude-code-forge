# Rationale — ant

> 三段式 rationale 抽取自 `source-design-systems/ant/DESIGN.md`（生成式 stub，3KB）。
> ⚠️ 该 DESIGN.md 是抽象 token table 而非真实产品页 — 多数 rule 置信度 ≤ 0.5。

## Color & Typography

### decision: data-dense enterprise palette — primary blue (#1677FF) + 4 semantic colors

原 DESIGN.md 段落（auto-backfill）：
> > Category: Professional & Corporate
> > Structured, enterprise-focused design system emphasizing clarity, consistency, and efficiency for data-dense web applications.
- **trade_off**: 极简 monochrome ↔ 5-color semantic palette（enterprise data dense）
- **intent**: 让 dashboard 各类状态 / 操作 / 数据有显式语义色彩
- **avoid**: 单色 dashboard / 装饰多色 / non-semantic chromatic

### decision: Plus Jakarta Sans for primary + display + JetBrains Mono for code

原 DESIGN.md 段落（auto-backfill）：
> - **Scale:** 12/14/16/20/24/32
> - **Families:** primary=Plus Jakarta Sans, display=Plus Jakarta Sans, mono=JetBrains Mono
> - **Weights:** 100, 200, 300, 400, 500, 600, 700, 800, 900
> - Headings should carry the style personality; body text should optimize scanability and contrast.
- **trade_off**: 单字体（一致） ↔ sans + mono 分工（data UI 标准做法）
- **intent**: dashboard 数字 / code / log 用 mono 保对齐，UI 用 sans
- **avoid**: 装饰 serif / 单 family flatness

### decision: 12/14/16/20/24/32 type scale + 4/8/12/16/24/32 spacing scale

原 DESIGN.md 段落（auto-backfill）：
> - **Spacing scale:** 4/8/12/16/24/32
> - Keep vertical rhythm consistent across sections and components.
> - Align columns and modules to a predictable grid; avoid ad-hoc offsets.
- **trade_off**: 任意 scale ↔ 严格 step（enterprise consistency）
- **intent**: data-dense UI 需要严格节奏让 100+ element 不混乱
- **avoid**: 自由 step / 装饰 size / 不一致 spacing
