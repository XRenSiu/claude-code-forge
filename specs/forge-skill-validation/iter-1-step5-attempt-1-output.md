# Step 5 Worker 产出 — iter-1-step5-attempt-1

## 任务说明

本 Step **不是**实际执行测试 / 收集证据 / 评估 done_when 通过情况。本 Step 验证的是 **边界声明 / 移交契约的完整性**：`acceptance-spec` 和 `test-suite-generator` 两个 skill 是否正确地告诉用户 "Step 5 不归我管，要这样移交"，以及它们的产物是否给外部 runner（人手 hand off 到 `/ratchet` 或直接跑 pytest/playwright/mutmut）留下了足够上下文。

判断只来源于 skill 自己的文档 + Step 3/4 attempt-2 产物。**未** 读取 `~/Documents/Downloads/done-when-pipeline.md`（源 spec 文档）。

---

## 已检查文件清单

| 文件 | 检查重点 | 关键引用 |
|------|---------|---------|
| `plugins/done-when-pipeline/.claude-plugin/plugin.json` | plugin description 是否声明 Step 1-4 范围 + Step 5/6 manual | 第 3 行 description 长串 |
| `plugins/done-when-pipeline/README.md` | 顶层 pipeline 图 + "What this plugin does not do" + Version 段落 | line 38（ratchet 是 Step 5-6 oracle），line 69（不跑测试），line 90（Step 5/6 hand off MANUALLY） |
| `plugins/done-when-pipeline/INTEGRATION.md` | "Handoff: test-suite-generator → ratchet (manual)" 整节 + spec_drift_threshold 翻译表 + fitness 4-F 移交 | line 3、line 11-18 边界图、line 26-51 ratchet handoff recipe、line 58-62 "What ratchet does NOT do"、line 67-82 spec drift 翻译表、line 88-101 fitness 4-F 手工方案 |
| `plugins/.../acceptance-spec/SKILL.md` | iron rule 6 / S3 末尾 next-step / spec_drift_threshold 的措辞 | iron rule 6（line 41）、line 180-188（spec_drift 是 guidance, 不是 contract field）、line 195（next step: /test-suite-generator）|
| `plugins/.../test-suite-generator/SKILL.md` | iron rule 5 mutation 防作弊 / 4-F fitness 移交方案 / 末尾 next-step | iron rule 5（line 37）、4-E（line 238-251）、4-F line 254-270、line 280-283（不要自己跑） |
| `iter-1-step3-attempt-2-artifacts/done_when.yaml` | 是否含 v1 strict schema，所有阈值齐全 | thresholds 块全 4 个键齐全，fitness 用 `persona-judge` token，spec_drift_threshold 单字段 |
| `iter-1-step4-attempt-2-artifacts/existence/existence.sh` | fail-fast 模式 + REQ 注释 | set -euo pipefail + check() helper，每行带 REQ 注释 |
| `iter-1-step4-attempt-2-artifacts/mutation/mutation.sh` + `pyproject.toml` + `README.md` | 阈值是否从 done_when.yaml 拉取 + 防作弊原文 | THRESHOLD=70 与 thresholds.mutation_kill_rate 一致；README "If you bypass this script, you re-open the reward-hacking hole" |
| `iter-1-step4-attempt-2-artifacts/integration/conftest.py` | testcontainers 真容器 + 无 mock | line 13-15 imports testcontainers.postgres / .redis；line 11 注释 "NO MOCKS" |
| `iter-1-step4-attempt-2-artifacts/e2e/playwright.config.ts` | E2E 工具是否可直接 runnable | baseURL = `http://localhost:3000`（来源未指明） |
| `iter-1-step4-attempt-2-artifacts/fitness/README.md` + 两份 rubric | 4-F manual workflow 是否定义清楚 | README "How rubric files are consumed (today)" 5 步流程；rubric "How to run this rubric" 5 步流程 |

---

## 声明完整性

### 1. Hand-off to /ratchet 声明

**是否声明：yes（多处冗余声明，相互一致）**

引片段：

- `plugin.json` line 3:
  > "Step 5 execution and Step 6 ratchet feedback loop hand off MANUALLY — the user invokes /ratchet with translated Goal/Criteria/Scope; ratchet does not parse done_when.yaml directly."

