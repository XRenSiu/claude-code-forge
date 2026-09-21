#!/usr/bin/env python3
"""
agenda.py — the ritual's mechanical half: what is still open on a lockable artefact, and writing a
human's ruling back into it.

Why a script and not the engine's prose: the engine that just drafted the card is the worst reader of
"what did I leave open" — it remembers the parts it found interesting. The list has to come from the
file, every time, unfiltered (same reason `aidlc_state.py notes --for-gate` exists). And a ruling typed
back by hand loses who ruled and when; here it is stamped.

Usage:
  agenda.py <card.yaml> [--json]                      # print the open items, numbered, with evidence
  agenda.py <card.yaml> --rule <n|id> --resolution "…" --by "<human>"   # record one ruling, stamped
  agenda.py <card.yaml> --check                        # exit 0 when nothing is open, 1 otherwise

Exit: 0 ok / nothing open · 1 items still open (for --check) · 2 usage / IO.

What counts as open (same set `verify_card.py --ready-to-sign` rejects on, read from the same file):
  - `conflicts_for_legislation[]` without a `resolution`
  - a carded entry with `confidence: low` and no `resolution_note`
  - a carded entry whose `survival_test` is not `pass`
A ruling is a decision, not a deferral: `--resolution` may not be empty, and "待定 / TBD / 再说" is
refused — deferring is legitimate, but then the item belongs in open_questions with an owner, not in a
signature.
"""
import argparse
import datetime as _dt
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("agenda.py needs PyYAML\n"); sys.exit(2)

DEFERRAL = re.compile(r"^\s*(待定|待议|再说|回头|tbd|todo|later|pending|不确定)\b", re.I)


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except (OSError, yaml.YAMLError) as e:
        sys.stderr.write(f"agenda: cannot read {path}: {e}\n"); sys.exit(2)


def open_items(card):
    """→ [{id, kind, what, evidence, where}] — read from the file, never from memory."""
    out = []
    for i, c in enumerate(card.get("conflicts_for_legislation") or []):
        c = c or {}
        if str(c.get("resolution") or "").strip():
            continue
        out.append({
            "id": f"C{i + 1}",
            "kind": "conflict",
            "what": "两条不能同真，要人裁：规则改写 / 降级，还是现状是 bug",
            "evidence": {"a": c.get("a"), "b": c.get("b"), "note": c.get("note")},
            "where": f"conflicts_for_legislation[{i}]",
        })
    for col in ("hard_invariants", "overridable_defaults"):
        for i, e in enumerate(card.get(col) or []):
            e = e or {}
            eid = e.get("id", f"{col}[{i}]")
            if e.get("confidence") == "low" and not str(e.get("resolution_note") or "").strip():
                out.append({"id": eid, "kind": "low_confidence",
                            "what": "置信度低：skill 自己说这条需要人看过才能落地",
                            "evidence": {"statement": e.get("statement"), "provenance": e.get("provenance")},
                            "where": f"{col}[{i}].resolution_note"})
            if e.get("survival_test") != "pass":
                out.append({"id": eid, "kind": "survival",
                            "what": f"存活测试是 {e.get('survival_test')!r}，不是 pass：没活过 □/◊ 的候选不能冻成法",
                            "evidence": {"statement": e.get("statement")},
                            "where": f"{col}[{i}].survival_test"})
    return out


def find_item(card, key):
    items = open_items(card)
    for n, it in enumerate(items, 1):
        if key == it["id"] or key == str(n):
            return it
    sys.stderr.write(f"agenda: no open item {key!r}; open now: {[i['id'] for i in items] or '（无）'}\n")
    sys.exit(2)


