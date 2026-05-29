---
name: skill-evolve
description: >
  Skill Evolution Engine —— 任意 SKILL.md 的自主进化器。对目标 skill 执行
  「9 维 rubric 评分（含 SkillLens 验证的失败机制/可执行性/高风险黑名单三高信号维 +
  带 skill vs 无 skill 基线对比）→ 聚焦改进 → 独立 subagent 复评 → 棘轮保留/回滚」循环，
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
version: 0.2.1
---

# skill-evolve

**让一个 skill 从 1 分变 100 分，不靠灵感，靠循环。**

Announce at start: "I'm using the skill-evolve skill to run the 9-dimension rubric (with no-skill baseline comparison) + ratchet hill-climbing loop on the target SKILL.md."

> Skill（结构化 Prompt）和 ML 超参数一样，是可以被自动化搜索优化的参数空间。
>
> Skills are searchable parameter spaces — same as ML hyperparameters.

## 它解决什么问题

写完一个 SKILL.md 之后，绝大多数人停在「能跑就行」。但「能跑」和「好用」之间有一条 30 分的鸿沟：触发不准、步骤含糊、边界没定义、激活了不知道先干啥。

人工反复打磨成本极高，且改一处不知道是不是变差了。本 skill 把这个过程**自动化 + 防退化**：
- **自动化**：9 维 rubric 直接告诉你哪里弱、改哪里
- **防退化**：每次改完独立打分，不升反降立刻回滚，分数只能涨不能跌（棘轮）
- **防自欺**：rubric 的三个高信号维（失败机制 / 可执行性 / 高风险黑名单）来自 SkillLens 实测，且每轮强制跑「带 skill vs 不带 skill」基线对比——刷分但实际拖累 agent（负迁移）会被当场抓出并回滚

灵感来自 Karpathy autoresearch（修改→训练→保留/回滚）、alchaincyf/darwin-skill（把范式迁移到 Skill 优化），以及微软 SkillLens（arXiv 2605.23899，46.4%→73.8% 的三维药方 + 负迁移发现）/ SkillOpt（arXiv 2605.23904，拒绝缓冲 + 慢更新记忆 + 文本学习率三个稳定性控制）。

## 输入与输出

**输入**：
- 目标 skill 路径（必须包含 `SKILL.md`），例如 `plugins/foo/skills/bar/`
- （可选）3 个已知测试 prompt + 期望输出方向（无则自动从 SKILL.md 推断）
- （可选）目标分数（默认 90）/ 最大轮次（默认 15）/ 收敛阈值（默认连续 3 轮无提升）

**输出**：
- `.skill-evolve/<skill>/experiments.tsv` —— 每轮：{round, dim_scores(9), total, negative_transfer, change_summary, kept_or_reverted, flags(dry_run/single_judge), commit_hash}
- `.skill-evolve/<skill>/baseline.md` —— 初评全维度分数 + 最弱维度诊断 + 确认过的测试集
- `.skill-evolve/<skill>/learnings.md` / `dead-ends.md` —— 滚动正/负反馈记忆
- `.skill-evolve/<skill>/final-report.md` —— 终评 + 改进清单 + 前后对比 + 负迁移确认
- 每轮 `experiment: <desc>` 前缀的 git commit（棘轮历史）

## 触发后立即做什么

```
1. 确认目标 skill 路径存在且包含 SKILL.md
2. 检查 git working tree 是否干净（脏树先暂存或提示用户处理）
3. 创建工作目录 .skill-evolve/<skill-name>/ 存放日志和报告
4. 初始化滚动记忆（移植自 SkillOpt）：
   : > .skill-evolve/<skill-name>/learnings.md   # 已验证规律（正反馈）
   : > .skill-evolve/<skill-name>/dead-ends.md   # 已证伪改法（负反馈，禁重试）
5. 检查 Agent/subagent 工具是否可用；不可用 → 走 dry_run 降级模式（见 test-protocol）
6. 进入 Phase 0
```

## Phase 0.5：测试 prompt 设计与确认（先于评估的门）

测试 prompt 的质量直接决定优化方向对不对（SkillLens：测试太弱会导致「分数虚高、实战还烂」）。所以在任何评估之前：

1. 按 test-protocol「测试 prompt 自动生成」规则备出 3 个测试 prompt（happy path）+ 1 个边缘 prompt（相邻领域、超范围）
2. 写入 `baseline.md` 的「测试集」区，**展示给用户确认**
3. 用户可替换/补充更刁钻的 case。**用户确认后才进入 Phase 0**——这一步不许跳过

（用户若明确说「不用确认，自动跑」可跳过门，但要在 baseline.md 标注 `test_prompts: auto-unconfirmed`。）

