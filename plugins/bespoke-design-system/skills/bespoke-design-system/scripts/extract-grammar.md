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

### v1.6.0 工作流加强

**第 0 步（必做）**：跑 `tools/prepare_a3_context.py <system_name>` 把所有相关
context（tokens.json 切片 / DESIGN.md sections / kansei 词表 / 12 archetype 表 /
peer 系统格式示例）汇总到一份 markdown，再开始写 A3。**这是 input prep 不
做 judgment**——所有 trade_off / kansei / archetype 选择仍由 LLM 完成。

**第 1.5 步（幂等保护）**：A3 入口先检查 `grammar/rules/<system_name>.yaml`
是否已存在：

- 存在 + 用户没说 `--force` / `--merge` → **停下并询问**："已检测到
  grammar/rules/<X>.yaml（N 条规则）。要 (a) 覆盖、(b) 合并新规则、(c) 跳过？"
- 存在 + `--force` → 备份到 `grammar/rules/.archive/<system>-<timestamp>.yaml`
  后覆盖
- 不存在 → 正常写

**第 N 步（必做）**：写完后立刻跑 `python3 tools/validate_rules.py
grammar/rules/<system_name>.yaml`。0 blocker 才能算 A3 完成。`tools/
rebuild_graph.py` 会再次跑完整 validate 作为 preflight。

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
     inferred: true                                    # 可选 — 标记本条规则的 preconditions / action 是
                                                       # 从 DESIGN.md 推断而非字面提取（仅当原文未直说时设置）。
                                                       # 与 rationale.md 的 `[inferred]` 文本标注语义一致。
                                                       # 当前 validator 接受这个字段，下游工具暂未消费，但保留以备未来 B4 inheritance 引用质量降级使用。
   ```

2. **关键参数化**：把具体值（`#5E6AD2`）抽象成参数化模式（`hue: 240°-260°`）；具体值留在 tokens.json
3. **Kansei 标签**：用 `references/kansei-theory.md` 的词表，给 3-5 个调性词（不要造词）
4. **Brand archetype 标签（v1.5.0 必填，v1.6.0 加强非懒标）**：用 `references/brand-archetypes.md` 的 12 原型词表，给 1-2 个最贴切的（primary 必填、secondary 可选）。**判断启发式**：
   - 看 system 整体 brand 定位（Linear → Sage+Creator；Discord → Everyman+Jester；Apple → Creator+Magician）
   - 看 rule 的 `why.establish` 字段：知识 / 真相 / 清晰 → Sage；转化 / 神秘 → Magician；归属 / 关怀 → Caregiver；秩序 / 权威 → Ruler；自由 / 反叛 → Outlaw；玩味 / 欢乐 → Jester；造物 / 工艺 → Creator；探索 / 边界 → Explorer；纯净 / 简单 → Innocent；亲和 / 民主 → Everyman；激情 / 美感 → Lover；力量 / 战胜 → Hero
   - **不要全打 Sage**——Sage 是默认懒标，强迫自己想清楚 secondary

   **v1.6.0 反懒标硬约束**：

   不要把 system-level archetype 简单复制到所有规则。**特别检查这几类规则**：

   - **anti_patterns 类**：往往**比 system 默认覆盖更广** archetype 集合
     （anti-pattern 守的是边界，多个 archetype 都可能踩坑）。例如 Linear 整体
     是 Sage+Creator，但 anti-pattern-warmth-in-chrome 同样适用 Magician 系产品
     （它们也容易 chromatic creep）。Anti-pattern 规则可以列 3+ archetype。
   - **voice 类**：往往**比 system 整体 archetype 更窄**。Discord 整体是
     Everyman+Jester，但 voice-imperative-no-marketing 实际更贴 Sage / Outlaw
     立场（克制 / 反市场化）。Voice 通常 1 个 archetype。
   - **rule-bearing 类**（color/typography/components/layout/depth_elevation）：
     默认 = system-level archetypes 通常合适，但若该规则的 why.establish 与
     system 默认 archetype 矛盾，**必须**调整。例如 vercel 的 voice-
     infrastructure-invisible-009 实际更贴 Sage 单原型，而非 system 默认的
     Sage+Magician。

   写完每条 rule 的 brand_archetypes 后，**回过头自问**："如果这条 rule
   只剩 system 默认 archetype 之一，是否削弱了它？"如果答案是"差不多"，那
   你就在懒标——重新决定。
