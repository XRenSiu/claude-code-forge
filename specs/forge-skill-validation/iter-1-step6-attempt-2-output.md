# Step 6 Worker 产出 — iter-1-step6-attempt-2

## 任务说明

本 attempt 在 Fixer 已对 `INTEGRATION.md` 和 `README.md` 做完 P0 修改后，**重新**审查 Step 6（闭环迭代）的边界声明 / spec_drift_threshold 移交契约 / spec drift 兜底机制 / 两种出口 / "PBT 失败 ≠ 代码错" 设计哲学。

判断口径同 attempt-1，但所有文件**重新从磁盘读取**，**不**沿用 attempt-1 缓存的行号 / 引文。

---

## 已检查文件清单（重读后的现状）

| 文件 | 用途 | 关键行号（attempt-2 重读后） |
|---|---|---|
| `plugins/done-when-pipeline/skills/acceptance-spec/SKILL.md` | iron rules / S3 写 `done_when.yaml` `spec_drift_threshold:` 子段的硬规则 + guidance 注释 | iron rule 6（line 41）；schema "Hard rules for v1 字面" → `spec_drift_threshold` 段（line 177）；S3 内嵌示例 + guidance 段（line 180-184）；S3 末尾 next-step（line 196） |
| `plugins/done-when-pipeline/skills/test-suite-generator/SKILL.md` | 4-A 到 4-F 输出 + "After all six sub-steps" 末尾 hand-off | iron rule 1（line 33，"verifiable beats judgeable"，PBT 优先）；iron rule 7（line 39，"No inventing requirements"，生成时 push back upstream，但仍**不涉及** Step 6 闭环回路）；line 277-283 "After all six sub-steps" 块；line 281 "next-step suggestion: hand the spec + tests to `/ratchet`" |
| `plugins/done-when-pipeline/INTEGRATION.md` | Pipeline 边界 + ratchet handoff recipe + spec drift guidance 整节（**Fixer 改过 P0-1**） | line 11-18 边界图；line 26-51 ratchet handoff recipe；line 58-62 "What ratchet does NOT do"；line 65-84 "Spec drift guidance (not auto-honored)" 整节（**新版**，`applies_to:` 示例已删，加了 cross-reference 段）；line 80-82 "user (not the loop) decides ... spec is wrong, go back to /acceptance-spec" |
| `plugins/done-when-pipeline/README.md` | 顶层 pipeline 图 + 设计哲学第 4 条 + ratchet 表格行 + Version 段落（**Fixer 改过 P0-2**） | line 38-43 pipeline 图最后一节（**新版**，"user hands ... to /ratchet"，含 `max_fix_loops_before_escalation` 翻译说明 + "No auto-escalation in v0.1"）；line 58 设计哲学 4 "Spec drift is a first-class failure mode"；line 66 ratchet 表格行（**新版**，明确 "no auto-escalation" + "user decides"）；line 93 Version "hand off **manually**" |
| `plugins/done-when-pipeline/.claude-plugin/plugin.json` | description 中 Step 5/6 移交声明 | line 3 "Step 5 execution and Step 6 ratchet feedback loop hand off MANUALLY — the user invokes /ratchet with translated Goal/Criteria/Scope; ratchet does not parse done_when.yaml directly."（**未变**） |
| `specs/forge-skill-validation/iter-1-step3-attempt-2-artifacts/done_when.yaml` | 实际 Step 3 产物中 `spec_drift_threshold` 块（参考） | line 121-128（含说明性注释 "Guidance only — ratchet does not auto-read this; see INTEGRATION.md to translate into ratchet's `convergence` value when chaining."） |

---

## attempt-1 P0 修复验证

### P0-1：`INTEGRATION.md` `spec_drift_threshold` 示例不再含 `applies_to:`

**结果：消除。**

**证据 1（INTEGRATION.md 当前文本，line 65-84 整节）：**

- Line 69-72 新版示例 yaml：
  ```yaml
  spec_drift_threshold:
    max_fix_loops_before_escalation: 3
  ```
  仅一个子字段，**没有** `applies_to:`，与 `acceptance-spec/SKILL.md` line 177 严格 schema 一致。
