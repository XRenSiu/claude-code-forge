---
name: skill-evolve
description: >
  Skill Evolution Engine —— 任意 SKILL.md 的自主进化器。对目标 skill 执行
  「8 维 rubric 评分 → 聚焦改进 → 独立 subagent 复评 → 棘轮保留/回滚」循环，
  把一个能跑的 skill（~60 分）打磨到生产可交付（≥90 分）。
  Use when: (1) 用户说"优化这个 skill"/"让这个 skill 变好"/"evolve skill",
  (2) 新写的 SKILL.md 需要质量提升, (3) 已有 skill 在实战中表现不稳要回炉,
  (4) 批量提升一个目录下所有 skill 的质量水位线。
  Triggers: "优化 skill", "进化 skill", "improve skill", "evolve skill",
  "skill 变好", "skill-evolve", "darwin", "ratchet skill", "skill 调优"
when_to_use: |
  - 已经有一个能用的 SKILL.md，但效果不稳 / 触发不准 / 指令模糊
  - 新生成的 skill（来自 nuwa / persona-distill / 手写）需要进化精炼
  - 想对一个目录下多个 skill 做批量质量普查与定向修补
  - 不要用于：从零生成 skill（那是 distill-meta / nuwa 的活，本 skill 只优化已存在的）
version: 0.1.0
---

# skill-evolve

**让一个 skill 从 1 分变 100 分，不靠灵感，靠循环。**

Announce at start: "I'm using the skill-evolve skill to run the 8-dimension rubric + ratchet hill-climbing loop on the target SKILL.md."

> Skill（结构化 Prompt）和 ML 超参数一样，是可以被自动化搜索优化的参数空间。
>
> Skills are searchable parameter spaces — same as ML hyperparameters.

## 它解决什么问题

写完一个 SKILL.md 之后，绝大多数人停在「能跑就行」。但「能跑」和「好用」之间有一条 30 分的鸿沟：触发不准、步骤含糊、边界没定义、激活了不知道先干啥。

人工反复打磨成本极高，且改一处不知道是不是变差了。本 skill 把这个过程**自动化 + 防退化**：
- **自动化**：8 维 rubric 直接告诉你哪里弱、改哪里
- **防退化**：每次改完独立打分，不升反降立刻 `git revert`，分数只能涨不能跌（棘轮）

灵感来自 Karpathy autoresearch（修改→训练→保留/回滚）和 alchaincyf/darwin-skill（把范式迁移到 Skill 优化）。

## 输入与输出

**输入**：
- 目标 skill 路径（必须包含 `SKILL.md`），例如 `plugins/foo/skills/bar/`
- （可选）3 个已知测试 prompt + 期望输出方向（无则自动从 SKILL.md 推断）
- （可选）目标分数（默认 90）/ 最大轮次（默认 15）/ 收敛阈值（默认连续 3 轮无提升）

**输出**：
- `skill-evolve/experiments.tsv` —— 每轮：{round, dim_scores, total, change_summary, kept_or_reverted, commit_hash}
- `skill-evolve/baseline.md` —— 初评全维度分数 + 最弱维度诊断
- `skill-evolve/final-report.md` —— 终评 + 改进清单 + 前后对比
- 每轮 `experiment: <desc>` 前缀的 git commit（棘轮历史）

## 触发后立即做什么

```
1. 确认目标 skill 路径存在且包含 SKILL.md
2. 检查 git working tree 是否干净（脏树先暂存或提示用户处理）
3. 创建工作目录 .skill-evolve/<skill-name>/ 存放日志和报告
4. 进入 Phase 0
```

## Phase 0：基线评估（Baseline）

读取 `references/rubric.md` 中的完整 8 维评分细则，对当前 SKILL.md 打基线分。

**必须使用独立 subagent 评分**（spawn `general-purpose` agent，prompt 中**不要**透露这是初评），以避免主 agent 给自己打高分的偏差。subagent 的输入：被评估的 SKILL.md 全文 + rubric 全文 + 3 个测试 prompt。subagent 的输出：JSON 格式的 8 维分数 + 每维理由。

写入 `baseline.md`：
- 总分 + 8 维分数表
- 最弱 3 维 + 各自的失分理由（引用 SKILL.md 具体段落）
- 3 个测试 prompt 的实际输出 vs 期望对比

如果基线已经 ≥ 目标分数 → 直接出 final-report 并终止，告诉用户「这 skill 已经够好了」。

## Phase 1：进化循环（Hill-Climbing Ratchet）

每一轮 4 步，**原子修改 + 独立复评 + 强制 keep/revert**。

### 一轮的 4 步

