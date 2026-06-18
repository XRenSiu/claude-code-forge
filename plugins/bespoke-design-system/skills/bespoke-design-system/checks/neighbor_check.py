#!/usr/bin/env python3
"""
neighbor_check.py — Subcheck 4 of B5 P0 gate: DISTINCTIVENESS band vs corpus.

Loads grammar/meta/neighbor-corpus.json (built by tools/build_neighbor_corpus.py),
encodes the generated tokens with the same encoder, computes weighted Euclidean
distance to every system, and grades the NEAREST distance against a two-sided band.

=== v1.11.0 — semantic inversion (was: proximity reward) ===

BEFORE (v1.10.0 and earlier) this check REWARDED proximity to the corpus:
  distance < 0.3 → pass / 0.3–0.6 → needs_review / ≥0.6 → reject.
That was wrong in two compounding ways, both proven empirically against the
137-system corpus (see skill-issue-2026-06-18):

  1. NO-OP FLOOR. The corpus's own maximum nearest-neighbor distance is 0.26 —
     i.e. EVERY real system sits within 0.26 of another. A pass threshold of 0.30
     was set ABOVE that ceiling, so the gate never rejected anything the pipeline
     produced. It rubber-stamped output.
  2. PROXIMITY = COPYING. The pipeline (B2 retrieve → B3 densest self-consistent
     island → B4 translate) already converges on corpus members; a gate that
     *rewards* small distance therefore rewards cloning. The shipped
     examples/code-review-saas output is Linear with the accent recolored, scored
     a passing ~0.18, and was indistinguishable to this check from a real design.

This check now grades a DISTINCTIVENESS BAND instead. Distance from the corpus is
a thing to EARN (bounded), not a defect to minimise:

  d < clone_threshold (0.05)              → reject       (derivative_clone)
  clone ≤ d < suspect_threshold (0.12)    → needs_review (derivative_suspect)
  suspect ≤ d ≤ distinct_ceiling (0.45)   → pass         (distinctive)
  d > distinct_ceiling                    → needs_review (far_outlier)

Thresholds are CALIBRATED from the corpus's own distance distribution, not picked
by feel (skill-issue-2026-06-18):
  - corpus internal nearest-neighbor distances: median 0.12, p75 0.15, p90 0.20,
    max 0.26. So 0.12 (the median) is "as close as a typical real system is to its
    nearest peer" — a sensible floor for "this is its own thing".
  - an exact re-encode of any corpus member scores 0.0000 (perfect clone caught);
    a full structural clone of Linear with the brand hue nudged ±10° scores
    0.01–0.04 (caught by clone_threshold), ±20° scores ~0.08 (suspect).
  - 0.45 sits well above the corpus's 0.26 max NN, so far_outlier means "more
    distinct from EVERY known system than any real system is" — possibly bold,
    possibly incoherent. We do NOT auto-reject it: this check cannot tell bold
    from broken, so it defers to coherence_check / archetype_check / rationale.

=== HONEST LIMITATION (load-bearing — read before trusting a green) ===

This is a TOKEN-STATISTICAL distance over 37 low-level dims (color L/C/H, dark
canvas, scale, radius, weight, motion, component flags). It can catch a
token-space clone. It CANNOT see concept-level genericness — the organizing idea,
the signature move, the relationship between brand narrative and form. A design
can clone Linear's entire structural gestalt, recolor the accent, score ~0.18 and
PASS here while reading as "Linear again" to any designer. Worse, the encoder is
coarse enough that ~50 corpus systems collapse to <0.08 of a neighbor (e.g.
corporate/futuristic/sleek/storytelling all encode to the same point), so the
clone_threshold MUST stay low to avoid false-flagging legitimately-distinct close
systems. Catching perceived ("very ordinary") genericness is the job of the taste
critic, not this check. A pass here means "not a measurable clone", never "has
taste". See references/tacit-knowledge-boundary.md.

Usage:
  python3 neighbor_check.py <generated_tokens.json>
"""
from __future__ import annotations
import os
import sys
import json
import math
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', 'tools')))
from build_neighbor_corpus import encode, DIM_NAMES, DIM_WEIGHTS  # type: ignore


CORPUS_PATH = os.path.normpath(os.path.join(HERE, '..', 'grammar', 'meta', 'neighbor-corpus.json'))

# Calibrated from the corpus's own distance distribution (skill-issue-2026-06-18).
CLONE_THRESHOLD = 0.05      # below → measurably identical to an existing system
SUSPECT_THRESHOLD = 0.12    # corpus median NN distance — floor for "its own thing"
DISTINCT_CEILING = 0.45     # well above corpus max NN (0.26) — beyond = bold-or-broken


def weighted_euclidean(v1: list, v2: list, weights: list[float]) -> float:
    """Weighted Euclidean distance with UNKNOWN-dimension masking (v1.10.0).

    Any dimension that is None on EITHER side is skipped (we don't know it, so we
    don't accrue distance on it). The denominator stays the FULL weight sum, so
    corpus-internal distances are unchanged — the formerly-constant dims the A1
    corpus never recorded contributed 0 to corpus pairs and now skip to 0 — while
    a new, fully-populated design no longer eats spurious distance on dimensions
    the corpus has no value for. See build_neighbor_corpus.py UNKNOWN note +
    skill-issue-2026-06-13 (#1 serif bias, #2 B4-completeness bias).
    """
    if len(v1) != len(v2) or len(v1) != len(weights):
        raise ValueError(f'vector length mismatch: {len(v1)} vs {len(v2)} vs {len(weights)}')
    s = 0.0
    total_weight = sum(weights)
    for i in range(len(v1)):
        a, b = v1[i], v2[i]
        if a is None or b is None:
            continue  # UNKNOWN on either side → skip (full denominator preserved)
        diff = a - b
        s += weights[i] * diff * diff
    # Normalize by FULL total weight (not active-only) so corpus-internal
    # distances — and therefore the calibrated thresholds — are preserved.
    return math.sqrt(s / total_weight) if total_weight > 0 else math.sqrt(s)


