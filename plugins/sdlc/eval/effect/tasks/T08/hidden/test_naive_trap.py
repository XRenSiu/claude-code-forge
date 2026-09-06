"""朴素痕迹：曝光数据有没有真的被用上。

只判**用没用**，不判**在哪用**。2026-09-06（E-09）：这里曾经要求 `unread()` 里不许出现布尔 read，
而一个"写时更新的闩锁"实现（record_view 时推进状态，unread 读状态）确实用了曝光数据，
只是推导发生在写入侧——检查在规定架构，不是在判实质。行为对不对由 test_semantics.py 判，
那是行为测试，不关心你把推导放在哪一侧。
"""
import inspect

from src import inbox


def test_exposure_fields_are_consulted():
    src = inspect.getsource(inbox)
    assert "dwell_ms" in src and "fully_visible" in src, \
        "曝光数据一个字段都没用上 —— 已读还是那个布尔标记"


def test_open_thread_no_longer_blanket_marks_read():
    src = inspect.getsource(inbox.Inbox.open_thread)
    assert 'm["read"] = True' not in src and "read'] = True" not in src, \
        "open_thread 还在把所有消息一律置成已读 —— 投诉的第一条症状原样还在"
