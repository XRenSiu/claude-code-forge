# Color Harmony Math — coherence_check 的色彩判据

> 本文档是 `checks/coherence_check.py` 的色彩相关子检查（WCAG / OKLch / Hue Harmony）的理论依据。所有公式都已在 `checks/_shared/color_math.py` 实现，可直接调用。

## 1. WCAG 2.2 对比度

### 公式

```
contrast_ratio = (L_lighter + 0.05) / (L_darker + 0.05)
```

`L` 是相对亮度（relative luminance），按 sRGB → 线性 RGB → 加权和：

```
L = 0.2126 * R_lin + 0.7152 * G_lin + 0.0722 * B_lin
```

`R_lin / G_lin / B_lin` 通过 sRGB gamma 解码：

```
c_lin = c / 12.92                      if c <= 0.04045
      = ((c + 0.055) / 1.055) ^ 2.4    otherwise
```

### 阈值

| 内容类型 | WCAG AA | WCAG AAA |
|---|---|---|
| 正文文字（< 18pt 或 < 14pt 加粗） | 4.5:1 | 7:1 |
| 大字（≥ 18pt 或 ≥ 14pt 加粗） | 3:1 | 4.5:1 |
| 非文字 UI（图标、边框、focus ring） | 3:1（§1.4.11） | — |
| 装饰元素 / 禁用状态 | 不强制 | 不强制 |

### 实现策略（coherence_check）

不是所有 token 都按 4.5:1 评。`_classify_text_role()` 根据 role 名分级：

- `primary_text` / `body` / `heading` → 4.5:1（body tier）
- `link` / `brand` / `cta` / `accent` → 3:1（large/UI tier）
- `quaternary` / `disabled` / `placeholder` / `hover` / `success_*` / `warning_*` → 不强制（optional tier）
- 未知 role → optional（保守，避免 false positive）

只有 body tier 失败才算 blocker；其它 fail 进 warnings 列表。

## 2. OKLch 感知均匀色彩空间

### 为什么不用 HSL/RGB

HSL 的"亮度差 10%"在不同色相区域看起来差异巨大——蓝色区域人眼分辨低，黄色区域人眼分辨高。RGB 同样不感知均匀。

OKLch（Björn Ottosson 2020）是基于人眼感知设计的色彩空间，数值距离对应人眼实际感受到的差异，是当前 web 设计的最佳选择。

### 定义

- **L**（Lightness）：感知亮度，0..1
- **C**（Chroma）：饱和度（不是 HSL 的 saturation，是绝对的色度），0..0.4 typical
- **H**（Hue）：色相角度，0..360°

### 转换

sRGB → linear sRGB → OKLab → OKLch（极坐标）。完整公式见 `color_math.py::linear_srgb_to_oklab`。

### 子检查 2：Neutral Scale 均匀性

灰阶（neutral_scale）的 L 分量应：

1. **单调递增**或单调递减
2. **相邻两级 L 差值的极差/均值 < 0.3**（允许 ±15% 偏差）

公式：

```
deltas_L = [L[i+1] - L[i] for i in range(n-1)]
monotone = all(d > 0) or all(d < 0)
range_dev = (max(|deltas|) - min(|deltas|)) / mean(|deltas|)
uniformity = 1 - range_dev
```

`uniformity >= 0.7` 通过。

### 子检查：Color Family Consistency

同一色族（如 brand 的 primary/hover/light/deep）的 H 应一致（±10°），只在 L 和 C 上变化。这是 5-shade brand ladder 的隐含约束。

## 3. 色相协调 (Hue Harmony)

### 公认 schemes

色轮上的角度关系，公认 harmony schemes：

| Scheme | 角度关系 | 容差 |
|---|---|---|
| **Monochromatic** | 所有色相在 ±15° | ±15° |
| **Analogous** | 所有色相在 ±30° | ±30° + 15° |
| **Complementary** | 两组色相相差 180° | ±15° |
| **Split-complementary** | 一个 anchor + 两个相隔 150° 的色 | ±15° |
| **Triadic** | 三色相差 120° | ±15° |
| **Tetradic / Square** | 四色相差 90° | ±15° |

### 实现策略

`detect_harmony_scheme()` 算法：

1. 过滤出 chromatic colors（C ≥ 0.04）
2. 提取 H 列表
3. 按上述 scheme 优先级测试匹配
4. 都不匹配 → `free_combination`

### 子检查 3 的判定

`free_combination` **不算 fail**——产品可能合法地用多种 chromatic（如 Vercel 的 workflow 色 Develop/Preview/Ship 是三种独立功能色）。但会标 `is_free_combination: true` 让 B6 在 negotiation-summary 中提醒用户检查。

## 4. 实现位置

- `_shared/color_math.py::wcag_contrast()` / `wcag_passes()`
- `_shared/color_math.py::hex_to_oklch()` / `linear_srgb_to_oklab()`
- `_shared/color_math.py::neutral_scale_uniformity()` / `color_family_consistency()`
- `_shared/color_math.py::detect_harmony_scheme()`
- `coherence_check.py::subcheck_wcag()` / `subcheck_oklch_uniformity()` / `subcheck_hue_harmony()`

## 5. 参考

- W3C WCAG 2.2 §1.4.3 / §1.4.6 / §1.4.11
- Björn Ottosson, "A perceptual color space for image processing" (2020): https://bottosson.github.io/posts/oklab/
- Bringhurst, *The Elements of Typographic Style*（色彩协调一节）
- Itten, *The Art of Color*（色轮 harmony 经典文献）
