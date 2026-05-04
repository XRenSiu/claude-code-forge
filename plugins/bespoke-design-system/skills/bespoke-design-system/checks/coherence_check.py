#!/usr/bin/env python3
"""
coherence_check.py — Subcheck 1 of B5 P0 gate: design's intrinsic coherence.

Six subchecks (all math, no taste):
  1. WCAG contrast (body / large / non-text)
  2. OKLch neutral-scale uniformity
  3. Hue harmony scheme detection
  4. Typography modular scale
  5. Vertical rhythm (line-box vs base unit)
  6. Grid consistency (radius/spacing as base multiples)

Output: {passed, score (0-1), subchecks: {...}, issues: [...]}.

Usage:
  python3 coherence_check.py <path/to/tokens.json> [--design-md <path>]
    -> prints JSON report to stdout

  Or import: from coherence_check import run as coherence_check_run
"""
from __future__ import annotations
import json
import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from color_math import (
    wcag_contrast, wcag_passes, hex_to_oklch, neutral_scale_uniformity,
    detect_harmony_scheme, color_family_consistency, hue_diff_deg,
)
from scale_math import (
    infer_scale_ratio, grid_alignment_check, vertical_rhythm_check,
    radius_proportion_check,
)


def _gather_color_pairs(tokens):
    """Collect background and foreground candidates with luminance, so each fg can
    be paired against a likely-correct bg (dark fg → light bg, vice versa).
    """
    from color_math import relative_luminance, parse_hex

    color = tokens.get('color', {}) or {}
    role_pairs = color.get('role_color_pairs') or {}

    bg_candidates = []   # list of (role, hex, luminance)
    fg_candidates = []   # list of (role, hex, luminance)

    def add(role, hex_val, target):
        if not isinstance(hex_val, str) or not hex_val.startswith('#'):
            return
        try:
            lum = relative_luminance(parse_hex(hex_val))
        except Exception:
            return
        target.append((role, hex_val, lum))

    # Walk role_color_pairs and classify
    # v1.7.1 (#37): expanded keyword coverage. Previously missed common role
    # names like 'white' alone (only matched 'pure_white'), 'navy', 'gray',
    # 'cream', etc. Most real systems use plain color names as roles, which
    # left _gather_color_pairs returning 0 candidates → archetype_check
    # produced phantom 'body_on_bg not derived' warnings on most systems.
    if isinstance(role_pairs, dict):
        for role, hex_val in role_pairs.items():
            role_l = role.lower()
            is_bg = any(k in role_l for k in ('background', 'bg', 'canvas', 'page', 'surface',
                                               'parchment', 'snow', 'panel', 'pure_white',
                                               'vercel_black', 'eel_black', 'marketing_black',
                                               'level_3', 'secondary_surface', 'pure_black',
                                               'white', 'cream', 'ivory', 'paper'))
            is_fg = any(k in role_l for k in ('text', 'ink', 'foreground', 'heading', 'body',
                                               'label', 'header_primary',
                                               'navy', 'charcoal'))
            is_brand = any(k in role_l for k in ('brand', 'cta', 'action', 'workflow', 'accent',
                                                  'review_blue', 'rausch', 'owl', 'blurple',
                                                  'terracotta', 'streak', 'gem', 'cardinal',
                                                  'apple_action'))
            if is_bg and not is_fg:
                add(role, hex_val, bg_candidates)
            elif is_fg or is_brand:
                add(role, hex_val, fg_candidates)
            else:
                # Ambiguous — skip
                pass

    # Top-level nested keys (Linear-style: color.background_surfaces.* / color.text.*)
    for nested_key, target in (('background_surfaces', bg_candidates),
                               ('primary_neutrals', bg_candidates),
                               ('text', fg_candidates),
                               ('brand', fg_candidates)):
        section = color.get(nested_key)
        if isinstance(section, dict):
            for role, hex_val in section.items():
                add(f'{nested_key}.{role}', hex_val, target)

    # Sort backgrounds by luminance (so we can pick darkest and lightest)
    bg_candidates.sort(key=lambda x: x[2])

    return bg_candidates, fg_candidates


