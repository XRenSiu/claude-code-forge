#!/usr/bin/env python3
"""fvkit regression tests: expression safety, checking semantics, evidence integrity.

Every negative test is paired with a positive twin so a check that always says "no" (or
always "yes") cannot pass the suite.
"""
import copy
import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/accept-change/scripts"
sys.path.insert(0, str(SCRIPTS))
from fvkit.checker import check  # noqa: E402
from fvkit.contract_diff import diff, sample_universe  # noqa: E402
from fvkit.expr import Budget, compile_expr, set_budget  # noqa: E402
from fvkit.external import parse, run as run_external  # noqa: E402
from fvkit.mbt import build  # noqa: E402
from fvkit.mutate import run_mutants  # noqa: E402
from fvkit.qualify import qualify  # noqa: E402
from fvkit.receipt import make, validate  # noqa: E402
from fvkit.simulate import simulate  # noqa: E402
from fvkit.spec import Contract, Model  # noqa: E402
from fvkit.trace import check_trace  # noqa: E402
from fvkit.values import FMap, FvError  # noqa: E402

FV = [sys.executable, str(SCRIPTS / "fv.py")]

CONTRACT = {
    "schema_version": 1, "kind": "fv-contract", "id": "ticket", "version": 1, "parameters": ["STOCK", "USERS"],
    "observables": {"sold": {"type": "int", "domain": "range(0, 4)"}, "remaining": {"type": "int", "domain": "range(-2, 3)"},
                    "outcome": {"type": "map"}},
    "assumptions": [{"id": "A1", "text": "no restock"}],
    "properties": [
        {"id": "NoOversell", "kind": "invariant", "expr": "sold <= STOCK"},
        {"id": "StockNonNegative", "kind": "invariant", "expr": "remaining >= 0"},
        {"id": "Conservation", "kind": "invariant", "expr": "sold + remaining == STOCK"},
        {"id": "SoldNeverDecreases", "kind": "transition", "expr": "post.sold >= pre.sold"},
        {"id": "SomeoneCanBuy", "kind": "reachable", "expr": "sold == STOCK"},
        {"id": "Answered", "kind": "leads_to", "forall": {"u": "USERS"}, "from": "outcome[u] == 'pending'",
         "to": "outcome[u] in ('success', 'sold_out')"},
    ]}


def ticket_model(buy_guard="phase[u] == 'read' and remaining > 0", reject_guard="phase[u] == 'read' and remaining <= 0",
                 fairness=True, mutants=True):
    doc = {
        "schema_version": 1, "kind": "fv-model", "id": "ticket", "constants": {"STOCK": 1, "USERS": ["alice", "bob"]},
        "variables": {"remaining": {"init": "STOCK"}, "sold": {"init": "0"}, "phase": {"init": "{u: 'idle' for u in USERS}"},
                      "seen": {"init": "{u: 0 for u in USERS}"}, "result": {"init": "{u: 'none' for u in USERS}"}},
        "actions": {
            "request": {"params": {"u": "USERS"}, "guard": "phase[u] == 'idle'", "update": {"phase": "update(phase, u, 'requested')"}},
            "read": {"params": {"u": "USERS"}, "guard": "phase[u] == 'requested'",
                     "update": {"seen": "update(seen, u, remaining)", "phase": "update(phase, u, 'read')"}},
            "buy": {"params": {"u": "USERS"}, "guard": buy_guard,
                    "update": {"remaining": "remaining - 1", "sold": "sold + 1", "phase": "update(phase, u, 'done')",
                               "result": "update(result, u, 'success')"}},
            "reject": {"params": {"u": "USERS"}, "guard": reject_guard,
                       "update": {"phase": "update(phase, u, 'done')", "result": "update(result, u, 'sold_out')"}}},
        "fairness": [{"action": a, "kind": "weak", "per_params": True} for a in ("read", "buy", "reject")] if fairness else [],
        "terminal": "all(phase[u] in ('idle', 'done') for u in USERS)",
        "observables": {"sold": "sold", "remaining": "remaining",
                        "outcome": "{u: ('pending' if phase[u] in ('requested', 'read') else result[u]) for u in USERS}"},
    }
    if mutants:
        doc["mutants"] = [
            {"id": "check-then-act", "edits": [{"op": "set_guard", "action": "buy", "expr": "phase[u] == 'read' and seen[u] > 0"},
                                               {"op": "set_guard", "action": "reject", "expr": "phase[u] == 'read' and seen[u] <= 0"}],
             "expect_killed_by": ["NoOversell"]},
            {"id": "lost-decrement", "edits": [{"op": "drop_update", "action": "buy", "var": "remaining"}], "expect_killed_by": ["Conservation"]},
        ]
    return doc


BUGGY = dict(buy_guard="phase[u] == 'read' and seen[u] > 0", reject_guard="phase[u] == 'read' and seen[u] <= 0")


def load(doc, contract=None):
    return Model(doc, None, Contract(contract or CONTRACT))


def status(result):
    return {p["id"]: p["status"] for p in result["properties"]}


