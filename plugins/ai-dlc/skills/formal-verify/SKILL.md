---
name: formal-verify
description: >-
  给状态性需求做形式化验证，规则与模型由 AI 生成，生成过程本身可检。先从需求原文抽出逐字引用的
  需求清单；再由至少两个互不可见的 AI 生成者各写一份规则合同和一份模型，脚本逐条比较它们的语义
  与可观测行为，分歧交人裁决，另有全新上下文的审阅者对照需求审规则。之后进入统一的验证主干：
  模型检查、变异资格、真实代码轨迹一致性、源码映射漂移、契约弱化检测和风险分级 CI。新需求先建模
  再写代码；已有代码先用当前代码的真实轨迹校准 AI 建的现状模型，再找反例。
  用于“形式化验证”“模型检查”“不变量”“并发 / 一致性 / 幂等 / 超卖 / 重复执行”“TLA+ / Quint”
  “这个设计会不会出错”。纯函数用性质测试，UI 用 E2E，不走这里。
  前置：Python 3.9+（自带 fvkit，仅标准库）；YAML 资产需要 PyYAML；能派发隔离子 agent 的宿主。
argument-hint: "<需求或模块> [--entrance spec-first|code-first] [--slug <aidlc slug>] [--n 2]"
version: 1.1.0
user-invocable: true
---

# Formal Verify：AI 生成规则与模型，脚本检查生成，人裁决分歧

需求定义“应该怎样”，代码描述“实际上怎样”。规则（`fv-contract`）和模型（`fv-model`）**由 AI 生成**，这是流程的必经阶段。
但 AI 写的东西不因为是 AI 写的就可信，所以每一步都留下脚本能检查的产物，而且生成者与检查者是分开的。

检查器 `scripts/fv.py`（fvkit）与 trusted-acceptance 的副本逐字一致，不依赖任何外部引擎就能把
**需求 → 清单 → 规则 → 模型 → 检查 → 实现 → 轨迹一致性 → CI** 跑成闭环。

## 三条不能让步的原则

1. **规则来自需求。** 规则生成者看不到代码，即使是入口 B。“代码现在这样做”不能证明任何事，否则就把已有缺陷合法化了。规则只用合同的 observables 词表写，模型借精化映射接入，改模型改不了规则的含义。
2. **模型贴近现实。** 一个模型动作必须是真实代码里的一个原子步骤，`source-map.yaml` 用逐字锚点把动作钉在代码上。入口 B 的现状模型，要先用当前代码的真实轨迹校准，它找出的反例才算数。
3. **结果按证据分级。** E0–E4 各自只能声称自己那一级（[evidence-levels.md](references/evidence-levels.md)）。生成证据是 E0（证明过程，不证明正确）；`BOUNDED_PASS`、模拟和 `quint run` 都不是 PASS。

## AI 生成阶段（必经，两个入口都要走）

详细协议见 [references/generation.md](references/generation.md)。三个 agent 的提示词就是 `agents/rule-formalizer.md`、`agents/model-builder.md`、`agents/formal-reviewer.md`。

| 步 | 谁 | 产物 | 脚本怎么检 |
|---|---|---|---|
| G-1 需求清单 | `rule-formalizer`（第一个） | `requirements.yaml`：每条 R / A 逐字引用原文；没答案的问题写进 `open_questions` | `fv requirements-check`：引文必须逐字存在；原文里每一句“必须 / 不得 / 不会 / 最终 / 恰好 / must / never”都要落到需求、假设或带引文的 out_of_scope |
| G-2 规则候选 ×N（N≥2） | N 个互不可见的 `rule-formalizer`，只读需求 | `candidates/rules-<k>/contract.yaml` | `fv trace-rules`：每条需求被形式化或有处置（dispositions），每条性质引用真实存在的需求并写明 `text`，每条假设有来源 |
| G-3 规则分歧 | 脚本 | `rules-divergence.json` | `fv rules-divergence`：按需求逐条比较；有有限域的在全域上精确比较并给出见证值，否则按文本比较并标为待人判断；词表和假设的差别也列出 |
| G-4 裁决与采纳 | **人**（委托签须附授权原话） | `fv resolve` 写进报告的 rulings；`contract.yaml` | 采纳的合同必须是被比较过的候选之一（合并出新版本就把它也加进去，重新比较） |
| G-5 全新上下文审阅 | `formal-reviewer`，只读 | `rules-review.yaml` | `fv check-review`：摘要钉住被审的那一版；完成标记的条数等于实际条数（防截断）；阻断发现必须有人裁 |
| G-6 模型候选 ×N（N≥2） | N 个互不可见的 `model-builder`，只读已签合同和设计（入口 A）或代码（入口 B） | `candidates/model-<k>/model.yaml`（入口 B 另带 source-map） | `fv lint` / `fv check` |
| G-7 模型分歧 | 脚本 | `model-divergence.json` | `fv model-divergence`：比较观察者能看到的状态、步骤和规则判定，每处差别附见证路径；内部步数不同而观察不到的，不算分歧 |
| G-8 裁决与采纳 | **人** | rulings；`model.yaml` | 采纳的模型必须在被比较之列；入口 B 另需 `formal calibrate`：现状模型在当前代码轨迹上 CONFORMS |

`fv gen-evidence rules|model` 把上面的结论收成一份回执：READY 或 NOT_READY，并列出理由。
分歧不是失败，是给人的议程；没有裁决的分歧才是失败。