def apply_ruling(path, card, item, resolution, by):
    """Write the ruling in place, as TEXT.

    Not a yaml round-trip: `safe_dump` would drop every comment in the file, and an invariant card's
    comments carry "these are proposals, a human signature is what makes them law". Losing that while
    recording a ruling would be a bad trade, so the key is inserted into the entry's own block.
    """
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
    text = f"{stamp} {by}：{resolution}"
    col, idx = item["where"].split("[", 1)
    idx = int(idx.split("]")[0])
    key = {"conflict": "resolution", "low_confidence": "resolution_note"}.get(item["kind"])
    if not key:
        sys.stderr.write("agenda: a failed survival test is not closed by a ruling — rerun the □/◊ test, "
                         "then either fix the entry or drop it\n")
        sys.exit(2)
    section = "conflicts_for_legislation" if item["kind"] == "conflict" else col
    lines = open(path, encoding="utf-8").read().splitlines(keepends=True)
    start = next((i for i, l in enumerate(lines) if re.match(rf"^{re.escape(section)}\s*:", l)), None)
    if start is None:
        sys.stderr.write(f"agenda: section {section} not found in {path}\n"); sys.exit(2)
    # the section's list items: lines whose indent is the section's first "- " indent
    item_indent, seen, begin, end = None, -1, None, None
    for i in range(start + 1, len(lines) + 1):
        line = lines[i] if i < len(lines) else ""
        stripped = line.strip()
        if i < len(lines) and (not stripped or stripped.startswith("#")):
            continue
        indent = len(line) - len(line.lstrip()) if i < len(lines) else 0
        is_item = i < len(lines) and stripped.startswith("- ")
        if item_indent is None and is_item:
            item_indent = indent
        if i >= len(lines) or (indent == 0 and stripped and not is_item):        # section ended
            if begin is not None:
                end = i
            break
        if is_item and indent == item_indent:
            seen += 1
            if seen == idx:
                begin = i
            elif begin is not None and end is None:
                end = i
                break
    if begin is None:
        sys.stderr.write(f"agenda: could not locate {section}[{idx}] in {path} — edit it by hand\n"); sys.exit(2)
    end = end if end is not None else len(lines)
    while end > begin and not lines[end - 1].strip():
        end -= 1
    pad = " " * (item_indent + 2)
    quoted = text.replace('"', "'")
    lines.insert(end, f'{pad}{key}: "{quoted}"\n')
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.writelines(lines)
    if not (yaml.safe_load(open(tmp, encoding="utf-8")) or {}).get(section, [{}])[idx].get(key):
        sys.stderr.write("agenda: the write-back did not land where it should — file left untouched\n")
        os.remove(tmp); sys.exit(2)
    os.replace(tmp, path)
    return text



# ══════════════════════════════════════════════════════════════════════════
# G1 世界裁决记录（markdown）——与不变量卡同一段仪式，不同的制品
#
# 为什么放进 ratify 而不是另开一个 skill：人要的是「从草稿到签字」那段仪式本身，
# 而这段仪式在卡与 G1 上是同一个形状——从文件里读出未决项、逐条呈、当场裁、
# 带姓名日期写回、再跑判据、最后才签。两个 skill 教同一件事，早晚会漂成两套说法。
# 不同的只有末端：卡签在 lock_done_when.py，G1 签在 aidlc_state.py gate g1。
# ══════════════════════════════════════════════════════════════════════════

G1_TITLE = re.compile(r"^#\s+G1\s*世界裁决记录", re.M)
OQ_ID = re.compile(r"\b(OQ-\d+)\b")
SHA256 = re.compile(r"\b[0-9a-f]{64}\b")
# 四问的小标题：模板写成有序列表的粗体项
FOUR_Q = [
    ("Q1", "实体是不是我认的那些"),
    ("Q2", "有没有技术上对、产品上错"),
    ("Q3", "每条形态决策从哪条规律推出来的"),
    ("Q4", "含谓词的决策，能对一份最小样例算出来吗"),
]
PLACEHOLDER = re.compile(r"^\s*(<[^>]*>|\|\s*[-|\s]*\||-{3,})\s*$")


def is_g1_record(path):
    if not path.lower().endswith((".md", ".markdown")):
        return False
    try:
        with open(path, encoding="utf-8") as f:
            return bool(G1_TITLE.search(f.read(4000)))
    except OSError:
        return False


def md_section(text, pattern):
    """→ (start_line, end_line, body_lines)；按标题切，body 不含标题行。"""
    lines = text.splitlines()
    rx = re.compile(pattern)
    start = None
    for i, l in enumerate(lines):
        if l.startswith("#") and rx.search(l):
            start = i
            break
    if start is None:
        return None
    level = len(lines[start]) - len(lines[start].lstrip("#"))
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("#"):
            lvl = len(lines[j]) - len(lines[j].lstrip("#"))
            if lvl <= level:
                return (start, j, lines[start + 1:j])
    return (start, len(lines), lines[start + 1:])


