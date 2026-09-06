# G1 解释规则 — sdlc-ring-audit（第二轮解释轮，change-proposal-002 的前置）

> 签字版裁决在 `g1-record.md`，签完即冻结、进 G2 锁集合。**本文件不进锁**：解释自己的裁决是 G1 的合法职能，
> 补一条解释不改签字版形态草案的任何一个字节，不该被当成契约改动、不该走变更提案（dogfood 2026-09-06, I-60）。
> 边界：解释只能**收窄或澄清**已裁决的内容。要改结论、要动签字版形态草案 → 那是新的 G1（重推或改 PSL）；
> **G2 回流引发的形态追加（补签）不在这里**，它改了签字版本身，就该撞锁、走变更提案，写在 `g1-record.md`
> 的补签节里。`lock_done_when.py sign` 拒绝把本文件锁进去，就是为了让这条边界只能靠重裁决越过。

**签字版形态草案 sha256**: `746c56ef3e39e8e7089db0914bc01015b6dd522ef622c449e3d6260fbc10880d`　**对应 G1 记录**: `g1-record.md`

**轮次**: G1-interpretation-2　**日期**: 2026-09-06　**裁决人**: g1-judge
**签字性质**: **代签**（`signer_kind: delegated_agent`）——本文件中任何一处都不得渲染为「人签」
**授权**: user instruction 2026-09-05: '需要人审核的地方，请你弄一个子agent代替我审核一下'；extended 2026-09-06: '需要人做的你就帮我做了当做人做的'

## 本轮为什么开

`change-proposal-002-scope.md` A 段列了六条读法分歧 + 一条 G3 已裁的（mf-009）。
它们的共同点：**仪器现行行为与规格文本不一致，而没有人裁过哪一边是对的**。
先编谓词等于把实现者当时碰巧持有的那个读法冻成事实——这正是本次 run 第一次付过一遍学费的失败模式。
所以顺序是：先裁读法（本文件）→ G2 冻结 → l5-tests 编谓词与 fixture → 新造隐藏集。

在本文件签字之前，`known_gaps.yaml` 对仪器现行行为的描述一律是 **de facto，不是已裁**；签字之后，
下面七条即是该编进 `check_audit.py` 的读法，`known_gaps.yaml` 的 `status` 可从 `open` 改写为 `ruled`。

**七条全部不改冻结字节**：`done_when.yaml`（sha `fb5af3f0…`）、`derived/form-draft.md`（sha `746c56ef…`）、
`PSL-sdlc-ring-audit.md`、`g1-record.md` 一字不动。**七条全部不推翻现行 `audit.yaml`**：我把七条写成脚本对
`audit.yaml`（42 Part / 73 Gap / 39 Proposal / 31 Gate / 58 Artifact 行）逐条重跑，失败计数为 0（对账表见文末）。
这是有意的——一条让正确的审计过不了自己检查脚本的解释，就是错的解释（规则 1 第一次抓到的就是这个）。

## 解释逐条（追加，只增不删；每条要能指回被解释的那句裁决）

