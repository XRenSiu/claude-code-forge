#!/usr/bin/env python3
"""Property tests of the REAL ticket service against the contract (E3 evidence, not a proof).

Seeded random schedules drive the public API (request / read / purchase, including retries of
the same call) on a real SQLite database and check the contract's properties after every call:

    --check safety     NoOversell, StockNonNegative, Conservation, SoldNeverDecreases, and that some
                       schedule sells the whole stock (SomeoneCanBuy)
    --check liveness   EveryRequestAnswered: once the schedule stops, every requested user who
                       keeps calling read + purchase gets "success" or "sold_out" within a bound

The schedules are wider than the model's scope (more users, more stock) on purpose: the model
fixed the design on a small scope; the code must hold the properties on the inputs it meets.

    python3 test_properties.py --check safety                           # exit 0
    python3 test_properties.py --check safety --variant check-then-act  # negative control: exit 1
"""
import argparse
import random
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tickets import TicketService, setup  # noqa: E402

USERS = ("alice", "bob", "carol", "dave")


def schedule(rng, variant, stock, steps):
    """One random interleaving through the public API; returns the first violated property or None."""
    with tempfile.TemporaryDirectory() as tmp:
        db = str(Path(tmp) / "tickets.db")
        setup(db, stock)
        svc = TicketService(db, USERS, variant)
        try:
            before = svc.observe()
            for _ in range(steps):
                user = rng.choice(USERS)
                call = rng.choice(("request", "read", "purchase", "purchase"))   # retries happen: purchase twice
                if call == "request":
                    svc.request(user)
                elif call == "read":
                    svc.read(user)
                elif before["outcome"][user] != "none":
                    svc.purchase(user)
                after = svc.observe()
                for prop, ok in (("NoOversell", after["sold"] <= stock), ("StockNonNegative", after["remaining"] >= 0),
                                 ("Conservation", after["sold"] + after["remaining"] == stock),
                                 ("SoldNeverDecreases", after["sold"] >= before["sold"])):
                    if not ok:
                        return prop, after
                before = after
            return None, before
        finally:
            svc.close()


def safety(variant, seeds):
    sold_out_seen = False
    for seed in range(seeds):
        rng = random.Random(seed)
        stock = rng.choice((1, 2))
        bad, final = schedule(rng, variant, stock, steps=24)
        if bad:
            print("seed %d: %s violated, observed %s" % (seed, bad, final))
            return 1
        sold_out_seen = sold_out_seen or final["sold"] == stock
    if not sold_out_seen:
        print("SomeoneCanBuy: no schedule sold the whole stock")
        return 1
    print("safety: %d schedules, every property held after every call" % seeds)
    return 0


def liveness(variant, seeds, bound=8):
    for seed in range(seeds):
        rng = random.Random(seed)
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / "tickets.db")
            setup(db, rng.choice((1, 2)))
            svc = TicketService(db, USERS, variant)
            try:
                for _ in range(12):
                    user = rng.choice(USERS)
                    getattr(svc, rng.choice(("request", "read")))(user)
                for user in USERS:
                    if svc.observe()["outcome"][user] == "none":
                        continue
                    for _ in range(bound):
                        if svc.observe()["outcome"][user] in ("success", "sold_out"):
                            break
                        svc.read(user)
                        svc.purchase(user)
                    if svc.observe()["outcome"][user] not in ("success", "sold_out"):
                        print("seed %d: EveryRequestAnswered: %s still pending after %d attempts" % (seed, user, bound))
                        return 1
            finally:
                svc.close()
    print("liveness: %d schedules, every request answered" % seeds)
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--check", choices=["safety", "liveness"], required=True)
    p.add_argument("--variant", default="atomic", choices=["atomic", "check-then-act"])
    p.add_argument("--seeds", type=int, default=200)
    a = p.parse_args()
    return safety(a.variant, a.seeds) if a.check == "safety" else liveness(a.variant, a.seeds)


if __name__ == "__main__":
    sys.exit(main())
