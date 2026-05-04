#!/usr/bin/env python3
"""
validate_rules.py — Schema validator for grammar/rules/*.yaml.

Checks (no semantic judgment, only mechanical schema compliance):
  1. Required fields present (rule_id, section, preconditions, action, why, emerges_from, confidence)
  2. preconditions has product_type / kansei / brand_archetypes (v1.5.0+ mandate)
  3. Enum values legal:
     - section ∈ {color, typography, components, layout, depth_elevation, motion, voice, anti_patterns, spacing}
     - brand_archetypes ⊆ {Sage, Magician, Hero, Outlaw, Explorer, Creator, Innocent, Lover, Caregiver, Ruler, Jester, Everyman}
     - confidence ∈ [0, 1]
  4. rule_id format: <system>-<section>-<keyword>-<NNN>
  5. depends_on / known_conflicts target rule_ids exist somewhere in the library
  6. Kansei words ⊆ controlled vocabulary (references/kansei-theory.md)
     — outside-vocab words become **warnings** not failures (LLM may legitimately add new words)

Usage:
  python3 validate_rules.py [<rules.yaml> ...]      # validate specific files
  python3 validate_rules.py --all                    # validate all grammar/rules/*.yaml
  python3 validate_rules.py --all --strict           # warnings → errors

Exit code 0 = pass; 1 = blockers found; 2 = warnings only (with --strict).
"""
from __future__ import annotations
import sys
import os
import re
import json
import yaml
import glob
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.normpath(os.path.join(HERE, '..'))
RULES_DIR = os.path.join(SKILL_ROOT, 'grammar', 'rules')

VALID_SECTIONS = {'color', 'typography', 'components', 'layout',
                  'depth_elevation', 'motion', 'voice', 'anti_patterns',
                  'spacing'}
VALID_ARCHETYPES = {'Sage', 'Magician', 'Hero', 'Outlaw', 'Explorer', 'Creator',
                    'Innocent', 'Lover', 'Caregiver', 'Ruler', 'Jester', 'Everyman'}
RULE_ID_RE = re.compile(r'^[a-z0-9-]+-(color|typography|components|layout|depth_elevation|motion|voice|anti_patterns|spacing|elevation|color_palette|color_scale|cta|button|card|section|page|nav|header|footer|chrome|button_treatment|sub_section)-[\w-]+-\d{3}$')


def _load_kansei_vocab() -> set[str]:
    """Parse references/kansei-theory.md controlled vocabulary.

    The vocabulary lives in Markdown tables under `## 词表（按维度组织）` (or
    `## Controlled Vocabulary` after v1.6.0 reorg). Each row first cell is a
    word in backticks like `| \\`serious\\` | -0.8 | playful | ... |`."""
    path = os.path.join(SKILL_ROOT, 'references', 'kansei-theory.md')
    if not os.path.isfile(path):
        return set()
    with open(path) as f:
        text = f.read()
    vocab = set()
    in_vocab_section = False
    for line in text.splitlines():
        if re.match(r'^##\s+(Controlled Vocabulary|词表|Vocabulary)', line, re.IGNORECASE):
            in_vocab_section = True
            continue
        if in_vocab_section and re.match(r'^##\s', line):
            # Heuristic: stay inside vocab while we see `### subsection` or table rows
            if not line.startswith('## ') or line.startswith('### '):
                continue
            # Hit a top-level ## that's not vocab — exit
            if not re.match(r'^##\s+(词表|Controlled Vocabulary|Vocabulary)', line, re.IGNORECASE):
                in_vocab_section = False
                continue
        if not in_vocab_section:
            continue
        # Match table row: `| \`word\` | ...` (first cell with backticked word)
        m = re.match(r'^\s*\|\s*`([a-zA-Z_][a-zA-Z0-9_]+)`\s*\|', line)
        if m:
            vocab.add(m.group(1).lower())
            continue
        # Also match bullet-style `- word :` or `- **word**`
        m = re.match(r'^\s*[-*]\s+(?:\*\*)?`?([a-zA-Z_][a-zA-Z0-9_]+)`?', line)
        if m:
            vocab.add(m.group(1).lower())
    return vocab


def _collect_all_rule_ids() -> set[str]:
    """Walk grammar/rules/*.yaml and harvest every rule_id."""
    ids = set()
    for fp in glob.glob(os.path.join(RULES_DIR, '*.yaml')):
        name = os.path.basename(fp)
        if name.startswith('.'):
            continue
        try:
            d = yaml.safe_load(open(fp))
        except Exception:
            continue
        if not d or 'rules' not in d:
            continue
        for r in d['rules']:
            if isinstance(r, dict) and r.get('rule_id'):
                ids.add(r['rule_id'])
    return ids


