"""消息收件箱。现在「已读」是一个布尔标记，打开会话就置位。"""


class Inbox:
    def __init__(self):
        self.messages = []      # {"id", "text", "read"}
        self.views = []         # 曝光记录：{"id", "dwell_ms", "fully_visible"}

    def add(self, mid, text):
        self.messages.append({"id": mid, "text": text, "read": False})

    def open_thread(self):
        """打开会话：把所有消息标成已读。"""
        for m in self.messages:
            m["read"] = True

    def record_view(self, mid, dwell_ms, fully_visible):
        """客户端上报的曝光：这条消息在屏幕上停了多久、有没有完整露出。"""
        self.views.append({"id": mid, "dwell_ms": dwell_ms, "fully_visible": fully_visible})

    def unread(self):
        return [m for m in self.messages if not m["read"]]
