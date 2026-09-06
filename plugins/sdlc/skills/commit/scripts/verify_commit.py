#!/usr/bin/env python3
"""
verify_commit.py — the mechanical pre-gate for /commit: checks the PRODUCT (staged set + message)
before the commit lands. It is the whitelist executor (L6), the G2 lock check (A-tier), and the
secret/debug scan — things the engine can reason about but does not reliably execute (A′-1).

Usage:
  verify_commit.py [--msg-file FILE | --msg TEXT] [--card CARD.yaml] [--lock .done_when.lock]
                   [--issue N] [--allow-main] [--proposal-glob 'change-proposal-*.md']
                   [--max-added 800] [--range A..B]

Reads the staged diff by default (`git diff --cached`); with --range, the diff of that commit range
(useful in CI / pre-push). Exit 0 = pass (flags may remain) · 1 = REJECT · 2 = git/IO error.

Mechanical guarantees (REJECT — non-waivable half):
  - not on main/master/develop (unless --allow-main)
  - message: Conventional Commits `type(scope)?!?: subject`, subject ≤72, no trailing period, known type
    (`wip` allowed only off main); `!`/BREAKING CHANGE requires a body
  - staged set non-empty; forbidden artifacts not staged (.env, *.pem, id_rsa*, node_modules/, dist/…)
  - secret-looking strings in ADDED lines; debugger/pdb/binding.pry in ADDED lines
  - --card: every staged path matches allowed_files and none matches forbidden_files (whitelist overflow)
  - --lock: locked files changed/staged → REJECT unless a change-proposal-*.md is staged in the same diff
Flags (needs_semantic_review): console.log/print in added lines; > --max-added added lines; files across
>3 top-level dirs with no scope; body lines >100; missing Refs/Closes when --issue given; body absent
on non-trivial diffs.
"""
import argparse
import fnmatch
import hashlib
import json
import re
import subprocess
import sys

TYPES = {"feat", "fix", "docs", "style", "refactor", "perf", "test", "chore", "ci", "build", "revert", "wip"}
SUBJECT_RE = re.compile(r"^(?P<type>[a-z]+)(\((?P<scope>[a-z0-9\-./*]+)\))?(?P<bang>!)?: (?P<subject>\S.*)$")
SECRET_RE = re.compile(r"(AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{36}|sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}"
                       r"|-----BEGIN [A-Z ]*PRIVATE KEY-----|(api[_-]?key|secret|token|passw(or)?d)\s*[:=]\s*['\"][A-Za-z0-9/+_\-]{16,}['\"])", re.I)
DEBUG_REJECT_RE = re.compile(r"(^\s*debugger;?\s*$|pdb\.set_trace\(\)|breakpoint\(\)|binding\.pry|byebug\b)")
DEBUG_FLAG_RE = re.compile(r"(console\.(log|debug)\(|^\s*print\(|dd\(|var_dump\()")
FORBIDDEN_ARTIFACTS = [".env", ".env.*", "*.pem", "id_rsa*", "*.key", "node_modules/*", "dist/*", "build/*",
                       "__pycache__/*", ".DS_Store", "*.pyc"]
FORBIDDEN_EXCEPT = [".env.example", ".env.sample"]


def git(*args, check=True):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.stderr.write(f"verify_commit: git {' '.join(args)} failed: {r.stderr.strip()}\n"); sys.exit(2)
    return r.stdout


def matches_any(path, patterns):
    base = path.split("/")[-1]
    for p in patterns:
        if p.endswith("/*"):
            if path.startswith(p[:-2] + "/") or ("/" + p[:-2] + "/") in ("/" + path):
                return p
        elif "/" in p:
            if fnmatch.fnmatch(path, p) or fnmatch.fnmatch(path, p.replace("**/", "")):
                return p
        else:
            if fnmatch.fnmatch(base, p):
                return p
    return None


