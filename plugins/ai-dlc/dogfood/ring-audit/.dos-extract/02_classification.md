# Classification (Judgment 1) — sdlc plugin

Buckets: `business` (candidate object) · `ui` · `impl` · `rule/behavior` · `value` (attribute/enum of an object) · `unclear`.
Code-side inventory (`01_inventory.md`) produced 0 nouns (inventory.py parses only class definitions in ts/js/py/go/rs/java/kt;
the plugin's object shapes live in YAML/JSON/Markdown). Classification therefore rests on the docs inventory (`01b`) plus
the data assets (`state.schema.json`, `graph.yaml`, `loops.yaml`, `routing.yaml`) read as the code side.

| Term | J1 steps | Bucket | Note |
|---|---|---|---|
| Run / slug / feature / 一次交付 | 1 yes (a delivery from issue to archive, describable off-screen) · 2 no suffix · 4 remove → product collapses | business | state.json is its sufficient statistic |
| 契约 / Contract / done_when.yaml | 1 yes · 4 no | business | "契约 v2 是全线的转轴" |
| AC (acceptance criterion) | 1 yes · 4 no, but no independent lifecycle from its Contract | value (part of Contract) | trace anchors `AC-*` reference it directly |
| REQ | 1 yes; lives in issue/spec.md, upstream of the contract | value (reference id) | owned by requirement intake (upstream ctx) |
| 卡 / Card / CARD-xx | 1 yes ("self-contained unit of work for a context-free agent") · 2 **verify_dos.py treats `Card` as UI suffix** | business | canonical name collides with the verifier — see 03_convergence |
| 门 / Gate G1 G2 G3 | 1 yes (a human checkpoint with a verdict record) · 4 no ("每一步…被一道只能人签的门挡住") | business | `state.schema.json` has `$defs/gate` |
| 闸 / 预门 / 自动门 (verify_*.py, lint_cards) | 3 verb-shaped ("check before X") | rule/behavior | edge `guard:` / prereqs; not a Gate |
| 账本 ledger.md / 迹 trace.jsonl | containers of records (Pattern 9) | composition | two projections of one event stream |
| 记录 / 事件 / event (ledger row, trace event) | 3 action-shaped, but event-sourced exception (trace.py why/impact, metrics.py query it) | business | kinds: init·set·advance·waiver·gate·card·fail·reflow·failure_report·archive·escape |
| 失败 / fail / 回流 / reflow | kind of event | value (Event.kind) | |
| 信号 / signal | closed enum (routing.yaml) | value (Event.signal) | |
| 层 / layer | closed enum card⊂plan⊂task⊂ontology⊂world | value (Event.layer, Run.counters) | routing also uses pseudo-layers `exception`, `g3`, `human_attribution`, `next_outer` |
| 指纹 / fingerprint | derived value (sha1 of evidence) | value | |
| 路由规则 R01–R16 | 3 rule-shaped | rule (constitution: routing exists; policy: table contents) | not an object |
| 预算 budgets 3/2/1 · thresholds 6/2–3/3/0.95 | J3: system unchanged if numbers change; README calls them "文献先验" | policy — excluded | tune's closed target set |
| 环 (九环 R0–R8 ring) | 4 remove → product still describable (graph.yaml has no ring, only `role`) | composition (grouping of Nodes by role) | 环 overload with loop |
| 环契约 / loop (loops.yaml) | 1 yes (a cycle contract: generator ≠ verifier, stop 4 keys) · 4 no (rule 11) | business | |
| 触发 trigger (triggers.yaml) | binding of a loop to a native primitive | value (Loop.trigger) | |
| 图 graph.yaml | container of nodes + edges | composition | |
| 节点 node (skill · agent · human · stage) | 1 yes (participant with boundary identity: reads/must_not_read/writes/authority) · 4 no (rule 11) | business | J1 caution: judgments.md flags "Node" as impl-leak elsewhere; here the graph is the declared domain |
| 边 edge (sequential·conditional·fan_out·fan_in·loop_back·interrupt·handoff) | relation between nodes | relationship | |
| skill / agent / script / asset | 2 framework constructs of Claude Code plugins (Pattern 7) | impl → represented as Node.kind (skill/agent) | scripts = Π primitives (edge guards); assets = templates |
| stage (15 in ORDER) | value of Run.stage; also Node.kind=stage | value | |
| track psl \| task | closed enum | value (Run.track) | |
| 锁 / .done_when.lock | no identity apart from its Contract; signature record | value (Contract.lock) | two stages g2 / l5 |
| 变更提案 change-proposal-*.md | artifact required to amend a locked Contract | composition / behavior (Event AMENDS Contract) | |
| 失败报告 failure report | artifact derived from a reflow Event + convergence | composition | G3 input |
| 豁免 waiver | value (stage, reason, at) + Event kind | value (Run.waivers) | |
| 假设台账 assumption | value (id, req, risk, signed_by, verify_at, status) | value (Run.assumptions) | |
| 逃逸缺陷 escape defect | Event kind + issue kind + escape-defects.md row | value (Event.kind=escape) | |
| 隐藏集 / holdout | variant set of frozen ACs, implementer-unreadable | value (Contract-derived, calibrate ☐3) | |
| 产物 / artifact | 4 too generic (Pattern 9 / "Item") | composition (Archive) | rules 1 & 5 expressed via Node.writes and Event |
| issue / PR / review thread / commit / tag | external GitHub objects; slim refs in state (issue.number, pr.number, merge.sha) | upstream context (GitHub) | |
| finding / verdict / four-state / tier | acceptance-line vocabulary; overlap with lifecycle = file:line + tier→veto | downstream context (evaluation) | mapped to Event signals in Wiring sections |
| PSL / DOS / invariant card / dos-proposal | R0/R1 world artifacts; Run.world holds paths | upstream context (world) | |
| Territory / MemoryAsset / R001 R002 (qanat terms) | imported vocabulary with explicit 术语映射 | synonyms → bounded context / Run / Contract / rules | not objects |
| 三档 A/B/C | classification of checks | value (Finding.tier in evaluation ctx) | |
| ratchet-log/iteration-NNN | acceptance iteration directory | composition (evaluation ctx) | |

## `unclear` resolved in `03_convergence.md`

- Gate: object vs Run property vs human Node → **object** (own `$defs`, own records, stable identity G1/G2/G3, rule 6/9).
- Node vs skill/agent: **Node** wins; skill/agent are kinds (Pattern 7 framework terms).
- Event vs Failure vs Ledger: **Event** wins (Pattern 8 kinds; Pattern 9 container → composition).
- Ring vs Loop (both 环): **two things**; Ring → composition, Loop → object.
- Card: **object**, renamed **WorkUnit** for the verifier (see convergence + Q001).
