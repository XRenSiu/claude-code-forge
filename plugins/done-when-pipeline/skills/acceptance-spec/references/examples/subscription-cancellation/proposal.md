# Proposal: subscription-cancellation

## Why
Paying users currently have no self-service way to cancel without contacting support. This generates churn-blocking friction (users feel trapped) and ~40 weekly support tickets that could be self-served.

## What
A logged-in user with an active paid subscription can press a button to cancel. The next billing cycle is not charged. Premium access continues uninterrupted until the end of the period they already paid for. The user can see when their access expires and can change their mind before that date.

## Non-goals
- Refund flow for already-billed cycles (separate feature — finance/legal review needed)
- Cancellation by admin on behalf of user (separate flow)
- Downgrade from one paid plan to a cheaper paid plan (separate flow — different state semantics)
- Cancellation reasons / exit survey (out of scope for v1; can be added later as a non-blocking modal)

## Decisions made during clarify
- "End of paid period" = UTC 23:59:59 on `end_date`, not local-time midnight  — source: S2 round 1 Q1
- Cancellation is atomic across billing + access modules (both succeed, or both roll back) — source: S2 round 1 Q2
- "Premium access" = every feature the active plan currently grants, not a separate restricted subset — source: S2 round 1 Q3
- User can re-subscribe **only** by reactivating the cancelled subscription before `end_date`; creating a *new* subscription while `cancelled_active` is rejected — source: S2 round 2 Q1
- Trial-period cancellation is a separate REQ (REQ-004), no charges, immediate termination — source: S2 round 2 Q2
- Confirmation UI is a modal, not a separate page (one-click + confirm) — source: S2 round 2 Q3

## Linked artifacts
- spec.md — authoritative EARS requirements
- tasks.md — decomposed work
- done_when.yaml — machine-verifiable contract
