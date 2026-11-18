"""Lifted properties: existing tests turned into checks that are shown to run and shown to fail.

Theorem's OSS Verify turns a project's fuzz targets into theorem statements, and its rule is that
"a proof is only as strong as its fuzz target". The same holds for any property this skill lifts
out of a repository's tests — whether it is then proven by a code verifier, checked over a model,
or only run on generated inputs. The vendored procedure (oss-verify .claude/skills/add-project
step 3 and review.md item F) becomes a document an agent writes and a script checks:

  3.2  each property is a check that stops the run (abort / raise / panic), never a form the build
       can remove: C/C++ assert() (NDEBUG), Python assert (python -O), Rust debug_assert!;
       never `return -1` for a failed property
  3.3  coverage witness: a command that runs the check on example inputs and passes
  3.4  breakage: a one-line change `file:line old -> new` (the old text occurs once on that
       line) that makes *this* check fire; a check no change can make fail checks nothing;
       a stop that is not a property says `not a property: <reason>`
  F5   the check proves what its comment claims, in both directions
  F8   the expected value comes from the input and the documented rule, not from the library
       under test (else the library only agrees with itself)

`check` is static (E0). `run` executes the witness and every breakage in an isolated copy of the
repository (the real tree is never edited) and records whether each check was reached, whether
each breakage made it fire with its own marker, and the raw output tails. Its receipt is E1: the
checks ran and could fail on these runs — not that the property holds for every input.
"""
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from .spec import _keys, load_document
from .upstream import citations
from .values import require, sha_bytes

KIND = "fv-props"
REVIEW_KIND = "fv-props-review"
CHECK_KINDS = ("property", "expectation", "not_a_property")
EXPECTED_FROM = ("input", "documented_rule", "independent_entry_point", "library")
DIRECTIONS = ("one-way", "two-way")
TWO_WAY = re.compile(r"(?i)\b(iff|if and only if|exactly when|precisely when|exactly those)\b|当且仅当|恰好当|仅当且")
OUTPUT_TAIL = 4000
# oss-verify review.md F1: forms that a build removes or that report a failed property as a pass
FORBIDDEN = {
    ("c", "cpp"): [(re.compile(r"\bassert\s*\("), "assert() disappears under NDEBUG (CMake Release); write if (!cond) abort();"),
                   (re.compile(r"\breturn\s+-1\s*;"), "return -1 is read as 'do not keep this input', not a failure; call abort()")],
    ("python",): [(re.compile(r"^\s*assert\b"), "python -O removes assert; raise an exception nothing catches")],
    ("rust",): [(re.compile(r"\bdebug_assert(_eq|_ne)?!"), "debug_assert! is compiled out of release builds; use assert!/panic!")],
    ("go",): [(re.compile(r"\bos\.Exit\s*\("), "os.Exit hides the failure from the harness; panic or t.Fatal")],
}
EXT_LANG = {"c": "c", "h": "c", "cc": "cpp", "cpp": "cpp", "cxx": "cpp", "hpp": "cpp", "py": "python", "rs": "rust", "go": "go"}


def _nonempty(v):
    return isinstance(v, str) and bool(v.strip())


def _argv_ok(v):
    return isinstance(v, list) and v and all(isinstance(x, str) for x in v)


def _root(path, doc):
    return (Path(path).resolve().parent / (doc.get("root") or ".")).resolve()


def _inside(root, rel):
    p = (root / rel).resolve()
    return p if (root in p.parents and p.is_file()) else None


def load(path):
    doc = load_document(path)
    require(isinstance(doc, dict) and doc.get("kind") == KIND and doc.get("schema_version") == 1, "%s is not an fv-props (schema_version 1)" % path)
    _keys(doc, ["schema_version", "kind", "root", "procedure", "checks"], ["target", "isolation", "notes"], "props")
    return doc