- `README.md` line 90 (Version 段落):
  > "0.1.0 — initial release, covers Steps 1-4 of the pipeline. Step 5 (execution) and Step 6 (loop) hand off **manually** to `ratchet` (a chained `/ratchet` invocation whose Goal/Criteria/Scope the user translates from our outputs)."

- `README.md` line 69 ("What this plugin does not do"):
  > "It does not run tests. (That's Step 5 — pytest, vitest, Playwright, mutmut.)"

- `INTEGRATION.md` line 3:
  > "The done-when-pipeline plugin covers Steps 1-4 of the source design doc. Steps 5 (execution) and 6 (closed-loop iteration) hand off to other skills in this marketplace — **the handoff is manual on the user's part, not an automated structural integration**."

- `acceptance-spec/SKILL.md` iron rule 6 (line 41):
  > "**You do not write tests.** Tests are Step 4 (`test-suite-generator`). Your job ends at `done_when.yaml`."

- `test-suite-generator/SKILL.md` "After all six sub-steps" (line 281):
  > "The next-step suggestion: hand the spec + tests to `/ratchet` as the implementation contract."

- `test-suite-generator/SKILL.md` line 283:
  > "Do not implement the feature. Do not run the integration / e2e suites unless the user explicitly asks ... Mutation is too slow to run by default."

`acceptance-spec/SKILL.md` 末尾 line 195-198 还显式声明：
  > "That's the end of this skill. **Do not** generate tests, do not start implementing, do not run anything — those are downstream steps."

边界声明在五份文档里相互一致且多次重申。

### 2. Translation guidance（done_when.yaml → ratchet Goal/Criteria/Scope）

**是否有：yes（INTEGRATION.md 给了完整 recipe）**

引片段，`INTEGRATION.md` line 32-51（直接可贴的样板）：

```
/ratchet
  Goal: Implement the feature in specs/<feature>/spec.md.

  Criteria (P0, all must pass):
    - bash tests/<feature>/existence.sh exits 0
    - pytest tests/<feature>/unit/ -x passes all tests
    - pytest tests/<feature>/integration/ passes all tests
    - playwright test tests/<feature>/e2e/ passes
    - bash tests/<feature>/mutation.sh exits 0   # mutation_kill_rate >= 0.70

  Scope:
    CAN modify:    src/ (or whichever implementation paths the spec implies)
    CANNOT modify: specs/, tests/    # frozen — these are the contract

  done_when:
    success:     all P0 criteria pass
    convergence: 3 consecutive rounds with no new test passing
    budget:      max 15 rounds
```

并且明确说明 spec_drift_threshold.max_fix_loops_before_escalation 应该被翻译成 ratchet 的 `convergence` 值（line 77-82）：

> "Set ratchet's `convergence` to `max_fix_loops_before_escalation` (here: 3 rounds with no improvement → stop)."

同样的 recipe 在 `acceptance-spec/SKILL.md` line 184 也有提及（指向 INTEGRATION.md "for the recipe"）。

### 3. evaluation_result 输出结构是否被 skill 文档定义？

**是否：否（明确不定义；外部 runner 需要自己产）**

skill 文档**没有**约定 evaluation_result 的统一 JSON / YAML 结构（如 `{existence: pass, unit: pass, pbt_runs_observed: int, mutation_kill_rate: float, e2e: pass, fitness: {<criterion>: score}}`）。skill 只规定了**每个 layer 的退出语义**和"哪些命令应当为 P0"：

- `existence.sh`：fail-fast，exits 1 on first failure（test-suite-generator SKILL.md line 43 + iron rule 10）—— 即 exit code 是结果信号
- `unit/integration`：通过 `pytest -x` 跑，pytest 退出码即结果（INTEGRATION.md line 38-41）
- `mutation.sh`：明确"exit nonzero on kill-rate under threshold; this is the signal `ratchet` needs to decide 'not done'"（test-suite-generator SKILL.md 4-E 部分 line 248）
- `e2e`：playwright/cypress 的退出码
- `fitness`：每个 rubric 文件**自己**定义 aggregation + pass/fail 子句（如 `oncall_engineer_edge_case_prediction.rubric.md` 的 "Pass/fail" 段落：`final score >= 8.0 AND no sub-dimension < 5`）

换句话说，skill 把"如何把这些层折叠成一份结构化 evaluation_result"留给了 runner（或 ratchet 的 evaluate.sh）。INTEGRATION.md line 54-56 明确：

