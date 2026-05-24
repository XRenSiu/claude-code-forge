# iter-1 — Comprehensive P1/P2 patches

**Date**: 2026-05-25
**Scope**: Fix every iter-1 P1/P2 issue that is fixable at the skill-source layer (Category A), and add guidance for B-category issues where guidance is the right hammer.
**Plugin version bump**: `done-when-pipeline` 0.1.0 → 0.2.0 (minor bump — process/format hardening, no breaking schema change). Both skills bumped to 0.2.0 in their SKILL.md frontmatter.

---

## 1. 处理范围

### A 类 — 在 skill 源码层硬化（共 18 个修复点）

| # | iter-1 issue | 修在哪 | 修复 verb |
|---|---|---|---|
| A1 | step1/P1-1: State-driven vs Unwanted 选择牵强 | `acceptance-spec/references/ears-syntax.md` | 在 cheat-sheet 加 tie-breaker rule + 示例 |
| A2 | step1/P1-2, step2/P1-3: 跨 REQ 因果指代 | `acceptance-spec/SKILL.md` Iron rule 8 + `references/ears-syntax.md` Common drafting mistakes 表 | 新加 Iron rule 8 + 表格新行 |
| A3 | step1/P2-1: 草稿头部漏 `Feature:` 前缀 | `acceptance-spec/SKILL.md` S1 段 + `references/output-templates/spec-template.md` | 模板硬写 `# Feature: <slug> (draft)` |
| A4 | step1/P2-2: `[?]` 后问题书写格式不一致 | `acceptance-spec/SKILL.md` S1 + `references/clarify-protocol.md` 格式段 | 显示 `[?] [<tag>] "<noun>": <option-a> or <option-b>?` 范式，S1/S2 统一 |
| A5 | step1/P2-3: 歧义清单三份冗余 | `acceptance-spec/SKILL.md` S1 段 | 明示 "exactly two ambiguity surfaces, not three" |
| A6 | step1/P2-4: 中英文混排不统一 | `acceptance-spec/SKILL.md` Iron rule 10 | 新加 "Single-language per primary surface" iron rule |
| A7 | step2/P1-1: Round 3 < 3 题 | `acceptance-spec/references/clarify-protocol.md` Rule 2 | 新增 "What if the round has fewer than 3 questions left?" 子段 |
| A8 | step2/P1-2: 决策溯源颗粒度不一致 | `acceptance-spec/SKILL.md` S2 输出规则 + Iron rule 9 | 明示 "S2 不能输出 parallel decision-trace table，spec.md 的 source: 行为单一权威" |
| A9 | step2/P2-1, P2-4: 内部权衡过程暴露 / 元日志过厚 | `acceptance-spec/SKILL.md` Iron rule 9 | "Worker output ≠ internal decision process" iron rule |
| A10 | step2/P2-2: Glossary (working) 越界到 Step 2 输出 | `acceptance-spec/SKILL.md` S2 段 | "Do not include a `## Glossary` section in any S2 output" |
| A11 | step2/P2-3: REQ 内嵌定义子句过长 | `acceptance-spec/SKILL.md` S3 段 | "Keep REQ bodies tight (≤ ~25 words)" + 把定义移到 Glossary 的 worked example |
| A12 | step3/P2-1: spec.md "Extension:"/"Constraint:" 自创子标签 | `acceptance-spec/SKILL.md` S3 段 + `references/output-templates/spec-template.md` | 把 `### Constraint:` / `### Extension:` 列为合法、有限的两个 sub-clause 标签 |
| A13 | step4/P1-1: state machine PBT 测自身 bookkeeping | `test-suite-generator/references/sub-modules/unit-test-generator.md` | "PBT must reach the impl" 段，含 anti-pattern vs required-pattern 代码示例 |
| A14 | step4/P1-2: `_atomicity` 名实不符 | `test-suite-generator/references/sub-modules/unit-test-generator.md` + `integration-generator.md` | 新增 "Test name's archetype suffix must match the assertion semantics" 段 + per-suffix 对应表 |
| A15 | step4/P1-3: dispatch 返回类型不一致 | `test-suite-generator/references/sub-modules/unit-test-generator.md` | 新增 "Return-type consistency for the function under test" 段，含 anti-pattern + required-pattern |
| A16 | step4/P1-4: 测试用 endpoint 未登记 | `test-suite-generator/SKILL.md` Iron rule 11 + `references/sub-modules/existence-extractor.md` | 新增 Iron rule + 新段 "Test-only endpoints / hooks MUST be in `existence:`" |
| A17 | step4/P2-4: PBT alphabet 未文档化 | `test-suite-generator/references/pbt-property-types.md` + `references/sub-modules/integration-generator.md` | "Document narrow alphabets and label sets" 子段 + 示例 docstring |
| A18 | step6/P1-1, P1-4, P1-5, P1-6: SKILL.md 不讲兜底 / budget 出处 / escalate vs convergence 微差 / spec vs code 准则 | `acceptance-spec/SKILL.md` + `test-suite-generator/SKILL.md` 末尾 "Step 5-6 hand-off" 段 + `INTEGRATION.md` "Translation parameters" 表 + "How to decide: spec wrong vs code wrong" 段 | 集中加 hand-off 段；INTEGRATION 给 budget=15 的实证出处（"5-8 round 典型 × 2x headroom"），加 escalate 与 convergence 的语义微差说明，加判别准则表（PBT 反例 vs REQ 文本一致 → spec wrong；矛盾 → code wrong；mutation 漏 → code wrong；e2e 漏而 integration 过 → code wrong） |

