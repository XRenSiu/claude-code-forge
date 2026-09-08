# EARS — five sentence types

EARS (**E**asy **A**pproach to **R**equirements **S**yntax) is a constrained natural-language template. Its real value is **not** that it reads well — it reads slightly awkwardly. Its value is that the rigid template **forces hidden assumptions to surface as visible gaps**. If you have to fill in a `WHEN`, you have to know the trigger; if you don't, that's a question to ask.

Use it as a translation intermediary between fuzzy NL and unambiguous test derivation. Each sentence type maps cleanly onto a specific test-derivation pattern in Step 4.

---

## The five types

### 1. Ubiquitous — unconditional rule

```
THE <system> SHALL <action>.
```

A rule that holds at all times, no precondition. Often invariants or cross-cutting policies.

**Example:** `THE billing system SHALL encrypt all stored payment credentials at rest.`

**When to use:** the requirement applies to *every* state, *every* event. If you have to add "when X" or "if Y", it is not Ubiquitous — pick another type.

**Maps to:** unit + integration tests; the strongest case for property-based testing (global invariant — "no operation sequence can produce a state violating this").

---

### 2. Event-driven — trigger → response

```
WHEN <trigger event>, THE <system> SHALL <action>.
```

Describes "user does X, system responds Y". The most common type.

**Example:** `WHEN the user clicks "delete account", THE system SHALL display a confirmation dialog before performing any state change.`

**When to use:** a discrete event causes a discrete response.

**Maps to:** example-based unit + integration + e2e tests. Moderate-strength PBT case ("for any plausible trigger payload, response shape is consistent").

---

### 3. State-driven — state implies behavior

```
WHILE <system is in state>, THE <system> SHALL <action>.
```

Describes a continuous or repeated behavior that holds whenever the system is in some state.

**Example:** `WHILE the user is offline, THE system SHALL queue outgoing operations locally and replay them in order on reconnect.`

**When to use:** the requirement is about behavior persisting across some duration of being in a state, not a one-shot reaction to an event.

**Maps to:** **strongest case for state-machine PBT** (fast-check `model`, Hypothesis `RuleBasedStateMachine`). Any operation sequence that transitions into the state must exhibit the behavior — the property checker explores those sequences for you.

---

### 4. Unwanted — exception / forbidden condition

```
IF <undesirable condition>, THEN THE <system> SHALL <mitigating action>.
```

Describes error handling, abuse, edge cases, race conditions.

**Example:** `IF an API call times out, THEN THE system SHALL retry up to 3 times with exponential backoff before failing.`

**When to use:** the requirement is about what happens in failure / exception / bad-input cases.

**Maps to:** example-based error-injection tests; weaker PBT case, but a useful pattern is **reverse-PBT** — generate arbitrary inputs where the condition is *not* met and assert the mitigating action does *not* fire.

---

### 5. Optional — feature flag / opt-in

```
WHERE <feature is included / flag is on>, THE <system> SHALL <action>.
```

Describes behavior gated by a feature flag, license, plan tier, or compile-time option.

**Example:** `WHERE two-factor authentication is enabled for the user, THE system SHALL require the second factor on every login attempt.`

**When to use:** the behavior only applies when something is turned on. If the feature is always on, use Ubiquitous or Event-driven.

**Maps to:** example-based tests under both flag-on and flag-off (the latter often forgotten). Weaker PBT case.

---

## Selection cheat-sheet

Ask yourself, in order:

1. Is there a trigger event? → **Event-driven**.
2. Is there a precondition state that lasts? → **State-driven**.
3. Is there an error / forbidden condition to handle? → **Unwanted**.
4. Is there a feature flag / opt-in gate? → **Optional**.
5. Otherwise (always holds) → **Ubiquitous**.

If two apply, the requirement is probably two REQs — split it.

### Tie-breaker: State-driven vs Unwanted (the most common confusion)

Both can use a precondition. The decisive question is **what kind of action follows**:

- **State-driven** = the action is a *continuous / repeated behavior* that holds for the whole time the system is in the state. ("WHILE offline, queue all writes locally." — every write that occurs is queued, for as long as offline lasts.)
- **Unwanted** = the action is a *one-shot conditional branch* fired by the precondition meeting some incoming event. ("IF the API call times out, retry up to 3 times." — one branch per timeout, not a persistent behavior.)

