# Step 6 Auditor 报告 — iter-1-step6-attempt-1

> 独立审查 Worker 在 Step 6（闭环迭代）的产出，只挑刺，不修复。
> 审查范围：**第八章 8.1-8.4** + **第九章 角色分工总览**。
> 审查口径：两个 skill 不实现 Step 6，而是 hand off 到 `/ratchet`。审查焦点是**边界声明完整性**和**spec drift 兜底机制的移交契约**。

---

## 一、设计文档要求清单 + 满足情况

| # | 设计文档要求（章节号 / 原文） | 满足情况 | 证据 / Gap |
|---|---|---|---|
| R1 | **§8.1**："ratchet 消费 Step 5 的评估结果,对照 done_when.yaml 判定:完成,或继续迭代。" — Step 6 由 ratchet 主控判定 | 满足（in INTEGRATION），**SKILL.md 自身仅给"next-step 提示"** | `INTEGRATION.md` line 14-15 + `plugin.json` line 3 + `README.md` line 38 / 63 都声明 ratchet 是 Step 5-6 主控；两个 SKILL.md 只在末尾 next-step 提到 `/ratchet`（acceptance-spec line 196；test-suite-generator line 281） |
| R2 | **§8.2**：角色表 — 主控 `ratchet` + `claude-code-forge`；输入 = Step 5 评估结果 + done_when.yaml | 满足 | `INTEGRATION.md` line 12-18 + line 26-51 给完整 handoff recipe（Goal / Criteria / Scope / done_when 块） |
| R3 | **§8.3 (a)**：达标 → 归档结束（所有 existence pass / 所有阈值满足 / 所有 fitness 满足） | **未声明** | 两个 SKILL.md 均不讲"达标后应做什么"。`INTEGRATION.md` line 56-57 只说 "Ratchet's Step 5 wraps up when its own `done_when` triggers"——把归档动作全推给 ratchet 内部。skill 文档不讲 archive / lock spec / PR / close issue 中的任何一个 |
| R4 | **§8.3 (b)**：未达标 → 提取失败诊断 + PBT 最小反例 → 生成 fix prompt → 喂给实现 Agent | 部分声明 | `INTEGRATION.md` line 80-82 只把所有 "未达标" 压缩成"spec is wrong vs code is wrong"二分；不区分 PBT / mutation / e2e 失败的不同 fix 路径。"PBT 最小反例的提取" 这一步在 skill 文档完全未提（属于 ratchet 内部职责） |
| R5 | **§8.4 (核心硬性)**：Spec drift 兜底机制 — 连续 N 轮（建议 N=3）修代码后 PBT 仍失败 → ratchet 暂停 → 向用户报告 → 退回 Step 2 重新澄清需求 | 部分声明 | `README.md` line 39 / line 56 / line 63 + `INTEGRATION.md` line 65-84 都讲了此机制（含 N=3 默认值、退回 /acceptance-spec 路径、auto-escalation 是 future work）；**两个 SKILL.md 自身均不讲**——用户调 skill 时拿不到这条 mental model |
| R6 | **§8.4 配套**：skill 应该声明 `spec_drift_threshold.max_fix_loops_before_escalation: N` 字段（值 3 是设计文档建议） | 满足 | `acceptance-spec/SKILL.md` line 177 + line 180-184（严格 schema：exactly one sub-field）；本 Step 3 产物 done_when.yaml line 127-128（值=3） |
| R7 | **§8.4 配套**：skill 应该告诉用户怎么把这个值传给 ratchet | 满足 | `acceptance-spec/SKILL.md` line 184 + `INTEGRATION.md` line 77-82：明确翻译为 ratchet `convergence: 3 consecutive rounds with no improvement → stop`；line 41-51 给可贴模板 |
| R8 | **§8.4 配套**：acknowledge "代码或 spec 任一有 bug 的信号" 的双向语义 | 满足（仅 README + INTEGRATION） | `README.md` line 56（设计哲学 4 "Spec drift is a first-class failure mode"）+ `INTEGRATION.md` line 80-82（"spec wrong vs code wrong" 二选一）。两个 SKILL.md 不讲 |
| R9 | **§12.1 (IV)**：PBT 失败 ≠ 代码错。skill 文档应 acknowledge | 满足（仅 README + INTEGRATION） | 同 R8。两个 SKILL.md 不讲此 mental model |
| R10 | **§9 角色总览**：人类（你）"偶尔 Step 6（spec drift 兜底）" | 满足 | `INTEGRATION.md` line 80-82 显式：user (not the loop) decides spec wrong vs code wrong |

