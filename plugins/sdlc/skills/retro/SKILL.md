---
name: retro
description: >-
  补引擎自己给不出的缺口：把归档目录、账本、逃逸缺陷、发布记录读成"流程病在哪一层"的证据（回流分布、
  G1 拦截率、human AC 占比、返工轮次、逃逸缺陷率、豁免数），并把每条发现路由到能改的那一层——PSL 规律 /
  DOS 修订 / 不变量候选 / AC 收紧 / 路由预算 / skill 的 fix_list——而不是写一篇感想。产物：带日期的基线 +
  提案清单，每条提案有去向与验收方式。Use when: "复盘" / "retro" / "这次为什么返工这么多" / "看看流程哪里
  出问题" / "度量" / 一个或多个 feature 归档之后。NOT for: 单次 bug 的根因（/adversarial-debugging 类）、
  改 skill 本身（skill-evolve 邻居）。前置：`specs/*/` 至少一个归档。
argument-hint: "[--archive specs/] [--since YYYY-MM-DD] [--out retro/retro-<date>.md]"
version: 0.2.0
user-invocable: true
---

# retro — 先测基线，再看病在哪层

产物：`retro/retro-<date>.md`（基线表 + 发现 + 提案，形状 `assets/retro_template.md`）与 `metrics.json`。
本文件写：度量在流水线里是什么、什么算一条有用的发现、原语与出口、提案的去向。怎么解读是你的份额，
但每条提案必须有去向和验收方式。

## 缺口（Knowledge + Judgment + Capability）

deletion 测试：撤掉本 skill，引擎会写"这次沟通不够充分，下次加强测试"——没有数字、没有层、没人能验收。
缺的是：数据在哪（Σ）、什么算流程病的信号（φ）、导出脚本（Π）、提案必须落到层（γ）。

## 世界（Σ）

- **数据全部来自归档，不需要额外埋点**：`specs/<slug>/state.json`（阶段时间戳、分层计数、门的裁决、豁免）、
  `ledger.md`（每次失败与路由）、`done_when.yaml`（human AC 占比）、`escape-defects.md`、`releases/*.md`、
  `.sdlc/pr-watch/*.json`（review 轮次与 verdict 分布）。
- **指标与它诊断的层**：

  | 指标 | 数据源 | 高了说明哪层病 |
  |---|---|---|
  | 回流分布（card/plan/task/ontology/world） | counters | 哪一层最常被退回 = 那层的门太松或上游没建好 |
  | G1 拦截率（PSL 轨） | gates.g1 | 高 = 推导常错（PSL 欠定）或世界常错（好事：拦住了） |
  | human AC 占比 | done_when | 持续过半 = 该类需求不该走流水线 |
  | PR 返工轮次 | review.rounds / pr-watch | 高 = 契约或卡的粒度问题，不是 reviewer 苛刻 |
  | 逃逸缺陷率 | escape-defects | 压住"切小任务刷首过率"；逐条看归因层 |
  | 豁免数 | waivers | 门被 --force 绕过的次数；> 0 就要问为什么 |
  | lead time | created_at → merged_at | 与轮次一起看，单看无意义 |
  | 逃逸缺陷因果链（v0.6） | trace.jsonl：escape → caused_by* → 根 | 深度与根的层直接回答"为什么门没拦住"；根在 task = 契约；根在 gate = 人签时没看到 |
  | 契约返工率（v0.6） | trace.jsonl：`supersedes done_when.yaml#AC-*` / AC 总数 | 高 = G2 之前判据写得太早或太松 |

- **基线先于结论**：第一次跑只记基线（带日期），不下诊断；第二次起比差值。
- **提案的去向是封闭集**：`psl`（改规律 / 补 Mental Model）、`dos`（本体修订 → 变更提案）、`invariant`（→ /invariant-extract）、
  `ac`（收紧 done_when → 变更提案）、`routing`（预算 / 指纹阈值）、`skill`（某 skill 的 fix_list）、`human`（需要人定）。
- **关于用户的 Σ**："复盘一下"= 要数字 + 提案，不要感想；"这次做得挺好"= 也记基线。

## 判据（φ）

- 报告含带日期的基线表（`metrics.py` 输出原样粘贴，不手抄数字）。
- 每条发现引用具体数据（slug / 层 / 计数 / 账本行），每条提案有 `target ∈ 封闭集`、`change`、`verify_by`（下次哪个指标怎么变）。
- 只有一个 feature 时不下趋势结论（样本 1）。
- 残差：提案是否真的对症（人判）。

## 原语（Π）

- `scripts/metrics.py <archive_root> [--json OUT] [--md OUT]` —— X3 导出（lead time / 轮次 / 回流分布 / G1 率 / human AC / 逃逸 / 豁免）。
- `assets/retro_template.md` —— 报告形状。
- `references/reading-the-numbers.md` —— 各指标的解读与常见误读。

## 门（γ）

- **done_when**：`metrics.json` 落盘 ∧ 报告含基线 ∧ 每条提案有去向与验收方式 ∧ 提案已投递（改 PSL 的进 PSL 的
  Open Questions；改 DOS / AC 的写成 `change-proposal-*.md`；改 routing 的写 PR；改 skill 的写进其 `eval/gate.json` 的 fix_list）。
- 提案不自动生效：改契约 / 本体 / 预算都经变更提案与人签（G2/G3）。

## 高危黑名单（不可豁免）

- 绝不手抄数字；绝不用一个样本下趋势结论；绝不写没有去向的提案。
- 绝不直接改 PSL / dos.yaml / done_when.yaml / routing.yaml——只提案。
- 绝不把逃逸缺陷从统计里剔除以美化首过率。

## 接线

上游：`/sdlc archive`（含 trace.jsonl）、`/release`、`/issue --escape`、`/review-loop` 证据日志。下游：`/tune`（harness 参数——retro 改判据与世界，tune 改环的参数；同一次复盘可两个都跑）、`/psl`（Open Questions）、
`/dos-extract` / `/invariant-extract`（本体层）、`/donewhen-extract`（AC 收紧）、`routing.yaml`、各 skill `eval/gate.json`、
skill-evolve（邻居，学习槽）。

## 本 skill 自身的出口门

`eval/gate.json`：`static_only`——`metrics.py` 在 fixture 归档上冒烟。行为层未跑。
