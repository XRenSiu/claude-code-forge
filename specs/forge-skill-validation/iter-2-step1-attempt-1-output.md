# iter-2 step1 attempt-1 — acceptance-spec run log

## 1. Skill invocation

**Command attempted (preferred path):**
```
Skill tool → name="acceptance-spec"
        args="Reference Brief: \"用户能取消订阅，但已支付当月仍可访问\""
```

**Result:** `Unknown skill: acceptance-spec`.

Root cause: the `done-when-pipeline` plugin is **not** in the user's `~/.claude/settings.json → enabledPlugins` dictionary (verified by reading the file — only `frontend-design`, `playwright-skill`, `forge-teams`, `claude-hud`, `impeccable` are enabled). The Skill tool's available-list is fixed at session start (per the CLAUDE.md historical bug note), so the skill cannot be invoked via `/acceptance-spec` in the current session.

**Fallback (the actual execution path):** ran the skill source directly, exactly as CLAUDE.md prescribes for `bespoke-design-system`. Read `plugins/done-when-pipeline/skills/acceptance-spec/SKILL.md` (v0.3.0) and walked phases S0 → S1 → S2 → S2.5 → S3 verbatim, reading `references/ears-syntax.md`, `references/clarify-protocol.md`, `references/done-when-schema.yaml`, `references/spec-robustness-template.md` at the points the SKILL.md instructs.

**Input parameter (original brief, verbatim):**
```
用户能取消订阅，但已支付当月仍可访问
```

**S0 derivations (silent per SKILL.md line 77):**
- feature slug: `subscription-cancellation`
- scope: multi-module (cancellation flow + access-control across paid window)
- output directory: `/Users/xrensiu/development/claude-code/claude-code-forge/specs/subscription-cancellation/`

---

## 2. Complete clarify-loop dialogue

The user-facing skill output started with the SKILL.md line 22-23 mandated sentence:

> "I'm using the acceptance-spec skill. I'll draft EARS requirements, run a short clarify loop (only 3 question types, 2-3 rounds), then a quick spec-self-adversarial pass, then write proposal.md / spec.md / tasks.md / done_when.yaml / spec-robustness.md."

Then the S1 draft (visible to user) was emitted, immediately followed by S2 round 1 in the same response per SKILL.md line 113.

### S1 — draft

```markdown
# Feature: subscription-cancellation (draft)

## REQ-001 (Event-driven)
WHEN a user with status `active` requests subscription cancellation [?] [ambiguity] "requests" — via UI click, API call, or both?, THE system SHALL atomically (a) stop the next billing cycle's charge AND (b) transition the subscription to status `cancelled_active` [?] [undefined term] "cancelled_active" — is this the intended name for the post-cancel pre-expiry state?.

## REQ-002 (State-driven, follow-on from REQ-001)
WHILE the subscription is in status `cancelled_active`, THE system SHALL retain the user's premium feature access [?] [undefined term] "premium feature access" — exact scope? until the end of the already-paid current billing period [?] [ambiguity] "end of the already-paid current billing period" — what wall-clock boundary?.

## REQ-003 (Event-driven, follow-on from REQ-002)
WHEN the already-paid period boundary is reached for a subscription in status `cancelled_active`, THE system SHALL transition the subscription to status `expired` [?] [undefined term] "expired" — terminal state name? and revoke premium feature access [?] [missing edge] revocation latency — immediate at boundary, or eventual?.

## REQ-004 (Unwanted)
IF a user attempts to cancel a subscription that is already in status `cancelled_active` or `expired`, THEN THE system SHALL [?] [missing edge] idempotent-or-error? — return success (idempotent) or return an error indicating the subscription is already cancelled.

## REQ-005 (Unwanted)
IF a user attempts to access a premium feature while their subscription is in status `expired`, THEN THE system SHALL deny access AND surface a message indicating renewal is required [?] [missing edge] message wording — is exact copy specified or developer-chosen?.

## Open questions
- [?] [ambiguity] "requests cancellation": is the entry point UI-only, API-only, or both? (affects REQ-001)
- [?] [undefined term] "premium feature access": all paid features, or a named subset? (affects REQ-002, REQ-005)
- [?] [ambiguity] "end of the already-paid current billing period": user-local timezone midnight, UTC 23:59:59, or exact billing-cycle anchor timestamp? (affects REQ-002, REQ-003)
- [?] [missing edge] cancellation while a billing retry / dunning is in flight: refuse, abort the retry, or allow both to proceed? (affects REQ-001)
- [?] [missing edge] re-cancel attempt on `cancelled_active` subscription: idempotent success or error response? (affects REQ-004)
```