---

## 二、按 P0 / P1 / P2 分级

### P0（必须修：移交完全缺失 / 文档内自相矛盾导致 broken contract / 8.4 完全未提）

#### P0-1：`INTEGRATION.md` 中 `spec_drift_threshold` 示例与 `acceptance-spec/SKILL.md` 严格 schema 冲突

- **冲突位置**：
  - `INTEGRATION.md` line 67-75 在 "Spec drift guidance" 整节给的示例 yaml：
    ```yaml
    spec_drift_threshold:
      max_fix_loops_before_escalation: 3
      applies_to:
        - mutation_kill_rate
        - property_based_failure
    ```
  - `acceptance-spec/SKILL.md` line 177 严格规定：
    > "`spec_drift_threshold:` — exactly one sub-field, `max_fix_loops_before_escalation: <integer>`. **Do NOT add `applies_to:` or any other key.**"
- **判定**：用户先读 INTEGRATION.md 学这个字段语义 → 然后写 done_when.yaml 时，会模仿 INTEGRATION 示例带上 `applies_to:` → 但 SKILL.md 又禁止。**文档内自相矛盾会导致用户写错 contract**。
- **澄清**：本次 Step 3 产物（`iter-1-step3-attempt-2-artifacts/done_when.yaml` line 127-128）正确遵循了 SKILL.md，**没有** `applies_to:`——所以**生成端**当前能产出合规 yaml；**对外文档**有错。但下次用户绕开 acceptance-spec 直接写 yaml 时会踩坑。
- **设计文档援引**：§8.4 规范了 `max_fix_loops_before_escalation: N` 的字段名义，未规范 `applies_to:` 子字段——后者是 plugin 文档自己加的。

#### P0-2：`README.md` "ratchet receives the spec-drift escalation signal from PBT" 与 INTEGRATION.md 矛盾

- **冲突位置**：
  - `README.md` line 63 表格：
    > "ratchet ... Step 5-6 main controller. Consumes `done_when.yaml` as its acceptance contract; runs the master/subagent kill-and-restart loop; **receives the spec-drift escalation signal from PBT**."
  - `INTEGRATION.md` line 60-62 "What ratchet does NOT do"：
    > "It does not automatically escalate 'PBT failures look like spec bugs, not code bugs' back to the user — that escalation logic is not in ratchet today."
- **判定**：README 表格行措辞**比实际能力强**——"receives the spec-drift escalation signal from PBT"会让读者以为 ratchet 自己会 detect。INTEGRATION 才校正"该 escalation logic 当前不存在"。**文档内自相矛盾会让用户对 spec drift 兜底机制产生错误预期**——而这恰是 §8.4 要求 skill 文档完整声明的部分。
- **设计文档援引**：§8.4 "ratchet 应触发特殊状态:连续 N 轮... ratchet 暂停修代码... 向用户报告"——README 措辞暗示这是 ratchet 当前能力，INTEGRATION 撤回。

### P1（移交在但粗糙 / 8.3 某出口缺 / 措辞与硬约束有歧义但不破坏可执行）

#### P1-1：Spec drift 兜底机制（§8.4 硬性）在两个 SKILL.md 自身完全不出现

- **位置**：
  - `acceptance-spec/SKILL.md` 通篇无 "PBT failure / spec drift / 退回 Step 2" 措辞
  - `test-suite-generator/SKILL.md` 通篇无（line 39 iron rule 7 讲"生成时 push back upstream"，**不是** Step 6 运行后回路）
- **判定**：按审查口径指引——"如果 INTEGRATION.md 是 skill 包的官方对外文档，且它讲了这个机制，那 SKILL.md 自身不讲只是文档分布问题，记 P1"——本案 INTEGRATION.md line 65-84 整节"Spec drift guidance"已讲清楚，`README.md` line 39 / line 56 也讲了。**SKILL.md 不讲是文档分布缺陷而非契约缺失**，记 P1。
- **影响**：用户被 skill 工具调用时，默认入口是 SKILL.md。若用户没读 INTEGRATION.md 或 README.md，跑完 Step 1-4 后**完全不知道**还有 spec drift 兜底原则——只会一直让 ratchet 修代码。
- **设计文档援引**：§8.4 "skill 文档应该 acknowledge 这条兜底原则"——满足了，但只在 README/INTEGRATION 满足，未在 SKILL.md 入口面满足。

#### P1-2：达标出口（§8.3 (a)）未声明

