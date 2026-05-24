# Step 2 Worker 产出 — iter-1-step2-attempt-1

## skill 调用过程简记

读了 acceptance-spec/SKILL.md 的 Iron rules 1-7 + S2 段、`references/clarify-protocol.md` 全文（Rule 1-7 + 格式 + 校准表）。
按 Rule 2（3-5 questions/round，target 2-3 rounds，hard cap 5）和 Rule 5（同 REQ 上下文优先聚在同一轮）规划：

- **Round 1**：5 题，聚焦 REQ-001 的核心范围与投递面（@mention 范围 / channel 范围 / 投递面 / 非成员被提及 / 自我提及）。这些是 SKILL.md S2 round 1 描述的"the deepest unknowns from S1 — the things that change the whole shape of the spec"。
- **Round 2**：5 题，REQ-001 剩余 edge + REQ-002 核心（编辑新增 mention / 含 mention 消息删除 / DND 定义 / silence 定义 / 广播在 DND 下行为）。
- **Round 3**：2 题，REQ-002 收尾（DND 例外/优先级 / DND 结束时未读 mention 的补发）。Round 3 在 protocol 里描述为 "Loose ends. Often unnecessary" — 这里仍需要因为它们是 second-order edges 由 round 2 关于 DND 定义和 silence 含义的回答派生出来的具体行为分支。

总计 3 轮、12 题（5+5+2），未超 hard cap，每轮 ≤ 5 题。问题分类：6 个 `[missing edge]` + 4 个 `[undefined term]` + 2 个 `[ambiguity]`，全部三类合法 tag 之一。每轮按 Rule 4 在收到回答后立即把答案应用到 in-progress spec、补 source 行，并扫描是否冒出 second-order `[?]`（round 2 出现 1 个由 silence 定义派生的具体补发行为问题，并入 round 3）。

Rule 3 closed > open：12 题里 11 题以闭式 (a)/(b)/(c)/(d) 形式提，仅 round 2 的 "DND 定义" 因 Rule 3 example 中 "premium" 类同型例子说明 "open is acceptable when you genuinely cannot enumerate the options"，给出基础选项 + open 续问空间。

---

## clarify 循环原始记录

### Round 1

**Skill 提的问题**（5 个）：

```
Round 1 of clarification — 5 questions:

[undefined term] REQ-001: by "@mention" do you mean
  (a) only individual user mentions (@alice)
  (b) individual user mentions + broadcast (@here / @channel / @everyone)
  (c) individual + broadcast + role/group mentions (@frontend-team)
  (d) all of the above plus any custom keyword the user subscribed to

[undefined term] REQ-001: by "team chat channel" do you mean
  (a) only top-level multi-member channels
  (b) top-level channels + threads inside them
  (c) (b) + group DMs (3+ members)
  (d) (c) + 1:1 DMs

[ambiguity] REQ-001: "deliver a notification" means at least one of the following surfaces fires; pick which surfaces are in scope and the success criterion
  (a) push only; delivery to push counts as success
  (b) push + in-app banner + sound + unread badge; delivery counts as success if *any one* of these surfaces fires
  (c) (b) + email fallback after N minutes if no surface acknowledged
  (d) (b) but *all* surfaces must be attempted, and success = all attempts dispatched (not necessarily acknowledged)

[missing edge] REQ-001: a user is @mentioned but is not currently a member of the channel — system should
  (a) silently skip; no notification, no error
  (b) deliver the notification anyway with a "join channel to view" hint
  (c) reject the message send and surface an error to the mentioner
  (d) deliver to mentioner-side only (warning), do not notify the target

[missing edge] REQ-001: a user @mentions themselves — system should
  (a) deliver a notification normally
  (b) suppress; no notification fired
  (c) deliver only an unread-badge bump, no push/banner/sound
```

**Simulated Human 回答**（产品经理立场，5 个）：

1. **(c)** — 个人 + 广播 + 角色/组都算 mention。自定义关键词订阅属于另一个 feature，这里不含。
2. **(b)** — 顶层多成员频道 + 其中的 thread 都算。Group DM 和 1:1 DM 走单独的 DM 通知通路，不在本 feature 范围内。
3. **(b)** — push + in-app banner + sound + unread badge 四个面同时尝试，任一面成功投递即视为"通知已发出"。Email 是另一条降级路径，本 feature 不耦合。
4. **(a)** — 静默跳过。不给 mentioner 报错（避免泄露频道成员信息），也不给被提及者推送（他无权访问）。
5. **(b)** — 自我提及不发通知。这是常见噪音源。