### S2 — Round 1 (5 questions)

**Skill output (question batch):**

```
Round 1 of clarification — 5 questions:

[ambiguity] REQ-001: "requests cancellation" entry point means
  (a) UI button click only
  (b) API call only
  (c) both UI and a documented API endpoint

[undefined term] REQ-002 / REQ-005: by "premium feature access" do you mean
  (a) every feature the user had while `active` (full parity)
  (b) a documented subset of features (read-only premium content but no premium writes)
  (c) some other scoping

[ambiguity] REQ-002 / REQ-003: "end of the already-paid current billing period" means
  (a) user's local timezone 23:59:59 on the period-end date
  (b) UTC 23:59:59 on the period-end date
  (c) the exact billing-cycle anchor timestamp (e.g. if billed at 14:32 UTC on the 1st, expiry is 14:32 UTC on the next period's 1st)

[missing edge] REQ-001: if a billing retry / dunning charge is in flight when the user requests cancellation, the system should
  (a) refuse cancellation until the retry resolves
  (b) abort the retry and proceed with cancellation atomically
  (c) accept cancellation but let the in-flight retry complete and apply normally

[missing edge] REQ-004: a second cancel request on a subscription already in `cancelled_active` should
  (a) succeed idempotently (return the same payload as the original cancel)
  (b) return an error indicating the subscription is already cancelled
  (c) return success but include a flag/field indicating no state change occurred
```

**My answers (rational-PM persona, brief-literal + industry-standard practice):**

- **Q1 → (c) both UI and a documented API endpoint.** Industry standard for SaaS subscription products (Stripe, Slack, etc.) expose both; brief's "用户能取消订阅" does not restrict the channel.
- **Q2 → (a) every feature the user had while `active` (full parity).** Brief's "已支付当月仍可访问" most literally reads "same access as if still paying"; no reduced subset is implied.
- **Q3 → (c) the exact billing-cycle anchor timestamp.** Aligned with Stripe / Chargebee `period_end` semantics. The brief's "已支付当月" cleanly maps to "the period the user paid for"; the cleanest boundary is the same anchor timestamp.
- **Q4 → (c) accept cancellation but let the in-flight retry complete.** Retries against the already-paid period are for *that* period; cancelling future cycles shouldn't void a charge in flight against the current paid period.
- **Q5 → (a) succeed idempotently.** REST best practice for cancellation; reduces client complexity. No business reason in the brief to error.

### Apply-answers + second-order scan (silent, per clarify-protocol Rule 4)

