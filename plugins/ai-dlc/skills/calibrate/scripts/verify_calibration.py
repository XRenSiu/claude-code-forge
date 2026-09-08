#!/usr/bin/env python3
"""
verify_calibration.py — the META-GATE enforcement for calibrate.

This is not a well-formedness check; it is the gate ON the gate. It decides whether a compiled
standard (an eval_case set or a rubric_version) has earned the right to go live, by enforcing
the four 不可破 jud据 (HTML §05). A standard failing ANY of the four is FORBIDDEN to activate.

Usage:
    python verify_calibration.py <calibration_report.yaml> [--min-mutation 0.7] [--min-alpha 0.8]

Exit 0 = meta-gate PASS (standard may go live; rubric still needs human sign per R002).
Exit 1 = meta-gate FAIL (activation forbidden) or the report is unreadable.

Hard lines enforced (a breach forbids activation — the four jud据):
  - ☐1 kind=eval_case: mutation_score present and >= min-mutation
  - ☐2 kind=rubric:    krippendorff_alpha present and >= min-alpha (default 0.80)
  - ☐3 holdout_ref non-empty AND holdout_unexposed_confirmed (no holdout, no certification)
  - ☐4 isolation_attested true (no isolation, no evaluation)
  - surviving_mutants present but not each logged as a gate gap (eval_case_to_add) -> fail (no silent caps)
  - thresholds loosened below the standing hard lines (0.80 alpha) -> fail (lines only ratchet tighter)

Semantic half — FLAGGED as needs_semantic_review, never auto-passed:
  - is the mutant family the RIGHT one (covers the feared fault class)?
  - are the reference solutions representative, not cherry-picked?
  - is the holdout GENUINELY unseen (a human attestation, not a checkbox)?
"""
import sys
import json

try:
    import yaml
except ImportError:
    sys.stderr.write("verify_calibration.py needs PyYAML: pip install pyyaml\n")
    sys.exit(1)

HARD_ALPHA_FLOOR = 0.80      # the standing hard line; --min-alpha may only raise it, never lower
HARD_MUTATION_FLOOR = 0.70   # likewise for mutation score; --min-mutation only ratchets tighter


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def arg_float(name, default):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            try:
                return float(sys.argv[i + 1])
            except ValueError:
                pass
    return default


def main():
    if len(sys.argv) < 2:
        sys.stderr.write(__doc__)
        sys.exit(1)
    path = sys.argv[1]
    min_mutation = arg_float("--min-mutation", 0.7)
    min_alpha = arg_float("--min-alpha", HARD_ALPHA_FLOOR)

    try:
        rep = load(path)
    except Exception as e:
        sys.stderr.write(f"REJECT: cannot read report: {e}\n")
        sys.exit(1)

    rejects, flags = [], []
    kind = (rep.get("kind") or "").strip()

    # the hard lines only ratchet tighter — a report cannot pass by lowering a threshold
    if min_alpha < HARD_ALPHA_FLOOR:
        rejects.append(f"--min-alpha {min_alpha} below the standing hard line {HARD_ALPHA_FLOOR} — lines only ratchet tighter")
        min_alpha = HARD_ALPHA_FLOOR
    if min_mutation < HARD_MUTATION_FLOOR:
        rejects.append(f"--min-mutation {min_mutation} below the standing hard line {HARD_MUTATION_FLOOR} — lines only ratchet tighter")
        min_mutation = HARD_MUTATION_FLOOR

    # ☐1 mutation (eval_case)
    c1 = True
    if kind == "eval_case":
        mut = rep.get("mutation") or {}
        score = mut.get("mutation_score")
        if score is None or float(score) < min_mutation:
            c1 = False
            rejects.append(f"☐1 mutation_score {score} < {min_mutation} — eval_case is decoration, not load-bearing")
        for sm in (mut.get("surviving_mutants") or []):
            if not (sm.get("eval_case_to_add") or "").strip():
                rejects.append(f"☐1 surviving mutant {sm.get('mutant')!r} not logged as a gate gap (eval_case_to_add) — no silent caps")

    # ☐2 agreement (rubric)
    c2 = True
    if kind == "rubric":
        agr = rep.get("agreement") or {}
        alpha = agr.get("krippendorff_alpha")
        if alpha is None or float(alpha) < min_alpha:
            c2 = False
            rejects.append(f"☐2 krippendorff_alpha {alpha} < {min_alpha} — gate is wrong, not the agent")

    if kind not in ("eval_case", "rubric"):
        rejects.append(f"kind must be eval_case|rubric, got {kind!r}")

    # ☐3 holdout
    holdout = (rep.get("holdout_ref") or "").strip()
    c3 = bool(holdout) and bool(rep.get("holdout_unexposed_confirmed"))
    if not holdout:
        rejects.append("☐3 holdout_ref empty — no holdout, no certification (SpecBench)")
    elif not rep.get("holdout_unexposed_confirmed"):
        rejects.append("☐3 holdout_unexposed_confirmed false — a leaked holdout certifies nothing")

    # ☐4 isolation
    c4 = bool(rep.get("isolation_attested"))
    if not c4:
        rejects.append("☐4 isolation_attested false — no isolation, no evaluation (Berkeley RDI, R001)")
    if rep.get("cross_vendor_required") and not c4:
        flags.append("cross_vendor required by Territory — confirm evaluator vendor != executor vendor")

    flags.append("confirm the mutant family covers the feared fault class (judge call) — needs_semantic_review")
    flags.append("confirm reference solutions are representative, not cherry-picked — needs_semantic_review")
    flags.append("confirm the holdout was GENUINELY unseen, not just checkboxed — needs_semantic_review")

    result = "pass" if not rejects else "fail"
    report = {
        "report": path,
        "standard_ref": rep.get("standard_ref"),
        "kind": kind,
        "jud据": {"c1_mutation": c1, "c2_agreement": c2, "c3_holdout": c3, "c4_isolation": c4},
        "rejects": rejects,
        "needs_semantic_review": flags,
        "meta_gate": result.upper(),
        "activation": "ALLOWED (rubric still needs human sign, R002)" if result == "pass" else "FORBIDDEN",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if result == "pass" else 1)


if __name__ == "__main__":
    main()
