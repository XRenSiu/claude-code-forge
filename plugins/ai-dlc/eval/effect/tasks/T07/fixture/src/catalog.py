"""商品目录。每件商品有类目，和「买它的人还买了什么」的共现记录。"""

ITEMS = {
    "tent-2p":      {"name": "双人帐篷", "category": "户外", "price": 89900},
    "tent-4p":      {"name": "四人帐篷", "category": "户外", "price": 129900},
    "sleeping-bag": {"name": "睡袋",     "category": "户外", "price": 39900},
    "camp-stove":   {"name": "户外炉具", "category": "厨具", "price": 24900},
    "wok":          {"name": "炒锅",     "category": "厨具", "price": 19900},
    "yoga-mat":     {"name": "瑜伽垫",   "category": "运动", "price": 12900},
}

# 同一个订单里一起出现过的次数
CO_PURCHASE = {
    ("tent-2p", "sleeping-bag"): 180,
    ("tent-2p", "camp-stove"): 150,
    ("tent-2p", "tent-4p"): 2,
    ("wok", "camp-stove"): 3,
    ("yoga-mat", "tent-2p"): 1,
}


def related(sku, limit=3):
    """现在：同类目里价格最近的几个。"""
    me = ITEMS[sku]
    same = [(k, v) for k, v in ITEMS.items() if v["category"] == me["category"] and k != sku]
    same.sort(key=lambda kv: abs(kv[1]["price"] - me["price"]))
    return [k for k, _ in same[:limit]]


def co_count(a, b):
    return CO_PURCHASE.get((a, b), CO_PURCHASE.get((b, a), 0))