After applying answers, second-order ambiguities surfaced:
- (a) `cancelled_active` with full-parity access — does it admit irreversible / billable side-effects (team-member invites, metered-limit writes)? Need clarification.
- (b) The idempotent re-cancel response shape — byte-identical or "original payload + `already_cancelled: true` flag"?
- (c) Revocation latency at the boundary (S1's open `[?]` not yet resolved — round 2).
- (d) (Considered then dropped per clarify-protocol Rule 1 "do not invent") — admin-on-behalf-of-user cancellation; brief uses "用户能" (self-cancel only).
- (e) (Considered then dropped) — UI confirmation modal; brief never mentions confirmation.

### S2 — Round 2 (3 questions)

**Skill output:**

```
Round 2 of clarification — 3 questions:

[missing edge] REQ-002: while in `cancelled_active`, an action that creates org-wide / billable side-effects (e.g. inviting new team members beyond the free-tier cap, sending notifications counted against the premium plan limit) should
  (a) be treated identically to `active` — no extra restriction (clean access parity)
  (b) be capped — usage allowed up to the metered limit for the already-paid period, then refused
  (c) be blocked outright in `cancelled_active` (premium read-only)

[ambiguity] REQ-004: the idempotent cancel response payload should
  (a) be byte-identical to the original cancellation response
  (b) be the original response plus an `already_cancelled: true` indicator flag
  (c) return only a minimal `{status: 'cancelled_active', end_date: <iso>}` (no fresh timestamps)

[missing edge] REQ-003: at the boundary timestamp, premium-access revocation
  (a) is immediate — any request arriving after the boundary timestamp returns "access denied"
  (b) is eventual — revoked within a documented SLO (e.g. ≤ 60 seconds) after the boundary
  (c) is event-driven only — revoked the next time the user re-authenticates or the next billable action
```

**My answers:**

- **Q1 → (a) treated identically to `active`.** Brief's "已支付当月仍可访问" most literally = full parity. Adding caps would be scope creep beyond the brief. Industry-standard SaaS (Stripe, GitHub Pro, Notion) treats paid period as paid period.
- **Q2 → (b) original response + `already_cancelled: true` flag.** Best of both worlds: idempotency for legacy clients, observability for new clients. Stripe-style REST pattern.
- **Q3 → (a) immediate.** Brief mentions no SLO window. The cleanest mental model and the most testable: timestamp ≥ `period_end` → access denied.

### Apply-answers + second-order scan (silent)

- One S1 `[?]` still unresolved: REQ-005's "message wording" — `[missing edge]` on whether copy is specified or developer-chosen. Need a 1-question round 3 (per clarify-protocol Rule 2.1: lower-bound 3 is a target, not a hard floor; finishing with 1-2 is allowed; never pad).
- No new second-order ambiguities from round 2 answers that meet the 3-tag taxonomy. (Server-clock-skew is implementation; revocation across distributed nodes is implementation. Both dropped per Rule 1.)

### S2 — Round 3 (1 question)

**Skill output:**

```
Round 3 of clarification — 1 question:

[missing edge] REQ-005: the "renewal required" message returned to an `expired`-status user attempting to access a premium feature should
  (a) include exact specified copy text (provide the wording)
  (b) be developer-chosen prose, but carry a stable machine-readable error_code (e.g. `subscription_expired`) for client routing / i18n
  (c) be a structured payload `{error: 'subscription_expired', message: <dev-chosen>}` returned with HTTP 402 Payment Required
```

**My answer:**

- **Q1 → (c) HTTP 402 + structured payload + stable error code.** Most precise, most verifiable, industry standard (RFC 7231 status code for payment-required). Brief does not specify copy text; specifying a machine-readable contract is what is testable.

All `[?]` resolved → proceed to S2.5.

### S2.5 — spec-self-adversarial pass (silent)

Scanned resolved spec against the 6 RHD patterns from `spec-robustness-template.md`:

| Pattern | Finding | Action |
|---|---|---|
| 1. test_modification | REQ-001 "atomically stop charge AND transition status" — implementer could weaken to either-or | **CLOSE** — tighten SHALL wording to "in a single atomic operation … either both side-effects are persisted or neither is" |
| 1. test_modification | REQ-003 "deny access immediately" — could be gamed by cached session tokens that outlive `period_end` | **SURFACE** — `session_cache_revocation_gap` for `/acceptance-fleet` edge-case-hunter |
| 2. test_case_targeting | No specific concrete user IDs / tier names appear in any REQ | safe |
| 3. coverage_gaming | `unit_coverage >= 0.80 + mutation_kill_rate >= 0.70` per template; v1 has no branch_coverage field | **SURFACE** — `branch_coverage_gap` for `/acceptance-fleet` spec-gaming-detector |
| 4. degenerate_implementation | 3-state space (active / cancelled_active / expired) — a 5-row lookup table would satisfy example tests | **CLOSE** — added 4 PBT names (state-machine + monotonic transition + atomicity invariant + access-parity invariant) |
| 5. style_manipulation | Fitness criteria are persona-judge on user-facing renewal-prompt clarity; no surface metric proxies | safe (one accepted_risk recorded as audit trail) |
| 6. information_leakage | proposal.md "What" names state strings + HTTP 402, but those are contract terms not (input, output) tuples | **ACCEPT** with rationale |

Outcome: 2 closed, 2 surfaced, 2 accepted. No S2.5 rewrite was severe enough to demand the user-visible "please sanity-check" line per SKILL.md line 180 — the REQ-001 atomicity tightening is mechanical wording, not a semantic shift. Proceeded silently to S3.

### S3 — solidify (user-visible end-of-skill summary)

After writing the five files, the skill emitted the four-bullet closeout per SKILL.md lines 316-323:

> 1. Output directory: `/Users/xrensiu/development/claude-code/claude-code-forge/specs/subscription-cancellation/` — `proposal.md`, `spec.md`, `tasks.md`, `done_when.yaml`, `spec-robustness.md`.
> 2. Counts: 5 REQs, 7 existence checks, 22 test names, 2 fitness criteria, 2 surfaced gaming vectors (plus 2 closed and 2 accepted).
> 3. Immediate next step: `/test-suite-generator specs/subscription-cancellation/`.
> 4. Subsequent (Step 5-6): `/acceptance-fleet` (preferred; reads spec-robustness.md) or manually translate to `/ratchet` (legacy).

---

## 3. Output file inventory (`ls -la`)

```
total 48
drwxr-xr-x@ 7 xrensiu  staff   224 May 25 10:02 .
drwxr-xr-x  5 xrensiu  staff   160 May 25 10:00 ..
-rw-r--r--@ 1 xrensiu  staff  2670 May 25 10:02 done_when.yaml
-rw-r--r--@ 1 xrensiu  staff  3932 May 25 10:00 proposal.md
-rw-r--r--@ 1 xrensiu  staff  5854 May 25 10:02 spec-robustness.md
-rw-r--r--@ 1 xrensiu  staff  3823 May 25 10:00 spec.md
-rw-r--r--@ 1 xrensiu  staff  2952 May 25 10:02 tasks.md
```

Absolute paths:

- `/Users/xrensiu/development/claude-code/claude-code-forge/specs/subscription-cancellation/proposal.md`
- `/Users/xrensiu/development/claude-code/claude-code-forge/specs/subscription-cancellation/spec.md`
- `/Users/xrensiu/development/claude-code/claude-code-forge/specs/subscription-cancellation/tasks.md`
- `/Users/xrensiu/development/claude-code/claude-code-forge/specs/subscription-cancellation/done_when.yaml`
- `/Users/xrensiu/development/claude-code/claude-code-forge/specs/subscription-cancellation/spec-robustness.md`

---

## 4. Verbatim file contents

### 4.1 `proposal.md`

```markdown
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
```

### 4.2 `spec.md`

```markdown
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
```

### 4.3 `tasks.md`

```markdown
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
```

### 4.4 `done_when.yaml`

```yaml
feature: subscription-cancellation
based_on: [REQ-001, REQ-002, REQ-003, REQ-004, REQ-005]
created_at: 2026-05-25T00:00:00Z
created_by: acceptance-spec

existence:
  - file: src/billing/cancel_subscription_use_case.ts
  - function: CancelSubscriptionUseCase
  - route: POST /api/subscription/cancel
  - db_field: subscription.status
  - db_field: subscription.period_end
  - db_field: subscription.cancellation_timestamp
  - frontend_component: CancelSubscriptionButton

behavior:
  unit_tests:
    example_based:
      - test_cancel_active_transitions_status_to_cancelled_active
      - test_cancel_active_stops_next_billing_cycle_charge
      - test_cancel_records_cancellation_timestamp
      - test_cancel_on_cancelled_active_returns_already_cancelled_true
      - test_cancel_on_expired_returns_already_cancelled_true
      - test_premium_access_granted_while_cancelled_active
      - test_premium_request_returns_402_when_expired
      - test_402_body_error_field_equals_subscription_expired
      - test_period_boundary_transitions_to_expired_at_period_end
      - test_in_flight_billing_retry_continues_after_cancellation
    property_based:
      - test_cancel_is_idempotent
      - test_premium_access_invariant_active_and_cancelled_active_have_identical_access
      - test_status_transition_is_monotonic_active_to_cancelled_active_to_expired
      - test_cancel_atomicity_invariant_both_side_effects_or_neither

  integration_tests:
    example_based:
      - test_cancel_api_returns_200_and_cancellation_record
      - test_cancel_api_idempotent_re_cancel_returns_already_cancelled_true
      - test_premium_endpoint_returns_402_for_expired_subscription
    property_based:
      - test_subscription_status_state_machine_is_well_formed
      - test_no_premium_request_after_period_end_succeeds_state_machine

  e2e_tests:
    - test_user_can_cancel_active_subscription_via_ui_and_retains_access_until_period_end
    - test_user_with_expired_subscription_sees_renewal_prompt_on_premium_action

  thresholds:
    unit_coverage: ">= 0.80"
    integration_coverage: ">= 0.60"
    mutation_kill_rate: ">= 0.70"
    pbt_runs_per_property: ">= 500"

fitness:
  - criterion: the cancellation confirmation surface (UI button + response payload) clearly communicates to the user that access continues until period_end and is not lost on click
    judge: persona-judge
    score_threshold: ">= 8/10"
  - criterion: the HTTP 402 response body's human-readable `message` field accurately describes the renewal action without leaking internal terminology
    judge: persona-judge
    score_threshold: ">= 7/10"

spec_drift_threshold:
  max_fix_loops_before_escalation: 3
```

### 4.5 `spec-robustness.md`

```markdown
# Spec Robustness — subscription-cancellation

(Generated by acceptance-spec S2.5 self-adversarial pass. Consumed by /acceptance-fleet
spec-gaming-detector. Not part of the strict v1 contract — augmentation only.)

## closed_vectors

- pattern: assertion_weakening
  rewrote: REQ-001 SHALL clause tightened from "atomically stop the next billing cycle's
           charge AND transition to status `cancelled_active`" to "in a single atomic
           operation (a) stop the next billing-cycle charge AND (b) transition the
           subscription to status `cancelled_active`, such that either both side-effects
           are persisted or neither is."
  source: S2.5 (S2 round 1 Q1 + Q4 left the atomicity claim implicit; S2.5 noticed
           an implementer could weaken to either-or while still passing example tests)
  rhd_pattern: test_modification

- pattern: degenerate_implementation
  added_threshold: behavior.integration_tests.property_based now includes
                   `test_subscription_status_state_machine_is_well_formed` and
                   `test_no_premium_request_after_period_end_succeeds_state_machine`;
                   behavior.unit_tests.property_based includes
                   `test_status_transition_is_monotonic_active_to_cancelled_active_to_expired`
                   and `test_cancel_atomicity_invariant_both_side_effects_or_neither`.
  rationale: the 3-state space (active / cancelled_active / expired) is small enough that
             a hardcoded lookup table or 5-row if-else cascade would satisfy every
             example-based test. State-machine PBT forces the impl to generalize across
             arbitrary operation sequences.
  source: S2.5
  rhd_pattern: degenerate_implementation

## surfaced_vectors

- pattern: branch_coverage_gap
  spec_robustness_gap: done_when.yaml enforces unit_coverage >= 0.80 (line coverage by
                       default in pytest/vitest) and mutation_kill_rate >= 0.70, but v1
                       schema does not admit a separate branch_coverage threshold. An
                       impl that exercises every line yet skips the error branch of the
                       period-boundary check (e.g. always returns `active`-equivalent
                       authorization) could pass current thresholds if the mutation set
                       happens not to flip that branch.
  verifier_hint: /acceptance-fleet spec-gaming-detector — measure branch coverage on the
                 modules implementing REQ-002, REQ-003, REQ-005. If branch_coverage <
                 0.60 even when mutation_kill_rate >= 0.70, flag as gaming_risk +3 and
                 surface the un-covered branches for /acceptance-spec narrowing.
  affects: REQ-002, REQ-003, REQ-005
  rhd_pattern: coverage_gaming

- pattern: session_cache_revocation_gap
  spec_robustness_gap: REQ-003 mandates "deny premium feature access with immediate
                       effect on the next premium-feature request" but does not specify
                       how cached session tokens / authorization claims minted before
                       `period_end` are invalidated. An impl could embed `status=active`
                       claims in a JWT with a long TTL and never re-check the database
                       at request time, technically passing example tests where each
                       test creates a fresh session while failing in production where
                       sessions outlast `period_end`. v1 schema cannot express
                       "claim must be re-validated against fresh DB state per request".
  verifier_hint: /acceptance-fleet edge-case-hunter — derive a counter-test that
                 (i) mints a session while subscription is in cancelled_active,
                 (ii) advances clock past period_end, (iii) reuses the same session
                 for a premium feature request, (iv) asserts HTTP 402. If the impl
                 passes the example tests but fails this counter-test, flag as
                 gaming_risk +3.
  affects: REQ-003
  rhd_pattern: test_modification

## accepted_risks

- pattern: information_leakage in proposal.md "What" section
  rationale: the "What" paragraph names concrete state strings (`active`,
             `cancelled_active`, `expired`) and a concrete HTTP status (402); these
             are part of the contract itself, not test fixtures, and must appear in
             the spec for the contract to be unambiguous. They are not the kind of
             concrete (input, expected output) example tuple that invites copy-paste.

- pattern: style_manipulation on fitness criterion (renewal-prompt clarity)
  rationale: the persona-judge rubric for "clearly communicates that access continues
             until period_end" cannot be gamed by surface metrics (word count, formatting)
             without losing the underlying clarity the rubric measures. The judge sees
             the rendered UI / payload and assesses semantically.

## verifier_hints

- when scoring the cancel endpoint, /acceptance-fleet test-runner should check the
  response timing: if the API returns 200 in < 5 ms, suspect that the "atomic stop
  next billing cycle + status transition" might have been short-circuited (e.g. the
  status flip persisted but the billing-side cancellation deferred to an async job
  that the test does not observe). Cross-check that the billing-system snapshot
  immediately after the API response shows the next charge actually removed.

- for REQ-002 ("full parity"), /acceptance-fleet requirement-tracer should compare
  the set of premium-feature endpoints accessible in `active` against the set
  accessible in `cancelled_active`. The two sets must be byte-identical at the
  authorization level; any divergence is a REQ-002 violation even if no individual
  example test caught it.
```
