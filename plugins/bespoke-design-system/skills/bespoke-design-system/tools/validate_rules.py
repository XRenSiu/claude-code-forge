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
RULE_ID_RE = re.compile(r'^[a-z0-9-]+-(color|typography|components|layout|depth_elevation|motion|voice|anti_patterns|spacing|elevation|color_palette|color_scale|cta|button|card|section|page|nav|header|footer|chrome|button_treatment|sub_section|meta)-[\w-]+-\d{3}$')

# Map section names to all the rule_id-segment forms they can take. Used by
# the F3 system-section consistency check. Each segment is expanded to both
# underscore and hyphen forms (e.g., 'anti_patterns' → also matches '-anti-pattern-'
# in rule_ids since rule_ids use hyphens).
SECTION_TO_ID_SEGMENTS = {
    'color': {'color', 'color-palette', 'color-scale', 'color_palette', 'color_scale'},
    'typography': {'typography', 'type', 'fonts'},
    'components': {'components', 'component', 'cta', 'button', 'card', 'nav',
                   'header', 'footer', 'button-treatment', 'sub-section', 'form'},
    'layout': {'layout', 'spacing', 'grid'},
    'depth_elevation': {'depth_elevation', 'depth-elevation', 'elevation', 'shadow', 'depth'},
    'motion': {'motion', 'animation'},
    'voice': {'voice', 'tone', 'copy'},
    'anti_patterns': {'anti_patterns', 'anti-pattern', 'anti_pattern', 'antipattern', 'meta'},
    'spacing': {'spacing', 'layout'},
}


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
                   kansei_vocab: set[str], registry: dict | None = None,
                   strict_vocab: bool = False) -> tuple[list[str], list[str]]:
    """Return (blockers, warnings) for one rule.

    v1.7.0 additions:
      - F3: rule_id segment must be consistent with `section:` field
      - F5: high confidence on stub-source rules → warning
      - F8: confidence > 0.7 with single emerges_from → warning (premature high confidence)
      - --strict-vocab: off-vocab kansei → blocker instead of warning
    """
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

    # 4.5 (v1.7.0 F3): rule_id system-section consistency
    # rule_id format: <system>-<section_segment>-<keyword>-<NNN>. Verify the
    # second segment matches the actual `section:` field via SECTION_TO_ID_SEGMENTS.
    if rid and rid != '<missing rule_id>' and section:
        # Extract second segment. Handle compound system names like 'linear-app':
        # search for the section_segment by matching against the legal set.
        rid_lower = rid.lower()
        legal_segments = SECTION_TO_ID_SEGMENTS.get(section, set())
        if legal_segments:
            # Look for any legal segment as a `-<seg>-` pattern in the rule_id
            found = any(f'-{seg}-' in rid_lower for seg in legal_segments)
            if not found:
                warnings.append(
                    f'{rid}: rule_id segment does not match section `{section}`. '
                    f'Expected one of {sorted(legal_segments)} in the rule_id; '
                    f'this can confuse downstream rule_id parsing.'
                )

    # 5. depends_on / known_conflicts target existence
    deps = (r.get('preconditions', {}) or {}).get('requires', []) or []
    for dep in deps:
        if dep not in all_rule_ids:
            blockers.append(f'{rid}: requires `{dep}` does not exist in any rules.yaml')
    for kc in (r.get('known_conflicts') or []):
        target = kc.get('rule') if isinstance(kc, dict) else kc
        if target and target not in all_rule_ids:
            blockers.append(f'{rid}: known_conflicts.rule `{target}` does not exist')

    # 6. Kansei vocab compliance (warning by default; blocker with --strict-vocab — F2)
    kansei_words = pre.get('kansei', []) or []
    if kansei_vocab:
        for w in kansei_words:
            if isinstance(w, str) and w.lower() not in kansei_vocab:
                msg = f'{rid}: kansei `{w}` not in controlled vocabulary (references/kansei-theory.md). Consider adding to vocab or using a synonym.'
                if strict_vocab:
                    blockers.append(msg)
                else:
                    warnings.append(msg)

    # File-name vs rule_id system prefix consistency check (warning)
    expected_prefix = file_basename.replace('.yaml', '') + '-'
    if rid and not rid.startswith(expected_prefix) and rid != '<missing rule_id>':
        warnings.append(f'{rid}: rule_id should start with `{expected_prefix}` (file is {file_basename})')

    # 7. (v1.7.0 F5): high confidence on stub-source rules → warning
    emerges_from = r.get('emerges_from') or []
    if registry and emerges_from:
        confidence = r.get('confidence')
        try:
            cf = float(confidence) if confidence is not None else None
        except Exception:
            cf = None
        if cf is not None and cf > 0.55:
            for source_sys in emerges_from:
                entry = registry.get('systems', {}).get(source_sys, {})
                if entry.get('source_type') in ('stub', 'archetype_template_stub'):
                    warnings.append(
                        f'{rid}: confidence {cf:.2f} > 0.55 but source `{source_sys}` is marked '
                        f'`source_type: stub`. Stub DESIGN.md (e.g. generative archetype templates) '
                        f'cannot support high confidence — cap at 0.5.'
                    )
                    break

    # 8. (v1.7.0 F8): confidence > 0.7 with only one source → warning
    # First-extraction rules cannot have high confidence per the rubric in
    # scripts/extract-grammar.md A3 step 5.
    confidence = r.get('confidence')
    try:
        cf = float(confidence) if confidence is not None else None
    except Exception:
        cf = None
    if cf is not None and cf > 0.7 and len(emerges_from) == 1:
        warnings.append(
            f'{rid}: confidence {cf:.2f} > 0.7 but emerges_from has only 1 system '
            f'(`{emerges_from[0]}`). Per A3 confidence rubric, single-source rules cap at 0.7. '
            f'Either lower confidence, or merge_with peers from other systems first.'
        )

    return blockers, warnings


