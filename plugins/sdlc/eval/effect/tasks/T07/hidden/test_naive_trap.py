import inspect

from src import catalog


def test_co_purchase_is_actually_used():
    src = inspect.getsource(catalog.related)
    assert "CO_PURCHASE" in src or "co_count" in src, "related() 根本没读共现数据"


def test_not_ranked_by_price_distance_alone():
    src = inspect.getsource(catalog.related)
    assert "abs(" not in src or "co" in src.lower(), "还在按价格差排序"
