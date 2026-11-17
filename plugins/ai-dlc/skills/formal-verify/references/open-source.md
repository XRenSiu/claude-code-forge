# 借鉴的开源项目：借了什么，没借什么

fvkit 没有复制下列项目的代码。借的是方法与工作形状，自己实现成一个零依赖、可以自闭环的工具，同时保留接入这些工具的通道。各项目的能力和命令以其当前版本为准。

| 项目 | 借了什么 | 在 fvkit / 本 Skill 中的对应物 | 没借 / 区别 |
|---|---|---|---|
| [GitHub Spec Kit](https://github.com/github/spec-kit)（[agentic SDD](https://github.com/github/spec-kit/blob/main/docs/reference/agentic-sdd.md)） | specify / clarify：先澄清需求、列待决问题，再写规格 | A1 / B1 的 `requirements.md` 模板；AI-DLC 的 `/issue` 与 `/donewhen-extract` | 不是数学验证器；本仓库已有需求流程，不重复安装 |
| [Quint](https://github.com/quint-co/quint)（[checking properties](https://quint.sh/docs/checking-properties)） | 状态机加不变量加见证（witness）的建模方式；`run` 是模拟、`verify` 是有界模型检查 | `reachable` 性质防空洞；`simulate` 只给 E1；`quint run` 的适配器永不报 PASS | 不实现 Quint 语言；用 `fv external` 接入现有 `.qnt` |
| [Quint LLM Kit](https://github.com/quint-co/quint-llm-kit)（[quint-modeling](https://github.com/quint-co/quint-llm-kit/blob/main/quint-llm-kit-plugin/skills/quint-modeling/SKILL.md)） | 由 LLM 从需求（from-requirements）或代码（from-code）生成模型；规格优先 | `rule-formalizer` / `model-builder` 两个生成 agent；入口 A / 入口 B；`fv init --entrance` | 生成之后加了单个生成者没有的检查：逐字引文、≥2 份隔离生成的语义比较、裁决、全新上下文审阅 |
| [Specula](https://github.com/specula-org/Specula)（[workflow](https://github.com/specula-org/Specula/blob/main/skills/workflow-overview.md)） | code-analysis → spec-generation（AI 从源码生成模型）→ harness-generation → validation → bug-confirmation；用真实执行轨迹校准模型 | `model-builder`（入口 B 读代码写现状模型与 source-map）；`formal calibrate`（现状模型在当前代码轨迹上 CONFORMS 才可信）；反例重放向量（bug-confirmation） | 不需要 32GB 内存或 Java 工具链；生成的模型不止一份：≥2 份隔离生成在可观测层面比较 |
| [pstack](https://github.com/cursor/plugins/tree/main/pstack)（[create](https://github.com/cursor/plugins/blob/main/pstack/skills/create-formal-verification-skill/SKILL.md) / [maintain](https://github.com/cursor/plugins/blob/main/pstack/skills/maintain-formal-verification-skill/SKILL.md)） | 受保护文件、sync commit、“模型仍描述代码吗”的维护循环；故意制造坏实现确认验证仍能抓住 | `source-map.lock.json` 加 sync-log；mutant 资格；`fv ci` | 不生成项目专属 Skill；统一用 `fv` 与本 Skill |
| [TLA+ AgentSkills](https://github.com/tlaplus/AgentSkills) 与 [TLA+ 工具](https://lamport.azurewebsites.net/tla/tools.html) | TLC 的语义：stutter、`WF` / `SF`、`<A>_vars`、对称集、死锁检查、覆盖率 | 检查器的活性与公平语义、对称约简（活性时自动关闭）、死动作报告 | 不实现 TLA+；用 `fv external --engine tlc` 接入 |
| [FizzBee](https://github.com/fizzbee-io/fizzbee) | 上手容易的状态机描述；模型驱动测试（MBT） | Python 表达式写的模型；`fv gen-tests` 生成的向量供真实代码重放 | 适配器只解析 PASSED / FAILED，没有对照真实安装核实 |
| [Formal Verification Skills](https://github.com/Beneficial-AI-Foundation/formal-verification-skills) | 全新上下文的只读审阅者（fresh reviewer）；trust-audit：证明依赖哪些假设 | `formal-reviewer` agent + `fv check-review`（完成标记防截断、阻断发现须裁决）；合同 `assumptions` 显式化并追溯到清单；`diff-contract` 把新增假设判为弱化 | 不提供 Lean / Aeneas（E4 只能来自外部） |
| [fast-check](https://fast-check.dev/) | 性质测试把规则落到真实输入上 | 风险分流：纯函数走 `/test-suite-generator` 的 PBT 层；随机向量 `--strategy random` | 不是穷举证明 |

## 本仓库额外补上的部分（上述项目各自没有覆盖的组织边界）

- **规则与模型分权**：性质只能用合同的 observables 词表写；模型通过精化映射接入。改模型不能改变规则的含义。
- **弱化检测**：`fv diff-contract` 在有限域上精确判断，没有有限域时在模型及其自动变异的状态上抽样判断，并标明是抽样。
- **证据等级进入数据**：回执自带 `evidence_level` 与 may / may-not claim；有界、模拟、未完成都有独立的 verdict 和退出码。
- **可重算的证据**：反例与见证可在模型里重放；`--rerun` 重跑后逐项比较；trusted-acceptance 的 gate 在受保护环境用原件重算。
- **与 AI-DLC 状态机的硬接线**：合同进 G2 锁；`advance implement` 要求 QUALIFIED；`advance pr/merge` 要求 E3 证据且绑定当前候选。这些都不能被 `--force` 越过。
