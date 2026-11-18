"""Upstream procedures as checked artifacts: vendored copy, citations, intake, reviews, brief, triage.

Every rule below quotes an upstream source (Spec Kit clarify, Quint quint-modeling, Formal
Verification Skills review contract, Specula). Each test shows the procedure carried out (passes)
and a specific way of skipping it (caught), as twins.
"""
import atexit
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/accept-change/scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fvkit.methods import (FVS_SURFACES, QUINT_STRUCTURAL, SPECKIT_TAXONOMY, check_brief, check_cex_triage,  # noqa: E402
                           check_handoff, check_intake, check_model_review, check_review)
from fvkit.spec import load_contract, load_model  # noqa: E402
from fvkit.upstream import REQUIRED, Upstream, citations, refresh  # noqa: E402
from fvkit.values import FvError  # noqa: E402
from test_formal import BUGGY, CONTRACT, FV, ticket_model  # noqa: E402


def sha(p):
    return "sha256:" + hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build_upstream(root):
    """A miniature vendored tree holding every file a generation artifact must cite."""
    files = {}
    for needs in REQUIRED.values():
        for proj, path in needs:
            files.setdefault(proj, set()).add(path)
    projects = []
    for proj, paths in sorted(files.items()):
        base = root / proj
        base.mkdir(parents=True, exist_ok=True)
        (base / "LICENSE").write_text("MIT License (test fixture)\n")
        entries = []
        for path in sorted(paths):
            p = base / path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("procedure text of %s %s\n" % (proj, path))
            entries.append({"upstream_path": path, "path": "%s/%s" % (proj, path), "sha256": sha(p)})
        projects.append({"id": proj, "repo": "https://example.invalid/" + proj, "commit": "0" * 40, "license": "MIT",
                         "license_file": proj + "/LICENSE", "license_sha256": sha(base / "LICENSE"), "files": entries})
    m = root / "UPSTREAM.json"
    m.write_text(json.dumps({"schema_version": 1, "kind": "fv-upstream", "modified": False, "projects": projects}, indent=1))
    return m


_TMP = Path(tempfile.mkdtemp(prefix="fv-upstream-"))
atexit.register(shutil.rmtree, _TMP, True)
MANIFEST = build_upstream(_TMP / "upstream")
UP = Upstream(MANIFEST)


def cite_all(kind):
    return [UP.cite(p, path) for p, path in REQUIRED[kind]]


def intake_doc(reqs):
    scan = {k: {"status": "Clear", "note": "stated"} for k in SPECKIT_TAXONOMY}
    scan["integration_and_external_dependencies"] = {"status": "Partial", "note": "how users reach the stock"}
    return {"schema_version": 1, "kind": "fv-rules-intake", "requirements_digest": reqs.digest(), "procedure": cite_all("fv-rules-intake"),
            "system_model": {"actors": {"answer": "users and one service", "source": "R1"},
                             "communication": {"answer": "shared database", "source": "Q1"},
                             "failures": {"answer": "no crash modelled", "source": "A1"},
                             "time": {"answer": "asynchronous", "source": "R2"}},
            "ambiguity_scan": scan,
            "clarifications": [{"id": "Q1", "category": "integration_and_external_dependencies",
                                "question": "How do users and the stock interact?", "answer": "shared database",
                                "by": "owner", "signer_kind": "human"}],
            "extraction": [{"requirement": "R1", "element": "property", "text": "no oversell", "impact": "High"},
                           {"requirement": "R1", "element": "operation", "text": "buy", "impact": "High"},
                           {"requirement": "R2", "element": "property", "text": "answered", "impact": "Medium"},
                           {"requirement": "A1", "element": "assumption", "text": "no restock", "impact": "Medium"}],
            "granularity": [{"requirement": "R1", "grain": "split", "reason": "read and buy interleave"}]}


def review_doc(contract, reqs, verdict="PASS", findings=()):
    findings = list(findings)
    return {"schema_version": 2, "kind": "fv-rules-review", "contract_digest": contract.digest, "requirements_digest": reqs.digest(),
            "procedure": cite_all("fv-rules-review"), "reviewer": {"name": "formal-reviewer", "context": "fresh"}, "round": 1,
            "surfaces": {k: {"status": "checked", "checked": "compared with the source", "uncertain": "none"} for k in FVS_SURFACES},
            "findings": findings, "content_coverage": "every property against R1-R2", "verdict": verdict,
            "review_complete": {"status": "complete", "findings_count": len(findings)}}


