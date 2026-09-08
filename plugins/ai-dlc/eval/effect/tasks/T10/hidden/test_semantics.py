"""置顶是一段关系，不是一个布尔。过期与撞车两条用例上，布尔模型给相反答案。"""
import datetime

from src.feed import Feed

TODAY = datetime.date(2026, 9, 6)


def _pin(f, pid, **kw):
    """逐个丢掉实现不认识的关键字，而不是一次全丢——
    一个支持 until 但不支持 priority 的实现，不该连 until 都用不上（E-08）。"""
    try:
        return f.pin(pid, **kw)
    except TypeError:
        pass
    for k in list(kw):
        sub = {x: v for x, v in kw.items() if x != k}
        try:
            return f.pin(pid, **sub)
        except TypeError:
            continue
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
    """同一组置顶，换一个插入顺序，结果必须一样。
    不要求任何特定实现——priority 也好、置顶时间也好，只要它写在数据里、不取决于谁先被加进来。
    2026-09-06（E-08）：这条曾经硬传 priority=，一个不叫这个名字的实现会 TypeError 退化，被判红。"""
    def build(order):
        f = Feed()
        for pid, title, d in order:
            f.add(pid, title, d)
        for pid, pri in ((1, 10), (2, 1)):
            _pin(f, pid, priority=pri)
        return _ids(f)

    a = build([(1, "A 置顶", datetime.date(2026, 9, 1)), (2, "B 置顶", datetime.date(2026, 9, 2))])
    b = build([(2, "B 置顶", datetime.date(2026, 9, 2)), (1, "A 置顶", datetime.date(2026, 9, 1))])
    assert a[0] == b[0], f"换个插入顺序，置顶的先后就变了（{a} vs {b}）—— 那就是「看运气」"