> "Ratchet's own Step 1-3 runs: it reads the goal/criteria/scope above, writes `<experiment-dir>/ratchet.md` + `<experiment-dir>/evaluate.sh` (which is effectively a wrapper around our test commands)."

即 evaluate.sh 由 ratchet 自己生成、根据 P0 criteria 串成；本 plugin **不**提供模板。

PBT runs（pbt_runs_per_property >= 500）的"实际观察到多少 runs"也**不**作为 skill 输出，而是隐含在 PBT 测试代码里（`mutation/README.md` line 46 说 `encoded as max_examples=500 in PBT tests`）—— 即 PBT 实际跑了多少次是 Hypothesis/fast-check 报告的事，不在 done_when 评估输出 schema 里。

### 4. 做判分离原则在 skill 文档中的体现

**是否声明：yes（哲学层面强声明，但无强制机制）**

引片段：

- `README.md` line 9-13 "Why this exists":
  > "**Independently verifiable** — the agent that builds and the agent that judges are different sessions"

- `acceptance-spec/SKILL.md` line 19-20 引导语暗含 spec / 实现 分离（"the contract that ratchet and test-suite-generator will consume"）

- `test-suite-generator/SKILL.md` 4-F line 263-266 fitness rubric "How-to-run block" 显式要求 fresh Claude session：
  > "Until packaged automation for arbitrary-artifact persona judging lands, the rubric is consumed by a fresh Claude session driven manually (paste the rubric + artifact paths into a new session and ask for the score)."

- `INTEGRATION.md` line 94-95（fitness handoff 段）:
  > "the rubric file is intended to be loaded by a fresh Claude session (no implementer context) which reads the rubric + the artifacts + emits a score."

- 产物层面，rubric 文件自带强声明（`oncall_engineer_edge_case_prediction.rubric.md` line 16-18）:
  > "1. Open a fresh Claude session, separate from the implementer's context.
  > 2. Paste this rubric file.
  > 3. Paste in (or provide the path to) `spec.md`."

**强制机制层面：partial / 实际是约定式而非工具式**

- 没有任何代码 / 工具会**自动**保证"做的 session ≠ 判的 session"——skill 只能在文档里**告诉用户**"开新会话"。
- 单元 / 集成 / E2E / mutation 这四层是 fully 程序化（runner 与 implementer 天然分离：testcontainers + pytest + mutmut 不读模型上下文），所以做判分离在这几层是天然成立的；仅 fitness 层依赖人为遵守新开会话。
- README "Why this exists" 把 independently verifiable 列为 4 条核心原则之一，但 plugin 不能也没有声称能强制——这是哲学+工具组合（PBT/mutation 是工具，fitness 新会话是约定）。

### 5. PBT 反 reward hacking 的声明

**是否声明：yes（多处明确把 PBT 列为反作弊层）**

引片段：

- `plugin.json` description 末尾:
  > "PBT closes the reward-hacking loop because the agent cannot predict Hypothesis/fast-check inputs at write time."

- `README.md` line 53-55 ("Design philosophy" 第 3 条):
  > "**Anti-reward-hacking is mandatory, not optional.** A done_when that only checks coverage ≥ 80% incentivizes `assert True`. Mutation testing closes that loop; PBT closes the 'agent memorized the test cases' loop."

- `README.md` line 38-40 (pipeline 图末):
  > "spec-drift bailout: PBT failing >=3 rounds escalates back to clarify"
  （这句把 PBT 失败定位为 spec bug 而非 code bug 的关键信号）

- `test-suite-generator/SKILL.md` iron rule 5 (line 37):
  > "Mutation testing is mandatory, not optional. A done_when that only enforces coverage ≥ 80% will incentivize the implementer to write `assert True` to inflate the number. Mutation kill rate ≥ 70% is the gate that closes that loop. Always emit a `mutation.config` file (4-E)."

- `test-suite-generator/SKILL.md` iron rule 3 (line 35) 间接呼应：PBT property archetype 必须从测试名后缀恢复（`_is_idempotent`、`_invariant`、`_state_machine` 等），意味着 PBT 不是装饰物，archetype 决定了 Hypothesis/fast-check 怎么生成对抗输入。

- 产物层 `mutation/README.md` "Why this matters" 段（line 19-34）整段就是反作弊原理图，举的也是 `assert True` 案例 + mutation `<` → `<=` 的工作机制。

