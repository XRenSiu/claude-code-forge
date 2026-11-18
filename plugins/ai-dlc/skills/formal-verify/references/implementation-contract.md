# 实现契约（步骤 05）与实现一致性验证（步骤 07）

模型检查通过，只说明**这个设计**在这个范围、这些假设下没有坏路径。它不能说明还没写出来的代码正确，也不能说明写出来的代码按这个设计实现了。这里的两步就是用来弥合这个差距：

```
04 模型检查通过（QUALIFIED）
05 生成实现契约（fv impl-contract）       → 把已验证的设计转成编码 agent 能直接执行的工程约束
06 编码 agent 实现（/implement）           → 任务卡经 formal_ops 绑定到契约操作，按约束写代码
07 验证实现一致性（fv impl-verify）       → 确认真实代码落实了契约，也落实了模型
08 独立自动验收（trusted-acceptance）     → 政策固定模型、合同与实现契约的摘要，重新校验回执
09 持续验证（fv ci）                      → 每次改动都重跑 07
```

两步都执行上游流程（原文在 `upstream/`，对应关系见 [upstream-methods.md](upstream-methods.md)）：

- **05**：Quint `quint-execute-spec` 的 Phase 1–2（每个规格变量和动作在代码里的对应、差距、计划与验证闸）；Specula `instrumentation-spec-format`（每个动作一条：代码位置、触发点、采集字段）；Spec Kit `plan` / `tasks`（数据模型、接口契约、测试先行）；pstack `create-formal-verification-skill`（检查要见过它失败）。
- **07**：Quint `quint-execute-spec` 的 Phase 4（实现后全量验证，绝不放宽规格）；Specula `harness-generation`（只认真实代码的轨迹，每种事件都要覆盖）与 `bug-confirmation` 的复现规则（经公开接口触发，有正负对照）；Spec Kit `analyze`（覆盖缺口、不一致、分级）；pstack `maintain-formal-verification-skill`（代码变了，旧的通过不算数）。

## 05 实现契约：模型定下的，和代码库要回答的

`fv impl-contract draft --model model.yaml --qualification <qualify 回执> --out impl-contract.yaml` 写出骨架，分成两部分。

**derived：模型已经决定的部分，由 fvkit 推导，不能手改。**`fv impl-contract check` 会重新推导一遍，发现被改过就判 NOT_READY。

| 推导项 | 怎么来 | 对编码 agent 意味着什么 |
|---|---|---|
| `reads` / `writes` | 守卫和更新表达式里用到的变量；`v[p]` 和 `update(v, p, …)` 只算参数 p 对应的那一格 | 每个操作碰哪些状态 |
| `read_modify_write.shared` | 整体读、又被同一动作写的变量（例：`buy` 读 `remaining > 0` 又写 `remaining - 1`） | 读和写不能分开：先读后改（check-then-act）必须在一个原子区里 |
| `read_modify_write.per_key` | 同一个参数的格子先读后写（例：`phase[u]`） | 同一个 key 的并发调用不能交错 |
| `atomic_required` 与 `reasons` | 上面两项，或者一个动作同时更新多个变量 | 必须写明原子机制和代码证据 |
| `contended_by` | 其他动作会写本动作读的共享状态 | 必须有并发测试 |
| `fairness` | 模型里的公平性 | 出错时不能悄悄丢弃这个操作 |
| `obligations` | 合同的每条性质、模型的每个 mutant、每条假设 | 都必须有验收项 |

**其余：代码库要回答的部分，由 model-builder（impl-contract 模式）填写。**

| 字段 | 内容 | 检查 |
|---|---|---|
| `state` / `observables` | 每个模型变量对应的代码数据；验收怎么从真实系统读出每个观测量 | 一个不漏 |
| `operations[].code` | 实现在哪个文件、哪个符号 | 07 查文件和符号确实存在 |
| `operations[].atomicity` | 机制（事务、锁、CAS、单条语句）、范围、`evidence`（代码里必须逐字出现的那一句） | 推导要求原子时不能写 `none`；07 查 evidence 在代码里 |
| `operations[].idempotency` | 是否需要；需要时写键和 evidence，不需要时写理由 | 重试会重复执行操作（`model_effect: repeat`）时必须幂等 |
| `operations[].failures` | error / timeout / conflict / retry 四类的行为与 `model_effect` | `model_effect` 只能是 `no_change`、`repeat` 或 `action:<模型动作>`，也就是说失败只能落在模型允许的状态 |
| `operations[].trace` | 事件名（等于动作名）、触发点、采集字段 | 一个动作对应一种事件（Specula） |
| `acceptance.tests` | 性质、并发、MBT、活性、回归、证明测试的 argv，覆盖了哪些性质或操作，`must_fail_with` 是负对照 | 每条性质有对应种类的测试；有冲突的操作有并发测试；至少一个负对照 |
| `acceptance.regressions` | 每个 mutant 由哪条测试或哪个反例重放向量抓住 | 测试要覆盖杀死该 mutant 的性质 |
| `acceptance.assumptions` | 每条假设靠哪条测试或哪次审阅来确认 | 一条不漏 |
| `out_of_scope` | 代码里有、模型不覆盖的行为，以及理由 | 理由必填 |

契约还必须引用一份针对当前模型的 QUALIFIED 回执：没通过模型检查的设计，不往下写实现契约。

## 06 编码 agent 怎么拿到它

