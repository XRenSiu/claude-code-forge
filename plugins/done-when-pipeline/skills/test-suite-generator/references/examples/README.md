# Worked example

The end-to-end example lives in the upstream skill:
`../../../acceptance-spec/references/examples/subscription-cancellation/`.

Walk that example as the input to `test-suite-generator` and the expected
output would be:

```
tests/subscription-cancellation/
├── README.md                              # ratios, run instructions
├── existence.sh                           # 4-A — 12 checks
├── unit/
│   ├── test_cancel_use_case.py            # 4-B example — 5 tests
│   ├── test_reactivate_use_case.py        # 4-B example — 1 test
│   ├── test_subscription_creation.py      # 4-B example — 1 test
│   └── property/
│       ├── test_cancel_properties.py      # 4-B PBT — 3 properties (idempotent, invariant, invariant)
│       └── test_reverse_properties.py     # 4-B PBT — 1 property (reversible)
├── integration/
│   ├── conftest.py                        # testcontainers fixture (postgres + smtp-mock)
│   ├── test_cancel_api.py                 # 4-C example — 2 tests
│   ├── test_cancel_side_effects.py        # 4-C example — 1 test
│   ├── test_expire_job.py                 # 4-C example — 1 test
│   └── test_subscription_state_machine.py # 4-C PBT — 2 state-machine properties
├── e2e/
│   ├── playwright.config.ts
│   └── cancel-subscription.spec.ts        # 4-D — 2 tests
├── mutation.sh                            # 4-E — runs mutmut, enforces ≥70%
└── fitness/
    ├── README.md
    ├── api_callable_by_independent_engineer.rubric.md          # 4-F llm-rubric (manual run)
    └── help_center_article_reads_clearly.rubric.md             # 4-F llm-rubric (manual run)
```

This is what a successful run looks like. Use it as a calibration target when
the user asks "how much test code should there be?" — the answer scales with
the number of REQs in the spec, but the structure stays consistent.

For each generated file, the rules and templates from
`../sub-modules/*.md` apply. Do not fork the templates per-feature; if you
find yourself wanting to, update the central template instead.