- Line 67-68 新增 schema 权威出处的 cross-reference：
  > "Per the v1 schema, it has **exactly one** sub-field (see `skills/acceptance-spec/SKILL.md` § "Hard rules for v1 字面" and `references/done-when-schema.yaml`)"
- Line 74 新增正向禁止 + 解释：
  > "Do not add `applies_to:` or any other key — strict v1 parsers will reject it. The threshold applies uniformly to *any* test failure category that keeps repeating across fix loops (PBT, mutation, e2e); v1 does not let you scope it per-category."

**证据 2（grep `applies_to` 跨文档检索）：**

```bash
$ grep -n "applies_to" plugins/done-when-pipeline/{INTEGRATION.md,README.md,skills/acceptance-spec/SKILL.md}
skills/acceptance-spec/SKILL.md:177:- `spec_drift_threshold:` ... Do NOT add `applies_to:` or any other key.
INTEGRATION.md:74:Do not add `applies_to:` or any other key — strict v1 parsers will reject it. ...
```

两处 `applies_to:` 残留 100% 是 "Do NOT" / "Do not" 形式（禁止语境），无示例残留。

**判定：P0-1 完全消除**。读 INTEGRATION.md 的人不会再看到 `applies_to:` 示例，因此不会模仿写错 contract。下游消费者（acceptance-spec 生成的 yaml）此前就遵循 SKILL.md 严格 schema，本次只是把对外文档与生成端口径校齐。

### P0-2：`README.md` 不再暗示 ratchet 自动 escalate

**结果：消除。**

**证据 1（README.md pipeline 图，attempt-1 line 38-39 → attempt-2 line 38-43）：**

旧版（attempt-1 引用，已不存在）：
```
ratchet  ─── consumes done_when.yaml as the kill/restart/done oracle (Step 5-6)
   spec-drift bailout: PBT failing >=3 rounds escalates back to clarify
```

新版（当前 README line 38-42）：
```
ratchet  ─── user hands done_when.yaml to /ratchet as the acceptance contract (Step 5-6)
   spec-drift bailout: after `max_fix_loops_before_escalation` (default 3) rounds
   with no improvement, ratchet's `convergence` stops the loop; the user then
   decides manually whether to re-run /ratchet or go back to /acceptance-spec.
   No auto-escalation in v0.1.
```

四处关键修订：
1. "consumes done_when.yaml" → "user hands done_when.yaml to /ratchet" —— 显式手工移交；
2. "kill/restart/done oracle" 措辞删除 —— 不再暗示 ratchet 自动 parse；
3. "PBT failing >=3 rounds escalates back to clarify" → "ratchet's `convergence` stops the loop; the user then decides manually" —— 触发主体改成用户；
4. 新增 "No auto-escalation in v0.1." —— 显式与 INTEGRATION line 61 / line 81 / line 83 立场对齐。

**证据 2（README.md ratchet 表格行，attempt-1 line 63 → attempt-2 line 66）：**

旧版（attempt-1 引用）：
> "ratchet ... Consumes `done_when.yaml` as its acceptance contract; runs the master/subagent kill-and-restart loop; **receives the spec-drift escalation signal from PBT**."

新版（当前 line 66）：
> "ratchet ... Step 5-6 main controller. The user **manually** translates our `done_when.yaml` into a `/ratchet` invocation (Goal / Criteria / Scope / done_when block) — ratchet does not parse our YAML directly. Ratchet then runs its master/subagent kill-and-restart loop. There is **no auto-escalation** of \"PBT failures look like spec bugs\" in v0.1; after ratchet's `convergence` stops the loop, the user decides whether to re-invoke `/ratchet` or go back to `/acceptance-spec`. See `INTEGRATION.md` for the handoff recipe."

三处关键修订：
1. "receives the spec-drift escalation signal from PBT" —— **完全删除**（attempt-1 P0-2 核心冲突）；
2. "Consumes `done_when.yaml`" → "The user **manually** translates our `done_when.yaml` into a `/ratchet` invocation" —— 与 INTEGRATION line 21 一致；
3. 显式 "no auto-escalation" + "user decides" —— 与 INTEGRATION line 80-82 字面一致；末尾指回 INTEGRATION 作权威 recipe。

