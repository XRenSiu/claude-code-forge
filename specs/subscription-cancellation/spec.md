# Feature: subscription-cancellation

## REQ-001 (Event-driven)
WHEN a user with subscription status `active` requests cancellation via the product UI or the documented cancellation API endpoint, THE system SHALL in a single atomic operation (a) stop the next billing-cycle charge AND (b) transition the subscription to status `cancelled_active`, such that either both side-effects are persisted or neither is.

### Constraint:
A billing retry or dunning charge already in flight against the already-paid current period continues to completion and is not aborted by this cancellation.

source: S2 round 1 Q1 (entry points = UI + API), S2 round 1 Q4 (in-flight retry continues), S2.5 self-adversarial (atomicity wording tightened to prevent assertion weakening).

## REQ-002 (State-driven, follow-on from REQ-001)
WHILE the subscription is in status `cancelled_active`, THE system SHALL grant the user the same premium feature access they had while in status `active`, with no additional usage cap, feature subset, or read-only restriction.

source: S2 round 1 Q2 (full parity), S2 round 2 Q1 (no metered restrictions in cancelled_active).

## REQ-003 (Event-driven, follow-on from REQ-002)
WHEN the server-observed timestamp reaches the `period_end` value of a subscription in status `cancelled_active`, THE system SHALL transition the subscription to status `expired` AND deny premium feature access for that subscription with immediate effect on the next premium-feature request.

source: S2 round 1 Q3 (period_end = billing-cycle anchor timestamp), S2 round 2 Q3 (revocation is immediate, no SLO window).

## REQ-004 (Unwanted)
IF a user requests cancellation while the subscription is in status `cancelled_active` or `expired`, THEN THE system SHALL respond successfully and idempotently, returning the same response body fields as the original cancellation plus the field `already_cancelled: true`, and SHALL NOT make any state change.

source: S2 round 1 Q5 (idempotent success), S2 round 2 Q2 (response = original payload + `already_cancelled: true`).

## REQ-005 (Unwanted)
IF a request for a premium feature is received for a subscription in status `expired`, THEN THE system SHALL respond with HTTP status 402 Payment Required AND a body whose `error` field equals the string `subscription_expired`.

### Constraint:
The body's human-readable `message` field is implementation-chosen but the `error` code string is the stable machine-readable contract.

source: S2 round 3 Q1 (HTTP 402 + structured payload with stable error_code).

## Glossary

- **`active`** — subscription state in which the user has paid for the current billing period and the next billing cycle is scheduled to charge. (source: implied baseline by the brief)
- **`cancelled_active`** — subscription state entered after a successful cancellation. The next billing-cycle charge is stopped; feature access remains at `active`-parity until `period_end`. (source: S2 round 1 Q1–Q2)
- **`expired`** — terminal subscription state entered when `period_end` is reached for a `cancelled_active` subscription. Premium feature access is denied. (source: S2 round 1 Q3 + round 2 Q3)
- **`period_end`** — the billing-cycle anchor timestamp at which the already-paid current period ends; computed as one billing-cycle interval after the cycle's start timestamp (e.g. if billed at 14:32:00 UTC on the 1st with a monthly cycle, `period_end` = 14:32:00 UTC on the next period's 1st). Not user-local midnight; not UTC midnight. (source: S2 round 1 Q3)
- **premium feature** — any product capability whose availability is gated on subscription status being `active` or `cancelled_active`. The full enumeration is owned by the product surface; this REQ contract only asserts access parity between the two non-terminal states. (source: S2 round 1 Q2)
