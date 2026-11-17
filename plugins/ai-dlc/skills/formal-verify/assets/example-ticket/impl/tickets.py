"""Ticket ordering service — the REAL code the model talks about (sqlite3, standard library).

Two purchase implementations exist on purpose:
- "atomic"          reserve with one conditional UPDATE inside an IMMEDIATE transaction
                    (the fixed design; source-map.yaml anchors model action `buy` here);
- "check-then-act"  decrement based on the value the user saw at read time (the original
                    design). It is kept so the example can show that trace conformance and the
                    concurrency test catch the defect in code, not only in the model.
"""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (event_id INTEGER PRIMARY KEY, remaining INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS requests (user TEXT PRIMARY KEY, status TEXT NOT NULL, seen INTEGER);
CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT NOT NULL, status TEXT NOT NULL);
"""
EVENT = 1


def connect(path):
    db = sqlite3.connect(path, isolation_level=None, timeout=30, check_same_thread=False)
    db.execute("PRAGMA journal_mode=WAL")
    return db


def setup(path, stock):
    db = connect(path)
    db.executescript(SCHEMA)
    db.execute("INSERT OR REPLACE INTO tickets (event_id, remaining) VALUES (?, ?)", (EVENT, stock))
    db.close()


class TicketService:
    def __init__(self, path, users, variant="atomic"):
        if variant not in ("atomic", "check-then-act"):
            raise ValueError("unknown variant " + variant)
        self.db, self.users, self.variant = connect(path), tuple(users), variant

    def request(self, user):
        self.db.execute("INSERT OR IGNORE INTO requests (user, status, seen) VALUES (?, 'pending', NULL)", (user,))

    def read(self, user):
        (remaining,) = self.db.execute("SELECT remaining FROM tickets WHERE event_id = ?", (EVENT,)).fetchone()
        self.db.execute("UPDATE requests SET seen = ? WHERE user = ?", (remaining, user))
        return remaining

    def purchase(self, user):
        if self.variant == "check-then-act":
            return self._purchase_check_then_act(user)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute("SELECT status FROM requests WHERE user = ?", (user,)).fetchone()
            if row is None or row[0] != "pending":   # idempotent retry: a repeated purchase returns the first answer
                self.db.execute("COMMIT")
                return row[0] if row else "no_request"
            reserved = self.db.execute(
                "UPDATE tickets SET remaining = remaining - 1 WHERE event_id = ? AND remaining > 0", (EVENT,)).rowcount
            status = "success" if reserved == 1 else "sold_out"
            if reserved == 1:
                self.db.execute("INSERT INTO orders (user, status) VALUES (?, 'success')", (user,))
            self.db.execute("UPDATE requests SET status = ? WHERE user = ?", (status, user))
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        return status

    def _purchase_check_then_act(self, user):
        (seen,) = self.db.execute("SELECT seen FROM requests WHERE user = ?", (user,)).fetchone()
        if seen is not None and seen > 0:
            self.db.execute("UPDATE tickets SET remaining = remaining - 1 WHERE event_id = ?", (EVENT,))
            self.db.execute("INSERT INTO orders (user, status) VALUES (?, 'success')", (user,))
            self.db.execute("UPDATE requests SET status = 'success' WHERE user = ?", (user,))
            return "success"
        self.db.execute("UPDATE requests SET status = 'sold_out' WHERE user = ?", (user,))
        return "sold_out"

    def observe(self):
        """The contract's observables, read from the database (not from the code's own claims)."""
        (sold,) = self.db.execute("SELECT COUNT(*) FROM orders WHERE status = 'success'").fetchone()
        (remaining,) = self.db.execute("SELECT remaining FROM tickets WHERE event_id = ?", (EVENT,)).fetchone()
        status = dict(self.db.execute("SELECT user, status FROM requests").fetchall())
        return {"sold": sold, "remaining": remaining, "outcome": {u: status.get(u, "none") for u in self.users}}

    def close(self):
        self.db.close()
