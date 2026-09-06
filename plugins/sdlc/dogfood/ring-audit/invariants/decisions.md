# invariant-extract · decisions.md（审计轨）— Territory `sdlc-plugin`

> 体例与 dos-extract 标准一致。每一处非平凡判断都留痕，供事后审计。
> 这把刀是起草书记员，不是立法者 —— 本文件是它向立法者交代"为什么这么草"的账本。
> 产物：`sdlc-plugin.card.yaml`（同目录）。本 run 同时是 invariant-extract skill 的 dogfood，skill 自身的问题记在末节。

## 运行元信息

- territory_id: `sdlc-plugin`
- 模式：auto（team-lead 给定绑定；无人在环，所有判断由 skill 自行做并留痕）
- **目的（取景框）**：name = "a self-closing product-engineering lifecycle whose every artifact is either script-checked or human-gated"；kpi = "escaped defects per merged feature, and waiver count"（docs/ARCHITECTURE.md §4 校准闭环 / retro）；主 aspect = correctness + reversibility；dos.scope 引用 = `plugins/sdlc/dogfood/ring-audit/dos.yaml#scope`
- dos_ref（统一语言来源）：`plugins/sdlc/dogfood/ring-audit/dos.yaml`（今日 dos-extract 产出的现状本体；`rules:` R001–R017 是去重基线，不重复立法）
- 代码面（work_target / paths）：`plugins/sdlc/skills/*/scripts/*.py`（23 个脚本，274 个 reject / die / exit(1) 执行点，ripgrep 采集）；`plugins/sdlc/skills/sdlc/scripts/sdlc_state.py prereqs()`（:236-292；该文件在本 run 期间被另一 agent 并发修改且未提交，所有 sdlc_state.py 行号按 14:20Z 工作树快照，引用同时带可 grep 的报错文案）
- failure.memory 计数：**84**（快照 2026-09-05T14:11:47Z；构成见下"通道说明"）
- **"Run" 在插件即领地下的读法**（非平凡判断）：dos.yaml 的 Run = 一次交付（fifteen stages）。但今日的失败记忆几乎全是"插件自己的验证器判错 / 自己的声明漂移"，它们发生在 *插件被使用的每一次*——含 dogfood 与插件自身的变更。本 run 把 "Run" 读为 **插件的任一次调用（交付 Run 或 dogfood/自变更）**，存活测试按此问。若只读作"一次交付"，I-02～I-15 全部投影为 ∅，卡上只剩演绎通道——那等于放弃护城河。此读法是 skill 未定的，记为 dogfood 发现 #1。

## 通道说明

- 通道一（演绎采集）是否跑：**是**。`rg "rejects\.append\(|die\(|sys\.exit\(1\)"` 覆盖 `plugins/sdlc/skills/*/scripts/*.py` 全部 23 个脚本；逐条按"插件级 □ / 交付 Run 级 □（多已是 R00x）/ 任务专属 / 防御性"分拣。dos.yaml 已把交付 Run 级的守卫立成 R001–R017，所以演绎通道的主要产出是**去重表**（19 条），只有 6 条落卡（INV-002/003/004/005/006/007 + DEF-003/004/005 的执行点）。
- 通道二（溯因恢复）是否有输入：**是**，84 条。构成：
  | 来源 | 条数 | 性质 |
  |---|---|---|
  | `dogfood/ring-audit/skill-issues.md` I-01…I-16 | 16 | 今日 dogfood 的 skill 缺陷（本 run 开始时 6 条，写卡前长到 16 条；按 14:11:47Z 快照） |
  | `.sdlc/sdlc-ring-audit/trace.jsonl` ev-0005、ev-0008（ledger deviation 行） | 2 | 审计者在 run 内修了被审的验证器（PSL-003 偏离，已记录） |
  | `skills/*/eval/gate.json` fix_list（28 个文件） | 52 | 已登记缺口 / 假阳性；34 个不同字串；约 20 条是同一句 "L2 never run" |
  | `docs/design-notes.md` 第二次整理 三类不自洽 | 3 | 推演发现的不自洽 |
  | `docs/design-notes.md` 第三次整理 dogfooding 发现 | 1 | graph.yaml 被自己的 lint 抓到两个无主圈 |
  | `docs/proposals/loop-graph-engineering.md` §0 | 5 | 五个缺口 |
  | `docs/proposals/loop-graph-engineering.md` §6 | 5 | 风险（非已发生失败；只作佐证，不单独取反） |
  | `git log -20`、`git show --stat f629e22` | （佐证） | v0.6.0 修了什么；不计入失败条数 |
