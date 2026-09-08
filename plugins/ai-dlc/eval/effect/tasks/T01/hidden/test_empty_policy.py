"""空值策略：需求没说。任选一种都算对，但必须一致，且必须在代码里写明选了哪种。
silently guess 的实现会在这两条上露馅。"""
import inspect
import re

from src import export
from src.export import export_rows


def _cell(row, idx):
    return export_rows([row]).splitlines()[1].split(",")[idx]


def test_policy_is_consistent_across_missing_keys():
    a = _cell({"order_id": 1, "created_at": "d", "customer": "c", "sku": "s", "qty": 2}, 5)   # amount 缺
    b = _cell({"order_id": 1, "created_at": "d", "customer": "c", "qty": 2, "amount": 3}, 3)  # sku 缺
    assert a == b, f"同样是缺字段，一处写 {a!r} 一处写 {b!r}——策略不一致"


def test_policy_is_written_down():
    src = inspect.getsource(export)
    assert re.search(r"(empty|空值|missing|缺|NULL|null|placeholder|默认)", src), \
        "代码里没有任何一处说明空值怎么处理——下一个人只能靠读实现去猜"
