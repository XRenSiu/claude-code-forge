# extract-grammar — 单套 DESIGN.md 拆解 4 步流程

> 被 `add-new-design-system.md` / `import-from-collection.md` / `rebuild-graph.md` 调用，也可独立跑。

## 输入

一个具体的 `<system_name>`，其 DESIGN.md 已位于 `source-design-systems/<system_name>/DESIGN.md`。

## 输出

- `grammar/tokens/<system_name>.json` (A1，程序化)
- `grammar/rationale/<system_name>.md` (A2，LLM)
- `grammar/rules/<system_name>.yaml` (A3，LLM)
- 更新 `grammar/graph/rules_graph.json` (A4，程序化)

---

## 工作分配（关键架构）

| 步骤 | 谁做 | 为什么 |
|---|---|---|
| **A1** Token 提取 | `tools/extract_tokens.py`（程序化） | 90%+ 字段是显式参数（hex / px / family / weight），正则就行 |
| **A2** Rationale 三段式 | LLM | 设计判断（trade_off / intent / avoid）需要语义理解，不能正则 |
| **A3** Rule 抽象 + Kansei 标签 | LLM | 参数化模式 + Kansei 词需要设计直觉 + 理论引用 |
| **A4** 关系图 | `tools/rebuild_graph.py`（程序化） | 4 类关系基于显式 yaml 字段，确定性算法 |

**不要让 LLM 重复程序化部分能做的事**——A1/A4 必须走 tools。LLM 只做 A2/A3。

---

## A1 — Token 层提取（程序化）

**直接调工具**：

```bash
python3 tools/extract_tokens.py source-design-systems/<system_name>/DESIGN.md
# 输出 grammar/tokens/<system_name>.json
```

工具自动：
- 调用 `tools/scan_dialect.py` 识别方言（A/B/C/...）+ 切片成 9-section 内部 slug
- 跑各 section 的字段抽取器（color hex / typography family + scale / spacing base + scale / radius / motion duration / breakpoints / dos_donts bullets）
- 标 `_confidence: high|medium|low` 让你（LLM）知道哪些字段质量高、哪些需要补

**LLM 仅在以下情况介入**：

- 程序化输出含 `_confidence: low` 的字段 → 读原文 + 用 markdown 解析手动补
- `sections_unhandled` 或 `sections_meta_for_llm` 列出的 section（visual_theme, agent_guide）→ 读原文 + 总结进散文/QA 字段

**质量检查**：
- [ ] tokens.json 文件存在且 parse 通过
- [ ] color/typography/spacing 的 high-confidence 字段非空
- [ ] sections_present 与 DESIGN.md 实际 section 数对得上

---

## A2 — Rationale 层抽取（LLM 主体工作）

**输入**：tokens.json + 原始 DESIGN.md

**输出**：`grammar/rationale/<system_name>.md`

**关键要求**：每个 decision 必须**三段式**：`trade_off` / `intent` / `avoid`。详见 `references/reflective-practice.md`。

**LLM 操作步骤**：

1. 读 `grammar/tokens/<system_name>.json`（含 dialect 标记 + sections_present + 程序化抽到的字段）
2. 读 `source-design-systems/<system_name>/DESIGN.md` 全文（关键关注散文段落 + Do's/Don'ts）
3. 对每个关键决策（一套设计系统通常 8-15 个），抽取：
   - `decision` —— 一句话描述（"主色 #5E6AD2 偏紫的冷蓝"）
   - `trade_off` —— 在哪两端取了平衡（"工程精度感 ↔ 人文温度"）
   - `intent` —— 希望传达的核心感受（"严肃但不冷漠"）
   - `avoid[]` —— 明确想避免的视觉/感受（["纯蓝带来的医疗器械感", "纯紫带来的游戏 UI 感"]）
4. DESIGN.md 没明说时 → 用文本证据推断，**必须**在条目上标 `[inferred]`
5. 写到 `grammar/rationale/<system_name>.md`，按 section 分组

**质量检查**：
- [ ] 每个 decision 三段式都有内容（不空）
- [ ] avoid 项措辞具体（"医疗器械感"），不抽象（"不专业感"）
- [ ] 推断条目标 `[inferred]`
- [ ] 不强行编造（如某 section DESIGN.md 写得很简短，rationale 也对应简短）

---

## A3 — Rule 层抽象（LLM 主体工作）

**输入**：tokens.json + rationale.md

**输出**：`grammar/rules/<system_name>.yaml`

**LLM 操作步骤**：

