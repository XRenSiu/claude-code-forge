# Bespoke-Design-System Skill 问题记录（qanat 生成）

> **✅ 已修复 2026-06-14（v1.10.0）** — 见文末「修复记录」。#1+#2 用统一的 UNKNOWN-维度掩码机制修复，#3 文档修正。

**日期**：2026-06-13（修复 2026-06-14）
**Skill 版本**：1.9.1 → **1.10.0（已修复）**
**触发场景**：在本仓库下为 `/Users/xrensiu/development/owner/qanat/README.md` 生成 DESIGN.md（interactive 模式，Sage+Ruler·暖·厚重）
**执行方式**：直接跑源码完整走 B0-B6（按 CLAUDE.md 默认路径）
**先看**：`skill-issue-2026-05-05.md`（上次 6 个问题，#2-#5 schema/docstring 类已在 v1.9.1 修复，本次未复发）

---

## 问题清单

| # | 严重度 | 类型 | 一句话描述 |
|---|-------|------|-----------|
| 1 | **high** | 算法偏差 | `build_neighbor_corpus.encode()` 的 `has_serif` 用字面子串检测，对**整个 corpus 结构性失效**——所有 137 套素材的 `typography.families` 都用品牌字体名（CursorGothic / CohereText / Anthropic Sans / BMWTypeNextLatin），无 serif/sans 类别标记，连真衬线（CohereText 实为衬线）都被编码成 `has_serif=0`。后果：corpus 该维度恒为 0，任何**诚实声明衬线**的新设计吃满 `weight=1.5` 的 0.234 全 corpus 距离惩罚，neighbor_check 结构性偏向无衬线设计。 |
| 2 | medium | 度量偏差 | neighbor corpus 由 A1-only tokens 编码（无 `color.contrast` / `color.status` / `components.buttons` / `no_explicit_section_dividers` 等 B4 合成字段），全 corpus 这些维度=0。一份**走完 B4 的完整 tokens.json** 在这些维度=1，被惩罚 ~0.24（status 0.135 + contrast 0.103 + components/dividers）。即「编码完整度差异」被误计成「设计空间距离」，使 B4 完整产物更难过 neighbor 闸。 |
| 3 | low | 流程/文档 | SKILL.md §八 与 b5-p0-gate.md 引用 skill-local `agents/rationale-judge.md`，但该文件实际只在 **plugin 级** `plugins/bespoke-design-system/agents/rationale-judge.md`（已注册为 agent 类型 `bespoke-design-system:rationale-judge`）。skill 目录下无此文件，按字面路径 Read 会 404。CLAUDE.md 已用 Agent 工具调用绕过，但 b5 prompt 的路径表述应修正。 |

---

## 问题 #1 详情（核心）

**位置**：`tools/build_neighbor_corpus.py` line ~231

```python
has_serif = 1.0 if any(k in family_names for k in ('serif','georgia','cormorant','didone')) else 0.0
```

**核验**：corpus 中真衬线系统的 families 字段：
- cursor: `[{"role":"display","family":"CursorGothic"}]`（无 body serif，实际 cursor body 用 jjannon 衬线但未录入）
- cohere: `[{"role":"display","family":"CohereText"}, ...]`（CohereText 是衬线，但名字无 "serif"）
- claude: `[{"role":"body","family":"Anthropic Sans"}, ...]`
- 全 corpus 无任何 family 名含 `serif/georgia/cormorant/didone` 子串 → has_serif 全 0

**实测影响（qanat）**：
- 原始 neighbor 距离 0.40（needs_review），最近邻 cursor
- 逐维诊断：`has_serif` 单维贡献 0.234（最大），`has_status_palette` 0.135，`body_contrast` 0.103，`no_explicit_dividers` 0.104，`num_button_variants` 0.080——前 5 名全是 corpus 系统性=0 的维度
- 中和这两个假象后真实设计空间距离 = **0.2449（最近 cursor，通过）**——证明 qanat 设计确实在 corpus 内，0.40 是测量假象不是漂移

**修复建议**（择一，需独立 commit + version bump + 重建 corpus）：
1. `encode()` 优先读显式类别字段（`typography.families[].category` 或 `typography.display.class` 含 'serif'），子串作 fallback；**并**给 corpus 的 137 套 tokens 补 `category` 标记（A1 重抽或人工）——否则只改 encode 不补 corpus 仍无法让 corpus 衬线系统翻成 1
2. 改用「掩码距离」：只在**双方都非缺省**的维度上算距离（避免 B4 完整产物被「拥有 corpus 没有的字段」惩罚），可同时缓解 #1 与 #2
3. 降 `has_serif` 权重（当前 1.5）至该维度在 corpus 有真实信号为止

