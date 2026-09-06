---
name: psl-derive
description: >-
  补引擎自己给不出的缺口：读完一份 PSL 之后，先产三样东西再产代码（DOS 提案 / Workflow / 形态草案），
  且每条形态决策必须引用它从哪条 PSL 规律推出来（PSL-ID 格式硬约束，否则 G1 里"推错了 vs 规律错了"
  全靠口头）；以及把"推导不可复现"从残余风险变成信号——N 次独立推导取分歧集，一致的部分是 PSL 真正
  约束住的，分歧集就是 G1 的议程。效果：功能级 PSL → derived/{dos-proposal.yaml, workflow.md,
  form-draft.md, divergence.md}，经 verify_derived.py 机械预门后交 G1 人裁决。Use when: "从 PSL 推
  形态" / "推导产物" / "先出形态草案再写代码" / "psl-derive" / "derive the form from the PSL" /
  "G1 要审什么" / 写完 PSL 之后、建 issue 之前。NOT for: 写 PSL 本身（/psl）、从代码抽本体
  （/dos-extract）、写验收契约（/donewhen-extract）、直接实现（那正是本 skill 要拦的）。
argument-hint: "<PSL-<name>.md 路径> [--n 3] [--out derived/] [--dos dos.yaml] [--auto]"
version: 0.2.0
user-invocable: true
---

# psl-derive — 读完世界，先推三样东西，再谈代码

产物是 `derived/` 下四个文件：`dos-proposal.yaml`（应然本体，与 `/dos-extract` 同一 12 节 schema）、
`workflow.md`（Σ 发生了什么 + φ 消歧判据，不是 Step 1/2/3）、`form-draft.md`（形态草案：每条决策带
PSL-ID）、`divergence.md`（分歧集）。本文件写：推导产物在世界里是什么、什么算推对了、原语与出口、
G1 前的门。推几次、先推哪层是你的份额——除非下面说它是依赖顺序。

## 缺口（Judgment + Control + Capability）

deletion 测试：撤掉本 skill，引擎读完 PSL 直接写代码或直接建 issue——形态在实现里"顺手"决定，没有人看过
它长什么样；等验收发现"AC 全绿但不是想要的"，贵一个数量级。缺的是：**产物序**（形态草案先于代码，且
落文件供 G1 裁决）、**追溯判据**（每条决策 ← PSL-ID）、**分歧集原语**（N 次推导取交并，把不可复现变成议程）。

## 世界（Σ）

- **三样推导产物是同一个世界的三个投影**：DOS 提案（有哪些实体 / 关系 / 不变量，应然本体）、Workflow（用户
  做 X 时世界里发生了什么、歧义怎么裁）、形态草案（界面 / 接口 / 数据形态上该有什么）。三者引用同一套词表
  （PSL 的 Domain Model 词），不允许各自造词。
- **DOS 提案复用 `/dos-extract` 的 schema**（`../dos-extract/assets/dos_template.yaml`）——同 schema 才能在
  X1 与现状本体逐条对账。它是"应然"，`/dos-extract` 抽出来的是"现状"；对账是人的事（G1 记录）。
- **形态草案是本次功能文档的前身**：G1 签字版形态草案 = 功能文档；它的 sha256 进 G1 记录，issue 的 Intent
  引用它。
- **分歧集是 PSL 欠定处的地图**：N（默认 3）次独立推导（不同会话 / 不同模型 / 至少不同随机性），逐条比对
  形态决策：全部一致 → PSL 约束住了；不一致 → 进 `divergence.md`，每条写明各版本的选择与各自引用的
  PSL-ID。分歧集非空时 G1 记录必须逐条回应。N=1 合法但要在 divergence.md 写 `n: 1 — 未做分歧检验`。
- **G1 是唯一能拦"正确的错误"的门**（日历筛选器那类）；本 skill 的全部产物都是给 G1 看的，不是给实现者的。
- **关于用户的 Σ**："推一下形态"= 要草案 + 分歧集，不要代码；"直接按 PSL 做"= 仍然先推导，因为 G1 不能跳。

## 判据（φ）：什么算推对了

