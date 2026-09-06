# 九环审计 — sdlc-ring-audit

本文件是 `plugins/sdlc/dogfood/ring-audit/audit.yaml` 的投影（F-12：两者同目录，**不一致时以 yaml 为准**）。
审计是否完整由退出码说话，不由本文的散文说话（F-13 / PSL-006）——判定在 `plugins/sdlc/dogfood/ring-audit/check_audit.py`。

| 项 | 值 |
|---|---|
| 机器可读半边 | `plugins/sdlc/dogfood/ring-audit/audit.yaml` |
| 判定脚本 | `plugins/sdlc/dogfood/ring-audit/check_audit.py` |
| 本文件的生成方式 | `python3 plugins/sdlc/dogfood/ring-audit/render_audit.py`（确定性、可重跑） |
| 规律来源 | `plugins/sdlc/dogfood/ring-audit/PSL-sdlc-ring-audit.md` |
| check-audit 对本文档 | exit 0 |
| check-audit 删环变体 | exit 1（F-14 校准孪生已记录） |
| 规模 | 10 环 · 42 配件 · 79 缺口 · 38 处登记为缺少 · 58 条产物-生产者 · 45 条提案 |

## 读法

- **implemented 是三态，不是布尔**（PSL-010）：`declared` 只有 SKILL.md / 提示 · `compiled` 有 verify 脚本或被门挡 ·
  `verified` 有行为层运行记录。本报告任何一处都不写「已实现 ✓」——那是布尔，`check_audit.py` 会 exit 1。
- **闸不是门**（PSL-006）：`kind: script` 的 Gate 一律写「闸」，`kind: human` 的三道门 G1 / G2 / G3 才写「门」。
- **代签不是人签**（F-15）：`signer_kind: delegated_agent` 一律渲染为「代签（delegated）」。
- **缺口四原子**（PSL-016）：Knowledge / Capability / Judgment / Control。
- **来源三种**（PSL-017）：lifecycle_blank（生命周期自列的空白）· newly_identified（本次新识别）·
  unenforced_rule（宪法写了规则、机器一侧无闸）。

<a id="ring-tables"></a>

# 环表（R0…R8 · spine）

## R0 世界

**问题**：这个产品为什么这样运转

3 个配件 · 2 处登记为缺少。

| 配件 / 缺少 | kind | 缺口 · 原子 | 独占产物 / 角色 | 闸 · 门 | artifact 闸（checked_by） | Loop | needed | implemented | naming |
|---|---|---|---|---|---|---|---|---|---|
| `psl` [^A-psl] | `skill` | `Knowledge+Judgment` world-before-form | `PSL-<feature>.md` | 闸 `verify_psl.py` | `PSL-<feature>.md` → `verify_psl.py` | `loops.yaml#lifecycle` | **necessary** | **compiled**<br>未达：`verified` | adopted → **fits** |
| `psl-derive` [^A-psl-derive] | `skill` | `Judgment+Control+Capability` derivation-traceability | `derived/**` | 闸 `verify_derived.py`<br>门 `G1` | `derived/**` → `verify_derived.py`、`G1` | `null` | **necessary** | **compiled**<br>未达：`verified` | authored → **fits** |
| `human_gate.G1` [^A-G1] | `human_gate` | `Control` world-verdict-door | `g1-record.md`<br>role `gate` | 闸 `sdlc_state.py` | `g1-record.md` → `sdlc_state.py` | `loops.yaml#lifecycle` | **necessary** | **compiled**<br>未达：`verified` | authored → **fits** |
| **（缺少）** `psl-reference-lint` | — | `Capability`<br>**lifecycle_blank（生命周期自列的空白）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：PSL 内部的 PSL-ID 交叉引用断链不被发现；psl-derive 的"每条决策 ← PSL-ID"校验拿到的是一份自身引用就残缺的 PSL，锚看似成立实则指空。<br>证据：`file:plugins/sdlc/docs/lifecycle.md#制品映射v12-制品--本插件--邻居--状态（产品级/功能级 PSL 行：已有，说明列"引用完整性 lint 未实现"）`<br>disposition `issue` | — | — |
| **（缺少）** `g1-external-evidence` | — | `Control`<br>**lifecycle_blank（生命周期自列的空白）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：G1 通过时"外部证据"只是记录模板里的一行 checklist，没有它照样 pass；本次审计只能以 substitute 顶替，门的证据强度不可度量，代签与人签在这一维上无差别。<br>证据：`file:plugins/sdlc/docs/lifecycle.md#制品映射v12-制品--本插件--邻居--状态（G1 世界裁决 行：说明列"外部证据只是 checklist 项"）` · `file:plugins/sdlc/skills/sdlc/assets/g1_record.md`<br>disposition `issue` | — | — |

### R0 判定详情

#### `psl` — A-psl（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后引擎按字面实现需求——"按时间搜索记忆"交出一个 created_at 字段加日历筛选器，产物技术正确、产品错误；且这类世界层错误一路漏到 R6 验收才暴露，回流要走 routing 的 world 层（无自动上限）。
    - 证据：`file:plugins/sdlc/skills/psl/SKILL.md#缺口` · `file:plugins/sdlc/docs/ARCHITECTURE.md#1-九环与一根脊柱`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：无带 / 不带 skill 的对比运行（gate.json tier2_status NOT RUN，T1–T5 未跑）；本 Run 产出了 PSL-sdlc-ring-audit.md，但产物存在不等于对比跑过，也没有 verify_psl.py 对它的运行记录。
    - 闸的保留：verify_psl.py 是"交付前必须跑"的声明式预门，未挂 hooks.json——gate.json fix_list 第一条即此（A'-1）。它构成 compiled，不构成不可跳过。
    - 重审更正：重审补记（2026-09-06）：gate_caveat 保持原判，并有一条现场核实——plugins/sdlc/ 下至今没有任何 plugin 级 hooks.json，skills/sdlc/assets/hooks/stop-clean-state.json 仍是未安装的模板， 所以「声明式预门、未挂 hooks」这句在 HEAD 上仍逐字为真，不是过期结论。 verify_psl.py 的检查面则变了（本轮 +177 行）：#L311-L321 拒绝无 PSL-NNN id 与重复 id （I-02，与 verify_derived.py 那条拒绝对齐，两道闸说同一句话），并按 form / content 分层输出 info， 决定下游 verify_derived.py 对哪些规律做未被引用 flag。
    - 证据：`file:plugins/sdlc/skills/psl/scripts/verify_psl.py` · `gate_json:plugins/sdlc/skills/psl/eval/gate.json#gate_pass` · `run_record:plugins/sdlc/dogfood/ring-audit/PSL-sdlc-ring-audit.md`
- **naming adopted → `fits`** — 位置 / 产物：`PSL-<feature>.md`
    - 贴合理由：收编自 looper v0.2.0，保留上游名；名字与独占产物 PSL-*.md 同词干，按 F-03 判 fits（收编不是免检，此处是真判过）。
    - 证据：`gate_json:plugins/sdlc/skills/psl/eval/gate.json#imported_into_sdlc.from` · `file:plugins/sdlc/docs/design-notes.md#直接收编整-skill-复制进本插件正文保留加术语映射--接线`
- **Loop `loops.yaml#lifecycle`**：graph.yaml#L311 的 loop_back（signal counterexample_cites_psl_rule）以 psl 为落点，环归属 lifecycle
- disposition `none`

#### `psl-derive` — A-psl-derive（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后 derived/ 四文件不存在，形态在实现里"顺手"定；G1 拿不到可裁之物，门空转——验收时出现"AC 全绿但交付的不是要的形态"，且无法归因"推错了 vs 规律错了"（每条决策 ← PSL-ID 的锚消失）。
    - 证据：`file:plugins/sdlc/skills/psl-derive/SKILL.md#缺口judgment--control--capability` · `file:plugins/sdlc/docs/design-notes.md#直接收编整-skill-复制进本插件正文保留加术语映射--接线`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：gate.json fix_list 明写 "L2：run N=3 isolated derivations on one real PSL and hold a real G1" 未做；本 Run 的 derived/ 有 v1/v2/v3 三稿，但那是同一推导者的三轮修订，不是 N 次隔离推导的分歧集，也不是带 / 不带 skill 的对比。
    - 重审更正：重审补记（2026-09-06）：判定不变（fix_list 的 "run N=3 isolated derivations and hold a real G1" 仍在）， 但"三轮修订不受任何机械约束"这层背景已不成立：verify_derived.py 本轮 +227 行，多轮推导现在有闸—— --round N 起，上一轮必须归档在 round{N-1}/ 且四件产物齐全、必须有 round-diff.md 且真的引用 round{N-1}/、 divergence.md 必须自报 round: N 且从第 2 轮起带「裁决 → 落点」表，缺一即 REJECT。 并更正一处容易误记的因果：「form-draft 引用不存在的 PSL id」这条拒绝**不是**本轮新增， 装配前就在；本轮新增的是 UI-n / A-n / DP-n 三类锚与 F-<digits> id 格式的拒绝。
    - 证据：`file:plugins/sdlc/skills/psl-derive/scripts/verify_derived.py` · `gate_json:plugins/sdlc/skills/psl-derive/eval/gate.json#gate_pass` · `run_record:plugins/sdlc/dogfood/ring-audit/derived/form-draft.md`
- **naming authored → `fits`** — 位置 / 产物：`derived/**`
    - 贴合理由：新写（gate.json 无 imported_into_sdlc 块），按产物命名；derive 与产物目录 derived/ 同词干，F-03 判 fits。
    - 证据：`file:plugins/sdlc/docs/design-notes.md#直接收编整-skill-复制进本插件正文保留加术语映射--接线` · `file:plugins/sdlc/skills/psl-derive/SKILL.md`
- disposition `none`

#### `human_gate.G1` — A-G1（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后形态草案由生产它的引擎自评通过（评估者 = 被评估者），PSL 与形态之间的分歧集无人裁；一次错误的形态推导直接进 issue 与契约，R2 之后每一件产物都建在它上面，返工要退回 world 层。
    - 证据：`file:plugins/sdlc/docs/ARCHITECTURE.md#32-三道门只能人签` · `file:plugins/sdlc/skills/sdlc/assets/g1_record.md`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：门本身在本 Run 走过两轮（第一轮否决），但签字人是 delegated_agent 代签，不是人签；PSL-006 下代签不得渲染为人签，因此"人签的门跑通了"这一层没有证据。重审补记（2026-09-06）：结论不变，但"代签与人签在机器一侧无差别"这层事实没了——sdlc_state.py 现在要求 --signer-kind human|delegated_agent（#L980 required），代签缺 --authorization 即 die（#L497），signer_kind 与 authorization 进 state.gates.<g> 与 ledger，trace 的 decided_by 也分 human: / agent: 前缀。代签因此是被记录且被约束的一等状态，但脚本从不拒绝一次代签本身，所以"只能人签"这条宪法仍未编译（见 spine/unenforced_rule/control/r008-human-signer）。
    - 闸的保留：sdlc_state.py gate g1 检的是状态字段（pass 要求 world.derived_dir、reject 要求 attribution），不是 g1-record.md 的内容——是部分检，不是对产物的完整闸。
    - 证据：`file:plugins/sdlc/skills/sdlc/assets/g1_record.md` · `gate_json:plugins/sdlc/skills/sdlc/eval/gate.json#provenance.scripts_run.sdlc_state.py` · `run_record:plugins/sdlc/dogfood/ring-audit/g1-record.md`
- **naming authored → `fits`** — 位置 / 产物：`G1（世界裁决门，ARCHITECTURE §1 R0 门闸列）`
    - 贴合理由：名字是位置名（三道门里的第一道，裁世界），F-03 的"位置名"分支判 fits。
    - 证据：`file:plugins/sdlc/docs/ARCHITECTURE.md#32-三道门只能人签`
- **Loop `loops.yaml#lifecycle`**：graph.yaml#L311 的 loop_back 由 human.g1 出发，环归属 lifecycle
- disposition `none`

