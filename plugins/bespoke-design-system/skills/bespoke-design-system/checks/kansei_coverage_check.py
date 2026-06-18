#!/usr/bin/env python3
"""
kansei_coverage_check.py — Subcheck 3 of B5 P0 gate: Kansei coverage + reverse conflicts.

Inputs:
  - profile (B1 user_profile yaml as dict): kansei_words.positive[] + reverse_constraint[]
  - provenance_report (B4 output): list of decisions, each with adaptation.fully_aligned_kansei[]
                                                         + adaptation.needs_extension_kansei[]

Output: {passed, coverage_rate, addressed, uncovered, reverse_violations}

Pass if coverage_rate >= threshold (default 0.8) AND len(reverse_violations) == 0.

v1.13.1: inputs may be YAML or JSON; runs WITHOUT PyYAML if given JSON (else degrades
to evaluable:false instead of crashing). `--kansei` overrides the profile's positive
list with the selected B4.5 winner's kansei (改动4: judge coverage against the winner,
not the full concept union).

Usage:
  python3 kansei_coverage_check.py --profile <user_profile.yaml|.json> --provenance <prov.yaml|.json>
  python3 kansei_coverage_check.py --profile ... --provenance ... --kansei structured,precise,calm,...
"""
from __future__ import annotations
import sys
import argparse
import json

# v1.13.1 (skill-issue-2026-06-18 #5): do NOT hard-crash when PyYAML is absent.
# All other B5 checks read JSON; this was the only one that exit(2)'d in a clean
# env (PEP 668 blocks `pip install`). Now: load YAML when available, else accept
# JSON, else degrade gracefully like neighbor_check (evaluable:false, exit 0) so
# the overall B5 gate doesn't blow up.
try:
    import yaml  # type: ignore
    _HAVE_YAML = True
except ImportError:
    yaml = None  # type: ignore
    _HAVE_YAML = False


def _load_doc(path: str):
    """Load a YAML or JSON document. Works WITHOUT PyYAML if the file is JSON.
    Returns (doc, error_message_or_None)."""
    with open(path) as f:
        text = f.read()
    if text.lstrip()[:1] in '{[':          # looks like JSON → dep-free path
        try:
            return json.loads(text), None
        except Exception as e:
            return None, f'{path}: looks like JSON but failed to parse ({e})'
    if _HAVE_YAML:
        return yaml.safe_load(text), None
    try:                                    # no yaml — last resort, maybe it's JSON
        return json.loads(text), None
    except Exception:
        return None, (f'PyYAML not installed and {path} is YAML. Install it '
                      f'(pip install pyyaml) or pass a JSON profile/provenance.')


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
        # Also check user_kansei_coverage.addressed_in_this_decision (B4 schema variant).
        # Schema-tolerant: per SKILL.md §六 3.3.7, user_kansei_coverage SHOULD be a dict
        # with `addressed_in_this_decision: [<word>, ...]`. Older drafts sometimes wrote
        # it as a free-form string ("precise + confident"). Accept both gracefully.
        just = (d or {}).get('justification', {}) or {}
        cov = just.get('user_kansei_coverage')
        if isinstance(cov, dict):
            for k in (cov.get('addressed_in_this_decision') or []):
                if isinstance(k, str):
                    addressed.add(k.lower().strip())
        elif isinstance(cov, str):
            # Legacy free-form string form: extract any tokens that look like kansei
            # words (lowercase identifiers). This is best-effort, not authoritative.
            import re as _re
            for tok in _re.findall(r'[a-z_]+', cov.lower()):
                addressed.add(tok)
        # else: cov is None or unsupported type — skip silently
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
        threshold: float = 0.8, kansei_override: list | None = None) -> dict:
    kansei_section = (profile or {}).get('kansei_words') or {}
    user_reverse_raw = kansei_section.get('reverse_constraint') or []
    if kansei_override:
        # v1.13.1 改动4 fix: after B4.5 picks a winner, judge coverage against the
        # WINNER concept's kansei (its kansei_lean + shared base), NOT the full
        # 3-concept union — otherwise the winner is penalised for not covering the
        # rejected concepts' kansei (the union-vs-winner tension, skill-issue #4).
        user_positive_raw = kansei_override
        kansei_basis = 'winner_override'
    else:
        user_positive_raw = kansei_section.get('positive') or []
        kansei_basis = 'profile_positive'
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
        'kansei_basis': kansei_basis,
        'kansei_evaluated': sorted(user_positive),
        'addressed': sorted(addressed),
        'addressed_in_user_positive': sorted(intersection),
        'uncovered': uncovered,
        'reverse_violations': reverse_violations,
        'threshold': threshold,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--profile', required=True, help='Path to user_profile YAML or JSON')
    p.add_argument('--provenance', required=True, help='Path to provenance YAML or JSON')
    p.add_argument('--rules-index', help='Optional path to rules index JSON for source-rule kansei lookup')
    p.add_argument('--threshold', type=float, default=0.8)
    p.add_argument('--kansei', help='Comma-separated WINNER kansei to judge coverage against, '
                                    'overriding profile.kansei_words.positive (v1.13.1 改动4 — use the '
                                    "selected B4.5 winner's kansei, not the full concept union)")
    args = p.parse_args()

    profile_doc, err = _load_doc(args.profile)
    provenance = None
    if err is None:
        provenance, err = _load_doc(args.provenance)
    if err is not None:
        # Graceful degrade (like neighbor_check missing-corpus): don't fail the whole gate.
        json.dump({'passed': True, 'evaluable': False, 'reason': err},
                  sys.stdout, indent=2, ensure_ascii=False)
        print()
        return
    # The B1 profile may be wrapped in a top-level 'user_profile' key (as inferred-fields.yaml is)
    profile = profile_doc.get('user_profile', profile_doc) if isinstance(profile_doc, dict) else profile_doc

    rules_index = None
    if args.rules_index:
        with open(args.rules_index) as f:
            rules_index = json.load(f)

    kansei_override = [k.strip() for k in args.kansei.split(',') if k.strip()] if args.kansei else None
    result = run(profile, provenance, rules_index, threshold=args.threshold,
                 kansei_override=kansei_override)
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == '__main__':
    main()
