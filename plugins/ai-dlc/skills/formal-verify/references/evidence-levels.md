# 证据等级与回执

对外汇报时，不同等级必须分开写。“模型检查通过”加上“测试通过”，也不等于“数学证明了整个项目正确”。

| 级别 | 产生方式 | 最多能声称 | 不能声称 |
|---|---|---|---|
| E0 静态审阅 | `fv lint`、`fv trace-rules`、`fv gen-evidence`（AI 生成过程的证据）、人工阅读 | 完成了静态审查；规则与模型经过多份隔离生成、比较、裁决与审阅 | 已验证正确；规则一定忠于需求 |
| E1 模拟 | `fv simulate`、`quint run` | 这些抽样路径没有发现问题 | 所有可能路径都没问题 |
| E2 模型检查 | `fv check` / `qualify`、TLC、Apalache、`quint verify` | 这个模型、这个范围、这些假设下，没有违反性质的路径 | 生产代码没有缺陷 |
| E3 实现验收 | `fv conform`、`fv trace-check`、`fv impl-verify`（实现契约的代码证据、测试与负对照、轨迹、反例重放、审阅）、真实并发测试 | 真实实现通过了这些具体的、留存的检查 | 所有输入和所有真实执行都已证明 |
| E4 代码级证明 | 外部工具（Lean / Kani / Aeneas） | 声明假设和覆盖范围内，指定性质已被证明 | 未覆盖的外部服务、环境和整个系统都可靠 |

## verdict 词表

| 命令 | 正面 | 负面 | 不确定（退出码 3，永不报绿） |
|---|---|---|---|
| check | PASS（完整探索） | FAIL（有反例） | BOUNDED_PASS（有界，看 `exhaustive_depth`）· INCOMPLETE |
| simulate | — | FAIL | NO_VIOLATION_SAMPLED |
| qualify | QUALIFIED | NOT_QUALIFIED | — |
| trace-check / conform | CONFORMS | NONCONFORMANT | INCOMPLETE |
| impl-contract | READY | NOT_READY | — |
| impl-verify | IMPLEMENTS | NOT_IMPLEMENTED | — |
| source-map verify | FRESH | STALE · BROKEN | — |
| diff-contract | NOT_WEAKENED · APPROVED | WEAKENED | UNKNOWN |
| ci | SATISFIED | UNSATISFIED | — |
| requirements-check | COMPLETE | GAPS | — |
| trace-rules | TRACEABLE | GAPS | — |
| rules-divergence / model-divergence | AGREED | DIVERGENT（议程，需裁决） | — |
| check-review | REVIEWED | NOT_REVIEWED | — |
| gen-evidence | READY | NOT_READY | — |
| external（quint-run） | — | FAIL | NO_VIOLATION_SAMPLED |
| external（quint-verify / apalache） | BOUNDED_PASS | FAIL | ERROR |

退出码：0 正面，1 负面，2 输入或求值错误，3 不确定。

## 回执（fv-receipt）

```
schema_version, kind: fv-receipt, command, invocation_id (uuid4), authority: local_advisory,
engine {name, version, digest}      # fvkit 源码摘要；--rerun 要求与当前构建一致
inputs {model {id, digest}, contract {id, version, digest, properties_digest, property_ids}}
settings, result, verdict, evidence_level, claims {may_claim, may_not_claim}, started_at, finished_at
```

- 回执只新建，不覆盖（输出路径已存在就报错）。失败的回执和成功的一样要保留。
- `fv validate <receipt> --model … [--rerun] [--min-level E3] [--expect QUALIFIED]` 会重新推出 verdict、重放每个反例和见证；加 `--rerun` 时重新执行，确定性字段必须逐项相同。
- conform 与 implement 回执里的 `result.source.head` 绑定生成证据时的提交；trusted-acceptance 的 gate 要求它等于被验收的候选。
- implement 回执（07）的理由完全由记录的各部分推出（契约检查、代码证据、测试与负对照的退出码、轨迹结论、操作覆盖、反例重放、审阅），`fv validate` 会重新推一遍，`--rerun` 时重查原始轨迹。测试本身不会被重跑：验收方不执行候选代码。
- 回执证明“字节一致、逻辑自洽、可重放”，**不证明是谁跑的**。正式验收的采集者身份由受保护控制区认证。
