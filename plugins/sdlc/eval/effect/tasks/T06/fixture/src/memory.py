"""记忆库。目前只有关键词搜索。"""
import datetime


class Store:
    def __init__(self):
        self._items = []

    def add(self, text, created_at, happened_at=None):
        """created_at: 写进库的时间；happened_at: 这件事发生的时间（可能为 None）。"""
        self._items.append({"text": text, "created_at": created_at, "happened_at": happened_at})
        return self._items[-1]

    def search(self, query):
        """现在只按关键词。"""
        return [i for i in self._items if query in i["text"]]

    def all(self):
        return list(self._items)


def month_range(today, offset=-1):
    """辅助：返回 offset 个月前那个月的 [起, 止)。offset=-1 就是上个月。"""
    y, m = today.year, today.month + offset
    while m <= 0:
        y, m = y - 1, m + 12
    start = datetime.date(y, m, 1)
    end = datetime.date(y + (m == 12), (m % 12) + 1, 1)
    return start, end
