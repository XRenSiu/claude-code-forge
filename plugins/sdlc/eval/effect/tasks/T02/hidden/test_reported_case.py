from src.discount import apply_coupons


def test_order_1042():
    assert apply_coupons(10000, [{"kind": "percent", "value": 10},
                                 {"kind": "percent", "value": 20}]) == 7200