| # | 日期 | 提问（谁在什么场景下不知道怎么办） | 解释 | 指回 g1-record 的哪一句 | 收窄 / 澄清 |
|---|---|---|---|---|---|
| 4 | 2026-09-06 | l5-tests 要为 KG-08 / M14 写 fixture：跨环的 FILLS 边算不算非法？仪器对 `fills[]` 执行同环，规则 2(e) 只对 `missing[]` 说同环 | **纠正仪器**：跨环 FILLS 边合法。`fills[]` 只要求 id 在 `gaps[]` 里存在，不要求同环；同环只约束 `missing[]` | 规则 2(e)「`missing[]` 里的每个键必在 `gaps[]` **且其 `ring` 一致**；`fills[]` 里的每个键必在 `gaps[]`」——两句的不对称是有意的 | 澄清（对 `fills` 是放宽，对 `missing` 是维持） |
| 5 | 2026-09-06 | 用 `--rings` 跑分环视图时，文档里混进一个非法环 id 无人发现——`--rings` 到底能让哪条谓词失效？ | **一半确认、一半纠正**：`--rings` 选定「哪些环必须到场」（`ring_missing` 的期望集），这是视图；但 `ring_unexpected` **不得**因 `--rings` 而失效，它问的是「文档里有没有十个法定 id 之外的环」，与看哪一环无关 | 签字版 F-17「`parts_without_assessment` 受 `--rings` 限定；**不改任何既有谓词**」（由 g1-record 第三轮 PASS 行整体签入） | 收窄（`--rings` 能免掉的只有 `ring_missing` 的期望集，别的一条都免不掉） |
| 6 | 2026-09-06 | AC-004-b 说「lacking a source assessment or gap id」，仪器只检键非空；holdout 的 `hv_proposal_dangling_source` 因此未命中 | **纠正仪器**：`source` 必须**解析得到**一个 `assessment.id` 或 `gaps[].id`。空键与悬空 id 是同一条谓词的两种失败，共用一个 token | AC-004-b 的 given 本身（契约层）+ `audit.schema.md` §Proposal「`source` 必须指向一个 Assessment id 或 Gap id」 | 收窄 |
| 7 | 2026-09-06 | `alternatives_of` 写任意非空串就免掉 `double_producer`；F-05 的三条件数据源是 graph.yaml，而检查脚本看不到 graph.yaml。该检什么？ | **纠正到文档自身能作证的那一半**：形状必须是 `stage.<x>`，且只能标在真有 ≥2 条记录的产物上，且不得每条都标。条件 (a)(b) 需要 graph.yaml，**明确不检**，并明确它是空隙不是通过 | 规则 1「Artifact 记录带 `alternatives_of`（F-05 三条件）→ 合法」——本条只裁「怎么机械核这个『带』字」 | 收窄（把「任意非空」收成「形状 + 位置」，同时诚实标出核不了的两条） |
| 8 | 2026-09-06 | `gates[]` 里 `kind` 既不是 `script` 也不是 `human` 时，rule-3 的两条谓词都不触发，静默放行 | **纠正仪器**：枚举外的 `kind`（含缺键）是错误。这是 fail-open：一个 `kind: shell, label: 门` 的记录今天既躲开 `script_gate_rendered_as_door` 也躲开 `gate_not_declared` | 规则 3 全条（`gates[]` 是设计视图）+ 签字版 F-06「Gate 记录带 `kind: script \| human`」、F-94「以 `kind` 字段区分而不以名字区分」 | 收窄 |
| 9 | 2026-09-06 | `disposition` 的枚举以谁为准：签字版 F-16 的 `fix_list \| issue \| none`，还是 `audit.schema.md` 的 `none \| issue`？ | **签字版 F-16 governs**。`audit.schema.md` 是下游文档，它自己写着「改这份文档不会改判定」——下游文档不能收窄签字版枚举。schema 须改回三值 | 第三轮 PASS 行整体签入的 F-16「Assessment 与 Gap 各带 `disposition: fix_list \| issue \| none`」 | 澄清（并附一条收窄：F-16 的「misfit 只能 issue 或 none」同为谓词） |
| 10 | 2026-09-06 | G3 已裁 F-06 按「独占 Artifact」读（mf-009）。要编成谓词，「独占」在数据里指哪个字段？ | **确认 G3 裁法**，并定死机械口径：「独占 Artifact」= 该 Part 记录自己的 `artifact` 字段所指的那一条 `artifacts[]` 记录（`id` = 该值且 `producer` = 该 Part）。不是「producer 是它的每一条记录」 | `g3-record.md` 第 1 项与 mf-009 专条「F-06 按**独占 Artifact** 读，不按『该 Part 沾到的每一个产物』读」；被解释的签字句是 F-06 | 收窄（把 G3 的读法钉到一个字段上，使谓词可写） |

---

## 规则 4 · 跨环 FILLS 边——**纠正仪器，同环只约束 `missing[]`**

`check_audit.py` 的 `resolve()` 被 `missing[]` 与 `fills[]` 共用，因而对两者一律要求 `gap.ring == 当前环`。
规则 2(e) 的原文只对 `missing[]` 写了「且其 `ring` 一致」，对 `fills[]` 只写「必在 `gaps[]`」。
这个不对称不是笔误，它是两个键的性质差别：

