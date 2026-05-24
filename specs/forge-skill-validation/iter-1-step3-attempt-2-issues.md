# Step 3 Auditor — iter-1-step3-attempt-2 审查报告

> 独立 Auditor subagent 对 Worker attempt-2 产出的逐项核对。
> 权威源：`/Users/xrensiu/Documents/Downloads/done-when-pipeline.md` 第五章「Step 3：规格固化」+ 附录 C「done_when YAML schema」。
> 已实际读取 4 件套磁盘文件（proposal.md / spec.md / tasks.md / done_when.yaml），不只读 manifest。

---

## 总体结论

**Attempt-1 的两个 P0 已全部消除；本次 attempt-2 在硬约束维度 zero P0、zero P1。** 仅存 1 项 P2（风格）。

---

## P0（违反 5.3 / 附录 C 硬性字段或枚举）

**无。**

attempt-1 的 2 个 P0 经核对均已修复：

### P0-1（attempt-1 历史）：`fitness[].judge` 枚举值错 — **已修复**

- 附录 C 原文（done-when-pipeline.md §附录 C, schema v1）：
  > `judge: <persona-judge | programmatic | manual>`
- attempt-2 实际产出（done_when.yaml 第 115、118 行）：
  ```
  - criterion: ...
    judge: persona-judge
    score_threshold: ">= 8/10"
  - criterion: ...
    judge: persona-judge
    score_threshold: ">= 8/10"
  ```
- 两条 fitness 的 judge 均落在三值 enum 内。**通过**。

### P0-2a（attempt-1 历史）：`existence[]` 每项加了 schema 未定义子字段 — **已修复**

- 附录 C 原文（§附录 C, schema v1, existence 节）：
  ```
  existence:
    - file: <path>                 # 文件必须存在
    - function: <name>             # 函数必须 export
    - route: <method> <path>       # 路由必须注册
    - db_field: <table>.<column>   # 数据库字段必须存在
    - frontend_component: <name>   # 前端组件必须存在
  ```
  每项是一个单键值对（key 为五种 kind 之一），schema 字面未列出任何子字段。
- attempt-2 实际产出（done_when.yaml 第 12–32 行）：20 条 existence 全部为单键值对（10 条 `function:` + 4 条 `route:` + 6 条 `db_field:`），无任何 `based_on:` / `applies_to:` / `tool:` 等子字段；五种 kind 中实际只用了 function / route / db_field，三者全部在 5 选 1 的合法集合内。**通过**。

### P0-2b（attempt-1 历史）：behavior leaf 应为 bare string，attempt-1 写成了 mapping — **已修复**

- 附录 C 原文（§附录 C, schema v1, behavior 节）：
  ```
  behavior:
    unit_tests:
      example_based:
        - <test_name>
      property_based:
        - <test_name>
    integration_tests:
      example_based:
        - <test_name>
      property_based:
        - <test_name>
    e2e_tests:
      - <test_name>
  ```
  每个 leaf 项目均为 `- <test_name>`，即 bare string，未列任何 sub-field。
- attempt-2 实际产出（done_when.yaml 第 44–98 行）：
  - `unit_tests.example_based` 27 项 — 全部 bare string；
  - `unit_tests.property_based` 9 项 — 全部 bare string；
  - `integration_tests.example_based` 6 项 — 全部 bare string；
  - `integration_tests.property_based` 2 项 — 全部 bare string；
  - `e2e_tests` 3 项 — 全部 bare string。
  无任何 `name:` / `based_on:` / `property_type:` / `dependencies:` / `tool:` 子字段。**通过**。

---

## 其他附录 C 硬约束逐项核对