1. 对每个 rationale decision 输出一条 rule，按 schema（详见 `references/design-md-spec.md` 的 8 个 rule-bearing slug）：
   ```yaml
   - rule_id: <system>-<section_slug>-<sequence>     # e.g. linear-app-color-balance-001
     section: color | typography | spacing | layout | components | depth_elevation | motion | voice | anti_patterns
     preconditions:
       product_type: [...]
       tone: [...]
       kansei: [...]                                  # 词表见 references/kansei-theory.md
       brand_archetypes: [...]                        # v1.5.0 必填 — 词表见 references/brand-archetypes.md
       sd_anchors: { warm_to_cold, ornate_to_minimal, serious_to_playful, modern_to_classical }  # optional
     action:
       <参数化模式 — 不放具体值（具体值在 tokens.json）>
     why:
       establish: <一句话>
       avoid: [...]
       balance: <a ↔ b>
     emerges_from: [<system_name>]                    # 首次拆解只有自己
     provenance: original                              # original | generated | merged
     confidence: 0.5-0.9
     known_conflicts:                                  # 可选 — 如观察到与已有规则冲突
       - rule: <rule_id>
         reason: <一句话>
   ```

2. **关键参数化**：把具体值（`#5E6AD2`）抽象成参数化模式（`hue: 240°-260°`）；具体值留在 tokens.json
3. **Kansei 标签**：用 `references/kansei-theory.md` 的词表，给 3-5 个调性词（不要造词）
4. **Brand archetype 标签（v1.5.0 必填）**：用 `references/brand-archetypes.md` 的 12 原型词表，给 1-2 个最贴切的（primary 必填、secondary 可选）。**判断启发式**：
   - 看 system 整体 brand 定位（Linear → Sage+Creator；Discord → Everyman+Jester；Apple → Creator+Magician）
   - 看 rule 的 `why.establish` 字段：知识 / 真相 / 清晰 → Sage；转化 / 神秘 → Magician；归属 / 关怀 → Caregiver；秩序 / 权威 → Ruler；自由 / 反叛 → Outlaw；玩味 / 欢乐 → Jester；造物 / 工艺 → Creator；探索 / 边界 → Explorer；纯净 / 简单 → Innocent；亲和 / 民主 → Everyman；激情 / 美感 → Lover；力量 / 战胜 → Hero
   - **不要全打 Sage**——Sage 是默认懒标，强迫自己想清楚 secondary
5. **Confidence 起步**：单一系统拆解默认 0.5-0.7；后续合并 / 共现会自动调高
6. 如果你（LLM）观察到这条规则与某已有规则有显然冲突（如 dark canvas vs white canvas），**直接在 rule yaml 加 `known_conflicts`**——A4 阶段会把这些声明吸入图

**质量检查**：
- [ ] 每条规则有完整 preconditions（product_type / kansei / **brand_archetypes** 都不为空）
- [ ] brand_archetypes 至少 1 个，最多 3 个，全部来自 12 原型词表
- [ ] action 是参数化的，不是具体值
- [ ] kansei 词与 `references/kansei-theory.md` 词表对齐
- [ ] confidence ∈ [0, 1]
- [ ] section slug 是 8 个统一 slug 之一（不要造新名）

---

## A4 — Pattern Language 关系图构建（程序化）

**直接调工具**（不要让 LLM 推关系——确定性算法更可靠）：

```bash
python3 tools/rebuild_graph.py
# 全量重算 grammar/graph/rules_graph.json
```

工具自动：
- 加载 `grammar/rules/*.yaml`（含 `_generated.yaml`）
- 按 section_dependency_order 推 depends_on / constrains
- 按 kansei 重叠 + 同 section 判 co_occurs_with（带 frequency）
- 按 kansei 反义词 + why.avoid 互引判 conflicts_with
- 吸入 yaml 中显式声明的 `known_conflicts`（A3 阶段标的）
- 双向边对称性自动维护

**何时跑**：每加 ≥ 3 套新规则、或修改了 conflict 判断逻辑后。每批结束的固定动作。

---

## 收尾

1. 更新 `grammar/meta/source-registry.json`（`tools/register_systems.py` 自动跑）
2. 更新 `grammar/meta/version.json` 的 `rules_version`（minor +0.1.0）
3. 更新 `grammar/meta/provenance-index.json`：登记新规则的 rule_ids → system 映射

完成后输出报告：

```
✅ Extracted <system_name>
   tokens: NN fields (programmatic, _confidence histogram: ...)
   rationale: NN decisions (LLM)
   rules: NN rules (LLM)
   graph: incremental NN nodes, NN edges (programmatic)
```
