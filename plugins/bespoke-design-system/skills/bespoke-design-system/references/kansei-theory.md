# Kansei Engineering — 调性词与设计参数的桥梁

> Kansei Engineering（感性工学）由广岛大学 Mitsuo Nagamachi 在 1970s 提出。核心：用情感/感性词汇（Kansei words）测量用户对产品的感受，再把这些词映射到具体的设计参数。

本 skill 用 Kansei 词作为**贯穿 B1/B2/B3/B5 的通用语言**——它是调性和参数之间唯一的可计算桥梁。

---

## 词表（按维度组织）

每个 Kansei 词都标注其在 SD（Semantic Differential）空间的典型位置 + 反义词 + 关联设计参数倾向。

### 严肃 / 玩味 维度

| 词 | SD: serious_to_playful | 反义词 | 关联设计倾向 |
|---|---|---|---|
| `serious` | -0.8 | playful | 字号克制 / 中性灰阶 / 细 stroke |
| `professional` | -0.6 | casual | 高对比度 / 标准间距 / 衬线 or 现代无衬线 |
| `precise` | -0.5 | loose | 紧凑字距 / 4px grid / 细圆角或直角 |
| `structured` | -0.4 | organic | 严格栅格 / 等宽字体 / 直线 |
| `playful` | +0.7 | serious | 多色渐变 / 大圆角 / 手写体或 humanist sans |
| `whimsical` | +0.8 | severe | 不规则装饰 / 柔色 / 弹性动效 |

### 冷 / 暖 维度

| 词 | SD: warm_to_cold | 反义词 | 关联 |
|---|---|---|---|
| `cold` | -0.8 | warm | 蓝绿色调 / 高对比 / 几何感 |
| `clinical` | -0.7 | cozy | 纯白底 / 蓝灰 / 极简装饰 |
| `cool` | -0.4 | warm | 偏蓝中性色 / 轻量阴影 |
| `neutral` | 0.0 | (none) | 灰阶基调 / 中性温度色 |
| `warm` | +0.5 | cold | 暖色调 / 柔和阴影 / 圆润形状 |
| `cozy` | +0.7 | clinical | 米白底 / 暖灰 / 软阴影 |
| `inviting` | +0.6 | austere | 暖色 + 中等饱和 + 圆角 |

### 现代 / 古典 维度

| 词 | SD: modern_to_classical | 反义词 | 关联 |
|---|---|---|---|
| `modern` | -0.7 | classical | 几何无衬线 / 平面 / 高饱和 |
| `minimalist` | -0.5 | ornate | 大量留白 / 单色调 / 无装饰 |
| `contemporary` | -0.4 | traditional | 当代字体 / 微妙阴影 |
| `classical` | +0.6 | modern | 衬线字体 / 对称构图 / 暗金 |
| `traditional` | +0.7 | contemporary | 衬线 / 暗木色 / 对称 |
| `ancient` | +0.8 | futuristic | 衬线 / 暗调 / 古色 / 留白多 |

### 装饰 / 极简 维度

| 词 | SD: ornate_to_minimal | 反义词 | 关联 |
|---|---|---|---|
| `ornate` | -0.8 | minimal | 多层装饰 / 多色 / 复杂图案 |
| `decorative` | -0.5 | spare | 装饰元素 / 多层阴影 |
| `rich` | -0.3 | sparse | 多色 / 多字重 / 多动效 |
| `clean` | +0.5 | cluttered | 单色调 / 大留白 / 单层结构 |
| `minimal` | +0.7 | ornate | 极少元素 / 大量空白 / 单色 |
| `spare` | +0.8 | rich | 黑白灰 / 系统字体 / 无动效 |

### 信任 / 神秘 / 权威

| 词 | 关联设计倾向 |
|---|---|
| `trustworthy` | 蓝色系 / 高对比 / 标准化布局 |
| `mystical` | 暗紫蓝 / 衬线显示字体 / 大留白 / 慢动效 |
| `authoritative` | 深色 / 衬线 / 严格栅格 / 大字号差 |
| `confident` | 中等饱和 / 粗 stroke / 明确层级 |
| `calm` | 低饱和 / 柔色 / 慢动效 / 多空白 |
| `energetic` | 高饱和 / 多色 / 快动效 / 渐变 |
| `aggressive` | 高对比 / 红/黑 / 快动效 / 大字号 |

### 情感色彩

| 词 | 关联 |
|---|---|
| `caring` | 暖色 / 圆角 / 柔阴影 |
| `nurturing` | 暖中性色 / 衬线或 humanist sans |
| `daring` | 高饱和强对比 / 极端字号 / 不对称 |
| `rebellious` | 黑/红/荧光 / 直角 / 字号大 |

---

## 反义对（用于冲突检测）

| Pair |
|---|
| modern ↔ classical / ancient |
| minimal ↔ ornate / decorative / rich |
| serious ↔ playful / whimsical |
| cold / clinical ↔ warm / cozy |
| precise / structured ↔ organic / loose |
| confident ↔ humble |
| energetic ↔ calm |
| aggressive ↔ gentle / nurturing |

B3 的 conflicts_with 关系图判断时使用此表。

---

## Kansei 词的使用约定（贯穿 skill）

1. **不造词**。如果某个调性需要新词描述，优先组合已有词（"mystical + ancient"），而非造新词。
2. **三段密度**：positive 词 3-7 个，reverse_constraint 1-4 个，刚好够画像表达，不冗余。
3. **避免重叠**：同一画像里 `precise` 和 `structured` 通常重叠，选其一即可。
4. **反义词不入 positive**：如果 positive 含 `modern`，reverse_constraint 不应再含 `classical`（多余）。但反过来必要：positive 含 `mystical` + reverse 含 `aggressive` 是合理的明确边界。

---

## SD 维度（4 个核心轴）

每个轴 [-1, +1] 连续：

- `warm_to_cold`：负 = 暖，正 = 冷
- `ornate_to_minimal`：负 = 装饰，正 = 极简
- `serious_to_playful`：负 = 严肃，正 = 玩味
- `modern_to_classical`：负 = 现代，正 = 古典

B2 的 SD 距离修正用 L2 距离：

```
sd_distance(profile, rule) = sqrt(Σ (rule.sd_anchors[axis] - profile.semantic_differentials[axis])²)
```

---

## 参考文献

- Nagamachi, M. (1995). *Kansei Engineering: A new ergonomic consumer-oriented technology for product development*
- Schütte, S. (2005). *Engineering emotional values in product design — Kansei engineering in development*
- Osgood, C. E. (1957). *The Measurement of Meaning*（Semantic Differential 起源）
