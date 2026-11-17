# fvkit 建模语言与文件格式

所有文件可写 JSON 或 YAML（YAML 需要 PyYAML）。重复键、浮点数、日期和 YAML 标签一律拒绝；摘要取规范化 JSON 的 sha256，所以同一内容写成 JSON 还是 YAML，摘要相同。

## 表达式

Python 语法，数据语义。允许：

- 字面量：整数、字符串、`True` / `False` / `None`，元组或列表（视为序列）、集合 `{a, b}`、映射 `{k: v}`。
- 运算：`+ - * // %`（只用于整数，`+` 也可以拼接序列或字符串），`| & - ^`（集合），比较与 `in`，`and or not`，`x if c else y`，下标与切片。
- 推导式：`[…]` / `{…}` / `{k: v …}` / 生成器。集合和映射总按规范顺序迭代，结果与 Python 哈希随机化无关。
- 函数：`len sum min max abs all any sorted set tuple range update keys values items get remove merge mapof implies powerset choose append head tail last count`。
- 迁移性质里可以用 `pre.<observable>` 和 `post.<observable>`。

不允许：属性访问（`pre.` / `post.` 除外）、`import`、`lambda`、白名单之外的调用、关键字参数、以下划线开头的名字、浮点数、`**`、`<<`、f-string。`range` 最多 10000 个元素；一次运行共用一个时间预算，失控的推导式会报错，而不是让检查器挂住。

函数参数都会先求值，所以 `implies(a, 1 // 0 == 0)` 会报错；要短路请写 `not a or …`。

## fv-contract（权威规则）

```yaml
schema_version: 1
kind: fv-contract
id: ticket-ordering
version: 1                      # 每次改规则递增；摘要另算
requirements: requirements.yaml # 必填：规则追溯到的 fv-requirements 清单（路径不计入摘要）
parameters: [STOCK, USERS]      # 模型必须定义的常量
observables:                    # 规则只能用这些词
  sold: {type: int, domain: "range(0, 4)"}   # domain 可选：有了它，弱化检测可以精确枚举
  outcome: {type: map}
assumptions: [{id: A1, text: "条件 UPDATE 在数据库里是原子的"}]
properties:                      # 每条都写 source（R 编号或列表）与 text（一句自然语言）
  - {id: NoOversell, kind: invariant, expr: "sold <= STOCK", source: R1, text: "成功订单不超过库存"}
  - {id: SoldNeverDecreases, kind: transition, expr: "post.sold >= pre.sold"}
  - {id: SomeoneCanBuy, kind: reachable, expr: "sold == STOCK"}     # 防空洞：必须能到达
  - {id: Answered, kind: leads_to, forall: {u: USERS}, from: "outcome[u] == 'pending'", to: "outcome[u] != 'pending'"}
  # 其他：eventually（从初始状态最终 Q）、infinitely_often（总能再次 Q）
```

`observables` 的类型（`int bool str set seq map any`）决定轨迹里 JSON 的解读方式。`forall` 的域只能用 parameters。
假设的 `source` 指向清单里的 A / R 编号，或写 `environment` / `design`。不形式化的需求写进
`dispositions: [{requirement: R5, status: not_formalizable|out_of_scope|covered_by_tests|covered_by_other_module, reason: …}]`。

## fv-requirements（AI 抽出的需求清单）

