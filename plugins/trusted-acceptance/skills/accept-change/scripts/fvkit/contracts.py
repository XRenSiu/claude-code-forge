"""Function contracts: FM-Agent's Hoare-style route for code without a stateful model.

FM-Agent (fmagent-project/FM-Agent) reasons about a whole codebase function by function: it writes
a behavioural spec for every function (pre-condition, post-condition, and what the function
expects of each callee), checks the code against its spec using the callee specs as summaries,
and turns every mismatch into a probe through the package's public entry point that prints
CONFIRMED or NOT CONFIRMED. The vendored procedure (md/system_prompt.md, md/workflow_spec_step4_batch.md,
md/bug_validator.md) becomes one `fv-function-specs` document an agent writes and a script checks:

  Rule 2/3   no implementation narration ("calls <helper>") and none of the vague terms the rules
             list ("appropriate", "correctly handles", "as expected", "processes", "manages",
             "properly", "validates the input", "handles the case")
  layers     specs are written top-down: a callee's spec is written after the callers that state
             what they expect of it, so a callee sits on the same layer (a cycle) or a later one
  batch      every function in the document has a reasoning result: MATCH or MISMATCH
             ("You MUST complete ALL functions in the batch")
  validator  every MISMATCH carries spec_claim / actual_behavior / code_evidence /
             trigger_condition and a probe with a confirmation status and an attempt count (<= 10)

With `run`, every probe is executed again from the repository root and its status re-derived
from its own output (bug_validator Step 2e), so a recorded CONFIRMED that does not reproduce is
caught. A reproduced CONFIRMED is a finding in real code (route: fv_implementation_defect); the
specs themselves stay E0 — a MATCH is the agent's reasoning, not a proof.
"""
import os
import re
import subprocess
import time
from pathlib import Path

from .spec import _keys, load_document
from .upstream import citations
from .values import require, sha_bytes

KIND = "fv-function-specs"
# FM-Agent md/system_prompt.md, Rule 3 ("Do NOT use: ...")
VAGUE = ("appropriate", "correctly handles", "as expected", "processes", "manages", "properly", "validates the input",
         "handles the case")
VAGUE_RE = re.compile(r"(?i)\b(%s)\b" % "|".join(re.escape(v) for v in VAGUE))
VERDICTS = ("MATCH", "MISMATCH")
GAPS = ("spec_claim", "actual_behavior", "code_evidence", "trigger_condition")
STATUS = ("confirmed", "not_confirmed", "error")
MAX_ATTEMPTS = 10
OUTPUT_TAIL = 4000


def _nonempty(v):
    return isinstance(v, str) and bool(v.strip())


def _short(name):
    return re.split(r"[.:#]+", name)[-1]


def classify(exit_code, stdout):
    """bug_validator Step 2e, read by verdict lines.

    The probe must "Print exactly `CONFIRMED` or `NOT CONFIRMED` to stdout (with any additional detail
    after the keyword)", and "`ERROR` or non-zero exit" is an error. So the verdict is the keyword a line
    starts with, never a word somewhere in the output: "ERROR: crashed before the CONFIRMED check" is an
    error and "NOT  CONFIRMED" is no verdict at all. A line starting with ERROR is an error (conservative:
    an error never fabricates a finding); a probe that prints both a CONFIRMED and a NOT CONFIRMED line
    has not decided and is an error too.
    """
    if exit_code != 0:
        return "error"
    heads = [line.strip() for line in stdout.splitlines()]
    if any(h.startswith("ERROR") for h in heads):
        return "error"
    no = any(re.match(r"NOT CONFIRMED\b", h) for h in heads)
    yes = any(re.match(r"CONFIRMED\b", h) for h in heads)
    if no and yes:
        return "error"
    return "not_confirmed" if no else ("confirmed" if yes else "error")


def _spec_lint(text, names, where):
    issues = []
    m = VAGUE_RE.search(text or "")
    if m:
        issues.append("%s uses the vague term %r: every claim must be verifiable and falsifiable (FM-Agent Rule 3)" % (where, m.group(0)))
    for n in names:
        if re.search(r"(?i)\bcall(s|ed|ing)?\s+`?%s\b" % re.escape(n), text or ""):
            issues.append("%s narrates a call of %s: describe what is guaranteed, not how (FM-Agent Rule 2)" % (where, n))
    return issues


