# invariant-extract · decisions.md（审计轨）— Territory `ai-dlc-plugin`

> 这把刀是起草书记员，不是立法者——本文件是它向立法者交代"为什么这么草"的账本。
> 产物：`ai-dlc-plugin.card.yaml`（同目录）。**硬不变量一律 propose-only**：它们进
> `Territory.invariants` 要走 G2（`change_proposal.md` + 人签），这份卡不安装任何东西。

2026-09-05 的首轮抽取（绑定、取景框、通道一的 274 个执行点、19 条去重、8 硬 5 默认 16 ◊）
**不在这里重复**，它在 `../dogfood/ring-audit/invariants/decisions.md`（199 行），除改名外仍然成立。
本文件记 0.2.0 修订加了什么。

## 为什么这份卡搬出了 `dogfood/ring-audit/`

和本体同一个理由：常驻不变量是**这块领地的法**，不是产出它那一次 Run 的记录。埋在某次 dogfood
的目录里，`repo_assets.py` 发现不了，`/spec-compile` 也就拿不到它编 property 测试——一份没人能
发现的法等于没有。搬到 `plugins/ai-dlc/invariants/`（进 git），不是仓库根：这是 monorepo，
领地边界是 package。

## 通道二输入的一处订正（对上一轮的判断，不是对代码的）

首轮把 `eval/gate.json` 的 **52 条 fix_list 算进了 failure.memory**（84 条里的大头）。这是错的，
而且 skill 的接线段现在写得很明白：**登记的缺口不是违反**——它说的是"还没做"，不是"做错了"。
取反一件从没做过的事得不到 □，只得到一句"应该去做"，那是 ◊。

已挪进卡的 `registered_gaps`（`destination` 必填）。`failure_memory_count` 因此从 84 落到
**29**，而且现在是从 `sources[].entries` 求和出来的——上一轮那个 84 谁也重算不出来。
数字变小不是退步，是上一轮那个数虚高。

## 本轮的两条新失败记忆，与它们的溯因

**F-A — X1 在每份文档里都被声明为横切阶段，在代码里一处都没有。**
`ORDER` 没有它，`prereqs()` 一个分支不提，`doctor` 只查工具链。三个消费者静默降级，而三种降级
在输出里都长得像通过（flag / info / exit 3）。

按取景框（correctness）投影后取反，得到的最直接那条是"**算不出来的检查不许长得像通过**"——
但它**已经是宪法**：同日写进 `dos.yaml` 的 R018。按纪律不重新立法，记进 `deduped_against_constitution`。

R018 覆盖不到的**残差**才是领地级的那条：三个 unevaluated 分支**在代码里全都存在、也都记录正确**，
DEF-003 也可以说被满足了（"编译成了一个 flag"），失败仍然发生——因为**没有任何 fixture 走过
"输入缺失"那条路**。五天的绿色 smoke 对它们一个字都没说。这就是 `INV-ai-dlc-plugin-009`：
一条没被 fixture 走过的 unevaluated 分支，和一条不存在的分支无法区分。

范围刻意收窄到 verifier，而不是"所有分支都要有覆盖"——障碍出现在哪个面上，规则就只覆到哪个面。

**F-B — 一个预门的 reject 文案指向一条没人读的豁免。**
`verify_dos.py:171-172` 一直写着"exceed only with a human waiver in decisions.md"，而没有任何代码
解析这样一条豁免。唯一的出路是忽略一个永远红的预门——而一个只能靠忽略才能过的门不是门，
是在训练人跳过红色。当天用已有的 `## Naming waivers` 解析器修好（`object_count`）。

这**不是** DEF-003（文档 → 强制）。面不一样，也更窄：**reject 文案本身**指出一条杠杆，而文案是被
挡住的人读的最后一样东西。而且它可机械化——grep reject 串里的 waiver / `--flag` 名字，断言那个
flag 真的能解析。没有推广成"脚本里每句话都得为真"，那种规则没有 fixture 能守。→ `INV-ai-dlc-plugin-010`。

## DEF-003 收到一次实测违反（这一条比两条新卡更重要）

F-A 不是新不变量，**它是 DEF-ai-dlc-plugin-003 存在却没挡住的一次违反**：X1 在 `SKILL.md` 的 Σ 表
与 `lifecycle.md` 里被声明为强制，既没被编译，也没标 `declarative (not compiled)`，五天无人发现。

它以 `corroboration` 记在那条默认上，`confidence` 提到 high，并进了
`constitution_promotion_suspects`——但**单领地的一次运行只能怀疑，不能晋升**（要 `--cross-territory`
加立法者签字）。现在它有两次独立障碍（2026-09-05 的 I-nn 与今天的 F-A/F-B），够进批量提案，
不够自己升。

## 本轮**没做**的

- **没有重新审视首轮那 8 硬 5 默认**。它们照原样带过来，只改了名字与路径。若其中有一条错了，
  这一轮抓不到。
- **五条 DEF 仍然没有 `narrowest_rule_note`**，`verify_card.py` 逐条标了 `needs_semantic_review`。
  首轮就缺，本轮没补——补它要重走一遍每条的"最窄规则在正确的面上"判断，那是一次完整的判据复审，
  不是修订能顺手做的事。**留在报告里而不是悄悄清掉**：一条被标记的判断至少还在等人看。
- **没有跑 `--cross-territory`**。只有一块领地抽过，凑不出批量提案需要的 ≥2。
