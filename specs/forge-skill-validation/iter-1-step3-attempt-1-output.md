# Step 3 Worker 产出 — iter-1-step3-attempt-1

## skill 调用过程简记

读了 acceptance-spec/SKILL.md 的 Iron rules + S3 段（含 Solidify 四件套要求和 `spec_drift_threshold` 块要求），以及四份 reference：
- `references/done-when-schema.yaml`（v1 schema：feature / based_on / created_at / created_by / existence / behavior{unit_tests,integration_tests,e2e_tests,thresholds} / fitness / spec_drift_threshold；允许的 existence kinds；fitness 三种 judge 值；example 中的字段命名风格）
- `references/output-templates/proposal-template.md`（5 节：Why / What / Non-goals / Decisions made during clarify / Linked artifacts）
- `references/output-templates/spec-template.md`（REQ-NNN 块 + Glossary 节）
- `references/output-templates/tasks-template.md`（按层分组，每条带 `implements:` 与 `size: S/M/L`）
- `references/output-templates/done-when-template.yaml`（schema 的填空版，最小骨架）
- 同时参照 `references/examples/subscription-cancellation/done_when.yaml` 校准实际填法（function/route/db_field 的命名粒度、PBT name 风格、fitness 句式）

S3 严格按 SKILL.md 列出的四件套交付：proposal.md / spec.md / tasks.md / done_when.yaml，每个文件对照其 template 填充，不增加 skill 未要求的节。done_when.yaml 含 `spec_drift_threshold` 块（SKILL.md 显式要求）。**未进入 Step 4**：没有生成 existence.sh、单元/集成/e2e 测试文件、mutation 配置或 fitness rubric markdown。

S3 阶段没有需要 Step 2 之外的 user 交互；所有内容都源自 Step 2 输出的 7 个 REQ + 决策溯源表 + working Glossary。每个 REQ 的 `source:` 行原样保留 round/Q 编号。Iron rule 3（stable REQ-ID）已遵守：REQ-001 至 REQ-007 维持原编号。Iron rule 4（每个决策溯源到一条 clarify answer）已逐条体现在 spec.md 的 `source:` 行与 proposal.md 的 Decisions 段。Iron rule 7（verifiable beats judgeable）：fitness 仅留 2 条，且都是 spec 自洽性 / 名词定义可分性这种确实超出机械检查范围的判断。

## 产出文件清单

| 文件名 | 路径 | 来源 template |
|------|-----|--------------|
| proposal.md | /Users/xrensiu/development/owner/claude-code-forge/specs/forge-skill-validation/iter-1-step3-artifacts/proposal.md | references/output-templates/proposal-template.md |
| spec.md | /Users/xrensiu/development/owner/claude-code-forge/specs/forge-skill-validation/iter-1-step3-artifacts/spec.md | references/output-templates/spec-template.md |
| tasks.md | /Users/xrensiu/development/owner/claude-code-forge/specs/forge-skill-validation/iter-1-step3-artifacts/tasks.md | references/output-templates/tasks-template.md |
| done_when.yaml | /Users/xrensiu/development/owner/claude-code-forge/specs/forge-skill-validation/iter-1-step3-artifacts/done_when.yaml | references/output-templates/done-when-template.yaml + references/done-when-schema.yaml |

计数（SKILL.md S3 末尾要求的"one-line count"）：**7 REQs, 16 existence checks, 47 test names (28 unit example_based + 9 unit property_based + 6 integration example_based + 2 integration property_based + 3 e2e), 2 fitness criteria.**

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
created_by: acceptance-spec/0.1.0