PBT 角度的"对抗输入不可预测"在 README + plugin.json 都说到了；mutation 角度的"`assert True` 被 mutmut 捕获"在 SKILL.md + 产物 README 都说到了。两层防作弊互相补足且**都**在 skill 文档里声明了"为何 mandatory"。

---

## Skill 是否提供足够上下文让外部 runner 跑通 Step 5？

逐个 layer 评估。

### 4-A existence: 可否直接 `bash existence.sh` 跑通？

- **跑通条件**：脚本本身**可执行**且**fail-fast 正确**——见 `existence.sh` line 16 `set -euo pipefail` + line 21-25 `check()` helper。这是 skill SKILL.md iron rule 10 + 4-A 段要求的模式，符合。
- **前置依赖**：脚本调用 `rg`（ripgrep），所以 runner 必须装 ripgrep。skill 文档（test-suite-generator SKILL.md 4-A line 88-94）说"a single script (`existence.sh` for shell-friendly projects, `existence.py` if Python-only stack)" + "rg -q '<name>' src/ || (ts-morph / python -c 'import ast' — language-specific)"，提到了 ts-morph 和 ast 但**没有**列出"需要 apt install ripgrep / npm i ts-morph"这一类前置安装清单。
- **当前一定 fail**（设计如此）：脚本搜的目录是 `src/` 和 `src/db/`，而本仓库当前**没有** `src/` 实现树（这是 forge-skill-validation iteration，实现尚未写）。脚本会在第一个 `check` 就退出 1。skill 文档对此**也明确**说了（test-suite-generator SKILL.md 4-A line 136）:
  > "Run it. If it fails (which is expected on first run — the implementer hasn't written the code yet), that's fine — the script becomes part of the contract, not a current-pass requirement."

  即：脚本的"现在跑会失败"是设计预期，runner 应当把它包到 ratchet 的 P0 criteria 里作为"目标"。

**结论：可直接 `bash existence.sh` 跑通（前提：装 ripgrep + cd 到包含 src/ 的项目根）；当下一定红，红是契约预期。skill 没有列出 ripgrep 这种 OS-级依赖清单，runner 需要自己处理。**

### 4-B/4-C/4-E unit/integration/mutation: 可否直接 `pytest`？mutation 怎么跑？

**unit (`pytest tests/<feature>/unit/`)**：
- 前置：必须装 pytest + Hypothesis（PBT 测试要 import hypothesis）。SKILL.md 4-B line 152 提到 "Use Hypothesis (Python)" 但**没有**列出 `pip install hypothesis pytest` 这种安装命令。
- 测试文件本身可被 collect（test_*.py + def test_*）。命名严格 verbatim from done_when.yaml（iron rule 9）。
- 当前一定 fail：unit 测试 import 了 `src.*` 模块，实现没写就会 collection 失败。这是契约预期。

**integration (`pytest tests/<feature>/integration/`)**：
- 前置：必须 Docker daemon 在跑 + 装 testcontainers + 装 redis + psycopg2 / asyncpg。`conftest.py` line 13-15 显式 import `testcontainers.postgres` 和 `testcontainers.redis`。**首次拉镜像可能要分钟级**（postgres:16-alpine, redis:7-alpine）。
- skill SKILL.md 4-C line 175-176 说 "Use testcontainers for the inferred dependencies. Postgres / Redis / Kafka / SMTP-mock — all have container images" + "Do not use HTTP mocks"，但**没有**列出"runner 要先确保 Docker daemon 在跑 + 镜像已 pull"的前置清单。
- conftest.py 还 import 了 `src.app.make_app` / `src.db.migrate.migrate` / `src.db.session`，这些在 collection 阶段就会 ImportError——也是契约预期。

**mutation (`bash mutation.sh`)**：
- 前置：装 mutmut + 已经能跑通 unit tests（mutmut 拿 pytest 作为 runner，见 `pyproject.toml` line 17-18：`runner = "pytest -x tests/channel-mention-notifications/unit/"`）。
- 退出语义：mutation.sh line 30-35 在 SCORE < 70 时 `exit 1`，符合 SKILL.md 4-E line 248 "exit nonzero on kill-rate under threshold; this is the signal `ratchet` needs to decide 'not done'"。
- 阈值是从 done_when.yaml 拉的吗？**partial**：mutation.sh line 13 写死 `THRESHOLD=70`，注释解释"corresponds to thresholds.mutation_kill_rate (>= 0.70)"——这是**人工同步**的硬编码，不是从 yaml 解析出来的。如果 done_when.yaml 改阈值，mutation.sh 不会自动跟随。skill SKILL.md 4-E line 244 说 "asserts kill rate ≥ the threshold from `done_when.yaml`" 但**没有**说该数字必须以 yaml 为唯一源（导致出现这种 hardcoded 同步的产物）。