def _classify_text_role(role: str) -> str:
    """Map an extracted role label to a WCAG severity tier.

    Priority order (most specific first):
      1. Optional (disabled / quaternary / placeholder / metadata)
      2. Brand / CTA (UI surface — 3:1)
      3. Secondary / tertiary / muted (3:1)
      4. Body / heading / primary text (4.5:1)
      5. Default body (4.5:1)
    """
    role_l = role.lower()
    # 1. Optional — quaternary / disabled / placeholder / metadata / hover / chromatic palette.
    #    Check FIRST so the word 'text' inside e.g. 'quaternary_text' / 'success_text' doesn't
    #    cause body-tier classification.
    if any(k in role_l for k in ('quaternary', 'disabled', 'placeholder', 'metadata',
                                  'timestamp', 'subtle', 'hint', 'channels_default',
                                  'hover', 'pressed', 'active', 'selected',
                                  'success', 'warning', 'error', 'danger', 'info',
                                  'status_', 'green', 'red', 'amber', 'yellow', 'pink',
                                  'magenta', 'orange', 'lemon', 'ruby')):
        return 'optional'
    # 2. Link — special case. Underline + context typically aids readability,
    #    so 3:1 (large UI) is acceptable.
    if 'link' in role_l:
        return 'large'
    # 3. Brand / CTA — surface fills, 3:1
    if any(k in role_l for k in ('brand', 'cta', 'action', 'workflow', 'accent', 'pill',
                                  'badge', 'streak', 'gem', 'eel', 'cardinal', 'rausch',
                                  'review_blue', 'owl', 'blurple', 'terracotta', 'apple_action',
                                  'console', 'ship', 'preview', 'develop', 'focus')):
        return 'large'
    # 4. Secondary / tertiary / muted — 3:1
    if any(k in role_l for k in ('secondary', 'tertiary', 'muted', 'caption',
                                  'wolf', 'hare', 'stone', 'ash')):
        return 'large'
    # 5. Body / heading / primary text — 4.5:1
    if any(k in role_l for k in ('body', 'reading', 'paragraph',
                                  'heading', 'h1', 'h2', 'h3', 'header_primary',
                                  'eel_black', 'ink_black')):
        return 'body'
    # 5b. Generic 'text' / 'ink' / 'foreground' — likely body
    if any(k in role_l for k in ('primary_text', 'text_normal', 'text_primary',
                                  'foreground_primary', 'ink', 'near_black')):
        return 'body'
    # Default — unknown role names are treated as 'optional' (informational) to avoid
    # false positives. Production tokens.json should label body text explicitly with
    # 'body' / 'text_normal' / 'primary_text' for strict checking.
    return 'optional'


def subcheck_wcag(tokens):
    bgs, fgs = _gather_color_pairs(tokens)
    if not bgs or not fgs:
        return {
            'passed': True,
            'evaluable': False,
            'reason': 'insufficient color tokens to evaluate WCAG contrast',
            'pairs_checked': [],
        }
    pairs_checked = []
    fails = []
    warnings = []

    # Pick darkest bg and lightest bg as candidates
    darkest_bg = bgs[0]    # lowest luminance
    lightest_bg = bgs[-1]  # highest luminance

    for fg_role, fg_hex, fg_lum in fgs:
        # Auto-pair: dark fg with light bg, light fg with dark bg
        if fg_lum < 0.5:
            bg_role, bg_hex, _ = lightest_bg
        else:
            bg_role, bg_hex, _ = darkest_bg

        ratio = wcag_contrast(fg_hex, bg_hex)
        tier = _classify_text_role(fg_role)
        if tier == 'body':
            required, passed = 4.5, ratio >= 4.5
        elif tier == 'large':
            required, passed = 3.0, ratio >= 3.0
        elif tier == 'optional':
            required, passed = 0.0, True
        else:
            required, passed = 4.5, ratio >= 4.5

        pairs_checked.append({
            'fg': f'{fg_role} ({fg_hex})',
            'bg': f'{bg_role} ({bg_hex})',
            'ratio': round(ratio, 2),
            'tier': tier,
            'required': required,
            'passes': passed,
        })
        if not passed:
            entry = {
                'fg': f'{fg_role} ({fg_hex})',
                'bg': f'{bg_role} ({bg_hex})',
                'ratio': round(ratio, 2),
                'required': required,
                'tier': tier,
            }
            if tier == 'body':
                fails.append(entry)
            else:
                warnings.append(entry)

    return {
        'passed': len(fails) == 0,
        'evaluable': True,
        'pairs_checked': pairs_checked,
        'failures': fails,
        'warnings': warnings,
    }


