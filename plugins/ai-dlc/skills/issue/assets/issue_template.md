<!-- issue body template — 段落序是产物序（出口可检）。标题另给：<type>: <一句话> -->

## Intent

<一段：为什么做、给谁、不做会怎样。可以引用 PSL 切片（PSL-xxx）或 G1 签字版形态草案哈希。>

## Track

- track: task            <!-- psl | task -->
- reason: <一句：为什么这条轨；PSL 轨写 G1 记录路径与形态草案 sha256>

## Scope

- do: <本次交付的行为，逐条>
- dont: <明确不做的，逐条>
- hard_constraints: <性能 / 兼容 / 合规 / 禁改路径>
- success_metric: <上线后怎么看它成功：指标 + 阈值 + 观测窗口>

## Acceptance

```yaml
acceptance:
  - id: AC-001-a
    req: REQ-001
    kind: mechanical
    observe: route:POST /search/time      # 观察边界：route: | cli: | ui:data-test= | db_field: | event:
    given: { input: "上个月", fixture: era-overlap }
    expect: { type: disambiguation_prompt, candidates: ">= 2" }
  - id: AC-001-b
    req: REQ-001
    kind: mechanical
    ears_type: unwanted                   # AC-001-a 的 unhappy 孪生
    observe: route:POST /search/time
    given: { input: "", fixture: none }
    expect: { status: 400, error: "empty_query" }
    paired_with: AC-001-a
  - id: AC-002-a
    req: REQ-002
    kind: human
    observe: ui:data-test=era-result
    statement: 返回的是"有场景的时期"，不是一行日期
    judge: product                        # product | design | tech（封闭集）
    evidence: demo                        # checklist | demo
thresholds:
  p95_latency_ms: "<= 300"                # 阈值本身就是判据；来源写在 threshold_source
threshold_source: "SLO: search-p95 (grafana dashboard X)"
existence:                                # 只留观察边界，不写文件 / 函数
  - route: POST /search/time
  - ui: data-test=era-result
```

## Assumptions

| id | assumption | bound_to | risk | verify_at | signed_by |
|---|---|---|---|---|---|
| A-1 | <答不上来的承重槽，写成假设> | REQ-001 | <medium> | AC-001-a / G3 | <name> |

## Depends on DOS

- objects: [Memory, Era]                 <!-- 结构化字段；闭包只查这里。无则写 none -->
- invariants: [R003]

## Links

- PSL: <path 或 none>　G1: <path 或 none>　related: #<n>
