#!/usr/bin/env python3
"""
build_neighbor_corpus.py — A5 phase: encode every system's tokens.json into a
fixed-length feature vector for nearest-neighbor distance lookup.

Vector schema (44 dimensions = 37 base + 7 v1.13.0 discriminative):
  Color (12 dims):
    [0]  primary_brand_L
    [1]  primary_brand_C
    [2]  primary_brand_H_sin       (sin/cos pair to handle hue circularity)
    [3]  primary_brand_H_cos
    [4]  neutral_L_min
    [5]  neutral_L_max
    [6]  palette_avg_saturation
    [7]  palette_hue_entropy        (Shannon entropy of hue distribution / log2(8))
    [8]  body_contrast_ratio        (or 0 if unknown), normalized to /21
    [9]  is_dark_canvas             (1 if neutral L_min < 0.15 else 0)
    [10] chromatic_count_norm       (min(N, 10) / 10)
    [11] palette_temp_score         (cool=-1, neutral=0, warm=+1, mixed=0)
  Typography (8 dims):
    [12] scale_ratio_inferred
    [13] scale_size_count_norm      (min(N, 12) / 12)
    [14] body_size_norm             (px / 20)
    [15] display_size_max_norm      (px / 100)
    [16] line_height_body
    [17] weight_max_norm            (max_weight / 900)
    [18] has_serif                  (0 or 1)
    [19] is_humanist_sans           (0 or 1)
  Spacing / Layout (5 dims):
    [20] base_norm                  (base / 8)
    [21] scale_length_norm          (min(N, 14) / 14)
    [22] scale_max_norm             (max / 100)
    [23] section_padding_min_norm   (min / 100, default 64)
    [24] no_explicit_dividers       (0 or 1; defaults 0 for unknown)
  Radius (4 dims):
    [25] radius_count_norm          (min(N, 8) / 8)
    [26] radius_max_norm            (max / 50)  — clamped, ignoring pill 9999
    [27] radius_pill_used           (1 if 9999 found else 0)
    [28] radius_max_step_ratio_norm (max(step_ratio, 1.0) - 1, clamped at 1.5)
  Motion (3 dims):
    [29] duration_count_norm        (min(N, 6) / 6)
    [30] duration_avg_norm          (avg / 500)
    [31] has_bounce                 (0 or 1)
  Components (5 dims):
    [32] button_radius_norm         (button_radius / 24)
    [33] num_button_variants_norm   (min(N, 6) / 6)
    [34] uses_shadow_as_border      (0 or 1, heuristic)
    [35] has_rgba_translucent_bg    (0 or 1, heuristic for ghost-button style)
    [36] has_status_palette         (0 or 1)
  v1.13.0 discriminative (7 dims) — skill-issue-2026-06-18 #2 (corpus degeneracy):
    [37] palette_mean_L             (lightness center of the palette)
    [38] L_contrast_range           (neutral_L_max - neutral_L_min)
    [39] chroma_spread              ((max_C - mean_C) / 0.4 — one punchy accent vs many)
    [40] neutral_avg_chroma         (warm vs cool neutrals; avg C of near-neutrals / 0.06)
    [41] has_mono                   (1 if a mono typeface present — dev signal)
    [42] num_font_families_norm     (min(distinct non-mono families, 4) / 4)
    [43] weight_spread_norm         ((max_weight - min_weight) / 900 — narrow vs wide ladder)

Output: grammar/meta/neighbor-corpus.json:
  {
    "schema_version": "1.0",
    "dim_count": 44,
    "dim_names": [...],
    "weights": [...],     // optional per-dim weight for distance calc
    "systems": {
      "<name>": {
        "vector": [...],
        "dialect": "A|B|...",
        "rule_count": N,
        "extracted_at": ...
      },
      ...
    }
  }

Usage:
  python3 tools/build_neighbor_corpus.py
"""
from __future__ import annotations
import os
import sys
import json
import math
import argparse
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SHARED = os.path.normpath(os.path.join(HERE, '..', 'checks', '_shared'))
sys.path.insert(0, SHARED)
from color_math import hex_to_oklch, parse_hex, relative_luminance


