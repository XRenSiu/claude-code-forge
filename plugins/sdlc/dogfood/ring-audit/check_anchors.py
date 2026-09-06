#!/usr/bin/env python3
"""check_anchors.py — 证据锚点的抗漂移锁（重审 2026-09-06 的产物）。

为什么存在
----------
audit.yaml 里 800 多条证据，其中 400 多条带行号锚点，两种写法都收：
`<file>#L<n>` / `#L<a>-L<b>`（evidence 的 ref 惯用）与 `<file>:<n>`（正文散句惯用）。
行号会漂：本轮 graph.yaml 插入 agent.pr-reviewer 节点（+10 行）与两条边（+2 行），
插入点之后的锚点分两段位移——`#L239` 本该指 human.merge，插完之后指到了新节点头上。

漂移**不被任何现有检查抓到**。check_audit.py 只看 evidence 的 kind 与 ref 非空，
不看 ref 是否还指着当初那句话；越界也抓不到，因为文件是变长的。一份锚点全指错的审计
照样 exit 0——那正是"报告声称有证据"与"证据还在原处"之间的缝。本轮手工修了 105 处，
修完如果不留工具，下一次插一行又全烂，而且没人会知道。

它凭什么判
----------
不猜、不算术、不依赖某个历史 commit：`snapshot` 把每个锚点当时指着的**那几行的哈希**
存进 `anchors.lock`；`verify` 拿当前文件重算。哈希一致 = 锚点仍指着同一段字，
不一致就到全文里找那段原文——找到且唯一即 MOVED（位置变了，内容没变，可 --fix 改），
找不到即 GONE（内容被改写了），多处命中即 AMBIGUOUS（原文不唯一，机器不该替人选）。

`--fix` 只改 MOVED。GONE 与 AMBIGUOUS 永不自动改：那是"内容变了"而不是"位置变了"，
替审计者决定新锚点指哪儿，就是替他下判断。

退出码
------
  0  verify 全部 SAME（UNLOCKED 只 warn：那是快照之后新写的锚点，不是漂移）
  1  有 MOVED / GONE / AMBIGUOUS / UNRESOLVED —— 报告在拿一个已经不指着原文的行号当证据。
     AMBIGUOUS 也算：走到那一支时"当前行号对不上锁"已经成立，不确定的只是它移到哪儿；
     UNRESOLVED 也算：归不出文件的锚点不等于没问题的锚点。
  2  用法错误 / 锁文件缺失、为空、损坏 / audit 文件不存在

这条闸现在的位置
----------------
独立工具，**不在** check_audit.py 里：那份是 role=gate 的冻结脚本，往里加检查要走变更提案。
缺口与提案见 audit.yaml 的 `spine/newly_identified/control/evidence-anchors-unprotected`
与 `P-RA-07`。在它被并进去之前，这条闸靠人记得跑——所以它自己也还不是"不可跳过"的。
"""

import argparse
import collections
import hashlib
import json
import os
import re
import sys

