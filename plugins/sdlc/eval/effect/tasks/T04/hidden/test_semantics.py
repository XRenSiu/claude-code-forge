from src.dedupe import dedupe


def test_keeps_first_not_last():
    rows = [{"id": 1, "v": "first"}, {"id": 1, "v": "second"}]
    assert dedupe(rows) == [{"id": 1, "v": "first"}]


def test_order_is_input_order():
    rows = [{"id": 3}, {"id": 1}, {"id": 2}, {"id": 1}]
    assert [r["id"] for r in dedupe(rows)] == [3, 1, 2]


def test_custom_key_and_missing_key():
    rows = [{"sku": "x"}, {"sku": "x"}, {}, {}]
    out = dedupe(rows, key="sku")
    assert out == [{"sku": "x"}, {}]


def test_unhashable_key_still_works():
    rows = [{"id": [1, 2]}, {"id": [1, 2]}, {"id": [3]}]
    out = dedupe(rows)
    assert len(out) == 2, "key 不可哈希时不能直接崩——朴素实现用的是 ==，语义不能丢"
