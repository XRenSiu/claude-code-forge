# Step 5 Auditor 审查 — iter-1-step5-attempt-1

**审查范围**:只看 Step 5(执行评估)边界声明完整性 + 移交契约可执行性。**严格不越界到 Step 4 或 Step 6**。
**审查对象**:Worker 产出 `iter-1-step5-attempt-1-output.md`。
**审查依据**:设计文档 `done-when-pipeline.md` 第七章 7.1-7.5、第九章角色分工总览。

---

## 一、设计文档要求清单 + 满足情况

| # | 设计文档来源 | 要求 | Worker 是否覆盖 | 覆盖位置 |
|---|---|---|---|---|
| R1 | 7.1 | 声明 Step 5 目标是"跑测试 + 收集证据",所有验证物已经写好 | yes(隐含) | output 任务说明段 + 第 4 节 4-A/B/C/D 逐 layer 跑通分析 |
| R2 | **7.2 硬性** | 显式声明"做的 Agent 和判的 Agent 必须分离" | yes(且引片证据) | output 第 4 节(README.md line 9-13、fitness rubric line 16-18、INTEGRATION.md line 94-95) |
| R3 | 7.2 | 处理"同 session 自我合理化"风险 | partial | output 第 4 节"强制机制层面:partial / 约定式而非工具式"——诚实承认 fitness 层只能靠约定,前 4 层因 runner 与 implementer 天然分离而成立 |
| R4 | 7.3 | 明确 Step 5 输入 = Step 4 全部验证物 + 实现代码 | yes | output 第 4 节列出 existence.sh / unit/ / integration/ / e2e/ / mutation.sh / fitness/ 五类验证物,且陈述"实现代码尚未写,脚本当下一定红——红是契约预期"(契合 spec §7.3 把"实现代码"列为输入) |
| R5 | 7.3 | 明确 Step 5 输出 = 评估结果汇总 | partial | output 第 3 节明确说 "evaluation_result schema 没定义",并把汇总职责推给 ratchet 的 evaluate.sh;审查口径上 Worker 已识别这是"边界声明"问题,但未引设计文档 7.4 schema 原文作为对照 |
| R6 | **7.4 硬性 schema** | evaluation_result 结构含 feature / timestamp / existence / unit_tests / integration_tests / e2e_tests / mutation_testing / fitness / overall_status / meets_done_when | **未对照** | output 第 3 节仅说"没有约定统一 JSON / YAML 结构,留给 runner",但**没有把 skill 文档与 7.4 列出的 10 个字段逐一比对**——审查的最重要硬性 schema 锚点缺失 |
| R7 | 7.5 | acknowledge PBT 关闭 reward hacking 的口子 | yes(且最完整) | output 第 5 节引片 plugin.json description / README line 53-55 / iron rule 5 / mutation/README.md "Why this matters" |
| R8 | 第九章角色分工 | 明确 skill 不充当 Step 5 实施 Agent | yes | output 第 1 节 hand-off 声明引 7 处文档,iron rule 6 / next-step 提示 |

**满足度小结**:R1 / R2 / R4 / R7 / R8 满足充分,R5 / R6 满足部分,R3 满足(并诚实标注限制)。**R6 是审查输出本身的缺口**:Worker 注意到 skill 没定义 evaluation_result schema,但没把 skill 边界声明与 §7.4 硬性 schema 的 10 字段逐项对应来核实"该推给 runner 的字段是否一个不漏地推干净了"。

---

## 二、P0 issues

无 P0。Worker 产出**完整覆盖了 P0 列表的全部红线**:

- skill 文档没有假装实现 Step 5(已查 5 份文档,Worker 第 6 节"边界声明的一致性"表格证明)
- 移交声明在 5 份文档中冗余且一致(第 1 节)
- 移交契约可执行(INTEGRATION.md ratchet recipe 是 copy-paste 可贴的样板,见 Worker 第 2 节引片)
- **7.2 做判分离原则**在 README + INTEGRATION + rubric 文件均显式声明(Worker 第 4 节)

**唯一接近 P0 的事项**(已落到 P1):evaluation_result schema 与 §7.4 的对照在审查口径中应做但未做(R6)。这不构成"skill 假装实现 Step 5",仅是审查覆盖深度的缺口,降为 P1。

---

## 三、P1 issues

### P1-1:未对照 §7.4 硬性 schema 的 10 个字段逐项核实

**位置**:Worker output 第 3 节"evaluation_result 输出结构是否被 skill 文档定义"。