def _substantive(body):
    """这一节有没有人真的写了东西（表头、分隔线、<占位符>、引用块都不算）。"""
    for l in body:
        s = l.strip()
        if not s or s.startswith(">") or PLACEHOLDER.match(s):
            continue
        if s.startswith("|") and set(s) <= set("|-: "):
            continue
        if s.startswith("|") and re.search(r"<[^>]*>", s):
            continue
        return True
    return False


def _table_rows(body):
    """表格里真正的数据行。

    表头必须跳掉：模板自带的 `| 决策 | 最小样例 | … |` 是有真实文字的，
    把它算成数据行会让「这一节还空着」永远为假——一道永远不响的闸。
    判据是 markdown 自己的：紧跟分隔线的那一行是表头。
    """
    rows, skip = [], set()
    stripped = [l.strip() for l in body]
    for i, s in enumerate(stripped):
        if s.startswith("|") and set(s) <= set("|-: ") and i > 0 and stripped[i - 1].startswith("|"):
            skip.add(i - 1)
    for i, s in enumerate(stripped):
        if i in skip:
            continue
        if not s.startswith("|"):
            continue
        if set(s) <= set("|-: "):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not any(cells):
            continue
        if all(re.fullmatch(r"<[^>]*>|", c) for c in cells):
            continue
        rows.append(cells)
    return rows


def psl_open_questions(psl_path):
    """PSL 的 Open Questions 节里每一条的 id 与一句话。读不到就返回 None——
    读不到不等于没有，这个区别要让上面看见。"""
    if not psl_path or not os.path.isfile(psl_path):
        return None
    text = open(psl_path, encoding="utf-8").read()
    sec = md_section(text, r"Open\s*Questions|开放问题|未决")
    if not sec:
        return []
    out = []
    for l in sec[2]:
        m = OQ_ID.search(l)
        if m and l.strip().startswith(("-", "*", "+")):
            out.append((m.group(1), l.strip().lstrip("-*+ ").replace("**", "").strip()[:160]))
    return out


