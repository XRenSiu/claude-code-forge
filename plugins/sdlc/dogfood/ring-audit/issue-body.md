## Intent

审计 sdlc 插件九环 + 脊柱上的每个配件（skill / agent / script / asset / 人签门 / 环契约），回答用户的四问：是否缺少、是否需要、是否实现、名字是否合适。
按 sdlc 自己的理念做：配件的存在理由是它填了一个引擎自己填不了的缺口（PSL-002），"已实现"是声明 / 编译 / 验证三态而不是布尔（PSL-010），
命名建议不等于重命名（PSL-014），空白诚实登记（PSL-017）。世界见 PSL-sdlc-ring-audit.md；形态见 G1 签字版 derived/form-draft.md（sha256 见 Track）。
不做会怎样：README 的表格读起来像"27 个 skill 都实现了"，而 gate.json 全部 static_only——没有人知道哪些环节真的缺、哪些名字只是上游遗留。

## Track

- track: psl
- reason: 语义份额主导（"必要 / 名字合适"是判断），G1 于 2026-09-05 由代签 agent 裁决；记录 g1-record.md；形态草案 sha256 `746c56ef3e39e8e7089db0914bc01015b6dd522ef622c449e3d6260fbc10880d`

## Scope

- do: 一份按环组织的审计报告 AUDIT.md；同构的机器可读 audit.yaml；检查脚本（命令 `check-audit`）；每个配件一条三维 Assessment（needed / implemented / naming）；每环的 missing（缺少）；run_evidence 节；提案清单（每条有去向）
- dont: 不重命名任何 skill / agent；不修改被审的 SKILL.md / gate.json / 脚本；不实现本次识别出的缺少配件；不给确定性配件套世界模型
- hard_constraints: 被审目录（plugins/sdlc/skills、agents、docs）在卡提交中零改动；Assessment 每维 ≥ 1 PSL-ID 与 ≥ 1 Evidence；audit.yaml 顶层 rings 恰为 10 项（R0–R8 + spine）
- success_metric: 提案清单中 ≥ 3 条在 7 天内落为 GitHub issue 或 skill fix_list 条目；被审目录被卡提交触碰的文件数 = 0

## Acceptance