- **诚实注记**：52 条 gate.json 条目中，绝大多数是"诚实登记的未知"（static_only、L2 未跑、路径未行使），不是违反。按 SKILL.md "a violation is the most reliable signal"，它们的溯因产出接近零：只有 psl fix_list[0]、commit fix_list[1] 进了 DEF-003；其余全部去重到 R017 或踢到 done_when（DW-001）。高价值输入是 skill-issues.md 的 16 条 + 2 条 deviation。
- **并发注记**：写卡期间 `sdlc_state.py` 被另一 agent 修改（+12/−3 行，未提交），本文件与卡内所有该文件的行号已按 14:20Z 快照重核并更新一次；其他被引脚本（verify_graph / verify_loop / verify_pr / verify_release / verify_calibration / lint_cards / trace / verify_done_when / verify_dos / verify_derived / lock_done_when）在读取与写卡之间无改动。

## 溯因 — 逐 obstacle 裁断

> 每条：目的投影（aspect / 是否 ∅）、来源 obstacle、取反出的候选、为什么取这条"最窄规则"、置信度、是否走 PROPOSE。

- **I-01**（.sdlc 无 VCS 策略）：投影 = ∅（打包/仓库卫生；dos.scope out_of_scope 有 plugin packaging；kpi 不动）→ 跳过，记 projected_out；修法是 ◊ → DW-016。
- **I-02**（verify_psl PASS 无编号 PSL，verify_derived 以此拒绝整个推导）：投影 aspect = correctness（一个产物过了自己的门、在下一道门上因为没被告知的属性挂掉）。候选 = "下游拒绝所依据的上游产物属性，必须在上游 φ 里声明并由上游验证器检查"。最窄性：不写成"上下游验证器检查同一组属性"——下游合法地检查*自己产物*的属性（form-draft 引了不存在的 PSL id）；只收窄到"上游产物的属性"。置信 = high（直接、窄、有两侧执行点：verify_derived.py:68 有 reject，verify_psl.py 全文无 PSL-NNN 检查）。□ 硬（一个任务不能合法地让产物过 A 门再在 B 门因未声明属性挂）→ **INV-008，propose**。
- **I-03**（G1 记录模板无 seam 计数栏）与 **I-06**（verifier flag 三条未引用规律但不告诉 G1 该删规律还是补决策）：同类——脚本→人 的交接丢信息，人在门上看不到脚本没判的东西。投影 aspect = correctness（门是装饰的，如果签字的人看不到洞）。合并取反为一条：flag / 未填承重槽 → 门记录的议程项。最窄性：不写"所有 verifier 输出进门记录"（reject 已经拦住了，无需上门），只写 flag（非 reject 发现）与承重空槽。可覆盖（签字人可声明直接读过产物）→ **DEF-001，carded**。两个 obstacle 合一条的理由：abduction.md 三"太窄 → 放过同类的另一个变体；放宽到覆盖该类"。
- **I-04**（模板引导语里的被禁 token 被当正文命中）、**I-05**（正则 re.S 贪婪吞空词表 → 7 个假拒绝，阻塞 U3）、**I-07**（一行 Links 被当一个键 → psl 轨假 flag；fixture 只有 task 轨）：同类——验证器在**真实产物**上假阳性，smoke 的 fixture 是手写最小样本 / 只覆盖一个枝。候选 = "带模板的验证器，其 pass-fixture 必须由自己的模板产出；验证器按枚举分枝时每枝一 fixture"。最窄性：不写"fixture 覆盖每个 reject 分枝"（I-05 的 reject 分枝在 fixture 上正确触发了——错的是真实输入上的假阳性，只有真实产物能暴露）；不写"每个正则都要单元测试"（过具体）。可覆盖（无模板 / 无枚举的 skill）→ **DEF-002，carded**。三个 obstacle 合一条，同上理由。
- **ev-0005、ev-0008**（run 内修了 gating 的验证器，偏离 PSL-003）：投影 aspect = correctness + reversibility（被门的一方改了尺子；kpi = waiver count 直接动了——deviation 就是 waiver）。候选族：(a) "永不动被审树"（PSL-003 原文）——过宽，I-05 那种 bug 会把门永久堵死；(b) "验证器可随时修"——过窄，放过静默改尺子；(c) **"Run 期间 gating 验证器 sha256 不变，或 deviation Event 先于 gate Event 且修复单独提交"**——恰好覆盖 obstacle（两次都是先记 deviation 再过门），不多禁一分。硬（一个 Run 不能合法地静默改门）→ **INV-001，propose**。机制上 lock_done_when.py 的 sha256 锁已有、只没套到脚本上（执行点）。分层探针：换任何领地的目的都成立（尺子不归被量者改）→ 同时标 **constitution_promotion_suspect #1**；卡上留的是绑到 `plugins/sdlc/skills/*/scripts` 的窄形。
- **I-08**（donewhen-extract 出口脚本检 qanat card 形状，sdlc 契约是 v2；无转换器）：投影 aspect = correctness。这是 **R002 的已观察违反**（"其他形态经转换进入"——card 形态没有转换器）。不另立法，记入 deduped(R002) 并加 note；修法 ◊ → DW-009。
- **I-09、I-12、I-13**（inventory.py 对 YAML/JSON 仓库抽 0 名词；文档通道无计数原语；decisions 模板预设名词>0）：投影 aspect = correctness（弱）。inventory.py 有 <10 告警，**没有违反任何不变量**，是 R1 工具对"插件即代码库"的能力缺口 → 全部 ◊ → DW-010。
- **I-10**（verify_dos.py 硬拒 "Card" 后缀、无整词豁免、无 waiver 通道；现状本体的正统对象名被验证器改写，影响产物=是）：投影 aspect = correctness（产物被迫说谎以躲启发式）。候选 = "启发式分类器的硬拒必须带可记录的 waiver 通道"。最窄性：不写"所有 reject 可 waive"（结构性 reject——缺必填字段、悬空引用——不该有 waiver）；只收窄到启发式（后缀表、词表）。执行点：verify_dos.py:67 的报错文案自己说 "exceed only with a human waiver in decisions.md"，但脚本不读任何 waiver、无条件 exit 1——**声明的通道不存在**。可覆盖（skill 作者判哪些是启发式）→ **DEF-005，carded**。与 INV-002 表面冲突 → conflicts[1]。
- **I-11、I-15**（dos_template 无 synonyms 槽、闭包不认 synonyms；qanat 词只在术语映射表里）：I-11 模板不合身 → ◊ DW-011。I-15 是 dos.yaml `agent_guidelines.should[1]`（导入词留在术语映射表）与闭包检查需求的**冲突** → conflicts[2]；修法 ◊ → DW-011。
- **I-14**（methodology 说 300–500 行、>800 膨胀，无机械检查）：与 psl fix_list[0]（"交付前必须跑"只是散文）、commit fix_list[1]（红绿证据手工）同类——**散文里说"必须"，没有东西编译它**。三个实例 → 取反成一条：绑定判据要么编译（prereq / hook / verify flag），要么标 `declarative (not compiled)`。最窄性：不写"所有 SKILL.md 陈述都要编译"（φ 的描述性句子不是判据）；只收窄到"作为约束陈述的判据"。可覆盖（design-notes 有意不做 hooks → 标注即合规）→ **DEF-003，carded**。执行点：sdlc_state.py:250-259 g2 prereq 跑 validate_done_when_v2 是"编译形态"的样板。
- **I-16**（五处文档↔代码分歧）：done_when.yaml 两个生产者 → R001/R002 已有 Q006/Q008，去重；docs 三道门 vs graph 五个 human 节点、五 agent vs 四 agent → **INV-003 预言的漂移在散文侧发生了**（散文无法被断言）→ 作 INV-003 的佐证 obstacle，修法 ◊ → DW-013（从 graph.yaml 生成计数）；伪层不在五层梯 → 本体问题，projected_out。
- **gate.json fix_list（52）**：
  - "L2: run inside a real …" 及所有 "not exercised / needs a live PR" 类（约 20+）：→ R017 去重；任务 → DW-001。
  - "classify the inherited phase-map order…"（×10）：投影 ∅（skillwise 评价框架，out_of_scope）→ projected_out。
  - acceptance-spec "upgrade to v2"：→ R002 去重；◊ DW-014。
  - psl "compile the delivery gate…"、commit "red-green evidence is manual"：→ DEF-003。
  - sdlc "graph.yaml vs ORDER: decide source"：→ INV-003 佐证；◊ DW-007。
  - sdlc / tune "thresholds are literature priors; calibrate after first real run"：◊ → DW-008。考虑过一条 □ "未校准的 harness 参数标 threshold_source: prior"——**未落卡**：没有违反发生、没有执行点 → 无溯源 → 按铁律不进卡。
  - sdlc "blank (registered): red-green script; meets_done_when comparison; contract.yaml schema; ontology-drift; psl-derive"、psl-derive "reconcile skill is a registered blank"、tune "targets in closed set but no rule emits them"：登记空白是**不变量被遵守**（有空白就登记）而非违反；无执行点强制登记 → 不落卡；R001 已覆盖"阶段无主"那一层。
  - release "deploy systems out of scope"、review-loop "linter persona hit false positive"：范围陈述 → projected_out。
  - tune "apply only emits diffs"（隐含）：→ R016 去重。
