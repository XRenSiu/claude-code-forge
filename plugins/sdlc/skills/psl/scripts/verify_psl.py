#!/usr/bin/env python3
"""verify_psl.py — PSL 文档的机械预门（L0）。

检产物不检过程。reject 的是产品级缺陷（层缺失或空壳、Workflow 写成具名步骤、
验收不可判、无 Open Questions 节、规律没有稳定 PSL-NNN id），不是格式洁癖。语义半边
（Domain Model 是否真推翻朴素实现、世界抓得对不对）机器不可判——本脚本只 flag
（needs_semantic_review），裁决权在 judge 与人。

规律 id（U1，dogfood 2026-09-05 I-02）：下游 `/psl-derive` 的每条形态决策必须 `← PSL-NNN`，
且 `verify_derived.py` 对"PSL 里一个 PSL-NNN 都没有"直接拒整份推导。两道闸必须说同一句话——
所以本脚本也拒。规律可以写在各层的条目上（`- PSL-001 [Σ] …`），也可以集中在「规律索引」节。

规律分层（I-20）：规律定义行的 id 后面可带 `（形态层）` / `（内容层）`（或 `(form)` /
`(content)` / `[layer: form|content]`）。约束**内容**的规律不出现在形态草案里是正常的——
`verify_derived.py` 只对 form 层的未引用规律 flag。不写 = form（默认）。

来路核对（I-23）：`[elicit:物料 <file> §N]` 里的文件与章节做存在性 flag（只 flag，不拒——
物料可能不在本机）。给 `--material-root` 指出物料树，默认取 PSL 同目录与当前工作目录。

用法：python3 verify_psl.py <PSL文件.md> [--material-root DIR]...
退出码：0 = pass（可带 flag/info），1 = reject，2 = 用法/IO 错。
"""

import argparse
import os
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

# 规律定义行：允许前置 bullet / 表格竖线 / 有序号，以及 `[Σ]` `[γ→人]` 这类标签，之后紧跟 PSL-NNN
LAW_DEF_RE = re.compile(r"^\s*(?:[-*+]\s+|\|\s*|\d+[.、)]\s+)?(?:\[[^\]]*\]\s*)*(PSL-\d{3,})\b")
# 分层标记：只在 id 之后的一小段里认，避免正文提到"形态层"时误判
LAYER_RE = re.compile(r"[（(]\s*(内容层|形态层|content|form)\s*[)）]|\[\s*layer\s*[:：]\s*(content|form|内容|形态)\s*\]", re.I)
CONTENT_LAYER = {"内容层", "content", "内容"}
# 来路标注：[elicit:物料 …] / [elicit:material …]
ELICIT_RE = re.compile(r"\[elicit\s*[:：]\s*(?:物料|material)([^\]]*)\]", re.I)
# 一条来路里的 token：章节引用（§7 / §6.1 / #3）优先于普通词
CITE_TOKEN_RE = re.compile(r"(?P<sec>[§#]\s*\d+(?:\.\d+)*)|(?P<word>[A-Za-z0-9_][A-Za-z0-9_./\-]*)")
MATERIAL_EXT = (".md", ".markdown", ".yaml", ".yml", ".json", ".py", ".sh", ".txt", ".toml", ".cfg", ".ts", ".js")
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".mypy_cache", ".pytest_cache"}

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


def non_fenced(lines):
    """(行号 1-based, 原文) 逐行，跳过 fenced code block 内容——示例里的 PSL-NNN 不是规律定义。"""
    out, in_fence = [], False
    for i, line in enumerate(lines):
        if re.match(r"^\s*(```|~~~)", line):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append((i + 1, line))
    return out


def parse_laws(lines):
    """扫规律定义行。返回 (laws, dupes)：laws = {id: {"line": n, "layer": "form"|"content"}}。"""
    laws, dupes = {}, []
    for lineno, line in non_fenced(lines):
        m = LAW_DEF_RE.match(line)
        if not m:
            continue
        law_id = m.group(1)
        tail = line[m.end(1):m.end(1) + 40]
        lm = LAYER_RE.search(tail)
        marker = (lm.group(1) or lm.group(2)).lower() if lm else None
        layer = "content" if marker in CONTENT_LAYER else "form"
        if law_id in laws:
            dupes.append((law_id, laws[law_id]["line"], lineno))
            continue
        laws[law_id] = {"line": lineno, "layer": layer, "declared": marker is not None}
    return laws, dupes


def index_materials(roots, cap=20000):
    """basename / stem（小写）→ 路径列表。只索引物料类扩展名，跳过 .git 等噪声目录。"""
    idx, n = {}, 0
    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
            for fn in filenames:
                if not fn.lower().endswith(MATERIAL_EXT):
                    continue
                n += 1
                if n > cap:
                    return idx
                full = os.path.join(dirpath, fn)
                idx.setdefault(fn.lower(), []).append(full)
                idx.setdefault(os.path.splitext(fn)[0].lower(), []).append(full)
    return idx