class ExpressionSafety(unittest.TestCase):
    def test_rejects_code_execution_shapes(self):
        for src in ["().__class__", "open('x')", "__import__('os')", "(lambda: 1)()", "x.__dict__", "_hidden",
                    "eval('1')", "f'{1}'", "1.5", "2 ** 10", "[x for x in range(3)].append(1)", "print(1)",
                    "{**{}}", "len(*[1])", "1 << 3", "b'x'"]:
            with self.subTest(src=src):
                with self.assertRaises(FvError):
                    compile_expr(src)

    def test_allowed_language_evaluates(self):
        env = {"m": FMap([("a", 1), ("b", 2)]), "s": frozenset({3, 1, 2})}
        self.assertEqual(compile_expr("sum(m[k] for k in m) + len(s)")(env), 6)
        self.assertEqual(compile_expr("sorted(s)")(env), (1, 2, 3))
        self.assertEqual(compile_expr("update(m, 'a', 9)['a']")(env), 9)
        self.assertEqual(compile_expr("{x for x in s if x > 1}")(env), frozenset({2, 3}))
        self.assertEqual(compile_expr("[x * 2 for x in s]")(env), (2, 4, 6))  # canonical order, not hash order
        self.assertEqual(compile_expr("{k: v + 1 for k, v in items(m)}")(env), FMap([("a", 2), ("b", 3)]))
        self.assertTrue(compile_expr("implies(False, False)")(env))
        self.assertTrue(compile_expr("not False or 1 // 0 == 0")(env))  # `or` short-circuits; function arguments do not
        self.assertEqual(compile_expr("choose({3, 1})")(env), 1)

    def test_resource_bounds(self):
        with self.assertRaises(FvError):
            compile_expr("range(10 ** 9)")
        with self.assertRaises(FvError):
            compile_expr("range(100000)")({})
        with self.assertRaises(FvError):
            compile_expr("'ab' * 100000000")({})
        with self.assertRaises(FvError):
            compile_expr("(1, 2) * 10")({})
        set_budget(Budget(0))
        try:
            with self.assertRaises(FvError):
                compile_expr("sum(1 for a in range(10000) for b in range(10000))")({})
        finally:
            set_budget(Budget())

    def test_model_vocabulary_is_checked(self):
        doc = ticket_model()
        doc["actions"]["buy"]["guard"] = "phase[u] == 'read' and stock_left > 0"
        with self.assertRaisesRegex(FvError, "unknown names"):
            load(doc)
        bad = copy.deepcopy(CONTRACT)
        bad["properties"][0]["expr"] = "phase['alice'] == 'done'"   # internal model state, not contract vocabulary
        with self.assertRaisesRegex(FvError, "outside the contract vocabulary"):
            Contract(bad)
        load(ticket_model())  # twin: the real model loads


