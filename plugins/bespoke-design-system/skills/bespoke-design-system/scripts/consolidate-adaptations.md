# consolidate-adaptations — 沉淀高频 adaptation 为新规则

> 自演化机制的具体执行子流程。把 B 阶段反复出现的 adaptation 提议为派生规则。

## 输入

`grammar/meta/adaptation-stats.json`（由 B6 持续更新）

## 输出

- 提议文档（用户审核用）
- 用户确认后，新规则写入 `grammar/rules/_generated.yaml`
- 关系图增量更新

---

## Step 1 — 扫描达阈值的 adaptation（程序化）

```bash
# 用 jq 或 Python 简单扫
python3 -c "
import json
stats = json.load(open('grammar/meta/adaptation-stats.json'))
threshold = stats.get('sedimentation_threshold', 5)
candidates = [(aid, info) for aid, info in stats.get('adaptations', {}).items()
              if info['occurrences'] >= threshold and not info.get('sedimented')]
print(f'{len(candidates)} candidate adaptations above threshold {threshold}:')
for aid, info in candidates:
    print(f'  {aid} ({info[\"occurrences\"]}x)')
"
```

阈值默认 5，可在 `grammar/meta/adaptation-stats.json` 的 `sedimentation_threshold` 字段调。

## Step 2 — 模式一致度分析（LLM 半自动）

对每条候选 adaptation：

1. 程序读 `info.contexts` 数组，计算：
   - dimension 一致度：≥ 80% contexts 改的是同一 dimension？
   - 方向一致度：≥ 80% contexts 都是降 / 都是升？
   - 触发 kansei 一致度：≥ 80% contexts 含某共同 kansei 词？
2. 一致度 < 80% → 标 `noisy`，跳过（不沉淀）
3. 一致度 ≥ 80% → 进入 Step 3

## Step 3 — LLM 起草新规则提议

按 `references/design-md-spec.md` 的 rule schema，起草派生规则：

```yaml
proposal:
  adaptation_id: <id>
  occurrences: <N>
  pattern_consistency: <%>

  proposed_new_rule:
    rule_id: generated-<section>-<short-name>-<seq>
    preconditions:
      product_type: <list inferred from contexts>
      tone: <inferred>
      kansei: <common kansei words from contexts>
    action:
      <dimension>_modifier: <delta>      # 派生规则通常只在 base rule 的某 dimension 上加修饰
    base_rule: <source_rule_id>
    why:
      establish: <一句话>
      avoid: <list>
    emerges_from:
      - "[generated:<context_type>]"
      - <base rule's emerges_from[0]>
    provenance: generated
    confidence: 0.6
    sedimented_from_adaptation_id: <id>
```

## Step 4 — 用户审核

把所有提议给用户：

```
🌱 沉淀提议（N 条）

以下 adaptation 已达沉淀阈值（occurrences ≥ 5）且模式一致度高：

1. <adaptation_id> (N 次)
   → 提议规则: generated-<...>-001
   → 影响: 未来 [kansei] 类产品的 B4 阶段可直接用，无需重复调适

   接受？(y/n/modify)

2. ...
```

## Step 5 — 写入 _generated.yaml + 元数据

接受的规则追加到 `grammar/rules/_generated.yaml`，加 `sedimented_*` 元数据。

## Step 6 — 关系图重建（程序化）

```bash
python3 tools/rebuild_graph.py
```

派生规则自动获得 depends_on（指向 base_rule）+ 继承 base_rule 的 co_occurs_with / conflicts_with。

## Step 7 — 标记 stats + bump 版本

```bash
# 标 sedimented (Python)
python3 -c "
import json
stats = json.load(open('grammar/meta/adaptation-stats.json'))
for aid in [<accepted_ids>]:
    stats['adaptations'][aid]['sedimented'] = True
    stats['adaptations'][aid]['sedimented_into_rule_id'] = '<new_rule_id>'
json.dump(stats, open('grammar/meta/adaptation-stats.json','w'), indent=2)
"

# bump rules_version (manual)
```

## 派生规则的质量保护

- **confidence 起步 0.6**（远低于原生规则的 0.85+）
- **provenance: generated** 让 B4 阶段优先级低于原生
- **若反复被 P0 闸门驳回** → 自动降级或撤销（v1.x 扩展）
- **每次沉淀都让用户审核**——不自动沉淀，"人在环上"机制
