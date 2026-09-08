# Spec: subscription-cancellation

## REQ-001 (Event-driven)
WHEN the user clicks the "cancel subscription" button AND the current subscription status is `active`,
THE system SHALL atomically (a) prevent any future charge from being scheduled for this subscription AND (b) transition the subscription status to `cancelled_active` AND (c) record the cancellation timestamp.
source: original brief + S2 round 1 Q2 (atomicity confirmed)

## REQ-002 (State-driven)
WHILE the subscription is in status `cancelled_active`,
THE system SHALL grant the user the same premium access they had under `active`, with no degradation, until `end_date` at UTC 23:59:59, at which point the system SHALL transition the subscription to status `expired`.
source: S2 round 1 Q1 (UTC boundary) + S2 round 1 Q3 ("premium" = full plan grants)

## REQ-003 (Event-driven, in `cancelled_active`)
WHEN the user logs in WHILE the subscription is in status `cancelled_active`,
THE system SHALL display a notice of the form "your subscription will expire on YYYY-MM-DD" along with a "reactivate" action.
source: S2 round 2 Q3 (confirmed notice + reactivate affordance)

## REQ-004 (Event-driven, trial branch)
WHEN a user whose subscription is in status `trialing` clicks the "cancel subscription" button,
THE system SHALL immediately transition the subscription to status `cancelled_expired`, terminate premium access at that instant, AND not record any charge.
source: S2 round 2 Q2 (trial cancellation diverges from paid flow)

## REQ-005 (Unwanted)
IF the user attempts to create a *new* subscription WHILE the existing subscription is in status `cancelled_active`,
THEN THE system SHALL reject the creation and surface the message "your current subscription remains active until <end_date> — use 'reactivate' to keep it ongoing."
source: S2 round 2 Q1 (no duplicate subscriptions in cancelled_active)

## REQ-006 (Event-driven, reverse of REQ-001)
WHEN the user clicks "reactivate" WHILE the subscription is in status `cancelled_active` AND `now < end_date`,
THE system SHALL transition the subscription back to status `active` AND schedule the next charge for `end_date + 1 second`.
source: S2 round 2 Q1 (reactivation path)

## Glossary

- **active** — subscription in good standing, will be charged at next billing cycle. (source: original brief)
- **cancelled_active** — cancellation requested; no future charges scheduled; premium access retained until `end_date` UTC 23:59:59. (source: S2 round 1 Q1, Q2)
- **expired** — `end_date` has passed; no premium access; subscription record retained for history. (source: S2 round 1 Q1)
- **cancelled_expired** — used only for trial cancellation: premium access terminated immediately, no charge. (source: S2 round 2 Q2)
- **trialing** — subscription is in its trial period; user has not been charged yet. (source: S2 round 2 Q2)
- **premium access** — every feature granted by the user's active plan, not a separate restricted subset. (source: S2 round 1 Q3)