class Checking(unittest.TestCase):
    def test_check_then_act_counterexample_is_the_shortest_interleaving(self):
        r, _, _ = check(load(ticket_model(**BUGGY)))
        self.assertEqual(r["verdict"], "FAIL")
        ce = next(p for p in r["properties"] if p["id"] == "NoOversell")["counterexample"]["steps"]
        self.assertEqual(len(ce), 7)
        self.assertEqual(ce[-1]["observed"]["sold"], 2)
        self.assertEqual([s["action"]["name"] for s in ce[1:]].count("read"), 2)

    def test_atomic_design_passes_completely(self):
        r, _, _ = check(load(ticket_model()))
        self.assertEqual((r["verdict"], r["complete"]), ("PASS", True))
        self.assertTrue(all(s == "PASS" for s in status(r).values()))

    def test_liveness_needs_fairness_and_reports_a_lasso(self):
        r, _, _ = check(load(ticket_model(fairness=False)))
        fails = [p for p in r["properties"] if p["status"] == "FAIL"]
        self.assertEqual({p["property"] for p in fails}, {"Answered"})
        ce = fails[0]["counterexample"]
        self.assertEqual(ce["kind"], "lasso")
        self.assertTrue(ce["stutter"])
        self.assertEqual(r["verdict"], "FAIL")

    def test_weak_versus_strong_fairness(self):
        contract = {"schema_version": 1, "kind": "fv-contract", "id": "lock", "version": 1,
                    "observables": {"pc": {"type": "str"}},
                    "properties": [{"id": "Acquires", "kind": "leads_to", "from": "pc == 'waiting'", "to": "pc == 'done'"}]}

        def model(kind):
            return Model({"schema_version": 1, "kind": "fv-model", "id": "lock",
                          "variables": {"busy": {"init": "False"}, "pc": {"init": "'waiting'"}},
                          "actions": {"toggle": {"update": {"busy": "not busy"}},
                                      "acquire": {"guard": "pc == 'waiting' and not busy", "update": {"pc": "'done'"}}},
                          "fairness": [{"action": "toggle", "kind": "weak"}, {"action": "acquire", "kind": kind}],
                          "observables": {"pc": "pc"}}, None, Contract(contract))
        weak, _, _ = check(model("weak"))
        strong, _, _ = check(model("strong"))
        self.assertEqual(weak["verdict"], "FAIL")
        ce = weak["properties"][0]["counterexample"]
        self.assertFalse(ce["stutter"])
        self.assertEqual([s["action"]["name"] for s in ce["cycle"]], ["toggle", "toggle"])
        self.assertEqual(strong["verdict"], "PASS")

    def test_bounded_runs_never_claim_pass(self):
        m = load(ticket_model())
        r, _, _ = check(m, max_states=8)
        self.assertEqual(r["verdict"], "BOUNDED_PASS")
        self.assertFalse(r["complete"])
        self.assertEqual(r["exhaustive_depth"], 2)
        self.assertIn("UNKNOWN", status(r).values())
        d, _, _ = check(m, max_depth=3)
        self.assertEqual((d["verdict"], d["exhaustive_depth"]), ("BOUNDED_PASS", 3))

    def test_deadlock_witness_and_dead_action(self):
        doc = ticket_model(mutants=False)
        doc.pop("terminal")
        r, _, _ = check(load(doc))
        self.assertEqual(r["deadlock"]["status"], "FAIL")
        doc = ticket_model(mutants=False)
        doc["actions"]["buy"]["guard"] = "False"
        r, _, _ = check(load(doc))
        self.assertEqual(status(r)["SomeoneCanBuy"], "FAIL")
        self.assertIn("buy", r["coverage"]["dead_actions"])

    def test_symmetry_preserves_verdicts_and_replays_concretely(self):
        c = copy.deepcopy(CONTRACT)
        c["properties"] = [p for p in c["properties"] if p["kind"] != "leads_to"]
        for kw in ({}, BUGGY):
            doc = ticket_model(mutants=False, **kw)
            doc["constants"] = {"STOCK": 2, "USERS": ["u1", "u2", "u3"]}
            doc["symmetry"] = ["USERS"]
            with_sym, _, _ = check(load(doc, c))
            without, _, _ = check(load(doc, c), symmetry=False)
            self.assertEqual(status(with_sym), status(without))
            self.assertLess(with_sym["stats"]["states"], without["stats"]["states"])

    def test_symmetry_refuses_named_members(self):
        doc = ticket_model(mutants=False)
        doc["symmetry"] = ["USERS"]
        doc["actions"]["request"]["guard"] = "phase[u] == 'idle' and u != 'alice'"
        with self.assertRaisesRegex(FvError, "symmetry would be unsound"):
            load(doc)

    def test_simulation_is_never_a_pass(self):
        self.assertEqual(simulate(load(ticket_model()), seed=3, runs=50)["verdict"], "NO_VIOLATION_SAMPLED")
        bad = simulate(load(ticket_model(**BUGGY)), seed=3, runs=500)
        self.assertEqual(bad["verdict"], "FAIL")


class Qualification(unittest.TestCase):
    def test_qualified_and_mutant_rules(self):
        q = qualify(load(ticket_model()))
        self.assertEqual(q["verdict"], "QUALIFIED", q["result"]["reasons"])
        none = qualify(load(ticket_model(mutants=False)))
        self.assertIn("no declared mutant", " ".join(none["result"]["reasons"]))
        doc = ticket_model()
        doc["mutants"][1]["expect_killed_by"] = ["SoldNeverDecreases"]   # caught, but only by other rules
        wrong = run_mutants(load(doc))
        self.assertEqual(wrong["declared"][1]["status"], "KILLED_BY_OTHER")
        self.assertEqual(qualify(load(doc))["verdict"], "NOT_QUALIFIED")
        doc = ticket_model()
        doc["mutants"][0]["edits"] = [{"op": "set_guard", "action": "buy", "expr": "nonsense_name"}]
        self.assertEqual(run_mutants(load(doc))["declared"][0]["status"], "ERROR")

    def test_counterexample_and_bounded_runs_do_not_qualify(self):
        self.assertEqual(qualify(load(ticket_model(**BUGGY)))["verdict"], "NOT_QUALIFIED")
        bounded = qualify(load(ticket_model()), {"max_states": 8})
        self.assertEqual(bounded["verdict"], "NOT_QUALIFIED")
        allowed = qualify(load(ticket_model()), {"max_states": 8, "allow_bounded": True, "min_depth": 2})
        self.assertNotIn("bounded", " ".join(allowed["result"]["reasons"]))
        # mutants run under the same bound: a truncated run cannot fake a kill
        self.assertIn("check-then-act UNKNOWN", " ".join(allowed["result"]["reasons"]))
        deeper = qualify(load(ticket_model()), {"max_states": 8, "allow_bounded": True, "min_depth": 5})
        self.assertIn("required 5", " ".join(deeper["result"]["reasons"]))

    def test_auto_mutants_report_survivors(self):
        res = run_mutants(load(ticket_model()), auto=True)
        self.assertGreater(res["auto_summary"]["total"], 5)
        self.assertGreater(res["auto_summary"]["killed"], 0)
        self.assertIn("auto:request:guard=True", [r["id"] for r in res["auto"]])


