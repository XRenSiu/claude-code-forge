"""朴素实现的两个痕迹：只认 created_at，或把没有 happened_at 的记忆直接丢掉而不说明。"""
import datetime
import inspect

from src import memory
from src.memory import Store


def test_created_at_is_not_the_only_time_used():
    src = inspect.getsource(memory)
    assert "happened_at" in src, "整份实现里没出现 happened_at —— 那就只可能是按写入时间做的"


def test_memory_without_happened_at_is_handled_not_silently_dropped():
    s = Store()
    s.add("不知道什么时候的事", created_at=datetime.date(2026, 8, 10), happened_at=None)
    src = inspect.getsource(memory)
    assert any(k in src for k in ("None", "or ", "fallback", "回退", "缺")), \
        "没有任何一处处理 happened_at 为空的情况"
