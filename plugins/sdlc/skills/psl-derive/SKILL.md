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
version: 0.1.1
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
- **形态草案每条决策带 PSL-ID**：形如 `- [F-03] 搜索结果以"时期卡"呈现 ← PSL-007, PSL-012`。无引用的决策 →
  拒；引用的 ID 在 PSL 里不存在 → 拒。"从常识推"不是引用——常识要先进 PSL（surface 来路）再引。
- **DOS 提案过 `verify_dos.py`**（≤ 7 对象、关系引用已声明对象、无 UI/impl 后缀、open_questions 非空）。
- **Workflow 不是流程**：出现 `Step N / 步骤 N / 阶段 N` → 拒；连续时序词 ≥ 3 → flag（同 `verify_psl.py`）。
- **分歧集每条有形状**：决策点 · 各版本选择 · 各自引用 · 建议议程（改 PSL 哪条 / 请人定）。
- **推导不引入 PSL 没有的实体**：DOS 提案的 objects 必须能在 PSL 的 Domain Model 里找到（或在 open_questions
  里声明为候选）——否则是引擎在即兴造世界。
- 残差（人 / G1）：推出来的形态对不对；分歧该按哪个版本定；PSL 该不该改。脚本只给 `needs_semantic_review`。

## 原语（Π）

- `scripts/verify_derived.py <derived_dir> --psl <PSL.md> [--n 3]` —— 机械预门：四文件存在；形态决策
  PSL-ID 引用完整；DOS 提案调用 `../dos-extract/scripts/verify_dos.py`；Workflow 无具名步骤；分歧集形状；
  DOS 提案 objects ⊆ PSL Domain Model 词表（∪ open_questions 候选）。exit 0 / 1 / 2。
- `assets/form_draft_template.md` · `assets/workflow_template.md` · `assets/divergence_template.md`；DOS 提案
  模板即 `../dos-extract/assets/dos_template.yaml`。
- `references/derivation.md` —— 从六层 PSL 到三样产物的推导对应（哪层喂哪样）、分歧集的比对方法、常见的
  "技术对产品错"信号。
- 隔离推导：N 次推导用 Agent 工具各开一个全新上下文（只给 PSL 文件路径 + 模板，不给前一次的结果）；
  合并与比对由主会话做。

## 门（γ）

- **产物序**：形态草案先于任何代码 / issue（第 5 格：出口可检——`sdlc_state.py gate g1 --verdict pass` 要求
  `world.derived_dir` 存在）。
- **G1 人签**：本 skill 不裁决世界；交付时明说"这份形态草案的正确性需要你在 G1 裁决"，把分歧集当议程。
- **done_when**：四文件落盘 ∧ `verify_derived.py` exit 0 ∧ 分歧集每条有议程 ∧ 回报路径 + 形态草案 sha256。
- **`--auto`**：跳过中途确认，但不跳过 G1。

## 失败机制

- PSL 缺层 / 过不了 `verify_psl.py` → 停，回 `/psl` 补，不在推导里替它补世界。
- 推出的实体在 PSL 里找不到 → 不塞进 DOS 提案；写进 `divergence.md` 的"PSL 欠定"段，作为 G1 议程（可能要改 PSL）。
- N 次推导彼此差异极大（> 半数决策不一致）→ 这是信号：PSL 约束太弱，回报"建议先补 PSL 的 Mental Model /
  Domain Model 再推"，不要用多数表决糊过去。
- G1 否决"推错了" → 用同一 PSL 重推（记 `sdlc_state.py gate g1 --verdict reject --attribution derivation_error`）；
  "规律错了" → 改 PSL 再推（`--attribution rule_error`，世界层计数 +1）。

## 高危黑名单（不可豁免）

- **绝不跳过 G1 直接进 issue / 代码**。
- **绝不写没有 PSL-ID 引用的形态决策**；绝不引用不存在的 ID。
- **绝不用多数表决消灭分歧集**——分歧是议程，不是噪声。
- **绝不在 DOS 提案里造 PSL 没有的实体**。
- **绝不把 Workflow 写成步骤**。

## 接线（在 sdlc 里的位置）

上游 `/psl`（世界）；本 skill 是 U3；下游 **G1**（`assets/g1_record.md` 三问 + 分歧集逐条回应）→ `/issue`
（Intent 引用签字版形态草案 sha256）。DOS 提案与 `/dos-extract` 的现状本体对账（X1，目前人做）。
路径记入 `sdlc_state.py set world.derived_dir=derived/`。

## 本 skill 自身的出口门

`eval/gate.json`：`static_only`——`verify_derived.py` 在 fixtures 上冒烟（合法 derived 目录 0 拒；缺引用 /
假 ID / 步骤化 Workflow / 造实体 各被拒）。行为层（N 次真实推导 + 一次真实 G1）未跑。
