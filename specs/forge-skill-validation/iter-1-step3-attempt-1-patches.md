# Step 3 Fixer Patches — iter-1-step3-attempt-1

**Issues source:** `iter-1-step3-attempt-1-issues.md`
**Authoritative schema:** `done-when-pipeline.md` Appendix C (schema v1).
**Scope:** only `acceptance-spec` and `test-suite-generator` skill source code modified.

---

## 处理的 P0 issues

- **P0-1** `fitness[].judge: llm-rubric` 不在 schema 枚举集合内。Skill 内部 `references/done-when-schema.yaml` 与设计文档附录 C 的 `persona-judge | programmatic | manual` 不一致，是根因。
- **P0-2** `existence[]` / `behavior` leaf 项被升格为带子字段的 mapping（`based_on:` / `property_type:` / `dependencies:` / `tool:` / `name:`），schema v1 字面只允许单键值对（existence）或 bare 字符串（behavior leaf）。

---

## 选用方案

**方案 A（严格收敛到 v1 字面 schema）** — 按任务指令选择。

- `existence[]` 回退为单键值对，5 种 kind（file / function / route / db_field / frontend_component），无任何子字段。
- `behavior.*` 各 test 列表回退为 bare 字符串（test name），无 mapping 形式。
- `fitness[].judge` 统一为附录 C 三选一：`persona-judge | programmatic | manual`。LLM-as-judge 入口的 contract token 是 `persona-judge`。
- `fitness[]` 移除 `rubric_file:`（rubric 文件是 test-suite-generator 4-F 的产物，不是契约字段）。
- `spec_drift_threshold` 仅保留 `max_fix_loops_before_escalation:`，移除 `applies_to:`。
- 现有 traceability 由 **顶层 `based_on:` 联合集 + spec.md 的 `source:` 行 + 测试名语义**承担。Leaf-row 级别的 `based_on:` 在 v1 不允许，这是 v1 的代价。
- PBT property type 由测试名后缀（`_invariant` / `_idempotent` / `_reversible` / `_boundary` / `_monotonic` / `_state_machine`）编码，downstream（test-suite-generator 4-B）按名字路由。

**为什么也要改 test-suite-generator？**
原 4-F 的逻辑是：用 `llm-rubric` 触发 rubric 生成、用 `persona-judge` 触发 reject。把 contract 枚举翻转后，必须同步翻转 4-F 的分支映射，否则下游会把合法 v1 contract 当作 malformed 拒掉。validator 也需要按 v1 严格集校验，并把"有 leaf 子字段"判为 malformed。

---

## 修改的文件清单