class Receipts(unittest.TestCase):
    def setUp(self):
        self.m = load(ticket_model(**BUGGY))
        r, _, _ = check(self.m)
        self.receipt = make("check", {"model": self.m.identity(), "contract": self.m.contract.identity()}, r["settings"], r,
                            r["verdict"], "E2", "t0")

    def test_valid_receipt_and_rerun(self):
        out = validate(self.receipt, model=self.m, contract=self.m.contract, rerun=True)
        self.assertTrue(out["valid"] and out["reexecuted"])

    def test_tampering_is_detected(self):
        r = copy.deepcopy(self.receipt)
        r["verdict"] = "PASS"
        with self.assertRaises(FvError):
            validate(r, model=self.m)
        r = copy.deepcopy(self.receipt)
        ce = next(p for p in r["result"]["properties"] if p["id"] == "NoOversell")["counterexample"]["steps"]
        ce[-1]["action"]["params"]["u"] = "alice"   # a step that is not enabled
        with self.assertRaises(FvError):
            validate(r, model=self.m)
        r = copy.deepcopy(self.receipt)
        r["result"]["stats"]["states"] += 1
        with self.assertRaisesRegex(FvError, "state count"):
            validate(r, model=self.m, rerun=True)
        with self.assertRaisesRegex(FvError, "different model"):
            validate(self.receipt, model=load(ticket_model()))
        r = copy.deepcopy(self.receipt)
        r["authority"] = "accepted_for_stage"
        with self.assertRaises(FvError):
            validate(r)
        with self.assertRaisesRegex(FvError, "below the required"):
            validate(self.receipt, min_level="E3")


class Traces(unittest.TestCase):
    def events(self, steps):
        out = [{"init": True, "observed": {"sold": 0, "remaining": 1, "outcome": {"alice": "none", "bob": "none"}}, "_line": 1}]
        for n, (action, u, obs) in enumerate(steps, start=2):
            ev = {"action": action, "params": {"u": u}, "observed": obs, "_line": n}
            if action.startswith("!"):
                ev["action"], ev["rejected"] = action[1:], True
            out.append(ev)
        return out

    def test_conforming_and_refused_steps(self):
        m = load(ticket_model())
        steps = [("request", "alice", {}), ("read", "alice", {}), ("request", "bob", {}), ("read", "bob", {}),
                 ("buy", "alice", {"sold": 1}), ("!buy", "bob", {"sold": 1, "remaining": 0}),
                 ("reject", "bob", {"sold": 1, "remaining": 0, "outcome": {"alice": "success", "bob": "sold_out"}})]
        self.assertEqual(check_trace(m, self.events(steps))["verdict"], "CONFORMS")

    def test_oversell_trace_is_nonconformant_and_monitored(self):
        m = load(ticket_model())
        full = {"sold": 2, "remaining": -1, "outcome": {"alice": "success", "bob": "success"}}
        steps = [("request", "alice", {}), ("read", "alice", {}), ("request", "bob", {}), ("read", "bob", {}),
                 ("buy", "alice", {"sold": 1}), ("buy", "bob", full)]
        r = check_trace(m, self.events(steps))
        self.assertEqual(r["verdict"], "NONCONFORMANT")
        self.assertEqual(r["failed_at_line"], 7)
        self.assertEqual({v["property"] for v in r["property_violations"]}, {"NoOversell", "StockNonNegative"})
        self.assertTrue(r["diagnostic"]["consistent_model_states"])

    def test_hidden_steps_and_bad_observables(self):
        m = load(ticket_model())
        skip = self.events([("buy", "alice", {"sold": 1})])
        self.assertEqual(check_trace(m, skip)["verdict"], "NONCONFORMANT")
        self.assertEqual(check_trace(m, skip, hidden_steps=2)["verdict"], "CONFORMS")
        with self.assertRaisesRegex(FvError, "unknown observable"):
            check_trace(m, self.events([("request", "alice", {"phase": 1})]))


class ContractDiff(unittest.TestCase):
    def variant(self, **changes):
        c = copy.deepcopy(CONTRACT)
        for pid, expr in changes.items():
            next(p for p in c["properties"] if p["id"] == pid)["expr"] = expr
        return Contract(c)

    def test_weakening_is_detected_on_finite_domains(self):
        consts = load(ticket_model()).constants
        old = Contract(CONTRACT)
        self.assertEqual(diff(old, self.variant(NoOversell="sold <= STOCK + 1"), consts)["verdict"], "WEAKENED")
        self.assertEqual(diff(old, self.variant(NoOversell="sold < STOCK + 1"), consts)["verdict"], "NOT_WEAKENED")
        self.assertEqual(diff(old, self.variant(NoOversell="sold == 0"), consts)["verdict"], "NOT_WEAKENED")
        c = copy.deepcopy(CONTRACT)
        c["properties"] = c["properties"][1:]
        self.assertEqual(diff(old, Contract(c), consts)["verdict"], "WEAKENED")
        c = copy.deepcopy(CONTRACT)
        c["assumptions"].append({"id": "A2", "text": "only one buyer at a time"})
        self.assertEqual(diff(old, Contract(c), consts)["verdict"], "WEAKENED")
        c = copy.deepcopy(CONTRACT)
        c["properties"][5]["forall"] = {"u": "USERS[:1]"}
        self.assertEqual(diff(old, Contract(c), consts)["verdict"], "WEAKENED")

    def test_without_domains_sampling_or_unknown(self):
        c = copy.deepcopy(CONTRACT)
        for o in c["observables"].values():
            o.pop("domain", None)
        old = Contract(c)
        c2 = copy.deepcopy(c)
        c2["properties"][1]["expr"] = "remaining >= -1"
        new = Contract(c2)
        consts = load(ticket_model()).constants
        self.assertEqual(diff(old, new, consts)["verdict"], "UNKNOWN")
        m = Model(ticket_model(), None, new)
        sampled = diff(old, new, consts, sample_universe(m))
        self.assertEqual(sampled["verdict"], "WEAKENED")
        self.assertTrue(sampled["sampled"])


