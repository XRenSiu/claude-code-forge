# 分歧集 — memory-time-search（第二轮，定向重推）

n: 1
round: 2
consistent_decisions: 6

> **未做分歧检验**。第一轮（n: 3，见 `round1/divergence.md`）的 D-1 已由 G1 裁定；本轮输入 =
> 同一 PSL + G1 裁决，n=1 定向重推合法。第二轮起分歧表由下面的「裁决 → 落点」表替代。

## G1 裁决 → 落点

| # | G1 ruling | applied in | note |
|---|---|---|---|
| 1 | D-1 重叠阈值取 2 | F-20 | PSL-008 仍是 Open Question，阈值先按 2 落地 |

## PSL 欠定

- `Scene` — 第一轮 v2 提出；G1 裁：留 open_questions，暂不进 Domain Model
