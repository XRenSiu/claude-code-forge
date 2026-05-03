# rebuild-graph — 重建规则关系图

> 程序化全量重算 `grammar/graph/rules_graph.json`。每批新规则加入后建议跑一次。

## 触发

用户说："重建关系图" / "rebuild graph" / "刚加了几套，重新跑一下图"。

也由 `import-from-collection.md` 在批量导入完成后自动建议。

## 用法

```bash
python3 tools/rebuild_graph.py
```

或 dry-run 看影响（不写文件）：

```bash
python3 tools/rebuild_graph.py --dry-run
```

## 工具自动做的步骤

1. 加载 `grammar/rules/*.yaml`（含 `_generated.yaml`）
2. **depends_on / constrains**：按 section 依赖图（components 依赖 color/typography/spacing/layout/depth_elevation；motion 依赖 components；typography/depth_elevation 依赖 color；layout 依赖 spacing），同源 system 内自动连边
3. **co_occurs_with**：对每对（同 section + Kansei 重叠 ≥ 0.2 的）规则，计算 `emerges_from` 集合的 Jaccard 频率，≥ 0.3 阈值的连边
4. **conflicts_with**：
   - **吸入** rule yaml 里显式声明的 `known_conflicts`（A3 阶段 LLM 标的）
   - **自动检测** Kansei 反义词对（modern↔classical, minimal↔ornate, ...）
   - **自动检测** A.why.avoid 包含 B.why.establish 的语义引用
5. 双向边对称性自动维护
6. 写 `grammar/graph/rules_graph.json`，含 `version` / `rebuilt_at` / `node_count` / `edge_counts`

## 何时该跑

| 场景 | 频率 |
|---|---|
| 新加了 ≥ 3 套规则 | 必跑 |
| 修改了已有规则的 known_conflicts / kansei | 必跑 |
| consolidate-adaptations 后产生派生规则 | 必跑 |
| 单条规则微调 confidence | 不需要（图结构不变） |

## 完整性检查

工具完成后自动报告：

```
Wrote .../grammar/graph/rules_graph.json
{
  "rules_loaded": NN,
  "edge_counts": {
    "depends_on": NN,
    "constrains": NN,
    "co_occurs_with": NN,
    "conflicts_with": NN
  },
  "avg_degree": N.N,
  "sections_seen": [...],
  "systems_seen": [...]
}
```

可以再跑健康检查：

```bash
python3 -c "
import json
g = json.load(open('grammar/graph/rules_graph.json'))
ids = {n['rule_id'] for n in g['nodes']}
broken = []
for n in g['nodes']:
    for k in ['depends_on','constrains','co_occurs_with','conflicts_with']:
        for e in n['relations'][k]:
            if e['rule'] not in ids:
                broken.append((n['rule_id'], k, e['rule']))
print(f'Broken refs: {len(broken)}')
print(f'Asymmetric (manual check needed): see node count vs edge count divisibility')
"
```

## 失败处理

- **PyYAML 缺失**：`pip install pyyaml`
- **rules/ 目录为空**：图会是空的（合法状态）。提示用户先做 A3 写规则。
- **rule yaml 损坏**：工具会 `WARN: skipping <fname>` 并继续。修复 yaml 后重跑。
