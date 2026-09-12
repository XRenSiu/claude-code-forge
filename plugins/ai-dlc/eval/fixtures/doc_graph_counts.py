#!/usr/bin/env python3
"""活文档里手抄的「N 节点 · M 边」必须等于 verify_graph.py 数出来的数。

2026-09-08 的报告抓到 ARCHITECTURE.md 写着 52/67 而图已是 53/69，改了那一处；SKILL.md 与
reference.md 里同样的数字没人改，又漂了三天。evaluation.md 的规矩是「条数以脚本结尾行为准，不在文档里
手抄」——这里把它变成一条期望：凡是活文档（不含 reports/ 与 dogfood/ 的冻结记录）里出现的节点 / 边计数，
都要等于图现在的数。

用法: doc_graph_counts.py <plugin root>   退出 0 一致 · 1 有漂移 · 2 IO
"""
import json
import pathlib
import re
import subprocess
import sys

LIVING = ["docs/ARCHITECTURE.md", "docs/reference.md", "docs/lifecycle.md", "skills/ai-dlc/SKILL.md", "README.md",
          "skills/ai-dlc/references/stages.md"]
PAT = re.compile(r"(\d+)\s*(?:个)?\s*(?:节点|nodes)\s*[·/,，、]\s*(\d+)\s*(?:条)?\s*(?:边|edges)")


def main():
    if len(sys.argv) != 2:
        sys.stderr.write(__doc__); return 2
    root = pathlib.Path(sys.argv[1])
    r = subprocess.run([sys.executable, str(root / "skills/ai-dlc/scripts/verify_graph.py"),
                        str(root / "skills/ai-dlc/assets/graph.yaml")], capture_output=True, text=True)
    m = re.search(r"\{.*\}", r.stdout, re.S)
    if not m:
        sys.stderr.write("doc_graph_counts: verify_graph.py printed no JSON\n"); return 2
    g = json.loads(m.group(0))
    nodes, edges = int(g["nodes"]), int(g["edges"])
    drift, seen = [], 0
    for rel in LIVING:
        p = root / rel
        if not p.is_file():
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            for mm in PAT.finditer(line):
                seen += 1
                n, e = int(mm.group(1)), int(mm.group(2))
                if (n, e) != (nodes, edges):
                    drift.append(f"{rel}:{i}: says {n} nodes / {e} edges, graph has {nodes} / {edges}")
    print(f"doc_graph_counts · graph {nodes} nodes / {edges} edges · {seen} mention(s) in living docs · drift {len(drift)}")
    for d in drift:
        print("  ✗ " + d)
    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
