# Mutation testing — channel-mention-notifications

This directory holds the anti-reward-hacking gate. It enforces that the test
suite catches the kinds of code changes the implementer would otherwise
sneak past with `assert True` / coverage-only assertions.

## Files

- `pyproject.toml` — fragment to merge into the project root `pyproject.toml`.
  Defines the mutmut paths/runner so `mutmut run` knows what to mutate and
  how to run the tests.
- `mutation.sh` — runner that invokes mutmut, parses the kill-rate output,
  and exits nonzero if kill rate is below 70%.

## Threshold

70% (from `done_when.yaml.thresholds.mutation_kill_rate: ">= 0.70"`).

This is **not optional**. If you bypass this you re-open the
reward-hacking hole the done_when pipeline was designed to close.

## When to run

- Pre-merge in CI, against the unit test layer (mutmut is wired to the
  unit suite only — integration would be too slow).
- Nightly batch (optional) against the full unit + integration suite for
  a deeper signal.
- **Not in the inner dev loop** — minutes-to-hours per run.

## When kill rate drops

1. Read the surviving mutants list at the bottom of the failed run.
2. For each survivor, find the unit test that already covers that line —
   it almost always exists; the test just lacks the assertion that would
   have caught this mutation.
3. Add the missing assertion. Re-run.

If a file is genuinely un-mutable (pure DTOs, generated code), exclude
the file in `[tool.mutmut.exclude]` — do not lower the global threshold.

## Excluded by default

- `src/notifications/models.py` — pure dataclasses, mutations would be vacuous
- `src/notifications/__init__.py` — re-exports only
