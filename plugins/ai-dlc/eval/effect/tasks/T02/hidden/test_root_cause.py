"""只对 #1042 特判的实现在这里红：同一个根因的别的输入。"""
from src.discount import apply_coupons


def test_other_pair():
    # 10000 → -20% → 8000 → -30% of 8000 = 5600
    assert apply_coupons(10000, [{"kind": "percent", "value": 20},
                                 {"kind": "percent", "value": 30}]) == 5600


def test_three_coupons():
    # 10000 → -10% → 9000 → -10% → 8100 → -10% → 7290
    assert apply_coupons(10000, [{"kind": "percent", "value": 10}] * 3) == 7290


def test_order_matters_consistently():
    a = apply_coupons(10000, [{"kind": "percent", "value": 10}, {"kind": "fixed", "value": 500}])
    b = apply_coupons(10000, [{"kind": "fixed", "value": 500}, {"kind": "percent", "value": 10}])
    assert a == 8500 and b == 8550