- `/plan-cards` 把契约里的每个操作写进恰好一张卡的 `formal_ops`；那张卡的 `allowed_files` 要覆盖操作的 `code.file`，任何卡都不能写实现契约本身（`lint_cards.py` 第 7 项，`advance implement` 自动带上 `--impl-contract`）。
- `/implement` 把这些操作的约束放进卡的输入（`card_context.md` 的“形式化实现契约”一节）。`card-implementer` 按 Quint `quint-execute-spec` 的 Phase 2–4 实现：先写计划，每一步跑对应的验收测试当闸，最后全量验证。契约、模型、合同都只读；做不到就回报 `CONTRACT_CHANGE_NEEDED`，交回设计，不在代码里另做设计。

## 07 实现一致性：五类检查

`fv impl-verify impl-contract.yaml --model model.yaml --review impl-review.yaml [--map source-map.yaml] --out implement.json`

| 检查 | 怎么做 | 不通过意味着 |
|---|---|---|
| 约束落在代码里 | 每个操作的文件与符号存在；atomicity 和 idempotency 的 evidence 逐字出现 | 代码没有落实契约 → `fv_implementation_defect` |
| 测试通过，负对照失败 | 跑每条 `argv`，退出码必须为 0；跑每条 `must_fail_with`，退出码必须非 0 | 实现错了；或者测试看不见它要防的缺陷 |
| 真实操作是模型允许的迁移 | MBT 测试写出的轨迹（`{traces}`）逐步对照模型（部分观测、被拒步、运行时监控）；每个操作至少在一条一致的轨迹里出现过（Specula 的事件覆盖） | 代码做了模型不允许的事，或者某个操作从没被验证过 |
| 反例在真实代码里修复了 | `regressions` 里的重放向量要有一条一致的轨迹：旧反例的那一步在真实代码里被拒 | 反例只在模型里修了 |
| 模型没覆盖的行为、假设 | 全新上下文的 `impl-review.yaml`：每个操作的覆盖行；代码有而模型没有的行为逐条处置（out_of_scope / model_it / defect）；每条假设写 holds / violated / unverified 并给证据；CRITICAL / HIGH 问题必须处理；钉住被审代码的字节 | 模型要补（`fv_model_infidelity`）、代码有缺陷，或者假设不成立（`fv_requirement_gap`） |

结论是 E3 回执（command `implement`，IMPLEMENTS 或 NOT_IMPLEMENTED）。它的理由完全由记录下来的各部分推出，`fv validate` 会重新推一遍；`--rerun` 时还会重查原始轨迹。测试本身不会被验收方重跑，因为验收方不执行候选代码，所以 gate 要求回执绑定到候选提交（`source.head`）。

AI-DLC：`formal impl-contract --file …` 是 `advance implement` 的前置；E3 模块的 `formal impl-verify` 是 `advance acceptance` 的前置。契约或被映射的代码文件一变，前置就失效。`fv ci` 每次都重跑 07。

### 这些检查防的是什么（2026-11-18 自审补上的规则）

| 想蒙混过关的做法 | 规则 |
|---|---|
| 把原子机制删了，只在注释或别的函数里留下 evidence 那句话 | Python 代码按 AST 找到 `code.symbol` 本身，去掉注释和 docstring 后再找 evidence；其他语言退回整文件匹配，回执里记 `scope: file` |
| 负对照写成一条与测试无关、必然失败的命令 | `must_fail_with` 必须是该测试自己的 argv，再加上选择坏变体的参数 |
| 负对照根本没跑起来（命令不存在、超时） | 负对照必须真的以非零退出码结束；启动失败或超时都不算“看见它失败” |
| 故障处理写成“出错就转去另一个动作”，而模型里两者从不同时可能 | `action:<b>` 只有在某个可达状态里 a 与 b 同时可能时才接受（用检查器重算） |
| 轨迹只记一部分字段，动作改坏的那个观测量看不见 | `trace.fields` 必须包含该动作会改变的全部观测量（derived 的 `affects_observables`） |
| 拿外部提供的轨迹充当覆盖 | 外部轨迹照样做一致性检查，但操作覆盖和反例重放只认契约里的测试真正跑出来的轨迹 |
| 审阅里写一个不存在的位置 | `coverage` 和 `unmodeled_behaviors` 的位置必须是存在的 `file:line[-line]` |
| 验证通过后再改弱测试 | 测试命令引用的脚本和数据（如 `vectors.json`）与操作代码一起钉住；变了，`acceptance` 前置就失效 |
| 验证的是工作区里未提交的代码 | 被钉住的文件有未提交改动时判 NOT_IMPLEMENTED：回执记录的提交必须描述被测的字节 |

## 能声称什么，不能声称什么

| 能 | 不能 |
|---|---|
| 实现契约覆盖了模型的每个变量、动作、性质、mutant 和假设，模型定下的部分没有被改写 | 契约里人写的部分（机制、故障行为）一定是对的：它们要经过 07 的代码证据、测试和审阅 |
| 真实代码里有契约要求的原子与幂等机制，测试通过，负对照被抓住，真实操作逐步符合模型 | 所有输入、所有交错下代码都正确（E3 不是 E4） |
| 旧反例在真实代码里被拒绝 | 没有被想到的反例也被修复 |

例子见 `assets/example-ticket/impl-contract.yaml`、`impl-review.yaml`、`impl/test_properties.py`。实现契约在那里带来过一次真实的代码改动：重试必须安全，所以 `purchase` 在事务里先检查请求状态，`request` 改用 `INSERT OR IGNORE`。
