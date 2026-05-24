# Step 2 Audit — iter-1-step2-attempt-1

审查对象：`/Users/xrensiu/development/owner/claude-code-forge/specs/forge-skill-validation/iter-1-step2-attempt-1-output.md`
权威源：`/Users/xrensiu/Documents/Downloads/done-when-pipeline.md` **第四章「Step 2:歧义消除」**（仅 4.1 / 4.2 / 4.3 / 4.4 / 4.5）。
辅助源（仅用于核验 skill 内部规约与设计文档 4.4 是否等价）：`plugins/done-when-pipeline/skills/acceptance-spec/references/clarify-protocol.md`。

## 一、设计文档要求清单（逐条对照）

| # | 设计要求（引设计文档原文 / 章节） | Worker 产出是否满足 | 证据 |
|---|---------------------------------|---------------------|------|
| 1 | 4.1 节「通过对话式澄清,把 Step 1 的所有 `[?]` 全部消除」（**硬性**） | yes | Step 1 共 12 个 `[?]`，Worker「决策溯源表」逐条对应到 round/Q，「收敛」段明确「12 个原始 `[?]` 100% 已转化为有溯源的决策，0 个 open」 |
| 2 | 4.2 节「输出 = 所有歧义已消除的 EARS 规格 + 每条决策有溯源」（**硬性**） | yes | 「收敛后的 EARS 规格」段含 REQ-001..REQ-007 七条 EARS，每条尾部都有 `source: round N QK (描述)` 行，覆盖全部新规则与对 REQ-001/REQ-002 的修改子句 |
| 3 | 4.3 节「每轮提问 3-5 个,不能更多(问太多用户会烦)」——**上限 5**（硬性） | yes | Round 1 = 5、Round 2 = 5、Round 3 = 2，三轮均 ≤ 5 |
| 4 | 4.3 节「每轮提问 3-5 个」——**下限 3**（约束力见 P1-1 分析） | no | Round 3 仅 2 题，低于下限。Worker 已自述选择 (B) 用 Rule 6 normal stop 替代凑数（output 第 141 行的「注」） |
| 5 | 4.3 节「2-3 轮收敛,不应超过 5 轮」——**target 2-3 / 上限 5**（硬性上限） | partial | 总 3 轮，落在 target 上限边（≤5 满足硬上限；2-3 target 仍满足，因为 3 ≤ 3） |
| 6 | 4.3 节「超过 5 轮说明需求本身太大,应该拆分」 | n/a | 未触发，3 ≤ 5 |
| 7 | 4.4 节「只允许三类问题：歧义 / 缺失边界 / 未定义术语」（**硬性**） | yes | 12 题分类：`[ambiguity]` ×2（R1Q3、R2Q5）、`[missing edge]` ×6（R1Q4、R1Q5、R2Q1、R2Q2、R2Q3、R3Q1、R3Q2——实为 7 但其中一些 tag 见下条）、`[undefined term]` ×4（R1Q1、R1Q2、R2Q4 — 第 4 类见下条争议、以及……），全部归入三类合法 tag 之一。逐题复核见下方「问题文本逐条 tag 复核」段。Worker 内部 skill 的 `clarify-protocol.md` Rule 1 三类 tag 与设计文档 4.4 三类问题**逐字对应等价**（`[ambiguity]` = 歧义 / `[missing edge]` = 缺失边界 / `[undefined term]` = 未定义术语）。 |
| 8 | 4.4 节「其他类型(如"你想用什么技术栈")属于后续步骤的事,不要提前」（**硬性**） | yes | 12 题全部为需求层问题，无任何「用什么数据库 / push 服务 / 框架 / v1-v2 排期」类提问。Worker 在 round 1 second-order 扫描段主动丢弃了 retry policy 与 mentioner 端 UI 反馈两个候选问题，理由是「implementation choice — drop」「下游 design/planning」，**主动避雷**与 4.4 节意图一致 |
| 9 | 4.2 节「每条决策有溯源」中"每条"的颗粒度——不只是顶层 REQ，还应包括对原 REQ 的修改子句 | yes | REQ-001 内的「thread 内 recipient 约束」子句单独标 `source: round 2 Q3`；REQ-002 内的「DND 定义」「silence 定义」「broadcast 扩展」分别标 round 2 Q4 / Q5 / round 3 Q2；颗粒度符合"每条决策"语义 |
| 10 | 4.5 节样例：澄清后输出含每条 REQ 完整的 EARS 句式（`WHEN ... THE 系统 SHALL ...` / `WHILE ... THE 系统 SHALL ...` / `IF ... THEN THE 系统 SHALL ...`） | yes | REQ-001..REQ-007 全部用完整 EARS 句式：3 个 Event-driven（001、005、006）、1 个 State-driven（002）、3 个 Unwanted（003、004、007）。句式完整 |

