#!/usr/bin/env python3
"""slice_agent_map.py — 把仓库地图按卡切片，塞进 card_context.md。

为什么是切片而不是整份：2607.27250 的 288 次运行说，把仓库知识整包灌进上下文**不提高正确率**；
真正起作用的是"这一张卡需要的那几行"。所以命令全给（实现者一定要跑测试），目录 / 禁区 / 陷阱
只给与本卡 allowed_files 相交的那几行。给多了是噪音，给少了实现者去猜。

用法：
  slice_agent_map.py <agent-map.md> --card cards/CARD-01.yaml [--out slice.md]

退出码：0 = 切出了内容 · 1 = 地图缺节或卡读不了 · 2 = 用法 / IO 错误。
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("slice_agent_map.py needs PyYAML\n"); sys.exit(2)

SECTION = lambda md, name: (re.search(rf"^##\s*{re.escape(name)}\s*$(.*?)(?=^##\s|\Z)", md, re.M | re.S) or [None, ""])[1] \
    if re.search(rf"^##\s*{re.escape(name)}\s*$", md, re.M) else None


def table_rows(block):
    head, rows = None, []
    for line in (block or "").splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c or "") for c in cells):
            continue
        if head is None:
            head = cells
        else:
            rows.append(cells)
    return head, rows


def globs_touch(a, b):
    """两个 glob 是否可能指同一批文件（粗判：前缀相交或互相匹配）。"""
    a, b = a.strip("`"), b.strip("`")
    if fnmatch.fnmatch(a, b) or fnmatch.fnmatch(b, a):
        return True
    pa, pb = a.split("*")[0].rstrip("/"), b.split("*")[0].rstrip("/")
    return bool(pa) and bool(pb) and (pa.startswith(pb) or pb.startswith(pa))


def render(head, rows):
    if not rows:
        return ""
    out = ["| " + " | ".join(head) + " |", "|" + "|".join(["---"] * len(head)) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("map"); ap.add_argument("--card", required=True); ap.add_argument("--out")
    a = ap.parse_args()
    try:
        md = open(a.map, encoding="utf-8").read()
        card = yaml.safe_load(open(a.card, encoding="utf-8")) or {}
    except OSError as e:
        sys.stderr.write(f"slice_agent_map: {e}\n"); return 2
    allowed = [str(x) for x in (card.get("allowed_files") or [])]
    forbidden = [str(x) for x in (card.get("forbidden_files") or [])]
    terms = [str(t) for t in ((card.get("dos_slice") or {}).get("objects") or [])]
    if not allowed:
        sys.stderr.write("card 没有 allowed_files —— 无从切片（lint_cards.py 本来就该拒这张卡）\n"); return 1

    parts, missing = [], []
    run = SECTION(md, "跑起来")
    if run is None:
        missing.append("跑起来")
    else:
        parts.append("### 怎么跑起来（全给：实现者的红-绿自证靠它）\n" + run.strip())

    for name, title in (("目录职责", "本卡碰得到的目录"), ("禁区", "本卡边上的禁区")):
        blk = SECTION(md, name)
        if blk is None:
            missing.append(name); continue
        head, rows = table_rows(blk)
        keep = [r for r in rows if r and any(globs_touch(r[0], g) for g in allowed + forbidden)]
        if keep:
            parts.append(f"### {title}\n" + render(head, keep))

    blk = SECTION(md, "已知陷阱")
    if blk is None:
        missing.append("已知陷阱")
    else:
        head, rows = table_rows(blk)
        keep = []
        for r in rows:
            joined = " ".join(r)
            # 路径相交，或 DOS 名词出现在「症状」列——整行匹配会让 skill / plugin 这种到处都是的词命中一切
            hit = any(globs_touch(m.group(1), g) for m in re.finditer(r"`([^`]+)`", joined) for g in allowed) \
                or any(t and len(t) >= 3 and t in (r[0] if r else "") for t in terms)
            if hit:
                keep.append(r)
        if keep:
            parts.append("### 这块地方踩过的坑（每条有来路）\n" + render(head, keep))

    if missing:
        sys.stderr.write(f"agent-map 缺节：{missing}——先跑 verify_agent_map.py\n"); return 1
    body = ("\n\n".join(parts) if parts else
            "（agent-map 里没有与本卡相交的行；命令一节仍应给实现者）")
    text = ("## 仓库怎么干活（agent-map 切片）\n\n"
            f"> 来源 `{os.path.relpath(a.map)}`，按本卡 allowed_files 切；整份地图不给，多余的行是噪音。\n\n"
            + body + "\n")
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text)
        print(f"slice → {a.out}（{len(parts)} 节）")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