def check_props(path, upstream=None, review=None):
    """Static: every check verbatim, never a removable form, a witness, a breakage per property, oracle declared."""
    doc = load(path)
    root = _root(path, doc)
    issues = citations(doc["procedure"], KIND, upstream)
    iso = doc.get("isolation") or {}
    if not isinstance(iso, dict) or not all(isinstance(x, str) for x in iso.get("link") or []):
        issues.append("isolation.link is a list of paths that are linked read-only into the copy (dependencies), never copied")
    ids = set()
    checks = doc["checks"] or []
    if not checks:
        issues.append("no checks: lift at least one property out of the project's tests")
    for i, c in enumerate(checks):
        _keys(c, ["id", "file", "check", "claim", "kind"],
              ["reason", "expected_from", "agreement", "directions", "witness", "reach_marker", "fires_with", "breakages", "notes"],
              "checks[%d]" % i)
        w = "check %s" % c["id"]
        if c["id"] in ids:
            issues.append("%s is duplicated" % w)
        ids.add(c["id"])
        f = _inside(root, c["file"])
        if f is None:
            issues.append("%s: %s is not a file under root" % (w, c["file"]))
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        if not _nonempty(c["check"]) or text.count(c["check"]) != 1:
            issues.append("%s: the check text must occur exactly once in %s (found %d)" % (w, c["file"], text.count(c["check"] or "\0")))
        lang = EXT_LANG.get(c["file"].rsplit(".", 1)[-1].lower())
        for langs, rules in FORBIDDEN.items():
            if lang in langs:
                for rx, why in rules:
                    if any(rx.search(line) for line in str(c["check"]).splitlines()):
                        issues.append("%s: %s (oss-verify add-project 3.2/3.7, review F1)" % (w, why))
        if not _nonempty(c["claim"]):
            issues.append("%s: claim — what it checks and why it must be true, in the maintainer's words (3.2)" % w)
        if c["kind"] not in CHECK_KINDS:
            issues.append("%s: kind must be one of %s" % (w, ", ".join(CHECK_KINDS)))
            continue
        if c["kind"] == "not_a_property":
            if not _nonempty(c.get("reason")):
                issues.append("%s: `not a property: <reason>` — say why this stop is not a property (3.4)" % w)
            continue
        if not (isinstance(c.get("witness"), dict) and _argv_ok(c["witness"].get("argv"))):
            issues.append("%s: witness {argv} runs the check on example inputs (coverage witness, 3.3)" % w)
        if not _nonempty(c.get("fires_with")):
            issues.append("%s: fires_with — text the output holds when THIS check fails, so another failure is not mistaken for it" % w)
        if c["kind"] == "property":
            ef = c.get("expected_from")
            if ef not in EXPECTED_FROM:
                issues.append("%s: expected_from must be one of %s (review F8)" % (w, ", ".join(EXPECTED_FROM)))
            elif ef == "library":
                issues.append("%s: the expected value comes from the library under test, so the library only agrees with itself; "
                              "compute it in the check from the input and the documented rule (review F8)" % w)
            elif ef == "independent_entry_point" and not _nonempty(c.get("agreement")):
                issues.append("%s: comparing two entry points is a property only when the claim says they must agree and they "
                              "share no code that computes the value; write that in `agreement` (review F8)" % w)
            if c.get("directions") not in DIRECTIONS:
                issues.append("%s: directions one-way|two-way (review F5: both directions of a two-way claim)" % w)
            elif TWO_WAY.search(c["claim"] or "") and c["directions"] != "two-way":
                issues.append("%s: the claim is two-way but the check is declared one-way (review F5)" % w)
            brk = c.get("breakages") or []
            if not brk:
                issues.append("%s: no breakage — a property no change can make fail checks nothing (3.4)" % w)
            for j, b in enumerate(brk):
                issues += _breakage_issues(root, b, "%s.breakages[%d]" % (w, j))
    if review is not None:
        issues += check_review(review, path, ids, upstream)
    return {"verdict": "READY" if not issues else "NOT_READY", "issues": issues, "checks": len(checks),
            "digest": sha_bytes(Path(path).read_bytes())}


def _breakage_issues(root, b, where):
    if not isinstance(b, dict):
        return ["%s must be {file, line, old, new}" % where]
    try:
        _keys(b, ["file", "line", "old", "new"], ["argv", "notes"], where)
    except ValueError as error:
        return [str(error)]
    issues = []
    f = _inside(root, b["file"])
    if f is None:
        return ["%s: %s is not a file under root" % (where, b["file"])]
    if not (isinstance(b["old"], str) and isinstance(b["new"], str) and b["old"] and b["old"] != b["new"]
            and "\n" not in b["old"] + b["new"]):
        return ["%s: old and new are different single-line texts (a one-line change, 3.4)" % where]
    lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
    if not (isinstance(b["line"], int) and 1 <= b["line"] <= len(lines)):
        return ["%s: line %s is outside %s" % (where, b["line"], b["file"])]
    if lines[b["line"] - 1].count(b["old"]) != 1:
        issues.append("%s: the old text must occur once on %s:%d (oss-verify mutant record format)" % (where, b["file"], b["line"]))
    if b.get("argv") is not None and not _argv_ok(b["argv"]):
        issues.append("%s: argv is a list of strings" % where)
    return issues


