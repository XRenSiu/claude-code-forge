from src.export import export_rows


def test_existing_three_columns_still_first():
    csv = export_rows([{"order_id": 7, "created_at": "2026-02-02", "customer": "beta"}])
    head = csv.splitlines()[0].split(",")
    assert head[:3] == ["order_id", "created_at", "customer"]
    assert csv.splitlines()[1].split(",")[:3] == ["7", "2026-02-02", "beta"]
