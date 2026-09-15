#!/usr/bin/env python3
"""
verify_release.py — the mechanical pre-gate for /release: the PRODUCT (changelog entry + tag + release notes)
must agree with each other and with the commits, before the irreversible actions (push tag / deploy).

Usage:
  verify_release.py --version X.Y.Z [--scheme semver|calver|external] [--changelog CHANGELOG.md]
                    [--notes releases/vX.Y.Z.md] [--base <prev tag>] [--bump auto] [--pre-tag] [--merge-sha SHA]

Exit 0 = pass (flags may remain) · 1 = REJECT · 2 = git/IO error.

Mechanical guarantees (REJECT):
  - CHANGELOG has a `## [X.Y.Z] - YYYY-MM-DD` entry with a valid date
  - release notes exist and carry Changes / Verification / Rollback / Escape sections; Rollback non-empty
  - version is valid under --scheme and > the previous tag (--base, else latest v* tag of the same scheme)
  - --bump auto: derived bump (major/minor/patch from commits base..HEAD) matches the version delta (semver only)
  - without --pre-tag: tag vX.Y.Z exists and points at --merge-sha (or HEAD)
  - with --pre-tag: tag vX.Y.Z must NOT already exist
--scheme (dogfood vana-builder V-09: a product versioned `26.04.01341` could only skip this gate whole):
  semver    (default) the checks above
  calver    YY[YY].MM[.N…] — numeric segments, month 1–12, ordered segment by segment; --bump auto is a usage
            error (a calendar version has no bump to derive)
  external  the version, tag and changelog belong to another release system (a CI pipeline that stamps the
            build). They are reported in `unchecked`, never as passed; what stays checked is AI-DLC's own part —
            release notes with Rollback / post-deploy Verification / Escape. `aidlc_state.py` still wants a tag for
            release.done, so a run whose release system cuts none records release.skipped_reason and keeps these
            notes as the evidence.
Flags: notes Verification lacks a post-deploy line; changelog entry empty sections.
"""
import argparse
import datetime as _dt
import json
import re
import subprocess
import sys

# SemVer 2.0.0 §2: numeric identifiers MUST NOT include leading zeroes. Without that rule a calendar build number
# such as 26.04.01341 read as SemVer and --bump auto derived a "bump" for it (vana-builder V-09).
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?$")
CALVER_RE = re.compile(r"^(\d{2}|\d{4})\.(\d{1,2})((?:\.\d+)*)$")


def git(*args, check=False):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.stderr.write(f"verify_release: git {' '.join(args)} failed: {r.stderr.strip()}\n"); sys.exit(2)
    return r.stdout.strip(), r.returncode


def parse(v, scheme="semver"):
    v = v.lstrip("v")
    if scheme == "calver":
        m = CALVER_RE.match(v)
        if not m or not 1 <= int(m.group(2)) <= 12:
            return None
        return tuple(int(x) for x in v.split("."))
    if scheme == "external":
        return None
    m = SEMVER_RE.match(v)
    return tuple(int(x) for x in m.groups()) if m else None


def derived_bump(base, head):
    out, rc = git("log", "--format=%s%n%b", f"{base}..{head}")
    if rc != 0:
        return None
    subjects = [l for l in out.splitlines() if l.strip()]
    if any(re.match(r"^[a-z]+(\([^)]+\))?!:", l) for l in subjects) or any("BREAKING CHANGE:" in l for l in subjects):
        return "major"
    if any(re.match(r"^feat(\([^)]+\))?:", l) for l in subjects):
        return "minor"
    return "patch"


