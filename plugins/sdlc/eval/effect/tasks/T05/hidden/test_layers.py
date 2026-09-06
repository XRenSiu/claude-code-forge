"""领域层不许 import 应用层。最省事的写法（在 pricing.py 里 import format_money）在这里红。"""
import ast
import pathlib


def test_domain_does_not_import_app():
    root = pathlib.Path(__file__).resolve().parent.parent
    bad = []
    for p in (root / "src" / "domain").rglob("*.py"):
        tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        for n in ast.walk(tree):
            mods = []
            if isinstance(n, ast.Import):
                mods = [a.name for a in n.names]
            elif isinstance(n, ast.ImportFrom):
                mods = [n.module or ""]
            for m in mods:
                if "app" in m.split("."):
                    bad.append(f"{p.name}: {m}")
    assert not bad, f"领域层反向依赖了应用层：{bad}"
