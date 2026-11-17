# formal-verify — evaluation marker

**gate_pass: `static_only`** · tier: production · evaluated_layers: `[]` · date: 2026-11-17

> 这只是作者自检记录，**没有**经过独立评审。evaluated_layers 为空是有意的：作者给自己审一遍不算评估。

## 已跑过的（脚本证据，不是效果证据）

- AI 生成阶段（示例）：清单引文逐字存在、规范句无遗漏（编造的引文被拒）；两份规则候选在 R1 上有语义分歧并给出见证值 remaining=-2；两份模型候选在“售罄后再次提交”上有可观测分歧；裁决与审阅齐备时生成证据 READY；未裁决、只有一份候选、采纳物未被比较、候选被删、code-first 未校准时 NOT_READY。
- 上游流程（2026-11-17 起）：收录的 7 个项目 36 个文件 `fv upstream verify` 为 INTACT（改一个字节即 TAMPERED）；示例的 intake、FVS 审阅与处置、模型审阅、入口 B 的 Specula brief 与 coverage、反例分诊都按上游规则检查通过，每项都有被拒的孪生（问题写成标签、REVISE 判定、该拆未拆的动作、ledger 少一条、Case B 没有被漏的守卫……）。
- 实现契约与实现一致性（05 / 07）：示例的实现契约由 `fv impl-contract draft` 从 QUALIFIED 模型推导后填写，READY；契约要求的幂等重试让示例代码改了一次（`purchase` 先查请求状态、`request` 用 `INSERT OR IGNORE`）。`fv impl-verify` 跑性质、活性、并发、MBT 四组测试，三组负对照（check-then-act 变体）都确实失败，真实轨迹逐步符合模型且四个操作都出现过，旧反例重放被拒，实现审阅通过 → IMPLEMENTS。孪生：删掉幂等检查 → NOT_IMPLEMENTED；契约把事务写成 none → NOT_READY；负对照改成通过 → 拒绝；伪造的回执 → 校验拒绝。
- 示例的完整闭环：初版设计 → 最短反例（exit 1）→ 修正设计 QUALIFIED（3 个 mutant 都被预期性质杀死）→ `validate --rerun` 结果相同 → 模型驱动向量 → 真实 SQLite 实现的轨迹：atomic 全部一致，check-then-act 不一致且触发运行时监控 → 真实线程并发测试。
- `eval/test_formal.py`：在真实 git 仓库里检查状态机接线——锁、资格、一致性、签字豁免、策略按 diff 推出模块、R17–R23 路由。每条拒绝都有一条放行的孪生。
- 变异证明：`formal_gate.py` / `aidlc_state.py` 上 5 个 fail-open 变异全部被冒烟杀死；fvkit 与 trusted-acceptance gate 上 12 个手工变异全部被它们的测试杀死。

## 没跑的（因此不声称）

- **实现契约的质量**：derived 部分是机械推导的；人写的部分（机制、故障行为、测试选择）只被检查“写了、在代码里、测试按预期”，没有被检查“是最好的设计”。示例的契约与实现审阅为演示撰写，不是隔离 agent 的运行记录。
- **生成质量**：示例中的候选、intake、审阅、brief 与分诊是为演示撰写的，不是真实隔离 agent 执行上游流程的运行结果；分歧检查衡量生成者之间是否一致，不衡量是否正确；上游产物的检查只证明“步骤做了并记下了”，不证明做得好。
- **效果层**：带 / 不带本 Skill 时，Agent 写出的模型是否更贴近真实原子边界、能否更早发现设计缺陷——没有对照实验。
- **外部引擎**：TLC / Apalache / Quint / FizzBee 没有在本仓库实际运行，适配器只用固定格式的样例输出测过解析；FizzBee 的输出格式没有对照真实安装核实。
- **规模**：内置检查器是显式状态枚举；示例规模很小（21 个状态）。大模型的性能与对称约简的收益只在单元测试规模上测过。
