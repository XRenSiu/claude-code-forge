"""订单折扣。券可以叠加。"""


def apply_coupons(amount, coupons):
    """amount: 分；coupons: [{"kind": "percent"|"fixed", "value": N}] → 折后金额（分）。"""
    total = amount
    for c in coupons:
        if c["kind"] == "percent":
            total = total - amount * c["value"] // 100
        else:
            total = total - c["value"]
    return total