- **四个文件落盘**，缺一不可（分歧集可以是"无分歧"但文件要在）。
- **形态草案每条决策带引用锚**：形如 `- [F-03] 搜索结果以"时期卡"呈现 ← PSL-007, UI-2`。合法的锚是
  `PSL-NNN`（规律索引）与 `UI-n` / `A-n` / `DP-n`（UI Contract / Acceptance / Design Principles 的条目）
  ——那三层同样承重，只认 PSL-NNN 会逼推导者借最近的规律再注 `(via UI-2)`，引用就成了装饰（I-19）。
  无引用的决策 → 拒；引用的锚在 PSL 里不存在 → 拒。"从常识推"不是引用——常识要先进 PSL（surface 来路）再引。
  只引形态层规律；PSL 里标 `（内容层）` 的规律不出现在本稿是正常的，不算漏决策（I-20）。
- **含谓词的决策带走查例**：出现"当且仅当 / ∧ / 缺一不算 / exit 0 / 若…则"时，同一行给 `例：<输入> → <判定>`。
  三处谓词欠定都是 L5 编 fixture 时才暴露的，其中一处测试选错读法、锁了之后只能走变更提案（I-56 / I-58）。
- **每种记录类型写落位**：「实体与数据形态」里每条决策说明该记录落在产物的哪个顶层键、被谁以什么字段引用。
- **引用数据文件结构的决策带一行证据**：断言 `graph.yaml` 的节点与边、某 schema 的顶层键时，把行号抄进来
  （`graph.yaml L320–321`）。这类错误读起来完全合理，只有对着原始数据才看得出来（I-36）。
- **DOS 提案过 `verify_dos.py`**（≤ 7 对象、关系引用已声明对象、无 UI/impl 后缀、open_questions 非空）。
- **Workflow 不是流程**：出现 `Step N / 步骤 N / 阶段 N` → 拒；连续时序词 ≥ 3 → flag（同 `verify_psl.py`）。
- **分歧集每条有形状**：决策点 · 各版本选择 · 各自引用 · 建议议程（改 PSL 哪条 / 请人定）。以 `| D-n`
  开头的行是 7 格，最后一格是议程，不能空、不能留占位符。
- **第 2 轮起的定向重推有归档**：覆盖四个文件前先原样归档到 `derived/round<n-1>/`，写 `round-diff.md`
  （逐决策 diff，左侧指向那个归档），divergence.md 声明 `round: n` 并用「G1 裁决 → 落点」表替代 D-表。
- **推导不引入 PSL 没有的实体**：DOS 提案的 objects 必须能在 PSL 的 Domain Model 里找到（或在 open_questions
  里声明为候选）——否则是引擎在即兴造世界。
- 残差（人 / G1）：推出来的形态对不对；分歧该按哪个版本定；PSL 该不该改。脚本只给 `needs_semantic_review`。

## 原语（Π）

- `scripts/verify_derived.py <derived_dir> --psl <PSL.md> [--n 3] [--round 1]` —— 机械预门：四文件存在；
  形态决策引用锚完整且锚在 PSL 里存在；DOS 提案调用 `../dos-extract/scripts/verify_dos.py`；Workflow 无具名
  步骤（**只跳过开篇前言里的引用行**——把流程藏进 `> ` 不豁免，I-77）；分歧集形状；DOS 提案 objects ⊆ PSL
  Domain Model 词表（∪ open_questions 候选）；`--round n≥2` 时检归档 / round-diff / `round: n` 声明 /
  裁决落点表。exit 0 / 1 / 2。
- `assets/form_draft_template.md` · `assets/workflow_template.md` · `assets/divergence_template.md` ·
  `assets/round_diff_template.md`；DOS 提案模板即 `../dos-extract/assets/dos_template.yaml`。
- `references/derivation.md` —— 从六层 PSL 到三样产物的推导对应（哪层喂哪样）、分歧集的比对方法、常见的
  "技术对产品错"信号。
- 隔离推导：N 次推导用 Agent 工具各开一个全新上下文（只给 PSL 文件路径 + 模板，不给前一次的结果）；
  合并与比对由主会话做。

## 门（γ）

- **产物序**：形态草案先于任何代码 / issue（第 5 格：出口可检——`sdlc_state.py gate g1 --verdict pass` 要求
  `world.derived_dir` 存在）。
- **G1 人签**：本 skill 不裁决世界；交付时明说"这份形态草案的正确性需要你在 G1 裁决"，把分歧集当议程。
- **done_when**：四文件落盘 ∧ `verify_derived.py` exit 0 ∧ 分歧集每条有议程 ∧ 每条含谓词的形态决策至少有
  一个走查例 ∧ 每种记录类型写了落位 ∧ 回报路径 + 形态草案 sha256（第 2 轮起另加：上一轮归档在
  `round<n-1>/` ∧ `round-diff.md` 落盘）。