- **design-notes 第二次整理**：#1 三个生产者两种 schema → R002；#2 四个环节无承载 skill → R001（阶段无 Node ⇒ 产物无生产者）；#3 命名 → 投影 ∅（本体）。
- **design-notes 第三次整理 dogfooding**：graph.yaml 两个无主圈 → R013（R013 的 rationale 就引了它）。
- **proposal §0**：row 1 收敛只比上一次指纹 → R012；row 2 bash 轮询 → 投影 ∅（时延/可运维）；row 3 无爬山外环 → 缺口已由 /tune 填、其守卫是 R016 → 去重；row 4 平表账本 → **DEF-004**（决策类 Event 必带 decided_by / caused_by 边；执行点 sdlc_state.py:370-372 waiver 边、trace.py:224-259 lint——注意 lint 只验边的合法性不验存在性，所以是"部分编译"）；row 5 图是 ASCII → R013 + **INV-003**（两源断言相等；执行点 verify_graph.py:197,205）。
- **proposal §6**：bullet 1 从未真跑 → R017 / DW-001；bullet 2 数据与代码谁是源 → INV-003；bullet 3 trace 双写不一致——原则"trace 是证据不是控制状态"已写在 dos.yaml `objects.Event.identity_rule`，且无失败发生 → 去重到对象声明（非 R00x），并向 dos-extract 标为升 R00x 候选；bullet 4 tune 变自动调参 → R016；bullet 5 词汇漂移 → 投影 ∅。

