#!/usr/bin/env python3
"""Durable local Docker pilot control. Never emits a formal accepted_for_stage.

Requests contain only binding + idempotency key. Contract, policy, task budgets,
collector commands and evidence are loaded from the operator's control directory.
The candidate has no mount of this directory and no control credentials.
"""
import argparse
from contextlib import contextmanager
import copy
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import sqlite3
import sys
import time
import uuid

from gate import evaluate, POLICY
from protocol import ATTEMPT, REQUEST, RESULT, digest, load, require, validate, validate_contract, ProtocolError


def parse_body(data):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, 'duplicate JSON key')
            value[key] = item
        return value
    def nonfinite(_):
        raise ProtocolError('non-finite JSON')
    value = json.loads(data, object_pairs_hook=unique, parse_constant=nonfinite)
    require(isinstance(value, dict), 'request body must be an object')
    return value


class Control:
    def __init__(self, directory):
        self.root = Path(directory).resolve()
        self.config = load(self.root / "control.json")
        require(self.config.get("schema_version") == 1 and self.config.get("mode") == "local-pilot", "only explicit local-pilot mode is supported; production publisher is a separate trust boundary")
        self.db = self.root / "control.sqlite"
        (self.root / "evidence").mkdir(parents=True, exist_ok=True)
        with self.transaction() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, project TEXT NOT NULL, revision INTEGER NOT NULL,
                    binding TEXT NOT NULL, specification TEXT NOT NULL, status TEXT NOT NULL, repairs INTEGER NOT NULL DEFAULT 0,
                    retries INTEGER NOT NULL DEFAULT 0, cost INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, principal TEXT NOT NULL, task TEXT NOT NULL,
                    key TEXT NOT NULL, digest TEXT NOT NULL, request TEXT NOT NULL, status TEXT NOT NULL,
                    fence INTEGER NOT NULL DEFAULT 0, lease_until INTEGER NOT NULL DEFAULT 0, worker TEXT,
                    result TEXT, created INTEGER NOT NULL, UNIQUE(principal, key));
                CREATE TABLE IF NOT EXISTS attempts (id TEXT PRIMARY KEY, task TEXT NOT NULL, run TEXT NOT NULL, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events (sequence INTEGER PRIMARY KEY AUTOINCREMENT, at INTEGER NOT NULL,
                    task TEXT NOT NULL, run TEXT, kind TEXT NOT NULL, data TEXT NOT NULL);
            ''')

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.db, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
        db.execute("BEGIN IMMEDIATE")
        try:
            yield db
            if db.in_transaction:
                db.commit()
        except BaseException:
            if db.in_transaction:
                db.rollback()
            raise
        finally:
            db.close()

    def event(self, db, task, run, kind, data):
        db.execute("INSERT INTO events(at,task,run,kind,data) VALUES (?,?,?,?,?)", (int(time.time()), task, run, kind, json.dumps(data)))

    def principal(self, token, role, project=None):
        hashed = hashlib.sha256(token.encode()).hexdigest()
        found = next((p for p in self.config["principals"] if secrets.compare_digest(p["token_sha256"], hashed)), None)
        require(found and role in found["roles"] and (project is None or project in found["projects"]), "unauthorized principal, role or project")
        return found["id"]

    def register(self, spec):
        """Operator CLI only. No HTTP route can approve a contract or change checks."""
        validate_contract(spec["contract"]); validate(spec["policy"], POLICY)
        binding = spec["binding"]
        validate({"schema_version": 1, "idempotency_key": "register", "binding": binding}, REQUEST)
        require(binding["contract_digest"] == digest(spec["contract"]) == spec["policy"]["contract_digest"], "contract digest mismatch")
        require(spec["contract"]["approval_ref"] == spec["policy"]["approval_ref"], "approval mismatch")
        for key in ("project_id", "task_id", "task_revision"):
            require(binding[key] == spec["contract"][key], "contract identity mismatch")
        for key in ("project_id", "stage", "adapter_digest", "check_bundle_digest"):
            require(binding[key] == spec["policy"][key], "policy identity mismatch")
        require(spec["authorization_expires_at"] > time.time() and spec["budget"]["deadline_at"] > time.time(), "expired authorization")
        require(spec["image"] == binding["artifact_digest"] and spec["image"].startswith("sha256:"), "candidate image must be pinned by inspected content ID")
        require(isinstance(spec["collector_argv"], list) and spec["collector_argv"], "collector argv required")
        require(spec.get("collector_files") and digest({f: hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in sorted(spec["collector_files"])}) == binding["check_bundle_digest"], "collector bundle differs from binding")
        require(all(Path(f).resolve().is_relative_to(self.root / 'bundle') and not Path(f).is_symlink() for f in spec['collector_files']), 'collector files must be frozen in the control bundle')
        require(len(spec['collector_argv']) >= 2 and Path(spec['collector_argv'][1]).resolve() in {Path(f).resolve() for f in spec['collector_files']} and Path(spec['collector_argv'][1]).is_absolute(), 'collector entry must be a declared frozen bundle file, not an interpreter expression or candidate path')
        require(type(spec.get('max_runs', 40)) is int and 1 <= spec.get('max_runs', 40) <= 1000, 'bounded max_runs required')
        recipe = {"candidate_argv": spec['candidate_argv'], "candidate_workdir": spec.get('candidate_workdir', '/app'), "collector_argv": spec['collector_argv'],
            'observer_image': spec['observer_image'],
            'worker_sha256': hashlib.sha256(Path(__file__).with_name('docker_worker.py').read_bytes()).hexdigest()}
        require(digest(recipe) == binding['adapter_digest'], 'adapter recipe binding mismatch')
        require(isinstance(spec['candidate_argv'], list) and spec['candidate_argv'] and all(isinstance(s, str) and s for s in spec['candidate_argv']), 'candidate argv required')
        task = binding["project_id"] + "/" + binding["task_id"]
        with self.transaction() as db:
            old = db.execute("SELECT * FROM tasks WHERE id=?", (task,)).fetchone()
            if old:
                require(binding["task_revision"] >= old["revision"], "revision cannot go backwards")
                previous = json.loads(old["specification"])
                if binding == json.loads(old["binding"]):
                    require(spec == previous, "same binding cannot change policy or budgets")
                    return task
                require(binding["task_revision"] > old["revision"], "new candidate or conditions require a new task revision")
                # A new candidate cannot reset cumulative usage or enlarge a running budget silently.
                require(spec["budget"] == previous["budget"], "task budget is immutable; start a separately authorized task")
                require(spec.get('max_runs', 40) == previous.get('max_runs', 40), 'run budget is immutable')
                require(old["repairs"] < spec["budget"]["max_code_repairs"], "code repair budget exhausted")
                db.execute("UPDATE tasks SET revision=?,binding=?,specification=?,status='active',repairs=repairs+1 WHERE id=?", (binding["task_revision"], json.dumps(binding), json.dumps(spec), task))
                db.execute("UPDATE runs SET status='obsolete',fence=fence+1 WHERE task=? AND status IN ('queued','running')", (task,))
            else:
                db.execute("INSERT INTO tasks(id,project,revision,binding,specification,status) VALUES (?,?,?,?,?,'active')", (task, binding["project_id"], binding["task_revision"], json.dumps(binding), json.dumps(spec)))
            self.event(db, task, None, "register", {"binding": binding, "specification_digest": digest(spec)})
        return task

    def submit(self, request, token):
        validate(request, REQUEST)
        principal = self.principal(token, "submit", request["binding"]["project_id"])
        task = request["binding"]["project_id"] + "/" + request["binding"]["task_id"]
        with self.transaction() as db:
            old = db.execute("SELECT * FROM runs WHERE principal=? AND key=?", (principal, request["idempotency_key"])).fetchone()
            if old:
                require(old["digest"] == digest(request), "idempotency conflict")
                return self.result_row(db, old)
            current = db.execute("SELECT * FROM tasks WHERE id=?", (task,)).fetchone()
            require(current and current["status"] == "active" and json.loads(current["binding"]) == request["binding"], "task inactive or binding not current")
            spec = json.loads(current["specification"])
            require(self.available(current, spec), "task authorization or cumulative budget exhausted")
            require(db.execute('SELECT count(*) FROM runs WHERE task=?', (task,)).fetchone()[0] < spec.get('max_runs', 40), 'task run budget exhausted')
            run = "run-" + uuid.uuid4().hex
            db.execute("INSERT INTO runs(id,principal,task,key,digest,request,status,created) VALUES (?,?,?,?,?,?,'queued',?)", (run, principal, task, request["idempotency_key"], digest(request), json.dumps(request), int(time.time())))
            self.event(db, task, run, "submitted", {"principal": principal})
            return self.result_row(db, db.execute("SELECT * FROM runs WHERE id=?", (run,)).fetchone())

    def available(self, task, spec):
        budget = spec["budget"]
        return (spec["authorization_expires_at"] > time.time() and budget["deadline_at"] > time.time() and
                task["repairs"] <= budget["max_code_repairs"] and task["retries"] <= budget["max_environment_retries"] and task["cost"] <= budget["max_cost_microunits"])

    def claim(self, token, project, lease_seconds=120):
        worker = self.principal(token, "collect", project)
        require(type(lease_seconds) is int and 5 <= lease_seconds <= 3600, "invalid lease duration")
        with self.transaction() as db:
            rows = db.execute("SELECT r.* FROM runs r JOIN tasks t ON r.task=t.id WHERE t.project=? AND t.status='active' AND (r.status='queued' OR (r.status='running' AND r.lease_until<=?)) ORDER BY r.created,r.id", (project, int(time.time()))).fetchall()
            for row in rows:
                task = db.execute("SELECT * FROM tasks WHERE id=?", (row["task"],)).fetchone()
                spec = json.loads(task["specification"])
                if not self.available(task, spec):
                    continue
                if row["status"] == "running":
                    if task["retries"] >= spec["budget"]["max_environment_retries"]:
                        continue
                    db.execute("UPDATE tasks SET retries=retries+1 WHERE id=?", (task["id"],))
                fence = row["fence"] + 1
                db.execute("UPDATE runs SET status='running',worker=?,fence=?,lease_until=? WHERE id=?", (worker, fence, int(time.time()) + lease_seconds, row["id"]))
                self.event(db, task["id"], row["id"], "leased", {"worker": worker, "fence": fence})
                return {"run_id": row["id"], "fence": fence, "request": json.loads(row["request"]), "specification": spec}
        return None

    def cancel(self, project, task_id, token):
        actor = self.principal(token, "cancel", project)
        task = project + "/" + task_id
        with self.transaction() as db:
            require(db.execute("SELECT id FROM tasks WHERE id=?", (task,)).fetchone(), "unknown task")
            db.execute("UPDATE tasks SET status='cancelled' WHERE id=?", (task,))
            db.execute("UPDATE runs SET status='obsolete',fence=fence+1 WHERE task=?", (task,))
            self.event(db, task, None, "cancelled", {"actor": actor})

    def complete(self, run_id, fence, token, attempt, cost_microunits):
        validate(attempt, ATTEMPT)
        require(type(cost_microunits) is int and cost_microunits >= 0, "collector must report measured cost; unknown cost cannot publish")
        worker = self.principal(token, "collect", attempt["binding"]["project_id"])
        with self.transaction() as db:
            row = db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
            require(row and row["status"] == "running" and row["worker"] == worker and row["fence"] == fence and row["lease_until"] > time.time(), "stale worker lease")
            task = db.execute("SELECT * FROM tasks WHERE id=?", (row["task"],)).fetchone()
            require(task["status"] == "active" and json.loads(task["binding"]) == attempt["binding"] == json.loads(row["request"])["binding"], "candidate superseded or cancelled")
            spec = json.loads(task["specification"])
            attempts = [json.loads(r["data"]) for r in db.execute("SELECT data FROM attempts WHERE task=? ORDER BY rowid", (task["id"],))]
            # Identity and sequence originate here, never in candidate JSON.
            attempt = copy.deepcopy(attempt)
            attempt["attempt_id"] = "attempt-" + uuid.uuid4().hex
            attempt["sequence"] = len(attempts) + 1
            attempts.append(attempt)
            environment_failure = int(any(c['failure_type'] == 'environment' for c in attempt['checks']))
            db.execute("UPDATE tasks SET cost=cost+?,retries=retries+? WHERE id=?", (cost_microunits, environment_failure, task["id"]))
            current = {"schema_version": 1, "run_id": run_id, "collector_id": worker, "request_digest": row["digest"], "binding": attempt["binding"],
                "task_status": task["status"], "authorization_expires_at": spec["authorization_expires_at"],
                "budget": {**spec["budget"], "code_repairs": task["repairs"], "environment_retries": task["retries"] + environment_failure, "cost_microunits": task["cost"] + cost_microunits},
                "attempt_manifest": [{"attempt_id": a["attempt_id"], "digest": digest(a)} for a in attempts]}
            case = {"contract": spec["contract"], "policy": spec["policy"], "current": current,
                    "run": {"schema_version": 1, "run_id": run_id, "collector_id": worker, "request_digest": row["digest"], "attempts": attempts}}
            decision = evaluate(case, self.root / "evidence")
            db.execute("INSERT INTO attempts(id,task,run,data) VALUES (?,?,?,?)", (attempt["attempt_id"], task["id"], run_id, json.dumps(attempt)))
            db.execute("UPDATE runs SET status='complete',result=? WHERE id=?", (json.dumps(decision), run_id))
            self.event(db, task["id"], run_id, "evaluated", {"decision": decision, "attempt_digest": digest(attempt)})
            # Transaction retains the current-task check through the decision commit.
            return decision

    def result_row(self, db, row):
        request = json.loads(row["request"])
        value = {"schema_version": 1, "run_id": row["id"], "request_digest": row["digest"], "binding": request["binding"],
            "state": row["status"] if row["status"] in ("queued", "running") else "complete", "verification_decision": "pending", "delivery_authorization": "not_granted",
            "checks": [], "evidence": [], "findings": [], "unverified": [], "reasons": []}
        task = db.execute("SELECT * FROM tasks WHERE id=?", (row["task"],)).fetchone()
        if row["status"] == "obsolete" or task["status"] != "active" or json.loads(task["binding"]) != request["binding"]:
            value.update(state="complete", verification_decision="obsolete", reasons=["Task cancelled or candidate superseded"])
        elif row["result"]:
            local = json.loads(row["result"])
            value["verification_decision"] = "blocked" if local["verification_decision"] == "eligible" else local["verification_decision"]
            value["reasons"] = ["Local Docker pilot; protected publication is not configured", *local["reasons"]]
            attempt = json.loads(db.execute("SELECT data FROM attempts WHERE run=? ORDER BY rowid DESC LIMIT 1", (row["id"],)).fetchone()["data"])
            for key in ("checks", "evidence", "findings", "unverified"):
                value[key] = attempt[key]
        validate(value, RESULT)
        return value

    def result(self, run, token, pilot=False):
        with self.transaction() as db:
            row = db.execute("SELECT * FROM runs WHERE id=?", (run,)).fetchone()
            require(row, "unknown run")
            principal = self.principal(token, "submit", json.loads(row["request"])["binding"]["project_id"])
            require(row["principal"] == principal, "foreign principal run")
            value = self.result_row(db, row)
            if pilot:
                value = {"protocol_result": value, "local_evaluation": json.loads(row["result"]) if row["result"] else None, "authority": "local_advisory"}
            return value


def serve(control, port):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(15)

        def log_message(self, *_):
            pass  # tokens, payloads and arbitrary candidate output never enter HTTP logs

        def do_GET(self):
            self.handle_request(False)

        def do_POST(self):
            self.handle_request(True)

        def handle_request(self, post):
            try:
                token = self.headers.get("Authorization", "").removeprefix("Bearer ")
                parts = self.path.strip('/').split('/')
                if post:
                    size = int(self.headers.get("Content-Length", "0"))
                    require(0 < size <= 2 * 1024 * 1024, "invalid body size")
                    data = parse_body(self.rfile.read(size))
                    if parts == ["runs"]:
                        require(self.headers.get("Idempotency-Key") == data.get("idempotency_key"), "idempotency header mismatch")
                        result = control.submit(data, token)
                    elif parts == ["cancel"]:
                        control.cancel(data["project_id"], data["task_id"], token); result = {"cancelled": True}
                    else:
                        raise ProtocolError("unknown endpoint")
                else:
                    require(len(parts) in (2, 3) and parts[0] == "runs" and (len(parts) == 2 or parts[2] == "pilot"), "unknown endpoint")
                    result = control.result(parts[1], token, len(parts) == 3)
                status = 200
            except (ProtocolError, ValueError, KeyError) as error:
                status = 409 if "idempotency conflict" in str(error) else 403 if "principal" in str(error) else 400
                result = {"error": str(error)}
            body = json.dumps(result).encode()
            self.send_response(status); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    with ThreadingHTTPServer(("127.0.0.1", port), Handler) as server:
        server.timeout = 15
        print(json.dumps({"endpoint": "http://127.0.0.1:" + str(server.server_port), "mode": "local-pilot"}), flush=True)
        server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["serve", "register"]); parser.add_argument("--control", required=True); parser.add_argument("--specification"); parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    control = Control(args.control)
    if args.action == "register":
        print(json.dumps({"task": control.register(load(args.specification))}))
    else:
        serve(control, args.port)
