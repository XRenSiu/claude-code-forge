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
