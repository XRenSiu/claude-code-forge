---
name: formal-verify
description: >-
  给状态性需求做形式化验证，两个入口共用一条验证主干。新需求先把规则写成合同、建可执行模型、
  做模型检查和变异资格判定，再交给实现；已有代码先独立取得规则，从源码还原行为模型、找反例，
  并在真实代码里重放。验证主干包括真实代码的轨迹一致性、源码映射漂移检测、契约弱化检测和
  风险分级 CI。用于“形式化验证”“模型检查”“不变量”“并发 / 一致性 / 幂等 / 超卖 / 重复执行”
  “TLA+ / Quint”“这个设计会不会出错”。纯函数用性质测试，UI 用 E2E，不走这里。
  前置：Python 3.9+（自带 fvkit，仅标准库）；YAML 资产需要 PyYAML。
argument-hint: "<需求或模块> [--entrance spec-first|code-first] [--slug <aidlc slug>]"
version: 1.0.0
user-invocable: true
---

# Formal Verify — 规则可审、模型可跑、代码可重放、CI 可追溯

需求定义“应该怎样”，代码描述“实际上怎样”。检查器在模型里找反例；验收则追问真实代码是否同样遵守规则。
本 Skill 自带检查器 `scripts/fv.py`（fvkit，与 trusted-acceptance 的副本逐字一致），不依赖任何外部引擎就能把
**需求 → 合同 → 模型 → 检查 → 实现 → 轨迹一致性 → CI** 跑成闭环。已有 TLA+ / Quint / FizzBee 资产时用
`fv external` 接入，结论按同一套证据等级记录。

## 三条不能让步的原则

1. **规则来自需求。** 即使从代码建模，也不把“代码现在这样做”当作正确标准，否则就把已有缺陷合法化了。合同（`fv-contract`）只用 observables 词表写性质，模型不能借改自己的内部变量让检查变绿。
2. **模型贴近现实。** 模型里的一个动作必须是真实代码里的一个原子步骤（一个事务、一次条件更新）。拆得太细会产生真实世界不可能的反例，合得太粗会漏掉真实的交错。`source-map.yaml` 写明每个动作的代码位置和原子性，并用逐字锚点钉住。
3. **结果按证据分级。** E0 静态审阅、E1 模拟、E2 模型检查、E3 实现验收、E4 代码级证明，各自只能声称自己那一级的结论（见 [references/evidence-levels.md](references/evidence-levels.md)）。`BOUNDED_PASS`、模拟和 `quint run` 都不是 PASS；检查没跑、跑失败、映射过期，都只能报 blocked 或 unknown。

## 先判断要不要做（按风险分配强度）

| 模块性质 | 默认强度 | 承载 |
|---|---|---|
| 并发、一致性、权限、重试与幂等 | E3：模型检查 + 变异资格 + 源码映射 + 真实轨迹一致性 | 本 Skill |
| 纯函数、算法 | E1–E4：性质测试，关键算法可上代码级证明 | `/test-suite-generator` 的 PBT 层 / 外部证明器 |
| UI、体验 | 运行时 E2E | Project Harness |
| 普通低风险修改 | 不强制 | — |

写成 `verification/policy.yaml`（`fv-policy`）后，`fv impact --base <ref>` 会从 git diff 推出这次改动触及哪些模块。
是否触及由 diff 决定，不由作者声明：漏报一个模块不等于跳过一道检查。

## 入口 A · 新需求：先建模再写代码

| 步 | 做什么 | 产物 | 过关条件 |
|---|---|---|---|
| A1 理解需求 | 参与者、事件、状态、正常与异常结果；问清“成功”指什么，以及超时、重试、取消、重复请求各怎么算 | `requirements.md`（`fv init --entrance spec-first`） | 每条承诺都能说清：在什么前提下、什么事件发生后、必须或不得出现什么结果 |
| A2 提升为独立规则 | invariant / transition / reachable（防空洞）/ leads_to（活性）；环境假设显式写进 `assumptions` | `contract.yaml` | **FV-G0**：规则由人审定。在 AI-DLC 里就是 G2，把 fv 合同和 `done_when.yaml` 一起锁 |
| A3 状态与原子动作 | 很小的范围（两个人、一张票）；`fv lint` → `fv check` | `model.yaml` + `model-scope.md` | 每个动作可执行，没有死动作，可达见证能到达 |
| A4 检查、分诊、修设计 | 有反例先分诊（见下文），绝不改弱规则；把旧设计作为 mutant 留在模型里 | `decisions.md`、qualify 回执 | **FV-G1**：`fv qualify` 判 QUALIFIED，即完整探索、见证可达、无死动作、必需 mutant 都被预期规则杀死 |

