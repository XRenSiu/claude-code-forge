# AC v2 形状与"形容词 → 阈值"

## 形状（以 AC 为单位，测试名不进来）

```yaml
- id: AC-<req>-<letter>       # 稳定 ID：G2 锁它、隐藏集是它的变体、review 引用它
  req: REQ-NNN                # 每条 AC 挂一个 REQ；REQ 全覆盖由脚本查
  kind: mechanical | human
  # mechanical（可降解 → A 档一票否决）
  observe: route:POST /x | cli:sub-cmd | ui:data-test=… | db_field:table.col | event:name
  given: { … }                # 数据，不是代码
  expect: { … }               # 可观测结果 + 阈值；不是"应正确处理"
  ears_type: event | state | unwanted | ubiquitous | optional
  paired_with: AC-…           # happy ↔ unhappy 互指
  # human（不可降解 → C 档，指定裁决人）
  statement: <一句可被人判真假的话>
  judge: product | design | tech
  evidence: checklist | demo
```

- 期望值是**数据不是代码**——driver 只能读它。`test_cancel_is_idempotent` 这种名字属于 tests-manifest。
- `existence` 只留观察边界（route / db_field / ui / cli）。文件、函数级存在性由任务卡的"可改文件"承担。
- human AC 占比可以从这份文件直接算出（喂 X3）；持续过半说明该需求不该走流水线。

## 形容词 → 阈值

| 日常语 | 阈值形态 | 来源必须是 |
|---|---|---|
| 快 / 及时 | `p95_latency_ms: "<= 300"` | SLO / KPI / 一次真实超时 |
| 稳定 / 可靠 | `error_rate: "< 0.1% over 1000 req"` | SLO / 事故复盘 |
| 大部分 / 多数 | `ratio: ">= 0.9"` | 产品度量 |
| 友好 / 自然 | 不是阈值 → `kind: human` + judge + evidence | — |

没有来源 → `threshold_source: needs_threshold_source` 并向用户问，不编。

## happy / unhappy 孪生

每条 `ears_type: event|state` 的 AC 配一条 `unwanted`：边界（空、超长、并发）、恶意（注入、越权）、
失败（下游超时、数据缺失）。裁决偏向：**宁可多写 unhappy，也不留隐式。**

## 反模式

- "系统应智能理解用户意图" —— 入口散文，不是产物检验。
- `observe: src/search/time.ts` —— 契约规定了实现结构。
- `expect: 正确返回` —— 不可证伪。
- 只有 happy，没有 unhappy —— 失败语义未定义，正是被钻的缝。
