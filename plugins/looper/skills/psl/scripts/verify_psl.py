#!/usr/bin/env python3
"""verify_psl.py — PSL 文档的机械预门（L0）。

检产物不检过程。reject 的是产品级缺陷（层缺失或空壳、Workflow 写成具名步骤、
验收不可判、无 Open Questions 节），不是格式洁癖。语义半边（Domain Model 是否真推翻朴素实现、
世界抓得对不对）机器不可判——本脚本只 flag（needs_semantic_review），裁决权在
judge 与人。

用法：python3 verify_psl.py <PSL文件.md>
退出码：0 = pass（可带 flag/info），1 = reject。
"""

import re
import sys

# 六个骨架层 + Open Questions；标题匹配中英同义词（大小写不敏感）
LAYERS = [
    ("Vision", r"vision|愿景"),
    ("Mental Model", r"mental\s*model|心智模型"),
    ("Domain Model", r"domain\s*model|领域模型"),
    ("State Machine", r"state\s*machine|状态机|状态流转"),
    ("Workflow", r"workflow|工作流"),
    ("Acceptance", r"acceptance|验收"),
]
OPEN_Q = ("Open Questions", r"open\s*questions?|开放问题|未决")

# Workflow 层内的具名步骤 → reject（写成了执行顺序，不是领域动力学）
STEP_PATTERNS = [
    re.compile(r"\bstep\s*[0-9]", re.IGNORECASE),
    re.compile(r"步骤\s*[0-9０-９一二三四五六七八九十]"),
    re.compile(r"第\s*[0-9０-９一二三四五六七八九十]+\s*步"),
    re.compile(r"阶段\s*[0-9０-９一二三四五六七八九十]"),
    re.compile(r"\bphase\s*[0-9]", re.IGNORECASE),
]

# Workflow 层内的命令式时序词——单个词合法（领域动力学有真实时间），
# 成串（≥3 处）则疑似伪装成散文/无序列表的流水线 → flag
SEQ_WORD_RE = re.compile(r"首先|其次|然后|接着|随后|最后|再来")

# 验收条目里的入口散文 → flag（"问 X → 返回 Y"之外的许愿式表述）
PROSE_PATTERN = re.compile(r"智能理解|智能地|intelligently|automatically\s+understand", re.IGNORECASE)

# 疑似默认值填充 → flag（承重未知应进 Open Questions，不应以"暂定"糊在正文）
DEFAULT_FILL_PATTERN = re.compile(r"\bTBD\b|\bTODO\b|暂定|默认假设", re.IGNORECASE)

BULLET_RE = re.compile(r"^(?:[-*+]|\d+[.、)])\s+")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)")
ARROW_RE = re.compile(r"→|->")


