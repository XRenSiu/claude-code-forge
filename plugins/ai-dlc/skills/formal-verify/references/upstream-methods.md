# 上游方法：每一步执行哪段开源流程、产出什么、怎么被检查

生成规则与建模不使用本仓库自写的方法。agent 执行的是 `upstream/` 里原样收录的开源流程（来源、提交、许可证见 [upstream/README.md](../upstream/README.md)）。本仓库只做三件事：

1. **翻译**：上游流程写的是 Quint、TLA+ 或 Lean，本仓库的检查器读的是 fv-contract / fv-model。下面的构造对照表负责转换。
2. **落盘**：每段流程规定了自己的产出（Spec Kit 的澄清记录、Specula 的 modeling brief、FVS 的审阅格式……）。这里把这些产出固定为可检查的文件。
3. **检查**：`scripts/fvkit/methods.py` 按上游原文中的规则检查这些文件，例如问题最多 5 个、问题以问号结尾、判定与发现数量一致、要拆分就必须拆分。规则旁边都注明了出处。

下表列的是有出入的地方：本仓库对上游流程做了**适配**的部分，以及适配的理由。

## 一、步骤 → 上游文件 → 产物 → 检查

路径相对于 `upstream/`。

| 步骤 | 执行者 | 上游流程（必须引用） | 产物 | 检查 |
|---|---|---|---|---|
| G-1 需求清单 | rule-formalizer（intake 模式） | `spec-kit/templates/commands/specify.md` 第 6 步（抽取参与者、动作、数据、约束；`[NEEDS CLARIFICATION]` 最多 3 个） | `requirements.yaml` | `fv requirements-check`：引文逐字存在；规范句一句不漏 |
| G-2 intake | rule-formalizer（intake 模式）+ 人答问题 | `spec-kit/templates/commands/clarify.md` 第 3–6 步；`quint-llm-kit/.../quint-modeling/SKILL.md` Step 1 系统模型清单；`.../guidelines/from-requirements.md`（抽取表、High/Medium/Low、范围与粒度） | `rules-intake.yaml`（fv-rules-intake） | `fv intake-check`：10 类歧义都有状态；Partial/Missing 要么问了，要么带理由延后；问题 ≤5、以问号结尾、由人回答；系统模型 4 项都有出处；每条需求都有抽取行；每个操作都有粒度决定 |
| G-3 规则候选 ×≥2 | rule-formalizer（candidate 模式，互相隔离） | `from-requirements.md` 第 4 项（保证 → 不变量，“能到达 X” → 见证）；`SKILL.md` Step 5（先见证、后不变量；活性用 temporal） | `candidates/rules-*/contract.yaml` | `fv trace-rules`；`fv rules-divergence`；High 影响的性质类需求必须被某条 property 形式化 |
| G-5 规则审阅 | formal-reviewer（rules 模式，全新上下文） | `fvs/fv-skills/references/fc-spec-review.md`（审阅契约）+ `review-policy.md`（作者处置） | `rules-review.yaml`（schema 2，不可改）+ `rules-triage.yaml` | `fv check-review --triage`：7 个审阅面；判定与发现一致；APPROVE-WITH-EDITS 必须有分诊；作者不能给自己裁决；最多 3 轮 |
| B1 代码分析（入口 B） | model-builder（analysis 模式） | `specula/skills/code_analysis/guide.md` Step 0–Phase 4；`.../references/modeling-brief-format.md`；Category B 读 `concurrent-analysis.md`，Category A 读 `distributed-analysis.md` | `modeling-brief.md` + `defect-ledger.json` | `fv brief-check`：第 1–7 节齐全；声明 Category A/B；Scenario 字段齐全；6.2 表与 JSON 一致 |
| G-6 模型候选 ×≥2 | model-builder（candidate 模式，互相隔离） | 入口 A：`quint-modeling/SKILL.md` Step 1–7；入口 B：另加 `guidelines/from-code.md`、`tlaplus-agentskills/skills/tlaplus-from-source/SKILL.md`、`specula/skills/spec_generation/guide.md` Phase 1 + `base-spec-methodology.md` | `candidates/model-*/model.yaml` + `notes.md`（Step 7 handoff），入口 B 加 `source-map.yaml` | `fv model-divergence`；每个候选的 `notes.md` 必须有 What it covers / What it does NOT cover / When to update |
| B 覆盖自检 | 采纳模型的作者 | `specula/skills/spec_generation/references/brief-coverage-checklist.md` | `brief-coverage.yaml` | `fv brief-check`：每个 Scenario、第 5 节每条不变量、6.1 每条发现都有落点；活性要有公平性 |
| G-8 模型审阅 | formal-reviewer（model 模式，全新上下文） | `quint-llm-kit/.../guidelines/review.md`（6 项结构检查与运行时检查）；`specula/.../base-spec-methodology.md` 粒度审计 | `model-review.yaml` | `fv model-review-check`：运行时检查由检查器重算；结构检查不能是 fail；warn 由人决定；每个动作都有粒度审计行，该拆不拆就拒绝；审阅者说 pass 但检查器发现死动作或空洞性质，同样拒绝 |
| C2 反例分诊 | formal-reviewer（triage 模式） | `specula/skills/tla-checking-workflow/references/spec-fidelity-checklist.md` Step 1–4；`specula/skills/bug-classification/guide.md` | `triage/*.yaml`（fv-cex-triage） | `fv triage-check` / `formal triage`：Case B 必须指出被漏掉或放宽的守卫，并写明模型改法；Case C 的状态与严重度要一致；给出路由 |
| 05 实现契约 | model-builder（impl-contract 模式） | `quint-llm-kit/.../skills/quint-execute-spec/SKILL.md` Phase 1–2；`specula/skills/spec_generation/references/instrumentation-spec-format.md`；`spec-kit/templates/commands/plan.md`、`tasks.md`；`pstack/skills/create-formal-verification-skill/SKILL.md` | `impl-contract.yaml`（fv-impl-contract） | `fv impl-contract check`：derived 一节由 fvkit 从 QUALIFIED 模型推导、不可改写；每个变量、观测量、动作都有代码对应；推导要求原子的动作有机制和证据；四类故障只能落在模型允许的状态；每条性质、mutant、假设都有验收项；至少一个负对照 |
| 06 编码 | card-implementer | `quint-execute-spec` Phase 2–4（先计划、每步过验证闸、全量验证、绝不改规格） | 代码 | `lint_cards.py` 第 7 项：每个契约操作恰好归一张卡，卡的白名单覆盖操作的文件，任何卡都不能写契约 |
| 07 实现一致性 | `fv impl-verify` + formal-reviewer（impl 模式） | `spec-kit/templates/commands/analyze.md`；`quint-execute-spec` Phase 1 第 3、4 问与 Phase 4；`specula/skills/harness-generation/guide.md`；`specula/skills/bug-confirmation/phases/02-reproduction.md`；`pstack/skills/maintain-formal-verification-skill/SKILL.md` | `impl-review.yaml`（fv-impl-review）+ `implement` 回执（E3） | 约束的 evidence 逐字在代码里；测试通过、负对照失败；真实轨迹符合模型且每个操作被执行过；反例重放被拒；审阅覆盖每个操作、处置每个模型外行为、确认每条假设、钉住被审代码 |
| 维护 | 编排者 | `pstack/skills/create-formal-verification-skill`、`maintain-formal-verification-skill` | 源码映射锁、mutant、`fv ci` | 能失败（mutant 被杀）；发现保持为发现（diff-contract）；与代码同步（source-map）；`fv ci` 每次重跑 07 |

