import datetime

from src.memory import Store, month_range


def test_keyword_search():
    s = Store()
    s.add("和小王吃了火锅", datetime.date(2026, 9, 1), datetime.date(2026, 8, 3))
    assert len(s.search("火锅")) == 1


def test_month_range():
    assert month_range(datetime.date(2026, 9, 6)) == (datetime.date(2026, 8, 1), datetime.date(2026, 9, 1))