**证据 3（grep "escalation" / "escalate" 跨文档检索）：**

```bash
$ grep -nE "escalat|auto-?escalation|escalation signal" plugins/done-when-pipeline/{INTEGRATION.md,README.md}
README.md:39:   spec-drift bailout: after `max_fix_loops_before_escalation` (default 3) rounds
README.md:42:   No auto-escalation in v0.1.
README.md:66:| `ratchet` | ... There is **no auto-escalation** of "PBT failures look like spec bugs" in v0.1; ...
INTEGRATION.md:60:- It does not honor a `spec_drift_threshold.max_fix_loops_before_escalation` field from our YAML.
INTEGRATION.md:61:- It does not automatically escalate "PBT failures look like spec bugs, not code bugs" back to the user ...
INTEGRATION.md:71:  max_fix_loops_before_escalation: 3
INTEGRATION.md:78:- Set ratchet's `convergence` to `max_fix_loops_before_escalation` (here: 3 rounds with no improvement → stop).
INTEGRATION.md:81:If you want auto-escalation, that needs to be built either ...
INTEGRATION.md:83:(The source design doc §8.4 describes auto-escalation as a desirable property; we explicitly mark it as future work.)
```

7 处 "escalation / escalate" 残留：5 处显式否定立场（"no auto-escalation" / "does not automatically escalate" / "does not honor" / "future work"），2 处是字段名 `max_fix_loops_before_escalation` 本身（无评价语义）。**0 处**残留旧版 "receives ... escalation signal" 之类正向暗示。

**判定：P0-2 完全消除**。README 不再有任何一处暗示 ratchet 自己能 detect spec drift 或自动 escalate。pipeline 图、表格行、Version 三处口径全部与 INTEGRATION.md 对齐。

---

## 重填的 Step 6 边界声明检查表（5 项）

### 1. Step 6 由 ratchet 主控声明

**是否声明：partial → full**（attempt-1 partial，attempt-2 升为 full）

新版 README 与 INTEGRATION 在三处全部说"用户手工把 Goal/Criteria/Scope 翻译给 ratchet"，不再有自相矛盾的"ratchet 自动 oracle"措辞：

- `plugin.json` line 3（**未变**）："Step 5 execution and Step 6 ratchet feedback loop hand off MANUALLY — the user invokes /ratchet with translated Goal/Criteria/Scope; ratchet does not parse done_when.yaml directly."
- `README.md` line 38-42（**新版** pipeline 图）："user hands done_when.yaml to /ratchet as the acceptance contract (Step 5-6) ... No auto-escalation in v0.1."
- `README.md` line 66（**新版**表格行）：明确 "user **manually** translates" + "ratchet does not parse our YAML directly" + "no auto-escalation"。
- `INTEGRATION.md` line 14-15 + line 26-51：handoff recipe 完整可贴。
- `INTEGRATION.md` line 58-62 "What ratchet does NOT do"：撤回所有暗示自动闭环的措辞（与 attempt-1 相同）。

**遗留**：两个 SKILL.md 自身依然只在 next-step 提到 `/ratchet`（acceptance-spec line 196；test-suite-generator line 281），不正面声明 "Step 6 由 ratchet 主控"。这是 P1-1 范畴，Fixer 显式不修。

### 2. spec_drift_threshold 语义和移交

**`max_fix_loops_before_escalation` 是给 ratchet 消费的吗？仅 guidance？**

**仅 guidance（人类参考）。** 与 attempt-1 同。文档无任何工具自动读这个字段。

**新版引片段（attempt-2 重读后的关键句）：**

- `acceptance-spec/SKILL.md` line 184（**未变**）：
  > "This is **guidance for the human chaining to `/ratchet`**, not a contract field anything auto-reads today. When chaining, translate `max_fix_loops_before_escalation` into ratchet's own `convergence` value (see `done-when-pipeline/INTEGRATION.md` for the recipe). Auto-escalation is future work; do not promise the user it happens automatically."

- `acceptance-spec/SKILL.md` line 177（**未变**）schema 硬规则：
  > "`spec_drift_threshold:` — exactly one sub-field, `max_fix_loops_before_escalation: <integer>`. Do NOT add `applies_to:` or any other key."

