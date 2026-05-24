# Step 3 Worker 产出 — iter-1-step3-attempt-2

## skill 调用过程简记

按指示**重新读取**了 skill 当前版本的源码，未参考 attempt-1 的 schema 直觉：

- `acceptance-spec/SKILL.md`（重点：Iron rules 1-7、S3 段，以及 S3 内对 `done_when.yaml` 的"硬规则"列表 —— 该列表在当前版本明确禁止 `existence:`/`behavior:`/`fitness:`/`spec_drift_threshold:` 里出现 v1 之外的 sub-fields）
- `references/done-when-schema.yaml` 全文（"AUTHORITATIVE SOURCE" 段、五种 existence kind 含义、behavior 三层 + thresholds、fitness 三值 enum `persona-judge | programmatic | manual`、`spec_drift_threshold.max_fix_loops_before_escalation` 唯一子字段）
- `references/output-templates/done-when-template.yaml`（"v1 STRICT RULES" 注释头、各段最小骨架）
- `references/output-templates/proposal-template.md`（5 节：Why / What / Non-goals / Decisions made during clarify / Linked artifacts）
- `references/output-templates/spec-template.md`（REQ-NNN + source + Glossary）
- `references/output-templates/tasks-template.md`（按层分组 + `implements:` + `size: S/M/L`）
- `references/examples/subscription-cancellation/done_when.yaml`（v1 字面 schema 的具体实施样本：existence 全部裸 key-value、behavior 全部 bare string、fitness 用 `persona-judge`、`created_by: acceptance-spec` 不带版本、无 `applies_to:` / `rubric_file:` / `based_on:` 等 sub-field）

按 SKILL.md 当前版本 S3 段交付 4 件套；done_when.yaml 严格遵守 v1 字面 schema。**未进入 Step 4**：不生成 existence.sh、单元/集成/e2e 测试文件、mutation 配置或 fitness rubric markdown。

---

## 产出文件清单

| 文件名 | 绝对路径 | 来源 template |
|------|--------|--------------|
| proposal.md | /Users/xrensiu/development/owner/claude-code-forge/specs/forge-skill-validation/iter-1-step3-attempt-2-artifacts/proposal.md | references/output-templates/proposal-template.md |
| spec.md | /Users/xrensiu/development/owner/claude-code-forge/specs/forge-skill-validation/iter-1-step3-attempt-2-artifacts/spec.md | references/output-templates/spec-template.md |
| tasks.md | /Users/xrensiu/development/owner/claude-code-forge/specs/forge-skill-validation/iter-1-step3-attempt-2-artifacts/tasks.md | references/output-templates/tasks-template.md |
| done_when.yaml | /Users/xrensiu/development/owner/claude-code-forge/specs/forge-skill-validation/iter-1-step3-attempt-2-artifacts/done_when.yaml | references/output-templates/done-when-template.yaml + references/done-when-schema.yaml |

计数（SKILL.md S3 末尾要求的"one-line count"，作为本 manifest 内的事实条目，不作 user-facing 输出）：**7 REQs, 20 existence checks (10 function + 4 route + 6 db_field), 44 test names (27 unit example_based + 9 unit property_based + 6 integration example_based + 2 integration property_based + 3 e2e), 2 fitness criteria.**

---

## 文件 1: proposal.md（全文嵌入）

