"""按 key 去重，保序。"""


def dedupe(records, key="id"):
    """records: [dict] → 去重后的列表，保持首次出现的顺序。"""
    out = []
    seen = []
    for r in records:
        k = r.get(key)
        if k not in seen:
            seen.append(k)
            out.append(r)
    return out
