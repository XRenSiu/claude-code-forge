# Fitness criterion: the HTTP 402 response body's human-readable `message` field accurately describes the renewal action without leaking internal terminology

**Source REQ(s):** REQ-005
**Judge:** persona-judge (manual workflow — see `fitness/README.md` "How to run a persona-judge rubric")
**Threshold:** >= 7/10

> **WARNING TO THE JUDGING AGENT:**
> Research (JudgeBench) shows naively-written rubrics drop judge accuracy
> from 55.6% (no rubric) to 42.9% (bad rubric) — 13 points *worse* than
> nothing. Use the structured sub-dimensions below verbatim. Do not collapse
> into "overall impression". Cite at least one passage from the inputs
> supporting every score.

## How to run

See `fitness/README.md` "How to run a persona-judge rubric" for the manual workflow. That section is the single canonical place for the procedure; this file does not duplicate it.

## Inputs

The judge examines:
- The literal `message` string(s) emitted by the impl when `error: 'subscription_expired'` (REQ-005). Source these from:
  - the integration test fixture `test_premium_endpoint_returns_402_for_expired_subscription` (which asserts the structured `error` field but not the `message`)
  - the actual impl module (`src/billing/cancel_subscription_use_case.ts` or wherever the 402 body is constructed)
  - if the message is localized: each locale's string for the EN-US baseline plus one other
- The renewal prompt UI copy (`src/components/RenewalPrompt.tsx` or similar) — to check consistency between API and UI surfaces
- `specs/subscription-cancellation/spec.md` REQ-005 (especially the Constraint: "human-readable `message` field is implementation-chosen but the `error` code string is the stable machine-readable contract")

## Audience archetype

**Audience archetype: integration engineer reading API response in debug log + end-user reading rendered UI message**

This rubric scores the *same string* against two readers:

1. **Integration engineer (third-party developer)** consuming the API:
   - Sees the `message` field in a debug log when their app gets back a 402.
   - Needs to understand: what state the user's subscription is in, what action will resolve it.
   - Does NOT need internal codenames, table names, status enum values like `cancelled_active`, or DB column names like `period_end`.

2. **End user** seeing this string rendered as-is in a UI banner (if the implementer chose to pass the message through without localizing/rewriting):
   - May not know what "subscription" means in technical terms.
   - Needs: a clear next-step verb ("Renew now") and clarity about why the action stopped.

If the impl localizes/rewrites the message before showing to end users, the second audience effectively reduces to "any developer reviewing the UI copy".

## Rubric

### Sub-dimension 1: action_clarity (weight 0.35)

Does the `message` field tell the reader what they (or the user) need to DO to resolve the 402?

Score 1-10 with these anchors:

- **10** — The message names a concrete user action with a verb (e.g. "Renew your subscription to continue accessing premium features"). The verb is recoverable both as a button label for UI and as a hint for API consumers.
- **7** — An action is mentioned but in passive voice or as a noun (e.g. "Renewal required to access premium features").
- **4** — Only the state is described ("Subscription is no longer active") with no resolution hint.
- **1** — Pure error reporting with no resolution hint ("Subscription expired" or worse, "Forbidden").

Cite the literal string and the relevant input.

### Sub-dimension 2: terminology_hygiene (weight 0.30)

Does the message avoid internal terminology that leaks implementation details (status enum values, DB column names, internal codenames, file paths, exception class names)?

Score 1-10 with these anchors:

- **10** — No internal terms appear. The message uses domain-level vocabulary the user/developer already has (e.g. "subscription", "renew", "premium features"). No status enum like `cancelled_active` or `expired` appears verbatim.
- **7** — One borderline term (e.g. `expired`) appears but in a form that reads naturally to a layperson ("Your subscription has expired"). No DB column or codename leakage.
- **4** — A status enum value or internal codename appears verbatim and is jarring (e.g. "Status: cancelled_active expired"). The message reads like a debug dump.
- **1** — Stack traces, file paths, or error class names leaked (e.g. "SubscriptionExpiredException at line 42 of cancel_subscription_use_case.ts").

Cite the literal string.

### Sub-dimension 3: precision_of_state (weight 0.20)

Does the message accurately state that the previous paid period has ended (REQ-003 — period_end reached), not some adjacent-but-different failure mode (payment failed, account suspended, plan downgraded)?

Score 1-10 with these anchors:

- **10** — The message specifically attributes the 402 to the paid period ending (e.g. "Your subscription period ended on June 30, 2026 — renew to continue."). Cannot be mistaken for an active payment-failure dunning state or admin action.
- **7** — The message says the subscription has expired but does not anchor to a date or the period-end framing. Could still be confused with a permanent termination.
- **4** — The message is ambiguous about cause ("Premium features are not available right now").
- **1** — The message mis-attributes (e.g. "Your payment failed — please update your card" when in fact the user explicitly cancelled and the period ended naturally).

Cite the literal string.

### Sub-dimension 4: ui_api_consistency (weight 0.15)

If the message is shown to end users in the UI renewal prompt, is the copy consistent (or sensibly adapted) between the API `message` field and the UI prompt? The two surfaces should not contradict each other.

Score 1-10 with these anchors:

- **10** — The UI renewal prompt's copy is a clean, audience-appropriate rewording of (or identical to) the API `message`. A developer comparing the two would say "same intent, same date, same action verb, audience-tuned register".
- **7** — The two surfaces convey the same intent but use different action verbs or different dates / formatting.
- **4** — The two surfaces conflict on a material detail (e.g. UI says "Renew" but API message says "Upgrade").
- **1** — The two surfaces describe different states entirely (API says expired, UI says payment failed).

Cite both passages.

## Aggregation

Final score = (action_clarity × 0.35) + (terminology_hygiene × 0.30) + (precision_of_state × 0.20) + (ui_api_consistency × 0.15)

(Weights sum to 1.0.)

## Pass/fail

Pass if:
- final score >= 7.0
- AND no sub-dimension scored below 5

## Re-run policy

If first pass produces a score within ±0.5 of threshold (i.e. 6.5–7.5), run the judge a second time on the revised string and require the score to not decrease before declaring pass.
