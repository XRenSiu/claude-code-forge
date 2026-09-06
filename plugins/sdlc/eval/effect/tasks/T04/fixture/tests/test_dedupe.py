from src.dedupe import dedupe


def test_keeps_first_and_order():
    rows = [{"id": 1, "v": "a"}, {"id": 2, "v": "b"}, {"id": 1, "v": "c"}]
    assert dedupe(rows) == [{"id": 1, "v": "a"}, {"id": 2, "v": "b"}]


def test_custom_key():
    rows = [{"sku": "x"}, {"sku": "x"}, {"sku": "y"}]
    assert dedupe(rows, key="sku") == [{"sku": "x"}, {"sku": "y"}]