**结论：runner 可以直接 `pytest` 和 `bash mutation.sh`，但前置工具栈（Docker daemon for testcontainers, mutmut binary, Hypothesis）在 skill 文档里只是被点名，没列出 install/setup 步骤。当下一定红——这是契约预期。mutation 阈值的 yaml↔脚本同步是人工的，存在漂移风险（事实陈述，非 bug 判定）。**

### 4-D e2e: 可否直接 `playwright test`？需要前置启动什么 server？

- 前置：`playwright.config.ts` line 14 写 `baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:3000'`，即默认指向 `localhost:3000`。**但 skill / 产物中没有任何文件**说明这个 server 是谁、怎么起、需要什么 seed。
- 测试本身用 `data-test=*` 选择器（符合 SKILL.md 4-D line 187）。
- skill SKILL.md 4-D line 184-187 选工具时说 "If the project has none, default to Playwright (web) or Maestro (mobile); tell the user which you picked"——`playwright.config.ts` 注释（line 5）也照做了："no Cypress/Maestro config detected in the project → Playwright (web default)"。
- skill SKILL.md "After all six sub-steps" line 280-283 明确：
  > "Do not implement the feature. Do not run the integration / e2e suites unless the user explicitly asks ('run integration')."

  即 e2e**默认就不跑**，是 runnable-but-not-run，留给 ratchet/runner 决定何时跑。
- INTEGRATION.md ratchet recipe 第 4 条 P0 criteria 也直接写 `playwright test tests/<feature>/e2e/ passes`——没说 server 怎么起，假设 ratchet 的实现 subagent 会先 `npm run dev` 或类似。

**结论：可以直接 `playwright test`，但需要 runner（或 ratchet 的实现 subagent）先手工启动 `localhost:3000` 的应用 server。这个前置步骤 skill 文档没有显式声明，是 implicit contract。这是事实陈述，对应于"模糊点"清单。**

### 4-F fitness: rubric 文件怎么用？谁来评？skill 给了指引吗？

- skill 给了**明确**指引——三个层级都讲到：
  1. SKILL.md 4-F line 254-270 列出三种 `judge:` 值（programmatic / persona-judge / manual）对应三种产物形态
  2. INTEGRATION.md line 88-101 整段讲 fitness handoff 当前的真实状态："no packaged consumer in this marketplace today"
  3. 产物层 `fitness/README.md` + 每份 rubric 的 "How to run this rubric" 段（如 oncall rubric line 14-26）写了 5 步手工流程
- 谁来评：**fresh Claude session**（不带 implementer context）——rubric 文件 line 16 显式写 "Open a fresh Claude session, separate from the implementer's context."
- 是否有 packaged auto-runner：**没有**，skill 文档反复强调这一点（README.md line 65 表格、INTEGRATION.md line 92、fitness rubric "How to run"）。
- 评分方式：rubric 自带子维度 + 权重 + anchors（1-10 + 锚点描述）+ Pass/fail 子句 + Re-run policy。这是 self-contained 的，runner 不需要 invent。

**结论：fitness 层的"怎么用"在 skill 文档里讲得最透彻——因为它是唯一无法机械化的层，文档写得最详细，反而 OK。**

---

## 边界声明的一致性

检查五份文档（plugin.json / README / INTEGRATION / acceptance-spec SKILL / test-suite-generator SKILL）里关于 "Step 范围" 的描述：

