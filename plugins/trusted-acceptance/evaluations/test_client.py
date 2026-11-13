import contextlib
import copy
import io
import json
import os
import tempfile
import unittest
import urllib.error
from email.message import Message
from pathlib import Path
from unittest.mock import patch

from demo import make_case
from protocol import (MAX_JSON_BYTES, REQUEST, ProtocolError, decode, digest, load,
                      validate, validate_contract, validate_result)
from acceptance import NoRedirect, endpoint_config, exchange, main, write_new


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.case, self.request = make_case(self.root / "evidence")
        self.config = {"schema_version": 1, "endpoint": "https://control.example.invalid/v1",
                       "token_env": "ACCEPTANCE_TEST_TOKEN", "timeout_seconds": 5}
        self.config_path = self.root / "control.json"
        self.config_path.write_text(json.dumps(self.config))
        self.request_path = self.root / "request.json"
        self.request_path.write_text(json.dumps(self.request))
        attempt = self.case["run"]["attempts"][0]
        self.result = {"schema_version": 1, "run_id": "run-1", "request_digest": digest(self.request),
                       "binding": copy.deepcopy(self.request["binding"]), "state": "complete",
                       "verification_decision": "accepted_for_stage", "delivery_authorization": "not_granted",
                       "checks": attempt["checks"], "evidence": attempt["evidence"], "findings": [],
                       "unverified": [], "reasons": ["All required checks verified by control endpoint"]}

    def invoke(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(list(args))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_request_and_contract_validators_accept_examples(self):
        validate(self.request, REQUEST)
        validate_contract(self.case["contract"])
        self.assertEqual(0, self.invoke("validate-request", str(self.request_path))[0])

    def test_strict_json_rejects_duplicates_nonfinite_oversize_and_wrong_types(self):
        for data in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}', b'\xff', b'[' * 2000,
                     b" " * (MAX_JSON_BYTES + 1)):
            with self.subTest(data=data[:20]), self.assertRaises(ProtocolError):
                decode(data)
        for mutate in (lambda r: r.update(schema_version=True), lambda r: r.update(approved=True),
                       lambda r: r["binding"].update(candidate_sha="main"),
                       lambda r: r["binding"].update(artifact_digest="sha256:placeholder")):
            request = copy.deepcopy(self.request)
            mutate(request)
            with self.assertRaises(ProtocolError):
                validate(request, REQUEST)

    def test_response_replay_and_invalid_state_block(self):
        for mutate in (lambda r: r.update(request_digest="sha256:" + "f" * 64),
                       lambda r: r["binding"].update(candidate_sha="f" * 40),
                       lambda r: r.update(state="running"), lambda r: r.update(checks=[]),
                       lambda r: r.update(evidence=[]),
                       lambda r: r["checks"][0].update(evidence_refs=[]),
                       lambda r: r.update(unverified=["missing capability"]),
                       lambda r: r.update(delivery_authorization="granted")):
            result = copy.deepcopy(self.result)
            mutate(result)
            with self.assertRaises(ProtocolError):
                validate_result(result, self.request)
        with self.assertRaises(ProtocolError):
            validate_result(self.result, self.request, "another-run")

    def test_https_config_and_token_required(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ProtocolError):
            endpoint_config(self.config_path)
        for endpoint in ("http://localhost/v1", "https://u:p@example.test", "https://example.test/?token=x", "https://example.test/#frag"):
            self.config_path.write_text(json.dumps(dict(self.config, endpoint=endpoint)))
            with patch.dict(os.environ, {"ACCEPTANCE_TEST_TOKEN": "synthetic-token"}), self.assertRaises(ProtocolError):
                endpoint_config(self.config_path)

    def test_redirects_never_forward_credentials(self):
        with self.assertRaises(ProtocolError):
            NoRedirect().redirect_request(None, None, 302, None, None, "https://other.example")

    def test_transport_carries_idempotency_key_and_caps_reads(self):
        headers = Message()
        headers["Content-Type"] = "application/json"

        class Response(io.BytesIO):
            status = 202

        response = Response(json.dumps(self.result).encode())
        response.headers = headers
        with patch("acceptance.urllib.request.build_opener") as build:
            build.return_value.open.return_value = response
            returned = exchange(self.config, "synthetic-token", "POST", "/runs", self.request, self.request["idempotency_key"])
            req = build.return_value.open.call_args.args[0]
            self.assertEqual("Bearer synthetic-token", req.get_header("Authorization"))
            self.assertEqual(self.request["idempotency_key"], req.get_header("Idempotency-key"))
            self.assertEqual(self.request, json.loads(req.data))
            self.assertEqual(self.result, returned)

    def test_transport_errors_do_not_print_tokens_or_server_body(self):
        with patch("acceptance.urllib.request.build_opener") as build:
            build.return_value.open.side_effect = urllib.error.HTTPError("https://secret-url", 403, "synthetic-token", {}, None)
            with self.assertRaisesRegex(ProtocolError, "control HTTP 403") as error:
                exchange(self.config, "synthetic-token", "GET", "/runs/run-1")
            self.assertNotIn("synthetic-token", str(error.exception))
            self.assertNotIn("secret-url", str(error.exception))

    def test_submit_pending_is_saved_with_exit_three_and_stable_request(self):
        pending = dict(self.result, state="queued", verification_decision="pending", checks=[], evidence=[])
        output = self.root / "receipt.json"
        with patch.dict(os.environ, {"ACCEPTANCE_TEST_TOKEN": "synthetic-token"}), patch("acceptance.exchange", return_value=pending) as transport:
            code, _, _ = self.invoke("submit", "--request", str(self.request_path), "--config", str(self.config_path), "--output", str(output))
            self.assertEqual(3, code)
            self.assertEqual(pending, load(output))
            self.assertEqual(self.request["idempotency_key"], transport.call_args.args[5])
            # Existing receipt must be preserved and no second network call issued.
            code, _, _ = self.invoke("submit", "--request", str(self.request_path), "--config", str(self.config_path), "--output", str(output))
            self.assertEqual(4, code)
            self.assertEqual(1, transport.call_count)

    def test_get_result_checks_run_binding_and_maps_exit_codes(self):
        args = ("get-result", "--request", str(self.request_path), "--config", str(self.config_path), "--run-id", "run-1")
        with patch.dict(os.environ, {"ACCEPTANCE_TEST_TOKEN": "synthetic-token"}), patch("acceptance.exchange", return_value=self.result):
            self.assertEqual(0, self.invoke(*args)[0])
            self.result["verification_decision"] = "blocked"
            self.assertEqual(2, self.invoke(*args)[0])
            self.result["run_id"] = "wrong-run"
            self.assertEqual(4, self.invoke(*args)[0])

    def test_no_shell_or_path_input_via_run_id(self):
        with patch.dict(os.environ, {"ACCEPTANCE_TEST_TOKEN": "synthetic-token"}), patch("acceptance.exchange") as transport:
            code, _, _ = self.invoke("get-result", "--request", str(self.request_path), "--config", str(self.config_path), "--run-id", "../run;touch-file")
            self.assertEqual(4, code)
            transport.assert_not_called()

    def test_write_never_overwrites_history(self):
        output = self.root / "history.json"
        write_new(output, self.result)
        with self.assertRaises(FileExistsError):
            write_new(output, {})
        self.assertEqual(self.result, load(output))


if __name__ == "__main__":
    unittest.main()
