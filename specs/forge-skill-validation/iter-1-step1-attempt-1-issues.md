# Step 1 Audit — iter-1-step1-attempt-1

审查对象：`/Users/xrensiu/development/owner/claude-code-forge/specs/forge-skill-validation/iter-1-step1-attempt-1-output.md`
权威源：`/Users/xrensiu/Documents/Downloads/done-when-pipeline.md` 第三章 + 附录 A + 11.1 节关于 `acceptance-spec` 的设计要求。

## 一、设计文档要求清单（逐条对照）

| # | 设计要求（引设计文档原文 / 章节） | Worker 产出是否满足 | 证据 |
|---|---------------------------------|---------------------|------|
| 1 | 3.2 节「输入：自然语言需求描述,可以非常粗糙」 | yes | Worker 在「skill 调用过程简记」隐式描述了 NL 输入 `@mention + 团队聊天频道 + DND` |
| 2 | 3.2 节「输出：EARS 格式草稿 + `[?]` 标记的歧义清单」 | yes | 输出含「EARS 草稿」段（REQ-001 / REQ-002）+「Open questions」+「歧义清单」三段，`[?]` 共 12 处 |
| 3 | 3.1 节「把模糊的自然语言需求**强行**塞进 EARS 五种句式之一」 / 附录 A.1 五种句式定义 | yes | REQ-001 标 `Event-driven` 用 `WHEN ..., THE system SHALL ...`；REQ-002 标 `State-driven` 用 `WHILE ..., THE system SHALL ...`，均落在附录 A.1 的五种之一 |
| 4 | 附录 A.2「多句式组合允许」 | yes | REQ-001 + REQ-002 拆成两条 REQ，是合规的多 REQ 拆解（虽 REQ-002 内并未做单条多型嵌套，符合允许范围） |
| 5 | 3.1 / 3.5 节「目标是把隐藏的歧义逼出来」「LLM 没有你脑子里的隐含上下文,所以它会问那些你想当然的问题」 | yes | 12 条 `[?]` 覆盖：@mention 范围（个人/广播/角色）、频道范围（DM/thread/sub-channel）、通知投递面（push/banner/sound/badge/email/OS）、DND 定义、静音粒度、被提及者非成员、自我提及、编辑触发、消息删除时的撤回、DND 优先级击穿、DND 结束补发、广播 mention 在 DND 下的特殊路径——隐含上下文被有效暴露 |
| 6 | 11.1 节「每条 EARS 必须有唯一 ID」 | yes | `REQ-001`、`REQ-002` 唯一 ID 都在 |
| 7 | 3.4 节样例顶头格式：`# Feature: <slug> (draft)` | 部分 | Worker 写成 `# channel-mention-notifications (draft)`，漏掉 `Feature:` 前缀 |
| 8 | 3.4 节样例每条 REQ 块格式：`## REQ-NNN (<EARS type>)` | yes | `## REQ-001 (Event-driven)` / `## REQ-002 (State-driven, follow-on from REQ-001)`，主结构一致；REQ-002 加了「follow-on from REQ-001」是附加说明，不违反 |
| 9 | 3.4 节样例 `[?]` 格式：`[?] "…"的具体时刻: …?` 冒号+问号引出问题 | 部分 | Worker 用 `[?] [tag] (question)` 括号包裹 + 三类 tag 标注。三类 tag 来自 acceptance-spec skill 自己的 Iron rule 1（与设计文档 4.4 节 Step 2 的三类问题限制对齐，提前打 tag 不违反 Step 1 约束），但括号写法与设计文档 3.4 节样例文体不一致 |
| 10 | 3.4 节样例「歧义清单」用单一 `## 待澄清歧义` 段 | 部分 | Worker 出现三处等价信息：(a) REQ 句式中间内嵌 12 个 `[?]`，(b) `## Open questions` 重列 12 条，(c) `## 歧义清单` 中文按 tag 分组再列一遍。语义无冲突但冗余 |
| 11 | EARS 句式选择应贴合附录 A.1 的语义（State-driven = 系统处于某状态时的持续行为；Unwanted = IF condition, THEN action） | 部分 | REQ-002 实质语义是「mention 触发后，**如果**接收者处于 DND，**则**静音」，更接近 Unwanted (`IF in DND, THEN silence`)；用 `WHILE` 在语法上成立但 action 是一次性的 silence 单条 notification，不是 State-driven 描述的「持续行为」（参附录 A.1 例：`WHILE 离线, 存本地队列`） |
| 12 | REQ 之间应可独立派生测试（隐含于 Step 4 各句式 → 测试映射，附录 A.1 每种句式都标了独立的派生测试类型） | 部分 | REQ-002 action 写成「silence the notification produced by REQ-001」，把 REQ-002 的可验证主体绑死在 REQ-001 的产物上。设计文档 3.4 节样例的 REQ-001 / REQ-002 是平行的，REQ-002 用独立条件 `WHILE 订阅状态为 cancelled_active`，没有跨 REQ 因果指代 |
| 13 | 不越界进入 Step 2（外部约束 + 设计文档 4.1 / 4.2 描述 Step 2 是 clarify 循环） | yes | Worker 明确未发起 clarify 提问；末尾说明「立刻进入 S2 round 1 的指示——本次任务明确限定不进入 S2」 |
| 14 | 不越界进入 Step 3（不应产出 proposal.md / spec.md / tasks.md / done_when.yaml） | yes | 仅输出 draft + 歧义清单，未产出 Step 3 的四件套 |

