# Reflective Practice — Rationale 必须叙事化

> Donald Schön 在 *The Reflective Practitioner* (1983) 中提出：专业判断的核心不是"应用规则"，而是 **reflection-in-action** ——在做的同时反思 trade_off、目标、避免项。叙事化的 rationale 是这种反思的产物。

本 skill 在 A2（拆解时）和 B4（生成时）都要求**三段式叙事 rationale**，根基就在这里。

---

## 为什么要叙事化

如果 rationale 只是参数（"primary color = #5E6AD2"），它就是描述结果，不是设计判断。

如果 rationale 含 trade_off / intent / avoid，它才是**判断**——告诉读者这个决策在哪两端取了平衡、希望传达什么、明确避免了什么。

判断的可贵之处在于**它是关于 边界 的**：

- trade_off：边界在哪两端
- intent：朝向哪一端用力
- avoid：另一端的失败模式长什么样

只有捕捉到边界，rationale 才能在 B4 阶段被**新场景**调用——新场景可能落在不同位置，但同一个 trade_off 仍成立。

---

## 三段式 schema（A2 拆解时）

```yaml
- decision: 主色 #5E6AD2(偏紫的冷蓝)
  trade_off: 工程精度感(纯蓝) ↔ 人文温度(偏紫)
  intent: 让产品看起来既严肃又不冷漠
  avoid:
    - 纯蓝带来的"医疗器械感"
    - 纯紫带来的"游戏 UI 感"
```

**质量门槛**：

- `trade_off`：必须是**两个**对立的具体感受（不是"好 vs 不好"）
- `intent`：必须是**正向的**调性描述，不是"要好用 / 要专业"
- `avoid`：必须是**具体的失败模式**（"医疗器械感"），不是抽象判断（"不专业"）

如果 DESIGN.md 原文没有显式说出 trade_off 或 avoid，A2 推断时必须在条目上标 `[inferred]`，让后续可追溯。

---

## 三段式 schema（B4 生成时）

生成时的 rationale 必须包含**三段**（schema 见 SKILL.md §六 3.3.7）：

| 段 | 角色 | 必须 |
|---|---|---|
| `inheritance` | 来源（哪些规则、哪些 system、原 rationale） | 具体 rule_id 列表 + 原始 trade_off/intent 文字 |
| `adaptation` | 调适（哪些维度改了、from/to、原因） | 每个 modification 的 dimension/from/to/reason |
| `justification` | 协同（与其它决策的内部一致性、Kansei 覆盖、冲突检查） | 至少一条 internal_consistency 指向具体已写 section |

这三段对应 Schön 的"reflection-in-action"的三个动作：

- **inheritance** = "我从哪里学到这个判断"
- **adaptation** = "为这个新场景，我做了什么调整"
- **justification** = "调整后，整体是否还成立"

少任何一段都让 rationale 退化为单向描述，违反双向对称原则。

---

## 双向对称（核心工程原则）

> 拆解时怎么提取 rationale，生成时就怎么产出 rationale。

这是本 skill 最关键的工程约束：

- 拆解只产参数 → 生成就只能拼贴
- 拆解产 rationale，生成只追溯来源 → 产物是"借用而非应用"
- **拆解产 rationale，生成也产 rationale → 产物才是真正"用语法生成新作品"**

`subagents/rationale-judge.md` 的存在就是为了守这条对称——评判方独立验证生成的 rationale 是否真实、可追溯、可证伪。

---

## 反例：不合格的 rationale

**不合格 1**（描述结果，无判断）：

```yaml
- decision: 主色 #5E6AD2
  reason: 这是一个偏紫的蓝色，看起来很专业。
```

无 trade_off、无明确的 intent、无 avoid。读者无法判断这个决策能否迁移到新场景。

**不合格 2**（justification 含糊）：

```yaml
justification:
  internal_consistency:
    - 与其它决策协同
  user_kansei_coverage:
    addressed_in_this_decision: [structured]
```

"与其它决策协同"——哪个决策？哪个字段？rationale-judge 必须能验证。

**不合格 3**（adaptation 编造 from）：

```yaml
adaptation:
  modifications:
    - dimension: saturation
      from: 0.50  # ← 但原规则的 saturation 是 0.45，不是 0.50
      to: 0.30
```

虚构 from 值是 inheritance 不真实的表现。rationale-judge 第 1 维度就会抓出来。

---

## 实操：从 DESIGN.md 推断 rationale

很多 DESIGN.md（特别是早期版本）只描述参数，不描述判断。A2 拆解时如何补 rationale？

**优先策略**：

1. **看散文段落**：DESIGN.md 中除了表格 / 列表外的散文段落往往含 trade_off / intent
2. **看 Anti-patterns section**：往往直接告诉 avoid
3. **看 Brand section**：常含 intent
4. **若都没有，再推断**：基于行业常识 + Brand Archetype 推断，但**必须标 [inferred]**

**禁止策略**：

- 编造 trade_off 让规则看起来更深刻
- 把"看起来不错"作为 intent

---

## 参考

- Schön, D. (1983). *The Reflective Practitioner: How Professionals Think in Action*
- Schön, D. (1987). *Educating the Reflective Practitioner*
- Cross, N. (2011). *Design Thinking: Understanding How Designers Think and Work*（Schön 工作的设计领域延伸）
