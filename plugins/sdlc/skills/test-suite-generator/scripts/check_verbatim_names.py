#!/usr/bin/env python3
"""
check_verbatim_names.py — the traceability primitive for test-suite-generator.

Iron rule 9 ("verbatim test names from done_when.yaml") exists because downstream
Step 5-6 reviewers grep contract names against the produced files; any paraphrase
(TS/JS `test('humanized title')`) silently breaks contract ↔ implementation
traceability. skillwise THEORY.md §3-4: a rule the author must self-enforce by
reading is not a guarantee; a runnable check of the *product* is. This script is
that exit check — it asserts every contract test name appears character-for-
character somewhere under the generated tests directory.

Usage:
    python check_verbatim_names.py <done_when.yaml> <tests_dir> [--json]
    python check_verbatim_names.py <done_when.yaml> <tests_dir> --check   # exit 1 if any missing
"""

import sys
import os
import json
import argparse

try:
    import yaml
except ImportError:
    sys.stderr.write("check_verbatim_names.py needs PyYAML: pip install pyyaml\n")
    sys.exit(2)

CODE_EXT = {".py", ".ts", ".tsx", ".js", ".jsx", ".kt", ".java", ".swift",
            ".rs", ".go", ".rb", ".cs", ".sh"}


def contract_names(doc):
    names = []
    b = doc.get("behavior") or {}
    for top in ("unit_tests", "integration_tests"):
        grp = b.get(top) or {}
        for sub in ("example_based", "property_based"):
            for n in (grp.get(sub) or []):
                if isinstance(n, str):
                    names.append(n)
    for n in (b.get("e2e_tests") or []):
        if isinstance(n, str):
            names.append(n)
    return names


def collect_text(tests_dir):
    blobs = []
    for root, _dirs, files in os.walk(tests_dir):
        for f in files:
            if os.path.splitext(f)[1].lower() in CODE_EXT:
                try:
                    with open(os.path.join(root, f), encoding="utf-8", errors="ignore") as fh:
                        blobs.append(fh.read())
                except OSError:
                    pass
    return "\n".join(blobs)


def main():
    ap = argparse.ArgumentParser(description="Assert every contract test name appears verbatim.")
    ap.add_argument("done_when")
    ap.add_argument("tests_dir")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check", action="store_true", help="exit 1 if any name is missing")
    args = ap.parse_args()

    with open(args.done_when, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    if not os.path.isdir(args.tests_dir):
        sys.stderr.write(f"Not a directory: {args.tests_dir}\n")
        sys.exit(2)

    names = contract_names(doc)
    haystack = collect_text(args.tests_dir)
    present = [n for n in names if n in haystack]
    missing = [n for n in names if n not in haystack]

    if args.json:
        print(json.dumps({"total": len(names), "present": len(present),
                          "missing": missing}, indent=2))
    else:
        tty = sys.stdout.isatty()
        def col(s, c): return f"\033[{c}m{s}\033[0m" if tty else s
        print(f"\n  verbatim-name check · {len(present)}/{len(names)} contract names found in {args.tests_dir}")
        for n in missing:
            print(f"  {col('✗', '31')} MISSING (verbatim): {n}")
        if not missing:
            print(f"  {col('✓', '32')} every contract test name appears character-for-character.")
        print()

    if args.check and missing:
        sys.exit(1)


if __name__ == "__main__":
    main()
