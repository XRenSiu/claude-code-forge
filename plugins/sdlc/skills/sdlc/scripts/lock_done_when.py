#!/usr/bin/env python3
"""
lock_done_when.py — G2 hash-freeze of the acceptance contract, and the A-tier lock check.

The contract (done_when.yaml, contract.yaml, and once written tests/**) is what the whole lower half
turns around: G2 freezes it, the hidden set is its variant, spec-gaming checks whether it was bypassed,
the ratchet reads it to decide DONE. Without a lock, "acceptance" degrades into a parrot of the design.

Usage:
  lock_done_when.py sign   --by NAME [--out .done_when.lock] FILE [FILE ...]
  lock_done_when.py verify [--lock .done_when.lock] [--proposal-glob 'change-proposal-*.md'] [--staged]

Exit codes:
  sign:   0 written · 2 IO error
  verify: 0 all locked files unchanged
          1 REJECT — a locked file changed/missing and no change proposal accompanies it
          2 CHANGED_WITH_PROPOSAL — a locked file changed AND a change proposal is present
            (legal path; counts as one task-layer reflow — the caller records it via sdlc_state.py fail
             --signal lock_hash_mismatch after confirming the proposal is legitimate)
          3 usage/IO error
With --staged, "a change proposal is present" means one is staged in git (git diff --cached --name-only),
so the proposal travels in the same diff as the change — that is the rule (G2: 同一 diff 附带变更提案文件).
"""
import argparse
import datetime as _dt
import glob
import hashlib
import json
import os
import subprocess
import sys


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def now():
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def cmd_sign(a):
    files = []
    for p in a.files:
        if not os.path.isfile(p):
            sys.stderr.write(f"lock: not a file: {p}\n"); sys.exit(2)
        files.append({"path": p, "sha256": sha256(p)})
    lock = {"version": 1, "signed_by": a.by, "signed_at": now(), "files": files,
            "note": "G2 freeze. Changing a listed file requires a change-proposal-*.md in the same diff."}
    tmp = a.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(lock, f, ensure_ascii=False, indent=2); f.write("\n")
    os.replace(tmp, a.out)
    print(json.dumps({"ok": True, "lock": a.out, "files": [x["path"] for x in files]}, ensure_ascii=False))


def staged_files():
    try:
        out = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, check=True).stdout
        return [l.strip() for l in out.splitlines() if l.strip()]
    except Exception as e:
        sys.stderr.write(f"lock: git unavailable for --staged: {e}\n"); sys.exit(3)


def cmd_verify(a):
    if not os.path.isfile(a.lock):
        sys.stderr.write(f"lock: no lock file at {a.lock} — G2 has not been signed\n"); sys.exit(3)
    with open(a.lock, encoding="utf-8") as f:
        lock = json.load(f)
    changed, missing = [], []
    for entry in lock.get("files", []):
        p = entry["path"]
        if not os.path.isfile(p):
            missing.append(p)
        elif sha256(p) != entry["sha256"]:
            changed.append(p)
    if a.staged:
        st = set(staged_files())
        for entry in lock.get("files", []):
            if entry["path"] in st and entry["path"] not in changed and entry["path"] not in missing:
                changed.append(entry["path"])  # staged but content equal to lock on disk? still flag: staged delta exists
        proposals = [f for f in st if glob.fnmatch.fnmatch(os.path.basename(f), a.proposal_glob)]
    else:
        proposals = glob.glob(a.proposal_glob) + glob.glob(os.path.join("**", a.proposal_glob), recursive=True)
    proposals = sorted(set(proposals))
    result = {"lock": a.lock, "signed_by": lock.get("signed_by"), "signed_at": lock.get("signed_at"),
              "changed": changed, "missing": missing, "proposals": proposals}
    if not changed and not missing:
        result["status"] = "ok"; print(json.dumps(result, ensure_ascii=False, indent=2)); sys.exit(0)
    if proposals:
        result["status"] = "changed_with_proposal"
        result["next"] = "confirm the proposal is legitimate, re-sign (`sign`), record `sdlc_state.py fail --signal lock_hash_mismatch`"
        print(json.dumps(result, ensure_ascii=False, indent=2)); sys.exit(2)
    result["status"] = "reject"
    result["why"] = "locked file changed without a change proposal in the same diff (G2 A-tier lock check)"
    print(json.dumps(result, ensure_ascii=False, indent=2)); sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sign"); s.add_argument("--by", required=True); s.add_argument("--out", default=".done_when.lock"); s.add_argument("files", nargs="+")
    s = sub.add_parser("verify"); s.add_argument("--lock", default=".done_when.lock"); s.add_argument("--proposal-glob", default="change-proposal-*.md"); s.add_argument("--staged", action="store_true")
    a = ap.parse_args()
    {"sign": cmd_sign, "verify": cmd_verify}[a.cmd](a)


if __name__ == "__main__":
    main()