## 二、Issues

### P0（阻断）

无。

设计文档第三章的硬性约束（EARS 五种句式之一、有 `[?]` 标记、有 EARS 草稿、有唯一 ID、不越界）全部满足。

### P1（质量）

**P1-1：REQ-002 句式语义选择牵强（State-driven vs Unwanted）**
- 证据：REQ-002 写作 `WHILE the mentioned member is in Do-Not-Disturb mode, THE system SHALL silence the notification produced by REQ-001`。
- 设计文档附录 A.1 对 State-driven 的定义是「描述系统处于某状态时的**持续行为**」，例：`WHILE 用户处于离线状态, THE 系统 SHALL 把操作存入本地队列`——动作是持续机制（任何操作都进队列）。
- 设计文档附录 A.1 对 Unwanted 的定义是「描述错误条件下的处理」，模板 `IF [condition], THEN THE 系统 SHALL [action]`，例：`IF API 调用超时, THEN 重试`。
- Worker 的 REQ-002 实质是「mention 触发的瞬间，如果接收者恰好在 DND 状态则压制单条通知」——是一次性条件分支，而非持续行为，更接近 Unwanted 的 `IF [in DND], THEN [silence this notification]`。
- 选 State-driven 在语法上成立但 action 不是「持续的」，与附录 A.1 给的范式偏离。

**P1-2：REQ-002 跨 REQ 因果指代，损害可独立派生测试性**
- 证据：REQ-002 action 写成 `silence the notification produced by REQ-001`，使 REQ-002 的验证物（Step 4-B 单元 / 4-C 集成）必须先复现 REQ-001 的执行链路才能验证。
- 设计文档 3.4 节样例（subscription-cancellation 的 REQ-001 / REQ-002）：REQ-002 用独立状态条件 `WHILE 订阅状态为 cancelled_active`，action 是独立的「显示过期提示」，两个 REQ 平行可独立派生测试。
- 附录 A.1 给 State-driven 派生的是「状态机 PBT」，前提是 REQ 自身的状态-动作映射是闭合的；Worker 写法把状态-动作链拆到两个 REQ 跨引用，后续 4-B 派生时会形成 fixture 耦合。
- 第三章并未明文禁止跨 REQ 引用，所以不构成 P0；但相对于设计文档 3.4 节样例确立的「REQ 之间应平行」范式，质量上有偏差。

### P2（风格）

**P2-1：草稿头部漏 `Feature:` 前缀**
- 设计文档 3.4 节样例：`# Feature: subscription-cancellation (draft)`。
- Worker：`# channel-mention-notifications (draft)`。
- 不影响下游消费，纯命名规约偏差。

**P2-2：`[?]` 后问题书写格式与样例不一致**
- 设计文档 3.4 节样例：`[?] "当前计费周期到期"的具体时刻:用户时区午夜?UTC 午夜?`（引号包名词 + 冒号 + 候选答案并列以问号结尾）。
- Worker：`[?] [tag] (does this cover only direct user mentions, or also @here / @channel / ...?)`（三类 tag + 括号包问题）。
- Worker 风格来自其 skill 自身规约（Iron rule 1 三类 tag），是 acceptance-spec skill 的合规扩展，不算违反设计文档，但文体与样例不一致。

**P2-3：歧义清单三份冗余**
- Worker 同时给出：(a) REQ 句式中间内嵌 12 处 `[?]`、(b) `## Open questions` 段列 12 条、(c) `## 歧义清单` 中文按 tag 分组再列。
- 设计文档 3.4 节样例只用一段 `## 待澄清歧义`。
- 内嵌 + 汇总两段已经足够；再加按 tag 分组的中文汇总属于装饰性冗余。

**P2-4：草稿正文中英文混排不统一**
- EARS 句体用英文（`WHEN a member is @mentioned ...`），但 `## 歧义清单` 段切换中文。
- 设计文档 3.4 节样例也是中英混排（EARS 体英文，注释中文），所以不算违反，但 Worker 把 Open questions 用英文、歧义清单用中文，做了两次平行翻译，进一步加重 P2-3 的冗余感。

## 三、计数

- P0: 0
- P1: 2
- P2: 4