### B 类 — 不可在 skill 源码层修复，但可加 guidance（共 4 个修复点）

| # | iter-1 issue | 处理 |
|---|---|---|
| B1 | step4/P2-1~P2-3: 6.8 矩阵偏离 | `test-suite-generator/SKILL.md` 新加 Iron rule 12 — 要求 worker 为每个 REQ 对照 §6.8 矩阵选 layer，矩阵 ✗ 但 YAML 列了的 → 在文件头部加 deviation comment；矩阵 ✓ 但 YAML 无的 → 不发明（符合 iron rule 7） |
| B2 | step5/P1-1~P1-5: Worker 未对照 §7.4 schema | 新建 `test-suite-generator/references/step-5-audit-checklist.md`：10-field §7.4 schema 钩子表 + 做判分离 verification 表 + anti-reward-hacking 三项检查 + reviewer 报告推荐结构。Resource index 引用。 |
| B3 | 测试用 endpoint 行为重定义 | 已在 A16 处理，A 类即可 |
| B4 | step6/P1-2, P1-3: 达标出口 / fix 路径细分（ratchet 职责） | INTEGRATION.md "How to decide: spec wrong vs code wrong" 已通过 forward reference 处理；不试图越俎代庖去文档 ratchet 内部流程 |

---

## 2. 修改的文件清单（9 个文件 + 1 新建）

```
plugins/done-when-pipeline/
├── .claude-plugin/plugin.json                 # version bump 0.1.0 → 0.2.0
├── INTEGRATION.md                              # +translation parameters 表, +spec vs code 判别段
├── skills/acceptance-spec/
│   ├── SKILL.md                                # +Iron rules 8/9/10, S1/S2/S3 段改写, +Step 5-6 hand-off 段, version 0.2.0
│   └── references/
│       ├── ears-syntax.md                      # +State-driven vs Unwanted tie-breaker, +跨 REQ 指代 anti-pattern 表行
│       ├── clarify-protocol.md                 # +Round 3 < 3 处理子段, +format 示例统一
│       └── output-templates/spec-template.md   # +Feature: 前缀, +Constraint/Extension sub-clause 规则
└── skills/test-suite-generator/
    ├── SKILL.md                                # +Iron rules 11/12, +Step 5-6 hand-off 段, +step-5-audit-checklist resource index, version 0.2.0
    └── references/
        ├── pbt-property-types.md               # +Document narrow alphabets 段
        ├── step-5-audit-checklist.md           # NEW 文件
        └── sub-modules/
            ├── existence-extractor.md          # +Test-only endpoints 段
            ├── unit-test-generator.md          # +PBT 必须 reach impl, +archetype suffix match assertion, +Return-type consistency, 去 property_type: 引用
            └── integration-generator.md        # +archetype suffix match (atomicity 重点), +PBT alphabet 文档化, 去 property_type: 引用

.claude-plugin/marketplace.json                 # done-when-pipeline version bump
```

---

## 3. 每个文件的修改前后摘要

### 3.1 `acceptance-spec/SKILL.md`

**Before:** 7 个 iron rules，S1 模板用 `# <slug> (draft)`，S1 输出含三份冗余歧义清单，S2 段没禁止 Glossary/元日志暴露，S3 段没规定 REQ body 长度也没规定 sub-clause 标签，末尾 next-step 只指 test-suite-generator。

