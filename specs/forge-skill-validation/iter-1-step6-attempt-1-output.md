# Step 6 Worker 产出 — iter-1-step6-attempt-1

## 任务说明

本 Step 验证 `acceptance-spec` 和 `test-suite-generator` 两个 skill 对 **Step 6（闭环迭代）** 的边界声明、`spec_drift_threshold` 的移交契约、以及 "PBT 持续失败 → 退回 Step 2 重新澄清需求" 这条 spec drift 兜底机制是否被显式、可被 ratchet 消费地交付。**不**审查 skill 是否真正去驱动 ratchet 闭环（那是 ratchet 自己的事），也**不**重复 Step 5 Worker 已审查的命令 / 阈值 / 退出语义层面。

---

## 已检查文件清单

| 文件 | 用途 | 关键行号 |
|---|---|---|
| `plugins/done-when-pipeline/skills/acceptance-spec/SKILL.md` | iron rules / S3 `done_when.yaml` 的 `spec_drift_threshold:` 写法 + guidance 注释 | iron rule 6（line 41）；`spec_drift_threshold:` 段（line 177、line 180-184）；guidance 注释（line 184）；S3 末尾 next-step（line 196） |
| `plugins/done-when-pipeline/skills/test-suite-generator/SKILL.md` | 4-A 到 4-F 输出 + "After all six sub-steps" 末尾 hand-off | iron rule 1（line 33，"verifiable beats judgeable"，PBT 优先于 judge）；line 277-283 "After all six sub-steps" 块；line 281 "next-step suggestion: hand the spec + tests to `/ratchet` as the implementation contract" |
| `plugins/done-when-pipeline/INTEGRATION.md` | "Pipeline boundaries (honest version)" + "Spec drift guidance (not auto-honored)" 整节 + 与 ratchet 的边界陈述 | line 11-18 边界图；line 26-51 ratchet handoff recipe；line 58-62 "What ratchet does NOT do"；line 66-84 "Spec drift guidance" 整节；line 80-82 "user (not the loop) decides ... spec is wrong, go back to /acceptance-spec" |
| `plugins/done-when-pipeline/README.md` | 顶层 pipeline 图 + 设计哲学第 4 条 + Version 段落 | line 38（"ratchet ... consumes done_when.yaml as the kill/restart/done oracle (Step 5-6)"）；line 39（"spec-drift bailout: PBT failing >=3 rounds escalates back to clarify"）；line 56（设计哲学第 4 条 "Spec drift is a first-class failure mode"）；line 63（表格中 "ratchet ... receives the spec-drift escalation signal from PBT"）；line 90（Version 中 Step 5/6 hand off MANUALLY） |
| `plugins/done-when-pipeline/.claude-plugin/plugin.json` | description 中 Step 5/6 移交声明 | line 3 中段 "Step 5 execution and Step 6 ratchet feedback loop hand off MANUALLY — the user invokes /ratchet with translated Goal/Criteria/Scope; ratchet does not parse done_when.yaml directly." |
| `specs/forge-skill-validation/iter-1-step3-attempt-2-artifacts/done_when.yaml` | 实际 Step 3 产物中 `spec_drift_threshold` 块 | line 121-128（含说明性注释 "Guidance only — ratchet does not auto-read this; see INTEGRATION.md to translate into ratchet's `convergence` value when chaining."） |
| `specs/forge-skill-validation/iter-1-step5-attempt-1-output.md` | Step 5 Worker 已审 hand-off 内容（避免重复） | line 5、line 16-18、line 31-110、line 248-250 |

---

## 边界声明检查

### 1. Step 6 由 ratchet 主控声明

**是否声明：partial**

四份 plugin 文档对 "Step 6 谁负责" 的措辞不完全一致：

