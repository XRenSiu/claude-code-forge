"""固定窗口限流。"""
import collections


class Limiter:
    def __init__(self, per_minute=60):
        self.per_minute = per_minute
        self._hits = collections.deque()

    def allow(self, now):
        """now: 单调秒（float）。返回 True 放行 / False 拒绝。"""
        while self._hits and now - self._hits[0] >= 60:
            self._hits.popleft()
        if len(self._hits) >= self.per_minute:
            return False
        self._hits.append(now)
        return True