**After:**
- Iron rules 增至 10 条。新 8/9/10 分别治：跨 REQ 指代禁止 / Worker output 只含交付物 / 单语言。
- S1 模板硬写 `# Feature: <slug> (draft)`。`## Open questions` 用统一格式 `[?] [<tag>] "<noun>": <a> or <b>?`。明示 "exactly two ambiguity surfaces"。
- S2 段加 "What you must not do" 两条：no Glossary、no decision-trace 表。明示 S2 输出只两件。
- S3 段 spec.md 部分：keep REQ tight ≤25 words，把长定义移 Glossary。新加 `### Constraint:` / `### Extension:` sub-clause 合法标签。
- 文末新加 "Step 5-6 hand-off" 段，含 spec_drift_threshold ↔ convergence 映射 + spec/code 判别 forward ref。
- version 0.2.0。

**理由：** 这一个文件覆盖 11 个 issue（step1 P1-1, P1-2, P2-1, P2-2, P2-3, P2-4；step2 P1-2, P1-3, P2-1, P2-2, P2-3；step3 P2-1；step6 P1-1）。集中在 SKILL.md 比散在 references 更可见。

---

### 3.2 `acceptance-spec/references/ears-syntax.md`

**Before:** Selection cheat-sheet 五条线性问题，Common drafting mistakes 表 6 行。

**After:**
- Cheat-sheet 末尾新加 "Tie-breaker: State-driven vs Unwanted (the most common confusion)" 子段，含 side-by-side 反例（DND case），并明示 "when in doubt, prefer Unwanted for per-event conditional handling"。
- Common drafting mistakes 表新加一行 "Cross-REQ causal indirection" + 示例 + 指回 SKILL.md Iron rule 8。

**理由：** Iron rule 8 在 SKILL.md 是规则，这里是 EARS 选型阶段就能看到的反例。两处加在一起，worker 在 S1 写 EARS 时能命中"是否落到 reverse 模式"的判断。

---

### 3.3 `acceptance-spec/references/clarify-protocol.md`

**Before:** Rule 2 表只列 round 1-5 的 typical content，没说凑不够 3 题怎么办。Format for clarify-round message 用占位符 `...`，没显示统一格式。

**After:**
- Rule 2 末尾新加 "What if the round has fewer than 3 questions left?" 子段，给三选一决策：(1) 把上轮 second-order 推迟到本轮、(2) 按 Rule 6 normal stop。明示 *不要* 编造伪问题来凑数（违反 Rule 1）。
- Format 段示例改写：用真实 REQ-001/002/003 例子取代占位符，明示 `[<tag>] [REQ-anchor]: "<noun>" <options>?` 格式，与 S1 `## Open questions` 统一。

**理由：** step2/P1-1 worker 已经识别 Rule 2/5/6 的权衡，但 protocol 没明文兜底，现在补上。Format 统一减少 step1 worker 自造风格的空间。

---

### 3.4 `acceptance-spec/references/output-templates/spec-template.md`

**Before:** `# Spec: <feature-slug>` 标题，REQ 块只有 EARS 句 + source 行。

**After:**
- 标题改 `# Feature: <feature-slug>`，与 S1 draft 头一致。
- README 段加 keep REQ tight 提示。
- REQ-002 块作为示例，展示 `### Constraint:` / `### Extension:` sub-clause 使用。
- 末尾新加 sub-clause grammar 段：只允许这两个 label，否则升级为独立 REQ。

---

### 3.5 `test-suite-generator/SKILL.md`

**Before:** 10 个 iron rules，末尾 "hand the spec + tests to /ratchet as the implementation contract" 一句话 next-step。Resource index 不含 step-5-audit-checklist。

**After:**
- Iron rules 增至 12 条：rule 11 治测试用 endpoint 未登记问题；rule 12 治 §6.8 矩阵偏离（要求加 deviation comment）。
- 文末新加 "Step 5-6 hand-off" 段：manual translation 强调，"PBT 持续失败 ≈ spec bug" mental model 引入，给 spec/code 判别 rule。改写 next-step 从 "as the implementation contract" 到 "manually translates ... into a `/ratchet` invocation"，避免误导用户以为 ratchet 自动消费 done_when.yaml。
- Resource index 加 step-5-audit-checklist.md 条目。
- version 0.2.0。

---

### 3.6 `test-suite-generator/references/sub-modules/unit-test-generator.md`

