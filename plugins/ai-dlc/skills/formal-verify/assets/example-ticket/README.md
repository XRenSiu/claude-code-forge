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

# C3/C4：模型驱动的向量（覆盖每个迁移 + 重放旧反例）→ 真实 SQLite 实现 → 轨迹 → 一致性
$FV gen-tests --model $EX/model.yaml --strategy transitions,counterexamples \
    --counterexample $OUT/check-then-act.json --out $OUT/vectors.json
python3 $EX/impl/harness.py --vectors $OUT/vectors.json --out $OUT/traces            # atomic：没有不一致
$FV trace-check --model $EX/model.yaml $OUT/traces/*.jsonl                          # CONFORMS
python3 $EX/impl/harness.py --vectors $OUT/vectors.json --out $OUT/bad --variant check-then-act   # 退出 1
$FV trace-check --model $EX/model.yaml $OUT/bad/*.jsonl                             # NONCONFORMANT + NoOversell 监控
python3 $EX/impl/test_concurrency.py                                                # 真实线程竞争

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