# ============================================================================
# LAYER 1 — EXISTENCE
# ============================================================================
existence:
  - function: ResolveMentionRecipients
    based_on: [REQ-001]
  - function: FilterIneligibleRecipients
    based_on: [REQ-003, REQ-004]
  - function: DispatchMentionNotification
    based_on: [REQ-001, REQ-002]
  - function: OnMessageEdited
    based_on: [REQ-005]
  - function: OnMessageDeleted
    based_on: [REQ-006]
  - function: OnDNDDeactivated
    based_on: [REQ-007]
  - function: PushSurface
    based_on: [REQ-001]
  - function: InAppBannerSurface
    based_on: [REQ-001, REQ-006]
  - function: SoundSurface
    based_on: [REQ-001]
  - function: UnreadBadgeSurface
    based_on: [REQ-001, REQ-002]
  - db_field: dnd_state.manual_on
    based_on: [REQ-002]
  - db_field: dnd_state.schedule_window
    based_on: [REQ-002]
  - db_field: dnd_state.muted_channels
    based_on: [REQ-002]
  - db_field: thread_participation.has_posted
    based_on: [REQ-001]
  - db_field: member_counters.unread_badge_count
    based_on: [REQ-001, REQ-002]
  - db_field: member_counters.unread_mention_count
    based_on: [REQ-001, REQ-002]

