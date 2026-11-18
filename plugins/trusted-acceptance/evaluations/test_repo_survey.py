"""Entrance C: repository survey, lifted properties, function contracts, code-level verifier adapters.

Each rule quotes a vendored procedure (pstack create-formal-verification-skill, Theorem OSS Verify
add-project / review.md, FM-Agent system_prompt / bug_validator). As in the other suites, every
check is shown twice: the procedure carried out (passes) and one specific way of skipping it (caught).
"""
import atexit
import copy
import json
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/accept-change/scripts"
sys.path.insert(0, str(SCRIPTS))
from fvkit.contracts import check_specs, classify  # noqa: E402
from fvkit.external import parse, reparse  # noqa: E402
from fvkit.props import check_props, run_props  # noqa: E402
from fvkit.receipt import make, validate  # noqa: E402
from fvkit.survey import check_targets, draft, is_test_file, role_of, scan  # noqa: E402
from fvkit.upstream import Upstream  # noqa: E402
from fvkit.values import FvError, sha_bytes  # noqa: E402

FORMAL = Path(__file__).resolve().parents[2] / "ai-dlc/skills/formal-verify"
EX = FORMAL / "assets/example-ticket"
UP = Upstream(FORMAL / "upstream/UPSTREAM.json")
FV = SCRIPTS / "fv.py"
_TMP = Path(tempfile.mkdtemp(prefix="fv-survey-"))
atexit.register(shutil.rmtree, _TMP, True)


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.invalid"] + list(args),
                          capture_output=True, text=True, check=True).stdout


def write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip("\n"))
    return path


def toy_repo(root):
    """A small repository with a ledger (stateful risk), a parser, tests, a fuzz target and a fix commit."""
    write(root / "src/ledger.py", '''
        import threading

        class Ledger:
            def __init__(self):
                self.lock = threading.Lock()
                self.balance = 0

            def transfer(self, amount):
                with self.lock:
                    if self.balance - amount < 0:
                        raise ValueError("insufficient balance")
                    self.balance -= amount
                    return self.balance
        ''')
    write(root / "src/codec.py", '''
        import json

        def decode(raw):
            return json.loads(raw)
        ''')
    write(root / "tests/test_ledger.py", '''
        from hypothesis import given, strategies as st
        from src.ledger import Ledger

        @given(st.integers())
        def test_never_negative(n):
            Ledger()
        ''')
    write(root / "fuzz/fuzz_codec.c", '''
        int LLVMFuzzerTestOneInput(const unsigned char *data, unsigned long size) { return 0; }
        ''')
    write(root / "scripts/smoke.py", "import json\nretry = 3\nstatus = 'ready'\n")
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "init")
    (root / "src/ledger.py").write_text((root / "src/ledger.py").read_text() + "\n# guard\n")
    git(root, "commit", "-qam", "fix race in transfer")
    return root


