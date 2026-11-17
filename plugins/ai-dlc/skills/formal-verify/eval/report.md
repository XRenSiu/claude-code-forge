# formal-verify — evaluation marker

**gate_pass: `static_only`** · tier: production · evaluated_layers: `[]` · date: 2026-11-17

> 这只是作者自检记录，**没有**经过独立评审。evaluated_layers 为空是有意的：作者给自己审一遍不算评估。

## 已跑过的（脚本证据，不是效果证据）

- 示例的完整闭环：初版设计 → 最短反例（exit 1）→ 修正设计 QUALIFIED（3 个 mutant 都被预期性质杀死）→ `validate --rerun` 结果相同 → 模型驱动向量 → 真实 SQLite 实现的轨迹：atomic 全部一致，check-then-act 不一致且触发运行时监控 → 真实线程并发测试。
- `eval/test_formal.py`：在真实 git 仓库里检查状态机接线——锁、资格、一致性、签字豁免、策略按 diff 推出模块、R17–R23 路由。每条拒绝都有一条放行的孪生。
- 变异证明：`formal_gate.py` / `aidlc_state.py` 上 5 个 fail-open 变异全部被冒烟杀死；fvkit 与 trusted-acceptance gate 上 12 个手工变异全部被它们的测试杀死。

## 没跑的（因此不声称）

- **效果层**：带 / 不带本 Skill 时，Agent 写出的模型是否更贴近真实原子边界、能否更早发现设计缺陷——没有对照实验。
- **外部引擎**：TLC / Apalache / Quint / FizzBee 没有在本仓库实际运行，适配器只用固定格式的样例输出测过解析；FizzBee 的输出格式没有对照真实安装核实。
- **规模**：内置检查器是显式状态枚举；示例规模很小（21 个状态）。大模型的性能与对称约简的收益只在单元测试规模上测过。