- `rings[].missing[]` 是**某个环对自己空白的声明**。一个环声明另一个环的空白，是记错了地方——同环是定义性的。
- `parts[].fills[]` 是**一条边**。边可以跨。F-04 明说 Gap 归属于恰一个 Ring、一个 Gap 可被多个 Part 填（N:N），
  而 Part 也归属于恰一个 Ring——两个「恰一个」相乘，跨环边就是这个数据模型的合法产物，不是异常。
  `spine` 上的 `sdlc` 与四个数据资产尤其如此：脊柱配件填某个环的 Control 缺口是本设计预期内的形状。

**这条正是规则 1 抓到的那类陷阱**：仪器比签字版**严**，于是一份记录正确的审计（脊柱 Part 填 R4 缺口）会被自己的
检查脚本拒掉。规则 1 当时的原话是「字面读法下正确的审计永远过不了自己的检查脚本」；这里是同一个病的另一处。

> **谓词**：`parts[].fills[]` 里的每个 id 必须在 `gaps[]` 中存在，**但不要求 `gaps[id].ring` 等于该 Part 所在的环**；
> `rings[].missing[]` 里的每个 id 必须在 `gaps[]` 中存在**且** `gaps[id].ring` 等于该环的 id；任一不满足 → exit 1 `unknown_gap_ref`。

**token**：`unknown_gap_ref`（沿用，不新增；定位串必须写清是 `.fills` 还是 `.missing`，以及期望环与实际环）。

**killing fixture 要有什么**（两个，缺一不可）：
1. **放宽面**：一个 `spine` 上的 Part，其 `fills[]` 指向一条 `ring: R4` 的 Gap，且该 Gap 因此**不**出现在 `R4.missing` 里
   → 必须 **exit 0**。今天的仪器对这个 fixture 报 `unknown_gap_ref`，这一条就是杀死现行过严行为的那个。
2. **维持面**（KG-08 / M14 真正缺的那个）：`R5.missing` 里放一个**存在但 `ring: R4`** 的 gap id → 必须 **exit 1 `unknown_gap_ref`**。
   现有 `mutant_unknown_gap_ref.yaml` 走的是「id 根本不在 `gaps[]`」那条分支，**没有**覆盖同环分支——M14 因此存活。

**与锁的关系**：不改任何一个锁内 fixture 的断言。`test_check_audit.py` 第 257 行的注释
（"rings[].missing[] (and parts[].fills[]) are ids that must exist in gaps[] with the same ring"）在本裁后过时，
该文件在 l5-tests 为新谓词重签时一并订正——那是锁内字节，走 l5 重签，不在本文件里改。

**契约字节**：不动。AC-004-a 只数 `orphan_gaps` / `rings_without_missing_key` / `proposals_without_source`。
**现行 audit.yaml**：通过（跨环 fills 计数 = 0，本裁对它是纯放宽）。

---

## 规则 5 · `--rings` 与环到场——**确认 `ring_missing` 的收窄，纠正 `ring_unexpected` 的失效**

F-13 的「Ring 集合 = {R0…R8, spine}」是一条**集合相等**，含两个方向：

| 方向 | 谓词 | 问的是 | `--rings` 该不该影响 |
|---|---|---|---|
| ⊆（法定环都在场吗） | `ring_missing` | 期望集里的环有没有缺席 | **该**——「看哪几环」就是期望集，这是视图的定义 |
| ⊇（有没有多出来的） | `ring_unexpected` | 文档里有没有十个法定 id 之外的环 | **不该**——这个问题与看哪一环无关，答案不随视图变 |

仪器现行是 `if selected_rings is None:` 才检 ⊇ 方向——**给了 `--rings` 就整条不检**。那不是收窄视图，是删掉谓词，
正撞 F-17 的「不改任何既有谓词」。具体后果：`check_audit.py audit.yaml --rings R6` 对一份含 `id: R9` 或
`id: R6 ` （尾空格）的文档报 exit 0。

反过来，`ring_missing` 随 `--rings` 收窄是 F-17 的本意，也是 AC-008..011 的运行方式，且卡级片段
（`audit/rings-R3-R5.yaml` 配 `--rings R3,R4,R5`）依赖它。这一半**确认**。

