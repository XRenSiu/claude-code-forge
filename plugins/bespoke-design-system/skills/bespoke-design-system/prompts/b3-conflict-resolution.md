# B3 — 冲突解决与自洽化

> 当 SKILL.md 主流程进入 B3 时读取本文件作为执行指引。引用 `references/pattern-language.md` 加深理论理解。

## 你的任务

把 B2 的候选集（100–200 条）通过**确定性图算法**收敛为一个自洽规则子集（典型 40–60 条）。**不让模型判断冲突**——所有判断都基于 `grammar/graph/rules_graph.json` 的有向图结构。

---

## Step 1 — 加载关系图

读 `grammar/graph/rules_graph.json`。如果文件不存在或损坏 → 提示用户运行 `scripts/rebuild-graph.md`，停下。

把图加载为四张邻接表：

- `depends_on[rule_id] = [{rule, reason}, ...]`
- `constrains[rule_id] = [rule_id, ...]`
- `co_occurs_with[rule_id] = [{rule, frequency}, ...]`
- `conflicts_with[rule_id] = [{rule, reason}, ...]`

## Step 2 — 冲突消解

对候选集中的每个 `(A, B)` 对：

1. 若 `B ∈ conflicts_with[A]`：保留 `final_score` 高的，剔除另一个
2. 若 final_score 在 5% 以内的微差 → 保留 `confidence` 高的（B2 给的 final_score 包含 confidence 加权，通常已稳定）
3. 若 confidence 也相同 → 保留 `emerges_from` 数量多的（更普适）

**记录每次剔除**：在工作日志里写 `dropped: <rule>, reason: conflicts_with <kept_rule> (<conflict_reason>)`，B6 阶段会作为产物的 `provenance.yaml` 元数据。

## Step 3 — 依赖补全

对剔除冲突后剩下的每条规则 `R`：

1. 沿 `depends_on[R]` 反向闭包，把所有传递依赖加入候选
2. 如果某个依赖项**不在原候选集**且**不在规则库**（罕见，意味着关系图引用了不存在的规则）→ 记录损坏并提示用户重建关系图
3. 如果某个依赖项与已留的规则 `conflicts_with` → 这是关系图自身矛盾，保留依赖、剔除冲突方，并记录到日志

## Step 4 — 风格岛聚集（**v1.5.0 规模感知**）

构建子图 `G_kept`：节点 = 当前留下的规则，边 = `co_occurs_with` 关系（带频率权重）。

### v1.5.0 Issue 7 修复 — 按规则库尺寸分支

**先看规则库总规模**（grammar/rules/*.yaml 里所有 yaml 解析后的 rule 总数）：

| 规则库尺寸 | 处理方式 |
|---|---|
| **< 30 条**（极小） | **完全 skip 风格岛聚类**——co_occurs 数据量不够形成有意义 cluster。直接按 `final_score` 排序保留 top 50%（保 section 覆盖前提下） |
| **30 – 100 条**（小） | 用宽松阈值（μ - σ 而非 μ）；允许多个小 cluster 共存，不强求收敛到 1-2 个主岛 |
| **100 – 300 条**（中） | 标准算法（μ 阈值 + 主岛 1-2 个） |
| **> 300 条**（大） | 标准算法 + 增加 cluster 数量上限（5 个主岛） |

### 标准算法（中规模）

1. 计算每条边的频率均值 `μ` 和标准差 `σ`
2. 保留权重 ≥ `μ` 的边（高 co-occurrence 是"自洽风格岛"信号）
3. 用连通分量算法找出所有 cluster
4. 对每个 cluster，计算 `cluster_score = mean(rule.final_score for rule in cluster)`
5. 保留 cluster_score 最高的 1–2 个 cluster 作为"主风格岛"
6. 主岛之外的孤立点：若 final_score > 候选集 median → 保留作为"补充规则"；否则剔除

### 小规模 fallback

```python
if len(all_rules_in_library) < 30:
    # Skip clustering entirely; co_occurs signal is too sparse
    final_set = sorted(kept_set, key=lambda rid: -score_map[rid])
    final_set = section_aware_top_n(final_set, target_size=max(15, len(kept_set) // 2))
    cluster_metadata = {'skipped_reason': 'small_library', 'library_size': len(all_rules_in_library)}
elif len(all_rules_in_library) < 100:
    # Loose threshold: keep edges with freq >= μ - σ (instead of >= μ)
    threshold = max(0.0, mu - sigma)
    # ... rest as standard
```

**为什么这样做**：素材库里高频共现的规则形成了"自洽设计判断的样本"。让候选集围绕这些岛聚集，比让模型自由组合更接近"真有人这么设计过、被市场验证过"。**但**当素材库太小时（< 30 条），共现统计本身不够稳定，强行聚类会得到伪 cluster，反而丢质量——此时直接 score 排序更诚实。

## Step 5 — Section 覆盖最终核查

9 个 section 每个必须至少 1 条规则。缺的 section：

1. 先回到 B2 候选集找该 section 分数最高的，加入
2. 仍缺 → 从 `defaults.yaml` 取该 product_category 该 section 的 backstop 规则
3. 仍缺（极端情况）→ 标记该 section 为"degraded"，B4 时用通用安全默认（白底黑字、4/8/16 spacing 等），但 B5 闸门会扣分

## Step 6 — 输出自洽子集

```yaml
self_consistent_subset:
  rules:
    - rule_id: ...
      section: ...
      final_score: ...
      kept_reason: cluster_main | dependency | backstop | supplementary
  clusters:
    - id: main_cluster_1
      density: 0.78
      member_count: 32
      dominant_systems: [linear, vercel]
  dropped:
    - rule_id: ...
      reason: conflicts_with <id> | low_score_isolated | reverse_constraint
  section_coverage:
    color: 8
    typography: 6
    ...
  degraded_sections: []
```

把自洽子集传给 B4。

---

## 算法细节：连通分量

对 `G_kept`（仅保留高频边后的子图）跑标准 BFS/DFS，得到所有 connected components。每个 component 就是一个 cluster。Python 风格伪代码：

```
visited = set()
clusters = []
for node in nodes:
    if node not in visited:
        cluster = []
        queue = [node]
        while queue:
            n = queue.pop()
            if n in visited: continue
            visited.add(n)
            cluster.append(n)
            queue.extend(neighbors_in_G_kept(n))
        clusters.append(cluster)
```

---

## 检查清单（B3 产出前必过）

- [ ] 自洽子集规模 ≥ max(9, 5 * rule_bearing_section_count)（小规则库下放宽下限；大规则库下保持 ≤ 80 上限）
  - 小规则库（总规则 < 50）：下限 9（每 rule-bearing section 至少 1 条 + 4 个安全规则补底）
  - 中规则库（50-200）：下限 20，上限 60
  - 大规则库（>200）：下限 40，上限 80
- [ ] 5 个 rule-bearing section（color / typography / components / layout / depth_elevation）都有规则覆盖（除非显式标 degraded）
- [ ] 任意两条规则之间**没有** `conflicts_with` 关系
- [ ] 每条规则的 `depends_on` 闭包都已纳入子集
- [ ] 主风格岛已识别，dominant_systems 已记录
- [ ] `dropped` 列表完整、每条有 reason
- [ ] **没有向用户追问任何信息**