```markdown
# Proposal: channel-mention-notifications

## Why
Members of team chat channels need to be reliably alerted when they are directly addressed (`@`-mentioned), without being woken up by every message in busy channels. Today the boundary between "must surface" and "must stay quiet" is fuzzy, which causes both missed-mention incidents (people learn about decisions late) and notification fatigue (people mute everything and then miss the things that mattered). This feature draws that line explicitly and in a single place.

## What
When a member is `@`-mentioned in a team chat channel (top-level channel or a thread they have participated in), the system fires a coordinated notification across push, in-app banner, sound, and unread-badge surfaces. While the member is in Do-Not-Disturb mode (manual toggle, scheduled window, or per-channel mute), the same mention is partially silenced — push / banner / sound are suppressed but the badge and unread count still increment, so the member discovers the mention on their next active session. Edits that add a new mention re-trigger the rule; deletions retract what can be retracted; non-membership and self-mention are silently skipped.

## Non-goals
- 1:1 DMs and group DMs — they have their own notification path and are explicitly out of scope here.
- Custom-keyword subscriptions (e.g. "notify me when anyone says 'deploy'") — separate feature.
- OS-level DND signal forwarding — depends on client capability, deferred.
- Email fallback / digest path when no in-app surface fires — separate feature.
- Retroactive resurfacing of mentions accumulated during DND once DND ends — explicitly rejected as noise.
- Emergency-broadcast / P0 channel that bypasses DND — separate feature if ever needed.
- Retry policy for un-acknowledged surfaces — that is the responsibility of the underlying delivery infrastructure, not this feature.
- UI rendering of skipped mentions (e.g. greying out an `@username` when the target is not a channel member) — design/planning concern.

## Decisions made during clarify
- `@mention` includes individual user mentions, broadcasts (`@here` / `@channel` / `@everyone`), and role/group mentions. Custom-keyword subscriptions are excluded. — source: S2 round 1 Q1
- "team chat channel" means a top-level multi-member channel or any thread within one. 1:1 and group DMs are out of scope. — source: S2 round 1 Q2
- "Deliver a notification" means push + in-app banner + sound + unread-badge are attempted concurrently; the event counts as delivered when at least one surface fires successfully. — source: S2 round 1 Q3
- A user `@`-mentioned in a channel they are not a member of is silently skipped — no notification to the target, no error to the mentioner (avoids leaking channel membership). — source: S2 round 1 Q4
- Self-mention does not produce a notification. — source: S2 round 1 Q5
- Editing a previously-sent message to add a new mention re-triggers the mention rule for the newly added member (closes the "edit-to-bypass" loophole). — source: S2 round 2 Q1
- Deleting a message containing a mention before the target has opened it retracts only the surfaces that support retraction (in-app banner); push, badge, and unread count are left as-is. — source: S2 round 2 Q2
- Inside a thread, only members who have already participated in that thread (sent at least one message) receive the mention; non-participants are silently skipped. — source: S2 round 2 Q3
- "Do-Not-Disturb mode" is active when any of these is true: manual toggle on, current time inside the scheduled DND window, or the channel has been explicitly muted by the member. OS-level DND is not part of the definition. — source: S2 round 2 Q4
- "Silence" under DND means partial suppression — no push, no in-app banner, no sound — while the unread badge and unread count still increment silently. — source: S2 round 2 Q5
- When DND becomes inactive, mentions accumulated during DND are not re-fired; the existing unread badge and unread count remain the only surfacing channel. — source: S2 round 3 Q1
- Broadcast mentions (`@here` / `@channel` / `@everyone`) under DND obey the same partial-silence rule as individual mentions; broadcast intent does not override the recipient's DND. — source: S2 round 3 Q2

## Linked artifacts
- spec.md — authoritative EARS requirements
- tasks.md — decomposed work
- done_when.yaml — machine-verifiable contract
```

---

## 文件 2: spec.md（全文嵌入）

