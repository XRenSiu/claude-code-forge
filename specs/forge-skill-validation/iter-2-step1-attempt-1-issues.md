# Step 1 Audit — iter-2-step1-attempt-1

审查对象：`specs/forge-skill-validation/iter-2-step1-attempt-1-output.md`
权威源：`plugins/done-when-pipeline/docs/pipeline-flow.md` (FLOW.md, v0.3.0 end-to-end reference)

## 全局计数

| 级别 | 数量 |
|------|------|
| P0   | 0    |
| P1   | 2    |
| P2   | 3    |

---

## P0 — 阻断

无。

按 FLOW.md 字面硬性约束逐项核对：

| FLOW.md 章节 | 字面要求 | Worker 产出状态 |
|------|----------|----------------|
| Step 1-3 全景图 / S3 行 (FLOW.md 行 27-37) | S3 写 5 份文件 (proposal.md / spec.md / tasks.md / done_when.yaml / spec-robustness.md) | 5 份齐备 (worker 产出 §3 `ls -la` + §4.1-§4.5)：proposal.md / spec.md / tasks.md / done_when.yaml / spec-robustness.md |
| Step 1-3 全景图 spec.md 行 (FLOW.md 行 32) | spec.md `EARS REQ-001..NNN,每条带 source: 行` | REQ-001..REQ-005 五条全部带 `source:` 行 (worker 产出 §4.2 spec.md 行 267 / 272 / 277 / 282 / 290) |
| Step 1-3 全景图 S2 行 (FLOW.md 行 23) | clarify `3 类问题、2-3 轮、≤5 轮硬上限` | 共跑 3 轮 (round 1: 5 题 / round 2: 3 题 / round 3: 1 题)，全部用 `[ambiguity] / [missing edge] / [undefined term]` 三标签 (worker 产出 §2 round 1/2/3 题目首行)；未触发 5 轮上限 |
| Step 1-3 全景图 S2 行 (FLOW.md 行 23) 三类问题语义 | 三类只覆盖：歧义 / 缺失边界 / 未定义术语；不允许问技术栈、性能指标等实现细节 | 9 个问题全部命中三类，无技术栈/SLO/库选型/部署等越界提问 (worker 产出 §2 完整题目列表) |
| Step 1-3 全景图 S2.5 行 (FLOW.md 行 24-25) | `S2.5 反作弊扫 6 类 RHD pattern, close/document/accept 每一项` | 6 类 RHD pattern 表格逐项扫过 (worker 产出 §2 S2.5 表)：close=2 / surface=2 / accept=1 / safe=1，所有非 safe 项都给了 close/surface/accept 处置 |
| Step 1-3 全景图 done_when.yaml 行 (FLOW.md 行 33) | `v1 strict 契约(Appendix C 不可加字段)` | 全部字段都在 Appendix C v1 范围内 (worker 产出 §4.4)：existence 全是 file/function/route/db_field/frontend_component 五种合法 kind 且每条单 key-value、behavior 各层 leaf 全是 bare string、thresholds 仅 4 个允许 key、fitness 仅 criterion/judge/score_threshold 三个 key 且 judge 用 persona-judge、spec_drift_threshold 只有 max_fix_loops_before_escalation 一个子字段。无附加字段 |
| Step 1-3 全景图 spec-robustness.md 行 (FLOW.md 行 33-37) | 四节齐备：`closed_vectors / surfaced_vectors / accepted_risks / verifier_hints` | 四节均存在 (worker 产出 §4.5)：`## closed_vectors` (2 条) / `## surfaced_vectors` (2 条) / `## accepted_risks` (2 条) / `## verifier_hints` (2 条) |

所有 P0 条款均通过。

---

## P1 — 质量

### P1-1: REQ-003 把两条独立可派生的行为强塞进一条 EARS 句

- **证据**：worker 产出 §4.2 spec.md 行 275，REQ-003 写作：
  > "WHEN the server-observed timestamp reaches the `period_end` value of a subscription in status `cancelled_active`, THE system SHALL transition the subscription to status `expired` AND deny premium feature access for that subscription with immediate effect on the next premium-feature request."
