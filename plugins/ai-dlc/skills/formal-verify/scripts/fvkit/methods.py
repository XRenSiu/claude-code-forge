"""Upstream generation procedures, turned into artifacts a script can check.

The agents that write rules and models do not follow instructions invented here. They execute
vendored open-source procedures (see upstream.py), and each procedure has a required output.
This module checks that output against the procedure's own rules, quoting where each rule
comes from. Nothing here judges whether a rule is *right*; it checks that the upstream step was
actually carried out, completely, and recorded.

  rules intake    Spec Kit clarify (10-category ambiguity scan, <=5 questions, Q -> A) and Quint
                  quint-modeling Step 1 + from-requirements (system-model checklist, extraction
                  table with High/Medium/Low scoring, granularity decision per operation)
  rules review    Formal Verification Skills fc-spec-review + review-policy (fresh reviewer,
                  7 surfaces, BLOCKER/MAJOR/MINOR, PASS/APPROVE-WITH-EDITS/REVISE/BLOCKED,
                  immutable review + separate author triage, <=3 rounds, author cannot self-rule)
  model review    Quint review.md (6 structural checks; runtime checks recomputed here) and Specula
                  base-spec-methodology granularity audit (one row per action)
  modeling brief  Specula modeling-brief-format (sections 1-7, defect ledger = defect-ledger.json)
                  and brief-coverage-checklist (every scenario / invariant / finding lands)
  cex triage      Specula spec-fidelity-checklist (Case B vs C from guards) and bug-classification
                  (status / severity consistency)
  model handoff   Quint quint-modeling Step 7 (what it covers / does NOT cover / when to update)
"""
import json
import re
from pathlib import Path

from .spec import _keys, load_document
from .upstream import citations
from .values import FvError, require, sha_bytes

# Spec Kit templates/commands/clarify.md, step 3 taxonomy and step 4 quota
SPECKIT_TAXONOMY = ("functional_scope_and_behavior", "domain_and_data_model", "interaction_and_ux_flow",
                    "non_functional_quality_attributes", "integration_and_external_dependencies",
                    "edge_cases_and_failure_handling", "constraints_and_tradeoffs", "terminology_and_consistency",
                    "completion_signals", "misc_and_placeholders")
SPECKIT_STATUS = ("Clear", "Partial", "Missing")
SPECKIT_DEFERRED = ("Deferred", "Outstanding")
SPECKIT_MAX_QUESTIONS = 5
# Quint quint-modeling SKILL.md Step 1 checklist; guidelines/from-requirements.md extraction and scoring
QUINT_SYSTEM_MODEL = ("actors", "communication", "failures", "time")
QUINT_ELEMENTS = ("entity", "operation", "property", "assumption")
QUINT_IMPACT = ("High", "Medium", "Low")
QUINT_GRAIN = ("atomic", "split")
# FVS fv-skills/references/fc-spec-review.md and review-policy.md
FVS_SURFACES = ("source_fidelity", "preconditions", "postconditions", "interpretation_and_quantifiers",
                "vacuity", "dependencies_and_evidence", "helper_reuse_and_scope")
FVS_SEVERITY = ("BLOCKER", "MAJOR", "MINOR")
FVS_CLASS = ("CONTENT", "PROCESS")
FVS_VERDICTS = ("PASS", "APPROVE-WITH-EDITS", "REVISE", "BLOCKED")
FVS_DISPOSITIONS = ("FIX", "DESCOPE", "DEFER-WITH-RULING", "REJECT-FINDING", "ASK-HUMAN")
FVS_MAX_ROUNDS = 3
FINDING_ID = re.compile(r"^F-[1-9][0-9]*$")
# Quint guidelines/review.md structural checks
QUINT_STRUCTURAL = ("guarded_actions", "enums_over_strings", "record_grouping", "witnesses_per_action",
                    "right_abstraction", "non_trivial_invariants")
QUINT_RESULTS = ("pass", "warn", "fail")
# Specula spec_generation/references/base-spec-methodology.md granularity audit
SPECULA_SPLIT_IF = ("observable_between_atomic_ops", "releases_lock_or_yields", "spans_await", "load_conditional_store")
SPECULA_ATOMIC_IF = ("single_atomic_op", "single_lock_whole_action")
SOURCE_REF = re.compile(r"^[^\s:]+:[0-9]+(-[0-9]+)?$")
# Specula code_analysis/references/modeling-brief-format.md
BRIEF_SECTIONS = {"1": "System Overview", "2": "Scenarios", "3": "Modeling Recommendations", "4": "Proposed Extensions",
                  "5": "Proposed Invariants", "6": "Findings Pending Verification", "7": "Reference Pointers"}