见 [generation.md](generation.md#1-需求清单g-1)：`sources`、`requirements` / `assumptions`（每条 `source: {doc, quote}` 或 `{doc, ac}`）、`out_of_scope`、`open_questions`。
摘要覆盖清单本身和每个来源文件的字节：原文一改，清单就要重新确认。

## fv-model（可执行设计）

```yaml
schema_version: 1
kind: fv-model
id: ticket-atomic-reserve
contract: contract.yaml
constants: {STOCK: 1, USERS: ["alice", "bob"]}
variables:
  remaining: {init: "STOCK"}
  phase: {init: "{u: 'idle' for u in USERS}"}
  # 非确定初值：{init_in: "range(0, 3)"}；init_constraint 再过滤
definitions: {free: "remaining > 0"}          # 零元辅助式，按依赖顺序求值
actions:
  buy:
    params: {u: USERS}                         # 参数域可以依赖状态，也可以依赖先声明的参数
    guard: "phase[u] == 'read' and free"
    update: {remaining: "remaining - 1", phase: "update(phase, u, 'done')"}
fairness: [{action: buy, kind: weak, per_params: true}]   # weak / strong；per_params = 对每组参数分别公平
terminal: "all(phase[u] == 'done' for u in USERS)"         # 允许停下的状态；其余无后继状态都算死锁
deadlock: check                                            # 或 allow
observables: {sold: "STOCK - remaining", outcome: "…"}     # 精化映射：模型状态 → 合同词表
model_invariants: [{id: TypeOK, expr: "…"}]                # 设计层不变量，不属于合同
symmetry: [USERS]                                          # 可互换的取值（模型里不得出现它们的字面量）
bounds: {max_states: 200000, max_depth: null, time_seconds: 600}
mutants:                                                   # 负例敏感性：这些错误设计必须被抓到
  - id: check-then-act
    edits: [{op: set_guard, action: buy, expr: "phase[u] == 'read' and seen[u] > 0"}]
    expect_killed_by: [NoOversell]
```

变异操作：`set_guard set_update drop_update drop_action add_action set_init drop_fairness set_observable set_constant`。

### 语义

- 状态是所有变量的取值；一个迁移就是一个动作的一组参数，且守卫为真。所有 update 同时读前状态，没列出的变量保持不变。
- 后继等于自身的迁移是 stutter：既不算“发生过”，也不算“使能”（同 TLA+ 的 `<A>_vars`）。
- 活性按 TLA+ 语义判：任何状态都可以永远停在原地，除非公平性禁止。所以活性性质必须配公平性，否则必然得到“停住”的套索反例。
- 弱公平 WF(A)：若 A 持续使能，最终会发生。强公平 SF(A)：若 A 无限次使能，最终会发生。
- 对称约简只用于安全性；有活性性质时自动关闭，并在结果的 notes 里写明。
- 广度优先保证安全反例最短。`exhaustive_depth` = 长度不超过它的行为已全部检查过。

## 轨迹（fv-trace，JSON Lines）

```json
{"kind": "fv-trace", "schema_version": 1, "model": "ticket-atomic-reserve", "vector": "replay:…"}
{"init": true, "observed": {"sold": 0, "remaining": 1, "outcome": {"alice": "none", "bob": "none"}}}
{"action": "buy", "params": {"u": "alice"}, "observed": {"sold": 1}}
{"action": "buy", "params": {"u": "bob"}, "rejected": true, "observed": {"sold": 1, "remaining": 0}}
```

`observed` 可以只给部分观测量。`rejected` 表示真实代码拒绝了这一步：模型里这一步必须不可使能，观测量也不能变。`--hidden-steps K` 允许事件之间穿插最多 K 个未观测的内部步骤。观测完整的事件还会直接按合同的不变量和迁移性质做运行时监控。

## 测试向量（fv-test-vectors）

`{"vectors": [{"id", "origin", "initial": {观测}, "steps": [{"action": {name, params}, "enabled": bool, "expect": {观测}}]}]}`。
`enabled: false` 表示按当前设计，这一步应当被拒绝。harness 记录真实代码实际做了什么（例如购买返回售罄，就记成 `reject`），对不上的由 `fv trace-check` / `fv conform` 判出。

## 源码映射（fv-source-map）

```yaml
schema_version: 1
kind: fv-source-map
model: model.yaml
root: "."                       # 可选：相对本文件；省略时为 git 仓库根
actions:
  buy:
    atomicity: "BEGIN IMMEDIATE 内一条条件 UPDATE"
    locations: [{path: src/tickets.py, symbol: purchase, anchor: "AND remaining > 0"}]   # anchor 必须逐字存在
environment_actions: {crash: "由测试注入，无对应代码"}
observables: {sold: {locations: [...]}}
protected_paths: ["src/tickets/**"]
```

`sync`（审阅后执行）写入 `source-map.lock.json`：文件摘要、模型摘要、审阅时的提交、审阅人和理由；同时追加一行到 `source-map.sync-log.jsonl`。
`verify` 的结论：FRESH；STALE（受保护路径变了、模型变了、映射被改了、从未同步）；BROKEN（锚点丢失、动作未映射、路径越界）。

## 分歧报告、intake、审阅、brief 与分诊

以下产物都带 `procedure: [{upstream, path, sha256}]`，引用它所执行的上游原文（`upstream/UPSTREAM.json`）。每类产物必须引用哪些原文，由 `fvkit/upstream.py` 的 `REQUIRED` 固定。字段完整的样例都在 `assets/example-ticket/`。

- `fv-rules-divergence` / `fv-model-divergence`（JSON，由 `fv rules-divergence` / `fv model-divergence` 写）：`candidates`（标签、摘要、相对报告的路径）、`items`（D* / M*，含类型、见证）、`rulings`（只由 `fv resolve` 追加：item、ruling、by、signer_kind、authorization、at）。
- `fv-rules-intake`（YAML，Spec Kit clarify + Quint）：`requirements_digest`、`system_model`（actors / communication / failures / time，各有 `answer` 与 `source`）、`ambiguity_scan`（10 类 → Clear / Partial / Missing）、`clarifications`（≤5：id、category、question、answer、by、signer_kind[, authorization]）、`deferred`（category、Deferred / Outstanding、rationale）、`extraction`（requirement、element ∈ entity / operation / property / assumption、text、impact ∈ High / Medium / Low）、`granularity`（requirement、atomic / split、reason）。
- `fv-rules-review`（YAML，schema 2，FVS 审阅契约，写完不再修改）：`contract_digest`、`requirements_digest`、`reviewer: {name, context: fresh}`、`round`（1–3；大于 1 时要有 `prior`）、`surfaces`（7 个审阅面 → `{status: checked, checked, uncertain}` 或 `{status: not_applicable, reason}`）、`findings`（`F-<n>`、severity ∈ BLOCKER / MAJOR / MINOR、class ∈ CONTENT / PROCESS、claim、evidence、suggested_change[, requirement, property]）、`content_coverage`、`verdict` ∈ PASS / APPROVE-WITH-EDITS / REVISE / BLOCKED、`review_complete: {status: complete, findings_count}`。schema 1 不再接受。
- `fv-review-triage`（YAML，作者写在审阅旁边）：`review_digest`（审阅文件字节的 sha256）、`contract_before` / `contract_after`、`reviewed_contract`（合同被改过时，保留被审的那一版）、`dispositions`（finding、FIX / DESCOPE / DEFER-WITH-RULING / REJECT-FINDING / ASK-HUMAN、detail[, evidence, ruling: {text, by, signer_kind[, authorization]}]）。
- `fv-model-review`（YAML，Quint review + Specula 粒度审计）：`model_digest`、`contract_digest`、`reviewer`、`structural`（6 项 → `{result: pass|warn|fail, note[, decision]}`，warn 的 decision 由人签）、`granularity`（每个动作一行：action、source、note，加 6 个布尔值）、`findings`（格式同上）、`review_complete`。运行时检查不由审阅者填写。
- 入口 B：`modeling-brief.md`（Specula 格式第 1–7 节）、`defect-ledger.json`（`{"defects": [{id, location, trigger, wrong_behavior, evidence, category, verification, scenario, known}]}`，与 brief 的 6.2 表一致），以及 `fv-brief-coverage`（YAML：`brief_digest`、`contract_digest`、`scenarios`（scenario、properties、hunt，或 merged_into + reason）、`invariants`（invariant、property，或 out_of_scope）、`findings`（finding、property、hunt））。
- `fv-cex-triage`（YAML，Specula fidelity checklist + bug classification）：`receipt`（带反例的回执，相对路径）、`property`、`preconditions`（precondition、modeled ∈ same / weaker / missing / none，非 none 的要带 `guard: file:line`）、`case` ∈ B / C、`spec_change`（B）、`status` 与 `severity`（C）、`reasoning`。

## 实现契约与实现审阅（05 / 07）

- `fv-impl-contract`（YAML，`fv impl-contract draft` 起草）：`model_digest`、`contract_digest`、`root`、`qualification: {receipt, digest}`、`procedure`、`derived`（fvkit 推导，不可改）、`state[]: {variable, code}`、`observables[]: {observable, read}`、`operations[]: {action, code: {file, symbol}, atomicity: {mechanism, scope, evidence}, idempotency: {required, key, evidence | reason}, failures: {error, timeout, conflict, retry → {behavior, model_effect}}, trace: {event, trigger, fields}[, plan]}`、`acceptance: {tests[]: {id, kind, argv, covers[, must_fail_with, timeout_seconds, receipt]}, regressions[]: {mutant, detected_by: {test | vector}}, assumptions[]: {assumption, evidence: test:<id> | review}}`、`out_of_scope[]: {behavior, reason}`。argv 不经过 shell，`{traces}` 会被替换成 07 的轨迹目录。
- `fv-impl-review`（YAML，formal-reviewer impl 模式）：`impl_contract_digest`、`source: {files: {path: sha256}}`、`procedure`、`reviewer`、`coverage[]: {operation, implemented, location}`、`unmodeled_behaviors[]: {behavior, location, disposition: out_of_scope | model_it | defect, reason}`、`assumptions[]: {assumption, status: holds | violated | unverified, evidence[, ruling]}`、`findings[]: {id, category, severity: CRITICAL | HIGH | MEDIUM | LOW, location, summary, recommendation[, resolution]}`、`review_complete`。

## 策略（fv-policy）

```yaml
schema_version: 1
kind: fv-policy
unclassified: review
risk_classes: {concurrency: {min_level: E3, tier: core}}   # 内置默认还有 consistency permission retry pure ui low
tiers: {core: {max_states: 500000, time_seconds: 900, mutants: true}}   # fast / core / deep 内置默认
modules:
  - {id: ticket-ordering, risk: concurrency, paths: ["src/tickets/**"], contract: …, model: …, source_map: …,
     vectors: …, trace_command: ["python3", "tests/harness.py", "--out", "{out}"], approvals: approvals.jsonl,
     entrance: spec-first, rules_intake: …, rules_divergence: …, rules_review: …, rules_review_triage: …,
     model_divergence: …, model_review: …, impl_contract: …, impl_review: …}   # code-first 另需 calibration、modeling_brief、defect_ledger、brief_coverage
upstream: upstream/UPSTREAM.json   # 可选：收录的上游清单（相对仓库根）；给出时，引用按字节核对
```

E2 以上的模块必须声明 AI 生成证据（`rules_intake`、`rules_divergence`、`rules_review`、`model_divergence`、`model_review`；code-first 还要 `calibration`、`modeling_brief`、`defect_ledger`、`brief_coverage`；E3 还要 `impl_contract`、`impl_review`），`fv ci` 每次重算，E3 模块每次都重跑实现一致性验证。`trace_command` 是 argv 数组，不经过 shell；`{out}` 会被替换成 CI 输出下的新目录。`approvals` 是 `fv approve` 追加写入的 JSONL，只有它能把对新合同摘要的 WEAKENED 变成 APPROVED。