### 问题文本逐条 tag 复核（4.4 节合规性细查）

| Round.Q | Worker 标的 tag | 问题主题 | 实质归属 | 是否合规 |
|---------|----------------|---------|---------|---------|
| 1.1 | `[undefined term]` | "@mention" 涵盖范围 | 域名词缺乏精确定义 | ✓ |
| 1.2 | `[undefined term]` | "team chat channel" 涵盖范围 | 域名词缺乏精确定义 | ✓ |
| 1.3 | `[ambiguity]` | "deliver a notification" 投递面 | 同一描述多种合理解读 | ✓ |
| 1.4 | `[missing edge]` | 非成员被提及 | 异常路径未定义 | ✓ |
| 1.5 | `[missing edge]` | 自我提及 | 极端情况未定义 | ✓ |
| 2.1 | `[missing edge]` | 编辑后新增 mention | 异常路径未定义 | ✓ |
| 2.2 | `[missing edge]` | 含 mention 消息被删 | 异常路径未定义 | ✓ |
| 2.3 | `[missing edge]` | thread 内 recipient 范围（second-order） | 派生异常路径 | ✓ |
| 2.4 | `[undefined term]` | DND 定义（multi-select） | 域名词缺乏精确定义 | ✓（虽然候选项 a/b/c/d 是设计要素枚举，但其用途是为 DND 这个域名词框定外延，未滑入"技术栈"类） |
| 2.5 | `[ambiguity]` | "silence" 含义 | 同一描述多种合理解读 | ✓ |
| 3.1 | `[missing edge]` | DND 结束补发 | 异常路径未定义 | ✓ |
| 3.2 | `[missing edge]` | 广播 mention 在 DND 下 | 异常路径未定义 | ✓ |

12/12 全部落在 4.4 节三类问题之内，无越界。

## 二、Issues

### P0（阻断）

无。

设计文档第四章的**硬性约束**全部满足：
- 4.1 12 个 `[?]` 全部消除 ✓
- 4.2 每条决策有溯源 ✓
- 4.3 总轮数 3 ≤ 5（硬上限） ✓ / 每轮 ≤ 5（硬上限） ✓
- 4.4 三类问题限制 ✓ / 无技术栈类越界 ✓

### P1（质量）

**P1-1：Round 3 仅 2 题，低于 4.3 节「每轮 3-5」的下限——判 P1 不判 P0**

