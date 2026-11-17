# ticket-ordering：决定（只增不删）

| at | 反例 / 改动 | 分类 | 决定 | by |
|----|-------------|------|------|----|
| 2026-11-17 | `fv check --model model-check-then-act.yaml`：alice 读到 1 → bob 读到 1 → alice 购买 → bob 购买，sold=2（违反 NoOversell、StockNonNegative） | design_defect | 模型如实反映了初版设计，规则不改。设计改为在提交时做一条原子条件 UPDATE（model.yaml 的 buy / reject 守卫）；初版设计作为 mutant `check-then-act` 留在模型里 | example |
| 2026-11-17 | `fv qualify --model model.yaml`：QUALIFIED，21 个状态，3 个 mutant 都被预期性质杀死 | — | 设计门槛通过，交给实现 | example |
| 2026-11-17 | 真实实现 `impl/tickets.py`：atomic 变体的 10 条向量轨迹全部 CONFORMS；保留的 check-then-act 变体在重放向量上 NONCONFORMANT，运行时监控报 NoOversell | implementation_defect（仅示例变体） | 生产路径用 atomic；check-then-act 变体留作“检查真的能看见缺陷”的对照 | example |
