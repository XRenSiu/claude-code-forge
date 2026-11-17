"""Steps 05 and 07: the implementation contract and the verification that code honours it.

Built on the AI-DLC example (a real SQLite implementation with property, concurrency and model-based
tests). Each test copies the example, breaks one thing the contract or the code must hold, and
shows the break is caught next to a twin that passes.
"""
import copy
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/accept-change/scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fvkit.implcontract import check_impl_contract, check_impl_review, derive, verify_implementation  # noqa: E402
from fvkit.spec import load_model  # noqa: E402
from test_formal import BUGGY, load, ticket_model  # noqa: E402

FORMAL = Path(__file__).resolve().parents[2] / "ai-dlc/skills/formal-verify"
EXAMPLE = FORMAL / "assets/example-ticket"
UPSTREAM = FORMAL / "upstream/UPSTREAM.json"
try:
    import yaml
except ImportError:   # the example is YAML
    yaml = None


def sha(p):
    return "sha256:" + hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Derivation(unittest.TestCase):
    """What the verified model fixes is computed, not written by the agent."""

    def test_shared_check_then_act_is_told_apart_from_per_key_state(self):
        ops = {o["action"]: o for o in derive(load(ticket_model()))["operations"]}
        self.assertEqual(ops["buy"]["read_modify_write"], {"shared": ["remaining", "sold"], "per_key": ["phase"]})
        self.assertEqual(ops["buy"]["contended_by"], ["buy"])                   # two buyers race on the shared stock
        self.assertEqual(ops["read"]["contended_by"], ["buy"])                  # a read can see stock change under it
        self.assertEqual(ops["request"]["contended_by"], [])                    # only the same user's calls touch phase[u]
        self.assertEqual(ops["request"]["same_key_contended_by"], ["buy", "read", "reject", "request"])
        self.assertTrue(all(o["atomic_required"] for o in ops.values()))
        self.assertEqual(ops["buy"]["fairness"], "weak")

    def test_obligations_follow_the_contract_and_the_mutants(self):
        d = derive(load(ticket_model()))
        kinds = {p["id"]: p["covered_by_kinds"] for p in d["obligations"]["properties"]}
        self.assertEqual(kinds["Answered"], ["liveness", "mbt", "proof"])
        self.assertEqual(kinds["NoOversell"], ["property", "mbt", "proof"])
        self.assertEqual([m["id"] for m in d["obligations"]["mutants"]], ["check-then-act", "lost-decrement"])
        self.assertEqual(d["obligations"]["assumptions"], ["A1"])
        self.assertEqual(derive(load(ticket_model())), derive(load(ticket_model())))   # deterministic
        buggy = {o["action"]: o for o in derive(load(ticket_model(**BUGGY)))["operations"]}
        self.assertEqual(buggy["buy"]["reads"]["seen"], ["u"])                 # the old design decides on a per-user snapshot


