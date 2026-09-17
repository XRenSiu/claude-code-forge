---
name: grill
description: >-
  补引擎自己给不出的缺口：把"逐节点陪 Agent 对齐需求"（grill-me 的 BFS）和"让 Agent 自己 grill 到它
  觉得对齐"（AFK 环）都换成一个停机不靠自评的对齐环——问题集来自形状（PSL 六层的承重槽 · DOS 词表
  闭包 · AC 的 happy/unhappy 孪生），不是 Agent 临时想到的树；通过条件来自 N 个隔离读者的分歧率与一份
  逐条有来路的待定清单，不是"我觉得清楚了"；每条槽只能以三种方式离开清单（物料来路可核对 / 人答 / 明确
  留给人），默认值被脚本硬拒。效果：一句需求 → `/psl --afk` 无人值守建世界 → `/psl-derive --n 3` 分歧集 →
  `grill_loop.py pending` 抽清单 → 机器先回仓库找来路、找不到才 defer → 人只裁 needs_human 行 →
  拿答案重推一轮 → converged 进 G1。Use when: "自动 grill" / "AFK 对齐需求" / "grill 这个需求但别一个个问我" /
  "先把能从代码里答的答了再来问我" / "align the requirement unattended" / "run the grill loop"。
  NOT for: 交互式逐题逼问（用 grill-me 类技能）、确定性需求（PRD 够用，双轨判据在 /issue 入口拦）、
  写 PSL 本身（/psl）、推导本身（/psl-derive）。前置：python3 + pyyaml；仓库里最好有 dos.yaml /
  decisions.md（没有时来路只能来自代码与文档，清单会长，这是诚实不是失败）。
argument-hint: "<需求一句话 | PSL 路径> [--n 3] [--max-rounds 4] [--max-divergence 0.20] [--material-root DIR]... [--out DIR]"
version: 0.1.0
user-invocable: true
---

# grill — 对齐环：问题集来自形状，停机来自分歧，默认值进不来

本文件只写引擎给不出的东西：为什么"Agent 觉得对齐了"不能当停机条件、完备是相对什么形状而言的、
四键停机怎么由脚本判、每条槽的三条合法出路。**推几次、先查哪份物料、怎么写 PSL 是你（引擎）的份额。**

## 缺口（Judgment + Control）

deletion 测试：撤掉本 skill，让引擎"AFK 把这个需求 grill 到对齐"。它会自问自答几轮，用仓库里能找到的
和找不到的（默认值）把 PSL 填满，然后说"已对齐"——一份看起来完整的文档比一份到处是空槽的文档更危险，
因为人对着它会签字（cognitive surrender）。三处缺口：

- **φ**：停机判据。Ambig-SWE（ICLR 2026）：模型分不清一个任务写清楚了没有。"引擎觉得对齐了"不是证据；
  "N 个隔离读者读出同一套判断"才是。`divergence.md` 的分歧率与 `pending.yaml` 的计数是可核对的量。
- **γ**：槽的出路。物料来路必须能打开（`grill_loop.py resolve --from materials` 找不到文件即拒）；
  `--from default` 被硬拒；留给人的每一条必须写"为什么需要人来定"。
- **Σ**：完备相对什么形状。BFS 只保证"长出来的节点都走到了"，不保证"该长的都长出来了"。形状给
  槽一个有限的、可数的集合（下表），完备 = 每个承重槽不处于"未填、未问、未 seam"三无状态。

## 世界（Σ）：完备相对哪个形状

| 完备的范围 | 槽从哪来 | 谁数 | 形状之外的漏洞由谁抓 |
|---|---|---|---|
| 世界层 | PSL 六层的承重槽（取值会改产品形态或翻转某条验收） | `verify_psl.py`（缺层 / 无 Open Questions 拒；`--afk` 再拒无来路与无 why） | 分歧集：N 次隔离推导读出不一样 = 形状没管住的欠定 |
| 词表层 | `dos.yaml` 里的对象与关系 | `verify_vocabulary.py --dos`（需求文本里本体解析不了的名词 = 一道必问题） | 逃逸缺陷回流（`aidlc_state.py escape --layer world`）下次形状多一个槽 |
| 验收层 | 每条 happy 配 unhappy、每个形容词配阈值 | `verify_issue.py` / `verify_done_when.py`；TASK 轨的 `divergence.py` | 同上 |