```markdown
# Spec: channel-mention-notifications

> Authoritative EARS specification. Every REQ has a stable ID (never renumber).
> Every clause traces back to a clarify answer via `source:`.

## REQ-001 (Event-driven)
WHEN a member is `@`-mentioned in a team chat channel,
THE system SHALL attempt delivery of a notification to that member concurrently on the push, in-app banner, sound, and unread-badge surfaces, AND THE event SHALL be considered delivered when at least one surface fires successfully.

Constraint (thread scope): within a thread, the mentioned member is delivered to only if that member has previously sent at least one message in that thread; mention attempts targeting members who have never participated in the thread SHALL be silently skipped.

(Where "`@`-mention" includes individual user mentions, broadcast mentions `@here` / `@channel` / `@everyone`, and role-or-group mentions; and where "team chat channel" means a top-level multi-member channel or a thread within such a channel — 1:1 DMs and group DMs are out of scope.)

source: S2 round 1 Q1 (mention-type scope), S2 round 1 Q2 (channel scope), S2 round 1 Q3 (surface set and success criterion), S2 round 2 Q3 (thread participation constraint).

## REQ-002 (State-driven, follow-on from REQ-001)
WHILE the mentioned member is in Do-Not-Disturb mode,
THE system SHALL silence the notification produced by REQ-001.

Extension: this silence rule SHALL apply uniformly whether the triggering `@`-mention is individual, broadcast (`@here` / `@channel` / `@everyone`), or role/group; broadcast intent SHALL NOT override the recipient's DND.

source: S2 round 2 Q4 (DND defined as union of manual toggle / scheduled window / per-channel mute), S2 round 2 Q5 (silence means partial suppression with badge retained), S2 round 3 Q2 (broadcast under DND obeys same rule).

## REQ-003 (Unwanted)
IF a user is `@`-mentioned in a channel of which they are not currently a member, THEN the system SHALL NOT deliver any notification to that user AND SHALL NOT surface an error to the mentioner.

source: S2 round 1 Q4 (silent-skip on non-member mention; avoids leaking channel membership).

## REQ-004 (Unwanted)
IF the mentioner identity is equal to the mentioned identity (self-mention), THEN the system SHALL NOT deliver any notification.

source: S2 round 1 Q5 (self-mention suppressed as noise).

## REQ-005 (Event-driven)
WHEN a previously-sent message is edited to add an `@`-mention of a member who was not mentioned in that message before the edit,
THE system SHALL treat the newly-added mention as equivalent to a fresh mention AND SHALL apply REQ-001 (and, where applicable, REQ-002 / REQ-003 / REQ-004) to the newly-mentioned member.

source: S2 round 2 Q1 (edit-added mentions re-trigger; closes the edit-to-bypass loophole).

## REQ-006 (Event-driven)
WHEN a message containing an `@`-mention is deleted before the mentioned member has opened the notification,
THE system SHALL retract the notification on surfaces that support retraction (in-app banner) AND SHALL leave non-retractable surfaces (push, unread badge, unread count) in their pre-deletion state.

source: S2 round 2 Q2 (partial retraction — in-app withdrawn, push/badge unchanged).

## REQ-007 (Unwanted)
IF a member's Do-Not-Disturb mode (as defined in REQ-002) becomes inactive AND unread mentions were silently accumulated during that DND period, THEN the system SHALL NOT fire any retroactive push, in-app banner, or sound for those accumulated mentions; the pre-existing unread badge and unread count SHALL remain the sole surfacing channel.

source: S2 round 3 Q1 (no retroactive resurfacing on DND-end; rely on badge / unread list).

## Glossary

- **`@`-mention** — a syntactic marker in a chat message that targets one or more recipients. Includes individual user mentions, broadcast mentions (`@here` / `@channel` / `@everyone`), and role/group mentions. Excludes custom-keyword subscriptions. (source: S2 round 1 Q1)
- **team chat channel** — a top-level multi-member channel, or any thread nested within such a channel. Excludes 1:1 DMs and group DMs. (source: S2 round 1 Q2)
- **deliver a notification** — attempt delivery concurrently on the push, in-app banner, sound, and unread-badge surfaces. Success = at least one surface fires successfully. (source: S2 round 1 Q3)
- **Do-Not-Disturb mode (DND)** — a recipient-side state that is active when any one of the following holds: (i) the member has manually toggled DND on, (ii) the current time is inside the member's scheduled DND window, or (iii) the member has explicitly muted the specific channel in which the mention occurs. OS-level DND is not part of this definition. (source: S2 round 2 Q4)
- **silence** (verb, applied to a notification under DND) — suppress the push, in-app banner, and sound surfaces while still incrementing the unread badge and unread count silently. (source: S2 round 2 Q5)
- **thread participation** — having sent at least one message in the thread. Used as the eligibility test for receiving an in-thread `@`-mention. (source: S2 round 2 Q3)
```

---

## 文件 3: tasks.md（全文嵌入）