> **谓词**：`ring_missing` 的期望集 = `--rings` 给出的列表，未给时 = `{R0..R8, spine}`；
> `ring_unexpected` **恒对整份文档执行**——`rings[]` 中任何 `id` 不属于 `{R0..R8, spine}` 即 exit 1，与 `--rings` 是否出现无关。

**token**：`ring_unexpected`（沿用）、`ring_missing`（沿用）。

**killing fixture 要有什么**：一份在合法十环之外**追加**一条 `id: R9` 的 audit，配 `--rings R6` 运行 →
必须 **exit 1 `ring_unexpected`**。今天 exit 0。这个 fixture 同时是 KG-05（M03 `ring_unexpected` 被禁用后存活）
在 `--rings` 分支上的杀手；M03 在无 `--rings` 分支上的杀手另需一条不带 `--rings` 的同形 fixture。

**明确不在本条里裁**：KG-03 的 `ring_duplicate`（`rings: 10` 是**计数**、F-13 是**集合**，同一个 id 出现两次
计数为 10 而集合为 9）。那是「计数与集合哪个算数」的问题，不是 `--rings` 的问题，留在 B 段单独立谓词。

**契约字节**：不动。AC-001-a（不带 `--rings`）与 AC-008..011-a（带 `--rings`，输入是 complete audit.yaml）
在本裁下的期望值一字不变。
**现行 audit.yaml**：通过（非法环 id 计数 = 0）。**锁内 `--rings` 测试**：全部用 `complete.yaml`（十环齐全），断言不变。

---

## 规则 6 · `proposal.source` 必须可解析——**纠正仪器**

AC-004-b 的 given 是「one proposal **lacking a source assessment or gap id**」。
「lacking a source assessment or gap id」的宾语是 *a source assessment or gap id*，不是 *a non-empty string*：
键写着 `source: A-nonexistent` 的提案，缺的正是「一个 source assessment 或 gap id」。
`audit.schema.md` §Proposal 也已写明「`source` 必须指向一个 Assessment id 或 Gap id」，并且自己登记了这条空隙。

命名空间就两处，不含糊：`rings[].parts[].assessment.id`（本次 42 个，唯一）∪ `gaps[].id`（本次 73 个）。

> **谓词**：每条 `proposals[]` 的 `source` 必须是非空字符串，**且**等于某个 `rings[].parts[].assessment.id`
> 或某个 `gaps[].id`；否则 exit 1 `proposal_without_source`，并计入 `proposals_without_source`。

**token**：`proposal_without_source`（**沿用同一个**）。**这一点是有意的**：AC-004-b 的
`expect: {exit: 1, error: proposal_without_source}` 是冻结字节，若为悬空 id 另起一个 token，
则「把 source 改成悬空 id」这个最自然的 fixture 会吐出 AC 没写的 token，逼出一次契约字节修改。
用一个 token 覆盖「空」与「悬空」两种失败，AC-004-b 在两种 fixture 下都成立，**契约字节不用动**。
两种失败在 `errors[]` 的定位串里区分（`P-xx: source is empty` vs `P-xx: source 'A-foo' resolves to no assessment or gap`）。

**killing fixture 要有什么**：一条 `{id: P-99, source: A-does-not-exist, destination: new_issue, text: ...}`——
`source` 键非空、格式像模像样、但解析不到。必须 exit 1，`proposals_without_source: 1`。
这就是 holdout 的 `hv_proposal_dangling_source`，本次未命中的四条之一。

**契约字节**：不动。
**现行 audit.yaml**：通过——我对 39 条提案逐条解析，39/39 命中（26 → Assessment id，13 → Gap id），0 悬空，
与 G3 第 16 项的独立复算一致。

---

## 规则 7 · `alternatives_of`——**纠正到文档能自证的那一半，并把核不了的另一半明确标成空隙**

F-05 的三条件里：

| 条件 | 数据源 | 检查脚本能不能核 |
|---|---|---|
| (a) 两个 Part 在同一 `stage.<x>` 节点的 `handled_by` 里 | graph.yaml | **不能**（脚本不读 graph.yaml） |
| (b) 它们之间有一条带 `when` 守卫的 `conditional` 边选执行者 | graph.yaml | **不能** |
| (c) 它们写同一 schema 的 Artifact | audit.yaml 自身 | **能**——它们是同一个 `artifacts[].id` 的两条记录，(c) 由「同 id」结构性成立 |