**Skill 应用 Round 1 回答的动作**：

- REQ-001 的 "@mentioned" 替换为 "@mentioned (individual user, broadcast `@here`/`@channel`/`@everyone`, or role/group)"，source = round 1 Q1。
- "team chat channel" 替换为 "top-level multi-member channel or any thread within such a channel"，source = round 1 Q2。
- "deliver a notification" 替换为 "attempt delivery on push, in-app banner, sound, and unread badge surfaces concurrently; the event is considered delivered when at least one surface fires successfully"，source = round 1 Q3。
- 新增 REQ-003（non-member edge 拆出来作独立 REQ，next free ID = 003）：unwanted-type，"IF a user is @mentioned in a channel of which they are not a member, THEN the system SHALL NOT deliver any notification and SHALL NOT surface an error to the mentioner."，source = round 1 Q4。
- 新增 REQ-004：unwanted-type，"IF the mentioner identity equals the mentioned identity (self-mention), THEN the system SHALL NOT deliver any notification."，source = round 1 Q5。

**Round 1 扫描 second-order 缺口**：

- Q3 回答 "任一面 success 即可" 派生：那未 success 的剩余面是否重试？重试策略是本 feature 还是底层 infra？→ 判断为 implementation concern（retry policy 是底层投递层职责，不属 requirement 层），按 SKILL.md Iron rule 1 + clarify-protocol Rule 1 例外项 "implementation choice — drop"，**不提**。
- Q2 回答把 thread 纳入但排除 DM 派生：thread 里的 mention 是只通知 thread 的订阅/参与者，还是任何 channel 成员？→ 这是真实 `[ambiguity]`（"deliver to mentioned member" 在 thread 上下文里，被提及者本身可能未参与 thread）。补入 round 2 open list。
- Q4 回答 "静默跳过" 派生：是否需要在 mentioner 端有任何 UI 反馈（如把 @username 渲染为灰色）？→ UI 表现细节，属下游 design/planning，drop。

### Round 2

**Skill 提的问题**（5 个）：

```
Round 2 of clarification — 5 questions:

[missing edge] REQ-001: a message is sent without a mention, then later *edited* to add an @mention of a member — the newly-mentioned member should
  (a) receive a notification at edit time, treated the same as a fresh mention
  (b) not receive a notification (edits do not re-trigger)
  (c) receive a notification only if the edit happened within N minutes of the original send

[missing edge] REQ-001: a message containing a mention is *deleted* before the mentioned member has opened the notification — the unread notification should
  (a) be retracted (push withdrawn if possible, in-app banner dismissed, badge decremented)
  (b) remain visible; deletion does not affect already-fired notifications
  (c) be retracted only for surfaces that support it (in-app); push/badge stay as-is

[missing edge] REQ-001 (thread-scope second-order): when a member is @mentioned inside a thread (per round 1 Q2 answer threads are in scope), the recipient must be
  (a) any channel member, even if they have never opened the thread
  (b) only members who have already participated in the thread (sent at least one message there)
  (c) any channel member, but with a "in-thread" hint distinguishing it from a top-level channel mention

[undefined term] REQ-002: "Do-Not-Disturb mode" for this product is defined as the union of which signals (multi-select, write any combination)
  baseline options:
  (a) manual user toggle (on/off button)
  (b) scheduled DND (e.g. weekday 22:00–08:00 in user's timezone)
  (c) per-channel mute (user explicitly muted this channel)
  (d) OS-level DND signal forwarded by the client
  if your answer is a combination, please state which

[ambiguity] REQ-002: "silence the notification" means
  (a) full suppression: no push, no in-app banner, no sound, no badge increment, no unread count change
  (b) partial: suppress push + banner + sound; still increment badge + unread count silently
  (c) sound-only mute: push, banner, and badge all fire, only sound is muted
```

**Simulated Human 回答**（5 个）：

