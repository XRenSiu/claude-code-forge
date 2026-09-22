#!/usr/bin/env python3
"""
sync_issue.py — 把一个阶段的**结果**送回它的 issue，并核对 issue 说的还是不是真的。

为什么需要它：环是 intake → track → issue → branch → contract → g2 → cards → implement → pr …，
issue **只被写一次**，之后再没有任何一步回来。而 G1 的裁决、冻结的判据、G2 的锁、任务卡的白名单
全都发生在它后面，落在 `.aidlc/<slug>/` 与 `docs/` 里。于是团队唯一会读的那份东西（issue）
停在需求阶段，而真正管事的判据在别处——两边慢慢长成两个不同的说法，没有任何一步会发现。
（dogfood vana-builder #2321，2026-09-22：issue 的 AC 编号与冻结版整体错位两位，
签字版哈希是补签之前的，一条 AC 在冻结时掉了没人知道，而被 G2 签住的契约根本没进 git。）

所以它不只是个渲染器，**它先是一道对账**：

  ① 渲染 —— 只读文件，不读模型的说法。state.json / .done_when.lock / done_when.yaml /
     cards/*.yaml / notes.md / ledger.md 里有的才写得出来，没有的不编。
  ② 对账 —— 把 issue 正文与当前判据比：AC id 集合、锁里的哈希、被锁文件在不在版本库。
     一份锁住了未入库文件的签名，是没人能核对的签名；那不是文档不同步，是冻结机制悬空。

用法：
  sync_issue.py <issue-number> [--slug S] [--root .aidlc] [--repo owner/name]
                [--stage STAGE]        # 默认取 state.json 的当前阶段
                [--out FILE] [--json]
                [--post]               # 真的发帖 / 改帖；不给就只打印

发帖是对外副作用，**默认不发**。`--post` 按 stage 打标记（`<!-- aidlc:sync … -->`），
同一 slug 同一 stage 再跑是**改那条帖**而不是再发一条——否则每次 advance 都灌一层楼。

退出码：0 = 没有对账问题 · 1 = 有漂移（照常产出正文）· 2 = 用法 / IO 错误。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("sync_issue.py needs PyYAML: pip install pyyaml\n")
    sys.exit(2)

MARKER = "<!-- aidlc:sync slug=%s stage=%s -->"
# 「这个哈希是旧值」的明示。带了它就不是漂移，是变更史。
SUPERSEDE_RE = re.compile(r"supersed|取代|旧值|原签字版|已废|历史值", re.I)
GATES = ("g1", "g2", "g3")


def load_yaml(p):
    try:
        with open(p, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except OSError:
        return None


def load_json(p):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def read_text(p):
    try:
        with open(p, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def tracked_by_git(path, cwd):
    """这个文件进版本库了吗。没进 = 别人 clone 下来看不到它。"""
    try:
        r = subprocess.run(["git", "ls-files", "--error-unmatch", "--", path],
                           cwd=cwd, capture_output=True, text=True)
        return r.returncode == 0
    except OSError:
        return None


def gh(args, cwd=None):
    r = subprocess.run(["gh"] + args, cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


# ---- 渲染：每一节都只读文件 ------------------------------------------------------------

def sec_intake(st):
    ik = st.get("intake") or {}
    if not ik:
        return None
    ev = ik.get("size_evidence") or {}
    ev_s = "、".join(f"{k}={v}" for k, v in ev.items()) if ev else "无计数证据"
    return ("| 规模 | 来源 | 证据 | 轨道 |\n|---|---|---|---|\n"
            f"| {ik.get('size', '—')} | {ik.get('size_source', '—')} | {ev_s} | {st.get('track', '—')} |")


def sec_gate(st, gate):
    g = (st.get("gates") or {}).get(gate) or {}
    if not g or g.get("verdict") in (None, "pending"):
        return None
    rows = [f"| verdict | **{g.get('verdict')}** |",
            f"| 签字人 | {g.get('by', '—')} |",
            f"| 签字性质 | `{g.get('signer_kind', '—')}` |",
            f"| 时间 | {g.get('at', '—')} |"]
    if g.get("record"):
        rows.append(f"| 记录 | `{g['record']}` |")
    if g.get("authorization"):
        rows.append(f"| 授权原话 | {g['authorization']} |")
    return "| | |\n|---|---|\n" + "\n".join(rows)


def sec_lock(lock):
    if not lock:
        return None
    rows = "\n".join(f"| `{f['path']}` | `{f['sha256'][:16]}…` | {f.get('role', '—')} |"
                     for f in lock.get("files") or [])
    return ("被锁住的文件（改其中任何一份都要同一 diff 附变更提案并重新签锁）：\n\n"
            "| 文件 | sha256 | 角色 |\n|---|---|---|\n" + rows)


def sec_contract(dw):
    if not dw:
        return None
    acs = dw.get("acceptance") or []
    reqs = sorted({a.get("req") for a in acs if a.get("req")})
    kinds, ears = {}, {}
    for a in acs:
        kinds[a.get("kind", "—")] = kinds.get(a.get("kind", "—"), 0) + 1
        ears[a.get("ears_type", "—")] = ears.get(a.get("ears_type", "—"), 0) + 1
    out = [f"**{len(acs)} 条 AC**，覆盖 {len(reqs)} 个 REQ（{', '.join(reqs)}）。",
           "按 kind：" + "、".join(f"{k} {v}" for k, v in sorted(kinds.items())) +
           "；按 ears_type：" + "、".join(f"{k} {v}" for k, v in sorted(ears.items())) + "。", ""]
    out.append("| AC | REQ | kind | ears | observe |")
    out.append("|---|---|---|---|---|")
    for a in acs:
        out.append("| %s | %s | %s | %s | `%s` |" % (
            a.get("id"), a.get("req"), a.get("kind"), a.get("ears_type", "—"), a.get("observe", "—")))
    missing = [a["id"] for a in acs if a.get("threshold_source", "").startswith("needs_threshold_source")]
    if missing:
        out += ["", "阈值**不编**、标为待回填的 AC：" + "、".join(f"`{m}`" for m in missing) + "。"]
    if dw.get("rules"):
        out += ["", "写死在 `rules:` 里的："] + [f"- {r}" for r in dw["rules"]]
    c = dw.get("constraints") or {}
    if c.get("test_globs") or c.get("forbidden_paths"):
        out += ["", "`constraints`：`test_globs` = %s；`forbidden_paths` 覆盖 %d 条模式。" % (
            ", ".join(f"`{g}`" for g in c.get("test_globs") or []) or "—",
            len(c.get("forbidden_paths") or []))]
    return "\n".join(out)


def sec_cards(cards_dir):
    if not cards_dir or not os.path.isdir(cards_dir):
        return None
    rows, n = [], 0
    for fn in sorted(os.listdir(cards_dir)):
        if not re.match(r"CARD-.*\.ya?ml$", fn):
            continue
        c = load_yaml(os.path.join(cards_dir, fn)) or {}
        n += 1
        rows.append("| **%s** %s | %s | %d | %s | %s | %s |" % (
            c.get("id", fn), c.get("title", ""),
            ", ".join(c.get("req_ids") or []) or "—",
            len(c.get("ac_ids") or []),
            " · ".join(f"`{p}`" for p in (c.get("allowed_files") or [])) or "—",
            ", ".join(c.get("depends_on") or []) or "—",
            c.get("context_estimate_tokens", "—")))
    if not n:
        return None
    return ("| 卡 | REQ | AC | 可改文件 | 依赖 | 上下文 |\n|---|---|---|---|---|---|\n" + "\n".join(rows) +
            "\n\n三项机器校验（`lint_cards.py`）：每个 REQ 恰归一张卡 · 卡间零文件写冲突 · "
            "卡里的领域名词能被本体解析。")


def sec_notes(notes_md):
    """解释日记逐字呈现，不筛选——这是门禁仪式的规矩，搬到 issue 上也不改。"""
    if not notes_md:
        return None
    keep = []
    for block in re.split(r"^## ", notes_md, flags=re.M)[1:]:
        title = block.splitlines()[0].strip()
        if title.lower().startswith("interpretations") or "Open questions" in title:
            pass
        body = "\n".join(l for l in block.splitlines()[1:] if l.strip())
        if body:
            keep.append("**%s**\n\n%s" % (title, body))
    return "\n\n".join(keep) if keep else None


def render(st, slug, stage, paths, artefacts):
    dw, lock, notes_md = artefacts["done_when"], artefacts["lock"], artefacts["notes"]
    parts = [MARKER % (slug, stage),
             "## AI-DLC 阶段结果 · `%s`" % stage,
             "",
             "> 由 `sync_issue.py` 从 `%s` 与它指向的制品渲染，**只读文件，不读任何人的说法**。"
             "没有落在文件里的东西这里写不出来。" % os.path.relpath(paths["state"], paths["repo"]),
             ""]
    blocks = [("需求定档", sec_intake(st)),
              ("G1 世界裁决", sec_gate(st, "g1")),
              ("判据契约", sec_contract(dw)),
              ("G2 判据冻结", sec_gate(st, "g2")),
              ("G2 锁住了什么", sec_lock(lock)),
              ("G3 例外复核", sec_gate(st, "g3")),
              ("任务卡", sec_cards(paths.get("cards_dir"))),
              ("解释 / 偏离 / 取舍（逐字，不筛选）", sec_notes(notes_md))]
    for title, body in blocks:
        if body:
            parts += ["### " + title, "", body, ""]
    return "\n".join(parts).rstrip() + "\n"


# ---- 对账：issue 说的还是不是真的 -------------------------------------------------------

def reconcile(body, dw, lock, paths, extra_paths):
    """→ (drift, notes)。drift 决定退出码；notes 是看见了但不算问题的那些。"""
    drift, notes = [], []
    if body is None:
        return (["issue 正文读不到——`gh` 没装、没登录，或 issue 号不对；对账没跑，不是通过"], [])

    if dw:
        contract_ids = {a.get("id") for a in dw.get("acceptance") or [] if a.get("id")}
        body_ids = set(re.findall(r"\bAC-\d{3}-[a-z]\b", body))
        if body_ids:
            gone = sorted(body_ids - contract_ids)
            new = sorted(contract_ids - body_ids)
            if gone:
                drift.append("issue 正文里的 AC %s 在冻结契约里不存在——编号错位或判据被改过，"
                             "读 issue 的人会按一份不存在的判据干活" % gone)
            if new:
                drift.append("冻结契约里的 AC %s 在 issue 正文里没有——issue 停在冻结之前的那一版" % new)

    if lock:
        # 正文里的哈希几乎总是截断写的（`3cbdd745…`），所以按**前缀**比，不按定长比。
        # 写死 16 位会把一个正确的 8 位前缀报成漂移——那种假阳性比漏报更伤：
        # 它会教人忽略这条检查。
        locked = {f["path"]: f["sha256"] for f in lock.get("files") or []}
        seen_hex = set(re.findall(r"\b([0-9a-f]{8,64})\b", body))
        for path, sha in locked.items():
            named = os.path.basename(path) in body
            matched = any(sha.startswith(h) for h in seen_hex)
            if named and not matched:
                drift.append("issue 提到 `%s`，但正文里没有任何与它当前 sha256 `%s…` 相符的哈希"
                             "——读的人核对不了这份文件是不是锁里那份"
                             % (os.path.basename(path), sha[:8]))
        # 一个对不上的哈希，只有在正文把它当**现值**呈现时才误导人。
        # 明写了「已被 supersede」的旧值是**来路**，不是漂移——把它报成漂移，
        # 等于逼人删掉自己的变更史，而那正是这条环最不该丢的东西。
        for h in sorted(seen_hex):
            if any(sha.startswith(h) for sha in locked.values()):
                continue
            line = next((l for l in body.splitlines() if h in l), "")
            historical = SUPERSEDE_RE.search(line)
            (notes if historical else drift).append(
                ("正文里的哈希 `%s…` 与任何被锁文件都对不上，但同一行写明了它是被取代的旧值——"
                 "当来路读，不当漂移" if historical else
                 "正文里的哈希 `%s…` 与任何被锁文件都对不上，且没说它是旧值——"
                 "照它核对的人会得到「对不上」然后不知道该信哪个") % h[:8])

    # 最重的一条：被签住的文件如果不在版本库，这个签名没人能核对
    to_check = [f["path"] for f in (lock or {}).get("files") or []]
    to_check += [p for p in extra_paths if p]
    seen = set()
    for p in to_check:
        rel = os.path.relpath(p, paths["repo"]) if os.path.isabs(p) else p
        if rel in seen:
            continue
        seen.add(rel)
        t = tracked_by_git(rel, paths["repo"])
        p = rel
        if t is False:
            drift.append("`%s` **不在版本库里**——别人 clone 下来打不开它。"
                         "被 G2 签住的文件不入库，等于那个签名没人能核对，冻结机制是悬空的" % p)
        elif t is None:
            drift.append("`%s` 是否入库查不了（git 跑不起来）——未检不是通过" % p)
    return drift, notes


# ---- 发帖：按 stage 打标记，同一 stage 改帖不新增 ----------------------------------------

def post(repo, number, slug, stage, body, cwd):
    """发帖，或改掉同一 slug 同一 stage 的那一条。

    标记比对交给 jq 在服务端做（marker 用 json.dumps 变成合法的 jq 字符串字面量），
    拿回来的就只是 id——正文里有换行、有引号、有表格，任何自己切分的方案都会在某一条评论上碎掉。"""
    marker = MARKER % (slug, stage)
    jq = ".[] | select(.body | contains(%s)) | .id" % json.dumps(marker)
    code, out, err = gh(["api", f"repos/{repo}/issues/{number}/comments", "--paginate", "--jq", jq], cwd)
    if code != 0:
        return None, f"列 issue 评论失败：{err.strip()[:200]}"
    ids = [l.strip() for l in out.splitlines() if l.strip()]
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
        fh.write(body)
        tmp = fh.name
    try:
        if ids:
            code, out, err = gh(["api", "-X", "PATCH", f"repos/{repo}/issues/comments/{ids[0]}",
                                 "-F", f"body=@{tmp}", "--jq", ".html_url"], cwd)
            verb = "改帖"
        else:
            code, out, err = gh(["issue", "comment", str(number), "--repo", repo, "--body-file", tmp], cwd)
            verb = "发帖"
    finally:
        os.unlink(tmp)
    if code != 0:
        return None, f"{verb}失败：{err.strip()[:200]}"
    last = out.strip().splitlines()[-1] if out.strip() else "(ok)"
    return f"{verb} → {last}", None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("number", help="issue 号")
    ap.add_argument("--root", default=".aidlc")
    ap.add_argument("--slug")
    ap.add_argument("--repo", help="owner/name；不给就让 gh 自己认当前仓库")
    ap.add_argument("--stage", help="默认取 state.json 的当前阶段")
    ap.add_argument("--out")
    ap.add_argument("--post", action="store_true",
                    help="真的发帖 / 改帖。发帖是对外副作用，默认只打印")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    root = os.path.abspath(a.root)
    slug = a.slug
    if not slug:
        subs = [d for d in sorted(os.listdir(root))
                if os.path.isfile(os.path.join(root, d, "state.json"))] if os.path.isdir(root) else []
        if len(subs) != 1:
            sys.stderr.write(f"sync_issue: {root} 下有 {len(subs)} 个 run，用 --slug 指定\n")
            return 2
        slug = subs[0]
    base = os.path.join(root, slug)
    st = load_json(os.path.join(base, "state.json"))
    if st is None:
        sys.stderr.write(f"sync_issue: 读不到 {base}/state.json\n")
        return 2
    stage = a.stage or st.get("stage") or "unknown"
    repo_root = os.path.dirname(root) or "."

    dw_path = ((st.get("contract") or {}).get("done_when")
               or os.path.join(base, "done_when.yaml"))
    cards_dir = (st.get("cards") or {}).get("dir")
    paths = {"state": os.path.join(base, "state.json"), "repo": repo_root,
             "cards_dir": os.path.join(repo_root, cards_dir) if cards_dir and not os.path.isabs(cards_dir) else cards_dir}
    artefacts = {
        "done_when": load_yaml(dw_path if os.path.isabs(dw_path) else os.path.join(repo_root, dw_path)),
        "lock": load_json(os.path.join(base, ".done_when.lock")),
        "notes": read_text(os.path.join(base, "notes.md")),
    }

    text = render(st, slug, stage, paths, artefacts)

    repo = a.repo
    if not repo:
        code, out, _ = gh(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"], repo_root)
        repo = out.strip() if code == 0 else None
    body = None
    if repo:
        code, out, _ = gh(["issue", "view", str(a.number), "--repo", repo, "--json", "body", "-q", ".body"], repo_root)
        body = out if code == 0 else None

    extra = [p for p in (dw_path, os.path.join(base, ".done_when.lock")) if p]
    if cards_dir:
        extra.append(cards_dir)
    drift, notes = reconcile(body, artefacts["done_when"], artefacts["lock"], paths, extra)

    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)

    posted, post_err = (None, None)
    if a.post:
        if not repo:
            post_err = "认不出仓库（给 --repo owner/name）"
        else:
            posted, post_err = post(repo, a.number, slug, stage, text, repo_root)

    if a.json:
        print(json.dumps({"slug": slug, "stage": stage, "issue": a.number, "repo": repo,
                          "drift": drift, "notes": notes, "posted": posted, "post_error": post_err,
                          "out": a.out, "verdict": "DRIFT" if drift else "IN_SYNC"},
                         ensure_ascii=False, indent=2))
    else:
        if not a.out and not a.post:
            print(text)
        print("sync_issue · %s · stage=%s · issue #%s · %s"
              % (slug, stage, a.number, "DRIFT" if drift else "IN_SYNC"), file=sys.stderr)
        for d in drift:
            print("  DRIFT  " + d, file=sys.stderr)
        for n in notes:
            print("  note   " + n, file=sys.stderr)
        if posted:
            print("  " + posted, file=sys.stderr)
        if post_err:
            print("  发帖没成：" + post_err, file=sys.stderr)
    if post_err:
        return 2
    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
