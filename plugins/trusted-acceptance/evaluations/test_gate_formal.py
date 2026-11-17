#!/usr/bin/env python3
"""Gate + formal evidence: the approved policy pins the model/contract and the evidence level.

A candidate can only satisfy a formal requirement with fv evidence for exactly the approved
model and contract, at or above the required level, bound to the candidate under test; with
`rerun` the gate re-decides qualification and trace conformance from the raw files.
"""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from demo import make_case, refresh_manifest  # noqa: E402
from gate import evaluate  # noqa: E402
from fvkit.qualify import conform, qualify  # noqa: E402
from fvkit.receipt import make  # noqa: E402
from fvkit.spec import Contract, Model  # noqa: E402
from fvkit.trace import check_files  # noqa: E402
from test_formal import BUGGY, CONTRACT, ticket_model  # noqa: E402

GOOD_TRACE = [
    {"kind": "fv-trace", "schema_version": 1, "model": "ticket"},
    {"init": True, "observed": {"sold": 0, "remaining": 1, "outcome": {"alice": "none", "bob": "none"}}},
    {"action": "request", "params": {"u": "alice"}, "observed": {"outcome": {"alice": "pending", "bob": "none"}}},
    {"action": "read", "params": {"u": "alice"}, "observed": {"remaining": 1}},
    {"action": "request", "params": {"u": "bob"}, "observed": {"outcome": {"alice": "pending", "bob": "pending"}}},
    {"action": "read", "params": {"u": "bob"}, "observed": {"remaining": 1}},
    {"action": "buy", "params": {"u": "alice"}, "observed": {"sold": 1, "remaining": 0, "outcome": {"alice": "success", "bob": "pending"}}},
    {"action": "buy", "params": {"u": "bob"}, "rejected": True, "observed": {"sold": 1, "remaining": 0}},
    {"action": "reject", "params": {"u": "bob"}, "observed": {"sold": 1, "remaining": 0, "outcome": {"alice": "success", "bob": "sold_out"}}},
]
BAD_TRACE = GOOD_TRACE[:7] + [
    {"action": "buy", "params": {"u": "bob"}, "observed": {"sold": 2, "remaining": -1, "outcome": {"alice": "success", "bob": "success"}}}]


def jsonl(events):
    return ("\n".join(json.dumps(e, sort_keys=True) for e in events) + "\n").encode()


class FormalGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.case, _ = make_case(self.root)
        self.binding = self.case["current"]["binding"]
        self.contract_doc = copy.deepcopy(CONTRACT)
        self.model_doc = ticket_model()
        self.contract = Contract(self.contract_doc)
        self.model = Model(self.model_doc, None, self.contract)

    # ---- fixtures ----------------------------------------------------------------------
    def inputs(self, model):
        return {"model": model.identity(), "contract": model.contract.identity()}

    def qualification(self, model=None):
        model = model or self.model
        q = qualify(model)
        return make("qualify", self.inputs(model), q["settings"], q["result"], q["verdict"], "E2", "t0")

    def conformance(self, trace_bytes, head=None):
        path = self.root / ("scratch-%s.jsonl" % hashlib.sha256(trace_bytes).hexdigest()[:8])
        path.write_bytes(trace_bytes)
        traces = check_files(self.model, [path])
        sm = {"status": "FRESH", "issues": [], "drifted_files": [], "stale": [], "files": {}, "map_digest": "sha256:" + "0" * 64}
        c = conform(self.model, sm, traces)
        result = {"source_map": sm, "traces": traces, "reasons": c["reasons"],
                  "source": {"head": head or self.binding["candidate_sha"], "files": {}}, "replays": []}
        return make("conform", self.inputs(self.model), {"hidden_steps": 0}, result, c["verdict"], "E3", "t0")

    def add(self, rec_id, kind, name, data, check_id="revoke-new-read"):
        if not isinstance(data, bytes):
            data = json.dumps(data, sort_keys=True).encode()
        (self.root / name).write_bytes(data)
        attempt = self.case["run"]["attempts"][-1]
        attempt["evidence"].append({"id": rec_id, "check_id": check_id, "type": kind, "path": name,
                                    "digest": "sha256:" + hashlib.sha256(data).hexdigest(), "size_bytes": len(data)})
        next(c for c in attempt["checks"] if c["id"] == check_id)["evidence_refs"].append(rec_id)

    def policy_v2(self, levels=(("E2", "QUALIFIED"), ("E3", "CONFORMS")), rerun=True, model=None):
        model = model or self.model
        p = self.case["policy"]
        p["schema_version"] = 2
        p["formal"] = [{"check_id": "revoke-new-read", "min_level": lvl, "model_digest": model.digest,
                        "contract_digest": model.contract.digest, "properties_digest": model.contract.properties_digest,
                        "pass_verdicts": [verdict], "rerun": rerun} for lvl, verdict in levels]

    def full_evidence(self, trace=None, head=None, qualification=None):
        trace = trace or jsonl(GOOD_TRACE)
        self.add("fv-model", "fv-model", "model.json", self.model_doc)
        self.add("fv-contract", "fv-contract", "contract.json", self.contract_doc)
        self.add("fv-trace-1", "fv-trace", "trace-1.jsonl", trace)
        self.add("fv-qualify", "fv-receipt", "qualify.json", qualification or self.qualification())
        self.add("fv-conform", "fv-receipt", "conform.json", self.conformance(trace, head))

    def decide(self, expected):
        refresh_manifest(self.case)
        result = evaluate(self.case, self.root)
        self.assertEqual(expected, result["verification_decision"], result)
        self.assertEqual("local_advisory", result["authority"])
        return result

    # ---- tests -------------------------------------------------------------------------
    def test_pinned_formal_evidence_with_reexecution_is_eligible(self):
        self.policy_v2()
        self.full_evidence()
        self.decide("eligible")

    def test_policy_v1_cases_are_unchanged(self):
        self.full_evidence()   # extra fv records under a v1 policy are just evidence files
        self.decide("eligible")

    def test_unapproved_model_or_contract_is_blocked(self):
        weaker = copy.deepcopy(CONTRACT)
        weaker["properties"][0]["expr"] = "sold <= STOCK + 1"
        other = Model(ticket_model(), None, Contract(weaker))
        self.policy_v2(model=other)
        self.full_evidence()
        r = self.decide("blocked")
        self.assertIn("approved policy", " ".join(r["reasons"]))

    def test_missing_level_or_receipt_is_blocked(self):
        self.policy_v2()
        self.add("fv-model", "fv-model", "model.json", self.model_doc)
        self.add("fv-contract", "fv-contract", "contract.json", self.contract_doc)
        self.add("fv-qualify", "fv-receipt", "qualify.json", self.qualification())
        r = self.decide("blocked")       # E2 qualification alone cannot satisfy the E3 requirement
        self.assertIn("E3", " ".join(r["reasons"]))

    def test_conformance_for_another_candidate_is_blocked(self):
        self.policy_v2()
        self.full_evidence(head="f" * 40)
        r = self.decide("blocked")
        self.assertIn("another candidate", " ".join(r["reasons"]))

    def test_tampered_receipt_or_trace_is_blocked(self):
        self.policy_v2()
        q = self.qualification()
        q["result"]["check"]["stats"]["states"] += 1          # consistent JSON, wrong facts
        self.full_evidence(qualification=q)
        self.decide("blocked")
        self.setUp()
        self.policy_v2()
        self.full_evidence()
        attempt = self.case["run"]["attempts"][-1]
        rec = next(e for e in attempt["evidence"] if e["id"] == "fv-trace-1")
        data = jsonl(GOOD_TRACE[:-1])                           # drop the final step, keep the record self-consistent
        (self.root / rec["path"]).write_bytes(data)
        rec.update(digest="sha256:" + hashlib.sha256(data).hexdigest(), size_bytes=len(data))
        r = self.decide("blocked")
        self.assertIn("raw trace", " ".join(r["reasons"]))

    def test_negative_formal_evidence_cannot_support_a_pass(self):
        self.policy_v2()
        bad = Model(ticket_model(**BUGGY), None, self.contract)
        self.full_evidence(qualification=self.qualification(bad))
        self.decide("blocked")

    def test_nonconforming_implementation_requests_repair(self):
        self.case, _ = make_case(self.root, passed=False)
        self.binding = self.case["current"]["binding"]
        self.policy_v2()
        self.full_evidence(trace=jsonl(BAD_TRACE))
        self.decide("needs_repair")

    def test_structural_validation_without_rerun(self):
        self.policy_v2(rerun=False)
        self.add("fv-qualify", "fv-receipt", "qualify.json", self.qualification())
        self.add("fv-trace-1", "fv-trace", "trace-1.jsonl", jsonl(GOOD_TRACE))
        self.add("fv-conform", "fv-receipt", "conform.json", self.conformance(jsonl(GOOD_TRACE)))
        self.decide("eligible")
        forged = self.conformance(jsonl(GOOD_TRACE))
        forged["verdict"] = "CONFORMS"
        forged["result"]["reasons"] = []
        forged["result"]["source_map"]["status"] = "STALE"    # a receipt that contradicts itself
        self.setUp()
        self.policy_v2(rerun=False)
        self.add("fv-qualify", "fv-receipt", "qualify.json", self.qualification())
        self.add("fv-conform", "fv-receipt", "conform.json", forged)
        self.decide("blocked")


if __name__ == "__main__":
    unittest.main()