- `INTEGRATION.md` line 65-84（**新版**整节）—— attempt-1 中含 `applies_to:` 示例的旧版被替换为：
  - line 67-68 显式 cross-reference 到 SKILL.md schema 段；
  - line 69-72 示例只保留 `max_fix_loops_before_escalation: 3`；
  - line 74 显式禁止 `applies_to:` + 解释 v1 不分类的设计原因；
  - line 76-79 翻译 recipe（"Set ratchet's `convergence` to `max_fix_loops_before_escalation`"）；
  - line 80-82 "user (not the loop) decides ... spec is wrong, go back to /acceptance-spec"。

- `INTEGRATION.md` line 60：
  > "It does not honor a `spec_drift_threshold.max_fix_loops_before_escalation` field from our YAML."

- 本次 Step 3 产物 `iter-1-step3-attempt-2-artifacts/done_when.yaml` line 121-128（**未变**）：
  > "Guidance only — ratchet does not auto-read this; see INTEGRATION.md to translate into ratchet's `convergence` value when chaining."

**skill 是否告诉用户怎么把这个值传给 ratchet？**

是。`INTEGRATION.md` line 41-51（handoff 模板）+ line 76-79（翻译规则）+ `acceptance-spec/SKILL.md` line 184（让生成端指向 INTEGRATION）三处冗余覆盖。**新版**还在 INTEGRATION line 67-68 加了反向 cross-reference（→ SKILL.md schema 段 + done-when-schema.yaml），形成 SKILL ↔ INTEGRATION 双向引用闭环。

→ **改进点**：attempt-1 时 INTEGRATION 示例与 SKILL.md schema 自相矛盾，attempt-2 已消除。**移交契约现在文档内 100% 口径一致**。

### 3. Spec drift 兜底机制（PBT 持续失败 → 退回 Step 2）

**是否声明：partial → partial**（attempt-1 partial，attempt-2 仍 partial）

声明存在，且**比 attempt-1 更一致**：

- `README.md` line 38-42（**新版**）pipeline 图增至 5 行，显式 "user decides manually whether to re-run /ratchet or go back to /acceptance-spec" + "No auto-escalation in v0.1"。attempt-1 时这里是单行 "PBT failing >=3 rounds escalates back to clarify"（措辞太强）。
- `README.md` line 58（设计哲学 4，**未变**）：
  > "**Spec drift is a first-class failure mode.** If PBT keeps finding counterexamples after multiple fix attempts, the spec is the bug. Bailout to the clarify loop, do not pile on more code patches."
- `README.md` line 66（**新版**表格行）：明确 "no auto-escalation" + "user decides"。attempt-1 时这一行写 "receives the spec-drift escalation signal from PBT"（与 INTEGRATION 直接矛盾）。
- `INTEGRATION.md` line 60-62（**未变**）：撤回 ratchet auto-escalate 能力。
- `INTEGRATION.md` line 80-82（**未变**）：给 user 二选一指引（spec wrong vs code wrong）。
- `INTEGRATION.md` line 81-83（**未变**）：auto-escalation 是 future work。

**仍 partial 的原因**：两份 SKILL.md 依然不正面讲此机制（P1-1）。`test-suite-generator/SKILL.md` line 39 iron rule 7 只讲生成时 push back upstream，不讲 Step 6 闭环回路。Fixer 显式不修 P1。

→ **改进点**：README/INTEGRATION 之间的字面冲突（attempt-1 P0-2 的实质）消除；触发主体（user）、触发动作（manual decide）、兜底动作（回 /acceptance-spec）三处描述跨文档一致。

### 4. 两种出口（达标 / 未达标）

**是否说清楚：partial → partial**（attempt-1 partial，attempt-2 仍 partial）

无变化。本次 Fixer 不修 P1-2 / P1-3。

- **达标归档**：两个 SKILL.md + INTEGRATION.md 均不讲 ratchet 跑完达标后做什么（archive / lock spec / PR / close issue 全部未提）。`INTEGRATION.md` line 56-57 只说 "Ratchet's Step 5 wraps up when its own `done_when` triggers" —— 把所有归档动作推给 ratchet 内部。
- **未达标 fix prompt 路径**：`INTEGRATION.md` line 80-82 把所有未达标压缩成 "spec wrong vs code wrong" 二分；不区分 PBT 失败 / mutation 失败 / e2e 失败的不同 fix 流程。

