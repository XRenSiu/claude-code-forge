#!/usr/bin/env python3
"""redactor.py — Write-time PII redactor for distill-collector.

Implements the regex set defined in
references/redaction-policy.md §1-§2. Replaces matches with
`[REDACTED:<KIND>-<4char-hash>]` placeholders using
SHA-256(match + salt).

Stdlib-only: re, hashlib, argparse, sys, unittest.

CLI:
    python redactor.py --in FILE --out FILE [--salt S] [--no-redact]
    python redactor.py --test            # run embedded test vectors

Library:
    from redactor import redact
    redacted = redact(text, salt="distill-collector-v1")

Exit codes match references/cli-spec.md: 0 ok, 2 usage, 4 input, 5 output.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import unittest
from typing import Iterable, List, Pattern, Tuple

DEFAULT_SALT = "distill-collector-v1"

# -- Regex catalogue (order matters: longer / more-specific patterns first) --
# KEY patterns first so sk-/AKIA/etc. don't get caught by generic card regex.
_PATTERNS: List[Tuple[str, Pattern[str]]] = [
    ("KEY", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("KEY", re.compile(r"\bghp_[A-Za-z0-9]{36,}\b")),
    ("KEY", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{80,}\b")),
    ("KEY", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("KEY", re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}\b")),
    ("KEY", re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{20,}\b")),
    # EMAIL before PHONE (emails contain digits in the local-part sometimes).
    ("EMAIL-HASH", re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")),
    # ID patterns before PHONE/CARD (18-digit CN ID would otherwise hit CARD).
    ("ID", re.compile(r"\b\d{17}[\dXx]\b")),
    ("ID", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    # PHONE patterns.
    ("PHONE", re.compile(r"\b1[3-9]\d{9}\b")),
    ("PHONE", re.compile(r"\+\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}")),
    ("PHONE", re.compile(r"\b\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}\b")),
    # CARD last (greediest 13-19 digit run).
    ("CARD", re.compile(r"\b(?:\d[\s\-]?){13,19}\b")),
]


def _placeholder(kind: str, match: str, salt: str) -> str:
    h = hashlib.sha256((match + salt).encode("utf-8")).hexdigest()[:4]
    return f"[REDACTED:{kind}-{h}]"


def redact(text: str, salt: str = DEFAULT_SALT) -> str:
    """Run all regex patterns in order, replacing hits with hashed placeholders.

    Each pattern's matches are processed before the next pattern runs, so that
    already-redacted placeholders (which contain only `[A-Za-z0-9:\\-]` and
    brackets) cannot be re-matched by subsequent patterns.
    """
    if not text:
        return text
    for kind, pat in _PATTERNS:
        def repl(m, kind=kind):
            return _placeholder(kind, m.group(0), salt)
        text = pat.sub(repl, text)
    return text


def _warn_no_redact() -> None:
    sys.stderr.write(
        "[WARN] --no-redact is set. Raw PII will be written to disk.\n"
        "       This may violate privacy obligations. See\n"
        "       references/redaction-policy.md §5.\n"
    )


def _main(argv: Iterable[str]) -> int:
    p = argparse.ArgumentParser(prog="redactor.py", description=__doc__)
    p.add_argument("--in", dest="infile", help="input text file")
    p.add_argument("--out", dest="outfile", help="output file")
    p.add_argument("--salt", default=DEFAULT_SALT, help="per-persona salt")
    p.add_argument("--no-redact", action="store_true",
                   help="skip redaction (writes raw text; prints WARN to stderr)")
    p.add_argument("--test", action="store_true",
                   help="run embedded test vectors and exit")
    args = p.parse_args(list(argv))

    if args.test:
        return _run_selftest()

    if not args.infile or not args.outfile:
        p.print_usage(sys.stderr)
        sys.stderr.write("exit 2: --in and --out are required unless --test\n")
        return 2

    try:
        with open(args.infile, "r", encoding="utf-8") as fh:
            src = fh.read()
    except OSError as e:
        sys.stderr.write(f"exit 4: cannot read {args.infile}: {e}\n")
        return 4

    if args.no_redact:
        _warn_no_redact()
        out = src
    else:
        out = redact(src, salt=args.salt)

    try:
        with open(args.outfile, "w", encoding="utf-8") as fh:
            fh.write(out)
    except OSError as e:
        sys.stderr.write(f"exit 5: cannot write {args.outfile}: {e}\n")
        return 5

    return 0


# --------------------------------------------------------------------------
# Embedded test vectors (mirror references/redaction-policy.md §6.1 and §6.2).
# Run via: python redactor.py --test
# --------------------------------------------------------------------------

class _RedactionTests(unittest.TestCase):

    # §6.1 positive cases — redaction MUST trigger.
    def test_cn_mobile(self):
        self.assertIn("REDACTED:PHONE-", redact("my cell is 13812345678"))
        self.assertNotIn("13812345678", redact("my cell is 13812345678"))

    def test_email(self):
        self.assertIn("REDACTED:EMAIL-HASH-",
                      redact("email alice@example.com for details"))

    def test_cn_id(self):
        out = redact("身份证 110101199001011234")
        self.assertIn("REDACTED:ID-", out)

    def test_ssn(self):
        out = redact("SSN 123-45-6789")
        self.assertIn("REDACTED:ID-", out)

    def test_api_key_openai(self):
        out = redact("key sk-AbCdEf1234567890XyZqRsTuVwX")
        self.assertIn("REDACTED:KEY-", out)
        self.assertNotIn("sk-AbCdEf1234567890XyZqRsTuVwX", out)

    # §6.2 negative cases — redaction MUST NOT trigger.
    def test_short_number(self):
        self.assertEqual(redact("let's meet at 12345"), "let's meet at 12345")

    def test_version_string(self):
        self.assertEqual(redact("version 1.2.3.4"), "version 1.2.3.4")

    def test_handle_not_email(self):
        self.assertEqual(redact("@alice replied"), "@alice replied")

    # Placeholder stability: same input + same salt → same hash.
    def test_stable_hash(self):
        a = redact("email alice@example.com", salt="s1")
        b = redact("email alice@example.com", salt="s1")
        self.assertEqual(a, b)

    def test_salt_changes_hash(self):
        a = redact("email alice@example.com", salt="s1")
        b = redact("email alice@example.com", salt="s2")
        self.assertNotEqual(a, b)


def _run_selftest() -> int:
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(_RedactionTests)
    runner = unittest.TextTestRunner(stream=sys.stderr, verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