| 文件 | 修改类型 | 简述 |
|---|---|---|
| `plugins/done-when-pipeline/skills/acceptance-spec/references/done-when-schema.yaml` | 重写 | 完全按 Appendix C v1 字面格式描述 schema；existence 5 kind no-sub-field；behavior leaf bare string；fitness judge 三选一去掉 llm-rubric；移除 applies_to / rubric_file。 |
| `plugins/done-when-pipeline/skills/acceptance-spec/references/output-templates/done-when-template.yaml` | 重写 | 模板骨架严格 v1；明确 v1 hard rules 在文件顶部注释列出。 |
| `plugins/done-when-pipeline/skills/acceptance-spec/references/examples/subscription-cancellation/done_when.yaml` | 重写 | 把 worked example 改成 v1 字面格式，作为 worker 模仿目标。 |
| `plugins/done-when-pipeline/skills/acceptance-spec/SKILL.md` | 局部修改（S3 §4） | 替换 done_when.yaml 写作指引：硬规则六条 + 严格 v1 提醒，明确不写 rubric_file / applies_to / leaf-row based_on / property_type / tool / dependencies。 |
| `plugins/done-when-pipeline/skills/test-suite-generator/SKILL.md` | 局部修改（iron rule 3 + 4-A + 4-B + 4-C + 4-D + 4-F） | iron rule 3 改为"从测试名后缀推 PBT 类型"；4-A 去掉 env_var/cli_command；4-B/4-C/4-D 不再读 leaf 子字段（property_type/dependencies/tool），改为从名字/项目惯例推断；4-F 反转 enum 分支：`persona-judge` 触发 rubric 生成，`llm-rubric` 触发 reject。 |
| `plugins/done-when-pipeline/skills/test-suite-generator/references/done-when-schema-validator.md` | 重写 | 按 v1 严格校验：existence 5 kind no-sub-field；behavior leaf bare string；fitness judge ∈ {persona-judge, programmatic, manual}；rubric_file/applies_to/env_var/cli_command 全部记为 malformed。 |
| `plugins/done-when-pipeline/skills/test-suite-generator/references/sub-modules/fitness-rubric.md` | 局部修改 | "Goal" 段、4-F enum 分支段、rubric 模板的 `**Judge:**` 行、push-back 列表 — 全部从 `llm-rubric` 改为 `persona-judge`；新增"persona-judge semantics 说明段"诚实标注当前 runner 仍是 manual。 |
| `plugins/done-when-pipeline/skills/test-suite-generator/references/sub-modules/existence-extractor.md` | 局部修改 | 表格只列 v1 五种 kind；env_var/cli_command 标为非 v1 应在 validator 阶段被拒。 |
| `plugins/done-when-pipeline/skills/test-suite-generator/references/fitness-rubric-guide.md` | 局部修改 | "Honest scope note" 改为：`persona-judge` 是 v1 contract token；现有 `persona-judge` skill 当前 scope 仍限 distilled-persona，rubric 文件仍走 manual workflow。模板 `**Judge:**` 行同步更新。 |
| `plugins/done-when-pipeline/skills/test-suite-generator/references/tooling-by-language.md` | 局部修改 | Python `LLM-judge` 行与 TS `LLM-judge` 行的注释从 `llm-rubric` 改为 `persona-judge`。 |
| `plugins/done-when-pipeline/skills/test-suite-generator/references/examples/README.md` | 局部修改 | 例子文件树注释 `4-F llm-rubric (manual run)` → `4-F persona-judge (manual run, v1)`。 |

---

## 详细修改

### 文件 1: `acceptance-spec/references/done-when-schema.yaml`

**修改类型:** 完全重写。

**修改前关键片段:**
```yaml
existence:
  - file: <path>
    based_on: [REQ-001]              # ← v1 不允许
  ...

behavior:
  unit_tests:
    example_based:
      - name: test_<what>             # ← v1 是 bare string
        based_on: [REQ-001]
    property_based:
      - name: test_<verb>_is_<property>
        property_type: idempotent     # ← v1 不允许
        based_on: [REQ-001]

fitness:
  - criterion: ...
    judge: llm-rubric                 # ← 不在 v1 enum
    rubric_file: ...                  # ← v1 不允许
    score_threshold: ">= 8/10"

spec_drift_threshold:
  max_fix_loops_before_escalation: 3
  applies_to:                         # ← v1 不允许
    - mutation_kill_rate
    - property_based_failure
```

**修改后关键片段:**
```yaml
existence:
  - file: src/billing/cancel_subscription_use_case.ts
  - function: CancelSubscriptionUseCase
  - route: POST /api/subscription/cancel
  - db_field: subscription.status
  - frontend_component: CancelSubscriptionButton

behavior:
  unit_tests:
    example_based:
      - test_cancel_active_sets_status_to_cancelled_active
    property_based:
      - test_cancel_is_idempotent

fitness:
  - criterion: ...
    judge: persona-judge
    score_threshold: ">= 8/10"
  - criterion: ...
    judge: programmatic

spec_drift_threshold:
  max_fix_loops_before_escalation: 3
```

**理由:** 文件是 worker 阅读的 schema 真理源。任何字面偏离都会被 worker 复制到产出。完全锚定 Appendix C lines 988-1034 的字面 schema。

---

### 文件 2: `acceptance-spec/references/output-templates/done-when-template.yaml`