- `plugin.json` (line 3) 是最干净的——明确说 "Step 5 execution and Step 6 ratchet feedback loop hand off MANUALLY — the user invokes /ratchet with translated Goal/Criteria/Scope; ratchet does not parse done_when.yaml directly."
- `README.md` line 38 在 pipeline 图里写 "ratchet — consumes done_when.yaml as the kill/restart/done oracle (Step 5-6)"——但下一行 line 39 又说 "spec-drift bailout: PBT failing >=3 rounds escalates back to clarify"。读 ASCII 图的人会把 ratchet 当成 Step 5-6 的自动 oracle。
- `README.md` line 63 表格中 "ratchet ... Step 5-6 main controller. Consumes `done_when.yaml` as its acceptance contract"——同样的措辞，会让人误以为 ratchet 直接读 yaml。
- `INTEGRATION.md` line 58-62 在 "What ratchet does NOT do" 中显式撤回：
  > "It does not parse our `done_when.yaml` directly. It does not honor a `spec_drift_threshold.max_fix_loops_before_escalation` field from our YAML. It does not automatically escalate 'PBT failures look like spec bugs, not code bugs' back to the user — that escalation logic is not in ratchet today."

→ "ratchet 是 Step 6 主控" 这个 claim 在 README 和表格里是简化的口号；在 INTEGRATION.md 才被矫正成 "用户手工把 Goal/Criteria/Scope 翻译过去，ratchet 用自己的 done_when 块跑自己的闭环"。读者必须读到 INTEGRATION.md 才能拿到准确语义。

skill SKILL.md 本身（acceptance-spec / test-suite-generator）几乎不直接谈 Step 6 ratchet 闭环——只在 next-step 提示中说 "hand off to /ratchet"（acceptance-spec line 196；test-suite-generator line 281），没有 spelling out "Step 6 由 ratchet 主控" 这个分工。

### 2. spec_drift_threshold 语义和移交

**`max_fix_loops_before_escalation` 是给 ratchet 消费的吗？仅 guidance？**

**仅 guidance（人类参考）。** skill 文档**没有**让任何工具自动读这个字段。

**引片段：**

- `acceptance-spec/SKILL.md` line 180-184（在 S3 写 `done_when.yaml` 的 `spec_drift_threshold` 子段后）：
  > "This is **guidance for the human chaining to `/ratchet`**, not a contract field anything auto-reads today. When chaining, translate `max_fix_loops_before_escalation` into ratchet's own `convergence` value (see `done-when-pipeline/INTEGRATION.md` for the recipe). Auto-escalation is future work; do not promise the user it happens automatically."

- `acceptance-spec/SKILL.md` line 177（schema 硬规则）：
  > "`spec_drift_threshold:` — exactly one sub-field, `max_fix_loops_before_escalation: <integer>`. Do NOT add `applies_to:` or any other key."
  ——schema 严格成单字段，明显是 "人读后翻译" 而非 "结构化解析" 设计。

- `INTEGRATION.md` line 60：
  > "It does not honor a `spec_drift_threshold.max_fix_loops_before_escalation` field from our YAML."

- `INTEGRATION.md` line 77-82（"Spec drift guidance (not auto-honored)"）整节：
  > "**This is guidance for the human composing the `/ratchet` invocation**, not a contract field anything reads automatically. Concretely, when chaining to ratchet, translate it as: Set ratchet's `convergence` to `max_fix_loops_before_escalation` (here: 3 rounds with no improvement → stop). After ratchet stops, the user (not the loop) decides whether the failure means 'spec is wrong, go back to /acceptance-spec' or 'code is wrong, re-invoke /ratchet with more budget'."

- 本次 Step 3 产物 `iter-1-step3-attempt-2-artifacts/done_when.yaml` line 122-125（acceptance-spec 自己生成的 yaml 注释也复述了这一点）：
  > "Guidance only — ratchet does not auto-read this; see INTEGRATION.md to translate into ratchet's `convergence` value when chaining."

**skill 是否告诉用户怎么把这个值传给 ratchet？**

是。`INTEGRATION.md` line 80-82 + line 41-51 给出了**可贴的 ratchet 调用模板**，其中 `convergence: 3 consecutive rounds with no new test passing` 直接对应 yaml 里 `max_fix_loops_before_escalation: 3`。`acceptance-spec/SKILL.md` line 184 显式让生成端把这个 mapping 指向 INTEGRATION.md。

→ 移交契约**明确**：人工翻译、用 INTEGRATION.md 当 recipe 表、ratchet 的 `convergence` 字段是着陆点。**没**有 dressing-up 成自动行为。

### 3. Spec drift 兜底机制（PBT 持续失败 → 退回 Step 2）

**是否声明：partial**

声明存在，但**仅在 README 和 INTEGRATION**，且 INTEGRATION 显式说这是手工动作不是自动逻辑。两个 skill 的 SKILL.md 都**不**直接讲 "PBT 持续失败应回到 Step 2 重新澄清"。

