import inspect

from src import inbox


def test_views_are_consulted():
    src = inspect.getsource(inbox)
    assert "dwell_ms" in src and "fully_visible" in src, "曝光数据一个字段都没用上"


def test_unread_is_not_just_the_boolean():
    src = inspect.getsource(inbox.Inbox.unread)
    assert src.count('"read"') < 1 or "view" in src.lower() or "dwell" in src.lower(), \
        "unread() 还是只看布尔 read 字段"
