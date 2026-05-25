# Tasks — subscription-cancellation

## Data layer

- Add `status` column to the `subscription` table with the enum `active | cancelled_active | expired`.
  implements: REQ-001, REQ-002, REQ-003
  size: S

- Persist `period_end` (timestamp) on the `subscription` table; set at the time the current billing cycle's charge succeeds.
  implements: REQ-002, REQ-003
  size: S

- Persist `cancellation_timestamp` (timestamp, nullable) on the `subscription` table; set atomically with the `active` → `cancelled_active` transition.
  implements: REQ-001, REQ-004
  size: S

## Business layer

- Implement `CancelSubscriptionUseCase` that performs the atomic (stop-next-charge AND set-status-to-cancelled_active) transition for an `active` subscription.
  implements: REQ-001
  size: M

- Extend `CancelSubscriptionUseCase` to handle the idempotent re-cancel case on `cancelled_active` / `expired` subscriptions; return the persisted cancellation record plus `already_cancelled: true`.
  implements: REQ-004
  size: S

- Implement the period-boundary transition `cancelled_active` → `expired` triggered when server-time reaches `period_end`. Implementation strategy is implementer's choice (scheduled job, on-access lazy check, or both) but every premium-feature request received at or after `period_end` MUST observe the `expired` status.
  implements: REQ-003
  size: M

- Implement the premium-access authorization check used by every premium feature endpoint: `active` and `cancelled_active` permit access; `expired` denies with the contract response.
  implements: REQ-002, REQ-003, REQ-005
  size: M

## API layer

- Register `POST /api/subscription/cancel` route. Authenticates the caller as the subscription owner; invokes `CancelSubscriptionUseCase`; returns 200 with the cancellation record (and `already_cancelled: true` on idempotent re-cancel).
  implements: REQ-001, REQ-004
  size: M

- Wire the premium-access authorization check into the request middleware so an `expired` subscription's premium request returns HTTP 402 with body `{error: 'subscription_expired', message: <text>}`.
  implements: REQ-005
  size: S

## UI layer

- Add `CancelSubscriptionButton` to the account/subscription management view; on confirm, calls `POST /api/subscription/cancel`.
  implements: REQ-001
  size: S

- After a successful cancellation, the account view displays the `cancelled_active` state (with the `period_end` timestamp) so the user can see how long their access remains.
  implements: REQ-002
  size: S

- When the user hits a premium feature and receives HTTP 402 with `error: 'subscription_expired'`, surface a renewal prompt in the UI.
  implements: REQ-005
  size: S

## Cross-cutting

- Property-based test scaffold for the `subscription` state machine: legal transitions are `active → cancelled_active`, `cancelled_active → expired`. All other transitions are forbidden invariants.
  implements: REQ-001, REQ-003, REQ-004
  size: M