所以「任意非空即豁免」太松，「按三条件核」则超出仪器的输入。裁法是**核文档自己能作证的形状，其余明确标空**：

> **谓词**：对每条带 `alternatives_of` 的 `artifacts[]` 记录 —— (i) 其值必须匹配 `^stage\.[A-Za-z0-9_.-]+$`；
> (ii) 同 `id` 的记录数必须 ≥ 2（单生产者上的豁免是装饰）；(iii) 同 `id` 的记录不得**每条**都带 `alternatives_of`
> （「alternatives_of」预设存在一个被替代的主分支）。任一不满足 → exit 1 `spurious_alternatives_of`。
> 条件 (a)(b) **不检**，`check_audit.py` 的 docstring 必须写明它们未被核，`known_gaps.yaml` 保留一条对应空隙。

**token**：`spurious_alternatives_of`（新增；与 `spurious_merge_candidate` 是同一条规则的两张脸——
规则 1 已立的「merge_candidate 不能当装饰撒」，这里是「alternatives_of 也不能」）。

**为什么不往前走一步**：把 (a)(b) 核起来需要给仪器加 `--graph graph.yaml` 输入，或给 Artifact 记录加一个
`alternatives_of_evidence: graph.yaml#L29,L320-321` 字段。**两者都动签字版形态**（F-13 的接口、F-05 的记录字段），
是新的 G1，不是解释。本文件不做，见「明确不做」。

**killing fixture 要有什么**（一正三反）：
- 正：保留 `card.allowed_files` 的现行形状——三条记录，`agent.card-implementer` 一条带 `alternatives_of: stage.implement`，
  另两条不带 → exit 0（若两条不带的都是 `merge_candidate`，`double_producer` 也不触发）。
- 反 1：`alternatives_of: implement`（不是 `stage.` 形状）→ exit 1。
- 反 2：某个只有一条记录的产物上标 `alternatives_of: stage.x` → exit 1。
- 反 3：同一产物两条记录**都**带 `alternatives_of: stage.x` → exit 1（这是最重要的一条：今天可以靠给双方都盖章
  把一次真的双生产者洗白成 `owners < 2`，`double_producer` 与 `spurious_merge_candidate` 双双不触发）。

**契约字节**：不动。
**现行 audit.yaml**：通过——全库唯一一条 `alternatives_of` 是 `card.allowed_files` / `agent.card-implementer` / `stage.implement`，
形状合规、同 id 有 3 条、并非全部带标。

---

## 规则 8 · `gates[].kind` 枚举外——**纠正仪器，这是 fail-open**

现行分支是 `if kind == "script": … elif kind == "human" and …:`。`kind` 写成 `human_gate`、`shell`、
或干脆没有这个键的记录，**两条 rule-3 谓词都不进**。后果不是漏一个小检查，而是给「把闸渲染成门」开了一条绕行道：
`{id: verify_x.py, kind: shell, label: 门}` 今天 exit 0。F-94 的原话是「以 `kind` 字段区分而不以名字区分」——
既然判定挂在这个字段上，这个字段本身就必须是封闭枚举，否则整条规则可被一个拼写绕过。

> **谓词**：每条 `gates[]` 记录的 `kind` 必须存在且 ∈ `{script, human}`；否则 exit 1 `gate_kind_outside_enum`，
> 且该记录**同时**照 `script` 与 `human` 两条规则各判一次（枚举外的脏值不因为脏就免检）。

**token**：`gate_kind_outside_enum`（新增；即 scope B 段的 mf-006）。

**killing fixture 要有什么**：`gates[]` 里两条——`{id: verify_x.py, kind: shell, label: 门}` 与
一条**没有 `kind` 键**的 `{id: G4, label: 门}` → exit 1，`gate_kind_outside_enum: 2`。
fixture 必须把 `label: 门` 一起写上：只有这样才看得出本裁堵的是「枚举外的 kind 顺带躲掉了 `script_gate_rendered_as_door`
与 `gate_not_declared`」这条绕行道，而不只是补一个孤立的枚举检查。

