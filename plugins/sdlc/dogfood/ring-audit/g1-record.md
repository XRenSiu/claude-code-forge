# G1 世界裁决记录 — sdlc-ring-audit

> 唯一能拦住"正确的错误"的门。人裁决 agent 推出来的世界。日历筛选器那类错误只能在这里拦，到验收再发现贵一个数量级。
> 输入：推导产物（DOS 提案 / Workflow / 形态草案）+ 分歧集。输出：三问答案 · 归因 · 决定 · 签字版形态草案哈希。

**日期**: 2026-09-05　**裁决人**: g1-judge (delegated_agent; authorization: user instruction 2026-09-05 "需要人审核的地方，请你弄一个子agent代替我审核一下")　**PSL**: plugins/sdlc/dogfood/ring-audit/PSL-sdlc-ring-audit.md　**形态草案**: plugins/sdlc/dogfood/ring-audit/derived/form-draft.md

> 签字性质：**代签**。签字人不是审计者、不是推导者，全新上下文只读 PSL / derived / dos.yaml / ARCHITECTURE。
> 审阅稿指纹（不是签字版，供回溯）：form-draft.md `265412e0…abad0d` · PSL `b64f81e8…8a2ad7` · dos-proposal.yaml `bdc17872…0522e0` · divergence.md `45f9e306…67d837`。
> 机械预门：本次重跑 `verify_derived.py … --n 3` → verdict PASS，23 决策，17 条规律被引 14 条，flag 2（PSL-008/009/012 未引 · needs_semantic_review）。

## 三问（每问必答，不允许"差不多"）

### 1. 实体是不是我认的那些？