**引片段：**

- `README.md` line 39（pipeline 图最后一行）：
  > "spec-drift bailout: PBT failing >=3 rounds escalates back to clarify"
  ——单行图注，没说 "由谁触发"、"escalate 到 acceptance-spec 还是给人提示"。

- `README.md` line 56（设计哲学 4）：
  > "**Spec drift is a first-class failure mode.** If PBT keeps finding counterexamples after multiple fix attempts, the spec is the bug. Bailout to the clarify loop, do not pile on more code patches."
  ——philosophy 级声明，但没说 "落地路径"。

- `README.md` line 63 表格：
  > "ratchet ... receives the spec-drift escalation signal from PBT."
  ——这一行**比实际能力强**，会让读者以为 ratchet 自己会 detect。

- `INTEGRATION.md` line 60-62 显式撤回上面的话术：
  > "It does not automatically escalate 'PBT failures look like spec bugs, not code bugs' back to the user — that escalation logic is not in ratchet today."

- `INTEGRATION.md` line 80-82 给出 manual 路径：
  > "After ratchet stops, the user (not the loop) decides whether the failure means 'spec is wrong, go back to /acceptance-spec' or 'code is wrong, re-invoke /ratchet with more budget'."

- `INTEGRATION.md` line 82-84 把 auto-escalation 标注成 future work：
  > "If you want auto-escalation, that needs to be built either (a) as a wrapper skill around ratchet that reads our `spec_drift_threshold:` and post-processes ratchet's exit, or (b) as a modification inside ratchet itself. Neither exists yet; do not promise the user this behavior."

- 两份 SKILL.md：**搜不到**任何 "PBT keep failing → go back to acceptance-spec" / "spec drift → Step 2 重新澄清需求" 的措辞。`test-suite-generator/SKILL.md` line 39 iron rule 7 ("No inventing requirements") 说 "push back upstream"，但讲的是**生成时**，不是 **Step 6 运行后**。

→ 兜底机制**有声明**但层级是 README/INTEGRATION 而非 skill 本体；其中 README pipeline 图含一句**容易被误读为自动**的话（line 63 "receives the spec-drift escalation signal from PBT"），由 INTEGRATION.md 在更下游显式校正。

### 4. 两种出口（达标 / 未达标）

**是否说清楚：partial**

- **达标归档** 这条 exit 几乎**没有**显式声明。两个 SKILL.md 都不告诉用户 "ratchet exit 0 后该归档什么、归档到哪、谁来 close PR"。`INTEGRATION.md` line 56-57 只说 "Ratchet's Step 5 wraps up when its own `done_when` triggers"——把 "wrap up" 后的归档动作全推给 ratchet。
- **未达标生成 fix prompt 回到 Step 5** 这条 exit 在 skill 文档里**没有**被分得这么细。`INTEGRATION.md` line 80-82 把所有 "未达标" 情况压缩成两类（"spec is wrong" → 回 /acceptance-spec；"code is wrong" → 重新 /ratchet with more budget），没区分 "PBT 失败 vs mutation 失败 vs e2e 失败" 是否走不同的 fix 流程。
- `test-suite-generator/SKILL.md` line 281 next-step：
  > "The next-step suggestion: hand the spec + tests to `/ratchet` as the implementation contract."
  ——只讲入口，不讲出口。

**引片段（最接近的两种出口描述）：**

- `INTEGRATION.md` line 80-82：
  > "After ratchet stops, the user (not the loop) decides whether the failure means 'spec is wrong, go back to /acceptance-spec' or 'code is wrong, re-invoke /ratchet with more budget'."

这是文档中**唯一**把两种"未达标走向"显式区分的句子。"达标"走向（归档 / close PR / 锁 spec / 删 implementer scratch）几乎不在文档中。

→ 仅 "未达标的两个分支" 被显式列出，"达标归档" 路径**未声明**。

### 5. PBT 失败 ≠ 代码错的设计哲学

**是否 acknowledge：yes**

`README.md` line 56（设计哲学 4）直白承认：

> "**Spec drift is a first-class failure mode.** If PBT keeps finding counterexamples after multiple fix attempts, the spec is the bug. Bailout to the clarify loop, do not pile on more code patches."

