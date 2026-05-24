# Step 3 Audit — iter-1, attempt 1

**Reviewed against:** `/Users/xrensiu/Documents/Downloads/done-when-pipeline.md`, 第五章「Step 3:规格固化」(5.1–5.4) + 附录 C「done_when YAML schema (v1)」.
**Worker manifest:** `iter-1-step3-attempt-1-output.md`
**Disk artifacts:** `iter-1-step3-artifacts/proposal.md`, `spec.md`, `tasks.md`, `done_when.yaml`.

Magnet rule: audit Step 3 only. Out of audit scope: anything about Step 1 草拟过程、Step 2 澄清问答、Step 4 测试派生实现、Step 5/6 执行与闭环。

---

## Summary

| Severity | Count |
|---|---|
| P0 (违反 5.3 文件结构 / 附录 C schema 硬性枚举或字段) | 2 |
| P1 (质量瑕疵但未违硬约束) | 6 |
| P2 (风格) | 3 |

整体结论:**4 件套结构正确、文件名/路径/数量与 5.3 节完全一致**;问题集中在 `done_when.yaml` 的 schema 字段层 ——`fitness[].judge` 用了 schema 不允许的枚举值,以及多处在 schema 之外自创了未定义的字段。manifest 中作者自陈的"模糊点"实际上有一项是**违反硬约束**而非模糊点,本审查按硬约束记 P0。

---

## P0 — 违反 5.3 / 附录 C 硬约束

### P0-1 `fitness[].judge: llm-rubric` 不在 schema 枚举集合内

- **位置:** `done_when.yaml` line 187 与 line 191(两条 fitness 条目全部用了同一个值)
- **设计文档原文(附录 C,line 1029):**
  > ```yaml
  > fitness:
  >   - criterion: <description>
  >     judge: <persona-judge | programmatic | manual>
  > ```
- **实际写入:**
  > ```yaml
  > fitness:
  >   - criterion: ...
  >     judge: llm-rubric
  >     ...
  >   - criterion: ...
  >     judge: llm-rubric
  > ```
- **判定:** schema 把 `judge` 字段的允许值限定为三选一字面量 `persona-judge | programmatic | manual`。`llm-rubric` 既不是这三个之一,也不是它们的别名 —— 在附录 C 的语义里,LLM 判官的对应值是 `persona-judge`(见 4.7 与 12.1 第二条都明确把 LLM-judge 入口收敛到 `persona-judge` skill 上)。
- **影响:** 任何按附录 C 实现的下游消费者(ratchet 解析、persona-judge 路由)看到 `llm-rubric` 会判失败或当 unknown enum 丢弃这两条 fitness,导致 Step 6 闭环时这两条静默蒸发。
- **额外旁证 —— manifest 自相矛盾:** done_when.yaml 文件注释 line 184 写道
  > `# judge ∈ {programmatic, llm-rubric, manual}; see ../done-when-schema.yaml.`
  这条注释把 `persona-judge` 改写成了 `llm-rubric`。这说明 worker 使用的 skill 内部 `references/done-when-schema.yaml` 与设计文档附录 C **本身已经偏离**,worker 在按 skill 内部偏离版的 schema 工作。但 audit 的权威源是设计文档,**skill 内部 schema 与设计文档不一致这件事本身就是 P0**。

### P0-2 `existence[]` 出现 schema 未定义的子字段 `based_on`

- **位置:** `done_when.yaml` lines 10–41,16 条 existence 条目全部带 `based_on: [...]`
- **设计文档原文(附录 C,line 996–1001):**
  > ```yaml
  > existence:
  >   - file: <path>
  >   - function: <name>
  >   - route: <method> <path>
  >   - db_field: <table>.<column>
  >   - frontend_component: <name>
  > ```
- **判定:** schema 明确每个 existence 条目只是 5 种 kind 之一的单一键值对(`file:` / `function:` / `route:` / `db_field:` / `frontend_component:`),**没有任何 sub-field**。Worker 给每条都加了 `based_on: [REQ-...]`。这是在 schema 上**新增了未定义字段**,严格按附录 C 解析时这些条目会被解析器要么 reject(strict)要么 warn-and-drop(lenient)。
- **同样的越界出现在 behavior 各 test 项:** `unit_tests.example_based[]` / `property_based[]` / `integration_tests.*[]` / `e2e_tests[]` 在附录 C 中都被定义为简单字符串数组(`- <test_name>`),worker 把每条扩展成了 mapping 形式带 `name:` / `based_on:` / `property_type:` / `dependencies:` / `tool:`(见 line 49–173)。这同样是**schema 之外加字段**。
- **影响:** 与 P0-1 同级 —— 严格 schema 解析会失败;宽松解析会丢失 `based_on` 这条最关键的可追溯链。

