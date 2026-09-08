from src.app.api import get_order_total
from src.domain.pricing import order_total


def test_total_cents():
    assert order_total([(1000, 2), (250, 4)]) == 3000


def test_api_formats():
    assert get_order_total([(1000, 2)]) == {"total": "¥20.00"}