class External(unittest.TestCase):
    def fake(self, d, body):
        p = Path(d) / "engine"
        p.write_text("#!/bin/sh\n" + body)
        p.chmod(p.stat().st_mode | stat.S_IEXEC)
        return str(p)

    def test_parsers_encode_engine_semantics(self):
        self.assertEqual(parse("tlc", "Model checking completed. No error has been found.\n12 states generated, 7 distinct states found")["verdict"], "PASS")
        self.assertEqual(parse("tlc", "Error: Invariant NoOversell is violated.")["violated"], ["NoOversell"])
        self.assertEqual(parse("tlc", "")["verdict"], "ERROR")
        self.assertEqual(parse("quint-verify", "[ok] No violation found (1234ms).")["verdict"], "BOUNDED_PASS")
        self.assertEqual(parse("quint-run", "[ok] No violation found (1234ms).")["verdict"], "NO_VIOLATION_SAMPLED")
        self.assertEqual(parse("quint-run", "[violation] Found an issue")["verdict"], "FAIL")
        self.assertEqual(parse("apalache", "The outcome is: NoError")["verdict"], "BOUNDED_PASS")
        self.assertEqual(parse("apalache", "The outcome is: NoError", exit_code=1)["verdict"], "ERROR")

    def test_run_records_raw_output_and_reparse_catches_tampering(self):
        with tempfile.TemporaryDirectory() as d:
            spec = Path(d) / "Spec.tla"
            spec.write_text("---- MODULE Spec ----\n====\n")
            tool = self.fake(d, "echo 'Model checking completed. No error has been found.'\n")
            receipt = run_external("tlc", [spec], Path(d) / "out", tool=tool)
            self.assertEqual((receipt["verdict"], receipt["evidence_level"]), ("PASS", "E2"))
            validate(receipt, base_dir=Path(d) / "out")
            (Path(d) / "out/stdout.txt").write_text("Error: Invariant X is violated.\n")
            with self.assertRaises(FvError):
                validate(receipt, base_dir=Path(d) / "out")
            missing = run_external("tlc", [spec], Path(d) / "out2", tool=str(Path(d) / "absent"))
            self.assertEqual(missing["verdict"], "ERROR")
            r = copy.deepcopy(receipt)
            r["settings"]["engine"] = "quint-run"
            r["evidence_level"] = "E1"
            with self.assertRaises(FvError):
                validate(r)