## Phase 0：基线评估（Baseline）

读取 `references/rubric.md` 中的完整 9 维评分细则，对当前 SKILL.md 打基线分。

**必须使用独立 subagent 评分，且默认 spawn 2 个独立评委取中位数**（见 test-protocol「多评委是默认」）。prompt 中**不要**透露这是初评，避免主 agent 给自己打高分的偏差。评委输入：被评估的 SKILL.md 全文 + rubric 全文 + Phase 0.5 确认的测试集。评委输出：JSON 格式的 9 维分数 + 每维理由 + `negative_transfer` 标志。

每个测试 prompt 都要跑**两遍**——带 skill（with_skill）与不带 skill（baseline）——对比出增益，这是 dim 8 的核心，也是抓负迁移的唯一手段。

写入 `baseline.md`：
- 总分 + 9 维分数表
- 最弱 3 维 + 各自的失分理由（引用 SKILL.md 具体段落）
- 3 个测试 prompt 的 with_skill vs baseline vs 期望 三方对比
- `negative_transfer` 是否触发

如果基线已经 ≥ 目标分数 **且 negative_transfer == false** → 直接出 final-report 并终止，告诉用户「这 skill 已经够好了」。若基线就有负迁移，无论分数多高都要进入循环修复。

## Phase 1：进化循环（Hill-Climbing Ratchet）

每一轮 4 步，**原子修改 + 独立复评 + 强制 keep/revert**。

### 一轮的 4 步

**Step 1 — Diagnose（诊断最弱维）**
- 读取最近一次评分，找出当前最低维度（高信号三维 failure_mechanism / executable_specificity / highrisk_blacklist 同分时优先修它们，性价比最高）
- **先读 `learnings.md` + `dead-ends.md`**：复用已验证规律，且**不重走 dead-ends 里证伪过的改法**（移植自 SkillOpt 拒绝缓冲）
- 在最弱维下精确定位 SKILL.md 失分段落（行号 + 引用）
- 形成假设句：「如果把 X 改成 Y，该维度应该 +N 分，因为 Z」
- 假设必须**单点聚焦**：只改一处，禁止顺手优化其它

**Step 2 — Mutate（执行修改）**
- 修改前 `git add . && git commit -m "experiment: <hypothesis>"` 锁定基线
- 用 Edit 工具实施假设中的修改
- **变更预算（硬约束，文本学习率）：单轮改动 ≤ 30 行**。想改更多 → 拆成多轮。无约束的大改易出「语义跳跃」、丢掉已打高分的段落（SkillOpt 消融证实）
- 修改完不要 commit，先让评估跑

**Step 3 — Re-evaluate（独立复评）**
- 再次 spawn 独立评委（默认 2 个取中位数），相同 rubric、相同测试集
- 评委必须不知道修改前的分数（不要在 prompt 里提）
- 拿到新分数 + `negative_transfer` 标志

**Step 4 — Ratchet（棘轮决策 + 记忆更新）**

完整决策表见 `references/ratchet-protocol.md`，要点：

| 条件 | 动作 |
|------|------|
| **`negative_transfer == true`** | **REVERT（铁律，优先于一切）**：带 skill 还不如不带，分再高也丢 |
| `new_total > old_total` 且无维度下降 | KEEP：`git commit -m "evolve: <change> (+N pts: A→B)"`，更新基线 |
| `new_total == old_total` 且某低维提升、无维度下降 | KEEP（横向重平衡） |
| `new_total < old_total` 或某维下降 | REVERT：`git checkout -- <SKILL.md path>` |
| 评分崩溃 / subagent 失败 | SKIP：记日志，下一轮 |

决策后**更新滚动记忆**：
- KEEP → 把「改了什么 + 为什么涨」蒸馏 ≤2 行追加进 `learnings.md`
- REVERT → 把「试了什么 + 为什么没用/退化」蒸馏 ≤2 行追加进 `dead-ends.md`

**每一轮都要写一行到 `experiments.tsv`**，无论保留还是回滚（dry_run 时标 `dry_run`，单评委时标 `single_judge`）。

### 收敛前的探索性重写（破局部最优，移植自 Darwin Phase 2.5）

当**连续 N 轮无 KEEP 即将判收敛**、或**某一维连续 5 轮改不动**时，先别放弃——做一次大扰动：

1. `git branch evolve-snapshot-rN` 保存当前最优
2. spawn 一个 mutate agent，prompt 特别说明：「增量路线已卡死，允许你**无视 30 行预算、重组该维度相关的整块结构**（但 frontmatter 的 name/version 不动，且不得引入负迁移）。参考 dead-ends.md，别重走死路」
3. 独立复评（仍含 baseline 对比）
4. 更好且无负迁移 → 采用，重置 plateau 计数；否则 → 回到 snapshot
5. 每个 skill **最多一次**探索性重写，避免无限扰动烧轮次