**修改类型:** 完全重写。

**修改前:** template 是带 `based_on:` 子字段的 mapping 形式，`judge: llm-rubric`，含 `rubric_file:` 与 `applies_to:`。

**修改后:** template 是 v1 字面骨架，文件顶部注释明确"v1 STRICT RULES"五条。

**理由:** worker 在 S3 段直接拿这个 template 作填空起点。template 长什么样，产出就长什么样。

---

### 文件 3: `acceptance-spec/references/examples/subscription-cancellation/done_when.yaml`

**修改类型:** 完全重写。

**修改前:** existence 每条带 `based_on:`，behavior leaf 是 mapping 带 `name:`/`based_on:`/`property_type:`/`dependencies:`/`tool:`，fitness `judge: llm-rubric` + `rubric_file:`，spec_drift_threshold 带 `applies_to:`。

**修改后:** 完全符合 v1 字面：existence 5 种 kind 全用单键值对；behavior leaf 全是 bare string，PBT 类型编进名字（如 `_is_idempotent`, `_invariant`, `_state_machine`）；fitness judge 用 persona-judge / programmatic；spec_drift_threshold 仅留 max_fix_loops_before_escalation。

**理由:** 这是 worked example，worker 跑 Step 3 时会照样模仿。example 不严格，下游就不严格。

---

### 文件 4: `acceptance-spec/SKILL.md`（S3 §4 `done_when.yaml` 段）

**修改前关键片段:**
> Three top-level blocks: `existence:` / `behavior:` / `fitness:`. Add a `spec_drift_threshold:` block with `max_fix_loops_before_escalation: 3` and `applies_to: [...]`.

**修改后关键片段:**
> Hard rules for v1 字面:
> - `existence:` — 单键值对，5 种 kind 之一，无子字段。
> - `behavior.*` — 每个 test entry 是 bare string，不是 mapping。无 `name:` / `based_on:` / `property_type:` / `dependencies:` / `tool:`。把 property 类型编进名字。
> - `fitness:` — exactly 三键 `criterion:` / `judge:` / `score_threshold:`。judge ∈ {`persona-judge`, `programmatic`, `manual`}。不用 `llm-rubric`。不加 `rubric_file:`。
> - `spec_drift_threshold:` — exactly 一个子键 `max_fix_loops_before_escalation:`。不加 `applies_to:`。
> - 顶层 `based_on:` — 所有 REQ 的 union，是 v1 下的主 traceability 锚。

**理由:** SKILL.md 是 worker 跑 S3 时第一份必读 spec。把 hard rules 直接列在 S3 §4 入口，避免 worker 默默偏离 schema。同时新增一段"为什么这么严"解释，让 worker 即使想"加 traceability"也理解为什么不能加。

---

### 文件 5: `test-suite-generator/SKILL.md`（多处修改）

#### 5a. iron rule 3 — PBT 类型识别

**修改前:**
> **PBT must declare its property type.** Every property-based test in `done_when.yaml` has a `property_type:` field ...

**修改后:**
> **PBT property type is recovered from the test name.** Under schema v1 ... every leaf entry is a bare string — there is no `property_type:` sub-field on the entry. Parse the test name suffix to infer the property archetype ...

**理由:** v1 leaf 没有 `property_type:` 字段，必须改为从名字推断。

#### 5b. 4-A existence 类型表

**修改前:** 7 种 kind（含 env_var / cli_command）。

**修改后:** 仅列 v1 五种，并加一段"看到 env_var/cli_command 立刻 bail 让用户重生 contract"。

#### 5c. 4-B / 4-C / 4-D — 不再读 leaf 子字段

**修改前 4-B:** `If under property_based: → look at property_type: and emit the matching pattern...`

**修改后 4-B:** `infer property_type from the test name suffix ... and emit the matching pattern`. 同时新增一句：v1 下没有 per-leaf based_on，REQ 链通过测试名 + spec.md `source:` 行复原。

**修改前 4-C:** `Use testcontainers for any dependencies: listed.`