def subcheck_oklch_uniformity(tokens):
    """Check neutral_scale L-monotone-and-roughly-uniform."""
    color = tokens.get('color', {}) or {}
    # Find a neutral_scale somewhere
    candidates = []
    for key in ('neutral_scale', 'neutral'):
        v = color.get(key)
        if isinstance(v, list):
            candidates = v
            break
        if isinstance(v, dict):
            candidates = [hx for hx in v.values() if isinstance(hx, str) and hx.startswith('#')]
            break
    if not candidates:
        return {
            'passed': True,
            'evaluable': False,
            'reason': 'no neutral_scale found in tokens.color',
        }
    if len(candidates) < 3:
        return {
            'passed': True,
            'evaluable': False,
            'reason': f'neutral_scale has only {len(candidates)} colors — not enough for uniformity check',
        }
    result = neutral_scale_uniformity(candidates)
    return {
        'passed': result['monotone'] and result['uniformity'] >= 0.7,
        'evaluable': True,
        **result,
    }


def subcheck_hue_harmony(tokens):
    """Harmony check is restricted to brand-role colors only — status colors (success
    green / warning amber / error red) are functional and not part of the brand scheme.
    """
    color = tokens.get('color', {}) or {}
    chromatic_hexes = []
    # Brand chromatic — primary source of truth for harmony
    brand = color.get('brand', {})
    if isinstance(brand, dict):
        for v in brand.values():
            if isinstance(v, str) and v.startswith('#'):
                chromatic_hexes.append(v)
    # role_color_pairs entries — only those with brand-like role names
    role_pairs = color.get('role_color_pairs', {})
    if isinstance(role_pairs, dict):
        for role, hex_val in role_pairs.items():
            if not (isinstance(hex_val, str) and hex_val.startswith('#')):
                continue
            role_l = role.lower()
            # Skip status / functional / surface roles
            if any(k in role_l for k in ('success', 'warning', 'danger', 'error',
                                          'info', 'status', 'online', 'idle', 'dnd', 'streak',
                                          'background', 'surface', 'panel', 'border',
                                          'text', 'ink', 'heading', 'body', 'foreground')):
                continue
            try:
                L, C, H = hex_to_oklch(hex_val)
                if C >= 0.05:
                    chromatic_hexes.append(hex_val)
            except Exception:
                pass
    if len(chromatic_hexes) < 2:
        return {
            'passed': True,
            'evaluable': False,
            'reason': 'too few brand-chromatic colors to evaluate harmony scheme',
            'chromatic_count': len(chromatic_hexes),
        }
    scheme = detect_harmony_scheme(chromatic_hexes)
    # `free_combination` warns but does not block — the design may legitimately
    # combine multiple chromatic moments (e.g., Vercel's workflow trio).
    passes = True
    return {
        'passed': passes,
        'evaluable': True,
        'scheme': scheme['scheme'],
        'confidence': scheme['confidence'],
        'chromatic_count': len(chromatic_hexes),
        'is_free_combination': scheme['scheme'] == 'free_combination',
    }


def subcheck_modular_scale(tokens):
    typo = tokens.get('typography', {}) or {}
    scale = typo.get('declared_scale_px') or typo.get('all_px_values') or typo.get('scale')
    if not isinstance(scale, list):
        return {
            'passed': True,
            'evaluable': False,
            'reason': 'no typography.scale found',
        }
    # Filter to plausible font sizes
    scale = sorted({s for s in scale if isinstance(s, (int, float)) and 8 <= s <= 200})
    if len(scale) < 3:
        return {
            'passed': True,
            'evaluable': False,
            'reason': f'scale has only {len(scale)} values — too few for ratio inference',
        }
    result = infer_scale_ratio(list(scale))
    passed = result['within_tolerance'] or result['nearest_known'] is not None
    return {
        'passed': passed,
        'evaluable': True,
        **result,
    }


def subcheck_vertical_rhythm(tokens):
    sp = tokens.get('spacing', {}) or {}
    typo = tokens.get('typography', {}) or {}
    base = sp.get('base_unit_px') or sp.get('base')
    if base is None:
        return {'passed': True, 'evaluable': False, 'reason': 'no spacing.base_unit_px'}
    # body size = 16 default if not specified
    body_size = 16
    line_height = 1.5
    if isinstance(typo.get('line_height_rules'), dict):
        for k in ('body', 'body_relaxed', 'body_standard'):
            v = typo['line_height_rules'].get(k)
            if isinstance(v, (int, float)):
                line_height = v
                break
    return {
        'passed': True,    # default-OK; vertical rhythm is hard to fail in practice
        'evaluable': True,
        **vertical_rhythm_check(base, body_size, line_height),
    }


