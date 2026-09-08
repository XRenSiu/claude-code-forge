# 失败模式与反模式 —— done_when 会先在哪崩

> 对应 HTML §01①（eval_case 不该只有例子）、§05 陷阱三。落卡前当 checklist。

---

## 三个自带的失败模式

### ① 不可证伪套话（头号病根）

把 Issue 意图直接 paraphrase 成 done_when，产出 `["信号诉求被兑现"]` 这类谁都过、永远红不了的条款。
这正是 dos.yaml 0.1.13 法办的病根（done_when 退化成不可证伪套话）。

→ **对策**：纪律①——形容词全换数字阈值，每条报出一个闸门能读的值；指不出仪器的条款，rewrite 或丢。

### ② 全 happy、无 unhappy（例子之间的缝）

只写该成功什么，把失败语义留空。agent 过了你列的例子，绕过你没列的边界——HTML §05 陷阱三点名的
"eval_case 只写例子不写属性"的任务级根源。

→ **对策**：纪律②——每条 happy 配一条 unhappy 孪生句（`ears_type: unwanted`），互填 `paired_with`；
边界至少覆盖 空/超长/越权/并发/重复/恶意输入。

### ③ 阈值拍脑袋（数字有了但没根）

把"更快"换成"p95 < 50ms"，听起来可证伪了，但 50ms 是从空气里抓的——既非 kpi、非 SLO、非真实失败。
假阈值比假形容词更危险：它伪装成可证伪，却把闸门设在一个无意义的线上。

→ **对策**：阈值必须溯到 Territory.kpi / 一条 SLO / 一次真实 failure_memory；溯不到的标
`needs_semantic_review`，不假装有根。

---

## 承重铁律：把 本次验收 留在任务级，把 常驻不变量 踢上去

每条落卡的 done_when 必须能活不过"未来一次不相关的 Run"——它只为*这次*成立。

> **能活过未来 Run 的不是 done_when，是 常驻不变量。它属于 invariant-extract，不是本卡。**

这是 donewhen-extract 区别于"把所有规则都写进 done_when"的根本分界。done_when 卡不是越积越多的
散文，是越积越多的、带阈值、happy/unhappy 成对、每条可证伪、能按 REQ-ID 追踪的任务级条款。

---

## 边界 / 越权反模式（别把这把刀做成别的刀）

- **别填 常驻不变量 列**：常驻不变量是 invariant-extract 的活。本刀的 §〇 分层闸把 常驻不变量 踢给它。
- **别编译**：把 done_when 下推成 eval_case / fitness fn / rubric 是 spec-compile 的活。本刀止于 SPEC。
- **别校准**：证明 eval_case/rubric 自己对（mutation score / agreement）是 calibrate 的活。本刀产输入，不产证明。
- **别自签合同**：done_when 骑在 Contract 模板上，模板是闸门资产只能人签（R002）；本刀起草，签约走 seam。
- **别让 executor 写自己的验收条件**：生成在 pre-Run、可信侧（Goodhart 墙）；执行会话无权起草 done_when。

---

## 一处理论诚实（引 EARS / Kiro / OpenSpec 时的措辞）

EARS 句式、Kiro 的 SMT 式一致性检查、OpenSpec strict 的缺场景探针，本刀**借其方法**做任务级 本次验收 恢复。
写 decisions.md / 对外解释时，诚实表述为"借 X 的方法做 done_when 恢复"，不要说成"本刀就是 X"。
本刀的独立定位：**invariant-extract 的任务级对称件**——溯因（failure_memory）+ 意图（Issue）双输入，
目的（name+kpi+模板）作取景框，产出 `Contract.done_when`。
