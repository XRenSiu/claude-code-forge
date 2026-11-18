"""FM-Agent bug_validator probe B1: two buyers who both saw one remaining ticket both get it (check-then-act).

Runs from the repository root of the example (impl/) and loads the service through its public
entry point, the `tickets` module: TicketService and setup.
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.getcwd())
try:
    from tickets import TicketService, setup
    with tempfile.TemporaryDirectory() as tmp:
        db = str(Path(tmp) / "tickets.db")
        setup(db, 1)                                   # one ticket left
        svc = TicketService(db, ("alice", "bob"), "check-then-act")
        for user in ("alice", "bob"):
            svc.request(user)
        svc.read("alice")
        svc.read("bob")                                # both saw remaining = 1
        answers = [svc.purchase("alice"), svc.purchase("bob")]
        observed = svc.observe()
        svc.close()
    expected_sold = 1                                  # the spec: never more successes than the initial stock
    passed = observed["sold"] > expected_sold
except Exception as error:
    print("ERROR:", error)
    sys.exit(1)

if passed:
    print("CONFIRMED - answers %s, sold %d of 1, remaining %d" % (answers, observed["sold"], observed["remaining"]))
else:
    print("NOT CONFIRMED - sold %d of 1" % observed["sold"])
