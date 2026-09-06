#!/usr/bin/env python3
"""
verify_commit.py — the mechanical pre-gate for /commit: checks the PRODUCT (staged set + message)
before the commit lands. It is the whitelist executor (L6), the G2 lock check (A-tier), and the
secret/debug scan — things the engine can reason about but does not reliably execute (A′-1).

Usage:
  verify_commit.py [--msg-file FILE | --msg TEXT] [--card CARD.yaml] [--lock .done_when.lock]
                   [--issue N] [--allow-main] [--proposal-glob 'change-proposal-*.md']
                   [--max-added 800] [--range A..B] [--no-version-sync]

Reads the staged diff by default (`git diff --cached`); with --range, the diff of that commit range
(useful in CI / pre-push). Exit 0 = pass (flags may remain) · 1 = REJECT · 2 = git/IO error.

`scripts/commit.sh` wraps this script and `git commit` into ONE command so the gate cannot be
sequenced away by a caller that swallows the exit code (dogfood 2026-09-06, I-50).

Mechanical guarantees (REJECT — non-waivable half):
  - not on main/master/develop (unless --allow-main)
  - message: Conventional Commits `type(scope)?!?: subject`, subject ≤72, no trailing period, known type
    (`wip` allowed only off main); `!`/BREAKING CHANGE requires a body
  - staged set non-empty; forbidden artifacts not staged (.env, *.pem, id_rsa*, node_modules/, dist/…)
  - secret-looking strings in ADDED lines; debugger/pdb/binding.pry in ADDED lines
  - --card: every staged path matches allowed_files and none matches forbidden_files (whitelist overflow)
  - --lock: locked files changed/staged → REJECT unless a change-proposal-*.md is staged in the same diff
  - --range only: plugin version sync (CLAUDE.md 三处 version) — see version_sync_issues below
Flags (needs_semantic_review): console.log/print in added lines; > --max-added added lines; files across
>3 top-level dirs with no scope; body lines >100; missing Refs/Closes when --issue given; body absent
on non-trivial diffs; `proposal_missing_path` (a changed locked file the change proposal never names);
version sync in staged mode (the bump is allowed to be a separate commit — the range/PR gate rejects).
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


def blob(ref, path):
    """The bytes of `path` at `ref` as text; ref None means the index (staged content). Missing → None."""
    r = subprocess.run(["git", "show", f"{ref}:{path}" if ref else f":{path}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def json_version(text):
    try:
        return (json.loads(text) or {}).get("version")
    except Exception:
        return None


def frontmatter_version(text):
    """`version:` from a SKILL.md YAML frontmatter block only — never from a body line."""
    if not text or not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    fm = text[: end if end > 0 else 2000]
    m = re.search(r"^version:\s*([^\s#]+)\s*$", fm, re.M)
    return m.group(1) if m else None


def mentions(text, path):
    """Coarse: does the proposal name this path — literally, by basename, or by a covering dir glob."""
    if path in text or path.rsplit("/", 1)[-1] in text:
        return True
    parts = path.split("/")
    return any(("/".join(parts[:i]) + "/*") in text or ("/".join(parts[:i]) + "/**") in text
               for i in range(1, len(parts)))


def version_sync_issues(files, base_ref, head_ref):
    """CLAUDE.md's 三处 version 同步 rule, compiled (dogfood 2026-09-06, I-76).

    Changing `plugins/<p>/skills/**` must bump `plugins/<p>/.claude-plugin/plugin.json`'s version, and
    `.claude-plugin/marketplace.json` must carry that same version for <p>. A plugin cache is keyed by
    version and serves `<marketplace>/<plugin>/<version>/`, so a skill fix shipped without a bump is a
    fix no installed user ever receives — the rule lived only in CLAUDE.md and nothing executed it.
    The skill's own SKILL.md frontmatter version is the third location, reported as soft.

    Returns (hard, soft). No `plugins/<p>/.claude-plugin/plugin.json` at head → not this layout, no-op.
    Keep in sync with the same function in ../../pr/scripts/verify_pr.py.
    """
    hard, soft = [], []
    touched = {}
    for f in files:
        parts = f.split("/")
        if len(parts) >= 4 and parts[0] == "plugins" and parts[2] == "skills":
            touched.setdefault(parts[1], set()).add(parts[3])
    if not touched:
        return hard, soft
    mk_entries = []
    mk = blob(head_ref, ".claude-plugin/marketplace.json")
    if mk:
        try:
            mk_entries = (json.loads(mk) or {}).get("plugins") or []
        except Exception:
            soft.append("marketplace.json is not readable JSON at the head side — version sync unchecked")
    for plugin, skills in sorted(touched.items()):
        manifest = f"plugins/{plugin}/.claude-plugin/plugin.json"
        head_txt = blob(head_ref, manifest)
        if head_txt is None:
            continue                                  # not a plugin-marketplace layout: nothing to enforce
        base_txt = blob(base_ref, manifest)
        hv, bv = json_version(head_txt), json_version(base_txt)
        if hv is None:
            soft.append(f"{manifest} has no readable `version` — version sync unchecked")
            continue
        if base_txt is not None and hv == bv:
            hard.append(f"plugins/{plugin}/skills/** changed but {manifest} version is still {hv} — "
                        f"bump it (CLAUDE.md 三处 version 同步; a version-keyed plugin cache never "
                        f"delivers an unbumped fix)")
        for e in mk_entries:
            if isinstance(e, dict) and e.get("name") == plugin and e.get("version") != hv:
                hard.append(f"marketplace.json registers {plugin} at {e.get('version')} but {manifest} "
                            f"says {hv} — the registry must match the manifest")
        for s in sorted(skills):
            sp = f"plugins/{plugin}/skills/{s}/SKILL.md"
            ht, bt = blob(head_ref, sp), blob(base_ref, sp)
            if ht is None or bt is None:
                continue
            if frontmatter_version(ht) == frontmatter_version(bt):
                soft.append(f"{sp} frontmatter version unchanged ({frontmatter_version(ht)}) while the "
                            f"skill's content changed — third of the three locations")
    return hard, soft


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--msg-file"); ap.add_argument("--msg"); ap.add_argument("--card"); ap.add_argument("--lock")
    ap.add_argument("--issue", type=int); ap.add_argument("--allow-main", action="store_true")
    ap.add_argument("--proposal-glob", default="change-proposal-*.md"); ap.add_argument("--max-added", type=int, default=800)
    ap.add_argument("--range"); ap.add_argument("--no-version-sync", action="store_true")
    a = ap.parse_args()
    # --range must name two endpoints: `git diff <one-ref>` is legal but means "worktree vs ref", and the
    # landing-content hash below would then read the WRONG side, letting a tampered locked file hash equal to
    # its own pre-change blob and drop out of `touched` (fail-open on the G2 lock; dogfood pre-review cr-001).
    if a.range is not None and ".." not in a.range:   # "" is not "no range" — it must not fall through to staged mode
        sys.stderr.write(f"verify_commit: --range needs A..B (got {a.range!r}); a single ref would compare the wrong side of the lock\n")
        sys.exit(2)
    rejects, flags = [], []
    # `A..` / `A...` are legal ranges whose right endpoint defaults to HEAD; the split then yields ""
    # and every `git show` below would read the INDEX — the wrong side (pre-review cr-004).
    rng_base = rng_head = None
    if a.range:
        _p = re.split(r"[.]{2,3}", a.range)
        rng_base, rng_head = (_p[0].strip() or "HEAD"), (_p[-1].strip() or "HEAD")

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

    # plugin version sync (CLAUDE.md 三处 version). A range sees the whole delivery, so the bump must be
    # inside it → REJECT. Staged mode sees one commit, and CLAUDE.md itself says the bump is its own
    # commit (`chore: bump …`) → flag only, or this gate would reject the workflow it prescribes (I-76).
    if not a.no_version_sync and files:
        vs_hard, vs_soft = version_sync_issues(files, rng_base or "HEAD", rng_head)
        if a.range:
            rejects.extend(vs_hard)
        else:
            flags.extend(h + " [staged mode: the bump may be its own commit — the --range / PR gate REJECTs]"
                         for h in vs_hard)
        flags.extend(vs_soft)

    # lock
    lock_status = None
    lock_detail = None
    if a.lock:
        try:
            lock = json.load(open(a.lock, encoding="utf-8"))
        except Exception as e:
            sys.stderr.write(f"verify_commit: cannot read lock: {e}\n"); sys.exit(2)
        locked = {e["path"] for e in lock.get("files", [])}
        locked_sha = {e["path"]: e.get("sha256") for e in lock.get("files", [])}

        def staged_sha256(path):
            # the content about to land: index blob in staged mode, the range head's blob in --range mode
            ref = f"{rng_head}:{path}" if rng_head else f":{path}"
            r = subprocess.run(["git", "show", ref], capture_output=True)
            return hashlib.sha256(r.stdout).hexdigest() if r.returncode == 0 else None

        # committing the frozen bytes themselves (first add, or an unchanged file in a range) is not a change of a
        # locked file — compare the landing content's hash with the lock (dogfood 2026-09-05, I-52)
        touched = [f for f in files
                   if (f in locked or any(f.startswith(l.rstrip("/") + "/") for l in locked))
                   and not (f in locked_sha and locked_sha[f] and staged_sha256(f) == locked_sha[f])]
        proposals_staged = [f for f in files if fnmatch.fnmatch(f.split("/")[-1], a.proposal_glob)]
        # The human reviewing the proposal needs the SET, not a verdict: which locked paths actually changed,
        # and whether the proposal names each of them. Computing that by hand across a 26-path lock is how
        # a path gets silently changed under a proposal that never mentions it (dogfood 2026-09-06, I-63).
        proposal_text = "\n".join(t for t in (blob(rng_head, p) for p in proposals_staged) if t)
        missing = sorted(f for f in touched if not mentions(proposal_text, f))
        lock_detail = {"locked_paths": sorted(locked), "locked_changed": sorted(touched),
                       "proposal_files": proposals_staged, "proposal_missing_path": missing}
        if touched and not proposals_staged:
            rejects.append(f"locked file(s) in diff without a change proposal: {touched} (G2 lock; add {a.proposal_glob})")
            lock_status = "reject"
        elif touched:
            flags.append(f"locked file(s) changed WITH proposal {proposals_staged}: {sorted(touched)} — record `sdlc_state.py fail --signal lock_hash_mismatch` and re-sign")
            lock_status = "changed_with_proposal"
            if missing:
                flags.append(f"proposal_missing_path: {missing} changed under the lock but no staged "
                             f"{a.proposal_glob} names them — the proposal must cover every changed locked path")
        else:
            lock_status = "ok"

    out = {"verdict": "REJECT" if rejects else "PASS", "branch": branch, "files": files, "added_lines": added,
           "lock": lock_status, "lock_detail": lock_detail, "rejects": rejects, "flags": flags}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(1 if rejects else 0)


if __name__ == "__main__":
    main()