BRIEF_SUBSECTIONS = ("3.1", "3.2", "6.1", "6.2")
LEDGER_FIELDS = ("id", "location", "trigger", "wrong_behavior", "evidence", "category", "verification", "scenario", "known")
LEDGER_CATEGORY = ("protocol", "concurrency", "low-level")
LEDGER_VERIFICATION = ("MC", "CR")
SAFETY_KINDS = ("invariant", "transition")
LIVENESS_KINDS = ("leads_to", "eventually", "infinitely_often")
# Specula tla-checking-workflow/references/spec-fidelity-checklist.md and bug-classification/guide.md
FIDELITY_MODELED = ("same", "weaker", "missing", "none")
BUG_SEVERITY_BEARING = ("REPRODUCED", "ENV_LIMITED", "MASKED")
BUG_DISPOSITIONS = ("FALSE POSITIVE", "NEEDS MORE INFO", "DROPPED", "PENDING REPAIR", "DEFERRED", "INCOMPLETE")
BUG_SEVERITY = ("Critical", "High", "Medium", "Low")
# Quint quint-modeling SKILL.md Step 7 handoff record
HANDOFF_HEADINGS = ("What it covers", "What it does NOT cover", "When to update")


def _nonempty(v):
    return isinstance(v, str) and bool(v.strip())


def _ruled(r):
    """A decision only a human (or an agent quoting the human's authorization) can make."""
    return isinstance(r, dict) and _nonempty(r.get("by")) and _nonempty(r.get("text")) and (
        r.get("signer_kind") == "human" or (r.get("signer_kind") == "delegated_agent" and _nonempty(r.get("authorization"))))


def _doc(path, kind, schema, required, optional, where):
    doc = load_document(path)
    require(isinstance(doc, dict) and doc.get("kind") == kind, "%s is not a %s" % (path, kind))
    require(doc.get("schema_version") == schema, "%s: %s needs schema_version %d" % (path, kind, schema))
    _keys(doc, ["schema_version", "kind"] + required, optional, where)
    return doc


def _verdict(issues, good, bad, **extra):
    out = {"verdict": good if not issues else bad, "issues": issues}
    out.update(extra)
    return out


# ---- rules intake: Spec Kit clarify + Quint from-requirements --------------------------------
def check_intake(path, reqs, upstream=None):
    doc = _doc(path, "fv-rules-intake", 1,
               ["requirements_digest", "procedure", "system_model", "ambiguity_scan", "clarifications", "extraction", "granularity"],
               ["deferred", "notes"], "rules intake")
    issues = []
    if doc["requirements_digest"] != reqs.digest():
        issues.append("intake was written against another requirement inventory")
    issues += citations(doc["procedure"], "fv-rules-intake", upstream)
    clar = doc["clarifications"] or []
    require(isinstance(clar, list), "clarifications must be a list")
    clar_ids = set()
    if len(clar) > SPECKIT_MAX_QUESTIONS:
        issues.append("%d clarification questions; Spec Kit clarify allows at most %d (prioritise by impact x uncertainty, defer the rest)"
                      % (len(clar), SPECKIT_MAX_QUESTIONS))
    for i, c in enumerate(clar):
        _keys(c, ["id", "category", "question"], ["answer", "by", "signer_kind", "authorization", "requirement"], "clarifications[%d]" % i)
        clar_ids.add(c["id"])
        if c["category"] not in SPECKIT_TAXONOMY:
            issues.append("clarification %s: category must be a Spec Kit taxonomy category" % c["id"])
        q = (c["question"] or "").strip()
        if not (q.endswith("?") or q.endswith("？")):
            issues.append("clarification %s: the question must be a full interrogative ending with '?' (Spec Kit question-writing rule)" % c["id"])
        if not _ruled({"by": c.get("by"), "text": c.get("answer"), "signer_kind": c.get("signer_kind"), "authorization": c.get("authorization")}):
            issues.append("clarification %s: answered by a human (or a delegated agent quoting the authorization), never by the generator" % c["id"])
    sm = doc["system_model"]
    require(isinstance(sm, dict), "system_model must be an object")
    for k in sorted(set(sm) - set(QUINT_SYSTEM_MODEL)):
        issues.append("system_model.%s is not on the Quint Step 1 checklist (%s)" % (k, ", ".join(QUINT_SYSTEM_MODEL)))
    for k in QUINT_SYSTEM_MODEL:
        e = sm.get(k)
        if not (isinstance(e, dict) and _nonempty(e.get("answer"))):
            issues.append("system_model.%s is unanswered (Quint quint-modeling Step 1 system-model checklist)" % k)
        elif e.get("source") not in reqs.items and e.get("source") not in clar_ids:
            issues.append("system_model.%s must cite an inventoried requirement/assumption or a clarification: where the document is silent, "
                          "ask one targeted question instead of inventing a default (from-requirements)" % k)
    scan = doc["ambiguity_scan"]
    require(isinstance(scan, dict), "ambiguity_scan must be an object")
    for k in sorted(set(scan) - set(SPECKIT_TAXONOMY)):
        issues.append("ambiguity_scan.%s is not a Spec Kit clarify category" % k)
    deferred = {}
    for i, d in enumerate(doc.get("deferred") or []):
        _keys(d, ["category", "status", "rationale"], [], "deferred[%d]" % i)
        if d["status"] not in SPECKIT_DEFERRED or not _nonempty(d["rationale"]):
            issues.append("deferred %s: status Deferred|Outstanding with a rationale (Spec Kit coverage summary)" % d["category"])
        deferred[d["category"]] = d
    asked = {c["category"] for c in clar}
    for k in SPECKIT_TAXONOMY:
        e = scan.get(k)
        if not (isinstance(e, dict) and e.get("status") in SPECKIT_STATUS):
            issues.append("ambiguity_scan.%s needs status Clear|Partial|Missing (Spec Kit clarify step 3)" % k)
        elif e["status"] != "Clear" and k not in asked and k not in deferred:
            issues.append("ambiguity_scan.%s is %s but was neither asked about nor deferred with a rationale" % (k, e["status"]))
    rows = doc["extraction"]
    require(isinstance(rows, list), "extraction must be a list")
    seen, ops, high = set(), set(), set()
    for i, r in enumerate(rows):
        _keys(r, ["requirement", "element", "text", "impact"], ["rationale"], "extraction[%d]" % i)
        if r["requirement"] not in reqs.items:
            issues.append("extraction[%d] cites unknown requirement %s" % (i, r["requirement"]))
        if r["element"] not in QUINT_ELEMENTS:
            issues.append("extraction[%d]: element must be entity|operation|property|assumption (from-requirements table)" % i)
        if r["impact"] not in QUINT_IMPACT:
            issues.append("extraction[%d]: impact must be High|Medium|Low (from-requirements scoring)" % i)
        if not _nonempty(r["text"]):
            issues.append("extraction[%d]: text is empty" % i)
        seen.add(r["requirement"])
        if r["element"] == "operation":
            ops.add(r["requirement"])
        if r["element"] == "property" and r["impact"] == "High":
            high.add(r["requirement"])
    for rid in reqs.requirement_ids:
        if rid not in seen:
            issues.append("requirement %s has no extraction row (from-requirements: link each decision to a line of the document)" % rid)
    grain = {}
    for i, g in enumerate(doc["granularity"] or []):
        _keys(g, ["requirement", "grain", "reason"], [], "granularity[%d]" % i)
        if g["grain"] not in QUINT_GRAIN or not _nonempty(g["reason"]):
            issues.append("granularity[%d]: grain atomic|split with a reason" % i)
        grain[g["requirement"]] = g
    for rid in sorted(ops - set(grain)):
        issues.append("operation from %s has no granularity decision (from-requirements: set scope and granularity before modelling)" % rid)
    return _verdict(issues, "COMPLETE", "GAPS", high_impact_properties=sorted(high), clarifications=len(clar),
                    digest=sha_bytes(Path(path).read_bytes()))