# ============================================================================
# LAYER 2 — BEHAVIOR
# ============================================================================
behavior:
  unit_tests:
    example_based:
      - name: test_individual_mention_in_top_level_channel_fires_all_four_surfaces
        based_on: [REQ-001]
      - name: test_mention_event_is_delivered_when_only_one_surface_succeeds
        based_on: [REQ-001]
      - name: test_broadcast_at_here_resolves_to_active_channel_members
        based_on: [REQ-001]
      - name: test_broadcast_at_channel_resolves_to_all_channel_members
        based_on: [REQ-001]
      - name: test_broadcast_at_everyone_resolves_to_all_workspace_members_in_channel
        based_on: [REQ-001]
      - name: test_role_group_mention_resolves_to_role_members
        based_on: [REQ-001]
      - name: test_in_thread_mention_to_non_participant_is_silently_skipped
        based_on: [REQ-001]
      - name: test_in_thread_mention_to_prior_participant_is_delivered
        based_on: [REQ-001]
      - name: test_mention_under_dnd_suppresses_push_banner_sound
        based_on: [REQ-002]
      - name: test_mention_under_dnd_still_increments_unread_badge_and_unread_count
        based_on: [REQ-002]
      - name: test_dnd_active_when_manual_toggle_is_on
        based_on: [REQ-002]
      - name: test_dnd_active_when_current_time_is_inside_scheduled_window
        based_on: [REQ-002]
      - name: test_dnd_active_when_channel_is_muted_for_member
        based_on: [REQ-002]
      - name: test_broadcast_mention_under_dnd_obeys_same_silence_rule_as_individual
        based_on: [REQ-002]
      - name: test_mention_to_non_member_of_channel_emits_no_notification
        based_on: [REQ-003]
      - name: test_mention_to_non_member_of_channel_does_not_error_to_mentioner
        based_on: [REQ-003]
      - name: test_self_mention_emits_no_notification
        based_on: [REQ-004]
      - name: test_edit_adding_new_mention_triggers_fresh_mention_pipeline
        based_on: [REQ-005]
      - name: test_edit_not_changing_mention_set_does_not_retrigger
        based_on: [REQ-005]
      - name: test_edit_added_mention_to_non_member_is_silently_skipped
        based_on: [REQ-005, REQ-003]
      - name: test_delete_retracts_in_app_banner_for_unopened_notification
        based_on: [REQ-006]
      - name: test_delete_leaves_push_unchanged
        based_on: [REQ-006]
      - name: test_delete_leaves_unread_badge_and_count_unchanged
        based_on: [REQ-006]
      - name: test_delete_after_target_opened_notification_is_a_noop
        based_on: [REQ-006]
      - name: test_dnd_deactivation_does_not_fire_retroactive_push
        based_on: [REQ-007]
      - name: test_dnd_deactivation_does_not_fire_retroactive_banner_or_sound
        based_on: [REQ-007]
      - name: test_dnd_deactivation_preserves_existing_unread_badge_and_count
        based_on: [REQ-007]

    property_based:
      - name: test_mention_pipeline_is_idempotent_on_repeated_dispatch_for_same_event
        property_type: idempotent
        based_on: [REQ-001]
      - name: test_unread_badge_count_is_monotonic_under_dnd
        property_type: monotonic
        based_on: [REQ-002]
      - name: test_dnd_silence_invariant_no_push_banner_sound_while_dnd_active
        property_type: invariant
        based_on: [REQ-002]
      - name: test_non_member_mention_invariant_zero_surfaces_fire
        property_type: invariant
        based_on: [REQ-003]
      - name: test_self_mention_invariant_zero_surfaces_fire
        property_type: invariant
        based_on: [REQ-004]
      - name: test_edit_then_unedit_mention_set_yields_no_duplicate_notifications
        property_type: reversible
        based_on: [REQ-005]
      - name: test_delete_then_reopen_retraction_does_not_un_retract_in_app_banner
        property_type: invariant
        based_on: [REQ-006]
      - name: test_thread_participation_boundary_only_prior_posters_receive_in_thread_mentions
        property_type: boundary
        based_on: [REQ-001]
      - name: test_dnd_lifecycle_state_machine_is_well_formed
        property_type: state_machine
        based_on: [REQ-002, REQ-007]

  integration_tests:
    example_based:
      - name: test_send_message_with_mention_dispatches_all_four_surfaces_end_to_end
        based_on: [REQ-001]
        dependencies: [postgres, redis, push_gateway_mock]
      - name: test_mention_under_dnd_increments_badge_but_no_external_dispatch_observed
        based_on: [REQ-002]
        dependencies: [postgres, redis, push_gateway_mock]
      - name: test_edit_adding_mention_dispatches_new_recipient_only
        based_on: [REQ-005]
        dependencies: [postgres, redis, push_gateway_mock]
      - name: test_delete_message_retracts_in_app_banner_via_realtime_channel
        based_on: [REQ-006]
        dependencies: [postgres, redis, realtime_socket]
      - name: test_dnd_window_expiry_does_not_trigger_resurfacing_dispatch
        based_on: [REQ-007]
        dependencies: [postgres, redis, push_gateway_mock]
      - name: test_broadcast_at_channel_under_dnd_does_not_dispatch_push
        based_on: [REQ-002]
        dependencies: [postgres, redis, push_gateway_mock]

    property_based:
      - name: test_mention_dispatch_atomicity_across_surfaces_and_counters
        property_type: invariant
        based_on: [REQ-001, REQ-002]
        dependencies: [postgres, redis]
      - name: test_per_channel_mute_consistently_silences_across_restart
        property_type: invariant
        based_on: [REQ-002]
        dependencies: [postgres, redis]

  e2e_tests:
    - name: test_mentioned_member_sees_in_app_banner_in_active_channel
      based_on: [REQ-001]
      tool: playwright
    - name: test_member_in_dnd_sees_only_badge_increment_no_banner_no_sound
      based_on: [REQ-002]
      tool: playwright
    - name: test_deleted_mention_message_retracts_visible_banner
      based_on: [REQ-006]
      tool: playwright

  thresholds:
    unit_coverage: ">= 0.80"
    integration_coverage: ">= 0.60"
    mutation_kill_rate: ">= 0.70"
    pbt_runs_per_property: ">= 500"

# ============================================================================
# LAYER 3 — FITNESS (soft, kept short on purpose)
# ============================================================================
# judge ∈ {programmatic, llm-rubric, manual}; see ../done-when-schema.yaml.
fitness:
  - criterion: an independent on-call engineer can read spec.md alone and correctly predict, for ten hand-crafted edge-case mention scenarios (non-member, self, edit-add, delete-before-open, in-thread non-participant, DND active, DND end with backlog, broadcast under DND, role mention, custom keyword), whether a notification fires and on which surfaces — without asking clarifying questions
    judge: llm-rubric
    rubric_file: tests/channel-mention-notifications/fitness/spec_is_self_contained_for_oncall.rubric.md
    score_threshold: ">= 8/10"
  - criterion: the glossary in spec.md defines `@`-mention, team chat channel, deliver, DND, silence, and thread participation precisely enough that two independent reviewers produce the same partition of "in scope" vs "out of scope" mention scenarios from a shared list of 20 cases
    judge: llm-rubric
    rubric_file: tests/channel-mention-notifications/fitness/glossary_drives_consistent_scope_partitioning.rubric.md
    score_threshold: ">= 8/10"

