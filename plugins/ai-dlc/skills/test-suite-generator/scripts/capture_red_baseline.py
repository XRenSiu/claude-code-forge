#!/usr/bin/env python3
"""
capture_red_baseline.py — the RED-baseline primitive for test-suite-generator (L5).

Why a primitive (I-62). The RED baseline is the evidence that a test suite fails
before the implementation exists. Captured in the working tree, it measures the
working tree — including files no commit contains. In the ring-audit run a parallel
implementer's untracked `check_audit.py` was sitting in the tree while the baseline
ran, so the recorded baseline said `19 ok / 15 FAIL` where the instrument-absent
truth was `34 FAIL`. Nothing in the artefact said which tree it had measured, so the
number looked like a fact.

This script makes the clean checkout mechanical instead of remembered:

  1. `git worktree add --detach <tmp> HEAD` — a checkout of HEAD with no working-tree
     spill (untracked files included: a linked worktree starts empty of them).
  2. `git status --porcelain` inside that checkout must be EMPTY, and the emptiness
     is written into the baseline header as evidence.
  3. The runner executes with cwd = the clean checkout, never the working tree.
  4. The outer working tree's dirt is recorded too — as what was EXCLUDED, so a
     reader can see the untracked instrument that did not get to vote.

`--verify` re-reads a recorded baseline and fails if that evidence is absent, so
"the baseline is honest" is a check, not a promise.

Usage:
    python capture_red_baseline.py <runner-path-relative-to-repo-root> \\
        [--repo DIR] [--out RED_BASELINE.txt] [--version X.Y.Z] [--based-on "REQ-001..011"] [--note TEXT]
    python capture_red_baseline.py --verify <RED_BASELINE.txt>

Exit codes: 0 ok (the runner's own exit is recorded, not propagated) ·
            1 the checkout was not clean / --verify found no evidence · 2 bad input
"""

import sys
import os
import re
import shutil
import argparse
import datetime
import subprocess
import tempfile

CLEAN_MARK = "git status --porcelain (clean checkout):"
CLEAN_EMPTY = "<empty>"
WORKTREE_MARK = "clean_checkout:"


def git(args, cwd, check=True):
    p = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    if check and p.returncode != 0:
        sys.stderr.write(f"capture_red_baseline.py: git {' '.join(args)} failed:\n{p.stderr}")
        sys.exit(2)
    return p.stdout.strip()


def verify(path):
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as e:
        sys.stderr.write(f"capture_red_baseline.py: {e}\n")
        sys.exit(2)
    problems = []
    if WORKTREE_MARK not in text:
        problems.append(f"no `{WORKTREE_MARK}` line — nothing says the baseline ran in a checkout of HEAD")
    m = re.search(re.escape(CLEAN_MARK) + r"[ \t]*(.*)", text)
    if not m:
        problems.append(f"no `{CLEAN_MARK}` evidence line")
    elif m.group(1).strip() != CLEAN_EMPTY:
        problems.append(f"`{CLEAN_MARK}` is not {CLEAN_EMPTY} — the tree it measured was dirty: "
                        f"{m.group(1).strip()[:80]}")
    if not re.search(r"^git HEAD:\s*[0-9a-f]{7,40}\s*$", text, re.M):
        problems.append("no `git HEAD: <sha>` line")
    if problems:
        sys.stderr.write(f"capture_red_baseline.py --verify {path}: baseline carries no clean-checkout evidence\n")
        for p in problems:
            sys.stderr.write(f"  ✗ {p}\n")
        sys.stderr.write("  Re-capture with capture_red_baseline.py; a baseline taken in the working tree "
                         "measures files no commit contains (I-62).\n")
        sys.exit(1)
    print(f"✓ {path}: captured in a clean checkout of HEAD ({CLEAN_MARK} {CLEAN_EMPTY})")


def main():
    ap = argparse.ArgumentParser(description="Capture a RED baseline in a clean checkout of HEAD.")
    ap.add_argument("runner", nargs="?", help="runner path, relative to the repo root")
    ap.add_argument("--repo", default=".", help="any path inside the git repo (default: cwd)")
    ap.add_argument("--out", help="write the baseline here (default: stdout)")
    ap.add_argument("--version", default="<skill-version>",
                    help="value of SKILL.md frontmatter version: (do NOT hardcode a literal)")
    ap.add_argument("--based-on", default="", help="REQ ids this suite covers, for the header")
    ap.add_argument("--note", default="", help="one extra header line (e.g. why this revision)")
    ap.add_argument("--verify", metavar="RED_BASELINE.txt",
                    help="check a recorded baseline carries the clean-checkout evidence")
    args = ap.parse_args()

    if args.verify:
        verify(args.verify)
        return
    if not args.runner:
        ap.error("runner is required unless --verify is given")

    repo = git(["rev-parse", "--show-toplevel"], cwd=args.repo)
    head = git(["rev-parse", "HEAD"], cwd=repo)
    dirty = git(["status", "--porcelain"], cwd=repo, check=False)
    dirty_lines = [ln for ln in dirty.splitlines() if ln.strip()]

    tmp = tempfile.mkdtemp(prefix="red-baseline-")
    work = os.path.join(tmp, "checkout")
    try:
        git(["worktree", "add", "--detach", "--quiet", work, head], cwd=repo)
        # The clean checkout is the ONLY tree the runner may see (I-62). A baseline taken
        # in the working tree measures untracked files that belong to nobody's commit.
        run_dir = work
        porcelain = git(["status", "--porcelain"], cwd=work, check=False)
        if porcelain.strip():
            sys.stderr.write("capture_red_baseline.py: the fresh checkout is not clean — refusing to "
                             f"record a baseline over it:\n{porcelain}\n")
            sys.exit(1)
        runner = os.path.join(run_dir, args.runner)
        if not os.path.isfile(runner):
            sys.stderr.write(f"capture_red_baseline.py: runner not found in the checkout of HEAD: "
                             f"{args.runner}\n(it is untracked, or the path is not repo-relative)\n")
            sys.exit(2)
        proc = subprocess.run(["bash", runner], cwd=run_dir, capture_output=True, text=True)
        output = (proc.stdout or "") + (proc.stderr or "")
        rc = proc.returncode
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", work],
                       cwd=repo, capture_output=True, text=True)
        shutil.rmtree(tmp, ignore_errors=True)
        subprocess.run(["git", "worktree", "prune"], cwd=repo, capture_output=True, text=True)

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    excluded = (f"{len(dirty_lines)} working-tree entries excluded "
                f"({', '.join(ln.strip()[:40] for ln in dirty_lines[:5])}"
                f"{', …' if len(dirty_lines) > 5 else ''})") if dirty_lines else "working tree was clean too"
    head_lines = [
        f"# Generated by test-suite-generator/{args.version} · scripts/capture_red_baseline.py",
        f"# based_on: {args.based_on}" if args.based_on else None,
        f"# {args.note}" if args.note else None,
        f"{WORKTREE_MARK} git worktree add --detach <tmp> {head[:7]}   "
        f"(the runner never saw the working tree)",
        f"{CLEAN_MARK} {CLEAN_EMPTY}",
        f"working tree at capture: {excluded}",
        f"git HEAD: {head}",
        f"date: {now}",
        f"command: bash {args.runner}",
        f"runner exit: {rc}",
        "",
        "## output",
        output.rstrip("\n"),
        "",
    ]
    text = "\n".join(ln for ln in head_lines if ln is not None) + "\n"

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"✓ RED baseline written to {args.out} (runner exit {rc}, clean checkout of {head[:7]})")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