# ---- rules review: Formal Verification Skills review contract --------------------------------
def _findings(doc, issues, known_requirements=(), known_properties=()):
    out = {}
    for i, f in enumerate(doc["findings"] or []):
        _keys(f, ["id", "severity", "class", "claim", "evidence", "suggested_change"], ["requirement", "property", "action"], "findings[%d]" % i)
        if not FINDING_ID.match(str(f["id"])) or f["id"] in out:
            issues.append("finding id %r must be a unique F-<integer>" % f["id"])
        if f["severity"] not in FVS_SEVERITY:
            issues.append("finding %s: severity must be BLOCKER|MAJOR|MINOR" % f["id"])
        if f["class"] not in FVS_CLASS:
            issues.append("finding %s: class must be CONTENT|PROCESS" % f["id"])
        if not (_nonempty(f["claim"]) and _nonempty(f["evidence"])):
            issues.append("finding %s: claim and evidence must be substantive (re-verifiable citation or concrete counterexample)" % f["id"])
        if f.get("requirement") and known_requirements and f["requirement"] not in known_requirements:
            issues.append("finding %s cites unknown requirement %s" % (f["id"], f["requirement"]))
        if f.get("property") and known_properties and f["property"] not in known_properties:
            issues.append("finding %s cites unknown property %s" % (f["id"], f["property"]))
        out[f["id"]] = f
    return out


def _complete(doc, n, issues):
    done = doc["review_complete"] or {}
    if done.get("status") != "complete" or done.get("findings_count") != n:
        issues.append("review is incomplete or truncated (completion marker missing, or finding count does not match)")
    if (doc["reviewer"] or {}).get("context") != "fresh":
        issues.append("the reviewer must work in a fresh context (reviewer.context: fresh)")