BFS 与 AFK 不是同一维度上的两个选项：BFS 说顺序，AFK 说谁答。顺序按 PSL 六层的推导序走（上一层是
下一层的定律），样子上像 BFS，但停机来自形状与分歧，不来自遍历。AFK 只决定每个槽由谁填：有人在场问人
（elicit）；无人在场，能从代码 / 文档里找到的填上并注明来路（surface），找不到的标待定（seam）。两种模式
的停机判据一样，产物形状一样，区别只是待定清单的长短。

**关于用户的 Σ。** "自动 grill 一下" = 跑机器份额到 `check` 说 human 或 converged 为止，然后把
`pending.yaml` 的 needs_human 行拿给用户，**不是把 PSL 全文拿给用户通读**。"别问我了直接写" = 全部 defer，
清单会长，照常交付。"你觉得清楚了就行" ≠ 跳过分歧检验——那正是这个环存在的理由。

## 判据（φ）：四键停机，由 `grill_loop.py check` 判

| 键 | 条件 | 退出码 | 之后 |
|---|---|---|---|
| success | open = 0 ∧ needs_human = 0 ∧ 本轮 resolve 都已重推 ∧ 分歧率 ≤ `--max-divergence`（缺省 0.20） | 0 `converged` | 进 G1：`pending.yaml` + `grill-ledger.md` 附进 `g1-record.md` |
| （机器份额做完） | open = 0 ∧ needs_human > 0 | 10 `human` | 把 needs_human 行交人；人答后 `resolve --from human --by` → 补 PSL → 重推一轮 → `pending` |
| convergence | open 数连续 `--plateau`（缺省 2）轮不降 | 1 `plateau` | 机器找不到来路了：全部 defer，交人 |
| budget | 轮数 > `--max-rounds`（缺省 4） | 1 `budget` | 写失败报告，交人 |
| impossible | 分歧率 > 0.5 | 1 `impossible` | PSL 约束太弱：回 `/psl` 补 Mental Model / Domain Model，**不用多数表决糊过去** |
| （继续） | 还有 open 项，或本轮有 resolve 尚未重推，或 divergence.md 变了但清单没重抽 | 20 `continue` | 见 reasons |

"本轮 resolve 都已重推"是环的一部分：一条槽用物料或人的答案填上之后，形状可能又长出新槽、分歧可能移动，
不重推就没人知道。`resolve` 记 `resolved_in_round`，`pending` 见到新的 divergence.md 就 round +1，
`check` 据此判。

## 门（γ）

- **槽的三条出路，没有第四条**：`resolve --from materials --provenance "<文件> §N"`（文件必须在
  `--material-root` 下找得到，否则 exit 1）· `resolve --from human --by <人>` · `defer --why "…"`。
  `--from default` 直接拒：默认值糊上的槽比空着的槽更危险。
- **交人的只有 needs_human 行**。人看的是议程（每行带 why_human），不是 PSL 全文。这是对
  cognitive surrender 的正面回答，也是这个环比"事后通读 PRD 再剪枝"省的那部分。
- **`--afk` 的 PSL 多两条 reject**：不得出现 `[elicit:用户 …]` 来路；Open Questions 每条要写为什么需要人来定
  （`verify_psl.py --afk`）。
- **G1 不能跳**。converged 只说明清单空了、读者一致了，不说明世界对——G1 三问仍由人签。
- **generator ≠ verifier**：填槽的是 `/psl`（--afk 与定向重推），判的是 `/psl-derive` 的 N 次隔离推导
  加本脚本的计数。填槽者不评自己（`loops.yaml#grill`，`verify_loop.py` 核）。

## 原语（Π）

- `scripts/grill_loop.py pending <PSL.md> [--derived DIR] [--out DIR] [--material-root DIR]...` —— 从 PSL Open
  Questions（Q-n）、`divergence.md` 的 D-行（D-n）与「PSL 欠定」（U-n）抽 `pending.yaml`；可重复运行，
  同一条槽按来源 + 归一化文本对齐并保留状态；divergence.md 变了即 round +1；写 `grill-ledger.md`（只增）。
