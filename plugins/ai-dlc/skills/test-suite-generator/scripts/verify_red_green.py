#!/usr/bin/env python3
"""verify_red_green.py — 红→绿证据的机械闸（L5 的另一半；capture_red_baseline.py 是前一半）。

缺口：`capture_red_baseline.py` 把「实现前哪些测试是红的」记进 RED_BASELINE.txt，带干净检出的证据。
但「实现后那些红的都绿了、而且一个都没少」一直靠人看（ARCHITECTURE §15「红-绿证据脚本」空白）。
少了这一半，红基线只是一张照片：实现者删掉一条红测试，或改写它，绿就来了——正是「绝不用改测试
的方式让测试过」要拦的那条路。这个脚本把它编译成三条判据：

  1. 基线诚实：RED_BASELINE.txt 必须带 capture_red_baseline.py 写进去的干净检出证据（同 --verify）
  2. 基线可继承：基线记的 `git HEAD` 必须是当前 HEAD 的祖先——不是祖先，说明测试是在另一条历史上量的
  3. 红→绿且无失踪：基线里每一条红的测试，现在都必须出现且通过；**消失的红测试算不绿**，
     因为删测试是最便宜的变绿方式

认得的测试行（两族，各自独立）：
  unittest -v：`test_x (mod.Class.test_x) ... ok|FAIL|ERROR|skipped …`
  pytest -v / -rA：`path::test_x PASSED|FAILED|ERROR|SKIPPED …` 与 `PASSED|FAILED|ERROR path::test_x`
  TAP 式：`ok <id>` / `not ok <id>` / `PASS <id>` / `FAIL <id>`
其它格式一律 unevaluated（不猜）。

用法：
  verify_red_green.py <RED_BASELINE.txt> --runner <runner-path-relative-to-repo-root>
                      [--repo DIR] [--out red-green-evidence.yaml] [--json]

退出码：
  0 = green：基线里每条红测试现在都通过，无失踪；基线 HEAD 是当前 HEAD 的祖先
  1 = not green：有红测试仍红 / 出错，或有红测试失踪（被删或改名）
  2 = 用法 / IO 错误
  3 = unevaluated：基线没有干净检出证据、基线 HEAD 不是祖先、或运行器输出里没有一条能认的测试行——
      **不是通过**（不变量 14）
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import subprocess
import sys

try:
    import yaml
except ImportError:
    yaml = None

CLEAN_MARK = "git status --porcelain (clean checkout):"
CLEAN_EMPTY = "<empty>"
WORKTREE_MARK = "clean_checkout:"

UNITTEST_RE = re.compile(r"^(?P<id>[A-Za-z_][\w]*)\s+\((?P<full>[\w.]+)\)\s+\.\.\.\s+(?P<res>ok|FAIL|ERROR|skipped|expected failure|unexpected success)\b", re.M)
PYTEST_V_RE = re.compile(r"^(?P<id>\S+::\S+)\s+(?P<res>PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\b", re.M)
PYTEST_RA_RE = re.compile(r"^(?P<res>PASSED|FAILED|ERROR)\s+(?P<id>\S+::\S+)", re.M)
TAP_RE = re.compile(r"^(?P<res>not ok|ok|PASS|FAIL)\s*[:\-]?\s+(?P<id>[\w./:\[\]-]+)", re.M)

RED = {"FAIL", "ERROR", "FAILED", "not ok"}
GREEN = {"ok", "PASSED", "PASS"}


def die(msg, code=2):
    sys.stderr.write(f"verify_red_green: {msg}\n")
    return code


def parse_results(text):
    """→ {test_id: 'red'|'green'|'other'}；认得两族写法，认不出的行不算。"""
    out = {}
    for rx in (UNITTEST_RE, PYTEST_V_RE, PYTEST_RA_RE, TAP_RE):
        for m in rx.finditer(text):
            tid = m.group("full") if "full" in m.groupdict() and m.groupdict().get("full") else m.group("id")
            res = m.group("res")
            out[tid] = "red" if res in RED else ("green" if res in GREEN else "other")
    return out


def baseline_evidence(text):
    problems = []
    if WORKTREE_MARK not in text:
        problems.append(f"no `{WORKTREE_MARK}` line — nothing says the baseline ran in a checkout of HEAD")
    m = re.search(re.escape(CLEAN_MARK) + r"[ \t]*(.*)", text)
    if not m:
        problems.append(f"no `{CLEAN_MARK}` evidence line")
    elif m.group(1).strip() != CLEAN_EMPTY:
        problems.append(f"`{CLEAN_MARK}` is not {CLEAN_EMPTY} — the tree it measured was dirty")
    h = re.search(r"^git HEAD:\s*([0-9a-f]{7,40})\s*$", text, re.M)
    if not h:
        problems.append("no `git HEAD: <sha>` line")
    return problems, (h.group(1) if h else None)


def git(args, cwd):
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("baseline", help="RED_BASELINE.txt written by capture_red_baseline.py")
    ap.add_argument("--runner", required=True, help="runner path, relative to the repo root (bash <runner>)")
    ap.add_argument("--repo", default=".", help="any path inside the git repo (default: cwd)")
    ap.add_argument("--out", default="red-green-evidence.yaml")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if not os.path.isfile(a.baseline):
        return die(f"not a file: {a.baseline}")
    with open(a.baseline, encoding="utf-8") as f:
        btext = f.read()
    problems, base_head = baseline_evidence(btext)
    report = {"verdict": None, "baseline": a.baseline, "baseline_head": base_head, "runner": a.runner,
              "baseline_evidence_problems": problems, "computed_at": _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()}

    def finish(verdict, **extra):
        report["verdict"] = verdict
        report.update(extra)
        text = json.dumps(report, ensure_ascii=False, indent=2) if (a.out.endswith(".json") or yaml is None) \
            else yaml.safe_dump(report, allow_unicode=True, sort_keys=False)
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text if text.endswith("\n") else text + "\n")
        if a.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"verify_red_green: {verdict} · red_in_baseline={report.get('red_in_baseline')} "
                  f"still_red={report.get('still_red')} missing={report.get('missing')} → {a.out}")
        return {"green": 0, "not_green": 1, "unevaluated": 3}[verdict]

    if problems:
        return finish("unevaluated", why="the baseline carries no clean-checkout evidence (re-capture with capture_red_baseline.py)")

    r = git(["rev-parse", "--show-toplevel"], a.repo)
    if r.returncode != 0:
        return die(f"not inside a git repo: {a.repo}")
    repo = r.stdout.strip()
    head = git(["rev-parse", "HEAD"], repo).stdout.strip()
    anc = git(["merge-base", "--is-ancestor", base_head, head], repo)
    report["head"] = head
    report["baseline_head_is_ancestor"] = anc.returncode == 0
    if anc.returncode != 0:
        return finish("unevaluated", why=f"baseline HEAD {base_head[:7]} is not an ancestor of HEAD {head[:7]} — "
                                          "the red tests were measured on another history; re-capture the baseline")

    base_results = parse_results(btext)
    red = sorted(t for t, s in base_results.items() if s == "red")
    report["baseline_tests_recognised"] = len(base_results)
    report["red_in_baseline"] = len(red)
    if not base_results:
        return finish("unevaluated", why="no recognisable test result line in the baseline (unittest -v / pytest -v / -rA / TAP)")

    runner = os.path.join(repo, a.runner)
    if not os.path.isfile(runner):
        return die(f"runner not found: {runner}")
    proc = subprocess.run(["bash", runner], cwd=repo, capture_output=True, text=True)
    now_results = parse_results((proc.stdout or "") + (proc.stderr or ""))
    report["runner_exit"] = proc.returncode
    report["now_tests_recognised"] = len(now_results)
    if not now_results:
        return finish("unevaluated", why="the runner's output has no recognisable test result line — cannot tell red from green")

    still_red = sorted(t for t in red if now_results.get(t) == "red")
    missing = sorted(t for t in red if t not in now_results)
    other = sorted(t for t in red if now_results.get(t) == "other")
    green_now = sorted(t for t in red if now_results.get(t) == "green")
    report.update(still_red=still_red, missing=missing, skipped_now=other, turned_green=green_now)
    if still_red or missing or other:
        why = []
        if still_red:
            why.append(f"{len(still_red)} red test(s) still red")
        if missing:
            why.append(f"{len(missing)} red test(s) vanished — a deleted or renamed test is the cheapest way to green, and it is not green")
        if other:
            why.append(f"{len(other)} red test(s) now skipped / xfail — not green")
        return finish("not_green", why="; ".join(why))
    return finish("green", why=f"all {len(red)} red test(s) in the baseline now pass; none missing; baseline HEAD is an ancestor")


if __name__ == "__main__":
    sys.exit(main())