> 说明:这两条 P0 的核心是 worker 把 skill 内部 schema 当作了真理源,但本 audit 锚定的是**设计文档附录 C**。如果团队事后决定"扩展附录 C 允许 traceability 字段",那是 spec 演进问题,不改变本次审查的判定。

---

## P1 — 质量瑕疵但未违硬约束

### P1-1 `tasks.md` 与 REQ 覆盖严重不平衡 / 跨 REQ 追溯有缺口

- **位置:** `tasks.md` 全篇 vs `spec.md` REQ-001 ~ REQ-007
- **观察:**
  - REQ-001 被引用 8 次(7 条业务/数据/surface + 1 条 doc),正常。
  - REQ-002 被引用 8 次,正常。
  - REQ-003 被引用 2 次(`FilterIneligibleRecipients` + Message-send hook),其中 hook 那条是 REQ-001/003/004 三 REQ 共挂的。无任何专门测试性/部署性 task。
  - REQ-004(self-mention)被引用 2 次,与 REQ-003 共担,**没有独立 task**。
  - REQ-005(edit re-trigger)被引用 2 次:`OnMessageEdited` + Message-edit endpoint hook。可执行性 OK。
  - REQ-006(delete partial retract)被引用 4 次,正常。
  - REQ-007(DND deactivation no resurfacing)被引用 2 次:`OnDNDDeactivated` + DND-state change endpoint hook。**没有任何 data 层或 telemetry 任务**保证"DND 期间累积的未读 mention" 这件状态实际可追踪。
- **5.3 节要求:** tasks.md 是"拆分后的**可执行**任务列表"。
- **判定:** 不违硬约束(5.3 没规定每个 REQ 必须有 N 个 task),但 REQ-003/004/007 的覆盖明显单薄,达不到"可执行任务列表"应有的 self-contained 程度。Step 4 派生测试时容易漏覆盖。

### P1-2 `existence[]` 把 surface "类" 塞进 `function:` kind 是违 schema 字面语义

- **位置:** `done_when.yaml` line 22–29 的 `PushSurface` / `InAppBannerSurface` / `SoundSurface` / `UnreadBadgeSurface`
- **设计文档原文(附录 C,line 998):** `function: <name>  # 函数必须 export`
- **观察:** Worker 把 4 个 surface "类/模块"作为 `function:` 条目登记。manifest 自陈的"模糊点 1"承认了这一点。
- **判定:** schema 字面定义的是"函数",而 `PushSurface.fire()` / `InAppBannerSurface.fire()/.retract()` 都是类方法。worker 选了 "function 条目挂类名" 的妥协(因为 schema 没 `class:` kind),在附录 C 字面下属**语义错配**而非字段错配 ——schema 没禁止把类名写在 `function:` 后面,但本来意图是"导出的可调用 function"。
- **降级理由:** 这是 schema v1 自身的颗粒度缺失,不是 worker 主动违约;subscription-cancellation 官方 example 也这么用(`function: CancelSubscriptionUseCase`),设计文档样例本身就在这么做(5.4 节 line 244)。所以记 P1,不记 P0。

### P1-3 `existence[]` 缺 `route:` 条目,但 tasks.md 明确有 4 个 API endpoint hook

- **位置:** `done_when.yaml` line 9–41 vs `tasks.md` line 27–31
- **观察:** tasks.md 列了 4 个 API endpoint hook(message-send / message-edit / message-delete / DND-state change),但 done_when.yaml 的 existence 里没有一条 `route: <method> <path>`。
- **5.3 节 & 附录 C:** `route:` 是 schema 允许的 5 种 kind 之一(line 999)。
- **判定:** Step 6 闭环时 ratchet 不会自动验证 4 个 endpoint 实际是否被注册,因为没有 route 存在性条目。Worker 留了 hook 任务但忘了把它们的存在性契约写入 done_when。
- **降级理由:** schema 没规定"tasks.md 中每个 API 任务必须在 existence 里有对应 route 条目",所以记 P1。