`INTEGRATION.md` line 80-82 同句话的运行时翻译：

> "the user (not the loop) decides whether the failure means 'spec is wrong, go back to /acceptance-spec' or 'code is wrong, re-invoke /ratchet with more budget'."

`test-suite-generator/SKILL.md` line 39 iron rule 7（不在 Step 6 上下文，但同源思想）：

> "If a property occurs to you that isn't in any REQ, **do not** add a test for it. Either push back upstream ('REQ-NNN seems to imply X — should that be a separate REQ?') or skip it."

→ 设计哲学这条**清晰、多文档冗余声明**。是 Step 6 边界处理中**最强**的一项。

---

## skill 是否提供足够上下文让 ratchet 跑通 Step 6？

**(done_when.yaml + Step 4 产物 + skill 文档作为输入)**

**充分性评估：**

- ratchet 跑 Step 6 需要的输入：(a) 一个"什么算完成"的判定（P0 criteria + thresholds），(b) 一个"什么时候放弃"的 budget，(c) 一个"放弃后怎么办"的指引。
- (a) skill **充分**提供：`done_when.yaml` 里 `behavior.thresholds` 四个固定键（unit_coverage, integration_coverage, mutation_kill_rate, pbt_runs_per_property）+ `INTEGRATION.md` line 36-50 把它们翻译成 ratchet 的 P0 criteria（直接可贴）。
- (b) skill **充分**提供：`spec_drift_threshold.max_fix_loops_before_escalation: 3` → ratchet 的 `convergence: 3 consecutive rounds with no new test passing`（`INTEGRATION.md` line 80-82）；ratchet 模板还显式带 `budget: max 15 rounds`（line 51），这是 skill **自己加的**默认值，不在 yaml 里。
- (c) skill **部分**提供：line 80-82 给的 "spec wrong vs code wrong" 二分指引是手工 decision tree，没给 ratchet 一个机器可读的 "PBT 失败 N 轮后 emit signal=spec_drift" 流程。

**关键 gap（事实陈述）：**

1. **`budget: 15 rounds` 出处不明：** `INTEGRATION.md` line 51 在 ratchet 模板里硬编码 `budget: max 15 rounds`。这个 15 不来自 `done_when.yaml`（yaml 里只有 `max_fix_loops_before_escalation: 3` 和 four thresholds），也不来自任何 SKILL.md 推导。runner 直接贴模板会拿到这个 15，但**没文档解释为什么**是 15 而不是 10 或 20。
2. **`max_fix_loops_before_escalation` 与 ratchet `convergence` 的语义不完全等价：** yaml 字段名是 "max fix loops **before escalation**"——暗示阈值后会**升级**（escalate）；ratchet 的 `convergence` 是"连续 N 轮无新测试通过即停"——语义是**停止**而非**升级**。两者数值上都是 3，但 ratchet stop 后**没有任何机制**触发 "escalate back to acceptance-spec"——那一步全靠 user 主动判断。这是 `INTEGRATION.md` line 80-82 已 acknowledge 的 gap，但 skill 没给"用户怎么决定 spec wrong vs code wrong"的判别准则（要看 PBT 反例的内容？看 mutation 哪个 mutant 漏杀？看 e2e 哪一步失败？skill 都不讲）。
3. **"Step 4 产物 + done_when.yaml" 对 ratchet 已够，但 ratchet 闭环结束后的归档动作未定义。** 见上一节。

→ 给 ratchet 启动 Step 6 闭环**够用**；让 ratchet 的失败结果回流到 acceptance-spec 重新 clarify 的路径**只能靠人工**，skill 文档承认这一点（INTEGRATION line 80-84）。

---

## 边界声明的一致性

**与 Step 5 Worker 已审查的边界声明不重复，专注 Step 6 特有内容：**

Step 5 Worker（iter-1-step5-attempt-1-output.md）已核对：(a) "Step 5 manual to ratchet" 在四份文档的一致性、(b) ratchet handoff recipe 的完整性、(c) fitness 4-F 的手工方案。本 Step 6 Worker 关注的是**Step 6 特有的三件事**：

### a. "PBT 失败暴露 spec bug" 的声明一致性