**修改后 4-C:** v1 下无 `dependencies:` 字段，从测试名 + spec.md 推断容器需求。

**修改前 4-D:** `Use the tool the entry specifies (tool: playwright / ...).`

**修改后 4-D:** v1 下无 `tool:` 字段，从项目惯例（`playwright.config.*` 等）推断；缺省 web→Playwright，mobile→Maestro。

**理由:** 与 v1 字面 schema 自洽。

#### 5d. 4-F — enum 分支翻转

**修改前:**
> If `judge: llm-rubric` → emit rubric file ...
> If `judge: persona-judge` → reject the entry ...

**修改后:**
> If `judge: persona-judge` → emit `fitness/<criterion>.rubric.md` ...
> If `judge: llm-rubric` → reject the entry (legacy value, not in v1 enum) ...

**理由:** P0-1 的下游对偶。Contract 枚举翻转后，4-F 的分支映射必须同步翻转，否则会把合法 v1 contract 当 malformed 拒掉。

---

### 文件 6: `test-suite-generator/references/done-when-schema-validator.md`

**修改类型:** 完全重写。

**修改前要点:**
- existence 接受 7 种 kind
- behavior leaf 必须有 `name:` / `based_on:` / `property_type:` 等子字段
- fitness judge ∈ {programmatic, llm-rubric, manual}; persona-judge 视为 malformed
- spec_drift_threshold 没规定不许有 applies_to

**修改后要点:**
- existence 仅五种 kind，必须无任何子字段
- behavior 各 leaf 必须是 bare string，是 mapping 就 malformed
- fitness judge ∈ {persona-judge, programmatic, manual}; llm-rubric 视为 malformed
- fitness 不许 `rubric_file:`; spec_drift_threshold 不许 `applies_to:`
- PBT 测试名应当包含可识别 archetype token（warning 级，不是 hard fail）

**理由:** validator 是 test-suite-generator 入口的第一道关。它放行的就是 worker 下次产出的真理。

---

### 文件 7: `test-suite-generator/references/sub-modules/fitness-rubric.md`

**修改类型:** 局部修改。

主要替换 `llm-rubric` → `persona-judge`：
- "Goal" 段：rubric 文件触发条件改成 `judge: persona-judge`。
- §"`judge: llm-rubric`" 段标题改为 §"`judge: persona-judge`"；段内 contract token 同步更新。
- Rubric 模板的 `**Judge:**` 行从 `llm-rubric` 改为 `persona-judge`。
- §"When to push back" 列表：`judge: llm-rubric` 现在是被拒方向；`judge: persona-judge` 不再被拒。
- 新增一段 §"Note on `persona-judge` semantics"：诚实说明现存 `persona-judge` skill 的 scope 不覆盖任意 artifact，所以现在 runner 仍是 manual fresh-Claude-session 工作流——但 contract token 按 v1 仍是 `persona-judge`。

**理由:** 这段文档解释了 4-F 的"为什么"，必须与翻转后的 enum 一致。

---

### 文件 8: `test-suite-generator/references/sub-modules/existence-extractor.md`

表格头新增一句"v1 五种 kind"；env_var / cli_command 两行删除；新增一段"如果看到 env_var/cli_command 则 bail，是非 v1 contract"。

---

### 文件 9: `test-suite-generator/references/fitness-rubric-guide.md`

§"Honest scope note" 重写：明确 v1 contract token 是 `persona-judge`；诚实说明现存 `persona-judge` skill 当前 scope 仅限 distilled-persona，rubric 文件仍走 manual。模板 `**Judge:**` 行同步更新为 `persona-judge`。

---

### 文件 10: `test-suite-generator/references/tooling-by-language.md`

两行注释 `automate judge: llm-rubric scoring` 与 `llm-rubric rubric files` 改为 `persona-judge` 对应描述。

---

### 文件 11: `test-suite-generator/references/examples/README.md`