**问题**:第 3 节正确识别 skill 文档没定义 evaluation_result 结构,但没拿设计文档 §7.4 原文(原文摘录:`evaluation_result: feature / timestamp / existence{status,checks_passed} / unit_tests{example_based.passed, property_based.passed, total_inputs_tested} / integration_tests{example_based, property_based{minimal_counterexample}} / e2e_tests{passed} / mutation_testing{mutants_killed, kill_rate, surviving_mutants} / fitness{<criterion>: score} / overall_status / meets_done_when`)做逐字段对照。

**期望**:对 10 个字段每个标注:
- (a) skill 文档是否要求产物**间接产出该字段所需信号**(如 `mutation.sh` 退出码 → `mutation_testing.kill_rate`;`pytest` 退出码 → `unit_tests.example_based.passed/N`),且
- (b) skill 文档是否声明该字段**由 ratchet/runner 自己拼装**(如 INTEGRATION.md line 54 "evaluate.sh ... effectively a wrapper around our test commands"),且
- (c) 哪些字段在当前 skill 产物 / 边界声明里**无对应信号或对应模糊**(候选:`minimal_counterexample`、`total_inputs_tested`、`surviving_mutants` 的具体 file/line/mutation 三元组)。

**为何 P1 而非 P0**:Worker 已识别这是设计选择(skill 把 schema 责任推给 ratchet),且 INTEGRATION.md 已显式 disclaimer,所以不是"skill 假装实现 Step 5"——只是审查的硬性 schema 锚点没做完。

### P1-2:`minimal_counterexample` 字段在 skill 文档中的覆盖未审

**位置**:Worker output 第 3 节、第 4 节 4-B/4-C 段。

**问题**:设计文档 §7.4 evaluation_result 的 `integration_tests.property_based.minimal_counterexample` 是 PBT 关键产出(对应 7.5 反 reward hacking 的核心证据——Hypothesis/fast-check 的 shrink 反例)。Worker 第 3 节笼统说"PBT runs ... Hypothesis/fast-check 报告的事,不在 done_when 评估输出 schema 里",但未单独审查:

- skill 文档是否要求 PBT 测试**保留** shrink 反例(Hypothesis 默认会在失败时打印 minimal example,但是否要 `--hypothesis-show-statistics` / 反例落盘?)
- 移交契约里是否告诉 runner "PBT 失败时,反例信号在 pytest stderr / 反例文件"?
- ratchet recipe 的 P0 criteria 仅写 `pytest tests/<feature>/integration/ passes all tests`——退出码维度无法承载 minimal_counterexample。

**期望**:审查 skill 是否给出"PBT 失败信号如何被外部捕获"的指引,或显式声明这是 runner 责任。

### P1-3:`surviving_mutants` 三元组(file/line/mutation)的捕获契约未审

**位置**:Worker output 第 4 节 mutation 段、第 3 节 evaluation_result 段。

**问题**:§7.4 要求 `mutation_testing.surviving_mutants: [{file, line, mutation}]`。Worker 第 4 节确认 `mutation.sh` 退出码反映 kill_rate 阈值,但**没有审查**:

- mutation.sh / pyproject.toml 是否要求 mutmut 输出 surviving mutants 列表到某固定路径?(mutmut 默认在 `.mutmut-cache/` 有数据库,但需 `mutmut results` 单独导出)
- skill 文档是否声明这个字段是 runner 自己 query mutmut 拿,还是 mutation.sh 应该兜底导出?

Worker 把 mutation 整段当成"退出码就够"来审,忽略了 §7.4 要求的**结构化 surviving_mutants 字段**。

### P1-4:第 4 节 R3"做判分离强制机制"未引设计文档 §7.2 原文

**位置**:Worker output 第 4 节。

**问题**:Worker 用 README.md line 9-13、INTEGRATION.md line 94-95、rubric line 16-18 三处证据论证"做判分离已声明",但**没有引设计文档 §7.2 原文**("做的 Agent 和判的 Agent 必须分离。同一个 session 既写代码又判结果,会出现自我合理化")来作为锚点 vs 实现对照。审查"是否满足 §7.2"必须有 §7.2 原文。

**期望**:第 4 节开头加一段"设计文档 §7.2 原文 vs skill 现状",再走证据。

### P1-5:Translation guidance 完整度审查未涵盖 fitness layer

**位置**:Worker output 第 2 节。

