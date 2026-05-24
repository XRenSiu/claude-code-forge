# PBT property archetypes

Property-based testing is not a magic wand — it works when you can name the **property**. There are six archetypes that cover ~95% of practical cases. If your REQ doesn't fit one of them, do not invent one; emit an example-based test instead.

Each entry below has: (a) when it applies, (b) the generic pattern, (c) snippets in Python (Hypothesis) and TypeScript (fast-check).

---

## 1. Invariant — "X is always true after any operation"

**When:** an EARS Ubiquitous or State-driven REQ. The property is a single condition that must hold across all reachable states.

**Pattern:**
```
∀ input → operation(input) → invariant(state) is true
```

**Python (Hypothesis):**
```python
from hypothesis import given, strategies as st

@given(st.lists(operations_strategy(), max_size=50))
def test_no_negative_balance_ever(ops):
    account = Account()
    for op in ops:
        account.apply(op)
        assert account.balance >= 0
```

**TypeScript (fast-check):**
```typescript
import fc from 'fast-check';

test('no negative balance', () => {
  fc.assert(fc.property(fc.array(opArb, { maxLength: 50 }), (ops) => {
    const acct = new Account();
    for (const op of ops) {
      acct.apply(op);
      if (acct.balance < 0) return false;
    }
    return true;
  }));
});
```

---

## 2. Idempotent — "doing it twice equals doing it once"

**When:** Event-driven REQs where the operation should be safe to retry. Very common in API design (PUT, DELETE).

**Pattern:**
```
∀ input → op(op(input)) ≡ op(input)
```

**Python:**
```python
@given(active_subscriptions())
def test_cancel_is_idempotent(sub):
    cancel(sub); s1 = sub.snapshot()
    cancel(sub); s2 = sub.snapshot()
    assert s1 == s2
```

**TypeScript:**
```typescript
test('cancel is idempotent', () => {
  fc.assert(fc.property(activeSubArb, (sub) => {
    cancel(sub);
    const s1 = snapshot(sub);
    cancel(sub);
    const s2 = snapshot(sub);
    return deepEqual(s1, s2);
  }));
});
```

---

## 3. Reversible — "undo composed with do is the identity"

**When:** there's an explicit inverse operation. Common in undo/redo, transactions, soft-delete + restore, cancel + reactivate.

**Pattern:**
```
∀ input → undo(do(input)) ≡ input        (within the legal window)
```

**Python:**
```python
@given(active_subscriptions(), st.datetimes_within_paid_period())
def test_cancel_then_reactivate_within_window_is_identity(sub, when):
    before = sub.snapshot()
    cancel(sub, at=when)
    reactivate(sub, at=when + timedelta(seconds=1))
    after = sub.snapshot()
    # status returns to active; cancelled_at is cleared
    assert after.status == before.status
    assert after.cancelled_at is None
```

**Note:** reversibility usually has a *window* — after `end_date` the inverse is no longer legal. Encode that in the generator (`st.datetimes_within_paid_period()`), not in the assertion.

---

## 4. Boundary — "behavior changes correctly at the boundary"

**When:** any REQ with a threshold, cutoff, or boundary value (the `end_date` in subscription-cancel, retry count of 3, max upload of 10 MB).

**Pattern:**
```
∀ value < boundary → behavior_A
∀ value ≥ boundary → behavior_B
specifically test value == boundary, value == boundary - 1, value == boundary + 1
```

**Python:**
```python
@given(st.integers(min_value=0, max_value=10))
def test_retries_stop_after_three(retry_count):
    handler = RetryingHandler(max_retries=3)
    for _ in range(retry_count):
        handler.attempt_with_timeout()
    if retry_count <= 3:
        assert not handler.gave_up
    else:
        assert handler.gave_up
```

Hypothesis automatically explores around boundaries with its `example()` and shrinking, but explicit `@example(3)` / `@example(4)` is good defensive practice.

---

## 5. Monotonic — "as X increases, Y does not decrease (or vice versa)"

