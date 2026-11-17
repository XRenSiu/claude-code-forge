# ticket-ordering：模型范围

- **检查的常量**：STOCK=1，USERS={alice, bob}。两个用户争一张票，已经覆盖“读到同一个值后各自提交”这类交错（小范围假设：更多用户只会出现同类交错的组合）。需要更大范围时，加 `symmetry: [USERS]`；这个模型带活性性质，对称约简会自动关闭。
- **完整性**：完整探索，21 个状态（见 qualify 回执的 stats 与 exhaustive_depth）。
- **原子动作**：request、read、buy（提交时的条件预占）、reject（同一条 UPDATE 返回 0 行）。每个动作对应 source-map.yaml 中的一段代码和原子性声明。
- **不覆盖（因此不声称）**：支付、退款、超时释放、崩溃恢复、多场次、补货。
- **假设**：A-NO-RESTOCK、A-FAIR（只用于活性）。数据库条件 UPDATE 的原子性由 `impl/test_concurrency.py` 的真实并发测试另行检验（E3），模型不证明它。