```yaml
acceptance:
  - id: AC-001-a
    req: REQ-001
    kind: mechanical
    ears_type: event
    observe: cli:check-audit
    given: { input: "complete audit.yaml", psl: "PSL-sdlc-ring-audit index 001..017", required_parts: "agent.card-implementer, agent.comment-fixer, agent.fix-verifier, agent.pr-reviewer, agent.review-triager" }
    expect: { exit: 0, rings: 10, parts_total: 42, parts_without_assessment: 0, required_parts_missing: 0 }
  - id: AC-001-b
    req: REQ-001
    kind: mechanical
    ears_type: unwanted
    observe: cli:check-audit
    given: { input: "audit.yaml with one ring entry removed" }
    expect: { exit: 1, error: "ring_missing" }
    paired_with: AC-001-a
  - id: AC-002-a
    req: REQ-002
    kind: mechanical
    ears_type: event
    observe: cli:check-audit
    given: { input: "complete audit.yaml", psl: "PSL-sdlc-ring-audit index 001..017" }
    expect: { dims_without_psl_id: 0, dims_with_unknown_psl_id: 0, dims_without_evidence: 0 }
  - id: AC-002-b
    req: REQ-002
    kind: mechanical
    ears_type: unwanted
    observe: cli:check-audit
    given: { input: "audit.yaml with one assessment dimension whose psl_ids is empty" }
    expect: { exit: 1, error: "psl_id_missing" }
    paired_with: AC-002-a
  - id: AC-003-a
    req: REQ-003
    kind: mechanical
    ears_type: event
    observe: cli:check-audit
    given: { input: "complete audit.yaml" }
    expect: { boolean_implemented: 0, implemented_outside_enum: 0, rename_true: 0 }
  - id: AC-003-b
    req: REQ-003
    kind: mechanical
    ears_type: unwanted
    observe: cli:check-audit
    given: { input: "audit.yaml with implemented set to a boolean on one part" }
    expect: { exit: 1, error: "boolean_implemented" }
    paired_with: AC-003-a
  - id: AC-004-a
    req: REQ-004
    kind: mechanical
    ears_type: event
    observe: cli:check-audit
    given: { input: "complete audit.yaml" }
    expect: { rings_without_missing_key: 0, orphan_gaps: 0, proposals_without_source: 0 }
  - id: AC-004-b
    req: REQ-004
    kind: mechanical
    ears_type: unwanted
    observe: cli:check-audit
    given: { input: "audit.yaml with one proposal lacking a source assessment or gap id" }
    expect: { exit: 1, error: "proposal_without_source" }
    paired_with: AC-004-a
  - id: AC-005-a
    req: REQ-005
    kind: human
    observe: ui:AUDIT.md#ring-tables
    statement: 每个 Part 行给出 Gap 原子集合、独占 Artifact（或 role）、检它的 Gate（闸 / 门分清）与 Loop；needed 的 deletion 测试写出撤掉后流水线会产出的具体错误产物或漏检；naming 先写来路再写贴合，misfit 给更贴产物或位置的建议名并标"不重命名"；疑似重复的 Part 对带 Artifact 对照与 distinct_exits / merge_candidate / alternatives_of 裁决；每环 missing 行带来源标签、necessity 与 deletion 一句
    judge: tech
    evidence: checklist
  - id: AC-006-a
    req: REQ-006
    kind: human
    observe: ui:AUDIT.md#run-evidence
    statement: run_evidence 节列出 G1 / G2 / G3 的签字人、signer_kind 与授权引用（代签不渲染为人签）；列出 check-audit 对 audit.yaml exit 0 与删环变体 exit 1 的两次运行记录（缺则标 uncalibrated）；列出 Card 提交对三个被审目录的 git diff --stat（为空）与 skill-issues.md 路径；外部证据替代品标 substitute
    judge: product
    evidence: checklist
  - id: AC-007-a
    req: REQ-007
    kind: mechanical
    ears_type: event
    observe: cli:verify-commit
    given: { input: "each commit carrying a Card footer on the feature branch, replayed with --range and its --card" }
    expect: { exit: 0, card_commits_touching_audited_dirs: 0 }
  - id: AC-007-b
    req: REQ-007
    kind: mechanical
    ears_type: unwanted
    observe: cli:verify-commit
    given: { input: "a Card commit whose diff modifies a file under the audited skills directory" }
    expect: { exit: 1, error: "whitelist_overflow" }
    paired_with: AC-007-a
  - id: AC-008-a
    req: REQ-008
    kind: mechanical
    ears_type: event
    observe: cli:check-audit
    given: { input: "complete audit.yaml", rings: "R0,R1,R2,spine", required_parts: "psl, psl-derive, human_gate.G1, dos-extract, invariant-extract, issue, donewhen-extract, acceptance-spec, human_gate.G2, sdlc, asset.graph.yaml, asset.loops.yaml, asset.routing.yaml, asset.triggers.yaml" }
    expect: { exit: 0, parts_without_assessment: 0, required_parts_missing: 0 }
  - id: AC-008-b
    req: REQ-008
    kind: mechanical
    ears_type: unwanted
    observe: cli:check-audit
    given: { input: "audit.yaml with one required part of rings R0,R1,R2,spine removed", rings: "R0,R1,R2,spine" }
    expect: { exit: 1, error: "required_part_missing" }
    paired_with: AC-008-a
  - id: AC-009-a
    req: REQ-009
    kind: mechanical
    ears_type: event
    observe: cli:check-audit
    given: { input: "complete audit.yaml", rings: "R3,R4,R5", required_parts: "test-suite-generator, spec-compile, calibrate, plan-cards, implement, commit, ratchet" }
    expect: { exit: 0, parts_without_assessment: 0, required_parts_missing: 0 }
  - id: AC-009-b
    req: REQ-009
    kind: mechanical
    ears_type: unwanted
    observe: cli:check-audit
    given: { input: "audit.yaml with one required part of rings R3,R4,R5 removed", rings: "R3,R4,R5" }
    expect: { exit: 1, error: "required_part_missing" }
    paired_with: AC-009-a
  - id: AC-010-a
    req: REQ-010
    kind: mechanical
    ears_type: event
    observe: cli:check-audit
    given: { input: "complete audit.yaml", rings: "R6", required_parts: "acceptance-fleet, code-reviewer, qa-reviewer, pm-reviewer, spec-drift-detector, spec-gaming-detector, meta-judge, pr-review, human_gate.G3" }
    expect: { exit: 0, parts_without_assessment: 0, required_parts_missing: 0 }
  - id: AC-010-b
    req: REQ-010
    kind: mechanical
    ears_type: unwanted
    observe: cli:check-audit
    given: { input: "audit.yaml with one required part of ring R6 removed", rings: "R6" }
    expect: { exit: 1, error: "required_part_missing" }
    paired_with: AC-010-a
  - id: AC-011-a
    req: REQ-011
    kind: mechanical
    ears_type: event
    observe: cli:check-audit
    given: { input: "complete audit.yaml", rings: "R7,R8", required_parts: "pr, review-loop, release, retro, tune, human_gate.merge, human_gate.harness-review" }
    expect: { exit: 0, parts_without_assessment: 0, required_parts_missing: 0 }
  - id: AC-011-b
    req: REQ-011
    kind: mechanical
    ears_type: unwanted
    observe: cli:check-audit
    given: { input: "audit.yaml with one required part of rings R7,R8 removed", rings: "R7,R8" }
    expect: { exit: 1, error: "required_part_missing" }
    paired_with: AC-011-a
thresholds:
  rings: "== 10"
  dims_with_psl_id_ratio: ">= 1.0"
  card_commits_touching_audited_dirs: "== 0"
  parts_total: "== 42"
  required_parts_by_ring_group: "R0-R2+spine: 14; R3-R5: 7; R6: 9; R7-R8: 7（含两个 human_gate）— 名单见 AC-008..011-a given；5 个 agent 不分组挂 AC-001-a"
threshold_source: "PSL γ 约束 + Acceptance A6 / A7 / A8 + 用户原话（四问全覆盖）；required_parts 来源 ARCHITECTURE §1 表 skill 列 + 门列人签门 + 脊柱四资产 + agents/*.md（2026-09-05 快照）"
existence:
  - cli: check-audit
  - cli: verify-commit
  - ui: AUDIT.md#ring-tables
  - ui: AUDIT.md#run-evidence
```