例子文件树注释 `# 4-F llm-rubric (manual run)` 改为 `# 4-F persona-judge (manual run, v1)`，两处同改。

---

## 不修的 issues（P1/P2 跳过）

按任务铁律"不修 P1/P2 issues"。下列保留给后续 iter 或 spec 演进：

| 编号 | 简述 | 跳过理由 |
|---|---|---|
| P1-1 | tasks.md 与 REQ 覆盖不平衡（REQ-003/004/007 单薄） | 这是 worker 的拆分质量问题，不是 skill 源码 bug。skill 的 tasks.md 模板已经要求"可执行"+"标 implements: REQ-xxx"，worker 没做到是 worker 的差异。可在后续 iter 增强 SKILL.md 的 tasks.md 段落做"每个 REQ 至少 1 个 task"硬要求，但本次不修。 |
| P1-2 | `existence.function:` 被用来装类名/Surface 模块 | v1 schema 颗粒度局限。Appendix C 的 `function:` 字面是 "函数必须 export"，但 worked example 自己也这么用。这是 spec v1 的颗粒度问题，需要附录 C v2 增加 `class:` / `module:` kind 才能根治。skill 不能擅自扩展枚举。 |
| P1-3 | 缺 `route:` 条目而 tasks.md 有 4 个 API endpoint hook | worker 的 contract 覆盖完整度问题。SKILL.md 可以增加"如果 tasks.md 有 API 任务，existence 必须有对应 route 条目"的 hint，但 v1 schema 没硬性规定，不算 skill 源码 bug。 |
| P1-4 | 缺 `frontend_component:` 条目但 e2e 显然涉及前端 | 同上 P1-3。是 worker 的覆盖完整度问题。 |
| P1-5 | `spec_drift_threshold.applies_to:` 越界 | 本次修了。schema/template/example/SKILL.md 都已明确禁止 `applies_to:`。注意：issue 文件登记为 P1，但本次修 P0-2 时已顺带覆盖（删除该字段属于"严格收敛到 v1 字面"的必然结果）。 |
| P1-6 | `fitness[].rubric_file:` 越界 | 本次修了。同 P1-5，作为 v1 严格收敛的副产物。 |
| P2-1 | `created_by: <skill>/<version>` 风格 | 风格条；template 已示范用 `created_by: acceptance-spec`（无版本号）。worker 是否照做属 P2 风格层。 |
| P2-2 | 装饰性 banner 注释 | 无害；不修。 |
| P2-3 | spec.md REQ-002 Extension: 子句 | spec.md 写法层；和 done_when.yaml schema 无关；不修。 |

**注:** P1-5 / P1-6 在 issue 文件中标 P1，但因为它们与 P0-2 同属"schema 之外加字段"类问题，方案 A 的严格收敛逻辑会自动消除它们。**不是越界修 P1，而是 P0-2 的修复 side-effect 覆盖了它们。** 这一点写在风险评估里。

---

## 风险评估

### 风险 1: P0-2 方案 A 牺牲了 leaf-row traceability

**症状:** v1 字面 schema 下，单个 test/existence entry 无法直接指明它出自哪个 REQ。下游 ratchet/test runner 看一个失败 test，需要回 spec.md 查 REQ。

**缓解:**
- 顶层 `based_on:` 是所有 REQ 的 union，能确认 contract 覆盖范围。
- spec.md 每个 REQ 已经有 `source:` 行；测试名按惯例编码 REQ 语义（如 `test_cancel_active_*` 对应 cancel-active REQ）。
- 写 down 在 patches 文件作为已知 trade-off，等附录 C v2 扩展再恢复。

**严重度:** 中。可接受，因为是设计文档 v1 的字面后果。

### 风险 2: `judge: persona-judge` 是 contract 上正确、runtime 上 aspirational

**症状:** 设计文档附录 C / §4.7 把 `persona-judge` 定为 LLM-as-judge 主力。但实际 `persona-distill/persona-judge` skill 的 input contract 是"persona-skill 根目录"，不能直接判任意 artifact。把 `judge: persona-judge` 写进 done_when.yaml 后，Step 4-F 实际仍走 manual fresh-Claude-session 工作流。

