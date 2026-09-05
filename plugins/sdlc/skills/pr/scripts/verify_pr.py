#!/usr/bin/env python3
"""
verify_pr.py — the mechanical pre-gate for /pr: the PRODUCT (PR body + title + branch diff) must
exhibit the section order, carry a linked issue, verification evidence, AC→evidence mapping, and be
within size limits. Pre-flight facts about the branch are checked from git, not from the model's claim.

Usage:
  verify_pr.py --body BODY.md [--title T] [--base main] [--head HEAD] [--done-when F] [--lock L]
               [--proposal-glob 'change-proposal-*.md'] [--allow-xl] [--skip-preflight]

Exit 0 = pass (flags may remain) · 1 = REJECT · 2 = git/IO error. Output JSON includes size_class.

Mechanical guarantees (REJECT — non-waivable half):
  - body sections: Summary / Scope(do,dont) / Linked issue(Closes|Fixes|Resolves|Refs #N) / Changes /
    Verification(≥1 command line in a fenced block or a test-evidence line) / Acceptance mapping /
    Risk & rollback / Reviewer focus
  - --done-when: every `kind: mechanical` AC id appears in the Acceptance mapping table
  - size_class XL (≥1000 changed lines, lockfiles/generated excluded) → reject unless --allow-xl
  - --title: Conventional Commits shape, ≤72
  - --lock: locked files in base..head diff without a change proposal in the diff → reject
  - preflight (unless --skip-preflight): head branch ≠ base; working tree clean; every commit in
    base..head has a Conventional Commits subject; not behind origin/<base> (flag if cannot fetch)
Flags: L size; untested; TODO/FIXME in body; Reviewer focus without file refs; draft recommended.
"""
import argparse
import fnmatch
import json
import re
import subprocess
import sys

SUBJECT_RE = re.compile(r"^(feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert|wip)(\([a-z0-9\-./*]+\))?!?: \S")
LINK_RE = re.compile(r"\b(Closes|Fixes|Resolves|Refs)\s+#\d+\b", re.I)
GENERATED = ["package-lock.json", "pnpm-lock.yaml", "yarn.lock", "Cargo.lock", "poetry.lock", "go.sum",
             "*.snap", "*.min.js", "*.min.css", "*.generated.*", "dist/*", "build/*"]


def git(*args, check=True):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.stderr.write(f"verify_pr: git {' '.join(args)} failed: {r.stderr.strip()}\n"); sys.exit(2)
    return r.stdout


def sections(md):
    out, cur, buf = {}, None, []
    for line in md.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if cur is not None:
                out[cur] = "\n".join(buf)
            cur, buf = m.group(1).strip().lower(), []
        else:
            buf.append(line)
    if cur is not None:
        out[cur] = "\n".join(buf)
    return out


