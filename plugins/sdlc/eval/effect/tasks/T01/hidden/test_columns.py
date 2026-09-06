from src.export import export_rows

WANT = ["order_id", "created_at", "customer", "sku", "qty", "amount"]


def test_six_columns_in_order():
    csv = export_rows([{c: c for c in WANT}])
    assert csv.splitlines()[0].split(",") == WANT
