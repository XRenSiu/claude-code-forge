# calibrate — 决策审计轨迹（per 标准）

> 每条非平凡校准判断都落这里：为什么这个 mutation 阈值、为什么这组参考解、holdout 怎么切、隔离怎么证。
> 与校准报告同生命周期；`--auto` 模式下这里是人事后审计的唯一通道。

## 本次校准

- 标准：eval_case 集 id / rubric_version id
- kind：eval_case | rubric
- 来源 compile manifest：
- 模式：interactive | auto
- 校准时间：

## 镜面①（mutation，kind=eval_case）

| 项 | 值 |
|---|---|
| 工具 / 总 mutant / 杀死 |  |
| mutation_score（阈值 ≥0.7） |  |
| 纳入的 failure_memory 天然 mutant |  |

存活 mutant 落账（逐个，no silent caps）：

| mutant | 溜过哪 | 待补 eval_case |
|---|---|---|

## 镜面②（agreement，kind=rubric）

| 项 | 值 |
|---|---|
| 参考解数（≥ min_cases） |  |
| Krippendorff α（硬线 ≥0.80） |  |
| 拉低 α 的维度 / 丢弃的 rubric 集（CDRRM） |  |

## 两条非协商项

- holdout：怎么切的 / holdout_ref / 人确认未泄漏？
- 隔离：独立进程？只读快照？输入只含产出+rubric？cross-vendor（若领地开）？

## 元闸门 verdict

- 四判据：☐1 ☐2 ☐3 ☐4 各 pass？
- result：pass / fail
- 若 fail：gap 退回（spec-compile 重编哪些 / spec 作者收紧哪些）
- 若 pass 且 kind=rubric：人签事件引用（R002）
