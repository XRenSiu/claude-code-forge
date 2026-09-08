"""报表导出。现在只有三列。"""

COLUMNS = ["order_id", "created_at", "customer"]


def export_rows(rows):
    """rows: [dict] → CSV 文本（含表头）。"""
    out = [",".join(COLUMNS)]
    for r in rows:
        out.append(",".join(str(r.get(c, "")) for c in COLUMNS))
    return "\n".join(out) + "\n"