`gen-evidence rules|model`（以及 AI-DLC 的 `formal generation`）把上表汇总起来：缺任何一项都是 NOT_READY。AI-DLC 闸门每次推进时都会重算一遍，并先确认 `upstream/UPSTREAM.json` 是 INTACT。

## 二、构造对照：上游语言 → fvkit

上游的映射表（`from-code.md` 的 “source-construct → Quint mapping”、`tlaplus-from-source` 的 Step 2.2）先把代码映射到 Quint/TLA+。本表再把 Quint/TLA+ 映射到 fvkit：

| Quint | TLA+ | fv-model / fv-contract |
|---|---|---|
| `const N: int`、`const NODES: Set[str]` | `CONSTANTS` | `constants`（模型）；合同的 `parameters` |
| `var x: T` | `VARIABLES x` | `variables.x.init` |
| `action init = all { x' = … }` | `Init` | 各变量的 `init` 表达式 |
| `pure def f(…)` | 运算符定义 | `definitions` 或内联表达式 |
| `action a(p) = all { guard, x' = … }` | `A(p) == /\ guard /\ x' = …` | `actions.a: {params: {p: 域}, guard, update}`（没写的变量 = UNCHANGED） |
| `step = any { a, b }` | `Next == \E p: A(p) \/ …` | 所有 `actions` 的析取（自动） |
| `val inv = …` | 不变量 | `properties` 中 `kind: invariant` |
| 见证 `val canX = not(X)`，用 `--witnesses` 检查 | `~X` 作为“应被违反”的不变量 | `kind: reachable`（检查器报告是否到达） |
| `temporal p = always(eventually(…))`、leads-to | `[]<>`、`~>` | `kind: infinitely_often` / `eventually` / `leads_to` |
| `weakFair` / `strongFair` | `WF_vars(A)` / `SF_vars(A)` | `fairness: [{action, kind: weak|strong, per_params}]` |
| sum type / 字符串常量 | 常量集合 | 字符串字面量（fvkit 没有枚举，审阅时按 `enums_over_strings` 记 warn，由人决定） |
| `assume` / `run` 测试 | `ASSUME` | 合同 `assumptions`（带来源）；可检查的前提写成 `model_invariants` |
| 代码位置注释（Specula “annotate every logic block with file:line”） | 同左 | `source-map.yaml` 的逐字锚点 + `atomicity` 声明 |