**Rule of thumb**: if you can rewrite the SHALL as "any operation that happens during the state is treated this way", it's State-driven. If you can rewrite it as "when X occurs and condition Y holds, do Z (once)", it's Unwanted (`IF Y AND-triggered-by X, THEN Z`).

Example side-by-side:

| Candidate sentence | Right type | Why |
|---|---|---|
| `WHILE user is offline, queue all writes locally and replay on reconnect.` | State-driven | Every write during the offline window is queued. Continuous behavior. |
| `IF the user is in DND when a mention arrives, suppress the push notification for that message.` | Unwanted | Single message → single suppression decision. One-shot, not persistent. State-driven `WHILE in DND, suppress notifications` reads grammatical but the SHALL action is per-event, not "continuous suppression of an ongoing thing". |

When in doubt, prefer **Unwanted** for per-event conditional handling — it routes to the reverse-PBT pattern that test-suite-generator already supports, and avoids accidentally implying "persistent behavior" that no test will exercise.

---

## Multi-type composition

Real requirements often need multiple sentence types describing related slices of behavior. Encode each slice as its own REQ with its own ID, and link them in the spec by referencing each other's IDs in prose:

```markdown
## REQ-001 (Event-driven)
WHEN the user clicks "cancel subscription" AND the current subscription status is `active`,
THE system SHALL atomically (a) stop the next billing cycle's charge AND (b) set status to `cancelled_active`.
source: user clarified at S2 round 1 Q2 — "atomic" means both succeed or both roll back.

## REQ-002 (State-driven, follow-on from REQ-001)
WHILE the subscription is in status `cancelled_active`,
THE system SHALL retain all premium feature access until `end_date` at UTC 23:59:59.
source: user clarified at S2 round 1 Q1 — UTC boundary, not local-time.

## REQ-003 (Unwanted, follow-on from REQ-002)
IF the user attempts to create a new subscription WHILE in status `cancelled_active`,
THEN THE system SHALL reject the creation AND surface "your current subscription remains active until <end_date>".
source: user added this case unprompted at S2 round 1.
```

This composition pattern (Event + State + Unwanted around one feature) is extremely common. Recognize it during S1.

---

## Common drafting mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| Combining trigger + state in one sentence | "WHEN the user is offline and clicks X, ..." | Split — the offline part is `WHILE`, the click is `WHEN`. Either nest or split into two REQs. |
| Vague subject | "the system" when it should be "the billing module" | Name the concrete component if the brief allows. |
| Vague action | "SHALL handle X gracefully" | "Gracefully" is a `[?]` — what does it actually do? Display? Log? Retry? Surface to user? |
| Implementation in the SHALL | "SHALL write to Postgres" | Storage choice is implementation, not requirement. Write "SHALL persist". Implementation comes later in design. |
| Missing measurement | "SHALL respond quickly" | Quickly = how many ms? Either get a number or write a `[?]`. |
| Verb that is its own assumption | "SHALL synchronize" | Sync to what? In which direction? With what conflict resolution? All `[?]`. |
| Cross-REQ causal indirection | "SHALL silence the notification produced by REQ-001" | Each REQ must be independently testable. Restate the precondition in REQ-002's own WHILE/IF clause (e.g. `IF a mention is delivered while the recipient is in DND, THEN ...`) — do not point at another REQ's runtime artifact. See Iron rule 8 in SKILL.md. |
| AND-compound SHALL packing two independent actions | "WHEN tick reaches end, SHALL (a) transition status to expired AND (b) deny premium access on next request" | Split into two REQs. One SHALL = one independently-derivable action. The two halves above have *different triggers* in practice — (a) fires on the clock tick, (b) fires on the next premium request. If you can derive a test for one half without the other half being involved at runtime, they are two REQs, not one. Acceptable AND-compound is **only** when both halves describe *one atomic indivisible effect* of the same trigger (e.g. `SHALL atomically set status to cancelled AND stop next-billing-cycle charge` — where atomicity itself is part of the contract). See Iron rule 11 in SKILL.md. |