**为什么至少两个。** 一个 AI 写一份规则再自己检查，等于自己给自己打分。两个互不可见的生成者对同一句需求读出不同的东西，那就是需求的含糊处或某一方读错了，这正是需要人看的地方。分歧集来自同样的思路（psl-derive 的 N 次推导、donewhen-extract 的 divergence）。

## 入口 A · 新需求：先建模再写代码

| 步 | 做什么 | 过关条件 |
|---|---|---|
| A1–A2 | G-1 到 G-5：清单、≥2 份规则候选、分歧裁决、审阅 | **FV-G0 = AI-DLC 的 G2**：合同和清单一起签进锁 |
| A3 | G-6 到 G-8：≥2 份模型候选、分歧裁决；很小的范围（两个人、一张票） | 模型生成 READY |
| A4 | `fv check`；有反例就分诊（见下），绝不改弱规则；把被推翻的设计作为 mutant 留在模型里，修正后的模型重新进入 G-7 比较 | **FV-G1**：`fv qualify` 判 QUALIFIED，即完整探索、见证可达、无死动作、必需 mutant 被预期性质杀死 |

## 入口 B · 已有代码：还原现实再找问题

| 步 | 做什么 | 过关条件 |
|---|---|---|
| B1 | G-1 到 G-5，规则生成者**只读需求、不读代码**；清单可以引用事故报告和 `/invariant-extract` 的卡 | 有一组独立于实现的规则 |
| B2–B3 | G-6 到 G-8，`model-builder` 读代码，找出事务和锁的边界，写现状模型和 source-map 候选；`fv source-map verify` 不能有 BROKEN | 关键动作都映射到真实代码 |
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
- **C2 分诊与资格**：分诊只有五类（下表）。改设计由 Agent 起草，改规则必须有授权的人同意，并且重新走一遍 G-2 到 G-5。
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
$S formal generation --slug X --kind rules --divergence …/rules-divergence.json --review …/rules-review.yaml
$S formal calibrate  --slug X --model …/candidates/model-a/model.yaml --traces traces/*.jsonl   # 仅 code-first
$S formal generation --slug X --kind model --divergence …/model-divergence.json
$S formal qualify    --slug X
$S formal conform    --slug X --traces traces/*.jsonl
$S formal status     --slug X
```

| 前置（`--force` 越不过） | 从哪个阶段起 |
|---|---|
| fv 合同和需求清单都在当前 G2/L5 锁里，字节未变 | `cards` |
| 规则生成 READY（每次推进都对当前文件重算） | `cards` |
| 模型生成 READY（code-first 要校准）+ QUALIFIED | `implement` |
| E3 模块：当前的 CONFORMS，映射代码与取证时一致，源码映射此刻 FRESH | `pr` / `merge` |

确实要降级，只能由人签 `formal waive`，并强制走 G3。配了策略时，需要哪些模块由 diff 推出；策略里 E2 以上的模块必须声明 `rules_divergence`、`rules_review`、`model_divergence`（code-first 还要声明 `calibration`）。

## 产物结构

```
specs/<feature>/formal/
  requirements.md            原文（或指向 PRD / issue / done_when）
  requirements.yaml          AI 抽出的清单（逐字引文）
  candidates/rules-*/        规则候选（保留，是记录的一部分）
  rules-divergence.json      分歧 + 裁决
  rules-review.yaml          全新上下文审阅
  contract.yaml              采纳的规则（随 G2 锁）
  candidates/model-*/        模型候选
  model-divergence.json      分歧 + 裁决
  model.yaml · model-scope.md · source-map.yaml · source-map.lock.json · vectors.json · decisions.md
verification/policy.yaml     模块 → 风险 → 证据等级 → CI 层 → 生成证据路径
```

`fv init --dir specs/<feature>/formal --name <feature> --entrance spec-first|code-first` 生成一套骨架（清单、合同、模型都能直接通过检查，`candidates/` 留给生成者）。
完整示例在 `assets/example-ticket/`：清单、两份规则候选（B 漏了“剩余不为负”，并把“答复”读成了“成功”）、两份模型候选（B 允许售罄后重试）、分歧报告与裁决、审阅、初版设计的反例、修正、真实 SQLite 实现与 harness、并发测试、策略、向量。

## 参考

- [references/generation.md](references/generation.md)：AI 生成协议：派发、隔离、清单、比较、裁决、审阅、采纳、校准
- [references/modeling-language.md](references/modeling-language.md)：清单、合同、模型、表达式、语义；轨迹、向量、源码映射、分歧报告、审阅、策略的格式
- [references/evidence-levels.md](references/evidence-levels.md)：E0–E4 各自能声称和不能声称什么；回执字段
- [references/triage-and-maintenance.md](references/triage-and-maintenance.md)：分诊、变异资格、CI 分层、持续校准循环、外部引擎
- [references/open-source.md](references/open-source.md)：借鉴了哪些开源项目、借了什么、没借什么

## 已知边界（如实登记）

- 分歧检查衡量的是**生成者之间是否一致**，不是是否正确：两个生成者可能犯同一个错。全新上下文审阅和人的裁决是另外两道防线，不是可以省掉的步骤。
- 语义比较只在声明了有限 domain 的观测量上是精确的；映射、序列这类没有 domain 的观测量只能按文本比较，结论交人判断。
- 示例里的候选是为演示而撰写的，不是真实隔离 agent 的运行记录。
- 内置检查器是显式状态枚举，不产生 E4。外部引擎适配只对固定格式的样例输出测过，本仓库没有实际运行 TLC / Apalache / Quint / FizzBee。
- 本 Skill 的行为层效果（AI 生成的规则与模型质量）尚未评测，证据等级为 `static_only`。