| 文档 | 说"覆盖 1-4" | 说"Step 5 manual to ratchet" | 说"无 packaged fitness-judge" | 说"不跑测试" |
|------|------------|---------------------------|--------------------------|------------|
| `plugin.json` description | yes（"compose Steps 1-4 of the pipeline"） | yes（"Step 5 execution and Step 6 ratchet feedback loop hand off MANUALLY"） | yes（"no packaged fitness-judge skill exists yet"） | implicit |
| `README.md` | yes（line 90 "covers Steps 1-4"） | yes（line 90 "hand off **manually** to `ratchet`"） | yes（line 65 表格 "no packaged fitness-judge skill exists yet"） | yes（line 69 "It does not run tests"） |
| `INTEGRATION.md` | yes（line 3） | yes（整文核心议题） | yes（line 88-101 整段） | yes（line 18 边界图） |
| `acceptance-spec/SKILL.md` | yes（line 10 "Covers Steps 1-3 of the done_when pipeline"——注意是 1-3，因为 test-suite-generator 是 Step 4）| yes（iron rule 6 + S3 line 195-198 "Do not ... run anything — those are downstream steps"） | n/a（这个 skill 不涉及 4-F） | yes（iron rule 6） |
| `test-suite-generator/SKILL.md` | yes（line 10-13 描述 Step 4 子步骤 4-A 到 4-F） | yes（line 281 next-step suggestion to /ratchet） | yes（4-F line 263-266 "Until packaged automation ... the rubric is consumed by a fresh Claude session driven manually"；同时 line 268 严拒 `judge: llm-rubric`，要求改用 `persona-judge`）| yes（line 282-283 "Do not run the integration / e2e suites unless ... Mutation is too slow to run by default"） |

**结论：边界声明在五份文档里完全一致**——四个核心断言（"覆盖 1-4 / Step 5 manual / 无 fitness-judge / 不跑测试"）每一份都覆盖到（除 acceptance-spec 不涉及 4-F 这点是合理的，因为它只产 contract 不产 fitness rubric 文件）。

INTEGRATION.md 第 5 行还显式记录了"上一版过度声明被回滚"的历史（"This file was rewritten on 2026-05-24 after the round-1 self-validation pass found that the previous version overclaimed the integrations"）—— 即一致性是被有意识维护的，而不是侥幸一致。

`acceptance-spec/SKILL.md` 的 spec_drift_threshold 段（line 180-188）特别值得点名：

> "This is **guidance for the human chaining to `/ratchet`**, not a contract field anything auto-reads today. When chaining, translate `max_fix_loops_before_escalation` into ratchet's own `convergence` value (see `done-when-pipeline/INTEGRATION.md` for the recipe). Auto-escalation is future work; do not promise the user it happens automatically."

acceptance-spec 自身在写 done_when.yaml 时就主动声明这个字段"不会被自动消费"，把 hand-off 责任明确推给 INTEGRATION.md——这是边界处理的高分点。

---

## skill 指令模糊点（事实陈述）

下面是审查中发现的指令模糊点 / 未明示的前置假设——**纯事实陈述，不作 issue 判定，不写 patch**：

1. **OS-级 / 工具栈安装清单缺失**：existence.sh 用 `rg`，integration 用 testcontainers + Docker daemon，mutation 用 mutmut，PBT 用 hypothesis/fast-check / jqwik。skill 在"reference 索引"（test-suite-generator SKILL.md line 296-305）里提到了 `tooling-by-language.md`，但顶层 SKILL.md / INTEGRATION.md / README **没有**列出"runner 跑 Step 5 之前要装这一组东西"的合并清单。runner（或 ratchet 的 evaluate.sh 起手）需要自己知道。

2. **E2E baseURL = localhost:3000 的应用 server 不在产物中**：`playwright.config.ts` 假设 `localhost:3000` 有应用在跑，但产物里**没有** `start-server.sh` 或 `docker-compose.yml` 把这个 server 起来。skill SKILL.md 4-D 也没说 e2e 测试预期由谁负责 boot up app（隐含假设是 ratchet 的实现 subagent 在 implementing 时一起起 server）。

3. **mutation 阈值在 yaml 和脚本里是 dual source**：`done_when.yaml` 写 `mutation_kill_rate: ">= 0.70"`，`mutation.sh` 写 `THRESHOLD=70`，二者由人工同步。test-suite-generator SKILL.md 4-E line 244 没说"必须运行时从 yaml parse"——这导致阈值漂移风险存在但被允许。事实陈述，不一定是 bug，因为 skill 当下的设计就是把 done_when.yaml 当成"被人/ratchet 读"的契约而非"被脚本读的配置文件"。

4. **PBT runs/property 阈值的执行点**：`pbt_runs_per_property: ">= 500"` 在 done_when.yaml 里，`mutation/README.md` 把它翻译成 "encoded as `max_examples=500` in PBT tests"——但 skill SKILL.md 4-B 段（line 142-160）讲 PBT 生成时**没有**显式要求 "test 必须设 `@given(...)` 的 max_examples 等于 done_when.yaml 的 pbt_runs_per_property"。换句话说，如果生成器忘了写 `max_examples=500`，下游 runner / ratchet 也观察不到这个失败——只能在 review 时人眼发现。