- 一条 Event-driven 句里同时承诺两个动作：(a) 状态机迁移 `cancelled_active → expired`，(b) 在下次 premium 请求时拒绝访问。后者 (b) 与 REQ-005 (worker 产出 §4.2 行 285) 已经独立写明的 `IF ... expired, THEN ... 402` 重叠。
- FLOW.md 行 32 字面要求 `EARS REQ-001..NNN`，即每条 REQ 是一条 EARS 句；FLOW.md 没禁止 AND 复合 SHALL，但把"边界 tick 时刻发生的状态迁移"和"下次 premium 请求时的拒绝"绑在同一个 WHEN 触发器下，让 REQ-003 自己不再独立可派生测试（验证 (b) 必须先 fixture 出"下一次 premium 请求"事件，而那已经是 REQ-005 的语义）。
- 这条算 P1（EARS 句式合法但选择不到位）：(b) 的触发器其实是"premium 请求到达 + 订阅是 expired"，与 REQ-005 重复；REQ-003 应只保留 (a) 状态机迁移这一动作。

### P1-2: existence 漏列 REQ-005 / REQ-002 隐含的两个组件

- **证据**：worker 产出 §4.4 done_when.yaml 行 377-384 的 existence block 共 7 条，全部围绕 cancel 流程 (use case / route / db field / button)。
- spec.md REQ-005 (worker 产出 §4.2 行 285) 与 tasks.md (worker 产出 §4.3 行 344, 358) 均把"premium-access authorization 中间件"和"UI 续费提示组件 (renewal prompt)"作为可命名工件，但 done_when.yaml 没有 `function:` 或 `frontend_component:` 入口指向它们。
- FLOW.md 行 33 字面要求 `done_when.yaml v1 strict 契约`；FLOW.md 未规定 existence 必须穷举，但漏列两条直接关联 REQ-005 的可命名工件，让 4-A existence 阶段对 REQ-005 整条只能靠 route+db_field 旁证。
- 这条算 P1（existence 检查只覆盖部分名词指代）：worker 已经在 tasks.md 命名了对应工件，但没把它们提升到 existence 入口。

---

## P2 — 风格

### P2-1: done_when.yaml `created_at` 时间戳与运行日期不一致

- **证据**：worker 产出 §4.4 done_when.yaml 行 374 `created_at: 2026-05-25T00:00:00Z`，但实际产出时间根据 §3 `ls -la` 的 `May 25 10:02` 大致是当天 10:02 UTC 偏移。
- FLOW.md 未规定 timestamp 必须精确到秒；用日期零点是常见占位，但与文件 mtime 不一致是风格瑕疵。

### P2-2: spec-robustness.md `closed_vectors` 条目用 `pattern:` 又用 `rhd_pattern:` 两个 key 表达同一意思

- **证据**：worker 产出 §4.5 spec-robustness.md 行 446-454 和行 456-468 两条 closed_vectors 同时给出 `pattern: assertion_weakening` 与 `rhd_pattern: test_modification`；surfaced_vectors 也一样 (`pattern: branch_coverage_gap` + `rhd_pattern: coverage_gaming`)。
- FLOW.md 仅规定四节标题，未规定每条目内字段名；但 `pattern:` 与 `rhd_pattern:` 同时出现且语义近似，纯排版冗余。

### P2-3: clarify 三轮答题段把 PM 决策理由内联到 worker 日志

- **证据**：worker 产出 §2 round 1/2/3 的 "My answers" 段（行 99-104 / 138-142 / 162-164）逐条带 industry-standard 引用（Stripe / RFC 7231 / Chargebee）和理由说明。
- FLOW.md 字面没有要求 clarify 答复必须简洁，也没禁止；但这些详细理由不是 skill 产出的一部分（落点不会写进任何 5 份文件），出现在归档日志里仅供观感参考，属于日志风格偏好。

---

## 分级标准回顾（照抄自审查指令）

**P0 阻断** — skill 违反 FLOW.md 明确写出的硬性约束：
- 未产出 5 份文件之一 (proposal.md / spec.md / tasks.md / done_when.yaml / spec-robustness.md)
- spec.md 中的 REQ 缺失 `source:` 字段
- clarify 循环超过 5 轮硬上限
- clarify 中问了非"歧义/缺失边界/未定义术语"三类之外的问题（例如问技术栈、性能指标等实现细节）
- done_when.yaml 添加了 Appendix C 不允许的字段 (v1 strict)
- spec-robustness.md 缺四节中任一节 (closed_vectors / surfaced_vectors / accepted_risks / verifier_hints)
- 没跑 S2.5 反作弊扫描

**P1 质量** — skill 完成了要求的动作但做得不到位：
- EARS 句式合法但选择不合理（例如 Event-driven 应该用 State-driven）
- PBT 识别的属性过于浅层（只有非空判断，没有不变量/幂等性）
- existence 检查只覆盖部分名词指代
- clarify 问题质量低，问了显而易见的事

**P2 风格** — 主观偏好不一致：
- 文件命名风格 / 注释详细程度 / 排版
