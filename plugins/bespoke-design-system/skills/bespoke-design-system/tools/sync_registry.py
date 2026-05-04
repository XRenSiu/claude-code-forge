#!/usr/bin/env python3
"""
sync_registry.py — Reconcile grammar/meta/source-registry.json's extraction_state
with on-disk truth.

For each registered system, check whether grammar/{tokens,rationale,rules}/
contain the system's outputs and set:
  - 'pending'         no tokens, no rationale, no rules
  - 'tokens_only'     tokens.json present, no rationale, no rules
  - 'rationale_only'  rationale.md present, no rules
  - 'rules'           rationale.md + rules.yaml (no tokens — rare)
  - 'full'            tokens.json + rationale.md + rules.yaml all present

Run this:
  - After manual A2/A3 work (extract_tokens.py auto-syncs A1 only)
  - Before rebuild_graph (rebuild_graph.py also calls this internally as of v1.6.0)
  - Periodically as a sanity check

Usage:
  python3 sync_registry.py [--dry-run]
"""
from __future__ import annotations
import sys
import os
import json
import argparse
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.normpath(os.path.join(HERE, '..'))
REGISTRY_PATH = os.path.join(SKILL_ROOT, 'grammar', 'meta', 'source-registry.json')
GRAMMAR_ROOT = os.path.join(SKILL_ROOT, 'grammar')


def derive_state(system_name: str) -> str:
    has_tokens = os.path.isfile(os.path.join(GRAMMAR_ROOT, 'tokens', f'{system_name}.json'))
    has_rationale = os.path.isfile(os.path.join(GRAMMAR_ROOT, 'rationale', f'{system_name}.md'))
    has_rules = os.path.isfile(os.path.join(GRAMMAR_ROOT, 'rules', f'{system_name}.yaml'))
    if has_tokens and has_rationale and has_rules:
        return 'full'
    if has_rationale and has_rules:
        return 'rules'
    if has_rationale:
        return 'rationale_only'
    if has_tokens:
        return 'tokens_only'
    return 'pending'


def sync(dry_run: bool = False) -> dict:
    if not os.path.isfile(REGISTRY_PATH):
        return {'error': f'registry not found at {REGISTRY_PATH}'}
    with open(REGISTRY_PATH) as f:
        reg = json.load(f)
    systems = reg.setdefault('systems', {})
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    changes = []
    state_count = {}
    for name, entry in systems.items():
        new_state = derive_state(name)
        state_count[new_state] = state_count.get(new_state, 0) + 1
        old_state = entry.get('extraction_state')
        if old_state != new_state:
            changes.append({'system': name, 'from': old_state, 'to': new_state})
            if not dry_run:
                entry['extraction_state'] = new_state
                if new_state != 'pending':
                    entry['last_extracted_at'] = ts
    if not dry_run and changes:
        with open(REGISTRY_PATH, 'w') as f:
            json.dump(reg, f, indent=2, ensure_ascii=False)
    return {
        'changes': changes,
        'state_distribution': state_count,
        'total_systems': len(systems),
        'dry_run': dry_run,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--dry-run', action='store_true', help='Show what would change without writing')
    p.add_argument('--json', action='store_true')
    args = p.parse_args()

    result = sync(dry_run=args.dry_run)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    if 'error' in result:
        print(f'ERROR: {result["error"]}')
        sys.exit(1)
    print(f'{"[dry-run] " if args.dry_run else ""}Synced {len(result["changes"])} entries (of {result["total_systems"]} registered)')
    print(f'State distribution: {result["state_distribution"]}')
    if result['changes']:
        print('\nChanges:')
        for c in result['changes'][:20]:
            print(f'  {c["system"]}: {c["from"]} -> {c["to"]}')
        if len(result['changes']) > 20:
            print(f'  ... ({len(result["changes"])-20} more)')


if __name__ == '__main__':
    main()
