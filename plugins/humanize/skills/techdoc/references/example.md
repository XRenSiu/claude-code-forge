# 完整推导示例：brief → 方案 → 三道闸门

> 本文件是示例，不是 PSL/方案本体；不要把它整个丢给 verify_techdoc.py（示例正文在引用块里，解析器看不到）。
> 对照的是**形状**，不是内容——别把这里的数字抄进别的系统。

## 输入

**brief**（用户原话）：

> 大促时订单查询接口扛不住，DB 连接池打满，想加缓存。写个方案，给架构组评审。

**materials**：`slow-query-2026-08-27.log` 摘要（92% 读请求集中在 5% 订单；这些订单一小时内状态基本不变）；
压测记录（单 Redis 集群 30 万 QPS 时网络往返 2ms）。

**推断值**：genre = proposal（"方案""评审"）；reader = 架构组评审；lang = zh。

## 提问（攒成一条，附推荐答案）

> 写之前确认三个承重事实，直接回字母即可：
> 1. 那次打满是哪天、P99 到了多少？ A) 上周三，1.4s（日志里看到的） B) 其他：___
> 2. 目标定多少？ A) 大促当天 P99 ≤ 150ms，DB 读 QPS 砍一半 B) 只要不打满就行 C) 其他
> 3. 这次只做 `GET /orders/{id}` 还是所有订单读接口？ A) 只做这一个（占 92% 读量） B) 全部

用户答：1A 2A 3A。（用户不在场时：三处全部 `[需核实]`，照常交付。）

## 主张句骨架（先于散文；每段一句，顺序即产物序）

1. 上周三大促预热 P99 80ms → 1.4s，连接池打满两次，92% 读集中在 5% 订单。
2. 我建议给 `GET /orders/{id}` 加缓存，先只做这一个接口；目标 P99 ≤ 150ms、DB 读砍半。
3. 怎么做：Caffeine 5 万条 / 60 秒 + Redis 兜底；状态变更事务提交后删 key，不用 MQ。
4. 没选只用 Redis（往返 2ms 对热单是主要开销）；没选 write-through（改动面三倍）。
5. 最担心：一致性（60 秒旧状态，支付回调绕过缓存）；雪崩（±10 秒抖动 + Redis 5 分钟兜底）。
6. 排期两天，周四灰度 10%，回滚是配置开关。
7. 没想清楚：客服后台改单不经过订单服务，缓存删不掉；先查量。

骨架通过自检：第 1 句有事件与数字；第 2 句是决定；第 4 句杀替代；第 5 句风险有兜底；第 7 句是未决点。

## 展开后的方案

见 `../../humanize/fixtures/human-zh.md`（624 字）。这里只放开头两段示意：

> # 订单查询加一层缓存
>
> 上周三大促预热，订单查询接口 P99 从平时的 80ms 涨到 1.4s，DB 连接池打满两次，每次持续三四分钟。事后看慢查询日志，92% 的读请求集中在 5% 的订单上，都是用户在支付页反复刷新自己那一单。这些数据一小时内基本不会变。
>
> 所以我建议给 `GET /orders/{id}` 加一层缓存，先只做这一个接口。目标很单一：大促当天这个接口 P99 压回 150ms 以内，DB 读 QPS 砍掉一半以上。

## 三道闸门的输出

**verify_techdoc**

```
verify_techdoc · genre=proposal · 8 段 · verdict = PASS
  形状齐全。方案对不对，脚本不判。
```

**humanlint**（改前 = 引擎默认稿 `fixtures/ai-zh.md`；改后 = 本方案）

```
ai-zh.md    AI 味指数 65/100 · FLAG   （套话 33/1k、路标句首 56%、0 个锚点、总结式收尾）
human-zh.md AI 味指数  2/100 · WARN   （仅 paragraph_len_cv 弱信号）
```

**factdiff**（source = brief + materials + 用户回答的合并文件）

```
factdiff · verdict = PASS
  [hard] number  source 9 → rewrite 14   ADDED: 10 秒, 5 分钟, 200 行, 10%, 100 次
```

五个 ADDED 逐一有来路：`10 秒` `5 分钟`（过期抖动与兜底，标为建议值）、`200 行` `10%`（作者估算，方案里写明"大约"）、
`100 次`（未决问题里的判断阈值，明确是"如果"）。都不是系统事实，不需要 `[需核实]`。若 ADDED 里出现"当前 QPS 30 万"这种
来源没有的系统数据，就必须改成 `[需核实]`。

**cold-reader round 1**（隔离调用，只给方案 + reader + genre）

```yaml
verdict: pass
one_sentence: "给订单查询接口加本地+Redis 两级缓存，两天上线，我来评审一致性与回滚"
decision_at_paragraph: 2
flags: []
paragraphs:
  - {n: 1, expected: "读完标题以为会先看到为什么要加", got: "上周三的事故与读请求分布", lost_at: null, told_not_shown: [], new_first: false}
  - {n: 2, expected: "打算怎么办", got: "只给一个接口加缓存，目标两个数字", lost_at: null, told_not_shown: [], new_first: false}
  - {n: 5, expected: "风险", got: "一致性的最坏情况与绕过路径", lost_at: null, told_not_shown: [], hedged_claim: false}
worst_three: []
```

## 对照：同一个 brief 的引擎默认稿哪里错了

`fixtures/ai-zh.md` 的 cold-reader 第一轮：

```yaml
verdict: needs_revision
one_sentence: null            # 读完不知道要我做什么
decision_at_paragraph: null
flags: [decision_buried, generic_opening, no_alternatives_killed]
paragraphs:
  - {n: 1, expected: "触发这份方案的问题", got: "行业背景与缓存的重要性", lost_at: "值得注意的是，缓存作为", told_not_shown: ["行之有效", "至关重要的角色"], new_first: true}
  - {n: 2, expected: "问题是什么", got: "四条加粗目标，无数字", lost_at: null, told_not_shown: ["显著降低", "有效减少", "提高容错"], list_replaces_argument: true}
  - {n: 4, expected: "为什么这样设计", got: "四条关键技术点，项间实为前提关系", list_replaces_argument: true}
  - {n: 6, expected: "具体风险", got: "'可能面临一定的风险'", hedged_claim: true}
worst_three:
  - {n: 1, why: "两段没有任何事实，读者到第 3 段还不知道要解决什么"}
  - {n: 4, why: "四条并列 bullet，2 是 1 的前提、4 是 3 的对策，读者自己猜"}
  - {n: 6, why: "风险是套话，作者自己信不信都看不出来"}
```

这三条 worst_three 分别对应 `discourse.md` 的 §8 套路化开头、§4 列表替代论证、§5 立场扁平。修法不是换词，是补内容
（第 1 段需要日志里的数字，第 4 段需要把前提关系写成句子，第 6 段需要最坏情况与兜底）。
