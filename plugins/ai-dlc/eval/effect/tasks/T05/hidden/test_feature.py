"""功能：能一次拿到每行小计 + 总额，格式对。接口名不限，探测常见几种。"""
import importlib


def _find():
    for mod, names in (("src.app.api", ("get_order_receipt", "get_receipt", "order_receipt",
                                        "get_order_lines", "get_order_detail", "get_order_totals",
                                        "receipt", "get_order_total_detail")),):
        m = importlib.import_module(mod)
        for n in names:
            if hasattr(m, n):
                return getattr(m, n)
        for n in dir(m):
            if n.startswith("_"):
                continue
            f = getattr(m, n)
            if callable(f) and n not in ("format_money", "order_total", "get_order_total"):
                try:
                    r = f([(1000, 2), (250, 4)])
                except Exception:
                    continue
                if isinstance(r, dict) and any(isinstance(v, (list, tuple)) for v in r.values()):
                    return f
    return None


def test_lines_and_total():
    fn = _find()
    assert fn is not None, "找不到能一次返回每行小计 + 总额的接口"
    r = fn([(1000, 2), (250, 4)])
    flat = repr(r)
    assert "¥20.00" in flat and "¥10.00" in flat, f"每行小计的格式不对：{flat}"
    assert "¥30.00" in flat, f"总额的格式不对：{flat}"
