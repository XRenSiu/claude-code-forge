# Shape Grammar — 规则反推与生成机制

> 由 George Stiny 与 James Gips 在 1971 年提出。Knight & Stiny 在 *Making Grammars* (2015) 中系统化。本 skill 在两个方向上使用 Shape Grammar：拆解时**反推规则**，生成时**应用规则**。

---

## 核心思想

一组成熟的设计作品（这里：DESIGN.md 集合）可以被视为某套**生成语法**的产物：

- **词汇 (vocabulary)**：基本元素（颜色、字号、间距、形状...）
- **规则 (rules)**：替换/变换的产生规则（"if precondition X then action Y"）
- **关系 (relations)**：规则之间的依赖、冲突、共现

如果能反推出语法，就能用语法**生成新的、合规的、未见过的**作品——而不是简单复制现有样本。

---

## 拆解时：从作品反推规则

### 反推的三个层次

| 层次 | 输出 | 例子 |
|---|---|---|
| 词汇 | 这套设计用了哪些 token | `#5E6AD2 / Inter / 4px grid / cubic-bezier(0.16,1,0.3,1)` |
| 句法 | 这些 token 如何组合 | "primary color 用在 CTA + 顶部 nav active state；其它地方用 neutral" |
| 语义 | 为什么这样组合 | "让 primary 成为视觉锚点，控制注意力路径" |

本 skill 的 A1（Token 层）对应词汇，A2（Rationale）+ A3（Rule）对应句法 + 语义，A4（关系图）对应规则间的更高层语法。

### 反推时的工程纪律

1. **不止于词汇**：只列 hex 和 px 值是 token 库，不是语法。必须抽到"参数化模式 + preconditions + why"的层级。
2. **不止于规则**：单条规则没有解释力，规则之间的关系（依赖、冲突、共现）才是语法的本质。
3. **保留多解释**：同一作品可以由多套语法生成。反推时若有歧义，倾向选**与素材库其它系统相容性更高**的那套（即更接近 co_occurs_with 高密度的解释）。

---

## 生成时：用语法做新判断

### 生成 ≠ few-shot 模仿

| | few-shot | shape-grammar 生成 |
|---|---|---|
| 输入 | 几个例子 | 一组规则 + 关系 |
| 模型工作 | 模式匹配 + 类比 | 规则在新 preconditions 下的实例化 + 调适 |
| 产物 | 像例子的新作 | **不必像任何例子**的合规新作 |
| 可解释性 | 弱（"模型觉得这样像"） | 强（每个决策都能追溯到具体规则 + adaptation） |

本 skill 严格走 shape-grammar 路径而非 few-shot，原因：

- few-shot 在调性维度独立时容易"参数拼贴"
- few-shot 不能产 rationale（因为模型不知道为什么模仿）
- shape-grammar 让 P0 闸门有可验证的对象（rule_id + adaptation 是可数的）

### 生成的两种动作

**Step 1 — 实例化（Instantiation）**

把规则的参数化 action 翻译成具体值，前提是 preconditions 与画像匹配。例：

```yaml
# 规则
action:
  hue: 240°-260°
  saturation: 0.40-0.50
  lightness: 0.50-0.60

# 画像匹配后实例化为
hsl(250°, 0.45, 0.55) = #5E6AD2
```

**Step 2 — 调适（Adaptation）**

当画像与规则 preconditions 部分匹配（不是完全匹配）时，沿着规则的 action 维度做受控偏移。例：

```yaml
# 规则原 action（适用 [structured, professional]）
saturation: 0.45

# 画像新增 [mystical, ancient]
# 不在原 preconditions 中，但 Kansei 理论上 ancient → 低饱和度
# adaptation: saturation 0.45 → 0.30，reason: ancient 需要低饱和度的"夜空感"
```

调适必须能在 Kansei / 色彩心理学 / Brand Archetype 等参考理论中找到支持。否则就是凭空发挥，违反 shape-grammar 的"在已有语法上生成"原则。

---

## 关键约束

1. **规则不能凭空创造**：B4 阶段不允许引入 B3 子集之外的新规则。任何看起来像新规则的判断都要追溯到某条已有规则的 instantiation 或 adaptation。
2. **adaptation 必须沿 dimension 偏移**：不能"全面重写"一条规则；只能在该规则的某些 dimension 上调 from/to。
3. **关系图先于生成**：B3 用图算法解决冲突 + 找风格岛，是为了让 B4 的输入是一个**已经自洽**的子语法。否则 B4 可能在自相矛盾的规则上生成。

---

## 自演化（Grammar Evolution）

当某条 adaptation 反复出现（occurrences ≥ 5）且模式一致 → 它已经是一条**事实上的新规则**，应该正式沉淀进语法（`scripts/consolidate-adaptations.md`）。

这对应 Shape Grammar 文献中的"grammar evolution"或"meta-grammar"概念：语法本身可以被使用经验修改。

派生规则的 `provenance: generated` 与原生规则区分，便于：

- 独立追溯（哪些规则是来自素材的、哪些是从使用中长出来的）
- 独立回滚（如果某派生规则反复在 P0 闸门被驳回）
- 独立分析（用 generated rules 的分布反观素材库的覆盖盲区）

---

## 参考

- Stiny, G. & Gips, J. (1971). *Shape Grammars and the Generative Specification of Painting and Sculpture*
- Knight, T. & Stiny, G. (2015). *Making Grammars: From Computing with Shapes to Computing with Things*
- Stiny, G. (2006). *Shape: Talking About Seeing and Doing*