def size_class(n):
    return "XS" if n < 50 else "S" if n < 200 else "M" if n < 500 else "L" if n < 1000 else "XL"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--body", required=True); ap.add_argument("--title"); ap.add_argument("--base", default="main")
    ap.add_argument("--head", default="HEAD"); ap.add_argument("--done-when"); ap.add_argument("--lock")
    ap.add_argument("--proposal-glob", default="change-proposal-*.md"); ap.add_argument("--allow-xl", action="store_true")
    ap.add_argument("--skip-preflight", action="store_true")
    a = ap.parse_args()
    rejects, flags = [], []
    md = open(a.body, encoding="utf-8").read()
    secs = sections(md)

    for s in ["summary", "scope", "linked issue", "changes", "verification", "acceptance mapping", "risk & rollback", "reviewer focus"]:
        if s not in secs:
            rejects.append(f"section missing: ## {s.title()}")
    if "scope" in secs:
        for k in ("do", "dont"):
            m = re.search(rf"^\s*[-*]\s*{k}\s*:\s*(.+)$", secs["scope"], re.M)
            if not m or m.group(1).strip().startswith("<"):
                rejects.append(f"Scope.{k} empty — the scope declaration is the baseline for out-of-scope judgments")
    if "linked issue" in secs and not LINK_RE.search(secs["linked issue"]):
        rejects.append("Linked issue: needs `Closes #N` / `Refs #N`")
    if "verification" in secs:
        v = secs["verification"]
        has_cmd = bool(re.search(r"```[a-z]*\n\s*\S", v)) or bool(re.search(r"^\s*[-*]\s*\S.*(pass|✅|ok|green|failed on)", v, re.I | re.M))
        if not has_cmd:
            rejects.append("Verification: no command / test evidence line")
        if "untested" in v.lower():
            flags.append("untested — reviewer should run it; draft recommended")
    if "reviewer focus" in secs and not re.search(r"[\w/.-]+\.(ts|tsx|js|py|go|rs|java|kt|rb|vue|md|yaml|yml|json)(:\d+)?", secs["reviewer focus"]):
        flags.append("Reviewer focus names no file — point at file:line")
    if re.search(r"\b(TODO|FIXME|XXX)\b", md):
        flags.append("TODO/FIXME in body — resolve or move to an issue")
    if a.title:
        if not SUBJECT_RE.match(a.title):
            rejects.append(f"title not Conventional Commits: {a.title!r}")
        if len(a.title) > 72:
            rejects.append("title > 72 chars")

    # acceptance mapping vs done_when
    if a.done_when:
        try:
            import yaml
            dw = yaml.safe_load(open(a.done_when, encoding="utf-8")) or {}
        except Exception as e:
            sys.stderr.write(f"verify_pr: cannot read done_when: {e}\n"); sys.exit(2)
        table = secs.get("acceptance mapping", "")
        for ac in dw.get("acceptance") or []:
            if isinstance(ac, dict) and ac.get("kind") == "mechanical" and ac.get("id") not in table:
                rejects.append(f"Acceptance mapping: {ac.get('id')} (mechanical) has no evidence row")
        for ac in dw.get("acceptance") or []:
            if isinstance(ac, dict) and ac.get("kind") == "human" and ac.get("id") not in table:
                flags.append(f"Acceptance mapping: {ac.get('id')} (human) missing — mark judge/evidence for G3")
    elif "acceptance mapping" in secs and not re.search(r"^\|\s*AC-", secs["acceptance mapping"], re.M):
        flags.append("Acceptance mapping has no AC rows (fine only when no contract exists)")

    # diff size + lock
    rng = f"{a.base}...{a.head}"
    numstat = git("diff", "--numstat", rng, check=False)
    changed, files = 0, []
    for line in numstat.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        add, dele, path = parts
        files.append(path)
        if any(fnmatch.fnmatch(path, g) or fnmatch.fnmatch(path.split("/")[-1], g) for g in GENERATED):
            continue
        changed += (int(add) if add.isdigit() else 0) + (int(dele) if dele.isdigit() else 0)
    sc = size_class(changed)
    if sc == "XL" and not a.allow_xl:
        rejects.append(f"size XL ({changed} lines) — must split (see references/size-and-split.md) or --allow-xl with justification")
    elif sc == "L":
        flags.append(f"size L ({changed} lines) — consider splitting; draft recommended")
    if a.lock:
        try:
            lock = json.load(open(a.lock, encoding="utf-8"))
            locked = {e["path"] for e in lock.get("files", [])}
            touched = [f for f in files if f in locked or any(f.startswith(l.rstrip('/') + '/') for l in locked)]
            proposals = [f for f in files if fnmatch.fnmatch(f.split("/")[-1], a.proposal_glob)]
            if touched and not proposals:
                rejects.append(f"locked file(s) changed in {rng} without a change proposal: {touched}")
            elif touched:
                flags.append(f"locked file(s) changed with proposal {proposals} — note in body")
        except Exception as e:
            sys.stderr.write(f"verify_pr: cannot read lock: {e}\n"); sys.exit(2)

    # preflight
    if not a.skip_preflight:
        branch = git("rev-parse", "--abbrev-ref", a.head, check=False).strip()
        if branch == a.base:
            rejects.append(f"head branch is the base branch `{a.base}`")
        if git("status", "--porcelain", check=False).strip():
            rejects.append("working tree not clean — commit or stash first")
        subs = [l for l in git("log", "--format=%s", rng, check=False).splitlines() if l]
        bad = [s for s in subs if not SUBJECT_RE.match(s)]
        if not subs:
            rejects.append(f"no commits in {rng}")
        if bad:
            rejects.append(f"non-conventional commit subjects in range: {bad[:3]}")
        r = subprocess.run(["git", "rev-list", "--count", f"{a.head}..origin/{a.base}"], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip().isdigit() and int(r.stdout.strip()) > 0:
            rejects.append(f"behind origin/{a.base} by {r.stdout.strip()} commit(s) — merge origin/{a.base} first (no rebase)")
        elif r.returncode != 0:
            flags.append(f"could not compare with origin/{a.base} (no remote?) — sync check skipped")

    out = {"verdict": "REJECT" if rejects else "PASS", "size_class": sc, "changed_lines": changed, "files": len(files),
           "draft_recommended": bool(flags) or sc in ("L",), "rejects": rejects, "flags": flags}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(1 if rejects else 0)


if __name__ == "__main__":
    main()