**契约字节**：不动（没有任何 AC 提到 `gates[].kind`；AC-006-a 是 human AC，走 G3）。
**现行 audit.yaml**：通过（31 条 Gate = 28 script + 3 human，枚举外 0）。

---

## 规则 9 · `disposition` 枚举——**签字版 F-16 governs，`audit.schema.md` 须改回**

`audit.schema.md` 在自己的开头写着：「**改这份文档不会改判定**，判定在 `check_audit.py` 里；
这份文档的责任是让内容卡不必读源码就写对。」一份自述为投影的下游文档，不能把签字版的三值枚举收成两值。
方向也很关键：schema 的 `{none, issue}` 是签字版 `{fix_list, issue, none}` 的**真子集**——
按 schema 编谓词，会拒掉一条 F-16 明文允许的 `disposition: fix_list`。**又是「正确的审计过不了自己检查脚本」那一类**，
所以不能按 schema 编。

`fix_list` 与 `destination` 之间也没有真冲突：F-16 自己就写了提案每条带 `destination`
（`{id, source, destination, text}`），它约束的是**提案条目往哪去**；`disposition` 约束的是
**Assessment / Gap 要不要长出提案、长成哪一类**。两个字段，不是一个字段的两种写法。

> **谓词一**：每个 `rings[].parts[].assessment.disposition` 与每个 `gaps[].disposition` 必须 ∈ `{fix_list, issue, none}`；
> 否则 exit 1 `disposition_outside_enum`。
> **谓词二**（F-16 同句的后半）：`assessment.naming.fit == misfit` 的 Part，其 `assessment.disposition` 只能是
> `issue` 或 `none`；写成 `fix_list` → exit 1 `misfit_disposition_outside_enum`。

**token**：`disposition_outside_enum`、`misfit_disposition_outside_enum`（均新增）。

**killing fixture 要有什么**（正反都要，否则会把「schema 读法」误当通过）：
- 正 1：一个 Assessment 写 `disposition: fix_list` → **必须 exit 0**。这一条是分辨两种读法的唯一判据——
  按 schema 编的谓词会在这里 exit 1。
- 正 2：一个 Gap 写 `disposition: fix_list` → exit 0。
- 反 1：`disposition: escalate` → exit 1 `disposition_outside_enum`。
- 反 2：`naming.fit: misfit` 且 `disposition: fix_list` → exit 1 `misfit_disposition_outside_enum`。

**连带（非契约、非锁）**：`audit.schema.md` 的 §Assessment 与 §Gap 两处 `none | issue` 改回
`fix_list | issue | none`，并补一句说明 `disposition` 与 `Proposal.destination` 各管什么。
该文件不在 `.done_when.lock` 的 43 项里，改它不撞锁、不需变更提案。

**契约字节**：不动。
**现行 audit.yaml**：通过——42 个 Assessment（22 none / 20 issue）+ 73 个 Gap（40 none / 33 issue）全在三值内；
唯一的 misfit（`R8/tune`）disposition 是 `issue`，满足谓词二。本裁对现有数据是纯放宽。

---

## 规则 10 · F-06 封顶（G3 已裁）——**确认「独占」读法，钉到 `part.artifact` 字段**

G3 在 `g3-record.md` 第 1 项与 mf-009 专条已裁：F-06 按**独占 Artifact** 读，不按「该 Part 沾到的每一个产物」读。
理由是 F-06 要防的是「配件为**自己的产品**索取未挣得的成熟度」；无闸的**副**产物是该登记的缺口（已登记 73 条里有），
不是对配件的降级。我确认这条裁法，本规则只解决「怎么写成谓词」。

**「独占」在数据里就是 Part 记录的 `artifact` 字段**（`audit.schema.md` §Part：「独占生产的产物；无产物写 null」）。
不是「`artifacts[]` 里 `producer` 等于它的每一条」。两者的差在本次数据上是可量的：

| 读法 | 被压到 declared 的 Part | 与 G3 裁决 |
|---|---|---|
| **独占**（本裁） | 无 | 一致 |
| 任一 | `R1/dos-extract`（因副产物 `decisions.md` 无闸）、`R7/review-loop`（因 `github:reply` / `github:resolve` 无闸） | **冲突**——G3 第 1 项点名 `dos-extract` 不该被压 |