class Fixture(unittest.TestCase):
    PRD = "# Ticket\n\n| id | must |\n|---|---|\n| R1 | sold must never exceed STOCK and remaining must stay non-negative |\n" \
          "| R2 | every pending request must eventually be answered |\n\nAssumption: there is no restock during the sale.\n"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.d = Path(self.tmp.name)
        (self.d / "prd.md").write_text(self.PRD)
        self.write("requirements.json", {
            "schema_version": 1, "kind": "fv-requirements", "id": "t", "sources": [{"id": "prd", "path": "prd.md"}],
            "requirements": [
                {"id": "R1", "text": "no oversell", "source": {"doc": "prd", "quote": "sold must never exceed STOCK and remaining must stay non-negative"}},
                {"id": "R2", "text": "answered", "source": {"doc": "prd", "quote": "every pending request must eventually be answered"}}],
            "assumptions": [{"id": "A1", "text": "no restock", "source": {"doc": "prd", "quote": "there is no restock during the sale"}}]})
        c = copy.deepcopy(CONTRACT)
        c["requirements"] = "requirements.json"
        c["assumptions"] = [{"id": "A-NR", "text": "no restock", "source": "A1"}]
        for p in c["properties"]:
            p["source"], p["text"] = ("R2" if p["kind"] == "leads_to" else "R1"), p["id"]
        self.contract_path = self.write("contract.json", c)
        self.contract = load_contract(self.contract_path)
        from fvkit.generation import requirements_for
        self.reqs = requirements_for(self.contract)
        m = ticket_model()
        m["contract"] = "contract.json"
        self.model_path = self.write("model.json", m)
        self.model = load_model(self.model_path)

    def write(self, name, doc):
        p = self.d / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(doc if isinstance(doc, str) else json.dumps(doc, ensure_ascii=False))
        return p

    def issues(self, result):
        return " ".join(result["issues"])


