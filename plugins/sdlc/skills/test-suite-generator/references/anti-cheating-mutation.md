# Anti-cheating layer: mutation testing

## Why this exists

A done_when contract that only enforces `unit_coverage >= 0.80` creates a perverse incentive: the implementer (human or AI) can write tests like

```python
def test_cancel_works():
    cancel(some_sub)
    assert True   # ← coverage counts, assertion is vacuous
```

…and hit 80% coverage without verifying anything. Coverage measures *which lines were touched*, not *whether breaking those lines would be detected*.

**Mutation testing fixes this** by injecting small bugs (mutants) into the source — flipping `<` to `<=`, changing `+` to `-`, replacing `return x` with `return None`, etc. — and checking whether the test suite catches them. The percentage of injected mutants caught is the **kill rate**.

If kill rate is high, the tests are actually exercising the logic. If kill rate is low, the tests are pretending.

For AI-generated code in particular, this matters more than usual — LLMs are very good at generating plausible-looking tests that don't actually pin down behavior. Mutation testing is the gate that prevents that from passing the contract.

---

## The mandatory threshold

`done_when.yaml` carries `thresholds.mutation_kill_rate: ">= 0.70"`. This is enforced by `ratchet` in Step 6.

**70% is the floor, not the goal.** Good test suites hit 85%+ on well-mutated code. If kill rate climbs to 95%+ and you suspect the mutation tool isn't generating interesting mutants, increase the operator set (turn on more mutation operators) rather than declaring victory.

---

## What mutmut / Stryker / PIT do

Each tool walks the AST of the source code and applies a set of mutation operators:

| Operator | Original | Mutated |
|---|---|---|
| Arithmetic | `a + b` | `a - b` |
| Comparison | `x < y` | `x <= y`, `x > y`, `x == y` |
| Boolean | `a and b` | `a or b` |
| Constant | `return 0` | `return 1`, `return -1`, `return None` |
| Conditional | `if cond:` | `if not cond:` |
| Boundary | `range(n)` | `range(n-1)`, `range(n+1)` |
| Statement deletion | `do_thing()` | `pass` |

For each mutated version, the tool runs the test suite. If a test fails, the mutant is **killed**. If all tests pass, the mutant **survives** — meaning the test suite did not detect this bug, which is a real problem.

---

## Reading kill-rate output

Typical output:

```
Killed:    47   (75.8%)
Survived:  10   (16.1%)
Timeout:    3    (4.8%)
NoCov:      2    (3.2%)
─────────────────────────
Total:     62
Score:    75.8%
```

- **Killed** — bug introduced, test failed → good.
- **Survived** — bug introduced, all tests passed → **bug not covered**. List them.
- **Timeout** — mutated code looped forever → counted as killed; not a problem unless the rate is high.
- **NoCov** — line not covered by any test → killed-by-default but signals weak coverage.

Always look at the surviving mutants. They tell you exactly what your tests miss. Example:

```
Survived:
  src/cancel.ts:47   "x <= boundary"   →   "x < boundary"
```

This means: changing `<=` to `<` doesn't break any test. So no test pins down the *boundary value itself*. Add `test_cancel_exactly_at_end_date()`.

---

## How long does it take?

Mutation testing is **N × longer than the test suite**, where N = number of mutants (typically 50-500 for a small module, thousands for a large codebase). For a ~5-second test suite, expect mutation runs of 5-30 minutes for small modules, hours for large ones.

Recommendations:
- Do **not** run mutation in the inner dev loop.
- Run it pre-merge (in CI), or nightly, or as a Step 6 gate before declaring "done".
- Use the tool's incremental mode (`mutmut --incremental`, Stryker's `incremental`) if available.

---

## What ratchet does with the kill-rate signal

`ratchet` reads `done_when.yaml.thresholds.mutation_kill_rate` and runs the `mutation.sh` script from 4-E. If kill rate is below threshold:

1. First time → tells the implementer "kill rate is X; surviving mutants are at <files/lines>; add tests that distinguish these cases".
2. After `spec_drift_threshold.max_fix_loops_before_escalation` attempts (default 3) without progress → escalates to the user: "kill rate stuck at X across N attempts; either the spec is missing acceptance criteria these mutants should fail against, or the source code is structured such that meaningful mutants are unreachable. Recommend reviewing REQ-NNN."

This escalation is the spec-drift bailout (the source doc's Pitfall #5 fix).

---

## When to lower the threshold (rare)

- For pure-data DTOs / generated code → kill rate can legitimately be low; the source has little logic to mutate. Exempt those files via the tool's `exclude:` config rather than lowering the global threshold.
- For one-off scripts or migrations → mutation testing is overkill; consider omitting the threshold for that path.

Never lower the threshold to "make CI green". That defeats the entire purpose. If the threshold is genuinely too high for the project's testability, fix the testability (extract logic from hard-to-test paths), don't paper over.
