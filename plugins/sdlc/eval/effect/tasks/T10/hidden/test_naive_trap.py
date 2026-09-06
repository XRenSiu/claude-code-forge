import inspect

from src import feed


def test_pin_carries_more_than_a_boolean():
    src = inspect.getsource(feed)
    assert any(k in src for k in ("until", "expires", "expire", "end", "到期", "过期")), "置顶没有终点"
    assert any(k in src for k in ("priority", "rank", "weight", "优先")), "置顶没有优先级"


def test_list_does_not_rank_by_the_boolean_alone():
    src = inspect.getsource(feed.Feed.list)
    assert 'p["pinned"]' not in src or "priority" in src or "until" in src, "排序还是只看布尔 pinned"