def check_review(path, props_path, ids, upstream=None):
    """Fresh-context review under oss-verify review.md F5 / F8: every check read, every weak one shown by a one-line change."""
    doc = load_document(path)
    if not (isinstance(doc, dict) and doc.get("kind") == REVIEW_KIND and doc.get("schema_version") == 1):
        return ["%s is not an fv-props-review (schema_version 1)" % path]
    _keys(doc, ["schema_version", "kind", "props_digest", "reviewer", "procedure", "checks"], ["notes"], "props review")
    issues = citations(doc["procedure"], REVIEW_KIND, upstream)
    if doc["props_digest"] != sha_bytes(Path(props_path).read_bytes()):
        issues.append("the review read another version of the props file; review the current one")
    rv = doc["reviewer"] if isinstance(doc["reviewer"], dict) else {}
    if rv.get("context") != "fresh" or not _nonempty(rv.get("id")):
        issues.append("reviewer {id, context: fresh}: the author does not review its own checks")
    seen = set()
    for i, c in enumerate(doc["checks"] or []):
        _keys(c, ["id", "verdict"], ["weakness", "one_line_change", "evidence"], "review.checks[%d]" % i)
        seen.add(c["id"])
        if c["verdict"] not in ("pass", "fail"):
            issues.append("review of %s: verdict pass|fail" % c["id"])
        elif c["verdict"] == "fail":
            ch = c.get("one_line_change")
            if not (isinstance(ch, dict) and _nonempty(ch.get("file")) and isinstance(ch.get("line"), int) and _nonempty(ch.get("change"))):
                issues.append("review of %s: a weak check is shown by a one-line change {file, line, change} that keeps the check "
                              "true and makes the claim false (review F5/F8)" % c["id"])
            issues.append("check %s failed review: %s" % (c["id"], c.get("weakness") or "weak check"))
        elif not _nonempty(c.get("evidence")):
            issues.append("review of %s: give evidence for a pass (a file and line, or a command and its output)" % c["id"])
    for cid in sorted(ids - seen):
        issues.append("check %s was not reviewed: read every check, not a sample (review F5)" % cid)
    return issues


# ---- run: witness and breakages in an isolated copy -----------------------------------------
def _run(argv, cwd, timeout):
    started = time.monotonic()
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        p = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True, timeout=timeout, env=env)
        out = p.stdout + p.stderr
        return {"argv": argv, "exit": p.returncode, "timed_out": False, "millis": int((time.monotonic() - started) * 1000),
                "output": out, "output_tail": out[-OUTPUT_TAIL:], "output_digest": sha_bytes(out.encode("utf-8"))}
    except subprocess.TimeoutExpired:
        return {"argv": argv, "exit": None, "timed_out": True, "millis": int((time.monotonic() - started) * 1000),
                "output": "", "output_tail": "", "output_digest": None}
    except OSError as error:
        return {"argv": argv, "exit": None, "timed_out": False, "millis": 0, "output": "",
                "output_tail": "cannot start: %s" % error, "output_digest": None}


def _sandbox(root, link, work):
    """Copy the tree (minus .git and the linked dependency paths), then link those read-only paths back in."""
    dst = Path(work) / "tree"
    linked = {str(Path(x)) for x in link}

    def ignore(d, names):
        rel = os.path.relpath(d, root)
        skip = {".git"}
        for n in names:
            r = os.path.normpath(os.path.join(rel, n))
            if r in linked:
                skip.add(n)
        return skip
    shutil.copytree(root, dst, ignore=ignore, symlinks=True)
    for x in sorted(linked):
        src = (root / x).resolve()
        if src.exists():
            target = dst / x
            target.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(src, target)
    return dst


def breakage_outcome(run, fires_with):
    if run["exit"] is None:
        return "ERROR"
    if run["exit"] == 0:
        return "MISSED"
    return "CAUGHT" if fires_with in run["output"] else "WRONG_CHECK"


