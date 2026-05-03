# rebuild-graph — 重建规则关系图

> 用于已有规则库的全量重算。每加入一批新素材后建议跑一次，让 `co_occurs_with` 频率收敛到真实分布。

## 输入

`grammar/rules/*.yaml`（含 `_generated.yaml`）

## 输出

`grammar/graph/rules_graph.json` 全量重写

---

## Step 1 — 加载所有规则

读取 `grammar/rules/` 下所有 .yaml，构建规则字典 `rules: {rule_id → rule_object}`。

读取 `grammar/meta/source-registry.json` 获取每个 system 的 rule_ids 列表。

## Step 2 — 重算 depends_on / constrains

对每条规则：

1. 按 §extract-grammar.md A4 的"depends_on"逻辑重新扫描，但**不依赖之前的 graph 数据**——从 0 算
2. 标准依赖关系（color → 其它、typography → spacing、components → 全部）按规则的 `section` 字段自动连边
3. 自定义依赖（规则的 action 显式引用其它规则）按 action 文本扫描

constrains = depends_on 的反向边。

## Step 3 — 重算 co_occurs_with（带频率）

对每对规则 `(A, B)`：

```
systems_with_A = set(s for s in source_systems if A in rules_of(s))
systems_with_B = set(s for s in source_systems if B in rules_of(s))
both = systems_with_A & systems_with_B
either = systems_with_A | systems_with_B

if |either| > 0:
    frequency = |both| / |either|
else:
    frequency = 0
```

阈值：`frequency >= 0.3` 才记入图（避免噪音）。

**优化**：实际上"语义相似"的规则才有共现意义。判断"语义相似"的方式：

- 同 section
- preconditions.kansei 重叠 ≥ 2 个词
- action 描述的是同一类决策（都是 primary color、都是 type scale 等）

不满足"语义相似"的对即使共现也不算 co_occurs（避免无意义的 button 规则与 color 规则的共现噪音）。

## Step 4 — 重算 conflicts_with

对每对规则 `(A, B)`：

1. 检查 `A.why.avoid ∩ B.why.establish` 是否非空
2. 检查 `A.action` 和 `B.action` 是否在同一 dimension 上方向相反，且 `A.preconditions.product_type ∩ B.preconditions.product_type` 非空
3. 检查 `A.preconditions.kansei` 是否含 `B.preconditions.kansei` 的反义词（参考 `references/kansei-theory.md` 的反义对）

任一条件成立 → 加 `conflicts_with: {rule: B, reason: ...}`。

**对称性**：conflicts_with 是双向的，A 列出 B 时 B 也要列出 A。

## Step 5 — 写回

把全部图结构写回 `grammar/graph/rules_graph.json`，覆盖原文件。文件结构：

```json
{
  "version": "<rules_version>",
  "rebuilt_at": "<ISO 8601>",
  "node_count": NN,
  "edge_counts": {
    "depends_on": NN,
    "constrains": NN,
    "co_occurs_with": NN,
    "conflicts_with": NN
  },
  "nodes": [
    {
      "rule_id": "linear-color-balance-001",
      "relations": {
        "depends_on": [...],
        "constrains": [...],
        "co_occurs_with": [...],
        "conflicts_with": [...]
      }
    },
    ...
  ]
}
```

## Step 6 — 完整性检查

- [ ] 所有 depends_on 项的 rule 都存在于 rules 字典中（否则报告损坏的引用）
- [ ] depends_on 与 constrains 双向对称
- [ ] conflicts_with 双向对称
- [ ] 所有规则都有 `relations` 字段（即使是空对象 `{}`）
- [ ] 无自环（A 不能 depends_on / conflicts_with A 自己）

## Step 7 — 报告

```
✅ Graph rebuilt
   Nodes: NN
   Edges: depends_on: NN, constrains: NN, co_occurs: NN, conflicts: NN
   Avg degree: NN
   Largest co-occur cluster: NN nodes (dominant systems: ...)
   Conflict pairs: NN
   Broken refs: NN  ← if > 0, list them
```

如果 broken refs > 0，告诉用户哪些规则引用了不存在的目标，建议删除或修正。
