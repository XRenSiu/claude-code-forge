#!/usr/bin/env python3
"""
next_iteration.py — derive iteration N's cross-iteration dispatch parameters from iteration N-1's outputs.

Why this exists (I-72). Every parameter that carries information ACROSS iterations — `--baseline-score`,
`--history`, `--baseline`, `--prev-review` — used to be hand-written by the orchestrator into the dispatch
prompts. In the sdlc-ring-audit run, iteration-003's task file was produced by editing iteration-002's: the
sed changed the *label* from iteration-001 to iteration-002 but left the *number* at 3.5, while
iteration-002's real score was 4.0. The gaming detector was handed a baseline half a point too low, read a
flat trajectory as rising, and flagged the inconsistency itself. A number and its provenance must come from
the same read, or they drift apart the first time a template is edited.

So: the orchestrator stops typing these values. It runs

    eval "$(next_iteration.py <ratchet-log-dir> <N> --done-when <done_when.yaml>)"

and uses the variables. Every emitted path is one that exists on disk; every emitted number was read from
the file it names.

Usage:
  next_iteration.py <ratchet_log_dir> <N> [--done-when PATH] [--format sh|json]

Emitted variables (empty when not applicable — `${VAR:+--flag="$VAR"}` then omits the flag):
  ITERATION             N
  ITER_DIR              <ratchet_log_dir>/iteration-NNN
  PREV_ITER_DIR         iteration-(N-1), empty when N == 1
  PREV_SNAPSHOT         prev impl-snapshot.tar.gz            → /spec-gaming-detector --history
  PREV_GAMING_SCORE     prev gaming_risk_score               → /spec-gaming-detector --baseline-score
  PREV_QA_REPORT        prev fleet-outputs/qa-reviewer.yaml  → /qa-reviewer --baseline
  PREV_PM_REVIEW        prev fleet-outputs/pm-reviewer.yaml  → /pm-reviewer --prev-review
  GAMING_TRAJECTORY     comma-joined scores for iterations 1..N-1
  GAMING_DONE_BELOW     done_when.gaming_risk_threshold.done_below (default 3)
  GAMING_BLOCK_AT       done_when.gaming_risk_threshold.block_at_or_above (default 7)
  PREV_GAMING_BAND      clean | elevated | blocking | unknown — which S3 band the previous score fell in
  SPEC_DRIFT_TRIGGER    done_when.spec_drift_threshold.max_fix_loops_before_escalation (default 3)
  BASELINE_DISCREPANCY  set when a past iteration recorded a baseline_score that disagrees with the score
                        actually produced by the iteration before it (the I-72 failure, after the fact)

Exit 0 = parameters emitted. Exit 1 = the run is inconsistent (missing predecessor, unusable threshold
band) — do NOT dispatch on guessed values. Exit 2 = usage / IO error.
"""
import argparse
import glob
import json
import os
import re
import shlex
import sys

try:
    import yaml
except ImportError:  # the fallback keeps the orchestrator runnable on a bare python3
    yaml = None

SCORE_RE = re.compile(r"^\s*gaming_risk_score:\s*([0-9]*\.?[0-9]+)", re.MULTILINE)
BASELINE_RE = re.compile(r"^\s*baseline_score:\s*([0-9]*\.?[0-9]+)", re.MULTILINE)
DEFAULT_DONE_BELOW = 3
DEFAULT_BLOCK_AT = 7
DEFAULT_DRIFT_TRIGGER = 3


def die(msg, code=2):
    sys.stderr.write("next_iteration: %s\n" % msg)
    sys.exit(code)


def warn(msg):
    sys.stderr.write("next_iteration: warning: %s\n" % msg)


def iter_dir(root, n):
    return os.path.join(root, "iteration-%03d" % n)


def load_yaml(path):
    """Parse a YAML file; None when absent or unparseable. Callers must tolerate None."""
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            if yaml is None:
                return None
            return yaml.safe_load(f) or {}
    except Exception as e:
        warn("could not parse %s (%s)" % (path, e))
        return None


def read_text(path):
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        warn("could not read %s (%s)" % (path, e))
        return None


def gaming_file(root, n):
    return os.path.join(iter_dir(root, n), "fleet-outputs", "spec-gaming-detector.yaml")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def gaming_scores(root, n):
    """(gaming_risk_score, baseline_score) recorded by iteration n. Either may be None."""
    path = gaming_file(root, n)
    doc = load_yaml(path)
    if isinstance(doc, dict):
        block = doc.get("gaming_assessment")
        if isinstance(block, dict):
            return _num(block.get("gaming_risk_score")), _num(block.get("baseline_score"))
        return _num(doc.get("gaming_risk_score")), _num(doc.get("baseline_score"))
    text = read_text(path)
    if text is None:
        return None, None
    m, b = SCORE_RE.search(text), BASELINE_RE.search(text)
    return (_num(m.group(1)) if m else None), (_num(b.group(1)) if b else None)


def fmt_num(x):
    """4.0 → "4", 3.5 → "3.5". The detector's schema allows int or float; the shell gets one canonical form."""
    if x is None:
        return ""
    f = float(x)
    return str(int(f)) if f.is_integer() else repr(f)


def band(score, done_below, block_at):
    if score is None:
        return "unknown"
    if score < done_below:
        return "clean"
    if score < block_at:
        return "elevated"
    return "blocking"