### P1-4 `existence[]` 缺 `frontend_component:` 条目,但 REQ-001 / REQ-002 / REQ-006 明显涉及前端

- **位置:** `done_when.yaml` 同上
- **观察:** REQ-006 提到 "in-app banner retraction",REQ-002 提到 "badge increment under DND",e2e_tests 三条都是 playwright(line 165–173),意味着前端组件存在;tasks.md 却没有 UI 层(也没有前端组件 task),done_when 也没有 `frontend_component:` 条目。
- **判定:** 与 P1-3 同源 —— 前端的 mention banner / unread-badge UI / DND toggle 这些组件没有任何契约层登记。
- **降级理由:** 设计文档没硬性要求"凡 e2e_tests 涉及 UI 必须有 frontend_component 条目",所以记 P1。但这是 Step 4-D playwright 测试能跑通的关键依赖,后续大概率会暴露。

### P1-5 `spec_drift_threshold.applies_to` 是 schema 未定义的子字段

- **位置:** `done_when.yaml` line 198–200
- **设计文档原文(附录 C,line 1033–1034):**
  > ```yaml
  > spec_drift_threshold:
  >   max_fix_loops_before_escalation: 3
  > ```
- **实际写入:**
  > ```yaml
  > spec_drift_threshold:
  >   max_fix_loops_before_escalation: 3
  >   applies_to:
  >     - mutation_kill_rate
  >     - property_based_failure
  > ```
- **判定:** schema 只定义了一个子字段 `max_fix_loops_before_escalation: 3`。worker 新增的 `applies_to` 是 schema 之外的扩展。
- **降级理由:** 这条新增没有破坏 `max_fix_loops_before_escalation: 3` 这条**唯一硬约束**(8.4 节明确"建议 N=3");`applies_to` 是无害的额外语义。所以记 P1 而非 P0 ——它没替换强制字段,只是越界。但严格按附录 C v1 解析仍属于 unknown field。

### P1-6 `fitness[].rubric_file` 是 schema 未定义的子字段

- **位置:** `done_when.yaml` line 188 / 192
- **观察:** 附录 C 的 fitness 条目只有 `criterion` / `judge` / `score_threshold`(line 1028–1030)。worker 在两条 fitness 都加了 `rubric_file: tests/.../*.rubric.md`。
- **判定:** 又一处 schema 之外新增字段。意图可以理解(把 rubric 指向具体文件,方便 Step 4-F 实现),但附录 C v1 没定义这个 hook。
- **降级理由:** 不影响 schema 强制字段的语义,只是越界。归类与 P1-5 同。

---

## P2 — 风格

### P2-1 `created_by: acceptance-spec/0.1.0` 写法在设计文档无规约

- **位置:** `done_when.yaml` line 4
- **设计文档原文(附录 C,line 994):** `created_by: <skill-name>`
- **判定:** 设计文档示例没有要求版本号格式,worker 选了 `<skill>/<semver>` 这种 OCI/Docker tag 风格。属于合理扩展,值含 skill 名也满足 schema。仅记风格条。

### P2-2 `done_when.yaml` 在 schema 之外大量使用 `# === LAYER N — ... ===` 装饰性注释

- **位置:** `done_when.yaml` line 6–8, 43–45, 181–183
- **观察:** 5.4 节样例没有这种 banner 注释,但 YAML 允许。装饰性注释方便人读但和 schema 无关。Worker 在 `created_by` 之后写了一句对 schema 名字的指向("see ../done-when-schema.yaml")也属此类(line 184)。
- **判定:** 无害,但和设计文档样例风格不同。

### P2-3 `spec.md` 在 REQ-002 引入了 schema 之外的 "Extension:" 子句格式