| 实体 | 判 | 理由 / 该是什么 |
|---|---|---|
| Ring（环） | ✓ | 聚合根对。脊柱按 `id=spine` 的一条 Ring 处理（回答欠定第 8 条）。补两点：(a) Part 的 Ring 归属**从 graph.yaml 的 `Node.role` 经 dos.yaml `composition.Ring` 的映射推出**（world→R0 … learning→R8，orchestrator→spine），不手填，证据写 graph.yaml 行号；(b) 三道人签门归它检的 Artifact 所在的环（G1→R0、G2→R2、G3→R6，与 ARCHITECTURE §1 表一致），不归 spine——spine 上的 Part 是 `sdlc` skill 与 graph/loops/routing/triggers 四个数据资产。 |
| Part（配件） | ✓ | 单位对：用户原话是"配件或者 skill"，比 skill 宽。但草案没定粒度，补一条裁决：**skill 目录下的脚本是该 skill 的 Gate（`checked_by`）或 Capability，不是独立 Part**；Part = ARCHITECTURE §1 表 skill 列 / 门闸列（人签门）里出现的名字 + agents/*.md + 脊柱四个数据资产。`kind` 枚举去掉 `script`，保留 `skill / agent / asset / human_gate`。现状对账显示 Part ≠ Node：`pr-reviewer.md` 有文件无节点、四个数据资产无节点、stage 节点不是 Part。 |
| Gap（缺口） | ✓（修一处） | 值对象对，但 dos-proposal 给它 `state: identified_no_part \| has_part` 又说"不可变"——带可变状态的不是值对象。裁：`state` **不存储，派生**（= 是否存在 `Part FILLS Gap` 边）。`necessity` 与 `deletion_test` 保留。Gap 的三个来源要写明：lifecycle 空白行、本次新识别、**dos.yaml 里 `enforced_by ∈ {user_workflow, not_enforced}` 的规则**（R001/R008/R010/R017——声明了却没脚本检，就是 Control 缺口）。 |
| Artifact（产物） | ✓ | 对。身份 = graph.yaml `Node.writes` 的路径模式 ∪ ARCHITECTURE §1 产物列。现状 Q006 已指出 done_when.yaml 有两个写者、卡文件三个、github:pr 两个——见三问 2 的 P-3。 |
| Gate（闸/门） | ✓（词有冲突） | 对象可以合一，但现状本体明说"机械预门**不是** Gate，是边守卫"，而应然把脚本也叫 Gate。中文 闸/门 能分，英文 Gate 不能。裁：保留 `kind: script \| human`，报告与 audit.yaml **禁止把 script 渲染成"门"**，用"闸"；`kind=human` 仅 G1/G2/G3。 |
| Finding（审计判定） | **✗** | 两处错。(a) **名字撞车**：sdlc 已有 Finding——R6 六审查 skill 与 pr-review 的产物 `findings.yaml`（severity / file:line / tier），本次审计的 R6 行就要把它列为 Artifact；同一份报告里 Finding 既是审计单位又是被审产物名，必错。该是 **Assessment（审计判定）**。(b) **四维错一维**：`missing` 对 33 个真实 Part 恒为"不缺"，只对 lifecycle 空白非空——而空白在 dos-proposal 里同时是 Part 的 `空白` 态和 Gap 的 `identified_no_part`，双重表示。用户的"缺少"问的是**环上缺什么**，不是**这个配件缺不缺**。该是三维 `needed / implemented / naming`，"缺少"由 Ring.missing（Gap 列表）回答，报告可把 Gap 渲染成环表末尾带"（缺少）"标记的行。四个词都还有去处：缺少→Ring.missing，需要→needed，实现→implemented，名字→naming。 |
| Loop（环契约） | ✓ | 只引用不复述，对。 |

### 2. 有没有技术上对、产品上错？

| # | 决策 | 为什么照字面对、产品上错 | 归因 |
|---|---|---|---|
| P-1 | F-03 "adopted 且与上游同名的 Part 判 `fits`，即使名字不是产物名" | 收编的 skill 有 16 个（looper 3、qanat 3、done-when-pipeline 9、ratchet 1）。这条把 16/28 个 skill 的"名字合适"直接判合适，用户问的恰是这个。PSL Workflow φ 写的是"先判来路，**再**判贴合：名字 = 产物名或位置名 → 合适"，来路只决定**改不改**，不决定**合不合适**。`donewhen-extract` 产 done_when.yaml 是贴合；`calibrate` 产 calibration_report 勉强；`ratchet` 产什么？——这些才是用户要的答案。 | **推错了**（PSL-014 本身没错） |
| P-2 | F-01/F-02/F-13 每 Part 四维、`missing` 一维 | 见三问 1 Finding (b)。33 行同值的一列 + 空白双重表示。 | **规律错了**（PSL Domain Model / Personas / State Machine） |
| P-3 | F-05 "同一 Artifact 名出现两个 producer → 两者都 merge_candidate" | 机械执行会把 `implement` / `card-implementer` / `ratchet` 判成合并候选——它们是同一阶段的**条件替代**（graph.yaml conditional 边），不是"争"。PSL-001 用的字是"争"，已含竞争义。但 `donewhen-extract` / `acceptance-spec` 都写 done_when.yaml 且形状不同（现状 Q008）——这个**该**触发。 | **推错了**：加"同阶段条件替代分支不算第二生产者" |
| P-4 | F-08 "`loop: null` 必附 `loop_reason`" | 六个环覆盖不到十个节点，其余二十多个 Part 都要写一句"不在任何圈里"。PSL-011 说每个**圈**有环契约，没说每个 Part。 | **推错了**：仅当 Part 是 graph.yaml loop_back 端点或 Loop 的 generator/verifier 时 null 需要理由 |
| P-5 | Finding 命名 | 见三问 1。 | **规律错了**（Domain Model 命名） |
| P-6 | 整体形式化程度 | 33 Part × 3 维 × (≥1 PSL-ID + ≥1 证据) ≈ 100 格。重，但这正是 PSL Vision 要的"不是 `ls`"，且作者自己的原则是"每个产物被脚本检"。**不否决**；只要求人读的报告一 Part 一行、PSL-ID 做脚注，机器读的 audit.yaml 才带全字段。 | 接受，渲染要求 |

### 3. 每条形态决策从哪条规律推出来的？

`verify_derived.py` 已 exit 0：23 条决策每条至少一个 PSL-ID，无假 ID。**装饰性引用**（引了但推不出来）：

- F-10 ← PSL-011（"图与环是数据"推不出"报告按 Ring 分节"）。真正来源是 PSL **UI Contract 第一条**——它没有编号，推导者只能借最近的编号规律。
- F-13 ← PSL-004（"预算与终止由脚本强制"推不出检查脚本的谓词集）。PSL-015 才是；PSL-004 是凑数。
- F-12 ← PSL-011（弱，同上）。
- 其余引用成立。**根因是契约级的**：PSL 的 UI Contract / Acceptance / Design Principles 三层都承重、都没编号，PSL-ID 硬约束把推导者逼去借规律。见末节摩擦 5。

## 分歧集逐条回应（分歧集非空时必填）

| # | 分歧 | 回应 | 归因 |
|---|---|---|---|
| D-1 | implemented 态数 | 三态 `declared / compiled / verified`；`verified` 附 `calibrated: bool`（PSL-007）；**`空白` 不是 Part 的态**，空白是 Gap（identified_no_part, source=lifecycle_blank）。临时取向成立，但 PSL 自相矛盾必须改（Domain Model 三态 vs State Machine 五态）。 | `rule_error`（PSL Domain Model + State Machine Part 行 → E-1/E-3） |
| D-2 | Gap 在 audit.yaml 的落位 | 每 Ring 自己的 `missing` 键；Domain Model 加 "Ring 暴露 0..n Gap"。三版都各自发明了这条关系，正是 PSL 欠定的证据。 | `rule_error`（Domain Model 关联段 → E-2） |
| D-3 | 无 Gate 检的 Artifact 的后果 | 采 v3（producer 的 implemented ≤ declared，evidence `no_gate`）**并**加 v2（该 Artifact 浮现为一条 Control 缺口进所在 Ring 的 `missing`，source=newly_identified）。两者都是 PSL-010 对"编译"的定义（有 verify 脚本或被门挡）+ PSL-015/016 的直接推论；推导者请求"补 Workflow φ"不必要。 | `accepted`（扩展；PSL 不动） |
| D-4 | 两类"缺少"是否分标签 | 分：`source ∈ {lifecycle_blank, newly_identified, unenforced_rule}`（第三个来源见三问 1 Gap 行）。Mental Model 已经把两种来源分开写了，标签是忠实推导。 | `accepted`（E-12 只加第三来源一句） |
| D-5 | 检查脚本自校准是否证据必需项 | 采 v3：同一运行里没跑"删任一 Ring 的变体 → exit 1"的 exit 0 标 `uncalibrated`，不算证据。这是 /calibrate 的 mutation 思想缩到一个脚本上，代价一次运行，和 PSL-007 一致。 | `accepted` |
| D-7 | audit.yaml 顶层形状 | `rings:` 列表，每项 `{id, question, parts[], missing[]}`；`parts[].assessment{needed, implemented, naming}`（按 E-3/E-4 改名减维）。 | `accepted` |
| D-8 | Gate 与 Part / Finding 的关系 | 加 `Gate(kind=human) ADJUDICATES Assessment 1:N`，**仅 G3**（或报告的人审）；**G1 裁决的是形态，不是判定**——G1 在 issue 之前，那时一条审计判定都还不存在。不加 `Part CARRIES Gate`（Gate 检产物不检配件，推导者的理由成立）。 | `rule_error`（PSL State Machine Finding 行写 "G1 / G3" 错 → E-5） |

### PSL 欠定 12 条的去向

| 欠定项 | 去向 | 裁决 |
|---|---|---|
| Proposal（提案） | open_questions | 是 Assessment.disposition 的投影，不建实体；若日后要 owner / 状态再升。 |
| Evidence（证据） | **进 Domain Model（属性类型）** | 值类型 `{kind ∈ {file, gate_json, smoke, run_record}, ref}`——State Machine 已列这四种来源，给个形状让检查脚本不只检非空。不算第 8 个对象。 |
| Signer / Authorization | **进 Domain Model（Gate 属性）** | `signer / signer_kind ∈ {human, delegated_agent} / authorization_ref`。本次就是代签，承重。注意现状 `sdlc_state.py gate` 无条件写 `decided_by human:<by>`——见摩擦 1。 |
| Run（本次运行） | **不建模，只引用** | Run 是现状本体的聚合根（上游 bounded context）。审计的 `run_evidence` 引用 sdlc Run 的 slug / state.json / ledger，不自己建 Run。v3 的跨运行指纹 F-23 不进。 |
| skill 源码问题 | **不建模，只引用** | 它们是上述 Run 账本里的 Event（skill-issues.md 是投影）；run_evidence 给路径。不是 Part 的 implemented 逆向流转证据——被审文件没变。 |
| Ring.question | **进 Domain Model** | 字符串属性，取 ARCHITECTURE §1 表"问题"列。 |
| Gap 反向基数 | **进 Domain Model** | `Part FILLS Gap N:N`——六个审查 skill 共填一个 Judgment 缺口是常态。 |
| 脊柱是否是 Ring | **改 PSL Domain Model** | 是，`id=spine`；人签门不归 spine（见三问 1 Ring 行）。 |
| Gate 与 Loop.verifier | **现在回答，不留 open** | 不同物：Loop.verifier 是一个 Part（评估者节点）在环内判 generator 的产物；Gate 检 Artifact。verifier 若恰是脚本，它同时也是一道闸——两个角色一个实体，本体里各自引用即可。 |
| PSL 规律是否实体 | 舍弃 | 元层。同意推导者。 |
| F-93 验收挂钩弱 | **补 PSL Acceptance** | A8："问'审计动过被审目录吗' → 返回被审目录 git diff 为空 + skill-issues.md 路径"。 |
| 未引用的 PSL-008/009/012 | **保留，不删不补决策** | 三条约束的是**审计内容**不是**审计形态**：`sdlc_state.py fail` 填哪个 Control 缺口 ← PSL-008；`release` ← PSL-009；routing v2 收敛检测 ← PSL-012。它们会出现在 Assessment.needed.psl_ids 里，不会出现在 form-draft 里。verify_derived 的 flag 把两层规律混了——摩擦 4。规律索引加一句分层说明（E-11）。 |

## 应然 ↔ 现状对账（X1，ARCHITECTURE §2 说这件事在 G1 记录里做）

| 应然（dos-proposal） | 现状（dos.yaml） | 关系 | 对审计形态的后果 |
|---|---|---|---|
| Ring | `composition.Ring`：Node.role 分组，"docs-only view"，graph.yaml 无 ring 字段 | 名异实同（对象 vs 视图） | Part 的 Ring 归属从 Node.role 派生并给证据行；ARCHITECTURE §1 与 Node.role 已知不一致处（gate / orchestrator vs 脊柱，现状 Q002）直接成为 Assessment，不在审计里调和。 |
| Part | Node（kind skill / agent / human） | 名异实同 + 只在应然一侧的部分 | Part ⊋ Node∖stage：`pr-reviewer.md` 有文件无节点（现状 I-16 也抓到）、四个数据资产无节点；stage 节点不是 Part。审计必须显式列出"无节点的 Part"——这本身是 R6 / 脊柱的一条 Assessment。 |
| Gap | —（散在 ARCHITECTURE §7 / lifecycle 制品映射的"空白"行、gate.json fix_list、dos.yaml `enforced_by ≠ system` 的规则） | 只在应然 | Gap 的三个证据来源如上；lifecycle_blank 的 evidence 就是那一行；`user_workflow / not_enforced` 规则是候选 Control 缺口——现状自己已经诚实标了，审计照抄即可。 |
| Artifact | `Node.writes` / `Run.artifacts`（属性，非对象） | 名异实同（对象 vs 属性） | 身份取 writes 的路径模式。现状 Q006：done_when.yaml ×2（该触发 merge_candidate，对应 Q008）、卡文件 ×3 与 github:pr ×2（同阶段条件替代，**不该**触发）→ F-05 必须加豁免（P-3）。 |
| Gate | Gate（仅 g1/g2/g3 人签）；verify_*.py 是"边守卫，**不是** Gate" | 实质冲突（词） | 应然合一可以，但报告禁止把脚本叫"门"。现状 `sdlc_state.py gate` 只有 `--by`，没有 signer_kind / authorization：**本次代签会被记成 `human:g1-judge`**——现状缺口，进 skill-issues。 |
| Finding → Assessment | —；且与评估上下文的 Finding（findings.yaml：severity / tier / confidence）撞名，现状明说那个 Finding 不在本体里 | 只在应然 + 名冲突 | 改名 Assessment（E-4）。 |
| Loop | Loop（loops.yaml） | 一致 | Part.loop = Node.loop（generator 侧）∪ Loop.verifier；`null` 无需理由除非是 loop_back 端点（P-4）。 |

## Open Questions 逐条（承重空槽）

| PSL Open Question | 裁 | 内容 |
|---|---|---|
| "必要"的裁决标准：deletion 测试 vs 流水线闭合 | **现在回答** | 单一标准 = deletion 测试，但**在生命周期高度上读**："撤掉它，这条流水线会不会产出错的或不可验证的东西"，而不是"引擎会不会拒绝往下走"。`psl-derive` 的例子：撤掉它引擎照样推导，但 G1 没有落盘产物可裁，世界层错误一路漏到验收——这就是"会做错"，只是延迟。所以"闭合所需"不是第二标准，是 deletion 失败的一种证据。F-21 的 `contested` 保留给两者读完仍冲突的残余。 |
| 命名建议是否落地 | **现在回答** | 本次不改名（design-notes 决定不动，PSL-014）。但**贴合要对所有 Part 诚实判**（P-1），misfit 的 disposition=issue，让作者拿到一张"哪些名字别扭 + 建议名"的表后**一次**决定要不要开重命名变更提案。`rename: false` 常量保留。 |
| 审计报告的主读者 | **现在回答** | 插件作者（要提案）。使用者的一句话留 README 既有表。报告人读版一 Part 一行（P-6）。 |
| "缺少"的配件是否本次补齐 | **现在回答** | 只登记 + issue 草稿，不实现。用户原话是"检查"，不是"补齐"；且 F-93 要求被审目录 git diff 为空。 |
| 外部证据的替代品 | **现在回答（有条件接受）** | 接受"审计脚本对报告的机械检查 + 代签 agent 的独立读"充当，**前提**：(a) run_evidence 里标 `evidence_kind: substitute`，不得渲染成用户验证；(b) 检查脚本必须跑 D-5 的删环变体（脚本自己的校准）；(c) 仅对本次 dogfood 自审有效，不成为 PSL 轨的通例。 |

## 归因（否决时必填；喂 X2 世界层回流计数）

- [x] **推错了** → 重推（PSL 不动）——P-1、P-3、P-4、三问 3 的装饰引用、Gap.state 派生、Ring 归属派生
- [x] **规律错了** → 改 PSL（记 PSL-ID）——**主归因**，世界层计数 +1：
  - E-1 Domain Model "Finding" 行 implemented 三态 ↔ State Machine Part 行五态 自相矛盾 → 统一三态 + `calibrated` 附注；`空白` 移出 Part 态（D-1）
  - E-2 Domain Model 关联段加 "Ring 暴露 0..n Gap"、"Part 填 Gap N:N"；Ring 加 `question` 属性（D-2、欠定 6/7）
  - E-3 Domain Model / Personas / Workflow φ"对的结果" / UI Contract / γ done_when：Finding 四维 → 三维，"缺少"由 Ring 级 Gap 回答（三问 1、P-2）
  - E-4 Domain Model：Finding 改名 **Assessment（审计判定）**，避开 R6 的 findings.yaml（三问 1、P-5）
  - E-5 State Machine Finding 行 "已裁决（G1 / G3 …）" → "已裁决（G3 或报告人审）"；关联段加 "Gate(kind=human) 裁决 0..n Assessment"（D-8）
  - E-6 Domain Model：脊柱按 `id=spine` 的 Ring；人签门归其所检 Artifact 的环；Part 粒度与 `kind` 枚举（去 script）（欠定 8、三问 1 Part 行）
  - E-7 Domain Model：Gate 加 `signer / signer_kind / authorization_ref`；Evidence 值类型 `{kind, ref}`（欠定 2/3）
  - E-8 Acceptance 加 A8（审计动过被审目录吗 → git diff 为空）（欠定 11）
  - E-9 来路标注修正：`[elicit:物料 lifecycle.md §7]` → lifecycle.md 无 §7，实为 lifecycle.md 制品映射表 + ARCHITECTURE.md §7
  - E-10 Domain Model 加"不建模、只引用"一行：Run / skill 源码问题 / PSL 规律（欠定 4/5/10）
  - E-11 规律索引头加一句：规律分"约束形态"与"约束内容"两层，PSL-008/009/012 属后者，由 Assessment 引用（欠定 12）
  - E-12 Mental Model "缺少有两种" → 三种，加 dos.yaml `enforced_by ≠ system` 的规则（对账后果）

## 决定

- [ ] **PASS** — 签字版形态草案 sha256: `（未签）`
- [x] **REJECT** — 回退目标: **改 PSL（E-1…E-12）→ 重推 → G1 第二轮**

说明：
- 草案约 85% 站得住——14 条一致决策全部保留，7 条分歧里 4 条 accepted。否决不是因为它差，是因为 **PSL 本身要改**（自相矛盾一处、欠定四处、命名一处），而 psl-derive 契约写明"规律错了 → 改 PSL 再推"，G1 席上手改草案等于 G1 兼任推导者，且会让世界层计数漏记一次真实的世界层错误。
- 重推建议：PSL 改完后 **n=1 定向重推可接受**（divergence.md 按契约写 `n: 1 — 未做分歧检验`，理由：7 条分歧已在本记录逐条裁定，重推的输入是"PSL v2 + 本记录的裁决"）；若主会话坚持 n=3 也行，但预期分歧应收敛到 ≤ 2。
- 第二轮 G1 只需核对：E-1…E-12 是否进了 PSL；P-1/P-3/P-4 是否在草案里改掉；三维 Assessment + Ring.missing 的形状；装饰引用是否消失。可由同一代签 agent 做，预计一轮。
- 状态机记录建议：`sdlc_state.py gate g1 --verdict reject --attribution rule_error --by g1-judge --record plugins/sdlc/dogfood/ring-audit/g1-record.md`，并在账本 note 里写明 `signer_kind=delegated_agent`（脚本本身没有这个槽，见摩擦 1）。

## 外部证据（PSL 轨强制，至少一项）

- [x] 原型走查 / 用户验证记录: **未做，原因：自审，无外部用户，无原型。** 替代品：(1) `verify_derived.py` 机械重跑 exit 0（本记录头部）；(2) 本记录——一次全新上下文、非推导者、非审计者的独立读，抓到分歧集之外的三处问题（P-1、P-2/P-5、P-3）。**接受为替代**，仅限本次 dogfood，且 run_evidence 必须标 `substitute`（见 Open Questions 末条的三个前提）。

## 本次 G1 的 dogfood 摩擦（进 skill-issues.md 的候选）

1. `sdlc_state.py gate` 只有 `--by`，无 `--signer-kind` / `--authorization`；trace 边无条件写 `decided_by human:<by>`。代签会被记成人签——与 PSL-006 / 形态 F-15"不得渲染为人签"直接冲突。
2. `g1_record.md` 模板无 signer_kind / authorization 槽（表头只有"裁决人"）。
3. 模板无"Open Questions 逐条"节（I-03 已记）、无"应然↔现状对账"节——但 ARCHITECTURE §2 与 dos-extract 接线都说 X1 对账在 G1 记录里做。两节本次手加。
4. `verify_derived.py` 的"未引用规律"flag 把约束形态的规律与约束内容的规律混为一谈，会催推导者硬凑引用。
5. PSL-ID 硬约束没有办法引用 UI Contract / Acceptance / Design Principles 条目 → 装饰性引用（三问 3）。建议：允许 `← UI-1` / `← A3` 这类锚，或要求 /psl 给这三层也编号。
6. 模板决定只有 PASS / REJECT；对"85% 对、PSL 要小改"的草案，契约要求全量重推。建议契约明写"定向重推（n=1 + 分歧裁决作为输入）"是合法回退。
7. 归因两个复选框看着互斥，实际常同时成立；模板应说明"可多选，主归因喂计数"。

---

## G1 第二轮（2026-09-05）

**日期**: 2026-09-05　**裁决人**: g1-judge　**签字性质**: delegated_agent（authorization: user instruction 2026-09-05 "需要人审核的地方，请你弄一个子agent代替我审核一下"；允许到：G1 裁决与记录，不含改 PSL / 改草案）　**PSL**: plugins/sdlc/dogfood/ring-audit/PSL-sdlc-ring-audit.md（v2，sha256 `4d84dcee985087fa2fcfb6babdbe0cd902b9a6419609ca8f32b5bc60ef85f86a`，本地复算一致）　**形态草案**: plugins/sdlc/dogfood/ring-audit/derived/form-draft.md（审阅稿 sha256 `13859dd63fffaa4bd59e34390f79d2cd3dc4df1b5a826584a356dee33ceb96f2`，本地复算一致；**未签**）

> 输入：PSL v2 + n=1 定向重推（derived/，round1 归档在 derived/round1/）+ divergence.md 的 38 行"裁决 → 落点"表。
> 机械预门：本地重跑 `verify_derived.py … --n 1` → PASS，27 决策全部带 PSL-ID，7 对象均为 PSL v2 Domain Model 名，唯一 flag 是预期中的 PSL-008/009/012 未引（内容层）。
> 状态核对：`.sdlc/sdlc-ring-audit/state.json` gates.g1 = reject / rule_error / signer_kind=delegated_agent / authorization 在场；counters.world = 1。第一轮摩擦 1、2 已修（`--signer-kind` / `--authorization` 落地，模板加三节），账本记为 deviation。

### 三问复核

1. **实体**：7 个对象全部是 PSL v2 的名字，Assessment 三维 ✓，Gap 值对象且状态派生（composition.GapState）✓，Evidence 值类型 ✓，Ring.question ✓，Gate 三元组 ✓。**一处未覆盖**：graph.yaml 有 5 个 kind=human 节点（g1 / g2 / g3 / merge / harness-review），F-08 与 dos-proposal 的 `human_gate` 只说了三道门；`human.merge`（R7，"合并是人类动作"）与 `human.harness-review`（R8，tune 提案经人 PR）在四个 kind 里无处可放，而第一轮对账已裁"Part ⊋ Node∖stage"。→ N-1。
2. **技术对产品错**：第一轮的 P-1…P-6 全部落地，无新的产品层错误。两处**精度**问题会让检查脚本或裁决落到错的对象上：(a) F-05 的"同阶段"定义与 graph.yaml 不符（见残余 2）；(b) F-07 的 `report_review` 与同一份 dos-proposal 里 Gate.kind 的"human 仅 G1/G2/G3"自相矛盾（见残余 1）。另一处**建议**：F-03 "名字 = 独占 Artifact 的名或位置名"若按字面相等执行，`calibrate` / `dos-extract` / `retro` 这类词干相同的名字会被判 misfit，naming 列反过来变噪声；应写"同词干或同义即 fits，不要求字面相等"。
3. **引用**：装饰性引用已消失或变得可辩护——F-10 改引 PSL-017（缺少行）+ PSL-010（implemented 列）并注 via UI-1；F-12 只引 PSL-015 并注 via UI-2；F-13 保留 PSL-004 但补了它真正推出的子句（审计完成由 exit 码给出，审计者不自宣），成立。十条 `(via UI-n / A-n / DP-n)` 接受为权宜，根治仍是 verifier 放开锚格式（skill-issues I-19）。

### E / P / D → 是否落地

| 项 | 落地 | 落点 | 备注 |
|---|---|---|---|
| E-1 三态 + calibrated；空白移出 Part 态 | 是 | PSL Mental Model / State Machine；F-02 | — |
| E-2 Ring 暴露 Gap；Part 填 Gap N:N；Ring.question | 是 | PSL 关联段；F-04 / F-11 / F-12 | — |
| E-3 三维 + Ring.missing | 是 | PSL Domain Model / UI-1 / γ；F-01 / F-10 / F-11 / F-13 | — |
| E-4 Finding → Assessment | 是 | PSL；F-01 / F-95 | — |
| E-5 只 G3 裁 Assessment；G1 不裁 | 是，**过头** | PSL State Machine / 关联段；F-07 | 我写的"G3 或报告人审"被推成两道门 → 残余 1 |
| E-6 spine = Ring；门归所检产物的环；kind 去 script | 是，**漏两节点** | PSL Domain Model；F-08 | human.merge / harness-review 无 kind → N-1 |
| E-7 Gate 签字三元组；Evidence 值类型 | 是 | PSL；F-01 / F-07 / F-13 / F-15 | — |
| E-8 Acceptance A8 | 是 | PSL；F-93、验收挂钩 | — |
| E-9 来路标注修正 | 是 | PSL 头注 / Mental Model / PSL-017 | — |
| E-10 Run / skill 源码问题 / 规律 不建模只引用 | 是 | PSL Domain Model；F-15 | — |
| E-11 规律分形态层 / 内容层 | 是 | PSL 规律索引头注；草案头注 | verify_derived 的 flag 属预期 |
| E-12 缺少三种来源 | 是 | PSL Mental Model / PSL-017；F-04 / F-11 | — |
| P-1 收编不免检 | 是 | PSL-014；F-03 / F-23 | 建议放宽字面相等（见三问 2） |
| P-2 missing 维删除 | 是 | 同 E-3 | — |
| P-3 同阶段条件替代豁免 | 是，**定义错** | PSL-001；F-05 / F-13 / F-20 | 残余 2 |
| P-4 loop_reason 只对圈端点 | 是 | PSL-011；F-09 | — |
| P-5 Finding 命名 | 是 | 同 E-4 | — |
| P-6 人读一行、机器读全字段 | 是 | UI-1 / UI-2；F-10 / F-12 | — |
| D-1 / D-2 / D-8（rule_error 三条） | 是 | F-02 / F-04+F-11 / F-07 | D-8 见残余 1 |
| D-3 双后果 · D-4 标签 · D-5 uncalibrated · D-7 rings 列表 | 是 | F-06 / F-11 / F-14 / F-12 | — |
| 对账后果（Ring 派生、Part ⊋ Node、Q006 触发范围、闸不叫门） | 是 | F-08 / F-24 / F-05+F-20 / F-94 | F-24 是新增且正确 |
| Open Q 五条答案 | 是 | F-21 / F-03+F-16 / F-10 / F-11+F-92 / F-14+F-15 | — |

### 残余两问的裁决

**残余 1 · 报告人审是不是一道 Gate（`report_review`）**：**不是**。审计报告是本次 Run 的交付物，对它的人审就是 G3（例外复核 human AC："这个 Part 的 Gap 归类对不对"正是 human AC）。报告合入之后再推翻某条 Assessment，是逃逸缺陷（`/issue --escape`）触发下一次审计 Run 的新 Assessment 带 `supersedes`，不是第四道门。→ F-07 `adjudications[].gate` 只取 `G3`；dos-proposal Assessment.adjudications 枚举、R010、ADJUDICATES 描述同步去掉 report_review。PSL v2 里我自己写的"G3 或报告人审"读作同位语，建议下次触 PSL 时改成"G3（报告人审即 G3 的内容）"——去掉一个选项不会造成推导错误，**不阻塞**。归因：derivation_error（推导把同位语推成了并列）。

**残余 2 · "同阶段"的判据来源**：推导者定义为"graph.yaml 从同一 stage 节点出发的 conditional 边"。**对照数据不成立**：实现侧的两条 conditional 边是 `implement → agent.card-implementer` 与 `implement → ratchet`，起点是 skill 节点不是 stage 节点；契约侧 `stage.contract` 的 handled_by 是 [donewhen-extract, acceptance-spec]，两者之间**没有任何 conditional 边**（各自 interrupt 到 human.g2）。按字面执行，卡文件三写者不会被豁免（错），done_when.yaml 两写者不会被豁免（对，但是碰巧）。裁：**同阶段条件替代 = 同一 `stage.<x>` 节点 `handled_by` 里的多个 Part，且它们之间由 graph.yaml `conditional` 边（`when` 守卫）选择执行者，且产出同一 schema 的 Artifact**。三个条件缺一不算替代：implement / card-implementer / ratchet 三条件全满足 → 豁免；donewhen-extract / acceptance-spec 只满足第一条（无 conditional 边、v1 ≠ v2 需转换器）→ 触发 merge_candidate，与现状 Q008 一致。数据源就是 graph.yaml（stage 列表虽有两源，`graph check` 已断言相等）。→ F-05 括注与 dos-proposal Artifact.alternatives_of 描述按此改写。PSL-001 不需要改；建议下次触 PSL 时在 Workflow φ 补这一句，**不阻塞**。归因：derivation_error。

**N-1（本轮新发现）· 两个非门人节点**：`human_gate` kind 覆盖 graph.yaml 全部 5 个 kind=human 节点，其中持有 Gate 对象的三个归所检 Artifact 的环（G1→R0、G2→R2、G3→R6），`human.merge` → R7、`human.harness-review` → R8（ARCHITECTURE §1 表 R7 门闸列"merge / push tag 是人类动作"、R8 "提案不自动生效"）；后两者 `ring_evidence` 写 graph.yaml 行号，Assessment.needed 照常做 deletion 测试，现状 Q004（它们算不算门）就是它们的一条 Assessment。→ F-08 加一句；dos-proposal Part.kind 描述同步。PSL Domain Model 的 kind 枚举不变，不阻塞。归因：derivation_error。

### 归因

- [x] **推错了** → 重推（PSL 不动）——残余 1、残余 2、N-1 三处，均为 F-05 / F-07 / F-08 及 dos-proposal 对应行的局部改写
- [ ] **规律错了** → 改 PSL

### 决定

- [ ] **PASS** — 签字版形态草案 sha256: `（未签）`
- [x] **REJECT** — 回退目标: **重推（定向，n=1，PSL v2 不动）→ G1 第三轮**

说明：
- 三处都不涉及产品形状，但两处会让检查脚本的豁免谓词落到错的对象上（残余 2）或让同一份本体自相矛盾（残余 1），签字版 = 功能文档，不能签一份对数据说错话的文档。第三轮预期是 **diff 核对**：若 round3 的 form-draft 相对 round2 只改了 F-05 / F-07 / F-08（+ 头注、F-03 可选放宽）且内容与上面三段一致，G1 第三轮直接签 sha。
- 需落地的最小改动：
  1. F-07：`gate: G3 | report_review` → `gate: G3`；dos-proposal adjudications 枚举 / R010 / ADJUDICATES 描述同步。
  2. F-05：括注改为"同一 stage 节点 handled_by 内、由 conditional 边选执行者、且产出同一 schema 的 Artifact 的多个 Part；三条件缺一不算替代"；dos-proposal Artifact.alternatives_of 同步；F-20 的例子已正确，不动。
  3. F-08：加"human_gate 覆盖 graph.yaml 全部 kind=human 节点；human.merge → R7，human.harness-review → R8，ring_evidence 写行号"；dos-proposal Part.kind 描述同步。
  4. （建议，不阻塞）F-03：fit 判据加"同词干或同义即 fits，不要求字面相等"。
- 状态机记录建议：`gate g1 --verdict reject --attribution derivation_error --by g1-judge --signer-kind delegated_agent --authorization "…" --record <本文件>`。**注意**：`sdlc_state.py` 对任何 g1 reject 都 `counters.world += 1`，而 psl-derive 失败机制与 dos.yaml Gate.attribution 都说只有 rule_error 计世界层——本次 derivation_error 会把 world 计成 2。见下方摩擦 a；retro 读 attribution 字段可纠正。

### 外部证据

- [x] 原型走查 / 用户验证记录: **未做，原因同第一轮（自审）。** 替代品：`verify_derived.py --n 1` 本地重跑 exit 0；本记录的独立复读（对照 graph.yaml 原始边数据核验了残余 2，对照 dos-proposal 内部一致性核验了残余 1）。接受为替代，条件同第一轮（run_evidence 标 substitute）。

### 第二轮 dogfood 摩擦（追加候选）

- a. `sdlc_state.py cmd_gate`：`if a.gate == "g1" and a.verdict == "reject": counters.world += 1` 不看 attribution；契约与现状本体都说只有 rule_error 计世界层。derivation_error 的否决会污染 retro 的世界层回流分布。建议只在 attribution=rule_error 时 +1。
- b. 定向重推没有机械的"只改了裁决点"证明：divergence.md 的 38 行对照表是人工替代。建议 psl-derive 在 targeted 模式下输出 `derived/round-diff.md`（round1 ↔ round2 逐 F 行 diff），G1 第 N 轮才能做 diff 核对而不是全读。
- c. 推导者对"同阶段"给了一个未对照数据的定义（graph.yaml 就在仓库里）。psl-derive 的 references/derivation.md 可加一条信号："形态决策引用某份数据文件的结构时，必须附该文件的一行证据"——这次是 G1 手工核出来的。
- d. dos_template.yaml 没有办法把一个属性标成"派生视图的物化"（Ring.missing），verify_dos 因此检不出"存了派生数据但没写派生规则"；本次靠 composition.GapState + R014 兜住，属推导者自觉。

---

## G1 第三轮（2026-09-05）

**日期**: 2026-09-05　**裁决人**: g1-judge　**签字性质**: delegated_agent（authorization: user instruction 2026-09-05 "需要人审核的地方，请你弄一个子agent代替我审核一下"；允许到：G1 裁决与记录，不含改 PSL / 改草案）　**PSL**: plugins/sdlc/dogfood/ring-audit/PSL-sdlc-ring-audit.md（v2.1，sha256 `3e3d91f9a56f68e0e022b43a6f31766217a48034bbb3be883cd0a5ea33de1210`，本地复算一致；相对 v2 只做"报告人审即 G3"措辞整理，规律文本未变）　**形态草案**: plugins/sdlc/dogfood/ring-audit/derived/form-draft.md

> 性质：**diff 核对**，按第二轮决定节的约定——若草案相对第二轮只改 F-05 / F-07 / F-08（+ 建议项 F-03）且与三段裁决一致，直接签。
> 机械预门：本地重跑 `verify_derived.py … --n 1` → PASS，27 决策，7 对象同名，无 reject，唯一 flag 仍是预期中的 PSL-008/009/012（内容层）。
> 状态核对：gates.g1 = reject / derivation_error / delegated_agent（第二轮记录）；counters.world = 1——derivation_error 未再 +1，第二轮摩擦 a 已修（行为层确认）。

### round-diff.md 核对

`derived/round-diff.md`：27 → 27 条 F 行，diff 仅三个 hunk（3c3 / 5c5 / 7,8c7,8），变动 id = {F-03, F-05, F-07, F-08}。逐条对照第二轮裁决：

| 裁决 | 落点 | 核对 |
|---|---|---|
| 残余 1：报告人审 = G3，非第四道门；合入后推翻 = 逃逸缺陷 → 下次审计 Run 新 Assessment + supersedes | F-07 `gate: G3`；dos-proposal 0.2.1 的 adjudications 枚举 / lifecycle / R010 / ADJUDICATES / behaviors 同步；workflow.md 三处；Q002 关闭进 evolution_log | **一致**。`report_review` 全库仅存于 evolution_log 0.2.1 的"去 report_review"摘要，属历史记载 |
| 残余 2：同阶段 = (a) 同一 stage 节点 handled_by ∧ (b) 带 when 守卫的 conditional 边选执行者 ∧ (c) 同 schema Artifact，缺一不算，数据源 graph.yaml | F-05 三条件；implement 组引 L29（`stage.implement handled_by`）与 L320–321（两条 conditional 边）→ 豁免；契约组引 L26（`stage.contract`），无 conditional 边、v1≠v2 → 触发 merge_candidate | **一致**。三处行号本地核对：L29 / L320–321 / L26 与引文相符 |
| N-1：human_gate 覆盖五个 kind=human 节点；merge → R7、harness-review → R8；文档三门 vs 数据五节点成为 Assessment（现状 Q004） | F-08；dos-proposal Part.kind / Part.ring / composition.RingMembership 同步；行号 L239–243 / L269–273 | **一致**。L239 = human.merge、L269 = human.harness-review 本地核对相符 |
| 建议项：fit 同词干或同义即 fits | F-03 | **一致**，例子（calibrate / dos-extract / retro）正确 |

其余 23 条 F 行按 round-diff 逐字节相同；对照我在第二轮通读的文本（F-01 / F-21 / F-24 / F-95 抽查）无出入。头注、验收挂钩表、"PSL 欠定"节的非 F 行变动见 divergence.md《第三轮改动》，内容只是把两条已裁欠定改为"已裁"，无新决策。

### F-21 措辞裁决

F-21 末句"adjudication 留空交 G3 / 报告人审"**可以站住，不必改**：(1) 它是关于残余冲突去向的散文，不是 schema 字段——检查脚本与 audit.yaml 的裁决门枚举由 F-07 给出，那里只有 G3；(2) PSL v2.1 已在 State Machine 与 γ 两处写明"报告人审即 G3"，斜杠在这个世界里读作同位语；(3) 改它会让本轮"diff 只落在裁决点"的机械证明失效，得不偿失。**解释规则记入本记录**：本形态草案中凡"G3 / 报告人审"并列处，均指 G3 一道门。下次因其他原因触草案时顺手统一为"G3"，不单独开轮。

### 三问复核（简）

1. 实体：7 个，名字与 PSL v2.1 Domain Model 一致；第二轮的 N-1 已补，五个人节点都有归属。✓
2. 技术对产品错：无新增。第二轮三处精度问题已修；F-05 现在对 graph.yaml 说的是真话。✓
3. 引用：27 条全部带形态层 PSL-ID；`(via UI-n / A-n / DP-n)` 十处维持第二轮接受。✓

### 归因

- [ ] 推错了
- [ ] 规律错了
（通过，不适用）

### 决定

- [x] **PASS** — 签字版形态草案 sha256: `ce22a46bb4dd45581c4ba78718bce5c830fa7586bff5475d6e6c03525421c05d`
- [ ] **REJECT**

说明：
- 签字对象是上述 sha256 对应的 `derived/form-draft.md` 字节；配套的 `dos-proposal.yaml` 0.2.1 sha256 `d3386d0a54dfec66325f4c37bda73e9fa78452d4e7f991151989c28a3621e475`、PSL v2.1 sha256 见表头，作为签字版的同批次引用记录于此。
- 签字版即功能文档；issue 的 Intent 引用本 sha256。issue-body.md 里的假设 A-2（"收编 skill 保留上游名判 fits"）与签字版 F-03 / F-23 矛盾，A-1 仍用 v1 的"闭合为辅"措辞，AC-004-b 用了被否决的 "finding" 一词——建 issue 前须按签字版改写，否则 issue 与功能文档不一致（第二轮已提，此处再记一次，因为签字之后它成了硬约束）。
- 状态机记录建议：`gate g1 --verdict pass --by g1-judge --signer-kind delegated_agent --authorization "…" --record plugins/sdlc/dogfood/ring-audit/g1-record.md`，并 `set world.form_draft_sha256=ce22a46b…c05d`。

### 外部证据

- [x] 原型走查 / 用户验证记录: **未做，原因同前（自审）。** 替代品：`verify_derived.py` 本地重跑 exit 0；round-diff.md 的机械 diff 证明 + 本记录对三处行号引文的原始数据核对。接受为替代，条件同第一轮（run_evidence 标 substitute；审计自己的检查脚本仍须跑删环变体）。

### 第三轮 dogfood 摩擦（追加候选）

- e. round-diff.md 的左侧（第二轮 F 行）不可由第三方复现：derived/ 只归档了 round1，第二轮草案被原地覆盖。定向重推应把上一轮也归档（derived/round2/），否则 diff 证明依赖生成者自述。
- f. 三轮 G1 共发现签字版与 issue-body.md 的三处不一致（A-1 / A-2 / AC-004-b），说明 /issue 的草稿在 G1 签字前就生成了，且没有机械对照签字版词表。建议 verify_issue.py 在 PSL 轨下检查 issue 的 Assumptions / AC 文本不含被签字版否决的词（可从 g1-record.md 的 ✗ 行与"明确不做"节取词表）。

### 第三轮补签（G2 E-11 引发的追加决策；追加于第三轮签字之后，append-only）

**触发**：G2（代签）复核 E-11 后要求形态草案追加一条检查脚本接口决策（G2 提案 id "F-13a"），否则契约（REQ-008..011 的 `required_parts` / `parts_total`）无法冻结。G2 定性为"同一输入上的视图 + 加性谓词，不换仪器，不重推"。团队负责人请求 G1 亲自把该行写进 `derived/form-draft.md` 并签新 sha。

**程序裁决：签字人不写自己签的东西。** 评估者与被评估者分离（PSL-003、ARCHITECTURE §6.3）是这条流水线的设计不变量，也是本记录第一轮拒绝手改草案的理由；G1 一旦成为草案的作者，签字就变成自签。落盘由推导者（或任何非 G1 角色）做，n=1 定向追加。为了不多开一轮，G1 在此**预签**：把"签字版 ce22… + 下面两处精确改动"在隔离目录里构造出来、跑过预门、算出 sha，签字条件是落盘文件与之字节一致。

**实质裁决：接受 G2 的决策内容，改三处形式。**
1. **id 必须是 `F-17`，不能是 `F-13a`**。`verify_derived.py` 的 `DECISION_RE = ^\s*-\s*\[F-\d+\]…` 只认纯数字——用 "F-13a" 时预门计数仍是 27，该行的 PSL-ID 引用**根本没被检查**（在隔离目录实测）。带字母后缀的决策会静默绕过预门，这是 verifier 的洞（摩擦 g），不能用一条会绕过预门的 id 签功能文档。F-17 是界面 / 接口形态节下一个空号。
2. **位置在 F-16 之后**（保持编号顺序），正文以"扩展 F-13："开头指回被扩展的决策；G2 要求的"F-13 之后"改为文内引用。
3. **补一句 iff 扩展**："不改任何既有谓词，F-13 的 exit 0 条件随之并含'给出 `--required-parts` 时 `required_parts_missing = 0`'"——否则 F-13 的"当且仅当"与新增 exit 1 条件自相矛盾。
4. **验收挂钩表 A6 行加 F-17**——PSL φ 要求每条形态决策至少被一条 Acceptance 检到，A6（能不能被机器检）正是它的钩子。
引用 PSL-015、PSL-004 接受：γ "每个 Part 三维判定齐"预设了 Part 清单，检查脚本要检"全覆盖"就必须拿到 required_parts；A6 / UI-2 是其锚。G2 的"视图 + 加性谓词、不重推"定性接受——无新实体、PSL 不动、输入不变；但它**是**形态变更，所以需要新签字，不能沿用 ce22。

**要落盘的精确改动**（相对签字版 ce22…，只此两处，其他任何字节不得变）：
```diff
34a35
> - [F-17] 扩展 F-13：`check_audit.py` 接口加 `[--rings R0,..] [--required-parts a,b,..]`；谓词加 `required_parts_missing`（given 里列出的 Part 名不在 audit.yaml 对应 Ring 的 parts 里 → 计数 + exit 1 `required_part_missing`）、`parts_total`（全部 Ring 的 Part 数）；`parts_without_assessment` 受 `--rings` 限定；不改任何既有谓词，F-13 的 exit 0 条件随之并含"给出 `--required-parts` 时 `required_parts_missing = 0`" ← PSL-015, PSL-004
62c63
< | A6 问"能不能被机器检" → audit.yaml + 脚本路径，删环变体 exit 1 且有记录 | F-12, F-13, F-14 |
---
> | A6 问"能不能被机器检" → audit.yaml + 脚本路径，删环变体 exit 1 且有记录 | F-12, F-13, F-14, F-17 |
```
隔离目录实测：改后 `verify_derived.py --n 1` → PASS，决策 28 条（F-17 被计入），无 reject。`divergence.md` 的《第三轮改动》应由推导者加一行"F-17（G2 提案 id F-13a）来自 G2 E-11：契约 required_parts / parts_total 需要的检查脚本视图；G1 补签见 g1-record.md"——divergence.md 不在签字范围内。

**决定（条件签字）**
- [x] **PASS（条件）** — 签字版形态草案 sha256: `746c56ef3e39e8e7089db0914bc01015b6dd522ef622c449e3d6260fbc10880d`
  条件：`derived/form-draft.md` 落盘后 `shasum -a 256` 恰为此值（即 ce22… + 上述两处 diff，别无其他）。满足则本签字生效并 **supersedes** 第三轮的 `ce22a46b…c05d`；不满足则本签字无效，回来带 diff。落盘者不得是 G1。
- 状态机：`set world.form_draft_sha256=746c56ef…880d`；gate g1 pass 记录同前（delegated_agent + authorization），账本 note 写 "supersedes ce22a46b…（G2 E-11 追加 F-17）"。

**顺带对 G2 的一条警示（契约层，G1 只标不裁）**：按签字版 F-08，Part 总数 = 28 skill + 5 agent + 5 human_gate（graph.yaml 全部 kind=human 节点）+ 4 脊柱数据资产 = **42**。若 AC-001-a 写 `parts_total: 40`，多半是漏了 human.merge / human.harness-review，与 F-08 矛盾；G2 冻结前须对齐（要么 42，要么把排除理由写进契约）。

**F-21**：维持第三轮裁决——"交 G3 / 报告人审"读作同位语，F-07 的枚举是权威，不改。

**摩擦（追加候选）**
- g. `verify_derived.py` 的 `DECISION_RE` 只认 `[F-\d+]`：形如 `- [F-13a] … ← …` 的行既不计入决策也不检引用，静默通过。应改为"以 `- [F-` 开头但不匹配格式的行 → reject"，或放开为 `[F-\d+[a-z]?]`。
- h. 契约链缺"G2 引发的形态追加"路径：谁落盘（推导者，n=1 定向）、G1 如何再签（diff 核对）、旧 sha 如何 supersedes——本次靠 G1 现场立规。建议写进 psl-derive 接线段与 g1_record.md 模板（"补签"小节）。

---

## G1 第三轮 b（2026-09-05）

**日期**: 2026-09-05　**裁决人**: g1-judge　**签字性质**: delegated_agent（authorization: user instruction 2026-09-05 "需要人审核的地方，请你弄一个子agent代替我审核一下"；允许到：G1 裁决与记录，不含改 PSL / 改草案）　**PSL**: v2.1（sha256 `3e3d91f9…de1210`，未变）　**形态草案**: plugins/sdlc/dogfood/ring-audit/derived/form-draft.md

**发生了什么**：编排者按《第三轮补签》的 diff 块落盘（ledger 14:51:22Z `set world.form_draft_sha256=746c56ef…`），并在 divergence.md《第三轮改动》加了 F-17 一行。落盘者不是 G1——预签条件"落盘者不得是 G1"成立，PSL-003 无偏离。团队负责人随后再次要求 G1 亲自追加 "F-13a"（消息与落盘交叉）；G1 按要求尝试时，脚本的守卫 `assert '[F-17]' not in s` 拒绝了二次插入，form-draft.md **未被 G1 改动一个字节**。G1 的脚本另在 divergence.md 追加了一条与编排者重复的说明，已由 G1 删除自己那一条（只删自己写的字节，编排者的行保留）——此处如实记录。

**核对**
- `shasum -a 256 derived/form-draft.md` = `746c56ef3e39e8e7089db0914bc01015b6dd522ef622c449e3d6260fbc10880d`，与《第三轮补签》预签值字节一致（与隔离构造稿 diff 为空）。
- 相对第三轮签字版 `ce22a46b…c05d` 恰两处：F-16 后新增 F-17（含"扩展 F-13"前缀与 iff 扩展句，引 PSL-015、PSL-004）；验收挂钩 A6 行加 F-17。**加性**：既有 27 条决策与所有既有谓词逐字节未变。
- `verify_derived.py --n 1` → PASS，决策 28 条（F-17 被计入），无 reject；flag 仍只有预期的 PSL-008/009/012。
- **id 是 F-17 不是 F-13a**：`verify_derived.py` 的决策正则只认 `[F-\d+]`，"F-13a" 会静默不计入、引用不检（隔离目录实测决策数停在 27）。G2 提案的实质全部保留，只换了 verifier 看得见的 id。
- 第二轮记录标"F-13 之后"为 G2 建议位置；本稿放在 F-16 之后保持编号顺序，正文"扩展 F-13："指回。

**决定**
- [x] **PASS** — 签字版形态草案 sha256: `746c56ef3e39e8e7089db0914bc01015b6dd522ef622c449e3d6260fbc10880d`（本签字**无条件**生效，**supersedes** 第三轮的 `ce22a46bb4dd45581c4ba78718bce5c830fa7586bff5475d6e6c03525421c05d`——后者保留为"第三轮 · F-17 之前"的形态草案哈希，可回溯）
- [ ] REJECT

**归因**：不适用（通过）。

**外部证据**：同第三轮（自审替代：预门重跑 + 隔离构造稿字节比对 + 本记录）。

**仍对 G2 有效的警示**：签字版 F-08 下 Part 总数 = 42（28 skill + 5 agent + 5 human_gate + 4 脊柱数据资产）；契约若写 `parts_total: 40`，与签字版矛盾，冻结前须对齐。

**摩擦（追加候选）**
- i. state.json 的 `gates.g1` 在 verdict=pass 后仍带上一轮的 `attribution: derivation_error`；`gate … --verdict pass` 应清掉 attribution，否则 retro 读到"pass 且 derivation_error"。
- j. 编排者落盘与"请 G1 落盘"的消息交叉，导致 G1 差点二次写入；靠脚本守卫挡住。追加类形态变更应有唯一落盘者并在 ledger 先记 `set world.form_draft_sha256` 再发消息（本次编排者做到了前者）。
