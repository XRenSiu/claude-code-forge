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

Where the names live
--------------------
v1 contracts carry the test list in `done_when.yaml`'s `behavior:` block. v2
contracts (schema: 2) do NOT: `behavior:` is an empty seed and the real list is
`tests/<feature>/tests-manifest.yaml`, which L5 fills and locks. Pass the manifest
— either as the positional argument or via `--manifest` — or this check has
nothing to check.

An EMPTY name set is a FAILURE, never a pass (I-59): "0/0 contract names found ✓"
is a success report over an empty set, which claims traceability nobody verified.

Usage:
    python check_verbatim_names.py <done_when.yaml|tests-manifest.yaml> <tests_dir> [--json]
    python check_verbatim_names.py <done_when.yaml> <tests_dir> --manifest tests/<f>/tests-manifest.yaml --check
    python check_verbatim_names.py <spec> <tests_dir> --check   # exit 1 if any name is missing

Exit codes: 0 ok · 1 a contract name is missing · 2 no names to check / bad input
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

EMPTY_EXIT = 2   # an empty contract-name set is a failure, never a pass (I-59)

CODE_EXT = {".py", ".ts", ".tsx", ".js", ".jsx", ".kt", ".java", ".swift",
            ".rs", ".go", ".rb", ".cs", ".sh"}

EMPTY_HINT = (
    "no contract test names found in {sources}.\n"
    "A v2 contract (schema: 2) keeps `behavior:` as an empty seed — the real test list is the\n"
    "L5 manifest. Re-run against it:\n"
    "    python check_verbatim_names.py <done_when.yaml> <tests_dir> --manifest tests/<feature>/tests-manifest.yaml --check\n"
    "An empty name set is not a pass: 0/0 would report traceability nobody checked.\n"
)


def contract_names(doc):
    names = []
    b = (doc or {}).get("behavior") or {}
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


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    except OSError as e:
        sys.stderr.write(f"check_verbatim_names.py: {e}\n")
        sys.exit(2)


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
    ap.add_argument("done_when", help="done_when.yaml (v1) or tests-manifest.yaml (v2)")
    ap.add_argument("tests_dir")
    ap.add_argument("--manifest", help="tests-manifest.yaml holding the v2 test list "
                                       "(v2 `behavior:` is an empty seed); names are unioned")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check", action="store_true", help="exit 1 if any name is missing")
    args = ap.parse_args()

    sources = [args.done_when]
    names = contract_names(load(args.done_when))
    if args.manifest:
        sources.append(args.manifest)
        seen = set(names)
        for n in contract_names(load(args.manifest)):
            if n not in seen:
                seen.add(n)
                names.append(n)

    if not os.path.isdir(args.tests_dir):
        sys.stderr.write(f"Not a directory: {args.tests_dir}\n")
        sys.exit(2)

    if not names:
        hint = EMPTY_HINT.format(sources=" + ".join(sources))
        if args.json:
            print(json.dumps({"total": 0, "present": 0, "missing": [],
                              "error": "empty_contract_name_set",
                              "sources": sources}, indent=2))
        sys.stderr.write("check_verbatim_names.py: " + hint)
        sys.exit(EMPTY_EXIT)

    haystack = collect_text(args.tests_dir)
    present = [n for n in names if n in haystack]
    missing = [n for n in names if n not in haystack]

    if args.json:
        print(json.dumps({"total": len(names), "present": len(present),
                          "missing": missing, "sources": sources}, indent=2))
    else:
        tty = sys.stdout.isatty()
        def col(s, c): return f"\033[{c}m{s}\033[0m" if tty else s
        print(f"\n  verbatim-name check · {len(present)}/{len(names)} contract names found in {args.tests_dir}")
        print(f"  names from: {' + '.join(sources)}")
        for n in missing:
            print(f"  {col('✗', '31')} MISSING (verbatim): {n}")
        if not missing:
            print(f"  {col('✓', '32')} every contract test name appears character-for-character.")
        print()

    if args.check and missing:
        sys.exit(1)


if __name__ == "__main__":
    main()
