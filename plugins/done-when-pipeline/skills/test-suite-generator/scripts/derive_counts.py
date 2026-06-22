#!/usr/bin/env python3
"""
derive_counts.py — the count primitive for test-suite-generator.

The skill's "Counts must be verbatim from done_when.yaml" rule exists because of a
real, recorded bug (iter-2 step2 P2-4: README said 16 unit tests, the YAML listed
14). That divergence is exactly the skillwise THEORY.md §3 failure: a count
re-derived by hand in prose has no named slot to land in, so a wrong number slips
through. This script makes the counts a primitive — the relationship M = E + P is
arithmetic done once, not narrated.

Emit the headline-line counts and the per-group breakdown straight from the
contract. The SKILL body and the generated README must paste these numbers
verbatim; never hand-count test files.

Usage:
    python derive_counts.py <path-to-done_when.yaml>            # human line + table
    python derive_counts.py <path-to-done_when.yaml> --json     # machine JSON
"""

import sys
import json
import argparse

try:
    import yaml
except ImportError:
    sys.stderr.write("derive_counts.py needs PyYAML: pip install pyyaml\n")
    sys.exit(2)


def _len(x):
    return len(x) if isinstance(x, list) else 0


def counts(doc):
    existence = doc.get("existence") or []
    b = doc.get("behavior") or {}
    unit = b.get("unit_tests") or {}
    integ = b.get("integration_tests") or {}
    e = _len(unit.get("example_based"))
    p = _len(unit.get("property_based"))
    ie = _len(integ.get("example_based"))
    ip = _len(integ.get("property_based"))
    k = _len(b.get("e2e_tests"))
    return {
        "existence": _len(existence),
        "unit_total": e + p,          # M = E + P (arithmetic, not narrative)
        "unit_example": e,            # E
        "unit_property": p,           # P
        "integration_total": ie + ip,
        "integration_example": ie,
        "integration_property": ip,
        "e2e": k,                     # K
    }


def main():
    ap = argparse.ArgumentParser(description="Derive canonical test counts from done_when.yaml.")
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    with open(args.path, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    c = counts(doc)

    if args.json:
        print(json.dumps(c, indent=2))
        return

    print(f"\n  Canonical counts from {args.path}\n")
    print(f"  {c['existence']} existence checks · "
          f"{c['unit_total']} unit tests ({c['unit_example']} example / {c['unit_property']} PBT) · "
          f"{c['integration_total']} integration tests · {c['e2e']} e2e tests")
    print("\n  Paste this line verbatim into the user summary AND tests/<feature>/README.md.")
    print("  Never hand-count generated files — M = E + P is arithmetic, not narrative.\n")


if __name__ == "__main__":
    main()