FizzBee（`fizzbee/.claude/skills/fizz-spec`）：role → 每个参与者一组变量；`atomic` 块 → 一个动作；`fair` 动作 → `fairness`；`always assertion` → invariant；`eventually` → eventually / leads_to。

## 三、适配（与上游不同的地方，以及理由）

| 上游的做法 | 这里的做法 | 理由 |
|---|---|---|
| Quint Step 2：类型草图要先得到用户批准，再写逻辑 | 生成者把类型草图写在 `notes.md` 开头；≥2 份隔离候选的 divergence 与人的裁决起到“批准”的作用 | 隔离生成者在中途不能和用户对话；比较与裁决是批准的书面形式 |
| from-requirements / from-nothing：遇到分歧就停下来问用户一个问题 | 生成者把问题写进 intake 的 `clarifications`（`answer` 为空）或清单的 `open_questions`；编排者转给人，人的回答写回文件 | 同上；Spec Kit clarify 同样规定一次只问一个、最多 5 个，并由人回答 |
| FVS：建议使用另一家运行时的审阅者，记录模型与 effort | 要求全新上下文（`reviewer.context: fresh`）；如有条件，应使用不同的模型或运行时，并写进 `reviewer` | 本仓库不能假设用户装了其他运行时；独立性的最低要求是全新上下文 |
| FVS 审阅面针对 Lean 规格（溢出、limb 编码等） | 7 个审阅面保留名称，含义换成规则合同：source_fidelity＝规则对需求原文；preconditions＝assumptions；postconditions＝性质方向与遗漏；interpretation_and_quantifiers＝量词作用域与有限域；vacuity＝永不触发的蕴含与见证；dependencies_and_evidence＝假设来源与 trace-rules；helper_reuse_and_scope＝观测量与定义的复用 | 审阅契约的结构（逐面检查、发现格式、判定规则、作者分诊）原样保留，只替换审阅对象 |
| Quint review 的运行时检查（C-init…R2）用 `quint run` 驱动 | 由 `fv model-review-check` 用 fvkit 检查器重算，不采用审阅者自己填写的结果 | 能重算的结果就不依赖口头声明；C-step 在 fvkit 里改为报告“从未被写的变量”，因为没写的变量默认 UNCHANGED |
| Specula：TLC 跑 MC / hunt cfg、Trace.tla 校验轨迹 | fvkit 的 `check` / `qualify` 代替 MC；hunt cfg 对应 `brief-coverage.yaml` 中的 hunt 模型；轨迹校验用 `fv trace-check` / `formal calibrate` | 不要求 Java 与 32GB 内存；装了 TLC 时可以直接使用（见下节） |
| Specula bug-confirmation（复现、提交修复请求） | 实现缺陷路由为 `fv_implementation_defect`，交 AI-DLC 的卡片修复；复现证据是 E3 轨迹 | AI-DLC 已有修复回路 |
| Quint quint-execute-spec：计划先给用户看；每步用 `quint run` / `quint verify` 当验证闸 | 计划写进实现契约的 `plan` 与任务卡，经 `lint_cards` 与 AI-DLC 的门；验证闸换成契约里的验收测试（性质、并发、MBT），由 `fv impl-verify` 统一跑 | fvkit 模型不在编码时运行；对代码有意义的闸是对代码跑的测试 |
| Specula harness-generation：对源码插桩，Trace.tla 校验轨迹 | 项目自己的 harness 驱动公开接口、写 fv-trace；`fv impl-verify` 逐步对照模型并检查每个动作都出现过 | 不需要 TLA+ 工具链；轨迹格式见 modeling-language.md |
| Spec Kit analyze：只读的跨制品报告，不写文件 | 审阅结果写进 `impl-review.yaml`，按同样的分级与覆盖表检查 | 闸门需要可检查的文件 |
| pstack：为项目生成一个专属的 verify skill | 不生成专属 skill，统一使用 `fv` 与本 Skill；“能失败 / 与代码同步 / 诚实的范围”由 mutant、source-map 锁与 handoff 承担 | 一套工具覆盖所有模块，闸门才能统一检查 |