→ **改进点**：无；P1 范畴。

### 5. PBT 失败 ≠ 代码错的设计哲学

**是否 acknowledge：yes → yes**（attempt-1 yes，attempt-2 yes）

无降级。三处声明无变化：

- `README.md` line 58（设计哲学 4）："Spec drift is a first-class failure mode."（未变）
- `INTEGRATION.md` line 80-82：user 决定 spec wrong vs code wrong。（未变）
- `test-suite-generator/SKILL.md` line 39 iron rule 7：生成时 push back upstream，源于同一思想但不在 Step 6 上下文。（未变）

**实质上更稳健**：attempt-1 时 README 表格行 "ratchet receives ... escalation signal from PBT" 与设计哲学 4 自相矛盾 —— 哲学说 "user bailout to clarify loop"，表格暗示 "ratchet receives signal"，主体错乱。attempt-2 表格行改写后，"主体始终是 user" 的口径在 README 内部统一。

→ **改进点**：跨段落主体一致性提升，从 "哲学层正确 + 表格层错主体" 变成 "两层都正确"。

---

## 与 attempt-1 相比的修正（diff 摘要）

### INTEGRATION.md 行号 diff

| 关注点 | attempt-1 引用 | attempt-2 实际 | 措辞变化 |
|---|---|---|---|
| `spec_drift_threshold` 示例 | line 67-75（含 `applies_to:` 二级字段） | line 67-72（**只剩** `max_fix_loops_before_escalation: 3`） | 删 4 行（`applies_to:` + 两个示例条目 + 空行）；增 2 行（line 67-68 cross-reference "Per the v1 schema, it has exactly one sub-field"） |
| schema 出处反向引用 | 无 | line 67-68 新增（"see `skills/acceptance-spec/SKILL.md` § 'Hard rules for v1 字面' and `references/done-when-schema.yaml`"） | 新增 |
| `applies_to:` 禁止说明 | 无 | line 74 新增（"Do not add `applies_to:` or any other key — strict v1 parsers will reject it ..."） | 新增 |
| 其他段落（"What ratchet does NOT do" line 58-62、"Spec drift guidance" 后半 line 76-84、handoff recipe line 26-51） | 同 attempt-1 | **未变** | — |

整节 line 范围从 attempt-1 的 65-84 → attempt-2 的 65-84（数字范围相同，但内容重组）。本次 INTEGRATION.md 总长度 145 行，与 attempt-1 相同（删 4 增 4）。

### README.md 行号 diff

| 关注点 | attempt-1 引用 | attempt-2 实际 | 措辞变化 |
|---|---|---|---|
| Pipeline 图 ratchet 段 | line 38-39（2 行："consumes ... oracle" + "PBT failing >=3 rounds escalates back to clarify"） | line 38-42（**5 行**："user hands ... to /ratchet" + 3 行 manual decide 说明 + "No auto-escalation in v0.1"） | "consumes" → "user hands"；"oracle" 删除；"escalates back" → "user then decides manually" + "go back to /acceptance-spec"；新增 "No auto-escalation in v0.1" |
| 设计哲学 4 行号 | line 56 | line 58（行号 +2，因 pipeline 图扩张 3 行） | 内容**未变** |
| ratchet 表格行 | line 63（"Consumes ... acceptance contract ... **receives the spec-drift escalation signal from PBT**"） | line 66（行号 +3；"user **manually** translates ... ratchet does not parse our YAML directly ... **no auto-escalation** ... user decides whether to re-invoke /ratchet or go back to /acceptance-spec ... See `INTEGRATION.md`"） | 删 "receives ... escalation signal from PBT"；增 manual translate / 不 parse / no auto-escalation / user decide / cross-reference 至 INTEGRATION |
| Version 段 | line 90 | line 93（行号 +3） | 内容**未变** |
| 第二个 ratchet 表格行（fitness 行）相邻段 | line 65 | line 68 | 内容**未变** |

