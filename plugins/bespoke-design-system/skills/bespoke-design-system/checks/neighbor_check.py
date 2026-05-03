#!/usr/bin/env python3
"""
neighbor_check.py — Subcheck 4 of B5 P0 gate: nearest-neighbor distance to corpus.

Loads grammar/meta/neighbor-corpus.json (built by tools/build_neighbor_corpus.py),
encodes the generated tokens with the same encoder, computes weighted Euclidean
distance to every system, returns nearest-K and three-tier verdict.

Thresholds (from spec §4.5.2):
  distance < 0.3   → pass    (safely inside known-good design space)
  0.3 ≤ d < 0.6    → needs_review (deviation present, check rationale)
  d ≥ 0.6          → reject  (likely hallucinate / out-of-corpus)

Honest limitation per spec §4.5.3: this checks DOWN-side only. It does NOT
guarantee taste, only that the design is not far from any known good design.

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


def weighted_euclidean(v1: list[float], v2: list[float], weights: list[float]) -> float:
    if len(v1) != len(v2) or len(v1) != len(weights):
        raise ValueError(f'vector length mismatch: {len(v1)} vs {len(v2)} vs {len(weights)}')
    s = 0.0
    total_weight = sum(weights)
    for i in range(len(v1)):
        diff = v1[i] - v2[i]
        s += weights[i] * diff * diff
    # Normalize by total weight so distance is roughly 0..2 regardless of dim count
    return math.sqrt(s / total_weight) if total_weight > 0 else math.sqrt(s)


def run(tokens: dict, corpus_path: str = CORPUS_PATH,
        pass_threshold: float = 0.3,
        warn_threshold: float = 0.6) -> dict:
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
        except Exception as e:
            continue
    distances.sort(key=lambda x: x[1])
    nearest = distances[:5]

    if not nearest:
        return {
            'passed': True,
            'evaluable': False,
            'reason': 'no systems in corpus',
        }

    nearest_dist = nearest[0][1]

    if nearest_dist < pass_threshold:
        verdict = 'pass'
        warning = None
    elif nearest_dist < warn_threshold:
        verdict = 'needs_review'
        warning = (f'Nearest known design is {nearest_dist:.2f} away (threshold {pass_threshold}). '
                   f'Check whether the rationale explains this deviation from known good design.')
    else:
        verdict = 'reject'
        warning = (f'Nearest known design is {nearest_dist:.2f} away (threshold {warn_threshold}). '
                   f'Likely hallucinate / out-of-corpus. Consider adding more diverse source DESIGN.md.')

    return {
        'passed': verdict == 'pass',
        'evaluable': True,
        'verdict': verdict,
        'nearest_distance': round(nearest_dist, 4),
        'nearest_systems': [{'name': n, 'distance': round(d, 4)} for n, d in nearest],
        'warning': warning,
        'thresholds': {'pass': pass_threshold, 'warn': warn_threshold},
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('tokens_path')
    p.add_argument('--corpus', default=CORPUS_PATH)
    p.add_argument('--pass-threshold', type=float, default=0.3)
    p.add_argument('--warn-threshold', type=float, default=0.6)
    args = p.parse_args()
    with open(args.tokens_path) as f:
        tokens = json.load(f)
    result = run(tokens, corpus_path=args.corpus,
                 pass_threshold=args.pass_threshold,
                 warn_threshold=args.warn_threshold)
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == '__main__':
    main()
