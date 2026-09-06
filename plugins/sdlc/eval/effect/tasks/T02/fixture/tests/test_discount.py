from src.discount import apply_coupons


def test_single_percent():
    assert apply_coupons(10000, [{"kind": "percent", "value": 10}]) == 9000


def test_single_fixed():
    assert apply_coupons(10000, [{"kind": "fixed", "value": 500}]) == 9500
