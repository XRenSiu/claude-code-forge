# build-neighbor-corpus — 构建邻居语料库（A5 阶段）

> 程序化把 tokens 编码成定长 44 维特征向量（v1.14.0；137 套中排除 16 个 Tailwind-stub → 121 套真实系统），写入 `grammar/meta/neighbor-corpus.json`。供 B5 的 `neighbor_check.py` 使用。

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
2. 对每套调 `encode(tokens)`，把 tokens 映射成 44 维向量（37 base + 7 v1.13.0）：
   - 12 维 color（primary L/C/H + 灰阶范围 + 调色板属性）
   - 8 维 typography（scale ratio + 字号 + line-height + weight + serif/humanist）
   - 5 维 spacing/layout
   - 4 维 radius
   - 3 维 motion
   - 5 维 components
   - **7 维 v1.13.0 判别维**（palette_mean_L / L_contrast_range / chroma_spread / neutral_avg_chroma / has_mono / num_font_families / weight_spread；skill-issue-2026-06-18 #2 增）
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

## 距离阈值的诚实声明（v1.11.0 语义反转）

`neighbor_check.py` **从 v1.11.0 起是「独特性带」**：距离是要赚来的、有界的，不再是越小越 pass。分级 `<0.05 reject(clone)` / `0.05–0.12 needs_review(疑似派生)` / `0.12–0.45 pass(独特)` / `>0.45 needs_review(过远)`。

阈值**从 corpus 自身距离分布校准**（不是经验拍脑袋）。重建 corpus 后应复核分布是否漂移：

- corpus 内部最近邻距离应大致维持 中位 ~0.12 / p90 ~0.20 / 最大 ~0.26；`suspect`(0.12) 取的就是这个中位数。若分布大幅变化，按比例调 `SUSPECT_THRESHOLD` / `DISTINCT_CEILING`。
- **编码器分辨率 + stub 排除（v1.13.0/v1.14.0）**：37→44 维（加 has_mono / num_font_families / 更细色彩维）破开了大部分坍缩；v1.14.0 进一步把 16 个共用 Tailwind 默认 7 色、无规则文件的"形容词 stub"系统排除出语料库（`_is_stub()` 按调色板检测，`--keep-stubs` 可保留）。结果:**exact-0 重复邻居 = 0**(原 6),corpus 137→121。NN 中位仍 ~0.126,改动1 阈值不变。`clone` 阈值仍不宜上调太多(编码器对真实相近系统仍有分辨率上限)。详见 `bespoke-design/skill-issue-2026-06-18.md` #2/#3。

如果用户反映"生成的设计很普通"，**不要**指望调这个 check——它只能抓 token clone。感知层面的平庸是 taste critic 的职责。

## 与 spec §3.4 A5 的对应

spec 列出的特征向量维度示例（30-50 维）：

| 类别 | spec 提示 | 实际实现 |
|---|---|---|
| 色彩 | 12 维 | 12 维 ✓ |
| 字体 | 8 维 | 8 维 ✓ |
| 间距 | 6 维 | 5 维（合并 layout） |
| 节奏 | 4 维 | 4 维 radius ✓ |
| 其它 | — | 3 维 motion + 5 维 components |
| 判别维（v1.13.0） | — | 7 维（color 细化 4 + font 信号 3） |

总 44 维（37 base + 7 v1.13.0），落在 spec 30-50 区间内。