[^A-psl]: `psl` 的 PSL-ID 追溯 — needed PSL-002, PSL-016 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L48-L53（Node.role=world → R0）`。
[^A-psl-derive]: `psl-derive` 的 PSL-ID 追溯 — needed PSL-002, PSL-003 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L54-L59（Node.role=world → R0）`。
[^A-G1]: `human_gate.G1` 的 PSL-ID 追溯 — needed PSL-006, PSL-003 · implemented PSL-006, PSL-010 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L60-L66（Node.role=gate，非环角色；按 F-08 归其所检产物 derived/** 所在环 R0，并与 ARCHITECTURE.md §1 表 R0 门闸列的 G1 一致，两源不冲突）`。

## R1 本体

**问题**：系统里有什么、叫什么、什么不可违反

2 个配件 · 3 处登记为缺少。

| 配件 / 缺少 | kind | 缺口 · 原子 | 独占产物 / 角色 | 闸 · 门 | artifact 闸（checked_by） | Loop | needed | implemented | naming |
|---|---|---|---|---|---|---|---|---|---|
| `dos-extract` [^A-dos-extract] | `skill` | `Knowledge+Capability+Judgment` shared-ontology<br>`Control` dos-proposal-reconcile（**重审：已填**，详见判定详情） | `dos.yaml` | 闸 `verify_dos.py` | `dos.yaml` → `verify_dos.py`<br>`decisions.md` → **（无闸 → 封顶 declared）** | `null` | **necessary** | **compiled**<br>未达：`verified` | adopted → **fits** |
| `invariant-extract` [^A-invariant-extract] | `skill` | `Judgment+Control+Capability` resident-invariants | `invariants/*.yaml` | 闸 `verify_card.py` | `invariants/*.yaml` → `verify_card.py` | `null` | **necessary** | **compiled**<br>未达：`verified` | adopted → **fits** |
| **（缺少）** `ontology-drift` | — | `Knowledge+Control`<br>**lifecycle_blank（生命周期自列的空白）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：代码演化后本体与代码分叉不被发现，dos.yaml 变成一份过期宪法；verify_issue.py --dos 拿过期词表判新 issue，闭包"通过"反而掩盖了真实的词表缺口。<br>证据：`file:plugins/sdlc/docs/ARCHITECTURE.md#7-覆盖矩阵与空白（X1 行：ontology-drift 空白）` · `file:plugins/sdlc/docs/lifecycle.md#十个裁决在本插件里的落点（C5 drift 两义：ontology-drift 本体层 空白）`<br>disposition `issue` | — | — |
| **（缺少）** `dos-candidate-namespace` | — | `Knowledge`<br>**lifecycle_blank（生命周期自列的空白）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：新名词没有候选态可落，要么被硬塞进 dos.yaml 触发 ≤7 objects 的无条件拒绝，要么以非本体词在 issue 与卡里流通——两条路都让词表闭包检查失去意义。<br>证据：`file:plugins/sdlc/docs/ARCHITECTURE.md#7-覆盖矩阵与空白（X1 行：candidate 命名空间 空白）`<br>disposition `issue` | — | — |
| **（缺少）** `decisions-md-no-gate` | — | `Control`<br>**newly_identified（本次审计新识别）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：decisions.md 可以为空、可以与 dos.yaml 矛盾而无人发现——这半句仍真。另半句要按重审（2026-09-06）分开算：整词 UI/impl 名的豁免路径已经落地（verify_dos.py 的 parse_waivers 读 `## Naming waivers`，#L182-L185 把 REJECT 降级成 FLAG），那条不再指向空气；但 ">7 objects" 那条拒绝的措辞仍写着 "exceed only with a human waiver in decisions.md"，代码里却是无条件 reject、从不查 waivers（#L167-L189）。同一个文件里两条豁免路径，一条通了，一条仍指向空气。<br>证据：`file:plugins/sdlc/skills/dos-extract/scripts/verify_dos.py#L169` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L73`<br>disposition `issue` | — | — |

### R1 判定详情

#### `dos-extract` — A-dos-extract（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后 issue 的 DOS 词表闭包没有解析源、卡的 dos_slice 没有来源，verify_issue.py --dos 与 lint_cards.py --dos 退化成不检；产出的 issue 与卡里同一个对象带三个名字，且"该转 PSL 轨"的客观触发（闭包失败）永远不会触发。
    - 证据：`file:plugins/sdlc/skills/dos-extract/SKILL.md#the-gap-why-a-scan-is-not-an-ontology` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L314-L315`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：gate.json tier2_status NOT RUN——需要 held-out repo 上带 / 不带 delta_exist 的对比；本 Run 产出了 dos.yaml 与 decisions.md，但没有对比臂。
    - 无闸：decisions.md（graph.yaml#L73 的第二个 writes）仍无闸，但重审更正（2026-09-06）：它不再是无人读。verify_dos.py --decisions 解析它的 `## Naming waivers` 节（#L73-L96），整词 UI/impl 名的 REJECT 由那里的一条豁免降级成 FLAG（#L182-L185），smoke 有一对孪生期望盯着这条路。检的仍然是 dos.yaml——decisions.md 自身为空、内容与 dos.yaml 矛盾、或豁免写错格式，都只表现为"没豁免成功"，没有任何非零退出路径指向 decisions.md 本身。而且同一个文件里两条豁免路径只通了一条：>7 objects 那条拒绝（#L167-L189）的措辞仍写着 "exceed only with a human waiver in decisions.md"，代码里却是无条件 reject、从不查 waivers。Gap R1/newly_identified/control/decisions-md-no-gate 仍开着；按独占产物 dos.yaml 有闸，不把本 Part 压回 declared。
    - 证据：`file:plugins/sdlc/skills/dos-extract/scripts/verify_dos.py` · `gate_json:plugins/sdlc/skills/dos-extract/eval/gate.json#gate_pass` · `run_record:plugins/sdlc/dogfood/ring-audit/dos.yaml`
- **naming adopted → `fits`** — 位置 / 产物：`dos.yaml`
    - 贴合理由：收编自 looper v0.2.0，保留上游名；名字与独占产物 dos.yaml 同词干，F-03 判 fits。
    - 证据：`gate_json:plugins/sdlc/skills/dos-extract/eval/gate.json#imported_into_sdlc.from`
- **填上的缺口 `R1/lifecycle_blank/control/dos-proposal-reconcile`**：已填（重审 2026-09-06）：新脚本 reconcile_dos.py 就是这条缺口点名的应然↔现状对账 —— --as-is dos.yaml 与 --to-be derived/dos-proposal.yaml 逐对象逐规则比，输出 dos-reconciled.yaml， 把映射上的 to-be 名折成 as-is 对象的 synonyms，于是下游只剩一个闭包源。它是真闸不是报告工具： 有 to-be 对象找不到 as-is 对应、或同一 rule id 在两份本体里说两件事，verdict=INCOMPLETE 且 return 1； --map 指向不存在的 as-is 对象 return 2；只有 --allow-unmapped 才写文件，并把未映射的名字记进 open_questions。它明确拒绝自己发明映射（docstring: "What it never does: invent a mapping"）。 **填的是机械半边，不是编排半边**：reconcile_dos.py 没有进 graph.yaml、没有 hooks、 没有任何上游强制它跑，产出的 dos-reconciled.yaml 也还没在 artifacts[] 里登记。 FILLS 边因此挂上，但这条缺口的编排半边转由 R5/newly_identified/control/gate-json-stale-after-script-lands 同类的"脚本落地了、周边没跟上"问题承接。
- disposition `none`

#### `invariant-extract` — A-invariant-extract（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后从失败里学到的 □ 不变量没有落点，spec-compile 只剩 done_when 一个编译源；同一类事故第二次发生时账本里没有可引用的不变量卡，routing 把它当一次新失败在 card 层重跑——付过学费的知识不进制品。
    - 证据：`file:plugins/sdlc/skills/invariant-extract/SKILL.md#the-gap-why-the-engine-cant-just-read-them-off-the-code` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L316`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：gate.json tier2_status NOT RUN——需要一个带真实 failure.memory 的 Territory 上的带 / 不带对比；本 Run 产出了一张不变量卡，无对比臂。
    - 重审更正：重审补记（2026-09-06）：verify_card.py 本轮 +212 行，检查面宽了一大截，旧 evidence 会低估它的承重—— 新增拒绝：hard 不变量必须 disposition: propose、低置信必须 propose、carded 条目的 altitude 必须是 territory 级、◊ 候选不得同时以 □ 入卡、channel_2_input.failure_memory_count 有数无 sources、 registered_gaps 条目缺 destination；新增 flag：与 dos.yaml 规则的近重复检测（--near-duplicate，默认 0.6）、 缺 narrowest_rule_note。gate.json dogfood_fixes 记 I-24…I-29 六条，13 条新 smoke 期望， 每条都跑过变异证明。tier2_status 仍是 NOT RUN，implemented 维持 compiled。
    - 证据：`file:plugins/sdlc/skills/invariant-extract/scripts/verify_card.py` · `gate_json:plugins/sdlc/skills/invariant-extract/eval/gate.json#gate_pass` · `run_record:plugins/sdlc/dogfood/ring-audit/invariants/sdlc-plugin.card.yaml`
- **naming adopted → `fits`** — 位置 / 产物：`invariants/*.yaml`
    - 贴合理由：收编自 looper v0.2.0，保留上游名；名字与独占产物 invariants/*.yaml 同词干，F-03 判 fits。
    - 证据：`gate_json:plugins/sdlc/skills/invariant-extract/eval/gate.json#imported_into_sdlc.from`
- disposition `none`

[^A-dos-extract]: `dos-extract` 的 PSL-ID 追溯 — needed PSL-002, PSL-016 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L69-L74（Node.role=knowledge → R1）`。
[^A-invariant-extract]: `invariant-extract` 的 PSL-ID 追溯 — needed PSL-002, PSL-005 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L75-L80（Node.role=knowledge → R1）`。

## R2 契约

**问题**：什么算做完

4 个配件 · 4 处登记为缺少。

| 配件 / 缺少 | kind | 缺口 · 原子 | 独占产物 / 角色 | 闸 · 门 | artifact 闸（checked_by） | Loop | needed | implemented | naming |
|---|---|---|---|---|---|---|---|---|---|
| `issue` [^A-issue] | `skill` | `Judgment+Capability+Control` falsifiable-task-seed | `github:issue` | 闸 `verify_issue.py` | `github:issue` → `verify_issue.py` | `null` | **necessary** | **compiled**<br>未达：`verified` | authored → **fits** |
| `donewhen-extract` [^A-donewhen-extract] | `skill` | `Judgment+Capability+Control` falsifiable-acceptance | `done_when.yaml` | 闸 `verify_done_when.py`<br>闸 `validate_done_when_v2.py`<br>门 `G2` | `done_when.yaml` → `verify_done_when.py`、`validate_done_when_v2.py`、`G2` | `null` | **merge_candidate**<br>与 `acceptance-spec` 并列 | **compiled**<br>未达：`verified` | adopted → **fits** |
| `acceptance-spec` [^A-acceptance-spec] | `skill` | `Judgment+Capability+Control` falsifiable-acceptance | `specs/<f>/spec.md` | 闸 `validate_done_when.py`<br>门 `G2` | `done_when.yaml` → `validate_done_when.py`、`G2`<br>`specs/<f>/spec.md` → **（无闸 → 封顶 declared）**<br>`specs/<f>/spec-robustness.md` → **（无闸 → 封顶 declared）** | `null` | **merge_candidate**<br>与 `donewhen-extract` 并列 | **declared**<br>未达：`compiled` / `verified` | adopted → **fits** |
| `human_gate.G2` [^A-G2] | `human_gate` | `Control` contract-freeze-door | `.done_when.lock`<br>role `gate` | 闸 `lock_done_when.py`<br>闸 `sdlc_state.py` | `.done_when.lock` → `lock_done_when.py`、`sdlc_state.py` | `null` | **necessary** | **compiled**<br>未达：`verified` | authored → **fits** |
| **（缺少）** `interface-contract` | — | `Knowledge+Control`<br>**lifecycle_blank（生命周期自列的空白）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：观察边界与接口形状没有契约承载，verify_issue.py 只 flag observe 未解析；下游测试各按自己理解的接口写，红-绿在互不相容的接口假设上各自成立，集成时才炸。<br>证据：`file:plugins/sdlc/docs/ARCHITECTURE.md#7-覆盖矩阵与空白（L2 接口契约 行：承载 —，状态 空白）` · `file:plugins/sdlc/docs/lifecycle.md#制品映射v12-制品--本插件--邻居--状态（接口契约 行）`<br>disposition `issue` | — | — |
| **（缺少）** `clarify-round-budget` | — | `Control`<br>**lifecycle_blank（生命周期自列的空白）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：澄清轮次上限与假设台账只是 SKILL.md 里的判据，没编译进任何脚本；引擎可以问到第九轮，也可以一轮不问就收工并把未知当已知填进契约，台账空不空无人检。<br>证据：`file:plugins/sdlc/docs/lifecycle.md#制品映射v12-制品--本插件--邻居--状态（澄清 + 假设台账 行：说明列"3 轮上限是判据，未编译"）`<br>disposition `issue` | — | — |
| **（缺少）** `spec-md-no-gate` | — | `Control`<br>**newly_identified（本次审计新识别）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：spec.md 与 spec-robustness.md 可以是空壳、也可以与 done_when.yaml 互相矛盾而照样过 G2；spec-gaming-detector 拿到一份 surfaced_vectors 为空的输入，仍然会报"无作弊迹象"——一条永远绿的判据线。<br>证据：`file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L99` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L183` · `file:plugins/sdlc/docs/ARCHITECTURE.md#1-九环与一根脊柱（R2 行门闸列只有 verify_issue.py / verify_done_when.py / validate_done_when_v2.py / G2）`<br>disposition `issue` | — | — |
| **（缺少）** `gaming-band-unvalidated-at-r2` | — | `Control`<br>**newly_identified（本次审计新识别）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：本轮给 done_when.yaml 加了新字段 gaming_risk_threshold（done_below / block_at_or_above，acceptance-spec 的 v1 schema 与模板都写了它），但 R2 侧的两个校验器 都不认识它：acceptance-spec 自己的 validate_done_when.py 本轮一个字节未动、没有这个 字段的任何校验（它只对 spec_drift_threshold 做 extra_keys 检查），donewhen-extract 的 validate_done_when_v2.py 里连这个词都不出现。唯一校验它的是 R6 的 acceptance-fleet/scripts/next_iteration.py:156-165（未知子字段 / 非数字 / 带反的区间 → die(…, 1)）。后果：一份 done_below=7 / block_at_or_above=3 的倒挂契约在 R2 判为 clean、被 G2 冻进 .done_when.lock，直到 R6 第一次 ratchet 才炸；那时改契约要走变更提案 走回 G2，代价从「写契约时改一行」变成「解冻一份已签字的契约」。<br>证据：`file:plugins/sdlc/skills/acceptance-spec/references/done-when-schema.yaml#gaming_risk_threshold` · `file:plugins/sdlc/skills/acceptance-fleet/scripts/next_iteration.py#L156-L165` · `file:plugins/sdlc/skills/acceptance-spec/scripts/validate_done_when.py`<br>disposition `issue` | — | — |

### R2 判定详情

#### `issue` — A-issue（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后需求原文直接当 issue body——"让搜索更快"这种任何实现都能通过的 issue 进入流水线；donewhen-extract 没有可证伪的源头，pr 的 AC→证据映射无基准，review 判"越界"也无基准。产出的是一条永远不会失败的验收线。
    - 证据：`file:plugins/sdlc/skills/issue/SKILL.md#缺口judgment--capability--control` · `gate_json:plugins/sdlc/skills/issue/eval/gate.json#provenance.scripts_run.verify_issue.py`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：gate.json fix_list 明写 gh issue create / edit 路径未跑（需要 live repo），DOS 闭包触发 PSL 轨这件事也只在 fixture 上验过，没有带 / 不带 skill 的对比。
    - 重审更正：重审补记（2026-09-06）：verify_issue.py 本轮 +86 行，两处结构性变化——DOS 闭包改为 import dos-extract/scripts/dos_closure.py 这一个共享 resolver（lint_cards.py import 同一个），闭包现在认 objects.synonyms / rules.aliases；新增 --g1 读 g1-record.md 与 g1-interpretations.md 的「明确不做」节。 要点是这两条都**不构成闸**：--g1 的交叉核对只产 flag 不产 reject，按"闸 = 存在非零退出路径"的定义 它不构成对 g1-record.md 的闸，g1-record.md 的 checked_by 不因此改变；dos_closure import 失败时 降级为 flag，--dos 在邻居 skill 缺席时是 fail-open 的。implemented 维持 compiled， 因为正文里 20 余条 rejects.append 是真拒绝。
    - 证据：`file:plugins/sdlc/skills/issue/scripts/verify_issue.py` · `gate_json:plugins/sdlc/skills/issue/eval/gate.json#gate_pass` · `run_record:plugins/sdlc/dogfood/ring-audit/issue-body.md`
- **naming authored → `fits`** — 位置 / 产物：`github:issue`
    - 贴合理由：新写（gate.json 无 imported_into_sdlc 块；design-notes 把它列在"直接改编"——借的是 qanat 三纪律与 looper 双轨判据，不是整 skill 收编），按产物命名，F-03 判 fits。
    - 证据：`gate_json:plugins/sdlc/skills/issue/eval/gate.json#provenance` · `file:plugins/sdlc/docs/design-notes.md#直接改编`
- disposition `none`

#### `donewhen-extract` — A-donewhen-extract（state: evidenced）

- **needed `merge_candidate`** — 撤掉后：撤掉后引擎把 issue 复述成 done_when——"信号诉求被兑现"这类不可证伪套话；G2 冻结的是一份任何产出都能通过的契约，A 档一票否决永远不触发，隐藏变体集也无从生成。配件本身必要，判 merge_candidate 是因为产物有争，不是因为不必要。
    - 并列生产的判定：done_when.yaml 有两个非豁免生产者。按 F-05 三条件逐条判：(a) 满足——graph.yaml#L26 stage.contract 的 handled_by 同时含两者；(b) 不满足——两者之间没有带 when 守卫的 conditional 边（对照 L320-L321 implement→card-implementer/ratchet 那种真替代）；(c) 不满足——一个产 v2、一个产 v1 需经 convert_v1_to_v2.py 转，不是同 schema。三缺二 → 不豁免 → 双方都标 merge_candidate，审计者不当场裁掉一个。
    - 证据：`file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L26` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L89-L100` · `file:plugins/sdlc/docs/design-notes.md#2026-09-05-第二次整理按逻辑重拆用户要求产研自闭环自洽覆盖方方面面` · `file:plugins/sdlc/skills/donewhen-extract/SKILL.md#the-gap-why-the-engine-cant-just-paraphrase-the-issue`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：gate.json tier2_status NOT RUN——需要一批带 failure_memory 的真实 Issue 上的带 / 不带对比；本 Run 产出了 done_when.yaml 与 done_when_card.yaml，无对比臂。
    - 重审更正：重审补记（2026-09-06）：validate_done_when_v2.py 本轮 +73 行——新增 --form-draft（每个 expect 键 必须是签字版形态草案里点过名的谓词，否则 REJECT，I-40）、given 必须是具名前置条件的 mapping、 human AC 的 statement 含无阈值模糊词即拒。needed.merge_reason 的 F-05 三条件判定重核过**仍然成立**： acceptance-spec 本轮只改了 SKILL.md 版本号与两份 reference，scripts/validate_done_when.py 一个字节未动， 仍是 v1 校验器，所以"一个产 v2、一个产 v1"这条不豁免的理由不变。
    - 证据：`file:plugins/sdlc/skills/donewhen-extract/scripts/validate_done_when_v2.py` · `gate_json:plugins/sdlc/skills/donewhen-extract/eval/gate.json#gate_pass` · `run_record:plugins/sdlc/dogfood/ring-audit/done_when.yaml`
- **naming adopted → `fits`** — 位置 / 产物：`done_when.yaml`
    - 贴合理由：收编自 qanat，保留上游名；名字与独占产物 done_when.yaml 同词干（donewhen / done_when），F-23 把这一条点名为 fits 的样例。
    - 证据：`gate_json:plugins/sdlc/skills/donewhen-extract/eval/gate.json#imported_into_sdlc.from`
- disposition `issue`

#### `acceptance-spec` — A-acceptance-spec（state: evidenced）

- **needed `merge_candidate`** — 撤掉后：撤掉后 EARS spec.md 与 spec-robustness.md 无人生产：spec-gaming-detector 失去它的输入（graph.yaml#L183 明列 spec-robustness.md 为 reads），pm-reviewer 的 REQ 归一化没有权威源，R6 少两条判据线。done_when.yaml 一侧不受影响（v2 由 donewhen-extract 独立产出）——这正是"两者只在 done_when.yaml 上争"的证据，也是 merge 只该合掉重叠面的理由。
    - 并列生产的判定：同 A-donewhen-extract 的 F-05 三条件判定；本 Part 的独占产物是 spec.md / spec-robustness.md，与 donewhen-extract 争的只有 done_when.yaml 这一件。
    - 证据：`file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L26` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L95-L100` · `file:plugins/sdlc/docs/ARCHITECTURE.md#2-制品链一个产物只有一个生产者`
- **implemented `declared`** — declared（只有 SKILL.md / 提示）
    - 未达 `compiled`：no_gate——本 Part 独占的两件产物 specs/<f>/spec.md 与 specs/<f>/spec-robustness.md 的 checked_by 为空。重审更正（2026-09-06）：装配时写的是"全插件 31 个 scripts/*.py 里没有一个读 spec.md"，两处都错——HEAD 上是 36 个 skills/*/scripts/*.py，其中四个**读** spec.md（本 Part 自己的 validate_done_when.py:264、donewhen-extract 的 validate_done_when_v2.py 与 convert_v1_to_v2.py、plan-cards 的 lint_cards.py）。但判定不变，因为读 ≠ 检：它们把 spec.md 当参照语料去判**别的**产物，spec.md 缺失即静默跳过，唯一源自 spec.md 内容的发现（spec.req_not_in_based_on）是 warn 而非 error，且 validate_done_when.py 不传 --check 时恒 exit 0（#L288-L291）。没有一条非零退出路径以 spec.md 为对象。spec-robustness.md 仍只在 verify_graph.py:31 的 FORBIDDEN_CARRY_TOKENS 里作禁带词出现，不是被检。它自带的 validate_done_when.py 检的是它产的 v1 done_when.yaml——那件产物是与 donewhen-extract 有争的那件，不是它的独占产物。按 F-06 封顶 declared，审计者不得以"读了 SKILL.md 觉得能跑"抬到 compiled。
    - 未达 `verified`：无带 / 不带对比运行；gate.json fix_list 明写"L2：run inside a real /sdlc acceptance stage"未做。本 Run 根本没走 acceptance-spec 这条支路（dogfood 目录里无 spec.md）。
    - 无闸：specs/<f>/spec.md · specs/<f>/spec-robustness.md
    - 证据：`file:plugins/sdlc/skills/acceptance-spec/SKILL.md` · `file:plugins/sdlc/skills/acceptance-spec/` · `gate_json:plugins/sdlc/skills/acceptance-spec/eval/gate.json#fix_list` · `file:plugins/sdlc/skills/acceptance-spec/scripts/validate_done_when.py#L288-L291` · `file:plugins/sdlc/skills/sdlc/scripts/verify_graph.py#L31`
- **naming adopted → `fits`** — 位置 / 产物：`specs/<f>/spec.md`
    - 贴合理由：收编自 done-when-pipeline v1.1.0，保留上游名；名字后半与独占产物 spec.md 同词干，按 F-03 判 fits。存疑但不判 misfit：名字前半的 "acceptance-" 指向的是与 donewhen-extract 有争的 done_when.yaml，而不是它的独占产物——这层不贴合已由 needed.merge_candidate 承载，F-03 明确要求不要把它再记一遍成 naming 噪声。
    - 证据：`gate_json:plugins/sdlc/skills/acceptance-spec/eval/gate.json#imported_into_sdlc.from`
- disposition `issue`

#### `human_gate.G2` — A-G2（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后判据不冻结，实现者可以在实现途中改 done_when 让自己变绿；.done_when.lock 不存在则 verify_commit.py 与 verify_pr.py 的锁校验全线空转，C6（测试非实现者写、写完锁）与 C7 防作弊清单里的锁那一项一起失效——产出的是一份"绿是因为线被挪了"的验收。
    - 证据：`file:plugins/sdlc/docs/ARCHITECTURE.md#32-三道门只能人签` · `file:plugins/sdlc/skills/sdlc/scripts/lock_done_when.py`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：本 Run 的 G2 由 delegated_agent（g2-judge）代签，不是人签；PSL-006 下代签不渲染为人签，"人签的门跑通了"无证据。锁机制本身（sign --stage g2 / l5、篡改被拒、附提案放行）在 fixture 与本 Run 的 43 文件 l5 锁上都走过，那是 compiled 的证据，不是 verified 的。
    - 重审更正：重审补记（2026-09-06）：代签不是人签这条结论不变，但锁机制本轮多了三条非零退出路径，旧描述已不完整—— sign --gate SCRIPT 把执行契约的 verify_*.py 一起冻进锁（role=gate），check 把 changed_gates 与 changed 分开报（INV-001 / I-30）；sign 拒绝把 g1-interpretations*.md 锁进去（exit 2，I-60）； 代签缺 --authorization 时 exit 1，signer_kind 写进锁文件。这些都是 compiled 的证据，不是 verified 的。
    - 证据：`gate_json:plugins/sdlc/skills/sdlc/eval/gate.json#provenance.scripts_run.lock_done_when.py` · `run_record:plugins/sdlc/dogfood/ring-audit/.done_when.lock` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml`
- **naming authored → `fits`** — 位置 / 产物：`G2（判据冻结门，ARCHITECTURE §1 R2 门闸列）`
    - 贴合理由：位置名（三道门里的第二道，冻判据），F-03 的位置名分支判 fits。
    - 证据：`file:plugins/sdlc/docs/ARCHITECTURE.md#32-三道门只能人签`
- disposition `none`

[^A-issue]: `issue` 的 PSL-ID 追溯 — needed PSL-002, PSL-003 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L83-L88（Node.role=contract → R2）`。
[^A-donewhen-extract]: `donewhen-extract` 的 PSL-ID 追溯 — needed PSL-001, PSL-002 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L89-L94（Node.role=contract → R2）`。
[^A-acceptance-spec]: `acceptance-spec` 的 PSL-ID 追溯 — needed PSL-001, PSL-002 · implemented PSL-015, PSL-010 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L95-L100（Node.role=contract → R2）`。
[^A-G2]: `human_gate.G2` 的 PSL-ID 追溯 — needed PSL-003, PSL-006 · implemented PSL-006, PSL-010 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L101-L107（Node.role=gate，非环角色；按 F-08 归其所检产物 done_when.yaml / .done_when.lock 所在环 R2，与 ARCHITECTURE.md §1 表 R2 门闸列的 G2 一致）`。

## R3 标准

**问题**：判据怎么被机器执行

3 个配件 · 2 处登记为缺少。

| 配件 / 缺少 | kind | 缺口 · 原子 | 独占产物 / 角色 | 闸 · 门 | artifact 闸（checked_by） | Loop | needed | implemented | naming |
|---|---|---|---|---|---|---|---|---|---|
| `test-suite-generator` [^A-test-suite-generator] | `skill` | `Knowledge+Capability` contract-to-test-pyramid | `tests/<f>/**` | 闸 `derive_counts.py`<br>闸 `gen_existence.py`<br>闸 `check_verbatim_names.py`<br>闸 `lock_done_when.py` | `tests/<f>/**` → `check_verbatim_names.py`、`capture_red_baseline.py`、`lock_done_when.py`<br>`tests-manifest.yaml` → `derive_counts.py`、`lock_done_when.py` | `null` | **necessary** | **compiled**<br>未达：`verified` | adopted → **fits** |
| `spec-compile` [^A-spec-compile] | `skill` | `Judgment` decidability-ladder-routing | `compile_manifest.yaml` | 闸 `verify_compile.py` | `compile_manifest.yaml` → `verify_compile.py`<br>`eval_cases/**` → `verify_compile.py` | `null` | **necessary** | **compiled**<br>未达：`verified` | adopted → **fits** |
| `calibrate` [^A-calibrate] | `skill` | `Judgment+Capability` ruler-itself-uncertified | `calibration_report.yaml` | 闸 `verify_calibration.py` | `calibration_report.yaml` → `verify_calibration.py` | `null` | **necessary** | **compiled**<br>未达：`verified` | adopted → **fits** |
| **（缺少）** `red-green-evidence-script` | — | `Control`<br>**lifecycle_blank（生命周期自列的空白）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：没有红-绿证据脚本，「测试先红后绿」全靠实现者自述：一个从来没有红过的测试（断言恒真、或测的是与 AC 无关的东西） 照样被写进 tests-manifest、被 L5 二次锁冻住，并在 acceptance 里当作该 AC 已被机器判定的证据； 真正的漏检要到逃逸缺陷回来时才知道。<br>证据：`file:plugins/sdlc/docs/ARCHITECTURE.md#L290` · `file:plugins/sdlc/docs/lifecycle.md#L40`<br>disposition `issue` | — | — |
| **（缺少）** `uncalibrated-standard-used-as-evidence` | — | `Control`<br>**unenforced_rule（宪法有规则、机器无闸）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：dos.yaml 的 R010 记着「未过 calibrate 的标准不当证据」，enforced_by 却是 not_enforced：没有任何脚本在 下游读标准之前检查 calibration_report.yaml 存在且过线。产出的是一份 calibration_pending 的标准照常被 acceptance 当闸用、结论照常写进 ratchet-log，而 PSL-007 在文档里仍然写着。 （R010 的另一半——meets_done_when 比对脚本——落在 R6，不在本环。）<br>证据：`file:plugins/sdlc/dogfood/ring-audit/dos.yaml#L412-L415` · `file:plugins/sdlc/docs/ARCHITECTURE.md#L292`<br>disposition `issue` | — | — |

### R3 判定详情

#### `test-suite-generator` — A-test-suite-generator（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后引擎把整份冻结契约一次铺成测试：产出一批只覆盖 happy 路径、没有 based_on REQ-ID 标签、 没有 mutation 配置的测试文件，tests-manifest 里每条 AC 都对得上一个测试名却对不上一条失败过的断言； REQ 与测试的一对一缺口要到 pm-reviewer 逐条比对时才暴露，而那时测试已经被 L5 二次锁冻住。
    - 证据：`file:plugins/sdlc/skills/test-suite-generator/SKILL.md` · `file:plugins/sdlc/docs/ARCHITECTURE.md#L37` · `gate_json:plugins/sdlc/skills/test-suite-generator/eval/gate.json#fix_list`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：gate_pass=static_only，且 gate.json 的 provenance 自记 NOT a decorrelated read, NOT an L2 run； 四个脚本（derive_counts / gen_existence / check_verbatim_names / capture_red_baseline） 只有作者本机冒烟，没有带 / 不带 skill 的行为对比。重审补记（2026-09-06）：本轮给 gate.json 补了 mutation_proof 块（10 个 mutant 全被杀），那证明的是 smoke 期望承重，不是 skill 的 带 / 不带效力对比 —— 它是本次交付里唯一更新了 gate.json 的 skill（对照缺口 R5/newly_identified/control/gate-json-stale-after-script-lands）。另：checked_by 里的 gen_existence.py 本轮被摘掉 —— 它没有拒绝路径，是生成器不是闸；替上的 capture_red_baseline.py 才是。
    - 证据：`file:plugins/sdlc/skills/test-suite-generator/SKILL.md` · `gate_json:plugins/sdlc/skills/test-suite-generator/eval/gate.json#gate_pass` · `smoke:plugins/sdlc/skills/test-suite-generator/eval/gate.json#provenance.scripts_run`
- **naming adopted → `fits`** — 位置 / 产物：`tests/<f>/** + tests-manifest.yaml`
    - 命名判定：不重命名；test-suite 与独占产物 tests/<f>/** 同词干（F-03），且收编自 done-when-pipeline v1.1.0，保留上游名。
    - 证据：`gate_json:plugins/sdlc/skills/test-suite-generator/eval/gate.json#imported_into_sdlc` · `file:plugins/sdlc/docs/design-notes.md#L39-L42`
- disposition `none`

#### `spec-compile` — A-spec-compile（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后每条判据都停在同一档：结构性子句（例如「每个 skill 目录必须有 eval/gate.json」）被写成 LLM rubric 的一个维度而不是 fitness function，行为子句只留几个 happy example，产出的 compile_manifest 里 decidability 一栏整列是 judgment。G2 冻结的于是是一把「看起来有判据」的尺子， 没有一条能被脚本跑；判据上移的方向错误要到 acceptance 全绿而隐藏变体一跑就红时才显形。
    - 证据：`file:plugins/sdlc/skills/spec-compile/SKILL.md` · `file:plugins/sdlc/skills/spec-compile/scripts/verify_compile.py`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：gate.json 的 tier2_status 自记 NOT RUN —— no held-out spec set + executor available， 按 effect-gate.md 解到 static_only；行为层的带 / 不带对比未跑。
    - 证据：`file:plugins/sdlc/skills/spec-compile/scripts/verify_compile.py` · `gate_json:plugins/sdlc/skills/spec-compile/eval/gate.json#gate_pass` · `smoke:plugins/sdlc/skills/spec-compile/eval/gate.json#round2.scripts_run.verify_compile.py`
- **naming adopted → `fits`** — 位置 / 产物：`compile_manifest.yaml + eval_cases/**`
    - 命名判定：不重命名；compile 与独占产物 compile_manifest.yaml 同词干（F-03）。收编自 qanat，正文保留 Territory / Run / R001 的上游词，靠术语映射表读成 sdlc 的对象——名字贴合而词表不贴合，词表问题属 R1，不在本环判定。
    - 证据：`gate_json:plugins/sdlc/skills/spec-compile/eval/gate.json#imported_into_sdlc` · `file:plugins/sdlc/docs/design-notes.md#L36-L38`
- disposition `none`

#### `calibrate` — A-calibrate（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后 spec-compile 出的 eval_case 集合与 rubric 直接上线当闸：一套杀不掉任何变异体的测试 （mutation_score 0.4）与一套评分者互不同意的 rubric（Krippendorff α 0.6）会给出全绿的 final-verdict.yaml，acceptance 把它写进 ratchet-log 当达标证据，holdout 从来没被隔离过。 gate.json round1 记下的正是这个洞的一个真实实例——阈值可以被 --min-mutation 0.3 调低到通过。
    - 证据：`file:plugins/sdlc/skills/calibrate/SKILL.md` · `gate_json:plugins/sdlc/skills/calibrate/eval/gate.json#round1.blocking`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：gate.json 的 tier2_status 自记 NOT RUN —— no held-out standard set + executor available； 本次审计也没有跑过任何一次真实校准。
    - 证据：`file:plugins/sdlc/skills/calibrate/scripts/verify_calibration.py` · `gate_json:plugins/sdlc/skills/calibrate/eval/gate.json#gate_pass` · `smoke:plugins/sdlc/skills/calibrate/eval/gate.json#round2.scripts_run.verify_calibration.py`
- **naming adopted → `fits`** — 位置 / 产物：`calibration_report.yaml`
    - 命名判定：不重命名；calibrate 与独占产物 calibration_report.yaml 同词干（F-03）。gate.json 的 naming_collision_check 已确认它与运行时 calibration.resolved 事件不是同一个东西。
    - 证据：`gate_json:plugins/sdlc/skills/calibrate/eval/gate.json#imported_into_sdlc` · `gate_json:plugins/sdlc/skills/calibrate/eval/gate.json#naming_collision_check`
- disposition `none`

[^A-test-suite-generator]: `test-suite-generator` 的 PSL-ID 追溯 — needed PSL-002, PSL-015 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L110-L115（role: standard → R3）`。
[^A-spec-compile]: `spec-compile` 的 PSL-ID 追溯 — needed PSL-002, PSL-010 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L116-L121（role: standard → R3）`。
[^A-calibrate]: `calibrate` 的 PSL-ID 追溯 — needed PSL-007, PSL-002 · implemented PSL-010, PSL-007 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L122-L128（role: standard → R3）`。

## R4 计划

**问题**：怎么拆成无上下文可做的卡

1 个配件 · 1 处登记为缺少。

| 配件 / 缺少 | kind | 缺口 · 原子 | 独占产物 / 角色 | 闸 · 门 | artifact 闸（checked_by） | Loop | needed | implemented | naming |
|---|---|---|---|---|---|---|---|---|---|
| `plan-cards` [^A-plan-cards] | `skill` | `Knowledge+Capability` context-free-card-split | `cards/CARD-*.yaml` | 闸 `lint_cards.py` | `cards/CARD-*.yaml` → `lint_cards.py` | `null` | **necessary** | **compiled**<br>未达：`verified` | authored → **fits** |
| **（缺少）** `card-depends-on-unchecked` | — | `Control`<br>**newly_identified（本次审计新识别）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：卡的 depends_on 是 plan-cards 决定哪些卡可并行的依据（SKILL.md#L38：无依赖的卡可并行），但 lint_cards.py 的五项检查里没有一条读它——全文无 depends_on。产出的卡集可以含互相依赖的一对（CARD-A depends_on CARD-B、 CARD-B depends_on CARD-A）或指向一个已被合并掉、根本不存在的卡号，lint 全绿；实现阶段两张卡要么互等， 要么因为「看起来无依赖」被并行发出去，各自写出半个功能。<br>证据：`file:plugins/sdlc/skills/plan-cards/scripts/lint_cards.py` · `file:plugins/sdlc/skills/plan-cards/assets/card_template.yaml#L23` · `file:plugins/sdlc/skills/plan-cards/SKILL.md#L39`<br>disposition `issue` | — | — |

### R4 判定详情

#### `plan-cards` — A-plan-cards（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后拆卡回到 /sdlc 的散文里：产出的卡没有 allowed_files，两张卡同时把同一份路由表列进可改文件， 写冲突要到第二张卡的 verify_commit.py 白名单检查或 merge 冲突时才炸；某个 REQ 无人认领而没有任何一处报错， 某个 REQ 被两张卡同时认领而两份实现互相覆盖；context_estimate 超过 40k 的卡被照发，实现者中途丢上下文后 自行扩大范围，产出一个跨越两张卡边界的 diff。
    - 证据：`file:plugins/sdlc/skills/plan-cards/SKILL.md` · `file:plugins/sdlc/docs/design-notes.md#L67-L68` · `file:plugins/sdlc/skills/plan-cards/scripts/lint_cards.py`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：gate_pass=static_only；fix_list 的 L2（把一份真实冻结契约拆成卡、交给全新会话的 card-implementer， 看它是否不再要上下文）仍未跑，没有带 / 不带的行为对比。
    - 重审更正：重审补记（2026-09-06）：lint_cards.py 本轮加了第 7 项检查——投影 ↔ 数据源不得跨卡（I-73，#L277-L321， 四条 rejects 路径，带 --repo-root 时还读脚本正文核验 reads_from），smoke 里有 4 条 I-73 期望 加 2 条 I-15/I-49 闭包期望。而 eval/gate.json 一个字节没动，仍写「bad card set rejected on 6 independent breaches」、仍标 2026-09-05，SKILL.md 已升到 v0.2.0——证据档比代码旧， 见缺口 R5/newly_identified/control/gate-json-stale-after-script-lands。
    - 证据：`file:plugins/sdlc/skills/plan-cards/scripts/lint_cards.py` · `gate_json:plugins/sdlc/skills/plan-cards/eval/gate.json#gate_pass` · `smoke:plugins/sdlc/skills/plan-cards/eval/gate.json#provenance.scripts_run.lint_cards.py`
- **naming authored → `fits`** — 位置 / 产物：`cards/CARD-*.yaml`
    - 命名判定：不重命名；新写的 skill 按产物命名，cards 与 cards/CARD-*.yaml 同词干（F-03 / PSL-014）。
    - 证据：`file:plugins/sdlc/docs/design-notes.md#L67-L69` · `gate_json:plugins/sdlc/skills/plan-cards/eval/gate.json#provenance.why_it_exists`
- disposition `none`

[^A-plan-cards]: `plan-cards` 的 PSL-ID 追溯 — needed PSL-002, PSL-003 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L131-L136（role: planner → R4）`。

## R5 实现

**问题**：按卡做、按卡提交

5 个配件 · 4 处登记为缺少。

| 配件 / 缺少 | kind | 缺口 · 原子 | 独占产物 / 角色 | 闸 · 门 | artifact 闸（checked_by） | Loop | needed | implemented | naming |
|---|---|---|---|---|---|---|---|---|---|
| `implement` [^A-implement] | `skill` | `Control+Judgment` implementer-sees-evaluator | `card.allowed_files` | 闸 `verify_commit.py` | `card.allowed_files` → `verify_commit.py` | `loops.yaml#card_retry` | **merge_candidate**<br>与 `agent.comment-fixer` 并列 | **compiled**<br>未达：`verified` | authored → **fits** |
| `agent.card-implementer` [^A-agent.card-implementer] | `agent` | `Capability` fresh-context-card-execution<br>`Control+Judgment` implementer-sees-evaluator | `card.allowed_files` | 闸 `verify_commit.py`<br>闸 `lock_done_when.py` | `card.allowed_files` → `verify_commit.py` | `loops.yaml#card_retry` | **necessary** | **compiled**<br>未达：`verified` | authored → **fits** |
| `agent.comment-fixer` [^A-agent.comment-fixer] | `agent` | `Control+Judgment` implementer-sees-evaluator | `card.allowed_files` | 闸 `verify_commit.py` | `card.allowed_files` → `verify_commit.py` | `loops.yaml#review_loop` | **merge_candidate**<br>与 `implement` 并列 | **compiled**<br>未达：`verified` | authored → **fits** |
| `commit` [^A-commit] | `skill` | `Control` atomic-auditable-commit | `git:commit` | 闸 `verify_commit.py` | `git:commit` → `verify_commit.py`、`commit.sh` | `null` | **necessary** | **compiled**<br>未达：`verified` | authored → **fits** |
| `ratchet` [^A-ratchet] | `skill` | `Capability` run-until-criteria-met | `experiment_dir/**` | **无闸无门** | `experiment_dir/**` → **（无闸 → 封顶 declared）** | `loops.yaml#ratchet` | **necessary** | **declared**<br>未达：`compiled` / `verified` | adopted → **fits** |
| **（缺少）** `experiment-dir-unchecked` | — | `Control`<br>**newly_identified（本次审计新识别）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：ratchet 的独占产物 experiment_dir/**（graph.yaml#L160）没有任何闸与门：results.tsv / learnings.md / dead-ends.md 的形状、预算消耗、generator 与 verifier 是否真的不同，全都无人检。产出的是一个自称 「所有 P0 criteria 通过」的实验目录，而「通过」是由跑实验的那一方写下的；PSL-015（每个环节的产物要么被 脚本检、要么被门挡）在这一条上直接落空，ratchet 的 implemented 因此被 F-06 压在 declared。<br>证据：`file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L155-L162` · `gate_json:plugins/sdlc/skills/ratchet/eval/gate.json#provenance.scripts_run`<br>disposition `issue` | — | — |
| **（缺少）** `one-producer-per-artifact-unlinted` | — | `Control`<br>**unenforced_rule（宪法有规则、机器无闸）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：dos.yaml 的 R001「一个产物只有一个生产者」enforced_by 是 user_workflow：verify_graph.py 的 lint 1 只检 写范围有界，不检某个产物是否只出现在一个 Node 的 writes 里。于是 card.allowed_files 在 graph.yaml 里 同时挂在 implement（#L144）、agent.card-implementer（#L152）、agent.comment-fixer（#L230）三个节点下， 图 lint 全绿。产出的后果是回滚与归因失去唯一落点：一次实现阶段的改动到底属于哪个执行者，只能靠 commit footer 猜；而条件替代（合法）与真的在争（不合法）这两种情况在数据上长得一模一样。<br>证据：`file:plugins/sdlc/dogfood/ring-audit/dos.yaml#L376-L379` · `file:plugins/sdlc/dogfood/ring-audit/dos.yaml#L677` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L144`<br>disposition `issue` | — | — |
| **（缺少）** `agent-parts-without-gate-json` | — | `Control`<br>**newly_identified（本次审计新识别）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：本环两个 kind=agent 的 Part（agent.card-implementer、agent.comment-fixer）在 plugins/sdlc/agents/ 下只有 一份 .md，没有 eval/gate.json——十三个 skill 每个都有的那份证据档，五个 agent 一个都没有。 产出的后果是这两个 Part 的效力档位没有任何记录可查：说它 static_only 还是 verified 都无从对账， R017（效力声明不得超过证据档）对 agent 这一类节点在数据上不成立。<br>证据：`file:plugins/sdlc/agents/card-implementer.md` · `file:plugins/sdlc/agents/comment-fixer.md` · `file:plugins/sdlc/dogfood/ring-audit/dos.yaml#L440-L443`<br>disposition `issue` | — | — |
| **（缺少）** `gate-json-stale-after-script-lands` | — | `Control`<br>**newly_identified（本次审计新识别）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：没有任何机械物要求「skill 的脚本变了，它的 eval/gate.json 必须一起变」。本轮 commit 长出一整个 新的承重脚本 commit.sh（它决定 git:commit 落不落地），verify_commit.py 加了六类新拒绝路径， 而 commit/eval/gate.json 一个字节没动——它仍标 2026-09-05、仍写「101 passed」、 scripts_run 里没有 commit.sh 这一行；plan-cards 同样：lint_cards.py 加了第 7 项检查、SKILL.md 升到 v0.2.0，gate.json 仍写「6 independent breaches」。产出的后果是效力档位失去对账基础： R017「效力声明不得超过证据档」在证据档比代码旧的时候形同虚设，而审计者只能靠逐行读 diff 才发现档案在说另一个版本的话。test-suite-generator 是同一次交付里唯一更新了 gate.json 的 （加了第四个脚本与 mutation_proof），三选一的命中率说明这靠的是记性不是机械物。<br>证据：`file:plugins/sdlc/skills/commit/scripts/commit.sh` · `gate_json:plugins/sdlc/skills/commit/eval/gate.json#provenance` · `gate_json:plugins/sdlc/skills/plan-cards/eval/gate.json#provenance.scripts_run` · `file:plugins/sdlc/skills/plan-cards/scripts/lint_cards.py#L277-L321` · `gate_json:plugins/sdlc/skills/test-suite-generator/eval/gate.json#provenance`<br>disposition `issue` | — | — |

### R5 判定详情

#### `implement` — A-implement（state: evidenced）

- **needed `merge_candidate`** — 撤掉后：撤掉后没有一处规定实现者只看卡：引擎在同一上下文里先读 ratchet-log 的评审发现再改代码，产出的 diff 精确命中评审者列出的那几行、隐藏变体覆盖的分支留成占位，acceptance 全绿而隐藏集一跑就红；同时改动不再 被 allowed_files 约束，卡外文件被顺手改掉而不是停在 WHITELIST_OVERFLOW，一张卡的 diff 里混进另一张卡的实现。
    - 并列生产的判定：card.allowed_files 在 graph.yaml 里有三个 writer：implement（#L144）、agent.card-implementer（#L152）、 agent.comment-fixer（#L230）。前两者满足 F-05 同阶段条件替代三条件（同在 stage.implement 的 handled_by #L29； #L320 有带 when 守卫的 conditional 边选执行者；同 schema 产物），记 alternatives_of 豁免；agent.comment-fixer 三条件只差得更远——它不在 stage.implement 的 handled_by 里，与 implement 之间也没有 conditional 边（#L349 是 handoff）——按规则 1 双方都记 merge_candidate，本审计不当场裁掉一个。
    - 证据：`file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L144` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L230` · `file:plugins/sdlc/skills/implement/SKILL.md` · `file:plugins/sdlc/dogfood/ring-audit/dos.yaml#L677`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：gate_pass=static_only；implement 自身无 scripts/（gate.json fix_list 写 no own script by design —— 闸是 verify_commit.py 与 sdlc_state.py），compiled 靠被闸挡而不是靠自带脚本；fix_list 的 L2（真跑一张卡看它 是否在白名单溢出时停机而不是扩范围）未跑。
    - 证据：`file:plugins/sdlc/skills/implement/SKILL.md` · `gate_json:plugins/sdlc/skills/implement/eval/gate.json#fix_list` · `smoke:plugins/sdlc/skills/commit/eval/gate.json#provenance.scripts_run.verify_commit.py`
- **naming authored → `fits`** — 位置 / 产物：`stage.implement（位置名，graph.yaml#L29）/ card.allowed_files`
    - 命名判定：不重命名；新写的 skill 按位置命名，implement 与 stage.implement 同词干（F-03 / PSL-014）。
    - 证据：`file:plugins/sdlc/docs/design-notes.md#L67-L68` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L29`
- disposition `issue`

#### `agent.card-implementer` — A-agent.card-implementer（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后 executor == agent 这条 conditional 分支没有承载者：卡只能在编排者自己的上下文里做，产出的 diff 带着编排者读过的评审发现、其他卡的实现与隐藏集线索。R005（实现者不读评估者输出）在 graph.yaml 的 must_not_read 里仍然写着、在实际执行里已经破了，而没有任何产物能显示这一点——隔离从此只是文档。
    - 证据：`file:plugins/sdlc/agents/card-implementer.md` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L330` · `file:plugins/sdlc/skills/sdlc/assets/loops.yaml#L32`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：plugins/sdlc/agents/ 下五个 agent 都没有 eval/gate.json，这个 Part 没有任何证据档；compiled 完全来自 它自己的判据「每个 commit 过 verify_commit.py exit 0 才 git commit」这道被闸挡的约束，没有行为层运行记录。
    - 证据：`file:plugins/sdlc/agents/card-implementer.md` · `gate_json:plugins/sdlc/skills/commit/eval/gate.json#provenance.scripts_run.verify_commit.py` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L147-L154`
- **naming authored → `fits`** — 位置 / 产物：`card.allowed_files / stage.implement 的执行器位置（graph.yaml#L330）`
    - 命名判定：不重命名；card-implementer 与它的输入（卡）和位置（stage.implement 的 agent 执行器）同词干（F-03）。
    - 证据：`file:plugins/sdlc/docs/design-notes.md#L68` · `file:plugins/sdlc/agents/card-implementer.md`
- **闸的补记**：重审补记（2026-09-06）：agents/card-implementer.md 本轮加了两条动手前的前置 —— 先跑 lock_done_when.py verify（工作区模式，exit 0 才算数，I-61）、一张卡一个 git worktree（I-64 / I-53）， 以及"绝不 amend 不是自己刚提的那条"。lock_done_when.py 是**流程前置**，检的是 .done_when.lock 与锁内文件，不是 card.allowed_files 这件独占产物上的闸，所以 artifacts[].checked_by 不变， implemented 也仍是 compiled。仍然成立：五个 agent 依旧一个 eval/gate.json 都没有， 缺口 R5/newly_identified/control/agent-parts-without-gate-json 未被填。
- disposition `none`

#### `agent.comment-fixer` — A-agent.comment-fixer（state: evidenced）

- **needed `merge_candidate`** — 撤掉后：撤掉后 review 环里「一条 ACCEPT 线程一个隔离修复者」没有承载者：修复在 review-loop 自己的上下文里做， 同一个上下文既持有 triage 的全部线程与评审者判据、又写代码，产出的 commit 一次扫掉多条线程且没有复现测试； 主张本来就不成立的那一类（UNEXPECTEDLY_PASSING）被静默改掉而不是停下回报，PR 上看到的是「都修了」， 实际是把评审者的措辞而不是缺陷改掉了。
    - 并列生产的判定：与 implement 并列生产 card.allowed_files 且不满足 F-05 同阶段条件替代三条件（不在 stage.implement 的 handled_by graph.yaml#L29 里；#L349 从 review-triager 过来的是 handoff 边而不是带 when 守卫的 conditional 边）， 按规则 1 两个生产者都记 merge_candidate。这与 dos.yaml#L677 记的 R001 现状问题是同一件事的两个位置。
    - 证据：`file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L230` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L144` · `file:plugins/sdlc/agents/comment-fixer.md`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：无 eval/gate.json、无行为层运行记录；且 graph.yaml#L225-L231 的节点缺 loop 键而 loops.yaml#L75 已把它 当 review_loop 的 generator，两份数据对同一个 Part 的环归属不一致（源码问题，不在本审计里调和）。
    - 证据：`file:plugins/sdlc/agents/comment-fixer.md` · `gate_json:plugins/sdlc/skills/commit/eval/gate.json#provenance.scripts_run.verify_commit.py` · `file:plugins/sdlc/skills/sdlc/assets/loops.yaml#L75`
- **naming authored → `fits`** — 位置 / 产物：`loops.yaml#review_loop 的 generator（位置名，loops.yaml#L75）`
    - 命名判定：不重命名。fit 按位置名判：comment-fixer 与它在 review_loop 里的位置（修一条 PR 评论线程）同义 → fits。 注意它改编自 qanat 的 issue-fixer 而没有保留上游名（design-notes.md#L56），provenance 因此按 authored 的那条路记；provenance 不参与 fit 判定（F-03），只决定 misfit 的去向理由，此处无 misfit。
    - 证据：`file:plugins/sdlc/docs/design-notes.md#L56` · `file:plugins/sdlc/skills/sdlc/assets/loops.yaml#L71-L84`
- **Loop `loops.yaml#review_loop`**：graph.yaml#L225-L231 的节点没有 loop 键，但 loops.yaml#L75 把它写成 review_loop 的 generator； 本 Part 按 loops.yaml 记环归属，graph.yaml 的缺键作为一条源码问题记在 implemented.evidence 里。
- disposition `issue`

#### `commit` — A-commit（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后落地前的那组机械闸不存在（按类枚举：白名单溢出 / 锁篡改与提案覆盖 / secret 与调试代码 / --range 形状 / 插件三处版本同步 —— 重审更正：装配时写死的"三道"已经不够数了）， 引擎按默认习惯 git add -A && git commit -m "update"：产出一条混了两个 关注点、把 .env 与一枚 AKIA 开头的 key 一起暂存、消息不带 Card footer 的提交。卡的白名单溢出与 .done_when.lock 命中都不会被拒——契约被改掉而同一 diff 里没有 change-proposal——之后 replay_card_commits.sh 无从按卡回放，PSL-003（审计者不改被审对象）这类性质失去机械证明。
    - 证据：`file:plugins/sdlc/skills/commit/SKILL.md` · `file:plugins/sdlc/skills/commit/scripts/verify_commit.py` · `file:plugins/sdlc/docs/ARCHITECTURE.md#L39`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：gate_pass=static_only；fix_list 自记两条未跑——L2（拿一份真实的多关注点 diff 看引擎是否真的拆成两条提交） 与「红-绿证据是手工的，没有脚本」；脚本冒烟在临时仓库里跑过，不等于 skill 的带 / 不带行为对比。
    - 证据：`file:plugins/sdlc/skills/commit/scripts/verify_commit.py` · `gate_json:plugins/sdlc/skills/commit/eval/gate.json#gate_pass` · `smoke:plugins/sdlc/skills/commit/eval/gate.json#smoke —— 该字段逐字写着 "101 passed, 0 failed, 2026-09-05"，那是它自己的登记值，**不是**当前计数：smoke.sh 在 b77feb0 上实跑 391 passed / 0 failed。gate.json 未随 commit.sh 与 verify_commit.py 的六类新拒绝路径更新，见缺口 R5/newly_identified/control/gate-json-stale-after-script-lands`
- **naming authored → `fits`** — 位置 / 产物：`git:commit`
    - 命名判定：不重命名；commit 与独占产物 git:commit 同词干（F-03）。它改编自 pdforge 的 git-workflow 约定 （design-notes.md#L52，「直接改编」而非「直接收编」），正文重写成判据 + 预门形态、gate.json 没有 imported_into_sdlc 块，故 provenance 记 authored。
    - 证据：`file:plugins/sdlc/docs/design-notes.md#L52-L53` · `gate_json:plugins/sdlc/skills/commit/eval/gate.json#provenance`
- disposition `none`

#### `ratchet` — A-ratchet（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后「跑到达标为止」的那一类卡只能靠引擎在同一会话里自评自改：没有独立评估者、没有杀死重启，产出的是 一串各自声称有改进的 diff 与一份由生成者本人写的通过结论。results.tsv / learnings.md / dead-ends.md 不存在， 同一条死路被反复走；plateau 与 oscillation 因为无人计数而永不触发升级，单卡预算 3 在实际上变成无上限。
    - 证据：`file:plugins/sdlc/skills/ratchet/SKILL.md` · `file:plugins/sdlc/skills/sdlc/assets/loops.yaml#L37-L52` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L331`
- **implemented `declared`** — declared（只有 SKILL.md / 提示）
    - 未达 `compiled`：no_gate —— 无 scripts/，且独占产物 experiment_dir/** 的 checked_by 为空；按 F-06 生产者不得高于 declared， 审计者不得以「读了 SKILL.md 觉得能跑」抬到 compiled。它的 commit 走 /commit 的闸，但那道闸检的是 git:commit，不是 experiment_dir/**。
    - 未达 `verified`：gate_pass=static_only 且 gate.json 的 provenance.scripts_run 为空对象，没有任何脚本或行为层记录。
    - 证据：`file:plugins/sdlc/skills/ratchet/SKILL.md` · `file:plugins/sdlc/skills/ratchet` · `gate_json:plugins/sdlc/skills/ratchet/eval/gate.json#gate_pass`
- **naming adopted → `fits`** — 位置 / 产物：`loops.yaml#ratchet（位置名）/ experiment_dir/**`
    - 命名判定：不重命名；ratchet 与它拥有的环 loops.yaml#ratchet 同词干（F-03），且收编自 ratchet v1.1.0，保留上游名。
    - 证据：`gate_json:plugins/sdlc/skills/ratchet/eval/gate.json#imported_into_sdlc` · `file:plugins/sdlc/skills/sdlc/assets/loops.yaml#L37`
- disposition `issue`

[^A-implement]: `implement` 的 PSL-ID 追溯 — needed PSL-001, PSL-002 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L139-L146（role: implementer → R5）`。
[^A-agent.card-implementer]: `agent.card-implementer` 的 PSL-ID 追溯 — needed PSL-002, PSL-003 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L147-L154（role: implementer → R5）`。
[^A-agent.comment-fixer]: `agent.comment-fixer` 的 PSL-ID 追溯 — needed PSL-001, PSL-002 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L225-L231（role: implementer → R5）· role_conflict： plugins/sdlc/docs/ARCHITECTURE.md#L41 的 R7 交付行把 review-loop 归 R7，而本 Part 是 loops.yaml#L71-L84 review_loop 的 generator、graph.yaml#L359 上 stage.review 的下游；§1 表不点名 agent， comment-fixer 只经 review-loop 间接归 R7。两源并列，本审计不调和（F-08 / F-24）。`。
[^A-commit]: `commit` 的 PSL-ID 追溯 — needed PSL-002, PSL-004 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L163-L168（role: implementer → R5）`。
[^A-ratchet]: `ratchet` 的 PSL-ID 追溯 — needed PSL-002, PSL-012 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L155-L162（role: implementer → R5）`。

## R6 验收

**问题**：三档验收，谁一票否决

11 个配件 · 10 处登记为缺少。

| 配件 / 缺少 | kind | 缺口 · 原子 | 独占产物 / 角色 | 闸 · 门 | artifact 闸（checked_by） | Loop | needed | implemented | naming |
|---|---|---|---|---|---|---|---|---|---|
| `acceptance-fleet` [^A-acceptance-fleet] | `skill` | `Control+Judgment` six-evaluator-dispatch-and-ratchet | `ratchet-log/iteration-NNN/final-state.json`<br>role `orchestrator` | 门 `G3` | `ratchet-log/iteration-NNN/**` → `next_iteration.py`<br>`ratchet-log/iteration-NNN/final-state.json` → **（无闸 → 封顶 declared）** | `loops.yaml#acceptance_ratchet` | **necessary** | **declared**<br>未达：`compiled` / `verified` | adopted → **fits** |
| `code-reviewer` [^A-code-reviewer] | `skill` | `Judgment` diff-bug-findings-with-reproduction | `ratchet-log/iteration-NNN/code-review-*.yaml` | **无闸无门** | `ratchet-log/iteration-NNN/code-review-*.yaml` → **（无闸 → 封顶 declared）** | `null` | **necessary** | **declared**<br>未达：`compiled` / `verified` | adopted → **fits** |
| `qa-reviewer` [^A-qa-reviewer] | `skill` | `Capability+Judgment` test-execution-and-failure-classification | `ratchet-log/iteration-NNN/qa-review.yaml` | **无闸无门** | `ratchet-log/iteration-NNN/qa-review.yaml` → `qa_facts.py` | `null` | **necessary** | **compiled**<br>未达：`verified` | adopted → **fits** |
| `pm-reviewer` [^A-pm-reviewer] | `skill` | `Judgment` per-requirement-compliance-verdict | `ratchet-log/iteration-NNN/pm-review.yaml` | **无闸无门** | `ratchet-log/iteration-NNN/pm-review.yaml` → **（无闸 → 封顶 declared）** | `null` | **necessary** | **declared**<br>未达：`compiled` / `verified` | adopted → **fits** |
| `spec-drift-detector` [^A-spec-drift-detector] | `skill` | `Knowledge+Judgment` spec-code-divergence-archaeology | `ratchet-log/iteration-NNN/drift.yaml` | **无闸无门** | `ratchet-log/iteration-NNN/drift.yaml` → **（无闸 → 封顶 declared）** | `null` | **necessary** | **declared**<br>未达：`compiled` / `verified` | adopted → **fits** |
| `spec-gaming-detector` [^A-spec-gaming-detector] | `skill` | `Judgment` contract-gaming-detection | `ratchet-log/iteration-NNN/gaming.yaml` | 闸 `compute_score.py` | `ratchet-log/iteration-NNN/gaming.yaml` → **（无闸 → 封顶 declared）** | `null` | **necessary** | **declared**<br>未达：`compiled` / `verified` | adopted → **fits** |
| `meta-judge` [^A-meta-judge] | `skill` | `Judgment` finding-synthesis-without-re-review | `ratchet-log/iteration-NNN/final-verdict.yaml` | 闸 `compute_confidence.py` | `ratchet-log/iteration-NNN/final-verdict.yaml` → **（无闸 → 封顶 declared）** | `loops.yaml#acceptance_ratchet` | **necessary** | **declared**<br>未达：`compiled` / `verified` | adopted → **fits** |
| `pr-review` [^A-pr-review] | `skill` | `Judgment` single-pr-finding-tiering | `.sdlc/review/*.yaml` | 闸 `post_review.py` | `.sdlc/review/*.yaml` → `post_review.py`<br>`github:review` → `post_review.py` | `null` | **necessary** | **compiled**<br>未达：`verified`<br>`calibrated: false` | authored → **fits** |
| `human_gate.G3` [^A-G3] | `human_gate` | `Judgment` exception-review-before-merge | `g3-record.md`<br>role `gate` | 门 `G3` | `g3-record.md` → **（无闸 → 封顶 declared）** | `loops.yaml#lifecycle` | **necessary** | **declared**<br>未达：`compiled` / `verified` | authored → **fits** |
| `agent.review-triager` [^A-review-triager] | `agent` | `Judgment` review-comment-as-claim-verification | `triage.yaml` | **无闸无门** | `triage.yaml` → **（无闸 → 封顶 declared）** | `loops.yaml#review_loop` | **necessary** | **declared**<br>未达：`compiled` / `verified` | authored → **fits** |
| `agent.fix-verifier` [^A-fix-verifier] | `agent` | `Control+Judgment` isolated-fix-verification | `verify.yaml` | **无闸无门** | `verify.yaml` → **（无闸 → 封顶 declared）** | `loops.yaml#review_loop` | **necessary** | **declared**<br>未达：`compiled` / `verified` | adopted → **fits** |
| **（缺少）** `meets-done-when-compare-script` | — | `Capability+Control`<br>**lifecycle_blank（生命周期自列的空白）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：没有脚本按契约阈值算 meets_done_when：这一栏只能由评估 agent 用自然语言宣布"达标了"。错误产物是一份 final-state.json 里写着 DONE、而没有任何一处把 done_when.yaml 的 thresholds 与实测数字并排比过——ARCHITECTURE §6.7 那句「meets_done_when 由脚本比对，不由评估 agent 宣布」在 R6 没有执行处。<br>证据：`file:plugins/sdlc/docs/ARCHITECTURE.md#L292` · `file:plugins/sdlc/docs/lifecycle.md#L42` · `file:plugins/sdlc/docs/design-notes.md#L31`<br>disposition `issue` | — | — |
| **（缺少）** `evaluator-may-declare-meets-done-when` | — | `Control`<br>**unenforced_rule（宪法有规则、机器无闸）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：dos.yaml R001..R017 里的 R010（enforced_by: not_enforced）说 meets_done_when 只能由脚本算、绝不由评估 Node 宣布。实际上 acceptance.meets_done_when 就在 sdlc_state.py 的 SETTABLE 白名单里（#L67），任何 agent 一句 `sdlc_state.py set acceptance.meets_done_when=true` 就写进了 state.json，没有任何校验、也不记谁写的类型。这与上一条是两个洞：上一条是"没有脚本去算"，这一条是"就算有脚本，也没有东西阻止别人直接写"。<br>证据：`file:plugins/sdlc/dogfood/ring-audit/dos.yaml#R010` · `file:plugins/sdlc/skills/sdlc/scripts/sdlc_state.py#L76` · `file:plugins/sdlc/skills/sdlc/scripts/sdlc_state.py#L435-L444`<br>disposition `issue` | — | — |
| **（缺少）** `gate-signer-must-be-human` | — | `Control`<br>**unenforced_rule（宪法有规则、机器无闸）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：dos.yaml R008（enforced_by: user_workflow）说门的判决必须有人签，skill / agent 类 Node 一个都不许记。sdlc_state.py 的 cmd_gate 只做了半条：signer_kind = delegated_agent 时必须带 --authorization（#L394-L395），但它照收 delegated_agent 这个值——也就是说带一句授权说明，agent 就能把 G3 签成 pass。错误产物：一条 verdict = pass 的 G3 记录，signer_kind 是 delegated_agent，而"授权"只是一个自由文本串，没有任何一处核对它是否真的来自人。<br>证据：`file:plugins/sdlc/dogfood/ring-audit/dos.yaml#R008` · `file:plugins/sdlc/skills/sdlc/scripts/sdlc_state.py#L502-L503` · `file:plugins/sdlc/skills/sdlc/scripts/sdlc_state.py#L520-L524`<br>disposition `issue` | — | — |
| **（缺少）** `static-only-never-called-verified` | — | `Knowledge`<br>**unenforced_rule（宪法有规则、机器无闸）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：dos.yaml R017（enforced_by: user_workflow）说配件的有效性主张不得超过它的证据档位，static_only 的 skill 绝不许被说成 verified。R6 的八个 skill 全部 gate_pass = static_only，没有任何机械物阻止文档或播报把它们说成"已验证"。错误产物：一份把 R6 说成"已实现 ✓"的报告——布尔取代三态，读者以为验收线跑过而其实一次都没跑。这条规律是横切的，但它咬得最狠的位置就是 R6：验收线自己没被验收。<br>证据：`file:plugins/sdlc/dogfood/ring-audit/dos.yaml#R017` · `gate_json:plugins/sdlc/skills/acceptance-fleet/eval/gate.json#gate_pass=static_only` · `gate_json:plugins/sdlc/skills/meta-judge/eval/gate.json#gate_pass=static_only`<br>disposition `issue` | — | — |
| **（缺少）** `one-artifact-one-producer-in-ratchet-log` | — | `Control`<br>**unenforced_rule（宪法有规则、机器无闸）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：dos.yaml R001（enforced_by: user_workflow）要求一个产物只有一个写者。R6 里 acceptance-fleet 声明 writes: ratchet-log/iteration-NNN/**（graph.yaml#L176），而五个评审者与 meta-judge 各自声明写这个目录里的具体文件（#L179-L190）——写域相互包含。verify_graph.py 的 lint ① 只检 writes 非空且不是裸 ** / * / / / .（#L131-L139），不检写域是否相交，所以这一处包含关系不会被任何脚本抓到。错误产物：两个 Node 同时改同一份 iteration 目录里的同一个文件时，provenance 与回滚归属含糊，而账本上看不出是谁写的。<br>证据：`file:plugins/sdlc/dogfood/ring-audit/dos.yaml#R001` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L176` · `file:plugins/sdlc/skills/sdlc/scripts/verify_graph.py#L131-L139`<br>disposition `issue` | — | — |
| **（缺少）** `ratchet-log-shape-unchecked` | — | `Control`<br>**newly_identified（本次审计新识别）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：R6 的产物没有任何形状校验，连存在性都不检。advance pr 只要求 acceptance.evaluation_result 是个非空串（sdlc_state.py#L366-L368）——同一个文件里 advance cards 对 lock.path 是 `get_path(...) and os.path.isfile(...)`（#L262），advance pr 这一支少了后半截。错误产物：`set acceptance.evaluation_result=ratchet-log/iteration-999/final-state.json` 指向一个不存在的路径，流水线照常推进到 pr、review、merge；ratchet-log-format.md 那份目录契约（fleet-outputs/ 七个文件 + meta-judge-output.yaml + final-state.json）没有一行被机器读过。<br>证据：`file:plugins/sdlc/skills/sdlc/scripts/sdlc_state.py#L366-L368` · `file:plugins/sdlc/skills/sdlc/scripts/sdlc_state.py#L357` · `file:plugins/sdlc/skills/acceptance-fleet/references/ratchet-log-format.md#L41`<br>disposition `issue` | — | — |
| **（缺少）** `g3-pass-has-no-input-precondition` | — | `Control`<br>**newly_identified（本次审计新识别）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：三道门里只有 G3 的 pass 没有输入前置。cmd_gate 里 G2 pass 要求 lock.path 是个存在的文件、G1 pass 要求 world.derived_dir 是个存在的目录（sdlc_state.py#L486-L494），G3 那一支什么都不检；advance g3 也只要 review.done（#L276-L277）。错误产物：一条 gates.g3.verdict = pass 的记录，而 acceptance.evaluation_result 为空、失败报告不存在、human AC 清单从未生成——门盖了章，章下面没有纸。G1 的注释把这件事说得很清楚：「G1 adjudicates derivation products, not vibes」，G3 现在恰恰是 vibes。<br>证据：`file:plugins/sdlc/skills/sdlc/scripts/sdlc_state.py#L486-L494` · `file:plugins/sdlc/skills/sdlc/scripts/sdlc_state.py#L370-L371` · `file:plugins/sdlc/docs/ARCHITECTURE.md#L40`<br>disposition `issue` | — | — |
| **（缺少）** `drift-consumer-flag-not-updated` | — | `Control`<br>**newly_identified（本次审计新识别）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：本轮为修 I-71（drift 读到了 qa 的 findings 与 GO/NO-GO，被 meta-judge 记为隔离破口）建的墙只砌了 编排者这一侧。acceptance-fleet 侧：skill-dispatch-matrix.md#L147 传 --qa-measurements，#L151 加粗写 "**Never `--qa-report`**"；SKILL.md#L63 把它写成铁律 2 的唯一例外。消费者侧： spec-drift-detector/SKILL.md#L63 的参数表仍然只定义 `--qa-report=<path>`（说明文字仍是 "A `/qa-reviewer` output"），#L50 的铁律 8 仍指导拿它做非功能漂移的度量依据， references/divergence-types.md#L225 同样。--qa-measurements 在被调用方一处都没定义。 于是两种错误产物二选一：照 drift 自己的 SKILL.md 调用 → 又把整份 qa 报告递过去，I-71 原样复发； 照编排者的矩阵调用 → drift 收到一个自己文档里不存在的参数，度量证据来源未定义。 墙只有一面，另一面写着"请走这里"。<br>证据：`file:plugins/sdlc/skills/spec-drift-detector/SKILL.md#L63` · `file:plugins/sdlc/skills/spec-drift-detector/SKILL.md#L50` · `file:plugins/sdlc/skills/acceptance-fleet/references/skill-dispatch-matrix.md#L147-L151` · `file:plugins/sdlc/skills/spec-drift-detector/references/divergence-types.md#L225`<br>disposition `issue` | — | — |
| **（缺少）** `ratchet-log-filenames-diverge-from-graph` | — | `Knowledge+Control`<br>**newly_identified（本次审计新识别）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：graph.yaml#L179-L189 为五个评审者与 meta-judge 声明的 writes 路径，没有一条是系统真正产出的文件： graph 说 iteration-NNN/{code-review-*,qa-review,pm-review,drift,gaming,final-verdict}.yaml， 磁盘上（三轮真实 run，plugins/sdlc/dogfood/ring-audit/ratchet-log/）与 ratchet-log-format.md / skill-dispatch-matrix.md 里都是 iteration-NNN/fleet-outputs/{code-reviewer-*,qa-reviewer, pm-reviewer,spec-drift-detector,spec-gaming-detector}.yaml 加 iteration-NNN/meta-judge-output.yaml。 六条里五条是新识别的（meta-judge 那条已是 P-R6-05）。 以前这条分歧是惰性的——没有任何脚本读 ratchet-log，写错也没人碰。本轮它变成承重的： next_iteration.py#L101/#L214-L216 把 fleet-outputs/{spec-gaming-detector,qa-reviewer,pm-reviewer}.yaml 硬编码进代码，qa_facts.py 的整条数据流也建立在这套拼法上。于是第一批读 ratchet-log 的脚本， 依赖的是图从未声明过的路径。错误产物：graph.yaml 的 writes lint（verify_graph.py）核对的是一套 永远不会出现的文件名，而真正落地的那套没有任何一处声明——audit.yaml 的 artifacts registry 也照抄了 图的拼法，于是"某产物有没有闸"这个判定所指的对象，本身指不到磁盘上的东西。<br>证据：`file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L179-L189` · `file:plugins/sdlc/skills/acceptance-fleet/scripts/next_iteration.py#L101` · `file:plugins/sdlc/skills/acceptance-fleet/scripts/next_iteration.py#L214-L216` · `file:plugins/sdlc/skills/acceptance-fleet/references/ratchet-log-format.md#L28-L40` · `run_record:ab67052 · find plugins/sdlc/dogfood/ring-audit/ratchet-log -type f —— 三轮 iteration 里 qa-review.yaml / pm-review.yaml / drift.yaml / gaming.yaml / final-verdict.yaml 一个都不存在`<br>disposition `issue` | — | — |
| **（缺少）** `gate-json-not-synced-with-smoke-coverage` | — | `Control`<br>**newly_identified（本次审计新识别）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：acceptance-fleet 本轮新增两个脚本，smoke.sh#L1156-L1173 给了 12 条期望（其中 5 条断言非零退出）， 在 ab67052 上实跑 389 passed / 0 failed 全绿。而 skills/acceptance-fleet/eval/gate.json 一个字节没动： gate_pass 仍 static_only、evaluated_layers 仍只有 [structural]、provenance.scripts_run 仍是 {}， provenance 里那句"smoke.sh on bundled scripts"是脚本还不存在时写的，现在字面为真而所指为空。 没有任何机械物让证据档位记录跟上真实覆盖：gate.json 是这个插件用来防止"把 static_only 说成 verified"（R017）的唯一账本，而这个账本本身没有人对账。错误产物：一份低报自己证据档位的 gate.json， 与一份可能高报的报告，两个方向的错都无法被发现——因为没有第三方去比"smoke 实际跑了什么" 与"gate.json 声称跑了什么"。<br>证据：`gate_json:plugins/sdlc/skills/acceptance-fleet/eval/gate.json#provenance.scripts_run（空对象）` · `file:plugins/sdlc/eval/smoke.sh#L1156-L1173` · `run_record:ab67052 · bash plugins/sdlc/eval/smoke.sh → exit 0, "smoke: 389 passed, 0 failed"；其中 acceptance-fleet 段 12/12 PASS`<br>disposition `issue` | — | — |

### R6 判定详情

#### `acceptance-fleet` — A-acceptance-fleet（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后没有任何配件把六份评审输出收成一次可对比的迭代并落盘。引擎会在实现它的同一个 session 里自问自答跑完"验收"，产出一段口头结论：ratchet-log/iteration-NNN/ 不存在，于是 acceptance.evaluation_result 指不到文件，四态（FIX / SPEC_DRIFT / GAMING_RISK / NEEDS_HUMAN）塌缩成一句"再改改"——契约层的错被当成实现层的错发回去重写代码。更具体的漏检：没有 impl-diff.patch 与上一轮快照，spec-gaming-detector 的 diff 模式（"实现者看过上一轮评审后才改的那一处"，它自述置信度最高的模式）永久失效。
    - 证据：`file:plugins/sdlc/skills/acceptance-fleet/SKILL.md#L73` · `file:plugins/sdlc/skills/acceptance-fleet/references/evaluation-isolation-levels.md` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L347-L353`
- **implemented `declared`** — declared（只有 SKILL.md / 提示）
    - 未达 `compiled`：F-06 封顶：独占产物 ratchet-log/iteration-NNN/final-state.json 的 checked_by 仍为空，没有任何脚本读它，v1.1.0 新加的三个必填字段也无人检。重审更正（2026-09-06）：装配时写的"skills/acceptance-fleet/ 下无 scripts/"已不成立——scripts/ 现在有两个脚本，且两个都是真闸：next_iteration.py 在 gaming_risk_threshold 有未知子字段 / 阈值非数字 / done_below > block_at_or_above / 不是映射（#L156-L171）以及前一轮目录缺失（#L189-L191、#L206-L212）时 exit 1；qa_facts.py 在输入不是 qa 报告（#L96）或投影仍带意见键（#L115-L118、#L130-L134）时 exit 1。但它们检的都不是本 Part 的独占产物，所以封顶不动。另两条机械前置的薄弱处仍在：advance pr（sdlc_state.py#L366-L368）只要求 acceptance.evaluation_result 是个非空串，没有 os.path.isfile（对比 #L357 的 lock.path），指向不存在的路径也放行；G3 的 pass 不检任何输入（#L486-L494 只给 G1/G2 写了输入前置）。
    - 未达 `verified`：gate.json evaluated_layers 只有 structural，scripts_run 为空，provenance 自述 NOT a decorrelated read, NOT an L2 run。重审更正（2026-09-06）："本次审计也没有在真实 specs/<feature>/ 上跑过它"已不成立：仓库里有 specs/sdlc-ring-audit/ 与三轮完整的 ratchet-log/iteration-00{1,2,3}（7 份 fleet-outputs + meta-judge-output.yaml + final-state.json + isolation.json，medium 隔离），state.json 的 acceptance.evaluation_result 就指向 iteration-003。按时间戳它在写下时可能就已不成立（iteration-003 written_at 01:03Z，audit.yaml 装配于 01:52）。判定仍是 declared，因为 F-06 的封顶与有没有运行证据无关——"没跑过"不能再当理由，正确的理由只有独占产物无闸这一条。这批记录算不算 Part 级行为层证据仍存疑：isolation.json 自陈 orchestrator 亦是提示词作者，跑的是手工派发的角色提示还是打包的 skill，分辨不出。
    - 证据：`gate_json:plugins/sdlc/skills/acceptance-fleet/eval/gate.json#gate_pass=static_only` · `gate_json:plugins/sdlc/skills/acceptance-fleet/eval/gate.json#scripts_run（空对象）` · `file:plugins/sdlc/skills/sdlc/scripts/sdlc_state.py#L366-L368`
- **naming adopted → `fits`** — 位置 / 产物：`ratchet-log/iteration-NNN/（final-state.json 是它的收口文件）`
    - 命名判定：保留 done-when-pipeline v1.1.0 的上游名，符合 PSL-014「收编保留上游名」；名字指的是"一队评审者"，与它 v1.0.0 重构后"只调度不评审"的职责仍然贴合。
    - 证据：`file:plugins/sdlc/docs/design-notes.md#L39-L42` · `file:plugins/sdlc/skills/acceptance-fleet/SKILL.md#L1-L20`
- **Loop `loops.yaml#acceptance_ratchet`**：acceptance_ratchet 的 loop_back 端点：接 meta-judge 的 iteration_complete 回交（graph.yaml#L349），并按四态向 stage.implement / stage.contract 发回流（graph.yaml#L350-L352）。它本身既不是该环的 generator（implement，loops.yaml#L58）也不是 verifier（meta-judge，loops.yaml#L59）——但它是另一个环 card_retry 的 verifier（loops.yaml#L25），两个身份同时成立。
- disposition `issue`

#### `code-reviewer` — A-code-reviewer（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后 diff 层的缺陷只剩 qa-reviewer 的"测试红不红"。测试没覆盖到的路径——没有断言的分支、错误处理、并发窗口、被吞掉的异常——不再有人读，ARCHITECTURE §3.5 A 档里"有复现的缺陷"那一栏结构性地永远为空，一个可复现的空指针能带着全绿测试合入。同时失去按 focus 并行的多次独立读（security / logic / perf 各一遍），单次"全都看一眼"的读法把同源盲区留在原地。
    - 证据：`file:plugins/sdlc/skills/code-reviewer/SKILL.md#L1-L20` · `file:plugins/sdlc/skills/code-reviewer/references/finding-schema.yaml` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L179`
- **implemented `declared`** — declared（只有 SKILL.md / 提示）
    - 未达 `compiled`：skills/code-reviewer/ 下无 scripts/ 目录；输出 code-review-*.yaml 的形状（references/finding-schema.yaml）无任何脚本校验，也不被门挡——它经 meta-judge 汇入 final-verdict.yaml，而 G3 的 pass 不检任何输入。
    - 未达 `verified`：gate.json evaluated_layers 只有 structural，provenance 自述 NOT an L2 run；无行为层运行记录。
    - 重审更正：重审补记（2026-09-06）：产物名与磁盘不符已被真实 run 坐实——落地的是 fleet-outputs/code-reviewer-{security,logic,perf}.yaml，而 registry 与 graph.yaml#L179 写的是 ratchet-log/iteration-NNN/code-review-*.yaml：少一段 fleet-outputs/，词干也是 code-review- 不是 code-reviewer-。见新缺口 R6/newly_identified/knowledge+control/ratchet-log-filenames-diverge-from-graph。
    - 证据：`gate_json:plugins/sdlc/skills/code-reviewer/eval/gate.json#gate_pass=static_only` · `gate_json:plugins/sdlc/skills/code-reviewer/eval/gate.json#residual=no bundled script`
- **naming adopted → `fits`** — 位置 / 产物：`ratchet-log/iteration-NNN/code-review-*.yaml`
    - 命名判定：保留上游名（PSL-014）。但 gate.json 的 residual 自述"overlaps /pr-review"：同一个仓库里有两个读 diff 出发现的配件，判据几乎同源（pr-review 是它的改编，design-notes#L50-L51）。这不是命名不贴合，是两个配件的边界待裁——记入提案 P-R6-08，不改名。
    - 证据：`file:plugins/sdlc/docs/design-notes.md#L39-L42` · `gate_json:plugins/sdlc/skills/code-reviewer/eval/gate.json#residual=overlaps /pr-review`
- **Loop**：`None` — graph.yaml 节点未带 loop 键；它经 fan_out / fan_in 参与 acceptance_ratchet 的一次迭代（graph.yaml#L347-L348），不是回边端点，故按 PSL-011「不要求每个配件属于某个环」不强行归环。
- disposition `issue`

#### `qa-reviewer` — A-qa-reviewer（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后没有配件真的去执行测试：引擎读一遍测试文件然后声称"这些应该会过"，用 LLM 的阅读取代进程的退出码——这正是 PSL-010「静态过审 ≠ 有效」点名的那次替换。具体错误产物：一份 qa-review.yaml 里写着 go，而套件从未运行；失败分类（测试自己腐烂 vs 代码真错）消失，一条改了断言的旧测试与一个真 bug 不可分辨；mutation 一栏空着，行覆盖率成为唯一且可刷的指标。
    - 证据：`file:plugins/sdlc/skills/qa-reviewer/SKILL.md#L1-L20` · `file:plugins/sdlc/skills/qa-reviewer/references/maintenance-vs-genuine.md` · `file:plugins/sdlc/skills/qa-reviewer/references/test-layer-protocol.md`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：gate.json evaluated_layers 只有 structural，scripts_run 为空；无行为层运行记录。这一条尤其刺眼：一个以"真跑"为定义性差异的配件，自身停在静态过审。而它自己"真跑测试"这条铁律仍然没有任何脚本兜底——qa_facts.py 只核对产物的根键在不在，没有一个执行器包装（thresholds 比对、退出码采集）可以证明套件确实跑过。skills/qa-reviewer/ 下至今无 scripts/。
    - 重审更正：declared → compiled（重审 2026-09-06，编排者裁，本次唯一一处有异议的抬档）。 新脚本 qa_facts.py 会拒绝本 Part 的产物：#L93-L96 读不到顶层 `qa_report:` 映射即 die(...,1)， 而顶层键 `qa_report:` 正是 qa-reviewer 自己的输出契约声明的根（references/finding-schema.yaml#L3）。 按本审计写下来的尺子 —— 闸 = 存在以该产物内容为条件的非零退出路径 —— 这一条成立； 它与 compute_score.py / compute_confidence.py 那种"也不拒绝任何输入"的计算原语正好相反， 而"不拒绝任何输入"正是本文件当初拒绝给它们 compiled 的原话。 **反对意见并列记下**：这条闸只核对根键在不在，且是投影脚本的副作用，不承载 qa-reviewer 的任何判据； 若按"脚本要承载该配件的判据才算 verify 脚本"的更严读法，应退回 declared。 裁定维持抬档 —— 在裁决时临时发明一条比审计写下来的更严的线来压低档位， 和发明一条更松的线来抬高它，是同一种漂移。薄在哪里写进 not_reached.verified，不藏。
    - 证据：`gate_json:plugins/sdlc/skills/qa-reviewer/eval/gate.json#gate_pass=static_only` · `gate_json:plugins/sdlc/skills/qa-reviewer/eval/gate.json#residual=no bundled script` · `file:plugins/sdlc/skills/acceptance-fleet/scripts/qa_facts.py#L96` · `file:plugins/sdlc/skills/qa-reviewer/references/finding-schema.yaml#L3`
- **naming adopted → `fits`** — 位置 / 产物：`ratchet-log/iteration-NNN/qa-review.yaml`
    - 命名判定：保留上游名（PSL-014）；qa 与它的产物 qa-review.yaml 同词干，按 F-03 判 fits。
    - 证据：`file:plugins/sdlc/docs/design-notes.md#L39-L42`
- **Loop**：`None` — 同 code-reviewer：fan_out / fan_in 成员（graph.yaml#L347-L348），非回边端点。它另被 loops.yaml#L22 记为 card_retry 的 goal 检查处之一。
- disposition `issue`

#### `pm-reviewer` — A-pm-reviewer（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后没有配件逐条把 REQ 对回代码。验收退化成"测试绿即合规"，于是契约里没被写成测试的 SHALL 条款——尤其那些只能由人判的 UI/UX 意图——无人认领：pm-review.yaml 里的 requires_human_verification 清单不存在，ARCHITECTURE §3.5 C 档"请求人工"的输入为空，G3 拿到的是一份没有待人判条目的报告，于是签得很轻松。REQ 覆盖率这个 A 档检查项失去数据源。
    - 证据：`file:plugins/sdlc/skills/pm-reviewer/SKILL.md#L1-L22` · `file:plugins/sdlc/skills/pm-reviewer/references/requirement-normalization.md` · `file:plugins/sdlc/skills/pm-reviewer/references/agent-as-judge-protocol.md`
- **implemented `declared`** — declared（只有 SKILL.md / 提示）
    - 未达 `compiled`：skills/pm-reviewer/ 下无 scripts/；四态判决（fully / partially / not_compliant / requires_human_verification）与 REQ 覆盖率都无脚本核对，pm-review.yaml 不被门挡。重审补记（2026-09-06）：现在有脚本会去 open 它——next_iteration.py#L214-L221 找 fleet-outputs/pm-reviewer.yaml，但只做 os.path.isfile，找不到就 warn 并把 PREV_PM_REVIEW 留空、继续 exit 0，从头到尾不解析文件内容。这是"有脚本读它 ≠ 有闸"的样本，写在这里免得下一轮有人看到脚本名就抬档。
    - 未达 `verified`：gate.json evaluated_layers 只有 structural，scripts_run 为空；无行为层运行记录。
    - 证据：`gate_json:plugins/sdlc/skills/pm-reviewer/eval/gate.json#gate_pass=static_only` · `gate_json:plugins/sdlc/skills/pm-reviewer/eval/gate.json#residual=no bundled script`
- **naming adopted → `fits`** — 位置 / 产物：`ratchet-log/iteration-NNN/pm-review.yaml`
    - 命名判定：保留上游名（PSL-014）；pm 与产物 pm-review.yaml 同词干，按 F-03 判 fits。
    - 证据：`file:plugins/sdlc/docs/design-notes.md#L39-L42`
- **Loop**：`None` — 同 code-reviewer：fan_out / fan_in 成员（graph.yaml#L347-L348），非回边端点。
- disposition `none`

#### `spec-drift-detector` — A-spec-drift-detector（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后 spec 与代码的分叉只会在下一次有人读文档时偶然发现。没有配件回答"它们何时分的岔、那个 commit 看起来是有意的吗"，于是四态里的 SPEC_DRIFT 永远不会被触发——graph.yaml#L351 那条 acceptance-fleet → stage.contract 的回边成为死边。后果不是少一份报告，是回流全部落到 card / plan 层（改代码），而真正该改的是契约：世界层与契约层的错在实现层被反复重试，正是 routing.yaml 存在要防的那件事。
    - 证据：`file:plugins/sdlc/skills/spec-drift-detector/SKILL.md#L1-L19` · `file:plugins/sdlc/skills/spec-drift-detector/references/divergence-types.md` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L351`
- **implemented `declared`** — declared（只有 SKILL.md / 提示）
    - 未达 `compiled`：skills/spec-drift-detector/ 下无 scripts/；git archaeology 全靠提示里的 git log / blame / show 约定，没有脚本固定它，drift.yaml 不被脚本校验也不被门挡。
    - 未达 `verified`：gate.json evaluated_layers 只有 structural，scripts_run 为空；无行为层运行记录。
    - 重审更正：重审补记（2026-09-06）：判定与 not_reached 全部不变（drift.yaml 仍无脚本、无门），但它的**输入契约** 本轮被单边改了而它自己不知道——acceptance-fleet 现在按 skill-dispatch-matrix.md#L147-L151 传 --qa-measurements 并明令禁止 --qa-report，而 spec-drift-detector/SKILL.md#L63 的参数表仍只定义 --qa-report、#L50 的铁律 8 仍指导用它。见新缺口 R6/newly_identified/control/drift-consumer-flag-not-updated。
    - 证据：`gate_json:plugins/sdlc/skills/spec-drift-detector/eval/gate.json#gate_pass=static_only` · `gate_json:plugins/sdlc/skills/spec-drift-detector/eval/gate.json#residual=no bundled script`
- **naming adopted → `fits`** — 位置 / 产物：`ratchet-log/iteration-NNN/drift.yaml`
    - 命名判定：保留上游名（PSL-014）。lifecycle.md#L62 记了一个同名不同层的对照：spec-drift（任务层）vs ontology-drift（本体层，空白）——名字带 spec- 前缀恰好把这条层次差别标出来了，判 fits。
    - 证据：`file:plugins/sdlc/docs/design-notes.md#L39-L42` · `file:plugins/sdlc/docs/lifecycle.md#L62`
- **Loop**：`None` — 同 code-reviewer：fan_out / fan_in 成员（graph.yaml#L347-L348），非回边端点。
- disposition `none`

#### `spec-gaming-detector` — A-spec-gaming-detector（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后没有配件以"作者在作弊"为默认假设读产物——其余五个评审者的默认假设都是"作者在努力做对"。于是这几类产物会以 A 档全绿的形态通过：把测试断言改松让它变绿、只对着测试用例硬编码期望值的分支、为覆盖率写的空断言测试。更远的后果在契约侧：gaming.yaml 的 spec_robustness_gaps 段不再回流给契约作者，下一轮 done_when.yaml 仍然同样好骗，四态里的 GAMING_RISK 从状态机里消失。
    - 证据：`file:plugins/sdlc/skills/spec-gaming-detector/SKILL.md#L1-L21` · `file:plugins/sdlc/skills/spec-gaming-detector/references/rhd-patterns.md` · `file:plugins/sdlc/skills/spec-gaming-detector/references/diff-mode-protocol.md`
- **implemented `declared`** — declared（只有 SKILL.md / 提示）
    - 未达 `compiled`：scripts/compute_score.py 存在，但它是确定性计算原语，不是 verify 脚本：它把 severity 折成一个 0-10 的分数并打印，除 IO / JSON 解析错误外没有任何非零退出路径，也不拒绝任何输入——它自己的收尾行写着"thresholds（≥7 = GAMING_RISK）are the consumer's call"。判据在消费者手里，脚本不承重，所以不构成 PSL-010 意义上的"有 verify 脚本"。gaming.yaml 也不被门挡。重审补记（2026-09-06）：现在有一个会真解析它的脚本——next_iteration.py#L100-L124 取 gaming_risk_score 与 baseline_score（先 yaml，退化到正则），但这条路径上没有任何非零退出：文件缺失返回 (None, None)，解析失败 warn，无分数 warn，甚至 #L236-L249 那条 baseline 对账查出真实矛盾也只是 warn。实测最有力：在真实 ratchet-log 上跑 N=3，它准确报出 "iteration-003 recorded baseline_score 3.5 but iteration-002 produced 4"——即 I-72 那个真缺陷——然后 exit 0。它是报告工具，不是闸。
    - 未达 `verified`：gate.json evaluated_layers 只有 structural，provenance 自述 NOT an L2 run；scripts_run 记录的是 compute_score.py 在 fixture 上的一次算术演练（P0+P1+P3 → 5.5），那是原语的行为层证据，不是配件的。
    - 证据：`gate_json:plugins/sdlc/skills/spec-gaming-detector/eval/gate.json#gate_pass=static_only` · `gate_json:plugins/sdlc/skills/spec-gaming-detector/eval/gate.json#scripts_run.compute_score.py` · `file:plugins/sdlc/skills/spec-gaming-detector/scripts/compute_score.py#L68-L101`
- **naming adopted → `fits`** — 位置 / 产物：`ratchet-log/iteration-NNN/gaming.yaml`
    - 命名判定：保留上游名（PSL-014）；gaming 与产物 gaming.yaml 同词干，判 fits。
    - 证据：`file:plugins/sdlc/docs/design-notes.md#L39-L42`
- **Loop**：`None` — 同 code-reviewer：fan_out / fan_in 成员（graph.yaml#L347-L348），非回边端点。
- disposition `issue`

#### `meta-judge` — A-meta-judge（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后五份评审输出没有配件做去重 / 加权 / 仲裁 / 归档。具体错误产物：同一处缺陷被五个角色各报一次，fix-prompt 里出现五条同根因的修改要求，实现者改三遍改出互相打架的 diff；两份互相矛盾的判决（pm-reviewer 说合规、spec-drift-detector 说分叉）没有裁决者，四态无法从证据推出——只能由 acceptance-fleet 自己下判，而它同时是调度者，评估与被评估合一，PSL-003 的分离在最后一步失效。它的硬墙（graph.yaml#L188 must_not_read: impl_dir）是这条分离的机器表达：合成者不许重读代码，否则它变成第六个评审者。
    - 证据：`file:plugins/sdlc/skills/meta-judge/SKILL.md#L1-L22` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L188` · `file:plugins/sdlc/skills/meta-judge/references/synthesis-protocol.md`
- **implemented `declared`** — declared（只有 SKILL.md / 提示）
    - 未达 `compiled`：scripts/compute_confidence.py 与 spec-gaming-detector 的 compute_score.py 同类：确定性加权原语，把 sources 折成一个 confidence 数，无任何 sys.exit(非零) 路径，不拒绝任何输入。它没有校验 final-verdict.yaml 的形状，也没有检查"是否真的没重读代码"这条硬墙。final-verdict.yaml 不被门挡：G3 的 pass 不检任何输入（sdlc_state.py#L486-L494）。
    - 未达 `verified`：gate.json evaluated_layers 只有 structural，provenance 自述 NOT an L2 run；scripts_run 里那条 two-source cross-vendor high → 1.0 是原语的算术演练，不是配件的行为层证据。
    - 重审更正：重审补记（2026-09-06）：产物标识分裂（final-verdict.yaml vs meta-judge-output.yaml，P-R6-05） 不但没修，还被真实 run 坐实——三轮 iteration 目录里落地的全是 meta-judge-output.yaml， 而 graph.yaml#L189 声明的是 final-verdict.yaml。
    - 证据：`gate_json:plugins/sdlc/skills/meta-judge/eval/gate.json#gate_pass=static_only` · `gate_json:plugins/sdlc/skills/meta-judge/eval/gate.json#scripts_run.compute_confidence.py` · `file:plugins/sdlc/skills/meta-judge/scripts/compute_confidence.py#L74-L104`
- **naming adopted → `fits`** — 位置 / 产物：`ratchet-log/iteration-NNN/final-verdict.yaml（graph.yaml#L189 的声明）`
    - 命名判定：配件名保留上游名（PSL-014），fits。但它的**产物**有两个名字：graph.yaml#L189 声明 writes: ratchet-log/iteration-NNN/final-verdict.yaml，而 meta-judge 自己的 --output 默认值（SKILL.md#L75）与 M5 步（#L87）、以及 acceptance-fleet 的目录契约（ratchet-log-format.md#L41、SKILL.md#L157/#L254）都写 meta-judge-output.yaml。同一份 SKILL.md 内部也不一致：description 与 M0 播报说 final-verdict.yaml，参数表说 meta-judge-output.yaml。这是产物标识分裂，不是配件命名问题——记入提案 P-R6-05，不改名。
    - 证据：`file:plugins/sdlc/docs/design-notes.md#L39-L42` · `file:plugins/sdlc/skills/meta-judge/SKILL.md#L75` · `file:plugins/sdlc/skills/acceptance-fleet/references/ratchet-log-format.md#L41`
- **Loop `loops.yaml#acceptance_ratchet`**：acceptance_ratchet 的 verifier（loops.yaml#L59）兼 loop_back 源（graph.yaml#L349，signal: iteration_complete）。该环 generator 是 implement（loops.yaml#L58），故 R014「generator ≠ verifier」在这个环上成立。注意 graph.yaml 的 meta-judge 节点本身没有 loop 键，环归属只能从边和 loops.yaml 反推——见提案 P-R6-05 附注。
- disposition `issue`

#### `pr-review` — A-pr-review（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后单个 PR 的手审没有配件，走全套 acceptance-fleet 又太重（它要 specs/<feature>/ 与 tests/），于是引擎回一句"看起来不错"就发出去，或者反过来堆二十条风格意见。具体错误产物：P0 不带复现场景就发成 GitHub 行内评论，reviewer 无法判真假只能自己重查；发现不分 A/B/C 档，B 档的复杂度告警和 A 档的缺陷一样一票否决，PR 要么卡死要么全放行——两种都不是三档。还有一处只有它守着：approve 是人的动作，没有它就没有配件拒绝 agent 去 approve。
    - 证据：`file:plugins/sdlc/skills/pr-review/SKILL.md#L1-L20` · `file:plugins/sdlc/skills/pr-review/references/tiers.md` · `file:plugins/sdlc/skills/pr-review/scripts/post_review.py#L77-L98`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：gate.json 的 harness_note 明写：gh 网络路径（真实 gh api .../reviews POST）未演练，只跑过 --dry-run 与 fixture。所以"发得出去、发对地方"这一层没有行为层证据。
    - 这把尺子本身校准了没有（PSL-007）：`calibrated: false`
    - 证据：`file:plugins/sdlc/skills/pr-review/scripts/post_review.py#L79` · `file:plugins/sdlc/skills/pr-review/scripts/post_review.py#L97` · `gate_json:plugins/sdlc/skills/pr-review/eval/gate.json#gate_pass=static_only` · `gate_json:plugins/sdlc/skills/pr-review/eval/gate.json#scripts_run.post_review.py`
- **naming authored → `fits`** — 位置 / 产物：`.sdlc/review/<pr>-<focus>.yaml（SKILL.md#L80；ARCHITECTURE.md#L40 在 R6 产物列里叫它 findings.yaml）`
    - 命名判定：它是 done-when-pipeline /code-reviewer v1.0.0 的**改编**（design-notes#L50-L51：判据照搬，加三档归位与 post_review.py），改编时没有保留上游名而是按位置新命名——按 design-notes#L70 的第 3 条（新 skill 按产物命名）走，故 provenance 判 authored 而非 adopted。名字指"审 PR 的入口"，与位置贴合。
    - 证据：`file:plugins/sdlc/docs/design-notes.md#L50-L51` · `file:plugins/sdlc/docs/design-notes.md#L70` · `file:plugins/sdlc/skills/pr-review/SKILL.md#L80`
- **Loop**：`None` — 不是回边端点：graph.yaml#L335-L336 的 pr → pr-review → review-loop 两条都是 handoff。它是 R6 的单 PR 手审入口（ARCHITECTURE.md#L40 R6 行末尾"单 PR 手审：/pr-review"），产物流向 R7 的作者环。
- disposition `issue`

#### `human_gate.G3` — A-G3（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后四态里的 NEEDS_HUMAN 无处落地。human AC（UI/UX 意图、架构取舍）、pm-reviewer 的 requires_human_verification 清单、以及"在当前契约下不可能"的升级报告都没有收件人，acceptance-fleet 只能把它们降级成 FIX 发回实现者——实现者拿到一个他判不了的判断题，于是猜一个改法，猜错的那一次以全绿合入。这就是"机器判不了的地方"被机器判了：三道门存在的位置，正是机器判断不被信任的位置。
    - 证据：`file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L197-L203` · `file:plugins/sdlc/docs/ARCHITECTURE.md#L40` · `file:plugins/sdlc/skills/sdlc/scripts/sdlc_state.py#L374-L375`
- **implemented `declared`** — declared（只有 SKILL.md / 提示）
    - 未达 `compiled`：F-06 封顶（G3 裁定，mf-009）：本 Part 登记的每一个 Artifact 的 checked_by 都为空——g3-record.md 没有任何脚本检其形状，cmd_gate 对 G3 的 pass 也不检任何输入。既然产物无闸，producer 不得高于 declared。原记 compiled 系按"有 sdlc_state.py gate 这条命令"读，G3 裁定该读法把"有命令"当成了"有闸"。
    - 未达 `verified`：重审更正（2026-09-06）：装配时写的"本次 Run 的 G3 还没到（stage = implement）"已不成立——state.json 里 stage 已是 archive，gates.g3 = {verdict: pass, by: g3-judge, at: 2026-09-06T02:11:00Z, signer_kind: delegated_agent, record: g3-record.md}。"没有真人签过"这半句仍成立：签字是 delegated_agent，不是人，而且那份记录自陈"G3 的 pass 无输入前置、--authorization 无人核对"。第二半句逐字仍成立：即便签了也不构成对 R6 产物的行为层校验——cmd_gate 对 G3 pass 不检任何输入，对比 G1 pass 要求 world.derived_dir 是个存在的目录、G2 pass 要求 lock.path 是个存在的文件（sdlc_state.py#L486-L494），G3 那一支是空的。见 gap R6/newly_identified/control/g3-pass-has-no-input-precondition。
    - 证据：`file:plugins/sdlc/skills/sdlc/scripts/sdlc_state.py#L373-L376` · `file:plugins/sdlc/skills/sdlc/scripts/sdlc_state.py#L502-L503` · `file:plugins/sdlc/skills/sdlc/scripts/sdlc_state.py#L392-L393`
- **naming authored → `fits`** — 位置 / 产物：`g3-record.md / 例外复核门（验收之后、合入之前）`
    - 命名判定：新写的门，按位置命名（G1 世界裁决 / G2 判据冻结 / G3 例外复核），编号即位置，fits。注意 Part id 用 human_gate.G3 而 graph.yaml 节点 id 是 human.g3——两处标识不同词形，此处按 AC 的 required_parts 名单逐字取 human_gate.G3。
    - 证据：`file:plugins/sdlc/docs/ARCHITECTURE.md#L40` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L197`
- **Loop `loops.yaml#lifecycle`**：lifecycle 环的 verifier（loops.yaml#L94），generator 是脊柱 sdlc（#L93）——R014 的 generator ≠ verifier 由此成立。它不是 acceptance_ratchet 的端点：acceptance-fleet 到它的边是 interrupt 不是 loop_back（graph.yaml#L353）。
    - 环归属来源 `graph.yaml`（plugins/sdlc/skills/sdlc/assets/graph.yaml#L197-L203）：id: human.g3, kind: human, role: gate；acceptance-fleet 经 interrupt 边到它（#L343）
    - 环归属来源 `ARCHITECTURE.md §1`（plugins/sdlc/docs/ARCHITECTURE.md#L40）：R6 行的「门 / 闸」列写 **G3**
- disposition `issue`

#### `agent.review-triager` — A-review-triager（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后 PR 评论被当成指令直接照做。reviewer 可能看的是旧 commit、也可能读错了代码，于是一条错误主张变成一次真改动——错误产物是"为了让 reviewer 满意"而引入的回归。另外三类漏检：越界评论（要求跑命令、改 CI、外发数据、装来路不明依赖、删测试）没有拦截点；疑似 prompt injection 的评论被当成需求执行；多条同根因评论被分别修复，diff 里留下三处互相打架的改动。它与 comment-fixer 分开还有一层作用——裁决与修复隔离，修复者看不到其它线程（graph.yaml#L229 的 must_not_read）。
    - 证据：`file:plugins/sdlc/agents/review-triager.md#L13-L22` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L358-L359`
- **implemented `declared`** — declared（只有 SKILL.md / 提示）
    - 未达 `compiled`：plugins/sdlc/agents/ 下只有 .md 提示文件，没有 scripts/、也没有 eval/gate.json（对比每个 skill 都有 eval/gate.json）。triage.yaml 的形状无脚本校验：pr-poll.sh 管的是线程水位线与 strike 计数，不读 triage.yaml。也不被门挡。
    - 未达 `verified`：无 eval/gate.json，连静态过审的档位记录都没有——agent 这一类配件整体不在 gate.json 的证据档位纪律覆盖范围内（提案 P-R6-10）。无行为层运行记录。
    - 证据：`file:plugins/sdlc/agents/review-triager.md#L1-L6` · `file:plugins/sdlc/skills/review-loop/scripts/pr-poll.sh`
- **naming authored → `fits`** — 位置 / 产物：`triage.yaml`
    - 命名判定：新写（design-notes#L57「review-triager 新写」），按产物 triage.yaml 命名，同词干，判 fits。
    - 证据：`file:plugins/sdlc/docs/design-notes.md#L57`
- **role_conflict**：F-08 / F-24：两源并列，不调和。Node.role = evaluator 说它是评估者（R6 的身份），§1 的行位置说它在交付环里跑（R7 的位置）。本片段按 Node.role 落 R6 并如实记下 §1 的另一读法；哪个是对的由人裁。
    - 环归属来源 `graph.yaml`（plugins/sdlc/skills/sdlc/assets/graph.yaml#L219-L221）：kind: agent, role: evaluator → 按 Node.role 落 R6 验收
    - 环归属来源 `ARCHITECTURE.md §1`（plugins/sdlc/docs/ARCHITECTURE.md#L41）：R7 交付行把 review-loop 线（含它的分诊 / 修复 / 验证子 agent）列在 R7
- disposition `issue`

#### `agent.fix-verifier` — A-fix-verifier（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后修复由修复者自己宣布完成。没有配件在全新上下文里从主张出发构造触发输入、确认原现象是否还在，于是"加了个 try/except 让报错不再打印"与"修了根因"产出同样的绿；没有人读复现测试的断言，一条断言为空、只断言不抛异常的测试会被当成复现证据；全套件不跑，回归留到 merge 之后；范围超界（顺手重构、动了 tests/ 断言或锁文件）在同一个 commit 里溜过去。本质是 generator 与 verifier 合一——self-verification，loops.yaml 头部点名的反模式。
    - 证据：`file:plugins/sdlc/agents/fix-verifier.md#L20-L28` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L232-L238` · `file:plugins/sdlc/skills/sdlc/assets/loops.yaml#L75-L76`
- **implemented `declared`** — declared（只有 SKILL.md / 提示）
    - 未达 `compiled`：plugins/sdlc/agents/ 下无 scripts/、无 eval/gate.json；verify.yaml 无脚本校验，也不被门挡。它自己第 3 条判据要求跑全套件 + lint + 类型 + 构建，但没有任何机械物证明这几条跑过——与 qa-reviewer 同型的问题。
    - 未达 `verified`：无 eval/gate.json，无行为层运行记录；loops.yaml#L76 本身把它标为可选，说明这条路径在设计上就允许不跑。
    - 证据：`file:plugins/sdlc/agents/fix-verifier.md#L1-L6` · `file:plugins/sdlc/skills/sdlc/assets/loops.yaml#L76`
- **naming adopted → `fits`** — 位置 / 产物：`verify.yaml`
    - 命名判定：判 fits：fix-verifier 按产物 verify.yaml / 位置（验修复）命名，贴合。但收编时**没有保留上游名**——design-notes#L56-L57 记的是 qanat quality-sentinel → fix-verifier，与 PSL-014「收编保留上游名」的那一路不一致（同批 agent 里 issue-fixer → comment-fixer、code-reviewer → pr-reviewer 都改了名）。要记的不是把它改回去（新名更贴合），而是"收编即改名"这件事与 PSL-014 的分歧本身——记入提案 P-R6-07。rename 恒为 false：建议不等于重命名。
    - 证据：`file:plugins/sdlc/docs/design-notes.md#L56-L57`
- **Loop `loops.yaml#review_loop`**：review_loop 的 loop_back 源（graph.yaml#L363，signal: iteration_complete）。loops.yaml#L76 把它记为**可选的**机器 verifier，该环正式 verifier 是 human_reviewer，generator 是 agent.comment-fixer（#L75）——R014 成立不依赖它。
- **role_conflict**：F-08 / F-24：两源并列，不调和。与 agent.review-triager 同一条冲突。
    - 环归属来源 `graph.yaml`（plugins/sdlc/skills/sdlc/assets/graph.yaml#L232-L234）：kind: agent, role: evaluator → 按 Node.role 落 R6 验收；must_not_read: fixer_session
    - 环归属来源 `ARCHITECTURE.md §1`（plugins/sdlc/docs/ARCHITECTURE.md#L41）：R7 交付行把 review-loop 线列在 R7
- disposition `issue`

[^A-acceptance-fleet]: `acceptance-fleet` 的 PSL-ID 追溯 — needed PSL-002, PSL-003, PSL-011 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L171-L178`。
[^A-code-reviewer]: `code-reviewer` 的 PSL-ID 追溯 — needed PSL-002, PSL-003 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L179`。
[^A-qa-reviewer]: `qa-reviewer` 的 PSL-ID 追溯 — needed PSL-002, PSL-010 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L180`。
[^A-pm-reviewer]: `pm-reviewer` 的 PSL-ID 追溯 — needed PSL-002, PSL-003 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L181`。
[^A-spec-drift-detector]: `spec-drift-detector` 的 PSL-ID 追溯 — needed PSL-002, PSL-008 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L182`。
[^A-spec-gaming-detector]: `spec-gaming-detector` 的 PSL-ID 追溯 — needed PSL-002, PSL-003, PSL-010 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L183`。
[^A-meta-judge]: `meta-judge` 的 PSL-ID 追溯 — needed PSL-002, PSL-003 · implemented PSL-010, PSL-015 · naming PSL-014, PSL-001。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L184-L190`。
[^A-pr-review]: `pr-review` 的 PSL-ID 追溯 — needed PSL-002, PSL-006 · implemented PSL-010, PSL-006, PSL-015 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L191-L196`。
[^A-G3]: `human_gate.G3` 的 PSL-ID 追溯 — needed PSL-006, PSL-002 · implemented PSL-006, PSL-010 · naming PSL-014, PSL-006。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L197-L203`。
[^A-review-triager]: `agent.review-triager` 的 PSL-ID 追溯 — needed PSL-002, PSL-003 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L219-L224`。
[^A-fix-verifier]: `agent.fix-verifier` 的 PSL-ID 追溯 — needed PSL-003, PSL-002 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L232-L238`。

## R7 交付

**问题**：合入与发布——改动怎么进 main，怎么算交付完成？

5 个配件 · 5 处登记为缺少。

| 配件 / 缺少 | kind | 缺口 · 原子 | 独占产物 / 角色 | 闸 · 门 | artifact 闸（checked_by） | Loop | needed | implemented | naming |
|---|---|---|---|---|---|---|---|---|---|
| `pr` [^A-pr] | `skill` | `Judgment+Control` pr-body-product-order | `github:pr` | 闸 `verify_pr.py` | `github:pr` → `verify_pr.py` | `null` | **necessary** | **compiled**<br>未达：`verified`<br>`calibrated: false` | authored → **fits** |
| `review-loop` [^A-review-loop] | `skill` | `Capability+Judgment+Control` review-convergence-binding | `.sdlc/pr-watch/pr-N.json` | 闸 `pr-poll.sh` | `.sdlc/pr-watch/pr-N.json` → `pr-poll.sh`<br>`github:reply` → **（无闸 → 封顶 declared）**<br>`github:resolve` → **（无闸 → 封顶 declared）** | `loops.yaml#review_loop` | **necessary** | **compiled**<br>未达：`verified`<br>`calibrated: false` | adopted → **fits** |
| `agent.pr-reviewer` [^A-agent.pr-reviewer] | `agent` | `Judgment` pre-review-isolated-second-read | `findings.yaml (pre-review)` | 闸 `verify_pr.py` | `findings.yaml (pre-review)` → `pr-poll.sh` | `review_loop` | **necessary** | **compiled**<br>未达：`verified`<br>`calibrated: false` | adopted → **fits** |
| `human_gate.merge` [^A-human_gate.merge] | `human_gate` | `Judgment+Control` merge-is-a-human-act | `github:merge`<br>role `gate` | **无闸无门** | `github:merge` → **（无闸 → 封顶 declared）** | `null` | **necessary** | **declared**<br>未达：`compiled` / `verified` | authored → **fits** |
| `release` [^A-release] | `skill` | `Judgment+Control` post-merge-delivery-order | `releases/vX.Y.Z.md` | 闸 `verify_release.py` | `git:tag vX.Y.Z` → `verify_release.py`<br>`CHANGELOG.md` → `verify_release.py`<br>`releases/vX.Y.Z.md` → `verify_release.py` | `null` | **necessary** | **compiled**<br>未达：`verified`<br>`calibrated: false` | authored → **fits** |
| **（缺少）** `merge-signer-not-enforced` | — | `Control`<br>**unenforced_rule（宪法有规则、机器无闸）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：dos.yaml R008「Gate 的裁决带人类签字人，skill / agent 节点不得记录它」的 enforced_by 是 user_workflow —— 没有脚本阻止一个 agent 记下 merge 这道人门的结论。具体漏检：一次由 agent 代记的合入裁决与人签的合入裁决在 state.json 里长得一模一样，事后无法分辨。<br>证据：`file:plugins/sdlc/dogfood/ring-audit/dos.yaml#L404-L407` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L249-L255`<br>disposition `issue` | — | — |
| **（缺少）** `static-only-claim-not-enforced` | — | `Judgment`<br>**unenforced_rule（宪法有规则、机器无闸）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：dos.yaml R017「效力主张不得超出证据档位，static_only 的 skill 不得被描述为 verified」的 enforced_by 是 user_workflow。R7 三个 skill 的 gate.json 全是 static_only，但流水线里没有任何 脚本会拒绝一份写着"已验证"的报告。具体错误产物：一份把 fixture 冒烟读成行为层证据的验收结论。<br>证据：`file:plugins/sdlc/dogfood/ring-audit/dos.yaml#L440-L443` · `gate_json:plugins/sdlc/skills/pr/eval/gate.json#gate_pass=static_only` · `gate_json:plugins/sdlc/skills/release/eval/gate.json#gate_pass=static_only`<br>disposition `issue` | — | — |
| **（缺少）** `merged-sha-vs-approved-head` | — | `Control`<br>**newly_identified（本次审计新识别）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：没有任何脚本核对 merge.sha 与 review / G3 批准过的 head 是不是同一个东西 —— sdlc_state.py 进 release 的前置条件只是"merge.sha 存在"（ARCHITECTURE §3.1）。 具体漏检：批准之后又推了一个 commit 再合入，合进 main 的内容没有被任何人看过， 而 release 照常打 tag 发版。<br>证据：`file:plugins/sdlc/docs/ARCHITECTURE.md#L99-L100` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L366-L367`<br>disposition `issue` | — | — |
| **（缺少）** `reply-resolve-order-unchecked` | — | `Control`<br>**newly_identified（本次审计新识别）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：「回帖先于 resolve」与「REJECT 不 resolve」是 review-loop/SKILL.md#L113-L117 的判据， 但 pr-poll.sh#L313 自己写明"该不该 resolve 是模型的判据；脚本只保证用对原语" —— resolve 子命令不核对该线程上有没有落地的回帖。具体错误产物：一个被无声折叠（未回帖即 resolve） 的 reviewer 异议线程，exit 0 的"未解决线程 = 0"因此可以被凑出来。<br>证据：`file:plugins/sdlc/skills/review-loop/scripts/pr-poll.sh#L312-L314` · `file:plugins/sdlc/skills/review-loop/SKILL.md#L113-L117`<br>disposition `issue` | — | — |
| **（缺少）** `solo-a-tier-count-not-from-the-contract` | — | `Judgment`<br>**newly_identified（本次审计新识别）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：solo 谓词用来替代人类 APPROVE 的六项条件里，"该轮 A 档存活 = 0"是唯一一项关于**内容**的判据， 而它的取数方式与 /pr-review 的产物契约对不上：pr-poll.sh#L400-L405 先找显式的 `a_tier_survivors: N`，找不到就 `grep -Eic '(tier\|severity):\s*(A\|P0)'` 数**行**。 但 `a_tier_survivors` 不是 /pr-review 输出的字段——findings_template.yaml 里根本没有它， 模板声明的是 `tier_summary: { A: n, B: n, C: n }`（#L14），而脚本从不读 tier_summary。 于是真实文件一律落进 fallback，而 fallback 数的是行不是条目：每条 A 档发现同时带 `tier: A` 与 `severity: P0` 两行，一条算两条。具体错误产物 —— 用本仓库真实的 pre-review/pr3-round-1.findings.yaml（tier_summary { A: 1 }）实测，脚本报 a_tier=2； 写进 counters 的 `.self_review.last.a_tier` 与 SKILL.md#L35 承诺向人汇报的"A 档存活数"因此是错的。 具体漏检 —— 方向上是 fail-closed（不会误判收敛），但它把作者逼回自证：round-1 里已修掉的 A 档没有任何机械方式表达为"已存活 0"，唯一出路是手写一个契约里不存在的 `a_tier_survivors: 0` 键——正是这道闸（I-87）想取消的那种自我声明。<br>证据：`file:plugins/sdlc/skills/review-loop/scripts/pr-poll.sh#L400-L405` · `file:plugins/sdlc/skills/pr-review/assets/findings_template.yaml#L14（tier_summary，无 a_tier_survivors）` · `file:plugins/sdlc/skills/review-loop/SKILL.md#L71-L73（判据自陈：显式 a_tier_survivors，没有就数 tier/severity 条目）` · `run_record:plugins/sdlc/dogfood/ring-audit/pre-review/pr3-round-1.findings.yaml：tier_summary { A: 1 }，脚本 fallback 计数 = 2（#L22 tier: A 与 #L23 severity: P0 各命中一次）`<br>disposition `fix_list` | — | — |

### R7 判定详情

#### `pr` — A-pr（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后引擎走 `gh pr create --fill`：产出的 PR body 是一串 commit 标题。具体错误产物 —— 一个没有 Scope 段与 AC→证据映射的 PR body；下游 /review-loop 判"越界类"评论失去基准 （review-loop/SKILL.md 以 PR body 的范围声明为对照），A 档验收拿不到"每条 mechanical AC 对应哪条可复现证据"；具体漏检 —— 一次 1200 行的 XL diff 不被体量判据拦下就进入 review。
    - 证据：`file:plugins/sdlc/skills/pr/SKILL.md#L23-L27` · `file:plugins/sdlc/skills/pr/scripts/verify_pr.py#L295` · `file:plugins/sdlc/skills/review-loop/SKILL.md#L31-L38`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：重审更正（2026-09-06）："无行为层运行记录"已不成立：gh pr create 这条路跑过一次 —— ledger 2026-09-06T01:52:22 记 "PR #2 opened as draft against main from docs/1-sdlc-ring-audit at efd45ac (46 commits). verify_pr PASS"，03:46:36 记该 PR 由用户本人合入（merge.sha=1e671f3）。 仍不到 verified，三条理由：(a) 那次实跑用的是**修复前**的 verify_pr.py —— PR 建于 09:52+08:00， 而版本同步（#L73-L125 + 调用点 #L239-L244，I-76）与 merge 提交主题豁免（#L265-L285，I-74） 这两条新增 REJECT 路径的提交落在 12:39+08:00 之后，它们至今只有 fixture 证据； (b) gate.json 的 harness_note 与 fix_list 第 2 条 "gh pr create path not exercised" 都没更新， 证据档比代码旧（见缺口 R5/newly_identified/control/gate-json-stale-after-script-lands）； (c) 一次成功路径不是带 / 不带对比运行。
    - 这把尺子本身校准了没有（PSL-007）：`calibrated: false`
    - 证据：`file:plugins/sdlc/skills/pr/scripts/verify_pr.py#L295` · `gate_json:plugins/sdlc/skills/pr/eval/gate.json#gate_pass=static_only` · `gate_json:plugins/sdlc/skills/pr/eval/gate.json#provenance.scripts_run.verify_pr.py`
- **naming authored → `fits`** — 位置 / 产物：`github:pr（产物命名）`
    - 命名判定：design-notes.md#L52 把 pr 列在"直接改编"（pdforge 的 rules/git-workflow.md 等约定），但改编的是 判据不是整个 skill，上游没有一个叫 pr 的 skill 可保留 —— 按 PSL-014 判为新写、按产物（PR）命名。
    - 证据：`file:plugins/sdlc/docs/design-notes.md#L52-L53` · `file:plugins/sdlc/skills/pr/SKILL.md#L2`
- disposition `none`

#### `review-loop` — A-review-loop（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后 PR 发出去只剩两种跟进方式：模型层每轮轮询（每次烧 token）或人工盯。具体错误产物 —— 一条把 reviewer 评论当指令直接照做的修复 commit（未先验证主张，review-loop/SKILL.md#L139 的"全部判定完成先于任何修复"没有承载者）；具体漏检 —— 轮次与线程往返没有编译态上限， 与 bot reviewer 的对喷不会停在 exit 30 / exit 31，预算耗尽这件事永远不会被 /sdlc 的 fail --signal 读到（PSL-004 预算由脚本强制）。
    - 证据：`file:plugins/sdlc/skills/review-loop/SKILL.md#L3-L11` · `file:plugins/sdlc/skills/review-loop/SKILL.md#L31-L38` · `file:plugins/sdlc/skills/sdlc/assets/loops.yaml#L71-L87`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：重审更正（2026-09-06）：`done`（连同它调用的 pr_state / threads_json / checks_state） 在真 PR 上跑过两次 —— ledger 01:57:08 与 01:58:19 记 PR #2 在 head efd45ac 与 79b4736 上 `pr-poll.sh done` 均 exit 20（reviewDecision 空 / unresolved_count 0 / 无 CI 配置）。 仍不到 verified：(a) 那两次跑的是**修复前**的脚本，checks 三态（I-82）与 solo 谓词（I-69） 的提交 bedc159 落在 12:39+08:00，晚于 09:57；(b) watch / snapshot / resolve / selfreview 至今没有一次联网或真 PR 上的运行 —— .sdlc/pr-watch/pr-2.counters.json 只有 {"rounds":1,"empty_watches":0,"strikes":{}}，无 self_review 键； (c) fix_list 第 1 条 "run on one real PR with ≥3 comments" 仍未做：PR #2 收到零条评论， 整个 review 环一条线程都没处理过。
    - 这把尺子本身校准了没有（PSL-007）：`calibrated: false`
    - 证据：`file:plugins/sdlc/skills/review-loop/scripts/pr-poll.sh#L345` · `gate_json:plugins/sdlc/skills/review-loop/eval/gate.json#gate_pass=static_only` · `gate_json:plugins/sdlc/skills/review-loop/eval/gate.json#provenance.scripts_run.pr-poll.sh`
- **naming adopted → `fits`** — 位置 / 产物：`.sdlc/pr-watch/pr-N.json / R7 的 review 环`
    - 命名判定：上游 vana-builder 的名字是 pr-review-loop，收编时缩成 review-loop —— 严格说这是 PSL-014 "收编保留上游名"的一处偏离；但同词干（F-03 同词干或同义即 fits），且本仓库另有 /pr-review （reviewer 一侧），保留全名会与它混淆。记录偏离，不改名。
    - 证据：`file:plugins/sdlc/skills/review-loop/SKILL.md#L12` · `file:plugins/sdlc/docs/design-notes.md#L47-L49`
- **Loop `loops.yaml#review_loop`**：是 review_loop 的 loop_back 端点：graph.yaml#L363 agent.fix-verifier → review-loop 带 signal: iteration_complete / loop: review_loop（一次迭代收口），graph.yaml#L357 stage.review 自环同环。 它本身不是该环的 generator（agent.comment-fixer）也不是 verifier（human_reviewer，loops.yaml#L75-L76）。
- disposition `none`

#### `agent.pr-reviewer` — A-agent.pr-reviewer（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后 `/pr --pre-review` 只能由写这个 PR 的同一上下文自审 —— 自审读不出自己的盲点 （PSL-003 评估者与被评估者分离）。具体错误产物 —— 一个 `## Known issues` 段没有来源、 条目无 file:line 锚点的 PR body（verify_pr.py --pre-review 会拒，于是 --pre-review 这条路直接不可用）； 具体漏检 —— 本可在 push 前修掉的 P0 全部推到 reviewer 侧，review 轮次上移。
    - 证据：`file:plugins/sdlc/agents/pr-reviewer.md#L10-L11` · `file:plugins/sdlc/skills/pr/SKILL.md#L69-L72` · `file:plugins/sdlc/docs/design-notes.md#L80-L81`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：gate.json fix_list 第 3 条 "L2: run /pr --pre-review once with agents/pr-reviewer.md in a fresh context and check survivors land in Known issues" 未做 —— 隔离预审从未真跑过。
    - 重审更正：declared → compiled（重审 2026-09-06，编排者裁）。原判被 G3 的 mf-009 用 F-06 封在 declared， 理由是"verify_pr.py --pre-review 检的是下游 PR 正文的 Known issues 段，不是本 agent 的 findings 文件本身"。这一轮（I-87，commit bedc159）把校验加到了**文件本身**上：pr-poll.sh#L365-L368 文件缺失或为空 exit 1；#L374-L395 的内嵌校验器逐条拒 —— PyYAML 缺席 exit 1（fail closed）、 不是合法 YAML、没有 `review:` 块、review 块缺 target / mergeable、没有 findings 键、 findings 为空列表又没有 rationale，全部 exit 1。它是承重的：单人仓库的终止谓词 （done --solo）把"≥1 轮 selfreview 记录"当作 APPROVED 的替代必要条件 （pr-poll.sh#L222-L228、review-loop/SKILL.md#L56-L75），产不出合格的 findings 文件就登记不了那一轮。 封顶的前提（独占产物无闸）因此消失，两种读法现在都落在 compiled。
    - 这把尺子本身校准了没有（PSL-007）：`calibrated: false`
    - 证据：`gate_json:plugins/sdlc/skills/pr/eval/gate.json#provenance.scripts_run.verify_pr.py --pre-review` · `file:plugins/sdlc/skills/pr/scripts/verify_pr.py#L295` · `file:plugins/sdlc/agents/pr-reviewer.md#L22-L25`
- **naming adopted → `fits`** — 位置 / 产物：`findings.yaml / /pr-review 的隔离只读执行体`
    - 命名判定：收编自 qanat 的 code-reviewer（design-notes.md#L56-L57「code-reviewer → pr-reviewer，去 persona， 保留判据」）—— 上游名未保留，是 PSL-014「收编保留上游名」的一处偏离；但本仓库 R6 已有一个 叫 code-reviewer 的 skill（ARCHITECTURE.md#L40），保留上游名必然撞名。与它服务的 /pr-review 同词干 → F-03 判 fits。记录偏离，不改名。
    - 证据：`file:plugins/sdlc/docs/design-notes.md#L56-L57` · `file:plugins/sdlc/agents/pr-reviewer.md#L2-L3`
- **Loop `review_loop`**：重审改写（原为 null）：它现在是 review_loop 的 loop_back 端点（graph.yaml#L361 带 loop: review_loop）。 与 review-loop 那个 Part 的处境相同 —— 是回边端点，但既不是该环的 generator（agent.comment-fixer） 也不是 verifier（human_reviewer，loops.yaml#L75-L76）。
- **争议裁决**：agent.pr-reviewer 的 implemented 该判 compiled 还是 declared？ — 采纳 compiled（下游投影被 verify_pr.py --pre-review 拒）；异见 declared（agents/*.md 无 gate.json，findings.yaml 本身无检）；resolved_by `G3 裁 declared（mf-009，F-06 封顶）；重审 2026-09-06 改判 compiled —— 分歧面消失，异议方要的"产物本身有检"由 pr-poll.sh selfreview 满足（I-87）`
- disposition `issue`

#### `human_gate.merge` — A-human_gate.merge（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后 review 一绿就由脚本 / agent 直接合入。具体错误产物 —— 一个没有任何人裁决过的 merge commit 落进 main；G3 的例外复核（human AC 清单 + 假设台账，graph.yaml#L200）结论无处生效， 因为 g3 → merge 这条 handoff（graph.yaml#L366）交给的就是这个人节点；具体漏检 —— "合入是不可逆的对外动作"这一条从此没有承载者，--autopilot 会连合并一起免掉（PSL-006）。
    - 证据：`file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L249-L255` · `file:plugins/sdlc/skills/pr/SKILL.md#L10` · `file:plugins/sdlc/docs/ARCHITECTURE.md#L41`
- **implemented `declared`** — declared（只有 SKILL.md / 提示）
    - 未达 `compiled`：无 verify 脚本、无 gate.json —— github:merge 的 checked_by 是空列表（F-06：生产者停在 declared）。 sdlc_state.py 的前置条件只检 review.done 与（G3 required 时）gates.g3=pass，检不到"合的是谁、合的是哪个 sha"。
    - 未达 `verified`：重审更正（2026-09-06）："本次 dogfood 未走到 merge 阶段"已明确为假：merge 真发生过 —— ledger 2026-09-06T03:46:36 记 "PR #2 merged into main as a merge commit 1e671f3 … Marked ready-for-review then merged by the USER's explicit decision — the delegated judges neither marked it ready nor merged"，state.json 里 merge.sha=1e671f3ceb42…、merged_at=03:46:18Z。这不改判定：F-06 的封顶只看独占产物 github:merge 的 checked_by，它仍是空列表，所以无论有没有运行记录都封在 declared。这一条反而是本次唯一由真人做的门动作 —— 三道门全是代签，唯独合入是用户本人按的。
    - 证据：`file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L249-L255` · `file:plugins/sdlc/docs/ARCHITECTURE.md#L99-L100`
- **naming authored → `fits`** — 位置 / 产物：`github:merge / graph.yaml#L249 的 human.merge 节点`
    - 命名判定：审计里的 Part id 写作 human_gate.merge（AC-011 的 required_parts 名单逐字如此），图上的节点 id 是 human.merge —— 前缀不同、同义同位置，F-03 判 fits。不改名。
    - 证据：`file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L249`
- disposition `none`

#### `release` — A-release（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后引擎在 merge 之后就说"完成"。具体错误产物 —— 一次没有 tag、没有 CHANGELOG 条目、 发布说明缺回滚方案的"交付"，以及一个部署了但没跑 --verify-cmd 就置 release.done=true 的状态； 具体漏检 —— 发布说明里的 `/issue --escape` 登记入口没了，线上反馈这条世界层唯一的外部校准源断掉， R8 的逃逸缺陷统计（retro/SKILL.md#L39 逃逸缺陷率）恒为空，"合入不是终点"这条规律无人承载（PSL-009）。
    - 证据：`file:plugins/sdlc/skills/release/SKILL.md#L21-L25` · `file:plugins/sdlc/skills/release/scripts/verify_release.py#L157` · `file:plugins/sdlc/docs/ARCHITECTURE.md#L101`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：无真实发布的运行记录 —— gate.json fix_list 第 1 条 "one real release with a --verify-cmd; check release.done stays false on red verification" 未做；脚本只在临时仓库上冒烟。 重审补记（2026-09-06）：release 阶段这次**走到了**，并被显式记为 skipped 而不是 done —— ledger 03:48:11「release SKIPPED with reason recorded: this repository has no tag / CHANGELOG / releases convention … verify_release.py not run because every artefact it checks is absent by design here. release.done stays false — skipped is not done」。这反而加固了原判： 脚本至今只在临时仓库对 fixture 冒烟，一次真实发布也没有。
    - 这把尺子本身校准了没有（PSL-007）：`calibrated: false`
    - 证据：`file:plugins/sdlc/skills/release/scripts/verify_release.py#L157` · `gate_json:plugins/sdlc/skills/release/eval/gate.json#gate_pass=static_only` · `gate_json:plugins/sdlc/skills/release/eval/gate.json#provenance.scripts_run.verify_release.py`
- **naming authored → `fits`** — 位置 / 产物：`releases/vX.Y.Z.md + git:tag（产物命名）`
    - 命名判定：design-notes.md#L67-L69 记它是 2026-09-05 第二次整理时新写的四个 skill 之一（L8 交付原本没有承载 skill）， 按产物 / 位置命名 —— 新写路径，PSL-014 不要求保留任何上游名。
    - 证据：`file:plugins/sdlc/docs/design-notes.md#L67-L69` · `file:plugins/sdlc/skills/release/SKILL.md#L2`
- disposition `none`

[^A-pr]: `pr` 的 PSL-ID 追溯 — needed PSL-002, PSL-016, PSL-009 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`graph.yaml#L206 (id: pr, role: delivery, writes: [github:pr]); ARCHITECTURE.md#L41 §1 R7 行`。
[^A-review-loop]: `review-loop` 的 PSL-ID 追溯 — needed PSL-002, PSL-016, PSL-004, PSL-012 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`graph.yaml#L212 (id: review-loop, role: delivery, loop: review_loop); ARCHITECTURE.md#L41 §1 R7 行`。
[^A-agent.pr-reviewer]: `agent.pr-reviewer` 的 PSL-ID 追溯 — needed PSL-002, PSL-016, PSL-003 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`graph.yaml#L239-L248（id: agent.pr-reviewer, kind: agent, role: evaluator, writes: [pre-review/round-N.findings.yaml], must_not_read: [implementer_session, ratchet-log/**]）， 两条边 graph.yaml#L360（pr → agent.pr-reviewer, conditional, guard: flag.pre_review）与 graph.yaml#L361（agent.pr-reviewer → pr, loop_back, signal: pre_review_round_done, loop: review_loop）。 重审更正（2026-09-06）：装配时这一栏写的是 no_node —— 当时图里确实没有这个节点，那正是本 Part 提的 P-R7-01。该提案已落地（I-16），所以 R7 的归属不再靠 ARCHITECTURE.md#L41 §1 推，图上自证。 同一份 agent 也服务 R6 的 /pr-review（ARCHITECTURE.md#L40 §1 R6 行列 pr-review 与 findings.yaml）， §1 与图不冲突，故仍不写 role_conflict。`。
[^A-human_gate.merge]: `human_gate.merge` 的 PSL-ID 追溯 — needed PSL-002, PSL-016, PSL-006, PSL-009 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`graph.yaml#L249 (id: human.merge, kind: human, role: gate, writes: [github:merge], authority: {merge: true}); ARCHITECTURE.md#L41 §1 R7 门/闸 列「merge / push tag 是人类动作」`。
[^A-release]: `release` 的 PSL-ID 追溯 — needed PSL-002, PSL-016, PSL-009 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`graph.yaml#L256 (id: release, role: delivery, writes: [CHANGELOG.md, releases/vX.Y.Z.md, git:tag]); ARCHITECTURE.md#L41 §1 R7 行`。

## R8 回流

**问题**：流程病在哪层；环的参数该不该调？

3 个配件 · 3 处登记为缺少。

| 配件 / 缺少 | kind | 缺口 · 原子 | 独占产物 / 角色 | 闸 · 门 | artifact 闸（checked_by） | Loop | needed | implemented | naming |
|---|---|---|---|---|---|---|---|---|---|
| `retro` [^A-retro] | `skill` | `Knowledge+Judgment` process-illness-baseline | `retro/retro-<date>.md` | 闸 `metrics.py` | `retro/retro-<date>.md` → **（无闸 → 封顶 declared）**<br>`metrics.json` → **（无闸 → 封顶 declared）**<br>`change-proposal-*.md` → **（无闸 → 封顶 declared）** | `loops.yaml#lifecycle` | **necessary** | **declared**<br>未达：`compiled` / `verified` | authored → **fits** |
| `tune` [^A-tune] | `skill` | `Knowledge+Judgment+Control` harness-param-from-evidence | `tune/harness-proposals-<date>.yaml` | 闸 `tune.py` | `tune/harness-proposals-<date>.yaml` → **（无闸 → 封顶 declared）**<br>`tune/*.patch` → **（无闸 → 封顶 declared）** | `loops.yaml#hill_climb` | **necessary** | **declared**<br>未达：`compiled` / `verified`<br>`calibrated: false` | authored → **misfit**<br>建议名 `harness-tune`<br>**不重命名** |
| `human_gate.harness-review` [^A-human_gate.harness-review] | `human_gate` | `Judgment+Control` harness-change-through-human | `github:pr (harness 提案)`<br>role `gate` | **无闸无门** | `github:pr (harness 提案)` → **（无闸 → 封顶 declared）** | `loops.yaml#hill_climb` | **necessary** | **declared**<br>未达：`compiled` / `verified` | authored → **fits** |
| **（缺少）** `retro-output-no-rejecting-gate` | — | `Control`<br>**newly_identified（本次审计新识别）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：retro 的产物（retro/retro-<date>.md、metrics.json）既没有会拒绝的脚本、也不被任何门挡： metrics.py 只导出，全文无非零退出路径。ARCHITECTURE.md#L42 §1 R8 的「门 / 闸」列却把它列成闸。 具体错误产物：一份提案没有 target / verify_by、数字手抄自记忆的复盘报告照样通过 archive， "每个环节的产物要么被脚本检要么被门挡"（PSL-015）在 R8 断掉。<br>证据：`file:plugins/sdlc/skills/retro/scripts/metrics.py#L197-L198` · `file:plugins/sdlc/docs/ARCHITECTURE.md#L42` · `gate_json:plugins/sdlc/skills/retro/eval/gate.json#gate_pass=static_only`<br>disposition `issue` | — | — |
| **（缺少）** `harness-change-effect-unmeasured` | — | `Knowledge+Judgment`<br>**newly_identified（本次审计新识别）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：hill_climb 的成功谓词是 harness_proposal_merged_or_rejected（loops.yaml#L109）—— 只问提案有没有被处置，不问指标有没有动。没有"上一期的 harness 改动之后 expected_delta 是否兑现"的回读者。具体漏检：一条把 MAX_ROUNDS 收紧的提案合入后 review 反而更常撞顶， 下一期只会看到"撞顶率高 → 再放宽"，爬山环在原地来回而 plateau 检测（同一 target 连续两期 方向相反）要到第三期才可能触发。<br>证据：`file:plugins/sdlc/skills/sdlc/assets/loops.yaml#L109-L114` · `file:plugins/sdlc/skills/tune/SKILL.md#L59-L61`<br>disposition `issue` | — | — |
| **（缺少）** `uncalibrated-tune-thresholds` | — | `Judgment`<br>**unenforced_rule（宪法有规则、机器无闸）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：dos.yaml R010「未过 calibrate 的标准不是证据」的 enforced_by 是 not_enforced。 tune 的 40% / 50% / 0.95 三个阈值是文献先验，gate.json fix_list 第 2 条自己写明"未在本仓库校准"， 但没有任何机制阻止用它们产出的提案被当作证据。具体错误产物：一条以未校准阈值为唯一依据的 routing 预算改动 PR，人在 review 时看不到"这把尺子没校准"（PSL-007）。<br>证据：`file:plugins/sdlc/dogfood/ring-audit/dos.yaml#L412-L415` · `gate_json:plugins/sdlc/skills/tune/eval/gate.json#fix_list[1]` · `file:plugins/sdlc/skills/tune/SKILL.md#L47-L49`<br>disposition `issue` | — | — |

### R8 判定详情

#### `retro` — A-retro（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后引擎产出的是一段"这次沟通不够充分，下次加强测试"。具体错误产物 —— 一份没有基线数字、 没有归层、每条提案没有 target/change/verify_by 的复盘文档，谁都无法验收它；具体漏检 —— 回流分布、G1 拦截率、human AC 占比、逃逸缺陷率、豁免数（--force 绕门的次数）从不被读出来， 于是"病在哪一层"永远回答不了，回到 R0/R1/R2 的变更提案永远长不出来（PSL-008 失败归层）。
    - 证据：`file:plugins/sdlc/skills/retro/SKILL.md#L21-L24` · `file:plugins/sdlc/skills/retro/SKILL.md#L33-L40` · `file:plugins/sdlc/docs/ARCHITECTURE.md#L42`
- **implemented `declared`** — declared（只有 SKILL.md / 提示）
    - 未达 `compiled`：metrics.py 是导出器不是验证器 —— 重审在 HEAD 上逐行复核后仍成立，而且更极端：全文一处 sys.exit 都没有（grep sys.exit / SystemExit 无输出），连 docstring 自称的 "Exit 0 always (reporting tool), 2 on IO error" 里的 2 都没有对应代码。本轮 I-84 的修复（gate_history_from_trace / gate_history_from_ledger，拦截数改从账本 / trace 的 reject 事件数取）是让**数字变对**，不是加拒绝路径。 retro 的产物（retro/retro-<date>.md、metrics.json）既无 verify 脚本可拒、也不被任何 G1/G2/G3 的门挡住。ARCHITECTURE.md#L42 §1 R8 的「门 / 闸」列却把 metrics.py 列在那里 —— 设计视图与实况 不一致，这是本卡审出的 skill 源码问题，登记为 R8 的 Gap 与 P-R8-02/P-R8-03，未改被审文件。
    - 未达 `verified`：重审更正（2026-09-06）："无真实归档的行为层运行记录"已不成立：metrics.py 在真归档上跑过一次，ledger 03:50:11 记 retro + tune 完成，产物 committed 在 retro/{metrics.json, metrics-baseline.md, retro-2026-09-06.md}（lead 14.1h / review rounds 1 / reflows card 4·task 2·world 1 / waivers 3）。仍不到 verified：(a) 只有 1 个归档，gate.json fix_list 第 1 条要 ≥2；(b) 那次跑的是**修复前**的 metrics.py —— 它正是在那次跑出了两个错数（g1_interception_rate=0.0 而账本里有 2 次 G1 reject，I-84；human_ac_ratio=null 因为 archive 不复制 done_when.yaml，I-85），修复提交 9c1e739 在 12:21+08:00 晚于那次运行，当前代码的正确性只有 fixture 证据；(c) 独占产物 retro/retro-<date>.md 的 checked_by 仍空，F-06 把 implemented 封在 declared，verified 在封顶下本就不可达。
    - 证据：`file:plugins/sdlc/skills/retro/scripts/metrics.py#L197-L198` · `gate_json:plugins/sdlc/skills/retro/eval/gate.json#gate_pass=static_only` · `file:plugins/sdlc/skills/retro/SKILL.md#L63-L68`
- **naming authored → `fits`** — 位置 / 产物：`retro/retro-<date>.md（产物命名）`
    - 证据：`file:plugins/sdlc/docs/design-notes.md#L67-L69` · `file:plugins/sdlc/skills/retro/SKILL.md#L2`
- **Loop `loops.yaml#lifecycle`**：是 lifecycle 环的 loop_back 起点：graph.yaml#L371 retro → stage.contract 带 signal: escape_defect / loop: lifecycle / carries: [change-proposal-*.md]。它不是该环的 generator（sdlc）也不是 verifier （human.g3，loops.yaml#L93-L94）。
- disposition `issue`

#### `tune` — A-tune（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后引擎在某次 review 跑到 exit 30 之后会说"MAX_ROUNDS 太小，改成 20"并直接 sed 改脚本。 具体错误产物 —— 一个没有跨 PR 数据支撑、没有 expected_delta / verify_by、也没经过人审的 harness 参数改动直接落进 pr-poll.sh / routing.yaml；具体漏检 —— "预算耗尽且伴随收敛升级" （层错了，不是预算不够，SKILL.md#L46）这一类会被读成预算问题，环的参数朝错误方向爬山， 且 harness 改动绕过人（PSL-013）。
    - 证据：`file:plugins/sdlc/skills/tune/SKILL.md#L23-L27` · `file:plugins/sdlc/skills/tune/SKILL.md#L36-L38` · `file:plugins/sdlc/skills/sdlc/assets/loops.yaml#L106-L121`
- **implemented `declared`** — declared（只有 SKILL.md / 提示）
    - 未达 `compiled`：F-06 封顶（G3 裁定，mf-009）：harness-proposals.yaml 与 *.patch 的 checked_by 均为空；tune.py 自身除 IO 错误外恒 exit 0（SKILL.md 自陈是报告工具），apply_proposal.py 只出 diff 不写目标文件。无非零退出路径即无闸，故封顶 declared。
    - 未达 `verified`：重审更正（2026-09-06）：tune.py 在真数据上跑过一次，但**样本不足以出提案** —— ledger 03:50:11「tune: insufficient_samples (1 archive < min 2) → baseline only, no proposals」， 产物 committed 在 retro/harness-proposals.yaml（inputs.archive_root=specs、pr_watch: null、 ratchet_logs: null、stats.features=1）。真 .sdlc/pr-watch 与 ≥2 归档两项都没喂进去， gate.json fix_list 第 1 条实质未做。tune.py / apply_proposal.py 本轮一个字节未改。
    - 备注：判 compiled 的承重点是 apply_proposal.py 的结构性控制：它只出 unified diff / patch，从不写目标文件 （SKILL.md#L70-L71），未知 apply.kind 直接 exit 1；tune.py#L302 对封闭 target 集外的 target exit 2。 但 tune.py 自身 exit 0 恒成立（SKILL.md#L69 自述"报告工具"），所以"每条提案 9 项齐"这条判据 没有编译态出口 —— 登记为 R8 的 Gap，不抬高本维判定。
    - 这把尺子本身校准了没有（PSL-007）：`calibrated: false`
    - 证据：`file:plugins/sdlc/skills/tune/scripts/apply_proposal.py#L100-L114` · `file:plugins/sdlc/skills/tune/scripts/tune.py#L302` · `gate_json:plugins/sdlc/skills/tune/eval/gate.json#gate_pass=static_only`
- **naming authored → `misfit`** — 位置 / 产物：`tune/harness-proposals-<date>.yaml / hill_climb 环的 generator`
    - 建议名 `harness-tune`，**不重命名**（PSL-014：建议不等于重命名，`rename: false`）
    - 命名判定：misfit 的理由：新写按产物或位置命名（PSL-014），产物是 harness-proposals、位置是 hill_climb 环， "tune"两者都不指 —— 在一个同时有 routing 预算、eval 阈值、prompt、测试的仓库里，"调什么"是 这个名字唯一没说的东西，而它的 target 恰恰是一个封闭集（只有 harness 参数，SKILL.md#L50 明写"绝不提改契约、改代码、改 skill 正文的提案"）。不重命名：改名要同时动 graph.yaml、 loops.yaml#hill_climb、triggers.yaml、ARCHITECTURE §1 与 retro 的接线段 —— 建议不等于重命名 （PSL-014），另开 G2 变更提案（P-R8-01）。
    - 证据：`file:plugins/sdlc/skills/tune/SKILL.md#L2` · `file:plugins/sdlc/skills/tune/SKILL.md#L36-L38` · `file:plugins/sdlc/skills/tune/SKILL.md#L89`
- **Loop `loops.yaml#hill_climb`**：是 hill_climb 环的 generator（loops.yaml#L110 generator: tune），也是 graph.yaml#L373 tune → human.harness-review 这条 interrupt 边的起点。
- disposition `issue`

#### `human_gate.harness-review` — A-human_gate.harness-review（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后 tune 的提案没有终点，唯一剩下的落地方式是让 apply_proposal.py 直接写目标文件。 具体错误产物 —— routing.yaml 的分层预算、pr-poll.sh 的 MAX_ROUNDS / MAX_THREAD_STRIKES、 各 skill gate.json 的 fix_list 被机器按自己算出来的阈值改写；具体漏检 —— hill_climb 环失去 verifier（loops.yaml#L111），generator 与 verifier 变成同一个（违反 dos.yaml R014）， "改 harness 的人手不能是提议 harness 的机器"这条边界（PSL-013）无人守。
    - 证据：`file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L279-L285` · `file:plugins/sdlc/skills/tune/SKILL.md#L80-L81` · `file:plugins/sdlc/docs/ARCHITECTURE.md#L42`
- **implemented `declared`** — declared（只有 SKILL.md / 提示）
    - 未达 `compiled`：无 verify 脚本、无 gate.json，本门的裁决没有任何落盘形状（对比 G1/G2/G3 各有 g1-record.md / .done_when.lock / g3-record.md）。apply_proposal.py 检的是 tune 提案的形状，不是本门的裁决； "提案永不自动生效"靠的是 apply_proposal.py 不写目标文件这一结构性事实，不是靠检本门签没签。
    - 未达 `verified`：无行为层运行记录 —— 本次 dogfood 未走到 harness-review。
    - 重审更正：重审补记（2026-09-06）：「本门的裁决没有任何落盘形状」仍成立，但现在有一条更硬的依据可并列—— ARCHITECTURE.md#L113-L116（本轮新增）明写 human.merge 与 human.harness-review「是人做的动作， 不是门」，没有 Gate 对象、sdlc_state.py 里也没有对应 verdict；check_audit.py#L94 的 HUMAN_GATES = {"G1","G2","G3"} 是同一条读法。即"无落盘形状"从实况升格成了写下来的设计意图，判定不变。 另：P-R8-06 的两条都还开着——该节点 writes 仍是 [github:pr]，与 pr 节点同名；仍没有 loop: 字段， 尽管 loops.yaml 把它列为 hill_climb 的 verifier、graph.yaml#L374 的边已带 loop: hill_climb。
    - 证据：`file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L279-L285` · `file:plugins/sdlc/skills/tune/scripts/apply_proposal.py#L31-L38`
- **naming authored → `fits`** — 位置 / 产物：`github:pr（harness 提案）/ graph.yaml#L279 的 human.harness-review 节点`
    - 命名判定：审计里的 Part id 写作 human_gate.harness-review（AC-011 required_parts 逐字如此），图上是 human.harness-review —— 前缀不同、同义同位置，F-03 判 fits。不改名。
    - 证据：`file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L279` · `file:plugins/sdlc/skills/sdlc/assets/loops.yaml#L111`
- **Loop `loops.yaml#hill_climb`**：是 hill_climb 环的 verifier（loops.yaml#L111 verifier: human.harness-review）且是 loop_back 端点 （graph.yaml#L374 human.harness-review → sdlc，signal: harness_change_merged, loop: hill_climb）。 注意 graph.yaml#L279-L285 这个节点本身**没有** loop: 字段，环归属只能从 loops.yaml 与边上读出来 —— 记为本卡审出的 skill 源码问题（P-R8-06），未改被审文件。
- disposition `issue`

[^A-retro]: `retro` 的 PSL-ID 追溯 — needed PSL-002, PSL-016, PSL-008 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`graph.yaml#L264 (id: retro, role: learning, loop: lifecycle); ARCHITECTURE.md#L42 §1 R8 行`。
[^A-tune]: `tune` 的 PSL-ID 追溯 — needed PSL-002, PSL-016, PSL-013, PSL-012 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`graph.yaml#L271 (id: tune, role: learning, loop: hill_climb); ARCHITECTURE.md#L42 §1 R8 行`。
[^A-human_gate.harness-review]: `human_gate.harness-review` 的 PSL-ID 追溯 — needed PSL-002, PSL-016, PSL-013, PSL-006 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`graph.yaml#L279 (id: human.harness-review, kind: human, role: gate, writes: [github:pr], authority: {merge: true}); ARCHITECTURE.md#L42 §1 R8 门/闸 列「提案不自动生效」`。

## spine 脊柱

**问题**：谁持有状态、记账、按层路由失败、把三道门编译成不可跳过、把图与环声明成数据（ARCHITECTURE §1 脊柱段；§1 表无脊柱行，没有"问题"列可取，此处取脊柱段的五件事）

5 个配件 · 4 处登记为缺少。

| 配件 / 缺少 | kind | 缺口 · 原子 | 独占产物 / 角色 | 闸 · 门 | artifact 闸（checked_by） | Loop | needed | implemented | naming |
|---|---|---|---|---|---|---|---|---|---|
| `sdlc` [^A-sdlc] | `skill` | `Control+Judgment+Knowledge` cross-session-lifecycle-state | `.sdlc/<slug>/state.json`<br>role `orchestrator` | 闸 `sdlc_state.py` | `.sdlc/<slug>/state.json` → `sdlc_state.py`<br>`.sdlc/<slug>/ledger.md` → `sdlc_state.py`<br>`.sdlc/<slug>/trace.jsonl` → `trace.py` | `loops.yaml#lifecycle` | **necessary** | **compiled**<br>未达：`verified` | authored → **fits** |
| `asset.graph.yaml` [^A-asset.graph.yaml] | `asset` | `Knowledge` graph-as-data | `skills/sdlc/assets/graph.yaml` | 闸 `verify_graph.py` | `skills/sdlc/assets/graph.yaml` → `verify_graph.py` | `null` | **necessary** | **compiled**<br>未达：`verified` | authored → **fits** |
| `asset.loops.yaml` [^A-asset.loops.yaml] | `asset` | `Knowledge+Control` loop-contract | `skills/sdlc/assets/loops.yaml` | 闸 `verify_loop.py` | `skills/sdlc/assets/loops.yaml` → `verify_loop.py` | `null` | **necessary** | **compiled**<br>未达：`verified` | authored → **fits** |
| `asset.routing.yaml` [^A-asset.routing.yaml] | `asset` | `Knowledge+Judgment` failure-routing-table | `skills/sdlc/assets/routing.yaml` | **无闸无门** | `skills/sdlc/assets/routing.yaml` → **（无闸 → 封顶 declared）** | `null` | **necessary** | **declared**<br>未达：`compiled` / `verified` | authored → **fits** |
| `asset.triggers.yaml` [^A-asset.triggers.yaml] | `asset` | `Knowledge` loop-trigger-binding | `skills/sdlc/assets/triggers.yaml` | **无闸无门** | `skills/sdlc/assets/triggers.yaml` → **（无闸 → 封顶 declared）** | `null` | **necessary** | **declared**<br>未达：`compiled` / `verified` | authored → **fits** |
| **（缺少）** `r001-single-producer` | — | `Control`<br>**unenforced_rule（宪法有规则、机器无闸）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：两个节点写同一产物不被任何脚本拒绝——verify_graph.py 只检 writes 有界，不检 writes 的交集；provenance 与回滚归属含混，而且这条宪法的违例只能靠人读图发现。本次审计正是靠审计自己的 check_audit.py 的 double_producer 谓词才把 done_when.yaml 的双生产者抓出来，插件自身没有这条闸。<br>证据：`file:plugins/sdlc/dogfood/ring-audit/dos.yaml#L376-L379（R001 enforced_by user_workflow）` · `file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L26`<br>disposition `issue` | — | — |
| **（缺少）** `r008-human-signer` | — | `Control`<br>**unenforced_rule（宪法有规则、机器无闸）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：签字人现在被记录也被约束：三处签字入口（sdlc_state.py gate / waive、lock_done_when.py sign）都要求 --signer-kind，代签必须自报 delegated_agent 并附 --authorization，否则非零退出；signer_kind 进 state / lock / ledger / trace，代签与人签不再同形。重审更正（2026-09-06）：装配时写的"在机器一侧完全没有承载"已不成立，而重审片段说的"--signer-kind 默认值就是 human，不传就被原样记成人签"在 HEAD 上也已不成立——b77feb0 把它改成 required=True（sdlc_state.py#L980/#L988、lock_done_when.py#L155），不传直接 argparse 报错。但 R008 说的是"三道门只能人签"，这一条仍未编译：没有任何脚本拒绝一次代签，一个 agent 只要传 --signer-kind human 就仍被记成人签，而没有一处核对那句 authorization 是否真的来自人。本次 dogfood 的三道门全是 delegated_agent 代签。这条宪法从"完全没有承载"变成"承载了记录与授权、没承载拒绝"，仍是 unenforced_rule。<br>证据：`file:plugins/sdlc/dogfood/ring-audit/dos.yaml#L404-L407（R008 enforced_by user_workflow）` · `file:plugins/sdlc/docs/ARCHITECTURE.md#32-三道门只能人签`<br>disposition `issue` | — | — |
| **（缺少）** `routing-yaml-no-verifier` | — | `Control`<br>**newly_identified（本次审计新识别）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：routing.yaml 的 rules 行写错 layer、漏 handler、或 budgets 的键与 layers 不对齐，都不在写入时报错，只在 fail 那一刻以"路由到错的层"的形式静默生效——错误的回流层会把世界层的错误安静地在 card 层重试到预算耗尽，症状与"实现者不行"完全一样。<br>证据：`file:plugins/sdlc/skills/sdlc/assets/routing.yaml` · `file:plugins/sdlc/docs/ARCHITECTURE.md#7-覆盖矩阵与空白（X2 行闸列为空）`<br>disposition `issue` | — | — |
| **（缺少）** `triggers-yaml-no-verifier` | — | `Control`<br>**newly_identified（本次审计新识别）** | — | — | — | — | necessity **necessary**<br>撤掉 / 不补它：triggers.yaml 的绑定引用了不存在的 predicate_scripts、或漏掉"or stop after N turns"，都只在无人值守跑的那一次显形，表现为环不停或环不启动；同一行还登记 Stop hook 只有模板未安装，即声明的绑定连安装状态都没被检。<br>证据：`file:plugins/sdlc/skills/sdlc/assets/triggers.yaml` · `file:plugins/sdlc/docs/ARCHITECTURE.md#7-覆盖矩阵与空白（环契约 / 图声明 / 触发绑定 行：闸列只有 verify_loop / verify_graph / check-clean）`<br>disposition `issue` | — | — |

### spine 判定详情

#### `sdlc` — A-sdlc（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后状态活在引擎记忆里，换一次会话就丢；失败一律在实现层重试到上下文耗尽（世界层的错误被在 card 层重试二十次，这正是 routing.yaml 头注说的"默认行为是灾难性的"）；三道门退化成文档里的建议，advance 没有前置条件可检，产出的是一条无人能复现、无人能审计的流水线。
    - 证据：`file:plugins/sdlc/skills/sdlc/SKILL.md#缺口control--judgment--knowledge` · `file:plugins/sdlc/docs/ARCHITECTURE.md#1-九环与一根脊柱`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：本 Run 亲历的是 sdlc 的原语路径（sdlc_state.py 的状态迁移、lock_done_when.py 的两段锁，证据即这份 .done_when.lock），不是带 / 不带 skill 的对比运行；gate.json fix_list 第一条"L2：run /sdlc end-to-end on one real TASK-track requirement in a fresh session"仍未做。原语跑过 ≠ 编排判断被验证。
    - 校准备注：即使抬到 verified 也须附 calibrated: false——routing v2 的收敛阈值（fingerprint_history 6 / oscillation periods 2-3 / plateau_rounds 3）按 gate.json fix_list 是文献先验，未经真实运行校准（PSL-007）。
    - 证据：`file:plugins/sdlc/skills/sdlc/scripts/sdlc_state.py` · `gate_json:plugins/sdlc/skills/sdlc/eval/gate.json#gate_pass` · `smoke:plugins/sdlc/eval/smoke.sh（在 b77feb0 实跑：391 passed, 0 failed。装配时引的是 gate.json provenance.smoke 的 178 / 2026-09-05，那个数已过期且 gate.json 未随之更新——引用时以 smoke.sh 的实跑为准，别引 gate.json 那个数，见缺口 R5/newly_identified/control/gate-json-stale-after-script-lands）` · `run_record:plugins/sdlc/dogfood/ring-audit/.done_when.lock`
- **naming authored → `fits`** — 位置 / 产物：`脊柱（ARCHITECTURE §1 的 /sdlc，持状态 · 记账 · 路由 · 编译门 · 声明图与环）`
    - 贴合理由：位置名（这根脊柱本身就是生命周期），F-03 的位置名分支判 fits；它的产物是 state.json / ledger.md 而非叫 sdlc 的东西，但位置名分支不要求与产物同名。
    - 证据：`file:plugins/sdlc/docs/ARCHITECTURE.md#1-九环与一根脊柱`
- disposition `none`

#### `asset.graph.yaml` — A-asset.graph.yaml（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后节点边界与边类型退回 ARCHITECTURE 的 ASCII 与 sdlc_state.py 的线性链两处，两处漂移无人发现；verify_graph.py 五条 lint 没有对象——首版 graph.yaml 被自己的 lint 抓到的那两个未标环归属的圈（"通过条件不可测的无界循环"）就会原样留在流水线里。
    - 证据：`file:plugins/sdlc/skills/sdlc/assets/graph.yaml#L1-L11` · `file:plugins/sdlc/docs/design-notes.md#2026-09-05-第三次整理loop-engineering--graph-engineering-的透镜v060`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：只有作者在 2026-09-05 的 smoke 记录（shipped graph 过五条 lint、6 个坏 fixture 各被拒），本 Run 没有跑过 verify_graph.py，更没有带 / 不带对比。
    - 重审更正：重审补记（2026-09-06）：被审对象本身变了——graph.yaml 加了 agent.pr-reviewer 节点与两条边（I-16， 填的正是本审计提的 P-R7-01）。重审在 HEAD 上跑过 verify_graph.py（无参，检 shipped graph）， rejects 0 / warnings 0 / exit 0，五条 lint 在新图上仍全过。这仍是 compiled 级证据： 没有带 / 不带对比臂，gate.json 仍 static_only。
    - 证据：`file:plugins/sdlc/skills/sdlc/scripts/verify_graph.py` · `gate_json:plugins/sdlc/skills/sdlc/eval/gate.json#provenance.scripts_run.verify_graph.py`
- **naming authored → `fits`** — 位置 / 产物：`skills/sdlc/assets/graph.yaml`
    - 贴合理由：数据资产的 Part 名就是它的产物文件名，字面相等，F-03 判 fits。
    - 证据：`file:plugins/sdlc/skills/sdlc/assets/graph.yaml`
- disposition `none`

#### `asset.loops.yaml` — A-asset.loops.yaml（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后六个环各说各话（retries / rounds / strikes / iterations / MAX_ROUNDS），没有一处能回答"现在哪个环在烧预算、烧到几成"；generator ≠ verifier 无处声明，自验证反模式（一个节点既生成又判定）不被任何 lint 拦，环会在自己判自己合格的情况下停下来。
    - 证据：`file:plugins/sdlc/skills/sdlc/assets/loops.yaml#L1-L16` · `file:plugins/sdlc/docs/ARCHITECTURE.md#37-图与环是数据v060`
- **implemented `compiled`** — compiled（有 verify 脚本或被门挡）
    - 未达 `verified`：同上，只有 2026-09-05 的作者 smoke（6 个环通过；generator==verifier / 缺 stop 键 / budget.ref 不可解析各被拒），本 Run 未跑，无对比臂。
    - 重审更正：重审补记（2026-09-06）：loops.yaml 本轮未改。重审在 HEAD 上跑过 verify_loop.py（无参， 检 shipped loops 与同目录 routing.yaml），rejects 0 / warnings 0 / exit 0，六个环全过。 仍是 compiled 级证据：没有带 / 不带对比臂。
    - 证据：`file:plugins/sdlc/skills/sdlc/scripts/verify_loop.py` · `gate_json:plugins/sdlc/skills/sdlc/eval/gate.json#provenance.scripts_run.verify_loop.py`
- **naming authored → `fits`** — 位置 / 产物：`skills/sdlc/assets/loops.yaml`
    - 贴合理由：Part 名即产物文件名，字面相等，F-03 判 fits。
    - 证据：`file:plugins/sdlc/skills/sdlc/assets/loops.yaml`
- disposition `none`

#### `asset.routing.yaml` — A-asset.routing.yaml（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后 sdlc_state.py fail 无表可查，失败一律归 card 层原地重试——世界层的错误在实现层被重试到预算耗尽，产出的是"重试二十次仍然错"的 diff；收敛检测（oscillation / plateau / impossible）没有参数可读，三种"再试也没用"都检不出来。
    - 证据：`file:plugins/sdlc/skills/sdlc/assets/routing.yaml#L1-L13` · `file:plugins/sdlc/docs/ARCHITECTURE.md#33-回流路由x2失败归层不原地重试`
- **implemented `declared`** — declared（只有 SKILL.md / 提示）
    - 未达 `compiled`：no_gate——HEAD 上仍没有 verify_routing.py，36 个 skills/*/scripts/*.py 里没有一个校验 routing.yaml 自身：rules 行的 layer / handler / action 是否合法、layers 与 budgets 的键是否对齐，都无人检。有四个脚本读它，读的都不是它的合法性——verify_loop.py#L62 只解 budget.ref 能否落点；sdlc_state.py 在 fail 时拿它查路由；trace.py#L253-L278 用它解 trace 里的 routing.R\d+ 目标，且写成 `if routing_rules and …`，routing.yaml 缺失或 rules 为空时这条校验静默失效（fail-open）；tune.py / apply_proposal.py 生成改它的 patch，而 apply_proposal.py 从不写目标文件。ARCHITECTURE §7 的 X2 行闸列仍为空。按 F-06 封顶 declared。
    - 未达 `verified`：无行为层运行记录，且收敛阈值按 gate.json fix_list 是文献先验、未校准（PSL-007）。
    - 无闸：skills/sdlc/assets/routing.yaml
    - 证据：`file:plugins/sdlc/skills/sdlc/assets/routing.yaml` · `file:plugins/sdlc/docs/ARCHITECTURE.md#7-覆盖矩阵与空白`
- **naming authored → `fits`** — 位置 / 产物：`skills/sdlc/assets/routing.yaml`
    - 贴合理由：Part 名即产物文件名，字面相等，F-03 判 fits。
    - 证据：`file:plugins/sdlc/skills/sdlc/assets/routing.yaml`
- disposition `issue`

#### `asset.triggers.yaml` — A-asset.triggers.yaml（state: evidenced）

- **needed `necessary`** — 撤掉后：撤掉后环的等待退回 pr-poll.sh 的 bash sleep 一种；无人值守 / headless 下每个环的 /goal 条件与"or stop after N turns"预算上限无处声明，产出的是要么根本不启动、要么停不下来的环，而且"哪些退出码必须回显到对话里"这条 /goal 陷阱无人记录。
    - 证据：`file:plugins/sdlc/skills/sdlc/assets/triggers.yaml#L1-L11` · `file:plugins/sdlc/docs/ARCHITECTURE.md#7-覆盖矩阵与空白`
- **implemented `declared`** — declared（只有 SKILL.md / 提示）
    - 未达 `compiled`：no_gate——仍没有 verify_triggers.py，ARCHITECTURE §7 对应行的闸列仍只写 verify_loop / verify_graph / check-clean。重审更正（2026-09-06）：装配时写的"triggers.yaml 不在任何一个的检查范围内"措辞过宽——smoke.sh 里有一条内联断言盯着它（每个 trigger.loop 必须是 loops.yaml 里声明过的环），断言失败即非零退出。那是插件自测套件对自家资产的回归保护，不是流水线上挡产物的闸，也不覆盖本缺口点名的两种失效（引用不存在的 predicate_scripts、漏 "or stop after N turns"）。三种绑定（interactive / unattended / headless）仍一种都没走，Stop hook 仍只有模板：assets/hooks/stop-clean-state.json 是插件里唯一的 hooks 文件，plugins/sdlc/ 下至今没有 plugin 级 hooks.json。按 F-06 封顶 declared。
    - 未达 `verified`：无行为层运行记录；三种绑定（interactive / unattended / headless）本 Run 一种都没走。
    - 无闸：skills/sdlc/assets/triggers.yaml
    - 证据：`file:plugins/sdlc/skills/sdlc/assets/triggers.yaml` · `file:plugins/sdlc/docs/ARCHITECTURE.md#7-覆盖矩阵与空白`
- **naming authored → `fits`** — 位置 / 产物：`skills/sdlc/assets/triggers.yaml`
    - 贴合理由：Part 名即产物文件名，字面相等，F-03 判 fits。
    - 证据：`file:plugins/sdlc/skills/sdlc/assets/triggers.yaml`
- disposition `issue`

[^A-sdlc]: `sdlc` 的 PSL-ID 追溯 — needed PSL-004, PSL-002 · implemented PSL-010, PSL-004 · naming PSL-014。环归属证据：`plugins/sdlc/skills/sdlc/assets/graph.yaml#L39-L45（Node.role=orchestrator → spine）`。
[^A-asset.graph.yaml]: `asset.graph.yaml` 的 PSL-ID 追溯 — needed PSL-011, PSL-002 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`no_node（graph.yaml 里没有它自己的节点）+ ARCHITECTURE.md#1-九环与一根脊柱 脊柱段"把图与环声明成数据（graph.yaml / loops.yaml / triggers.yaml）"→ spine；F-08 明列四个数据资产为脊柱上的 Part。两源不冲突。`。
[^A-asset.loops.yaml]: `asset.loops.yaml` 的 PSL-ID 追溯 — needed PSL-011, PSL-004 · implemented PSL-010, PSL-015 · naming PSL-014。环归属证据：`no_node + ARCHITECTURE.md#1-九环与一根脊柱 脊柱段（图与环声明成数据）→ spine；F-08 明列。`。
[^A-asset.routing.yaml]: `asset.routing.yaml` 的 PSL-ID 追溯 — needed PSL-008, PSL-004 · implemented PSL-015, PSL-010 · naming PSL-014。环归属证据：`no_node + ARCHITECTURE.md#1-九环与一根脊柱 脊柱段"路由失败（routing.yaml v2，含收敛检测）"→ spine；F-08 明列。`。
[^A-asset.triggers.yaml]: `asset.triggers.yaml` 的 PSL-ID 追溯 — needed PSL-011, PSL-004 · implemented PSL-015, PSL-010 · naming PSL-014。环归属证据：`no_node + ARCHITECTURE.md#1-九环与一根脊柱 脊柱段（图与环声明成数据，含 triggers.yaml）→ spine；F-08 明列。`。

## 疑似重复的 Part 对

同一件事有没有两个配件在做？下表的 **Artifact 对照** 与 **裁决** 都是从 `artifacts[]` 与两个 Part 的
`needed.verdict` 现算的（G1 规则 1 + F-05），不是抄 `suspected_duplicate_pairs` 里的那一行——
两者不一致时表里会写「登记 ≠ 现算」。三种裁决：`distinct_exits`（产物无交集，不是一回事）·
`merge_candidate`（在争同一个产物，两边都认领为合并候选，审计不当场裁）·
`alternatives_of`（同阶段的条件替代分支，F-05 三条件齐，不算争）。

| 对 | Artifact 对照 | 裁决 | 落在哪份记录 |
|---|---|---|---|
| `donewhen-extract`<br>vs<br>`acceptance-spec` | `donewhen-extract` → `done_when.yaml`<br>`acceptance-spec` → `done_when.yaml`、`specs/<f>/spec.md`、`specs/<f>/spec-robustness.md`<br>共同产物：`done_when.yaml` | **merge_candidate** | `A-donewhen-extract`、`A-acceptance-spec`<br>提案 `P-02-01` |
| `implement`<br>vs<br>`agent.comment-fixer` | `implement` → `card.allowed_files`<br>`agent.comment-fixer` → `card.allowed_files`<br>共同产物：`card.allowed_files` | **merge_candidate** | `A-implement`、`A-agent.comment-fixer`<br>提案 `P-R5-01`、`P-R5-04` |
| `implement`<br>vs<br>`agent.card-implementer` | `implement` → `card.allowed_files`<br>`agent.card-implementer` → `card.allowed_files`（alternatives_of `stage.implement`）<br>共同产物：`card.allowed_files` | **alternatives_of** | `A-implement`、`A-agent.card-implementer` |
| `pr-review`<br>vs<br>`code-reviewer` | `pr-review` → `.sdlc/review/*.yaml`、`github:review`<br>`code-reviewer` → `ratchet-log/iteration-NNN/code-review-*.yaml`<br>共同产物：无 | **distinct_exits** | `A-code-reviewer`、`A-pr-review`<br>提案 `P-R6-08` |
| `pr`<br>vs<br>`human_gate.harness-review` | `pr` → `github:pr`<br>`human_gate.harness-review` → `github:pr (harness 提案)`<br>共同产物：无 | **distinct_exits** | `A-human_gate.harness-review`<br>提案 `P-R8-06` |

- **SDP-01 `donewhen-extract` vs `acceptance-spec`** — F-05 三条件三缺二（只满足 (a) 同在 stage.contract 的 handled_by），不构成同阶段条件替代；两边 needed.verdict 都记 merge_candidate 并互指。审计不当场裁，交 G3 与一次 G2 变更提案。
- **SDP-02 `implement` vs `agent.comment-fixer`** — card.allowed_files 的第二、第三个 writer。agent.comment-fixer 不在 stage.implement 的 handled_by 里、与 implement 之间是 handoff 边而非带 when 守卫的 conditional 边，三条件不成立 → 双方都记 merge_candidate。
- **SDP-03 `implement` vs `agent.card-implementer`** — 同一个 card.allowed_files，但两者同在 stage.implement 的 handled_by、有带 when 守卫的 conditional 边选执行者、产物同 schema —— F-05 三条件齐，记 alternatives_of: stage.implement 豁免，不是争。
- **SDP-04 `pr-review` vs `code-reviewer`** — code-reviewer 的 gate.json residual 自述 overlaps /pr-review，pr-review 又是它的改编（design-notes#L50-L51）：判据同源、输入同为 diff。但两者的产物没有交集——一个进 ratchet-log 供 meta-judge 汇总，一个进 .sdlc/review 直接发成 GitHub review。按产物判 distinct_exits；边界要不要合并是 P-R6-08 的问题，不是本次的裁决。
- **SDP-05 `pr` vs `human_gate.harness-review`** — graph.yaml 里两个节点的 writes 字符串都叫 github:pr（#L210 / #L273），一读就是双生产者。但它们是两个不同的 PR（特性交付 PR / harness 提案 PR），故按两个 Artifact 登记，图里的同名当源码问题记 P-R8-06。

## proposals

45 条。每条都必须指向一个已识别的 Assessment 或 Gap（DP-2：补的理由不能是「这环显得单薄」）——`proposal_without_source` 就是这条的闸。
按 destination 分组：

### new_issue（29）

| id | source | 提案 |
|---|---|---|
| `P-02-01` | `A-acceptance-spec` | done_when.yaml 有两个非豁免生产者（donewhen-extract / acceptance-spec，F-05 三条件只满足 (a)）。建议以 done_when.yaml v2 为唯一契约，acceptance-spec 的契约出口收敛为"产 spec.md + 经 convert_v1_to_v2.py 交棒"，或反向合并。审计不当场裁，交 G3 与一次 G2 变更提案。 |
| `P-02-02` | `R2/newly_identified/control/spec-md-no-gate` | specs/<f>/spec.md 与 spec-robustness.md 无任何闸。建议加 verify_spec.py（EARS 句型 + REQ-ID 稳定性 + 与 done_when.yaml 的 REQ 覆盖对账），或在 §1 表里显式登记"无闸"并把其生产者的 implemented 钉在 declared。 |
| `P-02-03` | `spine/newly_identified/control/routing-yaml-no-verifier` | routing.yaml 无自身验证器。建议加 verify_routing.py：rules 行的 signal / layer / handler / action 在封闭集内、layers 与 budgets 键对齐、impossible_reporters 全部是图里存在的节点、每个 signal 被 loops.yaml 的某个环声明。 |
| `P-02-04` | `spine/newly_identified/control/triggers-yaml-no-verifier` | triggers.yaml 无自身验证器。建议扩 verify_loop.py 或新增 verify_triggers.py：每个 loop 在 loops.yaml 内、kind 与该环的 trigger 一致、predicate_scripts 指向存在的文件、每个 unattended 绑定含 "or stop after" 预算子句。 |
| `P-02-05` | `R1/newly_identified/control/decisions-md-no-gate` | decisions.md 无闸，而 verify_dos.py 的 ">7 objects" 拒绝把豁免路径指向它。建议 verify_dos.py 增加一项：objects > 7 时要求同目录 decisions.md 存在且含对应豁免条目，否则拒——否则这是一条指向空气的豁免路径。 |
| `P-02-06` | `spine/unenforced_rule/control/r008-human-signer` | R008（三道门只能人签，enforced_by user_workflow）在机器一侧无承载。建议 sdlc_state.py gate 记录 signer_kind 并对 delegated_agent 强制 authorization_ref（与 check_audit.py 的 delegated_without_authorization_ref 谓词同形），至少让代签留下不可省略的痕迹。 |
| `P-02-08` | `R0/lifecycle_blank/capability/psl-reference-lint` | PSL 引用完整性 lint 未实现（lifecycle.md 自列）。它是 psl-derive 的 PSL-ID 追溯校验的前提：一份自身引用残缺的 PSL 会让"每条决策 ← PSL-ID"的锚看似成立实则指空。 |
| `P-R3-01` | `R3/lifecycle_blank/control/red-green-evidence-script` | L5 的红-绿证据脚本在 ARCHITECTURE §7 与 lifecycle.md 制品映射表里都登记为空白。开一条 issue： 定义「一个测试在实现前红过」的机器可读证据形状，并把它编进 lock --stage l5 的前置条件。 |
| `P-R3-02` | `R3/unenforced_rule/control/uncalibrated-standard-used-as-evidence` | dos.yaml R010 的 calibrate 那一半 enforced_by=not_enforced。开一条 issue：在下游读标准之前加一道检查， 要求 calibration_report.yaml 存在且 mutation / agreement 双线过底线，否则标记 calibration_pending 并拒绝当证据。 |
| `P-R5-01` | `A-implement` | card.allowed_files 有三个 writer，其中 implement 与 agent.comment-fixer 不构成 F-05 同阶段条件替代， 两者都记 merge_candidate。请人裁：是把 comment-fixer 的写范围改成一个独立的产物名（它写的是被接受线程的最小修复）， 还是把 R001 降级为文档规则。审计不当场裁掉一个。 |
| `P-R5-02` | `A-agent.comment-fixer` | role_conflict：graph.yaml 的 Node.role=implementer 把 comment-fixer 推到 R5，而 ARCHITECTURE §1 表把它所属的 review-loop 归在 R7，loops.yaml 又把它写成 review_loop 的 generator（graph.yaml 那个节点却没有 loop 键）。 请人裁归属并让两份数据一致；本审计并列两源，不调和。 |
| `P-R5-04` | `R5/unenforced_rule/control/one-producer-per-artifact-unlinted` | R001 无机械检查。开一条 issue：给 verify_graph.py 加一条唯一生产者 lint（同阶段条件替代显式豁免）， 否则「条件替代」与「真的在争」在 graph.yaml 里长得一样。 |
| `P-R6-01` | `R6/newly_identified/control/g3-pass-has-no-input-precondition` | 给 cmd_gate 的 G3 pass 补输入前置，与 G1 / G2 对齐：pass 前要求 acceptance.evaluation_result 指向一个存在的文件（或显式 skipped_reason），reject / waived 要求 pending.failure_report 存在。现状是三道门里唯一一道盖章不看纸的门。 |
| `P-R6-02` | `R6/lifecycle_blank/capability+control/meets-done-when-compare-script` | 补 meets_done_when 比对脚本（ARCHITECTURE §7 L7 行与 lifecycle.md 制品映射表都把它记为空白）：读 done_when.yaml 的 thresholds 与本轮实测数字并排比，退出码即结论，写进 final-state.json。在它落地前，R6 的"达标"只有自然语言形态。 |
| `P-R6-03` | `R6/unenforced_rule/control/evaluator-may-declare-meets-done-when` | 把 acceptance.meets_done_when 移出 sdlc_state.py 的 SETTABLE 白名单（#L67），改为只能由 P-R6-02 那个比对脚本写入。否则即便脚本落地，任何 agent 仍可一句 set 直接宣布达标——dos.yaml R010 的 not_enforced 说的就是这个。 |
| `P-R6-04` | `R6/newly_identified/control/ratchet-log-shape-unchecked` | advance pr 对 acceptance.evaluation_result 补 os.path.isfile（对齐同文件 #L262 对 lock.path 的写法），并加一个 verify_ratchet_log.py 按 ratchet-log-format.md 检目录形状。现状是一个指向不存在路径的字符串就能把流水线放行到 merge。 |
| `P-R6-07` | `A-fix-verifier` | 收编即改名与 PSL-014「收编保留上游名」的分歧：design-notes#L56-L57 记的这批 agent 里 quality-sentinel → fix-verifier、issue-fixer → comment-fixer、code-reviewer → pr-reviewer 三处都改了名，而同一份文档 #L70 的命名规则只说"保留导入 skill 的原名"。要么把规则改成"skill 保留上游名、agent 按产物重命名"，要么把这三处记成显式例外。不改名（新名更贴合），改的是规则的说法。 |
| `P-R6-09` | `R6/unenforced_rule/control/one-artifact-one-producer-in-ratchet-log` | 给 verify_graph.py 加一条 lint：skill / agent 节点的 writes 之间不得相互包含。现有 lint ①（#L131-L139）只挡裸 ** / * / / / .，挡不住 ratchet-log/iteration-NNN/** 覆盖同目录下六个具体文件这种包含关系——dos.yaml R001 的 user_workflow 就落在这个缺口上。 |
| `P-R6-10` | `A-review-triager` | plugins/sdlc/agents/ 下的五个 agent 都只有 .md 提示，没有 eval/gate.json——每个 skill 都有的证据档位纪律（tier / evaluated_layers / gate_pass / fix_list）整体不覆盖 agent。至少给每个 agent 补一份 gate.json 记它停在哪一档，否则 dos.yaml R017「有效性主张不得超过证据档位」对这一半配件没有落点。 |
| `P-R6-11` | `R6/unenforced_rule/control/gate-signer-must-be-human` | cmd_gate 收 signer_kind = delegated_agent 只要带一句 --authorization 自由文本（sdlc_state.py#L502-L503），没有任何一处核对授权是否真来自人。要么把 authorization 收成一个引用（指向一份人写的授权记录文件并检存在），要么让 G3 只接受 signer_kind = human。dos.yaml R008 现在是 user_workflow。 |
| `P-R7-02` | `R7/newly_identified/control/merged-sha-vs-approved-head` | 合入的 sha 与 review / G3 批准过的 head 无脚本核对；建议在 advance release 的前置条件里加一条 merge.sha 与 review.approved_head 的比对，或由 verify_release.py 检。 |
| `P-R7-04` | `R7/unenforced_rule/control/merge-signer-not-enforced` | dos.yaml R008 的 enforced_by 是 user_workflow：没有脚本阻止 agent 记录 merge 这道人门的结论。要么把它编译（记录签字人与 signer_kind），要么把 R008 的 enforced_by 诚实降级并在 §1 写明。 |
| `P-R7-05` | `R7/unenforced_rule/judgment/static-only-claim-not-enforced` | dos.yaml R017 的 enforced_by 是 user_workflow：流水线里没有脚本拒绝一份把 static_only 说成 verified 的报告。本次审计用 check_audit.py 的 boolean_implemented / implemented_outside_enum 编译了这条规则，但只在审计文档内生效 —— 建议推广到验收侧。 |
| `P-R8-01` | `A-tune` | naming misfit: tune → suggested_name harness-tune（产物是 harness-proposals，位置是 hill_climb 环，"调什么"是这个名字唯一没说的东西，而 target 恰是封闭集）；不重命名，另开 G2 变更提案 —— 改名要同时动 graph.yaml / loops.yaml / triggers.yaml / ARCHITECTURE §1 / retro 接线段。 |
| `P-R8-03` | `R8/newly_identified/control/retro-output-no-rejecting-gate` | retro 的产物无拒绝型闸也无门，PSL-015 在 R8 断掉；建议补一个 verify_retro.py（检基线表存在、每条提案有 target ∈ 封闭集 / change / verify_by、数字来自 metrics.json 而非手抄）。 |
| `P-R8-04` | `R8/newly_identified/knowledge+judgment/harness-change-effect-unmeasured` | hill_climb 的 success 谓词只到 merged \| rejected，没有"上期 expected_delta 是否兑现"的回读；建议在 loops.yaml#hill_climb 的 goal 里加一条效果谓词，并让 tune.py 下一期先核对上期提案的 verify_by。 |
| `P-RA-02` | `R5/newly_identified/control/gate-json-stale-after-script-lands` | 没有任何机械物要求「skill 的脚本变了，它的 eval/gate.json 必须一起变」。本轮 commit 长出承重脚本 commit.sh、verify_commit.py 加了六类新拒绝，而 commit/eval/gate.json 一个字节没动；plan-cards 同样。后果是效力档位失去对账基础——R017「效力声明不得超过证据档」在证据档比代码旧的时候形同虚设。建议：给 verify_commit.py 加一条检查，skills/<s>/scripts/ 有改动而 skills/<s>/eval/gate.json 的 provenance.date 未动即 flag（不是 reject，因为文档改动也算改动）。 |
| `P-RA-04` | `R6/newly_identified/knowledge+control/ratchet-log-filenames-diverge-from-graph` | ratchet-log 的文件名两处不一致，已被三轮真实 run 坐实：落地的是 fleet-outputs/{code-reviewer-security,qa-reviewer,pm-reviewer,…}.yaml 与 meta-judge-output.yaml，而 graph.yaml 写的是 ratchet-log/iteration-NNN/{code-review-*,qa-review,…}.yaml 与 final-verdict.yaml——目录层级、文件基名都不同。任何按 graph.yaml 找文件的下游都会扑空。定一个名并全线改齐（与 P-R6-05 是同一件事的两半）。 |
| `P-RA-06` | `R7/newly_identified/judgment/solo-a-tier-count-not-from-the-contract` | 单人仓库替代谓词把「该轮 A 档存活 = 0」当作 APPROVED 的替代必要条件，但 A 档的数怎么来没有契约：脚本取 findings 文件里显式的 a_tier_survivors，没有就数 tier: A / severity: P0 的条目——两种数法可能给出不同的数，而写 findings 的是被审方自己的预审 agent。建议把 A 档判据写进 done_when 或 agents/pr-reviewer.md 的输出契约，让这个数有来源。 |

### skill_fix_list（16）

| id | source | 提案 |
|---|---|---|
| `P-02-07` | `A-psl` | verify_psl.py 是声明式预门（SKILL.md 写"交付前必须跑"，无 hooks.json 绑定），gate.json fix_list 已自列为 A'-1。本次审计只据此判 compiled，不判"被门挡"。 |
| `P-R4-01` | `R4/newly_identified/control/card-depends-on-unchecked` | lint_cards.py 加第六项：depends_on 里的每个卡号必须存在，且卡之间的 depends_on 图无环；违反 REJECT。 现状是 SKILL.md 用 depends_on 决定并行而 lint 完全不读它。 |
| `P-R5-03` | `R5/newly_identified/control/experiment-dir-unchecked` | ratchet 的 experiment_dir/** 无闸无门，按 F-06 把 ratchet 的 implemented 压在 declared。 fix_list 加一条：给 experiment_dir 写一个形状 + 预算 + generator≠verifier 的 verify 脚本，或明确记为不检并说明理由。 |
| `P-R5-05` | `A-ratchet` | loops.yaml#ratchet 的 generator 写 ratchet.worker、verifier 写 ratchet.master，这两个 id 在 graph.yaml 的 nodes 里都不存在（只有节点 ratchet）。verify_loop.py 只检 generator ≠ verifier，不检两者可解析成图节点， 所以这条悬空引用一直绿着。fix_list 加一条：环契约的 generator / verifier 必须解析到 graph.yaml 的节点 id。 |
| `P-R5-06` | `R5/newly_identified/control/agent-parts-without-gate-json` | plugins/sdlc/agents/ 下五个 agent 都没有 eval/gate.json，效力档位无处可查。 fix_list 加一条：给 agent 定义与 skill 同形的证据档，或在 ARCHITECTURE 里明确写「agent 的效力随其宿主 skill 记」。 |
| `P-R6-05` | `A-meta-judge` | meta-judge 的产物有两个名字：graph.yaml#L189 写 final-verdict.yaml，SKILL.md 的 --output 默认值（#L75）与 M5 步（#L87）、ratchet-log-format.md#L41 与 acceptance-fleet SKILL.md#L163/#L254 都写 meta-judge-output.yaml；连 SKILL.md 内部都不一致（description 与 M0 播报说 final-verdict.yaml）。定一个名并全线改齐。附注：meta-judge 节点没有 loop 键，而它是 acceptance_ratchet 的 verifier 兼 loop_back 源，环归属只能从边反推——顺带补上。 |
| `P-R6-06` | `A-acceptance-fleet` | 五个评审者的产物路径两处不一致：graph.yaml#L179-L183 写扁平的 ratchet-log/iteration-NNN/{code-review-*,qa-review,pm-review,drift,gaming}.yaml，acceptance-fleet SKILL.md#L122 与 #L237-L256、ratchet-log-format.md#L41 写 ratchet-log/iteration-NNN/fleet-outputs/{code-reviewer-security,qa-reviewer,pm-reviewer,spec-drift-detector,spec-gaming-detector}.yaml——目录层级与文件基名都不同。任何按 graph.yaml 找文件的下游都会扑空。 |
| `P-R6-08` | `A-code-reviewer` | code-reviewer 的 gate.json residual 自述"overlaps /pr-review"，而 pr-review 正是它的改编（design-notes#L50-L51）。两个配件读同一种输入（diff）、出同一种产物（发现列表），只是一个进 ratchet-log 一个进 .sdlc/review。写清边界：谁在 fleet 里跑、谁给单 PR 手审用，或者合并成一个带模式开关的配件。 |
| `P-R7-01` | `A-agent.pr-reviewer` | agents/pr-reviewer.md 在 graph.yaml 无节点（R6 的 /pr-review 与 R7 的 /pr --pre-review 都调它），环归属只能靠 ARCHITECTURE §1 与两份 SKILL.md 推；建议在 graph.yaml 补节点并显式标环，否则 §1 与图对不上。另记：收编时上游名 code-reviewer 未保留（撞 R6 同名 skill），是 PSL-014 的一处受迫偏离。 |
| `P-R7-03` | `R7/newly_identified/control/reply-resolve-order-unchecked` | pr-poll.sh resolve 不核对该线程上是否已有落地回帖，"回帖先于 resolve"只活在 SKILL.md 的判据里；建议 resolve 子命令先查一次该线程的 comments，无自己的回帖则 exit 22。收件人：review-loop 的 eval/gate.json fix_list。 |
| `P-R8-02` | `A-retro` | ARCHITECTURE.md#L42 §1 R8 的「门 / 闸」列把 metrics.py 与 tune.py 渲染成闸，但两者都无非零退出路径（tune/SKILL.md#L69 自述"报告工具"）。建议把该列改写为「导出：metrics.py / tune.py；控制：apply_proposal.py 只出 diff + human.harness-review」，否则设计视图高于实况（R017）。 |
| `P-R8-05` | `R8/unenforced_rule/judgment/uncalibrated-tune-thresholds` | tune 的 40% / 50% / 0.95 是文献先验、未在本仓库校准（gate.json fix_list 已自述），但产出的提案没有携带"未校准"的标记；建议 tune.py 在每条提案里带 calibrated: false，让人在 review 时看得见（PSL-007）。 |
| `P-R8-06` | `A-human_gate.harness-review` | graph.yaml 两处待修：① L273 human.harness-review 的 writes 与 L210 pr 的 writes 同名 github:pr，但它们是两个不同的 PR，按 R001 一读就成了双生产者；② 该节点没有 loop: 字段，尽管 loops.yaml#L111 把它列为 hill_climb 的 verifier、L362 的边已带 loop: hill_climb。 |
| `P-RA-01` | `R2/newly_identified/control/gaming-band-unvalidated-at-r2` | done_when.yaml 新增的 gaming_risk_threshold（done_below / block_at_or_above）在 R2 无人校验：acceptance-spec 的 validate_done_when.py 与 donewhen-extract 的 validate_done_when_v2.py 都不认识这个字段，唯一校验它的是 R6 的 next_iteration.py。后果是一份倒挂的阈值（done_below=7 / block_at_or_above=3）在 R2 判 clean、被 G2 冻进锁，直到 R6 第一次 ratchet 才炸——那时改契约的代价从"写契约时改一行"变成"解冻一份已签字的契约"。建议把这条校验前移到 v2 校验器。收件人：donewhen-extract 的 eval/gate.json fix_list。 |
| `P-RA-03` | `R6/newly_identified/control/drift-consumer-flag-not-updated` | spec-drift-detector 的输入契约被单边改了而它自己不知道：acceptance-fleet 现在按 skill-dispatch-matrix.md 传 --qa-measurements 并明令禁止 --qa-report，而 spec-drift-detector/SKILL.md 的参数表仍只定义 --qa-report、铁律 8 仍指导用它。调度方与被调度方对同一个 flag 说两件事。建议改齐 SKILL.md，或让调度矩阵与参数表同源。收件人：spec-drift-detector 的 eval/gate.json fix_list。 |
| `P-RA-05` | `R6/newly_identified/control/gate-json-not-synced-with-smoke-coverage` | acceptance-fleet 长出了两个真闸（next_iteration.py / qa_facts.py）并有 smoke 覆盖，而它的 eval/gate.json 仍写 gate_pass=static_only、scripts_run 为空对象。证据档比代码旧，读 gate.json 的人会低估它的承重。收件人：acceptance-fleet 的 eval/gate.json。 |

### no_action（0）

本次无。

<a id="run-evidence"></a>

## run_evidence

本次运行的行为层证据。签字三元组住在这里，不在 `gates[]`（G1 规则 3b）。

| 项 | 值 |
|---|---|
| slug | `sdlc-ring-audit` |
| 状态机 | `.sdlc/sdlc-ring-audit/state.json` |
| 账本 | `.sdlc/sdlc-ring-audit/ledger.md` |
| 分支 | `docs/1-sdlc-ring-audit` |
| issue | `#1` |

### 三道门的签字（F-07 三元组）

`verdict` ∈ pending / pass / reject / waived。pending 之外的任何判决都必须有 signer 与 signer_kind；
`delegated_agent` 必须附授权引用，并且**只能渲染为「代签（delegated）」——本次三道门没有一道是人签**。

| 门 | verdict | 签字人 | signer_kind | 渲染为 | 授权引用 | 时间 |
|---|---|---|---|---|---|---|
| `G1` | **pass** | `g1-judge` | `delegated_agent` | **代签（delegated）** | g1-record.md#签字性质 (user instruction 2026-09-05: '需要人审核的地方，请你弄一个子agent代替我审核一下') | `2026-09-05T14:59:49Z` |
| `G2` | **pass** | `g2-judge` | `delegated_agent` | **代签（delegated）** | .done_when.lock#authorization | `2026-09-05T14:58:31Z` |
| `G3` | **pass** | `g3-judge` | `delegated_agent` | **代签（delegated）** | plugins/sdlc/dogfood/ring-audit/g3-record.md — user instruction 2026-09-05: '需要人审核的地方，请你弄一个子agent代替我审核一下'；代签，非人签。该记录自陈：G3 的 pass 无输入前置、--authorization 无人核对，故其效力来自记录中列出的可重跑复现，不来自盖章本身 | `2026-09-06` |

### check-audit 的两次运行（F-14 校准孪生）

对报告的 exit 0 只有在同一次运行里配上删环变体的 exit 1 才算证据；没有变体记录的 exit 0 标 `uncalibrated`，不当证据。

**本次：变体记录在场，exit 0 可作证据。**

运行 1 — **exit 0**

```
python3 plugins/sdlc/dogfood/ring-audit/check_audit.py plugins/sdlc/dogfood/ring-audit/audit.yaml --psl plugins/sdlc/dogfood/ring-audit/PSL-sdlc-ring-audit.md --required-parts "agent.card-implementer, agent.comment-fixer, agent.fix-verifier, agent.pr-reviewer, agent.review-triager"
```

观察到：`rings: 10` · `parts_total: 42` · `parts_without_assessment: 0` · `required_parts_missing: 0` · `failed_predicates: []`

运行 2 — **exit 1**

```
python3 plugins/sdlc/dogfood/ring-audit/check_audit.py plugins/sdlc/dogfood/ring-audit/audit.yaml --psl plugins/sdlc/dogfood/ring-audit/PSL-sdlc-ring-audit.md --required-parts "agent.card-implementer, agent.comment-fixer, agent.fix-verifier, agent.pr-reviewer, agent.review-triager" --variant delete-ring:R6
```

观察到：`rings: 9` · `parts_total: 31` · `required_parts_missing: 2` · `orphan_gaps: 21` · `failed_predicates: [ring_missing, orphan_gap, proposal_without_source, required_part_missing]` · `error: ring_missing: R6`

> 删掉 R6 后 R6 的 11 个 Part 连同它们的 FILLS 边一起消失，R6 的 21 个 Gap 变孤儿、两个必到 Part 缺席、以 R6 的 Assessment 为 source 的提案失去来源——ring_missing 之外的三条谓词都是同一次删除的连带，不是另外的缺陷。（重审后 R6 新增三条缺口，孤儿数 18 → 21，并多出 proposal_without_source 这条连带；两次都是 exit 1。）

### 修复后的重审（PSL-009：合入不是终点）

装配时的判定读的是 `ab67052` 之前的代码。缺陷登记表里的修复落地后，四份 delta 在 `ab67052` 上重读了全部十环，本文件是它们的落点（应用于 `b77feb0`）。签字：`reaudit-orchestrator` — **代签（delegated_agent）**，授权 user instruction 2026-09-06: '把所有没有完成的都完成，需要人做的你就帮我做了当做人做的'；代签，非人签。

| 项 | 值 |
|---|---|
| implemented 档位分布 | 重审前 declared 19 / compiled 23 / verified 0 → 重审后 **declared 17 / compiled 25 / verified 0** |
| 缺口 | 73 → **79**（闭合 1，新增 6） |
| 证据锚点 | 重定位 105 处，原位未动 257 处 |
| 提案 | 39 → **45**（新增 6） |
| 没有变的 | 0 个配件达到 verified；三道门仍全是代签；仓库仍无 CI。 |

> 锚点怎么修的：逐个锚点从装配时的 fbc6a3c 取原文，再到 HEAD 里按内容定位，得出新行号——不用算术推算。 graph.yaml 本轮插入 agent.pr-reviewer 节点（+10 行）与两条边（+2 行），插入点之后的锚点分两段位移，算术会算错，故一律按内容重定位。

改档的两处（其余 40 个配件一处没动）：

- `R6/qa-reviewer` 的 `implemented`：`declared` → `compiled` — 本次唯一有异议的抬档；异议原文与裁定理由写在该 Part 的 reaudit_note 里
- `R7/agent.pr-reviewer` 的 `implemented`：`declared` → `compiled` — F-06 封顶的前提消失——独占产物 findings.yaml 现在被 pr-poll.sh selfreview 校验（I-87）

四份 delta 逐字保留在：`plugins/sdlc/dogfood/ring-audit/reaudit/delta-R0-R2-spine.yaml` · `plugins/sdlc/dogfood/ring-audit/reaudit/delta-R3-R5.yaml` · `plugins/sdlc/dogfood/ring-audit/reaudit/delta-R6.yaml` · `plugins/sdlc/dogfood/ring-audit/reaudit/delta-R7-R8.yaml`

### 审计者不改被审对象（PSL-003）

由 `plugins/sdlc/dogfood/ring-audit/replay_card_commits.sh` 证明，不由记忆保证：分支上每个带 `Card:` footer 的提交，按它自己那张卡的
白名单回放一遍 `verify_commit.py`，并检查它有没有碰被审的三个目录。

| 项 | 值 |
|---|---|
| 回放命令 | `bash plugins/sdlc/dogfood/ring-audit/replay_card_commits.sh` |
| 回放 exit | **0** |
| 回放结论 | `ok: true` |
| 分支 · HEAD | `docs/1-sdlc-ring-audit` @ `a2deb83` · `range_spec: main..HEAD` |
| 重新求证 | `bash plugins/sdlc/dogfood/ring-audit/replay_card_commits.sh at a2deb83 on docs/1-sdlc-ring-audit`（`sha_scope: branch-specific` — 下表的 sha 只在这个分支上解析得出，换分支或 rebase 后必须重跑） |
| Card-footer 提交数 | 14 |
| **碰了被审目录的提交数** | **0** |
| 回放被拒的提交数 | 0 |
| 无 Card footer 的提交（只记录，不进判定） | 自第一个 Card 提交起扫了 20 个，其中 **4** 个碰了被审目录 |

| 提交 | 卡 | 回放 exit | 碰被审目录 |
|---|---|---|---|
| `a2deb83` | `CARD-01` | 0 | `false` |
| `ba7d5e2` | `CARD-06` | 0 | `false` |
| `7cb1f55` | `CARD-01` | 0 | `false` |
| `843c3ee` | `CARD-06` | 0 | `false` |
| `5c84a5a` | `CARD-06` | 0 | `false` |
| `b24243d` | `CARD-06` | 0 | `false` |
| `6326123` | `CARD-06` | 0 | `false` |
| `3441ba4` | `CARD-06` | 0 | `false` |
| `eba9796` | `CARD-04` | 0 | `false` |
| `419a364` | `CARD-02` | 0 | `false` |
| `f8ef234` | `CARD-05` | 0 | `false` |
| `05963a5` | `CARD-03` | 0 | `false` |
| `08238cd` | `CARD-01` | 0 | `false` |
| `0be2770` | `CARD-01` | 0 | `false` |

三个被审目录（`plugins/sdlc/skills`、`plugins/sdlc/agents`、`plugins/sdlc/docs`）自第一个 Card 提交（`0be2770`）起的 `git diff --stat`：

```
git diff --stat 0be2770^..HEAD -- plugins/sdlc/skills plugins/sdlc/agents plugins/sdlc/docs
→ 0 行输出（空）
```

### skill 源码问题

路径：`plugins/sdlc/dogfood/ring-audit/skill-issues.md` — 81 条（`grep -c '^| I-'`）。

### 这把尺子校准到什么程度

> instrument mutation 0.767 (23/30); fixture mutation 24/24; holdout 6/10 with 4 known gaps — never the unqualified word 'calibrated'

以上措辞逐字取自 `calibration/known_gaps.yaml`（calibrate 阶段的已接受声明）。
**报告里不出现不带限定语的「calibrated」**：本次的尺子有 11 项已知空隙，列在下面。

#### holdout（实现者从未见过的那一片）

| 项 | 值 |
|---|---|
| 记录 | `.sdlc/sdlc-ring-audit/hidden/ring-audit/holdout_run.json` |
| 清单 | `.sdlc/sdlc-ring-audit/hidden/ring-audit/holdout_manifest.yaml` |
| 仪器 HEAD | `5a6889c` |
| 变体 | 10 |
| 命中 / 未命中 | 6 / 4（hit_rate 0.6） |
| 见证人 | `orchestrator` · **代签（delegated）** |
| 授权 | user instruction 2026-09-05: '需要人审核的地方，请你弄一个子agent代替我审核一下' |
| 渲染规定 | `render_as: delegated` — F-15：不渲染为人的验证 |

#### 已知空隙（11 项，逐字取自 `calibration/known_gaps.yaml`）

每一条都是 open，去向 change-proposal-002（先过 G1 解释轮，再补锁定测试，再要一片新的 holdout）。

| id | 空隙 | 规格出处 | 期望 token | 状态 |
|---|---|---|---|---|
| `KG-01` | waived_without_waiver_ref | g1-record.md 签字版解释规则 3c — waived 只能引用 state.json 的 waiver 记录 | `unspecified` | open → change-proposal-002 (needs waiver_ref field + token) |
| `KG-02` | proposal_dangling_source | done_when.yaml AC-004-b given 'lacking a source assessment or gap id'; audit.schema.md §Proposal | `proposal_without_source` | open → change-proposal-002 (instrument checks non-empty key only) |
| `KG-03` | duplicate_ring_id | done_when.yaml AC-001-a expect rings: 10; thresholds rings == 10 (count) vs F-13 ring SET | `unspecified (ring_unexpected checks id membership, not count)` | open → change-proposal-002 (ring_duplicate predicate) |
| `KG-04` | signer_kind_outside_enum | derived/form-draft.md F-07 signer_kind ∈ {human, delegated_agent} | `unspecified` | open → change-proposal-002 |
| `KG-05` | M03 ring_unexpected predicate disabled → undetected | F-13 ring set; AC-001-a | `ring_unexpected` | open → change-proposal-002 (mutant_ring_unexpected.yaml) |
| `KG-06` | M04 parts_missing predicate disabled → undetected | F-13 three dimensions per Part; AC-001-a parts_without_assessment | `parts_missing` | open → change-proposal-002 (mutant_part_without_assessment.yaml) |
| `KG-07` | M07 evidence_missing predicate disabled → undetected | F-13 evidence ≥ 1 per dimension; AC-002-a dims_without_evidence | `evidence_missing` | open → change-proposal-002 (mutant_evidence_missing.yaml) |
| `KG-08` | M14 cross-ring gap reference check disabled → undetected | G1 rule 2e same-ring; AC-004-a | `unknown_gap_ref` | open → change-proposal-002 (mutant_gap_ref_wrong_ring.yaml) |
| `KG-09` | M22 gate_verdict_outside_enum predicate disabled → undetected | G1 rule 3b verdict ∈ {pending, pass, reject, waived}; AC-006-a | `gate_verdict_outside_enum` | open → change-proposal-002 (mutant_gate_verdict_outside_enum.yaml) |
| `KG-10` | M23 signer required only on pass (reject / waived without signer undetected) | G1 rule 3b; AC-006-a | `human_gate_without_signer` | open → change-proposal-002 (mutant_gate_reject_without_signer.yaml) |
| `KG-11` | M28 --rings view ignored → undetected | F-17 view narrowing; AC-008..011-a | `ring_missing (twin) / exit 0 (narrowed view)` | open → change-proposal-002 (test_AC_010_a_F17_rings_view_excludes_absent_rings) |

### 外部证据

- 档位：**`substitute`** — 这是外部证据的**替代品**，不是用户验证，也不是行为层的对比运行。
- 内容：check-audit 机械检查 + 代签 agent 独立读
- 有效范围：`this dogfood only`

## assembly notes

CARD-06 只做装配。四个片段的正文逐字保留（同一段 YAML 在片段与 `audit.yaml` 里字节一致），装配时只做了下面这些事，一处不漏：

| # | 改动 | 为什么 | 影响 |
|---|---|---|---|
| 1 | rings 重排为 R0…R8, spine | 片段的自然顺序是 R0,R1,R2,spine / R3,R4,R5 / R6 / R7,R8；`spine` 移到末尾 | 只改顺序，环与配件的内容一字未动 |
| 2 | 去重 `gates[]` 的 `lock_done_when.py` | CARD-02 与 CARD-03 各登记了一次，两条内容完全相同 | 保留第一条；31 条 Gate 无内容冲突 |
| 3 | 新增顶层 `suspected_duplicate_pairs[]` | 「哪两个配件疑似重复」是跨片段的事实，任何单张卡都写不了；AC-005-a 点名要 pr-review vs code-reviewer 与 donewhen-extract vs acceptance-spec 两对 | 只是索引：Artifact 对照与裁决由 `render_audit.py` 从 `artifacts[]` 现算并与登记值比对，不一致会在表里标出来 |
| 4 | 新增顶层 `run_evidence{}` | 片段按约定不写它（它是整份文档级的证据） | 门的签字、2 次 check 运行、回放结果、校准措辞与 11 项已知空隙 |
| 5 | `run_evidence.calibration_wording` / `holdout` / `known_gaps` 逐字复制 | 它们是 calibrate 阶段的已接受声明 | 未改一字，含「never the unqualified word 'calibrated'」这条措辞禁令 |

**其余全部为空**：没有新增、删除或改写任何 Part、Assessment、Gap、Artifact、Gate、Proposal；
没有解决任何片段间的内容冲突（因为没有冲突：79 个 Gap、58 条产物-生产者、45 条提案的 id 两两不撞）。

### 装配核对：PSL-017 三种来源都登记了吗

`dos.yaml` 有 4 条规则的 `enforced_by` 不是 `system`（R001 / R008 / R010 / R017）——每一条都必须在合并后的 `gaps[]` 里至少有一条
`source: unenforced_rule` 的登记。下表的「登记在」与「缺口数」由 `render_audit.py` 拿
`unenforced_rules[].dos_anchors` 去 `gaps[].evidence[].ref` 现算，不是抄来的：

| dos.yaml 规则 | enforced_by | 登记在 | 缺口数 | 要补登吗 |
|---|---|---|---|---|
| R001 一个产物只有一个生产者 | `user_workflow` | `R5` · `R6` · `spine` | 3 | 否，片段已覆盖 |
| R008 三道门只能人签 | `user_workflow` | `R6` · `R7` · `spine` | 3 | 否，片段已覆盖 |
| R010 未校准的标准不当证据 | `not_enforced` | `R3` · `R6` · `R8` | 3 | 否，片段已覆盖 |
| R017 静态过审 ≠ 有效 | `user_workflow` | `R6` · `R7` | 2 | 否，片段已覆盖 |

4 / 4 条规则有登记；11 条 `source: unenforced_rule` 的缺口里 11 条归到了上表，没有落单的。

R017 归到的两个环不是装配当时预判的 R3 / R8（上表现算的结果为准）：一处是「验收线自己没被验收」的
位置，一处是三个 static_only 的交付 skill——都比预判的位置更贴。

### 输入片段

- `plugins/sdlc/dogfood/ring-audit/audit/rings-R0-R2-spine.yaml`
- `plugins/sdlc/dogfood/ring-audit/audit/rings-R3-R5.yaml`
- `plugins/sdlc/dogfood/ring-audit/audit/rings-R6.yaml`
- `plugins/sdlc/dogfood/ring-audit/audit/rings-R7-R8.yaml`

### 铁律

check-audit 的 exit 0 说的是**这份文档的形状齐全**，不是「九环做到位了」。42 个配件里 17 个停在 `declared`、25 个停在 `compiled`，**没有一个到 `verified`**；三道门里 3 道代签（delegated）；外部证据是 `substitute`。
这份报告能不能当结论，由 G3 的人看完上面这些标记之后决定。
