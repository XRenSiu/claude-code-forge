import datetime

from src.feed import Feed


def test_pinned_first():
    f = Feed()
    f.add(1, "旧", datetime.date(2026, 1, 1))
    f.add(2, "新", datetime.date(2026, 9, 1))
    f.pin(1)
    assert [p["id"] for p in f.list()] == [1, 2]


def test_default_order_is_recent_first():
    f = Feed()
    f.add(1, "旧", datetime.date(2026, 1, 1))
    f.add(2, "新", datetime.date(2026, 9, 1))
    assert [p["id"] for p in f.list()][0] == 2
