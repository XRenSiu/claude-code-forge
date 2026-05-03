#!/usr/bin/env python3
"""
check_state.py — Scan extraction_state across the registered systems.

For each system in source-registry.json, report:
  - has source DESIGN.md?
  - has tokens/<name>.json?
  - has rationale/<name>.md?
  - has rules/<name>.yaml?
  - state: pending | tokens_only | rationale_only | rules_only | full

Used by Claude (or maintainer) to know what work remains.

Usage:
  python3 check_state.py
    -> human-readable summary table

  python3 check_state.py --json
    -> JSON for downstream tools

  python3 check_state.py --pending-tokens   -> list system names needing A1 (programmatic)
  python3 check_state.py --pending-rationale -> list system names needing A2 (LLM)
  python3 check_state.py --pending-rules    -> list system names needing A3 (LLM)
"""
import os, sys, json, argparse


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    here = os.path.dirname(os.path.abspath(__file__))
    skill_root = os.path.normpath(os.path.join(here, '..'))
    p.add_argument('--skill-root', default=skill_root)
    p.add_argument('--json', action='store_true', help='Emit JSON')
    p.add_argument('--pending-tokens', action='store_true')
    p.add_argument('--pending-rationale', action='store_true')
    p.add_argument('--pending-rules', action='store_true')
    p.add_argument('--limit', type=int, default=None, help='Limit list outputs to N entries')
    args = p.parse_args()

    registry_path = os.path.join(args.skill_root, 'grammar', 'meta', 'source-registry.json')
    if not os.path.isfile(registry_path):
        print(f'ERROR: registry not found: {registry_path}', file=sys.stderr)
        sys.exit(2)

    with open(registry_path) as f:
        registry = json.load(f)

    src_root = os.path.join(args.skill_root, 'source-design-systems')
    tokens_root = os.path.join(args.skill_root, 'grammar', 'tokens')
    rationale_root = os.path.join(args.skill_root, 'grammar', 'rationale')
    rules_root = os.path.join(args.skill_root, 'grammar', 'rules')

    state = {}
    for system, meta in registry.get('systems', {}).items():
        has_src = os.path.isfile(os.path.join(src_root, system, 'DESIGN.md'))
        has_tokens = os.path.isfile(os.path.join(tokens_root, f'{system}.json'))
        has_rationale = os.path.isfile(os.path.join(rationale_root, f'{system}.md'))
        has_rules = os.path.isfile(os.path.join(rules_root, f'{system}.yaml'))

        if has_rules:
            phase = 'rules'
        elif has_rationale:
            phase = 'rationale_only'
        elif has_tokens:
            phase = 'tokens_only'
        elif has_src:
            phase = 'pending'
        else:
            phase = 'missing_source'
        state[system] = {
            'phase': phase,
            'dialect': meta.get('dialect'),
            'has_src': has_src,
            'has_tokens': has_tokens,
            'has_rationale': has_rationale,
            'has_rules': has_rules,
        }

    pending_tokens = sorted([s for s, st in state.items() if not st['has_tokens'] and st['has_src']])
    pending_rationale = sorted([s for s, st in state.items() if not st['has_rationale'] and st['has_tokens']])
    pending_rules = sorted([s for s, st in state.items() if not st['has_rules'] and st['has_rationale']])

    if args.pending_tokens:
        for s in (pending_tokens[:args.limit] if args.limit else pending_tokens):
            print(s)
        return
    if args.pending_rationale:
        for s in (pending_rationale[:args.limit] if args.limit else pending_rationale):
            print(s)
        return
    if args.pending_rules:
        for s in (pending_rules[:args.limit] if args.limit else pending_rules):
            print(s)
        return

    if args.json:
        json.dump({
            'state_per_system': state,
            'summary': {
                'total': len(state),
                'pending_tokens_count': len(pending_tokens),
                'pending_rationale_count': len(pending_rationale),
                'pending_rules_count': len(pending_rules),
            },
        }, sys.stdout, indent=2)
        print()
        return

    # Human-readable summary
    from collections import Counter
    phase_counts = Counter(st['phase'] for st in state.values())
    dialect_counts = Counter(st['dialect'] for st in state.values())
    print(f'Total registered systems: {len(state)}')
    print(f'\nExtraction phase distribution:')
    for phase in ['missing_source', 'pending', 'tokens_only', 'rationale_only', 'rules']:
        n = phase_counts.get(phase, 0)
        bar = '█' * min(n, 50)
        print(f'  {phase:18s} {n:4d}  {bar}')
    print(f'\nDialect distribution: {dict(dialect_counts)}')
    print(f'\nWork remaining:')
    print(f'  pending A1 (token extract — programmatic): {len(pending_tokens)} systems')
    if pending_tokens[:5]:
        print(f'    e.g. {", ".join(pending_tokens[:5])}{"..." if len(pending_tokens) > 5 else ""}')
    print(f'  pending A2 (rationale extract — LLM):       {len(pending_rationale)} systems')
    if pending_rationale[:5]:
        print(f'    e.g. {", ".join(pending_rationale[:5])}{"..." if len(pending_rationale) > 5 else ""}')
    print(f'  pending A3 (rule abstract — LLM):           {len(pending_rules)} systems')
    if pending_rules[:5]:
        print(f'    e.g. {", ".join(pending_rules[:5])}{"..." if len(pending_rules) > 5 else ""}')


if __name__ == '__main__':
    main()