BASENAMES = {
    "graph.yaml": "plugins/sdlc/skills/sdlc/assets/graph.yaml",
    "loops.yaml": "plugins/sdlc/skills/sdlc/assets/loops.yaml",
    "routing.yaml": "plugins/sdlc/skills/sdlc/assets/routing.yaml",
    "triggers.yaml": "plugins/sdlc/skills/sdlc/assets/triggers.yaml",
    "ARCHITECTURE.md": "plugins/sdlc/docs/ARCHITECTURE.md",
    "design-notes.md": "plugins/sdlc/docs/design-notes.md",
    "lifecycle.md": "plugins/sdlc/docs/lifecycle.md",
    "sdlc_state.py": "plugins/sdlc/skills/sdlc/scripts/sdlc_state.py",
    "dos.yaml": "plugins/sdlc/dogfood/ring-audit/dos.yaml",
    "ratchet-log-format.md": "plugins/sdlc/skills/acceptance-fleet/references/ratchet-log-format.md",
    "verify_pr.py": "plugins/sdlc/skills/pr/scripts/verify_pr.py",
    "pr-poll.sh": "plugins/sdlc/skills/review-loop/scripts/pr-poll.sh",
    "tune.py": "plugins/sdlc/skills/tune/scripts/tune.py",
    "metrics.py": "plugins/sdlc/skills/retro/scripts/metrics.py",
    "next_iteration.py": "plugins/sdlc/skills/acceptance-fleet/scripts/next_iteration.py",
    "qa_facts.py": "plugins/sdlc/skills/acceptance-fleet/scripts/qa_facts.py",
    "skill-dispatch-matrix.md": "plugins/sdlc/skills/acceptance-fleet/references/skill-dispatch-matrix.md",
    "references/finding-schema.yaml": "plugins/sdlc/skills/qa-reviewer/references/finding-schema.yaml",
    "references/divergence-types.md": "plugins/sdlc/skills/spec-drift-detector/references/divergence-types.md",
    "check_audit.py": "plugins/sdlc/dogfood/ring-audit/check_audit.py",
    "verify_loop.py": "plugins/sdlc/skills/sdlc/scripts/verify_loop.py",
    "verify_graph.py": "plugins/sdlc/skills/sdlc/scripts/verify_graph.py",
    "trace.py": "plugins/sdlc/skills/sdlc/scripts/trace.py",
    "lock_done_when.py": "plugins/sdlc/skills/sdlc/scripts/lock_done_when.py",
    "verify_dos.py": "plugins/sdlc/skills/dos-extract/scripts/verify_dos.py",
    "verify_commit.py": "plugins/sdlc/skills/commit/scripts/verify_commit.py",
    "smoke.sh": "plugins/sdlc/eval/smoke.sh",
    "validate_done_when.py": "plugins/sdlc/skills/acceptance-spec/scripts/validate_done_when.py",
    "validate_done_when_v2.py": "plugins/sdlc/skills/donewhen-extract/scripts/validate_done_when_v2.py",
    "verify_psl.py": "plugins/sdlc/skills/psl/scripts/verify_psl.py",
    "verify_derived.py": "plugins/sdlc/skills/psl-derive/scripts/verify_derived.py",
    "verify_issue.py": "plugins/sdlc/skills/issue/scripts/verify_issue.py",
    "verify_card.py": "plugins/sdlc/skills/invariant-extract/scripts/verify_card.py",
    "lint_cards.py": "plugins/sdlc/skills/plan-cards/scripts/lint_cards.py",
    "verify_release.py": "plugins/sdlc/skills/release/scripts/verify_release.py",
    "apply_proposal.py": "plugins/sdlc/skills/tune/scripts/apply_proposal.py",
    "post_review.py": "plugins/sdlc/skills/pr-review/scripts/post_review.py",
    "compute_score.py": "plugins/sdlc/skills/spec-gaming-detector/scripts/compute_score.py",
    "compute_confidence.py": "plugins/sdlc/skills/meta-judge/scripts/compute_confidence.py",
    "reconcile_dos.py": "plugins/sdlc/skills/dos-extract/scripts/reconcile_dos.py",
    "dos_closure.py": "plugins/sdlc/skills/dos-extract/scripts/dos_closure.py",
    "findings_template.yaml": "plugins/sdlc/skills/pr-review/assets/findings_template.yaml",
}

# `unenforced_rules[].dos_anchors` 里的 `#L376-L379` 是**匹配模式**，render_audit.py 拿它去
# gaps[].evidence[].ref 里现算归属；它不是一条指向某文件某行的引用，锁它没有意义。
NOT_A_REFERENCE = re.compile(r"^\s*(?:-\s+)?.*\bdos_anchors:")

