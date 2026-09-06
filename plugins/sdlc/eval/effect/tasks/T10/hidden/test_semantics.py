"""置顶是一段关系，不是一个布尔。过期与撞车两条用例上，布尔模型给相反答案。"""
import datetime

from src.feed import Feed

TODAY = datetime.date(2026, 9, 6)


def _pin(f, pid, **kw):
    try:
        return f.pin(pid, **kw)
    except TypeError:
        return f.pin(pid)


def _ids(f):
    try:
        return [p["id"] for p in f.list(TODAY)]
    except TypeError:
        return [p["id"] for p in f.list()]


def test_an_expired_pin_falls_off():
    f = Feed()
    f.add(1, "上个月的活动公告", datetime.date(2026, 8, 1))
    f.add(2, "今天的新帖", datetime.date(2026, 9, 5))
    _pin(f, 1, until=datetime.date(2026, 8, 31))
    assert _ids(f)[0] == 2, "活动结束了公告还挂在顶上 —— 置顶没有终点"


def test_two_pins_have_a_deterministic_order():
    f = Feed()
    f.add(1, "A 置顶", datetime.date(2026, 9, 1))
    f.add(2, "B 置顶", datetime.date(2026, 9, 2))
    _pin(f, 1, priority=10)
    _pin(f, 2, priority=1)
    first = _ids(f)[0]
    f2 = Feed()
    f2.add(2, "B 置顶", datetime.date(2026, 9, 2))
    f2.add(1, "A 置顶", datetime.date(2026, 9, 1))
    _pin(f2, 2, priority=1)
    _pin(f2, 1, priority=10)
    assert _ids(f2)[0] == first, "两条置顶的先后取决于插入顺序 —— 那就是「看运气」"
