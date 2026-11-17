---
name: formal-verify
description: >-
  给状态性需求做形式化验证，规则与模型由 AI 生成，生成过程本身可检。生成不用自写提示词，而是执行
  原样收录的开源流程（Spec Kit specify/clarify、Quint LLM Kit quint-modeling、TLA+ AgentSkills、
  Specula code analysis / spec generation / fidelity triage、Formal Verification Skills 审阅契约），
  每段流程的产出都落成脚本能检查的文件。至少两个互不可见的 AI 生成者各写一份规则合同和一份模型，
  脚本逐条比较它们的语义与可观测行为，分歧交人裁决，全新上下文的审阅者按上游审阅契约审规则和模型。
  模型检查通过后，再把已验证的设计转成实现契约（状态映射、原子 / 幂等 / 事务、故障处理、验收测试与负对照），
  编码 agent 按契约实现；实现之后验证代码确实落实了契约与模型，然后才进独立验收。之后进入统一的验证主干：
  模型检查、变异资格、真实代码轨迹一致性、源码映射漂移、契约弱化检测和风险分级 CI。新需求先建模
  再写代码；已有代码先用当前代码的真实轨迹校准 AI 建的现状模型，再找反例。
  用于“形式化验证”“模型检查”“不变量”“并发 / 一致性 / 幂等 / 超卖 / 重复执行”“TLA+ / Quint”
  “这个设计会不会出错”。纯函数用性质测试，UI 用 E2E，不走这里。
  前置：Python 3.9+（自带 fvkit，仅标准库）；YAML 资产需要 PyYAML；能派发隔离子 agent 的宿主。
argument-hint: "<需求或模块> [--entrance spec-first|code-first] [--slug <aidlc slug>] [--n 2]"
version: 1.2.0
user-invocable: true
---

# Formal Verify：AI 生成规则与模型，脚本检查生成，人裁决分歧

需求定义“应该怎样”，代码描述“实际上怎样”。规则（`fv-contract`）和模型（`fv-model`）**由 AI 生成**，这是流程的必经阶段。
但 AI 写的东西不因为是 AI 写的就可信，所以每一步都留下脚本能检查的产物，而且生成者与检查者是分开的。

检查器 `scripts/fv.py`（fvkit）与 trusted-acceptance 的副本逐字一致，不依赖任何外部引擎就能把
**需求 → 清单 → 规则 → 模型 → 检查 → 实现 → 轨迹一致性 → CI** 跑成闭环。

## 完整流程（01–09）

| # | 环节 | 产物 | 检查 |
|---|---|---|---|
| 01 | 需求入口：新需求（入口 A）/ 已有代码（入口 B） | `requirements.md`；入口 B 加 Specula modeling brief | — |
| 02 | 定义规则与不变量（AI 生成，必经） | 清单、intake、≥2 份规则候选、审阅 → `contract.yaml` | `requirements-check` / `intake-check` / `rules-divergence` / `check-review`，G2 锁 |
| 03 | 建立行为模型（AI 生成，必经） | ≥2 份模型候选、模型审阅 → `model.yaml` | `model-divergence` / `model-review-check`；入口 B 加校准 |
| 04 | 形式化模型检查 | 反例 → 分诊 → 迭代设计 | `check` / `triage-check` / `qualify`（QUALIFIED） |
| **05** | **生成实现契约**：把模型转成具体的工程约束 | `impl-contract.yaml` | `impl-contract check`（READY）：模型定下的部分由 fvkit 推导、不可改写 |
| 06 | Coding Agent 按契约实现 | 代码；卡经 `formal_ops` 绑定契约操作 | `lint_cards.py` 第 7 项；卡的输入带契约约束 |
| **07** | **验证实现一致性**：真实代码落实了模型与契约 | `impl-review.yaml`、`implement` 回执（E3） | `impl-verify`（IMPLEMENTS）：代码证据、测试与负对照、轨迹一致、操作覆盖、反例重放、全新上下文审阅 |
| 08 | 独立自动验收 | trusted-acceptance 政策固定模型、合同、实现契约摘要 | gate 重新校验每份回执，并把 `conform` / `implement` 回执绑定到候选提交 |
| 09 | 持续验证闭环 | — | `fv ci` 每次改动都重跑 02–07 的证据：生成证据、资格、一致性、实现验证 |

**模型检查通过，不代表真实代码正确。**05 让编码 agent 按已验证的设计实现，而不是重新猜一遍设计；07 专门弥合“模型对、代码错”的差距。细节见 [references/implementation-contract.md](references/implementation-contract.md)。