**缓解:**
- 在 4-F 段 + fitness-rubric-guide.md + fitness-rubric.md 三处都加了"persona-judge semantics 说明段"，诚实说明 contract token 与 runner 之间的间隙。
- 生成的 rubric.md 文件顶部 How-to-run block 明示是 manual workflow。
- 未来工作：要么扩展 `persona-judge` skill 接受任意 artifact + rubric.md，要么新建 `fitness-judge` skill。任一路径完成后，此风险自动消失。

**严重度:** 中。已透明化，不算 silent bug。

### 风险 3: test-suite-generator validator 收紧后，更老的 done_when.yaml 会被判为 malformed

**症状:** 如果用户手里还有以"旧 schema"（带 leaf 子字段 / llm-rubric / applies_to / rubric_file）生成的 done_when.yaml，下次跑 `/test-suite-generator` 会直接 bail。

**缓解:**
- validator 的 bail 信息明确指向 `/acceptance-spec` 重生 contract。这是正确路径。
- acceptance-spec 已经按 v1 字面输出，所以重生即可。
- 此项暂不写 migration tool，因为 schema v1 是设计文档要求的字面字段集，"旧 schema" 本身就是 skill bug 期间的产物，重生比迁移成本更低。

**严重度:** 低。仅影响有遗留 contract 的用户，且修复路径清晰。

### 风险 4: PBT property type 推断依赖测试命名规范

**症状:** v1 没 `property_type:` 字段，4-B 必须从测试名后缀（`_invariant` / `_idempotent` / ...）推断。如果 worker 写的 PBT 名字没有可识别 archetype token，4-B 走不下去。

**缓解:**
- acceptance-spec 的 schema 注释明确"property_based 测试名应当编码 archetype"。
- worked example 全部按这个命名（`_idempotent`, `_reversible`, `_invariant`, `_state_machine`）。
- validator 把"PBT 名字不含 archetype token"标 warning（不阻塞），但 4-B 看到无法推断的会要求用户重新命名。

**严重度:** 中。引入了对命名规范的隐式契约。可在后续 iter 加 lint。

### 风险 5: 修改可能破坏 SKILL.md/skill 内既有 README / INTEGRATION.md 描述

**症状:** 没修改 SKILL.md 之外的 plugin README / INTEGRATION.md / 顶层文档（任务铁律：只改 skill 源码）。这些文件如果引用 `llm-rubric`，会与新 schema 不一致。

**缓解:**
- 任务铁律已限制 scope，所以这是已知 out-of-scope。
- 后续可在新 iter 加一个 sweep PR 清理 plugin-level 文档。

**严重度:** 低。仅是文档不同步，不影响 skill 行为。

---

## 自检确认

| 检查项 | 状态 |
|---|---|
| 每一份在"修改文件清单"里的文件都实际改过 | ✓ |
| 没动设计文档 `done-when-pipeline.md` | ✓ |
| 没动 `iter-1-step3-attempt-1-output.md` / `iter-1-step3-artifacts/*` | ✓ |
| 没动 `iter-1-step3-attempt-1-issues.md` | ✓ |
| 仅修改 `plugins/done-when-pipeline/skills/acceptance-spec/` 与 `plugins/done-when-pipeline/skills/test-suite-generator/` 下文件 | ✓ |
| 没修 P1/P2 issues（P1-5/P1-6 是 P0-2 修复的副产物，不是单独修） | ✓ |
| 没新增依赖、没改 plugin.json、没改 marketplace.json | ✓ |
| acceptance-spec/SKILL.md 的 Step 3 部分已明确要求 v1 字面输出 | ✓ |
| Schema / Template / Example 三处全部对齐 Appendix C v1 字面 | ✓ |
| 下游 test-suite-generator 的 enum 分支与新 contract 自洽（不会把合法 v1 contract 判 malformed） | ✓ |