即：「任一」读法会让一份 G3 判为正确的审计**过不了自己的检查脚本**。这是规则 1 立下的判据，也是本条不选它的理由。

> **谓词**：对每个 `artifact` 非 null 的 Part P（值为单个字符串），令 E = `artifacts[]` 中 `id == P.artifact`
> 且 `producer == P.id` 的那条记录。
> (i) E 不存在 → exit 1 `exclusive_artifact_unregistered`；
> (ii) E 存在且 `E.checked_by` 为空列表（或缺键）→ P 的 `assessment.implemented.verdict` **必须**是 `declared`，
> 是 `compiled` 或 `verified` → exit 1 `implemented_above_gate_cap`。
> 判定只看 E 一条，**不看** `producer == P.id` 的其它 `artifacts[]` 记录。

**token**：`implemented_above_gate_cap`、`exclusive_artifact_unregistered`（均新增）。

**killing fixture 要有什么**（三条，第二条最容易被漏掉）：
1. **封顶面**：一个 Part，其 `artifact` 指向的记录 `checked_by: []`，而 `implemented.verdict: compiled`
   → exit 1 `implemented_above_gate_cap`。照 mf-009 修复前的 `R8/tune` 原样造（`tune/harness-proposals-<date>.yaml`，
   `checked_by: []`，verdict `compiled`）——这是本次真实出现过的记录，不是编的。
2. **反过界面**（缺了它，「任一」读法会静默通过整个套件、G3 的裁决被无声推翻）：一个 Part，其**独占**产物有闸、
   而另有一条 `producer` 是它的**非独占**记录无闸，`implemented.verdict: compiled` → **必须 exit 0**。
   照 `R1/dos-extract` 原样造（`dos.yaml` / `checked_by: [verify_dos.py]` + `decisions.md` / `checked_by: []`）。
3. **登记面**：一个 Part 的 `artifact` 写了个 `artifacts[]` 里没有对应 `(id, producer)` 的值 → exit 1 `exclusive_artifact_unregistered`。

**与 F-17 的对账**（G3 Open Question 1 点名要做的）：本谓词读**整份文档**，不受 `--rings` 限定——
它属于 F-17 所说的「维度、Gap、Artifact、Gate、Proposal 谓词永远读整份文档」那一类。
`--rings` 只影响 `ring_missing` 的期望集、`parts_without_assessment` 的计数范围与 `--required-parts` 的查找池（规则 5）。
因此本谓词与 F-17 的「不改任何既有谓词」无冲突：它是**新增**谓词，不是对既有谓词的修改。

**本条不裁 F-06 的另一半**：F-06 的第二个后果——「一条 Control 原子的 Gap `{source: newly_identified}`
进该 Artifact 所在 Ring 的 missing」——不在 G3 Open Question 1 的问法里，也不在我被召来裁的七条里。
我复算了它在现行数据上成立（27 条无闸产物，其生产者所在的 7 个环全部至少有一条 `newly_identified` + Control 缺口，27/27），
但**成立不等于已裁**：它是否该编成谓词、编在环粒度还是产物粒度，留 B 段。见「明确不做」。

**契约字节**：不动。AC-003-a 数的是 `boolean_implemented` / `implemented_outside_enum` / `rename_true`，
三个 verdict 仍在三态枚举内，计数不变。
**现行 audit.yaml**：通过——违规计数 0。前提是 mf-009 的三处（`R6/human_gate.G3`、`R7/agent.pr-reviewer`、`R8/tune`）
**已按 G3 裁决改成 `declared`**（我在文件上复核过，三处均为 `declared`，`not_reached.compiled` 已写）。
若那三处还是 `compiled`，本谓词会给出 3 条 `implemented_above_gate_cap`——这正是它该有的行为。

---

## 明确不做

> 一行一条。凡是「会让本文件从解释变成改动」的写法，都列在这里，并写清它该去哪。

