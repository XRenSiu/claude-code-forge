# 订单定价

Python 3.11，纯标准库。分层是硬约定：

- `src/domain/**` 是领域层，**不许 import `src/app/**`**（领域不知道有 HTTP 这回事）
- `src/app/**` 是应用层，可以 import 领域层
- 金额在领域层一律是分（int），格式化只发生在应用层

跑测试：`python3 -m pytest -q`
