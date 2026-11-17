# 开源项目：哪些直接使用，哪些借鉴

本 Skill 和开源项目的关系分三种：

- **原样收录并执行**：生成规则、建模、审阅、分诊的方法是上游原文，收录在 `upstream/`。agent 读原文、执行其步骤；`fv upstream verify` 确认原文没有被改动。
- **借鉴实现**：fvkit 自己实现了检查器（零依赖、能自闭环），语义上借鉴 TLC / Quint。
- **通过适配器直接调用**：用户装了 TLC / Apalache / Quint / FizzBee，可以用 `fv external` 调用它们，原始输出会保留下来。

每一步对应哪段原文、做了哪些适配，见 [upstream-methods.md](upstream-methods.md)。收录的版本（仓库、提交、sha256）见 `upstream/UPSTREAM.json`。

| 项目 | 许可证 | 原样收录并执行的流程 | 本仓库补上或实现的部分 |
|---|---|---|---|
| [GitHub Spec Kit](https://github.com/github/spec-kit) | MIT | `specify`（需求抽取，`[NEEDS CLARIFICATION]` ≤3）、`clarify`（10 类歧义扫描，≤5 个问题，问题以问号结尾，答案由人给）；`plan` / `tasks`（数据模型、接口契约、测试先行）；`analyze`（跨制品覆盖与一致性、分级）；`implement` | `fv requirements-check`（逐字引文、规范句一句不漏）；`fv intake-check` 把 clarify 的规则变成检查 |
| [Quint LLM Kit](https://github.com/quint-co/quint-llm-kit) · quint-modeling / quint-execute-spec | Apache-2.0 | 建模主线 Step 1–7（系统模型清单、先见证后不变量、guarded actions、Step 7 handoff）；from-requirements / from-code / from-nothing / from-tlaplus；review.md（6 项结构检查与运行时检查）；quint-execute-spec（按已验证规格实现：差距分析、带验证闸的计划、实现后验证、绝不改规格） | intake 的系统模型与抽取表；候选的 handoff 检查；`fv model-review-check` 用检查器重算运行时检查；构造对照到 fv-model |
| [Specula](https://github.com/specula-org/Specula) | Apache-2.0 | code_analysis（Category A/B、bug archaeology、modeling brief、defect ledger）；spec_generation（基础规格方法、粒度审计、brief coverage、活性模式、instrumentation spec）；harness-generation；bug-confirmation 的复现规则；spec-fidelity checklist；bug-classification | `fv brief-check`（brief 格式、ledger 与 JSON 一致、覆盖自检）；`fv triage-check`（Case B/C、状态与严重度一致、路由）；用 fvkit 检查器与 `fv trace-check` 代替 TLC 和 Trace.tla |
| [TLA+ AgentSkills](https://github.com/tlaplus/AgentSkills) | MIT | tlaplus-from-source（Phase 1–4、代码 → TLA+ 映射）；tlaplus-split-action；tlaplus-add-variable | TLA+ → fv-model 对照；检查器的 stutter、`WF` / `SF`、对称约简、死锁语义借鉴 TLC；`fv external --engine tlc|apalache` |
| [Formal Verification Skills](https://github.com/Beneficial-AI-Foundation/formal-verification-skills) | MIT | lean-spec-review 的审阅契约 `fc-spec-review`（7 个审阅面、BLOCKER/MAJOR/MINOR、四种判定、审阅不可改）；`review-policy`（作者处置、作者不能给自己裁决、≤3 轮）；trust-audit | `fv check-review --triage`；审阅面换成规则合同的含义（见 upstream-methods.md 第三节）；不提供 Lean / Aeneas，E4 只能来自外部 |
| [pstack](https://github.com/cursor/plugins/tree/main/pstack) | MIT | create / maintain-formal-verification-skill：检查要能失败、发现保持为发现、范围要诚实、与代码同步 | mutant 资格（`fv qualify`）、`fv diff-contract`、handoff、`source-map.lock.json` 与 `fv ci` |
| [FizzBee](https://github.com/fizzbee-io/fizzbee) | Apache-2.0 | fizz-spec / fizz-check / fizz-mbt / fizz-debug（直接使用时） | FizzBee → fv-model 对照；`fv external --engine fizzbee`（只解析 PASSED / FAILED）；`fv gen-tests` 生成的向量供真实代码重放 |
| [Quint](https://github.com/quint-co/quint) | Apache-2.0 | —（工具本身，不收录） | `reachable` 见证；`fv simulate` 与 `quint run` 都只到 E1；`fv external --engine quint-verify|quint-run` |
| [fast-check](https://fast-check.dev/) | MIT | — | 风险分流：纯函数走 `/test-suite-generator` 的 PBT 层；`--strategy random` 的随机向量 |

## 本仓库额外补上的部分（上游各自没有覆盖的组织边界）

- **生成者不检查自己**：≥2 份隔离候选按语义（规则）和可观测行为（模型）比较，分歧交人裁决，采纳的版本必须在被比较之列。上游流程都是单个生成者的。
- **规则与模型分权**：性质只能用合同的 observables 词表写；模型通过精化映射接入。改模型不能改变规则的含义。
- **弱化检测**：`fv diff-contract` 在有限域上精确判断，没有有限域时在模型及其自动变异的状态上抽样判断，并标明是抽样。
- **证据等级进入数据**：回执自带 `evidence_level` 与 may / may-not claim；有界、模拟、未完成都有独立的 verdict 和退出码。
- **可重算的证据**：反例与见证可在模型里重放；`--rerun` 重跑后逐项比较；trusted-acceptance 的 gate 在受保护环境用原件重算。
- **与 AI-DLC 状态机的硬接线**：合同进 G2 锁；`advance cards` 要求规则生成 READY（含 intake 与 FVS 审阅）；`advance implement` 要求模型生成 READY（含模型审阅与 handoff）与 QUALIFIED；`advance pr/merge` 要求 E3 证据且绑定当前候选。这些都不能被 `--force` 越过。

## 没有做到的（如实登记）

- 本仓库**没有运行过** TLC、Apalache、Quint、FizzBee；适配器只用测试替身验证过解析和留证据。
- 上游流程里需要中途与用户对话、并行子 agent 或 TLC 的步骤，做了适配（见 upstream-methods.md 第三节），不是逐字照做。
- 上游项目会更新。收录的版本固定在 `UPSTREAM.json` 的提交上，更新需要用 `fv upstream refresh` 并经过评审。
