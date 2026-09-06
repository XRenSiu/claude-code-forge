from src.catalog import co_count, related


def test_related_returns_skus():
    out = related("tent-2p")
    assert isinstance(out, list) and all(isinstance(x, str) for x in out)


def test_co_count_symmetric():
    assert co_count("tent-2p", "sleeping-bag") == co_count("sleeping-bag", "tent-2p") == 180
