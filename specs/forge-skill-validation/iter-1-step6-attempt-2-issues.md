# Audit — iter-1 Step 6 attempt 2 (post-Fixer)

**Auditor**: independent subagent (read-only; not the Worker, not the Fixer).
**Inputs verified by direct file reads on disk**:
- `plugins/done-when-pipeline/INTEGRATION.md` (144 lines)
- `plugins/done-when-pipeline/README.md` (93 lines)
- `plugins/done-when-pipeline/skills/acceptance-spec/SKILL.md` (217 lines)
- `plugins/done-when-pipeline/skills/test-suite-generator/SKILL.md` (305 lines)
- `plugins/done-when-pipeline/.claude-plugin/plugin.json` (description line 3)
- `specs/forge-skill-validation/iter-1-step6-attempt-2-output.md` (Worker's claim sheet)
- 设计文档 `done-when-pipeline.md` 第八章 (§8.1-8.4) 与 §12.1.IV

> Worker 给出的行号在两份目标文档上**自己读时 +1**（worker 报 145/94 lines，实际 `wc -l` 为 144/93）。这是无尾换行 vs 有尾换行的差，不实质影响其引文定位 — 抽查 INTEGRATION line 60-83 / README line 38-66 内容与 worker 引用一致。下文一律以**实际磁盘 line 号**记。

---

## 1. P0 修复验证

### P0-1：`INTEGRATION.md` 不再含 `applies_to:` 示例

**结论：完全消除（confirmed）。**

跨四文档 `grep -n "applies_to"` 实测命中：

```
INTEGRATION.md:74:Do not add `applies_to:` or any other key — strict v1 parsers will reject it.
acceptance-spec/SKILL.md:177:- `spec_drift_threshold:` ... Do NOT add `applies_to:` or any other key.
```

两处全部是**禁止语境**（"Do not / Do NOT"），0 处示例残留。`INTEGRATION.md` line 69-72 现版示例 yaml：

```yaml
spec_drift_threshold:
  max_fix_loops_before_escalation: 3
```

字面与 `acceptance-spec/SKILL.md` line 177 严格 schema 一致。INTEGRATION line 67-68 新增反向引用至 SKILL.md 与 `references/done-when-schema.yaml`，形成权威出处闭环。修复合格。

### P0-2：`README.md` 不再暗示 ratchet 自动 escalate

**结论：完全消除（confirmed）。**

跨四文档 `grep -nE "escalat|auto-?escalation"` 实测命中 12 处。分类核对：

| 文件:行 | 命中 | 性质 |
|---|---|---|
| acceptance-spec/SKILL.md:177 | "Do NOT add `applies_to:`" 段含字段名 | 字段名（无评价） |
| acceptance-spec/SKILL.md:182 | yaml 示例字段名 | 字段名（无评价） |
| acceptance-spec/SKILL.md:184 | "Auto-escalation is future work; do not promise..." | **显式否定** |
| README.md:39 | "after `max_fix_loops_before_escalation` (default 3) rounds" | 字段名 |
| README.md:42 | "No auto-escalation in v0.1." | **显式否定** |
| README.md:66 | "no auto-escalation of 'PBT failures look like spec bugs' in v0.1" | **显式否定** |
| INTEGRATION.md:60 | "does not honor a `spec_drift_threshold.max_fix_loops_before_escalation` field" | **显式否定** |
| INTEGRATION.md:61 | "does not automatically escalate ... not in ratchet today" | **显式否定** |
| INTEGRATION.md:71 | yaml 示例字段名 | 字段名 |
| INTEGRATION.md:78 | "Set ratchet's `convergence` to `max_fix_loops_before_escalation`" | 翻译 recipe（动作主体 = user） |
| INTEGRATION.md:81 | "auto-escalation ... needs to be built ... Neither exists yet" | **显式否定** |
| INTEGRATION.md:83 | "§8.4 describes auto-escalation as a desirable property; we explicitly mark it as future work" | **显式否定 + 设计文档承认** |

7 处显式否定 + 4 处字段名 + 1 处翻译 recipe = **0 处正向暗示 ratchet 自动 escalate**。

README pipeline 图（line 38-43）与 ratchet 表格行（line 66）口径一致，且与 INTEGRATION line 60-62 / line 80-82 / plugin.json line 3 跨文档一致。修复合格。

---

## 2. Step 6 设计文档约束 逐项审查（设计文档章节号已校到原文）

### 约束 A — Step 6 由 ratchet 主控（§8.2「ratchet skill（主控）+ claude-code-forge（执行细节）」）

**评级：partial（与 attempt-1 相同；Fixer 未承诺修正这块，残余的不是 P0）。**

- ✓ `plugin.json` line 3、`README.md` line 38-42 + 66、`INTEGRATION.md` line 14-15 三处均说明"`/ratchet` 是 Step 5-6 主控、由 user 手工翻译契约移交"。
- ✗ 两份 SKILL.md 入口面不正面声明此事，只在末尾 next-step 用"hand to `/ratchet`"一笔带过：
  - `acceptance-spec/SKILL.md` line 196：「Suggested next step: `/test-suite-generator <output_dir>/`」（这条根本不指向 ratchet）
  - `test-suite-generator/SKILL.md` line 281：「The next-step suggestion: hand the spec + tests to `/ratchet` as the implementation contract.」（只说"hand to"，不说"ratchet 是 Step 6 主控"）

设计文档 §8.2 把 ratchet 列为 Step 6 主控；当前 README + INTEGRATION 在 Step 5-6 范围内拢着说，没拆 5/6 谁主控。这一刀切不算自相矛盾，但**与 §8.2 的措辞颗粒度有出入**。

**分级 P1-1**（与 attempt-1 同号、同性质，Fixer 显式不动）。

### 约束 B — `spec_drift_threshold` 语义和移交（§8.4 + 附录 C 末段）

**评级：full（attempt-1 partial → attempt-2 full）。**

设计文档附录 C 把 `spec_drift_threshold.max_fix_loops_before_escalation: 3` 列为 done_when.yaml 元信息字段；§8.4 用流程图把它绑成"ratchet 暂停修代码 → 向用户报告 → 退回 Step 2"的触发条件。

attempt-2 后的文档里：

- 字段是**guidance only**：`acceptance-spec/SKILL.md` line 184 "guidance for the human chaining to `/ratchet`, not a contract field anything auto-reads today"
- 翻译路径：`INTEGRATION.md` line 76-79 "Set ratchet's `convergence` to `max_fix_loops_before_escalation`"
- 显式标注 future work：`INTEGRATION.md` line 83 "§8.4 describes auto-escalation as a desirable property; we explicitly mark it as future work"
- schema 严格性：`acceptance-spec/SKILL.md` line 177、`INTEGRATION.md` line 67-68 双向 cross-reference

attempt-1 的 INTEGRATION 错误示例（`applies_to:` 子段）已删，与 SKILL.md 严格 schema 的字面冲突消失。**移交契约现在文档内 100% 口径一致**。

### 约束 C — Spec drift 兜底机制（§8.4 硬性："ratchet 应触发特殊状态... 退回 Step 2"）

**评级：partial（与 attempt-1 相同性质，但口径更稳健）。**

设计文档 §8.4 流程图：「连续 N 轮(建议 N=3)修代码后 PBT 仍失败 → ratchet 暂停修代码 → 向用户报告 → 退回 Step 2」。

当前文档**承认这个机制是 desirable**，但**v0.1 不自动实现**，由 user 手工承担"决定退回与否"的环节。三处声明：

- `README.md` line 39-42（pipeline 图）：用户在 ratchet 停止后"manually decide ... whether to ... go back to /acceptance-spec"
- `README.md` line 59（设计哲学 4）："Spec drift is a first-class failure mode ... Bailout to the clarify loop"
- `INTEGRATION.md` line 79-82："user (not the loop) decides ... 'spec is wrong, go back to /acceptance-spec'"
- `INTEGRATION.md` line 83：明示 §8.4 是 future work

合理性：与设计文档 §8.4 之间是「v0.1 honest scope cut」的关系，不是「broken contract」—— 文档明示了 gap、命名了 gap、给出了 manual workaround、引用了原始设计章节号。不达 P0。

**仍 partial 的原因（attempt-1 同号 P1-1）**：两份 SKILL.md 入口本身不传递这条 mental model；用户先碰到 SKILL.md 时不会自然 internalize "PBT 失败可能是 spec bug"。

→ **改进点 vs attempt-1**：README 表格行 line 66 与 pipeline 图 line 38-42 现在不再与 INTEGRATION line 60-62 主体冲突；触发主体（user）跨文档一致。

### 约束 D — 两种出口：达标归档 / 未达标 fix prompt（§8.3）

**评级：partial（attempt-1 = attempt-2，Fixer 不动 P1-2/P1-3）。**

设计文档 §8.3 明列两种出口的产物：

> (a) 达标 → 归档结束（existence/thresholds/fitness 全过）
> (b) 未达标 → 生成 fix prompt → 回到 Step 5（提取失败诊断 + PBT 最小反例 → fix prompt → 喂给实现 Agent）

当前 skill 文档：

- **达标归档**：两份 SKILL.md + INTEGRATION.md **全部不讲** ratchet 跑完达标后做什么。`INTEGRATION.md` line 56-57 一笔"Ratchet's Step 5 wraps up when its own `done_when` triggers"，把所有归档行为推给 ratchet 内部，不交代 archive / lock spec / PR / close issue。
- **未达标 fix prompt 路径**：`INTEGRATION.md` line 79-82 把所有未达标压缩成 "spec wrong vs code wrong" 二选一；不区分 PBT 失败 / mutation 失败 / e2e 失败的不同处理。
- **PBT 最小反例的传递**：设计文档 §7.4 评估输出里有 `minimal_counterexample` 字段；§8.3 (b) 说要把它带进 fix prompt。当前 skill 文档无任何说明这个反例怎么从评估结果传到下一轮实现。

不达 P0（pipeline 边界外，可推给 ratchet 内部约定），但**与 §8.3 字面要求的覆盖度 < 50%**。

**分级 P1-2 / P1-3**（与 attempt-1 同号、同性质）。

### 约束 E — "PBT 失败 ≠ 代码错"（§12.1.IV）

**评级：yes（attempt-1 yes → attempt-2 yes，跨段主体一致性提升）。**

设计文档 §12.1.IV 原文：

> 很多时候 PBT 找到的反例暴露的是 spec 的 bug,不是代码的 bug
> ratchet 不应自动触发"修代码",应触发"先判断到底谁错了"
> 这是 spec drift 的天然检测器

三处 acknowledge：

- `README.md` line 59 设计哲学 4：「Spec drift is a first-class failure mode. If PBT keeps finding counterexamples after multiple fix attempts, the spec is the bug.」
- `INTEGRATION.md` line 79-82：user 决定 spec wrong vs code wrong
- `test-suite-generator/SKILL.md` line 39 iron rule 7（push back upstream）— 严格说讲的是"生成时"而非"评估时"，但思想同源

attempt-1 时 README 表格行 "ratchet receives the spec-drift escalation signal from PBT" 与 line 59 哲学 4 主体冲突（哲学说"user bailout"，表格暗示"ratchet receives"），attempt-2 表格行（line 66）改写后矛盾消失。**两层都正确**。

---

## 3. 新发现的问题（attempt-1 未列出，attempt-2 新看到）

### N-1 (P2) — `acceptance-spec/SKILL.md` line 196 末尾的 next-step 不指向 ratchet

`acceptance-spec/SKILL.md` line 196：

> Suggested next step: `/test-suite-generator <output_dir>/` (which will turn the contract into the actual test files).

只指向 `/test-suite-generator`，下游的 Step 5-6 (ratchet) 在这里完全没出现。同 skill 内 line 184 已引导用户去 INTEGRATION 读 ratchet 翻译 recipe，但首屏入口（"After writing the four files"）不提 ratchet 这一步。**与 INTEGRATION + README 跨文档不冲突**，只是入口面信息密度低。

**P2**（风格 / 用户体验，不达 P1）。

### N-2 (P2) — `test-suite-generator/SKILL.md` line 281 "implementation contract" 措辞与 INTEGRATION line 21 字面有微张力

- `test-suite-generator/SKILL.md` line 281：「hand the spec + tests to `/ratchet` as **the implementation contract**.」
- `INTEGRATION.md` line 21：「ratchet does **not** parse our `done_when.yaml`. It builds its own `ratchet.md` + `evaluate.sh` from a NL goal.」

"hand X to /ratchet as the implementation contract" 读起来像把 done_when.yaml 直接喂给 ratchet。INTEGRATION 的 handoff recipe（line 26-51）才是事实：user 把 yaml **手工翻译**成 ratchet 的 Goal/Criteria/Scope/done_when 块。SKILL.md line 281 没显式说"翻译"，会让首读用户误以为 yaml 是直接消费的契约。

读完 SKILL.md → INTEGRATION 全文，用户能恢复正确 mental model；但从 next-step 一句话直接跳去用，**有传错信息的风险**。

**P2**（措辞精确度，attempt-1 P0-2 修订的同源 pattern 还在 SKILL.md 残留一点，不达 P1，因为 SKILL.md 没主张"ratchet 自动闭环"也没主张"automatic escalation"，只是省略了 "manually translate"）。

### N-3 (P2) — `INTEGRATION.md` line 60 字段名引用 `spec_drift_threshold.max_fix_loops_before_escalation` 与 line 71 yaml 缩进示例字面一致，但 SKILL.md line 184 称之为 "spec_drift_threshold 块的 max_fix_loops_before_escalation 字段"（口语化）

跨文档对同一字段的 referring expression 略不统一，但不达 P1 — 都能解析。

---

## 4. 与 attempt-1 issue 列表的逐项继承表

| attempt-1 issue | attempt-1 分级 | attempt-2 状态 | 备注 |
|---|---|---|---|
| P0-1 INTEGRATION `applies_to:` 示例 vs SKILL.md schema | P0 | **CLOSED** | 示例删除 + 反向 cross-ref + 禁止说明 三重保险 |
| P0-2 README "receives spec-drift escalation signal" 与 INTEGRATION "does not automatically escalate" 主体矛盾 | P0 | **CLOSED** | pipeline 图 + 表格行重写；4 处字面对齐 |
| P1-1 SKILL.md 入口不讲 Step 6 兜底 mental model | P1 | **PERSIST**（Fixer 显式不动） | 见上 §2-A、§2-C |
| P1-2 达标归档行为未声明 | P1 | **PERSIST** | 见上 §2-D |
| P1-3 未达标 fix prompt 路径 / PBT 最小反例传递未声明 | P1 | **PERSIST** | 见上 §2-D |
| P1-4 `budget: max 15 rounds` 出处不明 | P1 | **PERSIST** | INTEGRATION line 51 仍硬编码 |
| P1-5 `max_fix_loops_before_escalation` 与 ratchet `convergence` 语义不完全等价 | P1 | **PERSIST**（已 acknowledge 但未展开） | INTEGRATION line 78-79 给出映射，未讨论语义差 |
| P1-6 "spec wrong vs code wrong" 可操作判别准则缺失 | P1 | **PERSIST** | INTEGRATION line 79-82 仍只列二分，无判别规则 |

---

## 5. 总结

### P0（必须修）

**无。** 两个 attempt-1 P0 已修复合格，无新 P0。

### P1（应修，本轮 Fixer 显式 out-of-scope）

继承 attempt-1 全部 6 项（P1-1 ~ P1-6），无新增、无降级。

### P2（风格）

- N-1：`acceptance-spec/SKILL.md` line 196 next-step 不指向 ratchet（首屏信息密度低）
- N-2：`test-suite-generator/SKILL.md` line 281 "hand ... as the implementation contract" 没显式说"manually translate"
- N-3：referring expression 跨文档微差异

### attempt 2 状态判定

**Fixer 完成承诺范围内的两条 P0 修复，且未引入新的 P0 或 P1 回归。**

可以进入下一阶段（如继续 iter / 推 P1 / 转其它 Step 审查）。

---

## 附录：实测 grep 证据原文（auditor 独立跑，不沿用 worker 引用）

```bash
$ grep -n "applies_to" plugins/done-when-pipeline/{INTEGRATION,README}.md plugins/done-when-pipeline/skills/{acceptance-spec,test-suite-generator}/SKILL.md
plugins/done-when-pipeline/INTEGRATION.md:74:Do not add `applies_to:` or any other key — strict v1 parsers will reject it. ...
plugins/done-when-pipeline/skills/acceptance-spec/SKILL.md:177:- `spec_drift_threshold:` — exactly one sub-field, `max_fix_loops_before_escalation: <integer>`. Do NOT add `applies_to:` or any other key.

$ grep -nE "escalat|auto-?escalation" plugins/done-when-pipeline/{INTEGRATION,README}.md plugins/done-when-pipeline/skills/{acceptance-spec,test-suite-generator}/SKILL.md
plugins/done-when-pipeline/skills/acceptance-spec/SKILL.md:177:- `spec_drift_threshold:` — exactly one sub-field, `max_fix_loops_before_escalation: <integer>`. ...
plugins/done-when-pipeline/skills/acceptance-spec/SKILL.md:182:  max_fix_loops_before_escalation: 3
plugins/done-when-pipeline/skills/acceptance-spec/SKILL.md:184:This is **guidance for the human chaining to `/ratchet`** ... Auto-escalation is future work; do not promise the user it happens automatically.
plugins/done-when-pipeline/README.md:39:   spec-drift bailout: after `max_fix_loops_before_escalation` (default 3) rounds
plugins/done-when-pipeline/README.md:42:   No auto-escalation in v0.1.
plugins/done-when-pipeline/README.md:66:| `ratchet` | ... There is **no auto-escalation** of "PBT failures look like spec bugs" in v0.1; ...
plugins/done-when-pipeline/INTEGRATION.md:60:- It does not honor a `spec_drift_threshold.max_fix_loops_before_escalation` field from our YAML.
plugins/done-when-pipeline/INTEGRATION.md:61:- It does not automatically escalate "PBT failures look like spec bugs, not code bugs" back to the user — that escalation logic is not in ratchet today.
plugins/done-when-pipeline/INTEGRATION.md:71:  max_fix_loops_before_escalation: 3
plugins/done-when-pipeline/INTEGRATION.md:78:- Set ratchet's `convergence` to `max_fix_loops_before_escalation` (here: 3 rounds with no improvement → stop).
plugins/done-when-pipeline/INTEGRATION.md:81:If you want auto-escalation, that needs to be built ...
plugins/done-when-pipeline/INTEGRATION.md:83:(The source design doc §8.4 describes auto-escalation as a desirable property; we explicitly mark it as future work.)

$ grep -nE "oracle|consume" plugins/done-when-pipeline/{INTEGRATION,README}.md
plugins/done-when-pipeline/README.md:68:| (no packaged fitness-judge skill exists yet) | Step 4-F rubric files are consumed manually by a fresh Claude session ...
plugins/done-when-pipeline/INTEGRATION.md:22:- persona-judge does **not** consume our fitness rubric files. ...
plugins/done-when-pipeline/INTEGRATION.md:91:So Step 4-F as designed has no packaged consumer in this marketplace today. ...
```

`oracle` 在所有 4 个文档 0 次命中。`consume(s)` 3 次命中，全部 **non-ratchet** 上下文（讲 persona-judge 不 consume / fitness rubric manually consumed by fresh session / fitness has no packaged consumer），无 "ratchet consumes done_when.yaml" 残留。