def decide(res):
    """Verdict from the recorded runs only (also used by `fv validate`)."""
    reasons = []
    for c in res["checks"]:
        if c["kind"] == "not_a_property":
            continue
        w = c.get("witness")
        if not w or w["exit"] != 0:
            reasons.append("check %s: its witness did not pass on the unchanged code" % c["id"])
        elif c.get("reach_marker") and not w.get("reached"):
            reasons.append("check %s: the witness passed without printing its reach marker (never ran, 3.3)" % c["id"])
        if c["kind"] == "property":
            if not c["breakages"]:
                reasons.append("check %s: no breakage was run" % c["id"])
            for b in c["breakages"]:
                if b["outcome"] != "CAUGHT":
                    reasons.append("check %s: breakage %s:%d %s (%s)" % (c["id"], b["file"], b["line"], b["outcome"], {
                        "MISSED": "the tests still pass on the broken code", "WRONG_CHECK": "the run failed, but not at this check",
                        "ERROR": "the run never reached a verdict", "NOT_APPLIED": "the old text is not on that line"}.get(b["outcome"], "")))
    return reasons


def run_props(path, out_dir=None, timeout=600, upstream=None):
    static = check_props(path, upstream)
    doc = load(path)
    root = _root(path, doc)
    work = Path(out_dir or tempfile.mkdtemp(prefix="fv-props-")).resolve()
    require(not (work / "tree").exists(), "work directory already holds a copy: %s" % work)
    tree = _sandbox(root, (doc.get("isolation") or {}).get("link") or [], work)
    files = {}
    res = {"static": {"verdict": static["verdict"], "issues": static["issues"]}, "checks": [], "source": {"head": None, "files": files}}
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True)
    res["source"]["head"] = head.stdout.strip() if head.returncode == 0 else None
    for c in doc["checks"] or []:
        entry = {"id": c["id"], "kind": c["kind"], "file": c["file"], "fires_with": c.get("fires_with"),
                 "reach_marker": c.get("reach_marker"), "witness": None, "breakages": []}
        res["checks"].append(entry)
        f = _inside(root, c["file"])
        if f is not None:
            files[c["file"]] = sha_bytes(f.read_bytes())
        if c["kind"] == "not_a_property" or not (isinstance(c.get("witness"), dict) and _argv_ok(c["witness"].get("argv"))):
            continue
        argv = c["witness"]["argv"]
        w = _run(argv, tree, c["witness"].get("timeout_seconds") or timeout)
        w["reached"] = bool(c.get("reach_marker")) and c["reach_marker"] in w["output"]
        entry["witness"] = {k: v for k, v in w.items() if k != "output"}
        if c["kind"] != "property":
            continue
        for b in c.get("breakages") or []:
            target = (tree / b["file"])
            rec = {"file": b["file"], "line": b["line"], "old": b["old"], "new": b["new"]}
            original = target.read_bytes() if target.is_file() and not target.is_symlink() else None
            lines = original.split(b"\n") if original is not None else []   # bytes: only the named line changes
            old, new = str(b["old"]).encode("utf-8"), str(b["new"]).encode("utf-8")
            if original is None or not (isinstance(b["line"], int) and 1 <= b["line"] <= len(lines)) or lines[b["line"] - 1].count(old) != 1:
                rec.update({"outcome": "NOT_APPLIED"})
                entry["breakages"].append(rec)
                continue
            src = _inside(root, b["file"])
            files[b["file"]] = sha_bytes(src.read_bytes())
            lines[b["line"] - 1] = lines[b["line"] - 1].replace(old, new, 1)
            target.write_bytes(b"\n".join(lines))
            try:
                r = _run(b.get("argv") or argv, tree, c["witness"].get("timeout_seconds") or timeout)
            finally:
                target.write_bytes(original)
            rec.update({k: v for k, v in r.items() if k != "output"})
            rec["outcome"] = breakage_outcome(r, c.get("fires_with") or "\0")
            entry["breakages"].append(rec)
    reasons = (["static check: " + x for x in static["issues"]]) + decide(res)
    res["reasons"] = reasons
    return {"verdict": "ABLE_TO_FAIL" if not reasons else "WEAK", "result": res,
            "props": {"path": str(path), "digest": static["digest"]}, "work": str(work)}


__all__ = ["check_props", "check_review", "run_props", "decide", "load"]