def g1_open_items(path, psl=None, derived=None, dos=None):
    """G1 记录上还没被回答的东西。每一条都从文件里读出来，不从记忆里挑。"""
    text = open(path, encoding="utf-8").read()
    out = []

    head = text[:1200]
    psl_path = psl
    if not psl_path:
        m = re.search(r"\*\*PSL\*\*\s*:\s*([^\s　]+)", head)
        if m and m.group(1) not in ("<path>",):
            cand = m.group(1)
            psl_path = cand if os.path.isabs(cand) else os.path.join(os.path.dirname(os.path.abspath(path)), cand)
            if not os.path.isfile(psl_path):
                psl_path = cand

    # ① 四问——模板自带的是**问题**，答案是仪式追加的那种（带日期 · 姓名 ·（Qn））。
    #    用 _substantive 判这一节会永远为真：问题文字本身就是文字。
    four = md_section(text, r"四问")
    answered = set(re.findall(r"[（(](Q[1-4])[)）]", "\n".join(four[2]))) if four else set()
    for qid, qtext in FOUR_Q:
        if four and qid not in answered:
            out.append({"id": qid, "kind": "four_question",
                        "what": f"G1 四问之一还没答：{qtext}",
                        "evidence": {"提示": "「差不多」不是答案；Q3 要逐条点出无引用锚的决策，Q4 要给最小样例"},
                        "where": "四问"})

    # ② PSL 的每一条 Open Question 都要有一行裁决
    oqs = psl_open_questions(psl_path)
    if oqs is None:
        out.append({"id": "PSL", "kind": "psl_unreachable",
                    "what": "读不到 PSL，无法核对它的 Open Questions 是否都被裁过",
                    "evidence": {"header 里的 PSL": psl_path or "（未写）",
                                 "提示": "读不到 ≠ 没有；用 --psl 指过来，或把 header 的路径写对"},
                    "where": "header · **PSL**"})
    else:
        sec = md_section(text, r"Open\s*Questions")
        ruled = {}
        if sec:
            for cells in _table_rows(sec[2]):
                m = OQ_ID.search(cells[0] if cells else "")
                if m:
                    ruled[m.group(1)] = cells[1] if len(cells) > 1 else ""
        for oq_id, oq_text in oqs:
            verdict = ruled.get(oq_id)
            if verdict is None:
                out.append({"id": oq_id, "kind": "psl_oq",
                            "what": "PSL 的承重空槽，要你三选一：接受 seam / 现在回答 / 阻塞",
                            "evidence": {"原文": oq_text},
                            "where": "Open Questions 表"})
            elif "阻塞" in verdict or "block" in verdict.lower():
                out.append({"id": oq_id, "kind": "blocking_oq",
                            "what": "这条被裁为**阻塞**：G1 不能 PASS，要先写清阻塞点与谁来答",
                            "evidence": {"原文": oq_text, "当前裁决": verdict},
                            "where": "Open Questions 表"})

    # ③ 分歧集 / verify_derived flag
    div_file = os.path.join(derived, "divergence.md") if derived else None
    sec = md_section(text, r"分歧集")
    has_div_source = bool(div_file and os.path.isfile(div_file))
    if sec and not _table_rows(sec[2]) and has_div_source:
        out.append({"id": "DIV", "kind": "divergence",
                    "what": "分歧集非空但记录里一行都没有：每条分歧与每条 flag 都要落到一行并点名议程项",
                    "evidence": {"来源": div_file, "提示": "flag 不点名议程项就会悬空"},
                    "where": "分歧集逐条回应"})

    # ④ 应然 ↔ 现状对账（有 dos.yaml 时必填）
    sec = md_section(text, r"应然\s*↔\s*现状|对账")
    if sec and not _table_rows(sec[2]) and dos and os.path.isfile(dos):
        out.append({"id": "REC", "kind": "reconciliation",
                    "what": "有 dos.yaml，应然↔现状对账就必须填：这件事按约定在 G1 记录里做",
                    "evidence": {"dos": dos},
                    "where": "应然 ↔ 现状对账"})

    # ⑤ 明确不做（下游 verify_issue.py --g1 读的就是这一节）
    sec = md_section(text, r"明确不做")
    words = []
    if sec:
        for l in sec[2]:
            s = l.strip()
            if s.startswith(">") or not s.startswith(("-", "*", "+")):
                continue
            w = re.split(r"—|--|:|：", s.lstrip("-*+ "), 1)[0].strip().strip("`")
            if len(w) >= 2 and not w.startswith("<"):
                words.append(w)
    if not words:
        out.append({"id": "NEG", "kind": "negations",
                    "what": "「明确不做」是空的：留空 = verify_issue.py 报「这份 issue 的措辞无从核对」",
                    "evidence": {"提示": "一行一个词，不能写成散文——散文里否掉的东西只在人记得时才算被否掉"},
                    "where": "明确不做"})

    # ⑥ 外部证据（PSL 轨强制）
    sec = md_section(text, r"外部证据")
    if sec and not _substantive([l for l in sec[2] if "<path" not in l]):
        out.append({"id": "EXT", "kind": "external_evidence",
                    "what": "PSL 轨强制至少一项外部证据：原型走查 / 用户验证，或明写「未做，原因：…」",
                    "evidence": {"提示": "「未做 + 原因」是合法答案；空着不是"},
                    "where": "外部证据"})

    # ⑦ 决定与签字版哈希
    sec = md_section(text, r"^\s*#+\s*决定|决定")
    decided = False
    if sec:
        body = "\n".join(sec[2])
        if re.search(r"\[\s*[xX]\s*\]\s*\*\*?PASS", body) or re.search(r"\[\s*[xX]\s*\]\s*\*\*?REJECT", body):
            decided = True
        named = set(SHA256.findall(body))
        if re.search(r"\[\s*[xX]\s*\]\s*\*\*?PASS", body):
            fd = os.path.join(derived, "form-draft.md") if derived else None
            if fd and os.path.isfile(fd):
                import hashlib
                h = hashlib.sha256(open(fd, "rb").read()).hexdigest()
                if h not in named:
                    out.append({"id": "SHA", "kind": "sha_mismatch",
                                "what": "决定是 PASS，但记录里的 sha256 不是当前 derived/form-draft.md",
                                "evidence": {"当前": h, "记录里": sorted(named) or "（没写）"},
                                "where": "决定"})
            elif not named:
                out.append({"id": "SHA", "kind": "sha_missing",
                            "what": "决定是 PASS 但没有签字版形态草案的 sha256——签的是哪一份说不清",
                            "evidence": {}, "where": "决定"})
    if not decided:
        out.append({"id": "DEC", "kind": "decision",
                    "what": "决定还没勾：PASS 还是 REJECT。这一条永远排在最后——前面全答完才轮到它",
                    "evidence": {}, "where": "决定"})
    return out