- **`ring_duplicate`** — KG-03 的「计数 10 vs 集合 10」不由本轮裁；它与 `--rings` 无关，去 B 段单独立谓词。
- **`waiver_ref`** — KG-01 的 `waived` 无授权引用，本轮不裁；规则 3(c) 已定「`waived` 只能引用 state.json 的 waiver 记录」，编字段与 token 去 B 段。
- **`signer_kind_outside_enum`** — KG-04 同理，本轮不裁，去 B 段。
- **`--graph <path>`** — 给 `check_audit.py` 加 graph.yaml 输入以核 F-05 条件 (a)(b)：改 F-13 的接口，是新的 G1，不是解释。
- **`alternatives_of_evidence`** — 给 Artifact 记录加 graph.yaml 行锚字段：改 F-05 的记录形态，是新的 G1，不是解释。
- **`exercised` / `not_exercised`** — 规则 3 已判这两个键不存在；本轮不复活，签字三元组仍只住 `run_evidence.gates[]`。
- **对 `artifact: null` 的 Part 封顶** — F-06 只对「有 Artifact 且其 `checked_by` 为空」发话；把封顶扩到没有产物的配件是新规则，不是收窄。
- **F-06 的缺口登记半条编成谓词** — 「无闸产物 ⇒ 其环 missing 里有一条 newly_identified 的 Control 缺口」本轮不裁，去 B 段（粒度问题：环粒度可算、产物粒度需新增链接字段）。
- **「闸 = 存在非零退出路径」写进规格** — G3 Open Question 2，需要人定，不由本轮解释代答。
- **「人签」** — 本文件的每一处签字都是代签（`delegated_agent`），任何下游投影不得渲染为人签（F-15、PSL-006）。
- **`disposition` 收成 `{none, issue}`** — 即使现行数据只用到这两值；收窄签字版枚举是形态改动，且会拒掉 F-16 明文允许的 `fix_list`。
- **改 `audit.yaml` 让它去迎合某条读法** — 七条裁定全部经复算对现行 `audit.yaml` 无失败；本文件不要求动数据一个字节。

---

## 对账 — 七条裁定在现行 `audit.yaml` 上的重跑

把七条写成脚本，对 `audit.yaml`（10 环 / 42 Part / 73 Gap / 58 Artifact 行 / 31 Gate / 39 Proposal）逐条执行：

| 规则 | 谓词 token | 失败计数 |
|---|---|---|
| 4 | `unknown_gap_ref`（fills 跨环放宽后） | 0 |
| 5 | `ring_unexpected`（恒执行） | 0 |
| 6 | `proposal_without_source`（须解析） | 0（39/39 命中） |
| 7 | `spurious_alternatives_of` | 0 |
| 8 | `gate_kind_outside_enum` | 0 |
| 9 | `disposition_outside_enum` / `misfit_disposition_outside_enum` | 0 / 0 |
| 10 | `implemented_above_gate_cap` / `exclusive_artifact_unregistered` | 0 / 0 |

**七条合计失败 0。** 结论：本轮解释**不推翻现行审计的任何一条判定**，也不要求改任何冻结字节；
它改的只是仪器——把三处过严（规则 4）与四处 fail-open（规则 5 的 ⊇ 方向、规则 6、规则 7、规则 8）纠正，
并把两条从未编译的规格（规则 9、规则 10）第一次编成谓词。

**这份对账本身是弱证据，别当强的用**：它证明的是「七条裁定与现行数据不冲突」，
**不**证明「七条裁定被机械执行过」——那要等 l5-tests 把 fixture 写出来、看它们由红转绿。
在那之前，上表每一个 0 都只是我这次复算的 0。

**摩擦（追加候选）**
- m. 本轮七条里有四条（规则 5 ⊇ 方向、规则 6、规则 7、规则 8）是同一种病：**谓词在某个分支上静默不执行**，
  而输出 JSON 里对应计数照样是 0——「0」既表示「检了没问题」也表示「没检」。建议给 `check_audit.py` 的输出
  加一个 `predicates_evaluated[]`，让「没检」和「检了是 0」在字面上分开。这是 I-82（`checks_green` 拆三态）
  与 I-83（`review.done` 拆 `done | waived`）的同一个病的第三个实例。
- n. 规则 4 / 9 / 10 三条都是「下游文档（`check_audit.py` docstring、`audit.schema.md`、卡面 notes）
  与签字版不一致，而没有任何机械检查发现」。建议 `verify_derived.py` 或一个新的小脚本核对
  「下游文档里出现的枚举 / 谓词名」是否是签字版枚举的子集且未收窄。
