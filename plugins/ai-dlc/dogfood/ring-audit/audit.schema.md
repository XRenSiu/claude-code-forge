# audit.yaml schema

`audit.yaml` 是九环审计的机器可读半边，`AUDIT.md` 是它的投影（F-12：两者同目录，不一致时以 yaml 为准）。
这份 schema 是内容卡（CARD-02…CARD-06）填 `audit.yaml` 时照抄的形状，也是 `check_audit.py` 实际执行的那一份——
**改这份文档不会改判定**，判定在 `check_audit.py` 里；这份文档的责任是让内容卡不必读源码就写对。

来源：`derived/form-draft.md` F-12 / F-13 / F-14 / F-17（G1 签字版 `746c56ef…`），按 `g1-record.md`
**签字版解释规则 1-3**（2026-09-05）读。规则 1-3 定死了三处 F-12 留白：产物的双生产者怎么算合法、
Gap 的边怎么物化、签字三元组住在哪。

> 与 CARD-01 卡面 `notes` 的差异（卡面早于 G1 解释规则写成，以本文件为准）：
> 签字三元组**不在** `gates[]`，`gates[].exercised` / `not_exercised` 这两个键**不存在**；
> `merge_candidate` 标在 `assessment.needed.verdict` 上，不是标在 Assessment 顶层；
> `rings[].missing[]` 是 **gap id 字符串**，不是 Gap 记录。

## 检查脚本

```
python3 check_audit.py <audit.yaml> [--psl PSL-<feature>.md] [--rings R0,R1,..]
                       [--required-parts a,b,..] [--variant delete-ring:<id>]
```

exit 0 = 全部谓词成立 · exit 1 = 至少一条失败（谓词名与定位在 stdout JSON 的 `error` / `errors` /
`failed_predicates`）· exit 2 = 输入读不了（文件不存在、YAML 解析失败、缺 pyyaml）。stdout 恒为一个 JSON 对象。

`--rings` 只限定**视图**：哪些环必须在场、`parts_without_assessment` 数哪些 Part、`--required-parts`
去哪里找。它不收窄其它任何谓词（F-17：不改任何既有谓词）——维度、Gap、Artifact、Gate、Proposal
谓词永远读整份文档。

`--variant delete-ring:<id>` 在内存里删掉一个环再检，必须 exit 1。F-14：**对报告的 exit 0 只有在同一次运行里
配上删环变体的 exit 1 才算证据**，两条运行都要写进 `run_evidence.check_runs`；没有变体记录的 exit 0 标
`uncalibrated`，不当证据。

## 顶层

六个加法式注册表，缺一不可（rule 2a）：

```yaml
schema: audit/1
feature: sdlc-ring-audit
psl: PSL-sdlc-ring-audit.md      # 相对本文件；psl_ids 的闭集来自它的「规律索引」节
check: check_audit.py
rings: []                        # 环 → Part → Assessment
gaps: []                         # Gap 注册表（唯一真源）
artifacts: []                    # 一条 = 一个 (产物, 生产者) 对
gates: []                        # 设计视图：门与闸各是什么
proposals: []                    # 从 Assessment / Gap 长出来的提案
run_evidence: {}                 # 本次运行的行为层证据
```

## Ring

```yaml
- id: R0                         # 必须是 R0…R8 / spine 之一，十个一个不少（ring_missing / ring_unexpected）
  question: 这个产品的世界是什么样的、它的规律是什么？   # ARCHITECTURE §1 表「问题」列
  parts: []
  missing: []                    # gap id 列表。空列表是答案，**没有这个键**是沉默（rings_without_missing_key）
```

`missing[]` 里每个 id 必须在 `gaps[]` 里存在且 `ring` 相同（`unknown_gap_ref`）。

## Part

配件不是文件，是缺口的填充物（PSL-002）。`kind` ∈ `skill | agent | human_gate | asset`。

