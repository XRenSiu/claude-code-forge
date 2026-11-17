# model-a：生成者 A 的说明（Quint quint-modeling Step 7 handoff）

## What it covers

- 两个用户争 STOCK=1 张票：request → read → buy / reject 四个动作，购买在提交时检查库存。
- 合同的六条性质全部在这个范围内检查；活性依赖 read / buy / reject 的弱公平（对应 A-FAIR）。

## What it does NOT cover

- 支付、退款、超时释放、崩溃恢复、多场次、补货（需求的不在范围清单）。
- 数据库条件 UPDATE 的原子性：模型把它当作一个动作，真实原子性由并发测试检验。

## When to update

- 购买路径的事务边界或判定条件变了：先改模型、重跑检查，再改代码。
- 合同新增观测量或性质时，补上精化映射。
