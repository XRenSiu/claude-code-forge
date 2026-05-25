# Proposal — subscription-cancellation

## Why

Users on a paid subscription must be able to stop future billing without losing immediate access to the period they have already paid for. Today the brief leaves this implicit; the lack of an explicit contract creates two failure modes: (a) cancellation that instantly revokes access (user feels cheated of paid time) and (b) cancellation that fails to stop the next charge (user feels billed for a service they cancelled). This feature closes both gaps with a state-machine contract.

## What

A user with an `active` subscription can request cancellation through either the product UI or a documented API endpoint. The system atomically (i) stops the next billing-cycle charge and (ii) transitions the subscription to `cancelled_active`. While in `cancelled_active`, the user retains full premium feature access — identical to the access they had in `active` — until the billing-cycle anchor timestamp of the already-paid period. At that timestamp the system transitions the subscription to `expired` and immediately revokes premium access; subsequent premium-feature requests receive an HTTP 402 with a structured `{error: 'subscription_expired', ...}` payload. Repeat cancel requests on a non-`active` subscription succeed idempotently.

## Non-goals

- Refund flows for the already-paid period (the brief is "still accessible", not "refunded").
- Plan downgrades (this feature is binary cancel, not tier-switch).
- Admin-on-behalf-of-user cancellation (brief uses "用户能" — self-cancel only).
- UI confirmation modal design (treated as implementation/UX detail, not a behavioral REQ).
- Reactivation / un-cancel flow during `cancelled_active` (brief does not authorize this case).
- Specific UX copy in the access-denied message (only the structured payload contract is specified).
- Billing retry / dunning behavior beyond honoring an in-flight retry against the already-paid period.

## Decisions made during clarify

- **Cancellation entry points = both UI and a documented API endpoint.** (source: S2 round 1 Q1)
- **"Premium feature access" during `cancelled_active` = full parity with `active`.** No usage caps, no read-only mode, no feature subset. (source: S2 round 1 Q2; reaffirmed S2 round 2 Q1 — no metered restrictions either)
- **Boundary = billing-cycle anchor timestamp.** If the user was billed at 14:32 UTC on the 1st, access expires at 14:32 UTC on the next period's 1st. Not user-local midnight, not UTC midnight. (source: S2 round 1 Q3)
- **In-flight billing retry at time of cancellation completes normally.** Cancellation stops the *next* cycle; charges already in flight against the already-paid period proceed to completion. (source: S2 round 1 Q4)
- **Re-cancel is idempotent.** Response = original cancellation response payload plus an `already_cancelled: true` flag. (source: S2 round 1 Q5 + S2 round 2 Q2)
- **Revocation at `period_end` is immediate.** Any request arriving with server-observed timestamp ≥ `period_end` for an `expired` subscription receives HTTP 402; no SLO window. (source: S2 round 2 Q3)
- **Access-denied response = HTTP 402 + structured payload** with stable `error: 'subscription_expired'` code; the human-readable `message` field is developer-chosen. (source: S2 round 3 Q1)
- **REQ-001 atomicity wording tightened.** (S2.5 self-adversarial) Original "atomically stop the next billing cycle's charge AND transition status" could be weakened by an implementer to either-or; revised to "in a single atomic operation such that either both observable side-effects are persisted or neither is."
- **State-machine PBT enforced.** (S2.5 self-adversarial) The 3-state space (active / cancelled_active / expired) is small enough that a lookup-table impl would pass example tests; `test_subscription_status_state_machine_is_well_formed` is added under `behavior.integration_tests.property_based` to force generalization.
