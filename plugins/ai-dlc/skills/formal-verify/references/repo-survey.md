# 入口 C：给已有仓库生成形式化验证

入口 A 和 B 都从一条已经点名的需求出发。入口 C 只拿到一个仓库，要回答的是：**这里什么值得验证、用什么工具验证、怎么证明这个验证本身不是摆设**。

这一节借鉴的开源项目都是“对已有仓库做形式化验证”的代表做法，原文收录在 `../upstream/`（逐字节、钉提交、带许可证，见 [upstream/README.md](../upstream/README.md)）：

| 项目 | 它对已有仓库做什么 | 这里执行它的哪一段 |
|---|---|---|
| [Theorem OSS Verify](https://github.com/theorem-labs/oss-verify)（Apache-2.0。Theorem 与 Anthropic 在 2026-10 的[研究](https://www.anthropic.com/research/formal-verification)里把 123 个 OSS-Fuzz 库的 fuzz 测试变成定理并证明；OSS Verify 是 Theorem 向其他开源项目开放这条流程的入组仓库，带一个 Claude skill） | 不另写规格：把项目**已有的 fuzz 测试**当规格，“这个测试对任何输入都通过”就是定理 | `add-project` 第 1 步（问清“正确”：六个话题，不猜）、第 3 步（性质写成会终止的检查；覆盖见证；每条性质一个一行破坏）；`review.md` F 节（F1 被构建删掉的形式、F5 两个方向、F8 期望值不能来自被测库） |
| [FM-Agent](https://github.com/fmagent-project/FM-Agent)（Apache-2.0，arXiv 2604.11556） | 对整个代码库按调用图逐函数写行为规格，用被调函数的规格做 Hoare 式推理，不一致就写探针确认 | `system_prompt.md` 规则 1–7（写做什么不写怎么做、不用含糊词、按调用者需要写、规格写正确行为而非现有 bug）、`workflow_spec_step4_batch.md`（自顶向下、每个函数都要完成）、`bug_validator.md`（只经公开入口、打印 CONFIRMED / NOT CONFIRMED、≤3 次）、`workflow_generate_phases.md`（分模块、排除测试） |
| [pstack](https://github.com/cursor/plugins)（已收录） | 在仓库里找出最值得形式化验证的一个承诺，选工具，留下可重跑的检查 | “Choose the target from the code”“Let the question choose the tool”“What makes it good”——之前收录了但没有哪一步执行它，入口 C 补上 |
| [Kani](https://github.com/model-checking/kani) `autoharness` | 扫描整个 crate，为参数都能任意生成的函数自动造 proof harness 并验证 | 不收录原文（只是一个命令）；`fv external --engine kani --arg=autoharness --arg=-Z --arg=autoharness` 调用它，0 个函数被验证判 ERROR |
| [AutoVerus](https://github.com/microsoft/verus-proof-synthesis)、[CrossHair](https://github.com/pschanely/CrossHair)、CBMC / ESBMC、Dafny、Lean | 在代码上（或代码的证明语言版本上）验证性质 | 适配器：证据上限写死，见下 |
| [SysMoBench](https://github.com/specula-org/SysMoBench)（Specula 团队） | 评测 AI 给真实系统写 TLA+ 的能力：语法、运行、轨迹一致、不变量 | 不收录；它的结论支持入口 B 已有的做法：模型要先用真实轨迹校准（LLM 的模型常“进入真实系统到不了的状态”或“到不了真实系统总会到的状态”） |

## C1 普查：`fv survey scan`

```bash
FV="python3 $SKILL_DIR/scripts/fv.py"
$FV survey scan --root <仓库> --out survey.json [--exclude <glob>] [--history 500]
```

只用标准库，结果可重算（同一提交、同一设置，信号与已有检查完全相同）：

- **文件**：在 git 工作区里用 `git ls-files`（遵守 .gitignore），否则遍历目录；默认跳过 `node_modules`、`vendor`、`dist`、`target`、`.venv` 等，跳过二进制与 1 MB 以上的文件。
- **测试文件**：FM-Agent 的规则（`test/`、`tests/`、`__tests__/` 目录，`*_test.*`、`test_*.*`、`*_spec.*`），加上 JS 的 `*.test.*` / `*.spec.*`。测试文件不出风险信号，但用来找“已有检查”和“哪些测试提到了这个文件”。
- **已有检查**：fuzz 目标（libFuzzer、atheris、cargo-fuzz、Go、Jazzer）、性质测试（Hypothesis、fast-check、proptest、quickcheck、jqwik、rapid）、形式化规格（.tla、.qnt、.fizz、.als、.pml、fvkit 模型 / 合同）、代码证明（Kani、Verus、Rust 合约、CBMC、Frama-C、Dafny、Lean）、Python 合约。OSS Verify 从这些出发，不从零写。
- **风险信号**：9 类（concurrency、transaction、retry-idempotency、permission、state-machine、quantity、parser、low-level、time-lease），每个命中带文件、行号和原行。正则匹配，有误报也有漏报。
- **历史**：最近 N 个提交里，标题像修复（fix、race、deadlock、duplicate、idempotent、retry、leak、overflow、revert、修复、竞态、重复、死锁……）的提交改过哪些文件。浅克隆会注明“下限”。
- **工具**：本机装了哪些验证器（pstack：优先选开发者能装能跑的工具）。
- **簇**：按文件聚合，分数 = 3×风险种类数 + 2×状态性种类数 + min(命中数, 20) + 2×min(修复提交数, 10)。产品代码排在前面，`scripts/`、`tools/`、`examples/`、smoke、harness、benchmark 之类标为 `tooling` 排在后面。**分数只决定阅读顺序。**

在 PostHolder（TypeScript，约 5.4 万行）上跑一次约 5 秒：前 10 个产品簇里有 `employees.ts`（C2）和 `dispatcher.ts`（C8），正是它已经做过形式化验证（授权撤销）的两个文件。

## C2 选目标：fv-targets

`target-surveyor`（survey 模式）写，`fv survey draft` 给骨架，`fv survey check` 检查：

| 字段 | 规则（出处） |
|---|---|
| `survey.digest` | 钉住普查文件；重扫仓库，信号或已有检查变了就判 STALE |
| `correctness` 六个话题 | entry_points、untrusted_input、input_size、expected_outcomes、refused_resources、properties（OSS Verify 第 1 步，从 fuzz 目标推广到任意目标）；`observed` 要有逐字锚点，`answered` 要指向维护者回答过的问题，`not_applicable` 要写理由；TODO 不过 |
| `questions` | ≤5 个，问号结尾，由人（或附授权原话的委托 agent）回答——“Do not guess an answer” |
| `targets[].promise` / `harm` | 各一句话（pstack：不懂验证语言也能看懂） |
| `targets[].anchors` | 逐字出现在仓库文件里（pstack：true to the code） |
| `targets[].signals` / `source` | 引用普查的信号；用户点名的写 `source: {kind: user, quote}` |
| `targets[].why_tests_miss` | 好目标是测试很少走到的承诺 |
| `targets[].route` / `tool` | 五种路由；工具与语言匹配（Kani / Verus 只验 Rust，CrossHair 只验 Python……）；本机没装就写 `install`；没有验证器就写 `no_verifier_reason`；状态性风险不走模型检查要写 `route_reason` |
| `targets[].scope` | verified、bounds、assumptions、not_covered（≥1 条）——pstack 的诚实范围，OSS Verify `what-gets-proven.md` 把每个例外都列出来 |
| 第 1 名的 `why_first` | 最强的，不是最容易的 |
| `dismissed` | 前 N 个产品簇、每个已有 fuzz / 性质测试，要么被目标引用 / 抬升，要么写理由。没有理由的跳过就是静默丢弃 |

## C4 抬升已有测试：fv-props

OSS Verify 的原话是 “A proof is only as strong as its fuzz target”。无论之后是证明、模型检查还是只跑生成输入，先保证被抬升的检查能失败：

```bash
$FV props check --props props.json [--review props-review.json] --upstream $UP     # 静态（E0）
$FV props run   --props props.json --out <回执> [--work <新目录>]                  # 隔离副本里跑（E1）
```

`run` 把仓库复制到工作目录（`.git` 不复制，`isolation.link` 里的依赖目录只读链接），先跑每个检查的见证命令（必须通过；声明了 `reach_marker` 时输出必须有它），再对每个破坏：在副本里把那一行的 `old` 换成 `new`，跑命令，恢复原文。

| 破坏的结果 | 含义 |
|---|---|
| CAUGHT | 命令失败，输出里有这个检查的 `fires_with` |
| WRONG_CHECK | 命令失败，但不是这个检查发现的 |
| MISSED | 测试在坏代码上照样通过：这个检查什么都没查 |
| NOT_APPLIED / ERROR | 那一行没有 `old`；或命令超时 / 起不来 |

全部 CAUGHT、见证全部通过才是 ABLE_TO_FAIL。`fv validate` 只凭回执里记录的结果重新推导判定。

示例 `assets/example-ticket/survey/props.json` 从 `impl/test_properties.py` 抬出 NoOversell 与 Conservation：`AND remaining > 0` → `AND remaining > -1` 让 NoOversell 失败，`VALUES (?, 'success')` → `VALUES (?, 'failed')` 让 Conservation 失败。StockNonNegative 与 SoldNeverDecreases 找不到让它们**先**失败的一行改动，没有抬，写进了 T2 的 `not_covered`。

## C5 函数契约：fv-function-specs

```bash
$FV contracts check --specs function-specs.json --upstream $UP --run [--out <回执>]    # 回执 E0，记录每次重跑；fv validate 重新推导
```

检查：规格不用 FM-Agent 规则 3 列出的含糊词、不叙述调用了哪个 helper（规则 2）；被调函数不在调用者之前的层；每个函数都有 MATCH / MISMATCH；MISMATCH 有四项 gaps 和探针。`--run` 从仓库根目录重跑每个探针，按 bug_validator Step 2e 从输出重新推导，和记录不一致就拒绝。判定看**行首关键字**，不搜全文的词（原文：“Print exactly `CONFIRMED` or `NOT CONFIRMED` … with any additional detail after the keyword”）：非零退出或任何一行以 ERROR 开头是 error；一行以 NOT CONFIRMED 开头是 not_confirmed；一行以 CONFIRMED 开头是 confirmed；两种判定行都有、或都没有，是 error。`ERROR: … CONFIRMED …`、`NOT  CONFIRMED`（两个空格）在 1.4.0 曾被读成 confirmed，1.4.1 起不再如此（PostHolder 入口 C 的 T6 发现）。`--out` 写 E0 回执（`contracts`），`fv validate` 用记录的输出重新推导每个探针的状态。

示例的探针 B1 经 `tickets` 模块的公开接口复现了 check-then-act 变体的超卖：`CONFIRMED - answers ['success', 'success'], sold 2 of 1, remaining -1`。

## 代码级验证器：证据上限

| 引擎 | 命令（`fv external --engine …`） | 最好的判定 | 等级 | 不算通过的情况 |
|---|---|---|---|---|
| kani | `cargo kani [autoharness -Z autoharness]`，spec 是 Cargo.toml | PASS | E4 | 有 Failed Checks；“Complete - 0 successfully verified” 或没有 SUCCESSFUL |
| dafny / verus | `dafny verify <file>` / `verus <file>` | PASS | E4 | 有 error；有 time out（INCOMPLETE）；0 verified |
| lean | `lake build`，spec 是 lakefile | PASS | E4 | 输出有 `declaration uses 'sorry'`（INCOMPLETE） |
| cbmc / esbmc | `<tool> <file> [--unwind N]` | BOUNDED_PASS | E2 | VERIFICATION FAILED |
| crosshair | `crosshair check --report_all [--per_condition_timeout N] <file>` | NO_COUNTEREXAMPLE_FOUND | E1 | 有 error；“no checkable functions”；没有任何条件被报告 |

本次只真实运行过 CrossHair 0.0.113（通过、反例、未确认、无可检查函数四种输出都按实际输出测过）；其余引擎的解析只对它们文档里的输出格式测过。

## 和其他入口怎么接

- `stateful-model` 目标就是入口 B 的起点：普查的锚点、修复历史和 `why_tests_miss` 交给 `model-builder`（analysis）写 Specula brief。
- `property-lift` 与 `generated-inputs` 的 ABLE_TO_FAIL 回执（E1）可以作为实现契约验收测试的负对照依据。
- `function-contracts` 复现的缺陷路由 `fv_implementation_defect`，与反例分诊相同。
- 尚未接进 AI-DLC 状态机：`formal configure` 仍以模块（合同 + 模型）为单位，入口 C 是选出模块之前的一步。