## 入口 B · 已有代码：还原现实再找问题

| 步 | 做什么 | 产物 | 过关条件 |
|---|---|---|---|
| B1 独立取得正确性标准 | 从 PRD、接口契约、事故报告、`/invariant-extract` 的卡整理规则；区分“代码事实上这么做”和“业务要求必须这么做” | `requirements.md` 的事实/要求对照表、`contract.yaml` | 有一组独立于实现的规则；“代码目前就是这样”不能证明任何事 |
| B2 行为地图 | 关键文件、调用链、锁与事务边界、重试和失败窗口；从历史缺陷中提炼失效场景 | `source-map.yaml`（动作 ↔ 代码，逐字锚点） | `fv source-map verify` 没有 BROKEN；审阅后 `sync` |
| B3 实现模型 | 保留故障、并发、重试这些关键动作；不能被代码实现的动作写进 `environment_actions` 并说明原因 | `model.yaml` | 关键动作都映射到真实代码 |
| B4 找反例并重放 | `fv check` 找到反例后，`fv gen-tests --strategy counterexamples` 生成重放向量，用 harness 在真实代码里跑出轨迹 | 回执、向量、轨迹、`decisions.md` | 能在真实代码里重放的才是缺陷；不能重放的，先质疑模型假设 |

## 统一验证主干（两个入口汇合后相同）

```bash
FV="python3 $SKILL_DIR/scripts/fv.py"
$FV check   --model model.yaml --out r/check.json          # C1 模型检查（E2）
$FV qualify --model model.yaml --out r/qualify.json        # C2 设计门槛：资格判定
$FV gen-tests --model model.yaml --strategy transitions,counterexamples \
    --counterexample r/old-design-check.json --out vectors.json        # C3 模型驱动测试向量
python3 impl/harness.py --vectors vectors.json --out traces/           # 项目自己的 harness 驱动真实代码，记录轨迹
$FV conform --model model.yaml --map source-map.yaml --traces traces/*.jsonl --out r/conform.json   # C4（E3）
$FV ci --policy verification/policy.yaml --base origin/main --out ci-out/   # C5 每次 PR：影响分析 + 分层重验
```

- **C1 模型检查**：广度优先的完整探索，给最短反例；活性在弱/强公平下判，反例是套索。`--max-states` / `--max-depth` 截断时报 `BOUNDED_PASS`，并写明 `exhaustive_depth`。
- **C2 反例分诊与资格**：分诊结论只有五类，写进 `decisions.md`，再交给路由（见 [references/triage-and-maintenance.md](references/triage-and-maintenance.md)）。改设计可以由 Agent 起草；改规则必须有授权的人同意。
- **C3 实现或修复**：实现以已审定的合同为准，不能为了通过检查放宽条件。只重跑模型不能证明改过的代码正确。
- **C4 真实代码独立验收**：真实轨迹必须逐步符合同一个模型，被拒绝的步骤要在轨迹里体现为拒绝，完整观测的事件同时按合同做运行时监控。并发场景另配真实的并发测试（例子见 `assets/example-ticket/impl/test_concurrency.py`）。
- **C5 持续维护**：受保护文件一变，源码映射就 STALE。契约变了要做弱化检测，向量的模型摘要变了要重新生成。`fv ci` 只要有一项没跑、跑失败或已失效，就判 UNSATISFIED。

## 反例分诊（结论只有五种）

| 分类 | 判据 | 谁处理 | AI-DLC 信号 |
|---|---|---|---|
| `requirement_gap` 需求漏项 | 规则没覆盖这种情况，需要产品决定 | 需求负责人：新合同版本，经 G2 变更提案 | `fv_requirement_gap` → task |
| `model_infidelity` 模型失真 | 反例在真实代码里不可能发生（原子边界拆错、漏了约束） | 建模者修模型和映射，重新 qualify | `fv_model_infidelity` → plan |
| `design_defect` 设计缺陷 | 模型如实反映了设计，而设计本身允许坏结果 | 改设计；旧设计留作 mutant | `fv_design_defect` → plan |
| `implementation_defect` 实现缺陷 | 反例或非一致轨迹在真实代码里重放成功 | 实现者修代码；重放向量留作回归 | `fv_implementation_defect` → card |
| `checker_defect` 检查器或环境问题 | 引擎缺失、超时、harness 错误 | 维护检查器或环境；不让产品返工 | `fv_checker_defect` → exception |