### 按目的投影为 ∅ 而跳过的 obstacle（非排他，可被别的领地接走）

- I-01：why_empty = 打包/仓库卫生，dos.scope out_of_scope；kpi 不动。
- gate.json "classify phase-map into six cells / φ-γ" ×10：why_empty = skillwise 评价框架，out_of_scope。
- design-notes 第二次 #3 命名：why_empty = 本体 / 统一语言是 dos-extract 的列（Q001、Q002）。
- proposal §0 row 2 触发方式：why_empty = 时延/可运维维度；轮询不改变任何 verdict。
- proposal §6 bullet 5 词汇漂移：why_empty = 本体。
- I-16 伪层不在五层梯：why_empty = Layer 的本体（dos.yaml composition.Layer 已注）；审计 Finding 而非不变量。
- verify_commit.py:149,152 secret / debugger：why_empty = 交付代码卫生，/commit 自己的 φ；泄密不可逆属于产品的安全领地，非生命周期自身正确性。
- verify_dos.py:67 / verify_psl.py:117-172 形状规则：why_empty = R0/R1 世界内容，out_of_scope。
- lint_cards.py:198 上下文 ≤ 40k：why_empty = 策略数字（dos decisions 排除了策略数字），成本维度。
- release / review-loop 的范围陈述：why_empty = 不是失败。

## 存活测试 — □/◊ 逐候选裁断

> 每条：能否活过揭示它的那次 Run、判 □ 还是 ◊、◊ 的移交去向。"未来一次与揭示它的那次毫不相关的 Run"按上文"Run = 插件的任一次调用"问。

- INV-001 "gating 验证器 Run 内 sha256 不变或先记 deviation"：任何一次用插件的 Run 都必须守 → **□**。
- INV-002 "调用方 flag 不能压低硬底线"：任何 calibrate 调用 → **□**。
- INV-003 "两源声明每次 smoke 断言相等"：任何插件变更 → **□**（Q003 定了单源后变为空真，不是被违反）。
- INV-004 "引用必须解析、不许字串匹配"：任何声明 / Run 产物 → **□**。
- INV-005 "永不改写已推送历史 / 覆盖 tag"：任何 pr / release Run → **□**。
- INV-006 "无 Rollback how: 的 release notes 拒绝"：任何 release Run → **□**。
- INV-007 "Known issues 永不带 P0 / A 级"：任何 pr Run → **□**。
- INV-008 "下游拒绝所依据的上游属性须上游声明并检查"：任何 skill 接缝 → **□**。
- DEF-001 "flag / 承重空槽进门记录议程"：任何人签的门 → **□**（可覆盖）。
- DEF-002 "pass-fixture 模板产出、每枝一 fixture"：任何带验证器的 skill → **□**（可覆盖）。
- DEF-003 "绑定判据编译或标 declarative"：任何 SKILL.md → **□**（可覆盖）。
- DEF-004 "决策类 Event 带边"：任何 Run 的账本 → **□**（可覆盖：init/set/advance/custom 允许无边）。
- DEF-005 "启发式硬拒带可记录 waiver 通道"：任何带启发式 reject 的验证器 → **□**（可覆盖）。
- ◊（踢回，16 条，全在卡的 kicked_to_done_when，handoff_to = donewhen-extract）：DW-001 真跑一次 L2；DW-002 提交两次 run 内修复；DW-003 三个 fixture；DW-004 g1_record 加节；DW-005 flag 文案；DW-006 psl hook 或标注；DW-007 Q003 拍板；DW-008 阈值校准；DW-009 三纪律移植 / card→v2；DW-010 inventory YAML/JSON；DW-011 synonyms 槽；DW-012 verify_dos 整词豁免 + 体量 flag；DW-013 从 graph.yaml 生成文档计数；DW-014 acceptance-spec 出 v2；DW-015 编译 INV-001；DW-016 .sdlc VCS 策略。每条 why_diamond 都写了"达成即弃"及其对应的 □。
- **裁断边界上的取舍**（宁可踢下）："未校准参数标 prior" 本可算 □，但无违反、无执行点 → 不进卡，只留 DW-008；"登记空白"是被遵守的实践 → 不立法。

