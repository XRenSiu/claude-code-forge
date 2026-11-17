# 示例：只剩一张票，从需求一路走到可合并的证据

在仓库根目录运行（需要 PyYAML）。`FV` 指向本 Skill 的 `scripts/fv.py`；所有回执写到仓库外的临时目录。

```bash
FV="python3 plugins/ai-dlc/skills/formal-verify/scripts/fv.py"
EX=plugins/ai-dlc/skills/formal-verify/assets/example-ticket
OUT=$(mktemp -d)

# A3/A4：初版设计（先读后扣）→ 最短反例，两人都买成功，sold=2
$FV check --model $EX/model-check-then-act.yaml --out $OUT/check-then-act.json     # 退出 1

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
cp -R $EX /tmp/ticket && cd /tmp/ticket && git init -q && git add -A && git commit -qm init
$FV source-map sync --map source-map.yaml --model model.yaml --by <审阅人> --reason "锚点与动作一致"
git add -A && git commit -qm "reviewed mapping"
$FV ci --policy policy.yaml --base HEAD~1 --all --out /tmp/ticket-ci                # SATISFIED（E3）
```

`vectors.json` 是 `gen-tests` 的产物，已经入库。模型或合同一变，`fv ci` 就会要求重新生成。
