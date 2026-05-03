#!/usr/bin/env python3
"""
archetype_check.py — Subcheck 2 of B5 P0 gate: brand archetype fit.

Loads checks/_shared/archetype_rules.json and evaluates each rule's assertion
against the generated tokens. Primary archetype's `never` rules are blockers;
secondary archetype's `never` rules are warnings; `always` missing → warning.

Usage:
  python3 archetype_check.py <tokens.json> --primary Sage [--secondary Magician]
"""
from __future__ import annotations
import json
import sys
import os
import argparse
import re
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from color_math import hex_to_oklch


HERE = os.path.dirname(os.path.abspath(__file__))
RULES_PATH = os.path.join(HERE, '_shared', 'archetype_rules.json')


def _all_chromatic_hexes(tokens: dict) -> list[tuple[str, float, float, float]]:
    color = tokens.get('color', {}) or {}
    out = []
    seen = set()
    for hx in (color.get('all_hex_colors') or []):
        if isinstance(hx, str) and hx.startswith('#') and hx.lower() not in seen:
            try:
                L, C, H = hex_to_oklch(hx)
                out.append((hx, L, C, H))
                seen.add(hx.lower())
            except Exception:
                pass
    return out


def _derived_signals(tokens: dict) -> dict:
    color = tokens.get('color', {}) or {}
    typo = tokens.get('typography', {}) or {}
    radius = tokens.get('radius', {}) or {}
    motion = tokens.get('motion', {}) or {}

    chromatics = _all_chromatic_hexes(tokens)
    chromatic_only = [c for c in chromatics if c[2] >= 0.06]

    sat_max = max((c[2] for c in chromatic_only), default=0.0)
    sat_avg = (sum(c[2] for c in chromatic_only) / len(chromatic_only)) if chromatic_only else 0.0
    L_min = min((c[1] for c in chromatics), default=1.0)
    L_max = max((c[1] for c in chromatics), default=0.0)

    palette_hues = [c[3] for c in chromatic_only]
    has_warm = any(0 <= h <= 60 or 300 <= h < 360 for h in palette_hues)
    has_cool = any(180 <= h <= 270 for h in palette_hues)
    has_purple = any(260 <= h <= 320 for h in palette_hues)

    if has_warm and not has_cool:
        palette_temp = 'warm'
    elif has_cool and not has_warm:
        palette_temp = 'cool'
    elif has_warm and has_cool:
        palette_temp = 'mixed'
    elif chromatic_only:
        palette_temp = 'neutral'
    else:
        palette_temp = 'achromatic'

    weights = typo.get('weights_seen') or []
    weight_max = max(weights) if weights else 0
    families = typo.get('families') or []
    family_names = ' '.join(f.get('family', '') if isinstance(f, dict) else str(f)
                             for f in families).lower()
    has_serif = any(k in family_names for k in ('serif', 'georgia', 'cormorant', 'didone'))
    is_humanist = any(k in family_names for k in ('inter', 'sf pro', 'system-ui',
                                                    'feather', 'gg sans', 'cereal',
                                                    'helvetica', 'sohne'))

    radius_role_pairs = (radius.get('role_radius_pairs') or {}) if isinstance(radius, dict) else {}
    radius_values = []
    for v in radius_role_pairs.values():
        if isinstance(v, (int, float)) and 0 < v < 200:
            radius_values.append(v)
    if not radius_values and isinstance(radius, dict):
        for v in radius.values():
            if isinstance(v, (int, float)) and 0 < v < 200:
                radius_values.append(v)
    radius_max = max(radius_values, default=0)
    radius_medium = sorted(radius_values)[len(radius_values) // 2] if radius_values else 0

    easing_kw = ' '.join(motion.get('easing_keywords') or [])
    bezier_curves = motion.get('cubic_bezier_curves') or []
    has_bounce = ('spring' in easing_kw.lower() or 'bounce' in easing_kw.lower()
                  or any(re.search(r'1\.[5-9]', str(c)) for c in bezier_curves))

    body_contrast = (color.get('contrast', {}) or {}).get('body_on_bg', None)
    if body_contrast is None:
        try:
            from coherence_check import subcheck_wcag
            wcag = subcheck_wcag(tokens)
            if wcag.get('pairs_checked'):
                body_pairs = [p for p in wcag['pairs_checked'] if p.get('tier') == 'body']
                if body_pairs:
                    body_contrast = max(p['ratio'] for p in body_pairs)
        except Exception:
            pass

    return {
        'color': {
            'brand': {
                'saturation_max': round(sat_max, 3),
                'saturation_avg': round(sat_avg, 3),
                'chromatic_count': len(chromatic_only),
                'is_dark_or_navy': L_min <= 0.20,
                'is_safe_blue_purple': any(220 <= h <= 280 for h in palette_hues) and 0.4 <= sat_avg <= 0.7,
            },
            'dark_surface': {
                'lightness_min': round(L_min, 3),
            },
            'palette_temperature': palette_temp,
            'palette_includes_purple_or_metallic': has_purple,
            'palette_includes_dark_or_metallic': L_min <= 0.20 or has_purple,
            'palette_has_earth_tones': any(20 <= h <= 60 for h in palette_hues) and any(c[2] < 0.5 for c in chromatic_only),
            'is_pure_monochromatic': len(palette_hues) > 0 and len(set(round(h / 30) * 30 for h in palette_hues)) == 1,
            'palette_is_monochromatic_only': len(palette_hues) > 0 and len(set(round(h / 30) * 30 for h in palette_hues)) == 1,
            'has_high_contrast_binary': L_min < 0.10 and L_max > 0.95,
            'has_high_contrast_severe': L_min < 0.05 and L_max > 0.98,
            'has_aggressive_palette': sat_max > 0.85 and L_max > 0.7,
            'has_multiple_brand_colors': len(chromatic_only) >= 3,
            'uses_pastel_or_soft_tints': any(L > 0.85 and 0.05 < c <= 0.3 for hx, L, c, h in chromatics),
            'gradient_count': 0,
            'contrast': {
                'body_on_bg': body_contrast,
            },
        },
        'spacing': {
            'base': (tokens.get('spacing', {}) or {}).get('base_unit_px'),
        },
        'radius': {
            'max': radius_max,
            'medium': radius_medium,
        },
        'typography': {
            'weight_ladder_max': weight_max,
            'has_serif': has_serif,
            'has_humanist_or_serif': has_serif or is_humanist,
            'has_humanist_or_rounded': is_humanist,
            'is_humanist_sans': is_humanist and not has_serif,
            'has_serif_or_strong_weight_contrast': has_serif or (weight_max - min(weights, default=400) >= 200),
            'is_geometric_only': not has_serif and not is_humanist,
            'is_geometric_cold': not has_serif and 'inter' not in family_names and 'feather' not in family_names,
            'has_distinctive_typography': has_serif or any(k in family_names for k in ('cereal','feather','sohne','geist')),
            'has_serif_or_strong_geometric_sans': has_serif or weight_max >= 600,
            'has_handwritten_or_quirky': any(k in family_names for k in ('handwritten', 'cursive', 'comic', 'script')),
            'allows_extreme_weight_jump': bool(weights) and (max(weights) - min(weights) >= 300),
            'body_line_height': (typo.get('line_height_rules', {}) or {}).get('body', 1.5),
        },
        'motion': {
            'has_bounce_easing': has_bounce,
            'has_bounce_or_overshoot': has_bounce,
        },
        'design': {
            'has_anti_pattern_intent': False,
            'is_corporate_template': False,
            'has_decorative_polish': False,
            'imagery_role': 'unknown',
            'is_synthetic_aesthetic': False,
            'allows_color_in_content': True,
            'locks_user_to_one_aesthetic': False,
            'has_disciplined_chrome_with_rich_content': False,
            'has_generous_whitespace': False,
            'is_dense_information': False,
            'has_delicate_details': False,
            'has_severe_geometry': False,
            'has_grid_strict_alignment': False,
            'feels_casual_or_playful': False,
            'feels_corporate_serious': False,
            'feels_elite_or_exclusive': False,
            'feels_mysterious_or_inaccessible': False,
            'flat_only': False,
        },
    }


def _get(d: dict, path: str) -> Any:
    cur = d
    for part in path.split('.'):
        if isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            return None
        if cur is None:
            return None
    return cur


def evaluate(rule: dict, signals: dict) -> tuple[bool, str | None]:
    field = rule.get('field')
    op = rule.get('operator')
    value = rule.get('value')
    if field is None or op is None:
        return False, 'rule missing field/operator'
    actual = _get(signals, field)
    if op == 'exists':
        return actual is not None, None
    if op == 'not_exists':
        return actual is None, None
    if actual is None:
        return False, f'field {field} not derived'
    if op == 'lt': return actual < value, None
    if op == 'lte': return actual <= value, None
    if op == 'gt': return actual > value, None
    if op == 'gte': return actual >= value, None
    if op == 'eq': return actual == value, None
    if op == 'neq': return actual != value, None
    if op == 'in': return actual in value, None
    if op == 'not_in': return actual not in value, None
    if op == 'between':
        try:
            lo, hi = value
            return lo <= actual <= hi, None
        except Exception:
            return False, 'between requires [min, max]'
    if op == 'contains_text':
        return isinstance(actual, str) and str(value).lower() in actual.lower(), None
    if op == 'matches_regex':
        return isinstance(actual, str) and bool(re.search(str(value), actual)), None
    return False, f'unknown operator: {op}'


def run(tokens: dict, primary: str, secondary: str | None = None,
        rules_path: str = RULES_PATH) -> dict:
    with open(rules_path) as f:
        archetype_rules = json.load(f)
    if primary not in archetype_rules:
        return {
            'passed': True,
            'evaluable': False,
            'reason': f'primary archetype "{primary}" not in rules',
            'violations': [],
        }
    signals = _derived_signals(tokens)
    violations = []

    def _block(arch_name, block_name, role):
        block = archetype_rules.get(arch_name, {}).get(block_name) or []
        for rule in block:
            holds, diag = evaluate(rule, signals)
            severity = rule.get('severity')
            if block_name == 'never' and holds:
                if severity is None:
                    severity = 'blocker' if role == 'primary' else 'warning'
                violations.append({
                    'archetype': arch_name,
                    'role': role,
                    'block': 'never',
                    'rule': rule.get('rationale', '<no rationale>'),
                    'field': rule.get('field'),
                    'severity': severity,
                    'diagnostic': diag,
                })
            elif block_name == 'always' and not holds:
                violations.append({
                    'archetype': arch_name,
                    'role': role,
                    'block': 'always',
                    'rule': rule.get('rationale', '<no rationale>'),
                    'field': rule.get('field'),
                    'severity': 'warning',
                    'diagnostic': diag,
                })

    _block(primary, 'never', 'primary')
    _block(primary, 'always', 'primary')
    if secondary and secondary in archetype_rules:
        _block(secondary, 'never', 'secondary')

    blockers = [v for v in violations if v['severity'] == 'blocker']
    return {
        'passed': len(blockers) == 0,
        'evaluable': True,
        'primary': primary,
        'secondary': secondary,
        'blocker_count': len(blockers),
        'warning_count': len(violations) - len(blockers),
        'violations': violations,
        'derived_signals_summary': {
            'sat_max': signals['color']['brand']['saturation_max'],
            'sat_avg': signals['color']['brand']['saturation_avg'],
            'palette_temperature': signals['color']['palette_temperature'],
            'L_min': signals['color']['dark_surface']['lightness_min'],
            'has_serif': signals['typography']['has_serif'],
            'weight_max': signals['typography']['weight_ladder_max'],
            'radius_max': signals['radius']['max'],
        },
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('tokens_path')
    p.add_argument('--primary', required=True)
    p.add_argument('--secondary', default=None)
    args = p.parse_args()
    with open(args.tokens_path) as f:
        tokens = json.load(f)
    result = run(tokens, args.primary, args.secondary)
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == '__main__':
    main()
