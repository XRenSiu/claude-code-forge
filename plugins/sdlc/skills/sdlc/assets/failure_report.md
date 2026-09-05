# 失败报告 — <slug> · <stage>

> 路由的前提是归因器。本报告由引擎按 routing.yaml 的启发式生成候选层与证据，人只做确认或改判。
> 它是 G3 的输入——人不看原始日志。

**信号**: `<signal>`　**指纹**: `<fingerprint>`　**层计数**: card=<n> plan=<n> task=<n> ontology=<n> world=<n>

## 当前状态

<一段：卡 / PR / 测试 / checks 的现状>

## 候选归因层

- **层**: <card | plan | task | ontology | world>
- **依据**: routing.yaml `<rule id>` — <规则描述>
- **证据**: <最小反例 / 失败输出 / diff 片段 / 引用的 DOS 不变量或 PSL 规律>

## 已排除的可能

- <层 X>：<为什么不是>

## 建议回退目标

- <重试卡 CARD-xx | 改卡 | 改 REQ-xxx / AC-xxx（附变更提案）| 对账 dos.yaml | 重开 G1>

## 请人确认

- [ ] 确认候选层　- [ ] 改判为: <层>，理由: <…>