**Step 1 — Diagnose（诊断最弱维）**
- 读取最近一次评分，找出当前最低维度
- 在该维度下精确定位 SKILL.md 中失分的段落（行号 + 引用）
- 形成假设句：「如果把 X 改成 Y，该维度应该 +N 分，因为 Z」
- 假设必须**单点聚焦**：只改一处，禁止顺手优化其它

**Step 2 — Mutate（执行修改）**
- 用 Edit 工具实施假设中的修改
- 修改前 `git add . && git commit -m "experiment: <hypothesis>"` 锁定基线
- 修改完不要 commit，先让评估跑

**Step 3 — Re-evaluate（独立复评）**
- 再次 spawn 独立 subagent，相同 rubric、相同测试 prompt
- subagent 必须不知道修改前的分数（不要在 prompt 里提）
- 拿到新分数

**Step 4 — Ratchet（棘轮决策）**

| 条件 | 动作 |
|------|------|
| `new_total > old_total` | KEEP：`git add . && git commit -m "evolve: <change> (+N pts: A→B)"`，更新基线分数 |
| `new_total == old_total` 且某低维提升 | KEEP（横向重平衡）：同上 commit |
| `new_total < old_total` | REVERT：`git checkout -- <SKILL.md path>`，丢弃修改 |
| 评分崩溃 / subagent 失败 | SKIP：记日志，下一轮 |

**每一轮都要写一行到 `experiments.tsv`**，无论保留还是回滚。

### 终止条件（任一满足即停）

- `total >= target_score`（默认 90）
- 连续 N 轮无提升（默认 N=3，收敛）
- 达到 `max_rounds`（默认 15）
- 用户 Ctrl-C / 显式叫停

## Phase 2：终评与交付

- 跑最后一次独立评分作为终分（与最近 KEEP 后的分数应一致；不一致说明评分不稳，记录差异）
- 生成 `final-report.md`：基线 vs 终值表 / 8 维变化 / 实验数（成功/回滚/跳过）/ 关键改进列表（取每次 KEEP 的 commit message）
- 列出剩余的最弱维度作为「下一轮可继续进化的方向」

## 关键工程约束（MUST FOLLOW）

1. **永远独立评分**。评估必须由不同 subagent 执行，且 prompt 中**不暴露**「这是改进版」「这是上一版」「目标是涨分」等信息，否则评分被污染。
2. **永远原子修改**。一轮只改一处。如果想同时改两处，拆成两轮。
3. **永远 git 兜底**。修改前 commit 实验快照，回滚靠 `git checkout`，不靠人工记忆。
4. **永远不退步**。即使新分等于旧分，只要某低维下降也回滚，除非低维是被刻意牺牲（罕见，需用户确认）。
5. **永远写日志**。`experiments.tsv` 的每一行都是后续迭代不重复犯错的依据；失败比成功更值钱。

## 文件总览

```
skill-evolve/
├── SKILL.md                        # 你正在读
├── references/
│   ├── rubric.md                   # 8 维评分细则（必读）
│   ├── ratchet-protocol.md         # git 操作 + keep/revert 决策表
│   ├── test-protocol.md            # subagent 复评的标准 prompt 与 JSON schema
│   └── design-rationale.md         # 为什么这么设计（来自 Karpathy + darwin）
└── templates/
    ├── baseline.md.tmpl
    ├── experiments.tsv.tmpl
    └── final-report.md.tmpl
```

读 `references/` 是强制的。第一次激活时一次性读 `rubric.md` + `ratchet-protocol.md` + `test-protocol.md`，不要边跑边读。

## 与生态中其它 skill 的边界

| 场景 | 用本 skill | 用别的 |
|------|-----------|--------|
| 已有 SKILL.md，要变好 | ✅ skill-evolve | — |
| 从零生成一个 persona skill | ❌ | persona-distill / distill-meta |
| 评估 persona skill 是否合格（一次性打分，不迭代） | ❌ | persona-judge |
| 把人物认知操作系统蒸馏成 skill | ❌ | persona-distill |
| 设计稿转代码 / 反向克隆网站 | ❌ | design-clone |

简言之：**生成是 distill 的活，评分是 judge 的活，进化是本 skill 的活。** 三者职责不重叠。

## 常见失败模式

- **评分震荡**：subagent 间分差 > 5 → rubric 太主观，改 rubric 或加平均评分
- **永远改不动某一维**：连续 5 轮某维不涨 → 该维度可能已封顶或受限于 skill 本质，标记为「已达上限」并跳过
- **分数虚高**：终分 95，实战还是烂 → 测试 prompt 太弱，加更刁钻的边缘 case
- **回滚太多**：>50% 实验被回滚 → 改进生成器太激进，要求每次只改 ≤10 行

## 一句话总结

棘轮 + 独立评分 + 8 维 rubric = 一个 skill 的可控进化路径。
不靠灵感，靠循环；不怕改坏，因为能回滚。