## 三条不能让步的原则

1. **规则来自需求。** 规则生成者看不到代码，即使是入口 B。“代码现在这样做”不能证明任何事，否则就把已有缺陷合法化了。规则只用合同的 observables 词表写，模型借精化映射接入，改模型改不了规则的含义。
2. **模型贴近现实。** 一个模型动作必须是真实代码里的一个原子步骤，`source-map.yaml` 用逐字锚点把动作钉在代码上。入口 B 的现状模型，要先用当前代码的真实轨迹校准，它找出的反例才算数。
3. **结果按证据分级。** E0–E4 各自只能声称自己那一级（[evidence-levels.md](references/evidence-levels.md)）。生成证据是 E0（证明过程，不证明正确）；`BOUNDED_PASS`、模拟和 `quint run` 都不是 PASS。

## AI 生成阶段（必经，两个入口都要走）

详细协议见 [references/generation.md](references/generation.md)。**方法来自上游，不自创。**三个 agent（`agents/rule-formalizer.md`、`agents/model-builder.md`、`agents/formal-reviewer.md`）只做适配：读 `upstream/` 里原样收录的开源流程，执行其中的步骤，把产出翻译成 fvkit 文件。每一步对应哪段上游原文、产出什么、脚本怎么检查、哪里做了适配，见 [references/upstream-methods.md](references/upstream-methods.md)。`fv upstream verify upstream/UPSTREAM.json` 确认收录的原文没有被改动；每份生成产物在 `procedure:` 里按 sha256 引用它所执行的原文。

| 步 | 谁 · 执行的上游流程 | 产物 | 脚本怎么检 |
|---|---|---|---|
| G-1 需求清单 | `rule-formalizer`（intake）· Spec Kit `specify` 第 6 步 | `requirements.yaml`：每条 R / A 逐字引用原文 | `fv requirements-check`：引文必须逐字存在；每一句“必须 / 不得 / 不会 / 最终 / 恰好 / must / never”都要落到需求、假设或带引文的 out_of_scope |
| G-2 intake | `rule-formalizer`（intake）+ **人**答问题 · Spec Kit `clarify`；Quint quint-modeling Step 1；from-requirements | `rules-intake.yaml` | `fv intake-check`：10 类歧义逐类有状态；问题 ≤5、以问号结尾、由人回答；系统模型 4 项有出处；每条需求有抽取行与影响分；每个操作有粒度决定 |
| G-3 规则候选 ×N（N≥2） | N 个互不可见的 `rule-formalizer`（candidate），只读需求 · from-requirements 第 4 项；Quint Step 5 | `candidates/rules-<k>/contract.yaml` | `fv trace-rules`：每条需求被形式化或有处置，每条性质引用真实需求并写明 `text`；High 影响的性质类需求必须被形式化 |
| G-4 规则分歧与裁决 | 脚本 + **人**（委托签须附授权原话） | `rules-divergence.json` 的 rulings；`contract.yaml` | `fv rules-divergence`：按需求逐条比较，有限域上精确比较并给出见证值；采纳的合同必须是被比较过的候选之一 |
| G-5 规则审阅 | `formal-reviewer`（rules，全新上下文）· FVS `fc-spec-review` + `review-policy` | `rules-review.yaml`（不可改）+ 作者的 `rules-triage.yaml` | `fv check-review --triage`：7 个审阅面；发现格式；PASS / APPROVE-WITH-EDITS / REVISE / BLOCKED 规则；延后要人裁决；≤3 轮 |
| B1 代码分析（入口 B） | `model-builder`（analysis）· Specula `code_analysis` | `modeling-brief.md` + `defect-ledger.json` | `fv brief-check`：第 1–7 节、Category A/B、Scenario 字段；6.2 表与 JSON 一致 |
| G-6 模型候选 ×N（N≥2） | N 个互不可见的 `model-builder`（candidate）· Quint Step 1–7；入口 B 加 from-code、tlaplus-from-source、Specula spec_generation | `candidates/model-<k>/model.yaml` + `notes.md`（Step 7 handoff）；入口 B 加 source-map | `fv lint` / `fv check`；每个候选的 handoff 三节非空 |
| G-7 模型分歧与裁决 | 脚本 + **人** | `model-divergence.json` 的 rulings；`model.yaml` | `fv model-divergence`：比较观察者看得到的状态、步骤与判定；采纳的模型必须在被比较之列；入口 B 另需 `formal calibrate` 与 `brief-coverage.yaml`（Specula brief coverage） |
| G-8 模型审阅 | `formal-reviewer`（model，全新上下文）· Quint `review.md` + Specula 粒度审计 | `model-review.yaml` | `fv model-review-check`：运行时检查由检查器重算；结构检查不能是 fail，warn 由人决定；该拆的动作必须拆 |

