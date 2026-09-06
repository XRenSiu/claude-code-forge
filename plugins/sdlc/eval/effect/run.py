#!/usr/bin/env python3
"""run.py — 行为层对比的物化与收分（三个 arm 拿同一段需求，隐藏集事后跑）。

缺口：sdlc 的 28 个 skill 全部 static_only —— 脚本在 fixture 上冒烟过，但"**带 sdlc 的 agent 交付
是不是比不带的好**"一次都没测过。所有闸门阈值都是文献先验。一个声称抬高下限的插件，自己没有下限的
测量值。这是整个插件最大的不完备，也是本目录存在的唯一理由。

三个 arm（拿到的需求一字不差）：
  bare      裸 agent：fixture 里连 CLAUDE.md 都删掉
  claudemd  fixture 自带的 CLAUDE.md 留着（业界默认做法；2607.27250 说它对正确率没有可测量的影响）
  sdlc      同上，外加 sdlc 的纪律与脚本（判据先写、隐藏集不可见、白名单、结构闸）

用法：
  run.py prepare <task-id> --arm bare|claudemd|sdlc --workdir DIR
  run.py collect <task-id> --arm bare|claudemd|sdlc --workdir DIR [--json]

纪律（不可协商，否则这份数据一文不值）：
  - **隐藏集在 collect 时才进工作区**。prepare 出来的目录里没有 hidden/ 的任何字节；
    arm 看得到隐藏集 = 这次运行作废。
  - **三个 arm 的需求文本逐字相同**。arm 之间的差别只能是上下文与纪律，不能是题面。
  - **收分的是脚本**，不是评委的印象；LLM 只在 arm 里干活，不在评分里说话。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ARMS = ("bare", "claudemd", "sdlc")

SDLC_BRIEF = """
## 这一轮按 sdlc 的纪律做（arm=sdlc）

插件在 {plugin}。按这个顺序，每一步的产物留在仓库里：

1. `issue.md` —— 把需求写成可证伪的条目：形容词换成阈值（阈值要写来源）；每条正向验收配一条
   反向孪生（边界 / 失败输入时系统该怎么办）；验收只写观察边界，不写文件路径。
   写完跑 `python3 {plugin}/skills/issue/scripts/verify_issue.py issue.md`。
2. `done_when.yaml` —— schema 2 的契约（`acceptance` 以 AC 为单位，每条 mechanical 的要有
   observe / given / expect）。跑 `python3 {plugin}/skills/donewhen-extract/scripts/validate_done_when_v2.py done_when.yaml`。
   需求里没说清的地方**不许默认填**：写进 `ASSUMPTIONS.md`，一条一行，写明假设了什么、风险是什么。
