#!/usr/bin/env python3
"""
validate_rationale.py — Schema validator for grammar/rationale/*.md.

Checks (no semantic judgment, only mechanical schema compliance):
  1. Top-level header present: `# Rationale — <system>`
  2. At least one `## <section>` heading (color / typography / etc.)
  3. Each `### decision: <text>` block contains:
     - `- **trade_off**:` line
     - `- **intent**:` line
     - `- **avoid**:` line
  4. v1.7.0 F9: each decision should contain at least one verbatim DESIGN.md
     blockquote (lines starting with `>`) — flagged as warning if absent
  5. System name in header matches filename

Usage:
  python3 validate_rationale.py [<rationale.md> ...]
  python3 validate_rationale.py --all

Exit code 0 = pass; 1 = blockers; 2 = warnings only with --strict.
"""
from __future__ import annotations
import sys
import os
import re
import json
import glob
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.normpath(os.path.join(HERE, '..'))
RATIONALE_DIR = os.path.join(SKILL_ROOT, 'grammar', 'rationale')

# v1.7.1: tighten DECISION_RE so an empty `### decision:` line cannot silently
# absorb the next line as its title via `\s+` spanning newlines. We restrict
# the post-colon whitespace to spaces/tabs and require the title to start
# with a non-whitespace character.
DECISION_RE = re.compile(r'^###[ \t]+decision:[ \t]+(\S.*)$', re.MULTILINE)
EMPTY_DECISION_RE = re.compile(r'^###[ \t]+decision:[ \t]*$', re.MULTILINE)
SECTION_RE = re.compile(r'^##\s+(.+?)$', re.MULTILINE)


def _split_decisions(text: str) -> list[tuple[str, str]]:
    """Return list of (decision_title, decision_body) tuples."""
    matches = list(DECISION_RE.finditer(text))
    out = []
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        out.append((title, text[start:end]))
    return out


def validate_file(path: str) -> dict:
    basename = os.path.basename(path)
    out = {'file': path, 'blockers': [], 'warnings': [], 'decision_count': 0,
           'system_in_header': None}
    if not os.path.isfile(path):
        out['blockers'].append(f'{basename}: file not found')
        return out
    with open(path) as f:
        text = f.read()

    # 1. Top-level header
    m = re.match(r'^#\s+Rationale\s+[—\-]\s+(\S+)', text)
    if not m:
        out['blockers'].append(f'{basename}: missing top-level `# Rationale — <system>` header')
    else:
        sys_name = m.group(1)
        out['system_in_header'] = sys_name
        # 5. system name matches filename
        expected = basename.replace('.md', '')
        if sys_name != expected:
            out['warnings'].append(f'{basename}: header system `{sys_name}` does not match filename `{expected}`')

    # 2. At least one `## section` heading
    sections = SECTION_RE.findall(text)
    if not sections:
        out['blockers'].append(f'{basename}: no `## <section>` headings found')

    # 3. Each decision must have trade_off / intent / avoid
    decisions = _split_decisions(text)
    out['decision_count'] = len(decisions)
    if not decisions:
        out['blockers'].append(f'{basename}: no `### decision:` blocks found')

    # 3.5 (v1.7.1): titleless `### decision:` lines are blockers. Previously
    # the lax `\s+` regex absorbed the next line as a title and silently
    # produced confusing downstream messages. Catch these explicitly.
    for m in EMPTY_DECISION_RE.finditer(text):
        line_no = text[:m.start()].count('\n') + 1
        out['blockers'].append(
            f'{basename}: empty `### decision:` header at line {line_no} — '
            f'every decision needs a non-empty one-line title.'
        )

    for i, (title, body) in enumerate(decisions):
        title_short = title[:60]
        # Required three-part fields (with markdown emphasis)
        # v1.7.1 (#35): also require non-empty content after the colon.
        # Previously `- **trade_off**:` (empty value) would pass, leaving
        # rationale schema-shaped but semantically void.
        for required in ('trade_off', 'intent', 'avoid'):
            present_pattern = re.compile(
                rf'^\s*[-*]\s*\*\*{re.escape(required)}\*\*\s*:', re.MULTILINE
            )
            # Content can be either:
            #   (a) on the same line: `- **avoid**: 多色感 / 干涸感`
            #   (b) on indented sub-bullets: `- **avoid**:\n  - x\n  - y`
            # Reject only when neither (a) nor (b) is satisfied.
            same_line_pattern = re.compile(
                rf'^\s*[-*]\s*\*\*{re.escape(required)}\*\*\s*:[ \t]*\S',
                re.MULTILINE,
            )
            sub_bullet_pattern = re.compile(
                rf'^\s*[-*]\s*\*\*{re.escape(required)}\*\*\s*:[ \t]*\n(?:[ \t]+[-*]\s+\S)',
                re.MULTILINE,
            )
            if not present_pattern.search(body):
                out['blockers'].append(
                    f'{basename}: decision "{title_short}" missing `- **{required}**:` line'
                )
            elif not (same_line_pattern.search(body) or sub_bullet_pattern.search(body)):
                out['blockers'].append(
                    f'{basename}: decision "{title_short}" has empty `- **{required}**:` '
                    f'(line is present but no content after the colon and no sub-bullets follow)'
                )

        # 4. (v1.7.0 F9): verbatim DESIGN.md blockquote presence (warning)
        # Look for at least one line starting with `>` in this decision body
        if not re.search(r'^>\s', body, re.MULTILINE):
            out['warnings'].append(
                f'{basename}: decision "{title_short}" lacks a `>` blockquote citing the DESIGN.md '
                f'source — per v1.7.0 F9, A2 rationale should include verbatim quotes from DESIGN.md '
                f'so downstream B4 inheritance can trace to the original designer prose.'
            )

    return out


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('files', nargs='*', help='Specific rationale.md files (default: all)')
    p.add_argument('--all', action='store_true', help='Validate all grammar/rationale/*.md')
    p.add_argument('--strict', action='store_true', help='Warnings become exit-code-2 failures')
    p.add_argument('--json', action='store_true')
    args = p.parse_args()

    if args.all or not args.files:
        files = sorted([f for f in glob.glob(os.path.join(RATIONALE_DIR, '*.md'))
                         if not os.path.basename(f).startswith('.')])
    else:
        files = args.files

    results = [validate_file(fp) for fp in files]
    total_blockers = sum(len(r['blockers']) for r in results)
    total_warnings = sum(len(r['warnings']) for r in results)
    total_decisions = sum(r['decision_count'] for r in results)

    if args.json:
        print(json.dumps({
            'files_checked': len(results),
            'total_decisions': total_decisions,
            'total_blockers': total_blockers,
            'total_warnings': total_warnings,
            'results': results,
        }, indent=2))
    else:
        print(f'Validated {len(results)} rationale files / {total_decisions} decisions')
        print(f'  Blockers: {total_blockers}')
        print(f'  Warnings: {total_warnings}')
        if total_blockers:
            print('\nBLOCKERS:')
            for r in results:
                for b in r['blockers']:
                    print(f'  ✗ {b}')
        if total_warnings:
            print('\nWARNINGS:')
            shown = 0
            for r in results:
                for w in r['warnings']:
                    print(f'  ⚠ {w}')
                    shown += 1
                    if shown >= 30:
                        remaining = total_warnings - shown
                        if remaining > 0:
                            print(f'  ... ({remaining} more, run with --json for full list)')
                            break
                if shown >= 30:
                    break

    if total_blockers:
        sys.exit(1)
    if total_warnings and args.strict:
        sys.exit(2)
    sys.exit(0)


if __name__ == '__main__':
    main()
