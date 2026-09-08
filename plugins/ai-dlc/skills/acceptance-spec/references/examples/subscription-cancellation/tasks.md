# Tasks: subscription-cancellation

## Data layer
- [ ] Add `cancelled_active`, `cancelled_expired`, `expired` to `subscription.status` enum — implements: REQ-001, REQ-002, REQ-004 — size: S
- [ ] Add `cancelled_at TIMESTAMP NULL` column to `subscription` table — implements: REQ-001 — size: S
- [ ] Add `end_date TIMESTAMP NOT NULL` column (if not present) with UTC normalization — implements: REQ-002 — size: S

## Business logic
- [ ] `CancelSubscriptionUseCase` — atomic transition + future-charge cleanup — implements: REQ-001, REQ-004 — size: M
- [ ] `ReactivateSubscriptionUseCase` — reverse of cancel while in `cancelled_active` — implements: REQ-006 — size: S
- [ ] `BlockDuplicateSubscriptionCreation` — guard in subscription-creation path — implements: REQ-005 — size: S
- [ ] `ExpireSubscriptionJob` — scheduled job that transitions `cancelled_active` → `expired` at `end_date` UTC 23:59:59 — implements: REQ-002 — size: M

## API layer
- [ ] `POST /api/subscription/cancel` — implements: REQ-001, REQ-004 — size: S
- [ ] `POST /api/subscription/reactivate` — implements: REQ-006 — size: S
- [ ] Update `POST /api/subscription` to reject creation when an existing subscription is `cancelled_active` — implements: REQ-005 — size: S

## UI layer
- [ ] `CancelSubscriptionButton` + confirmation modal — implements: REQ-001 — size: M
- [ ] `ExpiryNoticeBanner` shown on login in `cancelled_active` — implements: REQ-003 — size: S
- [ ] "Reactivate" action button inside the expiry banner — implements: REQ-006 — size: S

## Docs / DX
- [ ] Update API reference for the two new endpoints — implements: REQ-001, REQ-006 — size: S
- [ ] User-facing help-center article on how cancellation works — implements: REQ-001, REQ-002, REQ-003 — size: S
