"""信息流。置顶现在是一个布尔字段。"""
import datetime


class Feed:
    def __init__(self):
        self.posts = []   # {"id","title","created_at","pinned"}

    def add(self, pid, title, created_at, pinned=False):
        self.posts.append({"id": pid, "title": title, "created_at": created_at, "pinned": pinned})

    def pin(self, pid):
        for p in self.posts:
            if p["id"] == pid:
                p["pinned"] = True

    def list(self, today=None):
        """置顶的在前，其余按时间倒序。"""
        pinned = [p for p in self.posts if p["pinned"]]
        rest = sorted((p for p in self.posts if not p["pinned"]),
                      key=lambda p: p["created_at"], reverse=True)
        return pinned + rest