@unittest.skipUnless(yaml is not None and EXAMPLE.is_dir(), "needs PyYAML and the AI-DLC example")
class Contract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ex = Path(self.tmp.name) / "ex"
        shutil.copytree(EXAMPLE, self.ex)
        self.model = load_model(self.ex / "model.yaml")
        self.doc = yaml.safe_load((self.ex / "impl-contract.yaml").read_text())

    def check(self, doc=None, name="impl-contract.yaml"):
        p = self.ex / name
        p.write_text(yaml.safe_dump(doc if doc is not None else self.doc, allow_unicode=True, sort_keys=False))
        return check_impl_contract(p, self.model, _upstream())

    def op(self, doc, action):
        return next(o for o in doc["operations"] if o["action"] == action)

    def test_the_example_contract_is_ready(self):
        res = self.check()
        self.assertEqual(res["verdict"], "READY", res["issues"])

    def test_what_the_model_fixes_cannot_be_reinterpreted(self):
        d = copy.deepcopy(self.doc)
        next(o for o in d["derived"]["operations"] if o["action"] == "buy")["atomic_required"] = False
        self.assertIn("derived section differs", " ".join(self.check(d)["issues"]))
        d = copy.deepcopy(self.doc)
        self.op(d, "buy")["atomicity"]["mechanism"] = "none"                   # "it is fast enough"
        self.assertIn("operation buy must be atomic", " ".join(self.check(d)["issues"]))
        d = copy.deepcopy(self.doc)
        d["state"] = [s for s in d["state"] if s["variable"] != "seen"]
        self.assertIn("model variable seen has no code counterpart", " ".join(self.check(d)["issues"]))
        d = copy.deepcopy(self.doc)
        self.op(d, "read")["trace"]["event"] = "show_stock"
        self.assertIn("one trace event type per spec action", " ".join(self.check(d)["issues"]))

    def test_failures_must_land_on_states_the_model_allows(self):
        d = copy.deepcopy(self.doc)
        self.op(d, "read")["failures"]["retry"]["model_effect"] = "repeat"     # a retry that re-runs a non-idempotent step
        self.assertIn("requires idempotency", " ".join(self.check(d)["issues"]))
        d = copy.deepcopy(self.doc)
        self.op(d, "buy")["failures"]["error"]["model_effect"] = "action:refund"   # no such transition
        self.assertIn("a failure may only leave the system in a state the model allows", " ".join(self.check(d)["issues"]))
        d = copy.deepcopy(self.doc)
        self.op(d, "buy")["failures"]["timeout"]["behavior"] = "drop the request after 30 s"
        self.assertIn("must not silently drop it", " ".join(self.check(d)["issues"]))
        d = copy.deepcopy(self.doc)
        self.op(d, "request")["failures"].pop("conflict")
        self.assertIn("failures.conflict", " ".join(self.check(d)["issues"]))

    def test_acceptance_obligations_cover_properties_mutants_assumptions(self):
        d = copy.deepcopy(self.doc)
        d["acceptance"]["tests"] = [t for t in d["acceptance"]["tests"] if t["id"] != "T-liveness"]
        issues = " ".join(self.check(d)["issues"])
        self.assertIn("property EveryRequestAnswered (leads_to) has no acceptance test", issues)
        d = copy.deepcopy(self.doc)
        for t in d["acceptance"]["tests"]:
            t.pop("must_fail_with", None)
        self.assertIn("no test declares must_fail_with", " ".join(self.check(d)["issues"]))
        d = copy.deepcopy(self.doc)
        d["acceptance"]["regressions"] = [r for r in d["acceptance"]["regressions"] if r["mutant"] != "lost-decrement"]
        self.assertIn("mutant lost-decrement", " ".join(self.check(d)["issues"]))
        d = copy.deepcopy(self.doc)
        next(r for r in d["acceptance"]["regressions"] if r["mutant"] == "lost-decrement")["detected_by"] = {"test": "T-liveness"}
        self.assertIn("covers none of the properties that kill it", " ".join(self.check(d)["issues"]))
        d = copy.deepcopy(self.doc)
        d["acceptance"]["assumptions"][0]["evidence"] = "TODO"
        self.assertIn("assumption A-NO-RESTOCK", " ".join(self.check(d)["issues"]))
        d = copy.deepcopy(self.doc)
        d["acceptance"]["tests"] = [t for t in d["acceptance"]["tests"] if t["kind"] != "concurrency"]
        self.assertIn("operation buy contends with ['buy']: it needs a concurrency test", " ".join(self.check(d)["issues"]))

    def test_it_comes_after_a_qualified_model(self):
        d = copy.deepcopy(self.doc)
        d["qualification"] = None
        self.assertIn("no QUALIFIED receipt", " ".join(self.check(d)["issues"]))
        (self.ex / "receipts/qualify.json").write_text((self.ex / "receipts/qualify.json").read_text().replace('"QUALIFIED"', '"NOT_QUALIFIED"', 1))
        self.assertIn("qualification receipt", " ".join(self.check()["issues"]))
        from fvkit.qualify import qualify
        from fvkit.receipt import make, write
        bad_model = load_model(self.ex / "model-check-then-act.yaml")         # a design the checker rejects
        q = qualify(bad_model)
        rp = write(self.ex / "receipts/bad-qualify.json", make("qualify", {"model": bad_model.identity(), "contract": bad_model.contract.identity()},
                                                                q["settings"], q["result"], q["verdict"], "E2", "t0"))
        d = copy.deepcopy(self.doc)
        d["qualification"] = {"receipt": "receipts/bad-qualify.json", "digest": sha(rp)}  # cited faithfully, but not QUALIFIED for this model
        self.assertIn("qualification receipt rejected", " ".join(self.check(d)["issues"]))
        other = load_model(self.ex / "model-check-then-act.yaml")
        res = check_impl_contract(self.ex / "impl-contract.yaml", other, _upstream())
        self.assertIn("written for another model", " ".join(res["issues"]))