**本次处置（不改共享数据）**：
- tokens.json 按真实字体名命名（`GT Sectra` / `Söhne` / `Berkeley Mono`，符合 Linear 写 "Inter Variable"、cohere 写 "CohereText" 的命名惯例），衬线性质保留在 `typography.display.class="transitional_literary_serif"` + `families[].category="serif"` + DESIGN.md §3 散文。**未删任何真实 B4 字段**（status/contrast/components 是 qanat 真实且有价值的内容，删之即 gaming）。
- neighbor 闸如实跑、如实记 needs_review，并在 gate 报告附「corpus 可比距离 0.2449 / 最近邻 cursor」作为 needs_review 要求的 rationale 核查证据。
- 未在生成中途改 encode/corpus/weights——那是影响全体用户的 skill 变更，应独立提案 + version bump + 验证。

## 本次是否影响产物质量

**否**。coherence 0 blocker（score 1.0，6/6 子检查全过）、archetype Sage/Ruler 0 blocker 0 warning。neighbor 的 needs_review 是**度量层假象**，corpus 可比距离与最近邻（cursor，暖深色+衬线+等宽编辑器）都印证设计在已知良好空间内。产物 DESIGN.md 的设计判断不受影响。

> 建议：把 #1/#2 作为 neighbor_check 的已知局限写进 `references/tacit-knowledge-boundary.md` 或 b5-p0-gate.md，并排期一次 corpus 重抽（补 font category + 关键 B4 字段），让 neighbor 闸对 B4 完整 / 衬线产物公平。

---

## 修复记录（2026-06-14 · v1.10.0）

**根因统一**：编码器对「源数据缺失」的维度**伪造默认值**（`body_contrast=0` / `line_height=1.5` / `button_radius=0.333` / `has_serif=0`…），把「未知」当成「真值」。跨 A1-only corpus 这让 9 个维度恒为常数（std=0），加上 has_serif 基本是噪声——任何走完 B4 / 诚实声明衬线的新设计都被「与伪造常数不同」白白惩罚。#1 与 #2 是同一个根因的两面。

**修法（统一机制：UNKNOWN-维度掩码）**：
1. `tools/build_neighbor_corpus.py` `encode()`：源数据缺失时发 `None`（UNKNOWN）而非伪造默认；新增 `_detect_serif_humanist()` 按显式 `families[].category` / `display.class` / 已知字体名判定衬线，判不出即 `None`（品牌字体名不再被当成 sans）。
2. `checks/neighbor_check.py` `weighted_euclidean()`：**任一方为 None 的维度跳过**，分母仍用全权重 → corpus 内部距离不变（那些维度本就对 corpus 内部贡献 0），新设计不再在 corpus 没记录的维度上吃距离。
3. 重建 corpus（`python3 tools/build_neighbor_corpus.py`）。

**验证**：
| 指标 | 修复前 | 修复后 |
|---|---|---|
| corpus 内部最近邻 median / max | 0.132 / 0.323（2 套 >0.3） | **0.120 / 0.262（0 套 >0.3）** 更紧聚类，阈值更稳 |
| 自一致性（cohere 重编码找自己） | — | **0.0** ✓ |
| **qanat neighbor** | needs_review 0.3267 | **pass 0.2449（最近邻 cursor）** ✓ |
| 最近邻配对合理性 | — | linear↔cohere / stripe↔revolut / cursor↔mistral-ai ✓ |

**阈值无需重标定**：全权重分母保证 corpus 内部距离不变（退化维度对 corpus 内部本就贡献 0），所以 0.3 阈值语义保持；且修复后全 137 套最近邻 <0.3，留有余量。

**#3（文档路径）**：SKILL.md §B5 表格的 rationale-judge 引用从 skill-local `agents/rationale-judge.md` 改为 plugin 级 `../../agents/rationale-judge.md` + 注明经 `Agent(subagent_type="bespoke-design-system:rationale-judge")` 调用。

**版本**：1.9.1 → 1.10.0（三处同步：SKILL.md / plugin.json / marketplace.json）。corpus 数据文件 `grammar/meta/neighbor-corpus.json` 已随之重建（向量含 null = UNKNOWN）。

**未做**：未给 137 套 corpus tokens 补 `category`/B4 字段（那是独立的 corpus 重抽增强）；当前修复让 neighbor 闸对「衬线 / B4 完整」产物**公平**已足够。