### 分层探针（换目的的思想实验）

- purpose-independent 嫌疑 #1（送立法上浮、卡上只留窄形 INV-001）：候选 "一个 Run 永不改动给自己把门的评估者，除非 deviation 先于门且修复单独提交"；why = 代入正确性领地（尺子）、时延领地（benchmark harness）、成本领地（计量器）都成立；是 R004 / R014 抬高一个海拔的同一条。
- purpose-independent 嫌疑 #2（送立法上浮、卡上只留窄形 INV-002）：候选 "被门的一方不能在调用时压低硬底线；底线只经立法移动"；why = Model Spec 指挥链，与底线量的是什么维度无关。
- **未标嫌疑的理由**：INV-004（引用解析）虽通用，但卡上的形式绑死到插件枚举的引用种类，换领地要重新枚举；INV-005（已推送历史不可改）只在有 git 交付面的领地成立。其余绑领地。
- **一处 skill 未定**：SKILL.md 说 purpose-independent 候选"不复制进每张卡"，但若不落卡，本领地在立法前无保护。本 run 的做法：**窄形落卡（绑 plugins/sdlc 路径）+ 广形标嫌疑**，两处互引。记 dogfood 发现 #7。

## 强度分类 — 逐 □

> 每条：任务能否合法违反、判硬 / 可覆盖、authority level、海拔（territory / 提案上升）。

- □ INV-001：能否合法违反 = 不能（静默改门无合法情形；合法的修复已由 deviation 子句放行）；栏 = hard；海拔 = territory；是否提案上升 R00x = **标嫌疑**（不自动升）。
- □ INV-002：不能；hard；territory；标嫌疑。
- □ INV-003：不能（往一侧加 stage 不加另一侧无合法情形）；hard；territory；否。
- □ INV-004：不能（悬空引用无合法情形）；hard；territory；否。
- □ INV-005：不能（commit SKILL.md 三处"永不"）；hard；territory；否。
- □ INV-006：不能；hard；territory；否。
- □ INV-007：不能；hard；territory；否。
- □ INV-008：不能（否则产物可过 A 门败 B 门而无从知晓）；hard；territory；否。
- □ DEF-001：能——签字人声明直接读过产物；栏 = overridable；authority = 门的人签者 / 模板归 skill 作者。
- □ DEF-002：能——无模板、无枚举的 skill；overridable；authority = skill 作者，waiver 记 gate.json fix_list。
- □ DEF-003：能——标 declarative 即合规（design-notes 有意不做 hooks 是常设 waiver）；overridable；authority = 插件作者。
- □ DEF-004：能——init / set / advance / custom ledger 允许无边；overridable；authority = 引擎（无边只限那几类）/ 新决策 kind 由插件作者 PR 加边。
- □ DEF-005：能——结构性 reject 不带 waiver；overridable；authority = decisions.md 里有名有姓的人，永不是裸 flag。
- **hard 全部 disposition: propose**（R008 / qanat R002：门资产只人签）；overridable 五条 carded 但提交复审。

## 去重与冲突