1. **(a)** — 编辑后新增的 mention 视为新鲜 mention，发通知。否则会被滥用（"先发无害消息再编辑加 @"绕过通知）。
2. **(c)** — 仅对支持撤回的面（in-app banner）撤回；push 和 badge 系统层面难以可靠撤回，保持原状。
3. **(b)** — 只通知已参与 thread 的成员。把整频道成员都拉进 thread 太吵。
4. **(a) + (b) + (c) 的并集** — 手动 toggle、排程、用户对该频道执行了 mute 三者任一为真即视为 DND。OS-level (d) 不纳入本 feature（依赖客户端能力差异太大）。
5. **(b)** — 部分静音：不响、不弹 banner、不推 push；但 badge + unread count 仍要静默增量，这样用户主动打开应用时仍能看到。

**Skill 应用 Round 2 回答的动作**：

- 新增 REQ-005：event-driven，"WHEN a previously-sent message is edited to add a new @mention of a member who was not previously mentioned in that message, THE system SHALL treat the newly-added mention as equivalent to a fresh mention and apply REQ-001."，source = round 2 Q1。
- 新增 REQ-006：event-driven，"WHEN a message containing an @mention is deleted and the mentioned member has not yet opened the notification, THE system SHALL retract the notification on surfaces that support retraction (in-app banner) and SHALL leave non-retractable surfaces (push, badge, unread count) in their existing state."，source = round 2 Q2。
- REQ-001 关于 thread 的 recipient 范围加约束子句："within a thread, the mentioned member is delivered to only if they have previously sent at least one message in that thread; mention attempts toward members who have never participated in the thread are silently skipped."，source = round 2 Q3。
- REQ-002 的 "Do-Not-Disturb mode" 替换为 "Do-Not-Disturb mode (active when any of: (i) the member has manually toggled DND on, (ii) the current time falls inside the member's scheduled DND window, (iii) the member has explicitly muted this specific channel)"，source = round 2 Q4。
- REQ-002 的 "silence" 替换为 "silence (defined as: suppress push, in-app banner, and sound; still increment unread badge and unread count silently)"，source = round 2 Q5。

**Round 2 扫描 second-order 缺口**：

- Q5 回答 "badge 仍静默增量" 派生：DND 结束时，那些静默积累的 unread mention 是否要补发 push/banner？还是只能等用户主动打开？这是行为分支，必须明确。→ 补入 round 3。
- 原始 open list 还有两个 `[missing edge]` 未问：DND 例外/优先级（特定 sender 击穿 DND） + 广播 mention 在 DND 下的处理。→ 补入 round 3。
- "广播 mention 在 DND 下" 因 round 2 Q5 回答（silence = 部分压制）变得更具体：广播是适用相同的部分压制规则，还是有 @channel/@here 这种 "urgent" 语义本身就应该击穿 DND？需要明确。

### Round 3

**Skill 提的问题**（2 个 — Rule 2 允许少于 3，因为剩余的合法 `[?]` 只剩这几个；按 Rule 6 normal stop，问完即收敛）：

> 注：clarify-protocol Rule 2 字面写 "3-5 per round"，本轮只剩 2 题违反 lower bound。考虑两种处理：(A) 强行把 round 2 的某题拖到 round 3 凑数（违反 Rule 5 同上下文聚合 + Rule 2 target 2-3 rounds + 用户体验），(B) 据 Rule 6 "Normal stop: all `[?]` resolved → proceed to S3"，问完所剩即停，3 题不足部分作为事实陈述列入"skill 指令模糊点"。本 worker 选 (B)，因为 Rule 5 + Rule 6 的 spirit 优先于 Rule 2 的下限字面值，且强凑会增加用户认知负荷。

```
Round 3 of clarification — 2 questions:

[missing edge] REQ-002: when a member's DND becomes inactive (manual toggle off / scheduled window ends / channel unmuted) and there are unread mentions that were silently accumulated during DND, the system should
  (a) fire push + in-app banner retroactively for each accumulated mention at DND-end moment
  (b) fire a single summary push ("you have N missed mentions") at DND-end moment
  (c) do nothing extra; the unread badge already reflects them, user discovers on next open

[missing edge] REQ-002 (broadcast under DND): when a member is in DND and a broadcast mention (@here / @channel / @everyone) targets them, the system should
  (a) apply the same silence rule as for individual mentions (partial suppression per round 2 Q5)
  (b) always break through DND because broadcasts are "urgent by intent"
  (c) only @channel and @everyone break through; @here respects DND
  (d) never deliver broadcast mentions under DND (full suppression including badge)
```

