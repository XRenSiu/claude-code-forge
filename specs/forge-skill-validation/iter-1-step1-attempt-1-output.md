# Step 1 Worker 产出 — iter-1-step1-attempt-1

## skill 调用过程简记

读了 acceptance-spec/SKILL.md（S0/S1 段落、Iron rules 1-7、Phase map）、`references/ears-syntax.md`（五种句型 + cheat-sheet + 多型组合范例 + 常见错误表）、`references/clarify-protocol.md`（三类合法 tag + 标注校准表）、`references/output-templates/spec-template.md`（REQ 块结构）。按 SKILL.md S0 静默完成 bootstrap（feature-slug 推断为 `channel-mention-notifications`，scope = 多模块：频道 / 提及解析 / 通知投递 / 用户 DND 偏好），然后按 S1 把需求拆成 EARS REQ 并对每个模糊点打 `[?]` 并强制以 `[ambiguity] / [missing edge] / [undefined term]` 三类之一打 tag（Iron rule 1）。未进入 S2（按指令不发起 clarify 轮次）。

需求被分解为两个 REQ：mention → notification（Event-driven）与 DND 状态下的静音行为（State-driven，作为 REQ-001 的 follow-on，遵循 ears-syntax.md "Multi-type composition" 范式 Event + State 复合）。

## EARS 草稿

```markdown
# channel-mention-notifications (draft)

## REQ-001 (Event-driven)
WHEN a member is @mentioned [?] [undefined term] (does this cover only direct user mentions, or also @here / @channel / @everyone / @<role-or-group>?) in a team chat channel [?] [undefined term] (does "team chat channel" include 1:1 DMs, group DMs, threads, and sub-channels, or only top-level channels with multiple members?),
THE system SHALL deliver a notification [?] [ambiguity] (what delivery surface(s) qualify as "a notification" — push, in-app banner, sound, unread badge, email, OS-level — and is one surface enough or must all be attempted?) to the mentioned member [?] [missing edge] (what if the mentioned identity is not currently a member of the channel — silently skip, deliver anyway with channel-access hint, or surface an error to the mentioner?).

## REQ-002 (State-driven, follow-on from REQ-001)
WHILE the mentioned member is in Do-Not-Disturb mode [?] [undefined term] (how is DND defined for this product — manually toggled, schedule-based, per-channel override, OS-level, or a combination?),
THE system SHALL silence the notification produced by REQ-001 [?] [ambiguity] (does "silence" mean suppress all surfaces including badge/unread count, suppress only audible+banner while keeping badge+unread, or only mute sound?).

## Open questions

- [?] [undefined term] REQ-001: scope of "@mention" — does broadcast (@here / @channel / @everyone) and group/role mention count, or only individual user mentions?
- [?] [undefined term] REQ-001: scope of "team chat channel" — DMs / group DMs / threads / sub-channels included or only top-level multi-member channels?
- [?] [ambiguity] REQ-001: what counts as "a notification" — which delivery surface(s) (push / in-app banner / sound / badge / email / OS), and is delivery to any one surface sufficient?
- [?] [missing edge] REQ-001: mentioned identity is not currently a channel member — silently skip, deliver-with-access-hint, or error to mentioner?
- [?] [missing edge] REQ-001: self-mention (a user @mentions themselves) — does it produce a notification or is it suppressed?
- [?] [missing edge] REQ-001: mention added by editing an existing message — does the edit re-trigger notification for the newly mentioned member?
- [?] [missing edge] REQ-001: message containing the mention is deleted before the mentioned member opens the notification — does the notification get retracted/recalled or remain?
- [?] [undefined term] REQ-002: definition of "Do-Not-Disturb mode" — manual toggle, schedule, per-channel mute, OS-level DND, or a union of these?
- [?] [ambiguity] REQ-002: definition of "silence" — full suppression (no badge, no banner, no sound, no unread surfacing), partial (only audible+banner suppressed, badge+unread retained), or sound-only mute?
- [?] [missing edge] REQ-002: priority/override path — can a member designate certain senders or @channel-class mentions to break through DND, and if so what's the default?
- [?] [missing edge] REQ-002: DND ends while the mention is still unread — does the previously silenced notification fire retroactively at that moment, surface only as a badge, or stay fully silent?
- [?] [missing edge] REQ-002: broadcast mentions (@here / @channel / @everyone) under DND — same silencing rule as direct @user mention, or different (e.g. always suppress, or always break through)?
```

## 歧义清单

汇总（与上面 Open questions 等价，按 tag 分组以便 S2 分轮）：

**`[undefined term]`（3 条）**
1. REQ-001 — "@mention" 的范围（个人 / 广播 / 角色 / 群组）
2. REQ-001 — "团队聊天频道" 的范围（DM / 群 DM / thread / 子频道）
3. REQ-002 — "勿扰模式" 的定义（手动 / 排程 / 频道级 / OS 级）

**`[ambiguity]`（2 条）**
4. REQ-001 — "通知" 指哪些投递面（push / banner / sound / badge / email / OS），任一即可还是全部尝试
5. REQ-002 — "静音" 指完全压制（含 badge/unread）/ 仅压制声音+banner 保留 badge / 仅静音

**`[missing edge]`（7 条）**
6. REQ-001 — 被提及者不在频道
7. REQ-001 — 自我提及
8. REQ-001 — 通过编辑消息新增 mention
9. REQ-001 — 含 mention 的消息在被查看前被删除
10. REQ-002 — DND 例外/优先级（特定发送者或 @channel 类是否可击穿）
11. REQ-002 — DND 结束时未读 mention 的补发行为
12. REQ-002 — 广播类 mention（@here / @channel / @everyone）在 DND 下的处理是否与个人 @ 相同

共 12 个 `[?]`，全部已按 Iron rule 1 用三类合法 tag 之一标注，无法归入三类的潜在问题（如"是否要做埋点 / 选哪个推送服务 / 是 v1 还是 v2"）已主动丢弃。S1 校准检查满足（开口问题数 12 远大于 3 的最低门槛）。

## skill 还要求的其他产出（如果有）

S1 在 SKILL.md 中明确列出的产出只有两块：
- 一个固定 markdown shape 的 draft（已在 "EARS 草稿" 段给出，含 `# <feature-slug> (draft)` / `## REQ-NNN (<EARS type>)` / `## Open questions` 三段）
- "立刻进入 S2 round 1" 的指示——本次任务明确限定不进入 S2，故未发起 clarify 提问。除此之外 SKILL.md S1 段不要求其他副产物。

S0 期间产生的状态（feature-slug、output_dir、scope 判断）SKILL.md 标注为 "Do not produce text output yet"，因此严格按 spec 没有作为正式产出输出，仅在 "skill 调用过程简记" 中以背景说明带过。
