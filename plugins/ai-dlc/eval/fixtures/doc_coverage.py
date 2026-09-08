#!/usr/bin/env python3
"""doc_coverage.py — 文档漂移的机械闸。

这个插件反复说「声明式的纪律不是纪律」。它自己的文档却漂了很久：2026-09-06 数过一遍，
8 个脚本、26 个资产在当时的六份文档里一次都没出现过——一个自称每步都有脚本检的插件，
使用者查不到脚本清单。

本脚本检两件事：
  1. 每个 `skills/*/scripts/` 下的脚本（一层，不含 eval/fixtures 里的副本）都在 docs/reference.md 里出现；
  2. 每个 `skills/*/assets/` 下的 .yaml / .md 资产也在。

用法：doc_coverage.py <plugin_root> [--json]
退出码：0 = 全覆盖 · 1 = 有遗漏 · 2 = 路径错。

**故意不检的**：文档里写的东西是不是对的。那是人的活，机器只能保证「不缺」，不能保证「不错」。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    root = pathlib.Path(a.root)
    ref = root / "docs" / "reference.md"
    if not ref.is_file():
        sys.stderr.write(f"没有 {ref} —— 索引本身就是缺的\n"); return 2
    text = ref.read_text(encoding="utf-8")

    scripts = sorted({p.name for p in root.glob("skills/*/scripts/*.py")}
                     | {p.name for p in root.glob("skills/*/scripts/*.sh")})
    assets = sorted({p.name for p in root.glob("skills/*/assets/*.yaml")}
                    | {p.name for p in root.glob("skills/*/assets/*.md")})
    miss_s = [s for s in scripts if s not in text]
    miss_a = [x for x in assets if x not in text]
    res = {"reference": str(ref), "scripts": len(scripts), "assets": len(assets),
           "missing_scripts": miss_s, "missing_assets": miss_a,
           "ok": not (miss_s or miss_a)}
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(f"doc_coverage · 脚本 {len(scripts)} · 资产 {len(assets)} · "
              f"{'全覆盖' if res['ok'] else '有遗漏'}")
        for s in miss_s:
            print(f"  缺: 脚本 {s}")
        for x in miss_a:
            print(f"  缺: 资产 {x}")
        if not res["ok"]:
            print("  → 补进 docs/reference.md。索引不全 = 使用者只能读源码。")
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
