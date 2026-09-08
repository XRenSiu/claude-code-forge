"""定价领域：只认分（int），不认展示。"""


def line_total(unit_cents, qty):
    return unit_cents * qty


def order_total(lines):
    """lines: [(unit_cents, qty)] → 总额（分）。"""
    return sum(line_total(u, q) for u, q in lines)
