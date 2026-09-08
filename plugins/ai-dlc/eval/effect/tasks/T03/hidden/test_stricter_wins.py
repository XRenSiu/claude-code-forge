from src.limiter import Limiter


def _mk():
    try:
        return Limiter(per_minute=100)
    except TypeError:
        return Limiter()


def test_burst_of_six_in_ten_seconds_is_capped():
    lim = _mk()
    got = [lim.allow(t) for t in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5)]
    assert got[:5] == [True] * 5, got
    assert got[5] is False, "10 秒窗口内第 6 次必须被拒"


def test_minute_cap_is_the_intersection_not_one_hundred():
    lim = _mk()
    allowed = sum(1 for i in range(200) if lim.allow(i * 0.3))  # 60 秒内密集打点
    assert allowed <= 30, f"两条规则的交集最多 30 次/分钟，实际放行 {allowed}"
    assert allowed >= 25, f"也不该过严，实际只放行 {allowed}"