**Before:** Per-test recipe 第 4 步用 `property_type:` 引用（schema v1 无此字段），quality checklist 7 项。

**After:**
- 第 4 步改为 archetype-from-suffix。
- 表头 `property_type:` 改为 archetype (= name suffix)。
- Quality checklist 加 3 项：PBT bookkeeping、return-type 一致、archetype-suffix match assertion。
- 文末新加三大段：
  1. **PBT must reach the impl** — 含 SubscriptionStateMachine 的 anti-pattern（asserting self.fired_history）vs required-pattern（asserting impl 返回值）。
  2. **Test name's archetype suffix must match the assertion semantics** — per-suffix 表（包括 `_atomicity` 必须 inject failure 检验 before == after）。
  3. **Return-type consistency for the function under test** — DispatchMentionNotification 例子，要求"同一文件统一 shape"，否则拆名。

---

### 3.7 `test-suite-generator/references/sub-modules/integration-generator.md`

**Before:** 末尾只 "when not to generate"，对 atomicity / alphabet 无指导，`property_type:` 字面引用 1 处。

**After:**
- `property_type:` 字面引用改为 "name-suffix archetype"。
- 文末新加两段：
  1. **Hard rule: archetype suffix must match the assertion semantics** — atomicity 重点：必须 (i) failure injection (ii) before==after 断言。明示 "delivery iff any surface fires" 不是 atomicity，是 invariant，应改名。
  2. **Hard rule: PBT alphabet / labels must be documented** — docstring 必须命名 narrow alphabet 出处。

---

### 3.8 `test-suite-generator/references/pbt-property-types.md`

**Before:** Generator hygiene 3 项（位置、shrinking、bound size）。

**After:** 加第 4 项 "Document narrow alphabets and label sets"，含 worked docstring 示例。

---

### 3.9 `test-suite-generator/references/sub-modules/existence-extractor.md`

**Before:** "What this script does not do" 段后结束。

**After:** 新加 "Test-only endpoints / hooks MUST be in `existence:`" 段：原则 + 工作流（先检查 done_when.yaml → 缺则 push back 上游或这里 augment + 在 manifest 标注）+ 适用范围（route/function/db_field/frontend_component 对称）。

---

### 3.10 `INTEGRATION.md`

**Before:** Recommended invocation 给的 `budget: max 15 rounds` 无出处；spec_drift 翻译段一笔带过 convergence；spec/code 二分无判别规则。

**After:**
- Recommended invocation 后新加 "Translation parameters — where the numbers come from" 表：success / convergence / budget 各栏含来源和语义微差说明。明示 `max_fix_loops_before_escalation` ≠ `convergence`（一是 escalate-to-user 动作，一是 stop-the-loop 动作），数值映射不冲突但语义不严等价。
- spec_drift 段末尾新加 "How to decide: spec wrong vs code wrong" 子段：4 个判断 case，每个有具体 trigger + 行动。

---

### 3.11 NEW: `test-suite-generator/references/step-5-audit-checklist.md`

10-field §7.4 schema 表（feature/timestamp/existence/unit_tests/integration_tests/e2e_tests/mutation_testing/fitness/overall_status/meets_done_when 各栏含 "where the signal comes from" + check 描述）+ §7.2 做判分离 verification 表（结构性 vs 约定式）+ §7.5 anti-reward-hacking 三项检查 + reviewer narrative report 推荐结构。

---

## 4. 未修的 issues 与原因

| iter-1 issue | 等级 | 为什么不修 |
|---|---|---|
| step5/P2-1: Worker 自述"未读 source spec" | P2 | Worker 行为问题，不是 skill 缺陷。step-5-audit-checklist.md 间接帮 reviewer 不再走这条路。 |
| step5/P2-2: Worker 列"事实陈述"越界 auditor 职责 | P2 | Worker 行为。 |
| step5/P2-3: 引片冗余可压缩 | P2 | Worker 风格选择。 |
| step5/P2-4: acceptance-spec 自称 "Steps 1-3" 与 done_when 归属讨论 | P2 | Step 5 边界外的讨论，Worker 自审。 |
| step6/P1-2: 达标归档行为未声明 | P1 | ratchet 的内部职责，不是 done-when-pipeline 的职责。INTEGRATION 中已有 forward reference 给 ratchet。 |
| step6/P1-3: fix prompt 路径细分（PBT/mutation/e2e 不同处理） | P1 | 同上，ratchet 职责。INTEGRATION 的 "How to decide: spec vs code" 已涵盖 PBT vs mutation vs e2e 的不同处理方向。 |
| step6/P2-1~P2-3: 措辞精度、首屏密度 | P2 | attempt-2 已修了大部分，残余的不构成误导。"hand ... as the implementation contract" 已在 test-suite-generator/SKILL.md 末尾 hand-off 段改写为 "manually translates"，N-2 的措辞张力已消。 |
| step4/P2-5: mutation 路径文档不一致 | P2 | 已在 mutation/README.md 中标 documented limitation。implementer 自然会移动文件；不需要在 mutation.sh 也加 echo。 |
| step4/P2-6: manifest count 错 | P2 | worker 报告 typo，不是 skill 缺陷。 |

