# Docs-side inventory — sdlc plugin (as-is)

Corpus: `README.md`, `docs/ARCHITECTURE.md`, `docs/lifecycle.md`, `docs/routing.md`, `docs/design-notes.md`,
`docs/proposals/loop-graph-engineering.md` (6 files, ~1050 lines). Secondary corpus (code-side prose): 28 `skills/*/SKILL.md`
+ 5 `agents/*.md`; data corpus: `skills/sdlc/assets/{graph,loops,routing,triggers}.yaml`, `state.schema.json`.
Counts are regex occurrences (case-insensitive, CJK + English variants), computed 2026-09-05; ≈ because variants overlap.

## Nouns

- **门 / Gate / G1 G2 G3** (≈150 docs · 321 skills · 68 data)
  - "三道门只能人签；--autopilot 免的是逐步确认，不是门" — `docs/ARCHITECTURE.md` §6
  - "每一步的产物要么能被脚本检，要么被一道只能人签的门挡住" — `README.md`
  - Notes: 门 is also used for "自动门 / 机械预门 / 闸" (script pre-gates) — overloaded (see Cross-references).
- **环 (all senses)** (≈107 docs) — two senses:
  - **九环 / R0–R8 ring** (≈21 docs · 0 skills · 9 data): "九环与一根脊柱" — `ARCHITECTURE.md` §1; "用 docs/ARCHITECTURE.md 的'九环'组织，不用前缀重命名" — `design-notes.md`
  - **环契约 / loop** (≈134 docs · 88 skills · 52 data): "六个环同一契约：card_retry · ratchet · acceptance_ratchet · review_loop · lifecycle · hill_climb" — `ARCHITECTURE.md` §3.7; "每个圈必须归属一个环" — §8
- **契约 / Contract / done_when** (≈112 docs · 424 skills · 46 data)
  - "契约 v2 是全线的转轴" — `ARCHITECTURE.md` §2; "契约只有一种 schema（v2）" — §6 rule 1
- **AC / 判据 / acceptance** (≈119 docs · 308 skills · 44 data)
  - "AC v2 … 验收条目；契约的最小单位" — `ARCHITECTURE.md` §8
- **卡 / 任务卡 / CARD-xx** (≈69 docs · 165 skills · 59 data)
  - "卡 | 自包含的任务单元；实现者的全部输入" — `ARCHITECTURE.md` §8; "卡 = 子 agent 的 prompt 载荷" — `skills/plan-cards/SKILL.md`
- **PR** (≈106 docs · 235 skills · 66 data) — GitHub pull request; `pr.number/url/size_class` in state.
- **skill** (≈93 docs · 286 skills · 35 data) — "二十八个 skill（九环 + 脊柱）" — `README.md`
- **图 / graph / 执行图** (≈68 docs) · **节点 / node** (≈29 docs · 8 skills · 8 data)
  - "节点带边界身份（reads / must_not_read / writes / authority），边带类型与守卫，回边带 loop:" — `ARCHITECTURE.md` §3.7
- **路由 / routing** (≈68 docs) · **层 / layer** (≈30 docs · 96 skills · 28 data) · **回流 / reflow** (≈17 docs)
  - "层 | card ⊂ plan ⊂ task ⊂ ontology ⊂ world：失败回流的坐标" — `ARCHITECTURE.md` §8
- **指纹 / fingerprint** (≈46 docs · 30 data) — "失败输出的稳定摘要；同指纹重复 = 无进展" — §8
- **信号 / signal** (≈19 docs · 100 skills · 55 data) — routing.yaml `signal:` closed set R01–R16
- **迹 / trace / 决策迹** (≈46 docs · 27 skills) · **账本 / ledger** (≈38 docs · 39 skills · 9 data)
  - "账本 | ledger.md，只增不删的失败与决定记录" ; "迹 | trace.jsonl：账本的类型边伴生" — §8
- **事件 / event** (≈14 docs · 20 skills) — "一行一个事件" — `ARCHITECTURE.md` §3.6 / proposal 方案 F
- **PSL** (≈65 docs) · **DOS** (≈40 docs) · **不变量 / invariant** (≈25 docs) — R0/R1 world-side artifacts
- **issue** (≈52 docs · 130 skills) — "issue 是 TASK 的雏形，不是契约本身" — `skills/issue/SKILL.md`
- **agent / 子 agent** (≈47 docs · 108 skills · 26 data) — "五个隔离子 agent" — `README.md`
- **脚本 / script** (≈42 docs · 166 skills) · **模板 / asset** (≈18 docs · 93 skills)
- **产物 / artifact** (≈28 docs · 102 skills) — "一个产物只有一个生产者" — `ARCHITECTURE.md` §2/§6
- **阶段 / stage** (≈23 docs · 33 skills · 95 data) — 15-value ORDER; graph.yaml `stage.*` nodes
- **轨道 / track** (≈26 docs) — "PSL 轨 / TASK 轨" — §8
- **逃逸缺陷 / escape defect** (≈25 docs · 42 skills) · **变更提案 / change proposal** (≈13 docs · 41 skills) ·
  **失败报告 / failure report** (≈14 docs · 11 skills) · **豁免 / waiver** (≈4 docs · 28 skills) · **锁 / lock** (≈22 docs · 39 skills)
