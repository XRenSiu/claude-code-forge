---
name: tune
description: >-
  补引擎自己给不出的缺口：把六个环留下的 trace（归档的 state / ledger / trace.jsonl、review-loop 的证据日志与
  计数器、ratchet 的 results.tsv）读成"每个环的预算用了几成、哪条路由规则最常升级、review 的 verdict 分布是不是
  一边倒"，并把每条发现变成一条**只改 harness 参数**的提案——routing 预算 / 指纹阈值 / MAX_ROUNDS / 隔离等级 /
  某 skill 的 fix_list——带证据、预期指标变化、验收方式，产出 diff 或 patch 由人开 PR。它是 LangChain 四层里的
  Hill-Climbing Loop："返回箭头伸进去改 agent loop 本身"，但改动先过人审。效果：归档目录进，
  `tune/harness-proposals-<date>.yaml` + 可 `git apply` 的 patch 出；归档 < 2 个只出基线。Use when: "调一下预算" /
  "review 是不是太顺了" / "tune" / "这些环的参数该改吗" / "harness 调参" / 每周 cron / retro 之后。NOT for:
  改契约或世界（/retro 的提案去向）、改代码（/implement）、改 skill 正文（skill-evolve 邻居）、单次 bug 根因。
  前置：`specs/*/` ≥ 2 个归档（少于 2 个只记基线）。
argument-hint: "<archive_root> [--pr-watch .aidlc/pr-watch] [--ratchet-logs DIR] [--out tune/harness-proposals-<date>.yaml] [--min-features 2]"
version: 0.3.1
user-invocable: true
---

# tune — 环改环的外环，改动永不自动生效

产物：`tune/harness-proposals-<date>.yaml`（形状 `assets/harness_proposals_template.yaml`）与可选的 `tune/*.patch`。
本文件写：这个环在流水线里是什么、什么算一条合格的 harness 提案、原语与出口、不可豁免的约束。哪条提案值得开 PR 是人的份额。

## 缺口（Knowledge + Judgment + Control）

deletion 测试：撤掉本 skill，引擎会在某次 review 跑到 exit 30 后说"MAX_ROUNDS 太小了，改成 20"——没有跨 PR 的数据、
没有对照"是预算不够还是层错了"、直接 sed 改脚本。缺的是：数据在哪、怎么算（Σ）；什么算 harness 参数需要动的信号，
什么只是一次噪声（φ）；导出与出 diff 的脚本（Π）；提案永不自动生效的门（γ）。

## 世界（Σ）

- **这是 hill_climb 环**（`../ai-dlc/assets/loops.yaml#hill_climb`）：generator = 本 skill，verifier = `human.harness-review`，
  timescale = days，trigger = cron。它读其他五个环的 memory 文件，不读实现者会话。
- **数据全部来自已有产物**：`specs/<slug>/{state.json, ledger.md, trace.jsonl, escape-defects.md}`、
  `.aidlc/pr-watch/pr-N.json` + `pr-N.counters.json`、`ratchet-log/**/results.tsv`；参数现值来自 `routing.yaml` / `loops.yaml` /
  `pr-poll.sh` 的默认值。不需要额外埋点。
- **可动的东西是封闭集**（target ∈）：`routing.budgets.<track>.<key>` · `routing.fingerprint_repeat_limit` · `routing.plateau_rounds` ·
  `review-loop.MAX_ROUNDS` · `review-loop.MAX_THREAD_STRIKES` · `acceptance-fleet.isolation_min` · `pr-review.b_tier_thresholds` ·
  `code-reviewer.focus_allocation` · `<skill>.fix_list`。契约、世界、代码、skill 正文都不在集合里——它们分别是 /retro、/implement、
  skill-evolve 的地盘。
- **信号与它说明的问题**：

  | 统计 | 说明 |
  |---|---|
  | 某层预算从未被碰（max_used = 0） | 预算可能过宽——降 1，不影响任何已发生的升级 |
  | 某层预算在 ≥ 50% 特性上耗尽 **且** 没有 repeat / oscillation / plateau 升级 | 重试在推进，预算真的短——升 1 |
  | 预算耗尽 **且伴随** 收敛升级 | 不是预算问题，是层错了——不提案，写 note |
  | review 轮次最大值 ≤ 40% MAX_ROUNDS 且从未 exit 30 | MAX_ROUNDS 可收紧（失控环更早停） |
  | ≥ 50% PR 撞到 MAX_ROUNDS | 升 2，但风险是掩盖本该去 G3 的争议 |
  | ACCEPT / 已裁决 ≥ 0.95 且线程 ≥ 5 | **sycophancy 反向代理**（SWE-Review）：REJECT 是合法且被期望的；进 review-loop 的 fix_list |
  | strike 冻结线程 ≥ 50% PR | 先审 REJECT 回帖有没有证据，不动 MAX_THREAD_STRIKES |
  | 逃逸缺陷按归因层 | 进对应层 skill 的 fix_list（task → donewhen-extract，plan → plan-cards，card → implement …）；`trace.py why` 看哪道门漏的 |
  | 豁免出现在 ≥ 50% 特性 | 前置条件可能定错了，不是人不小心——进 AI-DLC 的 fix_list |
  | G1 reject 以 rule_error 为主 | PSL 在推导分歧处欠定——进 psl 的 fix_list |