## Assumptions

| id | assumption | bound_to | risk | verify_at | signed_by |
|---|---|---|---|---|---|
| A-1 | "必要"= deletion 测试在生命周期高度上读；流水线闭合所需是 deletion 失败的一种证据，不是第二标准；两者读完仍冲突的残余写 contested 交 G3 | REQ-005 | medium | AC-005-a / G3 | g1-judge (delegated, round 1 Open Q1) |
| A-2 | 命名建议只登记不落地（rename 恒 false）；贴合对每个 skill 都诚实判，收编不是免检——来路只决定 misfit 的去向理由 | REQ-005 | low | AC-005-a | g1-judge (delegated, round 1 P-1) |
| A-3 | 代签 agent 的签字在用户"子 agent 代替我审核"的授权下有效，且在报告里标为 delegated | REQ-006 | medium | AC-006-a / G3 | g1-judge (delegated) |
| A-4 | 外部证据（原型走查 / 用户验证）由检查脚本的自校准（删环变体 exit 1）替代 | REQ-001 | medium | AC-001-b | g1-judge (delegated) |

## Depends on DOS

- objects: [Node, Gate, Loop, Run, Event]
- invariants: [R008, R017]

## Links

- PSL: plugins/sdlc/dogfood/ring-audit/PSL-sdlc-ring-audit.md　G1: plugins/sdlc/dogfood/ring-audit/g1-record.md　related: none
