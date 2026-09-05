## Intent

Users describe time in eras ("last month", "when I lived in Berlin"), not timestamps. Searching memories by relative time must return eras with scenes, not a date list.

## Track

- track: task
- reason: shape settled after G1 on 2026-09-01

## Scope

- do: relative time phrases → disambiguation prompt when eras overlap; era result cards
- dont: absolute date picker; timeline view
- hard_constraints: p95 <= 300ms; no schema migration in this issue
- success_metric: >= 60% of time searches resolve without a second query within 14 days

## Acceptance

```yaml
acceptance:
  - id: AC-001-a
    req: REQ-001
    kind: mechanical
    ears_type: event
    observe: route:POST /search/time
    given: { input: "上个月", fixture: era-overlap }
    expect: { type: disambiguation_prompt, candidates: ">= 2" }
  - id: AC-001-b
    req: REQ-001
    kind: mechanical
    ears_type: unwanted
    observe: route:POST /search/time
    given: { input: "", fixture: none }
    expect: { status: 400, error: "empty_query" }
    paired_with: AC-001-a
  - id: AC-002-a
    req: REQ-002
    kind: human
    observe: ui:data-test=era-result
    statement: result reads as a period with scenes, not a line of dates
    judge: product
    evidence: demo
thresholds:
  p95_latency_ms: "<= 300"
threshold_source: "SLO search-p95"
existence:
  - route: POST /search/time
  - ui: data-test=era-result
```

## Assumptions

| id | assumption | bound_to | risk | verify_at | signed_by |
|---|---|---|---|---|---|
| A-1 | overlap threshold is 2 eras | REQ-001 | low | AC-001-a | xrensiu |

## Depends on DOS

- objects: [Memory, Era]
- invariants: [R003]

## Links

- PSL: none　G1: none　related: none
