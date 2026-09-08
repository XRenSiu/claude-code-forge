"""已读 = 真的看到过，不是打开过会话。两条用例上，布尔模型给相反答案。"""
from src.inbox import Inbox


def _unread_ids(ib):
    return {m["id"] if isinstance(m, dict) else m for m in ib.unread()} if not ib.unread() or isinstance(
        ib.unread()[0], dict) else set(ib.unread())


def test_opening_without_seeing_does_not_clear():
    """打开会话但那条消息压根没露出来 —— 它还是未读。"""
    ib = Inbox()
    ib.add(1, "在屏幕外的那条")
    ib.open_thread()
    ids = {m["id"] for m in ib.unread()} if ib.unread() and isinstance(ib.unread()[0], dict) else set(ib.unread())
    assert 1 in ids, "打开会话就把没看到的消息清零了 —— 用的是布尔标记模型"


def test_a_real_long_view_marks_read():
    ib = Inbox()
    ib.add(2, "认真看过的那条")
    ib.record_view(2, dwell_ms=3000, fully_visible=True)
    ids = {m["id"] for m in ib.unread()} if ib.unread() and isinstance(ib.unread()[0], dict) else set(ib.unread())
    assert 2 not in ids, "完整露出 3 秒还算未读"


def test_a_glance_does_not_mark_read():
    ib = Inbox()
    ib.add(3, "飞快划过去的那条")
    ib.record_view(3, dwell_ms=40, fully_visible=False)
    ids = {m["id"] for m in ib.unread()} if ib.unread() and isinstance(ib.unread()[0], dict) else set(ib.unread())
    assert 3 in ids, "划过去 40ms 也算看过了"