DIM_NAMES = [
    'primary_brand_L', 'primary_brand_C', 'primary_brand_H_sin', 'primary_brand_H_cos',
    'neutral_L_min', 'neutral_L_max', 'palette_avg_saturation', 'palette_hue_entropy',
    'body_contrast_ratio_norm', 'is_dark_canvas', 'chromatic_count_norm', 'palette_temp_score',
    'scale_ratio_inferred', 'scale_size_count_norm', 'body_size_norm', 'display_size_max_norm',
    'line_height_body', 'weight_max_norm', 'has_serif', 'is_humanist_sans',
    'base_norm', 'spacing_scale_length_norm', 'spacing_scale_max_norm',
    'section_padding_min_norm', 'no_explicit_dividers',
    'radius_count_norm', 'radius_max_norm', 'radius_pill_used', 'radius_max_step_ratio_norm',
    'duration_count_norm', 'duration_avg_norm', 'has_bounce',
    'button_radius_norm', 'num_button_variants_norm', 'uses_shadow_as_border',
    'has_rgba_translucent_bg', 'has_status_palette',
    # v1.13.0 — discriminative dims (skill-issue-2026-06-18 #2: corpus degeneracy).
    # The 37-dim encoder collapsed ~50 systems to <0.08 of a neighbor; several
    # "adjective" stub systems share an identical Tailwind-default palette and
    # differ ONLY in fonts (which the old encoder barely saw). These add the
    # font-family + finer-color signal that breaks those ties and separates real
    # systems better.
    'palette_mean_L', 'L_contrast_range', 'chroma_spread', 'neutral_avg_chroma',
    'has_mono', 'num_font_families_norm', 'weight_spread_norm',
]

# Per-dimension weight for distance calculation. Color and typography are most
# distinctive; motion/components less so.
DIM_WEIGHTS = [
    1.5, 1.5, 1.5, 1.5,          # primary brand color (high)
    1.0, 1.0,                    # neutral range
    0.8, 0.8,                    # palette properties
    0.5, 1.5,                    # contrast (low) + dark canvas (high)
    0.7, 0.7,                    # chromatic count + temp
    1.2, 0.6, 0.6, 0.6,          # typography scale
    0.5, 1.0, 1.5, 1.0,          # line-height + weight + serif/humanist
    0.6, 0.6, 0.4,               # spacing
    0.4, 0.3,                    # padding + dividers
    0.5, 0.6, 0.4, 0.3,          # radius
    0.3, 0.3, 0.6,               # motion
    0.5, 0.4, 0.4, 0.4, 0.5,     # components
    # v1.13.0 discriminative dims: color refinement (mean_L/contrast/spread/neutral
    # temp) + font signal (mono / family count / weight ladder spread). Font dims
    # weighted relatively high — they carry identity the palette alone misses.
    1.0, 0.9, 0.8, 0.6,          # palette_mean_L, L_contrast_range, chroma_spread, neutral_avg_chroma
    1.0, 0.7, 0.7,               # has_mono, num_font_families_norm, weight_spread_norm
]
assert len(DIM_NAMES) == len(DIM_WEIGHTS), 'DIM_NAMES/DIM_WEIGHTS length mismatch'


# v1.10.0 — "unknown" convention for honest distance.
#
# Bug (skill-issue-2026-06-13 #1 + #2): encode() used to FABRICATE a default
# value (0 / 1.5 / 0.333) for dimensions whose source data was simply absent.
# Across the A1-extracted corpus this made 9 dimensions constant (std=0) —
# body_contrast / line_height / section_padding / no_explicit_dividers /
# button_radius / num_button_variants / uses_shadow_as_border /
# has_rgba_translucent_bg / has_status_palette — plus a mostly-noise has_serif
# (brand-named fonts are never substring-detected). A new, fully-B4 design that
# HONESTLY populates those fields was then penalised for differing from a
# fabricated constant, structurally biasing the neighbor gate against
# B4-complete and serif designs.
#
# Fix: when the source data for a dimension is genuinely absent, encode() emits
# `None` (UNKNOWN) instead of a fabricated default. weighted_euclidean() skips
# any dimension that is None on either side and normalises by the FULL weight
# sum — so corpus-internal distances are unchanged (the formerly-constant dims
# contributed 0 to corpus pairs and now skip to 0), while a new design no longer
# accrues spurious distance on dimensions the corpus never recorded.
UNKNOWN = None