def thresholds(done_when_path):
    done_below, block_at, drift = DEFAULT_DONE_BELOW, DEFAULT_BLOCK_AT, DEFAULT_DRIFT_TRIGGER
    if not done_when_path:
        return done_below, block_at, drift
    if not os.path.isfile(done_when_path):
        die("--done-when %s does not exist" % done_when_path)
    doc = load_yaml(done_when_path)
    if doc is None:
        warn("could not read thresholds from %s — using defaults %s / %s"
             % (done_when_path, DEFAULT_DONE_BELOW, DEFAULT_BLOCK_AT))
        return done_below, block_at, drift
    grt = doc.get("gaming_risk_threshold")
    if isinstance(grt, dict):
        extra = set(grt) - {"done_below", "block_at_or_above"}
        if extra:
            die("gaming_risk_threshold has unknown sub-fields %s — only done_below and "
                "block_at_or_above are defined" % sorted(extra), 1)
        for key, name in (("done_below", "done_below"), ("block_at_or_above", "block_at_or_above")):
            if key in grt and _num(grt[key]) is None:
                die("gaming_risk_threshold.%s is not a number: %r" % (name, grt[key]), 1)
        done_below = _num(grt.get("done_below", done_below))
        block_at = _num(grt.get("block_at_or_above", block_at))
        if done_below > block_at:
            die("gaming_risk_threshold: done_below %s > block_at_or_above %s — that band is empty and the "
                "S3 table would have no rule for scores between them" % (done_below, block_at), 1)
    elif grt is not None:
        die("gaming_risk_threshold must be a mapping with done_below / block_at_or_above", 1)
    sdt = doc.get("spec_drift_threshold")
    if isinstance(sdt, dict) and _num(sdt.get("max_fix_loops_before_escalation")) is not None:
        drift = _num(sdt["max_fix_loops_before_escalation"])
    return done_below, block_at, drift


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ratchet_log_dir")
    ap.add_argument("n", type=int, help="the iteration being dispatched (1-based)")
    ap.add_argument("--done-when", help="done_when.yaml the thresholds come from")
    ap.add_argument("--format", choices=["sh", "json"], default="sh")
    a = ap.parse_args()

    if a.n < 1:
        die("iteration must be >= 1, got %s" % a.n)
    root = a.ratchet_log_dir
    if not os.path.isdir(root) and a.n > 1:
        die("ratchet-log dir %s does not exist, so iteration %s has no predecessor to derive from"
            % (root, a.n), 1)

    done_below, block_at, drift = thresholds(a.done_when)
    out = {
        "ITERATION": str(a.n),
        "ITER_DIR": iter_dir(root, a.n),
        "PREV_ITER_DIR": "", "PREV_SNAPSHOT": "", "PREV_GAMING_SCORE": "",
        "PREV_QA_REPORT": "", "PREV_PM_REVIEW": "",
        "GAMING_TRAJECTORY": "",
        "GAMING_DONE_BELOW": fmt_num(done_below), "GAMING_BLOCK_AT": fmt_num(block_at),
        "PREV_GAMING_BAND": "unknown",
        "SPEC_DRIFT_TRIGGER": fmt_num(drift),
        "BASELINE_DISCREPANCY": "",
    }

    if a.n > 1:
        prev = iter_dir(root, a.n - 1)
        if not os.path.isdir(prev):
            existing = sorted(os.path.basename(p) for p in glob.glob(os.path.join(root, "iteration-*")))
            die("iteration %s needs %s, which does not exist (present: %s). Dispatching iteration %s "
                "without its predecessor's outputs means every cross-iteration parameter would be guessed."
                % (a.n, prev, ", ".join(existing) or "none", a.n), 1)
        out["PREV_ITER_DIR"] = prev
        for var, rel in (("PREV_SNAPSHOT", "impl-snapshot.tar.gz"),
                         ("PREV_QA_REPORT", os.path.join("fleet-outputs", "qa-reviewer.yaml")),
                         ("PREV_PM_REVIEW", os.path.join("fleet-outputs", "pm-reviewer.yaml"))):
            p = os.path.join(prev, rel)
            if os.path.isfile(p):
                out[var] = p
            else:
                warn("%s not found — %s will be dispatched without it" % (p, var))

        score, _ = gaming_scores(root, a.n - 1)
        if score is None:
            warn("no gaming_risk_score in %s — PREV_GAMING_SCORE stays empty rather than carrying a stale "
                 "number forward" % gaming_file(root, a.n - 1))
        out["PREV_GAMING_SCORE"] = fmt_num(score)
        out["PREV_GAMING_BAND"] = band(score, done_below, block_at)

        traj = [fmt_num(s) for s in (gaming_scores(root, i)[0] for i in range(1, a.n)) if s is not None]
        out["GAMING_TRAJECTORY"] = ",".join(traj)

    # Post-hoc audit over every iteration on disk, including ones already run: did any of them record a
    # baseline_score that disagrees with what its predecessor actually produced? That disagreement IS the
    # I-72 defect, and it stays invisible unless something compares the two reads.
    discrepancies = []
    for path in sorted(glob.glob(os.path.join(root, "iteration-*"))):
        m = re.fullmatch(r"iteration-(\d+)", os.path.basename(path))
        if not m or int(m.group(1)) < 2:
            continue
        i = int(m.group(1))
        _, recorded = gaming_scores(root, i)
        actual, _ = gaming_scores(root, i - 1)
        if recorded is not None and actual is not None and abs(recorded - actual) > 1e-9:
            discrepancies.append("iteration-%03d recorded baseline_score %s but iteration-%03d produced %s"
                                 % (i, fmt_num(recorded), i - 1, fmt_num(actual)))
    if discrepancies:
        out["BASELINE_DISCREPANCY"] = "; ".join(discrepancies)
        warn("baseline discrepancy in the log: " + out["BASELINE_DISCREPANCY"])

    if a.format == "json":
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        for k, v in out.items():
            print("%s=%s" % (k, shlex.quote(v)))
    sys.exit(0)


if __name__ == "__main__":
    main()
