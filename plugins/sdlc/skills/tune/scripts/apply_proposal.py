#!/usr/bin/env python3
"""
apply_proposal.py — turn a tune.py proposal into a reviewable diff. It NEVER writes to the target files: the only
outputs are a unified diff on stdout (--dry-run, the default) and/or a .patch file (--patch) a human applies on a
branch with `git apply` and opens a PR from. That is the hill-climbing loop's human gate, compiled.

Usage:
  apply_proposal.py PROPOSALS.yaml [--id P-1 ...] [--routing ROUTING.yaml] [--pr-poll pr-poll.sh]
                    [--skills-root plugins/sdlc/skills] [--dry-run] [--patch OUT.patch]

Proposal `apply` kinds:
  routing_budget  {track, key, value}   → edits the inline budgets line in routing.yaml (comments preserved)
  routing_scalar  {key, value}          → edits a top-level `key: value` line in routing.yaml
  pr_poll_env     {var, value}          → edits the `VAR="${VAR:-default}"` line in review-loop/scripts/pr-poll.sh
  gate_fix_list   {skill, item}         → appends to <skills-root>/<skill>/eval/gate.json fix_list (JSON re-dumped, indent 2)

Exit 0 = diff produced (possibly empty) · 1 = proposal id not found / target file missing / kind unknown · 2 = IO.
"""
import argparse
import difflib
import json
import os
import re
import sys


def load_yaml(path):
    try:
        import yaml
    except ImportError:
        sys.stderr.write("apply_proposal: PyYAML required\n"); sys.exit(2)
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def read(path):
    if not os.path.isfile(path):
        sys.stderr.write(f"apply_proposal: target file missing: {path}\n"); sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return f.read()


def udiff(path, old, new):
    rel = os.path.relpath(path)
    return "".join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), f"a/{rel}", f"b/{rel}"))


def routing_budget(text, track, key, value):
    pat = re.compile(rf"^(\s*{re.escape(track)}:\s*\{{[^}}]*?\b{re.escape(key)}:\s*)(\S+?)(\s*[,}}])", re.M)
    new, n = pat.subn(lambda m: f"{m.group(1)}{value}{m.group(3)}", text, count=1)
    if n == 0:
        sys.stderr.write(f"apply_proposal: could not find budgets.{track}.{key} line\n"); sys.exit(1)
    return new


def routing_scalar(text, key, value):
    pat = re.compile(rf"^({re.escape(key)}:\s*)(\S+)(.*)$", re.M)
    new, n = pat.subn(lambda m: f"{m.group(1)}{value}{m.group(3)}", text, count=1)
    if n == 0:
        sys.stderr.write(f"apply_proposal: could not find top-level {key}: line\n"); sys.exit(1)
    return new


def pr_poll_env(text, var, value):
    pat = re.compile(rf'^({re.escape(var)}="\$\{{{re.escape(var)}:-)([^}}]*)(\}}")', re.M)
    new, n = pat.subn(lambda m: f"{m.group(1)}{value}{m.group(3)}", text, count=1)
    if n == 0:
        sys.stderr.write(f"apply_proposal: could not find {var} default line in pr-poll.sh\n"); sys.exit(1)
    return new


def gate_fix_list(text, item):
    try:
        d = json.loads(text)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"apply_proposal: gate.json not valid JSON: {e}\n"); sys.exit(1)
    fl = d.setdefault("fix_list", [])
    if item not in fl:
        fl.append(item)
    return json.dumps(d, ensure_ascii=False, indent=2) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("proposals"); ap.add_argument("--id", action="append")
    ap.add_argument("--routing"); ap.add_argument("--pr-poll"); ap.add_argument("--skills-root")
    ap.add_argument("--dry-run", action="store_true", default=True); ap.add_argument("--patch")
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    skills_root = a.skills_root or os.path.join(here, "..", "..")
    routing = a.routing or os.path.join(skills_root, "sdlc", "assets", "routing.yaml")
    pr_poll = a.pr_poll or os.path.join(skills_root, "review-loop", "scripts", "pr-poll.sh")
    doc = load_yaml(a.proposals)
    props = doc.get("proposals") or []
    if a.id:
        want = set(a.id)
        props = [p for p in props if p.get("id") in want]
        missing = want - {p.get("id") for p in props}
        if missing:
            sys.stderr.write(f"apply_proposal: proposal id(s) not found: {sorted(missing)}\n"); sys.exit(1)
    if not props:
        print("(no proposals selected — nothing to diff)"); return
    diffs, touched = [], {}
    for p in props:
        ap_ = p.get("apply") or {}
        kind = ap_.get("kind")
        if kind in ("routing_budget", "routing_scalar"):
            path = routing
        elif kind == "pr_poll_env":
            path = pr_poll
        elif kind == "gate_fix_list":
            path = os.path.join(skills_root, ap_.get("skill", ""), "eval", "gate.json")
        else:
            sys.stderr.write(f"apply_proposal: {p.get('id')}: unknown apply.kind {kind!r}\n"); sys.exit(1)
        cur = touched.get(path) or read(path)
        if kind == "routing_budget":
            new = routing_budget(cur, ap_["track"], ap_["key"], ap_["value"])
        elif kind == "routing_scalar":
            new = routing_scalar(cur, ap_["key"], ap_["value"])
        elif kind == "pr_poll_env":
            new = pr_poll_env(cur, ap_["var"], ap_["value"])
        else:
            new = gate_fix_list(cur, ap_["item"])
        touched[path] = new
        diffs.append(f"# {p.get('id')} · {p.get('target')} · {p.get('current')} → {p.get('proposed')}\n# evidence: {'; '.join(p.get('evidence') or [])}\n# verify_by: {p.get('verify_by')}\n")
    body = ""
    for path, new in touched.items():
        body += udiff(path, read(path), new)
    out = "".join(diffs) + body
    if a.patch:
        with open(a.patch, "w", encoding="utf-8") as f:
            f.write(out)
        print(json.dumps({"ok": True, "patch": a.patch, "files": [os.path.relpath(p) for p in touched],
                          "note": "targets untouched — apply on a branch with `git apply` and open a PR; a human merges"}, ensure_ascii=False, indent=2))
    else:
        print(out if out.strip() else "(empty diff — proposal already in effect)")
        print("\n# dry-run: no file modified. Use --patch OUT.patch, then `git apply` on a branch and open a PR.", file=sys.stderr)


if __name__ == "__main__":
    main()