- 证据：output 第 137-144 行。Worker 自己识别到「clarify-protocol Rule 2 字面写 "3-5 per round"，本轮只剩 2 题违反 lower bound」，并显式选择方案 (B) 用 Rule 6 normal stop 替代凑数。
- 设计文档 4.3 节原文：「每轮提问 3-5 个,**不能更多**(问太多用户会烦)」——副词「不能更多」明确针对上限，其语义重心是「不超过 5」，下限「3」未带"硬性"语义副词，且 4.3 节并未规定「凑不够 3 题怎么办」的兜底；4.3 节给的另一硬性是「不应**超过** 5 轮」，同样是上限语义。
- 设计文档 4.4 节对问题类型的硬性约束是只允许三类；强凑第 3 题会有两种后果：(a) 从三类中硬找一个原本不必问的题，可能造成"为凑数而问的劣质 question"，反过来威胁 4.4 节问题质量；(b) 把原本 round 2 已可问的题拖到 round 3，违反 clarify-protocol Rule 5（同上下文聚合）。两种后果都加重而非减轻设计意图的破坏。
- 因此本判定：4.3 下限 3 题是**软目标**而非硬约束，Round 3 = 2 题属于 P1 偏离，非 P0 阻断。
- 但仍记为 P1 因为：Worker 实际可以让 round 3 增加 1 题（例如把 round 2 中 Q3 的 thread-scope second-order 推迟到 round 3，给 round 3 凑到 3 题，且 thread-scope 本身确实是 round 1 Q2 的派生 second-order，时间上推迟 1 轮不严重违反 Rule 5）。Worker 没有探讨这一备选，直接跳到 (B)，过程论证略草率。

**P1-2：决策溯源虽逐条都有 source 行，但「关键答复」颗粒度在溯源表中被压缩**

- 证据：output 末尾「决策溯源表」12 行，"关键答复" 列大多写「选 (b)；……」一句话；但部分决策的实质内涵在 EARS 正文 source 行才完整呈现（如 REQ-001 的「thread 约束」其溯源行写「round 2 Q3 (thread participation constraint)」，而表里描述是「(b)；不把整频道成员拖入 thread」，二者颗粒度不一致）。
- 设计文档 4.2 节「每条决策有溯源」并未规定双重表示形式之间必须保持词级一致，所以不构成 P0；但 Step 3 把这部分内容固化到 spec.md / done_when.yaml 时，存在哪一份是"权威溯源"的歧义风险。
- 建议（不修复，仅记录）：合并到单一 provenance 表，或在表中加 EARS 行引用，避免下游消费时取错版本。

**P1-3：REQ-005 / REQ-006 用「event-driven」描述编辑/删除事件，与 Step 1 REQ-001 同属 Event-driven 类，但缺少跨 REQ 的执行优先级关系**

- 证据：REQ-005「WHEN 编辑后新增 mention」要求「apply REQ-001」；REQ-006「WHEN 删除含 mention 消息」要求 retract REQ-001 已产生的通知。两条都以 REQ-001 作为前置依赖。
- 设计文档 4.5 节样例中 REQ-004（试用期取消）是 REQ-001 的并列分支（不同 trigger，独立 action 链），不依赖 REQ-001 的执行结果。Worker 这里把"对 REQ-001 产物的二次操作"也写成 event-driven，与 4.5 样例的"分支"模式偏离。
- 这是 Step 1 audit 中已记的 P1-2（REQ-002 跨 REQ 因果指代）的延续与扩散——Step 2 的 worker 在 Step 1 的范式上又新增了两个跨 REQ 指代（REQ-005、REQ-006），后续 Step 4 派生测试时会形成 fixture 链。
- 但 Step 2 设计文档第四章并未对"跨 REQ 关系"做硬性约束，所以仅记 P1。

### P2（风格）

**P2-1：Round 3 引言段（output 第 139-141 行）把 skill 内部规约（clarify-protocol Rule 2/5/6）的内部权衡过程暴露到 Worker 产出正文**

- 设计文档 4.5 节样例只展示"澄清后的 EARS 规格"，不展示 skill 内部决策记录。
- Worker 把 Rule 2 与 Rule 6 的权衡写在正文里，加大了产出文档的可读负担。这是 Worker 自述风格，不影响下游 Step 3 消费。

**P2-2：「Glossary (working)」在 EARS 规格段尾部出现，但设计文档第四章 4.5 节样例中没有 Glossary 段**