def validate_file(path: str, all_rule_ids: set[str], kansei_vocab: set[str],
                   registry: dict | None = None, strict_vocab: bool = False) -> dict:
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

    # v1.7.0 F6: archetype uniformity check at file level — calibrated v1.7.0
    # Small systems (≤ 5 rules) genuinely may have uniform brand_archetypes
    # since they are niche-specific. Trigger only when:
    #   - > 5 rules AND uniformity > 90%, OR
    #   - > 8 rules AND uniformity > 80%
    archetype_signatures = []
    for r in rules:
        if not isinstance(r, dict):
            continue
        archs = (r.get('preconditions') or {}).get('brand_archetypes') or []
        archetype_signatures.append(tuple(sorted(archs)))
    if len(archetype_signatures) > 5:
        from collections import Counter
        sig_counts = Counter(archetype_signatures)
        most_common, most_common_n = sig_counts.most_common(1)[0]
        uniformity = most_common_n / len(archetype_signatures)
        threshold_uniformity = 0.9 if len(archetype_signatures) <= 8 else 0.8
        if uniformity > threshold_uniformity and len(sig_counts) <= 2:
            out['warnings'].append(
                f'{basename}: {most_common_n}/{len(archetype_signatures)} rules ({uniformity*100:.0f}%) '
                f'share the same brand_archetypes `{list(most_common)}`. This may indicate lazy '
                f'system-default stamping — per v1.6.0 anti-laziness guidance, anti_patterns rules '
                f'often span more archetypes, voice rules often span fewer. Re-check per-rule archetype '
                f'choices.'
            )

    for r in rules:
        if not isinstance(r, dict):
            out['blockers'].append(f'{basename}: non-dict rule entry')
            continue
        b, w = validate_rule(r, basename, all_rule_ids, kansei_vocab,
                              registry=registry, strict_vocab=strict_vocab)
        out['blockers'].extend(b)
        out['warnings'].extend(w)
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('files', nargs='*', help='Specific rules.yaml files (default: all)')
    p.add_argument('--all', action='store_true', help='Validate all grammar/rules/*.yaml')
    p.add_argument('--strict', action='store_true', help='Warnings become exit-code-1 failures')
    p.add_argument('--strict-vocab', action='store_true',
                    help='v1.7.0 F2: off-vocab kansei words become blockers (governance: prevents on-the-fly vocab additions during A3)')
    p.add_argument('--json', action='store_true', help='Output as JSON instead of human text')
    args = p.parse_args()

    if args.all or not args.files:
        files = sorted([f for f in glob.glob(os.path.join(RULES_DIR, '*.yaml'))
                         if not os.path.basename(f).startswith('.')])
    else:
        files = args.files

    all_rule_ids = _collect_all_rule_ids()
    kansei_vocab = _load_kansei_vocab()

    # Load source-registry for F5 (stub-source confidence check)
    registry = None
    registry_path = os.path.join(SKILL_ROOT, 'grammar', 'meta', 'source-registry.json')
    if os.path.isfile(registry_path):
        try:
            with open(registry_path) as f:
                registry = json.load(f)
        except Exception:
            pass

    results = [validate_file(fp, all_rule_ids, kansei_vocab,
                              registry=registry, strict_vocab=args.strict_vocab) for fp in files]
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