- **位置:** `spec.md` line 20–21
- **观察:** Worker manifest "模糊点 7" 自陈了这一点 —— REQ-002 下用了一个 "Extension:" 段把 round 3 Q2 的广播规则塞进了 REQ-002 之内。设计文档 5 章和附录 A 的 EARS 样例里,一个 REQ 就是一条 EARS 句子;广播规则按 EARS 语法应该是独立的 Ubiquitous 或 State-driven 条款。
- **判定:** 这不在附录 A 五种句式的标准范围内,但也没违反 5.3 节(5.3 只要求 spec.md 是 EARS 规格本体,没规定每个 REQ 只能一句)。**实际后果:** Step 4 派生测试时,"REQ-002 → silence" 的派生器可能漏掉 Extension 段里的"广播在 DND 下也按相同规则"约束 ——broadcast 在 done_when.yaml 里只挂了 unit `test_broadcast_mention_under_dnd_obeys_same_silence_rule_as_individual`(line 75),漏了的话不会被 PBT 抓到。
- **降级理由:** 不违硬约束,但是 spec 写法的弱点。也可以另外拆出 REQ-008 (Ubiquitous: 任何 broadcast 在 DND 下不绕过 silence 规则)。

---

## Cross-check 表(对照审查口径 10 条)

| 口径条目 | 状态 | 备注 |
|---|---|---|
| 1. 4 件套文件名/路径/数量符合 5.3 | **PASS** | 4 个文件齐全,文件名完全一致,均在 `iter-1-step3-artifacts/` 下 |
| 2. done_when.yaml 顶层字段与附录 C 一致 | **PASS** | feature / based_on / created_at / created_by / existence / behavior / fitness / spec_drift_threshold 全部出现,**没有顶层多余字段** |
| 3. existence kind ∈ {file, function, route, db_field, frontend_component} | **PARTIAL** | 实际使用 function + db_field 两种;kind 都合法,但 P1-2/P1-3/P1-4 指出"该用 route/frontend_component 的没用、function 被滥用" |
| 4. behavior 结构符合附录 C | **VIOLATION (P0-2 的延伸)** | 结构骨架对(unit/integration/e2e/thresholds 都在,unit/integration 含 example_based/property_based),但 leaf 项从 schema 的 `<string>` 升格为带子字段的 mapping |
| 5. thresholds 四字段齐全 | **PASS** | unit_coverage / integration_coverage / mutation_kill_rate / pbt_runs_per_property 都在(line 176–179) |
| 6. fitness.judge ∈ {persona-judge, programmatic, manual} | **VIOLATION (P0-1)** | 用了 `llm-rubric`,两条都违反 |
| 7. spec_drift_threshold 在 | **PASS** | `max_fix_loops_before_escalation: 3` 满足 |
| 8. proposal/spec/tasks 符合 5.3 描述 | **PASS-WITH-CAVEATS** | 三份文件都符合各自高层意图,但见 P1-1(tasks 覆盖不均)和 P2-3(spec EARS 风格) |
| 9. spec.md 的 EARS 有唯一 ID | **PASS** | REQ-001 ~ REQ-007,无重复无跳号 |
| 10. created_by 字段合理 | **PASS** | 值含 skill 名,虽附加了版本号(P2-1)但语义无歧义 |

---

## Final verdict

**整体:NEEDS REVISION.**

- 必修(P0,2 项):`fitness[].judge` 改回附录 C 允许的三选一,且要修复 skill 内部 schema(`references/done-when-schema.yaml`)与设计文档附录 C 的不一致,否则后续每次跑 skill 都会重复同样错误;`existence[]` 和 `behavior[]` 的 leaf 项要么回退为 schema 允许的简单形态,要么由 spec 升级(附录 C v2)显式接纳 traceability 字段。
- 应修(P1,6 项):补 `route:` 和 `frontend_component:` existence 条目;补/拆 REQ-003 / REQ-004 / REQ-007 的 task 覆盖;移除 `spec_drift_threshold.applies_to` / `fitness[].rubric_file`,或在附录 C 中显式扩展。
- 可选(P2,3 项):统一 EARS 风格(把 REQ-002 的 Extension 拆出独立 REQ-008);删除装饰性 banner 注释;`created_by` 版本号格式可省略。

**不在审查范围(已明确忽略):**
- Step 1 草拟阶段的 EARS 句式选择是否最优。
- Step 2 澄清问答是否充分(本审查信任 manifest 中 12 条决策皆有 source)。
- Step 4 测试派生是否会基于本 spec 真的生成正确的 PBT/example 测试。
- Step 5 / Step 6 执行与闭环的可行性。