## 四、直接使用上游工具（已安装时）

用户已经装好上游工具链时，可以直接用上游 skill 写原生规格，并把结果作为额外证据收进来：

| 工具链 | 用哪个上游 skill 写 | 怎么检查、留证据 |
|---|---|---|
| Quint（`quint` CLI，可选 Quint LLM Kit 插件） | `quint-modeling`（本目录收录的版本） | `fv external --engine quint-verify --spec model.qnt …`（最多 BOUNDED_PASS，E2）；`quint-run` 只到 E1 |
| TLA+（TLC / Apalache） | `tlaplus-from-source`、`tlaplus-split-action`；入口 B 可按 Specula 的 spec_generation 写 MC.tla / cfg | `fv external --engine tlc …` / `--engine apalache …`，保留原始输出并可重新解析 |
| FizzBee（`fizz`） | `fizz-spec` / `fizz-check`；MBT 用 `fizz-mbt` | `fv external --engine fizzbee …`（只解析 PASSED / FAILED） |

直接使用**不能代替** fvkit 模型：AI-DLC 的闸门、mutant 资格、轨迹一致性与验收 gate 都读 fv-model。直接使用只是在同一份合同下多一份独立引擎的证据：`fv external` 回执可以交给 trusted-acceptance 的 gate，它会重新解析留存的原始输出，并限制等级上限。没有哪道闸门检查原生规格是怎么生成的，所以原生规格的可信度取决于你是否按上游 skill 做完了 Step 7 handoff 与 review。

**本仓库没有运行过上述外部工具。** 适配器只用测试替身验证过解析与留证据，没有对照真实安装检验过（见 [open-source.md](open-source.md)）。
