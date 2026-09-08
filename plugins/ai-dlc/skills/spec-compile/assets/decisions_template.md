# spec-compile — 决策审计轨迹（per 规约）

> 每条非平凡路由判断都落这里：为什么判这条可判性、为什么落这条线、为什么这组属性、为什么这维要上 G2。
> 与编译清单同生命周期；`--auto` 模式下这里是人事后审计的唯一通道。

## 本次编译

- 源规约：R00x id / done_when 卡 / contract id
- 源层级（标注）：responsibility(常驻不变量) / task(本次验收)
- 模式：interactive | auto
- 编译时间：

## 可判性裁断（决定产线）

| 源条目 | decidability | 落线 | "能不能再往下推一格" 的理由 |
|---|---|---|---|
|  | structural/behavioral/judgment | ①/②/③ |  |

## 产线① fitness function（原则先于工具）

| 条目 | 保/禁什么（溯到规则） | 选的工具 | 容差（棘轮值） |
|---|---|---|---|
|  |  |  |  |

## 产线② eval_case（三型 + 三过滤）

| 条目 | 例子数 | 属性 | 变形 | 若只例子的理由 | ACH mutant 族 |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## 产线③ judge program（PAJAMA）

| 维度 | 二元？ | 证据绑定 | 编译成的 probe |
|---|---|---|---|
|  |  |  |  |

- R001 隔离自检：独立进程？只读快照？输入只含产出+rubric？cross-vendor（若领地开）？

## 退回与交接

- 退回上游（不可编译）：条目 / 理由 / 退给 donewhen-extract | invariant-extract
- 交给 calibrate：eval_case 集 / rubric 版本（均 calibration_pending）
