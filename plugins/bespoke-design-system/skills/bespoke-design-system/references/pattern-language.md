# A Pattern Language — 规则关系图建模

> Christopher Alexander 的 *A Pattern Language* (1977) 提出：模式不是孤立存在的，模式之间有依赖、冲突、共现关系。理解一组模式必须理解它们之间的语言。

本 skill 在 A4 阶段构建关系图、在 B3 阶段用图算法解决冲突，理论根基都在这本书。

---

## 四类关系

### 1. depends_on（依赖）

> "B 必须先存在，A 才有意义。"

例：

- "button primary color" depends_on "color palette primary"
- "type scale heading_3" depends_on "type scale baseline"
- "card elevation level 2" depends_on "elevation system tokens"

depends_on 闭包是 B3 阶段必须保留的——选了 A 必须把 A 的所有依赖都纳入。

### 2. constrains（约束）

> depends_on 的反向边。"A 约束了 B 的选择空间。"

例：

- "color palette primary" constrains "button primary color"（按钮颜色受调色板限制）

constrains 在 B3 用于找"选了 A 之后哪些 B 必须重新选"。

### 3. co_occurs_with（共现，带频率）

> "在素材库中，A 和 B 经常一起出现。"

例：

- "8px base spacing" co_occurs_with "4px micro spacing"（频率 0.85 — 大多数 8px base 系统也用 4px micro）
- "Inter font family" co_occurs_with "low contrast neutral grays"（频率 0.62）

co_occurs_with 是**风格岛**的判据。高频共现的规则形成自洽的子图，B3 优先保留主岛。

**关键**：co_occurs_with 是基于真实素材的统计，**不是**模型的"觉得它们应该一起用"。这让 B3 的判断有客观锚点。

### 4. conflicts_with（冲突）

> "A 和 B 不能同时存在，会破坏整体一致性。"

例：

- "minimal serif display" conflicts_with "high-saturation playful color palette"（一个克制一个张扬）
- "developer-tool-cold-shore aesthetic" conflicts_with "warm welcoming caregiving palette"

conflicts_with 是双向的。B3 的"冲突消解"扫描候选集中的 conflicts_with 对，留 score 高的。

---

## 关系的几何

把 4 类关系合在一起，规则形成一个**有向带标有向图**（multi-edge directed graph with edge labels）：

- 节点：rule
- 边：4 种类型，每条带元数据（reason / frequency）

这个图在 B3 上发挥作用的方式：

```
1. 候选集是图的一个节点子集
2. 对每条 conflicts_with 边，留 score 高的端点
3. 沿 depends_on 反向闭包扩展
4. 在 co_occurs_with 子图上跑连通分量算法 → 找风格岛
5. 主岛保留，孤立点按 score 决定
```

每一步都是确定性算法，不让模型主观判断。

---

## 为什么要建图（而不是让模型 in-context 处理）

把 100-200 条规则全塞给模型让它"自己解决冲突"是可以的，但：

1. **不可调试**：模型为什么留了 A 而不留 B？无法解释
2. **不一致**：同样的输入跑两次可能得到不同子集
3. **难审计**：B5 闸门要验证 B3 的 dropping 决策时，没有客观依据

显式图 + 算法解决了这三个问题：

- dropping 决策可记录（`dropped: <rule>, reason: conflicts_with <kept_rule>`）
- 同输入同输出（确定性）
- 闸门可以重新跑算法验证

---

## Alexander 的更深主张

Alexander 在 *A Pattern Language* 之后的 *The Nature of Order* (2003-2004) 中提出："好的设计不是规则的集合，而是规则之间的关系所形成的整体性（wholeness）。"

本 skill 的"风格岛聚集"对应这个主张——主岛代表了素材库中**真有人用过、被市场验证过**的整体性，比孤立规则的随机组合更接近"自洽设计判断"。

---

## 实操注意

1. **关系图不是一次到位**：素材增量加入时（`add-new-design-system.md`），关系图增量更新。每次加入 ≥ 5 套素材或修改了 conflict 判断逻辑后，建议跑 `scripts/rebuild-graph.md` 全量重算。
2. **co_occurs_with 频率需要 ≥ 3 套素材才有意义**：少于 3 套时频率波动太大。新规则刚加入时频率可能误导，重建关系图后会收敛。
3. **conflicts_with 容易遗漏**：拆解新素材时，A4 步骤的 conflicts 检测主要靠 `why.avoid ↔ why.establish` 的语义对比，可能漏掉隐性冲突（如某两条规则的 action 在某些边界条件下冲突）。这是已知局限，未来版本可加更深的语义分析。

---

## 参考

- Alexander, C. (1977). *A Pattern Language: Towns, Buildings, Construction*
- Alexander, C. (2003-2004). *The Nature of Order* (4 vols)
- Alexander, C. (1979). *The Timeless Way of Building*（理论根基）
