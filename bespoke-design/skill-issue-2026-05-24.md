# Bespoke-Design-System Skill 问题记录（命理决策辅助引擎 dogfooding 跑）

**日期**: 2026-05-24
**Skill 版本**: 1.9.1
**触发场景**: 用户提供两份 HTML 产品定位文档（命之上下限/核心共识），要求"用 bespoke skill 生成调性方案"
**执行方式**: 按 CLAUDE.md 指示直接跑源码（不调 Skill 工具），完整走完 B0-B6
**最终结果**: 5 项 P0 闸门全部通过（2 轮迭代），产物落在 `~/Documents/Downloads/bespoke-design/mingli-decision-engine/`

---

## 问题清单（轻量级）

| # | 严重度 | 类型 | 一句话描述 |
|---|-------|------|-----------|
| 1 | medium | docs/工具 mismatch | SKILL.md B1a 硬上限 7 题，但 AskUserQuestion 工具 maxItems=4，没有"分批问"逻辑 |
| 2 | low | docs gap | B2 retrieval 没有 official Python script — 每次都要手写 _tmp_b2_retrieval.py |
| 3 | low | 提示文档增强 | B6 自演化阈值是 ≥5 occurrences，但 adaptation_id 命名规则不够规范，导致同一逻辑 adaptation 在不同产物里可能用不同 id 不会累加 |

---

## 问题 #1: B1a 题数上限不一致

**位置**: 
- `plugins/bespoke-design-system/skills/bespoke-design-system/SKILL.md` §三 B1a 节："问题数量硬上限 7 条"
- AskUserQuestion 工具 schema: `"maxItems": 4`

**症状**: 严格按 SKILL.md 走，B1a 想问 5-7 题时，AskUserQuestion 直接报 InputValidationError。本次执行只能压缩到 4 题，剩余 2-3 维度走默认推断（暗黑模式 / 命理符号视觉 / 品牌名）。

**对本次产物的影响**: 中等。压缩到 4 题后我把最关键的（UI 关系 / 使用频率 / 平台 / 用户）问完了，剩余维度走 spiritual_saas defaults，没有对核心调性产生明显损害。但理论上 5-7 题模式可以探入更细。

**修复建议**:
- 选 A：把 SKILL.md 改成硬上限 4 题（与工具一致）
- 选 B：在 SKILL.md 中显式说明"如果用户的 Claude Code 版本支持 AskUserQuestion 单次 ≥5 题，按 7 上限走；否则压到 4 题"——但需要侦测能力
- 选 C：让 skill 支持"分批 ask"逻辑，但这违反"一次性追问铁律"
- **建议 A**：直接 sync 到 4 题，简化流程，反正生成方在 B1a 内部应该有能力做"top-N 重要性"排序

---

## 问题 #2: B2 retrieval 没 official script

**位置**: `plugins/bespoke-design-system/skills/bespoke-design-system/prompts/b2-rule-retrieval.md`