5. **Confidence 校准（v1.7.0 具体 rubric — F8）**：

   不要凭手感标 confidence，按下表分档：

   | confidence | 信号 |
   |---|---|
   | **0.4-0.5** | DESIGN.md 是 stub / archetype template（< 5KB 且无具体产品引用）；首次抽取 |
   | **0.5-0.6** | 真实产品 DESIGN.md，但本规则只 emerges_from 单一系统 |
   | **0.6-0.7** | 同 product_type 的 2 个系统呈现同模式（merge 调高） |
   | **0.7-0.8** | 3+ 系统证实模式 + co_occurrence 频率 ≥ 0.6（A4 自动检测） |
   | **0.8+** | 5+ 系统 + 跨 product_type 通用模式（行业共识级） |

   **首次抽取的 rule 不能 ≥ 0.7**——因为还没机会证实多系统。validator
   `--strict` 会把 confidence > 0.7 但 emerges_from 只有 1 项的当 warning。

6. **Verbatim DESIGN.md 引用（v1.7.0 — F9）**：

   每条 rationale.md 里的 decision 段落**必须**包含至少一处对原 DESIGN.md
   的 verbatim 引用（用 markdown blockquote `>` 或代码块），让下游 B4
   inheritance.original_rationale 能 trace 回真实的设计师论述。

   **对的**：
   ```markdown
   ### decision: 4-tier near-black canvas

   原 DESIGN.md 段落（verbatim）：
   > Spotify's web interface is a dark, immersive music player that wraps
   > listeners in a near-black cocoon (`#121212`, `#181818`, `#1f1f1f`)
   > where album art and content become the primary source of color.

   - **trade_off**: ...
   - **intent**: ...
   - **avoid**: ...
   ```

   **不对**：
   ```markdown
   ### decision: 4-tier near-black canvas
   - **trade_off**: 单一深色 canvas 一致 ↔ 多层细微 lightness 深度信号
   ...
   ```
   （没有 DESIGN.md verbatim 引用 → B4 引用时只能 paraphrase 的 paraphrase，
   v1.5.1 闸 1.5 的对称问题在 A2 已经发生）

7. 如果你（LLM）观察到这条规则与某已有规则有显然冲突（如 dark canvas vs white canvas），**直接在 rule yaml 加 `known_conflicts`**——A4 阶段会把这些声明吸入图

8. **YAML pitfalls 预警（v1.7.0 — F1）**：

   LLM 写 yaml 时容易踩这几类语法陷阱，写完跑 `python3 tools/validate_rules.py`
   一定能抓出，但 **A3 阶段提前避开**省去 round-trip：

   - **括号在 unquoted scalar 后**：`neutral_hue_range: [50, 80] (olive_warmth)` 会炸——括号让 yaml 期望 mapping 而不是 scalar。**改**：整体加单引号：`'[50, 80] (olive_warmth)'`
   - **冒号在 unquoted 字符串里**：`reason: 5:1 contrast ratio` 会让 yaml 把 `5` 当 key、`1 contrast ratio` 当 value。**改**：`reason: '5:1 contrast ratio'`
   - **以特殊字符开头的字符串**：`- "适度透明" 是核心铁律：xxx`——开头双引号让 yaml 期望 quoted scalar，遇到 closing 后跟内容会炸。**改**：用单引号包整个，或转义内层引号
   - **多行字符串无 `|` / `>`**：长 reason 跨多行直接换行会被并入下一字段。**改**：用 `reason: |` 或 `reason: >` 块标量
   - **数字以 0 开头**：`opacity: 0.05` OK，但 `version: 0.5.0` 写成 `version: 0.5` 会被 parse 成 float。**改**：`version: '0.5.0'`
   - **`#` 在 unquoted 值里被当注释（v1.7.1 #41）**：`base_canvas: dark (#1e1f22 to #2b2d31)` 会被 yaml 解析为 `dark (` —— `#1e1f22 to #2b2d31)` 整段被当成行内注释吃掉。任何 hex 颜色 / `#anchor` / `# section` 都触发这个陷阱。**改**：整体加单引号：`base_canvas: 'dark (#1e1f22 to #2b2d31)'`。validate_rules 的 unmatched-parens 检测会捕获，但 A3 阶段提前避开。

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