README.md 总长度从 attempt-1 推测的 ~92 行 → attempt-2 的 94 行（净增 +2 行，pipeline 图扩张 3 行被其他段缩进重排吸收）。

### 检查表各项分级 diff

| 检查项 | attempt-1 评级 | attempt-2 评级 | 变化原因 |
|---|---|---|---|
| 1. Step 6 由 ratchet 主控声明 | partial | **full** | README pipeline 图 + 表格行不再有自动闭环暗示；与 plugin.json / INTEGRATION 跨文档完全口径一致 |
| 2. spec_drift_threshold 语义和移交 | 明确（手工翻译） | **明确，文档内 100% 一致** | INTEGRATION 示例已删 `applies_to:`，与 SKILL.md schema 不再矛盾；新增 INTEGRATION ↔ SKILL.md 双向 cross-reference |
| 3. Spec drift 兜底机制 | partial | **partial（但跨文档一致性提升）** | README 表格行 + pipeline 图与 INTEGRATION 立场对齐；SKILL.md 仍不讲（P1） |
| 4. 两种出口（达标 / 未达标） | partial | **partial（无变化）** | Fixer 不修 P1-2 / P1-3 |
| 5. PBT 失败 ≠ 代码错 | yes | **yes（主体一致性提升）** | README 内部不再有 "表格说 ratchet receives signal、哲学说 user bailout" 的主体矛盾 |

---

## attempt-2 残余冲突 / 文档间一致性核查

### 检查 1：`applies_to:` 跨文档残留

```bash
$ grep -n "applies_to" plugins/done-when-pipeline/{INTEGRATION.md,README.md,skills/acceptance-spec/SKILL.md,skills/test-suite-generator/SKILL.md}
SKILL.md (acceptance-spec):177:- `spec_drift_threshold:` ... Do NOT add `applies_to:` or any other key.
INTEGRATION.md:74:Do not add `applies_to:` or any other key — strict v1 parsers will reject it ...
```

**结论**：2 处残留 100% 是 "Do NOT / Do not" 形式（禁止语境），0 处示例残留。无冲突。

### 检查 2：ratchet 自动闭环 / escalation 跨文档残留

```bash
$ grep -nE "escalat|auto-?escalation" plugins/done-when-pipeline/{INTEGRATION.md,README.md}
README.md:39:   spec-drift bailout: after `max_fix_loops_before_escalation` (default 3) rounds
README.md:42:   No auto-escalation in v0.1.
README.md:66:... There is **no auto-escalation** of "PBT failures look like spec bugs" in v0.1 ...
INTEGRATION.md:60:- It does not honor a `spec_drift_threshold.max_fix_loops_before_escalation` field ...
INTEGRATION.md:61:- It does not automatically escalate ... that escalation logic is not in ratchet today.
INTEGRATION.md:71:  max_fix_loops_before_escalation: 3
INTEGRATION.md:78:- Set ratchet's `convergence` to `max_fix_loops_before_escalation` (here: 3 rounds ...).
INTEGRATION.md:81:If you want auto-escalation, that needs to be built ...
INTEGRATION.md:83:(... §8.4 describes auto-escalation as a desirable property; we explicitly mark it as future work.)
```

**结论**：9 处残留分布 = 5 处显式否定立场（no auto-escalation / does not automatically escalate / does not honor / future work / future work）+ 4 处字段名 `max_fix_loops_before_escalation` 本身（无评价语义）。**0 处**残留正向暗示 ratchet 自动 escalate。无冲突。

### 检查 3："consume(s)" / "oracle" 在 ratchet 上下文残留

```bash
$ grep -n "consume" plugins/done-when-pipeline/{INTEGRATION.md,README.md}
INTEGRATION.md:22:- persona-judge does **not** consume our fitness rubric files. ...
```

**结论**：1 处残留是 "persona-judge does **not** consume"（否定语境，且讲的是 persona-judge 而非 ratchet）。**0 处**残留 "ratchet consumes done_when.yaml" 之类暧昧措辞。无冲突。

```bash
$ grep -n "oracle" plugins/done-when-pipeline/
（无返回）
```

"kill/restart/done oracle" 措辞完全清除。

