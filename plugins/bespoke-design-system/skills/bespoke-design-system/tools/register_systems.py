#!/usr/bin/env python3
"""
register_systems.py — Idempotently register/update entries in source-registry.json.

Scans <skill_root>/source-design-systems/*/DESIGN.md, computes hash,
classifies dialect via scan_dialect.py, and merges into source-registry.json.
Preserves existing extraction_state for already-known systems.

Usage:
  python3 register_systems.py [--skill-root <path>] [--source-collection <name>] [--repo <owner/name>] [--base-path <p>]
"""
import os, sys, json, argparse, datetime, hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scan_dialect import scan as scan_design_md  # type: ignore


def fingerprint(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    here = os.path.dirname(os.path.abspath(__file__))
    p.add_argument('--skill-root', default=os.path.normpath(os.path.join(here, '..')))
    p.add_argument('--source-collection', default='custom', help='Tag for source_type (e.g. open-design)')
    p.add_argument('--repo', default='', help='GitHub owner/name for source_url construction')
    p.add_argument('--base-path', default='', help='Path inside repo (e.g. design-systems)')
    args = p.parse_args()

    src_root = os.path.join(args.skill_root, 'source-design-systems')
    registry_path = os.path.join(args.skill_root, 'grammar', 'meta', 'source-registry.json')

    if not os.path.isdir(src_root):
        print(f'ERROR: {src_root} not found', file=sys.stderr)
        sys.exit(2)

    # Load existing registry
    try:
        with open(registry_path) as f:
            registry = json.load(f)
    except Exception:
        registry = {
            '$schema_description': 'Registry of imported design systems. Updated by tools/register_systems.py.',
            'systems': {},
            '_template': {},
        }

    if 'systems' not in registry:
        registry['systems'] = {}

    now = datetime.datetime.utcnow().isoformat() + 'Z'
    added, updated, unchanged = 0, 0, 0

    for entry in sorted(os.listdir(src_root)):
        path = os.path.join(src_root, entry, 'DESIGN.md')
        if not os.path.isfile(path):
            continue

        h = fingerprint(path)
        scan = scan_design_md(path)

        if entry in registry['systems']:
            existing = registry['systems'][entry]
            if existing.get('fingerprint_hash') == h:
                unchanged += 1
                if 'dialect' not in existing:
                    existing['dialect'] = scan['dialect']
                    existing['section_count'] = scan['section_count']
                continue
            else:
                existing['fingerprint_hash'] = h
                existing['dialect'] = scan['dialect']
                existing['section_count'] = scan['section_count']
                existing['last_modified_at'] = now
                existing['needs_reextraction'] = True
                updated += 1
                continue

        source_url = ''
        if args.repo and args.base_path:
            source_url = f'https://github.com/{args.repo}/blob/main/{args.base_path}/{entry}/DESIGN.md'
        elif args.repo:
            source_url = f'https://github.com/{args.repo}/blob/main/{entry}/DESIGN.md'

        registry['systems'][entry] = {
            'added_at': now,
            'source_type': args.source_collection or 'user_added',
            'source_url': source_url,
            'license': 'see source',
            'commercial_use': 'unknown',
            'last_extracted_at': None,
            'rule_count': 0,
            'fingerprint_hash': h,
            'dialect': scan['dialect'],
            'section_count': scan['section_count'],
            'size_bytes': scan['size_bytes'],
            'extraction_state': 'pending',
        }
        added += 1

    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    print(f'Registry updated: +{added} new, ~{updated} changed, ={unchanged} unchanged')
    print(f'Total systems registered: {len(registry["systems"])}')


if __name__ == '__main__':
    main()