```markdown
# Tasks: channel-mention-notifications

> Decomposition of the work. Each task points to the REQ(s) it implements.
> Sizes are S / M / L sanity checks only — do not estimate hours here.

## Data layer
- [ ] Define `MentionEvent` record (message_id, channel_id, thread_id?, mentioner_id, mentioned_id, mention_kind ∈ {individual, broadcast_here, broadcast_channel, broadcast_everyone, role_group}, created_at) — implements: REQ-001 — size: S
- [ ] Define `DNDState` per member (manual_on: bool, schedule: window?, muted_channels: set) and the derived `is_dnd_for(member, channel, at)` query — implements: REQ-002 — size: M
- [ ] Define `ThreadParticipation` projection (member_id, thread_id, has_posted: bool) — implements: REQ-001 — size: S
- [ ] Store per-member `unread_badge_count` and `unread_mention_count` so they can be incremented under silence — implements: REQ-002 — size: S

## Business logic
- [ ] `ResolveMentionRecipients(message)` — expands individual / broadcast / role-group mentions into the candidate member set for the channel; applies thread-participation filter inside threads — implements: REQ-001 — size: M
- [ ] `FilterIneligibleRecipients(candidates, channel, mentioner)` — drops non-members of the channel and drops the mentioner themselves (self-mention) — implements: REQ-003, REQ-004 — size: S
- [ ] `DispatchMentionNotification(member, mention_event)` — fans out to push + in-app banner + sound + unread-badge surfaces concurrently; declares success when any one fires; under DND applies `SilenceProfile` (suppress push/banner/sound, still increment badge + unread count) — implements: REQ-001, REQ-002 — size: L
- [ ] `OnMessageEdited(old_message, new_message)` — diffs the mention set; for any newly added mention runs the full mention pipeline (REQ-001 → REQ-002/003/004) — implements: REQ-005 — size: M
- [ ] `OnMessageDeleted(message)` — for each unopened mention notification produced by that message, retract on retractable surfaces (in-app banner) and leave the rest untouched — implements: REQ-006 — size: M
- [ ] `OnDNDDeactivated(member)` — no retroactive push / banner / sound; explicitly a no-op beyond clearing the DND state itself — implements: REQ-007 — size: S
- [ ] Broadcast handling: ensure broadcast mentions flow through the same DND silence path as individual mentions (no urgent-override branch) — implements: REQ-002 — size: S

## Notification surfaces
- [ ] `PushSurface.fire(member, mention_event)` with idempotent dispatch keyed by `mention_event.id` — implements: REQ-001 — size: M
- [ ] `InAppBannerSurface.fire(member, mention_event)` + `.retract(mention_event_id)` (retract is required by REQ-006) — implements: REQ-001, REQ-006 — size: M
- [ ] `SoundSurface.fire(member, mention_event)` — implements: REQ-001 — size: S
- [ ] `UnreadBadgeSurface.increment(member, mention_event)` — must be callable under DND for silent accumulation — implements: REQ-001, REQ-002 — size: S

## API layer
- [ ] Message-send endpoint hook: after persistence, invoke the mention pipeline — implements: REQ-001, REQ-003, REQ-004 — size: S
- [ ] Message-edit endpoint hook: invoke `OnMessageEdited` — implements: REQ-005 — size: S
- [ ] Message-delete endpoint hook: invoke `OnMessageDeleted` — implements: REQ-006 — size: S
- [ ] DND-state change endpoint hook: when transitioning to inactive, invoke `OnDNDDeactivated` — implements: REQ-007 — size: S

## Docs / DX
- [ ] Reference doc enumerating mention kinds in scope (`@here` / `@channel` / `@everyone` / individual / role-group) and the kinds explicitly out of scope (custom-keyword subscriptions, 1:1 DMs, group DMs) — implements: REQ-001 — size: S
- [ ] Reference doc for the DND definition (manual ∪ schedule ∪ per-channel mute) and what "silence" suppresses vs. retains — implements: REQ-002 — size: S
- [ ] Reference doc for the deletion-retraction matrix (which surfaces are retractable, which are not) — implements: REQ-006 — size: S
```

---

## 文件 4: done_when.yaml（全文嵌入）

