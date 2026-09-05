# EARS sentence → test layer × style — decision matrix

This is the source of truth that drives sub-step 4-B through 4-D. The matrix is **deterministic**: given an EARS sentence type and a PBT property opportunity, the resulting test menu is fixed. Do not improvise.

---

## Master matrix

| EARS type | Unit example | Unit PBT | Integration example | Integration PBT | E2E example | E2E PBT | PBT strength* |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Ubiquitous (`SHALL Y`) | ✓ | ✓ strong | ✓ | ✓ strong | – | – | **★★★** |
| Event-driven (`WHEN X`) | ✓ | ✓ | ✓ | ✓ | ✓ | – | ★★ |
| State-driven (`WHILE state`) | ✓ | ✓ strong | ✓ | ✓ strong | – | – | **★★★** (state-machine) |
| Unwanted (`IF cond`) | ✓ | ✓ weak (reverse) | – | – | – | – | ★ |
| Optional (`WHERE feature`) | ✓ both flag states | ✓ weak | ✓ both flag states | – | ✓ | – | ★ |

*PBT strength = how often this EARS type yields a useful property-based test. Three stars = nearly always; one star = rarely.*

---

## How to use the matrix

For each REQ in `spec.md`:

1. Identify EARS type (look at the parenthetical: `(Event-driven)`, `(Unwanted)`, etc.).
2. Look at the row. Each ✓ tells you a test kind that *might* be in scope.
3. Cross-check `done_when.yaml`: the test name(s) listed under each layer×style for this REQ are the ones you actually generate.
4. If the YAML lists a test the matrix marks `–` (e.g. an E2E test for an Unwanted REQ) — that's unusual; emit it, but flag it in the file header as a deviation.
5. If the matrix marks ✓ but the YAML has no entry, do **not** invent a test — the spec author decided that combination wasn't needed.

The matrix is a sanity check on the YAML, not an override of it.

---

## Per-EARS-type generation pattern

### Ubiquitous — `THE system SHALL <action>`

> Example: `THE billing system SHALL encrypt all stored payment credentials at rest.`

**Unit example:** call any operation that writes credentials, assert the stored form is encrypted.
**Unit PBT:** `@given(arbitrary_payment_credential())` → after any storage operation, the persisted form ≠ plaintext. This is the **global invariant pattern**.
**Integration example:** end-to-end signup flow → check DB row directly.
**Integration PBT:** any sequence of CRUD ops → snapshot of DB → no row matches the original plaintext.

### Event-driven — `WHEN trigger, THE system SHALL action`

> Example: `WHEN the user clicks "delete account", THE system SHALL display a confirmation dialog.`

**Unit example:** invoke the handler with a synthetic event, assert the response (dialog shown).
**Unit PBT:** moderate — `@given(arbitrary_event_payload())` → response is well-formed (no crashes, correct shape).
**Integration example:** real HTTP request to the trigger endpoint → assert dialog state via observable side effect.
**E2E example:** click the button in a real browser → see the dialog.

### State-driven — `WHILE state, THE system SHALL action`

> Example: `WHILE the user is offline, THE system SHALL queue operations locally.`

**Unit example:** force the state, perform operations, assert local queue is populated.
**Unit PBT:** **strongest case for state-machine PBT.** Use fast-check's `model` or Hypothesis's `RuleBasedStateMachine`. Define the legal state transitions, generate arbitrary action sequences, verify the WHILE invariant holds whenever the state is entered.
**Integration example:** simulate network disconnect (testcontainers can do this) → observe queue behavior end-to-end.

### Unwanted — `IF condition, THEN THE system SHALL mitigating-action`

> Example: `IF an API call times out, THEN THE system SHALL retry up to 3 times.`

**Unit example:** inject the condition (mock the timeout), assert retries fire.
**Unit PBT (reverse pattern):** `@given(arbitrary_input where NOT condition)` → mitigating action does *not* fire. This is the "no false positive" guarantee.
**Integration example:** rarely needed; the unit test usually suffices unless the condition spans modules.

### Optional — `WHERE feature, THE system SHALL action`

> Example: `WHERE 2FA is enabled, THE system SHALL require second factor on login.`

**Unit example:** test with the flag both ON and OFF — the flag-OFF test is the one people forget; do not forget it.
**Integration example:** end-to-end login with flag toggled.
**E2E example:** if the flag is user-toggleable in the UI, test the toggle journey itself.

---

## When to *not* generate a PBT

You will be tempted to PBT everything. Resist. If you cannot complete this sentence in 30 seconds, do not write a PBT for the REQ:

> "For any <generator>, the result must satisfy <property>, because the REQ says <quote>."

If the property feels forced or duplicates an example-based test, the REQ probably isn't a PBT candidate. Cut your losses; write the example test and move on.

---

## Pyramid ratio target (per the source doc)

Traditional: 70% unit / 20% integration / 10% E2E.
AI-coding-era recommended: **50% unit / 35% integration / 15% E2E**.

Reason: LLMs make more module-boundary errors (interface mismatches, off-by-one in payloads, wrong field types, broken contract assumptions) than they make within-function errors. Integration tests catch these; unit tests do not.

When summarizing the generated suite at the end of the skill run, report actual ratios. If you're at 80/15/5, the integration layer is under-served — note this to the user.
