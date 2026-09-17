# 形状：完备相对什么而言

"问问题的能力要完备"没有绝对意义——任何方法都数不到未知的未知。能做到的是**相对一个声明的形状完备**，
再用两道后手抓形状之外的漏洞。这一页把形状写成槽清单，每个槽对应一个数它的脚本。

## 一、世界层：PSL 六层的承重槽

承重槽 = 取值会改变产品形态、或翻转某条验收结果的槽。不承重的私有槽直接 seam，不打扰人。

| 层 | 典型承重槽 | 空着时的症状 | 数它的脚本 |
|---|---|---|---|
| Vision | 根命题（能推翻朴素实现的那一句） | 形态草案与 PRD 字面实现无差别 | `verify_psl.py`（层缺 / 空壳拒） |
| Mental Model | 用户以为世界怎么运转的关键事实 | "技术正确、产品错误"（日历筛选器） | 同上；分歧集里 v1/v2/v3 在交互上三种界面 |
| Domain Model | 能推翻朴素表的实体与关系 | dos-proposal 与 `memories(created_at)` 同构 | `verify_psl.py`；`verify_derived.py` 的"不造实体" |
| State Machine | 合法终态（含"歧义"这类非错误终态） | 实现把 ambiguous 当 error | 分歧集 |
| Workflow φ | 消歧判据、"对"的样子 | 推导者各自即兴 | `verify_derived.py`（含谓词的决策要走查例） |
| Acceptance | 问 X → 返回 Y | 验收写成"智能理解" | `verify_psl.py`（无 → 拒） |
| Personas / JTBD | 意图词表 → 元素映射 | 最常被漏的一层 | 分歧集 |

`grill_loop.py pending` 从 Open Questions 抽 Q-n：PSL 作者（--afk 下是引擎）把填不上的承重槽落在这里，
每条带"为什么需要人来定"。

## 二、词表层：DOS 闭包

需求 / PSL / issue 文本里出现 `dos.yaml` 解析不了的名词，就是一道必问题（这个词在这个系统里是什么？
是已有对象的同义词，还是新实体？）。

```
python3 <plugin>/skills/dos-extract/scripts/verify_vocabulary.py --dos dos.yaml PSL-<name>.md --artifact-kind markdown
```

exit 3 = 没有本体、**未检**（不是通过）。没有 dos.yaml 的仓库先 `/dos-extract` 一次，那是仓库级、一次性的。

## 三、验收层：孪生与阈值

每条 happy 路径配 unhappy 孪生；每个形容词（快 / 稳定 / 大部分）配有来源的阈值。`verify_issue.py` /
`verify_done_when.py` 拒不合的。TASK 轨没有 PSL，同样的分歧机制用 `donewhen-extract/scripts/divergence.py`
对 N 份隔离的 done_when 草案做（`only_in_some / expect_differs / threshold_differs / kind_differs / twin_asymmetry`）。

## 形状之外的两道后手

1. **分歧集**：同一份 PSL 隔离推导 N 次，读者不一致处 = 形状没管住的欠定。`grill_loop.py pending` 把 D-行
   与「PSL 欠定」抽成 D-n / U-n。分歧率 > 0.5 不是"多投几票"，是"PSL 太弱"。
2. **逃逸缺陷**：上线后发现的问题 `aidlc_state.py escape --layer world` 登记，`/retro` 数它；下一次形状就多
   一个槽。这两道不假装完备，只把不完备变成可发现的。

## 顺序

按六层推导序走：上一层是下一层的定律。看起来像 BFS，但停机条件来自上面的槽清单与分歧率，不来自遍历。