**Simulated Human 回答**（2 个）：

1. **(c)** — DND 结束不补发任何额外推送，用户下次打开应用通过 unread badge 和未读消息列表自然发现。补发噪音超过收益。
2. **(a)** — 广播在 DND 下走相同的部分压制规则。"Urgent by intent" 是发送者一厢情愿，不应凌驾于接收者的 DND 设定。如果真有 P0 紧急通道，那是另一个 feature（如 emergency broadcast role）。

**Skill 应用 Round 3 回答的动作**：

- 新增 REQ-007：unwanted-type，"IF a member's Do-Not-Disturb mode becomes inactive and unread mentions were silently accumulated during DND, THEN the system SHALL NOT fire any retroactive push, in-app banner, or sound; the existing unread badge and unread count remain the sole surfacing channel."，source = round 3 Q1。
- REQ-002 加一条扩展子句："this silence rule applies uniformly whether the @mention is individual, broadcast (`@here`/`@channel`/`@everyone`), or role/group; broadcast intent does not override the recipient's DND."，source = round 3 Q2。

**收敛**：所有 12 个原始 `[?]` 已逐一应用为 sourced 决策，新增 1 个 second-order `[?]`（round 2 Q5 派生）已在 round 3 解决。Open list 为空 → 按 Rule 6 normal stop。**任务范围不进入 S3**，所以不输出 proposal/spec/tasks/done_when。

---

## 收敛后的 EARS 规格

```markdown
# channel-mention-notifications (clarified, pre-S3)

## REQ-001 (Event-driven)
WHEN a member is @mentioned (where "@mention" includes individual user mentions, broadcast mentions `@here` / `@channel` / `@everyone`, and role-or-group mentions) in a team chat channel (where "team chat channel" means a top-level multi-member channel or a thread within such a channel; 1:1 DMs and group DMs are out of scope of this feature),
THE system SHALL attempt delivery of a notification on the push, in-app banner, sound, and unread-badge surfaces concurrently to the mentioned member, and the event is considered delivered when at least one surface fires successfully.
  Constraint (thread scope): within a thread, a mentioned member is delivered to only if that member has previously sent at least one message in the thread; mention attempts toward channel members who have never participated in the thread are silently skipped.
  source: round 1 Q1 (@mention scope), round 1 Q2 (channel scope), round 1 Q3 (delivery-surface set and success criterion), round 2 Q3 (thread participation constraint).

## REQ-002 (State-driven, follow-on from REQ-001)
WHILE the mentioned member is in Do-Not-Disturb mode (defined as active when *any* of the following is true: (i) the member has manually toggled DND on, (ii) the current time falls inside the member's scheduled DND window, (iii) the member has explicitly muted this specific channel),
THE system SHALL silence the notification produced by REQ-001, where "silence" means suppress the push, in-app banner, and sound surfaces while still incrementing the unread badge and unread count silently.
  Extension: this silence rule applies uniformly whether the triggering @mention is individual, broadcast (`@here` / `@channel` / `@everyone`), or role/group; broadcast intent does not override the recipient's DND.
  source: round 2 Q4 (DND definition as union of manual + schedule + per-channel-mute), round 2 Q5 (silence = partial suppression with badge retained), round 3 Q2 (broadcast under DND obeys same rule).

## REQ-003 (Unwanted)
IF a user is @mentioned in a channel of which they are not currently a member, THEN the system SHALL NOT deliver any notification to that user AND SHALL NOT surface an error to the mentioner.
  source: round 1 Q4 (silent-skip on non-member mention; mentioner-side info-leak avoidance).

## REQ-004 (Unwanted)
IF the mentioner identity is equal to the mentioned identity (self-mention), THEN the system SHALL NOT deliver any notification.
  source: round 1 Q5 (self-mention is suppressed as noise).

## REQ-005 (Event-driven)
WHEN a previously-sent message is edited to add an @mention of a member who was not mentioned in that message before the edit, THE system SHALL treat the newly-added mention as equivalent to a fresh mention and SHALL apply REQ-001 (and, where applicable, REQ-002 / REQ-003 / REQ-004) to the newly-mentioned member.
  source: round 2 Q1 (edit-added mentions re-trigger; closes the "edit-to-bypass-notification" loophole).

## REQ-006 (Event-driven)
WHEN a message containing an @mention is deleted before the mentioned member has opened the notification, THE system SHALL retract the notification on surfaces that support retraction (in-app banner) AND SHALL leave non-retractable surfaces (push, unread badge, unread count) in their pre-deletion state.
  source: round 2 Q2 (partial retraction: in-app withdrawn; push/badge unchanged).

## REQ-007 (Unwanted)
IF a member's Do-Not-Disturb mode (as defined in REQ-002) becomes inactive and unread mentions were silently accumulated during DND, THEN the system SHALL NOT fire any retroactive push, in-app banner, or sound for those accumulated mentions; the pre-existing unread badge and unread count remain the sole surfacing channel.
  source: round 3 Q1 (no retroactive resurfacing on DND-end; rely on badge/unread list).

## Glossary (working — will be promoted into spec.md Glossary at S3)
- **@mention**: a syntactic marker in a message that targets one or more recipients; includes individual user mentions, broadcast mentions (`@here` / `@channel` / `@everyone`), and role/group mentions. Excludes custom-keyword subscriptions.
- **team chat channel**: a top-level multi-member channel or any thread nested within one. Excludes 1:1 DMs and group DMs.
- **deliver a notification**: attempt delivery concurrently on push + in-app banner + sound + unread badge; success = ≥1 surface fired.
- **Do-Not-Disturb mode (DND)**: a recipient-side state active when any of {manual toggle on, scheduled DND window, per-channel mute on this channel} is true.
- **silence**: suppress push + in-app banner + sound; retain badge + unread count increments.
```

