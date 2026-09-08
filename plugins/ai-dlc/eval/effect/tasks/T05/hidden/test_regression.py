from src.app.api import format_money, get_order_total
from src.domain.pricing import order_total


def test_existing_three():
    assert order_total([(1000, 2), (250, 4)]) == 3000
    assert get_order_total([(1000, 2)]) == {"total": "¥20.00"}
    assert format_money(3000) == "¥30.00"