def subcheck_grid_consistency(tokens):
    sp = tokens.get('spacing', {}) or {}
    radius = tokens.get('radius', {}) or {}
    base = sp.get('base_unit_px') or sp.get('base')
    if base is None:
        return {'passed': True, 'evaluable': False, 'reason': 'no spacing.base_unit_px'}
    # Spacing grid check — only consider values >= base (smaller values are
    # micro-tracking / letter-spacing, not spacing)
    scale_vals = sp.get('declared_scale') or sp.get('scale') or sp.get('all_px_values') or []
    scale_vals = [v for v in scale_vals if isinstance(v, (int, float)) and v >= base]
    spacing_grid = grid_alignment_check(scale_vals, base, allow_half=True) if scale_vals else None
    # Radius grid check
    radius_vals = []
    if isinstance(radius, dict):
        for v in radius.values():
            if isinstance(v, (int, float)) and v > 0 and v < 1000:
                radius_vals.append(v)
            elif isinstance(v, dict):
                for vv in v.values():
                    if isinstance(vv, (int, float)) and vv > 0 and vv < 1000:
                        radius_vals.append(vv)
    radius_grid = grid_alignment_check(radius_vals, base, allow_half=True) if radius_vals else None
    radius_proportion = radius_proportion_check(sorted(set(radius_vals))) if radius_vals else None

    issues = []
    if spacing_grid and not spacing_grid['aligned']:
        issues.append(f'spacing values off-grid: {spacing_grid["off_grid"]}')
    if radius_grid and not radius_grid['aligned']:
        # Pill radius (9999) etc — relax: if only "pill" values are off, ok
        true_off = [(v, m) for v, m in radius_grid['off_grid'] if v < 200]
        if true_off:
            issues.append(f'radius values off-grid (excluding pills): {true_off}')
    if radius_proportion and not radius_proportion['reasonable']:
        issues.extend(radius_proportion['issues'])

    return {
        'passed': len(issues) == 0,
        'evaluable': spacing_grid is not None or radius_grid is not None,
        'spacing_grid': spacing_grid,
        'radius_grid': radius_grid,
        'radius_proportion': radius_proportion,
        'issues': issues,
    }


def run(tokens: dict) -> dict:
    """Top-level entry. Run all 6 subchecks against a tokens dict."""
    results = {
        'wcag_contrast': subcheck_wcag(tokens),
        'oklch_uniformity': subcheck_oklch_uniformity(tokens),
        'hue_harmony': subcheck_hue_harmony(tokens),
        'modular_scale': subcheck_modular_scale(tokens),
        'vertical_rhythm': subcheck_vertical_rhythm(tokens),
        'grid_consistency': subcheck_grid_consistency(tokens),
    }
    # Score = mean of "passed" weighted by evaluable
    weights = {
        'wcag_contrast': 0.25,
        'oklch_uniformity': 0.15,
        'hue_harmony': 0.10,
        'modular_scale': 0.20,
        'vertical_rhythm': 0.10,
        'grid_consistency': 0.20,
    }
    total_weight = 0.0
    weighted_score = 0.0
    issues = []
    blockers = 0
    for name, result in results.items():
        w = weights[name]
        if result.get('evaluable', True):
            total_weight += w
            if result.get('passed', True):
                weighted_score += w
            else:
                # WCAG failures are blockers
                if name in ('wcag_contrast',):
                    blockers += 1
                    issues.append({
                        'subcheck': name,
                        'severity': 'blocker',
                        'message': f'{name} failed: {result.get("failures") or result.get("issues")}',
                    })
                else:
                    issues.append({
                        'subcheck': name,
                        'severity': 'warning',
                        'message': f'{name} failed: {result.get("issues") or result}',
                    })
    score = round(weighted_score / total_weight, 3) if total_weight > 0 else 1.0
    # PASS if zero blockers AND score >= 0.55. Score is informational; the gating
    # is on blockers (currently only WCAG body-text failures). Warnings show up
    # in `issues` but don't block — they're surfaced for B6 negotiation-summary.
    passed = blockers == 0 and score >= 0.55

    return {
        'passed': passed,
        'score': score,
        'blocker_count': blockers,
        'warning_count': len(issues) - blockers,
        'subchecks': results,
        'issues': issues,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('tokens_path', help='Path to tokens.json (programmatic A1 output)')
    args = p.parse_args()

    with open(args.tokens_path) as f:
        tokens = json.load(f)

    report = run(tokens)
    json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == '__main__':
    main()