`fv gen-evidence rules|model` 把上面的结论收成一份回执：READY 或 NOT_READY，并列出理由。
分歧不是失败，是给人的议程；没有裁决的分歧才是失败。

**为什么至少两个。** 一个 AI 写一份规则再自己检查，等于自己给自己打分。两个互不可见的生成者对同一句需求读出不同的东西，那就是需求的含糊处或某一方读错了，这正是需要人看的地方。分歧集来自同样的思路（psl-derive 的 N 次推导、donewhen-extract 的 divergence）。

## 入口 A · 新需求：先建模再写代码

| 步 | 做什么 | 过关条件 |
|---|---|---|
| A1–A2 | G-1 到 G-5：清单、intake、≥2 份规则候选、分歧裁决、审阅 | **FV-G0 = AI-DLC 的 G2**：合同和清单一起签进锁 |
| A3 | G-6 到 G-8：≥2 份模型候选（Quint 主线）、分歧裁决、模型审阅；很小的范围（两个人、一张票） | 模型生成 READY |
| A4 | `fv check`；有反例就分诊（见下），绝不改弱规则；把被推翻的设计作为 mutant 留在模型里，修正后的模型重新进入 G-7 比较 | **FV-G1**：`fv qualify` 判 QUALIFIED，即完整探索、见证可达、无死动作、必需 mutant 被预期性质杀死 |

## 入口 B · 已有代码：还原现实再找问题

| 步 | 做什么 | 过关条件 |
|---|---|---|
| B1 | G-1 到 G-5，规则生成者**只读需求、不读代码**；清单可以引用事故报告和 `/invariant-extract` 的卡 | 有一组独立于实现的规则 |
| B2–B3 | 先由一个 `model-builder`（analysis）按 Specula code_analysis 写 modeling brief；再走 G-6 到 G-8，候选按 from-code / tlaplus-from-source / Specula spec_generation 读代码，找出事务和锁的边界，写现状模型和 source-map 候选；`fv source-map verify` 不能有 BROKEN | 关键动作都映射到真实代码；brief coverage 完整 |
| B3′ 校准 | 用 harness 在**当前代码**上跑出轨迹，`formal calibrate --model <现状模型>`：轨迹必须 CONFORMS | 不一致说明 AI 建的模型不像这份代码，先修模型，不分诊反例 |
| B4 | `fv check` 找反例 → `fv gen-tests --strategy counterexamples` → harness 在真实代码里重放 | 能在真实代码里重放的才是缺陷 |

## 统一验证主干

```bash
FV="python3 $SKILL_DIR/scripts/fv.py"
$FV check   --model model.yaml --out r/check.json          # C1 模型检查（E2）
$FV qualify --model model.yaml --out r/qualify.json        # C2 设计门槛
$FV gen-tests --model model.yaml --strategy transitions,counterexamples --counterexample r/old-design.json --out vectors.json
python3 impl/harness.py --vectors vectors.json --out traces/           # 项目 harness 驱动真实代码，记录轨迹
$FV conform --model model.yaml --map source-map.yaml --traces traces/*.jsonl --out r/conform.json   # C4（E3）
$FV ci --policy verification/policy.yaml --base origin/main --out ci-out/   # C5：生成证据 + 资格 + 一致性，每个 PR
```

- **C1 模型检查**：广度优先的完整探索，给出最短反例；活性在弱 / 强公平下检查，反例是套索。截断就报 `BOUNDED_PASS`，并给出 `exhaustive_depth`。
- **C2 分诊与资格**：每个反例由 `formal-reviewer`（triage）按 Specula spec-fidelity checklist 与 bug-classification 写成 `fv-cex-triage`，`fv triage-check` / `formal triage` 核对并给出路由；结论只有五类（下表）。改设计由 Agent 起草，改规则必须有授权的人同意，并且重新走一遍 G-1 到 G-5。
- **C3 实现或修复**：实现以已签的合同为准。只重跑模型证明不了改过的代码正确。
- **C4 真实代码独立验收**：真实轨迹必须逐步符合同一个模型，被拒绝的步骤要在轨迹里体现为拒绝；观测完整的事件同时按合同做运行时监控。
- **C5 持续维护**：受保护文件变了，源码映射就 STALE；契约变了就做弱化检测；生成证据（分歧报告、审阅）跟着摘要失效。`fv ci` 只要有一项没跑、失败或失效，就判 UNSATISFIED。

