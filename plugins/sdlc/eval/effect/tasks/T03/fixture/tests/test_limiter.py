from src.limiter import Limiter


def test_allows_up_to_limit():
    lim = Limiter(per_minute=3)
    assert [lim.allow(t) for t in (0.0, 1.0, 2.0)] == [True, True, True]
    assert lim.allow(3.0) is False


def test_window_slides():
    lim = Limiter(per_minute=1)
    assert lim.allow(0.0) is True
    assert lim.allow(61.0) is True