def _numbered_heading(text, num):
    return re.search(r"^#{1,6}\s*§?\s*" + re.escape(num) + r"(?:[.．、:：)）\s]|$)", text, re.M)


def has_section(path, num):
    """<path> 里有没有 §<num>。三种算数：编号标题（`## 7. …` / `### 3.1 …`）、字面 `§<num>`、
    或 `a.b` 形式里 `## a.` 节内的第 b 条有序列表项（ARCHITECTURE §6.1 = §6 节的第 1 条规则）。"""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return True  # 读不到就不冤枉它
    if _numbered_heading(text, num) or re.search(r"§\s*" + re.escape(num) + r"\b", text):
        return True
    if "." in num:
        head, _, tail = num.rpartition(".")
        m = _numbered_heading(text, head)
        if m:
            body = text[m.end():]
            nxt = re.search(r"^#{1,2}\s", body, re.M)
            body = body[:nxt.start()] if nxt else body
            if re.search(r"^\s*" + re.escape(tail) + r"[.、)]\s", body, re.M):
                return True
    return False


def check_elicit(lines, idx):
    """对 [elicit:物料 …] 的文件与章节做存在性 flag。章节配它左边最近的那个已解析文件。"""
    out = []
    if not idx:
        return out
    for lineno, line in non_fenced(lines):
        for cm in ELICIT_RE.finditer(line):
            body = cm.group(1) or ""
            current = None
            resolved = []
            for tm in CITE_TOKEN_RE.finditer(body):
                if tm.group("word"):
                    w = tm.group("word")
                    hits = idx.get(w.lower()) or idx.get(os.path.basename(w).lower())
                    if hits:
                        current = (w, hits[0])
                        resolved.append(current)
                    elif re.search(r"[A-Za-z]", w) and re.search(r"\.[A-Za-z]{1,6}$", w):
                        # 长得像文件名却找不到——最可能是来路写错了
                        out.append(f"第 {lineno} 行来路 `[elicit:物料{body}]` 里的 `{w}` 在物料树里找不到"
                                   f"——来路核对不上，needs_semantic_review")
                        current = None
                elif tm.group("sec"):
                    num = re.sub(r"[^0-9.]", "", tm.group("sec"))
                    target = current or (resolved[0] if len(resolved) == 1 else None)
                    if target and not has_section(target[1], num):
                        out.append(f"第 {lineno} 行来路 `[elicit:物料{body}]` 引用 {target[0]} 的 §{num}，"
                                   f"但 {target[1]} 里没有这一节——来路凭记忆写的？needs_semantic_review")
    return out


def main():
    ap = argparse.ArgumentParser(add_help=True, description="PSL 文档的机械预门（L0）")
    ap.add_argument("psl", help="PSL-<name>.md")
    ap.add_argument("--material-root", action="append", default=[],
                    help="物料树根目录（可重复）。默认：PSL 同目录 + 当前工作目录")
    a = ap.parse_args()
    path = a.psl
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

    # 4. 规律 id（U1）：至少一条，且 id 唯一——下游 psl-derive 的每条形态决策都要引用它们。
    #    verify_derived.py 对"没有任何 PSL-NNN"直接拒整份推导；两道闸必须说同一句话（I-02）。
    laws, dupes = parse_laws(lines)
    if not laws:
        rejects.append("没有任何 `PSL-NNN` 规律 id——下游 /psl-derive 的形态决策无从引用"
                       "（verify_derived.py 会拒整份推导）。给每条规律一个稳定编号，"
                       "写在条目上（`- PSL-001 [Σ] …`）或集中在「规律索引」节")
    for law_id, first, again in dupes:
        rejects.append(f"规律 id `{law_id}` 被定义了两次（第 {first} 行与第 {again} 行）"
                       f"——id 不稳定，引用它的形态决策指向哪一条无法确定")
    if laws:
        content = sorted(k for k, v in laws.items() if v["layer"] == "content")
        declared = sum(1 for v in laws.values() if v["declared"])
        infos.append(f"规律 {len(laws)} 条（form {len(laws) - len(content)} / content {len(content)}）；"
                     f"带分层标记 {declared} 条"
                     + (f"，内容层：{content}" if content else "")
                     + "——分层决定 verify_derived.py 对哪些规律做「未被引用」flag（不写 = form）")

    # 5. 来路核对：`[elicit:物料 <file> §N]` 的文件与章节存在性（只 flag——物料可能不在本机）
    roots = a.material_root or [os.path.dirname(os.path.abspath(path)) or ".", os.getcwd()]
    flags.extend(check_elicit(lines, index_materials(roots)))

    # 6. 正文疑似默认值填充（Open Questions 节除外）
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