class Scan(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = toy_repo(_TMP / "scan-repo")
        cls.s = scan(cls.root, history=50)

    def test_inventory_tests_and_existing_checks(self):
        inv = self.s["inventory"]
        self.assertEqual(inv["languages"]["python"]["test_files"], 1)
        kinds = {(e["kind"], e["tool"], e["file"]) for e in self.s["existing_checks"]}
        self.assertIn(("property-test", "hypothesis", "tests/test_ledger.py"), kinds)
        self.assertIn(("fuzz-target", "libfuzzer", "fuzz/fuzz_codec.c"), kinds)   # OSS Verify starts from these

    def test_signals_skip_test_files_and_carry_verbatim_lines(self):
        files = {s["file"] for s in self.s["signals"]}
        self.assertNotIn("tests/test_ledger.py", files)
        lock = next(s for s in self.s["signals"] if s["class"] == "concurrency" and s["file"] == "src/ledger.py")
        line = (self.root / "src/ledger.py").read_text().splitlines()[lock["line"] - 1]
        self.assertEqual(lock["text"], line.strip())

    def test_fix_history_and_reading_order(self):
        self.assertEqual(self.s["history"]["files"].get("src/ledger.py"), 1)   # "fix race in transfer"
        order = [(c["file"], c["role"]) for c in self.s["clusters"]]
        self.assertEqual(order[0], ("src/ledger.py", "product"))
        self.assertEqual(order[-1], ("scripts/smoke.py", "tooling"))          # tooling after product code
        self.assertIn("tests/test_ledger.py", self.s["clusters"][0]["tests_mentioning"])

    def test_deterministic(self):
        again = scan(self.root, history=50)
        self.assertEqual(again["signals"], self.s["signals"])
        self.assertEqual(again["existing_checks"], self.s["existing_checks"])

    def test_classifiers(self):
        self.assertTrue(is_test_file("pkg/__tests__/a.ts") and is_test_file("a.spec.ts") and is_test_file("x_test.go"))
        self.assertFalse(is_test_file("src/attestation.py"))
        self.assertEqual((role_of("scripts/x.ts"), role_of("apps/hub/src/a.ts")), ("tooling", "product"))


class Targets(unittest.TestCase):
    """fv-targets: pstack (choose from the code, let the question choose the tool) + OSS Verify step 1."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(dir=_TMP))
        shutil.copytree(EX / "impl", self.tmp / "impl")
        shutil.copytree(EX / "survey", self.tmp / "survey")
        self.survey = self.tmp / "survey/survey.json"
        self.doc = json.loads((self.tmp / "survey/targets.json").read_text())

    def check(self, doc=None, **kw):
        p = self.tmp / "survey/t.json"
        p.write_text(json.dumps(doc or self.doc))
        return check_targets(p, self.survey, upstream=UP, **kw)

    def assertIssue(self, text, doc):
        r = self.check(doc)
        self.assertEqual(r["verdict"], "NOT_READY")
        self.assertIn(text, " ".join(r["issues"]))

    def test_shipped_example_is_ready(self):
        r = check_targets(EX / "survey/targets.json", EX / "survey/survey.json", upstream=UP)
        self.assertEqual(r["verdict"], "READY", r["issues"])
        self.assertEqual([t["route"] for t in r["targets"]], ["stateful-model", "property-lift", "function-contracts"])

    def test_anchor_must_be_verbatim(self):
        d = copy.deepcopy(self.doc)
        d["targets"][0]["anchors"][0]["quote"] = 'self.db.execute("BEGIN EXCLUSIVE")'
        self.assertIssue("not verbatim", d)

    def test_do_not_guess_what_correct_means(self):
        d = copy.deepcopy(self.doc)
        d["correctness"]["input_size"] = {"status": "TODO", "answer": "TODO"}
        self.assertIssue("do not guess", d)
        d = copy.deepcopy(self.doc)
        d["questions"][0].pop("signer_kind")          # the generator answering its own question
        self.assertIssue("answered by the maintainer", d)
        d = copy.deepcopy(self.doc)
        d["questions"][0]["question"] = "Tell me the untrusted inputs."
        self.assertIssue("ending with '?'", d)

    def test_one_sentence_promise_and_harm(self):
        d = copy.deepcopy(self.doc)
        d["targets"][0]["harm"] = "Two buyers pay for one seat. One is turned away."
        self.assertIssue("one plain sentence", d)
        d["targets"][0]["harm"] = "两个买家为同一个座位付了钱。其中一个在门口被拒。"
        self.assertIssue("one plain sentence", d)
        d["targets"][0]["harm"] = "两个买家为同一个座位付了钱，其中一个在门口被拒。"
        d["targets"][0]["rank"] = "1"
        self.assertIssue("ranks must be 1..3", d)

    def test_tool_fits_language_and_machine(self):
        d = copy.deepcopy(self.doc)
        d["targets"][1].update(route="code-verifier", tool={"name": "kani", "available": False, "why": "proofs"})
        r = self.check(d)
        text = " ".join(r["issues"])
        self.assertIn("kani verifies rust, but the anchored code is python", text)
        self.assertIn("not installed here; give tool.install", text)
        d["targets"][1]["tool"] = {"name": "crosshair", "available": True, "why": "symbolic"}
        self.assertIssue("the survey found crosshair missing", d)

    def test_stateful_promise_off_the_model_route_needs_a_reason(self):
        d = copy.deepcopy(self.doc)
        d["targets"][2].pop("route_reason")
        self.assertIssue("give route_reason for function-contracts", d)

    def test_nothing_dropped_silently(self):
        d = copy.deepcopy(self.doc)
        d["targets"][0]["signals"] = []
        d["targets"][0]["source"] = {"kind": "user", "quote": "verify purchase"}
        for t in d["targets"]:
            t["signals"] = []
            t["source"] = {"kind": "user", "quote": "x"}
        r = self.check(d)
        self.assertIn("C1", r["uncovered"])
        d["dismissed"] = [{"cluster": "C1", "file": "tickets.py", "reason": "covered by the existing model"}]
        self.assertEqual(self.check(d)["verdict"], "READY")

    def test_existing_fuzz_and_property_tests_are_lifted_or_dismissed(self):
        root = toy_repo(_TMP / "lift-repo")
        sp = _TMP / "lift-survey.json"
        doc = scan(root, history=0)
        doc["root"] = str(root)
        sp.write_text(json.dumps(doc))
        skeleton = draft(sp, UP)
        self.assertTrue(any(x.get("existing_check") for x in skeleton["dismissed"]))
        tp = _TMP / "lift-targets.json"
        tp.write_text(json.dumps(skeleton))
        r = check_targets(tp, sp, upstream=UP)
        self.assertIn("neither lifted by a target nor dismissed", " ".join(r["issues"]))   # TODO reasons
        self.assertIn("no target", " ".join(r["issues"]))

    def test_stale_survey(self):
        tickets = self.tmp / "impl/tickets.py"
        tickets.write_text(tickets.read_text() + "\nLEASE_TTL = 30  # new lease logic\n")
        r = self.check()
        self.assertEqual(r["verdict"], "STALE")

    def test_survey_digest_pins_the_scan(self):
        d = copy.deepcopy(self.doc)
        d["survey"]["digest"] = "sha256:" + "0" * 64
        self.assertIssue("another survey", d)


class Props(unittest.TestCase):
    """fv-props: OSS Verify add-project step 3 and review.md F."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(dir=_TMP))
        shutil.copytree(EX / "impl", self.tmp / "impl")
        shutil.copytree(EX / "survey", self.tmp / "survey")
        self.doc = json.loads((self.tmp / "survey/props.json").read_text())
        for c in self.doc["checks"]:
            c["witness"]["argv"] = c["witness"]["argv"][:-1] + ["8"]   # fewer seeds: the same breakages still fire

    def save(self, doc):
        p = self.tmp / "survey/p.json"
        p.write_text(json.dumps(doc))
        return p

    def test_shipped_example_ready_and_able_to_fail(self):
        r = check_props(EX / "survey/props.json", UP, EX / "survey/props-review.json")
        self.assertEqual(r["verdict"], "READY", r["issues"])
        v = run_props(self.save(self.doc), self.tmp / "work")
        self.assertEqual(v["verdict"], "ABLE_TO_FAIL", v["result"]["reasons"])
        self.assertEqual([b["outcome"] for c in v["result"]["checks"] for b in c["breakages"]], ["CAUGHT", "CAUGHT"])
        self.assertEqual((self.tmp / "impl/tickets.py").read_bytes(), (EX / "impl/tickets.py").read_bytes())  # never edited
        receipt = make("props", {"props": v["props"]}, {}, v["result"], v["verdict"], "E1", "2026-01-01T00:00:00+00:00")
        self.assertTrue(validate(receipt)["valid"])
        forged = copy.deepcopy(receipt)
        forged["result"]["checks"][0]["breakages"][0]["outcome"] = "MISSED"
        with self.assertRaises(FvError):
            validate(forged)

    def test_a_breakage_the_tests_miss_is_weak(self):
        d = copy.deepcopy(self.doc)
        line = next(i for i, x in enumerate((self.tmp / "impl/tickets.py").read_text().splitlines(), 1) if "idempotent retry" in x)
        d["checks"][0]["breakages"] = [{"file": "tickets.py", "line": line, "old": "idempotent retry", "new": "idempotent  retry"}]
        v = run_props(self.save(d), self.tmp / "w1")
        self.assertEqual(v["verdict"], "WEAK")
        self.assertIn("MISSED", " ".join(v["result"]["reasons"]))

    def test_a_failure_of_another_check_does_not_count(self):
        d = copy.deepcopy(self.doc)
        d["checks"][0]["breakages"] = copy.deepcopy(self.doc["checks"][1]["breakages"])   # Conservation's breakage
        v = run_props(self.save(d), self.tmp / "w2")
        self.assertEqual(v["verdict"], "WEAK")
        self.assertIn("WRONG_CHECK", " ".join(v["result"]["reasons"]))

    def assertIssue(self, text, doc, review=None):
        r = check_props(self.save(doc), UP, review)
        self.assertEqual(r["verdict"], "NOT_READY")
        self.assertIn(text, " ".join(r["issues"]))

    def test_static_rules(self):
        d = copy.deepcopy(self.doc)
        d["checks"][0]["breakages"][0]["old"] = "remaining > 7"
        self.assertIssue("must occur once on tickets.py", d)
        d = copy.deepcopy(self.doc)
        d["checks"][0]["breakages"] = []
        self.assertIssue("no change can make fail checks nothing", d)
        d = copy.deepcopy(self.doc)
        d["checks"][0]["expected_from"] = "library"
        self.assertIssue("only agrees with itself", d)
        d = copy.deepcopy(self.doc)
        d["checks"][0]["claim"] = "A purchase succeeds exactly when a ticket remains."
        self.assertIssue("two-way but the check is declared one-way", d)
        d = copy.deepcopy(self.doc)
        d["checks"][0]["kind"] = "not_a_property"
        self.assertIssue("not a property: <reason>", d)

    def test_removable_assert_is_not_a_property(self):
        write(self.tmp / "impl/test_assert.py", "def t(x):\n    assert x >= 0\n")
        d = copy.deepcopy(self.doc)
        d["checks"][0].update(file="test_assert.py", check="    assert x >= 0")
        self.assertIssue("python -O removes assert", d)

    def test_review_covers_every_check_and_shows_weakness(self):
        review = json.loads((self.tmp / "survey/props-review.json").read_text())
        p = self.save(self.doc)
        review["props_digest"] = sha_bytes(p.read_bytes())
        rp = self.tmp / "survey/r.json"
        rp.write_text(json.dumps(review))
        self.assertEqual(check_props(p, UP, rp)["verdict"], "READY")
        bad = copy.deepcopy(review)
        bad["checks"] = bad["checks"][:1]
        rp.write_text(json.dumps(bad))
        self.assertIn("check P2 was not reviewed", " ".join(check_props(p, UP, rp)["issues"]))
        bad = copy.deepcopy(review)
        bad["checks"][0] = {"id": "P1", "verdict": "fail", "weakness": "weak"}
        rp.write_text(json.dumps(bad))
        self.assertIn("one-line change", " ".join(check_props(p, UP, rp)["issues"]))
        bad = copy.deepcopy(review)
        bad["reviewer"]["context"] = "same-session"
        rp.write_text(json.dumps(bad))
        self.assertIn("author does not review", " ".join(check_props(p, UP, rp)["issues"]))
        rp.write_text((EX / "survey/props-review.json").read_text())   # pinned to the shipped props, not this edited copy
        self.assertIn("another version", " ".join(check_props(p, UP, rp)["issues"]))


class Contracts(unittest.TestCase):
    """fv-function-specs: FM-Agent rules, layers, a result per function, probes re-derived."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(dir=_TMP))
        shutil.copytree(EX / "impl", self.tmp / "impl")
        shutil.copytree(EX / "survey", self.tmp / "survey")
        self.doc = json.loads((self.tmp / "survey/function-specs.json").read_text())

    def check(self, doc, run=False):
        p = self.tmp / "survey/f.json"
        p.write_text(json.dumps(doc))
        return check_specs(p, UP, run=run)

    def test_shipped_example_complete_and_reproduced(self):
        r = check_specs(EX / "survey/function-specs.json", UP, run=True)
        self.assertEqual(r["verdict"], "COMPLETE", r["issues"])
        self.assertEqual([(f["id"], f["route"], f["reproduced_now"]) for f in r["findings"]], [("B1", "fv_implementation_defect", True)])

    def test_spec_rules(self):
        d = copy.deepcopy(self.doc)
        d["functions"][2]["post_condition"] = "Correctly handles the read and returns the stock."
        self.assertIn("vague term", " ".join(self.check(d)["issues"]))
        d = copy.deepcopy(self.doc)
        d["functions"][0]["post_condition"] += " It calls _purchase_check_then_act for the old variant."
        self.assertIn("narrates a call", " ".join(self.check(d)["issues"]))
        d = copy.deepcopy(self.doc)
        d["functions"][1]["layer"] = 0
        d["functions"][0]["layer"] = 1
        self.assertIn("earlier layer", " ".join(self.check(d)["issues"]))
        d = copy.deepcopy(self.doc)
        d["results"] = d["results"][:2]
        self.assertIn("no reasoning result", " ".join(self.check(d)["issues"]))

    def test_recorded_status_must_reproduce(self):
        d = copy.deepcopy(self.doc)
        write(self.tmp / "survey/probes/probe_x.py", "print('NOT CONFIRMED - sold 1 of 1')\n")
        d["results"][2]["validation"]["probe"] = "probes/probe_x.py"
        r = self.check(d, run=True)
        self.assertEqual(r["verdict"], "GAPS")
        self.assertIn("now says not_confirmed", " ".join(r["issues"]))

    def test_classify_reads_not_confirmed_first(self):
        self.assertEqual(classify(0, "NOT CONFIRMED - matched"), "not_confirmed")
        self.assertEqual(classify(0, "CONFIRMED - actual 2"), "confirmed")
        self.assertEqual(classify(1, "CONFIRMED"), "error")
        self.assertEqual(classify(0, "done"), "error")


class CodeVerifiers(unittest.TestCase):
    """Adapter ceilings. CrossHair strings are real output of crosshair-tool 0.0.113; Kani's are from its docs."""
    CH_OK = "/w/ok.py:4: info: Confirmed over all paths.\n"
    CH_UNCONFIRMED = "/w/unconf.py:3: info: Not confirmed.\n"
    CH_FAIL = "/w/bad.py:4: error: false when calling average([-1, -1, -1, -1]) (which returns 0)\n"
    CH_NONE = "WARNING: Targets found, but contain no checkable functions.\n"
    KANI_FAIL = ("Autoharness: Checking function estimate_size against all possible inputs...\nRESULTS:\n"
                 "Check 3: estimate_size.assertion.1\n         - Status: FAILURE\n"
                 "Verification failed for - estimate_size\nComplete - 0 successfully verified functions, 1 failures, 1 total.\n")
    KANI_OK = "VERIFICATION:- SUCCESSFUL\nComplete - 2 successfully verified harnesses, 0 failures, 2 total.\n"
    KANI_NONE = "VERIFICATION:- SUCCESSFUL\nComplete - 0 successfully verified functions, 0 failures, 0 total.\n"

    def test_crosshair_never_passes(self):
        self.assertEqual(parse("crosshair", self.CH_OK, "", 0)["verdict"], "NO_COUNTEREXAMPLE_FOUND")
        self.assertEqual(parse("crosshair", self.CH_UNCONFIRMED, "", 0)["stats"]["not_confirmed"], 1)
        r = parse("crosshair", self.CH_FAIL, "", 1)
        self.assertEqual((r["verdict"], r["violated"]), ("FAIL", ["false when calling average([-1, -1, -1, -1]) (which returns 0)"]))
        self.assertEqual(parse("crosshair", self.CH_NONE, "", 0)["verdict"], "ERROR")   # nothing checked
        self.assertEqual(parse("crosshair", "", "", 0)["verdict"], "ERROR")

    def test_kani(self):
        self.assertEqual(parse("kani", self.KANI_FAIL, "", 1)["verdict"], "FAIL")
        self.assertEqual(parse("kani", self.KANI_OK, "", 0)["verdict"], "PASS")
        self.assertEqual(parse("kani", self.KANI_NONE, "", 0)["verdict"], "ERROR")      # 0 functions verified

    def test_bounded_and_proof_tools(self):
        self.assertEqual(parse("cbmc", "** Results:\nVERIFICATION SUCCESSFUL\n", "", 0)["verdict"], "BOUNDED_PASS")
        self.assertEqual(parse("esbmc", "VERIFICATION FAILED\n", "", 1)["verdict"], "FAIL")
        self.assertEqual(parse("dafny", "Dafny program verifier finished with 4 verified, 0 errors\n", "", 0)["verdict"], "PASS")
        self.assertEqual(parse("dafny", "Dafny program verifier finished with 3 verified, 0 errors, 1 time out\n", "", 4)["verdict"],
                         "INCOMPLETE")
        self.assertEqual(parse("verus", "verification results:: 7 verified, 1 errors\n", "", 1)["verdict"], "FAIL")
        self.assertEqual(parse("lean", "warning: ./P.lean:3:8: declaration uses 'sorry'\n", "", 0)["verdict"], "INCOMPLETE")
        self.assertEqual(parse("lean", "Build completed successfully.\n", "", 0)["verdict"], "PASS")

    def test_receipt_ceiling(self):
        r = {"settings": {"engine": "crosshair"}, "evidence_level": "E1", "verdict": "PASS", "result": {}}
        with self.assertRaises(FvError):
            reparse(r, None)
        r = {"settings": {"engine": "esbmc"}, "evidence_level": "E2", "verdict": "PASS", "result": {}}
        with self.assertRaises(FvError):
            reparse(r, None)


class Cli(unittest.TestCase):
    def test_scan_writes_a_portable_survey_and_check_exit_codes(self):
        out = Path(tempfile.mkdtemp(dir=_TMP)) / "s.json"
        p = subprocess.run([sys.executable, str(FV), "survey", "scan", "--root", str(EX / "impl"), "--history", "0", "--out", str(out)],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertFalse(Path(json.loads(out.read_text())["root"]).is_absolute())
        p = subprocess.run([sys.executable, str(FV), "survey", "check", "--survey", str(EX / "survey/survey.json"),
                            "--targets", str(EX / "survey/targets.json"), "--upstream", str(FORMAL / "upstream/UPSTREAM.json")],
                           capture_output=True, text=True)
        self.assertEqual((p.returncode, json.loads(p.stdout)["verdict"]), (0, "READY"), p.stdout + p.stderr)


if __name__ == "__main__":
    unittest.main()
