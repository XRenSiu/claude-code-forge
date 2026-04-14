---
reference: density-scoring
version: 0.1.0
borrowed_from: reverse-use of anti-distill 4-level classifier
consumed_by: persona-judge (dimension 9 — Density; frontmatter `density_score`)
depends_on: plugins/persona-distill/skills/distill-meta/references/extraction/density-classifier.md
---

# Density Scoring — Operational Procedure

> persona-judge 的**段落级内容审计**。把 anti-distill 的 4 级 classifier 反向使用：
> 高比例 `REMOVE`/`MASK` = 高密度，高比例 `DILUTE` = 正确废话。
> 产出一个 `[0, 10]` 的 `density_score`；**< 3.0 强制 `verdict: FAIL`**，覆盖总分。

## Pipeline / 四步管线

```
┌──────────────────────────────────────────────────────────────┐
│ 1  SEGMENT   切分 SKILL.md + components/*.md → 段落数组     │
│ 2  CLASSIFY  对每段调用 density-classifier → 打标签         │
│ 3  AGGREGATE raw = 2·REMOVE + 1·MASK + 0·SAFE - 1·DILUTE    │
│              normalize → density_score ∈ [0, 10]            │
│ 4  EMIT      写入 frontmatter；< 3.0 时覆盖 verdict: FAIL   │
└──────────────────────────────────────────────────────────────┘
```

## Step 1 — SEGMENT / 段落切分

对 `{persona-root}/SKILL.md` 与 `{persona-root}/components/*.md` **逐文件**切分成段落数组。

**切分规则**：

1. **按空行分段**：连续非空行组成一段 (标准 Markdown 段落边界)。
2. **Bullet 组**：连续的 `-` / `*` / `1.` bullet 若属同一父级，合并为**一段**（一组 bullet 表达一个主张）；遇标题或空行断开。
3. **标题行独立成段**：`#`/`##`/`###` 标题若后接空行，**跳过不评分**（标题承载结构而非内容）。
4. **表格整体为一段**：每张 markdown 表格视作一个段落；若表格行数 > 15，按 `|---|` 分隔符拆为两段。
5. **代码块**：视为 **一个段落**，但**默认打 SAFE** (0)——代码不是散文，不能用 anti-distill 锚点评价。Shell/config 示例例外：若代码块紧跟一段散文解释，**合并**到该散文段落里，不单独计段。

**段长建议**：40-300 字/词；过短 (< 20 字) 合并到相邻段，过长 (> 400 字) 按逻辑断开。

## Step 2 — CLASSIFY / 调用分类器

对每个切分出的段落调用 `distill-meta/references/extraction/density-classifier.md` 中定义的 classifier prompt，传入：

- `{target}` = 当前文件路径
- `{text_segments}` = Step 1 得到的段落数组
- `{schema}` = 从 manifest 读到的 schema (`public-mirror` / `executor` / ...)
- `{existing_components}` = 同一 persona-root 下已评分过的组件路径列表 (用于跨组件重复检测)

每段获得一个标签 ∈ `{REMOVE, MASK, SAFE, DILUTE}` + ≤30 字 rationale。

**标签权重** (反向使用 anti-distill)：

| Tag | Weight | 解读 |
|-----|--------|------|
| REMOVE | **+2** | 高价值：具体阈值、反直觉经验、persona 独有判断 |
| MASK   | **+1** | 中高价值：人际网络/职业路径/项目内部抉择 |
| SAFE   |  **0** | 通用领域常识；非独有但非废话 |
| DILUTE | **-1** | 正确废话：大词、同义反复、跨组件重复 |

**schema-aware 调整** (参考 density-classifier.md §Input Schema)：`executor` schema 的流程规范天然更接近 SAFE，允许阈值宽松 0.5；其他 schema 不调整。

## Step 3 — AGGREGATE / 归一化

对每个文件：

```
raw_score = 2·|REMOVE| + 1·|MASK| + 0·|SAFE| - 1·|DILUTE|
max_possible = total_segments · 2
min_possible = total_segments · (-1)
normalized   = round( (raw - min_possible) / (max_possible - min_possible) * 10 , 1 )
```

**跨文件汇总**：

```
density_score = round( Σ(normalized_i · segments_i) / Σ(segments_i) , 1 )
# 即按段落数加权平均各文件的 normalized；避免 20 段小文件与 120 段 SKILL.md 等权稀释。
```

