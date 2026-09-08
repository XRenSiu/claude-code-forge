"""朴素痕迹：置顶只是一个布尔。

判的是**实质**：置顶有没有终点，以及排序有没有一个写在数据里的键。
2026-09-06（E-08）：这里曾要求源码里出现 `priority` 这个词，而一个用置顶时间排序的实现
（确定、可控、不看运气）实质满足却被判红——那是把作者的设计当成唯一答案。
"""
import inspect

from src import feed


def test_a_pin_has_an_end():
    src = inspect.getsource(feed)
    assert any(k in src for k in ("until", "expires", "expire", "expiry", "end", "到期", "过期")), \
        "置顶没有终点 —— 活动结束了还会挂在顶上"


def test_the_order_comes_from_stored_data_not_insertion():
    src = inspect.getsource(feed)
    assert any(k in src for k in ("priority", "rank", "weight", "优先", "pinned_at", "pin_at",
                                  "pinned_time", "at=", "seq", "order")), \
        "两条置顶之间没有任何一个写在数据里的排序键 —— 那就只能取决于插入顺序"


def test_list_does_not_rank_by_the_boolean_alone():
    src = inspect.getsource(feed.Feed.list)
    assert 'p["pinned"]' not in src or any(k in src for k in ("priority", "until", "at", "expire", "sort")), \
        "排序还是只看布尔 pinned"