KNOWN_SERIF_TOKENS = (
    'serif', 'georgia', 'cormorant', 'didone', 'tiempos', 'lyon', 'garamond',
    'times', 'freight', 'canela', 'recoleta', 'domine', 'lora', 'playfair',
    'signifier', 'reckless', 'jannon', 'sectra', 'spectral', 'noto serif',
    'source serif', 'ibm plex serif', 'pt serif', 'merriweather', 'newsreader',
)
KNOWN_SANS_TOKENS = (
    'inter', 'sf pro', 'system-ui', 'feather', 'gg sans', 'cereal', 'helvetica',
    'sohne', 'söhne', 'suisse', 'roboto', 'open sans', 'segoe', 'geist', 'arial',
    'circular', 'graphik', 'aktiv', 'neue', 'grotesk', 'grotesque',
)
KNOWN_HUMANIST_TOKENS = (
    'inter', 'sf pro', 'system-ui', 'feather', 'gg sans', 'cereal', 'roboto',
    'open sans', 'segoe',
)


def _detect_serif_humanist(typo):
    """Return (has_serif, is_humanist_sans), each in {1.0, 0.0, None}.

    None means "undeterminable from the tokens" (e.g. brand-named fonts with no
    `category`/`class` metadata) — NOT "absent / false". Prefers explicit
    `families[].category` and `display/body.class` signals, then a known-typeface
    token match, and only returns a concrete 0.0 when every family is positively
    classifiable as non-serif.
    """
    families = typo.get('families') or []
    cats, names = [], []
    for f in families:
        if isinstance(f, dict):
            c = (f.get('category') or '').lower()
            if c:
                cats.append(c)
            names.append(str(f.get('family', '')).lower())
        else:
            names.append(str(f).lower())
    for role in ('display', 'body', 'mono'):
        blk = typo.get(role)
        if isinstance(blk, dict):
            c = (blk.get('class') or blk.get('category') or '').lower()
            if c:
                cats.append(c)
            names.append(str(blk.get('family', '')).lower())
    joined_cats = ' '.join(cats)
    joined_names = ' '.join(names)

    # serif evidence: a category token containing 'serif' but not 'sans-serif',
    # or a known serif typeface name.
    cat_says_serif = any(('serif' in c and 'sans' not in c) for c in cats)
    name_says_serif = any(tok in joined_names for tok in KNOWN_SERIF_TOKENS)
    # non-serif evidence per family: category sans/grotesque/geometric/mono, or
    # a known sans/mono typeface name.
    def _fam_is_nonserif(cat, name):
        if cat and any(k in cat for k in ('sans', 'grotesque', 'geometric', 'mono', 'humanist')):
            return True
        if any(tok in name for tok in KNOWN_SANS_TOKENS) or 'mono' in name:
            return True
        return False

    if cat_says_serif or name_says_serif:
        has_serif = 1.0
    else:
        # need EVERY family positively classifiable as non-serif to claim 0.0;
        # any unclassifiable brand font → unknown.
        fam_pairs = []
        for f in families:
            if isinstance(f, dict):
                fam_pairs.append(((f.get('category') or '').lower(), str(f.get('family', '')).lower()))
        for role in ('display', 'body', 'mono'):
            blk = typo.get(role)
            if isinstance(blk, dict):
                fam_pairs.append(((blk.get('class') or blk.get('category') or '').lower(),
                                  str(blk.get('family', '')).lower()))
        if fam_pairs and all(_fam_is_nonserif(c, n) for c, n in fam_pairs):
            has_serif = 0.0
        else:
            has_serif = UNKNOWN

    if has_serif == 1.0:
        is_humanist = 0.0
    elif any(tok in joined_names for tok in KNOWN_HUMANIST_TOKENS) or 'humanist' in joined_cats:
        is_humanist = 1.0
    elif has_serif == 0.0:
        is_humanist = 0.0
    else:
        is_humanist = UNKNOWN
    return has_serif, is_humanist