| 文档 | 是否提 | 措辞 |
|---|---|---|
| `plugin.json` description | no | description 中说 "PBT closes the reward-hacking loop because the agent cannot predict Hypothesis/fast-check inputs at write time"——讲 PBT 的**反作弊价值**，不讲 PBT 失败可能暴露 spec bug |
| `README.md` | yes | line 56 设计哲学 4：明确说 spec is the bug |
| `README.md` pipeline 图 | yes | line 39 "spec-drift bailout: PBT failing >=3 rounds escalates back to clarify" |
| `INTEGRATION.md` | yes | line 80-82 给 "spec wrong vs code wrong" 二选一指引 |
| `acceptance-spec/SKILL.md` | **no** | SKILL.md 通篇不讲 Step 6 / PBT failure / spec drift 应对路径 |
| `test-suite-generator/SKILL.md` | partial | iron rule 7（line 39）讲生成时的 "push back upstream"，但不直接讲 Step 6 PBT 失败后的回路 |

**一致性问题：** 两个 SKILL.md 自身**不**承担"提醒用户 PBT 失败可能是 spec bug 而非 code bug"的责任。用户如果只读 SKILL.md（这是被 skill 调用时的默认入口），完全不会接触到这条原则。必须读到 README 设计哲学或 INTEGRATION line 80-82 才能 internalize 这个 mental model。

### b. `spec_drift_threshold` 语义在五份文档的统一性

| 文档 | `spec_drift_threshold` 的定位 |
|---|---|
| `acceptance-spec/SKILL.md` line 180-184 | "guidance for the human chaining to `/ratchet`, not a contract field" |
| `INTEGRATION.md` line 77 | "guidance for the human composing the `/ratchet` invocation, not a contract field anything reads automatically" |
| `INTEGRATION.md` line 60 | "ratchet does not honor a `spec_drift_threshold.max_fix_loops_before_escalation` field from our YAML" |
| done_when.yaml schema reference（acceptance-spec line 177） | 严格 "exactly one sub-field, `max_fix_loops_before_escalation: <integer>`" |
| 本 Step 3 产物 done_when.yaml line 122-125 | yaml 注释 "Guidance only — ratchet does not auto-read this" |
| `README.md` | **没有**提 spec_drift_threshold 这个字段名 |
| `plugin.json` description | **没有**提 spec_drift_threshold 这个字段名 |
| `test-suite-generator/SKILL.md` | **没有**提 spec_drift_threshold 这个字段名 |

**一致性问题：** 知道 `spec_drift_threshold` 是 guidance-only 的人，必须读 `acceptance-spec/SKILL.md` 或 `INTEGRATION.md`。如果用户只读 README 或 plugin.json 看 plugin 概览，看不到这个字段名，也不知道 yaml 里有这一段。这本身不是 bug（README 是高层文档），但意味着 yaml 字段是否被翻译进 ratchet 这件事**没有顶层指引**——只能从 `INTEGRATION.md` 撞见。

### c. README pipeline 图的"自动 oracle"措辞

`README.md` line 38 在 pipeline 图：
> "ratchet ─── consumes done_when.yaml as the kill/restart/done oracle (Step 5-6)"

`README.md` line 63 表格：
> "ratchet ... Consumes `done_when.yaml` as its acceptance contract"

这两处措辞**形式上**与 INTEGRATION.md line 58-62 "It does not parse our `done_when.yaml` directly" **冲突**——前者说"consume"，后者说"不 parse"。

仔细看，README 用的是英语模糊词 "consume / acceptance contract"，可以被解读为 "把 yaml 内容作为输入（即使是人工读完手工翻译）"；INTEGRATION 说的是 "not parse directly"（结构化解析）。两者**技术上**可以共存，但**字面**上一定会让首次读 README 的人形成"ratchet 自动读 yaml"的错误预期，要等到 INTEGRATION.md 才会修正。

Step 5 Worker 已就 INTEGRATION.md 的 honest disclaimer 部分给过好评（iter-1-step5-attempt-1-output.md line 47、line 250），但**没**指出 README 措辞与 INTEGRATION 措辞的字面差异——本 Step 6 Worker 补充记录。

---

## skill 指令模糊点（事实陈述）

1. **"PBT 失败 ≠ 代码错" 不在 skill 入口面：** acceptance-spec/SKILL.md 和 test-suite-generator/SKILL.md 都不讲这条 mental model。用户只读 SKILL.md（被 skill 调用时的默认入口）时接触不到。该原则仅在 README.md 设计哲学第 4 条 + INTEGRATION.md spec drift guidance 中存在。