另有两种信号由脚本产生，不经人分诊：`fv diff-contract` 判出弱化（`fv_contract_weakened` → task，必须重签），源码映射过期（`fv_model_stale` → plan）。

**最需要避免的反模式**：模型检查失败 → 实现者把 `sold <= 1` 改成 `sold <= 2` → 检查变绿 → 宣称完成。
在 AI-DLC 里这条路被三处堵住：fv 合同在 G2 锁里；`formal check` 比对锁内摘要；trusted-acceptance 的政策固定规则摘要。

## AI-DLC 接线

```bash
S="python3 $AI_DLC/scripts/aidlc_state.py"
$S formal configure --slug X --contract specs/x/formal/contract.yaml --model specs/x/formal/model.yaml \
    --source-map specs/x/formal/source-map.yaml --min-level E3        # 或 --policy verification/policy.yaml
$S formal qualify  --slug X        # 跑 fv qualify，回执存到项目外 artifacts 目录并按摘要登记
$S formal conform  --slug X --traces traces/*.jsonl
$S formal status   --slug X        # 当前要求、证据、哪里过期
```

- `advance cards` / `advance implement`：fv 合同必须在当前 G2/L5 锁里，摘要一致；`implement` 还要求 qualify 回执有效（QUALIFIED，且模型和合同摘要等于当前文件）。
- `advance pr` / `advance merge`：min_level 是 E3 时，还要求 conform 回执有效，并绑定当前 HEAD 和当前源码映射（FRESH）。
- 这些前置和 verification 接入一样**不能用 `--force` 越过**。确实要降级（比如这次只做到 E2），用 `formal waive --by <人> --signer-kind human --reason …` 留下记录，G3 时必看。
- 配了 policy 时，需要哪些模块由 `fv impact` 对 `branch.base` 的 diff 推出，而不是由执行者声明。
- trusted-acceptance 的政策 schema 2 可以固定同一份模型和合同的摘要，并在受保护环境重算。见 trusted-acceptance 的 `references/formal-evidence.md`。

## 产物结构（建议）

```
specs/<feature>/formal/   requirements.md · contract.yaml · model.yaml · model-scope.md
                          source-map.yaml · source-map.lock.json · decisions.md · vectors.json
                          counterexamples/ · approvals.jsonl
verification/policy.yaml  模块 → 风险 → 证据等级 → CI 层
.github/workflows/formal-verification.yml   assets/formal-verification.yml 改路径即可用
tools/fvkit/              fv vendor --to tools/fvkit 的自包含副本（CI 不依赖插件安装位置）
```

`fv init --dir specs/<feature>/formal --name <feature> --entrance spec-first|code-first` 生成一套能直接 qualify 的骨架。
完整的抢票示例在 `assets/example-ticket/`：初版设计的反例、修正、真实 SQLite 实现（含故意保留的 check-then-act 变体）、harness、并发测试、策略、向量。

## 参考

- [references/modeling-language.md](references/modeling-language.md)：合同、模型、表达式、语义（同时更新、stutter、公平、对称）；轨迹、向量、源码映射、策略的格式
- [references/evidence-levels.md](references/evidence-levels.md)：E0–E4 各自能声称和不能声称什么；回执字段
- [references/triage-and-maintenance.md](references/triage-and-maintenance.md)：分诊、变异资格、CI 分层、持续校准循环、外部引擎
- [references/open-source.md](references/open-source.md)：借鉴了哪些开源项目、借了什么、没借什么

## 已知边界（如实登记）

- 内置检查器是显式状态枚举：小范围精确，大范围靠对称约简与有界探索，并如实标为有界。它不做符号或无界证明，也不产生 E4。
- 外部引擎适配（TLC / Apalache / Quint / FizzBee）只用固定格式的样例输出测过解析，本仓库没有实际运行这些引擎；FizzBee 的输出格式没有对照真实安装核实。
- 轨迹一致性证明的是“这些轨迹符合模型”，不是“所有执行都符合”；轨迹的来源可信度由运行它的环境决定。
- 本 Skill 的行为层效果（带 / 不带它时 Agent 的建模质量）尚未评测，证据等级为 `static_only`：结构过审，加上脚本与示例在 fixture 上端到端跑通。
