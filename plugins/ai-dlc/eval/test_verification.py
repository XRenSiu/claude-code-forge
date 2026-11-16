"""Behavioral tests over real temporary Git projects and a local HTTPS control fixture.

The fixture is not a protected acceptance deployment. It exercises the client,
wire protocol, lifecycle binding and refusal paths without external credentials.
"""
import copy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import ssl
import subprocess
import sys
import tempfile
import threading
import unittest

import yaml

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "skills/ai-dlc/scripts"))
import verification as v
import aidlc_state as state
from compile_acceptance import compile_proposal, validate_proposal

HARNESS = Path(os.environ.get("AIDLC_TEST_HARNESS_SOURCE", str(PLUGIN.parent / "project-harness/skills/bootstrap-project-harness")))
TRUSTED = Path(os.environ.get("AIDLC_TEST_ACCEPTANCE_SOURCE", str(PLUGIN.parent / "trusted-acceptance/skills/accept-change/scripts")))


class ControlFixture:
    def __init__(self, cert, key):
        self.request = None
        self.mode = "accepted_for_stage"
        self.calls = []
        fixture = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def handle_request(self):
                fixture.calls.append(self.command)
                if self.headers.get("Authorization") != "Bearer fixture-token":
                    self.send_error(401)
                    return
                if fixture.mode == "http_error":
                    self.send_error(503)
                    return
                if self.command == "POST":
                    request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                    assert self.headers["Idempotency-Key"] == request["idempotency_key"]
                    fixture.request = request
                result = fixture.result()
                body = json.dumps(result).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            do_POST = handle_request
            do_GET = handle_request

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, key)
        self.server.socket = context.wrap_socket(self.server.socket, server_side=True)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def result(self):
        decision = "accepted_for_stage" if self.mode == "missing_baseline" else self.mode
        checks, evidence = [], []
        if decision != "pending":
            for key in (["behavior"] if self.mode == "missing_baseline" else ["behavior", "baseline"]):
                checks.append({"id": key, "status": "fail" if decision == "needs_repair" else "pass",
                               "requirement_ids": ["AC-1-http"] if key == "behavior" else [],
                               "failure_type": "implementation" if decision == "needs_repair" else "none",
                               "expected": "good", "observed": "bad" if decision == "needs_repair" else "good",
                               "reproduction_ref": "fixture", "evidence_refs": [key + "-evidence"]})
                evidence.append({"id": key + "-evidence", "check_id": key, "type": "json",
                                 "path": key + ".json", "digest": "sha256:" + "a" * 64, "size_bytes": 4})
        return {"schema_version": 1, "run_id": "run-example", "request_digest": v.digest(self.request),
                "binding": self.request["binding"], "state": "running" if decision == "pending" else "complete",
                "verification_decision": decision, "delivery_authorization": "not_granted", "checks": checks,
                "evidence": evidence, "findings": [], "unverified": [], "reasons": []}


class VerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shared = tempfile.TemporaryDirectory(prefix="aidlc-control-test-")
        root = Path(cls.shared.name)
        cls.cert, cls.key = root / "cert.pem", root / "key.pem"
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1",
                        "-subj", "/CN=localhost", "-addext", "subjectAltName=DNS:localhost",
                        "-keyout", str(cls.key), "-out", str(cls.cert)], check=True, capture_output=True)
        cls.client = root / "client"
        cls.client.mkdir()
        for name in ("acceptance.py", "protocol.py"):
            shutil.copyfile(TRUSTED / name, cls.client / name)

    @classmethod
    def tearDownClass(cls):
        cls.shared.cleanup()

    def setUp(self):
        self.previous_cwd, self.previous_env = Path.cwd(), dict(os.environ)
        self.temp = tempfile.TemporaryDirectory(prefix="aidlc-verification-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root, self.runtime = self.base / "project", self.base / "project/.aidlc"
        self.root.mkdir()
        os.chdir(self.root)
        self.addCleanup(os.chdir, self.previous_cwd)
        self.addCleanup(self.restore_env)
        os.environ.pop("AIDLC_VERIFICATION_CONFIG", None)
        os.environ["AIDLC_TEST_API_TOKEN"] = "fixture-token"
        os.environ["SSL_CERT_FILE"] = str(self.cert)
        os.environ["AIDLC_TEST_BEHAVIOR"] = "pass"
        self.git("init", "-q")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "user.name", "Verification Fixture")
        self.git("config", "commit.gpgsign", "false")
        (self.root / ".gitignore").write_text(".aidlc/\n")
        (self.root / "source.txt").write_text("good\n")
        self.document = {"schema": 2, "acceptance": [{"id": "AC-1", "kind": "mechanical", "req": "REQ-1", "observe": "cli:read", "given": {}, "expect": {"value": "good"}}]}
        self.dw = self.root / "done_when.yaml"
        self.dw.write_text(yaml.safe_dump(self.document))
        self.git("add", ".")
        self.git("commit", "-qm", "initial fixture")
        self.st = v.migrate({"version": 2, "slug": "example", "title": "Example", "track": "task", "stage": "intake",
                             "gates": {"g3": {"required": True}}, "counters": {}, "artifacts": {},
                             "contract": {"done_when": str(self.dw)}, "pending": {"failure_report": False}})
        (self.runtime / "example").mkdir(parents=True)
        self.mapping = {"schema_version": 1, "project_id": "example", "task_id": "example", "task_revision": 1,
                        "contract_id": "contract-example", "request_ref": "issue:1", "product_rules_ref": "rules:1",
                        "criteria": [{"id": "AC-1-http", "source_ref": "issue:1#AC-1", "given": "the fixture exists",
                                      "when": "read its value", "expected": "good", "check_id": "behavior",
                                      "evidence_types": ["json"], "scope": "the fixture", "method": "read the value",
                                      "ac_ids": ["AC-1"], "local_check_ids": ["behavior"], "obligations": []}]}

    def restore_env(self):
        os.environ.clear()
        os.environ.update(self.previous_env)

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, stderr=subprocess.PIPE, text=True).strip()

    def write(self, name, payload):
        path = self.base / name
        path.write_text(json.dumps(payload))
        return path

    def enroll(self, harness=False, trusted=False):
        config = {"schema_version": 1, "project_id": "example", "artifacts_dir": str(self.base / "artifacts"), "harness": None, "trusted": None}
        if harness:
            self.bootstrap()
            config["harness"] = {"manifest": ".harness/project.json", "runner": "scripts/project-verify.mjs", "node": "node",
                                 "environment_keys": ["AIDLC_TEST_BEHAVIOR"], "timeout_seconds": 20, "required_stages": ["pr", "merge"]}
        if trusted:
            self.control = ControlFixture(self.cert, self.key)
            self.addCleanup(self.control.close)
            control = self.write("control.json", {"schema_version": 1, "endpoint": "https://localhost:" + str(self.control.server.server_port),
                                                  "token_env": "AIDLC_TEST_API_TOKEN", "timeout_seconds": 3})
            config["trusted"] = {"client": str(self.client / "acceptance.py"), "control_config": str(control),
                                 "required_stages": ["merge", "release"], "baseline_check_ids": ["baseline"],
                                 **{key: "sha256:" + "b" * 64 for key in ("check_bundle_digest", "adapter_digest", "environment_digest")}}
        self.config_path = self.write("integration.json", config)
        v.configure(self.st, self.config_path)
        return config

    def bootstrap(self):
        script = """
          const {pathToFileURL} = await import('node:url');
          const base=process.argv[1];
          const {bootstrap}=await import(pathToFileURL(base+'/scripts/lib/bootstrap.mjs'));
          const {apply}=await import(pathToFileURL(base+'/scripts/lib/apply.mjs'));
          const root=process.argv[2];
          const code="const fs=require('node:fs');const ok=process.env.AIDLC_TEST_BEHAVIOR==='pass' && fs.readFileSync('source.txt','utf8').trim()==='good';console.log(JSON.stringify({schema_version:1,complete:true,examined:1,claims:[{id:'behavior',status:ok?'PASS':'FAIL'}]}));process.exitCode=ok?0:1";
          const check={id:'behavior',executable:'node',argv:['-e',code],cwd:'.',reporter:'claims-json',expected_claims:['behavior'],depends_on:[],timeout_ms:3000,required:true,effects:'temporary-artifacts'};
          const {plan}=bootstrap(root,{host:'portable',authorizationRef:'temporary test fixture',checks:[check]});
          apply(root,plan,{stateDir:process.argv[3],acceptedDigest:plan.digest});
        """
        result = subprocess.run(["node", "--input-type=module", "-e", script, str(HARNESS), str(self.root), str(self.base / "apply")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.git("add", ".")
        self.git("commit", "-qm", "bootstrap fixture")

    def prepare(self, stage="merge"):
        proposal = compile_proposal(self.dw, self.mapping)
        contract = {**proposal["contract"], "approval_ref": "fixture-approval"}
        artifact = self.base / "candidate.bin"
        artifact.write_bytes(b"built candidate")
        config = v.configuration(self.st)
        request = {"schema_version": 1, "idempotency_key": "fixture-" + stage,
                   "binding": {"project_id": "example", "task_id": "example", "task_revision": 1,
                               "candidate_sha": self.git("rev-parse", "HEAD"), "artifact_digest": v.file_digest(artifact),
                               "contract_digest": v.digest(contract), "stage": stage,
                               **{key: config["trusted"][key] for key in ("check_bundle_digest", "adapter_digest", "environment_digest")}}}
        self.request_path = self.write("request.json", request)
        self.contract_path = self.write("contract.json", contract)
        self.proposal_path = self.write("proposal.json", proposal)
        self.artifact = artifact
        return v.prepare(self.st, self.runtime, self.request_path, self.contract_path, self.proposal_path, artifact)

    def test_legacy_migration_does_not_invent_trusted_acceptance(self):
        st = v.migrate({"version": 1, "slug": "old", "acceptance": {"evaluation_result": "old.json"}})
        self.assertEqual(st["verification"]["review"]["status"], "legacy_local")
        self.assertEqual(st["verification"]["trusted"]["status"], "not_configured")
        self.assertEqual(st["version"], 2)

    def test_feature_mapping_binds_index_and_check_without_inventing_approval(self):
        index = {"schema_version": 1, "features": [{"id": "access", "entries": [{"id": "http", "check_id": "behavior", "claims": ["denied"]}]}]}
        (self.root / 'features.json').write_text(json.dumps(index))
        self.mapping['feature_index'] = 'features.json'
        self.mapping['criteria'][0]['feature_entries'] = ['access/http']
        proposal = compile_proposal(self.dw, self.mapping)
        self.assertEqual(proposal['feature_index_digest'], v.digest(index))
        self.assertEqual(proposal['unmapped_feature_entries'], [])
        self.assertEqual(proposal['authority'], 'proposal_only')
        self.assertNotIn('approval_ref', proposal['contract'])
        self.mapping['criteria'][0]['local_check_ids'] = ['wrong']
        with self.assertRaisesRegex(ValueError, 'local_check_ids'):
            compile_proposal(self.dw, self.mapping)

    def test_minimal_done_and_bad_completeness_are_rejected(self):
        for document in ({"state_decision": "DONE"}, {"state_decision": "DONE", "unevaluated_reviews": ""}, []):
            with self.subTest(document=document), self.assertRaises(v.VerificationError):
                v.review_issues(document)
        self.assertEqual(v.review_issues({"state_decision": "DONE", "unevaluated_reviews": []}), "DONE")

    def test_actual_harness_success_and_environment_invalidation(self):
        self.enroll(harness=True)
        result = v.run_harness(self.st, self.runtime)
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(v.guard(self.st, self.runtime, "pr"), [])
        os.environ["AIDLC_TEST_BEHAVIOR"] = "fail"
        self.assertTrue(v.guard(self.st, self.runtime, "pr"))
        self.assertEqual(v.run_harness(self.st, self.runtime)["status"], "failed")

    def test_candidate_and_runtime_changes_invalidate_receipt(self):
        self.enroll(harness=True)
        self.assertEqual(v.run_harness(self.st, self.runtime)["status"], "passed")
        (self.root / ".harness/runtime/core.mjs").write_text((self.root / ".harness/runtime/core.mjs").read_text() + "\n// runtime update\n")
        self.assertTrue(v.guard(self.st, self.runtime, "pr"))
        self.assertEqual(v.run_harness(self.st, self.runtime)["status"], "passed")
        (self.root / "source.txt").write_text("bad\n")
        self.assertTrue(v.guard(self.st, self.runtime, "pr"))
        self.assertEqual(v.run_harness(self.st, self.runtime)["status"], "failed")

    def test_missing_skip_and_duplicate_checks_never_pass(self):
        self.enroll(harness=True)
        record = v.run_harness(self.st, self.runtime)
        receipt = v.read_json(record["receipt_ref"])
        manifest = v.read_json(self.root / ".harness/project.json")
        for status in ("FAIL", "NOT_APPLICABLE", "NOT_RUN", "UNKNOWN", "ERROR"):
            changed = copy.deepcopy(receipt)
            changed["results"][0]["status"] = status
            self.assertTrue(v.receipt_issues(changed, manifest), status)
        for results in ([], receipt["results"] * 2):
            with self.assertRaises(v.VerificationError):
                v.receipt_issues({**receipt, "results": results}, manifest)

    def test_mutated_receipt_and_review_are_stale(self):
        self.enroll(harness=True)
        record = v.run_harness(self.st, self.runtime)
        Path(record["receipt_ref"]).write_text("{}")
        self.assertTrue(v.guard(self.st, self.runtime, "pr"))
        review = self.write("review.json", {"state_decision": "DONE", "unevaluated_reviews": [], "input_binding": v.source(self.st, self.runtime)})
        v.record_review(self.st, self.runtime, review)
        self.st["acceptance"] = {"evaluation_result": str(review)}
        review.write_text("{}")
        self.assertTrue(any("review" in x for x in v.guard(self.st, self.runtime, "pr")))

    def test_old_review_cannot_be_relabelled_for_new_candidate(self):
        self.enroll()
        review = self.write("review.json", {"state_decision": "DONE", "unevaluated_reviews": [], "input_binding": v.source(self.st, self.runtime)})
        v.record_review(self.st, self.runtime, review)
        self.git("commit", "--allow-empty", "-qm", "new review candidate")
        with self.assertRaisesRegex(v.VerificationError, "input_binding"):
            v.record_review(self.st, self.runtime, review)

    def test_configuration_cannot_move_inside_candidate_or_drift(self):
        self.enroll()
        moved = self.root / "integration.json"
        moved.write_text(self.config_path.read_text())
        with self.assertRaises(v.VerificationError):
            v.configure(self.st, moved)
        self.config_path.write_text(self.config_path.read_text() + "\n")
        self.assertTrue(v.guard(self.st, self.runtime, "merge"))

    def test_approved_contract_preserves_explicit_mapping(self):
        proposal = compile_proposal(self.dw, self.mapping)
        self.assertTrue(proposal["ready_for_approval"])
        self.assertNotIn("approval_ref", proposal["contract"])
        contract = {**proposal["contract"], "approval_ref": "fixture-approval"}
        validate_proposal(proposal, self.dw, contract)
        changed = copy.deepcopy(contract)
        changed["criteria"][0]["expected"] = "different"
        with self.assertRaises(v.VerificationError):
            validate_proposal(proposal, self.dw, changed)

    def test_thresholds_constraints_and_human_ac_cannot_disappear(self):
        self.document.update(behavior={"thresholds": {"unit_coverage": ">= 0.8"}}, constraints={"structure": {"complexity": 10}}, rules=["no P0"])
        self.document["acceptance"].append({"id": "AC-human", "kind": "human", "statement": "review appearance"})
        self.dw.write_text(yaml.safe_dump(self.document))
        proposal = compile_proposal(self.dw, self.mapping)
        self.assertFalse(proposal["ready_for_approval"])
        problems = " ".join(proposal["contract"]["unresolved_questions"])
        for text in ("threshold:unit_coverage", "structure:complexity", "rule:0", "AC-human", "attestation"):
            self.assertIn(text, problems)

    def test_one_ac_can_map_to_multiple_checks(self):
        second = copy.deepcopy(self.mapping["criteria"][0])
        second.update(id="AC-1-ui", check_id="ui")
        self.mapping["criteria"].append(second)
        proposal = compile_proposal(self.dw, self.mapping)
        self.assertEqual(proposal["contract"]["required_check_ids"], ["behavior", "ui"])
        self.assertEqual(len(proposal["coverage"]), 2)

    def test_source_change_invalidates_proposal(self):
        proposal = compile_proposal(self.dw, self.mapping)
        self.dw.write_text(self.dw.read_text() + "\n# revision\n")
        with self.assertRaises(v.VerificationError):
            validate_proposal(proposal, self.dw, {**proposal["contract"], "approval_ref": "fixture-approval"})

    def test_compiler_dependency_error_is_actionable_and_json_needs_no_yaml(self):
        compiler = PLUGIN / "skills/ai-dlc/scripts/compile_acceptance.py"
        mapping = self.write("mapping.json", self.mapping)
        command = [sys.executable, "-S", str(compiler), "--done-when", str(self.dw), "--mapping", str(mapping), "--out", str(self.base / "compiled.json")]
        missing = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(missing.returncode, 2)
        self.assertIn("PyYAML", missing.stderr)
        self.assertNotIn("Traceback", missing.stderr)
        self.dw.write_text(json.dumps(self.document))
        valid = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(valid.returncode, 0, valid.stderr)

    def test_cli_mutations_wait_for_the_writer_lock(self):
        state.save(str(self.runtime), "example", self.st)
        script = "import sys;sys.path.insert(0,sys.argv[1]);import verification as v\nwith v.writer_lock(sys.argv[2]):\n print('locked',flush=True)\n sys.stdin.readline()\n"
        holder = subprocess.Popen([sys.executable, "-c", script, str(PLUGIN / "skills/ai-dlc/scripts"), str(self.runtime)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(holder.stdout.readline().strip(), "locked")
            command = [sys.executable, str(PLUGIN / "skills/ai-dlc/scripts/aidlc_state.py"), "verification", "task", "--root", str(self.runtime), "--slug", "example", "--task-status", "cancelled", "--reason", "test serialization"]
            mutation = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                with self.assertRaises(subprocess.TimeoutExpired):
                    mutation.communicate(timeout=0.2)
                holder.communicate("release\n", timeout=5)
                stdout, stderr = mutation.communicate(timeout=5)
                self.assertEqual(mutation.returncode, 0, stderr)
                self.assertEqual(json.loads(stdout)["status"], "cancelled")
            finally:
                if mutation.poll() is None:
                    mutation.kill()
                    mutation.communicate()
        finally:
            if holder.poll() is None:
                holder.kill()
                holder.communicate()

    def test_real_https_client_submit_poll_and_final_refresh(self):
        self.enroll(trusted=True)
        record = self.prepare()
        self.control.mode = "pending"
        first = v.refresh(self.st, self.runtime, "merge", submit=True)
        self.assertEqual(first["status"], "pending")
        self.control.mode = "accepted_for_stage"
        self.assertEqual(v.refresh(self.st, self.runtime, "merge")["status"], "accepted")
        self.assertEqual(v.guard(self.st, self.runtime, "merge"), [])
        self.assertEqual(self.control.calls, ["POST", "GET", "GET"])
        self.assertEqual(record["delivery_authorization"], "not_granted")
        self.assertEqual(len(list(Path(record["history_ref"]).glob("result-*.json"))), 3)

    def test_same_binding_retry_must_keep_idempotency_key(self):
        self.enroll(trusted=True)
        first = self.prepare()
        self.assertIs(self.prepare(), first)
        request = v.read_json(self.request_path)
        request["idempotency_key"] = "changed-key"
        self.request_path.write_text(json.dumps(request))
        with self.assertRaises(v.VerificationError):
            v.prepare(self.st, self.runtime, self.request_path, self.contract_path, self.proposal_path, self.artifact)

    def test_missing_required_baseline_blocks_remote_success(self):
        self.enroll(trusted=True)
        self.prepare()
        self.control.mode = "missing_baseline"
        with self.assertRaisesRegex(v.VerificationError, "missing required"):
            v.refresh(self.st, self.runtime, "merge", submit=True)
        self.assertEqual(self.st["verification"]["trusted"]["runs"]["merge"]["authority"], "not_granted")

    def test_failed_refresh_revokes_cached_success(self):
        self.enroll(trusted=True)
        self.prepare()
        self.assertEqual(v.refresh(self.st, self.runtime, "merge", submit=True)["status"], "accepted")
        self.control.mode = "http_error"
        self.assertTrue(v.guard(self.st, self.runtime, "merge"))
        record = self.st["verification"]["trusted"]["runs"]["merge"]
        self.assertEqual(record["status"], "blocked")
        self.assertEqual(record["decision"], "blocked")
        self.assertEqual(record["last_remote_decision"], "accepted_for_stage")
        self.assertNotEqual(record["route"]["action"], "continue_stage")

    def test_artifact_change_and_wrong_stage_invalidate_success(self):
        self.enroll(trusted=True)
        self.prepare()
        v.refresh(self.st, self.runtime, "merge", submit=True)
        self.assertTrue(v.guard(self.st, self.runtime, "release"))
        state.save(str(self.runtime), "example", self.st)
        result = subprocess.run([sys.executable, str(PLUGIN / "skills/ai-dlc/scripts/aidlc_state.py"), "verification", "check", "--stage", "release", "--root", str(self.runtime), "--slug", "example"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout)["trusted_status"], "not_requested")
        self.artifact.write_bytes(b"changed build")
        self.assertTrue(v.guard(self.st, self.runtime, "merge"))

    def test_dirty_candidate_cannot_be_sent(self):
        self.enroll(trusted=True)
        (self.root / "source.txt").write_text("changed")
        with self.assertRaisesRegex(v.VerificationError, "clean committed"):
            self.prepare()
        self.assertEqual(self.control.calls, [])

    def test_commit_and_task_revision_invalidate_old_request(self):
        self.enroll(trusted=True)
        self.prepare()
        v.refresh(self.st, self.runtime, "merge", submit=True)
        self.git("commit", "--allow-empty", "-qm", "new candidate")
        self.assertTrue(v.guard(self.st, self.runtime, "merge"))
        v.task_update(self.st, "active", 2, "requirements revised")
        self.assertEqual(self.st["verification"]["trusted"]["runs"]["merge"]["status"], "obsolete")

    def test_cancelled_task_does_not_poll_or_advance(self):
        self.enroll(trusted=True)
        self.prepare()
        v.refresh(self.st, self.runtime, "merge", submit=True)
        v.task_update(self.st, "cancelled", 1, "cancel fixture")
        self.assertEqual(self.st["verification"]["trusted"]["runs"]["merge"]["decision"], "obsolete")
        self.assertEqual(self.st["verification"]["trusted"]["runs"]["merge"]["route"]["action"], "archive_only")
        self.assertEqual(v.refresh(self.st, self.runtime, "merge")["status"], "obsolete")
        self.assertEqual(self.control.calls, ["POST"])
        self.assertTrue(v.guard(self.st, self.runtime, "merge"))
        with self.assertRaises(v.VerificationError):
            v.task_update(self.st, "active", 1, "reuse identity")

    def test_sizing_and_force_cannot_waive_configured_gate(self):
        self.enroll(trusted=True)
        self.st.update(intake={"size": "S", "size_source": "derived"}, acceptance={"skipped_reason": "tiny change"})
        state.save(str(self.runtime), "example", self.st)
        result = subprocess.run([sys.executable, str(PLUGIN / "skills/ai-dlc/scripts/aidlc_state.py"), "advance", "merge", "--root", str(self.runtime), "--slug", "example", "--force", "--reason", "test waiver"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertFalse(json.loads(result.stdout)["force_allowed"])
        self.assertEqual(state.load(str(self.runtime), "example")["stage"], "intake")

    def test_review_verdict_is_bound_to_current_head(self):
        watch = self.runtime / "pr-watch"
        watch.mkdir()
        path = watch / "pr-17.done.json"
        self.st.update(pr={"number": 17}, review={"done": "done"})
        path.write_text(json.dumps({"pr": 17, "exit": 0, "head_sha": self.git("rev-parse", "HEAD")}))
        self.assertEqual(state.review_evidence_unmet(self.st, str(self.runtime)), [])
        self.git("commit", "--allow-empty", "-qm", "later review candidate")
        self.assertTrue(state.review_evidence_unmet(self.st, str(self.runtime)))

    def test_failure_domains_preserve_code_budget(self):
        self.assertTrue(v.route("needs_repair")["consumes_code_budget"])
        for decision in ("infrastructure_blocked", "checker_blocked", "blocked", "obsolete", "pending", "needs_review"):
            self.assertFalse(v.route(decision)["consumes_code_budget"])


if __name__ == "__main__":
    unittest.main()