class Cli(unittest.TestCase):
    def run_fv(self, *args, cwd=None):
        return subprocess.run(FV + list(args), capture_output=True, text=True, cwd=cwd)

    def test_end_to_end_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "contract.json").write_text(json.dumps(CONTRACT))
            good, bad = ticket_model(), ticket_model(**BUGGY)
            for name, doc in (("good.json", good), ("bad.json", bad)):
                doc["contract"] = "contract.json"
                (d / name).write_text(json.dumps(doc))
            self.assertEqual(self.run_fv("check", "--model", str(d / "good.json")).returncode, 0)
            self.assertEqual(self.run_fv("check", "--model", str(d / "bad.json"), "--out", str(d / "bad-r.json")).returncode, 1)
            self.assertEqual(self.run_fv("check", "--model", str(d / "good.json"), "--max-states", "5").returncode, 3)
            self.assertEqual(self.run_fv("qualify", "--model", str(d / "good.json"), "--out", str(d / "q.json")).returncode, 0)
            v = self.run_fv("validate", str(d / "q.json"), "--model", str(d / "good.json"), "--rerun", "--min-level", "E2")
            self.assertEqual(v.returncode, 0, v.stderr)
            self.assertEqual(self.run_fv("check", "--model", str(d / "bad.json"), "--out", str(d / "bad-r.json")).returncode, 2,
                             "receipts are never overwritten")
            g = self.run_fv("gen-tests", "--model", str(d / "good.json"), "--strategy", "transitions,counterexamples",
                            "--counterexample", str(d / "bad-r.json"), "--out", str(d / "vectors.json"))
            self.assertEqual(g.returncode, 0, g.stderr)
            vectors = json.loads((d / "vectors.json").read_text())
            replay = [v for v in vectors["vectors"] if v["id"].startswith("replay:")][0]
            self.assertEqual([s["enabled"] for s in replay["steps"]][-1], False)
            self.assertEqual(self.run_fv("lint", "--model", str(d / "missing.json")).returncode, 2)

    def test_init_skeleton_qualifies(self):
        with tempfile.TemporaryDirectory() as d:
            try:
                import yaml  # noqa: F401
            except ImportError:
                self.skipTest("PyYAML not installed; scaffold writes YAML")
            self.assertEqual(self.run_fv("init", "--dir", d + "/f", "--name", "x", "--entrance", "spec-first").returncode, 0)
            self.assertEqual(self.run_fv("qualify", "--model", d + "/f/model.yaml").returncode, 0)

    def test_source_map_lifecycle(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            git = lambda *a: subprocess.run(["git", "-C", str(d), *a], check=True, capture_output=True)  # noqa: E731
            git("init", "-q")
            (d / "svc.py").write_text("def buy():\n    db.execute('UPDATE t SET n = n - 1 WHERE n > 0')\n")
            (d / "contract.json").write_text(json.dumps(CONTRACT))
            doc = ticket_model()
            doc["contract"] = "contract.json"
            (d / "model.json").write_text(json.dumps(doc))
            sm = {"schema_version": 1, "kind": "fv-source-map", "model": "model.json",
                  "actions": {"buy": {"locations": [{"path": "svc.py", "anchor": "WHERE n > 0"}]}},
                  "environment_actions": {"request": "user intent", "read": "page view", "reject": "covered by the same UPDATE"},
                  "protected_paths": ["svc.py"]}
            (d / "map.json").write_text(json.dumps(sm))
            git("add", "-A")
            git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")
            verify = lambda: json.loads(self.run_fv("source-map", "verify", "--map", str(d / "map.json"), "--model", str(d / "model.json")).stdout)  # noqa: E731
            self.assertEqual(verify()["status"], "STALE")
            s = self.run_fv("source-map", "sync", "--map", str(d / "map.json"), "--model", str(d / "model.json"), "--by", "rev", "--reason", "ok")
            self.assertEqual(s.returncode, 0, s.stderr)
            self.assertEqual(verify()["status"], "FRESH")
            (d / "svc.py").write_text((d / "svc.py").read_text().replace("WHERE n > 0", "WHERE n >= 0"))
            self.assertEqual(verify()["status"], "BROKEN")
            self.assertEqual(self.run_fv("source-map", "sync", "--map", str(d / "map.json"), "--model", str(d / "model.json"),
                                         "--by", "rev", "--reason", "x").returncode, 2)


class Generation(unittest.TestCase):
    """AI-written inventory, rules and models are checked, compared and adopted only with rulings."""

    PRD = "# Ticket\n\n| id | must |\n|---|---|\n| R1 | sold must never exceed STOCK and remaining must stay non-negative |\n" \
          "| R2 | every pending request must eventually be answered |\n\nAssumption: there is no restock during the sale.\n"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.d = Path(self.tmp.name)
        (self.d / "prd.md").write_text(self.PRD)
        self.inventory = {"schema_version": 1, "kind": "fv-requirements", "id": "t", "sources": [{"id": "prd", "path": "prd.md"}],
                          "requirements": [
                              {"id": "R1", "text": "no oversell", "source": {"doc": "prd", "quote": "sold must never exceed STOCK and remaining must stay non-negative"}},
                              {"id": "R2", "text": "answered", "source": {"doc": "prd", "quote": "every pending request must eventually be answered"}}],
                          "assumptions": [{"id": "A1", "text": "no restock", "source": {"doc": "prd", "quote": "there is no restock during the sale"}}]}
        self.write("requirements.json", self.inventory)

    def write(self, name, doc):
        p = self.d / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(doc))
        return p

    def contract(self, name, r1="sold <= STOCK and remaining >= 0", r2_to="outcome[u] in ('success', 'sold_out')", extra_assumption=True):
        c = copy.deepcopy(CONTRACT)
        c["requirements"] = "../requirements.json" if "/" in name else "requirements.json"
        c["assumptions"] = [{"id": "A-NR", "text": "no restock", "source": "A1"}] + (
            [{"id": "A-FAIR", "text": "fair scheduling", "source": "environment"}] if extra_assumption else [])
        c["properties"] = [
            {"id": "Safe", "kind": "invariant", "expr": r1, "source": "R1", "text": "no oversell"},
            {"id": "Witness", "kind": "reachable", "expr": "sold == STOCK", "source": "R1", "text": "can sell"},
            {"id": "Answered", "kind": "leads_to", "forall": {"u": "USERS"}, "from": "outcome[u] == 'pending'", "to": r2_to,
             "source": "R2", "text": "answered"}]
        return self.write(name, c)

    def test_inventory_rejects_invented_quotes_and_silent_omissions(self):
        from fvkit.generation import Requirements
        self.assertEqual(Requirements(self.d / "requirements.json").check()["verdict"], "COMPLETE")
        bad = copy.deepcopy(self.inventory)
        bad["requirements"][0]["source"]["quote"] = "sold must never exceed twice the STOCK"   # nobody wrote this
        self.write("bad.json", bad)
        self.assertIn("not verbatim", " ".join(Requirements(self.d / "bad.json").check()["issues"]))
        dropped = copy.deepcopy(self.inventory)
        dropped["requirements"] = dropped["requirements"][:1]                                   # R2 silently lost
        self.write("dropped.json", dropped)
        self.assertIn("not inventoried", " ".join(Requirements(self.d / "dropped.json").check()["issues"]))
        dropped["out_of_scope"] = [{"text": "liveness later", "reason": "phase 2", "source": {"doc": "prd", "quote": "every pending request must eventually be answered"}}]
        self.write("scoped.json", dropped)
        self.assertEqual(Requirements(self.d / "scoped.json").check()["verdict"], "COMPLETE")   # twin: stated, not dropped

    def test_traceability(self):
        from fvkit.generation import requirements_for, trace_rules
        from fvkit.spec import load_contract
        c = load_contract(self.contract("c.json"))
        self.assertEqual(trace_rules(c, requirements_for(c))["verdict"], "TRACEABLE")
        doc = json.loads((self.d / "c.json").read_text())
        doc["properties"] = doc["properties"][:2]                        # R2 never formalized
        doc["properties"][0]["source"] = "R9"                            # cites a requirement nobody stated
        self.write("c2.json", doc)
        c2 = load_contract(self.d / "c2.json")
        issues = " ".join(trace_rules(c2, requirements_for(c2))["issues"])
        self.assertIn("R2 is neither formalized nor dispositioned", issues)
        self.assertIn("unknown requirement R9", issues)
        doc["properties"][0]["source"] = "R1"
        doc["dispositions"] = [{"requirement": "R2", "status": "covered_by_tests", "reason": "E2E covers answering"}]
        self.write("c3.json", doc)
        c3 = load_contract(self.d / "c3.json")
        self.assertEqual(trace_rules(c3, requirements_for(c3))["verdict"], "TRACEABLE")

    def test_rules_divergence_finds_semantic_differences_with_a_witness(self):
        from fvkit.generation import Requirements, rules_divergence
        from fvkit.spec import load_contract
        reqs = Requirements(self.d / "requirements.json")
        consts = load(ticket_model()).constants
        a, same = load_contract(self.contract("a/c.json")), load_contract(self.contract("s/c.json", r1="not (sold > STOCK or remaining < 0)"))
        agreed = rules_divergence(reqs, [("A", a), ("S", same)], consts)
        self.assertEqual(agreed["verdict"], "AGREED", agreed["items"])   # an equivalent rewrite is not a disagreement
        weak = load_contract(self.contract("b/c.json", r1="sold <= STOCK", r2_to="outcome[u] == 'success'", extra_assumption=False))
        report = rules_divergence(reqs, [("A", a), ("B", weak)], consts)
        types = {i["type"] for i in report["items"]}
        self.assertEqual(types, {"semantic", "unverified_equivalence", "assumptions"})
        semantic = next(i for i in report["items"] if i["type"] == "semantic")
        self.assertEqual(semantic["by_candidate"], {"A": False, "B": True})
        with self.assertRaises(FvError):
            rules_divergence(reqs, [("A", a)], consts)                    # one generator is not a comparison
        doc = json.loads((self.d / "a/c.json").read_text())
        doc["properties"] = doc["properties"][:2]
        doc["dispositions"] = [{"requirement": "R2", "status": "covered_by_tests", "reason": "left to E2E"}]
        skipped = load_contract(self.write("d/c.json", doc))
        cov = rules_divergence(reqs, [("A", a), ("D", skipped)], consts)
        item = next(i for i in cov["items"] if i["type"] == "coverage")
        self.assertEqual((item["requirement"], item["not_formalized_by"]), ("R2", {"D": "covered_by_tests"}))

    def test_adoption_needs_rulings_comparison_and_a_complete_review(self):
        from fvkit.generation import Requirements, resolve, rules_divergence, rules_evidence
        from fvkit.spec import load_contract
        from test_upstream_methods import intake_doc, review_doc
        reqs = Requirements(self.d / "requirements.json")
        consts = load(ticket_model()).constants
        a_path, b_path = self.contract("a/c.json"), self.contract("b/c.json", r1="sold <= STOCK")
        report = rules_divergence(reqs, [("A", load_contract(a_path)), ("B", load_contract(b_path))], consts)
        for c in report["candidates"]:
            c["path"] = str(Path(c["path"]).resolve())
        rp = self.write("div.json", report)
        final = load_contract(self.contract("c.json"))
        it = self.write("intake.json", intake_doc(reqs))
        finding = {"id": "F-1", "severity": "MAJOR", "class": "CONTENT", "requirement": "R1", "property": "Safe",
                   "claim": "Safe only holds without restock", "evidence": "prd.md: Assumption line", "suggested_change": "state it"}
        review = review_doc(final, reqs, verdict="APPROVE-WITH-EDITS", findings=[finding])
        rv = self.write("review.json", review)
        reasons = " ".join(rules_evidence(final, reqs, rp, rv, it)["reasons"])
        self.assertIn("without a ruling", reasons)
        self.assertIn("needs the author's separate triage", reasons)
        self.assertIn("no rules intake", " ".join(rules_evidence(final, reqs, rp, rv)["reasons"]))
        with self.assertRaises(FvError):
            resolve(rp, "D1", "adopt A", "agent", "delegated_agent")     # an agent cannot rule without the human's words
        for item in report["items"]:
            resolve(rp, item["id"], "adopt A", "owner", "human")
        import hashlib
        triage = {"schema_version": 1, "kind": "fv-review-triage", "review_digest": "sha256:" + hashlib.sha256(rv.read_bytes()).hexdigest(),
                  "procedure": [], "contract_before": final.digest, "contract_after": final.digest,
                  "dispositions": [{"finding": "F-1", "disposition": "ASK-HUMAN", "detail": "is restock possible?"}]}
        from test_upstream_methods import cite_all
        triage["procedure"] = cite_all("fv-review-triage")
        tr = self.write("triage.json", triage)
        self.assertIn("waiting for a human", " ".join(rules_evidence(final, reqs, rp, rv, it, tr)["reasons"]))
        triage["dispositions"][0].update(disposition="REJECT-FINDING", evidence="assumption A-NR already states no restock")
        self.write("triage.json", triage)
        self.assertEqual(rules_evidence(final, reqs, rp, rv, it, tr)["verdict"], "READY")
        review["review_complete"]["findings_count"] = 0                  # a truncated review
        self.write("review.json", review)
        self.assertIn("truncated", " ".join(rules_evidence(final, reqs, rp, rv, it, tr)["reasons"]))
        review["review_complete"]["findings_count"] = 1
        self.write("review.json", review)
        other = load_contract(self.contract("other.json", r1="sold <= STOCK + 1"))
        self.assertIn("not among the compared candidates", " ".join(rules_evidence(other, reqs, rp, rv, it, tr)["reasons"]))
        b_path.write_text(b_path.read_text().replace("sold <= STOCK", "sold < STOCK"))
        self.assertIn("changed after the divergence", " ".join(rules_evidence(final, reqs, rp, rv, it, tr)["reasons"]))
        single = json.loads(rp.read_text())
        single["candidates"] = single["candidates"][:1]                   # one generator compared with itself
        sp = self.write("single.json", single)
        self.assertIn("fewer than 2", " ".join(rules_evidence(final, reqs, sp, rv, it, tr)["reasons"]))
        doc = json.loads((self.d / "c.json").read_text())                # a High-impact property requirement left as a disposition
        doc["properties"] = doc["properties"][2:]
        doc["dispositions"] = [{"requirement": "R1", "status": "covered_by_tests", "reason": "E2E"}]
        skipped = load_contract(self.write("skipped.json", doc))
        self.assertIn("High-impact requirement R1", " ".join(rules_evidence(skipped, reqs, rp, rv, it, tr)["reasons"]))

    def test_model_divergence_compares_what_an_observer_sees(self):
        from fvkit.generation import model_divergence
        same = model_divergence([("A", load(ticket_model())), ("A2", load(ticket_model(mutants=False)))])
        self.assertEqual(same["verdict"], "AGREED")
        bad = model_divergence([("A", load(ticket_model())), ("B", load(ticket_model(**BUGGY)))])
        self.assertEqual(bad["verdict"], "DIVERGENT")
        verdicts = [i for i in bad["items"] if i["type"] == "verdict"]
        self.assertIn("NoOversell", {i["property"] for i in verdicts})
        reach = [i for i in bad["items"] if i["type"] == "reachable"]
        self.assertTrue(any(i["observed"]["sold"] == 2 and i["in_candidates"] == ["B"] for i in reach))


class VectorsDeterminism(unittest.TestCase):
    def test_same_seed_same_vectors(self):
        m = load(ticket_model())
        a = build(m, ["random", "transitions"], seed=7)
        b = build(m, ["random", "transitions"], seed=7)
        self.assertEqual(a, b)
        env = dict(os.environ, PYTHONHASHSEED="12345")
        code = textwrap.dedent("""
            import json, sys
            sys.path.insert(0, %r)
            sys.path.insert(0, %r)
            from test_formal import load, ticket_model
            from fvkit.checker import check
            r, _, _ = check(load(ticket_model(buy_guard="phase[u] == 'read' and seen[u] > 0", reject_guard="phase[u] == 'read' and seen[u] <= 0")))
            print(json.dumps([p.get('counterexample') for p in r['properties']], sort_keys=True))
        """ % (str(SCRIPTS), str(Path(__file__).parent)))
        outs = {subprocess.run([sys.executable, "-c", code], env=dict(env, PYTHONHASHSEED=str(seed)), capture_output=True, text=True).stdout
                for seed in (1, 2, 3)}
        self.assertEqual(len(outs), 1, "results must not depend on hash randomisation")


if __name__ == "__main__":
    unittest.main()