## 反例分诊（结论只有五种）

| 分类 | 判据 | 谁处理 | AI-DLC 信号 |
|---|---|---|---|
| `requirement_gap` | 规则没覆盖这种情况，需要产品决定 | 需求负责人：新合同版本，重走 G-1 到 G-5，G2 变更提案 | `fv_requirement_gap` → task |
| `model_infidelity` | 反例在真实代码里不可能发生 | 建模者修模型和映射，重新比较、校准、qualify | `fv_model_infidelity` → plan |
| `design_defect` | 模型如实反映了设计，而设计本身允许坏结果 | 改设计，旧设计留作 mutant | `fv_design_defect` → plan |
| `implementation_defect` | 反例或非一致轨迹在真实代码里重放成功 | 实现者修代码，重放向量留作回归 | `fv_implementation_defect` → card |
| `checker_defect` | 引擎、harness 或环境故障 | 维护检查器或环境 | `fv_checker_defect` → exception |

脚本还会自己产生两种信号：`fv diff-contract` 判出弱化时发 `fv_contract_weakened` → task，源码映射过期时发 `fv_model_stale` → plan。

**反模式**：模型检查失败 → 实现者把 `sold <= 1` 改成 `sold <= 2` → 检查变绿 → 宣称完成。
这条路被四处堵住：合同在 G2 锁里；改过的合同不在被比较的候选之列，生成证据失效；`fv diff-contract` 判为 WEAKENED；trusted-acceptance 的政策固定了规则摘要。

## AI-DLC 接线

```bash
S="python3 $AI_DLC/scripts/aidlc_state.py"
$S formal configure  --slug X --module m --contract …/contract.yaml --model …/model.yaml \
     --source-map …/source-map.yaml --min-level E3 --entrance spec-first|code-first   # 或 --policy verification/policy.yaml
$S formal generation --slug X --kind rules --divergence …/rules-divergence.json --intake …/rules-intake.yaml \
     --review …/rules-review.yaml --review-triage …/rules-triage.yaml
$S formal calibrate  --slug X --model …/candidates/model-a/model.yaml --traces traces/*.jsonl   # 仅 code-first
$S formal generation --slug X --kind model --divergence …/model-divergence.json --review …/model-review.yaml \
     [--brief …/modeling-brief.md --ledger …/defect-ledger.json --coverage …/brief-coverage.yaml]   # code-first 必填
$S formal triage     --slug X --file …/triage/<name>.yaml [--model <产生反例的模型>]
$S formal qualify    --slug X
$S formal impl-contract --slug X --file …/impl-contract.yaml          # 05：fv impl-contract draft 起草、填写后登记
$S formal impl-verify   --slug X --review …/impl-review.yaml          # 07：跑契约的测试与负对照、轨迹、反例重放、审阅
$S formal conform    --slug X --traces traces/*.jsonl
$S formal status     --slug X
```

| 前置（`--force` 越不过） | 从哪个阶段起 |
|---|---|
| fv 合同和需求清单都在当前 G2/L5 锁里，字节未变 | `cards` |
| `upstream/UPSTREAM.json` INTACT；规则生成 READY（每次推进都对当前文件重算） | `cards` |
| 模型生成 READY（模型审阅、handoff；code-first 要 brief 与校准）+ QUALIFIED + 实现契约 READY | `implement` |
| E3 模块：当前代码对当前实现契约 IMPLEMENTS（契约或被映射的文件变了就失效） | `acceptance` |
| E3 模块：当前的 CONFORMS，映射代码与取证时一致，源码映射此刻 FRESH | `pr` / `merge` |

确实要降级，只能由人签 `formal waive`，并强制走 G3。配了策略时，需要哪些模块由 diff 推出；策略里 E2 以上的模块必须声明 `rules_intake`、`rules_divergence`、`rules_review`、`model_divergence`、`model_review`（code-first 还要声明 `calibration`、`modeling_brief`、`defect_ledger`、`brief_coverage`；E3 还要 `impl_contract`、`impl_review`）；策略的 `upstream:` 指向收录的上游清单时，引用按字节核对。

## 产物结构