def delta(prev, new):
    if prev is None:
        return None
    if new[0] > prev[0]:
        return "major"
    if new[1] > prev[1]:
        return "minor"
    if new[2] > prev[2]:
        return "patch"
    return "none"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", required=True); ap.add_argument("--changelog", default="CHANGELOG.md")
    ap.add_argument("--notes"); ap.add_argument("--base"); ap.add_argument("--bump", choices=["auto"]); ap.add_argument("--pre-tag", action="store_true")
    ap.add_argument("--merge-sha")
    ap.add_argument("--scheme", choices=["semver", "calver", "external"], default="semver")
    a = ap.parse_args()
    rejects, flags, unchecked = [], [], []
    ext = a.scheme == "external"
    if a.bump and a.scheme != "semver":
        sys.stderr.write(f"verify_release: --bump auto derives a SemVer bump; it has no meaning under --scheme {a.scheme}\n"); sys.exit(2)
    v = a.version.lstrip("v"); pv = parse(v, a.scheme)
    if ext:
        if not v or re.search(r"\s", v):
            rejects.append(f"version {a.version!r} is empty or contains whitespace")
        unchecked.append("version format and ordering (--scheme external: owned by the release system)")
    elif not pv:
        rejects.append(f"version {a.version!r} is not {'SemVer' if a.scheme == 'semver' else 'CalVer YY[YY].MM[.N…]'}"
                       + (" — a calendar version? pass --scheme calver (or external)" if a.scheme == "semver" and parse(v, "calver") else ""))
    tag = f"v{v}"
    notes = a.notes or f"releases/{tag}.md"

    # changelog
    try:
        cl = open(a.changelog, encoding="utf-8").read()
    except OSError:
        cl = None
        if ext:
            unchecked.append(f"changelog ({a.changelog} absent — owned by the release system)")
        else:
            rejects.append(f"changelog not found: {a.changelog}")
    m = re.search(rf"^## \[{re.escape(v)}\]\s*-\s*(\d{{4}}-\d{{2}}-\d{{2}})\s*$", cl, re.M) if cl is not None else None
    if cl is None:
        pass
    elif not m:
        rejects.append(f"changelog has no `## [{v}] - YYYY-MM-DD` entry")
    else:
        try:
            _dt.date.fromisoformat(m.group(1))
        except ValueError:
            rejects.append(f"changelog entry date {m.group(1)} invalid")
        body = cl[m.end():]
        nxt = re.search(r"^## \[", body, re.M)
        body = body[:nxt.start()] if nxt else body
        if not re.search(r"^\s*-\s+\S", body, re.M):
            flags.append("changelog entry has no bullet lines")

    # notes
    try:
        nt = open(notes, encoding="utf-8").read()
    except OSError:
        nt = ""; rejects.append(f"release notes not found: {notes}")
    if nt:
        secs = {m.group(1).strip().lower(): m.start() for m in re.finditer(r"^##\s+(.+)$", nt, re.M)}
        for s in ("changes", "verification", "rollback", "escape"):
            if s not in secs:
                rejects.append(f"release notes missing section: ## {s.title()}")
        if "rollback" in secs:
            start = secs["rollback"]; rest = nt[start:]
            nxt = re.search(r"^##\s+", rest[3:], re.M)
            block = rest[: (nxt.start() + 3) if nxt else len(rest)]
            if not re.search(r"^\s*-\s*how\s*:\s*\S", block, re.M | re.I) or "<" in re.search(r"how\s*:(.*)", block, re.I).group(1):
                rejects.append("Rollback section has no concrete `how:` line")
        if "verification" in secs and not re.search(r"post-deploy\s*:\s*\S", nt, re.I):
            flags.append("Verification has no post-deploy line — release.done must stay false until it exists")

    # previous tag / ordering / bump
    base = a.base
    if ext:
        base = None
    elif not base:
        # previous release = highest v* tag strictly below the version under check (never the version's own tag)
        out, rc = git("tag", "--list", "v*", "--sort=-v:refname")
        for t in (out.splitlines() if rc == 0 else []):
            pt = parse(t, a.scheme)
            if pt and pv and pt < pv:
                base = t; break
    prev = parse(base, a.scheme) if base else None
    if prev and pv and pv <= prev:
        rejects.append(f"version {v} not greater than previous tag {base}")
    if a.bump == "auto":
        head = a.merge_sha or "HEAD"
        db = derived_bump(base, head) if base else None
        if db and prev:
            dl = delta(prev, pv)
            if prev[0] == 0 and db == "major":
                db = "minor"  # 0.x: breaking → minor
            if dl != db:
                rejects.append(f"bump mismatch: commits {base}..{head} imply {db}, version delta is {dl}")
        elif not base:
            flags.append("no previous tag — bump derivation skipped (first release)")

    # tag
    out, rc = git("rev-parse", "--verify", f"refs/tags/{tag}")
    exists = rc == 0
    if ext:
        unchecked.append("tag (--scheme external: cut by the release system, if at all)")
    elif a.pre_tag and exists:
        rejects.append(f"tag {tag} already exists — never overwrite a tag")
    if not a.pre_tag and not ext:
        if not exists:
            rejects.append(f"tag {tag} does not exist (run with --pre-tag before tagging)")
        else:
            target, _ = git("rev-list", "-n", "1", tag)
            want, _ = git("rev-parse", a.merge_sha or "HEAD")
            if target != want:
                rejects.append(f"tag {tag} points at {target[:7]}, expected {want[:7]}")
    out = {"verdict": "REJECT" if rejects else "PASS", "scheme": a.scheme, "version": v, "tag": None if ext else tag,
           "previous_tag": base, "unchecked": unchecked, "rejects": rejects, "flags": flags}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(1 if rejects else 0)


if __name__ == "__main__":
    main()