- `scripts/grill_loop.py resolve <DIR> <ITEM> --from materials|human …` / `defer <DIR> <ITEM> --why …` —— 三条出路。
- `scripts/grill_loop.py check <DIR> [--record] [--max-divergence 0.20] [--max-rounds 4] [--plateau 2] [--json]`
  —— 四键停机；`--record` 把本轮计数写进 `rounds.jsonl`（plateau 的记忆）。
- `../psl/scripts/verify_psl.py --afk`、`../psl-derive/scripts/verify_derived.py --round n`（每轮重推的归档与
  round-diff 纪律，见 psl-derive 的「分歧回流」段）、`../dos-extract/scripts/verify_vocabulary.py --dos`（词表层的必问题）。
- `assets/pending_template.yaml`（清单形状）· `references/shape.md`（三层形状的槽清单与对应脚本）。
- 隔离：N 次推导用 Agent 工具各开全新上下文（只给 PSL 路径 + 模板，不给前一次结果，不给 pending.yaml）；
  找来路的那一步可以在主会话做，但**找到的来路必须写进 PSL 正文**（`[elicit:物料 <文件> §N]`），不只写进清单。

## 失败机制

- `check` = impossible → 回 `/psl`：这是世界层信号（`counterexample_cites_psl_rule` 的近亲），不再自动转。
- `check` = plateau / budget → 剩余 open 全部 `defer --why "机器在 <找过的物料> 里没找到来路"`，交人；账本里
  有每一轮找了什么。
- `resolve --from materials` 被拒（文件找不到）→ 不是"换个说法再试"，是这条槽没有来路：defer。
- 人答完不重推就想进 G1 → `check` 判 continue（unrederived 非空），G1 的 `--record` 里没有 converged 的 check 输出
  就是没走完。
- `verify_psl.py --afk` 拒 → 回去补 why / 改来路，不在清单层面补救。

## 高危黑名单（不可豁免）

- **绝不用 `--from default` 或任何等价物关闭一条槽**——写进正文的默认值就是这个东西换了个名字。
- **绝不把 PSL 全文当作交给人的东西**——交的是 needs_human 行。
- **绝不用多数表决消灭分歧**——分歧率 > 0.5 是"PSL 太弱"的信号，不是投票现场。
- **绝不跳过重推就宣布 converged**。
- **绝不跳过 G1**。
- **绝不在 --afk 下写 `[elicit:用户 …]`**。

## 接线（在 AI-DLC 里的位置）

PSL 轨、`/psl` 之后、G1 之前，可选。`loops.yaml#grill`（level verification · generator psl · verifier psl-derive ·
stop 四键）；`triggers.yaml` 绑到 `/goal`；`graph.yaml` 里 `psl-derive → grill → psl` 是 `loop_back`，
`grill → human.g1` 是 `interrupt`。运行时产物放 `.aidlc/<slug>/grill/`（`aidlc_state.py loops` 读 `rounds.jsonl`
报预算消耗）；单独使用时放 `./grill/`。converged 之后 `aidlc_state.py gate g1 --record` 的记录里附
`pending.yaml` 与最后一次 `check --json` 的输出。TASK 轨没有 PSL：同样的环用 `donewhen-extract/scripts/divergence.py`
的分歧集当输入（`pending` 只吃 divergence.md 的 D-行与欠定段，`--derived` 指向放它的目录）。

环境里有 `grill-me` 类交互技能时：它是人在场那一段（needs_human 行）的一种问法，不是这个环的替代。

## 本 skill 自身的出口门

`eval/gate.json`：`static_only`——`grill_loop.py` 在 fixtures 上冒烟（清单三来源各抽到；default 被拒；
假来路被拒；未重推不 converged；needs_human 交人；分歧率 > 0.5 判 impossible；plateau 判停），
`verify_psl.py --afk` 的两条 reject 各有 twin。行为层（一次真实需求 + 一次真实 G1，对比"人逐题 grill"的
分歧率与人的用时）未跑。
