# add-new-design-system — 加入单套 DESIGN.md

> 用户已有一份 DESIGN.md（自有的、或从某处下载的），希望加入素材库。

## 输入

来自用户：

- DESIGN.md 的内容或路径
- 该设计系统的名字（例如 "stripe-2026"）
- 来源说明（用户自有 / 来自某仓库 / 来自某商业产品的公开文档）
- 许可信息（如果是开源 / fair-use / 用户原创）

## 输出

- `source-design-systems/<system_name>/DESIGN.md` 副本
- `grammar/tokens/<system_name>.json`
- `grammar/rationale/<system_name>.md`
- `grammar/rules/<system_name>.yaml`
- 更新 `grammar/graph/rules_graph.json`（增量）
- 更新 `grammar/meta/source-registry.json`

---

## Step 1 — 收集元数据

询问用户（这一步**允许问问题**——是维护流程，不是生成流程，铁律不适用）：

1. 系统名（slug）：用户会用什么名字引用它？默认从 DESIGN.md 标题推断
2. 来源类型：
   - `user_original`（用户/团队原创）
   - `open_source`（开源仓库，需要 URL + license）
   - `public_company_doc`（公开发布的公司设计系统文档，注明 URL）
   - `fair_use_reference`（fair-use 引用作为参考，注明出处）
3. 许可信息（按来源类型决定是否需要）

## Step 2 — 去重检查

读 `grammar/meta/source-registry.json`，检查：

- 是否已有同名 system
- 是否已有"语义指纹"接近的 system（如同时收录了 Linear 的两个版本）

如果重复：

- 完全相同 → 提示用户，问要不要覆盖
- 不同版本 → 建议用 `<system>-<date>` 或 `<system>-v<n>` 区分

## Step 3 — 落盘原始 DESIGN.md

`mkdir source-design-systems/<system_name>/`，写入 DESIGN.md。

如果 DESIGN.md **不符合 9-section 标准**：

- 简单缺失（如缺 `Anti-patterns` section）→ 警告但继续
- 严重不符（混入大量其它内容、section 名混乱）→ 停下，要求用户先按标准整理。引用 `references/design-md-spec.md`。

## Step 4 — 跑 extract-grammar 4 步

按 `scripts/extract-grammar.md` 的 A1-A4 全跑一遍。

## Step 5 — 更新 source-registry

```json
{
  "systems": {
    "<system_name>": {
      "added_at": "<ISO 8601>",
      "source_type": "user_original | open_source | public_company_doc | fair_use_reference",
      "source_url": "...",
      "license": "...",
      "last_extracted_at": "...",
      "rule_count": NN,
      "fingerprint_hash": "<sha256(DESIGN.md)>"
    }
  }
}
```

## Step 6 — 增量更新关系图

A4 已经做了与已有规则的初步关系扫描。但**强烈建议**完成后跑一次 `scripts/rebuild-graph.md`，让 co_occurs_with 频率重新收敛到包含新素材的真实分布。

提示用户：

```
新素材已加入。建议运行"重建关系图"让 co_occurs_with 频率重新收敛到包含新素材的真实分布。
要现在跑吗？(y/n)
```

如果用户同意 → 调用 `rebuild-graph.md`。

## Step 7 — 报告

```
✅ Added <system_name>
   source: <type> (<url or "user provided">)
   license: <license>
   tokens: NN fields
   rationale: NN decisions
   rules: NN rules added to grammar
   graph: incremental update applied (recommend full rebuild)
```
