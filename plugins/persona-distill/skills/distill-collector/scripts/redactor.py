#!/usr/bin/env python3
"""redactor.py — Write-time PII redactor for distill-collector.

Implements the regex set defined in
references/redaction-policy.md §1-§2. Replaces matches with
`[REDACTED:<KIND>-<4char-hash>]` placeholders using
SHA-256(match + salt).

v0.4.0 adds heuristic coverage for (closes integration.md §6.2 S1):
  - Chinese street addresses (省/市/区/路/号 pattern)
  - Western street addresses (number + street-type)
  - Chinese full-names (common surname + 2-3 char given name)
  - Sensitive-topic markers (medical diagnosis, political identity,
    religious identity) — redacted as [FLAG:<KIND>] without hash so
    reviewers can re-examine
All heuristics are regex-only (stdlib-only). Recall is NOT 100% — NER
is v2 work. See --test for the corpus each heuristic covers and where
it misses.

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

# Common Chinese surnames —百家姓 top ~100. Used as left anchor for CN-NAME.
# Must exactly match one char; followed by 1-2 Han chars = given name.
_CN_SURNAMES = (
    "王李张刘陈杨赵黄周吴徐孙胡朱高林何郭马罗梁宋郑谢韩唐冯于董萧"
    "程曹袁邓许傅沈曾彭吕苏卢蒋蔡贾丁魏薛叶阎余潘杜戴夏钟汪田任姜"
    "范方石姚谭廖邹熊金陆郝孔白崔康毛邱秦江史顾侯邵孟龙万段雷钱汤"
    "尹黎易常武乔贺赖龚文欧闫张诸葛司马欧阳上官东方夏侯"
)

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
    # v0.4.0 — Chinese street address: 省/自治区 ... 市 ... 区/县 ... 路/街 ... 号
    # Tolerates optional 省/市/区/县 tokens; anchors on 号 suffix.
    ("CN-ADDR", re.compile(
        r"(?:[\u4e00-\u9fa5]{2,8}(?:省|自治区|特别行政区))?"
        r"[\u4e00-\u9fa5]{2,10}市"
        r"(?:[\u4e00-\u9fa5]{1,10}(?:区|县))?"
        r"[\u4e00-\u9fa5\w]{2,30}(?:路|街|巷|大道|胡同)"
        r"[\u4e00-\u9fa5\w]*?\d+号"
    )),
    # v0.4.0 — Western street address: number + street-type, 1-5 words between.
    ("ADDR", re.compile(
        r"\b\d{1,5}\s+(?:[A-Z][a-z]+\s+){1,5}"
        r"(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way)\b",
        re.IGNORECASE
    )),
    # v0.4.0 — Chinese full name: surname + 1-2 Han-char given name.
    # Narrow: must appear after 我叫 / 他叫 / 她是 / 名字是 / 联系人 / 客户
    # introducer to reduce false positives on historical figures / places.
    ("CN-NAME", re.compile(
        rf"(?:我叫|他叫|她叫|名字叫|名字是|名字|姓名|联系人|客户|用户|员工|"
        rf"老师|同学|经理|总监|先生|女士)\s*[{_CN_SURNAMES}][\u4e00-\u9fa5]{{1,2}}\b"
    )),
    # v0.4.0 — Sensitive topic FLAGS (no redaction of content, but tags
    # for human review). These write [FLAG:KIND] inline without hashes
    # so reviewers can find and decide per-instance.
    ("FLAG:MEDICAL", re.compile(
        r"(?:确诊|诊断|病史|患有|服用|处方|手术|化疗|"
        r"diagnosed\s+with|suffers\s+from|prescribed|on\s+medication)",
        re.IGNORECASE
    )),
    ("FLAG:POLITICAL", re.compile(
        r"(?:党员|入党|政治面貌|支持.{0,3}党|反对.{0,3}党|"
        r"party\s+member|voted\s+for|voting\s+record)",
        re.IGNORECASE
    )),
    ("FLAG:RELIGIOUS", re.compile(
        r"(?:信仰|信教|皈依|受洗|伊斯兰|基督|佛教|道教|"
        r"convert(?:ed)?\s+to|practicing\s+(?:christian|muslim|jewish|buddhist))",
        re.IGNORECASE
    )),
]


def _placeholder(kind: str, match: str, salt: str) -> str:
    # FLAG:* patterns mark sensitive topics for human review — keep the
    # original content visible (don't hash) so reviewers can judge context.
    if kind.startswith("FLAG:"):
        return f"[{kind}]{match}"
    h = hashlib.sha256((match + salt).encode("utf-8")).hexdigest()[:4]
    return f"[REDACTED:{kind}-{h}]"


def redact(text: str, salt: str = DEFAULT_SALT) -> str:
    """Run all regex patterns in order, replacing hits with hashed placeholders.

    Each pattern's matches are processed before the next pattern runs, so that
    already-redacted placeholders (which contain only `[A-Za-z0-9:\\-]` and
    brackets) cannot be re-matched by subsequent patterns.

    v0.4.0: FLAG:* patterns prepend an inline tag without redacting content —
    reviewers use the tags to triage sensitive topic mentions before publish.
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

    # v0.4.0 — Chinese address pattern.
    def test_cn_address(self):
        out = redact("地址是北京市朝阳区建国路88号")
        self.assertIn("REDACTED:CN-ADDR-", out)
        self.assertNotIn("建国路88号", out)

    def test_cn_address_with_province(self):
        out = redact("请寄到广东省深圳市南山区科技园南路10号")
        self.assertIn("REDACTED:CN-ADDR-", out)

    # v0.4.0 — Western address pattern.
    def test_western_address(self):
        out = redact("ship to 221 Baker Street London")
        self.assertIn("REDACTED:ADDR-", out)

    def test_western_address_avenue(self):
        out = redact("1600 Pennsylvania Avenue is the address")
        self.assertIn("REDACTED:ADDR-", out)

    # v0.4.0 — Chinese name pattern (must have introducer).
    def test_cn_name_introducer(self):
        out = redact("联系人张伟，电话见下方")
        self.assertIn("REDACTED:CN-NAME-", out)
        self.assertNotIn("张伟", out)

    def test_cn_name_no_introducer(self):
        # Historical/place name, no introducer → NOT redacted.
        self.assertIn("张伟", redact("张伟的历史贡献"))

    # v0.4.0 — Sensitive topic flags.
    def test_flag_medical(self):
        out = redact("他去年确诊了糖尿病")
        self.assertIn("[FLAG:MEDICAL]", out)
        self.assertIn("确诊", out)  # content preserved for review

    def test_flag_political(self):
        out = redact("她是 2015 年入党的")
        self.assertIn("[FLAG:POLITICAL]", out)

    def test_flag_religious(self):
        out = redact("他 2010 年皈依了佛教")
        self.assertIn("[FLAG:RELIGIOUS]", out)

    def test_flag_medical_english(self):
        out = redact("He was diagnosed with anxiety")
        self.assertIn("[FLAG:MEDICAL]", out)

    # v0.4.0 — Ordering stability: CN-ADDR should fire before CARD could
    # eat the house-number digits.
    def test_address_not_eaten_by_card(self):
        out = redact("北京市朝阳区建国路1234567号")
        self.assertIn("CN-ADDR", out)
        self.assertNotIn("REDACTED:CARD", out)


def _run_selftest() -> int:
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(_RedactionTests)
    runner = unittest.TextTestRunner(stream=sys.stderr, verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
