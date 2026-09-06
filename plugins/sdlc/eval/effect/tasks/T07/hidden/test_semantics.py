"""相关 = 一起用，不是同一类。买双人帐篷的人要睡袋和炉具，不要四人帐篷（那是替代品）。"""
from src.catalog import related


def test_companions_beat_substitutes():
    out = related("tent-2p", limit=3)
    assert "sleeping-bag" in out, f"睡袋（共现 180）不在推荐里：{out}"
    assert "camp-stove" in out, f"炉具（共现 150）不在推荐里：{out}"


def test_substitute_is_not_top_ranked():
    out = related("tent-2p", limit=3)
    assert out[0] != "tent-4p", f"把替代品排在第一位：{out}"


def test_cross_category_is_allowed():
    """炉具在「厨具」类目下。只在同类目里找的实现永远推不出它。"""
    out = related("tent-2p", limit=3)
    assert any(s == "camp-stove" for s in out), "跨类目的真相关品被类目过滤挡住了"