5. **evaluation_result schema 没定义**：第 3 节已述。这不是缺陷，而是设计选择——skill 把这事推给 ratchet 的 evaluate.sh + ratchet 的 done_when 块——但意味着多个 ratchet 项目可能产出**结构不同**的 evaluation_result，不利于跨项目对比 Step 5 数据。

6. **"做判分离" 在程序化层是天然的，在 fitness 层只能靠约定**：第 4 节已述。这是设计的内在限制——skill 文档诚实承认了 "fresh Claude session" 是手工约束。**这点也是 honest 而非 hidden**。

7. **`acceptance-spec/SKILL.md` 描述自己 "Covers Steps 1-3"（line 10），但 `done_when.yaml` 在产物中已经被它写出**——这个 yaml 是 Step 4 的输入契约。即 acceptance-spec 实际覆盖的是 Step 1-3 + Step 4 的输入接口（contract 本体）；wording 没错（contract 是 Step 3 的产物），但读者可能误以为 Step 4 的所有内容都由 test-suite-generator 单独包办，包括 done_when.yaml 的 schema 定义——其实 schema 已经在 acceptance-spec 里被锁住了（references/done-when-schema.yaml）。

8. **`spec.md` 的 `source:` 行作为 traceability 兜底机制对外部 runner 不可见**：iron rule 4 + done_when.yaml v1 schema 把 per-row `based_on:` 拒之门外，traceability 推到 spec.md 的 `source:` 行 + 顶层 `based_on:` union 上。但 Step 5 runner（如 ratchet 的 evaluate.sh）通常只看测试**输出**（pytest report）+ exit codes，不读 spec.md 的 `source:` 行。如果某个 PBT 失败要回溯到具体 REQ-ID，必须人工去 spec.md 查 source 行。skill 文档（test-suite-generator SKILL.md 4-B line 148）说 "Re-derive the REQ link from the test name + the spec.md REQs ... When in doubt, attribute the test to the union top-level `based_on:`"——即承认这是 lossy traceability，事实陈述。

9. **`integration_coverage: ">= 0.60"` 的执行点未说明**：done_when.yaml 写了这个阈值，但 `mutation/README.md` line 40-45 表格只列了三个"enforced by"项（pytest --cov 给 unit + integration coverage，mutation.sh 给 kill rate）。具体 `pytest --cov` 命令在哪儿、谁来跑、`--cov-fail-under=60`** 是否被产出—— skill 文档**没**显式说明。runner 需要自己把 pytest --cov-fail-under 拼到 ratchet 的 P0 criteria 里（INTEGRATION.md ratchet recipe 里的第 3 行 `pytest tests/<feature>/integration/` 也**没**带 `--cov-fail-under`）。事实陈述。

10. **`acceptance-spec/SKILL.md` 对 "spec drift bailout from PBT" 的 ownership 不明**：README.md line 38-40 写 "spec-drift bailout: PBT failing >=3 rounds escalates back to clarify"——但 INTEGRATION.md line 60-62 明确 "It does not automatically escalate 'PBT failures look like spec bugs, not code bugs' back to the user — that escalation logic is not in ratchet today." 即"PBT 反复失败应回到 /acceptance-spec"这件事在 README 是宣传话术，在 INTEGRATION 是显式声明"不存在自动化"。两份文档的措辞一致（README 用 pipeline 图描绘，INTEGRATION 用 disclaimer 揭示），不矛盾，但 runner 看 README 的可能误以为有自动逻辑。这是一致性 OK + 显式 disclaimer 已加 的状态——记录为模糊点级别而非冲突。

---

**总评（一句话）**：两个 skill 对 Step 5 的边界处理在**声明层**和**移交契约层**都很到位（多文件冗余声明 + 完整可贴的 ratchet recipe + fitness 手工流程详细到操作步骤），实际 Step 5 执行所需的命令 / 退出语义 / 阈值都齐备；缺的主要是"工具栈前置安装清单 + e2e server boot + evaluation_result 结构 schema"这一类"runner 自己处理"的内容，且 skill 文档对此 honest（没装作自动）。