- 与 dos.yaml.rules 去重（已升宪法、不重复立法）的候选：**16 条对 R001–R017**（R007 无直接候选——账本只增不删今日没有候选触到它），逐条见卡 `deduped_against_constitution`。另 **3 条对 dos.yaml 对象声明**（`objects.Event.identity_rule` 证据非控制状态；`objects.Gate.lifecycle` G1/G2 前置；`objects.WorkUnit.identity_rule` REQ 单主 / allowed_files 不交）——已写下但不是 R00x，模板没有这一槽，用 `note:` 标明，并向 dos-extract 提"Event 证据非控制状态"升 R00x 候选。
- **去重中发现的 R00x 违反**（不立法，记账）：I-08 是 R002 的已观察违反（card 形态无转换器；R002 标 enforced_by: system 但该路径未覆盖）；I-16 done_when.yaml 两个生产者是 R001 字面违反（dos.yaml Q006 已提）。
- 与现有卡合并的同义条：无现有卡（本领地首张）。合并进单条的同类 obstacle：I-03+I-06 → DEF-001；I-04+I-05+I-07 → DEF-002；psl fix_list[0]+commit fix_list[1]+I-14 → DEF-003；ev-0005+ev-0008 → INV-001。
- 检出的冲突（两条不能同真 → 立法项，3 条，见卡 `conflicts_for_legislation`）：
  1. PSL-003 "审计者不碰被审树" vs INV-001 的 deviation 子句——今日两次 Run 都需要后者。
  2. INV-002 "调用方 flag 不能压线" vs DEF-005 "启发式 reject 要有 --waive / decisions.md 通道"——提议边界：数值校准底线 vs 启发式分类器；waiver 是有名字的人的记录，不是 flag。
  3. dos.yaml `agent_guidelines.should[1]`（导入词留在术语映射表）vs 闭包检查须解析卡 / issue 引用的每个名词（I-15）。

## 落卡与提案

- 落卡的可覆盖默认（候选）：DEF-sdlc-plugin-001 … 005（5 条，carded，提交复审）。
- 走 NEEDS_HUMAN / 立法的硬不变量与高风险溯因：INV-sdlc-plugin-001 … 008（8 条，全部 propose）；两条 constitution_promotion_suspects 送立法上浮。
- dos 修订提案（Territory.invariants 字段 / MemoryAsset 枚举）：**不需要新字段**——dos.yaml `objects.Run.properties.world` 已含 `invariants` 路径槽；SKILL.md 接线要求 `sdlc_state.py set world.invariants=…`，但本 run 的写入白名单只有 `plugins/sdlc/dogfood/ring-audit/invariants/`，**未执行**该状态写入（会改 `.sdlc/`）；由 team-lead 决定是否登记。另向 dos-extract 提两条：(a) `objects.Event.identity_rule` 的"证据非控制状态"升 R00x；(b) 模板 / 闭包认 `synonyms:`（conflicts[2]）。
- 登记为 golden 回归用例的不变量（棘轮）：8 条 INV 全部 `golden_regression: true`。可立即写成回归的：INV-003（smoke 已有 verify_graph 断言）、INV-004（六个执行点已有 reject）、INV-005/006/007（verify_pr / verify_release 已有 reject）、INV-002（verify_calibration 已有）。**尚无机械形态**的：INV-001（DW-015）、INV-008（需 verify_psl.py 加 PSL-NNN flag）。

## Self-review（验收自检）

- [x] 绑定了恰好一个 Territory，不变量用了它的统一语言（Run / Contract / WorkUnit / Gate / Event / Node / Loop / Layer；卡 / Card 只作同义词）
- [x] 拉了目的（name+kpi+scope）并当透镜贯穿：obstacle 按目的投影（∅ 的 10 类已跳过并记录），每条 □ 记了 aspect（correctness 或 reversibility）
- [x] purpose-independent 嫌疑已标记送立法（2 条），卡上只留绑路径的窄形（做法本身记为 skill 未定项）
- [x] 两条通道都跑了（通道二 84 条输入，构成表见上；无一处假装）
- [x] 每条落卡不变量都有溯源（执行点 file:line 或真实失败 ref；INV-005/006/007 演绎单通道，已标 obstacle_ref 为空并在 note 说明）
- [x] 没有 ◊ 混进卡；16 条 ◊ 已踢给 donewhen-extract（带 id，verify_card 的泄漏检查可用）
- [x] 硬不变量是被提案的，不是自动安装的（8/8 propose）
- [x] 与 dos.yaml.rules 去过重（16 条 R00x + 3 条对象声明）
- [x] 冲突被显式呈现为立法项（3 条）
- [x] 无 invariants 字段时，产出了有界 dos 修订提案 —— 字段已存在（`Run.world.invariants` 路径槽），不需要；两条相邻 dos 修订建议已列
- [x] `verify_card.py … --dos dos.yaml` exit 0（见下）

## verify_card.py 结果