**症状**: prompt 详细描述了三层检索（archetype 硬筛 / kansei Jaccard / SD L2）算法，但没有 reference Python implementation。每次跑 B2 都要手写脚本：
- 加载 grammar/rules/*.yaml
- 实现 archetype OR filter
- 实现 kansei intersect / union 计算
- 实现 reverse_constraint 硬剔除
- 实现 SD L2 distance
- 实现 truncation cliff detection
- 输出 _b2-candidates.json 的 canonical schema (`candidate_rules` 顶层字段)

每次手写有出错风险（schema 漂移 / 字段名 typo / 计算公式不一致），且不便于改进。

**对本次产物的影响**: 低。我按 prompt 写的 script 跑通了，输出 100 candidates 5 section 全覆盖。但 dogfooding 应该有 `tools/b2_retrieve.py --profile <yaml> --output <file>` 让 B2 像 B3 一样可重现。

**修复建议**: 把 prompt 中算法 codify 为 `tools/b2_retrieve.py`。让 prompt 改写成"调 tools/b2_retrieve.py，输入 profile，得 _b2-candidates.json"。

---

## 问题 #3: adaptation_id 命名规范不够稳定

**位置**: SKILL.md B6 自演化触发 + scripts/consolidate-adaptations.md

**症状**: B6 提示"如果某条 adaptation occurrences ≥ 5 提议为新规则"，但 adaptation_id 命名规则没有标准化。本次我生成的 ids 形如：

```
kami-color-warm-parchment-canvas-001:hex_shift_to_yellower_for_xuanzhi_chinese
linear-app-color-translucent-borders-003:alpha_range_inverted_for_warm_light_canvas
```

格式是 `<source_rule_id>:<adaptation_description>`，但 description 部分完全自由（每次跑不一定生成同一字符串）。例如下次跑可能生成 `kami-color-warm-parchment-canvas-001:warm_hex_to_yellower_chinese` 或 `kami-color-warm-parchment-canvas-001:xuanzhi_hex_shift`——这些都不会累加 occurrences，永远不到 ≥5 阈值。

**对本次产物的影响**: 低（本次 15 个新 adaptations 都是首次出现）。但如果未来希望"同一逻辑 adaptation 在多个产物中累加"，需要 adaptation_id 标准化。

**修复建议**: 在 scripts/consolidate-adaptations.md 或 SKILL.md B6 节中加 adaptation_id 命名规范，类似：

```
<source_rule_id>:<dimension>:<from_to_summary_kebab>
例: kami-color-warm-parchment-canvas-001:canvas_hex:scalar_shift_yellower
例: linear-app-color-translucent-borders-003:alpha_range:invert_for_light_canvas
```

让 dimension + 简短 from-to 描述 deterministic，未来跑跑出来基本会撞上。

---

## 历史对照

对比 2026-05-05 那次跑（opc-workbench dogfooding，发现 1 个部署 blocker + 5 个源码 bug 已修到 v1.9.1）：

| 维度 | 2026-05-05 | 2026-05-24（本次） |
|---|---|---|
| skill 工具是否可用 | 否（plugin cache 不同步）| 不重要，按 CLAUDE.md 走源码 |
| 完整 B0-B6 跑通 | 是 | 是 |
| B3_resolve schema 一致性 | 1.9.0 前不一致 → 已修 | 修复有效，本次顺利 |
| coherence_check --design-md 参数 | 文档与代码不一致 → 已修 | 修复有效，本次顺利 |
| kansei_coverage_check user_kansei_coverage dict/string | 不一致 → 已修 + best-effort 兼容 | 修复有效，本次写 dict 一次通过 |
| B4 选择性使用 vs B3 子集 | 1.9.0 前模糊 → 已修明确"B3 是上限不是下限"| 修复有效，本次正确使用 rejected_alternative_X |
| rationale-judge round 1→2 自动迭代 | 是（2 轮抓真问题）| 是（round 1 抓 6 warnings，round 2 全 RESOLVED）|

**结论**: v1.9.1 修复的 5 个 source bug 在本次都没复发。剩下的 3 个本次 issue 都是 docs 完善级别（非 blocker，不影响产物质量）。

---

## 对产物质量的实际影响

5 项 P0 闸门全过 + rationale-judge round 2 pass + 0 blocker / 0 warning。

最关键的 dogfooding 检验：rationale-judge round 1 抓到了 **6 个真实 warnings**（不是装饰），包括：
- inheritance over-citation (notion-canvas 实际只贡献 neutrals)
- confidence calibration inconsistency (3 个 decisions 高估 confidence)
- cross-rule rescue stretch (kami canvas 不是 components rule)
- structural pattern signal (cross_rule_rescue 用得多 = corpus 欠覆盖)

这些都是真问题，且 round 2 修订后全部 RESOLVED — 验证了 v4 对抗式审查机制是有效的（不只是装饰）。

特别值得记录：**round 1 reviewer 抓到的"corpus 欠覆盖"global warning** 让我在 provenance 顶部加了 `decision_anchoring_statistics` 块 — 12 fully rule-anchored / 8 cross-rule-rescued / 4 brief-derived = 24 total。这个透明披露本来 round 1 没有，是审查催出来的，对消费这份 DESIGN.md 的下游用户很有价值。
