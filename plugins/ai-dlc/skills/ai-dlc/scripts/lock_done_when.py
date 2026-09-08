#!/usr/bin/env python3
"""
lock_done_when.py — G2 hash-freeze of the acceptance contract, and the A-tier lock check.

The contract (done_when.yaml, contract.yaml, and once written tests/**) is what the whole lower half
turns around: G2 freezes it, the hidden set is its variant, spec-gaming checks whether it was bypassed,
the ratchet reads it to decide DONE. Without a lock, "acceptance" degrades into a parrot of the design.

Usage:
  lock_done_when.py sign   --by NAME [--stage g2|l5] [--out .done_when.lock] [--gate SCRIPT ...] FILE [FILE ...]
      two-stage lock: g2 signs the criteria (done_when.yaml [contract.yaml]); l5 re-signs after tests are written
      (done_when.yaml with behavior filled + tests/**) — C6: tests are locked too, they are just not the gate
      --gate freezes the scripts that ENFORCE the contract (verify_*.py …) alongside it: a frozen contract whose
      gate can be edited mid-run is not frozen (INV-001). Gate entries carry role=gate; changing one is a
      deviation to record in the ledger, not a change of the criteria (dogfood 2026-09-06, I-30).
  lock_done_when.py verify [--lock .done_when.lock] [--proposal-glob 'change-proposal-*.md'] [--staged]

Not lockable: g1-interpretations*.md. A G1 record's adjudication is frozen at signature, but interpreting
its own ruling is a legitimate G1 function; freezing the interpretations file would make every clarification
a contract change (dogfood 2026-09-06, I-60). Lock the signed form draft and the record instead.

Exit codes:
  sign:   0 written · 1 bad signature (delegated without authorization) · 2 IO error / refused lock set
  verify: 0 all locked files unchanged
          1 REJECT — a locked file changed/missing and no change proposal accompanies it
          2 CHANGED_WITH_PROPOSAL — a locked file changed AND a change proposal is present
            (legal path; counts as one task-layer reflow — the caller records it via aidlc_state.py fail
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


def die(msg, code=2):
    sys.stderr.write(f"lock_done_when: {msg}\n")
    sys.exit(code)


def now():
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def unlockable(path):
    """Files whose whole point is to be appended to after the signature (I-60)."""
    return glob.fnmatch.fnmatch(os.path.basename(path).lower(), "g1-interpretations*.md") or \
        glob.fnmatch.fnmatch(os.path.basename(path).lower(), "g1_interpretations*.md")


def cmd_sign(a):
    files = []
    for p, role in [(p, "contract") for p in a.files] + [(p, "gate") for p in (a.gate or [])]:
        if not os.path.isfile(p):
            sys.stderr.write(f"lock: not a file: {p}\n"); sys.exit(2)
        if unlockable(p):
            die(f"refusing to lock {p}: a G1 interpretation is appended after the signature and must not need a "
                "change proposal to land (I-60). Lock the signed form draft and the g1-record that carries its "
                "sha256; interpretation rules go in g1-interpretations.md, outside the lock", 2)
        files.append({"path": p, "sha256": sha256(p), "role": role})
    if a.signer_kind == "delegated_agent" and not a.authorization:
        die("--signer-kind delegated_agent requires --authorization (who / when / what allowed the delegation)", 1)
    gates = [x["path"] for x in files if x["role"] == "gate"]
    lock = {"version": 1, "stage": a.stage, "signed_by": a.by, "signer_kind": a.signer_kind,
            **({"authorization": a.authorization} if a.authorization else {}), "signed_at": now(), "files": files,
            "note": ("G2 freeze: acceptance/existence/thresholds/rules/constraints signed. " if a.stage == "g2" else
                     "L5 freeze: tests/** + behavior manifest signed (written by a non-implementer). ")
                    + "Changing a listed file requires a change-proposal-*.md in the same diff"
                    + ("; changing a role=gate file is a deviation to record in the ledger." if gates else ".")}
    tmp = a.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(lock, f, ensure_ascii=False, indent=2); f.write("\n")
    os.replace(tmp, a.out)
    out = {"ok": True, "lock": a.out, "files": [x["path"] for x in files]}
    if gates:
        out["gates"] = gates
    elif a.stage == "l5":
        # the contract and its tests are frozen, the scripts that enforce them are not: a gate can be edited
        # mid-run and nothing notices (INV-001, dogfood 2026-09-06 I-30)
        out["warning"] = ("no gate script in the l5 lock: the contract and its tests are frozen but the "
                          "verify_*.py that enforce them are not — pass --gate <script> for each")
    print(json.dumps(out, ensure_ascii=False))


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
    # a changed gate script is not a changed criterion: the contract still says what it said, the ruler moved.
    # It is reported on its own line so the record it needs (a deviation event) is the one the operator writes.
    roles = {e["path"]: e.get("role", "contract") for e in lock.get("files", [])}
    changed_gates = [p for p in changed if roles.get(p) == "gate"]
    changed = [p for p in changed if roles.get(p) != "gate"]
    result = {"lock": a.lock, "stage": lock.get("stage", "g2"), "signed_by": lock.get("signed_by"), "signer_kind": lock.get("signer_kind", "human"), "signed_at": lock.get("signed_at"),
              "changed": changed, "changed_gates": changed_gates, "missing": missing, "proposals": proposals}
    deviation = ("; a gate script changed under a frozen contract — record it as a deviation "
                 "(`aidlc_state.py ledger --kind deviation --signal gate_script_changed --ref references:<script>`) "
                 "and land it in its own commit (INV-001)") if changed_gates else ""
    if not changed and not changed_gates and not missing:
        result["status"] = "ok"; print(json.dumps(result, ensure_ascii=False, indent=2)); sys.exit(0)
    if proposals:
        result["status"] = "changed_with_proposal"
        result["next"] = ("confirm the proposal is legitimate, re-sign (`sign`), record "
                          "`aidlc_state.py fail --signal lock_hash_mismatch`" + deviation)
        print(json.dumps(result, ensure_ascii=False, indent=2)); sys.exit(2)
    result["status"] = "reject"
    result["why"] = "locked file changed without a change proposal in the same diff (G2 A-tier lock check)" + deviation
    print(json.dumps(result, ensure_ascii=False, indent=2)); sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sign"); s.add_argument("--by", required=True); s.add_argument("--out", default=".done_when.lock"); s.add_argument("--stage", choices=["g2", "l5"], default="g2")
    s.add_argument("--signer-kind", choices=["human", "delegated_agent"], required=True,
                   help="who is signing. No default: omitting it used to record an agent as a person, "
                        "and a discipline bypassable by omission is not a discipline (re-audit 2026-09-06)")
    s.add_argument("--authorization")
    s.add_argument("--gate", action="append", metavar="SCRIPT"); s.add_argument("files", nargs="+")
    s = sub.add_parser("verify"); s.add_argument("--lock", default=".done_when.lock"); s.add_argument("--proposal-glob", default="change-proposal-*.md"); s.add_argument("--staged", action="store_true")
    a = ap.parse_args()
    {"sign": cmd_sign, "verify": cmd_verify}[a.cmd](a)


if __name__ == "__main__":
    main()
