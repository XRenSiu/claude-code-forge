#!/usr/bin/env python3
"""
qa_facts.py — project a qa-reviewer report down to its MEASUREMENTS, so /spec-drift-detector can use the
performance evidence without ever seeing another reviewer's opinions.

Why this exists (I-71). Iron rule 2 says no two review skills may see each other's output while forming
opinions. The dispatch matrix nevertheless told the orchestrator to pass
`--qa-report=<iter>/fleet-outputs/qa-reviewer.yaml` to /spec-drift-detector — the whole report, findings
and GO/NO-GO decision included. Following the matrix broke the rule, and the sdlc-ring-audit meta-judge
recorded it as an isolation breach. The two documents disagreed because nothing forced them to agree.

The resolution: the orchestrator forwards a projection, never the report. Facts cross the wall; findings,
severities and the decision do not. This script IS that wall — it is an allowlist, so a key added to the
qa schema later is excluded until someone deliberately classifies it as a measurement.

What crosses (facts — counts, coverages, durations, what ran):
  agent_role · model · classifier_model · vendor · test_source · thresholds_source · baseline_source
  layers_run · layers_skipped · duration_seconds · auto_fix_maintenance · scope · results · mutation
What never crosses (opinions — someone's judgment about those facts):
  decision · decision_reasons · conditional_caveats · num_findings · findings · maintenance_issues
  regressions · caveats
`mutation.surviving_mutants[].hint` is dropped too: the surviving mutant is a fact, the hint about which
test would kill it is a suggestion.

Usage:
  qa_facts.py <qa-reviewer.yaml> [--output qa-measurements.yaml]   # project
  qa_facts.py --check <qa-measurements.yaml>                       # verify nothing forbidden got in

Exit 0 = projected / clean. Exit 1 = not a qa-reviewer report, or a checked file carries a forbidden key.
Exit 2 = usage / IO error.
"""
import argparse
import datetime as _dt
import os
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("qa_facts.py needs PyYAML: pip install pyyaml\n")
    sys.exit(2)

MEASUREMENT_KEYS = ("agent_role", "model", "classifier_model", "vendor", "test_source",
                    "thresholds_source", "baseline_source", "layers_run", "layers_skipped",
                    "duration_seconds", "auto_fix_maintenance", "scope", "results", "mutation")
OPINION_KEYS = ("decision", "decision_reasons", "conditional_caveats", "num_findings", "findings",
                "maintenance_issues", "regressions", "caveats")


def die(msg, code):
    sys.stderr.write("qa_facts: %s\n" % msg)
    sys.exit(code)


def load(path):
    if not os.path.isfile(path):
        die("%s does not exist" % path, 2)
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        die("could not parse %s (%s)" % (path, e), 2)


def strip_hints(mutation):
    """Keep every surviving mutant, drop the `hint` — the mutant is a fact, the hint is advice."""
    if not isinstance(mutation, dict):
        return mutation
    out = dict(mutation)
    survivors = out.get("surviving_mutants")
    if isinstance(survivors, list):
        out["surviving_mutants"] = [{k: v for k, v in m.items() if k != "hint"} if isinstance(m, dict) else m
                                    for m in survivors]
    return out


def forbidden_present(node, path="qa_measurements"):
    """Every place a forbidden key appears anywhere in the projected tree. Belt and braces over the
    allowlist: a measurement sub-tree must not smuggle a `findings:` list of its own."""
    hits = []
    if isinstance(node, dict):
        for k, v in node.items():
            here = "%s.%s" % (path, k)
            if k in OPINION_KEYS:
                hits.append(here)
            hits += forbidden_present(v, here)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            hits += forbidden_present(v, "%s[%d]" % (path, i))
    return hits


def project(src_path, doc):
    report = doc.get("qa_report")
    if not isinstance(report, dict):
        die("%s has no top-level `qa_report:` mapping — this is not a qa-reviewer report" % src_path, 1)
    facts = {}
    for k in MEASUREMENT_KEYS:
        if k in report:
            facts[k] = strip_hints(report[k]) if k == "mutation" else report[k]
    omitted = sorted(set(report) - set(facts))
    out = {
        "qa_measurements": dict(
            facts,
            provenance={
                "projected_from": src_path,
                "projected_by": "acceptance-fleet/scripts/qa_facts.py",
                "projected_at": _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat(),
                "omitted_keys": omitted,
                "why": ("iron rule 2: /spec-drift-detector may read qa's measurements, never its findings, "
                        "severities or GO/NO-GO decision"),
            },
        )
    }
    leaks = forbidden_present(out["qa_measurements"])
    if leaks:
        die("projection still carries opinion keys %s — refusing to write a file that breaks isolation"
            % leaks, 1)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="qa-reviewer.yaml to project, or (with --check) the projection to verify")
    ap.add_argument("--output", help="write the projection here instead of stdout")
    ap.add_argument("--check", action="store_true", help="verify an existing projection carries no opinion key")
    a = ap.parse_args()

    doc = load(a.path)
    if a.check:
        node = doc.get("qa_measurements", doc)
        leaks = forbidden_present(node)
        if leaks:
            die("%s carries opinion keys %s — /spec-drift-detector must not see these" % (a.path, leaks), 1)
        print("qa_facts: %s carries measurements only" % a.path)
        sys.exit(0)

    out = project(a.path, doc)
    text = ("# qa-measurements.yaml — measurements projected from a qa-reviewer report by qa_facts.py.\n"
            "# Findings, severities and the GO/NO-GO decision are deliberately absent (iron rule 2).\n"
            + yaml.safe_dump(out, allow_unicode=True, sort_keys=False, default_flow_style=False))
    if a.output:
        with open(a.output, "w", encoding="utf-8") as f:
            f.write(text)
        print("qa_facts: wrote %s (omitted %d opinion keys)"
              % (a.output, len(out["qa_measurements"]["provenance"]["omitted_keys"])))
    else:
        sys.stdout.write(text)
    sys.exit(0)


if __name__ == "__main__":
    main()