```yaml
  - id: psl                      # 与 --required-parts 逐字匹配的名字
    kind: skill
    ring: R0
    ring_evidence: graph.yaml#L12    # 凭什么说它在这个环上；无节点写 no_node
    provenance: authored             # authored 新写 | adopted 收编（PSL-014）
    loop: null                       # 属于某个圈时写 loops.yaml#<name>
    artifact: PSL-<feature>.md       # 独占生产的产物；无产物写 null
    role: gate                       # 可选：gate / orchestrator
    gates: [verify_psl.py]           # 检它的闸与门的 id
    fills: [R0/newly_identified/knowledge/world-before-form]   # FILLS 边 = gap id 列表
    assessment: {}
```

`fills[]` 每个 id 同样要在 `gaps[]` 里、同环（`unknown_gap_ref`）。
`fills: []`（填零缺口）**必须**把 `assessment.needed.verdict` 写成 `overfill`，否则 `overfill_unmarked`
——填零缺口 = 过填，PSL-002 不许悄悄放过。

## Assessment

每个 Part 三维齐（`parts_missing`）。三维各自带 `psl_ids`（非空、且都在 PSL 规律索引内）与 `evidence`（非空）。

```yaml
    assessment:
      id: A-psl
      state: evidenced
      needed:                        # 这个配件该不该在
        verdict: necessary           # necessary | overfill | merge_candidate
        psl_ids: [PSL-002, PSL-016]  # 非空（psl_id_missing），逐条在索引内（psl_id_unknown）
        evidence: [{kind: file, ref: plugins/sdlc/skills/psl/SKILL.md}]
        deletion_test: 撤掉后引擎从一句需求直接推形态，世界层错误延迟到 R6 才暴露
      implemented:                   # 做到哪一步了
        verdict: compiled            # declared | compiled | verified —— 禁止布尔（boolean_implemented）
        psl_ids: [PSL-010, PSL-015]
        evidence:
        - {kind: file, ref: plugins/sdlc/skills/psl/SKILL.md}
        - {kind: gate_json, ref: plugins/sdlc/skills/psl/gate.json#static_only}
        not_reached: {verified: 无行为层运行记录}   # 没到的那一态，诚实写为什么（DP-1）
        calibrated: false            # 可选：这把尺子本身校准了没有（PSL-007）
      naming:                        # 名字贴不贴合
        verdict: fits                # fits | misfit
        provenance: authored
        artifact_or_position: PSL-<feature>.md
        fit: fits
        rename: false                # 恒为 false —— 建议不等于重命名（rename_true / PSL-014 / DP-3）
        psl_ids: [PSL-014]
        evidence: [{kind: file, ref: plugins/sdlc/skills/psl/SKILL.md}]
        suggested_name: harness-tune         # 可选，misfit 时给
        rename_reason: 不重命名：另开 G2 变更提案
      disposition: none              # none | issue —— 要不要长出一条 proposal
      adjudications: []              # 争议裁决记录；无争议留空
```

`implemented.verdict` 三态（PSL-010）：`declared` 只有 SKILL.md · `compiled` 有 verify 脚本或被门挡 ·
`verified` 有行为层运行记录。**报告里禁止写「已实现 ✓」**，那是布尔，检查脚本会 exit 1。
一个 `checked_by: []` 的产物，它的生产者停在 `declared`（F-06）。

`needed.verdict: merge_candidate` 另带一个 `merge_candidate_with: <另一个 Part id>`，见下面 Artifact。

### Evidence

三维的 `evidence[]` 与 Gap 的 `evidence[]` 同一个形状。

```yaml
        - {kind: file, ref: plugins/sdlc/skills/psl/SKILL.md}
```

`kind` ∈ `file | gate_json | smoke | run_record`（`evidence_kind_outside_enum`），
`ref` 非空（`evidence_ref_empty`）。

## Gap

缺口四原子 Knowledge / Capability / Judgment / Control（PSL-016）。id 是确定式的，由字段拼出来，
不另起编号：`<ring>/<source>/<atoms 小写 + 号连接>/<slug>`。