G1_APPEND = {
    "four_question": ("四问", "- {stamp} {by}（{qid}）：{text}"),
    "psl_oq": ("Open Questions", "| {qid} | {verdict} | {stamp} {by}：{text} |"),
    "blocking_oq": ("Open Questions", "| {qid} | {verdict} | {stamp} {by}：{text} |"),
    "divergence": ("分歧集", "| — | {qid} | {text} | — | — |"),
    "reconciliation": ("应然 ↔ 现状对账|对账", "| {text} | — | — | — |"),
    "negations": ("明确不做", "- {text}"),
    "external_evidence": ("外部证据", "- [x] {text} — {stamp} {by}"),
}
OQ_VERDICTS = {"accept_seam": "接受 seam", "answer": "现在回答", "blocking": "阻塞"}


def g1_apply(path, item, resolution, by, verdict=None):
    """把一条裁决写回记录里对应的那一节。追加，不改写既有行。"""
    kind = item["kind"]
    if kind in ("decision", "sha_mismatch", "sha_missing", "psl_unreachable"):
        sys.stderr.write("agenda: 这一条不是靠一句裁决关掉的——"
                         "决定与哈希在签字那一步写，PSL 读不到要先把路径指对\n")
        sys.exit(2)
    if kind in ("psl_oq", "blocking_oq") and verdict not in OQ_VERDICTS:
        sys.stderr.write(f"agenda: PSL 的 Open Question 要三选一：--verdict {'|'.join(OQ_VERDICTS)}\n")
        sys.exit(2)
    sec_pat, tmpl = G1_APPEND[kind]
    text_all = open(path, encoding="utf-8").read()
    sec = md_section(text_all, sec_pat)
    if not sec:
        sys.stderr.write(f"agenda: 记录里找不到「{sec_pat}」这一节\n"); sys.exit(2)
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
    line = tmpl.format(stamp=stamp, by=by, qid=item["id"],
                       verdict=OQ_VERDICTS.get(verdict, ""), text=resolution)
    lines = text_all.splitlines(keepends=True)
    if line.lstrip().startswith("|"):
        # 表格行要插在表**里**——插到节末会落在表格后面的散文之后，
        # 把表结构撑断，而 markdown 不会报错，只是默默渲染成两段。
        end = None
        for i in range(sec[0] + 1, sec[1]):
            if lines[i].strip().startswith("|"):
                end = i + 1
        if end is None:
            sys.stderr.write(f"agenda: 「{sec_pat}」这一节里找不到表格——手工填\n"); sys.exit(2)
    else:
        end = sec[1]
        while end > sec[0] + 1 and not lines[end - 1].strip():
            end -= 1
    lines.insert(end, line + "\n")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.writelines(lines)
    if line not in open(tmp, encoding="utf-8").read():
        os.remove(tmp)
        sys.stderr.write("agenda: 写回没落到该落的地方——文件未动\n"); sys.exit(2)
    os.replace(tmp, path)
    return line


