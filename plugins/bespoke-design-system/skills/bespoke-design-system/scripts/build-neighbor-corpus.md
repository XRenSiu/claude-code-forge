# build-neighbor-corpus — 构建邻居语料库（A5 阶段）

> 程序化把 137 套 tokens 编码成定长 37 维特征向量，写入 `grammar/meta/neighbor-corpus.json`。供 B5 的 `neighbor_check.py` 使用。

## 用法

```bash
python3 tools/build_neighbor_corpus.py
```

或限定子集：

```bash
python3 tools/build_neighbor_corpus.py --include-only linear-app,vercel,apple
```

## 输出

`grammar/meta/neighbor-corpus.json`：

```json
{
  "schema_version": "1.0",
  "built_at": "<ISO 8601>",
  "dim_count": 37,
  "dim_names": [...],
  "weights": [...],
  "systems": {
    "<name>": {
      "vector": [37 floats],
      "dialect": "A|B|C|...",
      "extracted_at": "..."
    }
  }
}
```

## 何时该跑

| 触发场景 | 频率 |
|---|---|
| 新增 ≥ 1 套素材（A1 完成后） | 必跑 |
| 修改了 `tools/build_neighbor_corpus.py` 的 encode() 逻辑 | 必跑 |
| 修改了 dim_names / weights | 必跑 + bump schema_version |
| 仅修改 rules.yaml（不影响 tokens） | 不需要 |

## 工具自动做的

1. 加载 `grammar/tokens/*.json`
2. 对每套调 `encode(tokens)`，把 tokens 映射成 37 维向量：
   - 12 维 color（primary L/C/H + 灰阶范围 + 调色板属性）
   - 8 维 typography（scale ratio + 字号 + line-height + weight + serif/humanist）
   - 5 维 spacing/layout
   - 4 维 radius
   - 3 维 motion
   - 5 维 components
3. 写入 `neighbor-corpus.json`（覆盖式）

## 失败处理

- **PyYAML 缺失**：本工具不需要 yaml，只需要 json + math
- **某套 tokens.json 损坏**：跳过该套，继续处理其它套，报告 skipped 数量
- **dim 数变化**：旧的 corpus 与新 encode 不兼容；必须重跑全部 + bump `schema_version`

## 校验

跑完后可以快速 sanity check：

```bash
python3 -c "
import json
c = json.load(open('grammar/meta/neighbor-corpus.json'))
print(f'systems: {len(c[\"systems\"])}, dims: {c[\"dim_count\"]}')
# Verify all vectors have correct length
for name, info in c['systems'].items():
    assert len(info['vector']) == c['dim_count'], f'{name}: dim mismatch'
print('all vectors length-OK')
"
```

## 距离阈值的诚实声明

`neighbor_check.py` 用阈值 0.3 / 0.6 来分级 pass / needs_review / reject。**这两个值是经验值**，依赖 corpus 规模和 dialect 多样性：

- corpus 越大、风格越多，0.3 阈值越合理
- corpus 偏向某种风格（例如 80% 都是 dev SaaS），生成"非主流但好"的 brief 会被 reject — 这是 corpus 偏差，不是 bug

如果用户反映 reject 过多，建议先扩 corpus（添加更多 dialect / archetype 样本）而非调阈值。

## 与 spec §3.4 A5 的对应

spec 列出的特征向量维度示例（30-50 维）：

| 类别 | spec 提示 | 实际实现 |
|---|---|---|
| 色彩 | 12 维 | 12 维 ✓ |
| 字体 | 8 维 | 8 维 ✓ |
| 间距 | 6 维 | 5 维（合并 layout） |
| 节奏 | 4 维 | 4 维 radius ✓ |
| 其它 | — | 3 维 motion + 5 维 components |

总 37 维，落在 spec 30-50 区间内。