def glob_match(path, pat):
    if pat.endswith("/**"):
        base = pat[:-3]
        if base.startswith("**/"):          # "**/tests/**": any directory named tests at any depth
            seg = base[3:]
            return ("/" + path).find("/" + seg + "/") >= 0
        return path == base or path.startswith(base + "/")
    if "**" in pat:
        return fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(path, pat.replace("**/", "")) or fnmatch.fnmatch(path, pat.replace("**", "*"))
    if "/" not in pat:
        # a bare name (done_when.yaml, .done_when.lock) means "that file wherever it lives" — the contract validator
        # demands the bare form, so without this fallback a nested contract's forbidden set matched nothing (dogfood 2026-09-05, I-38)
        return fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(path.rsplit("/", 1)[-1], pat)
    return fnmatch.fnmatch(path, pat)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--msg-file"); ap.add_argument("--msg"); ap.add_argument("--card"); ap.add_argument("--lock")
    ap.add_argument("--issue", type=int); ap.add_argument("--allow-main", action="store_true")
    ap.add_argument("--proposal-glob", default="change-proposal-*.md"); ap.add_argument("--max-added", type=int, default=800)
    ap.add_argument("--range")
    a = ap.parse_args()
    # --range must name two endpoints: `git diff <one-ref>` is legal but means "worktree vs ref", and the
    # landing-content hash below would then read the WRONG side, letting a tampered locked file hash equal to
    # its own pre-change blob and drop out of `touched` (fail-open on the G2 lock; dogfood pre-review cr-001).
    if a.range is not None and ".." not in a.range:   # "" is not "no range" — it must not fall through to staged mode
        sys.stderr.write(f"verify_commit: --range needs A..B (got {a.range!r}); a single ref would compare the wrong side of the lock\n")
        sys.exit(2)
    rejects, flags = [], []

    branch = git("rev-parse", "--abbrev-ref", "HEAD", check=False).strip() or "?"
    if branch in ("main", "master", "develop") and not a.allow_main:
        rejects.append(f"on protected branch `{branch}` — commit on a feature branch (or --allow-main)")

    # staged files + diff
    if a.range:
        files = [l for l in git("diff", "--name-only", a.range).splitlines() if l]
        diff = git("diff", a.range)
    else:
        files = [l for l in git("diff", "--cached", "--name-only").splitlines() if l]
        diff = git("diff", "--cached")
    if not files:
        rejects.append("nothing staged (git add the files of ONE concern)")
    added_lines = [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
    added = len(added_lines)

    # message
    msg = None
    if a.msg_file:
        msg = open(a.msg_file, encoding="utf-8").read()
    elif a.msg is not None:
        msg = a.msg
    if msg is None:
        flags.append("no message given — run again with --msg-file before committing")
    else:
        lines = msg.rstrip("\n").split("\n")
        subj = lines[0].strip()
        m = SUBJECT_RE.match(subj)
        if not m:
            rejects.append(f"subject not Conventional Commits `type(scope)?: subject`: {subj!r}")
        else:
            t = m.group("type")
            if t not in TYPES:
                rejects.append(f"unknown type `{t}` (allowed: {sorted(TYPES)})")
            if t == "wip" and branch in ("main", "master"):
                rejects.append("wip commits are not allowed on main/master")
            if len(subj) > 72:
                rejects.append(f"subject {len(subj)} chars > 72")
            if subj.endswith("."):
                rejects.append("subject ends with a period")
            body = [l for l in lines[1:] if l.strip()]
            breaking = bool(m.group("bang")) or any(l.startswith("BREAKING CHANGE:") for l in lines)
            if breaking and not body:
                rejects.append("breaking change without a body explaining migration")
            for l in lines[1:]:
                if len(l) > 100:
                    flags.append(f"body line > 100 chars: {l[:40]}…"); break
            if a.issue and not re.search(rf"\b(Refs|Closes|Fixes|Resolves)\s+#{a.issue}\b", msg):
                flags.append(f"message does not reference #{a.issue} (add `Refs #{a.issue}` / `Closes #{a.issue}`)")
            if not body and added > 30:
                flags.append("no body on a non-trivial diff — say why, not just what")
            if not m.group("scope") and len({f.split('/')[0] for f in files}) > 3:
                flags.append("files span >3 top-level dirs and no scope — is this one concern?")

    # forbidden artifacts
    for f in files:
        if f.split("/")[-1] in FORBIDDEN_EXCEPT:
            continue
        p = matches_any(f, FORBIDDEN_ARTIFACTS)
        if p:
            rejects.append(f"forbidden artifact staged: {f} (matches {p})")

    # secrets / debug in added lines
    for l in added_lines:
        if SECRET_RE.search(l):
            rejects.append(f"secret-looking string in added line: {l.strip()[:60]}…"); break
    for l in added_lines:
        if DEBUG_REJECT_RE.search(l):
            rejects.append(f"debugger/breakpoint left in added line: {l.strip()[:60]}"); break
    for l in added_lines:
        if DEBUG_FLAG_RE.search(l):
            flags.append(f"console.log/print in added line: {l.strip()[:60]} — intentional?"); break
    if added > a.max_added:
        flags.append(f"{added} added lines > {a.max_added} — consider splitting")

    # card whitelist
    if a.card:
        try:
            import yaml
            card = yaml.safe_load(open(a.card, encoding="utf-8")) or {}
        except Exception as e:
            sys.stderr.write(f"verify_commit: cannot read card: {e}\n"); sys.exit(2)
        allowed = card.get("allowed_files") or []
        forbidden = card.get("forbidden_files") or []
        proposals_staged = [f for f in files if fnmatch.fnmatch(f.split("/")[-1], a.proposal_glob)]
        for f in files:
            if f in proposals_staged:
                continue
            if any(glob_match(f, p) for p in forbidden):
                rejects.append(f"whitelist overflow: {f} is forbidden by card {card.get('id')}")
            elif not any(glob_match(f, p) for p in allowed):
                rejects.append(f"whitelist overflow: {f} not in card {card.get('id')} allowed_files")

    # lock
    lock_status = None
    if a.lock:
        try:
            lock = json.load(open(a.lock, encoding="utf-8"))
        except Exception as e:
            sys.stderr.write(f"verify_commit: cannot read lock: {e}\n"); sys.exit(2)
        locked = {e["path"] for e in lock.get("files", [])}
        locked_sha = {e["path"]: e.get("sha256") for e in lock.get("files", [])}

        def staged_sha256(path):
            # the content about to land: index blob in staged mode, the range head's blob in --range mode
            # `A..` and `A...` are legal git ranges whose right endpoint defaults to HEAD; the split then yields
            # "" and `git show :path` would read the INDEX — the wrong side again (pre-review cr-004).
            head = (re.split(r"[.]{2,3}", a.range)[-1].strip() or "HEAD") if getattr(a, "range", None) else None
            ref = f"{head}:{path}" if head else f":{path}"
            r = subprocess.run(["git", "show", ref], capture_output=True)
            return hashlib.sha256(r.stdout).hexdigest() if r.returncode == 0 else None

        # committing the frozen bytes themselves (first add, or an unchanged file in a range) is not a change of a
        # locked file — compare the landing content's hash with the lock (dogfood 2026-09-05, I-52)
        touched = [f for f in files
                   if (f in locked or any(f.startswith(l.rstrip("/") + "/") for l in locked))
                   and not (f in locked_sha and locked_sha[f] and staged_sha256(f) == locked_sha[f])]
        proposals_staged = [f for f in files if fnmatch.fnmatch(f.split("/")[-1], a.proposal_glob)]
        if touched and not proposals_staged:
            rejects.append(f"locked file(s) in diff without a change proposal: {touched} (G2 lock; add {a.proposal_glob})")
            lock_status = "reject"
        elif touched:
            flags.append(f"locked file(s) changed WITH proposal {proposals_staged} — record `sdlc_state.py fail --signal lock_hash_mismatch` and re-sign")
            lock_status = "changed_with_proposal"
        else:
            lock_status = "ok"

    out = {"verdict": "REJECT" if rejects else "PASS", "branch": branch, "files": files, "added_lines": added,
           "lock": lock_status, "rejects": rejects, "flags": flags}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(1 if rejects else 0)


if __name__ == "__main__":
    main()
