# 推导对应：PSL 六层 → 三样产物

| PSL 层 | 喂给 | 推什么 |
|---|---|---|
| Vision | 形态草案的"明确不做" | 根命题否定掉的形态 |
| Mental Model | Workflow φ、形态草案的交互 | 用户以为世界怎么运转 → 界面必须顺着它 |
| Domain Model | DOS 提案 objects / relationships | 应然本体；对象 ≤ 7；不造 PSL 没有的实体 |
| State Machine | DOS 提案 behaviors、Workflow Σ | 状态流转 → 副作用清单 |
| Workflow（Σ+φ） | workflow.md | 原样投影，禁步骤化 |
| Acceptance | 形态草案的验收挂钩 | 每条形态决策至少能被一条 Acceptance 检到（否则它是装饰） |
| Personas / JTBD | 形态草案界面层 | 意图词表 → 元素映射 |
| UI Contract / Design Principles | 形态草案 | 产物须呈现的性质、冲突取舍 |

## 分歧集的比对方法

1. 把每个版本的形态草案按 `[F-nn]` 决策点对齐（同一决策点可能编号不同，按语义对齐，记录映射）。
2. 逐点比较：选择相同且引用相同 → 一致；选择相同引用不同 → 一致但记"多源"；选择不同 → 分歧。
3. 分歧率 > 50% → 不合并，回报"PSL 约束太弱"。
4. 每条分歧写议程：是 PSL 某条规律含糊（改 PSL）、是承重槽没填（补 Mental Model / Open Question 请人定）、
   还是推导者即兴（舍弃）。

## "技术对、产品错"的信号

- 形态草案里出现 PSL 没有的实体名（`TimeBucket`、`Filter`）。
- 决策引用的是 Domain Model 之外的常识（"用户通常想按日期筛"）。
- Workflow 写成了执行顺序。
- 验收挂钩缺失：某条形态决策没有任何 Acceptance 能检到。
- 三个版本在同一决策点上给出三种界面——这个点在 PSL 里是空的。