- **关于用户的 Σ**："调一下预算"= 要数据支撑的提案 + patch，不是直接改；"review 太顺了"= 看 accept_rate。

## 判据（φ）

- 每条提案齐 9 项：`id` · `target ∈ 封闭集` · `current` · `proposed` · `evidence`（≥ 1 条引用具体数据：特性 / PR / 计数）·
  `expected_delta`（下次哪个指标怎么变）· `risk` · `verify_by` · `delivered_as ∈ {PR, gate.json fix_list}`，外加 `apply` 段给
  `apply_proposal.py` 用。
- 一个 target 一次只提一条；同一 target 连续两期方向相反 → 停止提该 target（hill_climb 的 plateau），交人。
- 归档 < `--min-features`（默认 2）→ `proposals: []` + `insufficient_samples`；`/retro` 的"样本 1 不下结论"在这里同样成立。
- 残差（人）：提案是否对症；MAX_ROUNDS 收紧会不会误伤一次合法的长 review。

## 原语（Π）

- `scripts/tune.py <archive_root> [--pr-watch DIR] [--ratchet-logs DIR] [--routing F] [--loops F] [--out F] [--min-features N] [--json]`
  —— 统计 + 提案；exit 0 恒成立（报告工具）。
- `scripts/apply_proposal.py PROPOSALS.yaml [--id P-n …] [--skills-root DIR] [--dry-run] [--patch OUT.patch]`
  —— 只出 unified diff / patch 文件，**从不写目标文件**；`git apply` 与开 PR 是人的动作。
- `assets/harness_proposals_template.yaml` —— 产物形状与字段说明。
- 上游脚本：`../ai-dlc/scripts/aidlc_state.py loops`（当前活跃环的预算消耗）、`../ai-dlc/scripts/trace.py why`（逃逸缺陷归因链）、
  `../retro/scripts/metrics.py`（基线）。

## 评审精确率（v0.3.0）

`/tune` 一直只看 sycophancy 代理（ACCEPT 率 ≥ 0.95 = 修复方太顺从）。反方向那种病没人看：
**评审方乱开枪**。Greptile 2026 的独立复核测到抓 bug 率 82% 的工具精确率只有 36.5%——
316 条评论里 111 条挑刺、56 条是错的。一个 40% 时候是错的评审者，消耗的注意力比它省下的多。

两者不能混进一个指标，因为它们把同一个数往相反方向拉：

| 病 | 代理 | 提案落到哪 |
|---|---|---|
| 修复方顺从 | ACCEPT / 已裁决 ≥ 0.95（≥ 5 条） | `review-loop.fix_list`：审一遍那些 ACCEPT |
| 评审方误报 | 精确率 = 1 − REJECT / 已裁决 < 0.6（≥ 5 条） | `acceptance-fleet.evaluators.cross_vendor`（把该槽换成非本家）+ `pr-review.b_tier_thresholds` |

REJECT 意味着这条评审主张被验证后不成立——那是评审方的误报，不是修复方的顺从。
两条提案都进封闭 target 集，都只出 diff，都由人开 PR。

## 门（γ）

- **done_when**：`harness-proposals-<date>.yaml` 落盘 ∧ 每条提案 9 项齐 ∧ target 全在封闭集 ∧
  （`delivered_as: PR` 的有 patch 文件或 dry-run diff 已给人看；`fix_list` 的已由 `apply_proposal.py --patch` 出 gate.json diff）。
- **提案永不自动生效**：routing.yaml / pr-poll.sh / gate.json 的改动都是仓库文件，走 PR，`human.harness-review` 合；
  `--autopilot` 不适用于本 skill。
- 与 `/retro` 的边界：retro 改**判据与世界**（AC / DOS / PSL / 不变量），tune 改**harness 参数**；同一次复盘可以两个都跑，去向不同。

## 高危黑名单（不可豁免）

- 绝不直接改 routing.yaml / loops.yaml / pr-poll.sh / gate.json——只出 diff。
- 绝不在样本 < 2 时提案；绝不对同一 target 来回提。
- 绝不把"预算耗尽 + 收敛升级"读成预算不够。
- 绝不读实现者会话；绝不提改契约、改代码、改 skill 正文的提案（不在封闭集）。

## 接线

上游：`/ai-dlc archive`（`specs/*/`）、`/review-loop`（`.aidlc/pr-watch`）、`/ratchet`（results.tsv）、`/retro`（metrics.json）。
下游：`human.harness-review`（PR）；各 skill 的 `eval/gate.json` fix_list（skill-evolve 邻居读它）。图上的位置：`graph.yaml`
`retro → tune → human.harness-review → AI-DLC`（loop_back，loop: hill_climb）。触发：`triggers.yaml#hill_climb`（`/schedule` 每周）。

## 本 skill 自身的出口门

`eval/gate.json`：`static_only`——`tune.py` 在 2 归档 + 2 PR 的 fixture 上产出 ≥ 3 条提案且字段齐、单归档只出基线；
`apply_proposal.py --dry-run` 对 MAX_ROUNDS 提案输出正确 diff、`--patch` 落盘且目标文件不变。行为层（真实归档）未跑。