**When:** sort stability, rate limiting, accumulators, anything you'd expect to grow only in one direction.

**Pattern:**
```
∀ x1 < x2 → f(x1) ≤ f(x2)   (non-decreasing)
```

**Python:**
```python
@given(st.lists(st.integers(min_value=0), min_size=2))
def test_balance_only_decreases_on_withdrawal(amounts):
    sorted_amounts = sorted(amounts)
    account = Account(initial=1000)
    for amt in sorted_amounts:
        before = account.balance
        account.withdraw(amt)
        assert account.balance <= before  # never increases on withdrawal
```

---

## 6. State-machine — "no operation sequence violates the state model"

**When:** State-driven EARS REQs, or any feature with explicit lifecycle states (subscription: trialing → active → cancelled_active → expired). **The strongest application of PBT, period.**

**Python (Hypothesis `RuleBasedStateMachine`):**
```python
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant
from hypothesis import strategies as st

class SubscriptionStateMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.sub = Subscription.new_trialing()

    @rule()
    def cancel(self):
        cancel(self.sub)

    @rule()
    def reactivate(self):
        if self.sub.status == 'cancelled_active' and now() < self.sub.end_date:
            reactivate(self.sub)

    @rule(amount=st.integers(min_value=1, max_value=1000))
    def attempt_charge(self, amount):
        charge(self.sub, amount)

    @invariant()
    def status_is_known(self):
        assert self.sub.status in {'trialing', 'active', 'cancelled_active', 'expired'}

    @invariant()
    def no_charge_when_cancelled(self):
        if self.sub.status == 'cancelled_active':
            assert all(c.scheduled_for > self.sub.end_date for c in self.sub.charges)

TestSubscriptionStateMachine = SubscriptionStateMachine.TestCase
```

**TypeScript (fast-check `model`):**
```typescript
import * as fc from 'fast-check';

class SubscriptionModel { /* tracks expected state */ }
class SubscriptionReal { /* the real impl */ }

const CancelCommand = (): fc.Command<SubscriptionModel, SubscriptionReal> => ({
  check: (m) => m.status === 'active',
  run: (m, r) => { m.status = 'cancelled_active'; r.cancel(); }
});
// ... ReactivateCommand, ChargeCommand, etc.

test('subscription state machine', () => {
  fc.assert(fc.property(
    fc.commands([fc.constant(CancelCommand()), /* ... */], { maxCommands: 50 }),
    (cmds) => fc.modelRun(() => ({ model: new SubscriptionModel(), real: new SubscriptionReal() }), cmds)
  ));
});
```

State-machine PBT is the single highest-ROI test you can write for any feature with a status enum. **If your REQ has a status field, you owe yourself a state-machine PBT.**

---

## Generator hygiene

- **Generators must be in the test file or a `generators/` sibling**, not buried in the source code. The source should know nothing about Hypothesis or fast-check.
- **Shrinking matters.** Use library-native combinators (`st.builds`, `fc.record`) so the framework can shrink. Hand-rolled `st.lists(my_random_thing())` will shrink poorly.
- **Bound size.** Always pass `max_size` / `maxLength`. An unbounded list strategy will eventually generate a 10k-element input and timeout.

---

## Anti-patterns

| Anti-pattern | Why it's bad |
|---|---|
| `@given(st.text())` with no constraint | Hypothesis will spend ages trying invalid Unicode, dominate the test budget on irrelevant inputs. Constrain to the alphabet you actually need. |
| Asserting on randomly-generated specific values | "After processing input X, result should be Y" where X and Y both came from the generator. This is just an example test in PBT clothing — it provides no extra coverage. |
| A property that's secretly the implementation | If the property is `f(x) == reference_impl(x)` and `reference_impl` is just a copy of `f`, the test passes trivially. Use a *different* reference (mathematical definition, naive O(n²) version, etc.). |
| One giant PBT with 5 invariants | Split. When it fails, you want to know *which* invariant broke, not stare at a 5-line assertion. |