**问题**:第 2 节"Translation guidance"重点在 ratchet 的 Goal / Criteria / Scope,引 INTEGRATION.md line 32-51。但 fitness layer 的 P0 criteria **没有**出现在那个 ratchet recipe 里(recipe 只列 existence / unit / integration / e2e / mutation 五条),而 fitness 是 §7.4 evaluation_result.fitness 的字段来源。审查重点应该追问:

- ratchet recipe 不含 fitness P0 是否设计如此(因为 fitness 是手工 fresh-session 流程,不能并入 ratchet 自动 loop)?
- 是否 skill 文档有说明"fitness 结果如何回流到 ratchet 的 'done' 判定"?

Worker 第 5 节(关于 fitness)做了 layer-内审查,但**没有把 fitness 与 ratchet recipe 的关系单独点出来**——这是 translation guidance 完整度的一块拼图。

---

## 四、P2 issues

### P2-1:Worker 自述"未读源 spec 文档"是一个流程瑕疵

**位置**:Worker output 第 5-8 行("**未** 读取 `~/Documents/Downloads/done-when-pipeline.md`(源 spec 文档)")。

**问题**:Worker 主动声明没读 source spec,审查仅基于 skill 文档自洽性。这导致 §7.4 硬性 schema(P1-1)和 §7.2 原文(P1-4)无法被引用——这是 P1 几条的根因。Worker 把"判断只来源于 skill 自己的文档"作为方法论是过谨慎了:Step 5 审查口径就是"对照设计文档 §7"——脱离 §7 原文做不到"硬性约束核验"。

**建议**(不约束 Worker 此轮,记录给下一轮):审查 attempt-N 时应先读设计文档对应章节,再去看 skill 自洽性。

### P2-2:第 7 节"事实陈述"列表与"issues"未明确切分

**位置**:Worker output 第 7 节"skill 指令模糊点"。

**问题**:Worker 列了 10 条"事实陈述,不作 issue 判定",但 Worker 任务里没有"列事实陈述"的口子——Worker 角色是 Step 5 执行评估的产出,不是 auditor。这 10 条本质是 Worker 自审 + 主动 surface 风险点,有价值但越界到了 Auditor 角色应做的事。

**为何 P2**:不影响 Step 5 边界声明完整性的结论;只是角色边界稍模糊。

### P2-3:重复声明引片可压缩

**位置**:Worker output 第 1 节"Hand-off to /ratchet 声明"引 7 处。

**问题**:5 份文档共引 7 处片段证明"边界声明在",冗余度对最终结论无增益(第 6 节"边界声明的一致性"用表格已经把 5 份文档 × 4 项核心断言交叉过一遍,更高效)。第 1 节的 7 处引片可压缩到 2-3 处代表性引片 + 指向第 6 节表格。

**为何 P2**:风格瑕疵,不影响结论可信度。

### P2-4:`acceptance-spec` SKILL.md 自称 "Covers Steps 1-3" 与 done_when.yaml 归属的讨论可剥离

**位置**:Worker output 第 7 节第 7 条。

**问题**:这条讨论"acceptance-spec 写 done_when.yaml 是否算 Step 3 还是 Step 4 入口"——这是 Step 3/4 的边界事项,**不在 Step 5 审查范围**。Auditor 口径下应剔除。

**为何 P2**:不影响 Step 5 结论,但属于审查越界(很轻微,因 Worker 自己也只是事实陈述)。

---

## 五、计数

| 级别 | 数量 |
|---|---|
| P0 | 0 |
| P1 | 5 |
| P2 | 4 |
| **合计** | **9** |

---

## 六、整体评价(只给铁律允许范围的事实陈述)

Worker 对 Step 5 边界声明完整性 + 移交契约可执行性的核心结论**站得住**:

- 5 份 skill 文档边界声明一致(第 6 节表格 4×5 网格全覆盖)
- ratchet recipe 是 copy-paste 可贴的具体样板(INTEGRATION.md line 32-51)
- 7.2 做判分离在哲学层强声明,在 fitness 层用 "fresh Claude session" 显式约束
- 7.5 PBT 反 reward hacking 在 5 份文档冗余声明

主要审查缺口集中在**未与设计文档 §7.4 硬性 schema 做逐字段对照**(P1-1 至 P1-3),这是因为 Worker 主动不读 source spec(P2-1)。结论本身没错,但"硬性 schema"这个口径的证据闭环没完成——Worker 说"skill 不定义 evaluation_result schema,推给 runner",但**没说清楚 runner 收到的信号是否足够拼出 §7.4 那 10 个字段**(特别是 `minimal_counterexample` 和 `surviving_mutants` 这两个结构化字段)。

不许修复,记 issues 完毕。
