---
name: plan-cards
description: >-
  补引擎自己给不出的缺口：把一份冻结的判据契约拆成"单独丢给一个没有任何上下文的 agent 也能干完"的
  任务卡——每张卡带 REQ 归属、AC 子集、DOS 切片、可改/禁改文件白名单、上下文预估与预算；以及三项
  机器校验（REQ 全覆盖且无重复归属 · 卡间无文件写冲突含共享文件归属 · 名词能被 DOS 切片解析）、
  上下文 ≤ 40k 必拆的 lint、以及"投影与其数据源同卡"（渲染/报告脚本必须声明 reads_from，跨卡要
  depends_on + 接缝说明），全部编译在 lint_cards.py。Use when: "拆任务卡" / "PLAN" / "拆成能并行做的卡" /
  "split into cards" / "task cards" / 契约已 G2 冻结、准备实现之前。NOT for: 写契约（/donewhen-extract）、
  写测试（/test-suite-generator）、实现卡（/implement）。前置：`.done_when.lock` 存在（G2 已签）。
argument-hint: "<specs/<feature>/ 或 done_when.yaml> [--spec spec.md] [--dos dos.yaml] [--out cards/] [--max-context 40000]"
version: 0.1.0
user-invocable: true
---

# plan-cards — 自包含的卡，不是设计文档

产物是 `cards/CARD-xx.yaml`（形状：`assets/card_template.yaml`）。合格标准只有一条：单独丢给一个没有任何
上下文的 agent，它能干完。本文件写：卡在流水线里是什么、什么算拆对了、原语与出口、进实现前的门。
先拆哪块、拆几张是你的份额。

## 缺口（Judgment + Capability + Control）

deletion 测试：撤掉本 skill，引擎会写一份平铺的 tasks.md——没有文件归属、没有 AC 子集、两张卡都改
`package.json`、一张卡要 80k 上下文。并行实现时合并冲突，卡级验收没有对象，白名单执行器无从执行。
缺的是判据（自包含长什么样）、原语（三项 lint）、门（lint 不过不进 implement——`sdlc_state.py advance
implement` 要求 `cards.lint_passed`）。

## 世界（Σ）

- **卡 = 子 agent 的 prompt 载荷**（SKILL.state：只给卡 + 状态摘要，不给整段历史）。卡里没写的，实现者
  不知道；所以 `notes` 要自包含，不引用对话。
- **REQ 一卡一主**：每个 REQ 只能归一张卡（重复归属 = 两个实现者改同一行为）。AC 子集从 `done_when.acceptance`
  按 `req` 取。
- **文件级存在性在卡里，不在契约里**（C2）：`allowed_files` 是白名单执行器（`verify_commit.py --card`）的输入；
  `forbidden_files` 默认继承 `done_when.constraints.forbidden_paths` + `tests/**` + 锁文件。
- **共享文件**（lockfile / 配置 / 路由表 / schema）要么归一张卡，要么全部禁改——"卡间无写冲突"必须覆盖它们。
- **卡级验收 ≠ 需求级验收**：每张卡只跑 AC 子集；所有卡完成后必须整体跑一次（`/acceptance-fleet`）。
- **`depends_on`** 只表示依赖顺序（Σ 第 1 格），不是执行脚本；无依赖的卡可并行。
- **投影与其数据源同卡**：渲染 / 报告脚本与它读的数据在一张卡里，否则没人能原子地同时改数据的形状与它的
  标签。跨卡是例外，例外要 `reads_from` + `depends_on` + `notes` 里的接缝风险三样齐全（lint 项 6）。
- **上下文预估**：卡 + 相关源码 + AC 子集 + 测试 > 40k → 必拆（lint，不是备注）。
- **这条 40k 会反压契约**：一个 REQ 的实现读集若超 40k，"REQ 一卡一主"与"≤ 40k"同时成立就无解。
  **G2 冻结前**就要按分区把这类 REQ 拆开；G2 之后再拆要走变更提案 + 重新签锁。
- **关于用户的 Σ**："拆细一点"= 上下文预算更小，不是更多卡；"一张卡做完"= 合法，但仍要过 lint。

## 判据（φ）

- `lint_cards.py` 三项 + 上下文 + `ac_ids` 存在性 + `allowed_files` 非空 + 投影/数据源同卡 → 全过。
- 残差（人 / judge）：卡是否真的自包含；`allowed_files` 是否最小；上下文预估是否诚实。

## 原语（Π）

- `scripts/lint_cards.py <cards_dir> [--spec spec.md] [--done-when done_when.yaml] [--dos dos.yaml] [--max-context N] [--repo-root DIR] [--projection-pattern RE]`
  —— exit 0 / 1 / 2。**进 implement 前必须跑**，过了 `sdlc_state.py set cards.lint_passed=true`。
  给 `--repo-root` 时会读渲染脚本本身核验 `reads_from`，声明因此可核验而非自述。
- `assets/card_template.yaml` —— 卡的具名字段。
- `references/splitting.md` —— 拆分启发式（按观察边界 / 按 DOS 对象 / 先契约后 UI / 投影与数据源同卡）、
  共享文件处置、上下文估算法、以及 L4 对契约层 REQ 粒度的反压。

## 门（γ）

- **前置**：`.done_when.lock` 存在（契约冻结后才拆卡，否则卡的 AC 子集没有对象）。
- **done_when**：`lint_cards.py` exit 0 ∧ 每张卡 `sdlc_state.py card CARD-xx --status todo` 登记 ∧ `cards.lint_passed=true`。
- 卡的修改（重拆）= 方案层回流：`sdlc_state.py fail --signal same_card_same_fingerprint` 之后重拆，账本留痕。

## 失败机制

- lint 报 REQ 未覆盖 → 补卡或把 REQ 收进已有卡，不删 REQ。
- lint 报写冲突 → 收窄 glob 或把共享文件归一张卡并在其余卡 `forbidden_files` 列出。
- lint 报闭包失败 → 卡里的名词不在 dos.yaml：要么改用 DOS 词，要么先走本体层（`/dos-extract` 更新 / 变更提案）。
- 上下文超限 → 按 `references/splitting.md` 再拆；不要调大 `--max-context`。

## 高危黑名单（不可豁免）

- 绝不写没有 `allowed_files` 的卡；绝不用 `**` 放开一切。
- 绝不把 `tests/**`、`done_when.yaml`、`dos.yaml`、`.done_when.lock` 放进任何卡的 `allowed_files`。
- 绝不让两张卡拥有同一个 REQ；绝不为了过 lint 删 REQ。
- 绝不在卡里引用对话上下文（"如前所述"）。

## 接线

上游：G2（`.done_when.lock`）、`/donewhen-extract` / `/acceptance-spec`（REQ 与 AC）、`/dos-extract`（词表）。
下游：`/implement`（按卡）、`/test-suite-generator`（按卡分批）、`/commit --card`、`/sdlc`（`cards.items`）。

## 本 skill 自身的出口门

`eval/gate.json`：`static_only`——`lint_cards.py` 在 fixtures 上冒烟（坏卡集 6 项独立违规被拒；好卡集过）。行为层未跑。