```
specs/<feature>/formal/
  requirements.md            原文（或指向 PRD / issue / done_when）
  requirements.yaml          AI 抽出的清单（逐字引文）
  rules-intake.yaml          Spec Kit clarify + Quint from-requirements 的 intake
  candidates/rules-*/        规则候选（保留，是记录的一部分）
  rules-divergence.json      分歧 + 裁决
  rules-review.yaml · rules-triage.yaml   FVS 审阅（不可改）+ 作者处置
  contract.yaml              采纳的规则（随 G2 锁）
  modeling-brief.md · defect-ledger.json · brief-coverage.yaml   入口 B：Specula 分析与覆盖自检
  candidates/model-*/        模型候选（model.yaml + notes.md handoff）
  model-divergence.json      分歧 + 裁决
  model-review.yaml          Quint review + Specula 粒度审计
  triage/*.yaml              反例分诊（Specula fidelity checklist + bug classification）
  receipts/qualify.json      实现契约所依据的 QUALIFIED 回执
  impl-contract.yaml         05 实现契约（derived 由 fvkit 推导；其余由 model-builder 按上游流程填写）
  impl-review.yaml           07 实现审阅（Spec Kit analyze + Quint 差距问题；钉住被审代码的字节）
  model.yaml · model-scope.md · source-map.yaml · source-map.lock.json · vectors.json · decisions.md
verification/policy.yaml     模块 → 风险 → 证据等级 → CI 层 → 生成证据路径
```

`fv init --dir specs/<feature>/formal --name <feature> --entrance spec-first|code-first` 生成一套骨架（清单、合同、模型都能直接通过检查，`candidates/` 留给生成者）。
完整示例在 `assets/example-ticket/`：清单、intake（3 个澄清问题）、两份规则候选（B 漏了“剩余不为负”，并把“答复”读成了“成功”）、两份模型候选（B 允许售罄后重试）、分歧报告与裁决、FVS 审阅与分诊、模型审阅、入口 B 的 Specula brief（`code-first/`）、初版设计反例的分诊（`triage/`）、修正、真实 SQLite 实现与 harness、并发测试、策略、向量。

## 参考

- [references/generation.md](references/generation.md)：AI 生成协议：派发、隔离、清单、比较、裁决、审阅、采纳、校准
- [references/implementation-contract.md](references/implementation-contract.md)：05 实现契约（推导什么、填什么）、06 卡怎么绑定、07 实现一致性的五类检查、能声称什么
- [references/upstream-methods.md](references/upstream-methods.md)：每一步执行哪段上游原文、构造对照（Quint / TLA+ / FizzBee → fvkit）、适配与理由、直接使用上游工具
- [upstream/README.md](upstream/README.md)：收录的上游项目、许可证、不改原文的规则与更新方法
- [references/modeling-language.md](references/modeling-language.md)：清单、合同、模型、表达式、语义；轨迹、向量、源码映射、分歧报告、审阅、策略的格式
- [references/evidence-levels.md](references/evidence-levels.md)：E0–E4 各自能声称和不能声称什么；回执字段
- [references/triage-and-maintenance.md](references/triage-and-maintenance.md)：分诊、变异资格、CI 分层、持续校准循环、外部引擎
- [references/open-source.md](references/open-source.md)：借鉴了哪些开源项目、借了什么、没借什么

## 已知边界（如实登记）

- 分歧检查衡量的是**生成者之间是否一致**，不是是否正确：两个生成者可能犯同一个错。全新上下文审阅和人的裁决是另外两道防线，不是可以省掉的步骤。
- 语义比较只在声明了有限 domain 的观测量上是精确的；映射、序列这类没有 domain 的观测量只能按文本比较，结论交人判断。
- 示例里的候选、intake、审阅、brief、分诊、实现契约与实现审阅都是为演示而撰写的，不是真实隔离 agent 的运行记录。
- 实现一致性（07）是 E3：它证明代码里有契约要求的机制、测试与负对照按预期、真实轨迹符合模型，不证明所有输入与交错下都正确。验收方不重跑候选的测试，只重新推导回执、重查轨迹，并把回执绑定到候选提交。
- 脚本检查的是“上游流程的每一步都做了、记下了”，不是“做得对”：澄清问题问得好不好、brief 的分析深不深，仍要靠人的裁决与审阅。
- 上游流程有些步骤在隔离生成中做不到（中途找用户确认、并行子 agent、TLC 跑 hunt cfg），适配方式见 upstream-methods.md 第三节。
- 内置检查器是显式状态枚举，不产生 E4。外部引擎适配只对固定格式的样例输出测过，本仓库没有实际运行 TLC / Apalache / Quint / FizzBee。
- 本 Skill 的行为层效果（AI 生成的规则与模型质量）尚未评测，证据等级为 `static_only`。
