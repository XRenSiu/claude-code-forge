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
