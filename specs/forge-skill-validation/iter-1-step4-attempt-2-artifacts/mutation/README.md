# Mutation testing (channel-mention-notifications)

Mutation tests run via `bash mutation.sh`. They take time (minutes to hours
depending on project size) and so are typically run pre-merge in CI or
nightly, not in the inner dev loop.

The kill-rate threshold (**70%**) is **not optional**. It is the
anti-reward-hacking gate from `done_when.yaml.thresholds.mutation_kill_rate`.
If kill rate drops below threshold, look at the surviving mutants — they
pinpoint exactly which assertions are missing from the suite.

If you find yourself wanting to lower the threshold, instead:

1. Look at the surviving mutants — usually they reveal a real test gap.
2. If a file is genuinely un-mutable (pure DTOs, generated code), exclude
   it in `pyproject.toml` (`[tool.mutmut].paths_to_mutate`) — don't lower
   the global threshold.

## Why this matters

A `done_when.yaml` that only enforces `unit_coverage >= 0.80` creates a
perverse incentive: the implementer (human or AI) can write tests like

```python
def test_cancel_works():
    cancel(some_sub)
    assert True   # ← coverage counts, assertion is vacuous
```

…and hit 80% coverage without verifying anything. Mutation testing
introduces small bugs (e.g. `<` → `<=`, `a + b` → `a - b`) and counts how
many of them are caught by the suite. If kill rate is high, the tests
actually exercise the logic. If kill rate is low, the tests are
pretending.

## Mapping back to the contract

`done_when.yaml` field → behavior:

| Field | Value | Enforcement |
|---|---|---|
| `thresholds.mutation_kill_rate` | `">= 0.70"` | `mutation.sh` exits nonzero below 70% |
| `thresholds.unit_coverage` | `">= 0.80"` | enforced by `pytest --cov` separately |
| `thresholds.integration_coverage` | `">= 0.60"` | enforced by `pytest --cov` separately |
| `thresholds.pbt_runs_per_property` | `">= 500"` | encoded as `max_examples=500` in PBT tests |