```yaml
feature: channel-mention-notifications
based_on: [REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007]
created_at: 2026-05-24T00:00:00Z
created_by: acceptance-spec

# ============================================================================
# LAYER 1 — EXISTENCE
# v1 strict: each entry is a single key-value pair (no sub-fields).
# Allowed kinds: file | function | route | db_field | frontend_component.
# Traceability is preserved by top-level based_on: + spec.md source: lines.
# ============================================================================
existence:
  - function: ResolveMentionRecipients
  - function: FilterIneligibleRecipients
  - function: DispatchMentionNotification
  - function: OnMessageEdited
  - function: OnMessageDeleted
  - function: OnDNDDeactivated
  - function: PushSurface
  - function: InAppBannerSurface
  - function: SoundSurface
  - function: UnreadBadgeSurface
  - route: POST /api/messages
  - route: PATCH /api/messages/:id
  - route: DELETE /api/messages/:id
  - route: PUT /api/members/:id/dnd
  - db_field: dnd_state.manual_on
  - db_field: dnd_state.schedule_window
  - db_field: dnd_state.muted_channels
  - db_field: thread_participation.has_posted
  - db_field: member_counters.unread_badge_count
  - db_field: member_counters.unread_mention_count

# ============================================================================
# LAYER 2 — BEHAVIOR
# v1 strict: every test entry is a BARE STRING (the test name).
# No name:/based_on:/property_type:/dependencies:/tool: sub-fields.
# property_based test names encode the property archetype
# (invariant / idempotent / reversible / boundary / monotonic / state_machine)
# so test-suite-generator 4-B can route by name.
# ============================================================================
behavior:
  unit_tests:
    example_based:
      - test_individual_mention_in_top_level_channel_fires_all_four_surfaces
      - test_mention_event_is_delivered_when_only_one_surface_succeeds
      - test_broadcast_at_here_resolves_to_active_channel_members
      - test_broadcast_at_channel_resolves_to_all_channel_members
      - test_broadcast_at_everyone_resolves_to_all_workspace_members_in_channel
      - test_role_group_mention_resolves_to_role_members
      - test_in_thread_mention_to_non_participant_is_silently_skipped
      - test_in_thread_mention_to_prior_participant_is_delivered
      - test_mention_under_dnd_suppresses_push_banner_sound
      - test_mention_under_dnd_still_increments_unread_badge_and_unread_count
      - test_dnd_active_when_manual_toggle_is_on
      - test_dnd_active_when_current_time_is_inside_scheduled_window
      - test_dnd_active_when_channel_is_muted_for_member
      - test_broadcast_mention_under_dnd_obeys_same_silence_rule_as_individual
      - test_mention_to_non_member_of_channel_emits_no_notification
      - test_mention_to_non_member_of_channel_does_not_error_to_mentioner
      - test_self_mention_emits_no_notification
      - test_edit_adding_new_mention_triggers_fresh_mention_pipeline
      - test_edit_not_changing_mention_set_does_not_retrigger
      - test_edit_added_mention_to_non_member_is_silently_skipped
      - test_delete_retracts_in_app_banner_for_unopened_notification
      - test_delete_leaves_push_unchanged
      - test_delete_leaves_unread_badge_and_count_unchanged
      - test_delete_after_target_opened_notification_is_a_noop
      - test_dnd_deactivation_does_not_fire_retroactive_push
      - test_dnd_deactivation_does_not_fire_retroactive_banner_or_sound
      - test_dnd_deactivation_preserves_existing_unread_badge_and_count
    property_based:
      - test_mention_pipeline_is_idempotent_on_repeated_dispatch_for_same_event
      - test_unread_badge_count_is_monotonic_under_dnd
      - test_dnd_silence_invariant_no_push_banner_sound_while_dnd_active
      - test_non_member_mention_invariant_zero_surfaces_fire
      - test_self_mention_invariant_zero_surfaces_fire
      - test_edit_then_revert_mention_set_is_reversible_with_no_duplicate_notifications
      - test_delete_retraction_in_app_banner_invariant_no_un_retract
      - test_in_thread_participation_boundary_only_prior_posters_receive_mentions
      - test_dnd_lifecycle_state_machine_is_well_formed

  integration_tests:
    example_based:
      - test_send_message_with_mention_dispatches_all_four_surfaces_end_to_end
      - test_mention_under_dnd_increments_badge_but_no_external_dispatch_observed
      - test_edit_adding_mention_dispatches_new_recipient_only
      - test_delete_message_retracts_in_app_banner_via_realtime_channel
      - test_dnd_window_expiry_does_not_trigger_resurfacing_dispatch
      - test_broadcast_at_channel_under_dnd_does_not_dispatch_push
    property_based:
      - test_mention_dispatch_atomicity_across_surfaces_and_counters_invariant
      - test_per_channel_mute_consistently_silences_across_restart_invariant

  e2e_tests:
    - test_mentioned_member_sees_in_app_banner_in_active_channel
    - test_member_in_dnd_sees_only_badge_increment_no_banner_no_sound
    - test_deleted_mention_message_retracts_visible_banner

  thresholds:
    unit_coverage: ">= 0.80"
    integration_coverage: ">= 0.60"
    mutation_kill_rate: ">= 0.70"
    pbt_runs_per_property: ">= 500"

# ============================================================================
# LAYER 3 — FITNESS (soft; max 3 entries)
# v1 strict: entries have exactly 3 keys: criterion / judge / score_threshold
# (omit score_threshold only when judge: programmatic).
# judge ∈ {persona-judge | programmatic | manual} — NOT llm-rubric.
# No rubric_file: — that is a downstream artifact emitted by test-suite-generator 4-F.
# ============================================================================
fitness:
  - criterion: an independent on-call engineer can read spec.md alone and correctly predict, for ten hand-crafted edge-case mention scenarios (non-member, self, edit-add, delete-before-open, in-thread non-participant, DND active, DND end with backlog, broadcast under DND, role mention, custom keyword), whether a notification fires and on which surfaces — without asking clarifying questions
    judge: persona-judge
    score_threshold: ">= 8/10"
  - criterion: the glossary in spec.md defines `@`-mention, team chat channel, deliver, DND, silence, and thread participation precisely enough that two independent reviewers produce the same partition of "in scope" vs "out of scope" mention scenarios from a shared list of 20 cases
    judge: persona-judge
    score_threshold: ">= 8/10"

# ============================================================================
# SPEC-DRIFT THRESHOLD
# v1 strict: exactly one sub-field, `max_fix_loops_before_escalation: <int>`.
# Guidance only — ratchet does not auto-read this; see INTEGRATION.md to
# translate into ratchet's `convergence` value when chaining.
# ============================================================================
spec_drift_threshold:
  max_fix_loops_before_escalation: 3
```