def validate_rule(r: dict, file_basename: str, all_rule_ids: set[str],
                   kansei_vocab: set[str]) -> tuple[list[str], list[str]]:
    """Return (blockers, warnings) for one rule."""
    blockers, warnings = [], []
    rid = r.get('rule_id', '<missing rule_id>')

    # 1. Required fields
    for field in ('rule_id', 'section', 'preconditions', 'action', 'why',
                  'emerges_from', 'confidence'):
        if field not in r or r[field] in (None, '', []):
            blockers.append(f'{rid}: missing or empty `{field}`')

    # 2. preconditions must have kansei + brand_archetypes; product_type required
    # except for anti_patterns (which apply universally — they guard against
    # archetype degeneracies without targeting a specific product type).
    pre = r.get('preconditions', {}) or {}
    section = r.get('section')
    if not pre.get('product_type') and section != 'anti_patterns':
        blockers.append(f'{rid}: preconditions.product_type missing or empty')
    if not pre.get('kansei'):
        blockers.append(f'{rid}: preconditions.kansei missing or empty')
    if not pre.get('brand_archetypes'):
        blockers.append(f'{rid}: preconditions.brand_archetypes missing or empty (v1.5.0+ mandate)')

    # 3. Enum values
    section = r.get('section')
    if section and section not in VALID_SECTIONS:
        blockers.append(f'{rid}: section `{section}` not in valid set {sorted(VALID_SECTIONS)}')

    archetypes = pre.get('brand_archetypes', []) or []
    for a in archetypes:
        if a not in VALID_ARCHETYPES:
            blockers.append(f'{rid}: brand_archetype `{a}` not in 12-archetype list')

    conf = r.get('confidence')
    if conf is not None:
        try:
            cf = float(conf)
            if cf < 0 or cf > 1:
                blockers.append(f'{rid}: confidence `{conf}` out of [0, 1]')
        except (TypeError, ValueError):
            blockers.append(f'{rid}: confidence `{conf}` not numeric')

    # 4. rule_id format (warning, not blocker — some legacy rules may not match strictly)
    if rid and rid != '<missing rule_id>':
        if not re.match(r'^[a-z0-9-]+-[a-z_]+-[\w-]+-\d{3}$', rid):
            warnings.append(f'{rid}: rule_id format does not match `<system>-<section>-<keyword>-<NNN>`')

    # 5. depends_on / known_conflicts target existence
    deps = (r.get('preconditions', {}) or {}).get('requires', []) or []
    for dep in deps:
        if dep not in all_rule_ids:
            blockers.append(f'{rid}: requires `{dep}` does not exist in any rules.yaml')
    for kc in (r.get('known_conflicts') or []):
        target = kc.get('rule') if isinstance(kc, dict) else kc
        if target and target not in all_rule_ids:
            blockers.append(f'{rid}: known_conflicts.rule `{target}` does not exist')

    # 6. Kansei vocab compliance (warning only)
    kansei_words = pre.get('kansei', []) or []
    if kansei_vocab:
        for w in kansei_words:
            if isinstance(w, str) and w.lower() not in kansei_vocab:
                warnings.append(f'{rid}: kansei `{w}` not in controlled vocabulary (references/kansei-theory.md). Consider adding to vocab or using a synonym.')

    # File-name vs rule_id system prefix consistency check (warning)
    expected_prefix = file_basename.replace('.yaml', '') + '-'
    if rid and not rid.startswith(expected_prefix) and rid != '<missing rule_id>':
        warnings.append(f'{rid}: rule_id should start with `{expected_prefix}` (file is {file_basename})')

    return blockers, warnings


def validate_file(path: str, all_rule_ids: set[str], kansei_vocab: set[str]) -> dict:
    """Validate one rules.yaml file. Returns {blockers, warnings, rule_count}."""
    basename = os.path.basename(path)
    out = {'file': path, 'blockers': [], 'warnings': [], 'rule_count': 0}
    try:
        d = yaml.safe_load(open(path))
    except Exception as e:
        out['blockers'].append(f'{basename}: YAML parse error: {e}')
        return out
    if not d:
        out['warnings'].append(f'{basename}: empty file')
        return out
    if 'rules' not in d:
        out['blockers'].append(f'{basename}: top-level `rules:` key missing')
        return out
    rules = d['rules']
    if not isinstance(rules, list):
        out['blockers'].append(f'{basename}: `rules` is not a list')
        return out
    out['rule_count'] = len(rules)
    for r in rules:
        if not isinstance(r, dict):
            out['blockers'].append(f'{basename}: non-dict rule entry')
            continue
        b, w = validate_rule(r, basename, all_rule_ids, kansei_vocab)
        out['blockers'].extend(b)
        out['warnings'].extend(w)
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('files', nargs='*', help='Specific rules.yaml files (default: all)')
    p.add_argument('--all', action='store_true', help='Validate all grammar/rules/*.yaml')
    p.add_argument('--strict', action='store_true', help='Warnings become exit-code-1 failures')
    p.add_argument('--json', action='store_true', help='Output as JSON instead of human text')
    args = p.parse_args()

    if args.all or not args.files:
        files = sorted([f for f in glob.glob(os.path.join(RULES_DIR, '*.yaml'))
                         if not os.path.basename(f).startswith('.')])
    else:
        files = args.files

    all_rule_ids = _collect_all_rule_ids()
    kansei_vocab = _load_kansei_vocab()

    results = [validate_file(fp, all_rule_ids, kansei_vocab) for fp in files]
    total_blockers = sum(len(r['blockers']) for r in results)
    total_warnings = sum(len(r['warnings']) for r in results)
    total_rules = sum(r['rule_count'] for r in results)

    if args.json:
        print(json.dumps({
            'files_checked': len(results),
            'total_rules': total_rules,
            'total_blockers': total_blockers,
            'total_warnings': total_warnings,
            'kansei_vocab_size': len(kansei_vocab),
            'results': results,
        }, indent=2))
    else:
        print(f'Validated {len(results)} files / {total_rules} rules')
        print(f'  Blockers: {total_blockers}')
        print(f'  Warnings: {total_warnings}')
        print(f'  Kansei vocab loaded: {len(kansei_vocab)} words')
        if total_blockers:
            print('\nBLOCKERS:')
            for r in results:
                for b in r['blockers']:
                    print(f'  ✗ [{os.path.basename(r["file"])}] {b}')
        if total_warnings:
            print('\nWARNINGS:')
            shown = 0
            for r in results:
                for w in r['warnings']:
                    print(f'  ⚠ [{os.path.basename(r["file"])}] {w}')
                    shown += 1
                    if shown >= 30:
                        remaining = total_warnings - shown
                        if remaining > 0:
                            print(f'  ... ({remaining} more warnings, run with --json for full list)')
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
