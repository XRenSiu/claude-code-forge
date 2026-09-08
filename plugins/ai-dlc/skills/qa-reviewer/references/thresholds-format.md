# thresholds-format.md — permissive thresholds schema

The `--thresholds` file is the only contract input `qa-reviewer` consumes. It tells the skill what counts as go / no-go / conditional. The format is intentionally permissive: any YAML with the recognized top-level keys works. Unknown keys are warned, not rejected.

## Minimum example

```yaml
unit_coverage_min: 0.80
mutation_kill_rate_min: 0.70
failures_allowed_max:
  total: 0
```

That's it. Everything else has defaults.

## Full schema (all fields optional except `unit_coverage_min` or equivalent)

```yaml
# === COVERAGE THRESHOLDS ===
unit_coverage_min: 0.80                  # line coverage; required unless layer is excluded
unit_branch_coverage_min: 0.60           # OPTIONAL — only enforced if runner supports
integration_coverage_min: 0.50
e2e_coverage_min: <unused — E2E doesn't typically report coverage>

# === MUTATION ===
mutation_kill_rate_min: 0.70
mutation_qualified_only: true            # if true, kill rate from a non-qualified run is ignored
mutation_surviving_mutants_max: 0        # OPTIONAL — hard cap on count regardless of rate

# === FAILURE COUNT CAPS ===
failures_allowed_max:
  existence: 0                           # never tolerate missing symbols
  unit: 0
  integration: 0
  e2e: 0
  total: 0                               # aggregate cap; usually 0 for production gate

# === PER-FAILURE-SEVERITY POLICY ===
severity_policy:
  P0_genuine_allowed: false              # any P0 = NO-GO
  P1_genuine_allowed: false              # any P1 = NO-GO
  P2_genuine_allowed_max: 5              # up to 5 P2s = CONDITIONAL
  P3_genuine_allowed_max: unlimited

# === REGRESSION POLICY (only used if --baseline provided) ===
regression_policy:
  test_was_passing_now_failing: blocking      # | conditional | ignore
  coverage_dropped_more_than: 0.05             # if drop > 5 pp, blocking
  mutation_kill_rate_dropped_more_than: 0.05

# === MAINTENANCE FAILURE POLICY ===
maintenance_policy:
  surface_in_report: true                # always show maintenance issues, even if non-blocking
  auto_fix_when_flag_set: true           # honor --auto-fix-maintenance flag
  uncertain_classifications_blocking: true   # if classifier returns needs_human → CONDITIONAL

# === E2E SPECIFICS ===
e2e_required: true                       # must run E2E layer; --layers must include it
e2e_screenshots_required_on_failure: true

# === LAYER EXEMPTIONS (use sparingly) ===
exempt_layers: []                        # e.g. ["mutation"] for projects without mutation infra
                                         # exempting any layer changes decision to CONDITIONAL by default
```

## Field semantics

### Coverage thresholds

`<layer>_coverage_min` is a fraction in [0, 1]. The runner-reported coverage must be `>= min`. If the runner doesn't report coverage for a layer, the threshold is `unsupported_by_runner` (warning, not blocking).

### Mutation

`mutation_kill_rate_min` is the primary mutation gate. `mutation_qualified_only: true` (default) means a run that wasn't qualified (upstream layer crashed) doesn't count — kill rate from a partial run is unreliable.

`mutation_surviving_mutants_max` is a hard count cap. Use sparingly — kill rate is usually the better metric because it scales with codebase size; absolute count doesn't.

### Failure counts

`failures_allowed_max` caps the number of failing tests per layer + aggregate. Production gates usually want all 0. Dev / experimental projects might tolerate `unit: 2, total: 5`.

### Severity policy

After classifier runs (maintenance vs genuine), genuine failures are graded by the runner / framework severity assignment. The severity policy decides whether a given count of each severity blocks.

- `P0_genuine_allowed: false` is almost always set — a P0 = NO-GO.
- `P2/P3` typically allowed in larger counts; they're more noise than signal at gate time.

### Regression policy

Only triggered if `--baseline=<previous qa-report.yaml>` is provided. Three kinds:
- A test that previously passed now fails.
- Coverage dropped by more than the configured threshold.
- Mutation kill rate dropped.

`blocking` makes the regression a NO-GO regardless of absolute pass; `conditional` adds CONDITIONAL; `ignore` is permissive (rare).

### Maintenance policy

Always surface maintenance issues in the report. Auto-fix only with explicit flag. `uncertain_classifications_blocking` means: if the classifier said `needs_human`, the run cannot be GO without human input — sensible default.

### E2E specifics

`e2e_required: true` and `--layers=unit` together = refuse run (cannot satisfy threshold). The skill errors out at L0.

### Layer exemptions

`exempt_layers: ["mutation"]` means the mutation layer threshold doesn't apply. But exempting a layer typically means the project doesn't have anti-gaming defense at that layer — downgrade default decision to CONDITIONAL with a caveat.

## Loading thresholds from `done_when.yaml`

If the user is wiring `qa-reviewer` into a `done_when.yaml`-driven flow (i.e. `/acceptance-fleet`), the thresholds can be pulled directly from the contract's `behavior.thresholds:` block:

```yaml
# done_when.yaml excerpt
behavior:
  unit_tests:
    example_based: [...]
    property_based: [...]
  thresholds:
    unit_coverage_min: 0.85
    mutation_kill_rate_min: 0.70
    failures_allowed_max:
      total: 0
```

Pass `--thresholds=specs/<feature>/done_when.yaml` and the skill extracts the `behavior.thresholds:` sub-tree. No conversion needed.

## When to refuse the thresholds file

- File is not valid YAML → refuse with parse error location.
- File has no recognized top-level threshold key → refuse, list what was expected.
- File specifies impossible combinations (e.g. `e2e_required: true` with `exempt_layers: ["e2e"]`) → refuse, name the conflict.

Unknown keys are *warned* (in `qa_report.caveats.unknown_threshold_keys:`) but not refused. Permissive forward-compatibility.