最终 `density_score ∈ [0.0, 10.0]`，精度保留 1 位小数。

## Step 4 — EMIT / 写入与硬门槛

把 `density_score` 写入 `validation-report.md` 的两个位置：

1. **Frontmatter** 字段 `density_score: <0-10>` (契约要求，`distill-meta` 机读)；
2. **Body** 中 `## Dimension Scores` 表的 Density 行 (人读)。

**硬门槛** (rubric §Critical Failure Rules)：

```
if density_score < 3.0:
    verdict = "FAIL"
    critical_failures += 1
    Recommended Actions MUST 列出 Top-N 的 DILUTE 段落路径 + 修改建议
```

此规则覆盖 `overall_score_raw` 即使高达 95+。理由：**结构工整的正确废话比明显崩坏的 skill 更难被发现和清理**。

## Edge Cases / 边界情况

| 情形 | 处置 |
|------|------|
| **空文件** (`components/X.md` 0 字节) | Density 不计入；在 Weaknesses 标注 `empty-component:{path}` |
| **代码块独立成段** | 打 SAFE (0)；不参与正负权重 |
| **YAML frontmatter** (`---` 包围) | **排除**，不切不评；frontmatter 不是散文 |
| **manifest.json / config.yaml** | **排除**；结构化数据由 contract 校验，不走 density |
| **超短文件** (total_segments < 3) | 独立 normalized 不可靠；以总分 aggregate 贡献，但在 Weaknesses 提示 `under-segmented:{path}` |
| **单标签全打 REMOVE/DILUTE** | 分类器可能偏置；若某标签 > 80%，输出 warning 并建议人工复核 |
| **跨组件重复段落** | density-classifier 内置重复检测：相似度 > 0.9 自动降级为 DILUTE |
| **纯引用段** (> 60% 为外部引用) | 按引用**来源类型**判：primary 源 → MASK；secondary/web → SAFE；宣传语 → DILUTE |
| **非 ASCII 名词密集** | 不加分；REMOVE 必须凭具体阈值 / 反直觉断言，不凭术语堆砌 |

## Reproducibility / 可复现性

1. **同文本二次运行**：`density_score` 差异必须 ≤ 0.5；超过则在 Weaknesses 记 `density-instability` 并人工复审。
2. **种子化**：若 classifier LLM 支持 seed 参数，固定 seed；否则并发 3 次取中位数。
3. **证据段保留**：分类器的 `segment_scores[]` 明细**必须**写入 `versions/validation-report-{ISO}.md` 附录或单独的 `versions/density-detail-{ISO}.json`，供回归对比。

## Anti-patterns / 禁止事项

| 坏做法 | 为什么 | 正确做法 |
|--------|--------|---------|
| 把 YAML frontmatter 也切进去评分 | 结构字段会被误判 DILUTE | Step 1 切分时跳过 `---` 块 |
| 以"听起来有道理"标 REMOVE | REMOVE 必须有 anchor | 无数字/专名/反直觉断言一律降级 |
| density 低就放行不写 Recommended Actions | 用户无从修复 | 必须列 Top-N DILUTE 段路径 |
| 按字数而非段落加权 | 短但高价值的 bullet 被稀释 | 严格按段落数加权 |
| 跳过组件文件只评 SKILL.md | 单点作弊可能 | 所有 `components/*.md` 都要评 |
| density_score 用 raw_score 不归一化 | 段落数不同文件无法比较 | 必须用归一化公式 |

## Integration Points / 集成点

- **输入**：`distill-meta/references/extraction/density-classifier.md` — classifier prompt 与 output schema。
- **输出 frontmatter 字段**：`density_score` (`contracts/validation-report.schema.md` 定义)。
- **gating 条件**：`density_score < 3.0` → 强制 FAIL (rubric §Critical Failure Rules #1)。
- **配置**：`config.yaml` 的 `density_floor` (默认 3.0) 可覆写硬门槛；所有实际阈值必须写入 report `## Summary`。

---

**Traceability**: 算法来自 PRD §4.3 "密度评分（核心创新）" + anti-distill classifier。门槛 3.0 来自 `contracts/validation-report.schema.md` §Scoring Math。任何数值变更须先改契约再改本文件并 bump version。