# 审计里的行引用有**三**种写法，都会漂，都要保：
#   `path/to/file.py#L12` / `#L12-L20` / `#L12–20`   —— evidence 的 ref 惯用
#   `path/to/file.py:12` / `:12-20`                   —— 正文散句里惯用
#   `（#L73-L96）`  文件名在句子前半句点过，括号里只剩行号 —— 正文里最常见的一种
# 第三种是本工具第一版与第二版都漏掉的那 78 处（PR #3 预审 F-1）：它们连 UNRESOLVED 都不算，
# 静默跳过，于是「432/432 全绿」读起来像全覆盖，实际只覆盖了带文件名的那部分。
# 归属规则：裸锚点归给**同一个值块里、它左边最近一次出现的文件名**；归不出来就记 UNRESOLVED，
# 并且 UNRESOLVED 会让 verify 非零退出——一个查不出归属的锚点不能算"没问题"。
FILE_RE = r"[A-Za-z0-9_./<>*-]+\.(?:py|sh|yaml|json|md)"
# 每个文件名 token 都匹配（带不带锚点都要，因为它要更新"最近的文件名"），裸锚点单独一支。
SCAN = re.compile(
    rf"(?P<fname>{FILE_RE})"
    rf"(?:#L(?P<qa>\d+)(?:(?P<qd>[-–])L?(?P<qb>\d+))?"
    rf"|:(?P<ca>\d+)(?:(?P<cd>[-–])(?P<cb>\d+))?(?![\d/]))?"
    rf"|(?<![\w./-])#L(?P<ba>\d+)(?:(?P<bd>[-–])L?(?P<bb>\d+))?")
# 新的映射键起一行时，"最近的文件名"作废——跨判词继承会把锚点归到毫不相干的文件上。
NEW_KEY = re.compile(r"^\s*(?:-\s+)?[A-Za-z_][\w.<>+-]*:(?:\s|$)")
PART_ID = re.compile(r"^\s*-?\s*id:\s*([A-Za-z0-9_.<>-]+)\s*$")


def die(msg, code=2):
    sys.stderr.write(f"check_anchors: {msg}\n")
    sys.exit(code)


def digest(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:16]


def skill_paths():
    """<skill> → 它的 SKILL.md。裸 `SKILL.md#L` 靠所在 Part 的 id 消歧。"""
    out = {}
    root = "plugins/sdlc/skills"
    if os.path.isdir(root):
        for d in sorted(os.listdir(root)):
            p = f"{root}/{d}/SKILL.md"
            if os.path.isfile(p):
                out[d] = p
    return out


def resolve(name, part, skills):
    if name.startswith(("plugins/", "specs/", ".sdlc/")):
        return name
    if name in BASENAMES:
        return BASENAMES[name]
    if name.endswith("/SKILL.md") and name.count("/") == 1:
        return f"plugins/sdlc/skills/{name}"
    # `acceptance-fleet/scripts/next_iteration.py` 这种带 skill 名前缀的相对写法
    head = name.split("/", 1)[0]
    if "/" in name and os.path.isdir(f"plugins/sdlc/skills/{head}"):
        return f"plugins/sdlc/skills/{name}"
    if name == "SKILL.md" and part in skills:
        return skills[part]
    return None


def walk_anchors(audit_path, skills, on_anchor):
    """逐行扫 audit.yaml，把每个锚点交给 on_anchor(name, path, a, b, dash, part, style)。
    回调返回替换串（或 None 表示不动）。返回改写后的全文。

    裸锚点（`（#L73-L96）`）没有自带文件名，归给同一个值块里它左边最近一次出现的文件名。
    因此本函数必须**顺序**扫：每遇到一个文件名 token 就更新 last_file，遇到裸锚点就用它。
    """
    raw = open(audit_path, encoding="utf-8").read()
    part = [None]
    last_file = [None]
    out = []
    for line in raw.splitlines(keepends=True):
        stripped = line.rstrip("\n")
        pm = PART_ID.match(stripped)
        if pm and pm.group(1) in skills:
            part[0] = pm.group(1)
        if NEW_KEY.match(stripped):
            last_file[0] = None          # 换判词就换话题，别把上一条的文件名带过来
        if NOT_A_REFERENCE.match(stripped):
            out.append(line)             # dos_anchors 是模式不是引用
            continue

        def sub(m):
            if m.group("fname"):
                name = m.group("fname")
                last_file[0] = name
                if m.group("qa") is not None:
                    style, a, dash, b = "hash", int(m.group("qa")), m.group("qd"), m.group("qb")
                elif m.group("ca") is not None:
                    style, a, dash, b = "colon", int(m.group("ca")), m.group("cd"), m.group("cb")
                else:
                    return m.group(0)     # 只是提到一个文件名，不是锚点
            else:
                name = last_file[0]
                style, a, dash, b = "bare", int(m.group("ba")), m.group("bd"), m.group("bb")
            b = int(b) if b else a
            path = resolve(name, part[0], skills) if name else None
            r = on_anchor(name, path, a, b, dash, part[0], style)
            return r if r is not None else m.group(0)

        out.append(SCAN.sub(sub, line))
    return "".join(out)


