#!/usr/bin/env python3
"""slice_agent_map.py — 把仓库地图按卡切片，塞进 card_context.md。

为什么是切片而不是整份：2607.27250 的 288 次运行说，把仓库知识整包灌进上下文**不提高正确率**；
真正起作用的是"这一张卡需要的那几行"。所以命令全给（实现者一定要跑测试），目录与陷阱
只给与本卡文件相交的那几行。给多了是噪音，给少了实现者去猜。

**禁区是例外，全给。** 禁区的语义是"不能碰"，按"本卡能碰什么"去筛它，筛掉的恰恰是要防的那些——
一条与 allowed_files 不相交的禁区行不是噪音，它是唯一会拦住实现者走错的那句话。
（dogfood vana-builder 2026-09-22：fixture 与真仓库里，禁区表都被筛成空，每张卡都看不到它。）
反过来，一条**与 allowed_files 相交**的禁区行是矛盾：卡授权去改一个禁区。那种行标出来并报警。

目录职责分两张表：`allowed_files` 命中的是"可改"，只被 `forbidden_files` 命中的是"读得到但不许改"。
此前两者混在一张叫「本卡碰得到的目录」的表里，实现者分不出哪几行是给它写的。

用法：
  slice_agent_map.py <agent-map.md> --card cards/CARD-01.yaml [--out slice.md]

退出码：0 = 切出了内容 · 1 = 地图缺节或卡读不了 · 2 = 用法 / IO 错误 ·
        3 = 切出来了，但卡的 allowed_files 命中了禁区（产物照常写，矛盾报在 stderr）。
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
    """两个 glob 是否可能指同一批文件（粗判：路径前缀相交或互相匹配）。

    前缀比较按**路径分段**做：`app/main` 不该命中 `app/mainland/**`——
    字符串前缀会，这就是它们看起来相交的原因。"""
    a, b = a.strip("`"), b.strip("`")
    if fnmatch.fnmatch(a, b) or fnmatch.fnmatch(b, a):
        return True
    pa, pb = a.split("*")[0].rstrip("/"), b.split("*")[0].rstrip("/")
    if not pa or not pb:
        return False
    return pa == pb or pa.startswith(pb + "/") or pb.startswith(pa + "/")


def row_globs(row):
    """一行里的全部路径字面量。路径列常写成 `a/**`、`b/**` 两个反引号段。"""
    cell = row[0] if row else ""
    lits = re.findall(r"`([^`]+)`", cell)
    return lits or [cell]


def row_touches(row, globs):
    return any(globs_touch(lit, g) for lit in row_globs(row) for g in globs)


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

    parts, missing, conflicts = [], [], []
    run = SECTION(md, "跑起来")
    if run is None:
        missing.append("跑起来")
    else:
        parts.append("### 怎么跑起来（全给：实现者的红-绿自证靠它）\n" + run.strip())

    blk = SECTION(md, "目录职责")
    if blk is None:
        missing.append("目录职责")
    else:
        head, rows = table_rows(blk)
        writable = [r for r in rows if r and row_touches(r, allowed)]
        # 只被 forbidden 命中的：实现者读得到、但不许改。与可改的混在一张表里，它分不出来。
        readonly = [r for r in rows if r and not row_touches(r, allowed) and row_touches(r, forbidden)]
        if writable:
            parts.append("### 本卡可改的目录\n" + render(head, writable))
        if readonly:
            parts.append("### 本卡读得到、但不许改的目录\n" + render(head, readonly))

    # 禁区全给：按「本卡能碰什么」筛禁区，筛掉的恰恰是要防的那些。
    blk = SECTION(md, "禁区")
    if blk is None:
        missing.append("禁区")
    else:
        head, rows = table_rows(blk)
        rows = [r for r in rows if r]
        for r in rows:
            if row_touches(r, allowed):
                conflicts.append(r[0])
        if rows:
            note = ("\n\n> ⚠️ 下列禁区被本卡的 allowed_files 命中——卡授权去改一个禁区，"
                    "这是切卡的错，不是实现者的自由裁量：" + "、".join(conflicts)) if conflicts else ""
            parts.append("### 禁区（全给：这张表不按本卡的路径筛）\n" + render(head, rows) + note)

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
    if conflicts:
        sys.stderr.write(
            f"slice_agent_map: 卡 {card.get('id') or a.card} 的 allowed_files 命中禁区 "
            f"{conflicts}——切片已照常产出，但这张卡该收窄白名单或走变更提案\n")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