2. **"达标归档" 路径未定义：** Step 6 闭环达标后应该做什么——锁定 spec？归档 tests？提 PR？close issue？skill 文档全部未声明，全部 deferred to ratchet 或用户。`test-suite-generator/SKILL.md` line 277-283 "After all six sub-steps" 块也只讲生成完的 next-step 是 `/ratchet`，不讲 ratchet 跑完之后干什么。

3. **`spec_drift_threshold` 的 `applies_to:` 子字段历史遗留：** acceptance-spec/SKILL.md line 177 严格规定 "exactly one sub-field, `max_fix_loops_before_escalation: <integer>`. Do NOT add `applies_to:`"——但 `INTEGRATION.md` line 67-75 在解释 spec_drift_threshold 时**带了一个示例**写着：
   ```yaml
   spec_drift_threshold:
     max_fix_loops_before_escalation: 3
     applies_to:
       - mutation_kill_rate
       - property_based_failure
   ```
   这个 `applies_to:` 与 SKILL.md 的严格 schema **冲突**。读 INTEGRATION 的人会以为 `applies_to:` 合法；读 SKILL.md 的人知道它非法。这是文档内不一致，记录为事实。（注：本 Step 3 产物的 done_when.yaml 正确遵循 SKILL.md，**没**写 `applies_to:`——所以**生成端**是对的，**INTEGRATION 文档示例**是错的。）

4. **`budget: max 15 rounds` 出处不明：** INTEGRATION.md line 51 ratchet handoff 模板硬编码 `budget: max 15 rounds`，但 done_when.yaml schema 没有 budget 字段，SKILL.md 没解释 15 的来源。这是 skill 给 ratchet 凭空多塞的一个值。

5. **"PBT 失败 → 退回 Step 2 重新澄清" 的触发点未定：** README line 39 写 "escalates back to clarify"，但没说**谁**做这个 escalate（ratchet？user？wrapper skill？）。INTEGRATION.md line 80-82 澄清是 user 做。两份文档不冲突但层级跳跃——README 简化、INTEGRATION 修正。

6. **"PBT 失败暴露 spec bug" 的识别准则未给：** 用户被告知"PBT 反复失败可能是 spec bug"，但 skill 没给可操作的判别（如：看 PBT 反例输入是否在 spec 已定义边界内？看反例与 EARS 句的 trigger 是否对应？看 mutation 哪个 mutant 漏杀？）。判别全靠用户 ad hoc。

7. **Step 6 的两个出口未在 SKILL.md 入口面说明：** 两个 SKILL.md 都不讲 "Step 6 跑完后会有两种结果"。该信息只在 INTEGRATION.md line 80-82。

8. **README 表格 line 63 措辞"receives the spec-drift escalation signal from PBT"过强：** ratchet 实际**不接收**任何 spec-drift signal——INTEGRATION.md line 60-62 自己说的。表格行措辞与 INTEGRATION 矛盾。这是 README 的宣传话术与 INTEGRATION 的 honest disclaimer 之间的张力。

---

## 总评

**Step 6 边界处理的整体水位低于 Step 5。**

- Step 5 边界处理：四份文档**冗余声明**手工 hand-off + INTEGRATION 给完整可贴 recipe + skill SKILL.md 末尾给明确 next-step。
- Step 6 边界处理：核心原则（spec drift / PBT 失败可能是 spec bug / 闭环交给 ratchet）**只在 README 和 INTEGRATION** 出现，**两个 SKILL.md 自身不承担传递这些原则的责任**；ratchet 跑完后的"两种出口"只在 INTEGRATION.md 出现一次；README 措辞（line 38 / line 63）字面让人以为 ratchet 自动闭环，要靠 INTEGRATION.md 撤回。

**spec_drift_threshold 的移交契约**：值的**翻译路径**（yaml → ratchet `convergence`）声明清晰、有可贴 recipe；但**触发动作**（PBT 持续失败后做什么）声明只在两处（README 设计哲学 + INTEGRATION 二分指引），且 INTEGRATION 自己承认这是 user manual decision、非自动机制。

**最大缺失**：两个 SKILL.md 入口面不讲 Step 6 的兜底机制，用户调用 skill 时拿不到这个 mental model。
