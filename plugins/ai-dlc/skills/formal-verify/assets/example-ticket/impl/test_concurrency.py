#!/usr/bin/env python3
"""Real concurrent purchases against a real database file (E3 evidence, not a proof).

Two threads read "1 left", wait for each other, then purchase. The atomic reservation must
never oversell; the check-then-act variant is expected to oversell under the same schedule,
which shows the test can actually see the defect the model found.

    python3 test_concurrency.py                          # the shipped (atomic) implementation
    python3 test_concurrency.py --variant check-then-act # negative control: must FAIL (exit 1)

The second form is the implementation contract's `must_fail_with` for this test: a check that
was never seen failing proves nothing.
"""
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tickets import TicketService, setup  # noqa: E402

USERS = ("alice", "bob")
VARIANT = "atomic"


def race(variant, rounds=20):
    worst = 0
    for _ in range(rounds):
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / "tickets.db")
            setup(db, 1)
            barrier = threading.Barrier(len(USERS))
            errors = []

            def buyer(user):
                svc = TicketService(db, USERS, variant)
                try:
                    svc.request(user)
                    svc.read(user)
                    barrier.wait(timeout=10)      # both have seen "1 left"
                    svc.purchase(user)
                except Exception as error:      # surfaced below, never swallowed
                    errors.append(error)
                finally:
                    svc.close()
            threads = [threading.Thread(target=buyer, args=(u,)) for u in USERS]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            if errors:
                raise errors[0]
            svc = TicketService(db, USERS, variant)
            obs = svc.observe()
            svc.close()
            assert obs["sold"] + obs["remaining"] == 1 or variant != "atomic", obs
            worst = max(worst, obs["sold"])
    return worst


class ConcurrencyTest(unittest.TestCase):
    def test_reservation_never_oversells(self):
        self.assertEqual(race(VARIANT), 1)

    def test_check_then_act_oversells_under_the_counterexample_schedule(self):
        self.assertEqual(race("check-then-act", rounds=3), 2)


if __name__ == "__main__":
    if "--variant" in sys.argv:
        i = sys.argv.index("--variant")
        VARIANT = sys.argv[i + 1]
        del sys.argv[i:i + 2]
    unittest.main()
