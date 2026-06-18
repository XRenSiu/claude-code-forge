# B0.5 — Concept Seeding（v1.13.0 新增 / 改动3：concept-first）

> 当 SKILL.md 主流程进入 B0.5 时读取本文件。在 B0（模式分流）之后、B1（调性画像）之前执行。

## 为什么有这一步

旧流程从 **品类 → 固定质心** 出发：`defaults.yaml` 给每个 product_category 一组固定 archetype/kansei/SD，于是**每个八字 SaaS 拿到同一个起点画像**，产品的具体性在检索前就被丢掉了——这是"很普通"的第一个成因（在 B2 之前就已经塌缩到品类均值）。

B0.5 反转顺序：先为**这一个 brief** 生成几个**组织性概念（POV）**，让概念去**驱动**后续的画像推断与规则检索，而不是品类质心驱动。概念是设计的"统领想法"，token 应当从它派生，而不是堆 token 碰运气碰出身份。

## 你的任务

为当前 brief 生成 **3 个发散的设计概念种子**。每个是一个**具体的立场 / 隐喻**，绑定这个产品的独特之处——**不是品类标签**。

### 什么算合格的概念（POV）

- ✗ 品类标签："clean dev tool" / "trustworthy fintech" / "friendly SaaS" —— 这是分类，不是观点
- ✓ 具体立场 / 隐喻："把命理排盘当成天文台仪表盘——冷峻、精密、可信，而不是地摊算命" / "审查界面像代码本身一样克制" / "金融基础设施做成奢侈品的入会体验"
- 好概念能解释它**拒绝**什么（拒绝 = 有 stance）

### 三个种子要真发散

不是同一方向的三个微调。让它们在以下至少一个轴上**显著不同**：核心隐喻 / 情绪温度 / 借鉴的领域（编辑设计 vs 工业仪表 vs 游戏）/ 它愿意冒的险。覆盖"稳健—大胆"的不同点位（至少一个明显偏大胆）。

### 每个种子给

```yaml
concept_seeds:
  - id: A
    pov: <一句话立场/隐喻，绑定这个产品的具体特质>
    rejects: <这个概念有意拒绝的常规做法>
    signature_hypothesis: <它可能的签名动作方向——形式层面，不必精确到 px>
    tension_hint: <它可能需要的"不寻常组合"——B2 检索时要确保覆盖到，B3 会作为 productive_tension 留存>
    archetype_lean: <它把画像往哪个 archetype 偏，可与品类默认不同>
    kansei_lean: [<它强调的 1-3 个 kansei 词，可超出品类默认>]
    boldness: conservative | balanced | bold
  - id: B ...
  - id: C ...
```

## 输出怎么用（下游约定）

- **B1（画像）**：用 `concept_seeds` 的 `archetype_lean` / `kansei_lean` **覆盖或扩展** `defaults.yaml` 的品类质心——auto 模式下尤其重要，把品类默认当**先验**而非**结论**。把三个种子的 lean 取并集，得到一个**更宽、不塌缩**的画像（B2 检索要能服务任一概念）。在画像 `inferred_fields` / `concept_seeds` 中保留这三个种子供 B6 暴露。
- **B2（检索）**：除了 archetype/kansei 检索，额外确保每个 `tension_hint` 指向的规则**进入候选集**（哪怕它与主画像低共现）——否则 B3 没有张力原料可留、B4a 没法发散。
- **B3**：anchor 保协调，`tension_hint` 对应的规则会落进 `productive_tensions`。
- **B4a**：**不要重新发明概念**——把这三个种子**发展**成 grounded candidate directions（用 B3 真实规则 + anchor + tensions 落地）。B4.5 taste-critic 选其一。

## 铁律

- 概念绑定**这个 brief 的具体特质**，不是品类。
- 不向用户追问（interactive 模式下，概念基于 B1a 的回答 + brief；但 B0.5 本身不追加问题——它在 B1 之前只用 brief 起草，B1a 回答回来后可在 B1 微调种子）。
- 三个种子必须真发散，且至少一个 `boldness: bold`——否则等于没做 concept-first。