```yaml
- id: R1/lifecycle_blank/control/dos-drift-check
  ring: R1
  atoms: [Control]
  source: lifecycle_blank        # newly_identified | lifecycle_blank | unenforced_rule（PSL-017 三种来源）
  necessity: necessary
  deletion_test: 无 DOS 对账 / drift 检查：本体与代码分叉不被发现
  evidence: [{kind: file, ref: docs/lifecycle.md#制品映射表}]
  disposition: issue             # none | issue
```

**没有任何 Part 的 `fills[]` 指向它的 Gap，必须出现在它那个环的 `missing[]` 里**，否则 `orphan_gap`
——空白诚实登记，不装作已有（PSL-017）。

## Artifact

一条记录 = 一个 (产物, 生产者) 对。一个产物只有一个生产者（PSL-001）。

```yaml
- id: PSL-<feature>.md
  producer: psl                  # Part 的 id
  checked_by: [verify_psl.py]    # 检它的闸 / 门；空列表意味着生产者停在 declared（F-06）
```

同一个 `id` 有 ≥2 条记录时，合法只有两条路（rule 1），否则 `double_producer`：

```yaml
# 一、同阶段的条件替代分支 —— 不算争（PSL-001）
- {id: card diff + commits, producer: implement, checked_by: [verify_commit.py]}
- {id: card diff + commits, producer: agent.card-implementer, checked_by: [verify_commit.py], alternatives_of: stage.implement}
- {id: card diff + commits, producer: ratchet, checked_by: [verify_commit.py], alternatives_of: stage.implement}

# 二、真的在争，但两边都认领为合并候选 —— 每个生产者的 needed.verdict 都是 merge_candidate
- {id: done_when.yaml, producer: donewhen-extract, checked_by: [verify_donewhen.py, G2]}
- {id: done_when.yaml, producer: acceptance-spec, checked_by: [G2]}
```

反向也检：`needed.verdict: merge_candidate` 只能标在**真的有未豁免双生产者**的 Part 上，
标在单生产者身上是 `spurious_merge_candidate`。这是同一条规则的两张脸——不许拿 merge_candidate
当免检牌。

## Gate

设计视图：门谁签、闸谁跑。人门只有 G1 / G2 / G3 三道（rule 3d、F-06）——
`merge` 与 `harness-review` 是 `kind: human_gate` 的 **Part**，把它们写进 `gates[]` 是 `gate_not_declared`。

```yaml
- {id: G1, kind: human, label: 门, checks: [derived/form-draft.md]}
- {id: verify_psl.py, kind: script, label: 闸, ref: plugins/sdlc/skills/psl/scripts/verify_psl.py}
```

`kind: script` 的 `label` 写成 `门` 是 `script_gate_rendered_as_door`：闸不是门，代签不得渲染为人签（PSL-006）。

## Proposal

```yaml
- {id: P-01, source: A-tune, destination: new_issue, text: 'naming misfit: tune → suggested_name harness-tune；不重命名，另开 G2 变更提案'}
```

`source` 必须指向一个 Assessment id 或 Gap id（`proposal_without_source`）——补的理由只能是一个已识别的
Gap，不能因为「这环显得单薄」就提（DP-2）。`destination` ∈ `new_issue | skill_fix_list | no_action`。

**已知空隙（2026-09-06，failure-report-002）**：check_audit.py 08238cd 只检 `source` 非空，**不**解析该 id 是否存在（holdout hv_proposal_dangling_source 未命中）；解析谓词随 change-proposal-002 加入。写 audit.yaml 时仍应让 source 可解析——这是规格要求，只是本轮无机械闸。

## run_evidence

行为层证据 + F-07 签字三元组。**签字三元组住在这里，不在 `gates[]`**（rule 3b）。

