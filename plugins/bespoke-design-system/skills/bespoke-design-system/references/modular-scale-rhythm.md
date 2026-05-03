# Modular Scale & Vertical Rhythm — coherence_check 的字号/间距判据

> 本文档是 `checks/coherence_check.py` 的 modular_scale / vertical_rhythm / grid_consistency 子检查的理论依据。

## 1. Modular Scale（Bringhurst）

### 概念

Robert Bringhurst 在 *The Elements of Typographic Style* 中提出：好的字号 scale 应基于一个**音乐音程比率**（musical interval ratio），让所有字号呈几何递增。

### 公认比率

| 比率 | 名称 | 来源 / 适用场景 |
|---|---|---|
| 1.067 | minor second | 紧凑、密集排版 |
| 1.125 | major second | 平衡，适合 dashboard |
| 1.200 | minor third | 标准 SaaS（流行） |
| 1.250 | major third | Linear / Notion 等用过 |
| 1.333 | perfect fourth | 经典印刷 |
| 1.414 | augmented fourth | 中等 dramatic |
| 1.500 | perfect fifth | dramatic 显示 |
| 1.618 | golden ratio | 黄金比例 |
| 1.667 / 1.778 / 1.875 | minor/major sixth/seventh | 极致 dramatic |
| 2.000 | octave | 极端字号差 |

### 检查算法（`infer_scale_ratio()`）

输入：字号数组 `[12, 14, 16, 18, 24, 32, 48]`

步骤：

1. 计算相邻两数的比值数组 `[14/12, 16/14, 18/16, 24/18, 32/24, 48/32]`
   = `[1.167, 1.143, 1.125, 1.333, 1.333, 1.5]`
2. 取中位数作为 inferred ratio = `1.25` (left-middle of sorted)
3. 检查所有比值是否在 inferred ratio 的 ±10% 内
4. 检查 inferred ratio 是否接近某个公认比率（±3%）

### 子检查 4 的判定

| 情况 | 判定 |
|---|---|
| 比值内部一致（<10%）+ 接近公认比率 | pass |
| 比值内部一致（<10%）但不在公认比率上 | pass（可能是自定义） |
| 比值不一致（>10%） | warning |

完全无规律的 scale 不会进入生产 token，不需 reject——A1 程序化提取已能识别。

### 实践注意

很多设计系统的 scale **不严格遵循 modular**，例如 OD 多数 dialect B 用 `[14, 16, 18, 24, 32, 40]` 这种偏向 major third 但有变种。`coherence_check` 的策略是：

- 比值内部一致是必要条件
- 接近公认比率是加分项
- 都不满足才 warning

## 2. Vertical Rhythm

### 概念

排版的"基线网格"——所有 line-box 高度应该是基础单位（base unit，通常 4px 或 8px）的整数倍。这让多列内容在垂直方向上"对齐"，是高质量印刷传统的延续。

### 公式

```
line_box = body_size * line_height
要求：line_box % base == 0  (或 % (base/2) == 0，允许半步)
```

### 例子

- base = 4, body = 16, line_height = 1.5 → line_box = 24 → 24 % 4 == 0 ✓
- base = 4, body = 16, line_height = 1.6 → line_box = 25.6 → 25.6 % 4 = 1.6 ✗
- base = 8, body = 16, line_height = 1.5 → line_box = 24 → 24 % 8 == 0 ✓

### 子检查 5 的判定

`vertical_rhythm_check()` 默认 `passed=True`，因为大多数好系统都满足，不通过的极少。但报告里仍输出 `line_box` 和 `remainder` 供 LLM 在 B4 时验证。

## 3. Grid Consistency

### 子检查 6 的判定

**Spacing scale**：所有 spacing 值是 base 的整数倍（或 base/2 的整数倍）。

例如 base = 8 的合法 scale：`[4, 8, 12, 16, 24, 32]`（4 = base/2，其它都是 base 倍数）。

**Radius scale**：

- 所有 radius 是 base 的整数倍（同上）
- radius scale 内部各级有合理比例（每步 1.3x ~ 2.5x）

例如 `[2, 4, 8, 16]` 通过（每步 ~2x），`[2, 6, 7, 50]` 不通过（步比异常）。

### 实践注意

很多系统含有"特殊值"如 pill radius 9999、optical 修正 7/11/19。check 把 ≥1000 的视为 pill 不参与 grid 检查；< base 的视为 letter-spacing 不参与 spacing 检查。

## 4. 实现位置

- `_shared/scale_math.py::infer_scale_ratio()` / `KNOWN_RATIOS`
- `_shared/scale_math.py::grid_alignment_check()`
- `_shared/scale_math.py::vertical_rhythm_check()`
- `_shared/scale_math.py::radius_proportion_check()`
- `coherence_check.py::subcheck_modular_scale()` / `subcheck_vertical_rhythm()` / `subcheck_grid_consistency()`

## 5. 参考

- Bringhurst, *The Elements of Typographic Style* (1992, 4th ed. 2012) — 字号比率经典
- modularscale.com — 实用计算工具
- Tim Brown, "Modular Scale" Web Tools (2010)
- 24 Ways: "Compose to a Vertical Rhythm" by Richard Rutter (2006)
