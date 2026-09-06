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

Where the names live
--------------------
v1 contracts carry the test list in `behavior:`. v2 contracts (schema: 2) do NOT:
`behavior:` is an empty seed and the real list is `tests/<feature>/tests-manifest.yaml`.
Pass `--manifest` for those — behaviour counts then come from the manifest and the
`existence:` count from whichever document declares one. A behaviour block that is
empty with no `--manifest` is a config error (exit 2), not "0 tests": a zero count
pasted into a README is the same silent-empty report I-59 killed next door.

Usage:
    python derive_counts.py <path-to-done_when.yaml>            # human line + table
    python derive_counts.py <path-to-done_when.yaml> --json     # machine JSON
    python derive_counts.py <done_when.yaml> --manifest tests/<feature>/tests-manifest.yaml
    python derive_counts.py <tests-manifest.yaml>               # manifest as the only source

Exit codes: 0 ok · 2 empty behaviour block with no --manifest / bad input
"""

import sys
import json
import argparse

try:
    import yaml
except ImportError:
    sys.stderr.write("derive_counts.py needs PyYAML: pip install pyyaml\n")
    sys.exit(2)

EMPTY_EXIT = 2   # an empty behaviour block is a failure, never "0 tests" (I-54 / I-59)

EMPTY_HINT = (
    "behavior: is empty in {path} — a v2 contract (schema: 2) keeps it as a seed and the real\n"
    "test list lives in the L5 manifest. Re-run with:\n"
    "    python derive_counts.py {path} --manifest tests/<feature>/tests-manifest.yaml\n"
    "Reporting 0 unit / 0 integration / 0 e2e here would put a fabricated count in the README.\n"
)


def _len(x):
    return len(x) if isinstance(x, list) else 0


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except OSError as e:
        sys.stderr.write(f"derive_counts.py: {e}\n")
        sys.exit(2)


def counts(doc, behavior_doc=None):
    existence = doc.get("existence") or []
    src = behavior_doc if behavior_doc is not None else doc
    if not existence:
        existence = src.get("existence") or []
    b = src.get("behavior") or {}
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
    ap.add_argument("--manifest", help="tests-manifest.yaml holding the v2 test list "
                                       "(v2 `behavior:` is an empty seed)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    doc = load(args.path)
    behavior_doc = load(args.manifest) if args.manifest else None
    c = counts(doc, behavior_doc)

    if not args.manifest and c["unit_total"] + c["integration_total"] + c["e2e"] == 0:
        sys.stderr.write("derive_counts.py: " + EMPTY_HINT.format(path=args.path))
        sys.exit(EMPTY_EXIT)

    if args.json:
        print(json.dumps(c, indent=2))
        return

    source = args.path if not args.manifest else f"{args.path} + {args.manifest}"
    print(f"\n  Canonical counts from {source}\n")
    print(f"  {c['existence']} existence checks · "
          f"{c['unit_total']} unit tests ({c['unit_example']} example / {c['unit_property']} PBT) · "
          f"{c['integration_total']} integration tests · {c['e2e']} e2e tests")
    print("\n  Paste this line verbatim into the user summary AND tests/<feature>/README.md.")
    print("  Never hand-count generated files — M = E + P is arithmetic, not narrative.\n")


if __name__ == "__main__":
    main()