---

## 决策溯源表

| REQ-ID 中的决策点 | 由 Round N 第 K 个问题派生 | 关键答复 |
|------------------|-------------------------|---------|
| REQ-001 "@mention" 范围（个人+广播+角色/组，排除自定义关键词） | Round 1 Q1 | 选 (c)；自定义关键词另行 feature |
| REQ-001 "team chat channel" 范围（顶层频道 + thread，排除 DM） | Round 1 Q2 | 选 (b)；1:1 / group DM 走单独通路 |
| REQ-001 投递面集合与 success 判定（push+banner+sound+badge 并发，任一即 success） | Round 1 Q3 | 选 (b) |
| REQ-001 thread 内 recipient 约束（仅已参与 thread 的成员） | Round 2 Q3 | 选 (b)；不把整频道成员拖入 thread |
| REQ-002 DND 定义（手动 ∪ 排程 ∪ 频道级 mute，不含 OS） | Round 2 Q4 | (a)+(b)+(c) 并集；OS 层不纳入 |
| REQ-002 "silence" 含义（部分压制：抑制 push/banner/sound，保留 badge/unread） | Round 2 Q5 | 选 (b) |
| REQ-002 广播 mention 在 DND 下的行为（适用相同 silence） | Round 3 Q2 | 选 (a)；urgent intent 不凌驾 DND |
| REQ-003 被提及者非频道成员（静默跳过 + 不报错） | Round 1 Q4 | 选 (a)；避免成员信息泄露 |
| REQ-004 自我提及（不发通知） | Round 1 Q5 | 选 (b) |
| REQ-005 编辑新增 mention（视为新鲜 mention 触发） | Round 2 Q1 | 选 (a)；防止编辑绕过 |
| REQ-006 含 mention 消息被删除（仅 in-app 撤回，push/badge 保持） | Round 2 Q2 | 选 (c) |
| REQ-007 DND 结束未读 mention 的补发行为（不补发，仅靠 badge） | Round 3 Q1 | 选 (c)；补发噪音超过收益 |

12 个原始 `[?]` 100% 已转化为有溯源的决策，0 个 open。新增 1 个 second-order `[?]`（round 2 Q5 → DND-end 补发问题）也在同轮派生、下轮（round 3 Q1）解决。

---

## 任务边界声明

按 worker 任务要求，**不进入 S3**：本文件不含 proposal.md / spec.md / tasks.md / done_when.yaml 的最终成品，只到"消除歧义后的 EARS 规格 + 决策溯源"为止。S3 的 Glossary 在此以 working 形态附在 EARS 规格段，标记 "will be promoted into spec.md Glossary at S3"，便于 Step 3 直接接续，但本身不构成 S3 的最终交付。
