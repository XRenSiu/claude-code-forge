"""修完必须留下复现测试：仓库自己的测试里要有一条盯着叠加券的。"""
import pathlib
import re


def test_a_stacking_test_exists():
    root = pathlib.Path(__file__).resolve().parent.parent
    bodies = "\n".join(p.read_text(encoding="utf-8", errors="replace")
                       for p in (root / "tests").rglob("test_*.py"))
    assert re.search(r'"percent"[^\n]*\n?[^\n]*"percent"|percent.*value.*\].*percent|\[\s*\{[^}]*percent[^}]*\}\s*,\s*\{[^}]*percent',
                     bodies, re.S), "没有任何一个测试同时用了两张百分比券"