- Glossary 段是 Step 3 spec.md 的标准段落（设计文档 5.3 节列出的 spec.md 是 EARS 规格本体）。
- Worker 自述「will be promoted into spec.md Glossary at S3」并标记 working 状态，意图是为 Step 3 续接做准备，**没有越界**进入 Step 3 的最终产出（未生成 spec.md / done_when.yaml）。但 Glossary 段的存在让 Step 2 输出与 Step 3 输出的边界视觉上模糊。
- 风格偏差，不影响硬约束。

**P2-3：REQ-001 在 Round 1 Q3 应用后，原 Step 1 草稿「deliver a notification」短句被改写为长达 30 余词的复合从句，可读性下降**

- REQ-001 现状：`WHEN a member is @mentioned (where "@mention" includes individual user mentions, broadcast mentions @here/@channel/@everyone, and role-or-group mentions) in a team chat channel (where "team chat channel" means a top-level multi-member channel or a thread within such a channel; 1:1 DMs and group DMs are out of scope of this feature), THE system SHALL attempt delivery ...`
- 设计文档 4.5 节样例对 REQ-001 的清化写法是「精确插入新限定词（WHEN ... 且当前订阅状态为 active）」，而不是「内嵌定义子句到主句」。Worker 把定义放在 REQ 句体的括号里，使 REQ 自带 mini-glossary。
- 这部分定义如果迁移到 Glossary 段（即 P2-2 提到的 Glossary）会更整洁。Step 3 阶段 worker 可以重写，不阻断。

**P2-4：「skill 调用过程简记」段在 Step 2 产出里占 12 行，相当于一份元日志**

- 设计文档 4.5 节样例的 output 只包含"澄清后的 EARS 规格"。Worker 的产出含 4 段元信息：调用过程简记、clarify 循环原始记录、收敛后的 EARS 规格、决策溯源表、任务边界声明。
- 完整记录 Q&A 对下游审查（包括本次 audit）确实有价值，但与 4.5 节样例的极简风格偏离。
- 风格偏差，非约束违反。

## 三、计数

- P0: 0
- P1: 3
- P2: 4

## 四、关键判定纪要（Round 3 = 2 题的 P0/P1 分级证据链）

Caller 在 prompt 中明确要求给出 Round 3 = 2 题 的分级。本节单独留痕。

判定：**P1**。理由链：

1. 设计文档 4.3 节原文：「每轮提问 3-5 个,**不能更多**(问太多用户会烦)」。副词「不能更多」修饰的是上限语义；下限 3 未带强约束副词。
2. 同节另一句：「2-3 轮收敛,不应超过 5 轮」。「不应超过 5 轮」是硬上限；「2-3 轮」是 target。Worker 总轮数 3 严格满足硬上限，且满足 target 上边。
3. 4.3 节括号内解释「(问太多用户会烦)」明确动机是用户负荷过大，方向是从上往下压；没有为"问太少"配置类似的硬动机。
4. 4.4 节问题类型硬性限制只允许三类。如果强行让 round 3 凑到 3 题，Worker 必须从所剩问题以外的范围挖一题；但 output 的 round 2 末扫描显示彼时 open list 已只剩这 2 题。强凑会从两个方向破坏 4.4 硬性：要么编造一个不真歧义/不真 missing edge 的伪问题（违反 Rule 1 "If you tagged a question and it feels like a stretch, drop it"），要么把已应用的答案重新问一遍（违反 4.1 节「全部消除」语义）。
5. 因此 Round 3 = 2 题的偏离方向**对设计意图的破坏小于强凑后的 P0 违反**，分级在 P1 不在 P0。
6. 仍判 P1（不是 0 issue）因 Worker 没有在 round 2 时主动把 Q3（thread-scope second-order）保留到 round 3 以平衡每轮题数；这是过程优化的失误，但不是硬约束违反。
