# Given/When/Then —— 把 Issue 意图压成可证伪的 本次验收条件

> 本册是 donewhen-extract 的承重判断面。落卡前当 checklist。对应操作册 HTML §02-A、§04②。

---

## 〇、先分层：本次验收 还是 常驻不变量（KAOS 时序逻辑）

每条候选先过一道分层闸，问一句话：

> **这条规则，能不能活过这个 Territory 一次未来的、不相关的 Run？**

- **能** → 它对*每个* Run 都成立 = 常驻不变量。**不是本刀的产物，移交 invariant-extract。**
- **只对这次任务成立** → 本次验收，"这次要达成" = `done_when`。留下，继续往下压。

把 常驻不变量 塞进 done_when，等于重演 dos.yaml 0.1.13 法办的那个病根（责任级/任务级两层混淆）。
分层裁断偏向：**宁可踢给 invariant-extract，也不要把任务条款误当常驻法**——前者会被 invariant-extract
按目的重新接住，后者会让每个 Run 都被一条只该管这次的条款卡住。

---

## 一、Given/When/Then 形态 + EARS 表面语法

每条 done_when 是一个三元谓词，落到 EARS 句式的表面：

```
Given  <前置/上下文>           # 状态前提：WHILE <state>
When   <触发>                  # 事件触发：WHEN <event> / IF <condition>
Then   <可证伪的可观测结果>     # THE SYSTEM SHALL <observable outcome>
```

EARS 五型（落 `ears_type`，帮 spec-compile 选验证原型）：

- **ubiquitous**：无触发、恒成立的（`THE SYSTEM SHALL …`）——多半其实是 常驻不变量，回到 §〇 复查。
- **event**：`WHEN <事件> THE SYSTEM SHALL …`——任务级主力句型。
- **state**：`WHILE <状态> THE SYSTEM SHALL …`。
- **unwanted**：`IF <不该发生的> THEN THE SYSTEM SHALL <拒绝/降级/报错>`——unhappy 孪生句的家。
- **optional**：`WHERE <特性开启> THE SYSTEM SHALL …`。

形态是机械的（`assets/done_when_card.yaml` 的 given/when/then/ears_type 槽位）；**内容是判断**。

---

## 二、三条纪律（操作册点名的承重三件，HTML §02-A「纪律」）

### 纪律① 形容词全换数字阈值

形容词是验收条件的头号杀手——它把"可证伪"偷换成"可争辩"。

| 散文（不可证伪） | done_when（可证伪，落 `threshold`） |
|---|---|
| 接口"更快" | `WHEN 并发 1000 THE SYSTEM SHALL 返回 p95 < 200ms` |
| 结果"稳定" | `WHILE 持续 1h 压测 THE SYSTEM SHALL 错误率 = 0` |
| 覆盖"大部分" | `THE SYSTEM SHALL 覆盖 ≥ 95% 的 REQ-ID` |
| "尽快"重试 | `IF 首调失败 THEN THE SYSTEM SHALL 在 ≤ 3 次内重试后报错` |

铁律：**一条你指不出仪器去读的条款，是套话，不是验收条件。** 每条存活条款必须报出一个闸门能读的值。
阈值来源必须可溯：Territory 的 `kpi`、一条 SLO、或一次真实失败——**从空气里抓的数字标 `needs_semantic_review`**，
不要假装它有根。

### 纪律② 每条 happy 配一条 unhappy

只写"该成功什么"的条款，把失败语义留空——那正是 agent 钻空子的缝（过了例子，绕过边界）。

对每条 `WHEN <happy> THE SYSTEM SHALL <succeed>`，起草配对的
`IF <unhappy/边界/恶意输入> THEN THE SYSTEM SHALL <reject/降级/报错>`（`ears_type: unwanted`），
并在两条之间互填 `paired_with`。

裁断偏向：**宁可把 unhappy 路写满，也不要留它隐含。** 边界类型至少覆盖：空/超长/越权/并发/重复/恶意输入。

### 纪律③ 出口跑矛盾检查 + 覆盖检查

落卡不是终点，出口要证明这组条款**自洽且够全**——见 `references/contradiction-coverage.md`。
机械半（成对矛盾扫描 + 触发覆盖扫描）由 `verify_done_when.py` 跑；SMT 级一致性与缺场景的语义判
是 judge/tool call（抄 Kiro 的 SMT 式校验；退而用 OpenSpec strict 查缺场景）。

---

## 三、意图扫描（机械采集的输入面）

候选条款从三处采，不止 Issue 一处：

1. **Issue / Signal 意图本身**——主输入，但只给 happy 方向，需经纪律①②加工。
2. **该模板/领地的 `failure_memory`（末 N 条）**——每条坏样本是一条天然的 unhappy 候选 + 一个
   `based_on` 锚（复利溯源）。这是把"上次翻的车"变成"这次的验收条款"的通道。
3. **契约模板的历史 done_when**——继承已稳定的 REQ-ID，不重造；新条款追加，旧条款收紧。

采集是机械的（engine 可跑）；分层（§〇）、加工（§二）、出口（§三纪律③）是判断，不焊进固定步序。

---

## 四、与 acceptance-spec / OpenSpec / Kiro 的关系（诚实标注）

本刀的 EARS 句式与 strict 缺场景探针，**精神上**借自 acceptance-spec 类通用工具与 OpenSpec strict；
矛盾检查的 SMT 式思路借自 Kiro。写 decisions.md 时诚实表述为"借其方法做任务级 本次验收 恢复"，
不要说成"本刀=acceptance-spec"。本刀的定位是 **invariant-extract 的任务级对称件**：产出 `Contract.done_when`，
止于 SPEC，不编译（那是 spec-compile）、不校准（那是 calibrate）。