- **位置**：两个 SKILL.md + INTEGRATION.md 均不讲"ratchet 跑完达标后做什么"（archive / lock spec / PR / close issue 全部未提）
- **判定**：按审查口径指引——"达标出口（archive / lock / PR）是 ratchet 内部职责而非 skill 职责，skill 不讲不算违反设计文档对 skill 的要求"——记 P1（介于"对 skill 没强制"和"用户会困惑"之间）。
- **设计文档援引**：§8.3 (a) "达标 → 归档结束"——是对 **ratchet** 的要求，不是对 acceptance-spec / test-suite-generator 的要求。所以 skill 不讲不算违 8.3，但 hand-off 文档若能 cover 这块更好。

#### P1-3：未达标出口（§8.3 (b)）的细分缺失

- **位置**：`INTEGRATION.md` line 80-82 把所有 "未达标" 压缩成"spec is wrong vs code is wrong"二分，没区分：
  - PBT 失败 vs mutation kill 失败 vs e2e 失败 是否走不同的 fix 流程？
  - "PBT 最小反例的提取"（§8.3 (b) 明确要求）由谁做？skill / ratchet / user？
- **判定**：skill 不讲细分不算违反对 skill 的要求（这是 ratchet 内部职责），但 hand-off 契约的"未达标该回到哪一步"语义不细，记 P1。
- **设计文档援引**：§8.3 (b) "提取失败诊断 + PBT 最小反例 → 生成 fix prompt"。

#### P1-4：`budget: max 15 rounds` 出处不明

- **位置**：`INTEGRATION.md` line 51 ratchet handoff 模板硬编码 `budget: max 15 rounds`
- **冲突**：`done_when.yaml` schema 没有 budget 字段；SKILL.md 没解释 15 的来源
- **判定**：skill 自己往 ratchet 模板里塞了一个无文档支撑的默认值。设计文档 §8.3 不规范 budget；此值只是 ratchet 协议的字段。属于"模板字段值未论证"——粗糙但不破坏可执行。记 P1。

#### P1-5：`max_fix_loops_before_escalation` 与 ratchet `convergence` 语义不完全等价

- **位置**：yaml 字段名是 "max fix loops **before escalation**"（暗示 escalate）；ratchet 的 `convergence` 是"连续 N 轮无新测试通过即停"（停止，不升级）
- **判定**：两者数值都是 3，但 ratchet 停了**没有任何机制**触发 "escalate back to acceptance-spec"——靠 user 主动判断。`INTEGRATION.md` line 80-84 已 acknowledge 此 gap 并标注 auto-escalation 是 future work。**已 acknowledge 的 gap，且不影响当前手工流程可执行**。记 P1。
- **设计文档援引**：§8.4 "ratchet 暂停修代码 → 向用户报告"——当前 INTEGRATION 实现 = "ratchet 停 → user 判断 → user 可能回 /acceptance-spec"；语义一致，但触发路径 user-manual 而非 auto。

#### P1-6：判别 "spec wrong vs code wrong" 的可操作准则缺失

- **位置**：`INTEGRATION.md` line 80-82 让 user 决定"spec is wrong"还是"code is wrong"，但没给可操作判别（如：看 PBT 反例输入是否在 spec 边界内？看反例与 EARS 句的 trigger 是否对应？看 mutation 哪个 mutant 漏杀？）
- **判定**：判别准则缺失会让 user 在 spec drift 触发后 ad hoc 决策。skill 不给准则**不违反**设计文档（§8.4 只要求"向用户报告"，不要求 skill 给 user 判别准则），但移交契约粗糙。记 P1。

### P2（风格 / 冗余）

#### P2-1：`README.md` line 38 pipeline 图措辞 "consumes done_when.yaml as the kill/restart/done oracle" 与 INTEGRATION.md "does not parse our done_when.yaml directly" 字面冲突

- **位置**：
  - `README.md` line 38：`ratchet ─── consumes done_when.yaml as the kill/restart/done oracle (Step 5-6)`
  - `INTEGRATION.md` line 21：`ratchet does **not** parse our done_when.yaml. It builds its own ratchet.md + evaluate.sh from a NL goal.`
- **判定**：技术上可共存（"consume" 可指人工读完手工翻译；"parse" 指结构化解析）。**字面上**会让首次读 README 的人形成"ratchet 自动读 yaml"的错误预期。这是宣传话术 vs honest disclaimer 的张力，但 INTEGRATION.md 会撤回。记 P2（与 P0-2 的区别：line 38 措辞 "consume" 较 line 63 "receives the spec-drift escalation signal" 更模糊，可被善意解读；line 63 措辞则明显超出实际能力）。