---

## 与 attempt-1 的 schema 差异（对照当前 skill 版本要求）

attempt-2 严格遵守 skill **当前**版本（SKILL.md S3 段 + `references/done-when-schema.yaml` 的 v1 字面）要求，与 attempt-1 相比修复了以下 schema 违规：

| 字段 | attempt-1 实际写法（违规） | attempt-2 当前写法（合规） | 依据 |
|------|-----------------|-----------------|-----|
| `existence[]` 每条目 | 带 `based_on: [REQ-...]` sub-field | 仅一个 key-value（`function: X` / `route: METHOD /path` / `db_field: T.C`） | SKILL.md "v1 字面 schema — do not invent sub-fields" + schema "single key-value pair, no sub-fields" |
| `behavior.*` 测试条目 | mapping，含 `name:` / `based_on:` / `property_type:` / `dependencies:` / `tool:` | 裸字符串（bare string），属性原型编码在名字里 | SKILL.md "every test entry ... is a bare string ... not a mapping" + schema "each leaf is a BARE STRING" |
| `fitness[].judge` | `llm-rubric`（不在 v1 enum） | `persona-judge`（v1 三值 enum 之一） | SKILL.md "Do NOT use llm-rubric ... 三-值 enum: persona-judge \| programmatic \| manual" + schema "judge ∈ {persona-judge, programmatic, manual}" |
| `fitness[]` 额外字段 | 带 `rubric_file:` 子字段 | 仅 3 个 key：`criterion` / `judge` / `score_threshold` | SKILL.md "Do NOT add `rubric_file:` — the rubric file is a downstream artifact emitted by test-suite-generator 4-F" |
| `spec_drift_threshold` | 含 `applies_to: [...]` sub-field | 仅 `max_fix_loops_before_escalation: 3` | SKILL.md "exactly one sub-field ... Do NOT add `applies_to:`" + schema 同 |
| `created_by` | `acceptance-spec/0.1.0`（带版本） | `acceptance-spec`（plain skill 名） | schema "plain skill name; do not append version. e.g. acceptance-spec" |
| `existence` 中的 route 条目 | 未提供（仅 function + db_field） | 补 4 条 route（POST/PATCH/DELETE messages + PUT dnd） | schema 允许 5 种 kind，attempt-1 没用 route 是缺失而非违规，attempt-2 顺手补上提高 traceability |
| `property_based` 测试名 | 名字 + 单独 `property_type:` field | 名字本身编码 archetype（含 `idempotent` / `monotonic` / `invariant` / `reversible` / `boundary` / `state_machine` 关键词） | SKILL.md "Encode the property archetype ... in the test name itself so downstream (4-B in test-suite-generator) can route the PBT pattern by name" |

