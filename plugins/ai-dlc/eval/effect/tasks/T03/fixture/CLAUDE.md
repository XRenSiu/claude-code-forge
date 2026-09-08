# 网关限流

Python 3.11，纯标准库。`allow(now)` 的 now 是单调秒，调用方保证不倒流。

- 跑测试：`python3 -m pytest -q`
- 限流在 `src/limiter.py`