def check_review(path, contract, reqs, upstream=None, triage=None):
    raw = load_document(path)
    require(isinstance(raw, dict) and raw.get("kind") == "fv-rules-review", "%s is not an fv-rules-review" % path)
    require(raw.get("schema_version") == 2, "fv-rules-review needs schema_version 2 (the Formal Verification Skills review contract); "
            "schema 1 reviews are not accepted — run the review again")
    doc = _doc(path, "fv-rules-review", 2,
               ["contract_digest", "requirements_digest", "procedure", "reviewer", "round", "surfaces", "findings",
                "content_coverage", "verdict", "review_complete"], ["prior", "evidence", "notes"], "rules review")
    issues = []
    if doc["requirements_digest"] != reqs.digest():
        issues.append("review was written against another requirement inventory")
    issues += citations(doc["procedure"], "fv-rules-review", upstream)
    rnd = doc["round"]
    if not (isinstance(rnd, int) and 1 <= rnd <= FVS_MAX_ROUNDS):
        issues.append("round must be 1..%d (FVS: at most three reviewer rounds, then stop)" % FVS_MAX_ROUNDS)
    elif rnd > 1 and not doc.get("prior"):
        issues.append("round %d must carry the prior review/triage digests as history" % rnd)
    surfaces = doc["surfaces"]
    require(isinstance(surfaces, dict), "surfaces must be an object")
    for k in sorted(set(surfaces) - set(FVS_SURFACES)):
        issues.append("surfaces.%s is not an FVS review surface" % k)
    for k in FVS_SURFACES:
        s = surfaces.get(k)
        if not isinstance(s, dict) or s.get("status") not in ("checked", "not_applicable"):
            issues.append("surface %s: status checked|not_applicable (FVS: check every applicable surface)" % k)
        elif s["status"] == "checked" and not _nonempty(s.get("checked")):
            issues.append("surface %s: say what was checked (a blanket approval is insufficient)" % k)
        elif s["status"] == "not_applicable" and not _nonempty(s.get("reason")):
            issues.append("surface %s: not_applicable needs a reason" % k)
    if not _nonempty(doc["content_coverage"]):
        issues.append("content_coverage must name the surfaces examined, conclusions and uncertainties")
    findings = _findings(doc, issues, set(reqs.items), {p.id for p in contract.properties})
    verdict = doc["verdict"]
    if verdict not in FVS_VERDICTS:
        issues.append("verdict must be PASS|APPROVE-WITH-EDITS|REVISE|BLOCKED")
    elif verdict in ("APPROVE-WITH-EDITS", "REVISE") and not findings:
        issues.append("%s requires at least one finding (FVS)" % verdict)
    _complete(doc, len(findings), issues)
    outcome = None
    review_digest = sha_bytes(Path(path).read_bytes())
    if verdict == "PASS":
        if doc["contract_digest"] != contract.digest:
            issues.append("review was written for another contract version")
        if triage:
            t = check_triage(triage, review_digest, doc["contract_digest"], findings, contract, upstream, require_all=False)
            issues += ["triage: " + x for x in t["issues"]]
        outcome = "approved"
    elif verdict == "APPROVE-WITH-EDITS":
        if not triage:
            issues.append("APPROVE-WITH-EDITS needs the author's separate triage (fv-review-triage) with every finding dispositioned")
        else:
            t = check_triage(triage, review_digest, doc["contract_digest"], findings, contract, upstream, require_all=True)
            issues += ["triage: " + x for x in t["issues"]]
        outcome = "approved after edits"
    elif verdict in ("REVISE", "BLOCKED"):
        issues.append("verdict %s: revise the rules (or supply the missing evidence) and run another review round (at most %d)"
                      % (verdict, FVS_MAX_ROUNDS))
    return _verdict(issues, "REVIEWED", "NOT_REVIEWED", findings=len(findings), review_verdict=verdict, outcome=outcome,
                    digest=review_digest)


def check_triage(path, review_digest, reviewed_digest, findings, contract, upstream=None, require_all=True):
    from .spec import load_contract
    doc = _doc(path, "fv-review-triage", 1, ["review_digest", "procedure", "contract_before", "contract_after", "dispositions"],
               ["reviewed_contract", "notes"], "review triage")
    issues = []
    if doc["review_digest"] != review_digest:
        issues.append("triage belongs to another review (the reviewer response is immutable; triage is written beside it)")
    issues += citations(doc["procedure"], "fv-review-triage", upstream)
    if doc["contract_before"] != reviewed_digest:
        issues.append("contract_before must be the digest the review was written for")
    if doc["contract_after"] != contract.digest:
        issues.append("contract_after is not the current contract (edits after triage are unrecorded)")
    seen = {}
    for i, d in enumerate(doc["dispositions"] or []):
        _keys(d, ["finding", "disposition", "detail"], ["evidence", "ruling"], "dispositions[%d]" % i)
        f = findings.get(d["finding"])
        if f is None:
            issues.append("disposition for unknown finding %s" % d["finding"])
            continue
        if d["finding"] in seen:
            issues.append("finding %s has two dispositions" % d["finding"])
        seen[d["finding"]] = d
        kind = d["disposition"]
        if kind not in FVS_DISPOSITIONS:
            issues.append("finding %s: disposition must be FIX|DESCOPE|DEFER-WITH-RULING|REJECT-FINDING|ASK-HUMAN" % d["finding"])
        elif kind == "ASK-HUMAN":
            issues.append("finding %s is waiting for a human (ASK-HUMAN): approval remains pending" % d["finding"])
        elif kind == "DEFER-WITH-RULING" and not _ruled(d.get("ruling")):
            issues.append("finding %s: DEFER-WITH-RULING needs a human ruling {text, by, signer_kind}; the author cannot grant its own" % d["finding"])
        elif kind == "REJECT-FINDING" and not _nonempty(d.get("evidence")):
            issues.append("finding %s: REJECT-FINDING must show source evidence that the finding is wrong" % d["finding"])
        if not _nonempty(d["detail"]):
            issues.append("finding %s: detail is empty" % d["finding"])
    if require_all:
        for fid in sorted(set(findings) - set(seen)):
            issues.append("finding %s has no disposition (an unresolved required edit blocks approval)" % fid)
    edits = [d for d in seen.values() if d["disposition"] in ("FIX", "DESCOPE")]
    if edits and doc["contract_before"] == doc["contract_after"]:
        issues.append("FIX/DESCOPE recorded but the contract did not change")
    if doc["contract_before"] != doc["contract_after"]:
        kept = doc.get("reviewed_contract")
        if not kept:
            issues.append("the reviewed contract version must be kept (reviewed_contract) when edits follow the review")
        else:
            p = Path(kept) if Path(kept).is_absolute() else Path(path).resolve().parent / kept
            try:
                if load_contract(p).digest != doc["contract_before"]:
                    issues.append("reviewed_contract is not the version the review was written for")
            except (FvError, OSError) as error:
                issues.append("reviewed_contract cannot be loaded: %s" % error)
    return _verdict(issues, "TRIAGED", "NOT_TRIAGED", digest=sha_bytes(Path(path).read_bytes()))