def _upstream():
    from fvkit.upstream import Upstream
    return Upstream(UPSTREAM) if UPSTREAM.is_file() else None


@unittest.skipUnless(yaml is not None and EXAMPLE.is_dir(), "needs PyYAML and the AI-DLC example")
class Verification(unittest.TestCase):
    """Runs the example's real tests; each case takes a few seconds."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ex = Path(self.tmp.name) / "ex"
        shutil.copytree(EXAMPLE, self.ex)
        self.model = load_model(self.ex / "model.yaml")

    def verify(self, review=True, run=True):
        return verify_implementation(self.ex / "impl-contract.yaml", self.model, review=self.ex / "impl-review.yaml" if review else None,
                                     run=run, upstream=_upstream(), out_dir=Path(self.tmp.name) / ("w%d" % len(list(Path(self.tmp.name).iterdir()))))

    def test_the_example_implements_its_contract(self):
        v = self.verify()
        self.assertEqual(v["verdict"], "IMPLEMENTS", v["result"]["reasons"])
        res = v["result"]
        self.assertEqual(res["coverage"]["unexercised"], [])
        self.assertEqual([r["conforming_trace"] for r in res["replays"]], [True])
        self.assertEqual(sorted(t["id"] for t in res["tests"] if t["role"] == "negative"), ["T-concurrency", "T-mbt", "T-safety"])
        self.assertTrue(all(t["exit"] != 0 for t in res["tests"] if t["role"] == "negative"))

    def test_code_that_drops_a_contracted_constraint_does_not_implement_it(self):
        code = self.ex / "impl/tickets.py"
        text = code.read_text()
        code.write_text(text.replace('''            row = self.db.execute("SELECT status FROM requests WHERE user = ?", (user,)).fetchone()
            if row is None or row[0] != "pending":   # idempotent retry: a repeated purchase returns the first answer
                self.db.execute("COMMIT")
                return row[0] if row else "no_request"
''', ""))                                                               # retries would sell twice again
        v = self.verify()
        reasons = " ".join(v["result"]["reasons"])
        self.assertEqual(v["verdict"], "NOT_IMPLEMENTED")
        self.assertIn("operation buy: idempotency evidence", reasons)
        self.assertIn("reviewed code changed since the review", reasons)    # the review pinned other bytes

    def test_a_contracted_mechanism_missing_from_code_is_found_without_running_anything(self):
        code = self.ex / "impl/tickets.py"
        code.write_text(code.read_text().replace('self.db.execute("BEGIN IMMEDIATE")', 'self.db.execute("BEGIN")'))   # deferred lock: check and act can interleave
        reasons = " ".join(self.verify(review=False, run=False)["result"]["reasons"])
        self.assertIn("operation buy: atomicity evidence", reasons)
        self.assertIn("operation reject: atomicity evidence", reasons)

    def test_an_operation_never_seen_in_a_conforming_trace_is_not_verified(self):
        trace = self.ex / "partial.jsonl"
        trace.write_text("\n".join(json.dumps(e) for e in [
            {"init": True, "observed": {"sold": 0, "remaining": 1, "outcome": {"alice": "none", "bob": "none"}}},
            {"action": "request", "params": {"u": "alice"}, "observed": {"outcome": {"alice": "pending", "bob": "none"}}},
            {"action": "read", "params": {"u": "alice"}, "observed": {"remaining": 1}}]) + "\n")
        v = verify_implementation(self.ex / "impl-contract.yaml", self.model, traces=[trace], run=False, upstream=_upstream())
        self.assertEqual(v["result"]["traces"]["verdict"], "CONFORMS")
        self.assertEqual(v["result"]["coverage"]["unexercised"], ["buy", "reject"])
        reasons = " ".join(v["result"]["reasons"])
        self.assertIn("operation buy never happened in a conforming trace", reasons)

    def test_a_negative_control_that_passes_proves_nothing(self):
        p = self.ex / "impl-contract.yaml"
        doc = yaml.safe_load(p.read_text())
        t = next(t for t in doc["acceptance"]["tests"] if t["id"] == "T-concurrency")
        t["must_fail_with"] = list(t["argv"])                                 # "broken variant" = the shipped code
        p.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False))
        reasons = " ".join(self.verify(review=False)["result"]["reasons"])
        self.assertIn("test T-concurrency still passes on its broken variant", reasons)
        self.assertIn("no implementation review", reasons)

    def test_unrun_tests_and_unreviewed_code_are_not_evidence(self):
        reasons = " ".join(self.verify(run=False)["result"]["reasons"])
        self.assertIn("the acceptance tests were not run", reasons)
        self.assertIn("no implementation traces", reasons)
        self.assertIn("counterexample replay replay:check-then-act:NoOversell", reasons)

    def test_the_review_follows_spec_kit_analyze_and_quint_gap_questions(self):
        doc = yaml.safe_load((self.ex / "impl-contract.yaml").read_text())
        rp = self.ex / "impl-review.yaml"
        base = yaml.safe_load(rp.read_text())

        def check(mutate):
            r = copy.deepcopy(base)
            mutate(r)
            rp.write_text(yaml.safe_dump(r, allow_unicode=True, sort_keys=False))
            return " ".join(check_impl_review(rp, self.ex / "impl-contract.yaml", doc, self.ex, _upstream())["issues"])
        self.assertEqual(check(lambda r: None), "")
        self.assertIn("does not hold in the implementation", check(lambda r: r["assumptions"][0].update(status="violated")))
        self.assertIn("a human accepts the risk", check(lambda r: r["assumptions"][0].update(status="unverified")))
        self.assertIn("must be modelled before acceptance", check(lambda r: r["unmodeled_behaviors"][0].update(disposition="model_it")))
        self.assertIn("is a defect in the code", check(lambda r: r["unmodeled_behaviors"][0].update(disposition="defect")))
        self.assertIn("operation buy is not implemented", check(lambda r: r["coverage"][2].update(implemented=False)))
        self.assertIn("(HIGH) is open", check(lambda r: r["findings"][0].update(severity="HIGH")))
        self.assertIn("truncated", check(lambda r: r["review_complete"].update(findings_count=0)))
        self.assertIn("another version of the implementation contract", check(lambda r: r.update(impl_contract_digest="sha256:" + "0" * 64)))
        self.assertIn("did not pin the code", check(lambda r: r["source"].update(files={})))

    def test_receipt_is_redecided_from_its_parts(self):
        from fvkit.receipt import make, validate
        from fvkit.values import FvError
        v = self.verify()
        r = make("implement", {"model": self.model.identity(), "contract": self.model.contract.identity()}, {},
                 v["result"], v["verdict"], "E3", "2026-11-17T00:00:00+00:00")
        self.assertTrue(validate(json.loads(json.dumps(r)), model=self.model, expect_verdicts=["IMPLEMENTS"])["valid"])
        forged = json.loads(json.dumps(r))
        next(t for t in forged["result"]["tests"] if t["role"] == "negative")["exit"] = 0
        with self.assertRaises(FvError):
            validate(forged, model=self.model)


if __name__ == "__main__":
    unittest.main()
