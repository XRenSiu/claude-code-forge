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
version: 0.7.0
user-invocable: true
---

# plan-cards — 自包含的卡，不是设计文档

产物是 `cards/CARD-xx.yaml`（形状：`assets/card_template.yaml`）。合格标准只有一条：单独丢给一个没有任何
上下文的 agent，它能干完。本文件写：卡在流水线里是什么、什么算拆对了、原语与出口、进实现前的门。
先拆哪块、拆几张是你的份额。

## 缺口（Judgment + Capability + Control）

deletion 测试：撤掉本 skill，引擎会写一份平铺的 tasks.md——没有文件归属、没有 AC 子集、两张卡都改
`package.json`、一张卡要 80k 上下文。并行实现时合并冲突，卡级验收没有对象，白名单执行器无从执行。
缺的是判据（自包含长什么样）、原语（三项 lint）、门（lint 不过不进 implement——`aidlc_state.py advance
implement` 对 `cards.dir` **自己跑** `lint_cards.py`；`cards.lint_passed` 不可 set）。

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

- `scripts/lint_cards.py <cards_dir> [--spec spec.md] [--done-when done_when.yaml] [--dos dos.yaml] [--require-dos] [--max-context N] [--repo-root DIR] [--projection-pattern RE]`
  —— `--require-dos` 把"`dos_slice` 闭包未检"从一条 info 升成 reject，并在没给 `--dos` 时自动发现
  项目里的 `dos.yaml`（`../ai-dlc/scripts/repo_assets.py`）。M / L 档带上它：卡里出现一个本体
  解析不了的名词是整条流水线上代价最高的一次漂移，而"没算过"和"算过且通过"在旧输出里长得一样。
  —— exit 0 / 1 / 2。**进 implement 前必须跑**；`aidlc_state.py set cards.dir=cards` 后 `advance implement` 会再跑一遍并记 `cards.lint_passed`（它不可 set：一个引擎 set 的布尔是执行者的说法）。
  给 `--repo-root` 时会读渲染脚本本身核验 `reads_from`，声明因此可核验而非自述。
- `../dos-extract/scripts/verify_vocabulary.py --dos dos.yaml cards/CARD-*.yaml` —— **B 档术语传感器**。
  `lint_cards.py` 的第 3 项只闭包 `dos_slice.objects` / `dos_slice.invariants`（**结构化字段，作者主动列出来的**）；
  卡的 `title` 与 `notes` 是散文，从来没人检——而实现者拿到的**全部输入就是这张卡**，
  卡里出现一个本体解析不了的名词，是整条流水线上代价最高的一次漂移：实现者会自己给它挑一个意思，
  而这个意思要到验收才对得上。两者不重叠：结构化归 `lint_cards.py`（拒），散文归传感器（告警）。
  exit 0 / 1（超阈值）/ 2（IO）/ **3（没有 dos.yaml = 未检，不是通过；`--require-ontology` 变 1）**。
- `assets/card_template.yaml` —— 卡的具名字段。
- `references/splitting.md` —— 拆分启发式（按观察边界 / 按 DOS 对象 / 先契约后 UI / 投影与数据源同卡）、
  共享文件处置、上下文估算法、以及 L4 对契约层 REQ 粒度的反压。

## 仓库地图切片（v0.2.0）

卡给实现者卡 + AC 子集 + 红基线 + 约束，**没给**测试怎么跑、构建怎么起、这块目录谁管、边上哪里不能碰。
`scripts/slice_agent_map.py <agent-map.md> --card cards/CARD-xx.yaml --out slice.md` 把仓库地图按本卡切：
命令一节**全给**（红-绿自证靠它），目录 / 禁区 / 陷阱只给与 `allowed_files` 相交的行。
切出来的块拼进 `../implement/assets/card_context.md` 的「仓库怎么干活」一节。

给整份地图是噪音（2607.27250：堆仓库知识不提高正确率），给零行是让实现者去猜。切片是这两者之间那个东西。

## 门（γ）

- **前置**：`.done_when.lock` 存在（契约冻结后才拆卡，否则卡的 AC 子集没有对象）。
- **done_when**：`lint_cards.py` exit 0 ∧ 每张卡 `aidlc_state.py card CARD-xx --status todo` 登记 ∧ `cards.dir` 已 set（`advance implement` 自己跑 lint 并记 `cards.lint_passed`）。
- **B 档（告警，不挡）**：`verify_vocabulary.py --dos dos.yaml cards/CARD-*.yaml` 的计入发现记进账本。
  超阈值不阻止进 implement——术语漂移是告警不是否决——但它是"卡该不该重写一句话"的输入，
  且 exit 3（没有本体）必须按**未检**记，不许记成通过。
- 卡的修改（重拆）= 方案层回流：`aidlc_state.py fail --signal same_card_same_fingerprint` 之后重拆，账本留痕。

## 失败机制

- lint 报 REQ 未覆盖 → 补卡或把 REQ 收进已有卡，不删 REQ。
- lint 报写冲突 → 收窄 glob 或把共享文件归一张卡并在其余卡 `forbidden_files` 列出。
- lint 报闭包失败 → 卡的 `dos_slice` 名词不在 dos.yaml：要么改用 DOS 词，要么先走本体层（`/dos-extract` 更新 / 变更提案）。
- 传感器报 near_miss → 卡的散文里写了本体词的**省略式**（`transaction` 之于 `BankingTransaction`）或
  另一种写法（`work_unit` 之于 `WorkUnit`）：改卡用本体的词，或去 `dos.yaml` 把它写进 `synonyms:`。
  **不要靠调阈值让它闭嘴**——同义词是声明出来的，不是猜出来的（`dos_closure.py` 的铁律）。
- 上下文超限 → 按 `references/splitting.md` 再拆；不要调大 `--max-context`。

## 高危黑名单（不可豁免）

- 绝不写没有 `allowed_files` 的卡；绝不用 `**` 放开一切。
- 绝不把 `tests/**`、`done_when.yaml`、`dos.yaml`、`.done_when.lock` 放进任何卡的 `allowed_files`。
- 绝不让两张卡拥有同一个 REQ；绝不为了过 lint 删 REQ。
- 绝不在卡里引用对话上下文（"如前所述"）。

## 接线

上游：G2（`.done_when.lock`）、`/donewhen-extract` / `/acceptance-spec`（REQ 与 AC）、`/dos-extract`（词表 +
`verify_vocabulary.py` 传感器）。
下游：`/implement`（按卡）、`/test-suite-generator`（按卡分批）、`/commit --card`、`/ai-dlc`（`cards.items`）。

## 本 skill 自身的出口门

`eval/gate.json`：`static_only`——`lint_cards.py` 在 fixtures 上冒烟（坏卡集 6 项独立违规被拒；好卡集过）。行为层未跑。