3. 实现。契约里承诺的阈值要真的按阈值实现，不是写完就算。
4. `python3 -m pytest -q` 全绿。
"""


def task_dir(tid):
    return os.path.join(HERE, "tasks", tid)


def load_task(tid):
    import yaml
    with open(os.path.join(task_dir(tid), "task.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def sh(args, cwd=None, timeout=600):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def cmd_prepare(a):
    t = load_task(a.task)
    dst = os.path.join(a.workdir, f"{a.task}-{a.arm}")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(os.path.join(task_dir(a.task), t.get("fixture", "fixture")), dst)
    if a.arm == "bare":
        for f in ("CLAUDE.md", "AGENTS.md"):
            p = os.path.join(dst, f)
            if os.path.isfile(p):
                os.remove(p)
    # 隐藏集绝不进工作区 —— 断言一次，别靠记得
    for root, _, files in os.walk(dst):
        for f in files:
            assert "hidden" not in os.path.relpath(os.path.join(root, f), dst), "hidden leaked into the arm"
    prompt = t["prompt"].rstrip() + "\n"
    if a.arm == "sdlc":
        prompt += SDLC_BRIEF.format(plugin=os.path.abspath(os.path.join(HERE, "..", "..")))
    open(os.path.join(dst, "PROMPT.md"), "w", encoding="utf-8").write(prompt)
    sh(["git", "init", "-q", "."], cwd=dst)
    sh(["git", "add", "-A"], cwd=dst)
    sh(["git", "-c", "user.email=eval@local", "-c", "user.name=eval", "commit", "-qm", "fixture"], cwd=dst)
    print(json.dumps({"ok": True, "dir": dst, "arm": a.arm, "task": a.task,
                      "prompt_file": os.path.join(dst, "PROMPT.md"),
                      "note": "把 PROMPT.md 交给这个 arm；隐藏集不在这个目录里"}, ensure_ascii=False, indent=2))


def cmd_collect(a):
    t = load_task(a.task)
    arm_dir = os.path.join(a.workdir, f"{a.task}-{a.arm}")
    if not os.path.isdir(arm_dir):
        sys.stderr.write(f"没有这个 arm 的工作区：{arm_dir}（先 prepare 再让 arm 干活）\n"); return 2
    # 收分在**副本**里做，绝不碰 arm 的工作区。
    # 2026-09-06 run 1 的教训：collect 早跑了一步，隐藏集落进还在干活的 arm 目录，
    # 那个 arm 的最后一次 pytest 把 5 个隐藏测试也跑了（它自陈没读内容，但那已经是污染）。
    # 铁律「隐藏集在 collect 时才进工作区」当时只写在文档里，没有编译——现在编译了。
    d = os.path.join(a.workdir, f".score-{a.task}-{a.arm}")
    if os.path.exists(d):
        shutil.rmtree(d)
    # tests_hidden / result.json 若出现在 arm 目录里，本身就是污染证据：记下来，但不带进评分副本。
    # 污染与否由 mtime 机械判定，不由记忆判定：泄漏发生在 arm 全部产物之后 = 它没机会读到隐藏集。
    leaked = [p for p in os.listdir(arm_dir) if p in ("tests_hidden", "result.json")]
    leak_after_work = None
    if leaked:
        leak_t = min(os.path.getmtime(os.path.join(arm_dir, p)) for p in leaked)
        newest = 0.0
        for root, dirs, files in os.walk(arm_dir):
            dirs[:] = [x for x in dirs if x not in ("tests_hidden", "__pycache__", ".pytest_cache", ".git")]
            for f in files:
                if f in ("result.json",):
                    continue
                newest = max(newest, os.path.getmtime(os.path.join(root, f)))
        leak_after_work = newest <= leak_t
        leaked = [] if leak_after_work else leaked
    shutil.copytree(arm_dir, d, ignore=shutil.ignore_patterns(
        "__pycache__", ".pytest_cache", "tests_hidden", "result.json"))
    hidden_src = os.path.join(task_dir(a.task), t.get("hidden_dir", "hidden"))
    hidden_dst = os.path.join(d, "tests_hidden")
    shutil.copytree(hidden_src, hidden_dst)
    open(os.path.join(hidden_dst, "__init__.py"), "a").close()
    if leaked:
        sys.stderr.write(f"污染：{leaked} 出现在 arm 的工作区里——这一轮的分数不算数\n")

    checks, got, total = [], 0, 0
    for c in t.get("checks", []):
        w = int(c.get("weight", 1)); total += w
        t0 = time.time()
        try:
            r = sh(["python3", "-m", "pytest", "-q", os.path.join("tests_hidden", c["file"])], cwd=d, timeout=300)
            passed, tail = r.returncode == 0, (r.stdout or "").strip().splitlines()[-1:]
        except subprocess.TimeoutExpired:
            passed, tail = False, ["timeout"]
        got += w if passed else 0
        checks.append({"id": c["id"], "weight": w, "passed": passed, "seconds": round(time.time() - t0, 1),
                       "measures": c.get("measures", ""), "tail": "; ".join(tail)[:160]})

    # 欠定槽只在 **arm 新增的内容** 里找证据。曾经在整份文件里找 —— fixture 自带的 CLAUDE.md
    # 与源码注释就能命中，一个没干活的 arm 也拿满分（2026-09-06 预检抓到：T05 未干活 2/2）。
    # 「写下来了」指的是这次写下来的，不是仓库本来就有的。
    added = {}
    for f in {x for sl in t.get("underspecified_slots", []) for x in sl.get("evidence_in", [])}:
        fp = os.path.join(d, f)
        if not os.path.isfile(fp):
            continue
        tracked = sh(["git", "ls-files", "--error-unmatch", f], cwd=d).returncode == 0
        if tracked:
            out = sh(["git", "diff", "-U0", "HEAD", "--", f], cwd=d).stdout
            added[f] = "\n".join(l[1:] for l in out.splitlines()
                                  if l.startswith("+") and not l.startswith("+++"))
        else:
            added[f] = open(fp, encoding="utf-8", errors="replace").read()
    slots = []
    for sl in t.get("underspecified_slots", []):
        hit, where = False, None
        for f in sl.get("evidence_in", []):
            if re.search(sl["pattern"], added.get(f, "")):
                hit, where = True, f
                break
        slots.append({"id": sl["id"], "question": sl["question"], "addressed": hit, "found_in": where})

    r = sh(["git", "diff", "--stat", "HEAD"], cwd=d)
    res = {"task": a.task, "arm": a.arm, "dir": arm_dir, "scored_in": d,
           "contaminated": bool(leaked), "leak_after_work": leak_after_work,
           "checks": checks, "check_score": got, "check_total": total,
           "check_ratio": round(got / total, 3) if total else None,
           "slots": slots, "slots_addressed": sum(1 for s in slots if s["addressed"]), "slots_total": len(slots),
           "diffstat": (r.stdout or "").strip().splitlines()[-1:] or ["(no diff)"],
           "collected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    open(os.path.join(d, "result.json"), "w", encoding="utf-8").write(json.dumps(res, ensure_ascii=False, indent=2))
    if leaked:
        print(f"⚠ 污染：{leaked} 在 arm 的工作区里，这一轮 {a.task}/{a.arm} 的分数不算数")
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(f"{a.task}/{a.arm} · 隐藏集 {got}/{total} · 欠定槽处理 {res['slots_addressed']}/{res['slots_total']}")
        for c in checks:
            print(f"  {'ok  ' if c['passed'] else 'FAIL'}  {c['id']} (w{c['weight']}) {c['measures'][:60]}")
        for s in slots:
            print(f"  {'ok  ' if s['addressed'] else 'miss'}  {s['id']} {s['question'][:40]} → {s['found_in'] or '哪里都没写'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("prepare", "collect"):
        s = sub.add_parser(name)
        s.add_argument("task"); s.add_argument("--arm", required=True, choices=ARMS)
        s.add_argument("--workdir", required=True); s.add_argument("--json", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.workdir, exist_ok=True)
    return cmd_prepare(a) or 0 if a.cmd == "prepare" else cmd_collect(a)


if __name__ == "__main__":
    sys.exit(main())