```
python3 plugins/sdlc/skills/invariant-extract/scripts/verify_card.py \
  plugins/sdlc/dogfood/ring-audit/invariants/sdlc-plugin.card.yaml \
  --dos plugins/sdlc/dogfood/ring-audit/dos.yaml
→ hard: 8 · overridable: 5 · kicked_to_done_when: 16 · rejects: [] · exit: MECHANICALLY_CLEAN (exit 0)
→ needs_semantic_review: 13 条，全部是对每条无条件追加的 "confirm narrowest-rule-on-right-aspect"（见 dogfood D-6）；
  无 survival_test 缺失 flag，无 R00x statement 撞库 flag。
```

第一次运行即 exit 0（未迭代）。语义半边（□/◊ 是否真存活、是否最窄、是否对维度）由 judge / 人按本文件"存活测试""强度分类"两节复核，脚本不背书。

## Dogfood：invariant-extract skill 自身的问题（本 run 同时是 skill 的一次冒烟）

> 逐条：现象 → 根因 → 建议。按"是否影响本次产物"排序。

| # | 位置 | 现象 | 根因 / 影响 | 建议 |
|---|---|---|---|---|
| D-1 | SKILL.md 世界观 / 术语映射 | "Run" 对插件即领地有两种读法（交付 Run vs 插件的任一次调用含 dogfood）。按 dos.yaml 字面读，I-02～I-15 全部投影 ∅，溯因通道空转 | SKILL.md 与接线段只把 Run 映射为"一次交付"；对"领地 = 一个 skill 集合 / 一个插件"没有说明 | 接线段加一句："领地是插件或 skill 集合时，Run = 该插件的任一次调用（含 dogfood 与自身变更）" |
| D-2 | frontmatter 注释 vs 正文 | frontmatter 说 "see 接线 / 术语映射"，team-lead 也按"末尾有术语映射表"下达任务；**正文没有任何 术语映射 表**，只有一段 接线 散文（grep 只命中第 20 行注释） | 收编时 donewhen-extract / spec-compile / calibrate 加了表，invariant-extract 没加 | 补一张表：Territory→dos bounded context / 插件；Run→一次交付或一次调用；MemoryAsset→ledger fail/deviation 行、escape-defects.md、skill-issues.md、gate.json fix_list；R001→R014/R005；R002→R008 |
| D-3 | `assets/invariant_card.yaml` vs `scripts/verify_card.py` | 模板的 `overridable_defaults` 条目**没有 `aspect` 槽**，但 verify_card.py `check_entry` 对每条（含 overridable）无 aspect 即 **REJECT** | 模板与验证器不同步。**按模板原样填卡必被拒**——影响产物：本卡在每条 DEF 上手工加了 `aspect` | 模板 overridable 条目加 `aspect: ""`（并顺带加 `ears_type`，与 hard 对齐） |
| D-4 | verify_card.py ◊ 泄漏检查 | 检查用 `k.get("id")` 比对 kicked 与 carded 的 id，但模板的 `kicked_to_done_when` 条目**没有 id 字段** → `str(None)` 永不命中，检查**结构上空转** | 模板与验证器不同步 | 模板 kicked 条目加 `id:`，或验证器改为比对 statement |
| D-5 | verify_card.py 去重 | 只在 id 与 R00x id 相撞时 REJECT（INV-* 永不撞 R00x），statement 只做小写全等匹配才 flag → 换个措辞重新立法 R00x **机械上完全放过** | 去重实际全靠人 | 至少对 R00x statement 做 token 重叠率 flag；或要求每条 hard 填 `dedup_checked_against: [R00x…]` 并验非空 |
| D-6 | verify_card.py 输出 | 对**每条**无条件追加一条 "confirm narrowest-rule … needs_semantic_review"，13 条 = 13 条噪音，flag 数与卡长度成正比、无信号 | 语义半边没有任何可判的输入 | 只在 `narrowest_rule_note` 为空、或 channel=abductive 且 obstacle_ref 为空时 flag |
| D-7 | verify_card.py 报告 | 报告不计 `projected_out_obstacles` / `deduped_against_constitution` / `constitution_promotion_suspects` / `conflicts_for_legislation` 的条数，一张 0 投影、0 去重的卡与本卡输出形状相同 | 出口无法证明通道二被"工作过"而非"假装跑过"（SKILL.md 明写要防这个） | 报告加四个计数；`channel_2_input.failure_memory_count > 0` 且 `projected_out + hard(abductive) + deduped == 0` 时 flag "通道二有输入却无产出" |
| D-8 | SKILL.md 分层探针 | "purpose-independent 候选不复制进每张卡"与"本领地立法前需要保护"未协调；窄形可否落卡 + 广形标嫌疑，SKILL.md 未说 | 本 run 自行采用"窄形落卡 + 广形标嫌疑" | 在 survival-test.md 二点五 加一句允许（或禁止）该做法 |
| D-9 | `invariant_card.yaml` `channel_2_input` | 只有一个整数；本 run 84 条里 52 条是 gate.json 的"诚实登记的未知"，不是违反，单个整数会高估溯因信号 | 模板无来源分解 | 加 `sources: [{ref, entries, kind}]`（本卡已非标准地加了） |
| D-10 | SKILL.md 接线 "失败记忆的来源" | 只列 ledger fail 行 / escape-defects.md / G3 记录；本 run 最富产的来源是 **skill-issues.md（16 条）与 ledger 的 `deviation` 行**，gate.json fix_list 反而近零产出 | 接线段按交付 Run 写，没考虑插件 dogfood | 接线段加 skill-issues.md 与 deviation kind；并加一句"gate.json fix_list 的登记项是未知不是违反，喂 done_when 不喂 □" |
| D-11 | `invariant_card.yaml` `deduped_against_constitution.matched_rule` | 注释 "已是 R00x 的哪条"，但真实 dos.yaml 还在 `objects.*.identity_rule / lifecycle` 里声明了不变量（非 R00x）；没有"已写下但非规则"的槽 | 本卡用 `note:` 标明 | 加 `matched_kind: rule | object_declaration` |
| D-12 | hard 条目 `altitude: territory | proposed_to_constitution` vs 顶层 `constitution_promotion_suspects` | 同一件事两处可说，哪个为准未定 | 本卡 altitude 全 territory，嫌疑只写顶层节 | 删 `altitude` 的 `proposed_to_constitution` 值，或删顶层节，二选一 |
| D-13 | abduction.md 步骤 5 vs 模板 | 步骤 5 说置信度按"窄直接 → 高；宽 / 跨系统 / 需假设链 → 低"，模板只有 high \| low；overridable 的 disposition 模板写 carded，abduction.md 说低置信只 propose——验证器两者都不检 | 不影响本卡（全部 high） | 模板 disposition 注释写清 "confidence: low ⇒ propose，即使 overridable" 并进 verify_card |
| D-14 | SKILL.md 接线 "路径记入 `sdlc_state.py set world.invariants=…`" | 该命令写 `.sdlc/<slug>/state.json`，超出本 run 的写入白名单（只许 `dogfood/ring-audit/invariants/`）；接线要求与卡实现的隔离纪律相抵 | 未执行，留给 team-lead | 接线段改为"路径由编排者（/sdlc）登记，本 skill 只输出路径" |
| D-15 | 术语 | 卡模板与 references 用 R001/R002 指 qanat 的"评估者隔离 / 门资产人签"，dos.yaml 的 R001/R002 是"单生产者 / 单契约 schema"。在**同一张卡**里 `deduped_against_constitution.matched_rule: R002` 与模板注释 "(R002)" 指两件事 | 收编未改注释 | 模板注释里的 R001/R002 改成 "(qanat R002 ≙ sdlc R008)" 之类的双写 |
| D-16 | 环境 | 失败记忆在 run 中间长了（skill-issues.md 6→16 行，ledger 加了 ev-0008），卡的 `extracted_at` 与 `failure_memory_count` 只能标快照 | 并行 dogfood 是本仓库常态 | 模板 `channel_2_input` 加 `snapshot_at`；SKILL.md 提一句"记忆在增长时按快照写卡，落卡后新条目走棘轮" |

**影响本次产物质量的**：D-3（若不手工加 aspect，卡被拒）、D-1（若按字面读 Run，卡上无溯因条目）。其余不影响本卡，影响 skill 的可信度与下次使用。

### 实测（scratchpad 副本，不动产物）

| 实验 | 做法 | 结果 | 证实 |
|---|---|---|---|
| D-3 | 把 DEF-001 的 `aspect` 删掉（= 模板原形） | `REJECT: DEF-sdlc-plugin-001: aspect missing` | 按模板填卡必被拒 |
| D-4a | 追加一条 **无 id** 的 kicked 条目，statement 与 INV-001 逐字相同 | `MECHANICALLY_CLEAN`，rejects 空 | 模板形状下 ◊ 泄漏检查空转 |
| D-4b | 追加一条 kicked 条目 `id: INV-sdlc-plugin-001` | `REJECT: a ◊ candidate is also carded as □` | 检查只在作者自行加 id 时生效 |
| D-5 | 追加 hard 条目 INV-099，statement 是 R014 的改写（"A Loop's generator Node and its verifier Node SHALL be different Nodes."），带 `--dos` | `MECHANICALLY_CLEAN`，无任何 R00x flag | 机械去重放过改写的重复立法 |
