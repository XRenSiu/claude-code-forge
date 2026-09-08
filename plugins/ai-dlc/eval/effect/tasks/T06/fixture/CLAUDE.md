# 记忆产品

Python 3.11，纯标准库。`src/memory.py` 是记忆库。

- 跑测试：`python3 -m pytest -q`
- 每条记忆有两个时间：`created_at`（写进库的时间）和 `happened_at`（这件事发生的时间，可能为 None）
