#!/usr/bin/env python3
"""
scale_math.py — Modular scale + grid + vertical rhythm utilities.

Used by:
  - coherence_check.py (modular_scale / vertical_rhythm / grid_consistency subchecks)
  - build_neighbor_corpus.py (scale_ratio feature)
"""
from __future__ import annotations
from statistics import median
from math import isclose


# Well-known modular scale ratios (from Bringhurst's Elements of Typographic Style
# and modularscale.com).
KNOWN_RATIOS = {
    1.067: 'minor_second',
    1.125: 'major_second',
    1.200: 'minor_third',
    1.250: 'major_third',
    1.333: 'perfect_fourth',
    1.414: 'augmented_fourth',
    1.500: 'perfect_fifth',
    1.618: 'golden_ratio',
    1.667: 'minor_sixth',
    1.778: 'major_sixth',
    1.875: 'minor_seventh',
    2.000: 'octave',
}


def infer_scale_ratio(scale: list[float], tol_pct: float = 0.10) -> dict:
    """Given a typographic / spacing scale, infer the modular ratio.

    Returns:
      {
        ratio_median: float,
        ratio_per_step: [...],
        within_tolerance: bool,    # are all step-ratios within ±tol of median?
        nearest_known: ('major_third', 1.25, 0.0024),    # (name, value, abs_diff) or None
        deviation_pct: float,        # max |r - median| / median
      }
    """
    if len(scale) < 2:
        return {
            'ratio_median': 1.0,
            'ratio_per_step': [],
            'within_tolerance': True,
            'nearest_known': None,
            'deviation_pct': 0.0,
        }
    sorted_scale = sorted(scale)
    ratios = [sorted_scale[i + 1] / sorted_scale[i] for i in range(len(sorted_scale) - 1)]
    r_median = median(ratios)

    deviations = [abs(r - r_median) / r_median for r in ratios]
    max_dev = max(deviations)
    within = max_dev <= tol_pct

    # Find nearest known ratio
    nearest = None
    nearest_diff = float('inf')
    for known_r, known_name in KNOWN_RATIOS.items():
        diff = abs(r_median - known_r)
        if diff < nearest_diff:
            nearest_diff = diff
            nearest = (known_name, known_r, diff)

    # Only call it "nearest_known" if within ~3% of median
    if nearest and nearest_diff / r_median > 0.03:
        nearest = None

    return {
        'ratio_median': round(r_median, 4),
        'ratio_per_step': [round(r, 4) for r in ratios],
        'within_tolerance': within,
        'nearest_known': nearest,
        'deviation_pct': round(max_dev, 4),
    }


def grid_alignment_check(values: list[float], base: float, allow_half: bool = True) -> dict:
    """Check whether all values in `values` are integer multiples of `base`.

    If allow_half, then values that are integer multiples of base/2 are also accepted.

    Returns:
      {aligned: bool, off_grid: [(value, nearest_multiple), ...], unit: 'base' | 'half-base'}
    """
    off_grid = []
    half_base_used = False
    for v in values:
        if v == 0:
            continue
        on_full = isclose(v % base, 0, abs_tol=1e-6) or isclose(v % base, base, abs_tol=1e-6)
        if on_full:
            continue
        if allow_half:
            half = base / 2
            on_half = isclose(v % half, 0, abs_tol=1e-6) or isclose(v % half, half, abs_tol=1e-6)
            if on_half:
                half_base_used = True
                continue
        nearest = round(v / base) * base
        off_grid.append((v, nearest))
    return {
        'aligned': len(off_grid) == 0,
        'off_grid': off_grid,
        'unit': 'half-base' if half_base_used else 'base',
        'base': base,
    }


def vertical_rhythm_check(base: float, body_size: float, line_height: float) -> dict:
    """Check whether body line-box (body_size * line_height) is an integer multiple of base.

    e.g. base=4, body_size=16, line_height=1.5 → line_box=24 → 24 % 4 == 0 → OK
    """
    if base == 0:
        return {'rhythm_ok': False, 'line_box': 0, 'remainder': 0,
                'issue': 'base is zero'}
    line_box = body_size * line_height
    remainder = line_box % base
    rhythm_ok = isclose(remainder, 0, abs_tol=0.5) or isclose(remainder, base, abs_tol=0.5)
    return {
        'rhythm_ok': rhythm_ok,
        'line_box': round(line_box, 2),
        'remainder': round(remainder, 2),
        'issue': None if rhythm_ok else f'line_box={line_box:.1f} not divisible by base={base}',
    }


def radius_proportion_check(radius_scale: list[float]) -> dict:
    """Check whether a radius scale follows reasonable proportions (e.g., 1:2 / 1:2:4 / 1:2:3).

    Permissive — accepts any monotone-increasing scale where each step's ratio is in [1.3, 2.5].
    """
    if len(radius_scale) < 2:
        return {'reasonable': True, 'issues': []}
    sorted_r = sorted(radius_scale)
    issues = []
    if sorted_r[0] != radius_scale[0] or sorted_r != radius_scale:
        issues.append('radius_scale is not monotone-increasing')
    ratios = [sorted_r[i + 1] / sorted_r[i] for i in range(len(sorted_r) - 1) if sorted_r[i] > 0]
    out_of_range = [r for r in ratios if r < 1.3 or r > 2.5]
    if out_of_range:
        issues.append(f'radius step ratios out of [1.3, 2.5]: {[round(r, 2) for r in out_of_range]}')
    return {
        'reasonable': len(issues) == 0,
        'ratios': [round(r, 2) for r in ratios],
        'issues': issues,
    }


if __name__ == '__main__':
    # Self-test
    inf = infer_scale_ratio([12, 14, 16, 18, 24, 32, 48])
    # That scale's ratios are roughly 1.17, 1.14, 1.13, 1.33, 1.33, 1.5 — pretty inconsistent
    assert not inf['within_tolerance']

    inf2 = infer_scale_ratio([16, 20, 25, 31.25, 39.06])  # major_third 1.25
    assert inf2['within_tolerance']
    assert inf2['nearest_known'] == ('major_third', 1.25, 0.0)

    g = grid_alignment_check([4, 8, 12, 16, 24, 32], base=4)
    assert g['aligned']
    g2 = grid_alignment_check([4, 8, 11, 16], base=4, allow_half=True)
    # 11 is not an integer multiple of 4 OR 2 → fails
    assert not g2['aligned']
    g3 = grid_alignment_check([4, 8, 10, 16], base=4, allow_half=True)
    # 10 = 5 * 2 → multiple of base/2=2 → ok
    assert g3['aligned']

    vr = vertical_rhythm_check(base=4, body_size=16, line_height=1.5)
    assert vr['rhythm_ok']

    rp = radius_proportion_check([2, 4, 8, 16])
    assert rp['reasonable']

    print('scale_math self-test passed')
