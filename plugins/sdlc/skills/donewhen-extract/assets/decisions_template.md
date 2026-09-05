# donewhen-extract — 决策审计轨迹（per Issue）

> 每条非平凡判断都落这里：为什么这条阈值、为什么这样配 unhappy、为什么把某候选踢给 invariant-extract。
> 与 done_when 卡同生命周期；`--auto` 模式下这里是人事后审计的唯一通道。

## 本次提取

- Issue / Signal：
- Territory：
- 模式：interactive | auto
- risk_class：
- 提取时间：

## 分层裁断（本次验收 vs 常驻不变量）

| 候选 | 判 本次验收 / 常驻不变量 | 理由（能否活过未来不相关 Run） | 去向 |
|---|---|---|---|
|  |  |  | 留卡 / 踢 invariant-extract |

## 阈值来源（纪律①）

| 条款 REQ-ID | 原形容词 | 换成的阈值 | 来源（kpi/slo/failure_memory/待定） |
|---|---|---|---|
|  |  |  |  |

## happy/unhappy 配对（纪律②）

| happy REQ-ID | unhappy REQ-ID | 覆盖的边界类型 |
|---|---|---|
|  |  | 空/超长/越权/并发/重复/恶意 |

## 出口两检（纪律③）

- 矛盾检查：机械 pass？ 疑似对：  解除依据：
- 覆盖检查：机械 pass？ 缺场景：  显式不覆盖（及理由）：

## 签约处置

- disposition：draft（随合同签约）/ propose（高风险或改模板 → 立法收件箱，NEEDS_HUMAN）
- 若 propose：触发原因（risk_class=high / 改模板 / 阈值无根）：
