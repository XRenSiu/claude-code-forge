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
parameters: [STOCK, USERS]      # 模型必须定义的常量
observables:                    # 规则只能用这些词
  sold: {type: int, domain: "range(0, 4)"}   # domain 可选：有了它，弱化检测可以精确枚举
  outcome: {type: map}
assumptions: [{id: A1, text: "条件 UPDATE 在数据库里是原子的"}]
properties:
  - {id: NoOversell, kind: invariant, expr: "sold <= STOCK"}
  - {id: SoldNeverDecreases, kind: transition, expr: "post.sold >= pre.sold"}
  - {id: SomeoneCanBuy, kind: reachable, expr: "sold == STOCK"}     # 防空洞：必须能到达
  - {id: Answered, kind: leads_to, forall: {u: USERS}, from: "outcome[u] == 'pending'", to: "outcome[u] != 'pending'"}
  # 其他：eventually（从初始状态最终 Q）、infinitely_often（总能再次 Q）
```

`observables` 的类型（`int bool str set seq map any`）决定轨迹里 JSON 的解读方式。`forall` 的域只能用 parameters。

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

## 策略（fv-policy）

```yaml
schema_version: 1
kind: fv-policy
unclassified: review
risk_classes: {concurrency: {min_level: E3, tier: core}}   # 内置默认还有 consistency permission retry pure ui low
tiers: {core: {max_states: 500000, time_seconds: 900, mutants: true}}   # fast / core / deep 内置默认
modules:
  - {id: ticket-ordering, risk: concurrency, paths: ["src/tickets/**"], contract: …, model: …, source_map: …,
     vectors: …, trace_command: ["python3", "tests/harness.py", "--out", "{out}"], approvals: approvals.jsonl}
```

`trace_command` 是 argv 数组，不经过 shell；`{out}` 会被替换成 CI 输出下的新目录。`approvals` 是 `fv approve` 追加写入的 JSONL，只有它能把对新合同摘要的 WEAKENED 变成 APPROVED。
