from src.limiter import Limiter


def test_constructor_still_takes_per_minute():
    lim = Limiter(per_minute=3)
    assert [lim.allow(t) for t in (0.0, 20.0, 40.0)] == [True, True, True]
    assert lim.allow(50.0) is False


def test_window_still_slides():
    lim = Limiter(per_minute=1)
    assert lim.allow(0.0) is True
    assert lim.allow(61.0) is True
