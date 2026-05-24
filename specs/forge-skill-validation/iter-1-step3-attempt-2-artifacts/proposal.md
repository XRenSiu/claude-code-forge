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
