# divergence-types.md — three classification buckets

Every drift signal emitted by `spec-drift-detector` gets exactly one of three types. The taxonomy is single-valued; a signal that affects both contract and behavior is split into two signals. This document gives the precise definition + worked examples per type.

---

## Type 1: `timing_mismatch`

**Definition:** The behavior described by the spec occurs in the code, but the *timing* of when it occurs is different.

Sub-categories:
- Synchronous vs asynchronous: spec says "immediately"; code defers to a queue.
- Hot path vs deferred: spec implies "during the request"; code runs as a background job.
- Real-time vs batch: spec implies "as it happens"; code aggregates and processes nightly.
- Eager vs lazy: spec implies "on save"; code computes on read.
- Granular vs debounced: spec implies "per keystroke"; code throttles to once per second.

### Worked example 1: sync → async

Spec (excerpt from REQ-001):
> "Cancellation SHALL take effect immediately upon user confirmation."

Code (`src/billing/cancel.ts:42-58`):
```typescript
async function cancelSubscription(sub_id: string) {
  await cancellation_queue.enqueue({ sub_id, requested_at: new Date() });
  return { acknowledged: true, eta: '24h' };
}
```

`code_does:` Cancellation is *queued*, processed by a worker within 24h. Not immediate.

Drift signal:
- `divergence_type: timing_mismatch`
- `spec_claim: "Cancellation takes effect immediately upon user confirmation"`
- `code_behavior: "Cancellation is queued, processed within 24h"`
- `divergence_severity: high` (24h vs immediate is a material difference for billing).

### Worked example 2: real-time → batch

Spec:
> "Audit log entries are written as actions occur."

Code: `audit_log.flushPending()` is called by a cron job once per minute.

Drift signal:
- `divergence_type: timing_mismatch`
- `spec_claim: "audit log written in real-time"`
- `code_behavior: "audit log batched, flushed once per minute"`
- `divergence_severity: medium` (1-minute delay; usually acceptable for audit but worth flagging if compliance requires real-time).

### Worked example 3: eager → lazy

Spec:
> "User's display name is rendered consistently across all pages after editing in Settings."

Code: `User.displayName` is read from cache; cache invalidation happens on next session expiry (up to 24h).

Drift signal:
- `divergence_type: timing_mismatch`
- `spec_claim: "display name renders consistently after editing"`
- `code_behavior: "display name updates on next session refresh (up to 24h)"`
- `divergence_severity: medium`.

---

## Type 2: `behavior_mismatch`

**Definition:** The behavior itself differs — what the spec says the system does versus what the code does are materially different actions.

Sub-categories:
- Wrong action: spec says "send email"; code "sends SMS" (different action entirely).
- Wrong value: spec says "applies 5% discount"; code "applies 3% discount".
- Wrong target: spec says "logs to audit log"; code logs to stderr.
- Wrong condition: spec says "fires when subscription cancels"; code fires on any state change.
- Missing action: spec says "X SHALL also Y"; code only does X.
- Extra action: spec says "X"; code does X *and* something the spec didn't authorize.

### Worked example 1: wrong action

Spec:
> "On cancellation, the system SHALL send the user a confirmation email with refund details."

Code:
```typescript
// src/billing/cancel.ts
async function cancel(sub_id) {
  await mutate_status(sub_id, 'cancelled');
  await sms_service.send(user.phone, 'Subscription cancelled.');
  // Email is never sent.
}
```

Drift signal:
- `divergence_type: behavior_mismatch`
- `spec_claim: "send confirmation email with refund details"`
- `code_behavior: "sends SMS with no refund details; no email"`
- `divergence_severity: high`.

### Worked example 2: wrong value

Spec:
> "Trial users SHALL receive a 15-day grace period after cancellation."

Code:
```typescript
const GRACE_PERIOD_DAYS = 7;  // last touched in commit a1b2c3d
```

Drift signal:
- `divergence_type: behavior_mismatch`
- `spec_claim: "15-day grace period"`
- `code_behavior: "7-day grace period"`
- `divergence_severity: high`.

### Worked example 3: missing action

Spec:
> "On cancellation, the system SHALL revoke active sessions AND invalidate any pending invoices."

Code: Only revokes sessions; does not touch pending invoices.

Drift signal:
- `divergence_type: behavior_mismatch`
- `spec_claim: "revoke sessions AND invalidate pending invoices"`
- `code_behavior: "revokes sessions; does not touch pending invoices"`
- `divergence_severity: medium` (depends on whether stale invoices cause downstream harm).

