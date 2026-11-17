"""Formal verification inside the AI-DLC lifecycle, over a real temporary Git project.

The project is the formal-verify example (contract, models, real SQLite implementation,
harness). Each refusal is paired with the same step succeeding once the evidence exists,
so a guard that always says "no" cannot pass.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
STATE = PLUGIN / "skills/ai-dlc/scripts/aidlc_state.py"
LOCK = PLUGIN / "skills/ai-dlc/scripts/lock_done_when.py"
FV = PLUGIN / "skills/formal-verify/scripts/fv.py"
EXAMPLE = PLUGIN / "skills/formal-verify/assets/example-ticket"
F = "specs/ticket/formal"


class FormalLifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        shutil.copytree(EXAMPLE, self.repo / F)
        (self.repo / ".gitignore").write_text(".aidlc/\n")
        (self.repo / "done_when.yaml").write_text("schema_version: 2\n")
        self.git("init", "-q")
        self.commit("init")
        self.sh(FV, "source-map", "sync", "--map", F + "/source-map.yaml", "--model", F + "/model.yaml",
                "--by", "reviewer", "--reason", "anchors reviewed")
        self.commit("reviewed mapping")
        self.base = self.git("rev-parse", "HEAD").stdout.strip()

    # ---- helpers -----------------------------------------------------------------------
    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), "-c", "user.email=t@t", "-c", "user.name=t", *args],
                              check=True, capture_output=True, text=True)

    def commit(self, msg):
        self.git("add", "-A")
        self.git("commit", "-qm", msg)

    def sh(self, script, *args, ok=True):
        run = subprocess.run([sys.executable, str(script), *args], cwd=self.repo, capture_output=True, text=True)
        if ok:
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        return run

    def state(self, *args):
        run = subprocess.run([sys.executable, str(STATE), *args], cwd=self.repo, capture_output=True, text=True)
        try:
            return run.returncode, json.loads(run.stdout)
        except ValueError:
            return run.returncode, {"raw": run.stdout + run.stderr}

    def unmet(self, stage, slug="t"):
        code, out = self.state("formal", "check", "--slug", slug, "--stage", stage)
        self.assertIn(code, (0, 1), out)
        return " | ".join(out["unmet"])

    def sign(self, *files):
        self.sh(LOCK, "sign", "--by", "owner", "--signer-kind", "human", "--stage", "g2", "--out", ".done_when.lock", *files)
        self.state("set", "--slug", "t", "lock.path=.done_when.lock")

    def configure(self):
        self.state("init", "--slug", "t", "--title", "ticket")
        code, out = self.state("formal", "configure", "--slug", "t", "--module", "ticket", "--contract", F + "/contract.yaml",
                               "--model", F + "/model.yaml", "--source-map", F + "/source-map.yaml", "--min-level", "E3")
        self.assertEqual(code, 0, out)

    def traces(self, variant="atomic"):
        out = Path(tempfile.mkdtemp(prefix="traces-" + variant + "-", dir=self.tmp.name))
        run = subprocess.run([sys.executable, str(self.repo / F / "impl/harness.py"), "--vectors", str(self.repo / F / "vectors.json"),
                              "--out", str(out), "--variant", variant], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0 if variant == "atomic" else 1, run.stderr)
        return sorted(str(p) for p in out.glob("*.jsonl"))

    # ---- tests -------------------------------------------------------------------------
    def test_design_gate_contract_lock_and_force_cannot_bypass(self):
        self.configure()
        text = self.unmet("implement")
        self.assertIn("no G2 lock", text)
        self.assertIn("no qualification", text)
        code, out = self.state("advance", "--slug", "t", "implement", "--force", "--reason", "skip the model")
        self.assertEqual(code, 1)
        self.assertFalse(out["force_allowed"])
        self.sign("done_when.yaml")
        self.assertIn("is not in the g2 lock", self.unmet("cards"))
        self.sign("done_when.yaml", F + "/contract.yaml")
        self.assertEqual(self.unmet("cards"), "")
        code, out = self.state("formal", "qualify", "--slug", "t")
        self.assertEqual((code, out["verdict"]), (0, "QUALIFIED"), out)
        self.assertEqual(self.unmet("implement"), "")
        code, out = self.state("advance", "--slug", "t", "implement", "--force", "--reason", "other prerequisites are out of scope here")
        self.assertEqual(code, 0, out)   # twin: the formal guard itself is now satisfied

    def test_weakened_contract_or_changed_model_invalidates_the_design_gate(self):
        self.configure()
        self.sign("done_when.yaml", F + "/contract.yaml")
        self.state("formal", "qualify", "--slug", "t")
        contract = self.repo / F / "contract.yaml"
        original = contract.read_text()
        contract.write_text(original.replace('expr: "sold <= STOCK"', 'expr: "sold <= STOCK + 1"'))
        text = self.unmet("implement")
        self.assertIn("changed after it was locked", text)
        self.assertIn("qualification is not current", text)
        contract.write_text(original)
        self.assertEqual(self.unmet("implement"), "")
        model = self.repo / F / "model.yaml"
        model.write_text(model.read_text().replace("guard: \"phase[u] == 'read' and remaining > 0\"",
                                                   "guard: \"phase[u] == 'read' and seen[u] > 0\""))
        self.assertIn("different model", self.unmet("implement"))
        code, out = self.state("formal", "qualify", "--slug", "t")
        self.assertEqual((code, out["verdict"]), (1, "NOT_QUALIFIED"))   # the old design brings back the counterexample

    def test_implementation_gate_needs_current_conformance(self):
        self.configure()
        self.sign("done_when.yaml", F + "/contract.yaml")
        self.state("formal", "qualify", "--slug", "t")
        self.assertIn("E3 needs implementation evidence", self.unmet("pr"))
        code, out = self.state("formal", "conform", "--slug", "t", "--traces", *self.traces("check-then-act"))
        self.assertEqual((code, out["verdict"]), (1, "NONCONFORMANT"))
        self.assertIn("conformance is not current", self.unmet("pr"))
        code, out = self.state("formal", "conform", "--slug", "t", "--traces", *self.traces())
        self.assertEqual((code, out["verdict"]), (0, "CONFORMS"), out)
        self.assertEqual(self.unmet("pr"), "")
        self.assertEqual(self.unmet("merge"), "")
        impl = self.repo / F / "impl/tickets.py"
        impl.write_text(impl.read_text() + "\n# refactor later\n")
        self.assertIn("source map is STALE", self.unmet("pr"))
        # Re-reviewing the mapping is not new implementation evidence: the traces predate the code.
        self.commit("refactor")
        self.sh(FV, "source-map", "sync", "--map", F + "/source-map.yaml", "--model", F + "/model.yaml",
                "--by", "reviewer", "--reason", "comment only")
        self.commit("re-reviewed mapping")
        self.assertIn("mapped code changed since the conformance traces", self.unmet("pr"))
        code, out = self.state("formal", "conform", "--slug", "t", "--traces", *self.traces())
        self.assertEqual(self.unmet("pr"), "")

    def test_signed_waiver_lowers_a_module_and_forces_g3(self):
        self.configure()
        self.sign("done_when.yaml", F + "/contract.yaml")
        self.state("formal", "qualify", "--slug", "t")
        code, _ = self.state("formal", "waive", "--slug", "t", "--module", "ticket", "--level", "E2",
                             "--reason", "harness lands next sprint", "--by", "agent", "--signer-kind", "delegated_agent")
        self.assertEqual(code, 2)   # a delegated waiver without the human's words is refused
        code, out = self.state("formal", "waive", "--slug", "t", "--module", "ticket", "--level", "E2",
                               "--reason", "harness lands next sprint", "--by", "owner", "--signer-kind", "human")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.unmet("pr"), "")
        _, st = self.state("show", "--slug", "t")
        self.assertTrue(st["gates"]["g3"]["required"])

    def test_policy_derives_required_modules_from_the_diff(self):
        self.state("init", "--slug", "p", "--title", "policy run")
        root = self.repo / "verification"
        root.mkdir()
        (root / "policy.yaml").write_text("\n".join([
            "schema_version: 1", "kind: fv-policy", "modules:", "  - id: ticket-ordering", "    risk: concurrency",
            '    paths: ["%s/impl/**"]' % F, "    contract: %s/contract.yaml" % F, "    model: %s/model.yaml" % F,
            "    source_map: %s/source-map.yaml" % F, "    vectors: %s/vectors.json" % F,
            '    trace_command: ["python3", "%s/impl/harness.py", "--vectors", "%s/vectors.json", "--out", "{out}"]' % (F, F), ""]))
        self.commit("policy")
        code, out = self.state("formal", "configure", "--slug", "p", "--policy", "verification/policy.yaml")
        self.assertEqual(code, 0, out)
        self.assertIn("ticket-ordering", self.unmet("implement", "p"))      # no branch.base: every module, strict side
        self.state("set", "--slug", "p", "branch.base=" + self.git("rev-parse", "HEAD").stdout.strip())
        self.assertEqual(self.unmet("implement", "p"), "")                  # nothing touched
        impl = self.repo / F / "impl/tickets.py"
        impl.write_text(impl.read_text() + "\n# touch\n")
        self.assertIn("ticket-ordering", self.unmet("implement", "p"))      # the diff decides, not the author
        ci = subprocess.run([sys.executable, str(FV), "ci", "--policy", "verification/policy.yaml", "--base", "HEAD",
                             "--out", str(Path(self.tmp.name) / "ci")], cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(ci.returncode, 1, ci.stdout)                       # mapped code changed after review: STALE
        self.git("checkout", "--", F + "/impl/tickets.py")
        ci = subprocess.run([sys.executable, str(FV), "ci", "--policy", "verification/policy.yaml", "--all",
                             "--out", str(Path(self.tmp.name) / "ci2")], cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(ci.returncode, 0, ci.stdout)                       # twin: reviewed code, conforming traces

    def test_triage_signals_route_to_their_layers(self):
        self.state("init", "--slug", "t", "--title", "ticket")
        for signal, layer in (("fv_design_defect", "plan"), ("fv_implementation_defect", "card"),
                              ("fv_requirement_gap", "task"), ("fv_contract_weakened", "task"), ("fv_model_stale", "plan")):
            code, out = self.state("fail", "--slug", "t", "--signal", signal, "--evidence", "receipt sha256:abc " + signal)
            self.assertEqual(out.get("layer"), layer, out)


if __name__ == "__main__":
    unittest.main()