**总结**：attempt-2 done_when.yaml **严格符合 v1 字面 schema**，attempt-1 在 6 处场地违反 v1 schema（existence/behavior/fitness/spec_drift_threshold/created_by/PBT 名字）。其他三件套（proposal.md / spec.md / tasks.md）的 schema 在两个 attempt 间基本一致；attempt-2 仅在内容层保持稳定，无格式变更。

---

## Skill 指令模糊点（仅事实陈述，不评价、不建议修改）

跑完 attempt-2 后，按当前 skill 版本，仍有以下事实性解释空间：

1. **`existence:` 中 `function:` 的颗粒度仍未显式定义。** 当前 schema 注释为 "function: <name>  # function must be exported"，但 example（subscription-cancellation）里把 use-case 类（`CancelSubscriptionUseCase`）也作为 function 条目。本 worker 沿用相同模式，把 `PushSurface` / `InAppBannerSurface` 等 surface 类也写为 `function:` 条目。schema 没有独立的 `class:` 或 `module:` kind，所以 surface 类/模块只能挤进 `function:`。这是"v1 仅有 5 种 kind"的字面遵守，但与"function == 一个被导出的函数"的直觉表面字义存在张力。

2. **`db_field: <table>.<column>` 在非关系型字段下的表达。** 本 feature 的 `dnd_state.muted_channels`（set 类型）、`member_counters.unread_badge_count`（counter）在物理实现层可能落在 KV / JSON 列 / 计数器服务，而非传统的 SQL 行列。当前 schema 字面要求 `<table>.<column>`，但未明示 KV/集合/计数器是否要"伪装"为表.列。本 worker 选择写成"逻辑表名.字段名"。

3. **`tasks.md` 分组层。** template 列出 "Data layer / Business logic / API layer / UI layer / Docs / DX" 五层；本 feature 的 "Notification surfaces" 介于 business logic 和 infra 之间，并不天然落在五层之一。SKILL.md 写 "Group by layer if natural ... otherwise flat"，允许新增层但未明确判则。本 worker 新增了 "Notification surfaces" 一层。

4. **`spec.md` REQ 块下的 "Extension:" 子句。** spec-template 是 `REQ-NNN + 单段 EARS + source` 的扁平结构，未提供 sub-clause 的官方 markdown 语法。Step 2 在 REQ-002 下产生了一个 round 3 Q2 派生的"广播在 DND 下统一处理"扩展约束，被自然安放为 "Extension:" 子段。本 worker 保留 Extension 段并在该 REQ 的 source 行多列一个 round/Q 编号；严格说这属于 template 之外的自创格式（虽然不违反 v1 schema —— spec.md 不是 schema 受约束的 YAML）。

5. **Iron rule 4 与 `existence:`/`behavior:` 之间的"每行可溯源"如何对齐。** Iron rule 4 要求 "Every decision traces to one clarification answer"；但 v1 字面 schema 禁止在 existence / behavior 行级写 `based_on:`。SKILL.md 明确说"把 traceability 推到 test 名 + 顶层 `based_on:` + `spec.md` 的 `source:` 行"。本 worker 严格遵守该指引，但行级"每条 existence/test 到底来自哪条 REQ"只能由人类阅读 test 名时去回推（例如 `test_self_mention_emits_no_notification` 显然对应 REQ-004，但需读者自己 link）。这是 SKILL.md 显式承认的取舍（"per-row traceability 在 v1 是被牺牲掉的，等 v2"），不构成 skill 内部的不一致，但 reviewer 在审 done_when.yaml 时仍可能问"为什么这条 test 没标 REQ"。

6. **`one-line count` 的归属。** SKILL.md S3 末尾要求向用户报 "N REQs, M existence checks, K test names, J fitness criteria"。本 worker 作为 subagent 不直接面向 user 输出，因此把这条 count 并入本 manifest 的"产出文件清单"段下方，未单独作为 user-facing bullet 输出。这是 worker / 主 agent 分工产生的格式偏移，非 skill 内部模糊。