class Reader:
    def __init__(self):
        self._c = {}

    def lines(self, path):
        if path not in self._c:
            try:
                self._c[path] = open(path, encoding="utf-8").read().splitlines()
            except OSError:
                self._c[path] = None
        return self._c[path]


def key_of(path, a, b):
    return f"{path}#L{a}" + (f"-L{b}" if b != a else "")


def cmd_snapshot(args):
    reader, skills = Reader(), skill_paths()
    lock, stats = {}, collections.Counter()

    def on(name, path, a, b, dash, part, style="hash"):
        if path is None:
            stats["unresolved"] += 1
            return None
        lines = reader.lines(path)
        if lines is None or b > len(lines):
            stats["unreadable"] += 1
            return None
        block = lines[a - 1:b]
        if all(not x.strip() for x in block):
            stats["blank"] += 1
            return None
        lock[key_of(path, a, b)] = {"sha": digest(block), "lines": b - a + 1}
        stats["locked"] += 1
        return None

    walk_anchors(args.audit, skills, on)
    if not lock:
        die("锁里一个条目都没有 —— audit.yaml 里没找到可解析的行号锚点", 2)
    payload = {"schema": "anchors-lock/1", "audit": args.audit, "entries": lock}
    with open(args.lock, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"check_anchors snapshot: {len(lock)} 个锚点已锁进 {args.lock}")
    for k in ("unresolved", "unreadable", "blank"):
        if stats[k]:
            print(f"  未锁（{k}）: {stats[k]}")
    return 0


