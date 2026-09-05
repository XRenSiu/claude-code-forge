# 失败报告 — <slug> · <stage>

> 路由的前提是归因器。本报告由引擎按 routing.yaml 的启发式生成候选层与证据，人只做确认或改判。
> 它是 G3 的输入——人不看原始日志。写完后 `sdlc_state.py report --path <本文件>` 清掉 pending.failure_report。

**信号**: `<signal>`　**指纹**: `<fingerprint>`　**层计数**: card=<n> plan=<n> task=<n> ontology=<n> world=<n>

## 当前状态

<一段：卡 / PR / 测试 / checks 的现状>

## 收敛证据（fail 命令的 convergence 字段原样粘贴）

- **判定类型**: <repeat | oscillation(period p) | plateau(stale n) | budget | impossible | handler=human>
- **指纹历史**（新在右）: `<fp1> <fp2> <fp3> …`
- **score 序列**（有则填）: `<s1> <s2> <s3> …`　best=<x> stale=<n>
- 震荡 = 在两三个解之间往复，方案层无法解决一个权衡；平台 = 三个信号都稳但产物差，需要换方案不是再迭代；
  两者都**不是**"再试一次"的理由。

## 候选归因层

- **层**: <card | plan | task | ontology | world>
- **依据**: routing.yaml `<rule id>` — <规则描述>
- **证据**: <最小反例 / 失败输出 / diff 片段 / 引用的 DOS 不变量或 PSL 规律>

## 已排除的可能（`trace.py why <target>` 的因果链可预填此段）

- <层 X>：<为什么不是>

## 建议回退目标

- <重试卡 CARD-xx | 改卡 | 探索性重写一次 | 改 REQ-xxx / AC-xxx（附变更提案）| 对账 dos.yaml | 重开 G1>

## 请人确认

- [ ] 确认候选层　- [ ] 改判为: <层>，理由: <…>