# ---- model review: Quint review.md + Specula granularity audit --------------------------------
def runtime_checks(model):
    """Quint review.md runtime checks, recomputed by the checker (the reviewer's word is not used)."""
    from .checker import check
    result, _, _ = check(model)
    writes = set()
    for a in model.actions:
        writes |= set(a.updates)
    obs = set(model.contract.observables)

    def names(p):
        import ast
        out = set()
        for e in (p.expr, p.from_, p.to):
            if e is not None:
                out |= set(e.names)
                for n in ast.walk(e.tree):   # pre.x / post.x are rewritten to _fv_field(pre, "x")
                    if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_fv_field" and len(n.args) == 2
                            and isinstance(n.args[1], ast.Constant) and isinstance(n.args[1].value, str)):
                        out.add(n.args[1].value)
        return out
    at_init = [p["id"] for p in result["properties"] if p["status"] == "FAIL" and p["counterexample"]
               and len(p["counterexample"].get("steps") or []) == 1]
    later = [p["id"] for p in result["properties"] if p["status"] == "FAIL" and p["id"] not in at_init]
    return {
        "C-init": "fail" if result["verdict"] == "ERROR" or not result["stats"]["initial_states"] else "pass",
        "C-step": {"never_written": sorted(set(model.variables) - writes)},
        "C-step-complete": {"dead_actions": result["coverage"]["dead_actions"] if result["complete"] else None},
        "R1": {"violated_at_init": at_init},
        "R2": {"violated_after_actions": later, "verdict": result["verdict"]},
        "witnesses": [p.id for p in model.contract.properties if p.kind == "reachable"],
        "tautologies": [p.id for p in model.contract.properties if p.kind != "reachable" and not (names(p) & obs)],
    }


def check_model_review(path, model, upstream=None, entrance="spec-first", runtime=None):
    doc = _doc(path, "fv-model-review", 1,
               ["model_digest", "contract_digest", "procedure", "reviewer", "structural", "granularity", "findings", "review_complete"],
               ["top_issues", "notes"], "model review")
    issues = []
    if doc["model_digest"] != model.digest:
        issues.append("review was written for another model version")
    if doc["contract_digest"] != model.contract.digest:
        issues.append("review was written against another contract")
    issues += citations(doc["procedure"], "fv-model-review", upstream)
    st = doc["structural"]
    require(isinstance(st, dict), "structural must be an object")
    for k in sorted(set(st) - set(QUINT_STRUCTURAL)):
        issues.append("structural.%s is not a Quint review structural check" % k)
    for k in QUINT_STRUCTURAL:
        e = st.get(k)
        if not (isinstance(e, dict) and e.get("result") in QUINT_RESULTS and _nonempty(e.get("note"))):
            issues.append("structural.%s needs result pass|warn|fail and a note (Quint review: run all checks)" % k)
        elif e["result"] == "fail":
            issues.append("structural.%s failed — fix fails before adoption (Quint review: fails are correctness problems)" % k)
        elif e["result"] == "warn" and not _ruled(e.get("decision")):
            issues.append("structural.%s is a warn: the human decides address / leave-as-is (decision {text, by, signer_kind})" % k)
    rt = runtime if runtime is not None else runtime_checks(model)
    if rt["C-init"] == "fail":
        issues.append("C-init: the model has no initial state")
    if rt["R1"]["violated_at_init"]:
        issues.append("R1: invariants false at init (init is wrong or the invariant too strong): %s" % rt["R1"]["violated_at_init"])
    dead = rt["C-step-complete"]["dead_actions"]
    if dead:
        issues.append("C-step-complete / witnesses per action: actions never fire: %s" % dead)
    ws = (st.get("witnesses_per_action") or {}).get("result")
    if ws == "pass" and (dead or not rt["witnesses"]):
        issues.append("structural.witnesses_per_action says pass, but the checker finds %s"
                      % ("dead actions" if dead else "no reachable witness in the contract"))
    nt = (st.get("non_trivial_invariants") or {}).get("result")
    if nt == "pass" and rt["tautologies"]:
        issues.append("structural.non_trivial_invariants says pass, but these properties reference no observable: %s" % rt["tautologies"])
    rows = {}
    for i, g in enumerate(doc["granularity"] or []):
        _keys(g, ["action", "source", "note"] + list(SPECULA_SPLIT_IF + SPECULA_ATOMIC_IF), [], "granularity[%d]" % i)
        rows[g["action"]] = g
        for q in SPECULA_SPLIT_IF + SPECULA_ATOMIC_IF:
            if not isinstance(g[q], bool):
                issues.append("granularity %s.%s must be true/false" % (g["action"], q))
        if any(g[q] is True for q in SPECULA_SPLIT_IF) and not any(g[q] is True for q in SPECULA_ATOMIC_IF):
            issues.append("action %s must be split (Specula granularity audit: an interleaving point inside one action hides bugs)" % g["action"])
        if entrance == "code-first" and not (isinstance(g["source"], str) and SOURCE_REF.match(g["source"])):
            issues.append("granularity %s: code-first rows cite source as file:line[-line]" % g["action"])
    names = {a.name for a in model.actions}
    for a in sorted(names - set(rows)):
        issues.append("action %s has no granularity audit row" % a)
    for a in sorted(set(rows) - names):
        issues.append("granularity row for unknown action %s" % a)
    findings = _findings(doc, issues)
    for f in findings.values():
        if f["severity"] in ("BLOCKER", "MAJOR"):
            issues.append("model review finding %s (%s) is open: fix the model and review again" % (f["id"], f["severity"]))
    _complete(doc, len(findings), issues)
    return _verdict(issues, "REVIEWED", "NOT_REVIEWED", runtime=rt, findings=len(findings), digest=sha_bytes(Path(path).read_bytes()))