def parse_sections(lines):
    """按标题切节（忽略 fenced code block 内的行）。返回 [(title, level, start, end)]。"""
    headings = []
    in_fence = False
    for i, line in enumerate(lines):
        if re.match(r"^\s*(```|~~~)", line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING_RE.match(line)
        if m:
            headings.append((m.group(2).strip(), len(m.group(1)), i))
    sections = []
    for idx, (title, level, start) in enumerate(headings):
        end = len(lines)
        for t2, l2, s2 in headings[idx + 1:]:
            if l2 <= level:
                end = s2
                break
        sections.append((title, level, start, end))
    return sections


def body_lines(lines, start, end):
    """节内正文（去掉标题行与 fenced block 内容），带原始行号（1-based）。"""
    out = []
    in_fence = False
    for i in range(start + 1, end):
        line = lines[i]
        if re.match(r"^\s*(```|~~~)", line):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append((i + 1, line))
    return out


def find_section(sections, pattern):
    rx = re.compile(pattern, re.IGNORECASE)
    for title, level, start, end in sections:
        if rx.search(title):
            return (title, level, start, end)
    return None


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError as e:
        print(f"REJECT: 无法读取文件: {e}")
        return 1

    rejects, flags, infos = [], [], []
    sections = parse_sections(lines)

    # 1. 六层齐全且非空壳 + Open Questions 节存在
    found = {}
    for name, pattern in LAYERS:
        sec = find_section(sections, pattern)
        if sec is None:
            rejects.append(f"缺少骨架层「{name}」——六层缺一即不完整")
        else:
            found[name] = sec
            # 空壳检查按原始行（fenced 图表也算正文，避免误杀纯 mermaid 的 State Machine）
            raw_body = [l for l in lines[sec[2] + 1:sec[3]] if l.strip()]
            if not raw_body:
                rejects.append(f"骨架层「{name}」存在但正文为空——空壳不是完整，未知请写进 Open Questions")
    oq = find_section(sections, OPEN_Q[1])
    if oq is None:
        rejects.append("缺少 Open Questions 节——未知承重槽没有诚实着陆点（空节可以，缺节不行）")
    else:
        oq_body = [l for _, l in body_lines(lines, oq[2], oq[3]) if l.strip()]
        if not oq_body:
            infos.append("Open Questions 为空——仅当所有承重槽真的都被回答时才合法，请自查")

    # 2. Workflow：具名步骤 reject；长有序列表 flag；时序词成串 flag
    if "Workflow" in found:
        _, _, start, end = found["Workflow"]
        consecutive = 0
        seq_hits = 0
        for lineno, line in body_lines(lines, start, end):
            for pat in STEP_PATTERNS:
                if pat.search(line):
                    rejects.append(f"Workflow 层第 {lineno} 行出现具名步骤（{line.strip()[:40]}…）——写成了执行顺序，不是领域动力学")
            seq_hits += len(SEQ_WORD_RE.findall(line))
            if re.match(r"^\s*\d+[.、)]\s", line):
                consecutive += 1
                if consecutive == 3:
                    flags.append(f"Workflow 层第 {lineno} 行附近有 ≥3 连续有序列表项——是时序步骤还是判据枚举？needs_semantic_review")
            elif line.strip():
                consecutive = 0
        if seq_hits >= 3:
            flags.append(f"Workflow 层出现 {seq_hits} 处命令式时序词（首先/然后/接着/最后…）——疑似伪装成散文的流水线，needs_semantic_review")

    # 3. Acceptance：每条顶层条目必须是"问 X → 返回 Y"形态（含箭头）。
    #    条目 = 顶层 bullet + 其续行/缩进子行（跨行条目按整条判，不逐物理行误杀）。
    if "Acceptance" in found:
        _, _, start, end = found["Acceptance"]
        entries, current = [], None
        for n, l in body_lines(lines, start, end):
            if BULLET_RE.match(l):
                if current:
                    entries.append(current)
                current = [n, l.strip()]
            elif current and l.strip():
                current[1] += " " + l.strip()
            elif current:
                entries.append(current)
                current = None
        if current:
            entries.append(current)
        if not entries:
            rejects.append("Acceptance 层没有任何条目")
        for lineno, text in entries:
            if not ARROW_RE.search(text):
                rejects.append(f"Acceptance 第 {lineno} 行条目不含「→」——不是行为可判的「问 X → 返回 Y」形态：{text[:40]}…")
            if PROSE_PATTERN.search(text):
                flags.append(f"Acceptance 第 {lineno} 行条目疑似入口散文（智能理解…类）——needs_semantic_review")

    # 4. 正文疑似默认值填充（Open Questions 节除外）
    oq_range = range(oq[2], oq[3]) if oq else range(0)
    for title, _, start, end in sections:
        if start in oq_range:
            continue
        for lineno, line in body_lines(lines, start, end):
            if lineno - 1 in oq_range:
                continue
            if DEFAULT_FILL_PATTERN.search(line):
                flags.append(f"第 {lineno} 行疑似默认值填充（{line.strip()[:40]}…）——承重未知应进 Open Questions，needs_semantic_review")

    for msg in rejects:
        print(f"REJECT: {msg}")
    for msg in flags:
        print(f"FLAG:   {msg}")
    for msg in infos:
        print(f"INFO:   {msg}")

    if rejects:
        print(f"\n结论：REJECT（{len(rejects)} 项）——修复后重跑。")
        return 1
    print(f"\n结论：PASS（flag {len(flags)} / info {len(infos)}）。"
          "机械预门只降缺陷频率；Domain Model 是否真推翻朴素实现、世界抓得对不对，仍需 judge 与人裁决。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