def g1_main(a):
    """G1 记录走的那一条——同一段仪式，另一个制品。"""
    def items():
        return g1_open_items(a.card, psl=a.psl, derived=a.derived, dos=a.dos)

    if a.rule:
        if not a.resolution or not a.resolution.strip():
            sys.stderr.write("agenda: --resolution is required and may not be empty\n"); sys.exit(2)
        if DEFERRAL.match(a.resolution):
            sys.stderr.write("agenda: 这是拖延不是裁决。拖延是合法的——把它移进 open_questions 并写上负责人与"
                             "截止日期；它不能跟着签字一起过去\n")
            sys.exit(2)
        if not a.by or not a.by.strip():
            sys.stderr.write("agenda: --by is required: a ruling without a name is not a ruling\n"); sys.exit(2)
        cur = items()
        it = next((x for n, x in enumerate(cur, 1) if a.rule in (x["id"], str(n))), None)
        if it is None:
            sys.stderr.write(f"agenda: no open item {a.rule!r}; open now: {[i['id'] for i in cur] or '（无）'}\n")
            sys.exit(2)
        line = g1_apply(a.card, it, a.resolution.strip(), a.by.strip(), a.verdict)
        left = items()
        print(json.dumps({"ok": True, "ruled": it["id"], "recorded": line.strip(),
                          "still_open": [i["id"] for i in left]}, ensure_ascii=False, indent=2))
        return

    cur = items()
    if a.check:
        if cur:
            sys.stderr.write(f"agenda: {len(cur)} item(s) still open: {[i['id'] for i in cur]}\n")
            sys.exit(1)
        return
    if a.json:
        print(json.dumps({"record": a.card, "open": len(cur), "items": cur}, ensure_ascii=False, indent=2))
        return
    if not cur:
        print("议程为空：这份 G1 记录没有未决项——可以签了。")
        return
    blocking = [i for i in cur if i["kind"] == "blocking_oq"]
    print(f"这份 G1 记录还有 {len(cur)} 项要你裁：\n")
    for n, it in enumerate(cur, 1):
        print(f"{n}. [{it['id']}·{it['kind']}] {it['what']}")
        for k, v in (it["evidence"] or {}).items():
            if v:
                print(f"     {k}: {str(v)[:300]}")
        print(f"     写回：{it['where']}\n")
    if blocking:
        print(f"其中 {len(blocking)} 项被裁为**阻塞**：G1 不能 PASS，"
              f"先写清阻塞点与谁来答（{[i['id'] for i in blocking]}）")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("card")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--rule", help="item id or its number in the printed agenda")
    ap.add_argument("--resolution")
    ap.add_argument("--by", help="the human who ruled — never an agent name")
    ap.add_argument("--psl", help="G1：PSL 文件路径（默认读记录 header 里的 **PSL**:）")
    ap.add_argument("--derived", help="G1：psl-derive 的 derived/ 目录，用来核对分歧集与形态草案哈希")
    ap.add_argument("--dos", help="G1：dos.yaml 路径，用来判断应然↔现状对账是不是必填")
    ap.add_argument("--verdict", choices=sorted(OQ_VERDICTS), help="G1：裁 PSL 的 Open Question 时三选一")
    a = ap.parse_args()

    if is_g1_record(a.card):
        return g1_main(a)

    card = load(a.card)

    if a.rule:
        if not a.resolution or not a.resolution.strip():
            sys.stderr.write("agenda: --resolution is required and may not be empty\n"); sys.exit(2)
        if DEFERRAL.match(a.resolution):
            sys.stderr.write("agenda: that is a deferral, not a ruling. Deferring is fine — move the item to "
                             "open_questions with an owner and a deadline; it cannot ride along into a signature\n")
            sys.exit(2)
        if not a.by or not a.by.strip():
            sys.stderr.write("agenda: --by is required: a ruling without a name is not a ruling\n"); sys.exit(2)
        item = find_item(card, a.rule)
        text = apply_ruling(a.card, card, item, a.resolution.strip(), a.by.strip())
        left = open_items(load(a.card))
        print(json.dumps({"ok": True, "ruled": item["id"], "recorded": text,
                          "still_open": [i["id"] for i in left]}, ensure_ascii=False, indent=2))
        return

    items = open_items(card)
    if a.check:
        if items:
            sys.stderr.write(f"agenda: {len(items)} item(s) still open: {[i['id'] for i in items]}\n")
            sys.exit(1)
        return
    if a.json:
        print(json.dumps({"card": a.card, "open": len(items), "items": items}, ensure_ascii=False, indent=2))
        return
    if not items:
        print("议程为空：这张卡没有未决项。")
        return
    print(f"这张卡还有 {len(items)} 项要你裁：\n")
    for n, it in enumerate(items, 1):
        print(f"{n}. [{it['id']}·{it['kind']}] {it['what']}")
        for k, v in (it["evidence"] or {}).items():
            if v:
                print(f"     {k}: {str(v)[:300]}")
        print(f"     写回：{it['where']}\n")


if __name__ == "__main__":
    main()