class VendoredCopy(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "upstream"
        self.manifest = build_upstream(self.root)

    def test_edits_additions_and_missing_licenses_are_tampering(self):
        up = Upstream(self.manifest)
        self.assertEqual(up.verify()["verdict"], "INTACT")
        target = self.root / "specula/skills/bug-classification/guide.md"
        original = target.read_bytes()
        target.write_text("a friendlier rubric\n")                               # "improving" the upstream text
        self.assertIn("differs from the vendored upstream bytes", " ".join(up.verify()["issues"]))
        target.write_bytes(original)
        (self.root / "specula/skills/extra.md").write_text("our own step\n")    # smuggled in beside upstream files
        self.assertIn("not in the manifest", " ".join(up.verify()["issues"]))
        (self.root / "specula/skills/extra.md").unlink()
        (self.root / "fvs/LICENSE").unlink()
        self.assertIn("license file", " ".join(up.verify()["issues"]))
        doc = json.loads(self.manifest.read_text())
        doc["modified"] = True
        self.manifest.write_text(json.dumps(doc))
        with self.assertRaises(FvError):
            Upstream(self.manifest)

    def test_citations_name_required_procedures_with_vendored_bytes(self):
        up = Upstream(self.manifest)
        good = [up.cite(p, path) for p, path in REQUIRED["fv-cex-triage"]]
        self.assertEqual(citations(good, "fv-cex-triage", up), [])
        self.assertIn("must follow upstream specula", " ".join(citations(good[:1], "fv-cex-triage", up)))
        wrong = copy.deepcopy(good)
        wrong[0]["sha256"] = "sha256:" + "0" * 64
        self.assertIn("cites other bytes", " ".join(citations(wrong, "fv-cex-triage", up)))
        self.assertIn("not a vendored upstream file", " ".join(citations(good + [{"upstream": "specula", "path": "skills/x.md", "sha256": "x"}],
                                                                           "fv-cex-triage", up)))
        self.assertIn("names no upstream procedure", " ".join(citations([], "fv-cex-triage", up)))
        self.assertEqual(citations(wrong, "fv-cex-triage", None), [])           # without a manifest only the names are checked

    def test_remote_check_catches_a_file_edited_together_with_its_hash(self):
        up = Upstream(self.manifest)
        originals = {}
        for pid, proj in up.projects.items():
            repo = proj["repo"].replace("https://example.invalid/", "o/")
            originals[(repo, proj["license_file"].split("/", 1)[1])] = (self.root / proj["license_file"]).read_bytes()
            for f in proj["files"]:
                originals[(repo, f["upstream_path"])] = (self.root / f["path"]).read_bytes()
        doc = json.loads(self.manifest.read_text())
        for proj in doc["projects"]:
            proj["repo"] = proj["repo"].replace("https://example.invalid/", "https://github.com/o/")
        self.manifest.write_text(json.dumps(doc))
        fetch = lambda repo, commit, path: originals[(repo, path)]  # noqa: E731  (what upstream really serves)
        self.assertEqual(Upstream(self.manifest).verify_remote(fetch)["verdict"], "INTACT")
        target = self.root / "fvs/fv-skills/references/review-policy.md"
        target.write_text("a friendlier policy\n")                              # edit the file AND re-pin its hash
        for proj in doc["projects"]:
            for f in proj["files"]:
                if f["path"] == "fvs/fv-skills/references/review-policy.md":
                    f["sha256"] = "sha256:" + hashlib.sha256(target.read_bytes()).hexdigest()
        self.manifest.write_text(json.dumps(doc))
        forged = Upstream(self.manifest)
        self.assertEqual(forged.verify()["verdict"], "INTACT")                    # the local check cannot see it
        res = forged.verify_remote(fetch)
        self.assertEqual(res["verdict"], "TAMPERED")
        self.assertIn("review-policy.md", " ".join(res["issues"]))

        def offline(repo, commit, path):
            raise OSError("network unreachable")
        self.assertEqual(Upstream(self.manifest).verify_remote(offline)["verdict"], "INCOMPLETE")   # unknown, never intact

    def test_refresh_copies_listed_files_from_a_local_clone(self):
        clone = Path(self.tmp.name) / "clone"
        for f in Upstream(self.manifest).projects["fvs"]["files"]:
            p = clone / f["upstream_path"]
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("newer upstream text\n")
        (clone / "LICENSE").write_text("MIT License (test fixture)\n")
        res = refresh(self.manifest, "fvs", clone, "1" * 40)
        self.assertEqual(res["verdict"], "INTACT")
        self.assertEqual(Upstream(self.manifest).projects["fvs"]["commit"], "1" * 40)
        with self.assertRaises(FvError):
            refresh(self.manifest, "fvs", clone, "HEAD")                       # the pin is a full sha, never a ref


class Intake(Fixture):
    def check(self, doc):
        return check_intake(self.write("intake.json", doc), self.reqs, UP)

    def test_speckit_clarify_and_quint_intake(self):
        base = intake_doc(self.reqs)
        self.assertEqual(self.check(base)["verdict"], "COMPLETE", self.check(base)["issues"])
        cases = [
            (lambda d: d["clarifications"][0].update(question="Integration (FR-3)"), "full interrogative"),
            (lambda d: d["clarifications"].extend(dict(d["clarifications"][0], id="Q%d" % i) for i in range(2, 7)), "at most 5"),
            (lambda d: d["clarifications"][0].update(by="rule-formalizer", signer_kind="delegated_agent"), "answered by a human"),
            (lambda d: [d["clarifications"][0].pop(k) for k in ("answer", "by", "signer_kind")], "answered by a human"),   # still open
            (lambda d: d["ambiguity_scan"].update(non_functional_quality_attributes={"status": "Missing", "note": "no latency"}),
             "neither asked about nor deferred"),
            (lambda d: d["ambiguity_scan"].pop("completion_signals"), "needs status Clear|Partial|Missing"),
            (lambda d: d["system_model"]["failures"].update(source="gap"), "must cite an inventoried requirement"),
            (lambda d: d["system_model"].pop("time"), "system_model.time is unanswered"),
            (lambda d: d.update(extraction=[r for r in d["extraction"] if r["requirement"] != "R2"]), "R2 has no extraction row"),
            (lambda d: d["extraction"][0].update(impact="Critical"), "High|Medium|Low"),
            (lambda d: d.update(granularity=[]), "no granularity decision"),
            (lambda d: d.update(procedure=d["procedure"][:1]), "must follow upstream quint-llm-kit"),
            (lambda d: d.update(requirements_digest="sha256:" + "1" * 64), "another requirement inventory"),
        ]
        for mutate, expected in cases:
            doc = copy.deepcopy(base)
            mutate(doc)
            self.assertIn(expected, self.issues(self.check(doc)), expected)
        doc = copy.deepcopy(base)                                                 # twin: an explicit deferral is fine
        doc["ambiguity_scan"]["non_functional_quality_attributes"] = {"status": "Missing", "note": "no latency"}
        doc["deferred"] = [{"category": "non_functional_quality_attributes", "status": "Outstanding", "rationale": "latency is not promised"}]
        self.assertEqual(self.check(doc)["verdict"], "COMPLETE")
        self.assertEqual(self.check(base)["high_impact_properties"], ["R1"])


class RulesReview(Fixture):
    def check(self, doc, triage=None):
        return check_review(self.write("review.json", doc), self.contract, self.reqs, UP,
                            self.write("triage.json", triage) if triage is not None else None)

    FINDING = {"id": "F-1", "severity": "MAJOR", "class": "CONTENT", "requirement": "R1", "property": "NoOversell",
               "claim": "the rule does not say the stock never restocks", "evidence": "prd.md Assumption line", "suggested_change": "state A-NR"}

    def triage(self, review_path, dispositions, before=None, after=None, kept=None):
        doc = {"schema_version": 1, "kind": "fv-review-triage", "review_digest": sha(review_path), "procedure": cite_all("fv-review-triage"),
               "contract_before": before or self.contract.digest, "contract_after": after or self.contract.digest, "dispositions": dispositions}
        if kept:
            doc["reviewed_contract"] = kept
        return doc

    def test_fvs_verdicts_surfaces_and_markers(self):
        self.assertEqual(self.check(review_doc(self.contract, self.reqs))["verdict"], "REVIEWED")
        old = review_doc(self.contract, self.reqs)
        old["schema_version"] = 1
        with self.assertRaises(FvError):                                         # the self-invented v1 format is gone
            self.check(old)
        cases = [
            (dict(verdict="APPROVE-WITH-EDITS"), "requires at least one finding"),
            (dict(verdict="REVISE", findings=[self.FINDING]), "another review round"),
            (dict(verdict="BLOCKED"), "another review round"),
            (dict(round=4), "round must be 1..3"),
            (dict(round=2), "prior review/triage digests"),
            (dict(reviewer={"name": "r", "context": "same-session"}), "fresh context"),
            (dict(content_coverage=" "), "content_coverage"),
        ]
        for patch, expected in cases:
            doc = review_doc(self.contract, self.reqs, findings=patch.pop("findings", ()))
            doc.update(patch)
            doc["review_complete"]["findings_count"] = len(doc["findings"])
            self.assertIn(expected, self.issues(self.check(doc)), expected)
        doc = review_doc(self.contract, self.reqs)
        doc["surfaces"].pop("vacuity")
        self.assertIn("surface vacuity", self.issues(self.check(doc)))
        doc = review_doc(self.contract, self.reqs)
        doc["surfaces"]["preconditions"] = {"status": "checked"}
        self.assertIn("blanket approval is insufficient", self.issues(self.check(doc)))
        doc = review_doc(self.contract, self.reqs, findings=[dict(self.FINDING, id="F1")])
        self.assertIn("unique F-<integer>", self.issues(self.check(doc)))
        doc = review_doc(self.contract, self.reqs, findings=[self.FINDING])
        doc["review_complete"]["findings_count"] = 0
        self.assertIn("truncated", self.issues(self.check(doc)))

    def test_author_triage_beside_an_immutable_review(self):
        reviewed = load_contract(self.contract_path)
        kept = self.d / "reviewed/contract.json"
        kept.parent.mkdir()
        doc = json.loads(self.contract_path.read_text())
        doc["requirements"] = "../requirements.json"
        kept.write_text(json.dumps(doc))
        review = review_doc(reviewed, self.reqs, verdict="APPROVE-WITH-EDITS", findings=[self.FINDING])
        rp = self.write("review.json", review)
        self.assertIn("needs the author's separate triage", self.issues(self.check(review)))
        fixed = json.loads(self.contract_path.read_text())                       # the FIX: an explicit assumption
        fixed["assumptions"].append({"id": "A-NR2", "text": "no refunds", "source": "A1"})
        self.contract_path.write_text(json.dumps(fixed))
        self.contract = load_contract(self.contract_path)
        fix = [{"finding": "F-1", "disposition": "FIX", "detail": "stated as an assumption"}]
        ok = self.triage(rp, fix, before=reviewed.digest, kept="reviewed/contract.json")
        res = self.check(review, ok)
        self.assertEqual((res["verdict"], res["outcome"]), ("REVIEWED", "approved after edits"), res["issues"])
        cases = [
            (dict(dispositions=[]), "has no disposition"),
            (dict(dispositions=[dict(fix[0], disposition="ASK-HUMAN")]), "waiting for a human"),
            (dict(dispositions=[dict(fix[0], disposition="DEFER-WITH-RULING",
                                     ruling={"text": "later", "by": "rule-formalizer", "signer_kind": "delegated_agent"})]), "cannot grant its own"),
            (dict(dispositions=[dict(fix[0], disposition="REJECT-FINDING")]), "show source evidence"),
            (dict(review_digest="sha256:" + "2" * 64), "belongs to another review"),
            (dict(reviewed_contract=None), "must be kept"),
            (dict(contract_after=reviewed.digest), "not the current contract"),
        ]
        for patch, expected in cases:
            t = copy.deepcopy(ok)
            t.update(patch)
            if t.get("reviewed_contract") is None:
                t.pop("reviewed_contract", None)
            self.assertIn(expected, self.issues(self.check(review, t)), expected)
        self.contract_path.write_text(json.dumps(json.loads(kept.read_text()) | {"requirements": "requirements.json"}))
        self.contract = load_contract(self.contract_path)
        same = self.triage(rp, fix, before=reviewed.digest)
        self.assertIn("did not change", self.issues(self.check(review, same)))


class ModelReview(Fixture):
    def review(self, **patch):
        doc = {"schema_version": 1, "kind": "fv-model-review", "model_digest": self.model.digest, "contract_digest": self.contract.digest,
               "procedure": cite_all("fv-model-review"), "reviewer": {"name": "formal-reviewer", "context": "fresh"},
               "structural": {k: {"result": "pass", "note": "checked"} for k in QUINT_STRUCTURAL},
               "granularity": [dict(action=a, source="impl/tickets.py:%d" % n, note="one statement",
                                    observable_between_atomic_ops=False, releases_lock_or_yields=False, spans_await=False,
                                    load_conditional_store=(a == "buy"), single_atomic_op=(a != "buy"), single_lock_whole_action=(a == "buy"))
                               for n, a in enumerate(("buy", "read", "reject", "request"), start=40)],
               "findings": [], "review_complete": {"status": "complete", "findings_count": 0}}
        doc.update(patch)
        return doc

    def check(self, doc, model=None, entrance="spec-first"):
        return check_model_review(self.write("model-review.json", doc), model or self.model, UP, entrance)

    def test_quint_structural_checks_and_specula_granularity(self):
        self.assertEqual(self.check(self.review())["verdict"], "REVIEWED", self.check(self.review())["issues"])
        doc = self.review()
        doc["structural"]["guarded_actions"] = {"result": "fail", "note": "buy falls back to a no-op"}
        self.assertIn("fix fails before adoption", self.issues(self.check(doc)))
        doc = self.review()
        doc["structural"]["enums_over_strings"] = {"result": "warn", "note": "string phases"}
        self.assertIn("the human decides", self.issues(self.check(doc)))
        doc["structural"]["enums_over_strings"]["decision"] = {"text": "leave as-is", "by": "owner", "signer_kind": "human"}
        self.assertEqual(self.check(doc)["verdict"], "REVIEWED")
        doc = self.review()
        doc["granularity"][0]["single_lock_whole_action"] = False                 # load -> check -> store with no lock
        self.assertIn("action buy must be split", self.issues(self.check(doc)))
        doc = self.review(granularity=self.review()["granularity"][1:])
        self.assertIn("action buy has no granularity audit row", self.issues(self.check(doc)))
        doc = self.review()
        doc["granularity"][1]["source"] = "see tickets.py"
        self.assertIn("file:line", self.issues(self.check(doc, entrance="code-first")))
        self.assertEqual(self.check(doc)["verdict"], "REVIEWED")                  # spec-first rows need no code location
        doc = self.review(findings=[{"id": "F-1", "severity": "MAJOR", "class": "CONTENT", "action": "buy", "claim": "guard too weak",
                                     "evidence": "model.json buy", "suggested_change": "use remaining"}],
                          review_complete={"status": "complete", "findings_count": 1})
        self.assertIn("is open", self.issues(self.check(doc)))

    def test_runtime_checks_are_recomputed_not_believed(self):
        dead = ticket_model(reject_guard="False")
        dead["contract"] = "contract.json"
        model = load_model(self.write("dead.json", dead))
        doc = self.review(model_digest=model.digest)
        res = self.check(doc, model)
        self.assertIn("actions never fire: ['reject']", self.issues(res))
        self.assertIn("witnesses_per_action says pass", self.issues(res))
        c = json.loads(self.contract_path.read_text())
        c["properties"].append({"id": "Tauto", "kind": "invariant", "expr": "STOCK >= 0", "source": "R1", "text": "always"})
        c["properties"].append({"id": "SoldAtStart", "kind": "invariant", "expr": "sold >= 1", "source": "R1", "text": "wrong at init"})
        self.contract_path.write_text(json.dumps(c))
        model = load_model(self.model_path)
        res = self.check(self.review(model_digest=model.digest, contract_digest=model.contract.digest), model)
        self.assertIn("reference no observable: ['Tauto']", self.issues(res))
        self.assertIn("R1: invariants false at init", self.issues(res))
        self.assertEqual(res["runtime"]["R1"]["violated_at_init"], ["SoldAtStart"])


BRIEF = """# Modeling Brief

## 1. System Overview

- Category B (Concurrent / Lock-Free / Runtime): threads share one table.

## 2. Scenarios

### Scenario 1: stale read

**Mechanism**: decides on a value read earlier.

**Evidence**:
- Code analysis: `tickets.py:66` checks seen only.

**Suggested modeling approach**:
- Actions: split read and buy.

**Priority**: High

## 3. Modeling Recommendations

### 3.1 Model (with rationale)

- read and buy.

### 3.2 Do Not Model (with rationale)

- WAL settings: performance only.

## 4. Proposed Extensions

| Extension | Variables | Purpose | Scope / Contract / Scenario |
|-----------|-----------|---------|------------|
| snapshot | seen | stale read | Scenario 1 |

## 5. Proposed Invariants

| Invariant | Type | Description | Targets |
|-----------|------|-------------|---------|
| NoOversell | Safety | sold <= STOCK | Scenario 1 |
| Answered | Liveness | purchase reaches COMMIT (tickets.py:58) | Scenario 1 |

## 6. Findings Pending Verification

### 6.1 Model-Checkable

| ID | Description | Expected invariant violation | Scenario |
|----|-------------|----------------------------|------------|
| MC-1 | Can two stale reads both buy? | NoOversell | Scenario 1 |

### 6.2 Defect Ledger

| ID | Location | Trigger | Wrong behavior | Evidence | Category | Verification | Scenario | Known |
|----|----------|---------|----------------|----------|----------|--------------|----------|-------|
| D-1 | `tickets.py:66` | two reads of 1 | oversell | no transaction | concurrency | MC | Scenario 1 | none |
| D-2 | `tickets.py:40` | repeated request | IntegrityError | primary key | low-level | CR | — | none |

## 7. Reference Pointers

- tickets.py
"""
LEDGER = {"defects": [
    {"id": "D-1", "location": ["tickets.py:66"], "trigger": "two reads of 1", "wrong_behavior": "oversell", "evidence": "no transaction",
     "category": "concurrency", "verification": "MC", "scenario": "Scenario 1", "known": None},
    {"id": "D-2", "location": ["tickets.py:40"], "trigger": "repeated request", "wrong_behavior": "IntegrityError", "evidence": "primary key",
     "category": "low-level", "verification": "CR", "scenario": None, "known": None}]}


class ModelingBrief(Fixture):
    def setUp(self):
        super().setUp()
        hunt = ticket_model(**BUGGY)
        hunt["contract"] = "contract.json"
        self.write("hunt.json", hunt)

    def coverage(self, brief_path, **patch):
        doc = {"schema_version": 1, "kind": "fv-brief-coverage", "brief_digest": sha(brief_path), "contract_digest": self.contract.digest,
               "procedure": cite_all("fv-brief-coverage"),
               "scenarios": [{"scenario": 1, "properties": ["NoOversell"], "hunt": "hunt.json"}],
               "invariants": [{"invariant": "NoOversell", "property": "NoOversell"}, {"invariant": "Answered", "property": "Answered"}],
               "findings": [{"finding": "MC-1", "property": "NoOversell", "hunt": "hunt.json"}]}
        doc.update(patch)
        return doc

    def check(self, brief=BRIEF, ledger=LEDGER, model=None, **patch):
        bp = self.write("modeling-brief.md", brief)
        lp = self.write("defect-ledger.json", ledger)
        cp = self.write("brief-coverage.json", self.coverage(bp, **patch))
        return check_brief(bp, lp, cp, model or self.model, UP)

    def test_specula_brief_format_and_ledger(self):
        res = self.check()
        self.assertEqual((res["verdict"], res["category"]), ("COMPLETE", "B"), res["issues"])
        self.assertIn("lacks section `## 7. Reference Pointers`", self.issues(self.check(BRIEF.replace("## 7. Reference Pointers", "## Pointers"))))
        self.assertIn("classify Category A", self.issues(self.check(BRIEF.replace("Category B", "a concurrent system"))))
        self.assertIn("**Priority**", self.issues(self.check(BRIEF.replace("**Priority**: High", ""))))
        missing = copy.deepcopy(LEDGER)
        missing["defects"].pop()                                                 # a CR defect dropped because it will not be modelled
        self.assertIn("D-2 is in the brief's 6.2 table but not in defect-ledger.json", self.issues(self.check(ledger=missing)))
        drift = copy.deepcopy(LEDGER)
        drift["defects"][0]["verification"] = "CR"
        self.assertIn("verification differs", self.issues(self.check(ledger=drift)))
        orphan = copy.deepcopy(LEDGER)
        orphan["defects"][0]["scenario"] = "Scenario 9"
        self.assertIn("names no Scenario", self.issues(self.check(ledger=orphan)))

    def test_brief_coverage_catches_defined_but_not_enabled(self):
        self.assertIn("Scenario 1 has no coverage row", self.issues(self.check(scenarios=[])))
        self.assertIn("MC-1 (brief 6.1) has no hunting run", self.issues(self.check(findings=[])))
        self.assertIn("Answered (brief section 5) has no coverage row",
                      self.issues(self.check(invariants=[{"invariant": "NoOversell", "property": "NoOversell"}])))
        self.assertIn("not defined in the contract", self.issues(self.check(invariants=[
            {"invariant": "NoOversell", "property": "NoOversellX"}, {"invariant": "Answered", "property": "Answered"}])))
        self.assertIn("does not load", self.issues(self.check(findings=[{"finding": "MC-1", "property": "NoOversell", "hunt": "nope.json"}])))
        unfair = ticket_model(fairness=False)
        unfair["contract"] = "contract.json"
        self.assertIn("needs justified fairness", self.issues(self.check(model=load_model(self.write("unfair.json", unfair)))))
        self.assertIn("Liveness but property NoOversell", self.issues(self.check(invariants=[
            {"invariant": "NoOversell", "property": "NoOversell"}, {"invariant": "Answered", "property": "NoOversell"}])))
        bp = self.write("modeling-brief.md", BRIEF)
        cp = self.write("brief-coverage.json", self.coverage(bp))
        self.write("modeling-brief.md", BRIEF + "\n- one more pointer\n")        # brief edited after the audit
        self.assertIn("another version of the modeling brief",
                      self.issues(check_brief(bp, self.write("defect-ledger.json", LEDGER), cp, self.model, UP)))


class CounterexampleTriage(Fixture):
    def setUp(self):
        super().setUp()
        hunt = ticket_model(**BUGGY)
        hunt["contract"] = "contract.json"
        self.hunt_path = self.write("hunt.json", hunt)
        out = subprocess.run(FV + ["check", "--model", str(self.hunt_path), "--out", str(self.d / "cex.json")], capture_output=True, text=True)
        self.assertEqual(out.returncode, 1, out.stderr)

    def check(self, **patch):
        doc = {"schema_version": 1, "kind": "fv-cex-triage", "procedure": cite_all("fv-cex-triage"), "receipt": "cex.json",
               "property": "NoOversell",
               "preconditions": [{"precondition": "both users read remaining=1", "modeled": "none"},
                                 {"precondition": "buy looks at seen only", "guard": "impl/tickets.py:66", "modeled": "same"}],
               "case": "C", "status": "REPRODUCED", "severity": "Critical", "reasoning": "two successes for one ticket via the public API"}
        doc.update(patch)
        return check_cex_triage(self.write("triage.json", doc), load_model(self.hunt_path), UP)

    def test_specula_fidelity_checklist_and_classification(self):
        res = self.check()
        self.assertEqual((res["verdict"], res["route"]), ("TRIAGED", "fv_design_defect"), res["issues"])
        gap = [{"precondition": "a refund raced the purchase", "guard": "impl/tickets.py:50", "modeled": "missing"}]
        self.assertIn("Case B until the model is fixed", self.issues(self.check(preconditions=gap)))
        b = self.check(preconditions=gap, case="B", spec_change="model the refund lock", status=None, severity=None)
        self.assertEqual((b["verdict"], b["route"]), ("TRIAGED", "fv_model_infidelity"), b["issues"])
        self.assertIn("record the spec change", self.issues(self.check(preconditions=gap, case="B")))
        self.assertIn("Case B needs a guard", self.issues(self.check(case="B", spec_change="x")))
        self.assertIn("severity-bearing", self.issues(self.check(severity="—")))
        self.assertIn("disposition: severity must be —", self.issues(self.check(status="FALSE POSITIVE", severity="High")))
        self.assertEqual(self.check(status="FALSE POSITIVE", severity="—")["verdict"], "TRIAGED")
        self.assertIn("file:line", self.issues(self.check(preconditions=[{"precondition": "x", "modeled": "same"}])))
        self.assertIn("holds no counterexample for SomeoneCanBuy", self.issues(self.check(property="SomeoneCanBuy")))
        self.assertIn("write down the preconditions", self.issues(self.check(preconditions=[])))


class HandoffAndEvidence(Fixture):
    def test_quint_step7_handoff_travels_with_each_candidate(self):
        notes = self.d / "notes.md"
        self.assertIn("is missing", " ".join(check_handoff(notes)))
        notes.write_text("# m\n\n## What it covers\n\nbuy\n\n## What it does NOT cover\n\n\n## When to update\n\nnever\n")
        self.assertEqual(check_handoff(notes), ["notes.md lacks a non-empty `## What it does NOT cover` section (Quint Step 7 handoff)"])
        notes.write_text("## What it covers\n\nbuy\n\n## What it does NOT cover\n\npayments\n\n## When to update\n\non schema change\n")
        self.assertEqual(check_handoff(notes), [])

    def test_model_evidence_requires_review_handoff_and_code_first_brief(self):
        from fvkit.generation import model_divergence, model_evidence
        cands = []
        for label in ("a", "b"):
            doc = ticket_model(mutants=(label == "a"))
            doc["contract"] = "../../contract.json"
            p = self.write("candidates/model-%s/model.json" % label, doc)
            cands.append((label, load_model(p)))
        report = model_divergence(cands)
        for c in report["candidates"]:
            c["path"] = str(Path(c["path"]).resolve())
        dp = self.write("div.json", report)
        adopted = cands[0][1]
        reasons = " ".join(model_evidence(adopted, dp)["reasons"])
        self.assertIn("handoff:", reasons)
        self.assertIn("no model review", reasons)
        for label in ("a", "b"):
            self.write("candidates/model-%s/notes.md" % label,
                       "## What it covers\n\nx\n\n## What it does NOT cover\n\ny\n\n## When to update\n\nz\n")
        reasons = " ".join(model_evidence(adopted, dp, entrance="code-first")["reasons"])
        self.assertNotIn("handoff:", reasons)
        self.assertIn("Specula modeling brief", reasons)


class ShippedExample(unittest.TestCase):
    """The AI-DLC example carries every upstream artifact, checked against the real vendored copy."""
    ROOT = Path(__file__).resolve().parents[2] / "ai-dlc/skills/formal-verify"

    def test_example_artifacts_pass_against_the_vendored_upstream(self):
        try:
            import yaml  # noqa: F401
        except ImportError:
            self.skipTest("PyYAML is needed for the YAML example")
        ex, up = self.ROOT / "assets/example-ticket", Upstream(self.ROOT / "upstream/UPSTREAM.json")
        self.assertEqual(up.verify()["verdict"], "INTACT", up.verify()["issues"])
        from fvkit.generation import model_evidence, requirements_for, rules_evidence
        contract = load_contract(ex / "contract.yaml")
        model = load_model(ex / "model.yaml", contract=contract)
        rules = rules_evidence(contract, requirements_for(contract), ex / "rules-divergence.json", ex / "rules-review.yaml",
                               ex / "rules-intake.yaml", ex / "rules-triage.yaml", up)
        self.assertEqual(rules["verdict"], "READY", rules["reasons"])
        mod = model_evidence(model, ex / "model-divergence.json", "spec-first", None, ex / "model-review.yaml", None, up)
        self.assertEqual(mod["verdict"], "READY", mod["reasons"])
        brief = check_brief(ex / "code-first/modeling-brief.md", ex / "code-first/defect-ledger.json", ex / "code-first/brief-coverage.yaml", model, up)
        self.assertEqual(brief["verdict"], "COMPLETE", brief["issues"])
        tri = check_cex_triage(ex / "triage/check-then-act.yaml", load_model(ex / "model-check-then-act.yaml"), up)
        self.assertEqual((tri["verdict"], tri["route"]), ("TRIAGED", "fv_design_defect"), tri["issues"])


if __name__ == "__main__":
    unittest.main()
