# 分诊、资格、CI 分层与持续维护

## 反例分诊：先归类，再动手

模型报出反例，只说明“这个模型允许坏结果”。只有确认模型如实反映了真实代码，它才成立为产品缺陷。分诊顺序：

1. **重放到真实代码。** `fv gen-tests --strategy counterexamples --counterexample <check 回执>` 生成重放向量，harness 驱动真实代码记录轨迹，再用 `fv trace-check` 核对。重放成功，就是 `implementation_defect`（或者设计本来如此：`design_defect`）。
2. **无法重放时，先质疑模型。** 原子边界拆得太细，或漏了数据库约束，都会造出不可能的反例，这是 `model_infidelity`：修模型，修 `source-map.yaml` 的 atomicity，再重新 qualify。
3. **规则没覆盖的情况**（超时、取消、重复请求这类需求本身没说的），是 `requirement_gap`，交还需求负责人。在 AI-DLC 里走 G2 变更提案。
4. **引擎、harness 或环境坏了**，是 `checker_defect`，不让产品返工。

判断“模型失真还是真实缺陷”按 Specula 的 spec-fidelity checklist 来，不凭感觉。`formal-reviewer`（triage 模式）先写下违反状态需要的前提，再为每个前提在实现里找守卫（`file:line`），然后对照模型：模型漏掉或放宽了某个守卫，就是 Case B（`model_infidelity`），写明模型改法后重跑；没有，就是 Case C。Case C 再按 Specula bug-classification 写状态（REPRODUCED / ENV_LIMITED / MASKED 或某种处置）和严重度。结果写进 `triage/<name>.yaml`（fv-cex-triage），用 `fv triage-check` 核对，或在 AI-DLC 里用 `formal triage --file …` 记录。核对结果给出路由：`fv_model_infidelity`；`fv_design_defect`（反例来自模型检查）；`fv_implementation_defect`（反例来自真实代码的轨迹）。

每次分诊在 `decisions.md` 追加一行（时间、反例或改动、分类、决定、签字人），然后
`aidlc_state.py fail --signal fv_<分类> --evidence <回执摘要或反例>`，路由表把它送到对应的层。
**任何分类下都不许改弱合同让检查变绿**；必须改规则时，`fv diff-contract` 会给出 WEAKENED，需要新的 G2 签字或 `fv approve` 记录。

## 实现一致性失败（07）怎么分流

| 现象 | 去向 |
|---|---|
| 约束的 evidence 不在代码里、测试失败、真实轨迹出现模型不允许的步、某个操作从没被执行过 | 实现缺陷：`fv_implementation_defect` → card，按契约修代码 |
| 负对照通过了（坏变体没被抓住） | 测试看不见它要防的缺陷：修测试，归到同一张卡 |
| 审阅发现代码有而模型没有的行为，处置为 `model_it` | 模型失真：`fv_model_infidelity` → plan，补模型后重走 04–05 |
| 审阅判定某条假设 `violated` | 规则依赖的前提不成立：`fv_requirement_gap` → task |
| 实现者回报 `CONTRACT_CHANGE_NEEDED`（契约做不到） | 回到 05：修改实现契约，必要时回到设计（04）；不在代码里另做设计 |

## 资格判定（FV-G1 的机器部分）

`fv qualify` 同时要求以下几条：

- 完整探索（或者策略允许有界，并且 `exhaustive_depth ≥ min_depth`），且没有任何反例；
- 每个 `reachable` 见证都到达了，没有一条 `leads_to` 是空洞的（from 条件从未成立）；
- 没有死动作（从未改变状态的动作，要么是建模错误，要么是多余）；
- 至少一个声明的 mutant，并且每个必需 mutant 都被它**预期**的性质杀死。被别的规则抓到记 `KILLED_BY_OTHER`，加载失败记 `ERROR`，都不算数；mutant 的探索被截断记 `UNKNOWN`，有界运行不能假装杀死过。

`--auto-mutants` 额外跑自动变异：去掉守卫、去掉守卫的一个合取项、跳过一个更新。存活者会列出来：要么规则太弱，要么那段守卫多余。它不计入资格结论，但应该在 G1/G2 时给人看。

最好的 mutant 来自历史：入口 A 里被反例推翻的初版设计、入口 B 里修复前的代码行为。把它们留在模型里，规则一旦被改弱，它们就会存活下来。

## CI 分层（防止每个 PR 都跑得太重）

| 层 | 何时 | 跑什么 |
|---|---|---|
| fast | 每个 PR，低风险模块 | lint + 小范围检查（允许有界）+ 已有反例回归 |
| core | 改了并发、事务、重试等关键代码 | 完整检查 + 必需 mutant + 源码映射 + 真实轨迹一致性 |
| deep | 定期或发版前 | 更大的边界 + 自动变异 + 外部引擎深检 |

```bash
python3 tools/fvkit/fv.py ci --policy verification/policy.yaml --base origin/$BASE --out "$RUNNER_TEMP/fv"
```

`fv ci` 对每个受影响模块：契约有变化时，与 base 版本做弱化检测，未批准的弱化判失败；然后做资格判定、源码映射检查和向量摘要检查，执行 `trace_command`，再做一致性判定。任何一步没跑、失败或失效，都判 UNSATISFIED。回执存进 `--out`，上传为 CI 产物。工作流模板见 `assets/formal-verification.yml`。

## 持续校准循环（借鉴 pstack maintain-formal-verification-skill）

```
受保护文件变化（fv impact / source-map verify → STALE）
  ↓ 读自 lock.commit 以来的 diff
模型是否仍准确描述当前代码？
  ├─ 不一致：更新模型与映射（不可削弱规则）→ 重新 qualify
  └─ 一致：审阅人执行 fv source-map sync --by … --reason …（新 lock，追加 sync-log）
  ↓
运行检查 + 真实轨迹一致性（含历史反例的重放向量）
  ↓
mutant 仍然被杀死（证明检查仍然有效）
  ↓
留下回执与新的 sync 提交
```

`sync` 要求受保护文件没有未提交的改动，并且记录审阅人。由 Agent 代为 sync 时，必须带上人的授权原话（`--signer-kind delegated_agent --authorization "…"`）。

## 外部引擎

```bash
fv external --engine tlc --tool /opt/tla2tools.jar --spec Spec.tla --config Spec.cfg --out r/tlc
fv external --engine quint-verify --spec model.qnt --invariant noOversell --bound 12 --out r/qv
fv external --engine quint-run    --spec model.qnt --invariant noOversell --samples 10000 --out r/qr   # 只有 E1
fv external --engine apalache --spec Spec.tla --invariant Inv --bound 10 --out r/ap
fv external --engine fizzbee --spec model.fizz --out r/fz
```

原始 stdout/stderr 与摘要都会留存，`fv validate` 会重新解析它们。引擎缺失、超时或输出无法识别都判 ERROR。这些引擎的规则与 fvkit 合同不共享摘要，需要人工确认二者表达的是同一组规则，再写进 trusted-acceptance 的政策。
