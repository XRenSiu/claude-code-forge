#!/usr/bin/env python3
"""
count_terms.py — the mechanical primitive behind the docs channel.

`assets/docs_extraction_prompt.md` asks for each term's approximate frequency and
2-3 quotes showing how it is used. Without a primitive, "≈47 occurrences" is a
number the reader has to take on faith and nobody can reproduce — and the operator
ends up hand-rolling a regex per term. This script makes the count a rerunnable
measurement: same term file + same corpus => same table, byte for byte.

It counts. It does NOT classify, merge, or judge — those are Judgments 1/2/3/4.

Usage:
    count_terms.py --terms terms.txt --group docs='docs/**/*.md' \
                   --group skills='skills/*/SKILL.md' [--out 01b_docs_terms.md]
    count_terms.py --terms terms.txt --group all='**/*.md' --json

Terms file — one term-group per line, `#` comments and blank lines ignored:

    # canonical label = comma-separated variants counted toward it
    Gate = 门, Gate, G1, G2, G3
    Contract = 契约, Contract, done_when
    Card = /卡(?!通)/, Card, CARD-\\d+

  - A variant in `/.../` is a regular expression; anything else is a literal.
  - Literal variants that start and end with a word character are matched on word
    boundaries, so `PR` does not fire inside `PROPOSAL`. CJK variants have no word
    boundary and are matched as substrings — the same rule a hand-rolled grep uses.
  - Matching is case-insensitive unless `--case-sensitive` is given.
  - A line with no `=` is a term whose only variant is itself.

Groups — `--group NAME=GLOB` (repeatable) splits the corpus into named columns, the
`(≈150 docs · 321 skills · 68 data)` shape the docs pass reports. Globs are relative
to `--root` (default: the current directory) and understand `**`. With no `--group`,
everything matched by `--corpus` lands in one column called `all`.

Output: a Markdown table plus per-term evidence lines (`file:line` + the matching
line, trimmed), or `--json` for a machine-readable count map.

Exit 0 always unless the terms file or a glob is unreadable (exit 2), or a term
matched nothing anywhere (exit 1) — a zero-count term is either a dead word or a
typo in the term file, and silently reporting `0` hides both.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

WORDISH = re.compile(r"\w", re.UNICODE)
ASCII_WORD_EDGE = re.compile(r"^[A-Za-z0-9_].*[A-Za-z0-9_]$|^[A-Za-z0-9_]$")


def variant_pattern(variant: str) -> str:
    """Turn one variant into a regex source string."""
    v = variant.strip()
    if len(v) >= 2 and v.startswith("/") and v.endswith("/"):
        return v[1:-1]
    esc = re.escape(v)
    # Word boundaries only help for ASCII identifiers; CJK has no \b transition.
    if ASCII_WORD_EDGE.match(v):
        return rf"\b{esc}\b"
    return esc


def parse_terms(path: Path) -> list[tuple[str, list[str]]]:
    out: list[tuple[str, list[str]]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            label, rhs = line.split("=", 1)
            variants = [v for v in (x.strip() for x in rhs.split(",")) if v]
        else:
            label, variants = line, [line]
        label = label.strip()
        if not label or not variants:
            continue
        out.append((label, variants))
    return out


def compile_term(variants: list[str], case_sensitive: bool) -> re.Pattern:
    src = "|".join(f"(?:{variant_pattern(v)})" for v in variants)
    return re.compile(src, 0 if case_sensitive else re.IGNORECASE)


def expand(root: Path, patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pat in patterns:
        files.extend(p for p in root.glob(pat) if p.is_file())
    # stable, de-duplicated
    return sorted(set(files))


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--terms", type=Path, required=True, help="terms file (see the docstring)")
    ap.add_argument("--root", type=Path, default=Path("."), help="glob root (default: cwd)")
    ap.add_argument("--group", action="append", default=[], metavar="NAME=GLOB",
                    help="named corpus column; repeatable. Repeat the same NAME to add globs.")
    ap.add_argument("--corpus", action="append", default=[], metavar="GLOB",
                    help="ungrouped glob; everything lands in the column `all`")
    ap.add_argument("--quotes", type=int, default=3, help="evidence lines per term (default 3)")
    ap.add_argument("--quote-chars", type=int, default=120, help="max evidence line length")
    ap.add_argument("--case-sensitive", action="store_true")
    ap.add_argument("--out", type=Path, help="write Markdown here (default: stdout)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    a = ap.parse_args()

    if not a.terms.exists():
        sys.stderr.write(f"count_terms: terms file not found: {a.terms}\n")
        return 2
    terms = parse_terms(a.terms)
    if not terms:
        sys.stderr.write(f"count_terms: no terms parsed from {a.terms}\n")
        return 2

    groups: dict[str, list[str]] = defaultdict(list)
    for spec in a.group:
        if "=" not in spec:
            sys.stderr.write(f"count_terms: --group needs NAME=GLOB, got {spec!r}\n")
            return 2
        name, glob = spec.split("=", 1)
        groups[name.strip()].append(glob.strip())
    for glob in a.corpus:
        groups["all"].append(glob)
    if not groups:
        sys.stderr.write("count_terms: give at least one --group NAME=GLOB or --corpus GLOB\n")
        return 2

    group_files = {name: expand(a.root, pats) for name, pats in groups.items()}
    empty = [n for n, fs in group_files.items() if not fs]
    for n in empty:
        sys.stderr.write(f"count_terms: WARNING group '{n}' matched no files\n")

    counts: dict[str, dict[str, int]] = {label: {} for label, _ in terms}
    evidence: dict[str, list[str]] = defaultdict(list)
    files_read = 0

    compiled = [(label, compile_term(variants, a.case_sensitive), variants)
                for label, variants in terms]

    for gname, files in group_files.items():
        for label, _, _ in compiled:
            counts[label].setdefault(gname, 0)
        for path in files:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            files_read += 1
            rel = path.relative_to(a.root) if a.root in path.parents or path.parent == a.root \
                else path
            lines = text.splitlines()
            for label, pat, _ in compiled:
                if not pat.search(text):
                    continue
                for lineno, line in enumerate(lines, 1):
                    hits = len(pat.findall(line))
                    if not hits:
                        continue
                    counts[label][gname] += hits
                    if len(evidence[label]) < a.quotes:
                        snippet = line.strip()
                        if len(snippet) > a.quote_chars:
                            snippet = snippet[:a.quote_chars - 1] + "…"
                        evidence[label].append(f"`{rel}:{lineno}` — {snippet}")

    gnames = list(group_files.keys())
    zero = [label for label in counts if sum(counts[label].values()) == 0]

    if a.json:
        payload = {
            "terms": {label: {"by_group": counts[label],
                              "total": sum(counts[label].values()),
                              "variants": variants,
                              "evidence": evidence[label]}
                      for label, _, variants in compiled},
            "groups": {n: len(fs) for n, fs in group_files.items()},
            "files_read": files_read,
            "zero_count_terms": zero,
        }
        text = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        out: list[str] = []
        out.append("# Term counts")
        out.append("")
        out.append(f"- Terms file: `{a.terms}` ({len(terms)} term groups)")
        out.append(f"- Root: `{a.root}`")
        for n in gnames:
            out.append(f"- Corpus `{n}`: {len(group_files[n])} files "
                       f"({', '.join('`' + g + '`' for g in groups[n])})")
        out.append(f"- Matching: {'case-sensitive' if a.case_sensitive else 'case-insensitive'}; "
                   "ASCII variants on word boundaries, CJK variants as substrings")
        out.append("")
        out.append("| Term | " + " | ".join(gnames) + " | total | variants |")
        out.append("|---|" + "---|" * (len(gnames) + 2))
        for label, _, variants in sorted(
                compiled, key=lambda t: -sum(counts[t[0]].values())):
            row = [str(counts[label].get(g, 0)) for g in gnames]
            out.append(f"| **{label}** | " + " | ".join(row) + " | "
                       f"{sum(counts[label].values())} | "
                       f"{', '.join('`' + v + '`' for v in variants)} |")
        out.append("")
        out.append("## Evidence")
        out.append("")
        for label, _, _ in sorted(compiled, key=lambda t: -sum(counts[t[0]].values())):
            out.append(f"- **{label}** ({sum(counts[label].values())})")
            for e in evidence[label] or ["_no occurrence_"]:
                out.append(f"  - {e}")
        if zero:
            out.append("")
            out.append("## Zero-count terms")
            out.append("")
            out.append("Each of these is either a dead word or a typo in the terms file. "
                       "Resolve before using this table as evidence.")
            out.append("")
            for label in zero:
                out.append(f"- `{label}`")
        text = "\n".join(out) + "\n"

    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(text, encoding="utf-8")
        print(f"Wrote {a.out} — {len(terms)} terms over {files_read} files")
    else:
        print(text)

    if zero:
        sys.stderr.write(
            f"count_terms: {len(zero)} term(s) matched nothing: {', '.join(zero)}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