```yaml
run_evidence:
  run: {slug: sdlc-ring-audit, state: .sdlc/sdlc-ring-audit/state.json, ledger: .sdlc/sdlc-ring-audit/ledger.md}
  gates:
  - {gate: G1, verdict: pass, signer: g1-judge, signer_kind: delegated_agent, authorization_ref: 'g1-record.md#authorization'}
  - {gate: G3, verdict: pending, signer: null, signer_kind: null, authorization_ref: null}
  external_evidence: {kind: substitute, what: check-audit 机械检查 + 代签 agent 独立读, valid_for: this dogfood only}
  check_runs:
  - {cmd: python3 check_audit.py audit.yaml --psl PSL-sdlc-ring-audit.md, exit: 0}
  - {cmd: 'python3 check_audit.py audit.yaml --psl PSL-sdlc-ring-audit.md --variant delete-ring:R6', exit: 1}
  calibrated: true
  skill_issues: plugins/sdlc/dogfood/ring-audit/skill-issues.md
  audited_dirs_diff: git diff --stat (Card commits only) plugins/sdlc/skills plugins/sdlc/agents plugins/sdlc/docs → empty
```

`verdict` ∈ `pending | pass | reject | waived`（`gate_verdict_outside_enum`）。
`pending` 允许三个 null；**`pending` 之外的任何 verdict** 都必须有 `signer` 与 `signer_kind`
（`human_gate_without_signer`）；`signer_kind: delegated_agent` 必须附 `authorization_ref`
（`delegated_without_authorization_ref`）——代签须有授权记录（PSL-006）。

`check_runs` 里那对「正常跑 exit 0 + 删环变体 exit 1」就是 F-14 要的校准孪生；
`check_audit.py` 把它读成输出里的 `calibration_twin_recorded`，**只报告不设闸**——
是不是拿它当证据，是 G3 的人要看的东西。

## 谓词 → 计数字段

`check_audit.py` 的 stdout JSON 顶层带这些计数（判定用谓词名，人读用计数）：

| 谓词 token | 计数字段 |
|---|---|
| `ring_missing` / `ring_unexpected` | `rings` |
| `parts_missing` | `parts_without_assessment`（受 `--rings` 限定）、`parts_total`（全部环） |
| `psl_id_missing` | `dims_without_psl_id` |
| `psl_id_unknown` | `dims_with_unknown_psl_id` |
| `evidence_missing` | `dims_without_evidence` |
| `evidence_kind_outside_enum` / `evidence_ref_empty` | 同名计数 |
| `boolean_implemented` / `implemented_outside_enum` / `rename_true` | 同名计数 |
| `rings_without_missing_key` | 同名计数 |
| `unknown_gap_ref` | `unknown_gap_refs` |
| `orphan_gap` | `orphan_gaps` |
| `overfill_unmarked` | 同名计数 |
| `double_producer` / `spurious_merge_candidate` | 同名计数 |
| `gate_not_declared` | `gates_not_declared` |
| `script_gate_rendered_as_door` | `script_gates_rendered_as_door` |
| `gate_verdict_outside_enum` | 同名计数 |
| `human_gate_without_signer` | `human_gates_without_signer` |
| `delegated_without_authorization_ref` | 同名计数 |
| `proposal_without_source` | `proposals_without_source` |
| `required_part_missing` | `required_parts_missing` |

另有 `calibration_twin_recorded`（F-14，报告用）与 `psl_index_size`（读到几条规律，0 意味着 `--psl` 没给，
这一轮不检 `psl_id_unknown`）。

## 审计者不改被审对象

`replay_card_commits.sh` 是 REQ-007 的机械检查：分支上每个带 `Card: CARD-xx` footer 的提交，
按它自己那张卡的白名单回放一遍 `verify_commit.py --range <sha>^..<sha> --card cards/CARD-xx.yaml`。
任一回放被拒、或任一 Card 提交碰了 `plugins/sdlc/skills|agents|docs` → exit 1 + `whitelist_overflow`。
输出 JSON 的 `card_commits_touching_audited_dirs` 就是 `run_evidence.audited_dirs_diff` 该引的那个数
（PSL-003：审计者不改被审对象，且这件事由脚本证明，不由记忆保证）。
