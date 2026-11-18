# 示例：只剩一张票，从需求一路走到可合并的证据

在仓库根目录运行（需要 PyYAML）。`FV` 指向本 Skill 的 `scripts/fv.py`；所有回执写到仓库外的临时目录。
`candidates/` 里的规则与模型候选是为演示而撰写的，代表两个互不可见的 AI 生成者（见 `../../references/generation.md`）。intake、审阅、brief 和分诊也都是演示用的，各自按 `../../upstream/` 里的上游流程写成（对应关系见 `../../references/upstream-methods.md`）。`rules-divergence.json` / `model-divergence.json` 里的裁决人、澄清问题的回答人都是示例。

```bash
FV="python3 $PWD/plugins/ai-dlc/skills/formal-verify/scripts/fv.py"
EX=plugins/ai-dlc/skills/formal-verify/assets/example-ticket
UP=plugins/ai-dlc/skills/formal-verify/upstream/UPSTREAM.json
OUT=$(mktemp -d)
$FV upstream verify $UP                                                              # INTACT：收录的上游原文没被改过

# G-1 到 G-5：AI 生成规则（必经）。清单的引文逐字存在、规范句一句不漏；两份隔离候选逐需求比较
$FV requirements-check --requirements $EX/requirements.yaml                          # COMPLETE
$FV intake-check $EX/rules-intake.yaml --requirements $EX/requirements.yaml --upstream $UP   # COMPLETE：Spec Kit clarify + Quint intake
$FV rules-divergence --requirements $EX/requirements.yaml \
    --candidate A=$EX/candidates/rules-a/contract.yaml --candidate B=$EX/candidates/rules-b/contract.yaml \
    --model $EX/model.yaml --out $OUT/rules-divergence.json                          # DIVERGENT：R1 有见证值 remaining=-2
$FV check-review $EX/rules-review.yaml --contract $EX/contract.yaml --triage $EX/rules-triage.yaml --upstream $UP   # REVIEWED（FVS 审阅 + 作者处置）
$FV gen-evidence rules --contract $EX/contract.yaml --divergence $EX/rules-divergence.json --intake $EX/rules-intake.yaml \
    --review $EX/rules-review.yaml --review-triage $EX/rules-triage.yaml --upstream $UP          # READY（裁决已在入库的报告里）

# G-6 到 G-8：AI 建模（必经）。两份隔离模型候选在观察者层面比较
$FV model-divergence --candidate A=$EX/candidates/model-a/model.yaml --candidate B=$EX/candidates/model-b/model.yaml \
    --out $OUT/model-divergence.json                                                 # DIVERGENT：B 允许售罄后再次提交
$FV model-review-check $EX/model-review.yaml --model $EX/model.yaml --upstream $UP # REVIEWED：Quint review（运行时检查重算）+ Specula 粒度审计
$FV gen-evidence model --model $EX/model.yaml --divergence $EX/model-divergence.json --review $EX/model-review.yaml --upstream $UP   # READY

# 入口 B 的 Specula 代码分析：brief 第 1–7 节、defect ledger 与 JSON 一致、每个 Scenario / 不变量 / 发现都有落点
$FV brief-check --brief $EX/code-first/modeling-brief.md --ledger $EX/code-first/defect-ledger.json \
    --coverage $EX/code-first/brief-coverage.yaml --model $EX/model.yaml --upstream $UP          # COMPLETE，Category B

# A3/A4：初版设计（先读后扣）→ 最短反例，两人都买成功，sold=2
$FV check --model $EX/model-check-then-act.yaml --out $OUT/check-then-act.json     # 退出 1
$FV triage-check $EX/triage/check-then-act.yaml --model $EX/model-check-then-act.yaml --upstream $UP   # TRIAGED：Case C → fv_design_defect

# 修正设计：提交时原子预占 → 完整检查 + 见证 + 无死动作 + 3 个 mutant 被预期规则杀死
$FV qualify --model $EX/model.yaml --out $OUT/qualify.json                          # 退出 0，QUALIFIED
$FV validate $OUT/qualify.json --model $EX/model.yaml --rerun --min-level E2

# 05 实现契约：把 QUALIFIED 模型转成编码 agent 要执行的约束。derived 一节由 fvkit 推导（buy 对共享库存
#    read-modify-write → 必须原子；read / reject 被 buy 并发改写 → 要并发测试；每条性质、mutant、假设都要验收项），
#    其余（代码位置、事务机制、幂等键、出错 / 超时 / 冲突 / 重试的行为、测试命令与负对照）按上游流程填写
$FV impl-contract draft --model $EX/model.yaml --qualification $EX/receipts/qualify.json --out $OUT/impl-draft.yaml   # 骨架，TODO 待填
$FV impl-contract check $EX/impl-contract.yaml --model $EX/model.yaml --upstream $UP # READY

# C3/C4：模型驱动的向量（覆盖每个迁移 + 重放旧反例）→ 真实 SQLite 实现 → 轨迹 → 一致性
$FV gen-tests --model $EX/model.yaml --strategy transitions,counterexamples \
    --counterexample $OUT/check-then-act.json --out $OUT/vectors.json
python3 $EX/impl/harness.py --vectors $OUT/vectors.json --out $OUT/traces            # atomic：没有不一致
$FV trace-check --model $EX/model.yaml $OUT/traces/*.jsonl                          # CONFORMS
python3 $EX/impl/harness.py --vectors $OUT/vectors.json --out $OUT/bad --variant check-then-act   # 退出 1
$FV trace-check --model $EX/model.yaml $OUT/bad/*.jsonl                             # NONCONFORMANT + NoOversell 监控
python3 $EX/impl/test_concurrency.py                                                # 真实线程竞争

# 07 实现一致性：契约里的约束在代码里（锚点逐字存在）、性质 / 并发 / MBT 测试通过且负对照（check-then-act）
#    确实失败、真实轨迹每一步都是模型允许的迁移且四个操作都出现过、旧反例在真实代码里重放为被拒、
#    全新上下文的实现审阅（Spec Kit analyze + Quint 差距问题）没有未处置的问题
$FV impl-verify $EX/impl-contract.yaml --model $EX/model.yaml --review $EX/impl-review.yaml --upstream $UP \
    --out $OUT/implement.json                                                        # IMPLEMENTS（E3）
$FV validate $OUT/implement.json --model $EX/model.yaml --rerun --expect IMPLEMENTS  # 由记录的各部分重新判定 + 重查轨迹

# 规则不能被悄悄改弱
sed 's/expr: "sold <= STOCK"/expr: "sold <= STOCK + 1"/' $EX/contract.yaml > $OUT/weak.yaml
$FV diff-contract $EX/contract.yaml $OUT/weak.yaml --model $EX/model.yaml          # WEAKENED，退出 1
```