def cmd_verify(args):
    if not os.path.isfile(args.lock):
        die(f"锁文件不存在: {args.lock}（先跑 snapshot）", 2)
    try:
        payload = json.load(open(args.lock, encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        # 锁读不出来就退 2 而不是让异常裸奔：exit 1 在这里的含义是"锚点漂了"，
        # 拿它表示"锁坏了"会让调用方把两件事混为一谈。
        die(f"锁文件读不出来: {args.lock} — {exc}", 2)
    if not isinstance(payload, dict):
        die(f"锁文件不是一个对象: {args.lock}", 2)
    lock = payload.get("entries") or {}
    if not lock:
        die(f"{args.lock} 里没有任何条目", 2)
    reader, skills = Reader(), skill_paths()
    stats = collections.Counter()
    problems = []

    def on(name, path, a, b, dash, part, style="hash"):
        if path is None:
            stats["UNRESOLVED"] += 1
            shown = f"#L{a}" if style == "bare" else f"{name}#L{a}"
            problems.append(("UNRESOLVED", shown, part,
                             "归不出文件：裸锚点左边没有可解析的文件名，或该文件名不在映射里"
                             if style == "bare" else f"{name} 解析不到仓库路径"))
            return None
        entry = lock.get(key_of(path, a, b))
        lines = reader.lines(path)
        if lines is None:
            stats["GONE"] += 1
            problems.append(("GONE", f"{name}#L{a}", part, f"{path} 读不到"))
            return None
        if entry is None:
            # 锁里没有 = 这个锚点是快照之后新写的。报，但不算漂移。
            stats["UNLOCKED"] += 1
            problems.append(("UNLOCKED", key_of(name, a, b), part, "锁里没有它 —— 快照之后新增的锚点，跑一次 snapshot 收进来"))
            return None
        cur = lines[a - 1:b] if b <= len(lines) else []
        if cur and digest(cur) == entry["sha"]:
            stats["SAME"] += 1
            return None
        # 内容对不上：到全文里找锁住的那一段
        n = entry["lines"]
        hits = [i for i in range(len(lines) - n + 1)
                if digest(lines[i:i + n]) == entry["sha"]]
        if len(hits) == 1:
            na = hits[0] + 1
            nb = na + n - 1
            stats["MOVED"] += 1
            problems.append(("MOVED", key_of(name, a, b), part,
                             f"原文整段移到 L{na}" + (f"-L{nb}" if nb != na else "")))
            if args.fix:
                if style == "colon":
                    return f"{name}:{na}" + (f"{dash}{nb}" if dash else "")
                if style == "bare":
                    # 裸锚点原样是裸的：补上文件名会改写审计的行文
                    return f"#L{na}" + (f"{dash}L{nb}" if dash else "")
                return f"{name}#L{na}" + (f"{dash}L{nb}" if dash else "")
            return None
        if not hits:
            now = lines[a - 1].strip()[:60] if a <= len(lines) else "<超出文件尾>"
            stats["GONE"] += 1
            problems.append(("GONE", key_of(name, a, b), part,
                             f"锁住的原文已不存在；该行号现在是 {now!r}"))
            return None
        stats["AMBIGUOUS"] += 1
        problems.append(("AMBIGUOUS", key_of(name, a, b), part,
                         f"锁住的原文在当前文件里出现 {len(hits)} 次，机器不替人选"))
        return None

    fixed = walk_anchors(args.audit, skills, on)
    if args.fix and stats["MOVED"]:
        open(args.audit, "w", encoding="utf-8").write(fixed)

    total = sum(stats.values())
    covered = stats["SAME"] + stats["MOVED"] + stats["GONE"] + stats["AMBIGUOUS"]
    print(f"check_anchors verify: 走到 {total} 个行号锚点 · 锁里比对了 {covered} 个 · 锁 {args.lock}")
    for k in ("SAME", "MOVED", "GONE", "AMBIGUOUS", "UNLOCKED", "UNRESOLVED"):
        if stats[k]:
            print(f"  {k:11} {stats[k]}")
    if covered < total:
        # 覆盖率明写。"全绿"只在分母等于分子时才等于"全都检过了"——
        # 第一版正是在这里骗了人：432/432 绿，而当时另有 78 个锚点根本没进过 walk。
        print(f"  覆盖 {covered}/{total} —— 差额是未入锁的锚点，别把绿灯读成全覆盖")
    for verdict, anchor, part, detail in problems:
        where = f"（{part}）" if part else ""
        print(f"  {verdict:10} {anchor}{where} — {detail}")
    if args.fix and stats["MOVED"]:
        print(f"\n已就地改正 {stats['MOVED']} 处 MOVED；记得重跑 snapshot 刷新锁。"
              f"GONE / AMBIGUOUS 未动 —— 那是内容变了，不是位置变了。")
    # AMBIGUOUS 也退非零：走到那一支时"当前行号不再指着锁住的那段字"**已经成立**，
    # 不确定的只是它移到哪儿了。把"不能自动改"当成"没问题"，正是这条闸要防的那种绿灯
    # （PR #3 预审 F-2）。UNRESOLVED 同理：归不出文件的锚点不等于没有问题的锚点。
    bad = stats["MOVED"] + stats["GONE"] + stats["AMBIGUOUS"] + stats["UNRESOLVED"]
    if args.fix:
        bad -= stats["MOVED"]        # 刚改掉的不再算
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--audit", default="plugins/sdlc/dogfood/ring-audit/audit.yaml")
    ap.add_argument("--lock", default="plugins/sdlc/dogfood/ring-audit/anchors.lock")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("snapshot", help="把每个锚点当前指着的那几行的哈希锁下来")
    v = sub.add_parser("verify", help="按锁核对每个锚点是否还指着同一段字")
    v.add_argument("--fix", action="store_true", help="就地改正 MOVED（GONE / AMBIGUOUS 不动）")
    a = ap.parse_args()
    if not os.path.isfile(a.audit):
        die(f"audit 文件不存在: {a.audit}")
    sys.exit(cmd_snapshot(a) if a.cmd == "snapshot" else cmd_verify(a))


if __name__ == "__main__":
    main()