- **隐藏集 / holdout** (≈13 docs · 37 skills) — "冻结 AC 的变体，实现者不可读；calibrate 的 holdout" — §8
- **三档 A/B/C** (≈16 docs · 53 skills) · **四态 DONE/FIX/SPEC_DRIFT/GAMING_RISK** (≈16 docs · 95 skills)
- **finding** (≈8 docs · 189 skills) · **verdict / 裁决** (≈26 docs · 120 skills) — acceptance-line vocabulary, thin in docs
- **假设台账 / assumption** (≈8 docs · 15 skills · 2 data)
- **run / slug / feature / 一次交付** (≈17 docs, noisy) — the lifecycle instance has no strong docs noun; `.sdlc/<slug>/` is how README names it;
  `metrics.py`/`tune.py` say "feature"; the three qanat-imported skills' 术语映射 say "Run（一次执行）= 一次 issue → PR 的交付，即 .sdlc/<slug>/ 一个 slug".

## Verbs (docs usage; subject → object)

- **人签 / sign** — 人 → 门 ("三道门只能人签"); `lock_done_when.py sign --by`
- **冻结 / freeze** — G2 → 契约 ("G2 判据冻结")
- **拆 / split** — 契约 → 卡 ("契约 → 自包含任务卡")
- **回流 / reflow · 归层 / route · 升级 / escalate** — 失败 → 层 ("失败按层回流而不是原地重试")
- **记账 / append** — 脚本 → 账本 ("账本只增不删")
- **派发 / dispatch · 扇出/扇入** — acceptance-fleet → 六审查 skill → meta-judge
- **实现 / implements** — commit → 卡 → AC → REQ (trace edge)
- **推导 / derive** — PSL → derived/ (dos-proposal / workflow / form-draft)
- **对账 / reconcile** — dos-proposal ↔ dos.yaml (human, G1 record)
- **归档 / archive** — Run → specs/<slug>/
- **提案 / propose** — retro/tune → 变更提案 / harness proposal (never auto-applied)

## Definitions found (gold tier)

`docs/ARCHITECTURE.md` §8 术语 is an explicit glossary:

> PSL 轨 / TASK 轨 — 形态未定（先建世界）/ 形态已定（直接进契约）的两条轨道；DOS 闭包失败是客观转轨触发
> AC v2 — kind: mechanical（observe/given/expect）或 kind: human（statement/judge/evidence）的验收条目；契约的最小单位
> 卡 — 自包含的任务单元；实现者的全部输入
> 层 — card ⊂ plan ⊂ task ⊂ ontology ⊂ world：失败回流的坐标
> 指纹 — 失败输出的稳定摘要；同指纹重复 = 无进展
> 三档 — A 机械（否决）/ B 结构（告警）/ C 判断（请求人）
> 两段锁 — G2 锁判据；L5 锁测试与 manifest
> 隐藏集 — 冻结 AC 的变体，实现者不可读；calibrate 的 holdout
> 账本 — ledger.md，只增不删的失败与决定记录
> static_only — 结构过审、脚本冒烟，但带/不带 skill 的行为对比未跑
> 环契约 — loops.yaml 一条：generator ≠ verifier、stop 四键、budget.ref、memory、trigger
> 图 — graph.yaml：节点（边界身份）+ 边（类型 / 守卫 / 环归属）；每个圈必须归属一个环
> 迹 — trace.jsonl：账本的类型边伴生；caused_by 由效果指向原因
> oscillation / plateau / impossible — 三种"再试也没用"：往复 / 不涨 / 契约下不可能——分别归 plan / plan / task
> hill_climb — 环改环的外环：trace → 参数提案 → 人开 PR

## Cross-references ("we use X not Y")

- "注意 qanat 的 verify_g1 / review_g2（机器闸 / 评审闸）与 sdlc 的 G1（世界裁决）/ G2（判据冻结）不是同一对门" — `design-notes.md` + 术语映射 in donewhen-extract / spec-compile / calibrate SKILL.md
- "因果边写成 caused_by（效果 → 原因）而不是文献的 caused——只增日志只能向后指" — `design-notes.md` 第三次整理
- "代码与文档里只用 sdlc 自己的词（环 / 层 / 门 / 指纹 / 账本 / 迹），业界词只出现在本文与 design-notes 的借鉴段" — proposal §6
- "命名：保留导入 skill 的原名（与上游一致、内部互相引用不断），新 skill 按产物命名" — `design-notes.md` 第二次整理 #3
- "'context graph' 只取决策迹一义，不建知识图谱" — `design-notes.md`
- "Run（一次执行）→ 一次 issue → PR 的交付，即 .sdlc/<slug>/ 一个 slug" ; "Territory → 一个 bounded context / 模块：dos.yaml 的 bounded_contexts.current_context" — 术语映射 tables (3 skills)
- "merge 是人类动作" (not called a 门) — `ARCHITECTURE.md` §5.3, `skills/pr/SKILL.md`

## Bounded Context hints

- 上半段·建世界 (R0 psl/psl-derive/G1) · 横切 X1 本体 (dos-extract/invariant-extract) · 下半段·收敛交付 (R2–R8) · X2 路由 · X3 度量 · X4 环与图的声明 — `docs/lifecycle.md`
- "脊柱 /sdlc 不做任何一环的活，只做五件事：持有状态、记账、路由失败、把三道门编译成不可跳过、把图与环声明成数据" — `ARCHITECTURE.md` §1
- 邻居（缺席不阻塞）：forge-teams / pdforge（实现执行器）；looper / done-when-pipeline / ratchet（上游源插件）；skill-evolve（读 gate.json fix_list）— `README.md`
- GitHub as external surface: issue / PR / review thread / merge / tag are `gh`-mediated and "人类动作" for merge/approve
- 验收线（六审查 skill + meta-judge + acceptance-fleet）has its own vocabulary (finding / severity P0–P3 / tier A/B/C / verdict PASS·BLOCK_MERGE·NEEDS_HUMAN / four-state) mapped onto sdlc only in each SKILL.md "Wiring in sdlc" section