# ---- modeling brief: Specula code analysis handoff + brief coverage --------------------------
def _sections(text):
    out, cur = [], None
    for line in text.splitlines():
        m = re.match(r"^(#{2,3})\s+(.*?)\s*$", line)
        if m:
            cur = {"level": len(m.group(1)), "title": m.group(2), "body": []}
            out.append(cur)
        elif cur is not None:
            cur["body"].append(line)
    return out


def _table(lines):
    rows = [ln.strip() for ln in lines if ln.strip().startswith("|")]
    if len(rows) < 2:
        return []
    cells = [[c.strip().strip("`").strip() for c in r.strip("|").split("|")] for r in rows]
    head = [h.lower() for h in cells[0]]
    return [dict(zip(head, r)) for r in cells[2:] if any(r)]


def _scenario_no(v):
    m = re.search(r"([0-9]+)", str(v or ""))
    return int(m.group(1)) if m else None


def parse_brief(path):
    text = Path(path).read_text(encoding="utf-8")
    secs = _sections(text)
    issues, by_no = [], {}
    for s in secs:
        m = re.match(r"^([0-9]+(?:\.[0-9]+)?)\.?\s", s["title"] + " ")
        if m:
            by_no.setdefault(m.group(1), s)
    for n, name in BRIEF_SECTIONS.items():
        if n not in by_no or by_no[n]["level"] != 2:
            issues.append("modeling brief lacks section `## %s. %s` (Specula modeling-brief-format)" % (n, name))
    for n in BRIEF_SUBSECTIONS:
        if n not in by_no:
            issues.append("modeling brief lacks subsection `### %s` (Specula modeling-brief-format)" % n)
    overview = "\n".join(by_no["1"]["body"]) if "1" in by_no else ""
    category = "A" if "Category A" in overview else "B" if "Category B" in overview else None
    if category is None:
        issues.append("System Overview must classify Category A (distributed) or Category B (concurrent) — later phases must not rediscover it")
    scenarios = {}
    in2 = False
    for s in secs:
        if s["level"] == 2:
            in2 = s["title"].startswith("2.")
            continue
        m = re.match(r"^Scenario\s+([0-9]+)\s*:\s*(.+)$", s["title"])
        if in2 and m:
            body = "\n".join(s["body"])
            n = int(m.group(1))
            scenarios[n] = m.group(2)
            for field in ("**Mechanism**", "**Evidence**", "**Suggested modeling approach**"):
                if field not in body:
                    issues.append("Scenario %d lacks %s" % (n, field))
            if not re.search(r"\*\*Priority\*\*:\s*(High|Medium|Low)\b", body):
                issues.append("Scenario %d needs **Priority**: High|Medium|Low" % n)
    invariants = {}
    if "5" in by_no:
        for r in _table(by_no["5"]["body"]):
            name, typ = r.get("invariant"), r.get("type")
            if name:
                invariants[name] = typ
                if typ not in ("Safety", "Liveness"):
                    issues.append("invariant %s: Type must be Safety or Liveness" % name)
    mc = {}
    if "6.1" in by_no:
        for r in _table(by_no["6.1"]["body"]):
            if r.get("id"):
                mc[r["id"]] = r
    ledger = {}
    if "6.2" in by_no:
        for r in _table(by_no["6.2"]["body"]):
            if r.get("id"):
                ledger[r["id"]] = r
    return {"issues": issues, "category": category, "scenarios": scenarios, "invariants": invariants, "mc_findings": mc,
            "ledger": ledger, "digest": sha_bytes(Path(path).read_bytes())}