def check_specs(path, upstream=None, run=False, timeout=300):
    doc = load_document(path)
    require(isinstance(doc, dict) and doc.get("kind") == KIND and doc.get("schema_version") == 1, "%s is not an fv-function-specs (schema_version 1)" % path)
    _keys(doc, ["schema_version", "kind", "root", "procedure", "functions", "results"], ["target", "notes"], "function specs")
    base = Path(path).resolve().parent
    root = (base / doc["root"]).resolve()
    issues = citations(doc["procedure"], KIND, upstream)
    funcs = {}
    for i, f in enumerate(doc["functions"] or []):
        _keys(f, ["id", "file", "anchor", "layer", "signature", "pre_condition", "post_condition", "callees"], ["notes"], "functions[%d]" % i)
        if f["id"] in funcs:
            issues.append("function %s is duplicated" % f["id"])
        funcs[f["id"]] = f
    shorts = {}
    for fid in funcs:
        shorts.setdefault(_short(fid), []).append(fid)
    files = {}
    for fid, f in funcs.items():
        w = "function %s" % fid
        p = (root / f["file"]).resolve()
        if root not in p.parents or not p.is_file():
            issues.append("%s: %s is not a file under root" % (w, f["file"]))
        else:
            files[f["file"]] = sha_bytes(p.read_bytes())
            if not _nonempty(f["anchor"]) or f["anchor"] not in p.read_text(encoding="utf-8", errors="replace"):
                issues.append("%s: anchor is not verbatim in %s" % (w, f["file"]))
        if not (isinstance(f["layer"], int) and f["layer"] >= 0):
            issues.append("%s: layer is a non-negative integer (top-down spec order)" % w)
        for k in ("signature", "pre_condition", "post_condition"):
            if not _nonempty(f[k]):
                issues.append("%s: %s is empty" % (w, k))
        others = sorted({_short(x) for x in funcs if x != fid} | {_short(c.get("name", "")) for c in f["callees"] or [] if isinstance(c, dict)} - {""})
        issues += _spec_lint(f["pre_condition"], others, "%s pre_condition" % w)
        issues += _spec_lint(f["post_condition"], others, "%s post_condition" % w)
        for j, c in enumerate(f["callees"] or []):
            _keys(c, ["name", "pre_condition", "post_condition"], ["signature"], "%s.callees[%d]" % (w, j))
            if not (_nonempty(c["pre_condition"]) and _nonempty(c["post_condition"])):
                issues.append("%s: what it expects of callee %s needs a pre- and a post-condition (FM-Agent .info.json)" % (w, c["name"]))
            issues += _spec_lint(c["post_condition"], [], "%s expectation of %s" % (w, c["name"]))
            target = funcs.get(c["name"]) or (funcs.get(shorts[_short(c["name"])][0]) if len(shorts.get(_short(c["name"]), [])) == 1 else None)
            if target is not None and isinstance(f["layer"], int) and isinstance(target["layer"], int) and target["layer"] < f["layer"]:
                issues.append("%s expects things of %s, which sits on an earlier layer: a callee's spec is written after its callers "
                              "state what they need (workflow_spec_step4_batch: read earlier-layer caller specs)" % (w, target["id"]))
    results = {}
    findings, reruns = [], []
    for i, r in enumerate(doc["results"] or []):
        _keys(r, ["function", "verdict"], ["reasoning", "gaps", "validation", "notes"], "results[%d]" % i)
        w = "result for %s" % r["function"]
        if r["function"] not in funcs:
            issues.append("%s: no such function in the document" % w)
            continue
        if r["function"] in results:
            issues.append("%s is duplicated" % w)
        results[r["function"]] = r
        if r["verdict"] not in VERDICTS:
            issues.append("%s: verdict MATCH|MISMATCH" % w)
            continue
        if r["verdict"] == "MATCH":
            if r.get("gaps") or r.get("validation"):
                issues.append("%s: a MATCH has no gaps and no probe" % w)
            continue
        g = r.get("gaps") if isinstance(r.get("gaps"), dict) else {}
        missing = [k for k in GAPS if not _nonempty(g.get(k))]
        if missing:
            issues.append("%s: a MISMATCH records %s (bug_validator Step 1)" % (w, ", ".join(missing)))
        v = r.get("validation") if isinstance(r.get("validation"), dict) else None
        if v is None:
            issues.append("%s: a MISMATCH is validated by a probe through the public entry point (bug_validator)" % w)
            continue
        try:
            _keys(v, ["id", "probe", "argv", "confirmation_status", "attempts"], ["probe_stdout", "notes"], "%s.validation" % w)
        except ValueError as error:
            issues.append(str(error))
            continue
        probe = (base / v["probe"]).resolve()
        if not probe.is_file():
            issues.append("%s: probe %s is missing" % (w, v["probe"]))
            continue
        files[os.path.relpath(probe, base)] = sha_bytes(probe.read_bytes())
        if v["confirmation_status"] not in STATUS:
            issues.append("%s: confirmation_status confirmed|not_confirmed|error" % w)
        if not (isinstance(v["attempts"], int) and 1 <= v["attempts"] <= MAX_ATTEMPTS):
            issues.append("%s: attempts is 1..%d" % (w, MAX_ATTEMPTS))
        if not (isinstance(v["argv"], list) and v["argv"] and all(isinstance(x, str) for x in v["argv"])):
            issues.append("%s: argv is a list of strings ({probe} stands for the probe path)" % w)
            continue
        if run:
            argv = [x.replace("{probe}", str(probe)) for x in v["argv"]]
            started = time.monotonic()
            env = dict(os.environ)
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            try:
                p = subprocess.run(argv, cwd=str(root), capture_output=True, text=True, timeout=timeout, env=env)
                status, tail, code = classify(p.returncode, p.stdout), (p.stdout + p.stderr)[-OUTPUT_TAIL:], p.returncode
                stdout, complete = p.stdout[-OUTPUT_TAIL:], len(p.stdout) <= OUTPUT_TAIL
            except (OSError, subprocess.TimeoutExpired) as error:
                status, tail, code, stdout, complete = "error", str(error), None, "", False
            reruns.append({"id": v["id"], "function": r["function"], "recorded": v["confirmation_status"], "rerun": status,
                           "exit": code, "millis": int((time.monotonic() - started) * 1000), "output_tail": tail,
                           "stdout_tail": stdout, "stdout_complete": complete})
            if status != v["confirmation_status"]:
                issues.append("%s: probe %s now says %s, the document records %s (re-derived from its own output)"
                              % (w, v["id"], status, v["confirmation_status"]))
        if v["confirmation_status"] == "confirmed":
            findings.append({"id": v["id"], "function": r["function"], "spec_claim": g.get("spec_claim"),
                             "trigger": g.get("trigger_condition"), "route": "fv_implementation_defect",
                             "reproduced_now": (reruns[-1]["rerun"] == "confirmed") if run and reruns and reruns[-1]["id"] == v["id"] else None})
    for fid in sorted(set(funcs) - set(results)):
        issues.append("function %s has no reasoning result: complete every function in the batch (workflow_spec_step4_batch)" % fid)
    return {"verdict": "COMPLETE" if not issues else "GAPS", "issues": issues, "functions": len(funcs),
            "mismatches": sum(1 for r in results.values() if r.get("verdict") == "MISMATCH"), "findings": findings,
            "reruns": reruns, "source": {"files": files}, "digest": sha_bytes(Path(path).read_bytes())}


def decide(res, verdict):
    """Re-derive a contracts receipt from what it recorded (used by `fv validate`)."""
    reasons = []
    if verdict != ("COMPLETE" if not res["issues"] else "GAPS"):
        reasons.append("verdict %s contradicts %d recorded issues" % (verdict, len(res["issues"])))
    for r in res.get("reruns") or []:
        if r.get("stdout_complete") and r["rerun"] != classify(r["exit"], r.get("stdout_tail") or ""):
            reasons.append("probe %s: the recorded output re-derives %s, not %s" % (r["id"], classify(r["exit"], r["stdout_tail"]), r["rerun"]))
        if r["rerun"] != r["recorded"] and not any(r["id"] in x for x in res["issues"]):
            reasons.append("probe %s re-ran as %s against a recorded %s without an issue" % (r["id"], r["rerun"], r["recorded"]))
    return reasons


__all__ = ["check_specs", "classify", "decide", "VAGUE"]
