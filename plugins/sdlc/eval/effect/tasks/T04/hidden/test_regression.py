from src.dedupe import dedupe


def test_original_two_cases():
    rows = [{"id": 1, "v": "a"}, {"id": 2, "v": "b"}, {"id": 1, "v": "c"}]
    assert dedupe(rows) == [{"id": 1, "v": "a"}, {"id": 2, "v": "b"}]
    assert dedupe([{"sku": "x"}, {"sku": "x"}, {"sku": "y"}], key="sku") == [{"sku": "x"}, {"sku": "y"}]
