"""规模。朴素的 O(n²) 在 10 万条上约 14s，哈希实现约 0.02s——上限取 1.5s，
两边差三个数量级，阈值落在哪里都不影响判定。用 10 万而不是需求里的 50 万，
是为了让收分本身别变成一次十分钟的等待（朴素实现在 50 万上要几分钟）。"""
import time

from src.dedupe import dedupe


def test_100k_under_1s5():
    rows = [{"id": i % 50000, "v": i} for i in range(100000)]
    t0 = time.time()
    out = dedupe(rows)
    took = time.time() - t0
    assert len(out) == 50000, f"去重结果不对：{len(out)}"
    assert took < 1.5, f"10 万条用了 {took:.1f}s（朴素实现约 14s）"