def run(tokens: dict, corpus_path: str = CORPUS_PATH,
        clone_threshold: float = CLONE_THRESHOLD,
        suspect_threshold: float = SUSPECT_THRESHOLD,
        distinct_ceiling: float = DISTINCT_CEILING) -> dict:
    if not os.path.isfile(corpus_path):
        return {
            'passed': True,
            'evaluable': False,
            'reason': f'neighbor-corpus not found at {corpus_path}; run tools/build_neighbor_corpus.py',
        }
    with open(corpus_path) as f:
        corpus = json.load(f)

    weights = corpus.get('weights') or DIM_WEIGHTS
    new_vec = encode(tokens)

    distances = []
    for sys_name, info in corpus.get('systems', {}).items():
        sys_vec = info.get('vector', [])
        try:
            d = weighted_euclidean(new_vec, sys_vec, weights)
            distances.append((sys_name, d))
        except Exception:
            continue
    distances.sort(key=lambda x: x[1])
    nearest = distances[:5]

    if not nearest:
        return {
            'passed': True,
            'evaluable': False,
            'reason': 'no systems in corpus',
        }

    nearest_name, nearest_dist = nearest[0]

    # Two-sided distinctiveness band. Distance is EARNED, not minimised.
    if nearest_dist < clone_threshold:
        verdict, band = 'reject', 'derivative_clone'
        clone_of = nearest_name
        message = (
            f'Token-space clone of "{nearest_name}" (distance {nearest_dist:.3f} < '
            f'{clone_threshold}). The design is measurably identical to an existing '
            f'system in every encoded dimension. This is the failure the pipeline '
            f'must avoid: B3 likely converged on a single dense corpus island and B4 '
            f'reproduced it. Differentiate the concept / signature move, or inject a '
            f'productive tension in B3 — do not ship a recolored existing system.'
        )
    elif nearest_dist < suspect_threshold:
        verdict, band = 'needs_review', 'derivative_suspect'
        clone_of = nearest_name
        message = (
            f'Suspiciously close to "{nearest_name}" (distance {nearest_dist:.3f}, '
            f'below the corpus median nearest-neighbor of {suspect_threshold}). It may '
            f'still be its own design, but verify it has an identity beyond "{nearest_name} '
            f'with a different accent". The taste critic should confirm a distinct '
            f'point of view before this ships.'
        )
    elif nearest_dist <= distinct_ceiling:
        verdict, band = 'pass', 'distinctive'
        clone_of = None
        message = (
            f'Distinctive yet grounded (distance {nearest_dist:.3f} to nearest '
            f'"{nearest_name}", inside [{suspect_threshold}, {distinct_ceiling}]). '
            f'NOTE: this only certifies it is not a TOKEN-SPACE clone. It does NOT '
            f'certify taste or concept-level distinctiveness — a structural clone with '
            f'a recolored accent can land here. Final distinctiveness is the taste '
            f"critic's / a human's call."
        )
    else:
        verdict, band = 'needs_review', 'far_outlier'
        clone_of = None
        message = (
            f'Farther from every known system ({nearest_dist:.3f} to nearest '
            f'"{nearest_name}") than any real system is from its neighbor (corpus max '
            f'~0.26). Could be genuinely novel or could be incoherent — this check '
            f'cannot tell bold from broken. Defer to coherence_check / archetype_check '
            f'/ rationale-judge; do not auto-reject on distance alone.'
        )

    return {
        'passed': verdict == 'pass',
        'evaluable': True,
        'verdict': verdict,
        'band': band,
        'clone_of': clone_of,
        'nearest_distance': round(nearest_dist, 4),
        'nearest_systems': [{'name': n, 'distance': round(d, 4)} for n, d in nearest],
        'message': message,
        'thresholds': {
            'clone': clone_threshold,
            'suspect': suspect_threshold,
            'distinct_ceiling': distinct_ceiling,
        },
        'limitation': 'token-statistical distance only; cannot see concept-level '
                      'genericness — a pass is "not a measurable clone", not "has taste".',
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('tokens_path')
    p.add_argument('--corpus', default=CORPUS_PATH)
    p.add_argument('--clone-threshold', type=float, default=CLONE_THRESHOLD)
    p.add_argument('--suspect-threshold', type=float, default=SUSPECT_THRESHOLD)
    p.add_argument('--distinct-ceiling', type=float, default=DISTINCT_CEILING)
    args = p.parse_args()
    with open(args.tokens_path) as f:
        tokens = json.load(f)
    result = run(tokens, corpus_path=args.corpus,
                 clone_threshold=args.clone_threshold,
                 suspect_threshold=args.suspect_threshold,
                 distinct_ceiling=args.distinct_ceiling)
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == '__main__':
    main()