| 检查项 | 期望（附录 C / §5.3 原文） | attempt-2 实际 | 结果 |
|---|---|---|---|
| 4 件套文件名 | §5.3：`proposal.md / spec.md / tasks.md / done_when.yaml` | 4 个文件名完全一致，位于 `iter-1-step3-attempt-2-artifacts/` 下 | ✓ |
| 4 件套数量 | §5.3 写明就这 4 件 | 4 个，无多无少 | ✓ |
| 顶层字段完整 | 附录 C v1：`feature / based_on / created_at / created_by / existence / behavior / fitness / spec_drift_threshold` | done_when.yaml 顶层 8 个字段全在，无多余顶层字段 | ✓ |
| `feature` 命名 | 附录 C：`<string>` kebab-case | `channel-mention-notifications` | ✓ |
| `based_on` | 附录 C：`[<REQ-ID>, ...]` | `[REQ-001, ..., REQ-007]` 7 个 ID 与 spec.md 中实际 REQ 完全对齐 | ✓ |
| `created_at` | 附录 C：`<ISO-8601>` | `2026-05-24T00:00:00Z` | ✓ |
| `created_by` 含 skill 名 | 附录 C：`<skill-name>` | `acceptance-spec` | ✓ |
| `existence[]` kind 合法 | 5 选 1：`file / function / route / db_field / frontend_component` | 用到 function / route / db_field — 全合法（未用 file / frontend_component 是允许的，附录 C 未要求全用） | ✓ |
| `behavior` 三层 + thresholds 结构 | 附录 C：`unit_tests / integration_tests / e2e_tests / thresholds` 四子键齐全 | 四子键全齐 | ✓ |
| `unit_tests` 双风格 | 附录 C：`example_based / property_based` | 二者均出现 | ✓ |
| `integration_tests` 双风格 | 附录 C：`example_based / property_based` | 二者均出现 | ✓ |
| `e2e_tests` | 附录 C：扁平 list，无 example / PBT 子分 | done_when.yaml 第 95–98 行：3 项扁平 list | ✓ |
| `thresholds` 4 字段齐全 | 附录 C：`unit_coverage / integration_coverage / mutation_kill_rate / pbt_runs_per_property` | 4 字段全齐：`>= 0.80 / >= 0.60 / >= 0.70 / >= 500` | ✓ |
| `fitness[]` 每项含 criterion / judge / (score_threshold) | 附录 C：programmatic 可省 score_threshold；其余必填 | 两条 fitness 均含三键且 judge 为 persona-judge（非 programmatic），故 score_threshold 必填 — 均已填 | ✓ |
| `spec_drift_threshold` 仅 `max_fix_loops_before_escalation` | 附录 C：仅此一子字段 | 仅此一子字段，值为 3 | ✓ |
| spec.md REQ 唯一 ID | 设计文档 §11.1 关键 prompt：「每条 EARS 必须有唯一 ID」 | REQ-001 / REQ-002 / REQ-003 / REQ-004 / REQ-005 / REQ-006 / REQ-007，无重号 | ✓ |
| spec.md 每条决策可溯源 | 设计文档 §11.1：「每条决策追溯到一个澄清回答」 | 7 条 REQ 全部含 `source: S2 round X QY ...` 行 | ✓ |
| based_on 与 spec.md REQ 集合一致 | 附录 C：`based_on: [<REQ-ID>, ...]` 应指向 spec.md 的真实 REQ | done_when.yaml `based_on` 7 个 ID 与 spec.md 中 7 个 REQ 一一对应，无缺失、无多余 | ✓ |

---

## P1（质量瑕疵但未违硬约束）

**无。**

---

## P2（风格）

### P2-1：spec.md REQ 段使用了 "Extension:" 与 "Constraint (thread scope):" 自创子标签

- **位置**：spec.md 第 10 行（REQ-001 下的 "Constraint (thread scope):"）、第 20 行（REQ-002 下的 "Extension:"）。
- **设计文档相关章节**：§5.4 done_when.yaml 样例未约束 spec.md 内部 markdown 子段结构；附录 A 仅列举五种 EARS 句式模板，不涉及 REQ 段内子标签。
- **判定**：设计文档对 spec.md 的硬约束限于「EARS 句式 + 唯一 REQ ID + source 溯源」，未禁止 REQ 块内附加约束子段。Worker 自承（manifest §「Skill 指令模糊点」第 4 条）此为 template 之外的自创格式。**不构成违反**，但首次审阅可能引起"这是 EARS 哪种句式"的歧义。
- **不要求修复。**

---

## 审查方法学说明

1. 已独立打开磁盘 4 个文件（不只读 Worker manifest 的嵌入版本），逐字逐行对照附录 C v1 schema。
2. 重点针对 attempt-1 已知的 2 个 P0（fitness judge enum 错 / leaf 加子字段）逐字核验消除情况。
3. 顶层 8 字段、existence 五种 kind、behavior 三层 + thresholds 四阈值、fitness 三键、spec_drift_threshold 单子字段 — 全部勾选确认。
4. 跨文件交叉一致性：`based_on` (done_when.yaml) ↔ REQ-XXX (spec.md) ↔ `implements:` (tasks.md) — 7 条 REQ ID 在三处一致，无飘号。

## 最终裁定

- **P0：0 项**
- **P1：0 项**
- **P2：1 项**（风格，不要求修复）

**Attempt-2 在附录 C 硬约束层面通过审查。** Attempt-1 的两个 P0 全部按对齐到附录 C v1 的方式消除。

—— end of audit ——