### 终止条件（任一满足即停）

- `total >= target_score`（默认 90）**且 `negative_transfer == false`**
- 连续 N 轮无提升（默认 N=3，收敛）——但首次触发时先走一次探索性重写
- 达到 `max_rounds`（默认 15）
- 用户 Ctrl-C / 显式叫停

**带负迁移的版本永不算"达标"**——哪怕 total 95，只要 negative_transfer 为 true 就继续修或回退到最近一个干净版本。

## Phase 2：终评与交付

- 跑最后一次独立评分（默认 2 评委取中位数）作为终分（与最近 KEEP 后的分数应一致；不一致说明评分不稳，记录差异）
- **交付前确认 `negative_transfer == false`**：带负迁移的版本不许交付，回退到最近一个 negative_transfer=false 的 KEEP 版本
- 生成 `final-report.md`：基线 vs 终值表 / 9 维变化 / 实验数（成功/回滚/跳过/dry_run）/ 关键改进列表（取每次 KEEP 的 commit message）/ learnings.md 摘要
- 列出剩余的最弱维度作为「下一轮可继续进化的方向」

## 关键工程约束（MUST FOLLOW）

1. **永远独立评分，且默认多评委**。评估由不同 subagent 执行（默认 2 个取中位数），prompt 中**不暴露**「这是改进版」「上一版」「目标涨分」，否则评分被污染。单评委是 SkillLens 量化过的 46.4% 不可靠区。
2. **永远原子 + 限额修改**。一轮只改一处，且 ≤30 行（文本学习率）。想多改拆成多轮；唯一例外是探索性重写。
3. **永远 git 兜底**。修改前 commit 实验快照，回滚靠 `git checkout`，不靠人工记忆。
4. **永远不退步，且永不交付负迁移**。某低维下降即回滚（除非刻意牺牲且用户确认）；`negative_transfer==true` 一律回滚，优先于一切——带 skill 还不如不带的版本，分再高也不要。
5. **永远写日志 + 喂记忆**。`experiments.tsv` 记原始轨迹；每轮把规律蒸馏进 `learnings.md`、把死路蒸馏进 `dead-ends.md` 喂给下一轮（SkillOpt 消融中长程记忆是最致命的单一控制）。失败比成功更值钱。
6. **永远跑无 skill 基线**。效果维度必须 with_skill vs baseline 对比，不能只看「带 skill 做对没」——否则测不出负迁移。

## 文件总览

```
skill-evolve/                       # 源码（你正在读）
├── SKILL.md
├── references/
│   ├── rubric.md                   # 9 维评分细则（必读）
│   ├── ratchet-protocol.md         # git 操作 + keep/revert/negative-transfer 决策表
│   ├── test-protocol.md            # 多评委 + baseline 对比 + dry_run 的标准 prompt 与 JSON schema
│   └── design-rationale.md         # 为什么这么设计（Karpathy + darwin + SkillLens/SkillOpt）
└── templates/
    ├── baseline.md.tmpl
    ├── experiments.tsv.tmpl
    └── final-report.md.tmpl

.skill-evolve/<skill-name>/         # 运行时工作目录（每次迭代生成）
├── baseline.md / experiments.tsv / final-report.md
├── learnings.md                    # 滚动正反馈（已验证规律）
└── dead-ends.md                    # 滚动负反馈（已证伪改法，禁重试）
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

- **评分震荡**：评委间分差 > 10 → rubric 太主观，暂停循环调锚点（默认多评委已缓解小幅震荡）
- **永远改不动某一维**：连续 5 轮某维不涨 → 触发探索性重写（破局部最优）；仍不动再标「已达上限」并跳过
- **分数虚高**：终分 95 实战还烂 → 测试 prompt 太弱；Phase 0.5 确认门 + baseline 对比就是为防它，必要时加更刁钻的 case
- **刷分但拖累 agent**：total 涨了但 `negative_transfer` 真相暴露 → 这正是 dim 8 baseline 对比要抓的；铁律回滚，别交付
- **回滚太多**：>50% 实验被回滚 → 改进太激进，收紧到 ≤30 行/轮甚至更少，并多读 dead-ends.md 避免重复死路

## 一句话总结

棘轮 + 默认多评委 + 9 维 rubric（含 SkillLens 三高信号维 + 无 skill 基线对比）= 一个 skill 的可控进化路径。
不靠灵感，靠循环；不怕改坏，因为能回滚；不自欺，因为测得出负迁移。
