#!/usr/bin/env python3
"""
kansei_coverage_check.py — Subcheck 3 of B5 P0 gate: Kansei coverage + reverse conflicts.

Inputs:
  - profile (B1 user_profile yaml as dict): kansei_words.positive[] + reverse_constraint[]
  - provenance_report (B4 output): list of decisions, each with adaptation.fully_aligned_kansei[]
                                                         + adaptation.needs_extension_kansei[]

Output: {passed, coverage_rate, addressed, uncovered, reverse_violations}

Pass if coverage_rate >= threshold (default 0.8) AND len(reverse_violations) == 0.

Usage:
  python3 kansei_coverage_check.py --profile <user_profile.yaml> --provenance <provenance.yaml>
"""
from __future__ import annotations
import sys
import argparse
import json

try:
    import yaml
except ImportError:
    print('ERROR: PyYAML required', file=sys.stderr); sys.exit(2)


def collect_addressed_kansei(provenance: dict | list) -> set[str]:
    """Walk a provenance YAML structure (either {decisions: [...]} or [...]) and
    collect all kansei words that decisions claim to address."""
    decisions = provenance.get('decisions', provenance) if isinstance(provenance, dict) else provenance
    if not isinstance(decisions, list):
        return set()
    addressed = set()
    for d in decisions:
        adaptation = (d or {}).get('adaptation', {}) or {}
        for k in (adaptation.get('fully_aligned_kansei') or []):
            if isinstance(k, str):
                addressed.add(k.lower().strip())
        for k in (adaptation.get('needs_extension_kansei') or []):
            if isinstance(k, str):
                addressed.add(k.lower().strip())
        # Also check user_kansei_coverage.addressed_in_this_decision (B4 schema variant)
        just = (d or {}).get('justification', {}) or {}
        cov = just.get('user_kansei_coverage', {}) or {}
        for k in (cov.get('addressed_in_this_decision') or []):
            if isinstance(k, str):
                addressed.add(k.lower().strip())
    return addressed


def detect_reverse_violations(provenance: dict | list, reverse_constraint: set[str],
                              corpus_rules: dict | None = None) -> list[dict]:
    """Find decisions whose source rule kansei (or own kansei tags) intersect the user's
    reverse_constraint set. Each match is a blocker.

    `corpus_rules`: optional {rule_id: {kansei: [...]}} index for cross-checking source rules.
    """
    decisions = provenance.get('decisions', provenance) if isinstance(provenance, dict) else provenance
    if not isinstance(decisions, list):
        return []
    violations = []
    for d in decisions:
        adaptation = (d or {}).get('adaptation', {}) or {}
        # Same source: any kansei the decision claims to address
        decision_kansei = set()
        for k in (adaptation.get('fully_aligned_kansei') or []):
            if isinstance(k, str):
                decision_kansei.add(k.lower().strip())
        for k in (adaptation.get('needs_extension_kansei') or []):
            if isinstance(k, str):
                decision_kansei.add(k.lower().strip())

        # Pull source rule kansei (if rules index provided)
        if corpus_rules:
            inh = (d or {}).get('inheritance', {}) or {}
            for rule_id in (inh.get('source_rules') or []):
                rule = corpus_rules.get(rule_id, {})
                for k in (rule.get('preconditions', {}).get('kansei') or []):
                    if isinstance(k, str):
                        decision_kansei.add(k.lower().strip())

        violated = decision_kansei & reverse_constraint
        if violated:
            violations.append({
                'decision': d.get('decision', '<unnamed>'),
                'section': d.get('section', '?'),
                'violated_kansei': sorted(violated),
                'severity': 'blocker',
            })
    return violations


def run(profile: dict, provenance: dict | list, corpus_rules: dict | None = None,
        threshold: float = 0.8) -> dict:
    kansei_section = (profile or {}).get('kansei_words') or {}
    user_positive_raw = kansei_section.get('positive') or []
    user_reverse_raw = kansei_section.get('reverse_constraint') or []
    user_positive = {k.lower().strip() for k in user_positive_raw if isinstance(k, str)}
    user_reverse = {k.lower().strip() for k in user_reverse_raw if isinstance(k, str)}

    addressed = collect_addressed_kansei(provenance)
    intersection = addressed & user_positive
    if not user_positive:
        coverage = 1.0
    else:
        coverage = len(intersection) / len(user_positive)

    uncovered = sorted(user_positive - addressed)
    reverse_violations = detect_reverse_violations(provenance, user_reverse, corpus_rules)

    passed = coverage >= threshold and len(reverse_violations) == 0
    return {
        'passed': passed,
        'coverage_rate': round(coverage, 3),
        'addressed': sorted(addressed),
        'addressed_in_user_positive': sorted(intersection),
        'uncovered': uncovered,
        'reverse_violations': reverse_violations,
        'threshold': threshold,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--profile', required=True, help='Path to user_profile YAML')
    p.add_argument('--provenance', required=True, help='Path to provenance YAML')
    p.add_argument('--rules-index', help='Optional path to rules index JSON for source-rule kansei lookup')
    p.add_argument('--threshold', type=float, default=0.8)
    args = p.parse_args()

    with open(args.profile) as f:
        profile_doc = yaml.safe_load(f)
    # The B1 profile may be wrapped in a top-level 'user_profile' key (as inferred-fields.yaml is)
    profile = profile_doc.get('user_profile', profile_doc) if isinstance(profile_doc, dict) else profile_doc

    with open(args.provenance) as f:
        provenance = yaml.safe_load(f)

    rules_index = None
    if args.rules_index:
        with open(args.rules_index) as f:
            rules_index = json.load(f)

    result = run(profile, provenance, rules_index, threshold=args.threshold)
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == '__main__':
    main()