def check_ledger(path, brief):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    require(isinstance(doc, dict) and isinstance(doc.get("defects"), list), "defect-ledger.json must be {\"defects\": [...]}")
    issues, ids = [], set()
    for i, d in enumerate(doc["defects"]):
        if not (isinstance(d, dict) and set(d) == set(LEDGER_FIELDS)):
            issues.append("defects[%d] must have exactly the fields %s" % (i, list(LEDGER_FIELDS)))
            continue
        did = d["id"]
        if not re.match(r"^D-[0-9]+$", str(did)) or did in ids:
            issues.append("defect id %r must be a unique D-<n>" % did)
        ids.add(did)
        if d["category"] not in LEDGER_CATEGORY:
            issues.append("defect %s: category must be protocol|concurrency|low-level" % did)
        if d["verification"] not in LEDGER_VERIFICATION:
            issues.append("defect %s: verification must be MC|CR" % did)
        elif d["verification"] == "MC" and _scenario_no(d["scenario"]) not in brief["scenarios"]:
            issues.append("defect %s is MC but names no Scenario of the brief" % did)
        elif d["verification"] == "CR" and d["scenario"] not in (None, "", "—"):
            issues.append("defect %s is CR: scenario must be null" % did)
        row = brief["ledger"].get(did)
        if row is None:
            issues.append("defect %s is in defect-ledger.json but not in the brief's 6.2 table (keep them identical)" % did)
        else:
            for k in ("category", "verification"):
                if row.get(k) != d[k]:
                    issues.append("defect %s: %s differs between the 6.2 table and defect-ledger.json" % (did, k))
    for did in sorted(set(brief["ledger"]) - ids):
        issues.append("defect %s is in the brief's 6.2 table but not in defect-ledger.json" % did)
    return issues


def check_brief(brief_path, ledger_path, coverage_path, model, upstream=None):
    from .spec import load_model
    brief = parse_brief(brief_path)
    issues = list(brief["issues"])
    issues += check_ledger(ledger_path, brief)
    cov = _doc(coverage_path, "fv-brief-coverage", 1,
               ["brief_digest", "contract_digest", "procedure", "scenarios", "invariants", "findings"], ["notes"], "brief coverage")
    if cov["brief_digest"] != brief["digest"]:
        issues.append("brief coverage was written for another version of the modeling brief")
    if cov["contract_digest"] != model.contract.digest:
        issues.append("brief coverage was written against another contract")
    issues += citations(cov["procedure"], "fv-brief-coverage", upstream)
    props = {p.id: p for p in model.contract.properties}
    base = Path(coverage_path).resolve().parent

    def hunt_ok(where, rel):
        if not _nonempty(rel):
            return ["%s names no hunting model (a finding nothing targets will not be hunted)" % where]
        try:
            load_model(base / rel, contract=model.contract)
            return []
        except (FvError, OSError) as error:
            return ["%s: hunting model %s does not load against the contract: %s" % (where, rel, error)]
    rows = {}
    for i, r in enumerate(cov["scenarios"] or []):
        _keys(r, ["scenario"], ["properties", "hunt", "merged_into", "reason"], "scenarios[%d]" % i)
        rows[_scenario_no(r["scenario"])] = r
        if r.get("merged_into") is not None:
            if _scenario_no(r["merged_into"]) not in brief["scenarios"] or not _nonempty(r.get("reason")):
                issues.append("scenario %s: an explicit merger names an existing scenario and a reason" % r["scenario"])
            continue
        named = r.get("properties") or []
        if not named:
            issues.append("scenario %s targets no property" % r["scenario"])
        issues += ["scenario %s cites unknown property %s" % (r["scenario"], p) for p in named if p not in props]
        issues += hunt_ok("scenario %s" % r["scenario"], r.get("hunt"))
    for n in sorted(set(brief["scenarios"]) - set(rows)):
        issues.append("Scenario %d has no coverage row (Specula brief coverage: every scenario has a targeting run or a written merger)" % n)
    inv = {}
    for i, r in enumerate(cov["invariants"] or []):
        _keys(r, ["invariant"], ["property", "out_of_scope"], "invariants[%d]" % i)
        inv[r["invariant"]] = r
        if r.get("out_of_scope") is not None:
            if not _nonempty(r["out_of_scope"]):
                issues.append("invariant %s: out_of_scope needs a reason" % r["invariant"])
            continue
        p = props.get(r.get("property"))
        if p is None:
            issues.append("invariant %s is not defined in the contract (defined-but-not-enabled is the failure this audit catches)" % r["invariant"])
            continue
        typ = brief["invariants"].get(r["invariant"])
        if typ == "Safety" and p.kind not in SAFETY_KINDS:
            issues.append("invariant %s is Safety but property %s is %s" % (r["invariant"], p.id, p.kind))
        if typ == "Liveness":
            if p.kind not in LIVENESS_KINDS:
                issues.append("invariant %s is Liveness but property %s is %s" % (r["invariant"], p.id, p.kind))
            elif not model.fairness:
                issues.append("Liveness %s needs justified fairness in the model (Specula liveness pattern)" % r["invariant"])
    for name in sorted(set(brief["invariants"]) - set(inv)):
        issues.append("proposed invariant %s (brief section 5) has no coverage row" % name)
    found = {}
    for i, r in enumerate(cov["findings"] or []):
        _keys(r, ["finding", "property", "hunt"], ["note"], "findings[%d]" % i)
        found[r["finding"]] = r
        if r["property"] not in props:
            issues.append("finding %s targets unknown property %s" % (r["finding"], r["property"]))
        issues += hunt_ok("finding %s" % r["finding"], r["hunt"])
    for fid in sorted(set(brief["mc_findings"]) - set(found)):
        issues.append("model-checkable finding %s (brief 6.1) has no hunting run" % fid)
    return _verdict(issues, "COMPLETE", "GAPS", category=brief["category"], scenarios=sorted(brief["scenarios"]),
                    defects=len(brief["ledger"]), brief_digest=brief["digest"], digest=sha_bytes(Path(coverage_path).read_bytes()))


