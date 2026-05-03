# Examples — 端到端案例

> 本目录存放 bespoke-design-system 的完整生成案例。每个案例展示从用户原始需求到最终 DESIGN.md 的完整产物链路，便于：
>
> 1. 验证 skill 在不同场景下的产物质量
> 2. 作为新用户的参考样板
> 3. 提供 P0 闸门的 false-positive / false-negative 检测语料

## 单个案例的目录结构

每个案例一个子目录，命名 = 产品 slug：

```
examples/<case-slug>/
├── input.md                      # 用户原始需求（自然语言）
├── mode.txt                      # interactive | auto
├── clarification-batch.md        # 仅 interactive 模式有：B1a 输出的问题 + 用户回答
├── inferred-fields.yaml          # 仅 auto 模式有：B1b 推断的字段清单
├── user-profile.yaml             # B1 最终合成的调性画像
├── output-design.md              # B6 输出的 DESIGN.md（9-section 标准）
├── provenance.yaml               # B6 输出的决策追溯
└── negotiation-summary.md        # B6 输出的用户可读摘要
```

## 推荐案例（建议在使用 skill 一段时间后回头补全）

为覆盖典型 niche，建议至少有这些案例：

| Case slug | Product brief | Expected mode | 测试什么 |
|---|---|---|---|
| `bazi-saas` | "我想做一个八字 SaaS" | interactive | spiritual_saas + 一次性追问的最低充分性 |
| `dev-tool-cli` | "命令行 AI 编码助手" | auto | developer_tool 的零追问推断 |
| `kids-learning` | "给小学生用的数学学习平台" | interactive | Innocent + Caregiver + 严格的 reverse_constraint |
| `luxury-watch` | "高端机械表电商" | interactive | Lover + Ruler + 衬线优先 |
| `outlaw-zine` | "独立摄影师的作品集" | auto | Outlaw + Creator + 反 slop 的强信号 |
| `mental-health` | "情绪追踪 app" | interactive | Caregiver + 隐私敏感 + warm 调性 |

## 案例的用途

### 1. 验证产物质量

每次 skill 升级（minor 以上）后，用相同 input 跑一遍所有案例，对比新旧 output：

- 如果新 output 反而 slop 化或 rationale 退化 → 升级引入了回归
- 如果新 output 在 P0 闸门通过率提升 + rationale 质量提升 → 升级正确

### 2. 训练 anti-slop-blacklist

如果某案例多次跑出可疑模式（如不同 input 都产出 #8B5CF6 强调色），说明黑名单需要新增条目或现有条目检测过弱。

### 3. 沉淀 adaptation 的语料

`grammar/meta/adaptation-stats.json` 中每条 adaptation 的 contexts 来自实际生成。examples 是早期阶段最重要的 contexts 来源——它们让自演化机制有冷启动数据。

## 添加新案例

完成一次满意的生成后，可以把产物归档到 examples：

1. `mkdir examples/<slug>`
2. 复制三份产物 + B1 画像 + （如有）clarification batch
3. 在本 `_README.md` 表格中加一行（如果是新场景）
4. commit 时单独提交，commit message 格式：`docs(examples): add <slug> case`

## 案例的一致性维护

随着规则库版本演进，老案例的 output 可能与最新 skill 产生的不一致。维护策略：

- **保留老案例**作为历史快照（不重新生成）
- **对照新版本**生成时另起 `<slug>-v<n>/` 目录，便于 diff 对比
- 在 `_README.md` 表格中标注每个案例对应的 `rules_version`

## 隐私

如果案例 input 含用户的敏感产品想法（未公开），不要 commit 到公共仓库。本地 examples 目录可以加 `.gitignore` 规则。
