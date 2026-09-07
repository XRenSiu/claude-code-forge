# 接口说明

The settlement service reads each transaction from the queue and posts it to an Account.
A transaction that fails validation is retried once. When a transaction is settled the
batch is closed. 每条 transaction 的金额按 R001 校验。
