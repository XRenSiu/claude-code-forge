#!/usr/bin/env python3
"""
color_math.py — Color space conversions, WCAG contrast, hue harmony.

Used by:
  - coherence_check.py (WCAG / OKLch uniformity / hue harmony subchecks)
  - archetype_check.py (saturation/lightness queries on Linear/Vercel-style colors)
  - build_neighbor_corpus.py (encoding colors into feature vectors)

No external dependencies — pure stdlib so the check can run anywhere.
"""
from __future__ import annotations
import math
import re
from typing import Iterable


HEX_RE = re.compile(r'^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$')


def parse_hex(color: str) -> tuple[float, float, float]:
    """Parse a hex string into (r, g, b) in [0, 1]. Drops alpha if present."""
    s = color.strip().lstrip('#')
    if len(s) == 3:
        s = ''.join(c * 2 for c in s)
    if len(s) == 8:
        s = s[:6]   # drop alpha
    if len(s) != 6:
        raise ValueError(f'Invalid hex color: {color!r}')
    r = int(s[0:2], 16) / 255.0
    g = int(s[2:4], 16) / 255.0
    b = int(s[4:6], 16) / 255.0
    return r, g, b


def srgb_to_linear(c: float) -> float:
    """sRGB gamma decoding."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def linear_to_srgb(c: float) -> float:
    return c * 12.92 if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def relative_luminance(rgb: tuple[float, float, float]) -> float:
    """WCAG relative luminance (sRGB → linear → weighted sum)."""
    r, g, b = rgb
    rl = srgb_to_linear(r)
    gl = srgb_to_linear(g)
    bl = srgb_to_linear(b)
    return 0.2126 * rl + 0.7152 * gl + 0.0722 * bl


def wcag_contrast(fg: str, bg: str) -> float:
    """WCAG 2.2 contrast ratio: (L_lighter + 0.05) / (L_darker + 0.05)."""
    l1 = relative_luminance(parse_hex(fg))
    l2 = relative_luminance(parse_hex(bg))
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)


def wcag_passes(fg: str, bg: str, level: str = 'AA', size: str = 'normal') -> bool:
    """level ∈ {AA, AAA}, size ∈ {normal, large, ui}."""
    ratio = wcag_contrast(fg, bg)
    thresholds = {
        ('AA', 'normal'): 4.5,
        ('AA', 'large'): 3.0,
        ('AA', 'ui'): 3.0,        # WCAG 2.2 §1.4.11 non-text
        ('AAA', 'normal'): 7.0,
        ('AAA', 'large'): 4.5,
    }
    return ratio >= thresholds.get((level, size), 4.5)


# ---------- OKLab / OKLch ---------------------------------------------------


def linear_srgb_to_oklab(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    """Convert linear sRGB to OKLab (Björn Ottosson's reference impl)."""
    r, g, b = rgb
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b

    l_ = l ** (1 / 3) if l >= 0 else -((-l) ** (1 / 3))
    m_ = m ** (1 / 3) if m >= 0 else -((-m) ** (1 / 3))
    s_ = s ** (1 / 3) if s >= 0 else -((-s) ** (1 / 3))

    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    b_lab = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return L, a, b_lab


def hex_to_oklch(color: str) -> tuple[float, float, float]:
    """Hex → OKLch (L, C, H). H in degrees [0, 360)."""
    rgb_srgb = parse_hex(color)
    rgb_lin = tuple(srgb_to_linear(c) for c in rgb_srgb)
    L, a, b = linear_srgb_to_oklab(rgb_lin)
    C = math.hypot(a, b)
    H_rad = math.atan2(b, a)
    H_deg = (math.degrees(H_rad) + 360) % 360
    return L, C, H_deg


def oklch_distance(c1: tuple[float, float, float], c2: tuple[float, float, float]) -> float:
    """Perceptual distance in OKLab space (treats H,C as polar coords)."""
    L1, C1, H1 = c1
    L2, C2, H2 = c2
    a1, b1 = C1 * math.cos(math.radians(H1)), C1 * math.sin(math.radians(H1))
    a2, b2 = C2 * math.cos(math.radians(H2)), C2 * math.sin(math.radians(H2))
    return math.sqrt((L1 - L2) ** 2 + (a1 - a2) ** 2 + (b1 - b2) ** 2)


def hue_diff_deg(h1: float, h2: float) -> float:
    """Smallest angular distance on the color wheel, in degrees [0, 180]."""
    d = abs(h1 - h2) % 360
    return min(d, 360 - d)


# ---------- Hue harmony scheme detection ----------------------------------


def detect_harmony_scheme(hexes: Iterable[str], tol: float = 15.0) -> dict:
    """Given a set of distinct hex colors, identify which harmony scheme (if any) fits.

    Returns dict {scheme: <name>, confidence: 0..1, hues: [...]}.
    """
    distinct_hexes = []
    seen = set()
    for h in hexes:
        h_norm = h.lower().lstrip('#')
        if h_norm not in seen:
            seen.add(h_norm)
            distinct_hexes.append(h_norm)

    # Drop near-grayscale (very low chroma) — they don't contribute to scheme
    chromatic = []
    for h in distinct_hexes:
        L, C, H = hex_to_oklch('#' + h)
        if C >= 0.04:   # threshold for "is this chromatic"
            chromatic.append(H)

    if len(chromatic) <= 1:
        return {'scheme': 'achromatic_or_monochromatic', 'confidence': 1.0, 'hues': chromatic}

    # Sort hues
    hues = sorted(chromatic)

    # Check monochromatic — all within ±tol
    spread = max(hue_diff_deg(h, hues[0]) for h in hues)
    if spread <= tol:
        return {'scheme': 'monochromatic', 'confidence': 1.0, 'hues': hues}

    # Check analogous — all within ±30
    if spread <= 30 + tol:
        return {'scheme': 'analogous', 'confidence': 0.9, 'hues': hues}

    # Check complementary — exactly two clusters separated by ~180
    if len(hues) == 2:
        if abs(hue_diff_deg(hues[0], hues[1]) - 180) <= tol:
            return {'scheme': 'complementary', 'confidence': 0.95, 'hues': hues}

    # Check split-complementary — three hues, one anchor + two ~150° away on each side
    if len(hues) == 3:
        # Find which hue could be "the anchor" (the one whose two neighbors are equidistant)
        for anchor_idx, anchor in enumerate(hues):
            others = [h for i, h in enumerate(hues) if i != anchor_idx]
            d1 = hue_diff_deg(anchor, others[0])
            d2 = hue_diff_deg(anchor, others[1])
            if abs(d1 - 150) <= tol and abs(d2 - 150) <= tol:
                return {'scheme': 'split_complementary', 'confidence': 0.85, 'hues': hues}

    # Triadic — three hues separated by ~120
    if len(hues) == 3:
        deltas = sorted([hue_diff_deg(hues[0], hues[1]),
                         hue_diff_deg(hues[1], hues[2]),
                         hue_diff_deg(hues[0], hues[2])])
        if all(abs(d - 120) <= tol for d in deltas):
            return {'scheme': 'triadic', 'confidence': 0.85, 'hues': hues}

    # Tetradic / square — four hues at 90° apart
    if len(hues) == 4:
        deltas_to_first = [hue_diff_deg(h, hues[0]) for h in hues[1:]]
        # Sorted deltas should be roughly [90, 180, 90] (or some rotation)
        if any(abs(d - 90) <= tol for d in deltas_to_first):
            return {'scheme': 'tetradic_or_square', 'confidence': 0.7, 'hues': hues}

    # No scheme matched
    return {'scheme': 'free_combination', 'confidence': 0.0, 'hues': hues}


# ---------- OKLch scale uniformity -------------------------------------------


def neutral_scale_uniformity(neutral_hexes: list[str]) -> dict:
    """Check whether a neutral scale's L (lightness) values are monotone and roughly uniform.

    Returns:
      {monotone: bool, uniformity: 0..1, deltas_L: [...], issues: [...]}
    """
    if len(neutral_hexes) < 2:
        return {'monotone': True, 'uniformity': 1.0, 'deltas_L': [], 'issues': []}
    Ls = [hex_to_oklch(h)[0] for h in neutral_hexes]
    deltas = [Ls[i + 1] - Ls[i] for i in range(len(Ls) - 1)]
    monotone = all(d > 0 for d in deltas) or all(d < 0 for d in deltas)
    abs_deltas = [abs(d) for d in deltas]
    if not abs_deltas:
        return {'monotone': True, 'uniformity': 1.0, 'deltas_L': deltas, 'issues': []}
    mean = sum(abs_deltas) / len(abs_deltas)
    if mean == 0:
        return {'monotone': True, 'uniformity': 0.0, 'deltas_L': deltas,
                'issues': ['neutral_scale has zero L variation']}
    range_dev = (max(abs_deltas) - min(abs_deltas)) / mean
    issues = []
    if not monotone:
        issues.append('neutral_scale L values are not monotone')
    if range_dev > 0.3:
        issues.append(f'neutral_scale L deltas non-uniform (range/mean={range_dev:.2f}, threshold 0.3)')
    return {
        'monotone': monotone,
        'uniformity': max(0.0, 1.0 - range_dev),
        'deltas_L': deltas,
        'issues': issues,
    }


def color_family_consistency(hexes: list[str], tol_H_deg: float = 10) -> dict:
    """Check whether a set of colors forms a coherent family (same H, varying L/C)."""
    if len(hexes) < 2:
        return {'consistent': True, 'H_range': 0.0, 'issues': []}
    Hs = [hex_to_oklch(h)[2] for h in hexes if hex_to_oklch(h)[1] >= 0.04]
    if len(Hs) < 2:
        return {'consistent': True, 'H_range': 0.0, 'issues': []}
    H_range = max(hue_diff_deg(h, Hs[0]) for h in Hs)
    issues = []
    if H_range > tol_H_deg:
        issues.append(f'color family hue spread {H_range:.1f}° exceeds tol {tol_H_deg}°')
    return {
        'consistent': H_range <= tol_H_deg,
        'H_range': H_range,
        'issues': issues,
    }


if __name__ == '__main__':
    # Self-test
    assert abs(wcag_contrast('#000000', '#ffffff') - 21.0) < 0.01
    assert wcag_passes('#000000', '#ffffff', 'AAA', 'normal')
    assert not wcag_passes('#cccccc', '#ffffff', 'AA', 'normal')

    L, C, H = hex_to_oklch('#5e6ad2')
    assert 0.4 < L < 0.6, f'Linear primary L should be ~0.55, got {L:.2f}'
    assert C > 0.1, f'Linear primary should be chromatic, got C={C:.2f}'
    assert 250 < H < 280, f'Linear primary should be in indigo range, got H={H:.0f}'

    scheme = detect_harmony_scheme(['#5e6ad2', '#7170ff', '#828fff'])
    assert scheme['scheme'] in ('monochromatic', 'analogous'), scheme

    print('color_math self-test passed')
