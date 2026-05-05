# B2 — 规则检索

> 当 SKILL.md 主流程进入 B2 时读取本文件作为执行指引。

## 你的任务

从 `grammar/rules/*.yaml`（含 `_generated.yaml`）里捞出与调性画像匹配的候选规则集。**直接在规则层检索，不在 DESIGN.md 层**。候选集应宽，冲突解决留到 B3。

---

## Step 1 — 加载规则库

读取 `grammar/rules/` 下所有 `.yaml` 文件（除 `_generated.yaml` 也一起读，不要排除）。每条规则反序列化为对象。

如果规则库为空（0 条规则）→ 立刻停下并要求用户先导入起步素材。**不要硬撑**。

## Step 2 — 三层检索

### Layer 1: Archetype 主原型硬筛

保留 `preconditions.brand_archetypes` 含画像 `brand_archetypes.primary` 的规则。

如果 secondary 也明确指定，把 secondary 命中的规则也纳入候选（OR 关系）。

如果某条规则的 `preconditions.brand_archetypes` 为空（即"任何 archetype 都适用"），保留——这类是基础规则。

### Layer 2: Kansei 软排

对 Layer 1 留下的每条规则，计算 Kansei 匹配分：

```
kansei_score = |intersect(rule.preconditions.kansei, profile.kansei_words.positive)|
             / |union(rule.preconditions.kansei, profile.kansei_words.positive)|
```

**硬剔除**：如果 `intersect(rule.preconditions.kansei, profile.kansei_words.reverse_constraint)` ≠ 空 → 该规则与 reverse 约束直接冲突，剔除。

按 kansei_score 降序排。

### Layer 3: SD 距离修正

对每条留下的规则，如果其 preconditions 含 `sd_anchors`（部分规则会标），计算与画像 `semantic_differentials` 的 L2 距离：

```
sd_distance = sqrt(Σ (rule.sd_anchors[axis] - profile.semantic_differentials[axis])²)
```

最终分数：

```
final_score = kansei_score - 0.3 * sd_distance + 0.1 * confidence
```

confidence 来自规则 yaml 的 `confidence` 字段（emerges_from 数量与一致性）。

按 final_score 降序排。

## Step 3 — 截取候选集

取 final_score 最高的若干条作为候选集。规模随规则库总量自适应：

- **小规则库**（总规则 < 50）：保留 final_score > 0 的所有规则（不截断）
- **中规则库**（50-200）：取 top-50 至 top-100
- **大规则库**（>200）：取 top-100 至 top-200，且如果第 100-200 条之间出现 score 断崖（最大值 < 50%），从断崖处截

## Step 4 — Section 覆盖核查

确认候选集对 **5 个 rule-bearing section**（`color / typography / components / layout / depth_elevation`）每个都至少有规则覆盖。规则库小时 1 条即可；规则库大时建议每 section 至少 5 条。

某个 section 完全没规则 → 从该 section 的 `defaults.yaml` 中拿 `backstop_rules`（按 product_category 匹配）补齐。backstop 规则也是 `provenance: original` 的，但来自规则库内置兜底。

**4 个元 section**（Visual Theme / Do's & Don'ts / Responsive / Agent Guide）不需要在 B2 单独检索——它们在 B4 阶段从 rule-bearing 派生。

## Step 5 — 输出候选集

**落盘文件名**：`<output_dir>/_b2-candidates.json`（JSON 文件，不是 YAML 文件——`tools/b3_resolve.py` 用 `json.load` 读取）。
**顶层字段名**：必须是 `candidate_rules`（不是 `candidates`、`rules` 等其他名称）。`tools/b3_resolve.py` v1.9.1 起对 `candidates` 做了 best-effort 兼容，但 canonical 字段名始终是 `candidate_rules`。

输出结构：

```yaml
candidate_rules:
  - rule_id: linear-color-balance-001
    final_score: 0.78
    breakdown:
      kansei_score: 0.6
      sd_distance: 0.3
      confidence: 0.85
    source_systems: [linear, vercel, supabase]
    section: color
  - ...

stats:
  total: 142
  by_section:
    color: 18
    typography: 22
    ...
  archetype_filter_kept: 312
  kansei_filter_kept: 198
  reverse_constraint_blocked: 14
```

把候选集传给 B3。

---

## 检查清单（B2 产出前必过）

- [ ] 候选集规模符合规则库规模档位（小库不截、中库 top-50~100、大库 top-100~200）
- [ ] 5 个 rule-bearing section 都至少有 1 条规则覆盖（缺则从 defaults.yaml backstop 补）
- [ ] 没有任何规则与画像 `reverse_constraint` Kansei 词直接冲突
- [ ] final_score 排序正确，breakdown 字段完整
- [ ] `_generated.yaml`（如存在）已被加载
- [ ] 无候选时已停止流程并提示用户导入素材
