#!/usr/bin/env python3
"""Drive the real service with model-generated vectors and record implementation traces.

    python3 harness.py --vectors vectors.json --out traces/ [--variant atomic|check-then-act]

Each vector runs against a fresh database. The harness records what the implementation
ACTUALLY did (purchase -> `buy` on success, `reject` on sold out) together with the
observables read back from the database, so `fv trace-check` / `fv conform` can decide
whether reality fits the model. A step the model forbids but the code performs, or a step
the model allows but the code refuses, is also reported here as an expectation mismatch.
Exit 0 = every expectation met; 1 = mismatches (traces are still written).
"""
import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tickets import TicketService, setup  # noqa: E402


def run_vector(vector, variant, users, stock, out_dir, model_id):
    with tempfile.TemporaryDirectory() as tmp:
        db = str(Path(tmp) / "tickets.db")
        setup(db, stock)
        svc = TicketService(db, users, variant)
        name = re.sub(r"[^A-Za-z0-9._-]+", "_", vector["id"]).strip("_") or "vector"
        path = Path(out_dir) / (name + ".jsonl")
        mismatches = []
        with path.open("x", encoding="utf-8") as trace:
            def emit(obj):
                trace.write(json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n")
            emit({"kind": "fv-trace", "schema_version": 1, "model": model_id, "vector": vector["id"], "variant": variant})
            emit({"init": True, "observed": svc.observe()})
            for n, step in enumerate(vector["steps"], start=1):
                want, user = step["action"]["name"], step["action"]["params"]["u"]
                if want == "request":
                    svc.request(user)
                    actual = "request"
                elif want == "read":
                    svc.read(user)
                    actual = "read"
                elif want in ("buy", "reject"):
                    actual = "buy" if svc.purchase(user) == "success" else "reject"
                else:
                    raise SystemExit("harness has no adapter for action " + want)
                emit({"action": actual, "params": {"u": user}, "observed": svc.observe()})
                if step["enabled"] and actual != want:
                    mismatches.append({"vector": vector["id"], "step": n, "expected": want, "actual": actual})
                if not step["enabled"] and actual == want:
                    mismatches.append({"vector": vector["id"], "step": n, "expected": "refuse " + want, "actual": actual})
        svc.close()
        return str(path), mismatches


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--vectors", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--variant", default="atomic", choices=["atomic", "check-then-act"])
    a = p.parse_args()
    doc = json.loads(Path(a.vectors).read_text(encoding="utf-8"))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    users, stock = ("alice", "bob"), 1
    traces, mismatches = [], []
    for vector in doc["vectors"]:
        path, bad = run_vector(vector, a.variant, users, stock, out, doc["model"]["id"])
        traces.append(path)
        mismatches += bad
    print(json.dumps({"traces": traces, "mismatches": mismatches, "variant": a.variant}, ensure_ascii=False, indent=2))
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
