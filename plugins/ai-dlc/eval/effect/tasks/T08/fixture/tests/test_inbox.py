from src.inbox import Inbox


def test_open_marks_read():
    ib = Inbox()
    ib.add(1, "hi")
    assert len(ib.unread()) == 1
    ib.open_thread()
    assert ib.unread() == []


def test_views_are_recorded():
    ib = Inbox()
    ib.add(1, "hi")
    ib.record_view(1, dwell_ms=50, fully_visible=False)
    assert len(ib.views) == 1