#### P2-2：`spec_drift_threshold` 字段名在 README + plugin.json 未出现

- **位置**：`README.md` 全文 / `plugin.json` description 全文均不提 `spec_drift_threshold` 字段名
- **判定**：README / plugin.json 是高层文档，不必讲 yaml 字段细节。不违反设计文档。记 P2。

#### P2-3：两个 SKILL.md 不引 §8.4 / §12.1 第 IV 条认知措辞

- **位置**：两个 SKILL.md 不出现 "PBT 失败 ≠ 代码错" 或同义表述
- **判定**：是 P1-1 的子项（同一根因——SKILL.md 不传 mental model）。不另记。

---

## 三、计数

| 等级 | 计数 |
|---|---|
| **P0** | 2 |
| **P1** | 6 |
| **P2** | 3 |
| **合计** | 11 |

---

## 四、关键判定汇总（按审查指引明示）

| Worker 提的疑问 | 审查指引判定 | Auditor 结论 |
|---|---|---|
| Spec drift 兜底机制只在 README + INTEGRATION 出现，两个 SKILL.md 自身不讲——P0 还是 P1？ | "如果 INTEGRATION.md 是 skill 包的官方对外文档，且它讲了这个机制，那 SKILL.md 自身不讲只是文档分布问题，记 P1；如果连 INTEGRATION 都不讲，记 P0" | **P1**（INTEGRATION.md line 65-84 整节讲清楚了；README line 39 / 56 / 63 也讲了。SKILL.md 不讲是文档分布问题）→ **P1-1** |
| §8.3 (a) 达标出口未声明——P0 还是 P1？ | "达标出口（archive / lock / PR）是 ratchet 内部职责而非 skill 职责，skill 不讲不算违反设计文档对 skill 的要求。记 P1 或 P2" | **P1**（hand-off 契约粗糙但 skill 没强制责任）→ **P1-2** |
| INTEGRATION.md `applies_to:` 示例 vs SKILL.md schema 冲突——P0 还是 P1？ | "文档自相矛盾是合规问题，记 P0（因为这会让用户写错 contract）" | **P0**（自相矛盾导致 broken contract）→ **P0-1** |

---

## 五、Worker 产出整体水位评估

Worker 报告**事实陈述准确**，引证行号经抽查全部对位。覆盖面相对设计文档 §8.1-8.4 + §9 + §12.1 (IV) 完整。**Worker 漏的关键点**（本 Auditor 补）：

1. **Worker 未将 INTEGRATION.md line 67-75 的 `applies_to:` 示例升级为 P0**——Worker 第 220-228 行只记为"事实陈述"，未分级。Auditor 按审查指引判定为 **P0-1**（自相矛盾导致 broken contract）。
2. **Worker 未将 README line 63 "receives the spec-drift escalation signal from PBT" 单独升级为 P0**——Worker 在"边界声明的一致性"段（line 198-210）记录了 README vs INTEGRATION 措辞冲突，但只在"事实陈述"层面，未分级。Auditor 按"文档自相矛盾会让用户对 spec drift 兜底机制产生错误预期"判为 **P0-2**。

Worker 其余分析与 Auditor 判定一致。

---

## 六、设计文档原文对照（备查）

- **§8.1**："ratchet 消费 Step 5 的评估结果,对照 done_when.yaml 判定:完成,或继续迭代。"
- **§8.2**：主控=ratchet+claude-code-forge；输入=Step 5 评估结果+done_when.yaml；输出=两种之一
- **§8.3 (a)**："达标 → 归档结束" + 三个 sub-条件（existence pass / 阈值满足 / fitness 满足）
- **§8.3 (b)**："未达标 → 生成 fix prompt → 回到 Step 5" + 三个动作（提取失败诊断 / PBT 最小反例 / 喂给实现 Agent）
- **§8.4**："连续 N 轮(建议 N=3)修代码后 PBT 仍失败 → ratchet 暂停修代码 → 向用户报告 → 退回 Step 2 让用户重新澄清需求"
- **§8.4 结尾**："这种机制把 PBT 失败从'代码 bug 信号'扩展成了'代码或 spec 任一有 bug 的信号'"
- **§9**：人类 "偶尔 Step 6（spec drift 兜底）"；ratchet+forge "Step 5, 6（主控）"
- **§12.1 (IV)**：PBT 失败 ≠ 代码错