### Worked example 4: extra unauthorized action

Spec:
> "Cancellation is silent — no notification is sent to the user."

Code: Sends a notification via internal messaging system on cancellation.

Drift signal:
- `divergence_type: behavior_mismatch`
- `spec_claim: "no notification"`
- `code_behavior: "sends internal notification"`
- `divergence_severity: low | medium` depending on privacy implications.

---

## Type 3: `contract_mismatch`

**Definition:** The interface / signature / data shape / parameter list differs between spec and code. The behavior may be identical, but the *contract* with callers differs.

Sub-categories:
- HTTP method / route differs: spec says `POST /api/cancel`; code registers `DELETE /api/subscription/<id>`.
- Status code differs: spec says "returns 204"; code "returns 200 with empty body".
- Return shape differs: spec says "returns {status, end_date}"; code returns "{status, end_date, internal_flag, audit_id}".
- Required parameters differ: spec says "takes {sub_id}"; code requires "{sub_id, reason}".
- Optional parameter semantics differ: spec says "reason is optional, defaults to 'user_initiated'"; code defaults to null.
- Type / format differs: spec says "timestamp is ISO 8601 UTC"; code returns Unix epoch milliseconds.
- Error shape differs: spec says "errors return {code, message}"; code returns "{error, hint}".
- Header contract differs: spec says "responds with `X-RateLimit-Remaining`"; code doesn't set the header.

### Worked example 1: return shape extra fields

Spec:
> "The cancellation endpoint SHALL return {subscription_id, status, cancelled_at}."

Code: Returns `{subscription_id, status, cancelled_at, internal_invoice_id, audit_trace_id, debug_info}`.

Drift signal:
- `divergence_type: contract_mismatch`
- `spec_claim: "returns {subscription_id, status, cancelled_at}"`
- `code_behavior: "returns above plus {internal_invoice_id, audit_trace_id, debug_info}"`
- `divergence_severity: medium` (leaks internal fields; potential information disclosure).

### Worked example 2: missing required parameter spec

Spec:
> "POST /api/subscription/cancel takes {sub_id}."

Code: Requires `{sub_id, idempotency_key}` (returns 400 if `idempotency_key` is missing).

Drift signal:
- `divergence_type: contract_mismatch`
- `spec_claim: "request body: {sub_id}"`
- `code_behavior: "requires {sub_id, idempotency_key}; missing key returns 400"`
- `divergence_severity: high` (clients implementing per spec will fail).

### Worked example 3: status code mismatch

Spec:
> "Successful cancellation returns 204 No Content."

Code: Returns `200 OK` with body `{success: true}`.

Drift signal:
- `divergence_type: contract_mismatch`
- `spec_claim: "204 No Content"`
- `code_behavior: "200 OK with body {success: true}"`
- `divergence_severity: low | medium` (depends on whether clients depend on the 204 specifically).

### Worked example 4: type format

Spec:
> "Timestamps are ISO 8601 strings in UTC, e.g. `2026-05-25T14:32:07Z`."

Code:
```typescript
return { cancelled_at: Date.now() };  // Unix epoch ms number
```

Drift signal:
- `divergence_type: contract_mismatch`
- `spec_claim: "ISO 8601 UTC string"`
- `code_behavior: "Unix epoch milliseconds (number)"`
- `divergence_severity: high` (any caller parsing as ISO will fail).

---

## When a signal could be multiple types

If a single observation suggests both, say, `behavior_mismatch` and `contract_mismatch` (the impl returns a different value AND wraps it in a different shape), emit **two separate drift signals** rather than picking one. The taxonomy is single-valued per signal — splitting keeps the consumer's signal-handling logic simple. Cross-reference via `related_signal_id:` if downstream needs to know they originate from the same observation.

## Type filtering at the `--output` level

The skill output is the full list. Downstream consumers (like `/meta-judge`) filter by type if their workflow only cares about one. For example, `/acceptance-fleet` might only treat `behavior_mismatch` as ratchet-relevant, while `contract_mismatch` is surfaced to humans only.

## Non-functional drift caveat

If the drift relates to a non-functional spec claim (performance, availability, security posture), the type is usually `behavior_mismatch` but **the signal is only emitted if there's measurement evidence** (e.g. from a `--qa-report` perf layer). Without measurement, you'd be emitting "spec says fast, code might be slow" — vacuous. Per iron rule 8 in `SKILL.md`, skip the signal or route to `needs_human`.
