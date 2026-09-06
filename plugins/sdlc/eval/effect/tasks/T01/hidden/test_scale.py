"""「导出要快」是形容词。这条把它变成阈值：20 万行 2 秒内。"""
import time

from src.export import export_rows


def test_200k_rows_under_2s():
    rows = [{"order_id": i, "created_at": "2026-01-01", "customer": "c",
             "sku": "s", "qty": 1, "amount": 2} for i in range(200_000)]
    t0 = time.time()
    out = export_rows(rows)
    took = time.time() - t0
    n = out.count("\n") if isinstance(out, str) else sum(1 for _ in out)
    assert n >= 200_000
    assert took < 2.0, f"20 万行用了 {took:.1f}s"
