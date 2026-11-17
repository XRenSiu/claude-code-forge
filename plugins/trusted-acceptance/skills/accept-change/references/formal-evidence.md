# 形式化证据：怎么读、怎么核、能说什么

合同里有并发、一致性、权限、重试这类状态性承诺时读本文件。验收方不建模、不改规则，只做三件事：确认证据对应**已批准**的规则和模型；确认证据等级够；能重算时重算一遍，不相信报告里的结论。

工具是同目录的 `scripts/fv.py`（fvkit，Python 3.9+ 标准库；YAML 输入需要 PyYAML）。AI-DLC 的 `formal-verify` 技能带一份逐字相同的副本，开发侧和验收侧用的是同一个检查器。

## 证据分级：不同等级不能混称“已证明”

| 级别 | 产生方式 | 最多能声称 | 不能声称 |
|---|---|---|---|
| E0 静态审阅 | `fv lint`、人工阅读 | 完成了静态审查 | 已验证正确 |
| E1 模拟 | `fv simulate`、`quint run` | 抽样路径没有发现问题 | 所有路径都没问题 |
| E2 模型检查 | `fv check` / `fv qualify`、TLC、Apalache、`quint verify` | 这个模型、这个范围、这些假设下没有违反性质的路径 | 生产代码没有缺陷 |
| E3 实现验收 | `fv conform`（真实代码轨迹对模型的一致性 + 源码映射新鲜度） | 真实实现通过了这些具体的、留存的检查 | 所有输入和所有执行都已证明 |
| E4 代码级证明 | 外部工具（Lean / Kani / Aeneas 等） | 声明假设下，被覆盖代码满足指定性质 | 未建模的外部服务和整个系统可靠 |

`BOUNDED_PASS`（有界探索）、`NO_VIOLATION_SAMPLED`（模拟）、`INCOMPLETE`、`UNKNOWN` 都不是 PASS。fvkit 回执一律是 `local_advisory`：它证明“字节一致、逻辑自洽、可重放”，不证明采集者是谁。

## 回执里核什么（`validate-formal` 与 gate 共用同一套校验）

```bash
python3 "$SKILL_DIR/scripts/acceptance.py" validate-formal qualify.json \
  --model /approved/model.yaml --rerun --min-level E2 --expect QUALIFIED
python3 "$SKILL_DIR/scripts/acceptance.py" validate-formal conform.json \
  --model /approved/model.yaml --rerun --min-level E3 --expect CONFORMS --trace t1.jsonl --trace t2.jsonl
```

- **身份**：回执的 model / contract / properties 摘要必须等于传入的已批准文件；换了模型或改弱了规则，摘要就对不上。
- **自洽**：verdict 由结果重新推出（有一条 FAIL 就不能是 PASS；不完整的探索不能是 PASS；源码映射不新鲜或有一条轨迹不符就不能是 CONFORMS）。
- **反例重放**：每个反例、每个可达见证都在模型里逐步重放，最后一步必须真的违反（或满足）对应性质；活性反例必须是闭合的套索。
- **重算（`--rerun`）**：用当前检查器重跑模型检查、资格判定（含变异）或轨迹一致性，确定性字段必须逐项相同。不同构建的 fvkit 产生的回执不做重算比较，直接拒绝，要求用当前构建重跑。
- **外部引擎**：重新解析留存的原始输出。`quint run` 永远不能是 PASS；`quint verify` / Apalache 最多是 `BOUNDED_PASS`。

## 受保护 gate 的形式化要求（policy schema 2）

`acceptance-control/gate.py` 接受 `schema_version: 2` 的政策：v1 全部字段，加上 `formal` 数组。每一条由维护者在批准时固定：

```json
{"check_id": "ticket-oversell", "min_level": "E3", "model_digest": "sha256:…", "contract_digest": "sha256:…",
 "properties_digest": "sha256:…", "pass_verdicts": ["CONFORMS"], "rerun": true}
```

完整例子见 [formal-policy.example.json](../assets/formal-policy.example.json)。对每条要求，gate 按以下顺序判定，任何一步失败都是 `blocked`：

1. 该检查的证据里至少有一份 `fv-receipt`；每一份都按上一节校验，且摘要等于政策固定的摘要。
2. `rerun: true` 时，必须恰有一份 `fv-model` 和一份 `fv-contract` 证据，解析后的摘要等于政策；gate 用它们重跑资格判定，用 `fv-trace` 证据重算轨迹一致性。
3. `conform` 回执的 `source.head` 必须等于本次 binding 的 `candidate_sha`：给别的候选做的实现证据不能拿来用。
4. 检查状态为 pass 时，至少一份回执的等级 ≥ `min_level` 且 verdict 属于 `pass_verdicts`；任何一份负面回执都不能和 pass 并存。
5. 检查状态为 fail 时，形式化证据不能全是正面的；全是正面就说明检查失败和证据自相矛盾。可复现的实现缺陷照常进入 `needs_repair`。

同一检查可以有多条要求，例如一条 E2 `QUALIFIED`（设计已审定），一条 E3 `CONFORMS`（实现与设计一致）。v1 政策的行为不变。

## 采集侧的责任（gate 做不到的部分）

gate 不读候选仓库、也不运行候选代码。源码映射是否新鲜、轨迹是否真的来自候选的运行，要由受保护采集者在候选检出上运行 `fv conform` / `fv ci` 来保证，采集者与证据库的身份由部署方认证。项目自己跑出来的回执是 `project-self-check` 级别的输入，可以提交，但只在受保护环境重算之后才算数。

## 分流

| 现象 | 去向 |
|---|---|
| 模型反例且已在真实代码中重放 | 实现缺陷：`needs_repair`，交 Harness，附反例和重放轨迹 |
| 反例只在模型里出现、真实代码不可能发生 | 模型失真：检查器维护，`checker_blocked`；修模型后由维护者重新批准摘要 |
| 规则本身有漏项或要改动 | 产品裁决：新合同版本 + 新审批；绝不在验收里改规则 |
| 源码映射 STALE / BROKEN | 模型过期：重审映射后 `fv source-map sync`，再重跑一致性 |
| 引擎缺失、超时、输出无法识别 | 环境问题：`infrastructure_blocked`，不当作通过，也不让实现返工 |

反模式：模型检查失败后，实现者把 `sold <= 1` 改成 `sold <= 2`，检查变绿就宣称完成。规则摘要由政策固定，`fv diff-contract` 能判出弱化，所以这条路走不通。