- **`--auto`**：跳过中途确认，但不跳过 G1。

## 失败机制

- PSL 缺层 / 过不了 `verify_psl.py` → 停，回 `/psl` 补，不在推导里替它补世界。
- 推出的实体在 PSL 里找不到 → 不塞进 DOS 提案；写进 `divergence.md` 的"PSL 欠定"段，作为 G1 议程（可能要改 PSL）。
- N 次推导彼此差异极大（> 半数决策不一致）→ 这是信号：PSL 约束太弱，回报"建议先补 PSL 的 Mental Model /
  Domain Model 再推"，不要用多数表决糊过去。
- G1 否决"推错了" → 用同一 PSL 重推（记 `sdlc_state.py gate g1 --verdict reject --attribution derivation_error`）；
  "规律错了" → 改 PSL 再推（`--attribution rule_error`，世界层计数 +1）。
- **定向重推是合法回退，不是全量重来**。草案大部分对、只有 G1 裁定的几个点要改时，用"新 PSL +
  `g1-record.md` 的逐条裁决"做 **n=1 定向重推**：不必重跑 N 次独立推导，divergence.md 写
  `n: 1 — 未做分歧检验` 并说明理由。契约里没有这一条时 G1 只剩 PASS 与全量 REJECT 两个选项，
  对"85% 对"的草案两个都不对（dogfood 2026-09-05，I-21）。
- **每一轮都归档，覆盖之前先存档**。写新一轮的四个文件之前，把上一轮原样复制到 `derived/round<n-1>/`，
  然后写 `derived/round-diff.md`（逐决策 diff，左侧指向归档路径），divergence.md 声明 `round: n`。
  少了归档，"只改了裁定点"就是一句无法复核的自述——本次第三轮就地覆盖了第二轮，round-diff 的左侧
  没人能重算（I-35 / I-44）。`verify_derived.py --round n` 检这四件事。

## 高危黑名单（不可豁免）

- **绝不跳过 G1 直接进 issue / 代码**。
- **绝不写没有引用锚的形态决策**；绝不引用 PSL 里不存在的锚。
- **绝不用多数表决消灭分歧集**——分歧是议程，不是噪声。
- **绝不在 DOS 提案里造 PSL 没有的实体**。
- **绝不把 Workflow 写成步骤**——包括把步骤藏进引用块。
- **绝不就地覆盖上一轮的推导产物**：先归档 `round<n-1>/`，再写新一轮。

## 接线（在 sdlc 里的位置）

上游 `/psl`（世界）；本 skill 是 U3；下游 **G1**（`assets/g1_record.md` 三问 + 分歧集逐条回应）→ `/issue`
（Intent 引用签字版形态草案 sha256）。DOS 提案与 `/dos-extract` 的现状本体对账（X1，目前人做）。
路径记入 `sdlc_state.py set world.derived_dir=derived/`。

### G2 回流到形态（契约层发现形态少了一条）

G2 复核契约时可能发现形态草案缺一条决策（本次：契约要的 `required_parts` / `parts_total` 视图在
签字版里没有对应决策）。这条路径以前没写，只能靠 G1 现场立规——补上（I-48）：

1. **谁落盘：推导者，不是 G1。** 评估者与被评估者分离是这条流水线的设计不变量；G1 一旦成为草案的
   作者，签字就变成自签。追加走 n=1 定向重推，只动那一条决策。
2. **G1 怎么再签：按 diff 条件预签。** G1 在隔离目录里把"签字版 + 精确 diff"构造出来、跑过预门、
   算出 sha256，然后签一个**条件签字**：落盘文件的 sha256 恰为此值则生效，不符则无效、带 diff 回来。
   条件里明写"落盘者不得是 G1"。
3. **旧 sha 怎么退场：supersedes，不改写。** 新签字记 `supersedes <旧 sha>`，旧 sha 作为"追加之前"
   的形态草案哈希保留可回溯。G1 记录只增不改（账本纪律）。
4. 落盘者先 `sdlc_state.py set world.form_draft_sha256=<新 sha>` 再通知，避免与"请 G1 落盘"的消息
   交叉导致二次写入。

模板见 `../sdlc/assets/g1_record.md` 的「补签」小节。

## 本 skill 自身的出口门

`eval/gate.json`：`static_only`——`verify_derived.py` 在 fixtures 上冒烟（合法 derived 目录 0 拒；缺引用 /
假 ID / 步骤化 Workflow / 造实体 各被拒）。行为层（N 次真实推导 + 一次真实 G1）未跑。
