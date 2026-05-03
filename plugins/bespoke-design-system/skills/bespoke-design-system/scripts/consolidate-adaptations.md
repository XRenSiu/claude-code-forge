# consolidate-adaptations — 沉淀高频 adaptation 为新规则

> 自演化机制的具体执行子流程。把 B 阶段反复出现的 adaptation 提议为派生规则，让规则库随真实使用场景有机生长。

## 输入

`grammar/meta/adaptation-stats.json`（由 B6 持续更新）

## 输出

- 提议文档（用户审核用）
- 用户确认后，新规则写入 `grammar/rules/_generated.yaml`
- 关系图增量更新

---

## Step 1 — 扫描达阈值的 adaptation

读 `grammar/meta/adaptation-stats.json`。默认阈值 `occurrences ≥ 5`（用户可在调用时覆盖：`沉淀 adaptation threshold=10`）。

筛选出所有达阈值的条目。

## Step 2 — 分析每条 adaptation

对每条达阈值的 adaptation：

1. 查 `source_rule_id` → 找到原规则
2. 提取 adaptation 的"模式"：
   - 哪个 dimension 被改？
   - from / to 的方向是否一致？（10 次中是否都是 saturation 降低？还是混乱方向？）
   - 触发 adaptation 的 user_kansei 集合是什么？是否有共同子集？
3. 计算"模式一致度"：
   - dimension 一致：≥ 80% 的 contexts 改的是同一个 dimension
   - 方向一致：≥ 80% 的 contexts 改的方向相同（都是降 / 都是升）
   - 触发 kansei 一致：≥ 80% 的 contexts 包含某个共同 kansei 词

**只**对"模式一致度高"的 adaptation 提议沉淀。混乱的 adaptation 是噪音，不沉淀。

## Step 3 — 生成提议文档

对每条值得沉淀的 adaptation，生成一份提议条目：

```yaml
proposal:
  adaptation_id: linear-color-balance-001:saturation_decrease_for_mystical
  occurrences: 7
  pattern_consistency:
    dimension_consistency: 1.0
    direction_consistency: 1.0
    trigger_kansei_consistency: 0.86

  proposed_new_rule:
    rule_id: generated-color-mystical-saturation-001
    preconditions:
      product_type: [spiritual_saas, content_platform, lifestyle_app]
      tone: [professional, mystical]
      kansei: [mystical, ancient, calm]
    action:
      saturation_modifier: -0.15  # 在 base rule 的 saturation 上减 0.15
    base_rule: linear-color-balance-001
    why:
      establish: ancient_mystical_atmosphere
      avoid: [tech_brand_feeling]
      balance: structure ↔ mystery
    emerges_from:
      - "[generated:mystical_saas_contexts]"
      - linear  # base rule 的 emerges_from 之一
    provenance: generated
    confidence: 0.6   # 派生规则起步置信度低于原生

  expected_uses:
    - 当用户产品同时含 [mystical, ancient] kansei 时
    - 减少需要在 B4 反复手动调适
```

## Step 4 — 给用户审核

输出所有提议给用户：

```
🌱 沉淀提议（N 条）

下列 adaptation 已达沉淀阈值（occurrences ≥ 5）且模式一致度高，建议沉淀为新规则：

1. linear-color-balance-001:saturation_decrease_for_mystical (7 次)
   → 提议规则：generated-color-mystical-saturation-001
   → 影响：未来 [mystical, ancient] 类产品的 B4 阶段可直接用，无需重复调适
   接受？(y/n/modify)

2. ...
```

逐条让用户决定：

- `y` → 沉淀
- `n` → 跳过（不沉淀，但保留 adaptation-stats 中的统计）
- `modify` → 用户调整提议规则的某些字段（比如把 confidence 改 0.7）

## Step 5 — 写入 _generated.yaml

接受沉淀的规则追加到 `grammar/rules/_generated.yaml`：

```yaml
rules:
  - rule_id: generated-color-mystical-saturation-001
    preconditions: {...}
    action: {...}
    why: {...}
    emerges_from: [...]
    provenance: generated
    confidence: 0.6
    base_rule: linear-color-balance-001
    sedimented_from_adaptation_id: linear-color-balance-001:saturation_decrease_for_mystical
    sedimented_at: <ISO 8601>
    sedimented_after_occurrences: 7
  ...
```

`sedimented_*` 元数据让派生规则可独立追溯/回滚——如果未来发现质量问题，可以按 `sedimented_at` 时间窗或 `base_rule` 反向定位。

## Step 6 — 关系图更新

新派生规则需要加入关系图。**不**全量重建（成本高），而是：

1. depends_on：新规则自动 `depends_on: [base_rule]`，因为 action 是 base_rule 的修饰
2. co_occurs_with：跟 base_rule 的所有 co_occurs_with 自动继承一份（频率 = base 的 0.8 倍，作为初始估计）
3. conflicts_with：跟 base_rule 的 conflicts_with 自动继承
4. constrains：base_rule 反向加 `constrains: [generated_rule]`

**重要**：用户每接受 ≥ 5 条沉淀 → 建议跑一次 `scripts/rebuild-graph.md` 让派生规则的关系收敛。

## Step 7 — 更新元数据

- `grammar/meta/version.json`：rules_version minor +0.1.0（新增规则）
- `grammar/meta/adaptation-stats.json`：被沉淀的 adaptation 标 `sedimented: true`，不再累计 occurrences（避免重复沉淀）

## Step 8 — 报告

```
✅ Sedimentation complete
   Proposals reviewed: NN
   Accepted: NN
   Skipped: NN
   Modified before accepting: NN

   New rules added to _generated.yaml: NN
   Graph relations created: NN

   Rules library version: x.y.z → x.y+1.0

   💡 Recommend running "重建关系图" if NN+ rules were added.
```

---

## 沉淀规则的质量保护

派生规则比原生规则危险——它们没有经过设计师的真实验证，只是统计模式。所以：

- **confidence 起步 0.6**，远低于原生规则的 0.85+
- **provenance: generated** 让 B4 阶段在用到派生规则时优先级低于原生
- **若派生规则在后续 P0 闸门反复被驳回**（rationale-judge 标 blocker 多次涉及该规则），应自动降级或撤销——这是 v1.x 的扩展功能

每次沉淀都让用户审核，**不**自动沉淀。这是有意的"人在环上"机制。
