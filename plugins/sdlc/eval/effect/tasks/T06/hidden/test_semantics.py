"""领域模型被证伪的那条线：时间不是时间戳。
朴素模型按 created_at 过滤，正确模型按事件发生的时间。同一条数据，两种模型答案相反。
接口名不限——探测常见几种；找不到就是没实现。"""
import datetime

from src.memory import Store

TODAY = datetime.date(2026, 9, 6)


def _search(store, phrase):
    for name in ("search_by_time", "search_relative", "search_time", "search_period",
                 "search_by_period", "search_when", "relative_search"):
        fn = getattr(store, name, None)
        if fn:
            for args in ((phrase, TODAY), (phrase,)):
                try:
                    return fn(*args)
                except TypeError:
                    continue
    fn = getattr(store, "search", None)
    for args in ((phrase, TODAY), (phrase,)):
        try:
            return fn(*args)
        except TypeError:
            continue
    raise AssertionError("找不到能按相对时间搜索的接口")


def test_backfilled_last_month_event_is_included():
    """昨天补录的、上个月发生的事 —— 属于「上个月」。按写入时间过滤的实现会漏掉它。"""
    s = Store()
    s.add("八月和小王吃火锅", created_at=datetime.date(2026, 9, 5), happened_at=datetime.date(2026, 8, 3))
    out = _search(s, "上个月")
    assert any("火锅" in i["text"] for i in out), "补录的上月事件被漏掉了——用的是写入时间"


def test_this_month_event_written_last_month_is_excluded():
    """上个月写下的、这个月才发生的事 —— 不属于「上个月」。按写入时间过滤的实现会多收它。"""
    s = Store()
    s.add("九月要去体检", created_at=datetime.date(2026, 8, 20), happened_at=datetime.date(2026, 9, 4))
    out = _search(s, "上个月")
    assert not any("体检" in i["text"] for i in out), "把上月写下的未来事件算进了上个月——用的是写入时间"