---

## 5. 风险评估

| 风险 | 缓解 |
|---|---|
| Iron rules 增长（acceptance-spec 7→10，test-suite-generator 10→12） | 每条 iron rule 都有具体 anti-pattern 反例可对照；不是抽象原则。Worker 读 iron rules 时知道在防什么 bug。 |
| Step 5-6 hand-off 段在两份 SKILL.md 各写一份，可能漂移 | 两份都引同一份 INTEGRATION.md 作为权威 recipe，措辞约束在"manually translate"四字上，避免重定义协议。 |
| `### Constraint:` / `### Extension:` sub-clause 引入新格式，对下游 test-suite-generator 4-B/4-C 的 EARS 解析有影响吗？ | 不影响。Sub-clause 是 spec.md 的 markdown 子段，test-suite-generator 走 done_when.yaml 的 behavior 列表派生测试，不直接解析 spec.md 的 sub-clause。Sub-clause 的语义已经 baked-in 到 done_when.yaml 的测试名。 |
| Iron rule 11（test-only endpoint 登记）会让 worker 倾向于 augment done_when.yaml 而不是 push back 上游 | 已在 existence-extractor.md 强调 "push back upstream" 是首选，augment 是 fallback 且必须在 manifest 中显式标注。两条路径都安全。 |
| Iron rule 12（§6.8 矩阵偏离 deviation comment）增加了 worker 的报告负担 | deviation comment 只在 YAML 与矩阵不一致时加，矩阵正常一致时 worker 不需多做事。多出来的 comment 仅一行注释，cost 可忽略。 |

---

## 6. iter-2 重跑预期

iter-1 issues 中可在 skill 源码硬化的 18 个 P1/P2 + 加 guidance 的 4 个，共 22 个修复点全部就位。iter-2 重跑同一 channel-mention-notifications brief，期望：

- **step1 attempt-1 issues**: P1-1, P1-2, P2-1, P2-2, P2-3, P2-4 全消除。剩余仅可能是 EARS 句式选择艺术（不在硬约束范围）。
- **step2 attempt-1 issues**: P1-1（凑数）有 Rule 2 的兜底规则；P1-2（颗粒度）有 Iron rule 9 禁止 parallel trace table；P1-3（跨 REQ 指代延续）有 Iron rule 8；P2-1~P2-4 全有规则覆盖。
- **step3 attempt-2 issues**: P2-1（Extension/Constraint）已转为合法 sub-clause，不再算偏差。
- **step4 attempt-2 P1 issues**: P1-1（PBT bookkeeping）、P1-2（atomicity 名实）、P1-3（return-type）、P1-4（test-only endpoint）四条全有针对性规则 + 代码示例。
- **step4 attempt-2 P2**: 矩阵偏离（P2-1~P2-3）有 Iron rule 12 要求 deviation comment；alphabet（P2-6）有文档化规则。残余的 mutation 路径（P2-4/P2-5）和 manifest count（P2-6 注：原 P2-5）属 documented limitation，不影响契约。
- **step5 attempt-1 P1**: step-5-audit-checklist 提供 10-field §7.4 schema 钩子，reviewer 不再"未读 source spec"。
- **step6 attempt-2 P1**: budget 15 出处（P1-4）、escalate vs convergence 语义微差（P1-5）、spec wrong vs code wrong 准则（P1-6）三条在 INTEGRATION 中全有；兜底机制（P1-1）在两份 SKILL.md 末尾 hand-off 段引入。

剩余可能出现的 P1/P2 来自 worker 的具体内容选择（如某 REQ 的 EARS 类型选择是否最优），不属于 skill 规则可硬化的范畴。