spec_drift_threshold:
  # Guidance only — when chaining to /ratchet, translate into ratchet's `convergence`.
  max_fix_loops_before_escalation: 3
  applies_to:
    - mutation_kill_rate
    - property_based_failure
```

---

## Skill 指令模糊点（事实陈述）

以下是 S3 阶段执行中遇到的、SKILL.md / template / schema 之间存在解释空间或潜在不一致的地方。仅作事实陈述，不评价、不建议修改。

1. **`existence:` 中 `function:` 条目的颗粒度未定义。** schema 的描述是 "function/class must be exported"，example（subscription-cancellation）里把 use-case 类（如 `CancelSubscriptionUseCase`）当一个 function 条目。本 worker 沿用同一模式，把 `PushSurface` / `InAppBannerSurface` 这类 surface "类/模块" 也写成 `function:` 条目。schema 没有 `class:` 或 `module:` 单独 kind，所以 surface 类只能挤进 `function:`，但 schema 的字面 "function" 与实际 "class/module" 的关系不显式。

2. **`db_field:` 的命名空间。** schema 规定 `<table>.<column>` 格式。本 feature 大量状态是 KV / 内嵌结构（如 `dnd_state.muted_channels` 是 set 类型，`unread_mention_count` 是 counter）。在关系型 schema 下它们可能落成多张表或 JSON 列。本 worker 选了"逻辑表名.字段名"的写法，但 schema 在面对 KV / counter / set 这类非关系字段时没有显式规约。

3. **`tasks.md` 的分组层。** template 例子用 "Data layer / Business logic / API layer / UI layer / Docs / DX"。本 feature 的 "Notification surfaces" 不天然落在这五层中任何一个（介于 business logic 和 infra 之间）。SKILL.md 写 "Group by layer if natural (data / business / API / UI), otherwise flat"，允许新增层但未明示规则。本 worker 新增了 "Notification surfaces" 一层。

4. **`fitness:` 数量上限。** SKILL.md 写 "max 3 items; if you have more, you are over-using LLM-judge"，但没有最小值。本 worker 给了 2 条都用 `llm-rubric`，未使用 `programmatic` 或 `manual` 判官。SKILL.md 鼓励 "verifiable beats judgeable"，理论上 0 条 fitness 也合规，但 template 提供了占位条目，可能暗示至少 1 条。本 worker 留 2 条，因为 spec 自洽性与 glossary 可分性确实是机械检查难以覆盖的维度。

5. **S3 完成话术的"one-line count"。** SKILL.md 要求最终告知用户三件事之一是 "N REQs, M existence checks, K test names, J fitness criteria"，但本 worker 任务范围是写 4 件套到磁盘 + manifest，**不**面向用户输出"完成话术"。这条 count 已并入本 manifest 的"产出文件清单"段下方，未单独作为 user-facing 段落。

6. **`based_on:` 的多 REQ 顺序。** schema 和 example 中 `based_on: [REQ-001, REQ-002]` 列表都按 REQ 编号升序排列；SKILL.md 未规约顺序是否承载语义（如"主 REQ 优先"）。本 worker 一律升序。

7. **REQ-002 内嵌的 "Extension" 子句作为单独条款。** spec.md template 是 "REQ-NNN + 单段 EARS + source"，没有 sub-clause 块的官方语法。Step 2 输出在 REQ-002 下放了一个 "Extension" 段（广播在 DND 下的统一规则），是从 round 3 Q2 解锁的派生约束。本 worker 保留 Extension 段并在同一个 REQ 的 source 里多列一个 round/Q 编号，但严格说这属于在 template 之外自创格式。