源码映射需要 git 历史（`sync` 记录审阅时的提交），`policy.yaml` 演示 `fv ci` 的模块与证据要求。把本目录复制成一个独立仓库试：

```bash
cp -R $EX /tmp/ticket && cp -R plugins/ai-dlc/skills/formal-verify/upstream /tmp/ticket/upstream   # policy.yaml 的 upstream: 指向这里
cd /tmp/ticket && git init -q && git add -A && git commit -qm init
$FV source-map sync --map source-map.yaml --model model.yaml --by <审阅人> --reason "锚点与动作一致"
git add -A && git commit -qm "reviewed mapping"
$FV ci --policy policy.yaml --base HEAD~1 --all --out /tmp/ticket-ci                # SATISFIED（E3）
```

`vectors.json` 是 `gen-tests` 的产物，已经入库。模型或合同一变，`fv ci` 就会要求重新生成。

实现契约带来过一次真实的代码改动：契约要求“出错 / 超时后重试”必须安全，而最初的 `purchase` 被重复调用会再扣一次库存，`request` 重复提交会抛主键异常（code-first brief 里的 D-2）。现在的代码在事务里先检查请求状态，并改用 `INSERT OR IGNORE`；契约的 `idempotency.evidence` 指向这两处代码。删掉其中一处，`impl-verify` 就判 NOT_IMPLEMENTED。

## 入口 C：只给仓库，先普查再选目标（`survey/`）

假装只拿到 `impl/` 这个“仓库”，没有任何需求文档。`survey/` 里的目标、回答、审阅和推理是为演示而撰写的（回答人是示例），探针和破坏是真实可跑的。

```bash
S=$EX/survey
$FV survey scan --root $EX/impl --out $OUT/survey.json --history 0               # 26 个信号；C1 tickets.py（transaction / quantity / state-machine）
$FV survey check --survey $S/survey.json --targets $S/targets.json --upstream $UP # READY：六个“正确”话题、两个由人回答的问题、三个目标
# T1 stateful-model → 就是上面的入口 B（model.yaml、source-map.yaml、code-first/）
# T2 property-lift：把 test_properties.py 的 NoOversell / Conservation 抬成能失败的检查
$FV props check --props $S/props.json --review $S/props-review.json --upstream $UP  # READY（OSS Verify 第 3 步 + review.md F 节）
$FV props run --props $S/props.json --out $OUT/props.json                          # ABLE_TO_FAIL（E1）：两个一行破坏都以各自的标记失败
$FV validate $OUT/props.json --expect ABLE_TO_FAIL
# T3 function-contracts：FM-Agent 行为规格 + 经公开入口的探针
$FV contracts check --specs $S/function-specs.json --upstream $UP --run          # COMPLETE；B1 重跑复现：sold 2 of 1，路由 fv_implementation_defect
```

把 `props.json` 里 P1 的破坏改成不影响结果的一行（比如注释里的字），`props run` 判 WEAK（MISSED）：从没见过失败的检查不算检查。