# ---- counterexample triage: Specula spec-fidelity checklist + bug classification -----------
def check_cex_triage(path, model=None, upstream=None):
    from .receipt import load as load_receipt, validate
    doc = _doc(path, "fv-cex-triage", 1, ["procedure", "receipt", "property", "preconditions", "case", "reasoning"],
               ["spec_change", "status", "severity", "notes"], "counterexample triage")
    issues = citations(doc["procedure"], "fv-cex-triage", upstream)
    rp = Path(doc["receipt"]) if Path(doc["receipt"]).is_absolute() else Path(path).resolve().parent / doc["receipt"]
    command = None
    try:
        r = load_receipt(rp)
        validate(r, model=model)
        command = r["command"]
        res = r["result"].get("check", r["result"]) if command == "qualify" else r["result"]
        hit = [p for p in res.get("properties") or [] if p["property"] == doc["property"] and p["status"] == "FAIL" and p.get("counterexample")]
        if command == "conform":
            hit = hit or [v for t in res.get("traces") or [] for v in t.get("property_violations") or [] if v.get("property") == doc["property"]]
        if not hit:
            issues.append("receipt holds no counterexample for %s" % doc["property"])
    except (FvError, OSError, KeyError, AttributeError) as error:
        issues.append("counterexample receipt rejected: %s" % error)
    pre = doc["preconditions"] or []
    if not pre:
        issues.append("Step 1: write down the preconditions the violating state requires")
    gap = False
    for i, p in enumerate(pre):
        _keys(p, ["precondition", "modeled"], ["guard"], "preconditions[%d]" % i)
        if p["modeled"] not in FIDELITY_MODELED:
            issues.append("preconditions[%d].modeled must be same|weaker|missing|none" % i)
            continue
        if p["modeled"] != "none" and not (isinstance(p.get("guard"), str) and SOURCE_REF.match(p["guard"])):
            issues.append("preconditions[%d]: the implementation guard is cited as file:line (Step 2: what stops this in the real system?)" % i)
        gap = gap or p["modeled"] in ("weaker", "missing")
    case = doc["case"]
    route = None
    if case == "B":
        if not gap:
            issues.append("Case B needs a guard the model leaves out or weakens (spec-fidelity checklist Step 3)")
        if not _nonempty(doc.get("spec_change")):
            issues.append("Case B: record the spec change that models the guard, then re-run the checker (Step 4)")
        route = "fv_model_infidelity"
    elif case == "C":
        if gap:
            issues.append("a precondition is under-modeled: this is Case B until the model is fixed and the violation persists")
        status = doc.get("status") or ""
        lead = next((s for s in BUG_SEVERITY_BEARING + BUG_DISPOSITIONS if status.startswith(s)), None)
        if lead is None:
            issues.append("Case C needs a Phase 4 status (REPRODUCED, ENV_LIMITED, MASKED or a disposition)")
        elif lead in BUG_SEVERITY_BEARING and doc.get("severity") not in BUG_SEVERITY:
            issues.append("status %s is severity-bearing: severity Critical|High|Medium|Low (bug-classification)" % lead)
        elif lead in BUG_DISPOSITIONS and doc.get("severity") != "—":
            issues.append("status %s is a disposition: severity must be — (bug-classification)" % lead)
        route = "fv_implementation_defect" if command == "conform" else "fv_design_defect"
    else:
        issues.append("case must be B (fidelity gap) or C (real defect)")
    if not _nonempty(doc["reasoning"]):
        issues.append("reasoning must name the consequence and where it is triggerable from")
    return _verdict(issues, "TRIAGED", "NOT_TRIAGED", case=case, route=route, digest=sha_bytes(Path(path).read_bytes()))


# ---- model handoff: Quint quint-modeling Step 7 ---------------------------------------------
def check_handoff(notes_path):
    p = Path(notes_path)
    if not p.is_file():
        return ["%s is missing: the Step 7 handoff (what it covers / does NOT cover / when to update) travels with the model" % p]
    secs = {s["title"].strip().lower(): "\n".join(s["body"]).strip() for s in _sections(p.read_text(encoding="utf-8"))}
    issues = []
    for h in HANDOFF_HEADINGS:
        if not secs.get(h.lower()):
            issues.append("%s lacks a non-empty `## %s` section (Quint Step 7 handoff)" % (p.name, h))
    return issues