def _safe_max(seq, default=0):
    seq = [x for x in seq if isinstance(x, (int, float))]
    return max(seq) if seq else default


def _safe_min(seq, default=0):
    seq = [x for x in seq if isinstance(x, (int, float))]
    return min(seq) if seq else default


def _safe_avg(seq, default=0):
    seq = [x for x in seq if isinstance(x, (int, float))]
    return sum(seq) / len(seq) if seq else default


def encode(tokens: dict) -> list[float]:
    """Encode a tokens.json dict into a 44-dim vector (37 base + 7 v1.13.0)."""
    color = tokens.get('color', {}) or {}
    typo = tokens.get('typography', {}) or {}
    sp = tokens.get('spacing', {}) or {}
    radius = tokens.get('radius', {}) or {}
    motion = tokens.get('motion', {}) or {}
    components = tokens.get('components', {}) or {}

    # ---------- Color ----------
    all_hexes = color.get('all_hex_colors') or []
    chromatic = []
    L_values = []
    for hx in all_hexes:
        try:
            L, C, H = hex_to_oklch(hx)
            L_values.append(L)
            if C >= 0.06:
                chromatic.append((L, C, H))
        except Exception:
            continue

    # Find primary brand color (highest C)
    if chromatic:
        primary = max(chromatic, key=lambda x: x[1])
        pL, pC, pH = primary
    else:
        pL, pC, pH = 0.5, 0.0, 0.0

    pH_rad = math.radians(pH)
    primary_brand_L = pL
    primary_brand_C = min(pC / 0.4, 1.0)   # normalize to /0.4 typical max
    primary_brand_H_sin = math.sin(pH_rad)
    primary_brand_H_cos = math.cos(pH_rad)

    neutral_L_min = min(L_values, default=0.5)
    neutral_L_max = max(L_values, default=0.5)
    palette_avg_saturation = _safe_avg([c[1] for c in chromatic], 0.0)
    palette_avg_saturation_norm = min(palette_avg_saturation / 0.4, 1.0)

    # Hue entropy: bin into 8 octants
    if chromatic:
        bins = [0] * 8
        for _, _, H in chromatic:
            bins[int((H % 360) / 45)] += 1
        total = sum(bins)
        probs = [b / total for b in bins if b > 0]
        entropy = -sum(p * math.log2(p) for p in probs) / 3.0   # normalize by log2(8) = 3
    else:
        entropy = 0.0

    body_contrast = (color.get('contrast', {}) or {}).get('body_on_bg')
    body_contrast_norm = (body_contrast / 21) if isinstance(body_contrast, (int, float)) else UNKNOWN

    is_dark_canvas = 1.0 if neutral_L_min < 0.15 else 0.0
    chromatic_count_norm = min(len(chromatic), 10) / 10

    # Palette temperature
    if chromatic:
        warm_count = sum(1 for _, _, H in chromatic if 0 <= H <= 60 or 300 <= H < 360)
        cool_count = sum(1 for _, _, H in chromatic if 180 <= H <= 270)
        if warm_count > cool_count + 1:
            palette_temp_score = 1.0
        elif cool_count > warm_count + 1:
            palette_temp_score = -1.0
        else:
            palette_temp_score = 0.0
    else:
        palette_temp_score = 0.0

    # ---------- Typography ----------
    scale_px = typo.get('declared_scale_px') or typo.get('all_px_values') or []
    scale_px = sorted({s for s in scale_px if isinstance(s, (int, float)) and 8 <= s <= 200})
    if len(scale_px) >= 2:
        ratios = [scale_px[i+1] / scale_px[i] for i in range(len(scale_px) - 1)]
        ratios.sort()
        scale_ratio = ratios[len(ratios) // 2]
    else:
        scale_ratio = 1.0
    scale_size_count_norm = min(len(scale_px), 12) / 12

    body_size = next((s for s in scale_px if 14 <= s <= 18), 16)
    display_size_max = max(scale_px, default=16)
    body_size_norm = body_size / 20
    display_size_max_norm = min(display_size_max / 100, 1.0)

    lh_rules = typo.get('line_height_rules') or {}
    line_height_body = (lh_rules.get('body') or lh_rules.get('body_relaxed')
                         or lh_rules.get('body_standard'))
    if not isinstance(line_height_body, (int, float)):
        line_height_body = UNKNOWN   # absent → unknown, not a fabricated 1.5

    weights = typo.get('weights_seen') or []
    weight_max_norm = (max(weights) / 900) if weights else UNKNOWN

    # v1.10.0: serif/humanist via explicit category/class signals, else UNKNOWN
    # (brand-named fonts with no metadata are NOT assumed sans — that was the
    # has_serif structural bias bug).
    has_serif, is_humanist_sans = _detect_serif_humanist(typo)

    # ---------- Spacing ----------
    base = sp.get('base_unit_px') or 8
    base_norm = min((base or 8) / 8, 2.0)
    spacing_scale = sp.get('declared_scale') or sp.get('scale') or sp.get('all_px_values') or []
    spacing_scale = [v for v in spacing_scale if isinstance(v, (int, float)) and 0 < v < 200]
    spacing_scale_length_norm = min(len(spacing_scale), 14) / 14
    spacing_scale_max_norm = min(_safe_max(spacing_scale, 0) / 100, 1.0)
    section_padding_min = sp.get('section_vertical_padding_min_px') or sp.get('section_padding_min')
    section_padding_min_norm = min(section_padding_min / 100, 1.5) if isinstance(section_padding_min, (int, float)) else UNKNOWN
    # absence of the flag does NOT mean "has explicit dividers" — it's unknown.
    no_explicit_dividers = 1.0 if 'no_explicit_section_dividers' in str(sp) else UNKNOWN

    # ---------- Radius ----------
    radius_pairs = radius.get('role_radius_pairs') if isinstance(radius, dict) else None
    radius_values = []
    if isinstance(radius_pairs, dict):
        radius_values = [v for v in radius_pairs.values() if isinstance(v, (int, float))]
    if not radius_values and isinstance(radius, dict):
        radius_values = [v for v in radius.values() if isinstance(v, (int, float))]
    pill_used = 1.0 if any(v >= 1000 for v in radius_values) else 0.0
    non_pill = sorted([v for v in radius_values if 0 < v < 200])
    radius_count_norm = min(len(non_pill), 8) / 8
    radius_max_norm = min(_safe_max(non_pill, 0) / 50, 1.0)
    if len(non_pill) >= 2:
        steps = [non_pill[i+1] / non_pill[i] for i in range(len(non_pill) - 1) if non_pill[i] > 0]
        max_step = _safe_max(steps, 1.0)
        radius_max_step_ratio_norm = min((max_step - 1.0), 1.5) / 1.5
    else:
        radius_max_step_ratio_norm = 0.0

    # ---------- Motion ----------
    durations = motion.get('durations_ms') or []
    durations = [d for d in durations if isinstance(d, (int, float)) and 0 < d < 3000]
    duration_count_norm = min(len(durations), 6) / 6
    duration_avg_norm = min(_safe_avg(durations, 0) / 500, 1.0)
    bezier_curves = motion.get('cubic_bezier_curves') or []
    has_bounce = 1.0 if any('1.5' in str(c) or 'spring' in str(c).lower() for c in bezier_curves) else 0.0

    # ---------- Components (heuristic) ----------
    # v1.10.0: component dims are UNKNOWN when the tokens carry no components
    # block (the A1 corpus never recorded buttons), rather than a fabricated 0.
    button_section = components.get('buttons') if isinstance(components, dict) else None
    if isinstance(button_section, dict):
        num_button_variants = len(button_section)
        primary_btn = button_section.get('primary_brand') or button_section.get('primary_cta') or {}
        radius_field = primary_btn.get('radius') if isinstance(primary_btn, dict) else None
        button_radius = radius_field if isinstance(radius_field, (int, float)) else 8
        button_radius_norm = min(button_radius / 24, 1.5)
        num_button_variants_norm = min(num_button_variants, 6) / 6
        has_rgba_translucent_bg = 1.0 if ('rgba(255' in str(button_section) and ',0.0' in str(button_section)) else 0.0
    else:
        button_radius_norm = UNKNOWN
        num_button_variants_norm = UNKNOWN
        has_rgba_translucent_bg = UNKNOWN

    # shadow-as-border heuristic — UNKNOWN if no shadow data anywhere
    card_block = components.get('card') if isinstance(components, dict) else None
    rgba_shadows = card_block.get('shadow', '') if isinstance(card_block, dict) else ''
    depth_shadows = str((tokens.get('depth_elevation', {}) or {}).get('rgba_shadows', ''))
    if not rgba_shadows:
        rgba_shadows = depth_shadows
    if not rgba_shadows and not isinstance(card_block, dict):
        uses_shadow_as_border = UNKNOWN
    else:
        uses_shadow_as_border = 1.0 if '0px 0px 0px 1px' in rgba_shadows else 0.0

    # status palette — accept either color.status or color.state; UNKNOWN if neither block exists
    status_block = color.get('status') if isinstance(color.get('status'), dict) else None
    state_block = color.get('state') if isinstance(color.get('state'), dict) else None
    chosen = status_block or state_block
    if chosen is None:
        has_status_palette = UNKNOWN
    else:
        has_status_palette = 1.0 if len(chosen) >= 3 else 0.0

    # ---------- v1.13.0 discriminative dims (skill-issue-2026-06-18 #2) ----------
    # Color refinement: center lightness, contrast range, chroma spread (one punchy
    # accent vs many medium colors), warmth of the neutrals.
    palette_mean_L = _safe_avg(L_values, 0.5) if L_values else UNKNOWN
    L_contrast_range = (neutral_L_max - neutral_L_min) if L_values else UNKNOWN
    if chromatic:
        c_vals = [c[1] for c in chromatic]
        chroma_spread = min((max(c_vals) - (sum(c_vals) / len(c_vals))) / 0.4, 1.0)
    else:
        chroma_spread = UNKNOWN
    neutral_chromas = []
    for hx in all_hexes:
        try:
            _nL, _nC, _nH = hex_to_oklch(hx)
            if _nC < 0.06:
                neutral_chromas.append(_nC)
        except Exception:
            continue
    neutral_avg_chroma = (min(_safe_avg(neutral_chromas, 0.0) / 0.06, 1.0)
                          if neutral_chromas else UNKNOWN)

    # Font-family signal — the dimension the old encoder barely saw. This is what
    # separates the adjective-stub systems (identical palette, different fonts) and
    # carries dev-tool (mono) / multi-typeface identity.
    fam_names = []
    for f in (typo.get('families') or []):
        nm = (f.get('family') if isinstance(f, dict) else f)
        if nm:
            fam_names.append(str(nm).strip().lower())
    for role in ('display', 'body', 'mono'):
        blk = typo.get(role)
        if isinstance(blk, dict) and blk.get('family'):
            fam_names.append(str(blk['family']).strip().lower())
    distinct_fams = set(fam_names)
    if distinct_fams:
        has_mono = 1.0 if any('mono' in n for n in distinct_fams) else 0.0
        non_mono = {n for n in distinct_fams if 'mono' not in n}
        num_font_families_norm = min(len(non_mono), 4) / 4
    else:
        has_mono = UNKNOWN
        num_font_families_norm = UNKNOWN

    # Weight-ladder spread: narrow (e.g. Linear 400–590) vs wide (100–900 stub default).
    if len(weights) >= 2:
        weight_spread_norm = (max(weights) - min(weights)) / 900
    elif weights:
        weight_spread_norm = 0.0
    else:
        weight_spread_norm = UNKNOWN

    return [
        primary_brand_L, primary_brand_C, primary_brand_H_sin, primary_brand_H_cos,
        neutral_L_min, neutral_L_max, palette_avg_saturation_norm, entropy,
        body_contrast_norm, is_dark_canvas, chromatic_count_norm, palette_temp_score,
        scale_ratio, scale_size_count_norm, body_size_norm, display_size_max_norm,
        line_height_body, weight_max_norm, has_serif, is_humanist_sans,
        base_norm, spacing_scale_length_norm, spacing_scale_max_norm,
        section_padding_min_norm, no_explicit_dividers,
        radius_count_norm, radius_max_norm, pill_used, radius_max_step_ratio_norm,
        duration_count_norm, duration_avg_norm, has_bounce,
        button_radius_norm, num_button_variants_norm, uses_shadow_as_border,
        has_rgba_translucent_bg, has_status_palette,
        palette_mean_L, L_contrast_range, chroma_spread, neutral_avg_chroma,
        has_mono, num_font_families_norm, weight_spread_norm,
    ]


# v1.14.0 (skill-issue-2026-06-18 #2/#3): the "adjective" stub systems (clean,
# colorful, simple, corporate, futuristic, sleek, storytelling, cosmic, creative,
# ...) were never really extracted — they all carry the IDENTICAL Tailwind-default
# 7-hex palette and have no rule files. In the neighbor corpus they only create
# duplicate near-0 neighbors and confusing "clone of 'colorful'" messages. Skip any
# system whose palette is exactly this stub set (detected by value, not by name, so
# it catches any future stub regardless of label).
STUB_PALETTE = frozenset({
    '#3B82F6', '#8B5CF6', '#16A34A', '#D97706', '#DC2626', '#FFFFFF', '#111827',
})


def _is_stub(tokens: dict) -> bool:
    hexes = {str(h).upper() for h in ((tokens.get('color') or {}).get('all_hex_colors') or [])}
    return bool(hexes) and hexes == STUB_PALETTE


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--skill-root', default=os.path.normpath(os.path.join(HERE, '..')))
    p.add_argument('--keep-stubs', action='store_true',
                   help='Include Tailwind-default stub systems (default: exclude them — #2/#3)')
    p.add_argument('--include-only', help='Comma-separated list of system names to include (default: all)')
    args = p.parse_args()

    tokens_dir = os.path.join(args.skill_root, 'grammar', 'tokens')
    output_path = os.path.join(args.skill_root, 'grammar', 'meta', 'neighbor-corpus.json')

    only = set(args.include_only.split(',')) if args.include_only else None

    systems = {}
    skipped_stubs = []
    for fname in sorted(os.listdir(tokens_dir)):
        if not fname.endswith('.json'):
            continue
        sys_name = fname[:-5]
        if only and sys_name not in only:
            continue
        with open(os.path.join(tokens_dir, fname)) as f:
            try:
                tokens = json.load(f)
            except Exception as e:
                print(f'  skip {sys_name} (invalid JSON: {e})', file=sys.stderr)
                continue
        if not args.keep_stubs and _is_stub(tokens):
            skipped_stubs.append(sys_name)
            continue
        try:
            vec = encode(tokens)
        except Exception as e:
            print(f'  skip {sys_name} (encode error: {e})', file=sys.stderr)
            continue
        systems[sys_name] = {
            'vector': [round(v, 4) if isinstance(v, (int, float)) else None for v in vec],
            'dialect': tokens.get('dialect'),
            'extracted_at': tokens.get('extracted_at'),
        }

    # v1.7.1: idempotent built_at — only bump when systems vectors actually
    # change. Otherwise consecutive `build_neighbor_corpus` runs produce a
    # new file even when no input differs.
    new_now = datetime.datetime.utcnow().isoformat() + 'Z'
    built_at = new_now
    try:
        if os.path.isfile(output_path):
            with open(output_path) as f:
                prev = json.load(f)
            if prev.get('systems') == systems and prev.get('dim_names') == DIM_NAMES and prev.get('weights') == DIM_WEIGHTS:
                built_at = prev.get('built_at', new_now)
    except Exception:
        pass

    output = {
        'schema_version': '1.0',
        'built_at': built_at,
        'dim_count': len(DIM_NAMES),
        'dim_names': DIM_NAMES,
        'weights': DIM_WEIGHTS,
        'systems': systems,
    }
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f'Wrote {output_path}')
    print(f'  systems encoded: {len(systems)}')
    print(f'  dim_count: {len(DIM_NAMES)}')
    if skipped_stubs:
        print(f'  skipped {len(skipped_stubs)} Tailwind-default stub systems (#2/#3): '
              f'{", ".join(skipped_stubs)}')


if __name__ == '__main__':
    main()