### 检查 4：SKILL.md 与 INTEGRATION.md / README.md cross-reference 闭环

- `acceptance-spec/SKILL.md` line 184 → 指向 `done-when-pipeline/INTEGRATION.md`（spec_drift_threshold 翻译 recipe）✓
- `INTEGRATION.md` line 67-68（新版）→ 指向 `skills/acceptance-spec/SKILL.md` § "Hard rules for v1 字面" + `references/done-when-schema.yaml`（schema 权威出处）✓
- `README.md` line 66（新版）→ 指向 `INTEGRATION.md`（handoff recipe）✓

三处 cross-reference 形成闭环，attempt-1 时 SKILL.md → INTEGRATION 单向，INTEGRATION 内有错误示例无反向引用。**改进**。

---

## skill 是否提供足够上下文让 ratchet 跑通 Step 6？

**结论同 attempt-1（充分）**，但跨文档一致性提升后，runner 现在不会因 README 与 INTEGRATION 矛盾而困惑：

- (a) 完成判定 / P0 criteria / thresholds：`done_when.yaml` 提供 + `INTEGRATION.md` line 36-50 翻译成 ratchet 模板 ✓
- (b) budget 与 convergence：`spec_drift_threshold.max_fix_loops_before_escalation: 3` → ratchet `convergence: 3 ...`（`INTEGRATION.md` line 76-79）✓
- (c) 兜底动作：`INTEGRATION.md` line 80-82 给 user 二选一指引 ✓；**新版** README pipeline 图 line 41 + 表格行 line 66 重复声明，user 不再会从 README "ratchet receives spec-drift signal" 误判触发主体 ✓

**遗留 gap（无变化，P1）**：

1. `budget: max 15 rounds` 出处依然不明（INTEGRATION.md line 51 硬编码，无文档支撑）—— attempt-1 P1-4。
2. `max_fix_loops_before_escalation` 与 ratchet `convergence` 语义不完全等价（前者暗示 escalate 后者只是 stop）—— attempt-1 P1-5；新版 README 已 acknowledge "user then decides manually" 但未在数值映射上展开。
3. "spec wrong vs code wrong" 可操作判别准则缺失 —— attempt-1 P1-6。
4. SKILL.md 自身仍不讲 Step 6 兜底机制 —— attempt-1 P1-1。
5. 达标归档 / 未达标细分 fix 流程未声明 —— attempt-1 P1-2 / P1-3。

---

## 总评（attempt-1 → attempt-2）

**Step 6 边界处理整体水位：attempt-1 "低于 Step 5" → attempt-2 "接近 Step 5"。**

**核心改善**：

1. **文档内自相矛盾的两个 P0 完全消除** —— INTEGRATION `applies_to:` 示例 vs SKILL.md 严格 schema（P0-1）+ README ratchet "receives escalation signal" vs INTEGRATION "does not automatically escalate"（P0-2）。
2. **README 措辞主体一致性提升** —— pipeline 图、表格行、设计哲学 4、Version 段四处全部把 "Step 6 触发主体 = user manual"" 作为统一基调，与 INTEGRATION + plugin.json 跨文档对齐。
3. **跨文档 cross-reference 闭环** —— SKILL.md ↔ INTEGRATION ↔ README 三角引用，schema 权威出处可被任一入口追溯。

**最大遗留**（与 attempt-1 一致，本次 Fixer 显式不动）：

- 两个 SKILL.md 入口面**不**承担 Step 6 兜底 mental model 的传递责任；用户被 skill 工具调用时（SKILL.md 是默认入口），仍要主动去读 README / INTEGRATION 才能 internalize "PBT 失败可能是 spec bug" 这条原则。该改进属于内容增量（P1-1），不在 P0 修复范围。

**spec_drift_threshold 移交契约 attempt-2 状态**：值的翻译路径（yaml → ratchet `convergence`）声明清晰、有可贴 recipe、SKILL ↔ INTEGRATION 双向 cross-reference 闭环；触发动作（PBT 持续失败后做什么）由 README pipeline 图 + 设计哲学 4 + INTEGRATION 二分指引共三处冗余覆盖，且**主体口径**（user 而非 ratchet）跨文档完全一致。
