from src.export import export_rows


def test_header_and_row():
    csv = export_rows([{"order_id": 1, "created_at": "2026-01-01", "customer": "acme"}])
    lines = csv.strip().splitlines()
    assert lines[0].startswith("order_id,created_at,customer")
    assert lines[1].startswith("1,2026-01-01,acme")


def test_empty_input():
    assert export_rows([]).strip() == "order_id,created_at,customer"
